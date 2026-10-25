"""
Hypothesis Adversarial Property-Based and Stateful State Machine Tests.
Targets:
1. AIAG & VDA 2019 DFMEA Risk Mathematical Properties & Invariants.
2. RuleBasedStateMachine testing multi-step state transitions for:
   - Engineering Changes (CMII / ISO 26262 Approval Workflow)
   - DVP&R Plans and Test Run Synchronization
   - Issue Lifecycle & 5-Why Root Cause Closed-loop
"""

import json
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant, Bundle

from app.core.database import Base
from tests.conftest import TestingSessionLocal, engine as test_engine
from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun, EngineeringIssue,
    RootCauseAnalysis, EngineeringChange
)
from app.services.fmea_engine import calculate_rpn, calculate_action_priority
from app.services.services import (
    ProgramService, PartService, DFMEAService, DVPRService,
    TestRunService, IssueService, RootCauseService, ChangeService
)
from app.schemas.schemas import (
    ProgramCreate, PartCreate, DFMEACreate, DVPRCreate,
    TestRunCreate, IssueCreate, RootCauseCreate, ChangeCreate,
    ChangeUpdate, DVPRUpdate
)
from app.core.exceptions import BusinessRuleViolationError, EntityNotFoundError

# Prevent pytest from treating imported classes as test cases
TestRun.__test__ = False  # type: ignore
TestRunCreate.__test__ = False  # type: ignore
TestRunService.__test__ = False  # type: ignore


# ==============================================================================
# PART 1: DFMEA PROPERTY-BASED TESTS
# ==============================================================================

AP_WEIGHTS = {"Low": 1, "Medium": 2, "High": 3}


@settings(max_examples=500, deadline=None)
@given(
    s=st.integers(min_value=1, max_value=10),
    o=st.integers(min_value=1, max_value=10),
    d=st.integers(min_value=1, max_value=10)
)
def test_hypothesis_dfmea_valid_output_range(s: int, o: int, d: int):
    """Property 1: Output is always strictly within canonical set {Low, Medium, High}."""
    ap = calculate_action_priority(s, o, d)
    assert ap in ("Low", "Medium", "High")
    rpn = calculate_rpn(s, o, d)
    assert 1 <= rpn <= 1000
    assert rpn == s * o * d


@settings(max_examples=300, deadline=None)
@given(
    s1=st.integers(min_value=1, max_value=10),
    s2=st.integers(min_value=1, max_value=10),
    o1=st.integers(min_value=1, max_value=10),
    o2=st.integers(min_value=1, max_value=10),
    d1=st.integers(min_value=1, max_value=10),
    d2=st.integers(min_value=1, max_value=10),
)
def test_hypothesis_dfmea_monotonicity_property(s1: int, s2: int, o1: int, o2: int, d1: int, d2: int):
    """
    Property 2: Weak Pareto Monotonicity.
    If S1 <= S2 and O1 <= O2 and D1 <= D2, then Risk(S1, O1, D1) <= Risk(S2, O2, D2).
    """
    if s1 <= s2 and o1 <= o2 and d1 <= d2:
        w1 = AP_WEIGHTS[calculate_action_priority(s1, o1, d1)]
        w2 = AP_WEIGHTS[calculate_action_priority(s2, o2, d2)]
        assert w1 <= w2, f"Monotonicity violated: ({s1},{o1},{d1})={w1} > ({s2},{o2},{d2})={w2}"


@settings(max_examples=200, deadline=None)
@given(
    o=st.integers(min_value=6, max_value=10),
    d=st.integers(min_value=1, max_value=10)
)
def test_hypothesis_dfmea_safety_critical_invariance(o: int, d: int):
    """
    Property 3: Safety preservation rule.
    Any S in {9, 10} with high Occurrence (>= 6) MUST ALWAYS evaluate to High AP.
    """
    assert calculate_action_priority(9, o, d) == "High"
    assert calculate_action_priority(10, o, d) == "High"


@settings(max_examples=100, deadline=None)
@given(
    o=st.integers(min_value=1, max_value=10),
    d=st.integers(min_value=1, max_value=10)
)
def test_hypothesis_dfmea_minimal_severity_invariance(o: int, d: int):
    """
    Property 4: Minimal severity invariance.
    For S = 1 (no discernible effect), AP is ALWAYS Low regardless of O and D.
    """
    assert calculate_action_priority(1, o, d) == "Low"


