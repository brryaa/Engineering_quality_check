"""
Adversarial Unit Tests for Lifecycle & State Transition Engine
Engineering Quality Lab (EQL)

Targeted testing with exact string assertions to achieve 100% mutation kill rate:
- DVP&R test execution and status computation
- Root Cause analysis creation, confirmation, and deletion status transitions
- Engineering Change (CMII Gate) creation, revision validation, and status transitions
"""

import pytest
from app.core.exceptions import BusinessRuleViolationError
from app.services.lifecycle_engine import LifecycleEngine


# ==============================================================================
# DVP&R Validation and Transition Tests
# ==============================================================================

def test_validate_dvpr_blocked_raises():
    with pytest.raises(BusinessRuleViolationError) as exc:
        LifecycleEngine.validate_dvpr_test_execution("Blocked", None)
    assert exc.value.detail == "Business rule violation: Cannot execute test runs against a Blocked DVP&R plan."


def test_validate_dvpr_unblocked_succeeds():
    for status in ["Planned", "In Progress", "Passed", "Failed"]:
        LifecycleEngine.validate_dvpr_test_execution(status, None)
        LifecycleEngine.validate_dvpr_test_execution(status, '{"pressure_bar": 2.5}')


def test_validate_dvpr_invalid_json_telemetry():
    with pytest.raises(BusinessRuleViolationError) as exc:
        LifecycleEngine.validate_dvpr_test_execution("In Progress", "NOT_JSON_TELEMETRY")
    assert exc.value.detail == "Business rule violation: measurement_data must be valid JSON telemetry."


def test_compute_dvpr_status_planned_transitions():
    assert LifecycleEngine.compute_dvpr_status_transition("Planned", "Pass") == "Passed"
    assert LifecycleEngine.compute_dvpr_status_transition("Planned", "Fail") == "Failed"
    assert LifecycleEngine.compute_dvpr_status_transition("Planned", "Marginal") == "In Progress"


def test_compute_dvpr_status_fail_transitions():
    assert LifecycleEngine.compute_dvpr_status_transition("In Progress", "Fail") == "Failed"
    assert LifecycleEngine.compute_dvpr_status_transition("Passed", "Fail") == "Failed"
    assert LifecycleEngine.compute_dvpr_status_transition("Failed", "Fail") == "Failed"


def test_compute_dvpr_status_pass_transitions():
    assert LifecycleEngine.compute_dvpr_status_transition("In Progress", "Pass") == "Passed"
    assert LifecycleEngine.compute_dvpr_status_transition("Failed", "Pass") == "Failed"
    assert LifecycleEngine.compute_dvpr_status_transition("Passed", "Pass") == "Passed"


def test_compute_dvpr_status_other_results():
    assert LifecycleEngine.compute_dvpr_status_transition("In Progress", "Marginal") == "In Progress"
    assert LifecycleEngine.compute_dvpr_status_transition("Passed", "Marginal") == "Passed"
    assert LifecycleEngine.compute_dvpr_status_transition("Failed", "Marginal") == "Failed"


# ==============================================================================
# Root Cause Analysis Lifecycle Tests
# ==============================================================================

def test_validate_root_cause_creation_closed_issue():
    with pytest.raises(BusinessRuleViolationError) as exc:
        LifecycleEngine.validate_root_cause_creation("Closed")
    assert exc.value.detail == "Business rule violation: Cannot perform 5-Why root cause analysis on an already Closed issue. Issue must be reopened first."


def test_validate_root_cause_creation_open_issue():
    for status in ["New", "Investigating", "Containment", "RootCauseVerified", "ActionImplemented", "ValidationPass"]:
        LifecycleEngine.validate_root_cause_creation(status)


def test_compute_issue_status_confirmed_root_cause():
    for initial in ["New", "Investigating", "Containment"]:
        res = LifecycleEngine.compute_issue_status_on_root_cause("Confirmed", initial)
        assert res == "RootCauseVerified"


