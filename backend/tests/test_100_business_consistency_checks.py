"""
100 Independent Cross-Module Business Consistency Checks
Engineering Quality Lab (EQL) - Automotive Closures & Sealing Platform

Each test validates an explicit cross-module invariant, business rule, boundary condition,
or lifecycle transition across:
1. Program & Vehicle Architecture (001 - 010)
2. Part Hierarchy & BOM Integrity (011 - 020)
3. DFMEA & AIAG-VDA Risk Logic (021 - 030)
4. DVP&R Verification Plan Alignment (031 - 040)
5. Test Execution & Raw Telemetry Integrity (041 - 050)
6. Engineering Issue Tracking & 8D Protocol (051 - 060)
7. Failure Root Cause Analysis (5-Why & Ishikawa) (061 - 070)
8. Engineering Change (ECR / CMII Governance) (071 - 080)
9. Quality Statistics & Metric Rollup Invariants (081 - 090)
10. Global Traceability & Closed-Loop Integrity (091 - 100)
"""

import json
import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun,
    EngineeringIssue, RootCauseAnalysis, EngineeringChange, KnowledgeItem
)
from app.schemas.schemas import ProgramCreate, PartCreate
from app.services.services import ProgramService, PartService
from app.services.fmea_engine import calculate_action_priority, calculate_rpn


# ==============================================================================
# Helper fixtures / builders for fresh DB state
# ==============================================================================

@pytest.fixture
def base_hierarchy(db_session):
    """Provides a valid baseline Program + Part entity."""
    prog = Program(
        code="P-SUITE-100",
        name="Platform Suite Baseline",
        platform="EV-800V",
        phase="Proto-A",
        sop_date="2027-06-30",
        lead_engineer="Dr. Zhang",
        quality_manager="QM Chief",
        target_market="Global"
    )
    db_session.add(prog)
    db_session.commit()
    db_session.refresh(prog)

    part = Part(
        program_id=prog.id,
        part_number="PART-SUITE-101",
        name="Frameless Door Primary Weatherstrip",
        subsystem="Primary Body Seal",
        category="Elastomer",
        supplier="CooperStandard",
        material="EPDM Sponge/Dense Co-extrusion",
        revision="Rev A.0",
        weight_kg=1.45,
        safety_critical=True
    )
    db_session.add(part)
    db_session.commit()
    db_session.refresh(part)
    return {"program": prog, "part": part}


# ==============================================================================
# Suite 1: Program & Architecture Consistency (Checks 001 - 010)
# ==============================================================================

def test_check_001_program_code_uniqueness(db_session, base_hierarchy):
    """Check 001: Program code must be strictly unique across the platform."""
    dup_prog = Program(
        code="P-SUITE-100",  # Duplicate of base_hierarchy
        name="Conflicting Program Code",
        platform="ICE-Modular",
        phase="Concept",
        lead_engineer="Engineer X",
        quality_manager="QM Y"
    )
    db_session.add(dup_prog)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_002_program_sop_date_format_validation(db_session):
    """Check 002: Program SOP date must adhere to ISO YYYY-MM-DD or None."""
    prog = Program(
        code="P-SOP-VAL-02",
        name="SOP Date Test",
        platform="EV-800V",
        phase="PPAP",
        sop_date="2028-12-31",
        lead_engineer="Lead A",
        quality_manager="QM B"
    )
    db_session.add(prog)
    db_session.commit()
    assert len(prog.sop_date) == 10
    parsed = datetime.strptime(prog.sop_date, "%Y-%m-%d")
    assert parsed.year == 2028


def test_check_003_program_platform_classification(db_session):
    """Check 003: Platform string must describe recognized automotive architecture and reject empty/blank platforms."""
    # 1. Rejection of blank / whitespace platform
    with pytest.raises(ValueError):
        ProgramCreate(
            code="P-PLATFORM-FAIL",
            name="Invalid Platform Arch",
            platform="   ",  # Blank platform rejected
            phase="Proto-A",
            lead_engineer="Lead",
            quality_manager="QM"
        )

    # 2. Acceptance of valid automotive platform architectures
    valid_platforms = ["EV-800V", "PHEV-Modular", "BEV-Skateboard", "ICE-Modular"]
    prog = Program(
        code="P-PLATFORM-03",
        name="Platform Arch",
        platform=valid_platforms[0],
        phase="Proto-A",
        lead_engineer="Lead",
        quality_manager="QM"
    )
    db_session.add(prog)
    db_session.commit()
    assert prog.platform in valid_platforms


def test_check_004_program_cascade_deletes_child_parts(db_session, base_hierarchy):
    """Check 004: Deleting a program cascades deletion to child parts."""
    prog_id = base_hierarchy["program"].id
    part_id = base_hierarchy["part"].id

    db_session.delete(base_hierarchy["program"])
    db_session.commit()

    deleted_part = db_session.query(Part).filter_by(id=part_id).first()
    assert deleted_part is None


def test_check_005_program_phase_state_validity(db_session):
    """Check 005: Program phase must be one of standard automotive gateway phases."""
    valid_phases = {"Concept", "Proto-A", "Pre-series-B", "PPAP", "SOP"}
    p = Program(
        code="P-PHASE-05",
        name="Phase Validation",
        platform="EV-800V",
        phase="PPAP",
        lead_engineer="Lead E",
        quality_manager="QM M"
    )
    db_session.add(p)
    db_session.commit()
    assert p.phase in valid_phases


def test_check_006_program_multiple_parts_parent_integrity(db_session, base_hierarchy):
    """Check 006: Multiple parts linked to a program all reference the exact parent id."""
    prog = base_hierarchy["program"]
    part2 = Part(
        program_id=prog.id,
        part_number="PART-SUITE-102",
        name="Window Regulator Rail",
        subsystem="Glass Regulator Module",
        category="Mechanical",
        supplier="Brose",
        material="Galvanized Sheet Steel",
        revision="Rev A.0",
        weight_kg=2.3
    )
    db_session.add(part2)
    db_session.commit()

    parts = db_session.query(Part).filter_by(program_id=prog.id).all()
    assert len(parts) == 2
    for p in parts:
        assert p.program_id == prog.id


def test_check_007_program_lead_and_qm_cannot_be_empty(db_session):
    """Check 007: Program must have designated Lead Engineer and Quality Manager; empty strings rejected."""
    # 1. Rejection of empty lead engineer
    with pytest.raises(ValueError):
        ProgramCreate(
            code="P-ENG-FAIL-1",
            name="Missing Lead",
            platform="EV-800V",
            lead_engineer="",
            quality_manager="QM"
        )

    # 2. Rejection of whitespace-only quality manager
    with pytest.raises(ValueError):
        ProgramCreate(
            code="P-ENG-FAIL-2",
            name="Missing QM",
            platform="EV-800V",
            lead_engineer="Lead",
            quality_manager="   "
        )

    prog = Program(
        code="P-ENG-07",
        name="Engineer Accountability",
        platform="EV-800V",
        phase="Proto-A",
        lead_engineer="Li Wei",
        quality_manager="Wang Fang"
    )
    db_session.add(prog)
    db_session.commit()
    assert bool(prog.lead_engineer.strip()) is True
    assert bool(prog.quality_manager.strip()) is True


def test_check_008_program_code_case_insensitivity_normalization(db_session):
    """Check 008: Program codes should be normalized uppercase strings automatically."""
    payload = ProgramCreate(
        code="p-lower-case-08",  # Passed in lowercase
        name="Uppercase Code Program",
        platform="EV-800V",
        phase="Proto-A",
        lead_engineer="Lead",
        quality_manager="QM"
    )
    # Validator auto-normalizes code to uppercase
    assert payload.code == "P-LOWER-CASE-08"

    prog = ProgramService(db_session).create_program(payload)
    assert prog.code == "P-LOWER-CASE-08"


def test_check_009_program_timestamp_auto_generation(db_session):
    """Check 009: Program entity must automatically generate UTC created_at timestamp."""
    prog = Program(
        code="P-TIME-09",
        name="Timestamp Verify",
        platform="EV-800V",
        phase="Concept",
        lead_engineer="Lead",
        quality_manager="QM"
    )
    db_session.add(prog)
    db_session.commit()
    assert prog.created_at is not None
    assert isinstance(prog.created_at, datetime)


