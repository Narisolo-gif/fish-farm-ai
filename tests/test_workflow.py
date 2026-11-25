"""Tests du workflow LangGraph (tâche 1.4).

On assemble les vraies pièces (source simulée, workflow) avec le FAUX client LLM :
on teste notre orchestration, pas la qualité d'un modèle.
"""

import json

import pytest

from app.ai.client_llm import ErreurLLM
from app.ai.faux_client import FauxClientLLM
from app.mock_data import SUIVIS_SIMULES
from app.schemas import AnalyseRequest, AnalyseResponse, ReponseLLM, SuiviLot
from app.services.source_donnees import LotIntrouvable, SourceDonnees
from app.services.source_simulee import SourceSimulee
from app.workflows.analyse_alerte import AlerteIntrouvable, analyser_alerte
from app.workflows.consignes import CONSIGNES_PAR_ALERTE, CONSIGNE_PAR_DEFAUT

REPONSE = ReponseLLM(
    constat="La pesée prévue le 2026-10-27 n'a pas été saisie.",
    explication="Le suivi de la croissance pourrait être faussé.",
    action_proposee="Réaliser une pesée sur échantillon cette semaine.",
)


def lancer(lot_id, code_alerte, client=None, source=None):
    client = client or FauxClientLLM(REPONSE)
    resultat = analyser_alerte(
        AnalyseRequest(lot_id=lot_id, code_alerte=code_alerte),
        source=source or SourceSimulee(),
        client=client,
    )
    return resultat, client


def contexte_envoye(client):
    """Le contexte est envoyé au LLM sous forme de JSON : on le relit."""
    return json.loads(client.appels[0]["contexte"])


# --- Parcours normal --------------------------------------------------------------


def test_le_workflow_renvoie_l_analyse_du_llm():
    resultat, client = lancer(2, "PESEE_EN_RETARD")

    assert isinstance(resultat, AnalyseResponse)
    assert resultat.lot_id == 2
    assert resultat.code_alerte == "PESEE_EN_RETARD"
    assert resultat.analyse == REPONSE
    assert len(client.appels) == 1  # un seul appel au LLM


def test_les_consignes_contiennent_les_regles_generales_et_celles_de_l_alerte():
    _, client = lancer(2, "PESEE_EN_RETARD")
    consignes = client.appels[0]["consignes"]

    assert "N'invente aucune valeur" in consignes
    assert CONSIGNES_PAR_ALERTE["PESEE_EN_RETARD"] in consignes


def test_le_contexte_contient_l_alerte_a_expliquer_et_ses_valeurs():
    _, client = lancer(2, "PESEE_EN_RETARD")
    alerte = contexte_envoye(client)["alerte_a_expliquer"]

    assert alerte["code"] == "PESEE_EN_RETARD"
    assert alerte["jours_de_retard"] == 4
    assert alerte["message"] == "La pesée prévue le 2026-10-27 n'a pas été saisie."


def test_le_contexte_cite_les_autres_alertes_du_lot():
    _, client = lancer(6, "MORTALITE_ELEVEE")
    autres = contexte_envoye(client)["autres_alertes_du_lot"]

    assert {a["code"] for a in autres} == {"OXYGENE_BAS", "TEMPERATURE_ELEVEE"}


def test_le_contexte_ne_contient_ni_donnees_brutes_ni_marqueur_technique():
    _, client = lancer(6, "OXYGENE_BAS")
    texte = client.appels[0]["contexte"]

    assert "series" not in texte
    assert "simulee" not in texte  # info de développement, inutile au LLM


def test_donnees_manquantes_transmises_comme_null():
    _, client = lancer(9, "PESEE_EN_RETARD")
    contexte = contexte_envoye(client)

    # null = « donnée non disponible » : les consignes demandent de le signaler.
    assert contexte["dernieres_valeurs"] is None
    assert contexte["parametres_environnementaux"] is None


# --- Consignes métier ------------------------------------------------------------


def test_chaque_alerte_simulee_a_ses_propres_consignes():
    codes = {a["code"] for suivi in SUIVIS_SIMULES.values() for a in suivi["alertes"]}

    assert codes <= set(CONSIGNES_PAR_ALERTE)


class SourceAvecAlerteNouvelle(SourceDonnees):
    """Simule une alerte que Django ajouterait plus tard, encore sans consignes."""

    def recuperer_suivi(self, lot_id):
        donnees = json.loads(json.dumps(SUIVIS_SIMULES[1]))
        donnees["alertes"] = [{"code": "NOUVELLE_ALERTE", "niveau": "info", "message": "Test."}]
        return SuiviLot.model_validate(donnees)


def test_une_alerte_sans_consignes_utilise_la_consigne_par_defaut():
    _, client = lancer(1, "NOUVELLE_ALERTE", source=SourceAvecAlerteNouvelle())

    assert CONSIGNE_PAR_DEFAUT in client.appels[0]["consignes"]


# --- Erreurs : le LLM n'est jamais appelé pour rien --------------------------------


def test_lot_inconnu():
    client = FauxClientLLM(REPONSE)

    with pytest.raises(LotIntrouvable):
        lancer(999, "PESEE_EN_RETARD", client=client)
    assert client.appels == []


def test_alerte_absente_du_lot_est_refusee():
    # LOT001 n'a aucune alerte : on ne demande pas au LLM d'expliquer une alerte inventée.
    client = FauxClientLLM(REPONSE)

    with pytest.raises(AlerteIntrouvable, match="MORTALITE_ELEVEE"):
        lancer(1, "MORTALITE_ELEVEE", client=client)
    assert client.appels == []


def test_une_panne_du_llm_remonte_en_erreur_llm():
    client = FauxClientLLM(erreur=ErreurLLM("Le modèle de langage est indisponible."))

    with pytest.raises(ErreurLLM):
        lancer(2, "PESEE_EN_RETARD", client=client)


def test_une_reponse_vide_du_llm_est_refusee_a_la_validation():
    client = FauxClientLLM(reponse=None)

    with pytest.raises(ErreurLLM, match="invalide"):
        lancer(2, "PESEE_EN_RETARD", client=client)
