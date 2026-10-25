from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    platform = Column(String(64), nullable=False)  # EV-800V, PHEV-Modular, etc.
    phase = Column(String(32), nullable=False, default="Proto-A")  # Concept, Proto-A, Pre-series-B, PPAP, SOP
    sop_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    lead_engineer = Column(String(64), nullable=False)
    quality_manager = Column(String(64), nullable=False)
    target_market = Column(String(64), nullable=False, default="Global")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    parts = relationship("Part", back_populates="program", cascade="all, delete-orphan")
    dvprs = relationship("DVPR", back_populates="program", cascade="all, delete-orphan")
    issues = relationship("EngineeringIssue", back_populates="program")
    changes = relationship("EngineeringChange", back_populates="program")


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    part_number = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    subsystem = Column(String(64), nullable=False, index=True)
    category = Column(String(64), nullable=False)  # Mechanical, Elastomer, Glass, Electro-Mech, etc.
    supplier = Column(String(128), nullable=False)
    material = Column(String(128), nullable=False)
    revision = Column(String(16), nullable=False, default="Rev A.0")
    weight_kg = Column(Float, nullable=False, default=1.0)
    safety_critical = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    program = relationship("Program", back_populates="parts")
    dfmeas = relationship("DFMEA", back_populates="part", cascade="all, delete-orphan")
    dvprs = relationship("DVPR", back_populates="part", cascade="all, delete-orphan")
    issues = relationship("EngineeringIssue", back_populates="part")
    changes = relationship("EngineeringChange", back_populates="part")


class DFMEA(Base):
    __tablename__ = "dfmeas"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id", ondelete="CASCADE"), nullable=False, index=True)
    fmea_code = Column(String(64), unique=True, nullable=False, index=True)
    item_function = Column(Text, nullable=False)
    failure_mode = Column(Text, nullable=False)
    failure_effect = Column(Text, nullable=False)
    severity = Column(Integer, nullable=False)  # 1-10
    cause_mechanism = Column(Text, nullable=False)
    occurrence = Column(Integer, nullable=False)  # 1-10
    prevention_control = Column(Text, nullable=False)
    detection_control = Column(Text, nullable=False)
    detection = Column(Integer, nullable=False)  # 1-10
    rpn = Column(Integer, nullable=False)  # S * O * D
    action_priority = Column(String(16), nullable=False, default="Low")  # High, Medium, Low (AIAG-VDA)
    recommended_action = Column(Text, nullable=True)
    action_owner = Column(String(64), nullable=True)
    target_date = Column(String(10), nullable=True)
    action_status = Column(String(32), default="Open")  # Open, In Progress, Implemented, Verified, Closed
    post_severity = Column(Integer, nullable=True)
    post_occurrence = Column(Integer, nullable=True)
    post_detection = Column(Integer, nullable=True)
    post_rpn = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    part = relationship("Part", back_populates="dfmeas")


