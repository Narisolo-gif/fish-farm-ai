"""Données de suivi d'un lot, telles que renvoyées par l'API Django.

Route source : GET /api/v1/grossissement/lots-grossissement/{id}/suivi/

Ces schémas ne déclarent QUE les champs utiles au service IA. Pydantic ignore les
autres (ex. "series", la liste brute de toutes les pesées) : c'est la règle du manuel
« seuls des indicateurs agrégés quittent la plateforme ».

Les valeurs sont calculées par Django (source de vérité) : ici on les lit et on vérifie
leur forme, on ne les recalcule jamais.
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class SchemaDjango(BaseModel):
    """Base commune : les champs envoyés par Django mais non déclarés sont ignorés."""

    model_config = ConfigDict(extra="ignore")


class Lot(SchemaDjango):
    id: int
    code: str
    espece: str
    reference_bassin: str
    statut: str
    date_entree: date  # Django envoie "2026-09-01" ; Pydantic le convertit en date.
    jour_de_cycle: int
    effectif_initial: int
    poids_moyen_initial: Optional[float] = None
    effectif_vivant_actuel: int


class DernieresValeurs(SchemaDjango):
    """Indicateurs calculés par Django lors de la dernière pesée validée."""

    date_pesee: date
    jour_de_cycle: int
    effectif_vivant: Optional[int] = None
    poids_moyen: float
    biomasse_kg: Optional[float] = None
    gmq_periode: Optional[float] = None  # gain moyen quotidien (g/j) depuis la pesée précédente
    gmq_cumule: Optional[float] = None  # gain moyen quotidien depuis la mise en bassin
    ic_periode: Optional[float] = None  # indice de conversion alimentaire (ICA)
    ic_cumule: Optional[float] = None
    provende_periode_kg: Optional[float] = None


class Seuil(SchemaDjango):
    poids_vente_g: Optional[float] = None
    atteint: bool
    fin_cycle_possible: bool
    date_premiere_pesee_au_seuil: Optional[date] = None


class Alerte(BaseModel):
    """Alerte à seuil produite par Django.

    `extra="allow"` : chaque type d'alerte a ses propres valeurs (ex. `jours_de_retard`
    pour PESEE_EN_RETARD, `seuil_g` pour POIDS_VENTE_ATTEINT). On les garde toutes,
    accessibles via `alerte.model_extra`, car elles servent de faits au LLM.
    """

    model_config = ConfigDict(extra="allow")

    code: str
    # Literal = liste fermée de valeurs autorisées (niveaux utilisés par Django).
    niveau: Literal["info", "attention"]
    message: str


class ParametresEnvironnementaux(SchemaDjango):
    """Dernière mesure de qualité de l'eau du bassin (None si non mesuré)."""

    date_heure_prelevement: datetime
    temperature_eau: Optional[float] = None
    temperature_air: Optional[float] = None
    oxygene: Optional[float] = None  # mg/L
    ph: Optional[float] = None
    nitrite: Optional[float] = None
    nitrate: Optional[float] = None
    ammoniac: Optional[float] = None


class SuiviLot(SchemaDjango):
    """Réponse complète de la route de suivi, réduite à ce dont l'IA a besoin."""

    lot: Lot
    nombre_pesees: int
    dernieres_valeurs: Optional[DernieresValeurs] = None  # None si aucune pesée
    seuil: Seuil
    alertes: list[Alerte]
    parametres_environnementaux: Optional[ParametresEnvironnementaux] = None
