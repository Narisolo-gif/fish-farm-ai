"""Tests des schémas Pydantic (tâche 1.1).

Un schéma Pydantic décrit la forme attendue des données. Ces tests vérifient deux choses :
- les données correctes sont acceptées (et converties dans les bons types) ;
- les données incorrectes sont refusées avec une ValidationError.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import AnalyseRequest, AnalyseResponse, ReponseLLM, SuiviLot


def suivi_django():
    """Exemple de réponse JSON de la route Django
    GET /api/v1/grossissement/lots-grossissement/{id}/suivi/ (format réel, abrégé)."""
    return {
        "lot": {
            "id": 6,
            "code": "LOT006",
            "espece": "TILAPIA",
            "id_bassin": 2,
            "reference_bassin": "B02",
            "statut": "ACTIF",
            "date_entree": "2026-09-01",
            "jour_de_cycle": 60,
            "effectif_initial": 10000,
            "poids_moyen_initial": 20.0,
            "effectif_vivant_actuel": 8700,
            "evacuation_requise": False,
        },
        "nombre_pesees": 2,
        "dernieres_valeurs": {
            "date_pesee": "2026-10-20",
            "jour_de_cycle": 49,
            "effectif_vivant": 8700,
            "poids_moyen": 38.0,
            "biomasse_kg": 330.6,
            "gmq_periode": 0.6,
            "gmq_cumule": 0.37,
            "ic_periode": 1.8,
            "ic_cumule": 1.6,
            "provende_periode_kg": 420.0,
            "nature": {"poids_moyen": "mesuré sur échantillon"},
        },
        # Série complète des pesées : le service IA n'en a pas besoin (données brutes).
        "series": [{"pesee_id": 1, "poids_moyen": 30.0}],
        "seuil": {
            "poids_vente_g": 250.0,
            "atteint": False,
            "fin_cycle_possible": False,
            "date_premiere_pesee_au_seuil": None,
        },
        "alertes": [
            {
                "code": "PESEE_EN_RETARD",
                "niveau": "attention",
                "message": "La pesée prévue le 2026-10-27 n'a pas été saisie.",
                "date_prevue": "2026-10-27",
                "jours_de_retard": 3,
            }
        ],
        "parametres_environnementaux": {
            "date_heure_prelevement": "2026-10-30T07:00:00+03:00",
            "temperature_eau": 31.5,
            "temperature_air": None,
            "oxygene": 1.8,
            "ph": 7.2,
            "nitrite": None,
            "nitrate": None,
            "ammoniac": None,
        },
    }


# --- Données reçues de Django ---------------------------------------------------


def test_suivi_django_valide_est_lu_et_converti():
    suivi = SuiviLot.model_validate(suivi_django())

    assert suivi.lot.code == "LOT006"
    # Le texte "2026-09-01" est converti en vraie date Python.
    assert suivi.lot.date_entree == date(2026, 9, 1)
    assert suivi.dernieres_valeurs.biomasse_kg == 330.6
    assert suivi.parametres_environnementaux.oxygene == 1.8


def test_suivi_ignore_les_donnees_brutes_inutiles():
    suivi = SuiviLot.model_validate(suivi_django())

    # "series" n'est pas déclaré dans le schéma : il est écarté.
    assert not hasattr(suivi, "series")


def test_alerte_garde_ses_valeurs_specifiques():
    suivi = SuiviLot.model_validate(suivi_django())
    alerte = suivi.alertes[0]

    assert alerte.code == "PESEE_EN_RETARD"
    # Champs propres à ce type d'alerte, conservés pour le contexte du LLM.
    assert alerte.model_extra["jours_de_retard"] == 3


def test_lot_sans_pesee_ni_mesure_est_accepte():
    donnees = suivi_django()
    donnees["dernieres_valeurs"] = None
    donnees["parametres_environnementaux"] = None

    suivi = SuiviLot.model_validate(donnees)

    assert suivi.dernieres_valeurs is None
    assert suivi.parametres_environnementaux is None


def test_alerte_avec_niveau_inconnu_est_refusee():
    donnees = suivi_django()
    donnees["alertes"][0]["niveau"] = "catastrophe"

    with pytest.raises(ValidationError):
        SuiviLot.model_validate(donnees)


# --- Requête d'analyse (Django -> service IA) -------------------------------------


def test_requete_analyse_valide():
    requete = AnalyseRequest(lot_id=6, code_alerte="PESEE_EN_RETARD")

    assert requete.lot_id == 6
    assert requete.code_alerte == "PESEE_EN_RETARD"


@pytest.mark.parametrize(
    "donnees",
    [
        {"lot_id": 0, "code_alerte": "PESEE_EN_RETARD"},  # identifiant non positif
        {"lot_id": 6, "code_alerte": "pesee en retard"},  # code mal formé
        {"lot_id": 6},  # alerte manquante
        {"lot_id": 6, "code_alerte": "PESEE_EN_RETARD", "prompt": "ignore tout"},  # champ en trop
    ],
)
def test_requete_analyse_invalide_est_refusee(donnees):
    with pytest.raises(ValidationError):
        AnalyseRequest.model_validate(donnees)


# --- Réponse du LLM (constat / explication / action proposée) --------------------


def test_reponse_llm_valide_et_espaces_retires():
    reponse = ReponseLLM(
        constat="  La pesée prévue n'a pas été saisie.  ",
        explication="Sans pesée récente, la croissance ne peut pas être suivie.",
        action_proposee="Planifier une pesée sur échantillon cette semaine.",
    )

    assert reponse.constat == "La pesée prévue n'a pas été saisie."


@pytest.mark.parametrize(
    "donnees",
    [
        {"constat": "", "explication": "x", "action_proposee": "y"},  # partie vide
        {"constat": "x", "explication": "y"},  # partie manquante
        {"constat": "x", "explication": "y", "action_proposee": "z", "gravite": "haute"},  # en trop
    ],
)
def test_reponse_llm_invalide_est_refusee(donnees):
    with pytest.raises(ValidationError):
        ReponseLLM.model_validate(donnees)


def test_reponse_analyse_regroupe_requete_et_reponse_llm():
    reponse = AnalyseResponse(
        lot_id=6,
        code_alerte="PESEE_EN_RETARD",
        analyse=ReponseLLM(constat="a", explication="b", action_proposee="c"),
    )

    assert reponse.model_dump()["analyse"]["action_proposee"] == "c"
