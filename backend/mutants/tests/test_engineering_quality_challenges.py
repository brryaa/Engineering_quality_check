import pytest
from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun,
    EngineeringIssue, RootCauseAnalysis, EngineeringChange
)

TestRun.__test__ = False


def _seed_quality_challenge_fixture(db_session):
    """Seed comprehensive 5-challenge closures quality dataset."""
    # Program
    prog = Program(
        code="EP9-CLOSURE-CHALLENGE",
        name="Electric Coupe Frameless Platform",
        platform="E-SPORT-2026",
        phase="PV",
        lead_engineer="Dr. Zhang Closure Lead",
        quality_manager="Li Quality Director",
        target_market="Global"
    )
    db_session.add(prog)
    db_session.commit()
    db_session.refresh(prog)

    # 1. Challenge 1: Frameless Door Window Glass Position Repeatability
    p1 = Part(
        program_id=prog.id,
        part_number="EP9-WIN-GUIDE-01",
        name="Frameless Glass Front Guide Channel",
        subsystem="Frameless Window System",
        category="Assembly",
        material="Extruded 6061-T6 Aluminum",
        supplier="Brose Closures",
        weight_kg=1.45,
        revision="A.1"
    )
    # 2. Challenge 2: Regulator Motor & Anti-Pinch False Trigger
    p2 = Part(
        program_id=prog.id,
        part_number="EP9-REG-MOTOR-02",
        name="Smart DC Motor with Hall Sensor Anti-Pinch",
        subsystem="Glass Regulator Module",
        category="Electrical",
        material="Copper/RareEarth Magnet/POM Gear",
        supplier="Bosch Automotive",
        weight_kg=0.82,
        revision="B.0"
    )
    # 3. Challenge 3: Tailgate Sealing Water Leak
    p3 = Part(
        program_id=prog.id,
        part_number="EP9-SEAL-TAIL-03",
        name="Primary Tailgate Dual-Bulb Body Seal",
        subsystem="Power Tailgate System",
        category="EPDM-Sealing",
        material="Dense/Sponge EPDM Co-extrusion",
        supplier="Cooper Standard",
        weight_kg=1.12,
        revision="A.2"
    )
    # 4. Challenge 4: Door Hinge Sag & Rattle
    p4 = Part(
        program_id=prog.id,
        part_number="EP9-HINGE-UPPER-04",
        name="Front Door Upper Stamped Hinge with Bushing",
        subsystem="Door Hinge & Check Link",
        category="Hardware",
        material="High-Strength Stamped Steel 42CrMo",
        supplier="Edscha Hinge Systems",
        weight_kg=0.95,
        revision="A.0"
    )
    db_session.add_all([p1, p2, p3, p4])
    db_session.commit()
    for p in [p1, p2, p3, p4]:
        db_session.refresh(p)

    # DFMEA 1: Glass indexing position repeatability
    d1 = DFMEA(
        part_id=p1.id,
        fmea_code="DFMEA-WIN-001",
        item_function="Guide frameless glass indexing into header seal within +/-0.5mm over 30,000 cycles",
        failure_mode="Glass tilt angle yaw deviation exceeds 1.2mm",
        failure_effect="High-speed aerodynamic wind rush noise (>72 dB) and minor water seep in automated car wash",
        severity=7,
        cause_mechanism="Guide channel bracket lateral compliance deflection under aerodynamic suction load",
        occurrence=5,
        prevention_control="CAD structural topology optimization and CAE rigidity simulation",
        detection_control="Dynamic CMM fixture inspection and optical laser gap profile scan",
        detection=4,
        rpn=140,
        action_priority="High",
        recommended_action="Reinforce B-pillar bracket gusset thickness from 1.5mm to 2.2mm with stiffening ribs",
        action_owner="C. Wang Structure",
        target_date="2026-11-15",
        action_status="Completed"
    )
    # DVP&R 1: Wind Tunnel & High Speed Water Leak
    v1 = DVPR(
        program_id=prog.id,
        part_id=p1.id,
        plan_code="DVP-WIN-AERO-01",
        test_phase="PV-C",
        test_name="High-Speed Aeroacoustic Wind Tunnel & Rain Chamber Test",
        test_standard="ISO 20653 / OEM-SPEC-0842",
        acceptance_criteria="No water penetration at 160 km/h wind blast; glass indexing repeat error < 0.5mm",
        sample_size=3,
        test_facility="CAERI Aeroacoustic Wind Tunnel",
        planned_start_date="2026-10-01",
        planned_end_date="2026-10-10",
        status="Passed",
        responsible_engineer="Eng. Lin"
    )
    db_session.add_all([d1, v1])
    db_session.commit()
    db_session.refresh(d1)
    db_session.refresh(v1)

    # Test Run 1: Failed initially due to glass tilt
    tr1 = TestRun(
        dvpr_id=v1.id,
        run_number="RUN-WIN-AERO-001",
        sample_id="SAMPLE-WIN-01",
        test_date="2026-10-05",
        test_facility="CAERI Wind Tunnel",
        operator="Tester Liu",
        temperature_c=22.5,
        humidity_rh=55.0,
        cycles_completed=15000,
        measurement_data="{\"glass_yaw_dev_mm\": 1.35, \"wind_noise_db\": 74.2}",
        result="Fail",
        failure_summary="Glass yaw deviation exceeded threshold at 140 km/h, resulting in upper seal gap leak"
    )
    db_session.add(tr1)
    db_session.commit()
    db_session.refresh(tr1)

    # Issue 1
    iss1 = EngineeringIssue(
        issue_code="ISS-EP9-WIN-001",
        program_id=prog.id,
        part_id=p1.id,
        test_run_id=tr1.id,
        title="Frameless window glass pitch deviation under high-speed aerodynamic suction",
        severity="S2-Major",
        status="ValidationPass",
        description="During 140km/h wind tunnel test, frameless glass indexing drifted by 1.35mm, breaking seal contact.",
        occurrence_phase="PV-Trial",
        containment_action="Temporary shim applied to lower guide stop bracket on prototype fleet",
        assignee="Eng. C. Wang",
        reporter="Tester Liu",
        due_date="2026-11-20",
        closure_date="2026-11-18"
    )
    db_session.add(iss1)
    db_session.commit()
    db_session.refresh(iss1)

    # Root Cause 1: 5-Why
    rc1 = RootCauseAnalysis(
        issue_id=iss1.id,
        analysis_method="5-Why",
        direct_cause="Guide channel B-pillar bracket deflected by 1.2mm under 800N simulated aerodynamic suction force",
        why_1="Glass top edge pulled outward at high vehicle speeds",
        why_2="Lower guide bracket lacked adequate torsional stiffness in cross-car Y-direction",
        why_3="Stamping bracket design was simplified without transverse embossed swage ribs",
        why_4="DFMEA CAE simulation considered only static door closing slam, not dynamic aero suction coupling",
        why_5="Vehicle aerodynamics wind-load boundary condition was missing in door subsystem design guidelines",
        systemic_root_cause="Design rule omission: aerodynamic door window outward suction force standard not integrated into guide bracket design manual",
        verification_method="Static Y-axis stiffness load test (>1200 N/mm) and re-test in wind tunnel",
        verification_result="Confirmed",
        analyst="Dr. Zhang",
        analyzed_at="2026-10-12"
    )
    db_session.add(rc1)

    # Engineering Change 1
    ecr1 = EngineeringChange(
        change_code="ECR-EP9-WIN-001",
        program_id=prog.id,
        part_id=p1.id,
        issue_id=iss1.id,
        title="Add dual embossed swage ribs and increase bracket thickness to 2.2mm",
        change_type="Design-Mod",
        reason="Prevent frameless glass outward deflection and eliminate high-speed wind noise",
        pre_change_rev="A.1",
        post_change_rev="B.0",
        cost_impact_rmb=4.50,
        weight_impact_kg=0.08,
        tooling_lead_weeks=3,
        requires_homologation=False,
        requires_dvp_retest=True,
        approval_status="Implemented",
        initiator="Eng. C. Wang",
        approver="Chief Engineer Zhang",
        approval_date="2026-10-18",
        implementation_date="2026-11-05"
    )
    db_session.add(ecr1)
    db_session.commit()

    return {
        "program": prog,
        "parts": [p1, p2, p3, p4],
        "issue": iss1,
        "ecr": ecr1,
        "root_cause": rc1
    }


