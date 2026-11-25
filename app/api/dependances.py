"""Dépendances FastAPI : qui fournit la source de données et le client LLM à la route.

Notion : avec `Depends(...)`, FastAPI appelle ces fonctions à chaque requête et passe
leur résultat à la route. Dans les tests, `app.dependency_overrides` les remplace par
des versions simulées (faux LLM) sans toucher au code de la route.
"""

import logging
from functools import lru_cache

from fastapi import HTTPException, status

from app.ai.client_llm import ClientLLM
from app.ai.fabrique import creer_client_llm
from app.services.source_donnees import SourceDonnees
from app.services.source_simulee import SourceSimulee

journal = logging.getLogger(__name__)


def obtenir_source() -> SourceDonnees:
    # Provisoire : remplacée par le client HTTP Django à l'étape 3.2.
    return SourceSimulee()


@lru_cache  # un seul client créé pour toute la vie du service (pas un par requête)
def _client_llm_partage() -> ClientLLM:
    return creer_client_llm()


def obtenir_client_llm() -> ClientLLM:
    try:
        return _client_llm_partage()
    except ValueError as exc:
        # Configuration absente ou invalide (clé, modèle) : on ne plante pas le
        # service, seule l'analyse IA est indisponible. Le détail (qui peut citer la
        # configuration) va dans les journaux, pas dans la réponse.
        journal.warning("Client LLM non configuré : %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "LLM_NON_CONFIGURE",
                "message": "L'analyse IA n'est pas disponible pour le moment.",
            },
        ) from exc
