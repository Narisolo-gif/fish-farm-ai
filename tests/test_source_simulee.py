"""Tests de la source de données simulée (tâche 1.2).

La source simulée remplace provisoirement l'API Django : elle renvoie des données
de suivi AU FORMAT DJANGO, avec les alertes déjà présentes. Le service IA les lit
sans rien recalculer.
"""

import pytest

from app.mock_data import SUIVIS_SIMULES
from app.schemas import SuiviLot
from app.services.source_donnees import LotIntrouvable, SourceDonnees
from app.services.source_simulee import SourceSimulee


def codes_alertes(suivi):
    return {alerte.code for alerte in suivi.alertes}


def test_source_simulee_respecte_le_contrat_commun():
    # Le workflow ne connaîtra que SourceDonnees : demain, le client Django
    # prendra la place de SourceSimulee sans rien changer d'autre.
    assert isinstance(SourceSimulee(), SourceDonnees)


@pytest.mark.parametrize("lot_id", sorted(SUIVIS_SIMULES))
def test_chaque_scenario_est_au_format_django(lot_id):
    suivi = SourceSimulee().recuperer_suivi(lot_id)

    assert isinstance(suivi, SuiviLot)
    assert suivi.lot.id == lot_id


def test_lot_inconnu_leve_une_erreur_claire():
    with pytest.raises(LotIntrouvable, match="999"):
        SourceSimulee().recuperer_suivi(999)


@pytest.mark.parametrize(
    ("lot_id", "alertes_attendues"),
    [
        (1, set()),  # situation normale
        (2, {"PESEE_EN_RETARD"}),
        (3, {"POIDS_VENTE_ATTEINT"}),
        (6, {"MORTALITE_ELEVEE", "OXYGENE_BAS", "TEMPERATURE_ELEVEE"}),
        (9, {"PESEE_EN_RETARD"}),  # données incomplètes
    ],
)
def test_scenarios_et_leurs_alertes(lot_id, alertes_attendues):
    suivi = SourceSimulee().recuperer_suivi(lot_id)

    assert codes_alertes(suivi) == alertes_attendues


def test_alertes_simulees_sont_signalees_comme_telles():
    suivi = SourceSimulee().recuperer_suivi(6)

    # Ces alertes n'existent pas encore dans Django (étape 2) : on le marque.
    for alerte in suivi.alertes:
        assert alerte.model_extra["simulee"] is True


def test_alertes_existantes_dans_django_ne_sont_pas_marquees_simulees():
    suivi = SourceSimulee().recuperer_suivi(2)

    assert "simulee" not in suivi.alertes[0].model_extra


def test_alertes_simulees_coherentes_avec_les_mesures():
    # Une alerte doit reposer sur une valeur réellement présente dans les données.
    suivi = SourceSimulee().recuperer_suivi(6)
    alertes = {alerte.code: alerte.model_extra for alerte in suivi.alertes}
    mesure = suivi.parametres_environnementaux

    assert alertes["OXYGENE_BAS"]["valeur_mg_l"] == mesure.oxygene
    assert alertes["OXYGENE_BAS"]["valeur_mg_l"] < alertes["OXYGENE_BAS"]["seuil_mg_l"]
    assert alertes["TEMPERATURE_ELEVEE"]["valeur_c"] == mesure.temperature_eau
    assert alertes["TEMPERATURE_ELEVEE"]["valeur_c"] > alertes["TEMPERATURE_ELEVEE"]["seuil_c"]


def test_lot_aux_donnees_incompletes():
    suivi = SourceSimulee().recuperer_suivi(9)

    assert suivi.nombre_pesees == 0
    assert suivi.dernieres_valeurs is None
    assert suivi.parametres_environnementaux is None


def test_modifier_un_resultat_ne_modifie_pas_les_donnees_simulees():
    source = SourceSimulee()
    premier = source.recuperer_suivi(6)
    premier.alertes.clear()

    assert len(source.recuperer_suivi(6).alertes) == 3
