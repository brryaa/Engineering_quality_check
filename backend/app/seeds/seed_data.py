import json
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun, EngineeringIssue,
    RootCauseAnalysis, EngineeringChange, KnowledgeItem, User
)
from app.core.auth import hash_password
from app.services.fmea_engine import calculate_rpn, calculate_action_priority
from app.core.logging import logger

# Constants for realistic automotive closure & sealing engineering
PROGRAM_CONFIGS = [
    ("P-EP32", "Aurora EV SUV", "EV-800V-Platform", "Proto-A", "2027-06-30", "Dr. Wei Chen", "Ying Zhao", "Global"),
    ("P-C01", "Sedan C-Class Pure", "Modular-EV", "Pre-series-B", "2026-12-15", "Marcus Lindholm", "Liang Zhang", "China/EU"),
    ("P-T08", "Titan Off-road Pickup", "Ladder-Frame-PHEV", "Proto-A", "2027-11-20", "Frank Becker", "Tao Hu", "US-FMVSS/Global"),
    ("P-V09", "Vanguard MPV Executive", "EV-Comfort-Platform", "PPAP", "2026-09-01", "Hao Wang", "Elena Rostova", "China"),
    ("P-E05", "Echo Compact Urban EV", "Small-EV-Arch", "SOP", "2025-10-10", "Junichi Sato", "Mei Lin", "Global"),
    ("P-G07", "Grand Tourer Coupe", "High-Perf-Platform", "Pre-series-B", "2027-03-31", "Antoine Dubois", "Wei Chen", "EU-ECE"),
    ("P-M03", "Metro Delivery Van", "Commercial-EV", "PPAP", "2026-11-01", "Klaus Fischer", "Peng Liu", "Global"),
    ("P-K04", "Kestrel Sportback", "Modular-EV", "Concept", "2028-04-15", "Sarah Jenkins", "Guang Wang", "US-FMVSS"),
    ("P-N11", "Nebula Luxury Crossover", "EV-800V-Platform", "Proto-A", "2027-08-15", "Feng Zhou", "Anna Weber", "Global"),
    ("P-Z12", "Zenith Flagship Limousine", "Ultra-Luxury-EV", "Pre-series-B", "2027-01-30", "Robert Meier", "Liang Zhang", "Global"),
    ("P-R06", "Ranger Extreme 4x4", "Ladder-Frame-PHEV", "Concept", "2028-09-30", "Dirk Van Der Meer", "Tao Hu", "Global"),
    ("P-S02", "Solaris Solar-Assisted Sedan", "Aero-Eco-EV", "Proto-A", "2027-10-15", "Liwei Sun", "Ying Zhao", "China/EU")
]

SUBSYSTEMS = [
    "Front Door Closure",
    "Rear Door Closure",
    "Power Tailgate System",
    "Frameless Window System",
    "Primary Body Seal",
    "Secondary Acoustic Weatherstrip",
    "Water Deflector & Drainage",
    "Door Hinge & Check Link",
    "Glass Regulator Module",
    "Tailgate Spindle & Cinch Latch"
]

CATEGORIES = [
    "Mechanical",
    "Elastomer / Sealing",
    "Electro-Mechanical",
    "Glass & Guiding",
    "Structural / Hinge"
]

SUPPLIERS = [
    "Cooper Standard", "Hutchinson Automotive", "Brose Group",
    "Kiekert AG", "Fuyao Glass Industry", "Webasto",
    "Inalfa Roof Systems", "Stabilus", "Magna Closures", "Freudenberg Sealing"
]

MATERIALS = [
    "EPDM Dense + Sponge 45 Shore A",
    "EPDM Co-extruded with POM Clip",
    "Galvanized Steel DP600",
    "Cold Rolled High Strength Steel CR240LA",
    "Aluminum 6082-T6 Extrusion",
    "Tempered Laminated Acoustic Glass 4.8mm",
    "POM Polyoxymethylene Resin",
    "PA66-GF30 Reinforced Polymer",
    "Stainless Steel 304 Hinge Pin",
    "Silicone Coated Sponge Rubber"
]

