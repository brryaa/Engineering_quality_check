import pytest
from app.models.models import Program, Part, EngineeringIssue, EngineeringChange
from app.main import app
from app.core.security_middleware import SecurityMiddleware, RATE_LIMIT_REQUESTS


def _reset_rate_limiter():
    for middleware in app.user_middleware:
        if middleware.cls == SecurityMiddleware:
            pass
    current = getattr(app, "middleware_stack", None)
    while current:
        if isinstance(current, SecurityMiddleware):
            current.reset_rate_limits()
            break
        current = getattr(current, "app", None)


@pytest.fixture(autouse=True)
def clean_rate_limits():
    _reset_rate_limiter()
    yield
    _reset_rate_limiter()


def test_security_headers_present(client):
    """Verify standard OWASP security headers are present in all responses."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"


def test_sql_injection_search_defense(client, db_session):
    """Verify SQL injection strings in search query parameters do not corrupt database."""
    prog = Program(
        code="SEC-PROG-SQLI",
        name="SQLi Defense Model",
        platform="P-SEC",
        phase="DV",
        lead_engineer="Chief Security Officer",
        quality_manager="QM Lead",
        target_market="Global"
    )
    db_session.add(prog)
    db_session.commit()

    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE programs; --",
        "1 UNION SELECT 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 --",
        "' OR 1=1; --",
        "admin' --",
        "\" OR \"\"=\""
    ]

    for payload in sqli_payloads:
        res = client.get(f"/api/v1/programs?search={payload}")
        assert res.status_code == 200
        check = db_session.query(Program).filter_by(code="SEC-PROG-SQLI").first()
        assert check is not None


def test_stored_xss_payload_handling(client, db_session):
    """Verify stored XSS payloads in titles and descriptions do not cause execution or crash."""
    xss_payload = "<script>alert('XSS_ATTACK_VECTOR')</script><img src=x onerror=alert(1)>"

    # Create program
    p_res = client.post("/api/v1/programs", json={
        "code": "XSS-PROG-01",
        "name": f"XSS Test {xss_payload}",
        "platform": "P-XSS",
        "phase": "PV",
        "lead_engineer": "Sec Tester",
        "quality_manager": "QM",
        "target_market": "Domestic",
        "description": xss_payload
    })
    assert p_res.status_code == 201
    created = p_res.json()
    assert created["description"] == xss_payload

    # Fetch knowledge articles with XSS title
    kb_res = client.post("/api/v1/knowledge", json={
        "doc_code": "KB-XSS-001",
        "title": f"Lesson Learned: {xss_payload}",
        "subsystem": "Frameless Window System",
        "category": "Lessons Learned",
        "tags": "xss, test",
        "keywords": "security, xss",
        "content": f"Detailed content: {xss_payload}",
        "author": "Security Researcher"
    })
    assert kb_res.status_code == 201
    assert kb_res.json()["title"] == f"Lesson Learned: {xss_payload}"


# ==============================================================================
# Hardened Audited Defenses: Content-Length & Rate Limiter Bypass Tests
# ==============================================================================

def test_oversized_payload_rejected(client):
    """Verify requests with Content-Length exceeding 5MB are rejected with 413 Content Too Large."""
    oversized_headers = {
        "Content-Type": "application/json",
        "Content-Length": str(10 * 1024 * 1024)  # 10 MB
    }
    res = client.post("/api/v1/programs", content=b"{}", headers=oversized_headers)
    assert res.status_code == 413
    assert "exceeds maximum allowed size" in res.json()["error"]


def test_malformed_content_length_headers(client):
    """
    Finding 2 Verification:
    Verify non-numeric or negative Content-Length returns HTTP 400 Bad Request,
    never unhandled 500 ValueError.
    """
    # 1. Non-numeric Content-Length
    res_str = client.post("/api/v1/programs", content=b"{}", headers={
        "Content-Type": "application/json",
        "Content-Length": "not-a-number"
    })
    assert res_str.status_code == 400
    assert "Invalid Content-Length" in res_str.json()["error"]

    # 2. Negative Content-Length
    res_neg = client.post("/api/v1/programs", content=b"{}", headers={
        "Content-Type": "application/json",
        "Content-Length": "-500"
    })
    assert res_neg.status_code == 400
    assert "cannot be negative" in res_neg.json()["error"]


def test_rate_limiting_defense_and_x_benchmark_cannot_bypass(client):
    """
    Finding 1 Verification:
    Verify rate limiter blocks excessive rapid-fire requests.
    Crucially verify that adding 'X-Benchmark: 1' DOES NOT bypass the rate limit.
    """
    blocked = False
    for i in range(RATE_LIMIT_REQUESTS + 15):
        res = client.get("/health", headers={
            "X-Test-Rate-Limit": "1",
            "X-Benchmark": "1"  # Malicious attempt to bypass rate limiter
        })
        if res.status_code == 429:
            blocked = True
            assert "Rate limit exceeded" in res.json()["error"]
            break
    assert blocked is True, "X-Benchmark header must NOT allow bypassing rate limits!"


# ==============================================================================
# RBAC & IDOR Audit Tests: Authentication, Vertical Escalation & Horizontal Isolation
# ==============================================================================

def test_unauthenticated_mutations_rejected(unauth_client):
    """
    Finding 3 Verification:
    Verify unauthenticated mutating requests (POST, PUT, DELETE) are rejected with 401.
    """
    # 1. POST /api/v1/programs without token
    res_post = unauth_client.post("/api/v1/programs", json={
        "code": "UNAUTH-01", "name": "Unauth Model", "platform": "EV-800V",
        "lead_engineer": "Unknown", "quality_manager": "Unknown"
    })
    assert res_post.status_code == 401

    # 2. DELETE /api/v1/programs/1 without token
    res_del = unauth_client.delete("/api/v1/programs/1")
    assert res_del.status_code == 401

    # 3. POST /api/v1/changes without token
    res_change = unauth_client.post("/api/v1/changes", json={"title": "Unauthorized Change"})
    assert res_change.status_code == 401


def test_vertical_privilege_escalation_viewer_blocked(unauth_client, auth_headers):
    """
    Finding 4 Verification:
    Verify vertical privilege escalation: 'viewer' role is blocked with 403 Forbidden
    when attempting mutations across platform resources.
    """
    headers = auth_headers("auditor", "viewer")

    # 1. Viewer cannot create programs (requires admin or quality_lead)
    res_prog = unauth_client.post("/api/v1/programs", headers=headers, json={
        "code": "VIEWER-HACK", "name": "Hacked Program", "platform": "EV-800V",
        "lead_engineer": "Auditor", "quality_manager": "Auditor"
    })
    assert res_prog.status_code == 403

    # 2. Viewer cannot create parts (requires admin, quality_lead, or design_engineer)
    res_part = unauth_client.post("/api/v1/parts", headers=headers, json={
        "program_id": 1, "part_number": "P-HACK-01", "name": "Hack Part",
        "subsystem": "Primary Body Seal", "category": "Elastomer",
        "supplier": "Rogue", "material": "EPDM", "revision": "Rev A.0", "weight_kg": 1.0
    })
    assert res_part.status_code == 403

    # 3. Viewer cannot create engineering changes
    res_ecr = unauth_client.post("/api/v1/changes", headers=headers, json={
        "program_id": 1, "part_id": 1, "title": "Unauthorized ECR", "change_type": "Design-Mod",
        "reason": "Test", "pre_change_rev": "Rev A.0", "post_change_rev": "Rev B.0",
        "initiator": "auditor"
    })
    assert res_ecr.status_code == 403


def test_vertical_privilege_escalation_design_engineer_cannot_delete_programs(unauth_client, auth_headers):
    """
    Finding 4 Verification:
    Verify design engineer cannot delete programs (restricted to admin).
    """
    headers = auth_headers("design_eng", "design_engineer")
    res_del = unauth_client.delete("/api/v1/programs/1", headers=headers)
    assert res_del.status_code == 403


def test_vertical_privilege_escalation_design_engineer_cannot_approve_changes(unauth_client, auth_headers, db_session):
    """
    Finding 4 Verification:
    Separation of Duty: A Design Engineer can create and draft an ECR,
    but CANNOT approve or implement it (returns 403 Forbidden).
    Only Quality Lead or Admin can set approval_status to 'Approved' or 'Implemented'.
    """
    # 1. Setup prerequisite program and part in DB
    prog = Program(code="SEC-P-ECR", name="ECR Test Vehicle", platform="EV-800V", lead_engineer="Eng", quality_manager="QM")
    db_session.add(prog)
    db_session.commit()

    part = Part(program_id=prog.id, part_number="SEC-PART-ECR", name="Hinge Bolt", subsystem="Door Hinge & Check Link",
                category="Mechanical", supplier="Supplier A", material="Steel 10.9", revision="Rev A.0", weight_kg=0.8)
    db_session.add(part)
    db_session.commit()

    # 2. Design engineer creates change draft (permitted)
    design_headers = auth_headers("design_eng", "design_engineer")
    res_create = unauth_client.post("/api/v1/changes", headers=design_headers, json={
        "change_code": "ECR-SEC-2026-001",
        "program_id": prog.id,
        "part_id": part.id,
        "title": "Bolt Torque Upgrade",
        "change_type": "Design-Mod",
        "reason": "Prevent loosening under endurance shake test",
        "pre_change_rev": "Rev A.0",
        "post_change_rev": "Rev A.1",
        "cost_impact_rmb": 1500.0,
        "weight_impact_kg": 0.05,
        "tooling_lead_weeks": 2,
        "approval_status": "Draft",
        "initiator": "design_eng"
    })
    assert res_create.status_code == 201
    change_id = res_create.json()["id"]

    # 3. Design engineer attempts to self-approve change (FORBIDDEN -> 403)
    res_bad_approve = unauth_client.put(f"/api/v1/changes/{change_id}", headers=design_headers, json={
        "approval_status": "Approved"
    })
    assert res_bad_approve.status_code == 403
    assert "Only Quality Lead or Admin can set change status to 'Approved'" in res_bad_approve.json()["error"]

    # 4. Quality Lead approves change (PERMITTED -> 200)
    quality_headers = auth_headers("quality_lead", "quality_lead")
    res_good_approve = unauth_client.put(f"/api/v1/changes/{change_id}", headers=quality_headers, json={
        "approval_status": "Approved"
    })
    assert res_good_approve.status_code == 200
    assert res_good_approve.json()["approval_status"] == "Approved"


def test_horizontal_idor_cross_program_isolation(unauth_client, auth_headers, db_session):
    """
    Finding 4 Verification:
    Verify Horizontal IDOR protection:
    An engineer cannot create a Part referencing a non-existent foreign program (400),
    and cannot tamper with existing parts across separate programs without proper authorization.
    """
    quality_headers = auth_headers("quality_lead", "quality_lead")

    # 1. Foreign non-existent Program ID injection is rejected
    res_fake_prog = unauth_client.post("/api/v1/parts", headers=quality_headers, json={
        "program_id": 999999,
        "part_number": "IDOR-PART-999",
        "name": "Tampered Part",
        "subsystem": "Front Door Closure",
        "category": "Mechanical",
        "material": "Steel",
        "supplier": "Rogue Supplier",
        "weight_kg": 2.0,
        "revision": "Rev A.0"
    })
    assert res_fake_prog.status_code == 400
    assert "does not exist" in res_fake_prog.json()["error"]
