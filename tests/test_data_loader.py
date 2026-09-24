from app.services.data_loader import load_data
import pytest

def test_load_lot006():
    data = load_data("LOT006")

    assert data["lot_id"] == "LOT006"
    assert data["initial_population"] == 10000
    assert data["current_population"] == 8700
    assert data["current_weight_g"] == 38
    
def test_load_unknown_lot():
    with pytest.raises(ValueError, match="Lot not found: LOT999"):
        load_data("LOT999")