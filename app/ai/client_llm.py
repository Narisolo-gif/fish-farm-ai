"""Contrat commun à tous les clients LLM (Gemini, GPT-6.2 Sol, faux client de test).

Le workflow ne connaîtra que ClientLLM : changer de fournisseur ne le modifie pas
(exigence du manuel : « isoler l'appel au fournisseur »).
"""

from abc import ABC, abstractmethod

from app.schemas import ReponseLLM


class ErreurLLM(Exception):
    """Le LLM n'a pas pu fournir une réponse exploitable (panne, délai, format invalide).

    Une seule erreur pour tous les fournisseurs : la route d'analyse (tâche 1.5) pourra
    la transformer en réponse d'erreur propre, sans connaître le fournisseur.
    """


class ClientLLM(ABC):
    @abstractmethod
    def generer(self, consignes: str, contexte: str) -> ReponseLLM:
        """Interroge le LLM et renvoie une réponse validée.

        consignes : le prompt système, c'est-à-dire le rôle et les règles du LLM
                    (ne rien inventer, hypothèses formulées comme telles…).
        contexte  : les données du lot et l'alerte à expliquer.
        Lève ErreurLLM en cas d'échec.
        """
