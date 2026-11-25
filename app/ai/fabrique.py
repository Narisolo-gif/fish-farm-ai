"""Fabrique : crée le client LLM à partir de la configuration (.env).

Il n'y a plus de « si Gemini… sinon OpenAI… » : le nom du modèle (LLM_MODEL) suffit.
Les erreurs de configuration sont détectées ici, au démarrage, avec un message clair.
"""

from typing import Optional

from app.ai.client_langchain import ClientLangChain
from app.ai.client_llm import ClientLLM
from app.core.config import Settings, settings as settings_par_defaut


def creer_client_llm(config: Optional[Settings] = None) -> ClientLLM:
    config = config or settings_par_defaut

    if not config.llm_api_key:
        raise ValueError("LLM_API_KEY manquante dans le fichier .env.")

    try:
        return ClientLangChain(
            modele=config.llm_model,
            api_key=config.llm_api_key,
            timeout_s=config.llm_timeout_s,
            temperature=config.llm_temperature,
        )
    except ImportError as exc:
        # Le connecteur du fournisseur n'est pas installé ; LangChain indique lequel.
        raise ValueError(
            f"Connecteur manquant pour {config.llm_model!r} : {exc}. "
            "Ajoutez le paquet indiqué à requirements.txt puis reconstruisez l'image."
        ) from exc
    except ValueError as exc:
        raise ValueError(f"Fournisseur LLM inconnu dans {config.llm_model!r} : {exc}") from exc
