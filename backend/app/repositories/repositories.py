from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, asc, func
from app.repositories.base_repository import BaseRepository
from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun, EngineeringIssue,
    RootCauseAnalysis, EngineeringChange, KnowledgeItem
)

class ProgramRepository(BaseRepository[Program]):
    def __init__(self, db: Session):
        super().__init__(Program, db)

    def get_by_code(self, code: str) -> Optional[Program]:
        return self.db.query(Program).filter(Program.code == code).first()

    def filter_programs(
        self,
        search: Optional[str] = None,
        phase: Optional[str] = None,
        platform: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[Program], int]:
        q = self.db.query(Program)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(Program.code.ilike(s), Program.name.ilike(s), Program.platform.ilike(s)))
        if phase:
            q = q.filter(Program.phase == phase)
        if platform:
            q = q.filter(Program.platform == platform)

        order_col = getattr(Program, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.offset(offset).limit(limit).all()
        return items, total


class PartRepository(BaseRepository[Part]):
    def __init__(self, db: Session):
        super().__init__(Part, db)

    def get_by_part_number(self, part_number: str) -> Optional[Part]:
        return self.db.query(Part).filter(Part.part_number == part_number).first()

    def filter_parts(
        self,
        search: Optional[str] = None,
        program_id: Optional[int] = None,
        subsystem: Optional[str] = None,
        category: Optional[str] = None,
        safety_critical: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[Part], int]:
        q = self.db.query(Part).join(Program, Part.program_id == Program.id)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(Part.part_number.ilike(s), Part.name.ilike(s), Part.material.ilike(s), Part.supplier.ilike(s)))
        if program_id:
            q = q.filter(Part.program_id == program_id)
        if subsystem:
            q = q.filter(Part.subsystem == subsystem)
        if category:
            q = q.filter(Part.category == category)
        if safety_critical is not None:
            q = q.filter(Part.safety_critical == safety_critical)

        order_col = getattr(Part, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.options(joinedload(Part.program)).offset(offset).limit(limit).all()
        return items, total


class DFMEARepository(BaseRepository[DFMEA]):
    def __init__(self, db: Session):
        super().__init__(DFMEA, db)

    def get_by_code(self, fmea_code: str) -> Optional[DFMEA]:
        return self.db.query(DFMEA).filter(DFMEA.fmea_code == fmea_code).first()

    def filter_dfmeas(
        self,
        search: Optional[str] = None,
        part_id: Optional[int] = None,
        action_priority: Optional[str] = None,
        action_status: Optional[str] = None,
        min_rpn: Optional[int] = None,
        min_severity: Optional[int] = None,
        sort_by: str = "rpn",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[DFMEA], int]:
        q = self.db.query(DFMEA).join(Part, DFMEA.part_id == Part.id)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(
                DFMEA.fmea_code.ilike(s),
                DFMEA.item_function.ilike(s),
                DFMEA.failure_mode.ilike(s),
                DFMEA.failure_effect.ilike(s),
                DFMEA.cause_mechanism.ilike(s)
            ))
        if part_id:
            q = q.filter(DFMEA.part_id == part_id)
        if action_priority:
            q = q.filter(DFMEA.action_priority == action_priority)
        if action_status:
            q = q.filter(DFMEA.action_status == action_status)
        if min_rpn is not None:
            q = q.filter(DFMEA.rpn >= min_rpn)
        if min_severity is not None:
            q = q.filter(DFMEA.severity >= min_severity)

        order_col = getattr(DFMEA, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.options(joinedload(DFMEA.part)).offset(offset).limit(limit).all()
        return items, total


class DVPRRepository(BaseRepository[DVPR]):
    def __init__(self, db: Session):
        super().__init__(DVPR, db)

    def get_by_plan_code(self, plan_code: str) -> Optional[DVPR]:
        return self.db.query(DVPR).filter(DVPR.plan_code == plan_code).first()

    def filter_dvprs(
        self,
        search: Optional[str] = None,
        program_id: Optional[int] = None,
        part_id: Optional[int] = None,
        test_phase: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[DVPR], int]:
        q = self.db.query(DVPR).join(Program, DVPR.program_id == Program.id).join(Part, DVPR.part_id == Part.id)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(
                DVPR.plan_code.ilike(s),
                DVPR.test_name.ilike(s),
                DVPR.test_standard.ilike(s),
                DVPR.test_facility.ilike(s)
            ))
        if program_id:
            q = q.filter(DVPR.program_id == program_id)
        if part_id:
            q = q.filter(DVPR.part_id == part_id)
        if test_phase:
            q = q.filter(DVPR.test_phase == test_phase)
        if status:
            q = q.filter(DVPR.status == status)

        order_col = getattr(DVPR, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.options(joinedload(DVPR.program), joinedload(DVPR.part), joinedload(DVPR.test_runs)).offset(offset).limit(limit).all()
        return items, total


class TestRunRepository(BaseRepository[TestRun]):
    def __init__(self, db: Session):
        super().__init__(TestRun, db)

    def get_by_run_number(self, run_number: str) -> Optional[TestRun]:
        return self.db.query(TestRun).filter(TestRun.run_number == run_number).first()

    def filter_test_runs(
        self,
        search: Optional[str] = None,
        dvpr_id: Optional[int] = None,
        result: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[TestRun], int]:
        q = self.db.query(TestRun).join(DVPR, TestRun.dvpr_id == DVPR.id)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(
                TestRun.run_number.ilike(s),
                TestRun.sample_id.ilike(s),
                TestRun.operator.ilike(s),
                TestRun.test_facility.ilike(s)
            ))
        if dvpr_id:
            q = q.filter(TestRun.dvpr_id == dvpr_id)
        if result:
            q = q.filter(TestRun.result == result)

        order_col = getattr(TestRun, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.options(joinedload(TestRun.dvpr)).offset(offset).limit(limit).all()
        return items, total


class IssueRepository(BaseRepository[EngineeringIssue]):
    def __init__(self, db: Session):
        super().__init__(EngineeringIssue, db)

    def get_by_code(self, issue_code: str) -> Optional[EngineeringIssue]:
        return self.db.query(EngineeringIssue).filter(EngineeringIssue.issue_code == issue_code).first()

    def filter_issues(
        self,
        search: Optional[str] = None,
        program_id: Optional[int] = None,
        part_id: Optional[int] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[EngineeringIssue], int]:
        q = self.db.query(EngineeringIssue).join(Program, EngineeringIssue.program_id == Program.id).join(Part, EngineeringIssue.part_id == Part.id)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(
                EngineeringIssue.issue_code.ilike(s),
                EngineeringIssue.title.ilike(s),
                EngineeringIssue.description.ilike(s),
                EngineeringIssue.assignee.ilike(s),
                EngineeringIssue.reporter.ilike(s)
            ))
        if program_id:
            q = q.filter(EngineeringIssue.program_id == program_id)
        if part_id:
            q = q.filter(EngineeringIssue.part_id == part_id)
        if severity:
            q = q.filter(EngineeringIssue.severity == severity)
        if status:
            q = q.filter(EngineeringIssue.status == status)

        order_col = getattr(EngineeringIssue, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.options(
            joinedload(EngineeringIssue.program),
            joinedload(EngineeringIssue.part),
            joinedload(EngineeringIssue.root_cause)
        ).offset(offset).limit(limit).all()
        return items, total


class RootCauseRepository(BaseRepository[RootCauseAnalysis]):
    def __init__(self, db: Session):
        super().__init__(RootCauseAnalysis, db)

    def get_by_issue_id(self, issue_id: int) -> Optional[RootCauseAnalysis]:
        return self.db.query(RootCauseAnalysis).filter(RootCauseAnalysis.issue_id == issue_id).first()

    def filter_root_causes(
        self,
        issue_id: Optional[int] = None,
        analysis_method: Optional[str] = None,
        verification_result: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[RootCauseAnalysis], int]:
        q = self.db.query(RootCauseAnalysis).join(EngineeringIssue, RootCauseAnalysis.issue_id == EngineeringIssue.id)
        if issue_id:
            q = q.filter(RootCauseAnalysis.issue_id == issue_id)
        if analysis_method:
            q = q.filter(RootCauseAnalysis.analysis_method == analysis_method)
        if verification_result:
            q = q.filter(RootCauseAnalysis.verification_result == verification_result)

        order_col = getattr(RootCauseAnalysis, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.options(joinedload(RootCauseAnalysis.issue)).offset(offset).limit(limit).all()
        return items, total


class ChangeRepository(BaseRepository[EngineeringChange]):
    def __init__(self, db: Session):
        super().__init__(EngineeringChange, db)

    def get_by_change_code(self, change_code: str) -> Optional[EngineeringChange]:
        return self.db.query(EngineeringChange).filter(EngineeringChange.change_code == change_code).first()

    def filter_changes(
        self,
        search: Optional[str] = None,
        program_id: Optional[int] = None,
        part_id: Optional[int] = None,
        approval_status: Optional[str] = None,
        change_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[EngineeringChange], int]:
        q = self.db.query(EngineeringChange).join(Program, EngineeringChange.program_id == Program.id).join(Part, EngineeringChange.part_id == Part.id)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(
                EngineeringChange.change_code.ilike(s),
                EngineeringChange.title.ilike(s),
                EngineeringChange.reason.ilike(s),
                EngineeringChange.initiator.ilike(s)
            ))
        if program_id:
            q = q.filter(EngineeringChange.program_id == program_id)
        if part_id:
            q = q.filter(EngineeringChange.part_id == part_id)
        if approval_status:
            q = q.filter(EngineeringChange.approval_status == approval_status)
        if change_type:
            q = q.filter(EngineeringChange.change_type == change_type)

        order_col = getattr(EngineeringChange, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.options(
            joinedload(EngineeringChange.program),
            joinedload(EngineeringChange.part),
            joinedload(EngineeringChange.issue)
        ).offset(offset).limit(limit).all()
        return items, total


class KnowledgeRepository(BaseRepository[KnowledgeItem]):
    def __init__(self, db: Session):
        super().__init__(KnowledgeItem, db)

    def get_by_doc_code(self, doc_code: str) -> Optional[KnowledgeItem]:
        return self.db.query(KnowledgeItem).filter(KnowledgeItem.doc_code == doc_code).first()

    def filter_knowledge(
        self,
        search: Optional[str] = None,
        subsystem: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[KnowledgeItem], int]:
        q = self.db.query(KnowledgeItem)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(
                KnowledgeItem.doc_code.ilike(s),
                KnowledgeItem.title.ilike(s),
                KnowledgeItem.content.ilike(s),
                KnowledgeItem.keywords.ilike(s),
                KnowledgeItem.tags.ilike(s)
            ))
        if subsystem:
            q = q.filter(KnowledgeItem.subsystem == subsystem)
        if category:
            q = q.filter(KnowledgeItem.category == category)
        if tag:
            q = q.filter(KnowledgeItem.tags.ilike(f"%{tag}%"))

        order_col = getattr(KnowledgeItem, sort_by)
        q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

        total = q.count()
        items = q.offset(offset).limit(limit).all()
        return items, total
