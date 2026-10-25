import pytest
from app.services.fmea_engine import calculate_rpn, calculate_action_priority

def test_dfmea_all_1000_combinations_return_valid_ap():
    """Verify that every single one of the 1,000 combinations returns valid AP."""
    valid_aps = {"High", "Medium", "Low"}
    count = 0
    high_count = 0
    medium_count = 0
    low_count = 0

    for s in range(1, 11):
        for o in range(1, 11):
            for d in range(1, 11):
                ap = calculate_action_priority(s, o, d)
                assert ap in valid_aps, f"Invalid AP {ap} for S={s}, O={o}, D={d}"
                rpn = calculate_rpn(s, o, d)
                assert 1 <= rpn <= 1000
                count += 1
                if ap == "High":
                    high_count += 1
                elif ap == "Medium":
                    medium_count += 1
                else:
                    low_count += 1

    assert count == 1000
    print(f"\n[AIAG-VDA 2019 AP Distribution out of 1000]: High={high_count}, Medium={medium_count}, Low={low_count}")
    # High must be substantial (critical safety items), Low must be largest
    assert high_count > 100
    assert medium_count > 100
    assert low_count > 400

def test_dfmea_monotonic_risk_properties():
    """Verify monotonicity: higher severity, occurrence, or detection never decreases action priority."""
    ap_weights = {"Low": 1, "Medium": 2, "High": 3}

    # 1. Monotonic in Severity
    for o in range(1, 11):
        for d in range(1, 11):
            prev_weight = 0
            for s in range(1, 11):
                weight = ap_weights[calculate_action_priority(s, o, d)]
                assert weight >= prev_weight, f"Monotonicity violation on S for S={s}, O={o}, D={d}"
                prev_weight = weight

    # 2. Monotonic in Occurrence
    for s in range(1, 11):
        for d in range(1, 11):
            prev_weight = 0
            for o in range(1, 11):
                weight = ap_weights[calculate_action_priority(s, o, d)]
                assert weight >= prev_weight, f"Monotonicity violation on O for S={s}, O={o}, D={d}"
                prev_weight = weight

    # 3. Monotonic in Detection
    for s in range(1, 11):
        for o in range(1, 11):
            prev_weight = 0
            for d in range(1, 11):
                weight = ap_weights[calculate_action_priority(s, o, d)]
                assert weight >= prev_weight, f"Monotonicity violation on D for S={s}, O={o}, D={d}"
                prev_weight = weight

def test_dfmea_boundary_and_illegal_inputs():
    """Test boundary values and illegal inputs."""
    # S=1 -> always Low
    for o in range(1, 11):
        for d in range(1, 11):
            assert calculate_action_priority(1, o, d) == "Low"

    # Extreme safety S=10, O=10, D=10 -> High
    assert calculate_action_priority(10, 10, 10) == "High"
    # S=10, O=1, D=10 -> Low
    assert calculate_action_priority(10, 1, 10) == "Low"

    # S=7, O=4, D=7 -> High (fixed in WP4)
    assert calculate_action_priority(7, 4, 7) == "High"
    # S=7, O=2, D=7 -> Medium (fixed in WP4)
    assert calculate_action_priority(7, 2, 7) == "Medium"

    # Out of range inputs
    with pytest.raises(ValueError):
        calculate_action_priority(0, 5, 5)
    with pytest.raises(ValueError):
        calculate_action_priority(11, 5, 5)
    with pytest.raises(ValueError):
        calculate_action_priority(5, 0, 5)
    with pytest.raises(ValueError):
        calculate_action_priority(5, 5, 12)
    with pytest.raises(ValueError):
        calculate_rpn(-1, 5, 5)

    # Type errors
    with pytest.raises(TypeError):
        calculate_action_priority("10", 5, 5) # type: ignore