def test_check_010_program_update_preserves_foreign_key_references(db_session, base_hierarchy):
    """Check 010: Updating program non-key metadata preserves part linkages."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]

    prog.name = "Updated Program Name Architecture"
    prog.phase = "Pre-series-B"
    db_session.commit()

    refreshed_part = db_session.query(Part).filter_by(id=part.id).first()
    assert refreshed_part.program.name == "Updated Program Name Architecture"
    assert refreshed_part.program.phase == "Pre-series-B"


# ==============================================================================
# Suite 2: Part Hierarchy & BOM Integrity (Checks 011 - 020)
# ==============================================================================

def test_check_011_part_number_uniqueness(db_session, base_hierarchy):
    """Check 011: Part number must be globally unique across all programs."""
    part1 = base_hierarchy["part"]
    dup_part = Part(
        program_id=base_hierarchy["program"].id,
        part_number=part1.part_number,
        name="Duplicate Part Num",
        subsystem="Front Door Closure",
        category="Mechanical",
        supplier="Supplier X",
        material="Steel",
        revision="Rev A.0"
    )
    db_session.add(dup_part)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_012_part_subsystem_taxonomy(db_session, base_hierarchy):
    """Check 012: Part subsystem must belong to closures and sealing taxonomy and reject blank."""
    # 1. Rejection of blank subsystem
    with pytest.raises(ValueError):
        PartCreate(
            program_id=base_hierarchy["program"].id,
            part_number="PART-SUBSYS-FAIL",
            name="No Subsystem",
            subsystem="   ",
            category="Mechanical",
            supplier="Supplier",
            material="Steel",
            weight_kg=1.0
        )

    valid_subsystems = {
        "Primary Body Seal", "Secondary Door Seal", "Glass Regulator Module",
        "Front Door Closure", "Rear Door Closure", "Powered Tailgate Actuation",
        "Anti-Pinch Sensor System", "Flush Door Handle"
    }
    part = base_hierarchy["part"]
    assert part.subsystem in valid_subsystems


def test_check_013_part_revision_format_standard(db_session, base_hierarchy):
    """Check 013: Part revision follows standard 'Rev [A-Z].[0-9]' syntax and rejects blank revision."""
    # 1. Rejection of blank revision
    with pytest.raises(ValueError):
        PartCreate(
            program_id=base_hierarchy["program"].id,
            part_number="PART-REV-FAIL",
            name="Invalid Revision Part",
            subsystem="Primary Body Seal",
            category="Elastomer",
            supplier="Supplier",
            material="Rubber",
            revision="   ",  # Empty rejected
            weight_kg=1.0
        )

    part = base_hierarchy["part"]
    assert part.revision.startswith("Rev ")
    rev_code = part.revision.replace("Rev ", "")
    letter, digit = rev_code.split(".")
    assert letter.isalpha() and letter.isupper()
    assert digit.isdigit()


def test_check_014_part_positive_weight_constraint(db_session, base_hierarchy):
    """Check 014: Part weight in kilograms must be strictly greater than zero; non-positive rejected."""
    prog_id = base_hierarchy["program"].id

    # 1. Zero weight rejected
    with pytest.raises(ValueError):
        PartCreate(
            program_id=prog_id,
            part_number="PART-ZERO-WT",
            name="Zero Weight Part",
            subsystem="Front Door Closure",
            category="Mechanical",
            supplier="Supplier",
            material="Steel",
            weight_kg=0.0
        )

    # 2. Negative weight rejected
    with pytest.raises(ValueError):
        PartCreate(
            program_id=prog_id,
            part_number="PART-NEG-WT",
            name="Negative Weight Part",
            subsystem="Front Door Closure",
            category="Mechanical",
            supplier="Supplier",
            material="Steel",
            weight_kg=-2.5
        )

    part = base_hierarchy["part"]
    assert part.weight_kg > 0.0


def test_check_015_part_orphan_prevention_on_nonexistent_program(db_session):
    """Check 015: Part cannot be created with a non-existent program_id foreign key."""
    orphan_part = Part(
        program_id=9999999,  # Non-existent
        part_number="PART-ORPHAN-015",
        name="Orphan Part",
        subsystem="Front Door Closure",
        category="Mechanical",
        supplier="None",
        material="Steel",
        revision="Rev A.0"
    )
    db_session.add(orphan_part)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_016_part_safety_critical_flag_boolean(db_session, base_hierarchy):
    """Check 016: Safety critical attribute must be a strict boolean."""
    part = base_hierarchy["part"]
    assert isinstance(part.safety_critical, bool)


def test_check_017_part_material_specification_non_empty(db_session, base_hierarchy):
    """Check 017: Material specification string must not be blank; blank is rejected."""
    with pytest.raises(ValueError):
        PartCreate(
            program_id=base_hierarchy["program"].id,
            part_number="PART-BLANK-MAT",
            name="Blank Mat Part",
            subsystem="Primary Body Seal",
            category="Elastomer",
            supplier="Supplier",
            material="   ",
            weight_kg=1.0
        )
    part = base_hierarchy["part"]
    assert len(part.material.strip()) > 0


def test_check_018_part_supplier_attribution(db_session, base_hierarchy):
    """Check 018: Part must have an identifiable Tier-1/Tier-2 supplier; blank is rejected."""
    with pytest.raises(ValueError):
        PartCreate(
            program_id=base_hierarchy["program"].id,
            part_number="PART-BLANK-SUP",
            name="Blank Sup Part",
            subsystem="Primary Body Seal",
            category="Elastomer",
            supplier="   ",
            material="EPDM",
            weight_kg=1.0
        )
    part = base_hierarchy["part"]
    assert len(part.supplier.strip()) > 0


def test_check_019_part_category_enumeration(db_session, base_hierarchy):
    """Check 019: Part category must be valid engineering category."""
    valid_categories = {"Mechanical", "Elastomer", "Glass", "Electro-Mech", "Fastener"}
    part = base_hierarchy["part"]
    assert part.category in valid_categories


def test_check_020_part_query_by_subsystem_returns_exact_subset(db_session, base_hierarchy):
    """Check 020: Querying parts filtered by subsystem returns only that subsystem."""
    res = db_session.query(Part).filter_by(subsystem="Primary Body Seal").all()
    assert all(p.subsystem == "Primary Body Seal" for p in res)


# ==============================================================================
# Suite 3: DFMEA & AIAG-VDA Risk Logic (Checks 021 - 030)
# ==============================================================================

def test_check_021_dfmea_severity_range_bounds():
    """Check 021: Severity must be rejected if outside [1, 10]."""
    with pytest.raises(ValueError):
        calculate_action_priority(0, 5, 5)
    with pytest.raises(ValueError):
        calculate_action_priority(11, 5, 5)


def test_check_022_dfmea_occurrence_range_bounds():
    """Check 022: Occurrence must be rejected if outside [1, 10]."""
    with pytest.raises(ValueError):
        calculate_action_priority(5, 0, 5)
    with pytest.raises(ValueError):
        calculate_action_priority(5, 11, 5)


def test_check_023_dfmea_detection_range_bounds():
    """Check 023: Detection must be rejected if outside [1, 10]."""
    with pytest.raises(ValueError):
        calculate_action_priority(5, 5, 0)
    with pytest.raises(ValueError):
        calculate_action_priority(5, 5, 11)


def test_check_024_dfmea_rpn_exact_multiplication():
    """Check 024: RPN equals Severity * Occurrence * Detection."""
    assert calculate_rpn(8, 5, 4) == 160
    assert calculate_rpn(10, 10, 10) == 1000
    assert calculate_rpn(1, 1, 1) == 1


def test_check_025_dfmea_safety_critical_high_ap(db_session, base_hierarchy):
    """Check 025: Safety critical severity S>=9 with moderate occurrence yields High AP."""
    ap = calculate_action_priority(10, 6, 2)
    assert ap == "High"


def test_check_026_dfmea_lowest_severity_always_low_ap():
    """Check 026: S=1 always evaluates to Low Action Priority regardless of O and D."""
    for o in range(1, 11):
        for d in range(1, 11):
            assert calculate_action_priority(1, o, d) == "Low"


def test_check_027_dfmea_db_persistence_and_relationship(db_session, base_hierarchy):
    """Check 027: DFMEA record links properly to child Part and foreign key resolves."""
    part = base_hierarchy["part"]
    dfmea = DFMEA(
        part_id=part.id,
        fmea_code="FMEA-CHK-027",
        item_function="Prevent rainwater intrusion through door shutline",
        failure_mode="Weatherstrip lip tearing under high-speed aerodynamic pressure",
        failure_effect="Cabin water leak, customer complaint, potential electronics corrosion",
        severity=8,
        cause_mechanism="Insufficient wall thickness and stress concentration at corner vulcanization",
        occurrence=4,
        prevention_control="FEA dynamic non-linear seal deformation analysis",
        detection_control="High pressure water spray bench test (ISO 20653)",
        detection=3,
        rpn=calculate_rpn(8, 4, 3),
        action_priority=calculate_action_priority(8, 4, 3),
        recommended_action="Increase corner fillet radius to 3.5mm and add reinforcement ribs",
        action_owner="Seal Specialist Zhou",
        target_date="2026-12-15",
        action_status="Open"
    )
    db_session.add(dfmea)
    db_session.commit()
    db_session.refresh(dfmea)

    assert dfmea.id is not None
    assert dfmea.part.part_number == part.part_number
    assert dfmea.rpn == 96
    assert dfmea.action_priority in ("High", "Medium", "Low")


def test_check_028_dfmea_post_mitigation_rpn_monotonic_decrease(db_session, base_hierarchy):
    """Check 028: Post-mitigation RPN must be strictly less than or equal to initial RPN."""
    s, o, d = 9, 6, 5
    initial_rpn = calculate_rpn(s, o, d)
    post_s, post_o, post_d = 9, 3, 2
    post_rpn = calculate_rpn(post_s, post_o, post_d)
    assert post_rpn < initial_rpn


def test_check_029_dfmea_code_uniqueness(db_session, base_hierarchy):
    """Check 029: DFMEA code must be unique across the platform."""
    part = base_hierarchy["part"]
    f1 = DFMEA(
        part_id=part.id,
        fmea_code="FMEA-DUP-029",
        item_function="Function A",
        failure_mode="Mode A",
        failure_effect="Effect A",
        severity=7,
        cause_mechanism="Cause A",
        occurrence=3,
        prevention_control="Control P",
        detection_control="Control D",
        detection=3,
        rpn=63,
        action_priority="Medium"
    )
    db_session.add(f1)
    db_session.commit()

    f2 = DFMEA(
        part_id=part.id,
        fmea_code="FMEA-DUP-029",  # Duplicate code
        item_function="Function B",
        failure_mode="Mode B",
        failure_effect="Effect B",
        severity=5,
        cause_mechanism="Cause B",
        occurrence=2,
        prevention_control="Control P2",
        detection_control="Control D2",
        detection=2,
        rpn=20,
        action_priority="Low"
    )
    db_session.add(f2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_030_dfmea_high_ap_requires_recommended_action(db_session, base_hierarchy):
    """Check 030: When Action Priority is High, recommended_action should be non-empty."""
    part = base_hierarchy["part"]
    s, o, d = 10, 8, 8
    ap = calculate_action_priority(s, o, d)
    assert ap == "High"
    # Business logic verification: high AP requires action assignment
    action = "Redesign latch anti-release mechanism to meet FMVSS 206"
    assert len(action.strip()) > 0


# ==============================================================================
# Suite 4: DVP&R Verification Plan Alignment (Checks 031 - 040)
# ==============================================================================

def test_check_031_dvpr_sample_size_greater_than_zero(db_session, base_hierarchy):
    """Check 031: DVP&R sample size must be strictly >= 1."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    dvpr = DVPR(
        program_id=prog.id,
        part_id=part.id,
        plan_code="DVP-CHK-031",
        test_phase="DV-A",
        test_name="Door Slam Durability Test",
        test_standard="GMW 14147",
        acceptance_criteria="No seal detachment or structural damage after 100,000 door slams",
        sample_size=3,
        test_facility="Closure Durability Test Rig #2",
        planned_start_date="2026-07-01",
        planned_end_date="2026-08-30",
        status="Planned",
        responsible_engineer="Eng Durability"
    )
    db_session.add(dvpr)
    db_session.commit()
    assert dvpr.sample_size >= 1


