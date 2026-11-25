"""Contrat commun à toutes les sources de données du service IA.

Le workflow (tâche 1.4) ne dépendra QUE de ce contrat, jamais d'une source précise :
- aujourd'hui : SourceSimulee (données simulées, app/services/source_simulee.py) ;
- étape 3     : un client HTTP vers l'API Django.
Changer de source ne demandera donc aucune modification du workflow.
"""

from abc import ABC, abstractmethod

from app.schemas import SuiviLot


class LotIntrouvable(Exception):
    """Le lot demandé n'existe pas dans la source de données."""

    def __init__(self, lot_id: int):
        self.lot_id = lot_id
        super().__init__(f"Lot introuvable : {lot_id}")


class SourceDonnees(ABC):
    """Interface : toute source DOIT fournir le suivi d'un lot au format Django.

    ABC (Abstract Base Class) : on ne peut pas instancier SourceDonnees directement,
    et une sous-classe qui oublie `recuperer_suivi` provoque une erreur dès sa création.
    """

    @abstractmethod
    def recuperer_suivi(self, lot_id: int) -> SuiviLot:
        """Renvoie le suivi validé du lot, ou lève LotIntrouvable."""
