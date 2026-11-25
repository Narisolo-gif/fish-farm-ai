"""Tests du client LLM (tâche 1.3).

Aucun de ces tests n'appelle un vrai LLM : ils sont rapides, gratuits et donnent
toujours le même résultat. Le vrai appel est dans test_client_llm_reel.py,
lancé seulement à la demande.
"""

import pytest
from pydantic import ValidationError

from app.ai.client_langchain import ClientLangChain
from app.ai.client_llm import ClientLLM, ErreurLLM
from app.ai.fabrique import creer_client_llm
from app.ai.faux_client import FauxClientLLM
from app.core.config import Settings
from app.schemas import ReponseLLM

REPONSE = ReponseLLM(
    constat="La pesée prévue le 2026-10-27 n'a pas été saisie.",
    explication="Sans pesée récente, la croissance du lot ne peut pas être suivie.",
    action_proposee="Réaliser une pesée sur échantillon dès que possible.",
)


def config(**valeurs):
    """Configuration de test, indépendante du vrai fichier .env."""
    return Settings(_env_file=None, **valeurs)


class ChaineFactice:
    """Remplace la « chaîne » LangChain (modèle + format imposé) sans réseau.

    Elle renvoie (ou lève) ce qu'on lui demande et garde les messages reçus.
    """

    def __init__(self, resultat=None, erreur=None):
        self.resultat = resultat
        self.erreur = erreur
        self.messages_recus = None

    def invoke(self, messages):
        self.messages_recus = messages
        if self.erreur:
            raise self.erreur
        return self.resultat


# --- Faux client (servira aux tests du workflow) ----------------------------------


def test_faux_client_respecte_le_contrat():
    assert isinstance(FauxClientLLM(REPONSE), ClientLLM)


def test_faux_client_renvoie_la_reponse_prevue_et_garde_les_appels():
    client = FauxClientLLM(REPONSE)

    reponse = client.generer(consignes="Tu es un assistant.", contexte="Lot LOT002")

    assert reponse == REPONSE
    assert client.appels == [{"consignes": "Tu es un assistant.", "contexte": "Lot LOT002"}]


def test_faux_client_peut_simuler_une_panne():
    client = FauxClientLLM(erreur=ErreurLLM("Le modèle de langage est indisponible."))

    with pytest.raises(ErreurLLM):
        client.generer(consignes="...", contexte="...")


# --- Client générique LangChain, testé avec une chaîne factice --------------------


def test_client_envoie_consignes_et_contexte_dans_deux_messages():
    chaine = ChaineFactice(resultat=REPONSE)

    reponse = ClientLangChain(chaine=chaine).generer(consignes="CONSIGNES", contexte="CONTEXTE")

    assert reponse == REPONSE
    # Message « system » = règles du jeu ; message « human » = données à analyser.
    assert chaine.messages_recus == [("system", "CONSIGNES"), ("human", "CONTEXTE")]


def test_client_accepte_une_reponse_sous_forme_de_dict():
    chaine = ChaineFactice(resultat=REPONSE.model_dump())

    assert ClientLangChain(chaine=chaine).generer("c", "d") == REPONSE


def test_client_transforme_une_panne_en_erreur_llm():
    chaine = ChaineFactice(erreur=TimeoutError("délai dépassé"))

    with pytest.raises(ErreurLLM, match="indisponible"):
        ClientLangChain(chaine=chaine).generer("c", "d")


@pytest.mark.parametrize(
    "resultat",
    [
        None,  # le modèle n'a pas réussi à produire le format demandé
        {"constat": "x", "explication": "y"},  # une partie manque
        {"constat": "", "explication": "y", "action_proposee": "z"},  # partie vide
    ],
)
def test_client_refuse_une_reponse_mal_formee(resultat):
    chaine = ChaineFactice(resultat=resultat)

    with pytest.raises(ErreurLLM, match="invalide"):
        ClientLangChain(chaine=chaine).generer("c", "d")


# --- Configuration : le nom du modèle suffit ---------------------------------------


def test_le_nom_du_modele_doit_indiquer_le_fournisseur():
    # "gemini-2.5-flash" seul serait attribué par LangChain à Vertex AI (mauvais service).
    with pytest.raises(ValidationError, match="fournisseur:modele"):
        config(llm_model="gemini-2.5-flash")


def test_fabrique_cree_le_client_a_partir_du_seul_nom_du_modele():
    client = creer_client_llm(config(llm_model="google_genai:gemini-2.5-flash", llm_api_key="cle"))

    assert isinstance(client, ClientLangChain)
    assert client.modele == "google_genai:gemini-2.5-flash"


def test_fabrique_refuse_un_modele_sans_cle():
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        creer_client_llm(config(llm_api_key=""))


def test_fabrique_explique_quel_paquet_installer():
    # Le connecteur OpenAI n'est pas installé : message clair au lieu d'un plantage.
    with pytest.raises(ValueError, match="langchain-openai"):
        creer_client_llm(config(llm_model="openai:gpt-6.2-sol", llm_api_key="cle"))


def test_fabrique_refuse_un_fournisseur_inconnu():
    with pytest.raises(ValueError, match="inconnu"):
        creer_client_llm(config(llm_model="inconnu:modele", llm_api_key="cle"))