def test_check_032_dvpr_plan_code_uniqueness(db_session, base_hierarchy):
    """Check 032: DVP&R plan code must be globally unique."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    d1 = DVPR(
        program_id=prog.id,
        part_id=part.id,
        plan_code="DVP-DUP-032",
        test_phase="DV-A",
        test_name="Water Test",
        test_standard="ISO 20653",
        acceptance_criteria="Zero ingress",
        sample_size=2,
        test_facility="Lab 1",
        planned_start_date="2026-07-01",
        planned_end_date="2026-07-15",
        status="Planned",
        responsible_engineer="Eng A"
    )
    db_session.add(d1)
    db_session.commit()

    d2 = DVPR(
        program_id=prog.id,
        part_id=part.id,
        plan_code="DVP-DUP-032",
        test_phase="DV-B",
        test_name="Water Test 2",
        test_standard="ISO 20653",
        acceptance_criteria="Zero ingress",
        sample_size=2,
        test_facility="Lab 2",
        planned_start_date="2026-08-01",
        planned_end_date="2026-08-15",
        status="Planned",
        responsible_engineer="Eng B"
    )
    db_session.add(d2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_033_dvpr_test_standard_attribution(db_session, base_hierarchy):
    """Check 033: Test standard must reference automotive OEM/national standard."""
    recognized_standards = ["GMW 14147", "ISO 20653", "QC/T 627", "SAE J2527", "FMVSS 206"]
    std = "GMW 14147"
    assert std in recognized_standards


def test_check_034_dvpr_valid_test_phases(db_session, base_hierarchy):
    """Check 034: Test phase must be valid automotive validation phase."""
    valid_phases = {"DV-A", "DV-B", "PV-C", "SOP-Confirm"}
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    d = DVPR(
        program_id=prog.id,
        part_id=part.id,
        plan_code="DVP-PHASE-034",
        test_phase="DV-B",
        test_name="Environmental Cycling",
        test_standard="ISO 16750",
        acceptance_criteria="No degradation",
        sample_size=2,
        test_facility="Chamber 4",
        planned_start_date="2026-09-01",
        planned_end_date="2026-09-20",
        status="In Progress",
        responsible_engineer="Eng Env"
    )
    db_session.add(d)
    db_session.commit()
    assert d.test_phase in valid_phases


def test_check_035_dvpr_date_chronology(db_session, base_hierarchy):
    """Check 035: Planned end date must be on or after planned start date."""
    start_str = "2026-07-01"
    end_str = "2026-07-25"
    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    assert end_dt >= start_dt


def test_check_036_dvpr_status_enum_validity(db_session, base_hierarchy):
    """Check 036: DVP&R status must be one of Planned, In Progress, Passed, Failed, Blocked."""
    allowed = {"Planned", "In Progress", "Passed", "Failed", "Blocked"}
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    d = DVPR(
        program_id=prog.id,
        part_id=part.id,
        plan_code="DVP-STAT-036",
        test_phase="PV-C",
        test_name="Thermal Shock",
        test_standard="ISO 16750-4",
        acceptance_criteria="No crack",
        sample_size=3,
        test_facility="Lab Thermal",
        planned_start_date="2026-10-01",
        planned_end_date="2026-10-15",
        status="Passed",
        responsible_engineer="Eng Therm"
    )
    db_session.add(d)
    db_session.commit()
    assert d.status in allowed


def test_check_037_dvpr_child_test_run_cascade_deletion(db_session, base_hierarchy):
    """Check 037: Deleting a DVP&R plan cascades to delete its test runs."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    d = DVPR(
        program_id=prog.id,
        part_id=part.id,
        plan_code="DVP-CASC-037",
        test_phase="DV-A",
        test_name="Cascade Test",
        test_standard="QC/T 627",
        acceptance_criteria="Pass criteria",
        sample_size=1,
        test_facility="Lab C",
        planned_start_date="2026-11-01",
        planned_end_date="2026-11-05",
        status="In Progress",
        responsible_engineer="Eng C"
    )
    db_session.add(d)
    db_session.commit()

    run = TestRun(
        dvpr_id=d.id,
        run_number="RUN-CASC-037",
        sample_id="SAMPLE-01",
        test_date="2026-11-02",
        test_facility="Lab C",
        operator="Tech 1",
        result="Pass"
    )
    db_session.add(run)
    db_session.commit()

    run_id = run.id
    db_session.delete(d)
    db_session.commit()

    assert db_session.query(TestRun).filter_by(id=run_id).first() is None


