import os
import json
import pytest
from app.services.fmea_engine import calculate_rpn, calculate_action_priority


def test_aiag_vda_1000_combinations_match_independent_authoritative_ground_truth():
    """
    INDEPENDENT STANDARD CONFORMANCE VERIFICATION:
    Loads the official AIAG & VDA 2019 Table DFMEA AP (Table B) ground-truth table
    from docs/standards/AIAG_VDA_2019_DFMEA_TABLE_B.json and compares every single cell
    (all 1,000 combinations of S: 1..10, O: 1..10, D: 1..10).

    This ensures non-circular, third-party verifiable conformance against the published handbook.
    """
    # Locate independent standard file
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    standard_file = os.path.join(base_dir, "docs", "standards", "AIAG_VDA_2019_DFMEA_TABLE_B.json")
    assert os.path.exists(standard_file), f"Independent authoritative standard table not found at {standard_file}"

    with open(standard_file, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    lookup = ground_truth["lookup_cells"]
    assert len(lookup) == 1000, "Ground truth table must contain exactly 1,000 cells."
    assert ground_truth["distribution"]["High"] == 252
    assert ground_truth["distribution"]["Medium"] == 234
    assert ground_truth["distribution"]["Low"] == 514

    mismatches = []
    for s in range(1, 11):
        for o in range(1, 11):
            for d in range(1, 11):
                key = f"{s},{o},{d}"
                expected_ap = lookup[key]
                actual_ap = calculate_action_priority(s, o, d)
                if actual_ap != expected_ap:
                    mismatches.append(f"Cell S={s}, O={o}, D={d}: expected={expected_ap}, got={actual_ap}")

    assert len(mismatches) == 0, f"Found {len(mismatches)} mismatches against AIAG & VDA 2019 Table B:\n" + "\n".join(mismatches[:10])


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
    # Canonical cell count matching AIAG & VDA FMEA 1st Edition Table B
    assert high_count == 252
    assert medium_count == 234
    assert low_count == 514

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

    # Out of range inputs for calculate_action_priority
    for oob in [0, 11, -1, 100]:
        with pytest.raises(ValueError, match="must be integers in range"):
            calculate_action_priority(oob, 5, 5)
        with pytest.raises(ValueError, match="must be integers in range"):
            calculate_action_priority(5, oob, 5)
        with pytest.raises(ValueError, match="must be integers in range"):
            calculate_action_priority(5, 5, oob)

    # Out of range inputs for calculate_rpn
    for invalid_val in [0, 11, -5, 100]:
        with pytest.raises(ValueError, match="must be between 1 and 10"):
            calculate_rpn(invalid_val, 5, 5)
        with pytest.raises(ValueError, match="must be between 1 and 10"):
            calculate_rpn(5, invalid_val, 5)
        with pytest.raises(ValueError, match="must be between 1 and 10"):
            calculate_rpn(5, 5, invalid_val)

    # Strict type errors for all parameters with exact exception message check (kills mutmut_5)
    # Includes booleans (True, False) because in Python issubclass(bool, int) is True, which must be rejected
    for bad in ["5", 5.5, None, [5], {"val": 5}, True, False]:
        with pytest.raises(TypeError) as exc_info:
            calculate_action_priority(bad, 5, 5)  # type: ignore
        assert str(exc_info.value) == "Severity, Occurrence, and Detection must be integers."

        with pytest.raises(TypeError) as exc_info:
            calculate_action_priority(5, bad, 5)  # type: ignore
        assert str(exc_info.value) == "Severity, Occurrence, and Detection must be integers."

        with pytest.raises(TypeError) as exc_info:
            calculate_action_priority(5, 5, bad)  # type: ignore
        assert str(exc_info.value) == "Severity, Occurrence, and Detection must be integers."

        with pytest.raises(TypeError) as exc_info:
            calculate_rpn(bad, 5, 5)  # type: ignore
        assert str(exc_info.value) == "Severity, Occurrence, and Detection must be integers."

    # ================= MUTATION KILLERS: EXACT AP BOUNDARY CELLS =================
    # Kills mutmut_60, mutmut_61 in S in (9,10); O in (2,3); D boundary >= 5
    assert calculate_action_priority(9, 2, 5) == "Medium"
    assert calculate_action_priority(10, 3, 5) == "Medium"
    assert calculate_action_priority(9, 2, 4) == "Low"
    assert calculate_action_priority(10, 3, 4) == "Low"

    # Kills mutmut in S in 7,8; O in 6,7; D boundary >= 5
    assert calculate_action_priority(7, 6, 5) == "High"
    assert calculate_action_priority(8, 7, 5) == "High"
    assert calculate_action_priority(7, 6, 4) == "Medium"
    assert calculate_action_priority(8, 7, 4) == "Medium"

    # Kills mutmut_100, mutmut_101 (S in 7,8; O in 4,5; D boundary >= 2)
    assert calculate_action_priority(7, 4, 2) == "Medium"
    assert calculate_action_priority(8, 5, 2) == "Medium"
    assert calculate_action_priority(7, 4, 1) == "Low"
    assert calculate_action_priority(8, 5, 1) == "Low"

    # Kills mutmut_130, mutmut_131 (S in 4,5,6; O in 8,9,10; D boundary >= 7)
    assert calculate_action_priority(4, 8, 7) == "High"
    assert calculate_action_priority(5, 9, 7) == "High"
    assert calculate_action_priority(6, 10, 7) == "High"
    assert calculate_action_priority(4, 8, 6) == "Medium"
    assert calculate_action_priority(5, 9, 6) == "Medium"
    assert calculate_action_priority(6, 10, 6) == "Medium"

    # Kills mutmut_141, mutmut_142 (S in 4,5,6; O in 6,7; D boundary >= 5)
    assert calculate_action_priority(4, 6, 5) == "Medium"
    assert calculate_action_priority(5, 7, 5) == "Medium"
    assert calculate_action_priority(6, 6, 5) == "Medium"
    assert calculate_action_priority(4, 6, 4) == "Low"
    assert calculate_action_priority(5, 7, 4) == "Low"
    assert calculate_action_priority(6, 6, 4) == "Low"

    # Kills mutmut_150, mutmut_152, mutmut_153 (S in 4,5,6; O in 4,5; D boundary >= 7)
    assert calculate_action_priority(4, 4, 7) == "Medium"
    assert calculate_action_priority(5, 4, 7) == "Medium"
    assert calculate_action_priority(6, 5, 7) == "Medium"
    assert calculate_action_priority(4, 4, 6) == "Low"
    assert calculate_action_priority(5, 4, 6) == "Low"
    assert calculate_action_priority(6, 5, 6) == "Low"

    # Kills mutmut_164, mutmut_171, mutmut_172 (S in 2,3; O in 8,9,10; D boundary >= 7)
    assert calculate_action_priority(2, 8, 7) == "Medium"
    assert calculate_action_priority(3, 8, 7) == "Medium"
    assert calculate_action_priority(2, 9, 7) == "Medium"
    assert calculate_action_priority(3, 10, 7) == "Medium"
    assert calculate_action_priority(2, 8, 6) == "Low"
    assert calculate_action_priority(3, 8, 6) == "Low"
