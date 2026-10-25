"""
Lifecycle & State Transition Engine for Engineering Quality Lab (EQL).
Encapsulates automotive quality state machines:
- DVP&R test execution and status progression
- Engineering Issue 8D discipline and Root Cause verification
- Engineering Change (CMII Gate) approval and revision synchronization
"""

import json
from typing import Optional, Tuple, List
from app.core.exceptions import BusinessRuleViolationError


class LifecycleEngine:
    @staticmethod
    def validate_dvpr_test_execution(dvpr_status: str, measurement_data: Optional[str] = None) -> None:
        """Enforce validation rules before executing a test on a DVP&R plan."""
        if dvpr_status == "Blocked":
            raise BusinessRuleViolationError("Cannot execute test runs against a Blocked DVP&R plan.")
        if measurement_data:
            try:
                json.loads(measurement_data)
            except Exception:
                raise BusinessRuleViolationError("measurement_data must be valid JSON telemetry.")

    @staticmethod
    def compute_dvpr_status_transition(current_status: str, test_result: str) -> str:
        """Compute the resulting status of a DVP&R plan following a test execution."""
        status = "In Progress" if current_status == "Planned" else current_status
        if test_result == "Fail":
            return "Failed"
        if test_result == "Pass" and status == "In Progress":
            return "Passed"
        return status

    @staticmethod
    def validate_root_cause_creation(issue_status: str) -> None:
        """Validate whether a root cause analysis can be initiated on an issue."""
        if issue_status == "Closed":
            raise BusinessRuleViolationError(
                "Cannot perform 5-Why root cause analysis on an already Closed issue. Issue must be reopened first."
            )

    @staticmethod
    def compute_issue_status_on_root_cause(verification_result: str, current_issue_status: str) -> str:
        """Compute issue 8D status when root cause verification outcome is determined."""
        if verification_result == "Confirmed" and current_issue_status in ("New", "Investigating", "Containment"):
            return "RootCauseVerified"
        return current_issue_status

    @staticmethod
    def compute_issue_status_on_root_cause_deletion(current_issue_status: str) -> str:
        """Compute issue rollback status when root cause analysis is removed."""
        if current_issue_status == "RootCauseVerified":
            return "Investigating"
        return current_issue_status

    @staticmethod
    def validate_change_creation(pre_rev: Optional[str], post_rev: Optional[str], approval_status: str) -> None:
        """Enforce CMII gate rules upon ECR creation."""
        if pre_rev and post_rev and pre_rev == post_rev:
            raise BusinessRuleViolationError("post_change_rev must differ from pre_change_rev.")
        if approval_status == "Implemented":
            raise BusinessRuleViolationError("Cannot implement an unapproved engineering change. Must be Approved first.")

    @staticmethod
    def validate_change_transition(
        current_status: str,
        new_status: Optional[str],
        pre_rev: Optional[str],
        post_rev: Optional[str]
    ) -> None:
        """Enforce CMII gate rules upon ECR status and revision updates."""
        if new_status == "Implemented" and current_status != "Approved":
            raise BusinessRuleViolationError("Cannot implement an unapproved engineering change. Must be Approved first.")
        if pre_rev and post_rev and pre_rev == post_rev:
            raise BusinessRuleViolationError("post_change_rev must differ from pre_change_rev.")