def test_compute_issue_status_unconfirmed_or_advanced():
    assert LifecycleEngine.compute_issue_status_on_root_cause("Pending", "Investigating") == "Investigating"
    assert LifecycleEngine.compute_issue_status_on_root_cause("Rejected", "Investigating") == "Investigating"
    assert LifecycleEngine.compute_issue_status_on_root_cause("Confirmed", "ActionImplemented") == "ActionImplemented"
    assert LifecycleEngine.compute_issue_status_on_root_cause("Confirmed", "ValidationPass") == "ValidationPass"


def test_compute_issue_status_root_cause_deletion():
    assert LifecycleEngine.compute_issue_status_on_root_cause_deletion("RootCauseVerified") == "Investigating"
    assert LifecycleEngine.compute_issue_status_on_root_cause_deletion("New") == "New"
    assert LifecycleEngine.compute_issue_status_on_root_cause_deletion("Investigating") == "Investigating"
    assert LifecycleEngine.compute_issue_status_on_root_cause_deletion("ActionImplemented") == "ActionImplemented"


# ==============================================================================
# Engineering Change (CMII Gate) Tests
# ==============================================================================

def test_validate_change_creation_equal_revisions():
    with pytest.raises(BusinessRuleViolationError) as exc:
        LifecycleEngine.validate_change_creation("Rev A.0", "Rev A.0", "Draft")
    assert exc.value.detail == "Business rule violation: post_change_rev must differ from pre_change_rev."


def test_validate_change_creation_directly_implemented():
    with pytest.raises(BusinessRuleViolationError) as exc:
        LifecycleEngine.validate_change_creation("Rev A.0", "Rev B.0", "Implemented")
    assert exc.value.detail == "Business rule violation: Cannot implement an unapproved engineering change. Must be Approved first."


def test_validate_change_creation_valid():
    LifecycleEngine.validate_change_creation("Rev A.0", "Rev B.0", "Draft")
    LifecycleEngine.validate_change_creation("Rev A.0", "Rev B.0", "Review-Eng")
    LifecycleEngine.validate_change_creation(None, "Rev B.0", "Draft")
    LifecycleEngine.validate_change_creation("Rev A.0", None, "Draft")
    LifecycleEngine.validate_change_creation(None, None, "Draft")


def test_validate_change_transition_unapproved_to_implemented():
    for invalid_current in ["Draft", "Review-Eng", "Review-CostTooling", "Rejected"]:
        with pytest.raises(BusinessRuleViolationError) as exc:
            LifecycleEngine.validate_change_transition(invalid_current, "Implemented", "Rev A.0", "Rev B.0")
        assert exc.value.detail == "Business rule violation: Cannot implement an unapproved engineering change. Must be Approved first."


def test_validate_change_transition_approved_to_implemented():
    LifecycleEngine.validate_change_transition("Approved", "Implemented", "Rev A.0", "Rev B.0")


def test_validate_change_transition_equal_revisions():
    with pytest.raises(BusinessRuleViolationError) as exc:
        LifecycleEngine.validate_change_transition("Approved", "Approved", "Rev C.0", "Rev C.0")
    assert exc.value.detail == "Business rule violation: post_change_rev must differ from pre_change_rev."


def test_validate_change_transition_valid_transitions():
    LifecycleEngine.validate_change_transition("Draft", "Review-Eng", "Rev A.0", "Rev B.0")
    LifecycleEngine.validate_change_transition("Review-Eng", "Approved", "Rev A.0", "Rev B.0")
    LifecycleEngine.validate_change_transition("Draft", "Rejected", "Rev A.0", "Rev B.0")
    LifecycleEngine.validate_change_transition("Draft", None, "Rev A.0", "Rev B.0")
    LifecycleEngine.validate_change_transition("Draft", "Draft", None, "Rev B.0")
    LifecycleEngine.validate_change_transition("Draft", "Draft", "Rev A.0", None)
    LifecycleEngine.validate_change_transition("Draft", "Draft", None, None)
