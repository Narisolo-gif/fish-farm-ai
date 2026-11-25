"""Workflow LangGraph d'explication d'une alerte (3 étapes contrôlées, cf. manuel).

    START -> prepare_context -> call_llm -> validate_response -> END

Vocabulaire LangGraph :
- état (state)  : un dictionnaire partagé qui circule d'étape en étape ;
- nœud (node)   : une fonction qui lit l'état et renvoie les clés qu'elle ajoute ;
- arête (edge)  : l'ordre de passage entre les nœuds.
"""

from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.ai.client_llm import ClientLLM, ErreurLLM
from app.schemas import AnalyseRequest, AnalyseResponse, ReponseLLM
from app.services.source_donnees import SourceDonnees
from app.workflows.consignes import consignes_pour
from app.workflows.contexte import construire_contexte


class AlerteIntrouvable(Exception):
    """L'alerte demandée n'existe pas (ou plus) pour ce lot."""

    def __init__(self, lot_id: int, code_alerte: str):
        self.lot_id = lot_id
        self.code_alerte = code_alerte
        super().__init__(f"Alerte {code_alerte} introuvable pour le lot {lot_id}")


class EtatAnalyse(TypedDict, total=False):
    """L'état partagé. total=False : chaque nœud remplit ses clés au fur et à mesure."""

    lot_id: int  # entrée
    code_alerte: str  # entrée
    consignes: str  # rempli par prepare_context
    contexte: str  # rempli par prepare_context
    reponse_llm: Optional[ReponseLLM]  # rempli par call_llm
    resultat: AnalyseResponse  # rempli par validate_response


def construire_workflow(source: SourceDonnees, client: ClientLLM):
    """Assemble le graphe. Source et client sont « injectés » : simulés dans les
    tests, réels en production, sans changer une ligne du workflow."""

    def prepare_context(etat: EtatAnalyse) -> dict:
        # 1. Récupérer les données (lève LotIntrouvable si le lot n'existe pas).
        suivi = source.recuperer_suivi(etat["lot_id"])
        # 2. Vérifier que l'alerte existe VRAIMENT pour ce lot : le LLM n'explique
        #    jamais une alerte que Django n'a pas produite.
        alerte = next((a for a in suivi.alertes if a.code == etat["code_alerte"]), None)
        if alerte is None:
            raise AlerteIntrouvable(etat["lot_id"], etat["code_alerte"])
        # 3. Préparer les deux messages du LLM.
        return {
            "consignes": consignes_pour(alerte.code),
            "contexte": construire_contexte(suivi, alerte),
        }

    def call_llm(etat: EtatAnalyse) -> dict:
        # ErreurLLM (panne, délai…) remonte telle quelle : la route la traitera (1.5).
        return {"reponse_llm": client.generer(etat["consignes"], etat["contexte"])}

    def validate_response(etat: EtatAnalyse) -> dict:
        reponse = etat.get("reponse_llm")
        if reponse is None:
            raise ErreurLLM("Réponse du modèle invalide : réponse vide.")
        try:
            # Revalidation : on ne fait confiance à aucune sortie de LLM sans contrôle.
            analyse = ReponseLLM.model_validate(reponse.model_dump())
        except ValidationError as exc:
            raise ErreurLLM("Réponse du modèle invalide : structure non conforme.") from exc
        return {
            "resultat": AnalyseResponse(
                lot_id=etat["lot_id"],
                code_alerte=etat["code_alerte"],
                analyse=analyse,
            )
        }

    graphe = StateGraph(EtatAnalyse)
    graphe.add_node("prepare_context", prepare_context)
    graphe.add_node("call_llm", call_llm)
    graphe.add_node("validate_response", validate_response)
    graphe.add_edge(START, "prepare_context")
    graphe.add_edge("prepare_context", "call_llm")
    graphe.add_edge("call_llm", "validate_response")
    graphe.add_edge("validate_response", END)
    return graphe.compile()


def analyser_alerte(
    requete: AnalyseRequest, source: SourceDonnees, client: ClientLLM
) -> AnalyseResponse:
    """Point d'entrée : exécute le workflow pour un lot et une alerte."""
    workflow = construire_workflow(source, client)
    etat_final = workflow.invoke({"lot_id": requete.lot_id, "code_alerte": requete.code_alerte})
    return etat_final["resultat"]
