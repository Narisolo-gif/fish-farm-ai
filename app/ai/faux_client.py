"""Faux client LLM pour les tests : réponse fixée à l'avance, aucun réseau.

Un vrai LLM est lent, payant, dépend d'Internet et ne répond jamais deux fois pareil.
Pour tester NOTRE code (workflow, route), on le remplace par ce faux client
déterministe : même entrée -> même sortie, à chaque fois.
"""

from typing import Optional

from app.ai.client_llm import ClientLLM
from app.schemas import ReponseLLM


class FauxClientLLM(ClientLLM):
    def __init__(self, reponse: Optional[ReponseLLM] = None, erreur: Optional[Exception] = None):
        self.reponse = reponse
        self.erreur = erreur
        # Historique des appels : permet aux tests de vérifier CE QUI a été envoyé au LLM.
        self.appels: list[dict] = []

    def generer(self, consignes: str, contexte: str) -> ReponseLLM:
        self.appels.append({"consignes": consignes, "contexte": contexte})
        if self.erreur is not None:
            raise self.erreur
        return self.reponse
