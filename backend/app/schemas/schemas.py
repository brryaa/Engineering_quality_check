from typing import Optional, Generic, TypeVar, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from app.services.fmea_engine import calculate_rpn, calculate_action_priority

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

# ----------------- Module 1: Program -----------------
class ProgramBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=128)
    platform: str = Field(..., max_length=64)
    phase: str = Field(default="Proto-A", max_length=32)
    sop_date: Optional[str] = Field(default=None, max_length=10)
    lead_engineer: str = Field(..., max_length=64)
    quality_manager: str = Field(..., max_length=64)
    target_market: str = Field(default="Global", max_length=64)
    description: Optional[str] = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Program code cannot be empty.")
        return v.strip().upper()

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Program platform cannot be empty or blank.")
        return v.strip()

    @field_validator("name", "lead_engineer", "quality_manager")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v.strip()

class ProgramCreate(ProgramBase):
    pass

class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None
    phase: Optional[str] = None
    sop_date: Optional[str] = None
    lead_engineer: Optional[str] = None
    quality_manager: Optional[str] = None
    target_market: Optional[str] = None
    description: Optional[str] = None

class ProgramResponse(ProgramBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------- Module 2: Part -----------------
class PartBase(BaseModel):
    program_id: int
    part_number: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., min_length=2, max_length=128)
    subsystem: str = Field(..., max_length=64)
    category: str = Field(..., max_length=64)
    supplier: str = Field(..., max_length=128)
    material: str = Field(..., max_length=128)
    revision: str = Field(default="Rev A.0", max_length=16)
    weight_kg: float = Field(default=1.0, gt=0.0)
    safety_critical: bool = False

    @field_validator("subsystem", "supplier", "material", "revision")
    @classmethod
    def validate_part_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v.strip()

class PartCreate(PartBase):
    pass

class PartUpdate(BaseModel):
    name: Optional[str] = None
    subsystem: Optional[str] = None
    category: Optional[str] = None
    supplier: Optional[str] = None
    material: Optional[str] = None
    revision: Optional[str] = None
    weight_kg: Optional[float] = Field(default=None, gt=0.0)
    safety_critical: Optional[bool] = None

class PartResponse(PartBase):
    id: int
    created_at: datetime
    updated_at: datetime
    program_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------- Module 3: DFMEA -----------------
class DFMEABase(BaseModel):
    part_id: int
    fmea_code: str = Field(..., max_length=64)
    item_function: str
    failure_mode: str
    failure_effect: str
    severity: int = Field(..., ge=1, le=10)
    cause_mechanism: str
    occurrence: int = Field(..., ge=1, le=10)
    prevention_control: str
    detection_control: str
    detection: int = Field(..., ge=1, le=10)
    recommended_action: Optional[str] = None
    action_owner: Optional[str] = None
    target_date: Optional[str] = None
    action_status: str = Field(default="Open", max_length=32)
    post_severity: Optional[int] = Field(default=None, ge=1, le=10)
    post_occurrence: Optional[int] = Field(default=None, ge=1, le=10)
    post_detection: Optional[int] = Field(default=None, ge=1, le=10)

class DFMEACreate(DFMEABase):
    @model_validator(mode="after")
    def validate_action_priority_requirements(self) -> 'DFMEACreate':
        if self.recommended_action is not None and not self.recommended_action.strip():
            raise ValueError("DFMEA recommended_action cannot be empty or whitespace.")
        ap = calculate_action_priority(self.severity, self.occurrence, self.detection)
        if ap == "High" and self.action_status in ("In-Progress", "Completed", "Closed"):
            if not self.recommended_action or not self.recommended_action.strip():
                raise ValueError("DFMEA items with High Action Priority (AP) must specify a non-empty recommended_action when in-progress or closed.")
        return self

class DFMEAUpdate(BaseModel):
    item_function: Optional[str] = None
    failure_mode: Optional[str] = None
    failure_effect: Optional[str] = None
    severity: Optional[int] = Field(default=None, ge=1, le=10)
    cause_mechanism: Optional[str] = None
    occurrence: Optional[int] = Field(default=None, ge=1, le=10)
    prevention_control: Optional[str] = None
    detection_control: Optional[str] = None
    detection: Optional[int] = Field(default=None, ge=1, le=10)
    recommended_action: Optional[str] = None
    action_owner: Optional[str] = None
    target_date: Optional[str] = None
    action_status: Optional[str] = None
    post_severity: Optional[int] = Field(default=None, ge=1, le=10)
    post_occurrence: Optional[int] = Field(default=None, ge=1, le=10)
    post_detection: Optional[int] = Field(default=None, ge=1, le=10)

class DFMEAResponse(DFMEABase):
    id: int
    rpn: int
    action_priority: str
    post_rpn: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    part_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------- Module 4: DVP&R -----------------