@settings(max_examples=200, deadline=None)
@given(
    s=st.integers().filter(lambda x: x < 1 or x > 10),
    o=st.integers(min_value=1, max_value=10),
    d=st.integers(min_value=1, max_value=10)
)
def test_hypothesis_dfmea_out_of_bounds_rejection(s: int, o: int, d: int):
    """Property 5: Out of bounds severity must raise ValueError."""
    with pytest.raises(ValueError):
        calculate_action_priority(s, o, d)
    with pytest.raises(ValueError):
        calculate_rpn(s, o, d)


# ==============================================================================
# PART 2: STATEFUL STATE MACHINE TESTING (RuleBasedStateMachine)
# ==============================================================================

class EQLBusinessStateMachine(RuleBasedStateMachine):
    """
    State machine exploring adversarial interleaved operations across:
    - Programs & Parts
    - Engineering Changes (Draft -> Reviewed -> Approved -> Implemented)
    - DVP&R Plans & Test Runs (Planned -> In Progress -> Passed/Failed/Blocked)
    - Issues & 5-Why Root Cause (New -> Investigating -> RootCauseVerified -> Closed)
    """

    programs = Bundle("programs")
    parts = Bundle("parts")
    dvprs = Bundle("dvprs")
    issues = Bundle("issues")
    changes = Bundle("changes")

    @initialize()
    def setup_db(self):
        Base.metadata.create_all(bind=test_engine)
        self.db = TestingSessionLocal()
        self.prog_service = ProgramService(self.db)
        self.part_service = PartService(self.db)
        self.dvpr_service = DVPRService(self.db)
        self.test_service = TestRunService(self.db)
        self.issue_service = IssueService(self.db)
        self.rc_service = RootCauseService(self.db)
        self.change_service = ChangeService(self.db)
        self.seq = 0
        self.created_program_ids = []
        self.created_part_ids = []
        self.created_dvpr_ids = []
        self.created_test_run_ids = []
        self.created_ecr_ids = []

    def teardown(self):
        for eid in self.created_ecr_ids:
            try:
                self.change_service.delete_change(eid)
            except Exception:
                pass
        for tid in self.created_test_run_ids:
            try:
                self.test_service.delete_test_run(tid)
            except Exception:
                pass
        for did in self.created_dvpr_ids:
            try:
                self.dvpr_service.delete_dvpr(did)
            except Exception:
                pass
        for pid in self.created_part_ids:
            try:
                self.part_service.delete_part(pid)
            except Exception:
                pass
        for prid in self.created_program_ids:
            try:
                self.prog_service.delete_program(prid)
            except Exception:
                pass
        self.db.close()

    @rule(target=programs, name=st.text(min_size=2, max_size=10, alphabet="ABCDEFGH0123456789"))
    def create_program(self, name: str):
        self.seq += 1
        code = f"HYP-P{self.seq}-{name}"
        p = self.prog_service.create_program(ProgramCreate(
            code=code,
            name=f"Vehicle {code}",
            platform="BEV-800V",
            phase="Proto-A",
            lead_engineer="Chief Lead",
            quality_manager="QM Specialist"
        ))
        self.created_program_ids.append(p.id)
        return p

    @rule(target=parts, prog=programs, rev=st.sampled_from(["A.0", "B.0", "C.0"]))
    def create_part(self, prog, rev):
        self.seq += 1
        pt = self.part_service.create_part(PartCreate(
            program_id=prog.id,
            part_number=f"HYP-PART-{self.seq}",
            name=f"Seal Part {self.seq}",
            subsystem="Primary Body Seal",
            category="EPDM-Sealing",
            supplier="Tier-1 Supplier",
            material="EPDM",
            revision=rev,
            weight_kg=1.5,
            safety_critical=True
        ))
        self.created_part_ids.append(pt.id)
        return pt

    @rule(target=dvprs, prog=programs, part=parts, status=st.sampled_from(["Planned", "In Progress", "Blocked"]))
    def create_dvpr(self, prog, part, status):
        self.seq += 1
        dv = self.dvpr_service.create_dvpr(DVPRCreate(
            program_id=prog.id,
            part_id=part.id,
            plan_code=f"HYP-DVP-{self.seq}",
            test_phase="DV-A",
            test_name=f"High Pressure Spray {self.seq}",
            test_standard="ISO 20653",
            acceptance_criteria="No water ingress",
            sample_size=3,
            test_facility="Chamber 1",
            planned_start_date="2026-10-01",
            planned_end_date="2026-10-30",
            status=status,
            responsible_engineer="Lab Lead"
        ))
        self.created_dvpr_ids.append(dv.id)
        return dv

    @rule(target=changes, prog=programs, part=parts, post_rev=st.sampled_from(["A.1", "B.1", "C.1", "D.0"]))
    def create_change(self, prog, part, post_rev):
        self.seq += 1
        if post_rev == part.revision:
            post_rev = post_rev + "-MOD"
        ecr = self.change_service.create_change(ChangeCreate(
            change_code=f"HYP-ECR-{self.seq}",
            program_id=prog.id,
            part_id=part.id,
            title=f"Optimization {self.seq}",
            change_type="Design-Mod",
            reason="Seal lip stiffness upgrade",
            pre_change_rev=part.revision,
            post_change_rev=post_rev,
            cost_impact_rmb=5.0,
            tooling_lead_weeks=2,
            approval_status="Draft",
            initiator="Release Eng"
        ))
        self.created_ecr_ids.append(ecr.id)
        return ecr

    @rule(ecr=changes, next_status=st.sampled_from(["Review-Eng", "Review-CostTooling", "Approved", "Rejected"]))
    def advance_change_workflow(self, ecr, next_status):
        self.change_service.update_change(ecr.id, ChangeUpdate(
            approval_status=next_status,
            approver="Chief Engineer" if next_status == "Approved" else None
        ))

    @rule(ecr=changes)
    def attempt_implement_change(self, ecr):
        """
        Adversarial Rule: Attempt to implement ECR.
        Must succeed ONLY IF approval_status is Approved.
        If Draft or Review, must raise BusinessRuleViolationError.
        """
        current_ecr = self.change_service.get_change(ecr.id)
        if current_ecr.approval_status != "Approved":
            with pytest.raises(BusinessRuleViolationError):
                self.change_service.update_change(ecr.id, ChangeUpdate(approval_status="Implemented"))
        else:
            self.change_service.update_change(ecr.id, ChangeUpdate(approval_status="Implemented"))
            part = self.part_service.get_part(current_ecr.part_id)
            assert part.revision == current_ecr.post_change_rev, "Part revision must be bumped on implementation"

    @rule(dv=dvprs, result=st.sampled_from(["Pass", "Fail"]))
    def attempt_test_run_execution(self, dv, result):
        """
        Adversarial Rule: Test execution against DVPR.
        Must be REJECTED if DVPR is Blocked.
        """
        current_dv = self.dvpr_service.get_dvpr(dv.id)
        self.seq += 1
        if current_dv.status == "Blocked":
            with pytest.raises(BusinessRuleViolationError):
                self.test_service.create_test_run(TestRunCreate(
                    dvpr_id=dv.id,
                    run_number=f"HYP-RUN-{self.seq}",
                    sample_id="SAMPLE-01",
                    test_date="2026-10-25",
                    test_facility="Chamber 1",
                    temperature_c=25.0,
                    humidity_rh=50.0,
                    cycles_completed=1000,
                    result=result,
                    operator="Tester",
                    measurement_data='{"leakage_ml": 0.0}'
                ))
        else:
            tr = self.test_service.create_test_run(TestRunCreate(
                dvpr_id=dv.id,
                run_number=f"HYP-RUN-{self.seq}",
                sample_id="SAMPLE-01",
                test_date="2026-10-25",
                test_facility="Chamber 1",
                temperature_c=25.0,
                humidity_rh=50.0,
                cycles_completed=1000,
                result=result,
                operator="Tester",
                measurement_data='{"leakage_ml": 0.0}'
            ))
            self.created_test_run_ids.append(tr.id)
            # Status sync check
            refreshed_dv = self.dvpr_service.get_dvpr(dv.id)
            if result == "Fail":
                assert refreshed_dv.status == "Failed"
            elif result == "Pass" and current_dv.status == "In Progress":
                assert refreshed_dv.status == "Passed"

    @invariant()
    def check_ecr_implementation_invariance(self):
        """Invariant: Every Implemented ECR created must have bumped its part revision."""
        for ecr_id in self.created_ecr_ids:
            ecr = self.change_service.get_change(ecr_id)
            if ecr.approval_status == "Implemented":
                part = self.part_service.get_part(ecr.part_id)
                assert part.revision == ecr.post_change_rev, (
                    f"Invariant violated for ECR {ecr.change_code}: "
                    f"part revision {part.revision} != post_change_rev {ecr.post_change_rev}"
                )


TestEQLStateMachine = EQLBusinessStateMachine.TestCase
TestEQLStateMachine.settings = settings(max_examples=25, stateful_step_count=20, deadline=None)