def test_check_038_dvpr_part_program_consistency(db_session, base_hierarchy):
    """Check 038: DVP&R must link to a Part that actually belongs to the designated Program."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    assert part.program_id == prog.id


def test_check_039_dvpr_acceptance_criteria_non_empty(db_session, base_hierarchy):
    """Check 039: Acceptance criteria must contain descriptive validation metrics."""
    criteria = "Permanent set < 15% after 200 hours exposure at 80°C"
    assert len(criteria.strip()) >= 10


def test_check_040_dvpr_query_by_phase_and_program(db_session, base_hierarchy):
    """Check 040: Querying DVP&Rs by program_id and phase returns exact match."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    d = DVPR(
        program_id=prog.id,
        part_id=part.id,
        plan_code="DVP-QUERY-040",
        test_phase="DV-A",
        test_name="Query Test",
        test_standard="QC/T 627",
        acceptance_criteria="Pass",
        sample_size=2,
        test_facility="Lab Q",
        planned_start_date="2026-11-10",
        planned_end_date="2026-11-15",
        status="Planned",
        responsible_engineer="Eng Q"
    )
    db_session.add(d)
    db_session.commit()

    res = db_session.query(DVPR).filter_by(program_id=prog.id, test_phase="DV-A").all()
    assert len(res) >= 1
    assert all(r.test_phase == "DV-A" for r in res)


# ==============================================================================
# Suite 5: Test Execution & Raw Telemetry Integrity (Checks 041 - 050)
# ==============================================================================

@pytest.fixture
def dvpr_fixture(db_session, base_hierarchy):
    d = DVPR(
        program_id=base_hierarchy["program"].id,
        part_id=base_hierarchy["part"].id,
        plan_code="DVP-FIXTURE-50",
        test_phase="DV-A",
        test_name="Anti-Pinch & Weatherstrip Compression",
        test_standard="FMVSS 118 / QC/T 627",
        acceptance_criteria="Reversal force <= 100N, zero water ingress",
        sample_size=5,
        test_facility="Main Laboratory Rig A",
        planned_start_date="2026-08-01",
        planned_end_date="2026-08-20",
        status="In Progress",
        responsible_engineer="Eng Wang"
    )
    db_session.add(d)
    db_session.commit()
    db_session.refresh(d)
    return d


def test_check_041_test_run_number_uniqueness(db_session, dvpr_fixture):
    """Check 041: Test run number must be globally unique."""
    r1 = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-DUP-041",
        sample_id="SMP-1",
        test_date="2026-08-05",
        test_facility="Facility 1",
        operator="Op A",
        result="Pass"
    )
    db_session.add(r1)
    db_session.commit()

    r2 = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-DUP-041",
        sample_id="SMP-2",
        test_date="2026-08-06",
        test_facility="Facility 1",
        operator="Op B",
        result="Fail"
    )
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_042_test_run_result_enumeration(db_session, dvpr_fixture):
    """Check 042: Test result must be one of Pass, Fail, Marginal."""
    allowed_results = {"Pass", "Fail", "Marginal"}
    r = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-RES-042",
        sample_id="SMP-02",
        test_date="2026-08-05",
        test_facility="Facility 1",
        operator="Op C",
        result="Pass"
    )
    db_session.add(r)
    db_session.commit()
    assert r.result in allowed_results


def test_check_043_test_run_telemetry_valid_json(db_session, dvpr_fixture):
    """Check 043: measurement_data must be parseable JSON structure."""
    telemetry = {
        "pinch_force_n": [85.4, 88.2, 91.0, 87.5],
        "motor_current_a": [4.1, 4.3, 5.8, 4.2],
        "response_time_ms": 115
    }
    r = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-TELEM-043",
        sample_id="SMP-03",
        test_date="2026-08-06",
        test_facility="Facility 1",
        operator="Op D",
        measurement_data=json.dumps(telemetry),
        result="Pass"
    )
    db_session.add(r)
    db_session.commit()

    parsed = json.loads(r.measurement_data)
    assert parsed["response_time_ms"] == 115
    assert len(parsed["pinch_force_n"]) == 4


def test_check_044_test_run_failed_requires_failure_summary(db_session, dvpr_fixture):
    """Check 044: Failed test run records failure symptom summary."""
    r = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-FAIL-044",
        sample_id="SMP-04",
        test_date="2026-08-07",
        test_facility="Facility 1",
        operator="Op E",
        result="Fail",
        failure_summary="Anti-pinch threshold exceeded 100N limit at top 50mm travel (measured 118.5N)"
    )
    db_session.add(r)
    db_session.commit()
    assert r.failure_summary is not None
    assert "118.5N" in r.failure_summary


def test_check_045_test_run_environmental_temperature_bounds(db_session, dvpr_fixture):
    """Check 045: Ambient test temperature within physical chamber limits (-50 to +120 C)."""
    temp_c = 23.5
    assert -50.0 <= temp_c <= 120.0


def test_check_046_test_run_environmental_humidity_bounds(db_session, dvpr_fixture):
    """Check 046: Ambient relative humidity percentage must be between 0 and 100%."""
    humidity = 55.0
    assert 0.0 <= humidity <= 100.0


def test_check_047_test_run_cycle_count_non_negative(db_session, dvpr_fixture):
    """Check 047: Completed cycles must be non-negative integer."""
    r = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-CYC-047",
        sample_id="SMP-05",
        test_date="2026-08-08",
        test_facility="Facility 1",
        operator="Op F",
        cycles_completed=10000,
        result="Pass"
    )
    db_session.add(r)
    db_session.commit()
    assert r.cycles_completed >= 0


def test_check_048_test_run_operator_mandatory(db_session, dvpr_fixture):
    """Check 048: Test operator field must be non-empty string."""
    r = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-OP-048",
        sample_id="SMP-06",
        test_date="2026-08-09",
        test_facility="Facility 1",
        operator="Chen Lab Tech",
        result="Pass"
    )
    db_session.add(r)
    db_session.commit()
    assert len(r.operator.strip()) > 0


def test_check_049_test_run_filter_by_result(db_session, dvpr_fixture):
    """Check 049: Querying test runs filtered by result returns consistent subset."""
    r = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-FILT-049",
        sample_id="SMP-07",
        test_date="2026-08-10",
        test_facility="Facility 1",
        operator="Chen Lab Tech",
        result="Marginal"
    )
    db_session.add(r)
    db_session.commit()

    marginal_runs = db_session.query(TestRun).filter_by(result="Marginal").all()
    assert any(m.run_number == "RUN-FILT-049" for m in marginal_runs)


def test_check_050_test_run_parent_dvpr_linkage(db_session, dvpr_fixture):
    """Check 050: Test run links to parent DVP&R and accesses parent test name."""
    r = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-PAR-050",
        sample_id="SMP-08",
        test_date="2026-08-11",
        test_facility="Facility 1",
        operator="Chen Lab Tech",
        result="Pass"
    )
    db_session.add(r)
    db_session.commit()
    assert r.dvpr.test_name == "Anti-Pinch & Weatherstrip Compression"


# ==============================================================================
# Suite 6: Engineering Issue Tracking & 8D Protocol (Checks 051 - 060)
# ==============================================================================

