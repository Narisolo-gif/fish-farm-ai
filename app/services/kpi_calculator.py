def calculate_kpis(data: dict) -> dict:
    initial_population = data["initial_population"]
    current_population = data["current_population"]

    initial_weight = data["initial_weight_g"]
    current_weight = data["current_weight_g"]
    expected_weight = data["expected_weight_g"]

    period_days = data["period_days"]

    survival = (current_population / initial_population) * 100

    weight_gain = current_weight - initial_weight

    gap_to_expected = current_weight - expected_weight

    relative_gap = (gap_to_expected / expected_weight) * 100

    gmq = weight_gain / period_days

    current_biomass_kg = (
        current_population * current_weight
    ) / 1000

    return {
        "initial_population": initial_population,
        "current_population": current_population,
        "survival_pct": survival,
        "initial_weight_g": initial_weight,
        "current_weight_g": current_weight,
        "expected_weight_g": expected_weight,
        "weight_gain_g": weight_gain,
        "gap_to_expected_g": gap_to_expected,
        "relative_gap_pct": relative_gap,
        "gmq_g_per_day": gmq,
        "current_biomass_kg": current_biomass_kg,
    }