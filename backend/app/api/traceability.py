from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundError
from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun,
    EngineeringIssue, RootCauseAnalysis, EngineeringChange
)
from app.schemas.schemas import (
    IssueResponse, PartResponse, ProgramResponse,
    DFMEAResponse, DVPRResponse, TestRunResponse,
    RootCauseResponse, ChangeResponse
)

router = APIRouter(prefix="/traceability", tags=["Engineering Quality Traceability"])


class TraceabilityChainResponse(BaseModel):
    issue_code: str
    issue_title: str
    severity: str
    status: str
    program_code: str
    part_number: str
    subsystem: str
    dfmea_linkages: List[Dict[str, Any]]
    dvpr_test_plan: Optional[Dict[str, Any]] = None
    test_run_execution: Optional[Dict[str, Any]] = None
    root_cause_analysis: Optional[Dict[str, Any]] = None
    engineering_changes: List[Dict[str, Any]] = []
    closed_loop_verified: bool = False


@router.get("/lineage/{issue_id}", response_model=TraceabilityChainResponse)
def get_issue_traceability_lineage(issue_id: int, db: Session = Depends(get_db)):
    """
    Traces complete lifecycle lineage for an automotive engineering defect:
    Part -> DFMEA Risk Items -> DVP&R Plan -> Physical Test Telemetry -> Defect Issue -> 5-Why Analysis -> ECR Changes.
    """
    issue = db.query(EngineeringIssue).filter(EngineeringIssue.id == issue_id).first()
    if not issue:
        raise EntityNotFoundError("EngineeringIssue", issue_id)

    part = issue.part
    program = issue.program

    # 1. Associated DFMEA risks for this part
    dfmeas = db.query(DFMEA).filter(DFMEA.part_id == part.id).all() if part else []
    dfmea_data = [
        {
            "fmea_code": d.fmea_code,
            "failure_mode": d.failure_mode,
            "failure_cause": d.cause_mechanism,
            "severity": d.severity,
            "occurrence": d.occurrence,
            "detection": d.detection,
            "action_priority": d.action_priority,
            "rpn": d.rpn
        }
        for d in dfmeas
    ]

    # 2. Test Execution & DVP&R link
    test_run_data = None
    dvpr_data = None
    if issue.test_run:
        tr = issue.test_run
        test_run_data = {
            "run_number": tr.run_number,
            "sample_id": tr.sample_id,
            "test_date": tr.test_date,
            "result": tr.result,
            "cycles_completed": tr.cycles_completed,
            "failure_summary": tr.failure_summary
        }
        if tr.dvpr:
            dvpr = tr.dvpr
            dvpr_data = {
                "plan_code": dvpr.plan_code,
                "test_name": dvpr.test_name,
                "test_standard": dvpr.test_standard,
                "test_phase": dvpr.test_phase,
                "acceptance_criteria": dvpr.acceptance_criteria
            }

    # 3. Root Cause Analysis
    rc_data = None
    if issue.root_cause:
        rc = issue.root_cause
        rc_data = {
            "analysis_method": rc.analysis_method,
            "direct_cause": rc.direct_cause,
            "systemic_root_cause": rc.systemic_root_cause,
            "why_1": rc.why_1,
            "why_2": rc.why_2,
            "why_3": rc.why_3,
            "why_4": rc.why_4,
            "why_5": rc.why_5,
            "verification_result": rc.verification_result
        }

    # 4. Engineering Changes
    changes = db.query(EngineeringChange).filter(EngineeringChange.issue_id == issue.id).all()
    changes_data = [
        {
            "change_code": c.change_code,
            "title": c.title,
            "change_type": c.change_type,
            "pre_change_rev": c.pre_change_rev,
            "post_change_rev": c.post_change_rev,
            "cost_impact_rmb": c.cost_impact_rmb,
            "approval_status": c.approval_status
        }
        for c in changes
    ]

    # Closed-loop verification rule: Issue is ValidationPass/Closed, root cause confirmed, and change implemented/approved
    closed_loop = (
        issue.status in ["ValidationPass", "Closed"] and
        (issue.root_cause is not None and issue.root_cause.verification_result == "Confirmed") and
        (len(changes) > 0 and any(c.approval_status in ["Approved", "Implemented"] for c in changes))
    )

    return TraceabilityChainResponse(
        issue_code=issue.issue_code,
        issue_title=issue.title,
        severity=issue.severity,
        status=issue.status,
        program_code=program.code if program else "N/A",
        part_number=part.part_number if part else "N/A",
        subsystem=part.subsystem if part else "N/A",
        dfmea_linkages=dfmea_data,
        dvpr_test_plan=dvpr_data,
        test_run_execution=test_run_data,
        root_cause_analysis=rc_data,
        engineering_changes=changes_data,
        closed_loop_verified=closed_loop
    )


@router.get("/subsystem/{subsystem_name}")
def get_subsystem_quality_tree(subsystem_name: str, db: Session = Depends(get_db)):
    """Returns all parts, risks, and open issues aggregated under an automotive closure subsystem."""
    parts = db.query(Part).filter(Part.subsystem.ilike(f"%{subsystem_name}%")).all()
    part_ids = [p.id for p in parts]

    issues = db.query(EngineeringIssue).filter(EngineeringIssue.part_id.in_(part_ids)).all() if part_ids else []
    dfmeas = db.query(DFMEA).filter(DFMEA.part_id.in_(part_ids)).all() if part_ids else []

    return {
        "subsystem": subsystem_name,
        "parts_count": len(parts),
        "total_dfmeas": len(dfmeas),
        "high_ap_risks": sum(1 for d in dfmeas if d.action_priority == "High"),
        "total_issues": len(issues),
        "open_critical_issues": sum(1 for i in issues if i.severity == "S1-Critical" and i.status not in ["Closed", "Rejected"]),
        "parts": [
            {
                "id": p.id,
                "part_number": p.part_number,
                "name": p.name,
                "revision": p.revision,
                "supplier": p.supplier
            }
            for p in parts
        ]
    }
