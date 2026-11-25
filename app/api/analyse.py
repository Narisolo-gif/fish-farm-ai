"""Route d'analyse : POST /api/v1/ai/analyze (appelée par Django, cf. manuel).

La route est volontairement mince : elle reçoit, délègue au workflow et traduit les
erreurs en réponses HTTP claires. Toute la logique est dans le workflow (1.4).

Codes de réponse :
- 200 : analyse en 3 parties (constat / explication / action proposée) ;
- 422 : requête invalide (refusée par Pydantic avant tout traitement) ;
- 404 : lot inconnu, ou alerte absente de ce lot ;
- 503 : LLM indisponible ou non configuré. Django affiche alors un message et la
        plateforme continue de fonctionner sans l'IA.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.client_llm import ClientLLM, ErreurLLM
from app.api.dependances import obtenir_client_llm, obtenir_source
from app.schemas import AnalyseRequest, AnalyseResponse
from app.services.source_donnees import LotIntrouvable, SourceDonnees
from app.workflows.analyse_alerte import AlerteIntrouvable, analyser_alerte

journal = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["analyse IA"])


def _erreur(statut: int, code: str, message: str) -> HTTPException:
    # Un « code » stable que Django peut tester, et un message lisible par l'utilisateur.
    return HTTPException(status_code=statut, detail={"code": code, "message": message})


# `def` (et non `async def`) : l'appel au LLM est bloquant ; FastAPI exécute alors la
# fonction dans un thread séparé, et le service continue de répondre aux autres requêtes.
@router.post("/analyze", response_model=AnalyseResponse)
def analyser(
    requete: AnalyseRequest,
    source: SourceDonnees = Depends(obtenir_source),
    client: ClientLLM = Depends(obtenir_client_llm),
) -> AnalyseResponse:
    try:
        return analyser_alerte(requete, source=source, client=client)
    except LotIntrouvable:
        raise _erreur(
            status.HTTP_404_NOT_FOUND, "LOT_INTROUVABLE", f"Le lot {requete.lot_id} est introuvable."
        )
    except AlerteIntrouvable:
        raise _erreur(
            status.HTTP_404_NOT_FOUND,
            "ALERTE_INTROUVABLE",
            f"L'alerte {requete.code_alerte} n'existe pas pour le lot {requete.lot_id}.",
        )
    except ErreurLLM as exc:
        journal.warning("Échec du LLM : %s", exc)  # détail dans les journaux, pas dans la réponse
        raise _erreur(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "LLM_INDISPONIBLE",
            "L'analyse IA n'est pas disponible pour le moment. Réessayez plus tard.",
        )
