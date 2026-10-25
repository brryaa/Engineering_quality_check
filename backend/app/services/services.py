import json
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.exceptions import EntityNotFoundError, DuplicateEntityError, BusinessRuleViolationError
from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun, EngineeringIssue,
    RootCauseAnalysis, EngineeringChange, KnowledgeItem
)
from app.schemas.schemas import (
    ProgramCreate, ProgramUpdate, PartCreate, PartUpdate,
    DFMEACreate, DFMEAUpdate, DVPRCreate, DVPRUpdate,
    TestRunCreate, TestRunUpdate, IssueCreate, IssueUpdate,
    RootCauseCreate, RootCauseUpdate, ChangeCreate, ChangeUpdate,
    KnowledgeItemCreate, KnowledgeItemUpdate, QualityDashboardStats
)
from app.services.fmea_engine import calculate_rpn, calculate_action_priority
from app.repositories.repositories import (
    ProgramRepository, PartRepository, DFMEARepository,
    DVPRRepository, TestRunRepository, IssueRepository,
    RootCauseRepository, ChangeRepository, KnowledgeRepository
)

class ProgramService:
    def __init__(self, db: Session):
        self.repo = ProgramRepository(db)

    def get_program(self, program_id: int) -> Program:
        p = self.repo.get_by_id(program_id)
        if not p:
            raise EntityNotFoundError("Program", program_id)
        return p

    def list_programs(self, **kwargs) -> Tuple[List[Program], int]:
        return self.repo.filter_programs(**kwargs)

    def create_program(self, data: ProgramCreate) -> Program:
        if self.repo.get_by_code(data.code):
            raise DuplicateEntityError(f"Program with code '{data.code}' already exists.")
        p = Program(**data.model_dump())
        return self.repo.create(p)

    def update_program(self, program_id: int, data: ProgramUpdate) -> Program:
        p = self.get_program(program_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        return self.repo.update(p)

    def delete_program(self, program_id: int) -> None:
        p = self.get_program(program_id)
        self.repo.delete(p)


class PartService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PartRepository(db)
        self.program_repo = ProgramRepository(db)

    def get_part(self, part_id: int) -> Part:
        pt = self.repo.get_by_id(part_id)
        if not pt:
            raise EntityNotFoundError("Part", part_id)
        return pt

    def list_parts(self, **kwargs) -> Tuple[List[Part], int]:
        return self.repo.filter_parts(**kwargs)

    def create_part(self, data: PartCreate) -> Part:
        if not self.program_repo.get_by_id(data.program_id):
            raise BusinessRuleViolationError(f"Program with id {data.program_id} does not exist.")
        if self.repo.get_by_part_number(data.part_number):
            raise DuplicateEntityError(f"Part with number '{data.part_number}' already exists.")
        pt = Part(**data.model_dump())
        return self.repo.create(pt)

    def update_part(self, part_id: int, data: PartUpdate) -> Part:
        pt = self.get_part(part_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(pt, k, v)
        return self.repo.update(pt)

    def delete_part(self, part_id: int) -> None:
        pt = self.get_part(part_id)
        self.repo.delete(pt)


class DFMEAService:
    def __init__(self, db: Session):
        self.repo = DFMEARepository(db)
        self.part_repo = PartRepository(db)

    def get_dfmea(self, dfmea_id: int) -> DFMEA:
        row = self.repo.get_by_id(dfmea_id)
        if not row:
            raise EntityNotFoundError("DFMEA", dfmea_id)
        return row

    def list_dfmeas(self, **kwargs) -> Tuple[List[DFMEA], int]:
        return self.repo.filter_dfmeas(**kwargs)

    def create_dfmea(self, data: DFMEACreate) -> DFMEA:
        if not self.part_repo.get_by_id(data.part_id):
            raise BusinessRuleViolationError(f"Part with id {data.part_id} does not exist.")
        if self.repo.get_by_code(data.fmea_code):
            raise DuplicateEntityError(f"DFMEA with code '{data.fmea_code}' already exists.")

        rpn = calculate_rpn(data.severity, data.occurrence, data.detection)
        ap = calculate_action_priority(data.severity, data.occurrence, data.detection)

        post_rpn = None
        if data.post_severity and data.post_occurrence and data.post_detection:
            post_rpn = calculate_rpn(data.post_severity, data.post_occurrence, data.post_detection)

        payload = data.model_dump()
        payload["rpn"] = rpn
        payload["action_priority"] = ap
        payload["post_rpn"] = post_rpn

        dfmea = DFMEA(**payload)
        return self.repo.create(dfmea)

    def update_dfmea(self, dfmea_id: int, data: DFMEAUpdate) -> DFMEA:
        dfmea = self.get_dfmea(dfmea_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(dfmea, k, v)

        dfmea.rpn = calculate_rpn(dfmea.severity, dfmea.occurrence, dfmea.detection)
        dfmea.action_priority = calculate_action_priority(dfmea.severity, dfmea.occurrence, dfmea.detection)

        if dfmea.post_severity and dfmea.post_occurrence and dfmea.post_detection:
            dfmea.post_rpn = calculate_rpn(dfmea.post_severity, dfmea.post_occurrence, dfmea.post_detection)

        return self.repo.update(dfmea)

    def delete_dfmea(self, dfmea_id: int) -> None:
        dfmea = self.get_dfmea(dfmea_id)
        self.repo.delete(dfmea)


class DVPRService:
    def __init__(self, db: Session):
        self.repo = DVPRRepository(db)
        self.program_repo = ProgramRepository(db)
        self.part_repo = PartRepository(db)

    def get_dvpr(self, dvpr_id: int) -> DVPR:
        dv = self.repo.get_by_id(dvpr_id)
        if not dv:
            raise EntityNotFoundError("DVPR", dvpr_id)
        return dv

    def list_dvprs(self, **kwargs) -> Tuple[List[DVPR], int]:
        return self.repo.filter_dvprs(**kwargs)

    def create_dvpr(self, data: DVPRCreate) -> DVPR:
        if not self.program_repo.get_by_id(data.program_id):
            raise BusinessRuleViolationError(f"Program with id {data.program_id} does not exist.")
        if not self.part_repo.get_by_id(data.part_id):
            raise BusinessRuleViolationError(f"Part with id {data.part_id} does not exist.")
        if self.repo.get_by_plan_code(data.plan_code):
            raise DuplicateEntityError(f"DVPR with code '{data.plan_code}' already exists.")

        dv = DVPR(**data.model_dump())
        return self.repo.create(dv)

    def update_dvpr(self, dvpr_id: int, data: DVPRUpdate) -> DVPR:
        dv = self.get_dvpr(dvpr_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(dv, k, v)
        return self.repo.update(dv)

    def delete_dvpr(self, dvpr_id: int) -> None:
        dv = self.get_dvpr(dvpr_id)
        self.repo.delete(dv)


class TestRunService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TestRunRepository(db)
        self.dvpr_repo = DVPRRepository(db)

    def get_test_run(self, test_id: int) -> TestRun:
        tr = self.repo.get_by_id(test_id)
        if not tr:
            raise EntityNotFoundError("TestRun", test_id)
        return tr

    def list_test_runs(self, **kwargs) -> Tuple[List[TestRun], int]:
        return self.repo.filter_test_runs(**kwargs)

    def create_test_run(self, data: TestRunCreate) -> TestRun:
        dvpr = self.dvpr_repo.get_by_id(data.dvpr_id)
        if not dvpr:
            raise BusinessRuleViolationError(f"DVPR with id {data.dvpr_id} does not exist.")
        if dvpr.status == "Blocked":
            raise BusinessRuleViolationError("Cannot execute test runs against a Blocked DVP&R plan.")
        if data.measurement_data:
            try:
                json.loads(data.measurement_data)
            except Exception:
                raise BusinessRuleViolationError("measurement_data must be valid JSON telemetry.")
        if self.repo.get_by_run_number(data.run_number):
            raise DuplicateEntityError(f"TestRun with number '{data.run_number}' already exists.")

        tr = TestRun(**data.model_dump())
        self.db.add(tr)

        # Synchronize DVP status
        if dvpr.status == "Planned":
            dvpr.status = "In Progress"
        if data.result == "Fail" and dvpr.status != "Failed":
            dvpr.status = "Failed"
        elif data.result == "Pass" and dvpr.status == "In Progress":
            dvpr.status = "Passed"

        self.db.commit()
        self.db.refresh(tr)
        return tr

    def update_test_run(self, test_id: int, data: TestRunUpdate) -> TestRun:
        tr = self.get_test_run(test_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(tr, k, v)
        return self.repo.update(tr)

    def delete_test_run(self, test_id: int) -> None:
        tr = self.get_test_run(test_id)
        self.repo.delete(tr)


class IssueService:
    def __init__(self, db: Session):
        self.repo = IssueRepository(db)
        self.program_repo = ProgramRepository(db)
        self.part_repo = PartRepository(db)
        self.test_repo = TestRunRepository(db)

    def get_issue(self, issue_id: int) -> EngineeringIssue:
        iss = self.repo.get_by_id(issue_id)
        if not iss:
            raise EntityNotFoundError("EngineeringIssue", issue_id)
        return iss

    def list_issues(self, **kwargs) -> Tuple[List[EngineeringIssue], int]:
        return self.repo.filter_issues(**kwargs)

    def create_issue(self, data: IssueCreate) -> EngineeringIssue:
        if not self.program_repo.get_by_id(data.program_id):
            raise BusinessRuleViolationError(f"Program with id {data.program_id} does not exist.")
        if not self.part_repo.get_by_id(data.part_id):
            raise BusinessRuleViolationError(f"Part with id {data.part_id} does not exist.")
        if data.test_run_id and not self.test_repo.get_by_id(data.test_run_id):
            raise BusinessRuleViolationError(f"TestRun with id {data.test_run_id} does not exist.")
        if self.repo.get_by_code(data.issue_code):
            raise DuplicateEntityError(f"Issue with code '{data.issue_code}' already exists.")

        iss = EngineeringIssue(**data.model_dump())
        return self.repo.create(iss)

    def update_issue(self, issue_id: int, data: IssueUpdate) -> EngineeringIssue:
        iss = self.get_issue(issue_id)
        up_data = data.model_dump(exclude_unset=True)

        if up_data.get("status") == "Closed" and not up_data.get("closure_date") and not iss.closure_date:
            up_data["closure_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for k, v in up_data.items():
            setattr(iss, k, v)
        return self.repo.update(iss)

    def delete_issue(self, issue_id: int) -> None:
        iss = self.get_issue(issue_id)
        self.repo.delete(iss)


class RootCauseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RootCauseRepository(db)
        self.issue_repo = IssueRepository(db)

    def get_root_cause(self, rc_id: int) -> RootCauseAnalysis:
        rc = self.repo.get_by_id(rc_id)
        if not rc:
            raise EntityNotFoundError("RootCauseAnalysis", rc_id)
        return rc

    def get_by_issue_id(self, issue_id: int) -> RootCauseAnalysis:
        rc = self.repo.get_by_issue_id(issue_id)
        if not rc:
            raise EntityNotFoundError("RootCauseAnalysis for Issue", issue_id)
        return rc

    def list_root_causes(self, **kwargs) -> Tuple[List[RootCauseAnalysis], int]:
        return self.repo.filter_root_causes(**kwargs)

    def create_root_cause(self, data: RootCauseCreate) -> RootCauseAnalysis:
        issue = self.issue_repo.get_by_id(data.issue_id)
        if not issue:
            raise BusinessRuleViolationError(f"Issue with id {data.issue_id} does not exist.")
        if issue.status == "Closed":
            raise BusinessRuleViolationError("Cannot perform 5-Why root cause analysis on an already Closed issue. Issue must be reopened first.")
        if self.repo.get_by_issue_id(data.issue_id):
            raise DuplicateEntityError(f"Root Cause Analysis already exists for Issue {issue.issue_code}.")

        rc = RootCauseAnalysis(**data.model_dump())
        self.db.add(rc)

        if data.verification_result == "Confirmed" and issue.status in ["New", "Investigating", "Containment"]:
            issue.status = "RootCauseVerified"

        self.db.commit()
        self.db.refresh(rc)
        return rc

    def update_root_cause(self, rc_id: int, data: RootCauseUpdate) -> RootCauseAnalysis:
        rc = self.get_root_cause(rc_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(rc, k, v)

        if rc.verification_result == "Confirmed" and rc.issue.status in ["New", "Investigating", "Containment"]:
            rc.issue.status = "RootCauseVerified"

        return self.repo.update(rc)

    def delete_root_cause(self, rc_id: int) -> None:
        rc = self.get_root_cause(rc_id)
        if rc.issue and rc.issue.status == "RootCauseVerified":
            rc.issue.status = "Investigating"
        self.repo.delete(rc)


class ChangeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ChangeRepository(db)
        self.program_repo = ProgramRepository(db)
        self.part_repo = PartRepository(db)
        self.issue_repo = IssueRepository(db)

    def get_change(self, change_id: int) -> EngineeringChange:
        ecr = self.repo.get_by_id(change_id)
        if not ecr:
            raise EntityNotFoundError("EngineeringChange", change_id)
        return ecr

    def list_changes(self, **kwargs) -> Tuple[List[EngineeringChange], int]:
        return self.repo.filter_changes(**kwargs)

    def create_change(self, data: ChangeCreate) -> EngineeringChange:
        if not self.program_repo.get_by_id(data.program_id):
            raise BusinessRuleViolationError(f"Program with id {data.program_id} does not exist.")
        if not self.part_repo.get_by_id(data.part_id):
            raise BusinessRuleViolationError(f"Part with id {data.part_id} does not exist.")
        if data.issue_id and not self.issue_repo.get_by_id(data.issue_id):
            raise BusinessRuleViolationError(f"Issue with id {data.issue_id} does not exist.")
        if data.pre_change_rev and data.post_change_rev and data.post_change_rev == data.pre_change_rev:
            raise BusinessRuleViolationError("post_change_rev must differ from pre_change_rev.")
        if data.approval_status == "Implemented":
            raise BusinessRuleViolationError("Cannot implement an unapproved engineering change. Must be Approved first.")
        if self.repo.get_by_change_code(data.change_code):
            raise DuplicateEntityError(f"Change with code '{data.change_code}' already exists.")

        ecr = EngineeringChange(**data.model_dump())
        return self.repo.create(ecr)

    def update_change(self, change_id: int, data: ChangeUpdate) -> EngineeringChange:
        ecr = self.get_change(change_id)
        up_data = data.model_dump(exclude_unset=True)

        new_status = up_data.get("approval_status")
        if new_status == "Implemented" and ecr.approval_status != "Approved":
            raise BusinessRuleViolationError("Cannot implement an unapproved engineering change. Must be Approved first.")

        pre_rev = up_data.get("pre_change_rev", ecr.pre_change_rev)
        post_rev = up_data.get("post_change_rev", ecr.post_change_rev)
        if pre_rev and post_rev and pre_rev == post_rev:
            raise BusinessRuleViolationError("post_change_rev must differ from pre_change_rev.")

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if new_status == "Approved" and not up_data.get("approval_date") and not ecr.approval_date:
            up_data["approval_date"] = today_str

        if new_status == "Implemented":
            if not up_data.get("implementation_date") and not ecr.implementation_date:
                up_data["implementation_date"] = today_str
            part = self.part_repo.get_by_id(ecr.part_id)
            if part:
                part.revision = ecr.post_change_rev

        for k, v in up_data.items():
            setattr(ecr, k, v)

        return self.repo.update(ecr)

    def delete_change(self, change_id: int) -> None:
        ecr = self.get_change(change_id)
        self.repo.delete(ecr)


class KnowledgeService:
    def __init__(self, db: Session):
        self.repo = KnowledgeRepository(db)

    def get_knowledge_item(self, kb_id: int) -> KnowledgeItem:
        kb = self.repo.get_by_id(kb_id)
        if not kb:
            raise EntityNotFoundError("KnowledgeItem", kb_id)
        return kb

    def list_knowledge(self, **kwargs) -> Tuple[List[KnowledgeItem], int]:
        return self.repo.filter_knowledge(**kwargs)

    def create_knowledge_item(self, data: KnowledgeItemCreate) -> KnowledgeItem:
        if self.repo.get_by_doc_code(data.doc_code):
            raise DuplicateEntityError(f"Knowledge item with code '{data.doc_code}' already exists.")
        kb = KnowledgeItem(**data.model_dump())
        return self.repo.create(kb)

    def update_knowledge_item(self, kb_id: int, data: KnowledgeItemUpdate) -> KnowledgeItem:
        kb = self.get_knowledge_item(kb_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(kb, k, v)
        return self.repo.update(kb)

    def delete_knowledge_item(self, kb_id: int) -> None:
        kb = self.get_knowledge_item(kb_id)
        self.repo.delete(kb)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self, program_id: Optional[int] = None) -> QualityDashboardStats:
        part_q = self.db.query(Part)
        dfmea_q = self.db.query(DFMEA)
        dvpr_q = self.db.query(DVPR)
        test_q = self.db.query(TestRun)
        issue_q = self.db.query(EngineeringIssue)
        change_q = self.db.query(EngineeringChange)

        if program_id:
            part_q = part_q.filter(Part.program_id == program_id)
            dfmea_q = dfmea_q.join(Part, DFMEA.part_id == Part.id).filter(Part.program_id == program_id)
            dvpr_q = dvpr_q.filter(DVPR.program_id == program_id)
            test_q = test_q.join(DVPR, TestRun.dvpr_id == DVPR.id).filter(DVPR.program_id == program_id)
            issue_q = issue_q.filter(EngineeringIssue.program_id == program_id)
            change_q = change_q.filter(EngineeringChange.program_id == program_id)

        total_programs = self.db.query(Program).count() if not program_id else 1
        total_parts = part_q.count()
        total_dfmeas = dfmea_q.count()
        total_dvprs = dvpr_q.count()
        total_test_runs = test_q.count()
        total_issues = issue_q.count()
        total_changes = change_q.count()

        high_ap = dfmea_q.filter(DFMEA.action_priority == "High").count()
        med_ap = dfmea_q.filter(DFMEA.action_priority == "Medium").count()
        low_ap = dfmea_q.filter(DFMEA.action_priority == "Low").count()
        high_rpn = dfmea_q.filter(DFMEA.rpn >= 100).count()

        dvpr_status_rows = self.db.query(DVPR.status, func.count(DVPR.id))
        if program_id:
            dvpr_status_rows = dvpr_status_rows.filter(DVPR.program_id == program_id)
        dvpr_status_counts = dict(dvpr_status_rows.group_by(DVPR.status).all())

        test_res_rows = self.db.query(TestRun.result, func.count(TestRun.id))
        if program_id:
            test_res_rows = test_res_rows.join(DVPR, TestRun.dvpr_id == DVPR.id).filter(DVPR.program_id == program_id)
        test_run_result_counts = dict(test_res_rows.group_by(TestRun.result).all())

        pass_count = test_run_result_counts.get("Pass", 0)
        pass_rate_pct = round((pass_count / total_test_runs * 100), 2) if total_test_runs > 0 else 0.0

        issue_sev_rows = self.db.query(EngineeringIssue.severity, func.count(EngineeringIssue.id))
        if program_id:
            issue_sev_rows = issue_sev_rows.filter(EngineeringIssue.program_id == program_id)
        issue_severity_counts = dict(issue_sev_rows.group_by(EngineeringIssue.severity).all())

        issue_stat_rows = self.db.query(EngineeringIssue.status, func.count(EngineeringIssue.id))
        if program_id:
            issue_stat_rows = issue_stat_rows.filter(EngineeringIssue.program_id == program_id)
        issue_status_counts = dict(issue_stat_rows.group_by(EngineeringIssue.status).all())

        open_critical_issues_count = issue_q.filter(
            EngineeringIssue.severity == "S1-Critical",
            EngineeringIssue.status.notin_(["Closed", "Rejected", "ValidationPass"])
        ).count()

        cost_sum = self.db.query(func.sum(EngineeringChange.cost_impact_rmb))
        if program_id:
            cost_sum = cost_sum.filter(EngineeringChange.program_id == program_id)
        total_cost_impact = round(cost_sum.scalar() or 0.0, 2)

        change_stat_rows = self.db.query(EngineeringChange.approval_status, func.count(EngineeringChange.id))
        if program_id:
            change_stat_rows = change_stat_rows.filter(EngineeringChange.program_id == program_id)
        changes_by_status = dict(change_stat_rows.group_by(EngineeringChange.approval_status).all())

        subsystems_data = []
        subsystem_list = [
            "Front Door Closure", "Rear Door Closure", "Power Tailgate System",
            "Frameless Window System", "Primary Body Seal", "Secondary Acoustic Weatherstrip",
            "Water Deflector & Drainage", "Door Hinge & Check Link", "Glass Regulator Module",
            "Tailgate Spindle & Cinch Latch"
        ]
        for subsys in subsystem_list:
            sub_part_ids = [pt.id for pt in self.db.query(Part.id).filter(Part.subsystem == subsys).all()]
            if not sub_part_ids:
                continue
            sub_issues = self.db.query(EngineeringIssue).filter(EngineeringIssue.part_id.in_(sub_part_ids)).count()
            sub_critical = self.db.query(EngineeringIssue).filter(
                EngineeringIssue.part_id.in_(sub_part_ids),
                EngineeringIssue.severity == "S1-Critical",
                EngineeringIssue.status.notin_(["Closed", "Rejected"])
            ).count()
            health_score = max(20, 100 - (sub_critical * 15) - (sub_issues * 2))

            subsystems_data.append({
                "subsystem": subsys,
                "total_issues": sub_issues,
                "open_critical_issues": sub_critical,
                "health_score": health_score
            })

        subsystems_data.sort(key=lambda x: x["health_score"])

        return QualityDashboardStats(
            total_programs=total_programs,
            total_parts=total_parts,
            total_dfmeas=total_dfmeas,
            total_dvprs=total_dvprs,
            total_test_runs=total_test_runs,
            total_issues=total_issues,
            total_changes=total_changes,
            dfmea_high_ap_count=high_ap,
            dfmea_medium_ap_count=med_ap,
            dfmea_low_ap_count=low_ap,
            dfmea_high_rpn_count=high_rpn,
            dvpr_status_counts=dvpr_status_counts,
            test_run_pass_rate_pct=pass_rate_pct,
            test_run_result_counts=test_run_result_counts,
            issue_severity_counts=issue_severity_counts,
            issue_status_counts=issue_status_counts,
            open_critical_issues_count=open_critical_issues_count,
            total_change_cost_impact_rmb=total_cost_impact,
            changes_by_status=changes_by_status,
            subsystem_health=subsystems_data
        )
