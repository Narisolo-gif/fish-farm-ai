"""Construction du contexte envoyé au LLM (le message « human »).

Principe : on choisit ce que le LLM voit. Seuls les éléments utiles à l'explication
de l'alerte sont transmis, sous forme de JSON lisible ; rien n'est recalculé.
"""

import json

from app.schemas import Alerte, SuiviLot

# Champs de développement qui ne concernent pas le LLM.
CHAMPS_TECHNIQUES = {"simulee"}


def _alerte_complete(alerte: Alerte) -> dict:
    """Code, niveau, message + valeurs propres à l'alerte (jours de retard, seuil…)."""
    donnees = alerte.model_dump(mode="json")
    return {cle: valeur for cle, valeur in donnees.items() if cle not in CHAMPS_TECHNIQUES}


def construire_contexte(suivi: SuiviLot, alerte: Alerte) -> str:
    contexte = {
        "alerte_a_expliquer": _alerte_complete(alerte),
        # Les autres alertes aident à formuler des hypothèses (ex. mortalité + oxygène bas).
        "autres_alertes_du_lot": [
            {"code": autre.code, "message": autre.message}
            for autre in suivi.alertes
            if autre.code != alerte.code
        ],
        # mode="json" : dates converties en texte ISO ("2026-10-31").
        "lot": suivi.lot.model_dump(mode="json", exclude={"id"}),
        "nombre_pesees": suivi.nombre_pesees,
        "dernieres_valeurs": (
            suivi.dernieres_valeurs.model_dump(mode="json") if suivi.dernieres_valeurs else None
        ),
        "seuil_poids_vente": suivi.seuil.model_dump(mode="json"),
        "parametres_environnementaux": (
            suivi.parametres_environnementaux.model_dump(mode="json")
            if suivi.parametres_environnementaux
            else None
        ),
    }
    # ensure_ascii=False garde les accents lisibles ; indent aide le modèle à lire.
    return json.dumps(contexte, ensure_ascii=False, indent=2)