def test_challenge_1_frameless_window_traceability(client, db_session):
    """Verify Challenge 1: Frameless Door Window Glass Repeatability Full Traceability Chain."""
    data = _seed_quality_challenge_fixture(db_session)
    issue_id = data["issue"].id

    res = client.get(f"/api/v1/traceability/lineage/{issue_id}")
    assert res.status_code == 200
    chain = res.json()

    assert chain["issue_code"] == "ISS-EP9-WIN-001"
    assert chain["subsystem"] == "Frameless Window System"
    assert len(chain["dfmea_linkages"]) >= 1
    assert chain["dfmea_linkages"][0]["action_priority"] == "High"
    assert chain["dvpr_test_plan"]["test_standard"] == "ISO 20653 / OEM-SPEC-0842"
    assert chain["test_run_execution"]["result"] == "Fail"
    assert chain["root_cause_analysis"]["analysis_method"] == "5-Why"
    assert "suction force" in chain["root_cause_analysis"]["systemic_root_cause"]
    assert len(chain["engineering_changes"]) >= 1
    assert chain["engineering_changes"][0]["approval_status"] == "Implemented"
    assert chain["closed_loop_verified"] is True


def test_challenge_2_anti_pinch_subsystem_aggregation(client, db_session):
    """Verify Challenge 2: Regulator Motor & Anti-Pinch Subsystem Health & Defect Aggregation."""
    _seed_quality_challenge_fixture(db_session)
    res = client.get("/api/v1/traceability/subsystem/Glass Regulator Module")
    assert res.status_code == 200
    sub_data = res.json()
    assert sub_data["parts_count"] >= 1
    assert any(p["part_number"] == "EP9-REG-MOTOR-02" for p in sub_data["parts"])