CLOSURE_FAILURE_MODES = [
    ("Door weatherstrip water leakage during high-pressure car wash", "EPDM sponge bulb compression set under high clamping load", "Cabin carpet soaking, BCM connector wet oxidation", 8, 5, 4),
    ("Frameless window regulator pinch force exceeding 100N limit", "Hall sensor count mismatch due to cold grease friction in motor", "Risk of passenger finger trapping, ECE R21 non-compliance", 9, 4, 3),
    ("Tailgate electric spindle strut mechanical stall at -40°C", "Spindle drive ball screw lube oil dynamic viscosity freeze", "Power tailgate unable to open/close in cold climate regions", 7, 6, 4),
    ("Door sag exceeding 2.0mm after 100k slam cycles", "Upper hinge pin bush abrasive wear and mounting bolt loosening", "Door latch striker misalignment, excessive closing effort", 6, 5, 3),
    ("A-pillar secondary seal wind noise whistling at 120km/h", "Seal lip tip separation from body flange under turbulent draft", "Cabin high-frequency whistling noise > 68 dBA, customer complaint", 5, 7, 5),
    ("Tailgate cinch motor latch microswitch false door-open signal", "Water ingress through latch drain hole corroding gold contacts", "Instrument cluster false door warning, cabin light drain battery", 7, 4, 3),
    ("Window glass shudder during express up/down motion", "Glass run channel flocking fiber stripping and high friction", "Window motor thermal overload protection trigger, jerky movement", 4, 6, 4),
    ("Door inner bottom hem flange sealing mastic cracking", "Hem seal curing temperature profile mismatch on paint shop line", "Lower door skin corrosion and premature rust penetration", 8, 3, 5),
    ("Door check link detent hold force drop below 80N on 15° slope", "Check link torsion arm nylon overmold fatigue fracture", "Door self-closing on hill slope, striking passenger leg", 8, 4, 3),
    ("Tailgate gas damper rapid gas spring oil leakage", "Piston rod micro-scratch under dust road salt spray exposure", "Uncontrolled tailgate dropping down, safety hazard to operator", 9, 3, 4),
    ("Secondary door seal ice freezing adherence tearing", "Surface slip-coat coating peeling after UV ozone aging", "Door seal rubber torn when opening door after freezing rain", 6, 6, 4),
    ("Sunroof / Tailgate water drainage hose pop-off under backpressure", "Hose barb insertion depth insufficient, missing clamp spring", "Headliner water stain, panoramic roof electronics short", 7, 4, 3)
]

STANDARDS_AND_TESTS = [
    ("QC/T 627-2022", "Side Door Slam Durability 100,000 Cycles", "Door sag <= 1.5mm; latch function nominal; no seal tear", 3),
    ("ISO 20653 IPX9K", "High Pressure Water Wash Water Tightness", "No water ingress past secondary sealing line into cabin", 4),
    ("GMW 14147", "Door Weatherstrip Cold Compression Set (-40°C)", "Permanent compression set <= 25% after 200h soak", 6),
    ("ECE R21 / FMVSS 118", "Power Window Anti-Pinch Force Test", "Pinch reversal force < 100N between 4mm and 200mm opening", 5),
    ("SAE J1455", "Tailgate Environmental Vibration & Thermal Cycling", "No structural loosening; electrical cinch operate normal", 3),
    ("ISO 20567-1", "Closure Lower Surface Stone Chip Resistance", "Flaking rating <= 1.5; zero substrate rust exposure", 4),
    ("PV 3929", "Acoustic Sealing Wind Noise Chamber Evaluation", "Overall sound pressure level delta <= 1.5 dBA at 140km/h", 2),
    ("DIN 75220", "Polymer & Flocking Aging under Solar Simulation", "No color fade delta E < 2.0; flocking peeling force > 15N/cm", 4),
    ("GMW 14872", "Cyclic Corrosion Laboratory Test (80 Cycles)", "Zero red rust on hinges, latch strikers, and hem edges", 5),
    ("ISO 16750-2", "Power Tailgate Actuator Electrical Transient Overload", "Normal actuator operation without thermal cutout under 16V", 3)
]

FACILITIES = [
    "Closure Durability Rig #1 (Robot Arm)",
    "Environmental Dyno Chamber #2 (-40°C to 85°C)",
    "Aeroacoustic Wind Tunnel #1",
    "Dynamic Rain & Car Wash Test Booth #3",
    "Electrodynamic Vibration 6-DOF Rig",
    "CATARC Automotive Quality Lab",
    "Material Physics & Rubber Lab #4"
]

ENGINEERS = [
    "Dr. Wei Chen", "Marcus Lindholm", "Liang Zhang", "Elena Rostova",
    "Frank Becker", "Tao Hu", "Hao Wang", "Junichi Sato", "Mei Lin",
    "Antoine Dubois", "Klaus Fischer", "Peng Liu", "Sarah Jenkins",
    "Guang Wang", "Feng Zhou", "Anna Weber", "Liwei Sun", "Ying Zhao"
]


