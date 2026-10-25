import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.seeds.seed_data import seed_database

@pytest.fixture(scope="module")
def seeded_client():
    # Ensure database is seeded with full volume (>10 models, >200 parts, >300 DFMEAs, >500 DVPs, >1000 tests, >500 issues, >200 changes)
    seed_database()
    with TestClient(app) as client:
        yield client

def test_benchmark_dashboard_stats_aggregation(seeded_client):
    """Benchmark the complex multi-table dashboard metric aggregation API."""
    latencies = []
    # Warmup
    seeded_client.get("/api/v1/dashboard/stats")
    
    # 20 consecutive requests to benchmark P50 and P95
    for _ in range(20):
        t0 = time.perf_counter()
        res = seeded_client.get("/api/v1/dashboard/stats")
        dt_ms = (time.perf_counter() - t0) * 1000.0
        assert res.status_code == 200
        latencies.append(dt_ms)

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    avg = sum(latencies) / len(latencies)

    print(f"\n[Performance Benchmark] Dashboard Stats: Avg={avg:.2f}ms, P50={p50:.2f}ms, P95={p95:.2f}ms")
    # Must be under 150ms even on local single thread
    assert avg < 150.0

def test_benchmark_test_runs_pagination(seeded_client):
    """Benchmark pagination over 1000+ test execution telemetry records."""
    latencies = []
    for page in range(1, 15):
        t0 = time.perf_counter()
        res = seeded_client.get(f"/api/v1/tests?page={page}&page_size=20&result=Fail")
        dt_ms = (time.perf_counter() - t0) * 1000.0
        assert res.status_code == 200
        latencies.append(dt_ms)

    avg = sum(latencies) / len(latencies)
    print(f"\n[Performance Benchmark] Test Runs (1000+ rows) Filtered Pagination: Avg={avg:.2f}ms")
    assert avg < 50.0

def test_benchmark_issues_multi_filter_search(seeded_client):
    """Benchmark issues multi-column search and join across programs and parts."""
    latencies = []
    queries = ["leak", "slam", "pinch", "hinge", "motor"]
    for q in queries:
        t0 = time.perf_counter()
        res = seeded_client.get(f"/api/v1/issues?search={q}&severity=S1-Critical")
        dt_ms = (time.perf_counter() - t0) * 1000.0
        assert res.status_code == 200
        latencies.append(dt_ms)

    avg = sum(latencies) / len(latencies)
    print(f"\n[Performance Benchmark] Issues Multi-filter Search: Avg={avg:.2f}ms")
    assert avg < 50.0

def test_benchmark_knowledge_search(seeded_client):
    """Benchmark engineering knowledge full-text query."""
    latencies = []
    keywords = ["漏水", "防夹", "下垂量", "风噪", "翻边"]
    for kw in keywords:
        t0 = time.perf_counter()
        res = seeded_client.get(f"/api/v1/knowledge?search={kw}")
        dt_ms = (time.perf_counter() - t0) * 1000.0
        assert res.status_code == 200
        latencies.append(dt_ms)

    avg = sum(latencies) / len(latencies)
    print(f"\n[Performance Benchmark] Knowledge Full-text Search: Avg={avg:.2f}ms")
    assert avg < 50.0
