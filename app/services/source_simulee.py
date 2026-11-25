"""Source de données simulée : imite la route Django `suivi` à partir de app/mock_data.py.

Provisoire : remplacée par le client Django à l'étape 3 (même contrat SourceDonnees).
"""

import copy

from app.mock_data import SUIVIS_SIMULES
from app.schemas import SuiviLot
from app.services.source_donnees import LotIntrouvable, SourceDonnees


class SourceSimulee(SourceDonnees):
    def recuperer_suivi(self, lot_id: int) -> SuiviLot:
        donnees = SUIVIS_SIMULES.get(lot_id)
        if donnees is None:
            raise LotIntrouvable(lot_id)

        # Copie profonde : celui qui modifie le résultat ne peut pas abîmer les
        # données simulées partagées par tout le service (et par les autres tests).
        # model_validate vérifie ensuite que la simulation respecte le format Django,
        # exactement comme on vérifiera la vraie réponse de Django.
        return SuiviLot.model_validate(copy.deepcopy(donnees))