def seed_database():
    """Generates all models and populates realistic datasets."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 0. Seed RBAC Users
        users_config = [
            ("admin", "admin@eql-auto.internal", "admin123", "System Administrator", "admin", "Quality Systems IT"),
            ("quality_lead", "lead.qm@eql-auto.internal", "quality123", "Ying Zhao (Chief QM)", "quality_lead", "Quality Assurance"),
            ("design_eng", "designer@eql-auto.internal", "engineer123", "Dr. Wei Chen (Lead Engineer)", "design_eng", "Closures & Body Engineering"),
            ("auditor", "auditor@eql-auto.internal", "audit123", "Elena Rostova (Compliance Auditor)", "auditor", "Independent Audit & Compliance")
        ]
        for uname, email, pwd, fname, role, dept in users_config:
            if not db.query(User).filter_by(username=uname).first():
                db.add(User(
                    username=uname,
                    email=email,
                    hashed_password=hash_password(pwd),
                    full_name=fname,
                    role=role,
                    department=dept,
                    is_active=True
                ))
        db.commit()

        # Check existing count
        existing_programs = db.query(Program).count()
        if existing_programs >= 10:
            logger.info("Database already seeded with programs and users. Ready.")
            return

        logger.info("Starting high-fidelity automotive database seeding...")

        # 1. Seed Programs (12 programs)
        programs = []
        for code, name, platform, phase, sop, lead, qm, market in PROGRAM_CONFIGS:
            p = Program(
                code=code,
                name=name,
                platform=platform,
                phase=phase,
                sop_date=sop,
                lead_engineer=lead,
                quality_manager=qm,
                target_market=market,
                description=f"Automotive project {name} ({code}) on platform {platform} targeting {market}."
            )
            db.add(p)
            programs.append(p)
        db.commit()
        for p in programs:
            db.refresh(p)
        logger.info(f"Seeded {len(programs)} programs.")

        # 2. Seed Parts (>= 220 parts, distributed across programs & closure subsystems)
        parts = []
        part_idx = 1
        for p in programs:
            # 18-22 parts per vehicle program
            part_count_for_p = random.randint(18, 22)
            for i in range(part_count_for_p):
                subsystem = SUBSYSTEMS[part_idx % len(SUBSYSTEMS)]
                category = CATEGORIES[part_idx % len(CATEGORIES)]
                supplier = SUPPLIERS[part_idx % len(SUPPLIERS)]
                material = MATERIALS[part_idx % len(MATERIALS)]
                part_no = f"{p.code[:4]}-{subsystem[:3].upper()}-{part_idx:04d}"
                part_name = f"{p.name.split()[0]} {subsystem} Component {part_idx}"
                safety = (subsystem in ["Tailgate Spindle & Cinch Latch", "Frameless Window System", "Door Hinge & Check Link"] and random.random() < 0.45)
                
                part = Part(
                    program_id=p.id,
                    part_number=part_no,
                    name=part_name,
                    subsystem=subsystem,
                    category=category,
                    supplier=supplier,
                    material=material,
                    revision=f"Rev {random.choice(['A.0', 'A.1', 'B.0', 'B.2', 'C.0'])}",
                    weight_kg=round(random.uniform(0.15, 14.5), 2),
                    safety_critical=safety
                )
                db.add(part)
                parts.append(part)
                part_idx += 1
        db.commit()
        for pt in parts:
            db.refresh(pt)
        logger.info(f"Seeded {len(parts)} parts.")

        # 3. Seed DFMEA (>= 350 records)
        dfmeas = []
        dfmea_idx = 1
        for pt in parts:
            # 1 to 3 DFMEA rows per part
            num_fmea = 2 if dfmea_idx % 2 == 0 else 1
            if dfmea_idx % 5 == 0:
                num_fmea = 3
            
            for _ in range(num_fmea):
                fm_template = CLOSURE_FAILURE_MODES[dfmea_idx % len(CLOSURE_FAILURE_MODES)]
                # Add slight random variations
                s = min(10, max(1, fm_template[3] + random.choice([-1, 0, 1])))
                o = min(10, max(1, fm_template[4] + random.choice([-1, 0, 1, 2])))
                d = min(10, max(1, fm_template[5] + random.choice([-1, 0, 1])))
                rpn = calculate_rpn(s, o, d)
                ap = calculate_action_priority(s, o, d)
                
                fmea_code = f"DFMEA-{pt.part_number}-{dfmea_idx:03d}"
                action_status = random.choice(["Open", "In Progress", "Implemented", "Verified", "Closed"])
                
                # If verified or closed, set post-action scores
                post_s, post_o, post_d, post_rpn = None, None, None, None
                if action_status in ["Implemented", "Verified", "Closed"]:
                    post_s = s
                    post_o = max(1, o - random.randint(1, 3))
                    post_d = max(1, d - random.randint(1, 2))
                    post_rpn = calculate_rpn(post_s, post_o, post_d)

                dfmea = DFMEA(
                    part_id=pt.id,
                    fmea_code=fmea_code,
                    item_function=f"{pt.name}: maintain structural, sealing, and kinematics integrity under vehicle lifecycle load.",
                    failure_mode=fm_template[0],
                    failure_effect=fm_template[2],
                    severity=s,
                    cause_mechanism=fm_template[1],
                    occurrence=o,
                    prevention_control=f"Standard design guideline ES-QA-09 for {pt.subsystem}; CAE simulation optimization.",
                    detection_control="Validation bench test under environmental chamber and endurance rig.",
                    detection=d,
                    rpn=rpn,
                    action_priority=ap,
                    recommended_action="Improve seal bulb geometry, wall thickness >= 1.5mm; upgrade motor torque margin.",
                    action_owner=random.choice(ENGINEERS),
                    target_date=(datetime.now() + timedelta(days=random.randint(15, 120))).strftime("%Y-%m-%d"),
                    action_status=action_status,
                    post_severity=post_s,
                    post_occurrence=post_o,
                    post_detection=post_d,
                    post_rpn=post_rpn
                )
                db.add(dfmea)
                dfmeas.append(dfmea)
                dfmea_idx += 1
                if len(dfmeas) >= 360:
                    break
            if len(dfmeas) >= 360:
                break
        db.commit()
        logger.info(f"Seeded {len(dfmeas)} DFMEA items.")

        # 4. Seed DVP&R Verification Plans (>= 550 records)
        dvprs = []
        dvpr_idx = 1
        for pt in parts:
            # 2 to 4 DVP&R plans per part
            for k in range(random.randint(2, 3)):
                std_info = STANDARDS_AND_TESTS[(dvpr_idx + k) % len(STANDARDS_AND_TESTS)]
                status = random.choice(["Planned", "In Progress", "Passed", "Failed", "Blocked"])
                start_dt = datetime.now() - timedelta(days=random.randint(20, 180))
                end_dt = start_dt + timedelta(days=random.randint(7, 30))
                
                dvp = DVPR(
                    program_id=pt.program_id,
                    part_id=pt.id,
                    plan_code=f"DVP-{pt.part_number}-{dvpr_idx:03d}",
                    test_phase=random.choice(["DV-A", "DV-B", "PV-C", "SOP-Confirm"]),
                    test_name=f"{pt.subsystem}: {std_info[1]}",
                    test_standard=std_info[0],
                    acceptance_criteria=std_info[2],
                    sample_size=std_info[3],
                    test_facility=random.choice(FACILITIES),
                    planned_start_date=start_dt.strftime("%Y-%m-%d"),
                    planned_end_date=end_dt.strftime("%Y-%m-%d"),
                    status=status,
                    responsible_engineer=random.choice(ENGINEERS)
                )
                db.add(dvp)
                dvprs.append(dvp)
                dvpr_idx += 1
                if len(dvprs) >= 560:
                    break
            if len(dvprs) >= 560:
                break
        db.commit()
        for dv in dvprs:
            db.refresh(dv)
        logger.info(f"Seeded {len(dvprs)} DVP&R verification plans.")

        # 5. Seed Test Runs (>= 1100 records)
        test_runs = []
        run_idx = 1
        for dv in dvprs:
            # 1 to 3 test runs per DVP plan
            num_runs = random.randint(1, 3)
            for r in range(num_runs):
                result = "Pass"
                if dv.status == "Failed" or (random.random() < 0.22):
                    result = random.choice(["Fail", "Marginal"])
                elif dv.status == "In Progress" and r == num_runs - 1:
                    result = "Marginal"
                
                # Realistic closure test telemetry
                temp = random.choice([-40.0, -20.0, 23.0, 45.0, 85.0])
                humidity = random.choice([30.0, 50.0, 85.0, 95.0])
                cycles = random.randint(5000, 100000)
                
                measurements = {
                    "closing_velocity_mps": round(random.uniform(0.8, 1.8), 2),
                    "residual_sag_mm": round(random.uniform(0.2, 2.5), 2),
                    "seal_cld_n_per_100mm": round(random.uniform(35.0, 110.0), 1),
                    "water_leak_ml_min": round(random.uniform(0.0, 15.0), 1) if result != "Pass" else 0.0,
                    "pinch_force_n": round(random.uniform(65.0, 135.0), 1) if "Window" in dv.test_name else None,
                    "sound_pressure_delta_dba": round(random.uniform(0.5, 4.2), 1)
                }
                
                fail_summary = None
                if result == "Fail":
                    fail_summary = f"Test failure at cycle {cycles}: {random.choice(['Water leakage penetrated through seal lip', 'Pinch force reached 118N > 100N threshold', 'Door sag measured 2.1mm exceeding 1.5mm spec', 'Latch cinch motor thermal cutout triggered'])}."
                elif result == "Marginal":
                    fail_summary = f"Warning: parameter near borderline tolerance at {temp}°C environment."

                test_date = (datetime.now() - timedelta(days=random.randint(1, 150))).strftime("%Y-%m-%d")

                tr = TestRun(
                    dvpr_id=dv.id,
                    run_number=f"RUN-{dv.plan_code}-{run_idx:04d}",
                    sample_id=f"SMP-{run_idx:05d}",
                    test_date=test_date,
                    test_facility=dv.test_facility,
                    operator=random.choice(ENGINEERS),
                    temperature_c=temp,
                    humidity_rh=humidity,
                    cycles_completed=cycles,
                    measurement_data=json.dumps(measurements),
                    result=result,
                    failure_summary=fail_summary,
                    report_file_url=f"/reports/{dv.plan_code}_run{run_idx}.pdf"
                )
                db.add(tr)
                test_runs.append(tr)
                run_idx += 1
                if len(test_runs) >= 1150:
                    break
            if len(test_runs) >= 1150:
                break
        db.commit()
        for tr in test_runs:
            db.refresh(tr)
        logger.info(f"Seeded {len(test_runs)} test runs.")

        # 6. Seed Engineering Issues (>= 520 records)
        issues = []
        issue_idx = 1
        failed_runs = [t for t in test_runs if t.result in ["Fail", "Marginal"]]
        
        # Link failed tests to issues first, then generate additional prototype issues
        for idx_run, frun in enumerate(failed_runs):
            parent_dv = db.query(DVPR).filter(DVPR.id == frun.dvpr_id).first()
            sev = random.choice(["S1-Critical", "S2-Major", "S2-Major", "S3-Minor"])
            stat = random.choice(["New", "Investigating", "Containment", "RootCauseVerified", "ActionImplemented", "ValidationPass", "Closed"])
            
            created_dt = datetime.now() - timedelta(days=random.randint(10, 140))
            due_dt = created_dt + timedelta(days=random.randint(14, 45))
            closed_dt = None
            if stat in ["Closed", "ValidationPass"]:
                closed_dt = (due_dt - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d")

            issue = EngineeringIssue(
                issue_code=f"ISS-2026-{issue_idx:04d}",
                program_id=parent_dv.program_id,
                part_id=parent_dv.part_id,
                test_run_id=frun.id,
                title=f"[{parent_dv.test_standard}] {parent_dv.test_name} failure during verification",
                severity=sev,
                status=stat,
                description=frun.failure_summary or f"Deviation observed during {parent_dv.test_name} testing.",
                occurrence_phase=random.choice(["DV-Testing", "PV-Trial", "Pre-SOP"]),
                containment_action="Sort stock parts, tighten supplier incoming inspection sampling to 100% CMM.",
                assignee=random.choice(ENGINEERS),
                reporter=frun.operator,
                due_date=due_dt.strftime("%Y-%m-%d"),
                closure_date=closed_dt
            )
            db.add(issue)
            issues.append(issue)
            issue_idx += 1
            if len(issues) >= 530:
                break

        # If more issues needed to reach >= 530
        while len(issues) < 530:
            rand_part = random.choice(parts)
            sev = random.choice(["S1-Critical", "S2-Major", "S3-Minor", "S4-Cosmetic"])
            stat = random.choice(["New", "Investigating", "Containment", "RootCauseVerified", "ActionImplemented", "Closed"])
            created_dt = datetime.now() - timedelta(days=random.randint(5, 120))
            due_dt = created_dt + timedelta(days=random.randint(15, 60))
            closed_dt = due_dt.strftime("%Y-%m-%d") if stat == "Closed" else None
            
            issue = EngineeringIssue(
                issue_code=f"ISS-2026-{issue_idx:04d}",
                program_id=rand_part.program_id,
                part_id=rand_part.id,
                test_run_id=None,
                title=f"Prototype assembly interference / acoustic anomaly on {rand_part.name}",
                severity=sev,
                status=stat,
                description=f"Field or pilot build issue observed in {rand_part.subsystem}. Gap and flushness out of tolerance +0.8mm.",
                occurrence_phase=random.choice(["Proto-Build", "PV-Trial", "Pre-SOP"]),
                containment_action="Shim adjustment applied on hinge mounting pillar; supplier notified.",
                assignee=random.choice(ENGINEERS),
                reporter=random.choice(ENGINEERS),
                due_date=due_dt.strftime("%Y-%m-%d"),
                closure_date=closed_dt
            )
            db.add(issue)
            issues.append(issue)
            issue_idx += 1

        db.commit()
        for iss in issues:
            db.refresh(iss)
        logger.info(f"Seeded {len(issues)} engineering issues.")

        # 7. Seed Root Cause Analyses (for issues in investigating/verified/closed)
        root_causes = []
        analyst_idx = 0
        for iss in issues:
            if iss.status in ["RootCauseVerified", "ActionImplemented", "ValidationPass", "Closed"] or (random.random() < 0.4):
                direct_cause = f"Excessive mechanical tolerance stack-up or material formulation variance in {iss.title[:30]}."
                w1 = "Why did the test or component fail? Because measured value exceeded acceptance criteria limit."
                w2 = "Why did it exceed limit? Because localized stress / contact pressure collapsed under thermal deflection."
                w3 = "Why did thermal deflection occur? Because thermal expansion coefficients between POM bracket and aluminum frame were not compensated."
                w4 = "Why was it not compensated? Because preliminary FEA boundary condition assumed constant 20°C."
                w5 = "Why did FEA assume constant 20°C? Because temperature sweep simulation standard was not enforced in design checklist."
                
                rc = RootCauseAnalysis(
                    issue_id=iss.id,
                    analysis_method=random.choice(["5-Why", "Ishikawa-Fishbone", "FTA"]),
                    direct_cause=direct_cause,
                    why_1=w1,
                    why_2=w2,
                    why_3=w3,
                    why_4=w4,
                    why_5=w5,
                    systemic_root_cause="Design validation simulation guideline lacked multi-physics extreme temperature range criteria.",
                    fishbone_man="Operator torque gun angle deviation 5°",
                    fishbone_machine="Curing oven zone 3 temperature sensor drift +8°C",
                    fishbone_material="EPDM sponge density batch fluctuation 0.48 to 0.53 g/cm3",
                    fishbone_method="Work instruction revision out of sync with engineering bulletin",
                    fishbone_measurement="CMM optical scanning lighting reflection noise",
                    fishbone_environment="Chamber relative humidity exceeded 90% RH condensation point",
                    verification_method="Repeat temperature cycle test with compensated CAD model and revised seal hardness.",
                    verification_result="Confirmed" if iss.status in ["Closed", "ValidationPass"] else "Pending",
                    analyst=iss.assignee,
                    analyzed_at=(datetime.now() - timedelta(days=random.randint(5, 50))).strftime("%Y-%m-%d")
                )
                db.add(rc)
                root_causes.append(rc)
                analyst_idx += 1
        db.commit()
        logger.info(f"Seeded {len(root_causes)} root cause analyses.")

        # 8. Seed Engineering Changes (>= 220 records)
        changes = []
        change_idx = 1
        for iss in issues:
            if iss.status in ["ActionImplemented", "ValidationPass", "Closed"] or (random.random() < 0.25):
                part = db.query(Part).filter(Part.id == iss.part_id).first()
                if not part:
                    continue
                
                c_type = random.choice(["Design-Mod", "Material-Change", "Tooling-Tune", "Tolerance-Relaxation"])
                stat = random.choice(["Draft", "Review-Eng", "Review-CostTooling", "Approved", "Implemented"])
                cost = round(random.uniform(-45.0, 180.0), 2)
                weight = round(random.uniform(-0.35, 0.65), 3)
                homol = (part.safety_critical or random.random() < 0.15)
                
                app_dt = None
                imp_dt = None
                approver = None
                if stat in ["Approved", "Implemented"]:
                    approver = random.choice(ENGINEERS)
                    app_dt = (datetime.now() - timedelta(days=random.randint(5, 40))).strftime("%Y-%m-%d")
                orig_rev = part.revision
                post_rev = f"Rev {chr(ord(part.revision[4]) + 1)}.0" if len(part.revision) >= 5 else "Rev B.0"
                if stat == "Implemented":
                    imp_dt = (datetime.now() - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d")
                    part.revision = post_rev

                ecr = EngineeringChange(
                    change_code=f"ECR-2026-{change_idx:04d}",
                    program_id=part.program_id,
                    part_id=part.id,
                    issue_id=iss.id,
                    title=f"ECR: Optimize {part.name} to eliminate {iss.title[:35]}",
                    change_type=c_type,
                    reason=f"Corrective engineering modification prompted by issue {iss.issue_code}. "
                           f"Redesign seal cross-section / structural ribs to withstand slam fatigue.",
                    pre_change_rev=orig_rev,
                    post_change_rev=post_rev,
                    cost_impact_rmb=cost,
                    weight_impact_kg=weight,
                    tooling_lead_weeks=random.randint(2, 12),
                    requires_homologation=homol,
                    requires_dvp_retest=True,
                    approval_status=stat,
                    initiator=iss.assignee,
                    approver=approver,
                    approval_date=app_dt,
                    implementation_date=imp_dt
                )
                db.add(ecr)
                changes.append(ecr)
                change_idx += 1
                if len(changes) >= 230:
                    break
        
        # If needed to reach 230 changes
        while len(changes) < 230:
            rand_part = random.choice(parts)
            ecr = EngineeringChange(
                change_code=f"ECR-2026-{change_idx:04d}",
                program_id=rand_part.program_id,
                part_id=rand_part.id,
                issue_id=None,
                title=f"Value Engineering / Tooling Refinement for {rand_part.name}",
                change_type="Design-Mod",
                reason="Weight reduction and die-draw angle optimization for high-speed stamping.",
                pre_change_rev="Rev A.1",
                post_change_rev="Rev A.2",
                cost_impact_rmb=-12.5,
                weight_impact_kg=-0.08,
                tooling_lead_weeks=3,
                requires_homologation=False,
                requires_dvp_retest=False,
                approval_status="Approved",
                initiator=random.choice(ENGINEERS),
                approver="Dr. Wei Chen",
                approval_date="2026-04-10",
                implementation_date="2026-04-20"
            )
            db.add(ecr)
            changes.append(ecr)
            change_idx += 1

        db.commit()
        logger.info(f"Seeded {len(changes)} engineering changes.")

        # 9. Seed Knowledge Base (Engineering Lessons Learned, Standards & Guidelines)
        kb_articles = [
            ("KB-SEAL-001", "车门主密封条在高压洗车工况下的微量进水机理及对策", "Primary Body Seal", "Lesson-Learned",
             "water-leak,car-wash,EPDM,sponge-bulb",
             "在高压清洗机（100 bar, 距离300mm）垂直冲击A柱及车门上窗框夹角时，若密封条海绵泡管在动态风阻或高压水射流下发生局部倾覆（Rolling），会导致密封唇边反转造成水幕侵入。对策：1. 在A柱迎水拐角增设定位限位销（Clip spacing <= 85mm）；2. 将海绵泡管基底硬度由40 Shore A提升至50 Shore A，并设计双唇阻水槽（Double-lip barrier）。",
             "车门密封条 漏水 高压清洗 A柱 泡管倾覆 EPDM", "ES-QA-SEAL-012", "All EV/PHEV Programs", "Dr. Wei Chen"),
            
            ("KB-REG-002", "无框车门玻璃升降器防夹力在极端低温（-40℃）下的标定规范", "Frameless Window System", "Standard-Spec",
             "anti-pinch,ECE-R21,window-regulator,low-temp",
             "无框车门玻璃在-40℃工况下，玻璃导槽植绒条与EPDM收缩硬化，动摩擦系数由0.18跃升至0.45以上。如果电机控制器防夹算法依然沿用常温电流积分斜率，易引发低温误防夹或反向力超过ECE R21规定的100N阈值。规范：必须根据车门内总线环境温度传感器动态调节防夹触发阈值查表曲线（Temperature-compensated Hall algorithm）。",
             "升降器 防夹 低温 ECE R21 导槽摩擦力 无框玻璃", "ECE R21 / QC-T 627", "P-EP32, P-C01, P-Z12", "Marcus Lindholm"),
            
            ("KB-TAIL-003", "电动尾门双撑杆同步失步导致尾门扭曲变形的失效分析与控制", "Power Tailgate System", "Failure-Case",
             "tailgate,electric-spindle,sync-error,deformation",
             "某车型在极热（85℃暴晒）和左右路面斜坡停放工况下，左右电动撑杆行星齿轮箱内部阻尼不平衡，导致左撑杆速度比右撑杆快18mm/s。累积行程导致碳纤维/钢混尾门产生5.2mm扭转，触发锁扣错位并磨损D柱油漆。对策：采用高精度双霍尔脉冲闭环控制（Dual Hall synchronization loop <= 3 pulses diff），并强化撑杆自调心球头铰接刚度。",
             "电动尾门 双撑杆 同步误差 扭转变形 霍尔控制", "PRTS-FA-2025-089", "P-V09, P-T08", "Liang Zhang"),

            ("KB-HINGE-004", "高强度铝合金车门铰链10万次开关耐久下垂量控制准则", "Door Hinge & Check Link", "Design-Guideline",
             "door-sag,hinge-fatigue,durability,slam-test",
             "在车门10万次关闭耐久试验（关闭初速度1.5 m/s）后，下垂量（Door sag）不得超过1.5mm。试验失效主要集中在上铰链销轴无油衬套的磨损剥落与A柱内板加强件的微观疲劳裂纹。准则：1. 铰链销轴必须采用渗碳淬火304不锈钢，硬度>=HRC 55；2. A柱铰链安装安装面内板加强件厚度须>=2.5mm，螺栓预紧力矩>=48 Nm，并打胶固定。",
             "铰链 下垂量 10万次 疲劳 耐久 衬套 预紧力矩", "QC/T 627-2022", "All Vehicle Programs", "Frank Becker"),

            ("KB-AERO-005", "高速巡航（140km/h）后视镜及三角窗区域气动风噪啸叫排查指南", "Secondary Acoustic Weatherstrip", "Best-Practice",
             "wind-noise,acoustic,weatherstrip,whistle",
             "风洞试验表明，车速超过120km/h时，前车门三角窗高音喇叭护罩与车身钣金之间的副密封条若存在小于0.5mm的局部装配间隙，会形成亥姆霍兹共振腔（Helmholtz resonance），产生2.5kHz-4kHz的人耳敏感啸叫声。排查方法：使用高灵敏度声学相机定位声源，三角窗外压条接缝处注塑一体成型，取消分体式拼接橡胶垫。",
             "风噪 啸叫 三角窗 声学相机 亥姆霍兹共振 副密封", "PV 3929 / Wind-Tunnel-Manual", "P-EP32, P-C01, P-G07", "Antoine Dubois"),

            ("KB-CORR-006", "车门下边缘翻边咬口（Hem Flange）电泳液残留与防腐密封胶工艺窗口", "Water Deflector & Drainage", "Standard-Spec",
             "hem-flange,corrosion,paint-shop,sealer",
             "车门外板与内板折边咬口处若密封胶涂布不连续或断胶，电泳底漆无法完全渗透进入咬口内部（渗透率不足50%），酸性清洗液或潮湿盐雾滞留，2年后会导致车门下边缘起泡穿孔。标准：1. 折边胶必须采用双组分高粘度环氧/聚氨酯结构胶；2. 涂胶截面积>=8mm²，100%全自动机器人视觉检测连续性，严禁出现气泡和漏胶。",
             "折边胶 翻边 咬口 防腐 盐雾 穿孔 电泳", "ISO 14993 / GMW 14872", "All Steel/Al Closures", "Elena Rostova")
        ]

        for doc_code, title, subsys, cat, tags, content, kw, src, prog, auth in kb_articles:
            kb = KnowledgeItem(
                doc_code=doc_code,
                title=title,
                subsystem=subsys,
                category=cat,
                tags=tags,
                content=content,
                keywords=kw,
                source_reference=src,
                applicable_programs=prog,
                author=auth
            )
            db.add(kb)
        db.commit()
        logger.info(f"Seeded {len(kb_articles)} engineering knowledge articles.")

        logger.info("Successfully completed automotive test database seeding with all realistic domain datasets!")

    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}", exc_info=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
