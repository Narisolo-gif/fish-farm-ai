from app.mock_data import LOT006_DATA
from app.services.kpi_calculator import calculate_kpis


def test_calculate_kpis():
    kpis = calculate_kpis(LOT006_DATA)

    assert kpis["initial_population"] == 10000
    assert kpis["current_population"] == 8700

    assert kpis["survival_pct"] == 87.0

    assert kpis["initial_weight_g"] == 20
    assert kpis["current_weight_g"] == 38
    assert kpis["expected_weight_g"] == 52

    assert kpis["weight_gain_g"] == 18
    assert kpis["gap_to_expected_g"] == -14

    assert round(kpis["relative_gap_pct"], 2) == -26.92
    assert kpis["gmq_g_per_day"] == 0.6

    assert kpis["current_biomass_kg"] == 330.6