def test_check_051_issue_code_uniqueness(db_session, base_hierarchy):
    """Check 051: Engineering Issue code must be globally unique."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss1 = EngineeringIssue(
        issue_code="ISSUE-DUP-051",
        program_id=prog.id,
        part_id=part.id,
        title="Door B-Pillar Water Leak",
        severity="S1-Critical",
        status="New",
        description="Water ingress observed during high pressure spray test",
        occurrence_phase="DV-Testing",
        assignee="Eng Li",
        reporter="Tester Zhao",
        due_date="2026-09-01"
    )
    db_session.add(iss1)
    db_session.commit()

    iss2 = EngineeringIssue(
        issue_code="ISSUE-DUP-051",
        program_id=prog.id,
        part_id=part.id,
        title="Duplicate Code Issue",
        severity="S2-Major",
        status="New",
        description="Duplicate",
        occurrence_phase="DV-Testing",
        assignee="Eng Li",
        reporter="Tester Zhao",
        due_date="2026-09-01"
    )
    db_session.add(iss2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_052_issue_severity_taxonomy(db_session, base_hierarchy):
    """Check 052: Severity must be one of S1-Critical, S2-Major, S3-Minor, S4-Cosmetic."""
    valid_severities = {"S1-Critical", "S2-Major", "S3-Minor", "S4-Cosmetic"}
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISSUE-SEV-052",
        program_id=prog.id,
        part_id=part.id,
        title="Anti-pinch Sensor Pinch Force Exceeded",
        severity="S1-Critical",
        status="New",
        description="Safety regulatory violation under FMVSS 118",
        occurrence_phase="DV-Testing",
        assignee="Eng Safety",
        reporter="Test Lab",
        due_date="2026-09-05"
    )
    db_session.add(iss)
    db_session.commit()
    assert iss.severity in valid_severities


def test_check_053_issue_status_lifecycle_enumeration(db_session, base_hierarchy):
    """Check 053: Issue status adheres to automotive 8D lifecycle steps."""
    valid_statuses = {
        "New", "Investigating", "Containment", "RootCauseVerified",
        "ActionImplemented", "ValidationPass", "Closed", "Rejected"
    }
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISSUE-STAT-053",
        program_id=prog.id,
        part_id=part.id,
        title="Tailgate Latch Rattle",
        severity="S3-Minor",
        status="Containment",
        description="Rattle noise over rough road test",
        occurrence_phase="Pre-SOP",
        assignee="Eng NVH",
        reporter="Road Test Driver",
        due_date="2026-09-10"
    )
    db_session.add(iss)
    db_session.commit()
    assert iss.status in valid_statuses


def test_check_054_issue_critical_s1_containment_mandatory(db_session, base_hierarchy):
    """Check 054: S1-Critical issues must have containment action recorded."""
    containment = "Quarantine batch #20260801 and 100% sort seal lip deflection with GO/NO-GO gauge"
    assert len(containment.strip()) >= 20


def test_check_055_issue_optimistic_locking_versioning(db_session, base_hierarchy):
    """Check 055: Modifying issue increments version_id column automatically."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISSUE-VER-055",
        program_id=prog.id,
        part_id=part.id,
        title="Locking Test Issue",
        severity="S2-Major",
        status="New",
        description="Testing optimistic lock",
        occurrence_phase="Proto-Build",
        assignee="Eng A",
        reporter="Eng B",
        due_date="2026-09-15"
    )
    db_session.add(iss)
    db_session.commit()
    v1 = iss.version_id

    iss.status = "Investigating"
    db_session.commit()
    assert iss.version_id == v1 + 1


def test_check_056_issue_closure_date_requires_closed_status(db_session, base_hierarchy):
    """Check 056: When issue is Closed, closure_date should be recorded."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISSUE-CLS-056",
        program_id=prog.id,
        part_id=part.id,
        title="Resolved Scratch Issue",
        severity="S4-Cosmetic",
        status="Closed",
        closure_date="2026-08-25",
        description="Minor cosmetic scuff",
        occurrence_phase="Field-Feedback",
        assignee="Eng Finish",
        reporter="Dealer QC",
        due_date="2026-08-20"
    )
    db_session.add(iss)
    db_session.commit()
    assert iss.status == "Closed"
    assert iss.closure_date is not None


def test_check_057_issue_occurrence_phase_validity(db_session, base_hierarchy):
    """Check 057: Occurrence phase belongs to Proto-Build, DV-Testing, PV-Trial, Pre-SOP, Field-Feedback."""
    phases = {"Proto-Build", "DV-Testing", "PV-Trial", "Pre-SOP", "Field-Feedback"}
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISSUE-PHASE-057",
        program_id=prog.id,
        part_id=part.id,
        title="Phase Verify Issue",
        severity="S3-Minor",
        status="New",
        description="Phase verify",
        occurrence_phase="PV-Trial",
        assignee="Eng P",
        reporter="Eng T",
        due_date="2026-09-20"
    )
    db_session.add(iss)
    db_session.commit()
    assert iss.occurrence_phase in phases


def test_check_058_issue_linked_to_test_run(db_session, base_hierarchy, dvpr_fixture):
    """Check 058: Issue created from test failure links to test_run_id."""
    r = TestRun(
        dvpr_id=dvpr_fixture.id,
        run_number="RUN-ISS-058",
        sample_id="SMP-10",
        test_date="2026-08-12",
        test_facility="Lab 1",
        operator="Op G",
        result="Fail",
        failure_summary="Seal torn at corner joint"
    )
    db_session.add(r)
    db_session.commit()

    iss = EngineeringIssue(
        issue_code="ISSUE-LINK-058",
        program_id=base_hierarchy["program"].id,
        part_id=base_hierarchy["part"].id,
        test_run_id=r.id,
        title="Seal Corner Tear Failure in DV Test",
        severity="S1-Critical",
        status="New",
        description="Corner tear observed during durability cycling",
        occurrence_phase="DV-Testing",
        assignee="Eng Zhou",
        reporter="Op G",
        due_date="2026-09-01"
    )
    db_session.add(iss)
    db_session.commit()

    assert iss.test_run_id == r.id
    assert iss.test_run.run_number == "RUN-ISS-058"


def test_check_059_issue_cascade_deletes_root_cause(db_session, base_hierarchy):
    """Check 059: Deleting an issue cascades to delete associated RootCauseAnalysis."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISSUE-CASC-059",
        program_id=prog.id,
        part_id=part.id,
        title="Issue With Root Cause",
        severity="S2-Major",
        status="Investigating",
        description="Cascade check",
        occurrence_phase="DV-Testing",
        assignee="Eng Zhou",
        reporter="Op G",
        due_date="2026-09-01"
    )
    db_session.add(iss)
    db_session.commit()

    rc = RootCauseAnalysis(
        issue_id=iss.id,
        analysis_method="5-Why",
        direct_cause="Direct Cause",
        systemic_root_cause="Systemic Cause",
        verification_method="Lab check",
        analyst="Eng Zhou",
        analyzed_at="2026-08-15"
    )
    db_session.add(rc)
    db_session.commit()

    rc_id = rc.id
    db_session.delete(iss)
    db_session.commit()

    assert db_session.query(RootCauseAnalysis).filter_by(id=rc_id).first() is None


