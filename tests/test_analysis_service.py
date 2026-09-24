from app.services.analysis_service import analyze_lot


def test_analyze_lot():
    result = analyze_lot("LOT006")

    assert result["lot_id"] == "LOT006"

    assert result["kpis"]["survival_pct"] == 87.0
    assert result["kpis"]["weight_gain_g"] == 18
    assert result["kpis"]["gap_to_expected_g"] == -14
    assert result["kpis"]["gmq_g_per_day"] == 0.6