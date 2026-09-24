from app.services.data_loader import load_data
from app.services.kpi_calculator import calculate_kpis


def analyze_lot(lot_id: str) -> dict:
    data = load_data(lot_id)
    kpis = calculate_kpis(data)

    return {
        "lot_id": lot_id,
        "kpis": kpis,
    }