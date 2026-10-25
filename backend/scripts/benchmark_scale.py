#!/usr/bin/env python3
"""
Performance Scaling & Latency Benchmark Script
Empirically benchmarks P50, P95, P99 query latency, QPS throughput,
memory consumption, and B-Tree index acceleration across 10k, 100k, and 1M records.
"""
import os
import sys
import time
import sqlite3
import statistics
import psutil

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "perf_benchmark.db")


def get_process_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def setup_benchmark_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("""
        CREATE TABLE benchmark_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_code TEXT NOT NULL,
            program_id INTEGER NOT NULL,
            part_id INTEGER NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            title TEXT NOT NULL,
            assignee TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    return conn


def bulk_insert_records(conn, count: int, start_offset: int = 0):
    cur = conn.cursor()
    severities = ["S1-Critical", "S2-Major", "S3-Minor", "S4-Cosmetic"]
    statuses = ["New", "Investigating", "Containment", "RootCauseVerified", "ActionImplemented", "Closed"]
    subsystems = ["Door Closure", "Frameless Window", "EPDM Sealing", "Tailgate System", "Hinge & Link"]

    batch = []
    t0 = time.perf_counter()
    for i in range(start_offset, start_offset + count):
        sev = severities[i % 4]
        stat = statuses[i % 6]
        sub = subsystems[i % 5]
        batch.append((
            f"ISS-PERF-{i:07d}",
            (i % 50) + 1,
            (i % 1000) + 1,
            sev,
            stat,
            f"High speed vibration abnormal noise observed in {sub} during durability run {i}",
            f"Engineer_{(i % 200)}"
        ))

        if len(batch) >= 10000:
            cur.executemany("""
                INSERT INTO benchmark_issues (issue_code, program_id, part_id, severity, status, title, assignee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            batch.clear()

    if batch:
        cur.executemany("""
            INSERT INTO benchmark_issues (issue_code, program_id, part_id, severity, status, title, assignee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, batch)
        conn.commit()

    dt = time.perf_counter() - t0
    rate = count / dt if dt > 0 else 0
    return dt, rate


def run_query_benchmark(conn, iterations: int = 100):
    cur = conn.cursor()
    latencies = []

    # Run multi-filter query: filter by severity, status, and range scan
    for i in range(iterations):
        target_sev = ["S1-Critical", "S2-Major", "S3-Minor", "S4-Cosmetic"][i % 4]
        target_prog = (i % 50) + 1
        t0 = time.perf_counter()
        cur.execute("""
            SELECT id, issue_code, severity, status, title, assignee
            FROM benchmark_issues
            WHERE severity = ? AND program_id = ?
            ORDER BY id DESC
            LIMIT 50
        """, (target_sev, target_prog))
        cur.fetchall()
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt_ms)

    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    avg = statistics.mean(latencies)
    qps = 1000.0 / avg if avg > 0 else 0

    return {
        "avg_ms": avg,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "qps": qps
    }


def main():
    print("=" * 60)
    print("EQL DATABASE PERFORMANCE SCALING BENCHMARK (10k -> 100k -> 1M)")
    print("=" * 60)

    conn = setup_benchmark_db()
    init_mem = get_process_memory_mb()
    print(f"[*] Initial Process Memory: {init_mem:.2f} MB")

    # --- TIER 1: 10,000 Records (Unindexed Baseline) ---
    print("\n[Tier 1] Ingesting 10,000 records...")
    t_ins, r_ins = bulk_insert_records(conn, 10000, 0)
    mem_10k = get_process_memory_mb()
    print(f"  -> Ingestion time: {t_ins:.2f}s ({r_ins:.0f} rows/s), Memory: {mem_10k:.2f} MB")

    res_10k_no_idx = run_query_benchmark(conn, iterations=150)
    print(f"  [10k No-Index] Latency P50: {res_10k_no_idx['p50_ms']:.2f}ms | P95: {res_10k_no_idx['p95_ms']:.2f}ms | P99: {res_10k_no_idx['p99_ms']:.2f}ms | QPS: {res_10k_no_idx['qps']:.1f}")

    # Add composite index
    cur = conn.cursor()
    t_idx0 = time.perf_counter()
    cur.execute("CREATE INDEX idx_issues_sev_prog ON benchmark_issues(severity, program_id, id DESC);")
    conn.commit()
    t_idx_10k = (time.perf_counter() - t_idx0) * 1000.0

    res_10k_idx = run_query_benchmark(conn, iterations=150)
    print(f"  [10k Indexed]  Latency P50: {res_10k_idx['p50_ms']:.3f}ms | P95: {res_10k_idx['p95_ms']:.3f}ms | P99: {res_10k_idx['p99_ms']:.3f}ms | QPS: {res_10k_idx['qps']:.1f}")

    # --- TIER 2: 100,000 Records ---
    print("\n[Tier 2] Ingesting additional 90,000 records (Total = 100,000)...")
    t_ins_100k, r_ins_100k = bulk_insert_records(conn, 90000, 10000)
    mem_100k = get_process_memory_mb()
    print(f"  -> Ingestion time: {t_ins_100k:.2f}s ({r_ins_100k:.0f} rows/s), Memory: {mem_100k:.2f} MB")

    res_100k_idx = run_query_benchmark(conn, iterations=200)
    print(f"  [100k Indexed] Latency P50: {res_100k_idx['p50_ms']:.3f}ms | P95: {res_100k_idx['p95_ms']:.3f}ms | P99: {res_100k_idx['p99_ms']:.3f}ms | QPS: {res_100k_idx['qps']:.1f}")

    # Drop index to measure 100k unindexed penalty
    cur.execute("DROP INDEX idx_issues_sev_prog;")
    conn.commit()
    res_100k_no_idx = run_query_benchmark(conn, iterations=30)
    print(f"  [100k No-Index] Latency P50: {res_100k_no_idx['p50_ms']:.2f}ms | P95: {res_100k_no_idx['p95_ms']:.2f}ms | P99: {res_100k_no_idx['p99_ms']:.2f}ms | QPS: {res_100k_no_idx['qps']:.1f}")

    # Recreate index for scaling to 1,000,000
    cur.execute("CREATE INDEX idx_issues_sev_prog ON benchmark_issues(severity, program_id, id DESC);")
    conn.commit()

    # --- TIER 3: 1,000,000 Records Scaling ---
    print("\n[Tier 3] Scaling to 1,000,000 records (Ingesting 900,000 records in batches)...")
    t_ins_1m, r_ins_1m = bulk_insert_records(conn, 900000, 100000)
    mem_1m = get_process_memory_mb()
    db_size_mb = os.path.getsize(DB_FILE) / (1024 * 1024)
    print(f"  -> Ingestion time: {t_ins_1m:.2f}s ({r_ins_1m:.0f} rows/s), Memory: {mem_1m:.2f} MB, DB File Size: {db_size_mb:.2f} MB")

    res_1m_idx = run_query_benchmark(conn, iterations=300)
    print(f"  [1,000,000 Indexed] Latency P50: {res_1m_idx['p50_ms']:.3f}ms | P95: {res_1m_idx['p95_ms']:.3f}ms | P99: {res_1m_idx['p99_ms']:.3f}ms | QPS: {res_1m_idx['qps']:.1f}")

    speedup_100k = res_100k_no_idx["avg_ms"] / res_100k_idx["avg_ms"] if res_100k_idx["avg_ms"] > 0 else 0

    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY RESULTS TABLE")
    print("=" * 60)
    print(f"{'Scale Tier':<16} | {'Indexed':<8} | {'P50 (ms)':<9} | {'P95 (ms)':<9} | {'P99 (ms)':<9} | {'QPS':<10} | {'RAM (MB)':<8}")
    print("-" * 80)
    print(f"{'10,000':<16} | {'No':<8} | {res_10k_no_idx['p50_ms']:<9.3f} | {res_10k_no_idx['p95_ms']:<9.3f} | {res_10k_no_idx['p99_ms']:<9.3f} | {res_10k_no_idx['qps']:<10.1f} | {mem_10k:<8.1f}")
    print(f"{'10,000':<16} | {'Yes':<8} | {res_10k_idx['p50_ms']:<9.3f} | {res_10k_idx['p95_ms']:<9.3f} | {res_10k_idx['p99_ms']:<9.3f} | {res_10k_idx['qps']:<10.1f} | {mem_10k:<8.1f}")
    print(f"{'100,000':<16} | {'No':<8} | {res_100k_no_idx['p50_ms']:<9.3f} | {res_100k_no_idx['p95_ms']:<9.3f} | {res_100k_no_idx['p99_ms']:<9.3f} | {res_100k_no_idx['qps']:<10.1f} | {mem_100k:<8.1f}")
    print(f"{'100,000':<16} | {'Yes':<8} | {res_100k_idx['p50_ms']:<9.3f} | {res_100k_idx['p95_ms']:<9.3f} | {res_100k_idx['p99_ms']:<9.3f} | {res_100k_idx['qps']:<10.1f} | {mem_100k:<8.1f}")
    print(f"{'1,000,000':<16} | {'Yes':<8} | {res_1m_idx['p50_ms']:<9.3f} | {res_1m_idx['p95_ms']:<9.3f} | {res_1m_idx['p99_ms']:<9.3f} | {res_1m_idx['qps']:<10.1f} | {mem_1m:<8.1f}")
    print("=" * 60)
    print(f"Index Speedup on 100k records: {speedup_100k:.1f}x acceleration")

    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("[*] Benchmark cleanup completed.")


if __name__ == "__main__":
    main()
