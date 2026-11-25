"""Test avec le VRAI modèle configuré dans .env (LLM_MODEL), lancé seulement à la demande (réseau, quota, coût).

    docker compose run --rm -e TEST_LLM_REEL=1 ai-service python -m pytest tests/test_client_llm_reel.py -v -s

Offre gratuite de Gemini : Google peut réutiliser les données envoyées.
On n'envoie donc ici que des données SIMULÉES (règle du manuel).
"""

import os

import pytest

from app.ai.fabrique import creer_client_llm
from app.schemas import ReponseLLM

pytestmark = pytest.mark.skipif(
    os.getenv("TEST_LLM_REEL") != "1",
    reason="Appel réel au LLM : définir TEST_LLM_REEL=1 pour le lancer.",
)


def test_le_modele_repond_au_format_attendu():
    client = creer_client_llm()

    reponse = client.generer(
        consignes=(
            "Tu es un assistant d'aide à la décision en pisciculture. "
            "Réponds en français, en t'appuyant uniquement sur les données fournies."
        ),
        contexte=(
            "Alerte PESEE_EN_RETARD : la pesée prévue le 2026-10-27 n'a pas été saisie "
            "(4 jours de retard). Lot LOT002, carpe, jour 60 du cycle."
        ),
    )

    print("\n", reponse.model_dump_json(indent=2))
    assert isinstance(reponse, ReponseLLM)
