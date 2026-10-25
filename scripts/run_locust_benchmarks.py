#!/usr/bin/env python3
"""
Automated Multi-Tier Locust Benchmark Runner with Resource Monitoring.
Records P50/P95/P99, throughput, error rates, CPU and RAM for 3 concurrency levels.
"""

import subprocess
import os
import sys
import time
import json
import csv
import psutil

HOST = "http://127.0.0.1:8088"
REPORTS_DIR = "reports"
LOCUSTFILE = "backend/tests/locustfile.py"

TIERS = [
    {"name": "Level 1 (Low)", "users": 10, "spawn_rate": 5, "duration": "20s", "tag": "level1"},
    {"name": "Level 2 (Medium)", "users": 50, "spawn_rate": 10, "duration": "20s", "tag": "level2"},
    {"name": "Level 3 (High)", "users": 100, "spawn_rate": 20, "duration": "20s", "tag": "level3"},
]


def get_system_metrics():
    cpu_pct = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": cpu_pct,
        "mem_used_mb": round(mem.used / (1024 * 1024), 2),
        "mem_percent": mem.percent
    }


def run_tier(tier):
    tag = tier["tag"]
    csv_prefix = os.path.join(REPORTS_DIR, f"locust_{tag}")
    html_report = os.path.join(REPORTS_DIR, f"locust_{tag}.html")
    
    print(f"\n{'='*70}")
    print(f"🚀 Running Locust Benchmark: {tier['name']}")
    print(f"   Users: {tier['users']}, Spawn Rate: {tier['spawn_rate']}, Duration: {tier['duration']}")
    print(f"{'='*70}")

    pre_metrics = get_system_metrics()
    
    cmd = [
        "locust",
        "-f", LOCUSTFILE,
        "--headless",
        "-u", str(tier["users"]),
        "-r", str(tier["spawn_rate"]),
        "--run-time", tier["duration"],
        "--host", HOST,
        f"--csv={csv_prefix}",
        f"--html={html_report}"
    ]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Sample resources during run
    peak_cpu = pre_metrics["cpu_percent"]
    peak_mem = pre_metrics["mem_used_mb"]
    
    while p.poll() is None:
        time.sleep(1)
        m = get_system_metrics()
        peak_cpu = max(peak_cpu, m["cpu_percent"])
        peak_mem = max(peak_mem, m["mem_used_mb"])

    stdout, stderr = p.communicate()
    post_metrics = get_system_metrics()

    # Parse CSV results
    stats_csv = f"{csv_prefix}_stats.csv"
    aggregated_row = None
    if os.path.exists(stats_csv):
        with open(stats_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Type") is None or row.get("Name") == "Aggregated":
                    aggregated_row = row

    result = {
        "tier": tier["name"],
        "users": tier["users"],
        "duration": tier["duration"],
        "resource_monitoring": {
            "pre_cpu_pct": pre_metrics["cpu_percent"],
            "pre_mem_mb": pre_metrics["mem_used_mb"],
            "peak_cpu_pct": peak_cpu,
            "peak_mem_mb": peak_mem,
            "post_cpu_pct": post_metrics["cpu_percent"],
            "post_mem_mb": post_metrics["mem_used_mb"]
        },
        "stats": aggregated_row,
        "html_report": html_report,
        "csv_stats": stats_csv
    }

    if aggregated_row:
        total_reqs = int(aggregated_row.get("Request Count", 0))
        fail_reqs = int(aggregated_row.get("Failure Count", 0))
        fail_pct = round((fail_reqs / total_reqs * 100), 2) if total_reqs > 0 else 0.0
        rps = float(aggregated_row.get("Requests/s", 0))
        med_ms = float(aggregated_row.get("Median Response Time", 0))
        p95_ms = float(aggregated_row.get("95%", 0))
        p99_ms = float(aggregated_row.get("99%", 0))
        
        print(f"📊 Results Summary for {tier['name']}:")
        print(f"   • Total Requests: {total_reqs:,}")
        print(f"   • Throughput: {rps:.1f} req/s")
        print(f"   • Failure Rate: {fail_pct}% ({fail_reqs} failures)")
        print(f"   • Latency P50: {med_ms:.1f} ms | P95: {p95_ms:.1f} ms | P99: {p99_ms:.1f} ms")
        print(f"   • Peak CPU: {peak_cpu:.1f}% | Peak Memory: {peak_mem:.1f} MB")

    return result


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    all_results = []
    
    for tier in TIERS:
        res = run_tier(tier)
        all_results.append(res)
        time.sleep(2)  # Cooldown between tiers

    summary_file = os.path.join(REPORTS_DIR, "locust_benchmark_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"🎉 Complete multi-tier benchmarks finished! Saved summary to {summary_file}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
