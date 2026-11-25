"""Données simulées au FORMAT DE LA ROUTE DJANGO `suivi`.

GET /api/v1/grossissement/lots-grossissement/{id}/suivi/?date_reference=2026-10-31

Règles de cette simulation :
- Toutes les valeurs (GMQ, biomasse, ICA, taux de mortalité…) sont écrites « en dur »,
  comme si Django les avait calculées. Le service IA ne recalcule RIEN.
- Les alertes sont déjà présentes dans les données, comme Django les produirait.
- `PESEE_EN_RETARD` et `POIDS_VENTE_ATTEINT` reprennent le format exact de Django
  (apps/grossissement/calculs.py::alertes_suivi).
- `MORTALITE_ELEVEE`, `OXYGENE_BAS` et `TEMPERATURE_ELEVEE` n'existent pas encore dans
  Django : elles portent `"simulee": True`. Leurs seuils (5 %, 3 mg/L, 32 °C) sont
  PROVISOIRES et seront fixés avec l'exploitation à l'étape 2.
- Seuls les champs lus par le service IA sont présents (pas de `series`, `calendrier`…).
"""

SUIVIS_SIMULES = {
    # --- LOT001 : situation normale, aucune alerte ----------------------------------
    1: {
        "lot": {
            "id": 1,
            "code": "LOT001",
            "espece": "TILAPIA",
            "id_bassin": 1,
            "reference_bassin": "B01",
            "statut": "ACTIF",
            "date_entree": "2026-09-01",
            "jour_de_cycle": 60,
            "effectif_initial": 5000,
            "poids_moyen_initial": 15.0,
            "effectif_vivant_actuel": 4900,
            "evacuation_requise": False,
        },
        "nombre_pesees": 4,
        "dernieres_valeurs": {
            "date_pesee": "2026-10-26",
            "jour_de_cycle": 55,
            "effectif_vivant": 4900,
            "poids_moyen": 72.0,
            "biomasse_kg": 352.8,
            "gmq_periode": 1.03,
            "gmq_cumule": 1.04,
            "ic_periode": 1.6,
            "ic_cumule": 1.5,
            "provende_periode_kg": 110.0,
        },
        "seuil": {
            "poids_vente_g": 250.0,
            "atteint": False,
            "fin_cycle_possible": False,
            "date_premiere_pesee_au_seuil": None,
        },
        "alertes": [],
        "parametres_environnementaux": {
            "date_heure_prelevement": "2026-10-31T07:00:00+03:00",
            "temperature_eau": 28.5,
            "temperature_air": 30.0,
            "oxygene": 5.6,
            "ph": 7.4,
            "nitrite": 0.1,
            "nitrate": 5.0,
            "ammoniac": 0.2,
        },
    },
    # --- LOT002 : pesée en retard (alerte Django réelle) ----------------------------
    2: {
        "lot": {
            "id": 2,
            "code": "LOT002",
            "espece": "CARPE",
            "id_bassin": 2,
            "reference_bassin": "B02",
            "statut": "ACTIF",
            "date_entree": "2026-09-01",
            "jour_de_cycle": 60,
            "effectif_initial": 4000,
            "poids_moyen_initial": 18.0,
            "effectif_vivant_actuel": 3880,
            "evacuation_requise": False,
        },
        "nombre_pesees": 3,
        "dernieres_valeurs": {
            "date_pesee": "2026-10-13",
            "jour_de_cycle": 42,
            "effectif_vivant": 3890,
            "poids_moyen": 60.0,
            "biomasse_kg": 233.4,
            "gmq_periode": 1.0,
            "gmq_cumule": 1.0,
            "ic_periode": 1.7,
            "ic_cumule": 1.6,
            "provende_periode_kg": 95.0,
        },
        "seuil": {
            "poids_vente_g": 300.0,
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
                "jours_de_retard": 4,
            }
        ],
        "parametres_environnementaux": {
            "date_heure_prelevement": "2026-10-31T07:00:00+03:00",
            "temperature_eau": 27.0,
            "temperature_air": 29.0,
            "oxygene": 5.2,
            "ph": 7.3,
            "nitrite": None,
            "nitrate": None,
            "ammoniac": None,
        },
    },
    # --- LOT003 : poids de vente atteint (alerte Django réelle) ---------------------
    3: {
        "lot": {
            "id": 3,
            "code": "LOT003",
            "espece": "TILAPIA",
            "id_bassin": 3,
            "reference_bassin": "B03",
            "statut": "ACTIF",
            "date_entree": "2026-06-03",
            "jour_de_cycle": 150,
            "effectif_initial": 3000,
            "poids_moyen_initial": 20.0,
            "effectif_vivant_actuel": 2790,
            "evacuation_requise": False,
        },
        "nombre_pesees": 10,
        "dernieres_valeurs": {
            "date_pesee": "2026-10-28",
            "jour_de_cycle": 147,
            "effectif_vivant": 2790,
            "poids_moyen": 262.0,
            "biomasse_kg": 730.98,
            "gmq_periode": 1.71,
            "gmq_cumule": 1.65,
            "ic_periode": 1.9,
            "ic_cumule": 1.7,
            "provende_periode_kg": 125.0,
        },
        "seuil": {
            "poids_vente_g": 250.0,
            "atteint": True,
            "fin_cycle_possible": True,
            "date_premiere_pesee_au_seuil": "2026-10-28",
        },
        "alertes": [
            {
                "code": "POIDS_VENTE_ATTEINT",
                "niveau": "info",
                "message": (
                    "Le poids moyen a atteint 262 g, au-delà du seuil de 250 g : "
                    "fin de cycle possible."
                ),
                "poids_moyen": 262.0,
                "seuil_g": 250,
                "date_pesee": "2026-10-28",
            }
        ],
        "parametres_environnementaux": {
            "date_heure_prelevement": "2026-10-31T07:00:00+03:00",
            "temperature_eau": 28.0,
            "temperature_air": 30.0,
            "oxygene": 5.0,
            "ph": 7.5,
            "nitrite": None,
            "nitrate": None,
            "ammoniac": None,
        },
    },
    # --- LOT006 : mortalité + oxygène bas + température élevée (alertes SIMULÉES) ----
    6: {
        "lot": {
            "id": 6,
            "code": "LOT006",
            "espece": "TILAPIA",
            "id_bassin": 6,
            "reference_bassin": "B06",
            "statut": "ACTIF",
            "date_entree": "2026-10-01",
            "jour_de_cycle": 30,
            "effectif_initial": 10000,
            "poids_moyen_initial": 20.0,
            "effectif_vivant_actuel": 8700,
            "evacuation_requise": False,
        },
        "nombre_pesees": 1,
        "dernieres_valeurs": {
            "date_pesee": "2026-10-31",
            "jour_de_cycle": 30,
            "effectif_vivant": 8700,
            "poids_moyen": 38.0,
            "biomasse_kg": 330.6,
            "gmq_periode": 0.6,
            "gmq_cumule": 0.6,
            "ic_periode": 3.22,
            "ic_cumule": 3.22,
            "provende_periode_kg": 420.0,
        },
        "seuil": {
            "poids_vente_g": 250.0,
            "atteint": False,
            "fin_cycle_possible": False,
            "date_premiere_pesee_au_seuil": None,
        },
        "alertes": [
            {
                "code": "MORTALITE_ELEVEE",
                "niveau": "attention",
                "message": (
                    "Mortalité cumulée de 13 % depuis la mise en bassin, "
                    "au-delà du seuil de 5 %."
                ),
                "taux_mortalite_pct": 13.0,
                "seuil_pct": 5.0,
                "periode_jours": 30,
                "simulee": True,
            },
            {
                "code": "OXYGENE_BAS",
                "niveau": "attention",
                "message": "Oxygène dissous mesuré à 1,8 mg/L, sous le seuil de 3 mg/L.",
                "valeur_mg_l": 1.8,
                "seuil_mg_l": 3.0,
                "simulee": True,
            },
            {
                "code": "TEMPERATURE_ELEVEE",
                "niveau": "attention",
                "message": "Température de l'eau mesurée à 34 °C, au-dessus du seuil de 32 °C.",
                "valeur_c": 34.0,
                "seuil_c": 32.0,
                "simulee": True,
            },
        ],
        "parametres_environnementaux": {
            "date_heure_prelevement": "2026-10-31T07:00:00+03:00",
            "temperature_eau": 34.0,
            "temperature_air": 33.0,
            "oxygene": 1.8,
            "ph": 7.0,
            "nitrite": None,
            "nitrate": None,
            "ammoniac": None,
        },
    },
    # --- LOT009 : données incomplètes (aucune pesée, aucune mesure d'eau) ------------
    9: {
        "lot": {
            "id": 9,
            "code": "LOT009",
            "espece": "TILAPIA",
            "id_bassin": 9,
            "reference_bassin": "B09",
            "statut": "ACTIF",
            "date_entree": "2026-10-10",
            "jour_de_cycle": 21,
            "effectif_initial": 3000,
            "poids_moyen_initial": None,
            "effectif_vivant_actuel": 3000,
            "evacuation_requise": False,
        },
        "nombre_pesees": 0,
        "dernieres_valeurs": None,
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
                "message": "La pesée prévue le 2026-10-24 n'a pas été saisie.",
                "date_prevue": "2026-10-24",
                "jours_de_retard": 7,
            }
        ],
        "parametres_environnementaux": None,
    },
}