class DVPRBase(BaseModel):
    program_id: int
    part_id: int
    plan_code: str = Field(..., max_length=64)
    test_phase: str = Field(..., max_length=32)
    test_name: str = Field(..., max_length=128)
    test_standard: str = Field(..., max_length=128)
    acceptance_criteria: str
    sample_size: int = Field(default=3, ge=1)
    test_facility: str = Field(..., max_length=128)
    planned_start_date: str = Field(..., max_length=10)
    planned_end_date: str = Field(..., max_length=10)
    status: str = Field(default="Planned", max_length=32)
    responsible_engineer: str = Field(..., max_length=64)

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_acceptance_criteria(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Acceptance criteria cannot be empty or whitespace.")
        return v.strip()

class DVPRCreate(DVPRBase):
    pass

class DVPRUpdate(BaseModel):
    test_phase: Optional[str] = None
    test_name: Optional[str] = None
    test_standard: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    sample_size: Optional[int] = Field(default=None, ge=1)
    test_facility: Optional[str] = None
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    status: Optional[str] = None
    responsible_engineer: Optional[str] = None

class DVPRResponse(DVPRBase):
    id: int
    created_at: datetime
    updated_at: datetime
    program_code: Optional[str] = None
    part_number: Optional[str] = None
    test_runs_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


# ----------------- Module 5: Test Run -----------------
class TestRunBase(BaseModel):
    dvpr_id: int
    run_number: str = Field(..., max_length=64)
    sample_id: str = Field(..., max_length=64)
    test_date: str = Field(..., max_length=10)
    test_facility: str = Field(..., max_length=128)
    operator: str = Field(..., max_length=64)
    temperature_c: float = 23.0
    humidity_rh: float = 50.0
    cycles_completed: int = 0
    measurement_data: str = "{}"
    result: str = Field(..., max_length=32)  # Pass, Fail, Marginal
    failure_summary: Optional[str] = None
    report_file_url: Optional[str] = None

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Operator name cannot be empty or whitespace.")
        return v.strip()

class TestRunCreate(TestRunBase):
    pass

class TestRunUpdate(BaseModel):
    operator: Optional[str] = None
    temperature_c: Optional[float] = None
    humidity_rh: Optional[float] = None
    cycles_completed: Optional[int] = None
    measurement_data: Optional[str] = None
    result: Optional[str] = None
    failure_summary: Optional[str] = None
    report_file_url: Optional[str] = None

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Operator name cannot be empty or whitespace.")
        return v.strip() if v else None

class TestRunResponse(TestRunBase):
    id: int
    created_at: datetime
    updated_at: datetime
    plan_code: Optional[str] = None
    test_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------- Module 6: Engineering Issue -----------------
class IssueBase(BaseModel):
    issue_code: str = Field(..., min_length=2, max_length=64)
    program_id: int
    part_id: int
    test_run_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=256)
    severity: str = Field(..., max_length=16)  # S1-Critical, S2-Major, S3-Minor, S4-Cosmetic
    status: str = Field(default="New", max_length=32)
    description: str
    occurrence_phase: str = Field(..., max_length=32)
    containment_action: Optional[str] = None
    assignee: str = Field(..., max_length=64)
    reporter: str = Field(..., max_length=64)
    due_date: str = Field(..., max_length=10)
    closure_date: Optional[str] = None

class IssueCreate(IssueBase):
    @model_validator(mode="after")
    def validate_critical_issue_containment(self) -> 'IssueCreate':
        if self.severity == "S1-Critical" and self.status in ["Containment", "Under-Investigation", "In-Analysis", "Validating", "Closed"]:
            if not self.containment_action or not self.containment_action.strip():
                raise ValueError("S1-Critical issues in Containment or advanced status require a documented containment_action.")
        return self

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    occurrence_phase: Optional[str] = None
    containment_action: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    closure_date: Optional[str] = None
    version_id: Optional[int] = None

class IssueResponse(IssueBase):
    id: int
    version_id: int = 1
    created_at: datetime
    updated_at: datetime
    program_code: Optional[str] = None
    part_number: Optional[str] = None
    has_root_cause: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