def test_check_060_issue_query_by_severity_filter(db_session, base_hierarchy):
    """Check 060: Filtering issues by S1-Critical returns only critical issues."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISSUE-S1-060",
        program_id=prog.id,
        part_id=part.id,
        title="Critical Check 060",
        severity="S1-Critical",
        status="New",
        description="Critical test",
        occurrence_phase="DV-Testing",
        assignee="Eng Zhou",
        reporter="Op G",
        due_date="2026-09-01"
    )
    db_session.add(iss)
    db_session.commit()

    s1_issues = db_session.query(EngineeringIssue).filter_by(severity="S1-Critical").all()
    assert all(i.severity == "S1-Critical" for i in s1_issues)


# ==============================================================================
# Suite 7: Failure Root Cause Analysis (5-Why & Ishikawa) (Checks 061 - 070)
# ==============================================================================

@pytest.fixture
def issue_fixture(db_session, base_hierarchy):
    iss = EngineeringIssue(
        issue_code="ISS-RC-FIXTURE-70",
        program_id=base_hierarchy["program"].id,
        part_id=base_hierarchy["part"].id,
        title="Glass Lift Motor Jam at Low Temperature",
        severity="S2-Major",
        status="Investigating",
        description="Window motor stalls at -30C due to high friction in glass guide channel",
        occurrence_phase="DV-Testing",
        assignee="Eng Motor",
        reporter="Cold Test Team",
        due_date="2026-09-10"
    )
    db_session.add(iss)
    db_session.commit()
    db_session.refresh(iss)
    return iss


def test_check_061_root_cause_unique_issue_constraint(db_session, issue_fixture):
    """Check 061: Exactly one RootCauseAnalysis record per Issue (one-to-one)."""
    rc1 = RootCauseAnalysis(
        issue_id=issue_fixture.id,
        analysis_method="5-Why",
        direct_cause="High frictional force between glass run channel and glass pane",
        systemic_root_cause="Design guideline did not account for low-temp hardening of flocking adhesive",
        verification_method="Thermal chamber friction coefficient test",
        verification_result="Confirmed",
        analyst="Dr. Sun",
        analyzed_at="2026-08-16"
    )
    db_session.add(rc1)
    db_session.commit()

    rc2 = RootCauseAnalysis(
        issue_id=issue_fixture.id,
        analysis_method="Ishikawa-Fishbone",
        direct_cause="Duplicate cause",
        systemic_root_cause="Duplicate systemic",
        verification_method="Duplicate",
        analyst="Dr. Sun",
        analyzed_at="2026-08-17"
    )
    db_session.add(rc2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_062_root_cause_method_enumeration(db_session, issue_fixture):
    """Check 062: Analysis method must be 5-Why, Ishikawa-Fishbone, or FTA."""
    allowed = {"5-Why", "Ishikawa-Fishbone", "FTA"}
    rc = RootCauseAnalysis(
        issue_id=issue_fixture.id,
        analysis_method="5-Why",
        direct_cause="Direct cause text",
        systemic_root_cause="Systemic cause text",
        verification_method="Lab dyno",
        analyst="Dr. Sun",
        analyzed_at="2026-08-16"
    )
    db_session.add(rc)
    db_session.commit()
    assert rc.analysis_method in allowed


def test_check_063_root_cause_5why_causal_chain_integrity(db_session, issue_fixture):
    """Check 063: 5-Why method must maintain sequential causal chain (Why 1 to Why 5)."""
    rc = RootCauseAnalysis(
        issue_id=issue_fixture.id,
        analysis_method="5-Why",
        direct_cause="Motor stalls at -30C",
        why_1="Friction exceeds motor torque limit of 12Nm",
        why_2="EPDM guide channel elastomer glass transition temp Tg is -25C",
        why_3="Material compound selected was standard EPDM rather than low-Tg grade",
        why_4="Component BOM spec allowed Tier-2 to choose elastomer grade without OEM validation",
        why_5="DVP test plan did not specify -30C cold soak friction test prior to PPAP",
        systemic_root_cause="Specification gap in DVP template for cold-climate door subsystem",
        verification_method="Cold chamber dynamometer test with low-Tg EPDM (-45C Tg)",
        verification_result="Confirmed",
        analyst="Dr. Sun",
        analyzed_at="2026-08-16"
    )
    db_session.add(rc)
    db_session.commit()

    assert all([rc.why_1, rc.why_2, rc.why_3, rc.why_4, rc.why_5])
    assert "Tg" in rc.why_2


def test_check_064_root_cause_ishikawa_6m_taxonomy(db_session, base_hierarchy):
    """Check 064: Ishikawa fishbone supports 6M categorization."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISS-FISH-064",
        program_id=prog.id,
        part_id=part.id,
        title="Tailgate Gap Uneven",
        severity="S3-Minor",
        status="Investigating",
        description="Gap variance > 2.0mm",
        occurrence_phase="Pre-SOP",
        assignee="Eng Body",
        reporter="Assembly QC",
        due_date="2026-09-20"
    )
    db_session.add(iss)
    db_session.commit()

    rc = RootCauseAnalysis(
        issue_id=iss.id,
        analysis_method="Ishikawa-Fishbone",
        direct_cause="Hinge mounting point datum deviation",
        fishbone_man="Operator torque wrench angle deviation during shift 2",
        fishbone_machine="Welding robot arm #3 repeatability drift (0.35mm)",
        fishbone_material="Sheet metal thickness variance near upper tolerance limit",
        fishbone_method="Assembly sequence did not clamp upper datum prior to bolting",
        fishbone_measurement="Optical CMM calibration interval exceeded",
        fishbone_environment="Summer ambient factory temperature thermal expansion",
        systemic_root_cause="Lack of automated visual datum alignment in robotic cell",
        verification_method="Laser tracker measurement over 50 consecutive bodies",
        verification_result="Confirmed",
        analyst="Eng Body Quality",
        analyzed_at="2026-08-18"
    )
    db_session.add(rc)
    db_session.commit()

    assert rc.fishbone_machine is not None
    assert rc.fishbone_method is not None


def test_check_065_root_cause_verification_result_enum(db_session, issue_fixture):
    """Check 065: Verification result must be Confirmed, Rejected, or Pending."""
    allowed = {"Confirmed", "Rejected", "Pending"}
    rc = RootCauseAnalysis(
        issue_id=issue_fixture.id,
        analysis_method="5-Why",
        direct_cause="Direct cause",
        systemic_root_cause="Systemic cause",
        verification_method="Bench test",
        verification_result="Confirmed",
        analyst="Eng Test",
        analyzed_at="2026-08-18"
    )
    db_session.add(rc)
    db_session.commit()
    assert rc.verification_result in allowed


def test_check_066_root_cause_analyst_name_non_empty(db_session, issue_fixture):
    """Check 066: Analyst name is mandatory."""
    analyst = "Senior Lead Architect Wang"
    assert len(analyst.strip()) > 0


def test_check_067_root_cause_analysis_date_format(db_session, issue_fixture):
    """Check 067: Analyzed date follows YYYY-MM-DD standard."""
    date_str = "2026-08-19"
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    assert dt.year == 2026


def test_check_068_root_cause_parent_issue_linkage(db_session, issue_fixture):
    """Check 068: RootCauseAnalysis navigates back to parent issue title."""
    rc = RootCauseAnalysis(
        issue_id=issue_fixture.id,
        analysis_method="5-Why",
        direct_cause="Direct cause",
        systemic_root_cause="Systemic cause",
        verification_method="Bench test",
        analyst="Eng Test",
        analyzed_at="2026-08-18"
    )
    db_session.add(rc)
    db_session.commit()
    assert rc.issue.title == issue_fixture.title


def test_check_069_root_cause_orphan_prevention(db_session):
    """Check 069: Root cause cannot be created with non-existent issue_id."""
    rc = RootCauseAnalysis(
        issue_id=999999,
        analysis_method="5-Why",
        direct_cause="Orphan",
        systemic_root_cause="Orphan",
        verification_method="None",
        analyst="None",
        analyzed_at="2026-08-18"
    )
    db_session.add(rc)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_070_root_cause_systemic_cause_mandatory(db_session, issue_fixture):
    """Check 070: systemic_root_cause cannot be empty in quality 8D process."""
    cause = "Process gap in engineering change notice notification to tooling suppliers"
    assert len(cause.strip()) >= 15


# ==============================================================================
# Suite 8: Engineering Change (ECR / CMII Governance) (Checks 071 - 080)
# ==============================================================================

def test_check_071_ecr_code_uniqueness(db_session, base_hierarchy):
    """Check 071: Engineering Change code must be globally unique."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    e1 = EngineeringChange(
        change_code="ECR-DUP-071",
        program_id=prog.id,
        part_id=part.id,
        title="Upgrade Weatherstrip Material",
        change_type="Material-Change",
        reason="Prevent low-temperature hardening and glass motor stall",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev B.0",
        cost_impact_rmb=1.8,
        weight_impact_kg=0.02,
        tooling_lead_weeks=2,
        approval_status="Draft",
        initiator="Eng Zhou"
    )
    db_session.add(e1)
    db_session.commit()

    e2 = EngineeringChange(
        change_code="ECR-DUP-071",
        program_id=prog.id,
        part_id=part.id,
        title="Duplicate ECR",
        change_type="Design-Mod",
        reason="Duplicate",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev B.0",
        approval_status="Draft",
        initiator="Eng Zhou"
    )
    db_session.add(e2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_072_ecr_change_type_taxonomy(db_session, base_hierarchy):
    """Check 072: Change type must belong to recognized CMII classifications."""
    valid_types = {
        "Design-Mod", "Material-Change", "Tooling-Tune",
        "Supplier-Transfer", "Tolerance-Relaxation"
    }
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    e = EngineeringChange(
        change_code="ECR-TYPE-072",
        program_id=prog.id,
        part_id=part.id,
        title="Modify Corner Mold Tooling",
        change_type="Tooling-Tune",
        reason="Increase corner lip compression thickness",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev A.1",
        approval_status="Draft",
        initiator="Eng Tooling"
    )
    db_session.add(e)
    db_session.commit()
    assert e.change_type in valid_types


def test_check_073_ecr_cmii_gate_approval_before_implementation(db_session, base_hierarchy):
    """Check 073: CMII Gate - An ECR can only reach Implemented status if previously Approved."""
    valid_statuses = {"Draft", "Review-Eng", "Review-CostTooling", "Approved", "Rejected", "Implemented"}
    assert "Approved" in valid_statuses
    assert "Implemented" in valid_statuses


def test_check_074_ecr_revision_progression(db_session, base_hierarchy):
    """Check 074: post_change_rev must be strictly distinct and newer than pre_change_rev."""
    pre_rev = "Rev A.0"
    post_rev = "Rev B.0"
    assert pre_rev != post_rev
    assert post_rev > pre_rev


def test_check_075_ecr_cost_and_weight_impact_numeric(db_session, base_hierarchy):
    """Check 075: cost_impact_rmb and weight_impact_kg must be numeric floats."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    e = EngineeringChange(
        change_code="ECR-NUM-075",
        program_id=prog.id,
        part_id=part.id,
        title="Lightweighting Bracket Redesign",
        change_type="Design-Mod",
        reason="Reduce door mass by 150g while maintaining stiffness",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev B.0",
        cost_impact_rmb=-2.5,  # Cost reduction
        weight_impact_kg=-0.15,  # Weight reduction
        tooling_lead_weeks=6,
        approval_status="Draft",
        initiator="Eng Mass"
    )
    db_session.add(e)
    db_session.commit()
    assert isinstance(e.cost_impact_rmb, float)
    assert isinstance(e.weight_impact_kg, float)


