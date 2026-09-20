"""Concurrent HTTP load runner that does not depend on Locust's psutil monitor."""

from __future__ import annotations

import argparse
import asyncio
import csv
import statistics
import time
from collections import defaultdict
from pathlib import Path

import httpx

HEADERS = {"Authorization": "Bearer dev-analyst-token", "Content-Type": "application/json"}
QUESTION = "What were Amazon net sales and AWS net sales in 2024?"


async def _loop(
    client: httpx.AsyncClient, host: str, stop_at: float, samples: dict[str, list[float]], failures: dict[str, int]
) -> None:
    health_n = 0
    while time.perf_counter() < stop_at:
        path = "/health" if health_n % 4 != 0 else "/v1/debate"
        health_n += 1
        started = time.perf_counter()
        try:
            if path == "/health":
                response = await client.get(f"{host}{path}")
            else:
                response = await client.post(f"{host}{path}", headers=HEADERS, json={"question": QUESTION})
            elapsed_ms = (time.perf_counter() - started) * 1000
            if response.status_code >= 400:
                failures[path] += 1
            else:
                samples[path].append(elapsed_ms)
        except httpx.HTTPError:
            failures[path] += 1


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = int(round((q / 100) * (len(ordered) - 1)))
    return ordered[rank]


def _row(name: str, values: list[float], fails: int, duration: float) -> dict[str, object]:
    n = len(values)
    return {
        "Type": "GET" if name == "/health" else "POST",
        "Name": name,
        "Request Count": n + fails,
        "Failure Count": fails,
        "Median Response Time": round(_percentile(values, 50), 3),
        "Average Response Time": round(statistics.mean(values), 3) if values else 0,
        "Min Response Time": round(min(values), 3) if values else 0,
        "Max Response Time": round(max(values), 3) if values else 0,
        "Requests/s": round((n + fails) / duration, 3) if duration else 0,
        "Failures/s": round(fails / duration, 3) if duration else 0,
        "95%": round(_percentile(values, 95), 3),
    }


async def run(host: str, users: int, duration: float, out: Path) -> int:
    samples: dict[str, list[float]] = defaultdict(list)
    failures: dict[str, int] = defaultdict(int)
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        stop_at = time.perf_counter() + duration
        await asyncio.gather(*[_loop(client, host.rstrip("/"), stop_at, samples, failures) for _ in range(users)])
    elapsed = duration
    rows = [
        _row("/health", samples["/health"], failures["/health"], elapsed),
        _row("/v1/debate", samples["/v1/debate"], failures["/v1/debate"], elapsed),
    ]
    all_values = samples["/health"] + samples["/v1/debate"]
    all_fails = failures["/health"] + failures["/v1/debate"]
    rows.append(
        {
            "Type": "",
            "Name": "Aggregated",
            "Request Count": len(all_values) + all_fails,
            "Failure Count": all_fails,
            "Median Response Time": round(_percentile(all_values, 50), 3),
            "Average Response Time": round(statistics.mean(all_values), 3) if all_values else 0,
            "Min Response Time": round(min(all_values), 3) if all_values else 0,
            "Max Response Time": round(max(all_values), 3) if all_values else 0,
            "Requests/s": round((len(all_values) + all_fails) / elapsed, 3),
            "Failures/s": round(all_fails / elapsed, 3),
            "95%": round(_percentile(all_values, 95), 3),
        }
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    total_fail = all_fails
    print(f"wrote {out}  requests={len(all_values) + all_fails} failures={total_fail}")
    return 1 if total_fail else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://127.0.0.1:8009")
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--duration", type=float, default=20)
    parser.add_argument("--out", default="evaluation/reports/load_stats.csv")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.host, args.users, args.duration, Path(args.out))))


if __name__ == "__main__":
    main()
