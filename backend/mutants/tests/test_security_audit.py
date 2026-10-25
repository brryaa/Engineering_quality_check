import pytest
from app.models.models import Program, Part, EngineeringIssue
from app.main import app
from app.core.security_middleware import SecurityMiddleware, RATE_LIMIT_REQUESTS


def _reset_rate_limiter():
    for middleware in app.user_middleware:
        if middleware.cls == SecurityMiddleware:
            pass
    # Find active middleware instance in app.middleware_stack
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
        # Check that table still exists and program is intact
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


def test_oversized_payload_rejected(client):
    """Verify requests with Content-Length exceeding 5MB are rejected with 413 Content Too Large."""
    oversized_headers = {
        "Content-Type": "application/json",
        "Content-Length": str(10 * 1024 * 1024)  # 10 MB
    }
    res = client.post("/api/v1/programs", content=b"{}", headers=oversized_headers)
    assert res.status_code == 413
    assert "exceeds maximum allowed size" in res.json()["error"]


def test_rate_limiting_defense(client):
    """Verify rate limiter blocks excessive rapid-fire requests from single IP."""
    blocked = False
    for i in range(RATE_LIMIT_REQUESTS + 15):
        res = client.get("/health", headers={"X-Test-Rate-Limit": "1"})
        if res.status_code == 429:
            blocked = True
            assert "Rate limit exceeded" in res.json()["error"]
            break
    assert blocked is True


def test_idor_cross_program_isolation(client, db_session):
    """Verify IDOR: creating a part with a foreign non-existent program_id is rejected."""
    res = client.post("/api/v1/parts", json={
        "program_id": 88888,
        "part_number": "IDOR-PART-001",
        "name": "Unauthorized Cross Part",
        "subsystem": "Front Door Closure",
        "category": "Stamping",
        "material": "Steel",
        "supplier": "Rogue Supplier",
        "weight_kg": 2.0,
        "revision": "A"
    })
    assert res.status_code == 400
    assert "does not exist" in res.json()["error"]
