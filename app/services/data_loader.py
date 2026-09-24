from app.mock_data import LOT006_DATA


def load_data(lot_id: str) -> dict:
    if lot_id != LOT006_DATA["lot_id"]:
        raise ValueError(f"Lot not found: {lot_id}")

    return LOT006_DATA.copy()