def test_challenge_3_tailgate_sealing_water_leak_lineage(client, db_session):
    """Verify Challenge 3: Tailgate Sealing Failure Mode & Subsystem Aggregation."""
    _seed_quality_challenge_fixture(db_session)
    res = client.get("/api/v1/traceability/subsystem/Power Tailgate System")
    assert res.status_code == 200
    sub_data = res.json()
    assert sub_data["parts_count"] >= 1
    assert any(p["part_number"] == "EP9-SEAL-TAIL-03" for p in sub_data["parts"])


def test_challenge_4_door_hinge_durability_subsystem(client, db_session):
    """Verify Challenge 4: Door Hinge & Check Link Wear Durability Aggregation."""
    _seed_quality_challenge_fixture(db_session)
    res = client.get("/api/v1/traceability/subsystem/Door Hinge")
    assert res.status_code == 200
    sub_data = res.json()
    assert sub_data["parts_count"] >= 1
    assert any(p["part_number"] == "EP9-HINGE-UPPER-04" for p in sub_data["parts"])


def test_challenge_5_closed_loop_traceability_rule_enforcement(client, db_session):
    """Verify Challenge 5: Closed-loop status rule enforces all gates (Issue closure, RC confirm, ECR approval)."""
    data = _seed_quality_challenge_fixture(db_session)
    issue = data["issue"]

    # Revert issue status to "Investigating"
    issue.status = "Investigating"
    db_session.commit()

    res = client.get(f"/api/v1/traceability/lineage/{issue.id}")
    assert res.status_code == 200
    # Must NOT be marked closed-loop verified if issue is still in Investigating state
    assert res.json()["closed_loop_verified"] is False