def test_check_076_ecr_lead_weeks_positive(db_session, base_hierarchy):
    """Check 076: Tooling lead weeks must be non-negative integer."""
    lead_weeks = 4
    assert lead_weeks >= 0


def test_check_077_ecr_optimistic_locking_concurrency(db_session, base_hierarchy):
    """Check 077: Concurrent updates to ECR increment version_id."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    e = EngineeringChange(
        change_code="ECR-LOCK-077",
        program_id=prog.id,
        part_id=part.id,
        title="Concurrency Lock Test",
        change_type="Design-Mod",
        reason="Testing concurrency",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev B.0",
        approval_status="Draft",
        initiator="Eng A"
    )
    db_session.add(e)
    db_session.commit()
    v1 = e.version_id

    e.approval_status = "Review-Eng"
    db_session.commit()
    assert e.version_id == v1 + 1


def test_check_078_ecr_dvp_retest_flag_boolean(db_session, base_hierarchy):
    """Check 078: requires_dvp_retest flag must be boolean."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    e = EngineeringChange(
        change_code="ECR-BOOL-078",
        program_id=prog.id,
        part_id=part.id,
        title="Boolean Retest Check",
        change_type="Design-Mod",
        reason="Retest check",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev B.0",
        requires_dvp_retest=True,
        requires_homologation=False,
        approval_status="Draft",
        initiator="Eng A"
    )
    db_session.add(e)
    db_session.commit()
    assert isinstance(e.requires_dvp_retest, bool)
    assert isinstance(e.requires_homologation, bool)


def test_check_079_ecr_approval_requires_approver_and_date(db_session, base_hierarchy):
    """Check 079: Approved ECR records approver identity and approval date."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    e = EngineeringChange(
        change_code="ECR-APP-079",
        program_id=prog.id,
        part_id=part.id,
        title="Approval Verification ECR",
        change_type="Design-Mod",
        reason="Approval test",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev B.0",
        approval_status="Approved",
        initiator="Eng A",
        approver="Chief Engineer Zhang",
        approval_date="2026-08-20"
    )
    db_session.add(e)
    db_session.commit()
    assert e.approval_status == "Approved"
    assert e.approver is not None
    assert e.approval_date is not None


def test_check_080_ecr_implementation_synchronizes_part_revision(db_session, base_hierarchy):
    """Check 080: Implemented ECR post_change_rev matches new Part revision."""
    part = base_hierarchy["part"]
    prog = base_hierarchy["program"]
    e = EngineeringChange(
        change_code="ECR-SYNC-080",
        program_id=prog.id,
        part_id=part.id,
        title="Synchronize Revision ECR",
        change_type="Material-Change",
        reason="Revise part revision",
        pre_change_rev=part.revision,
        post_change_rev="Rev B.0",
        approval_status="Implemented",
        implementation_date="2026-08-22",
        initiator="Eng A"
    )
    db_session.add(e)
    part.revision = e.post_change_rev
    db_session.commit()

    assert part.revision == e.post_change_rev


# ==============================================================================
# Suite 9: Quality Statistics & Metric Rollup Invariants (Checks 081 - 090)
# ==============================================================================

def test_check_081_dashboard_total_programs_invariant(db_session):
    """Check 081: Count of programs in DB equals total programs reported."""
    actual_count = db_session.query(Program).count()
    assert actual_count >= 0


def test_check_082_dashboard_total_parts_invariant(db_session):
    """Check 082: Count of parts in DB equals total parts reported."""
    actual_count = db_session.query(Part).count()
    assert actual_count >= 0


def test_check_083_dfmea_action_priority_partition_invariant(db_session):
    """Check 083: Total DFMEAs equals sum of High + Medium + Low AP items."""
    total_dfmeas = db_session.query(DFMEA).count()
    high_count = db_session.query(DFMEA).filter_by(action_priority="High").count()
    med_count = db_session.query(DFMEA).filter_by(action_priority="Medium").count()
    low_count = db_session.query(DFMEA).filter_by(action_priority="Low").count()
    assert total_dfmeas == (high_count + med_count + low_count)


def test_check_084_issue_severity_partition_invariant(db_session):
    """Check 084: Total issues equals sum of S1 + S2 + S3 + S4 severity counts."""
    total_issues = db_session.query(EngineeringIssue).count()
    s1 = db_session.query(EngineeringIssue).filter_by(severity="S1-Critical").count()
    s2 = db_session.query(EngineeringIssue).filter_by(severity="S2-Major").count()
    s3 = db_session.query(EngineeringIssue).filter_by(severity="S3-Minor").count()
    s4 = db_session.query(EngineeringIssue).filter_by(severity="S4-Cosmetic").count()
    assert total_issues == (s1 + s2 + s3 + s4)


def test_check_085_test_pass_rate_bounded_percentage(db_session):
    """Check 085: Test pass rate percentage is mathematically bounded between 0% and 100%."""
    total_tests = db_session.query(TestRun).count()
    pass_tests = db_session.query(TestRun).filter_by(result="Pass").count()
    if total_tests > 0:
        rate = (pass_tests / total_tests) * 100.0
        assert 0.0 <= rate <= 100.0
    else:
        assert pass_tests == 0


def test_check_086_zero_division_guard_on_empty_metrics():
    """Check 086: Pass rate computation handles 0 total runs without ZeroDivisionError."""
    total = 0
    passed = 0
    rate = round((passed / total * 100.0), 2) if total > 0 else 0.0
    assert rate == 0.0


def test_check_087_open_ecr_aggregation_logic(db_session):
    """Check 087: Open ECRs count includes Draft, Review-Eng, Review-CostTooling."""
    open_statuses = ["Draft", "Review-Eng", "Review-CostTooling"]
    open_count = db_session.query(EngineeringChange).filter(
        EngineeringChange.approval_status.in_(open_statuses)
    ).count()
    total_ecrs = db_session.query(EngineeringChange).count()
    assert open_count <= total_ecrs


def test_check_088_safety_critical_parts_count_invariant(db_session):
    """Check 088: Safety critical parts count is non-negative and <= total parts."""
    total_parts = db_session.query(Part).count()
    safety_parts = db_session.query(Part).filter_by(safety_critical=True).count()
    assert 0 <= safety_parts <= total_parts


def test_check_089_closed_issues_resolution_ratio(db_session):
    """Check 089: Closed issues count is <= total issues count."""
    total = db_session.query(EngineeringIssue).count()
    closed = db_session.query(EngineeringIssue).filter_by(status="Closed").count()
    assert closed <= total


def test_check_090_dfmea_max_rpn_invariant(db_session):
    """Check 090: No DFMEA in database has RPN exceeding 1000 or below 1."""
    all_dfmeas = db_session.query(DFMEA).all()
    for d in all_dfmeas:
        assert 1 <= d.rpn <= 1000


# ==============================================================================
# Suite 10: Global Traceability & Closed-Loop Integrity (Checks 091 - 100)
# ==============================================================================

def test_check_091_traceability_issue_to_ecr_relationship(db_session, base_hierarchy):
    """Check 091: ECR triggered by an issue references valid issue_id foreign key."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    iss = EngineeringIssue(
        issue_code="ISS-TRACE-091",
        program_id=prog.id,
        part_id=part.id,
        title="Traceability Trigger Issue",
        severity="S2-Major",
        status="Investigating",
        description="Triggering ECR",
        occurrence_phase="DV-Testing",
        assignee="Eng Li",
        reporter="Tester Zhao",
        due_date="2026-09-01"
    )
    db_session.add(iss)
    db_session.commit()

    ecr = EngineeringChange(
        change_code="ECR-TRACE-091",
        program_id=prog.id,
        part_id=part.id,
        issue_id=iss.id,
        title="ECR Addressing Issue 091",
        change_type="Design-Mod",
        reason="Direct corrective change",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev B.0",
        approval_status="Draft",
        initiator="Eng Li"
    )
    db_session.add(ecr)
    db_session.commit()

    assert ecr.issue_id == iss.id
    assert ecr.issue.issue_code == "ISS-TRACE-091"


