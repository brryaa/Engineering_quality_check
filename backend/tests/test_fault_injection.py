import pytest
from unittest.mock import patch
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from app.models.models import Program, Part, EngineeringIssue


def test_fault_malformed_json_payload(client):
    """Test fault injection: malformed / syntactically broken JSON body."""
    res = client.post(
        "/api/v1/programs",
        content="{\"code\": \"MALFORMED-1\", \"name\": }",
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 422


def test_fault_invalid_data_types_json(client):
    """Test fault injection: invalid schema data types (e.g. string for integer, invalid enum)."""
    res = client.post(
        "/api/v1/parts",
        json={
            "program_id": "not_an_int",
            "part_number": "P-TEST-TYPE",
            "name": "Type Test Part",
            "subsystem": "Front Door Closure",
            "category": "Stamping",
            "material": "Steel",
            "supplier": "Supplier",
            "weight_kg": "not_a_float",
            "revision": "A"
        }
    )
    assert res.status_code == 422


def test_fault_extreme_pagination_out_of_bounds(client):
    """Test fault injection: massive pagination out of bounds (offset > 1,000,000)."""
    res = client.get("/api/v1/programs?page=1000000&page_size=100")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["page"] == 1000000


def test_fault_negative_and_zero_pagination(client):
    """Test fault injection: negative and zero page numbers are strictly validated."""
    res_zero = client.get("/api/v1/programs?page=0")
    assert res_zero.status_code == 422

    res_neg = client.get("/api/v1/programs?page=-5")
    assert res_neg.status_code == 422

    res_oversize = client.get("/api/v1/programs?page_size=10000")
    assert res_oversize.status_code == 422


def test_fault_duplicate_request_replay(client):
    """Test fault injection: duplicate unique code replay returns 409 Conflict."""
    payload = {
        "code": "FAULT-PROG-REPLAY",
        "name": "Replay Test Program",
        "platform=":"P-REPLAY",
        "platform": "P-REPLAY",
        "phase": "DV",
        "lead_engineer": "Eng 1",
        "quality_manager": "QM 1",
        "target_market": "Domestic"
    }
    # First request succeeds
    r1 = client.post("/api/v1/programs", json=payload)
    assert r1.status_code == 201

    # Second duplicate request must be rejected with 409 Conflict
    r2 = client.post("/api/v1/programs", json=payload)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["error"]


def test_fault_nonexistent_resource_404_resilience(client):
    """Test fault injection: querying non-existent resources across modules returns clean 404."""
    for path in [
        "/api/v1/programs/999999",
        "/api/v1/parts/999999",
        "/api/v1/dfmea/999999",
        "/api/v1/dvpr/999999",
        "/api/v1/tests/999999",
        "/api/v1/issues/999999",
        "/api/v1/root-cause/999999",
        "/api/v1/changes/999999",
        "/api/v1/knowledge/999999"
    ]:
        res = client.get(path)
        assert res.status_code == 404
        body = res.json()
        assert body["success"] is False
        assert "not found" in body["error"].lower()


def test_fault_database_connection_drop_simulation(client):
    """Test fault injection: simulated database disconnection yields HTTP 503 without crashing."""
    from fastapi.testclient import TestClient
    from app.main import app

    with patch("app.repositories.repositories.ProgramRepository.filter_programs") as mock_filter:
        mock_filter.side_effect = OperationalError("connection lost", {}, Exception("DB disconnect"))
        with TestClient(app, raise_server_exceptions=False) as safe_client:
            res = safe_client.get("/api/v1/programs")
            assert res.status_code == 503
            data = res.json()
            assert data["success"] is False
            assert "temporarily unavailable" in data["error"]
            assert "reference_id" in data


def test_fault_optimistic_lock_concurrent_api_conflict(client):
    """Test fault injection: concurrent API update throwing StaleDataError yields HTTP 409."""
    with patch("app.services.services.IssueRepository.update") as mock_update:
        mock_update.side_effect = StaleDataError("Row was updated or deleted by another transaction")
        # First create a valid program and part
        prog_res = client.post("/api/v1/programs", json={
            "code": "FAULT-PROG-OCC",
            "name": "OCC Test Program",
            "platform": "P-OCC",
            "phase": "PV",
            "lead_engineer": "Eng 1",
            "quality_manager": "QM 1",
            "target_market": "Global"
        })
        prog_id = prog_res.json()["id"]

        part_res = client.post("/api/v1/parts", json={
            "program_id": prog_id,
            "part_number": "P-OCC-01",
            "name": "OCC Part",
            "subsystem": "Front Door Closure",
            "category": "Stamping",
            "material": "Steel",
            "supplier": "Test",
            "weight_kg": 1.5,
            "revision": "A"
        })
        part_id = part_res.json()["id"]

        iss_res = client.post("/api/v1/issues", json={
            "issue_code": "ISS-OCC-FAULT-1",
            "program_id": prog_id,
            "part_id": part_id,
            "title": "Initial Issue",
            "severity": "S2-Major",
            "status": "New",
            "description": "Desc",
            "occurrence_phase": "DV-Testing",
            "assignee": "A",
            "reporter": "B",
            "due_date": "2026-12-31"
        })
        iss_id = iss_res.json()["id"]

        # Attempt update which encounters mocked StaleDataError
        up_res = client.put(f"/api/v1/issues/{iss_id}", json={"title": "Concurrent Update Title"})
        assert up_res.status_code == 409
        body = up_res.json()
        assert "modified by another user" in body["error"]


def test_fault_unhandled_exception_sanitized_500(client):
    """Test fault injection: unexpected runtime exception is masked to prevent security leak."""
    from fastapi.testclient import TestClient
    from app.main import app

    with patch("app.repositories.repositories.ProgramRepository.filter_programs") as mock_filter:
        mock_filter.side_effect = RuntimeError("SECRET_INTERNAL_DATABASE_CREDENTIALS_LEAK")
        with TestClient(app, raise_server_exceptions=False) as safe_client:
            res = safe_client.get("/api/v1/programs")
            assert res.status_code == 500
            data = res.json()
            assert data["success"] is False
            assert data["error"] == "Internal server error occurred."
            # Verify internal secret is NOT leaked to client
            assert "SECRET_INTERNAL_DATABASE_CREDENTIALS_LEAK" not in str(data)
            assert "reference_id" in data