# ----------------- Module 7: Root Cause Analysis -----------------
class RootCauseBase(BaseModel):
    issue_id: int
    analysis_method: str = Field(default="5-Why", max_length=32)
    direct_cause: str
    why_1: Optional[str] = None
    why_2: Optional[str] = None
    why_3: Optional[str] = None
    why_4: Optional[str] = None
    why_5: Optional[str] = None
    systemic_root_cause: str
    fishbone_man: Optional[str] = None
    fishbone_machine: Optional[str] = None
    fishbone_material: Optional[str] = None
    fishbone_method: Optional[str] = None
    fishbone_measurement: Optional[str] = None
    fishbone_environment: Optional[str] = None
    verification_method: str
    verification_result: str = Field(default="Pending", max_length=32)
    analyst: str = Field(..., max_length=64)
    analyzed_at: str = Field(..., max_length=10)

    @field_validator("analyst")
    @classmethod
    def validate_analyst(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Analyst name cannot be blank or whitespace.")
        return v.strip()

    @field_validator("analyzed_at")
    @classmethod
    def validate_analyzed_at(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Analyzed date cannot be blank.")
        try:
            datetime.strptime(v.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Analyzed date must be valid ISO format YYYY-MM-DD, got {v}")
        return v.strip()

    @field_validator("systemic_root_cause")
    @classmethod
    def validate_systemic_root_cause(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("systemic_root_cause cannot be empty or whitespace.")
        return v.strip()

class RootCauseCreate(RootCauseBase):
    pass

class RootCauseUpdate(BaseModel):
    analysis_method: Optional[str] = None
    direct_cause: Optional[str] = None
    why_1: Optional[str] = None
    why_2: Optional[str] = None
    why_3: Optional[str] = None
    why_4: Optional[str] = None
    why_5: Optional[str] = None
    systemic_root_cause: Optional[str] = None
    fishbone_man: Optional[str] = None
    fishbone_machine: Optional[str] = None
    fishbone_material: Optional[str] = None
    fishbone_method: Optional[str] = None
    fishbone_measurement: Optional[str] = None
    fishbone_environment: Optional[str] = None
    verification_method: Optional[str] = None
    verification_result: Optional[str] = None
    analyst: Optional[str] = None
    analyzed_at: Optional[str] = None

class RootCauseResponse(RootCauseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    issue_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------- Module 8: Engineering Change -----------------
class ChangeBase(BaseModel):
    change_code: str = Field(..., max_length=64)
    program_id: int
    part_id: int
    issue_id: Optional[int] = None
    title: str = Field(..., max_length=256)
    change_type: str = Field(..., max_length=32)
    reason: str
    pre_change_rev: str = Field(..., max_length=16)
    post_change_rev: str = Field(..., max_length=16)
    cost_impact_rmb: float = 0.0
    weight_impact_kg: float = 0.0
    tooling_lead_weeks: int = 4
    requires_homologation: bool = False
    requires_dvp_retest: bool = True
    approval_status: str = Field(default="Draft", max_length=32)
    initiator: str = Field(..., max_length=64)
    approver: Optional[str] = None
    approval_date: Optional[str] = None
    implementation_date: Optional[str] = None

class ChangeCreate(ChangeBase):
    pass

class ChangeUpdate(BaseModel):
    title: Optional[str] = None
    change_type: Optional[str] = None
    reason: Optional[str] = None
    pre_change_rev: Optional[str] = None
    post_change_rev: Optional[str] = None
    cost_impact_rmb: Optional[float] = None
    weight_impact_kg: Optional[float] = None
    tooling_lead_weeks: Optional[int] = None
    requires_homologation: Optional[bool] = None
    requires_dvp_retest: Optional[bool] = None
    approval_status: Optional[str] = None
    approver: Optional[str] = None
    approval_date: Optional[str] = None
    implementation_date: Optional[str] = None
    version_id: Optional[int] = None

class ChangeResponse(ChangeBase):
    id: int
    version_id: int = 1
    created_at: datetime
    updated_at: datetime
    program_code: Optional[str] = None
    part_number: Optional[str] = None
    issue_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------- Module 9: Quality Dashboard Stats -----------------
class QualityDashboardStats(BaseModel):
    total_programs: int
    total_parts: int
    total_dfmeas: int
    total_dvprs: int
    total_test_runs: int
    total_issues: int
    total_changes: int
    
    # DFMEA RPN & AP distribution
    dfmea_high_ap_count: int
    dfmea_medium_ap_count: int
    dfmea_low_ap_count: int
    dfmea_high_rpn_count: int  # RPN >= 100
    
    # DVP&R Burndown
    dvpr_status_counts: dict[str, int]
    
    # Test Run Pass Rate
    test_run_pass_rate_pct: float
    test_run_result_counts: dict[str, int]
    
    # Issue Metrics
    issue_severity_counts: dict[str, int]
    issue_status_counts: dict[str, int]
    open_critical_issues_count: int
    
    # Engineering Change Impact
    total_change_cost_impact_rmb: float
    changes_by_status: dict[str, int]
    
    # Subsystem Health Ranking
    subsystem_health: list[dict[str, Any]]


# ----------------- Module 10: Knowledge Retrieval -----------------
class KnowledgeItemBase(BaseModel):
    doc_code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=256)
    subsystem: str = Field(..., max_length=64)
    category: str = Field(..., max_length=32)
    tags: str
    content: str
    keywords: str
    source_reference: Optional[str] = None
    applicable_programs: Optional[str] = None
    author: str = Field(..., max_length=64)

class KnowledgeItemCreate(KnowledgeItemBase):
    pass

class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    subsystem: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[str] = None
    source_reference: Optional[str] = None
    applicable_programs: Optional[str] = None
    author: Optional[str] = None

class KnowledgeItemResponse(KnowledgeItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------- User & Authentication Schemas -----------------
class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., min_length=5, max_length=128)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=128)
    role: str = Field(default="viewer", max_length=32)
    department: str = Field(default="Engineering Quality", max_length=64)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = {"admin", "quality_lead", "design_eng", "design_engineer", "auditor", "viewer"}
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {sorted(valid_roles)}, got '{v}'")
        if v == "design_engineer":
            return "design_eng"
        if v == "viewer":
            return "auditor"
        return v


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    department: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_minutes: int
    user: UserResponse
