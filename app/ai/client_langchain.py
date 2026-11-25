"""Client LLM GÉNÉRIQUE, valable pour tous les fournisseurs gérés par LangChain.

`init_chat_model("fournisseur:modele")` crée le bon objet LangChain à partir du seul
nom du modèle :
    "google_genai:gemini-2.5-flash"  -> ChatGoogleGenerativeAI (Gemini, tests)
    "openai:gpt-6.2-sol"             -> ChatOpenAI (production, paquet langchain-openai)
Changer de modèle = changer LLM_MODEL (et LLM_API_KEY) dans .env. Rien d'autre.

Rôle de LangChain ici : parler au modèle et lui imposer un format de réponse
(structured output). Il ne fait aucun calcul métier.
"""

from typing import Any, Optional

from pydantic import ValidationError

from app.ai.client_llm import ClientLLM, ErreurLLM
from app.schemas import ReponseLLM


class ClientLangChain(ClientLLM):
    def __init__(
        self,
        modele: str = "",
        api_key: str = "",
        timeout_s: float = 30.0,
        temperature: Optional[float] = 0.2,
        chaine: Optional[Any] = None,
    ):
        """`chaine` permet aux tests d'injecter une chaîne factice (sans réseau)."""
        self.modele = modele
        if chaine is None:
            from langchain.chat_models import init_chat_model

            options = {"api_key": api_key, "timeout": timeout_s, "max_retries": 2}
            # Température basse = réponses plus stables et moins « créatives ».
            # Certains modèles (ex. modèles de raisonnement) refusent ce réglage :
            # LLM_TEMPERATURE vide dans .env -> on ne l'envoie pas.
            if temperature is not None:
                options["temperature"] = temperature

            modele_chat = init_chat_model(modele, **options)
            # Structured output : LangChain transmet le schéma ReponseLLM au modèle
            # et convertit sa réponse en objet ReponseLLM (constat / explication / action).
            chaine = modele_chat.with_structured_output(ReponseLLM)
        self._chaine = chaine

    def generer(self, consignes: str, contexte: str) -> ReponseLLM:
        messages = [
            ("system", consignes),  # rôle et règles du LLM
            ("human", contexte),  # données à analyser
        ]

        try:
            resultat = self._chaine.invoke(messages)
        except Exception as exc:  # réseau, quota, clé invalide, délai dépassé…
            # On ne renvoie pas le détail technique à l'utilisateur ; il reste dans
            # l'exception d'origine (`from exc`) pour les journaux.
            raise ErreurLLM("Le modèle de langage est indisponible.") from exc

        # Double sécurité : on revalide nous-mêmes, quelle que soit la forme reçue.
        if isinstance(resultat, ReponseLLM):
            resultat = resultat.model_dump()
        if not isinstance(resultat, dict):
            raise ErreurLLM("Réponse du modèle invalide : format inattendu.")
        try:
            return ReponseLLM.model_validate(resultat)
        except ValidationError as exc:
            raise ErreurLLM("Réponse du modèle invalide : structure non conforme.") from exc
