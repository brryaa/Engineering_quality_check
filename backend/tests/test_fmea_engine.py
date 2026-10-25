from app.services.fmea_engine import calculate_rpn, calculate_action_priority

def test_rpn_calculation():
    assert calculate_rpn(10, 5, 2) == 100
    assert calculate_rpn(1, 1, 1) == 1
    assert calculate_rpn(9, 9, 9) == 729

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