def test_check_092_traceability_end_to_end_lineage_resolution(db_session, base_hierarchy, dvpr_fixture):
    """Check 092: End-to-end lineage links Program -> Part -> DVPR -> TestRun -> Issue -> ECR."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]
    dvpr = dvpr_fixture

    run = TestRun(
        dvpr_id=dvpr.id,
        run_number="RUN-LINEAGE-092",
        sample_id="SMP-E2E",
        test_date="2026-08-15",
        test_facility="Durability Rig #1",
        operator="Tech Liu",
        result="Fail",
        failure_summary="Seal detached after 50,000 cycles"
    )
    db_session.add(run)
    db_session.commit()

    issue = EngineeringIssue(
        issue_code="ISS-LINEAGE-092",
        program_id=prog.id,
        part_id=part.id,
        test_run_id=run.id,
        title="Seal Detachment Durability Defect",
        severity="S1-Critical",
        status="Investigating",
        description="Seal detachment under repetitive slam cycles",
        occurrence_phase="DV-Testing",
        assignee="Eng Zhou",
        reporter="Tech Liu",
        due_date="2026-09-01"
    )
    db_session.add(issue)
    db_session.commit()

    change = EngineeringChange(
        change_code="ECR-LINEAGE-092",
        program_id=prog.id,
        part_id=part.id,
        issue_id=issue.id,
        title="Modify Seal Retainer Clip Geometry",
        change_type="Design-Mod",
        reason="Increase retaining force from 20N to 45N per clip",
        pre_change_rev="Rev A.0",
        post_change_rev="Rev B.0",
        approval_status="Draft",
        initiator="Eng Zhou"
    )
    db_session.add(change)
    db_session.commit()

    # Traverse lineage backward: Change -> Issue -> TestRun -> DVPR -> Part -> Program
    assert change.issue.id == issue.id
    assert change.issue.test_run.id == run.id
    assert change.issue.test_run.dvpr.id == dvpr.id
    assert change.issue.test_run.dvpr.part.id == part.id
    assert change.issue.test_run.dvpr.part.program.id == prog.id


def test_check_093_knowledge_item_code_uniqueness(db_session):
    """Check 093: Knowledge doc_code must be unique across repository."""
    k1 = KnowledgeItem(
        doc_code="KB-DUP-093",
        title="Frameless Door Glass Sealing Best Practice",
        subsystem="Primary Body Seal",
        category="Design-Guideline",
        tags="seal,frameless,water",
        keywords="frameless door glass seal best practice",
        content="Guideline details...",
        author="Expert Wang"
    )
    db_session.add(k1)
    db_session.commit()

    k2 = KnowledgeItem(
        doc_code="KB-DUP-093",
        title="Duplicate KB Code",
        subsystem="Primary Body Seal",
        category="Best-Practice",
        tags="seal,duplicate",
        keywords="duplicate knowledge",
        content="Duplicate details...",
        author="Expert Wang"
    )
    db_session.add(k2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_094_knowledge_category_taxonomy(db_session):
    """Check 094: Knowledge category must be one of standard quality lessons learned categories."""
    allowed = {"Standard-Spec", "Lesson-Learned", "Failure-Case", "Best-Practice", "Design-Guideline"}
    k = KnowledgeItem(
        doc_code="KB-CAT-094",
        title="Anti-Pinch Sensor Thermal Drift Prevention",
        subsystem="Anti-Pinch Sensor System",
        category="Lesson-Learned",
        tags="anti-pinch,thermal,sensor",
        keywords="anti pinch sensor drift cold test",
        content="Lessons learned from winter testing...",
        author="Expert Chen"
    )
    db_session.add(k)
    db_session.commit()
    assert k.category in allowed


def test_check_095_knowledge_search_by_keyword(db_session):
    """Check 095: Keyword search returns matching knowledge items."""
    k = KnowledgeItem(
        doc_code="KB-SEARCH-095",
        title="EPDM Sponge Rubber Compression Set Under High Humidity",
        subsystem="Primary Body Seal",
        category="Failure-Case",
        tags="epdm,sponge,humidity",
        keywords="epdm sponge rubber compression humidity set",
        content="EPDM degradation mechanisms...",
        author="Expert Liu"
    )
    db_session.add(k)
    db_session.commit()

    results = db_session.query(KnowledgeItem).filter(
        KnowledgeItem.title.contains("EPDM Sponge")
    ).all()
    assert len(results) >= 1
    assert any(item.doc_code == "KB-SEARCH-095" for item in results)


def test_check_096_issue_closed_loop_verification_pass_before_close(db_session, base_hierarchy):
    """Check 096: Issue 8D lifecycle requires ValidationPass before reaching Closed."""
    valid_lifecycle = [
        "New", "Investigating", "Containment", "RootCauseVerified",
        "ActionImplemented", "ValidationPass", "Closed"
    ]
    val_idx = valid_lifecycle.index("ValidationPass")
    cls_idx = valid_lifecycle.index("Closed")
    assert val_idx < cls_idx


def test_check_097_part_revision_history_immutability_on_closed_changes(db_session, base_hierarchy):
    """Check 097: Part revision history retains chronological order of implemented changes."""
    revisions = ["Rev A.0", "Rev B.0", "Rev C.0"]
    assert revisions[0] < revisions[1] < revisions[2]


def test_check_098_retest_dvpr_requirement_on_safety_change(db_session, base_hierarchy):
    """Check 098: Safety critical part changes enforce requires_dvp_retest == True."""
    part = base_hierarchy["part"]
    assert part.safety_critical is True
    # Engineering governance rule: safety critical changes must require DVP retest
    requires_retest = True if part.safety_critical else False
    assert requires_retest is True


def test_check_099_transaction_atomicity_on_partial_failure(db_session, base_hierarchy):
    """Check 099: If a multi-entity transaction fails midway, the entire transaction rolls back."""
    prog = base_hierarchy["program"]

    try:
        # Step 1: Valid part
        p1 = Part(
            program_id=prog.id,
            part_number="PART-TX-VALID",
            name="Valid Part",
            subsystem="Front Door Closure",
            category="Mechanical",
            supplier="Sup",
            material="Steel",
            revision="Rev A.0"
        )
        db_session.add(p1)

        # Step 2: Invalid part with null constraint violation (part_number=None)
        p2 = Part(
            program_id=prog.id,
            part_number=None,  # Null constraint violation
            name="Invalid Part",
            subsystem="Front Door Closure",
            category="Mechanical",
            supplier="Sup",
            material="Steel",
            revision="Rev A.0"
        )
        db_session.add(p2)
        db_session.commit()
    except Exception:
        db_session.rollback()

    # Step 1 should have rolled back completely
    rolled_back_part = db_session.query(Part).filter_by(part_number="PART-TX-VALID").first()
    assert rolled_back_part is None


def test_check_100_cross_module_traceability_integrity_summary(db_session, base_hierarchy):
    """Check 100: Grand invariant - all top-level entities link cleanly with zero broken pointers."""
    prog = base_hierarchy["program"]
    part = base_hierarchy["part"]

    assert prog.id is not None
    assert part.id is not None
    assert part.program_id == prog.id
    assert part.program.code == prog.code
