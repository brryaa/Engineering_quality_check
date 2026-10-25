def test_full_engineering_quality_lifecycle(client):
    # 1. Program Management
    prog = client.post("/api/v1/programs", json={
        "code": "P-FULL-CYCLE",
        "name": "Full Lifecycle Vehicle",
        "platform": "EV-Pure-800V",
        "phase": "Proto-A",
        "sop_date": "2027-08-30",
        "lead_engineer": "Dr. Wei Chen",
        "quality_manager": "Ying Zhao",
        "target_market": "Global",
        "description": "Full end-to-end quality test model"
    }).json()

    # 2. Parts Management
    part = client.post("/api/v1/parts", json={
        "program_id": prog["id"],
        "part_number": "PT-FULL-DOOR-01",
        "name": "Front Door Hinge Assembly",
        "subsystem": "Door Hinge & Check Link",
        "category": "Mechanical",
        "supplier": "Brose",
        "material": "High Strength Steel DP600",
        "revision": "Rev A.0",
        "weight_kg": 2.8,
        "safety_critical": True
    }).json()
    assert part["revision"] == "Rev A.0"

    # 3. DFMEA Risk Analysis
    dfmea = client.post("/api/v1/dfmea", json={
        "part_id": part["id"],
        "fmea_code": "DFMEA-FULL-001",
        "item_function": "Retain door sag within 1.5mm under 100k slam cycles",
        "failure_mode": "Hinge upper pin bronze bush excessive wear",
        "failure_effect": "Door sag > 2.0mm, striker misalignment",
        "severity": 8,
        "cause_mechanism": "Bush wall thickness inadequate (1.0mm) and high contact pressure",
        "occurrence": 7,
        "prevention_control": "CAD load calculation",
        "detection_control": "Durability bench test",
        "detection": 5,
        "recommended_action": "Increase bush wall thickness to 1.8mm and switch to sintered bronze"
    }).json()
    assert dfmea["rpn"] == 8 * 7 * 5  # 280
    assert dfmea["action_priority"] == "High"

    # 4. DVP&R Verification Plan
    dvp = client.post("/api/v1/dvpr", json={
        "program_id": prog["id"],
        "part_id": part["id"],
        "plan_code": "DVP-FULL-001",
        "test_phase": "DV-A",
        "test_name": "Door 100k Slam Durability",
        "test_standard": "QC/T 627-2022",
        "acceptance_criteria": "Door sag <= 1.5mm after 100,000 slams",
        "sample_size": 3,
        "test_facility": "Closure Rig Bench #1",
        "planned_start_date": "2026-10-01",
        "planned_end_date": "2026-10-25",
        "status": "Planned",
        "responsible_engineer": "Frank Becker"
    }).json()

    # 5. Test Run Execution (Failure occurs at cycle 65,000)
    test_run = client.post("/api/v1/tests", json={
        "dvpr_id": dvp["id"],
        "run_number": "RUN-FULL-001",
        "sample_id": "SMP-FULL-H01",
        "test_date": "2026-10-18",
        "test_facility": "Closure Rig Bench #1",
        "operator": "Frank Becker",
        "temperature_c": 23.0,
        "humidity_rh": 45.0,
        "cycles_completed": 65000,
        "measurement_data": '{"residual_sag_mm": 2.35, "closing_speed_mps": 1.5}',
        "result": "Fail",
        "failure_summary": "Door sag reached 2.35mm at cycle 65,000 exceeding 1.5mm spec threshold."
    }).json()
    assert test_run["result"] == "Fail"

    # Verify DVP status automatically synced to Failed
    dvp_check = client.get(f"/api/v1/dvpr/{dvp['id']}").json()
    assert dvp_check["status"] == "Failed"

    # 6. Issue Tracking (PRTS Ticket)
    issue = client.post("/api/v1/issues", json={
        "issue_code": "ISS-FULL-001",
        "program_id": prog["id"],
        "part_id": part["id"],
        "test_run_id": test_run["id"],
        "title": "Door sag 2.35mm failure at 65k cycles",
        "severity": "S2-Major",
        "status": "Investigating",
        "description": test_run["failure_summary"],
        "occurrence_phase": "DV-Testing",
        "containment_action": "Freeze hinge tooling sign-off",
        "assignee": "Dr. Wei Chen",
        "reporter": "Frank Becker",
        "due_date": "2026-11-15"
    }).json()
    assert issue["has_root_cause"] is False

    # 7. Root Cause Analysis (5-Why)
    rc = client.post("/api/v1/root-cause", json={
        "issue_id": issue["id"],
        "analysis_method": "5-Why",
        "direct_cause": "Upper hinge bronze bush bore ovalization under lateral impact",
        "why_1": "Why did door sag exceed 1.5mm? Because hinge pin pivoted off-axis.",
        "why_2": "Why did pin pivot off-axis? Because the bronze bush bore wore 0.8mm unevenly.",
        "why_3": "Why did bush wear unevenly? Because contact stress exceeded bush material compressive yield strength.",
        "why_4": "Why did contact stress exceed limit? Because bush length and thickness were undersized in initial lightweighting.",
        "why_5": "Why was it undersized? Because CAE model simplified the slam shock deceleration peak load by 35%.",
        "systemic_root_cause": "Hinge dynamic slam FEA load boundary standard did not incorporate 1.5 m/s velocity peak spike.",
        "verification_method": "Prototype with 1.8mm sintered bush and updated FEA model tested on rig.",
        "verification_result": "Confirmed",
        "analyst": "Dr. Wei Chen",
        "analyzed_at": "2026-10-22"
    }).json()
    assert rc["verification_result"] == "Confirmed"

    # Issue status promoted to RootCauseVerified
    issue_verified = client.get(f"/api/v1/issues/{issue['id']}").json()
    assert issue_verified["status"] == "RootCauseVerified"
    assert issue_verified["has_root_cause"] is True

    # 8. Engineering Change Management (ECR / ECO)
    ecr = client.post("/api/v1/changes", json={
        "change_code": "ECR-FULL-001",
        "program_id": prog["id"],
        "part_id": part["id"],
        "issue_id": issue["id"],
        "title": "ECR: Upgrade Hinge Bush Thickness and Material",
        "change_type": "Design-Mod",
        "reason": "Corrective action for issue ISS-FULL-001 to resolve door sag durability failure.",
        "pre_change_rev": "Rev A.0",
        "post_change_rev": "Rev B.0",
        "cost_impact_rmb": 2.2,
        "weight_impact_kg": 0.04,
        "tooling_lead_weeks": 3,
        "requires_homologation": False,
        "requires_dvp_retest": True,
        "approval_status": "Draft",
        "initiator": "Dr. Wei Chen"
    }).json()

    # Approve and Implement Change
    client.put(f"/api/v1/changes/{ecr['id']}", json={"approval_status": "Approved", "approver": "Chief Engineer"})
    client.put(f"/api/v1/changes/{ecr['id']}", json={"approval_status": "Implemented"})

    # Check Part revision was automatically updated to Rev B.0
    part_after_ecr = client.get(f"/api/v1/parts/{part['id']}").json()
    assert part_after_ecr["revision"] == "Rev B.0"

    # Close the Issue
    client.put(f"/api/v1/issues/{issue['id']}", json={"status": "Closed"})
    issue_closed = client.get(f"/api/v1/issues/{issue['id']}").json()
    assert issue_closed["status"] == "Closed"
    assert issue_closed["closure_date"] is not None

    # 9. R&D Quality Statistics Dashboard
    stats = client.get(f"/api/v1/dashboard/stats?program_id={prog['id']}").json()
    assert stats["total_programs"] == 1
    assert stats["total_parts"] == 1
    assert stats["total_dfmeas"] == 1
    assert stats["total_dvprs"] == 1
    assert stats["total_test_runs"] == 1
    assert stats["total_issues"] == 1
    assert stats["total_changes"] == 1
    assert stats["total_change_cost_impact_rmb"] == 2.2
    assert stats["changes_by_status"]["Implemented"] == 1
    assert stats["issue_status_counts"]["Closed"] == 1

    # 10. Engineering Knowledge Retrieval
    kb = client.post("/api/v1/knowledge", json={
        "doc_code": "KB-FULL-HINGE-01",
        "title": "高载荷车门铰链衬套动态冲击下垂量设计经验库",
        "subsystem": "Door Hinge & Check Link",
        "category": "Lesson-Learned",
        "tags": "hinge,door-sag,bush,fatigue",
        "content": "当关闭初速度达到1.5m/s时，铰链衬套壁厚必须>=1.8mm，建议使用烧结青铜自润滑材质，并在CAE边界考虑35%动态尖峰系数。",
        "keywords": "铰链 衬套 下垂量 烧结青铜 疲劳 动态冲击",
        "source_reference": "ISS-FULL-001 / ECR-FULL-001",
        "applicable_programs": "P-FULL-CYCLE",
        "author": "Dr. Wei Chen"
    }).json()

    # Search knowledge item
    search_res = client.get("/api/v1/knowledge?search=烧结青铜").json()
    assert search_res["total"] >= 1
    assert any(item["doc_code"] == "KB-FULL-HINGE-01" for item in search_res["items"])
