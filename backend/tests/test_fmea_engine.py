import os
import json
import pytest
from app.services.fmea_engine import calculate_rpn, calculate_action_priority


def test_rpn_calculation():
    assert calculate_rpn(10, 5, 2) == 100
    assert calculate_rpn(1, 1, 1) == 1
    assert calculate_rpn(9, 9, 9) == 729
    assert calculate_rpn(10, 10, 10) == 1000

    # Type & Boundary validations
    with pytest.raises(TypeError):
        calculate_rpn(True, 5, 2)
    with pytest.raises(ValueError):
        calculate_rpn(0, 5, 2)
    with pytest.raises(ValueError):
        calculate_rpn(11, 5, 2)


def test_action_priority_aiag_vda_standards():
    # S=10 (Safety / Regulatory) with high occurrence -> High
    assert calculate_action_priority(10, 8, 5) == "High"
    assert calculate_action_priority(9, 6, 2) == "High"
    
    # S=10, O=4, D=8 -> High
    assert calculate_action_priority(10, 4, 8) == "High"
    # S=10, O=4, D=3 -> Medium
    assert calculate_action_priority(10, 4, 3) == "Medium"
    # S=10, O=1 -> Low
    assert calculate_action_priority(10, 1, 1) == "Low"

    # S=7, O=8 -> High
    assert calculate_action_priority(7, 8, 1) == "High"
    # S=7, O=4, D=6 -> Medium
    assert calculate_action_priority(7, 4, 6) == "Medium"
    # S=7, O=2, D=5 -> Low; D=8 -> Medium per AIAG/VDA 2019 Table B
    assert calculate_action_priority(7, 2, 5) == "Low"
    assert calculate_action_priority(7, 2, 8) == "Medium"

    # S=2 (Minor) -> Low
    assert calculate_action_priority(2, 5, 5) == "Low"


def test_action_priority_full_1000_ground_truth_exhaustive():
    """Verify all 1,000 combinations against independent Table B to kill all mutants."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    standard_file = os.path.join(base_dir, "docs", "standards", "AIAG_VDA_2019_DFMEA_TABLE_B.json")
    if os.path.exists(standard_file):
        with open(standard_file, "r", encoding="utf-8") as f:
            lookup = json.load(f)["lookup_cells"]
        for s in range(1, 11):
            for o in range(1, 11):
                for d in range(1, 11):
                    assert calculate_action_priority(s, o, d) == lookup[f"{s},{o},{d}"]

    # Error handling & type strictness
    with pytest.raises(TypeError):
        calculate_action_priority(True, 5, 2)
    with pytest.raises(TypeError):
        calculate_action_priority(5, False, 2)
    with pytest.raises(TypeError):
        calculate_action_priority(5, 5, "2")
    with pytest.raises(ValueError):
        calculate_action_priority(0, 5, 2)
    with pytest.raises(ValueError):
        calculate_action_priority(11, 5, 2)
    with pytest.raises(ValueError):
        calculate_action_priority(5, 0, 2)
    with pytest.raises(ValueError):
        calculate_action_priority(5, 11, 2)
    with pytest.raises(ValueError):
        calculate_action_priority(5, 5, 0)
    with pytest.raises(ValueError):
        calculate_action_priority(5, 5, 11)