class DVPR(Base):
    __tablename__ = "dvprs"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    part_id = Column(Integer, ForeignKey("parts.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_code = Column(String(64), unique=True, nullable=False, index=True)
    test_phase = Column(String(32), nullable=False)  # DV-A, DV-B, PV-C, SOP-Confirm
    test_name = Column(String(128), nullable=False)
    test_standard = Column(String(128), nullable=False)  # QC/T 627, ISO 20653, GMW 14147, etc.
    acceptance_criteria = Column(Text, nullable=False)
    sample_size = Column(Integer, nullable=False, default=3)
    test_facility = Column(String(128), nullable=False)
    planned_start_date = Column(String(10), nullable=False)
    planned_end_date = Column(String(10), nullable=False)
    status = Column(String(32), nullable=False, default="Planned")  # Planned, In Progress, Passed, Failed, Blocked
    responsible_engineer = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    program = relationship("Program", back_populates="dvprs")
    part = relationship("Part", back_populates="dvprs")
    test_runs = relationship("TestRun", back_populates="dvpr", cascade="all, delete-orphan")


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    dvpr_id = Column(Integer, ForeignKey("dvprs.id", ondelete="CASCADE"), nullable=False, index=True)
    run_number = Column(String(64), unique=True, nullable=False, index=True)
    sample_id = Column(String(64), nullable=False)
    test_date = Column(String(10), nullable=False)
    test_facility = Column(String(128), nullable=False)
    operator = Column(String(64), nullable=False)
    temperature_c = Column(Float, nullable=False, default=23.0)
    humidity_rh = Column(Float, nullable=False, default=50.0)
    cycles_completed = Column(Integer, nullable=False, default=0)
    measurement_data = Column(Text, nullable=False, default="{}")  # JSON String
    result = Column(String(32), nullable=False)  # Pass, Fail, Marginal
    failure_summary = Column(Text, nullable=True)
    report_file_url = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    dvpr = relationship("DVPR", back_populates="test_runs")
    issues = relationship("EngineeringIssue", back_populates="test_run")


class EngineeringIssue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    issue_code = Column(String(64), unique=True, nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=True, index=True)
    title = Column(String(256), nullable=False)
    severity = Column(String(16), nullable=False)  # S1-Critical, S2-Major, S3-Minor, S4-Cosmetic
    status = Column(String(32), nullable=False, default="New")  # New, Investigating, Containment, RootCauseVerified, ActionImplemented, ValidationPass, Closed, Rejected
    description = Column(Text, nullable=False)
    occurrence_phase = Column(String(32), nullable=False)  # Proto-Build, DV-Testing, PV-Trial, Pre-SOP, Field-Feedback
    containment_action = Column(Text, nullable=True)
    assignee = Column(String(64), nullable=False)
    reporter = Column(String(64), nullable=False)
    due_date = Column(String(10), nullable=False)
    closure_date = Column(String(10), nullable=True)
    version_id = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    program = relationship("Program", back_populates="issues")
    part = relationship("Part", back_populates="issues")
    test_run = relationship("TestRun", back_populates="issues")
    root_cause = relationship("RootCauseAnalysis", back_populates="issue", uselist=False, cascade="all, delete-orphan")
    changes = relationship("EngineeringChange", back_populates="issue")


class RootCauseAnalysis(Base):
    __tablename__ = "root_causes"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    analysis_method = Column(String(32), nullable=False, default="5-Why")  # 5-Why, Ishikawa-Fishbone, FTA
    direct_cause = Column(Text, nullable=False)
    why_1 = Column(Text, nullable=True)
    why_2 = Column(Text, nullable=True)
    why_3 = Column(Text, nullable=True)
    why_4 = Column(Text, nullable=True)
    why_5 = Column(Text, nullable=True)
    systemic_root_cause = Column(Text, nullable=False)
    fishbone_man = Column(Text, nullable=True)
    fishbone_machine = Column(Text, nullable=True)
    fishbone_material = Column(Text, nullable=True)
    fishbone_method = Column(Text, nullable=True)
    fishbone_measurement = Column(Text, nullable=True)
    fishbone_environment = Column(Text, nullable=True)
    verification_method = Column(Text, nullable=False)
    verification_result = Column(String(32), nullable=False, default="Pending")  # Confirmed, Rejected, Pending
    analyst = Column(String(64), nullable=False)
    analyzed_at = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    issue = relationship("EngineeringIssue", back_populates="root_cause")


class EngineeringChange(Base):
    __tablename__ = "changes"

    id = Column(Integer, primary_key=True, index=True)
    change_code = Column(String(64), unique=True, nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=True, index=True)
    title = Column(String(256), nullable=False)
    change_type = Column(String(32), nullable=False)  # Design-Mod, Material-Change, Tooling-Tune, Supplier-Transfer, Tolerance-Relaxation
    reason = Column(Text, nullable=False)
    pre_change_rev = Column(String(16), nullable=False)
    post_change_rev = Column(String(16), nullable=False)
    cost_impact_rmb = Column(Float, nullable=False, default=0.0)
    weight_impact_kg = Column(Float, nullable=False, default=0.0)
    tooling_lead_weeks = Column(Integer, nullable=False, default=4)
    requires_homologation = Column(Boolean, default=False, nullable=False)
    requires_dvp_retest = Column(Boolean, default=True, nullable=False)
    approval_status = Column(String(32), nullable=False, default="Draft")  # Draft, Review-Eng, Review-CostTooling, Approved, Rejected, Implemented
    initiator = Column(String(64), nullable=False)
    approver = Column(String(64), nullable=True)
    approval_date = Column(String(10), nullable=True)
    implementation_date = Column(String(10), nullable=True)
    version_id = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    program = relationship("Program", back_populates="changes")
    part = relationship("Part", back_populates="changes")
    issue = relationship("EngineeringIssue", back_populates="changes")


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    doc_code = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=False, index=True)
    subsystem = Column(String(64), nullable=False, index=True)
    category = Column(String(32), nullable=False, index=True)  # Standard-Spec, Lesson-Learned, Failure-Case, Best-Practice, Design-Guideline
    tags = Column(String(256), nullable=False)  # comma separated
    content = Column(Text, nullable=False)
    keywords = Column(Text, nullable=False)
    source_reference = Column(String(128), nullable=True)
    applicable_programs = Column(String(128), nullable=True)
    author = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


# Additional compound indexes for high performance query & analytics
Index("ix_dfmea_part_rpn", DFMEA.part_id, DFMEA.rpn)
Index("ix_dvpr_prog_status", DVPR.program_id, DVPR.status)
Index("ix_testrun_dvpr_res", TestRun.dvpr_id, TestRun.result)
Index("ix_issue_prog_sev_stat", EngineeringIssue.program_id, EngineeringIssue.severity, EngineeringIssue.status)
Index("ix_change_prog_status", EngineeringChange.program_id, EngineeringChange.approval_status)
