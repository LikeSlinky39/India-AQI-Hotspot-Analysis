#!/usr/bin/env python3
"""
Download CPCB CAAQMS station data (all-India) from the public CCR file endpoint.

The CCR "CAAQMS Data Repository" page is captcha-protected, but the file endpoint
it calls is plain and open:

  https://airquality.cpcb.gov.in/caaqms-common/dataRepository/download-excel-file
      ?file_name=/Raw_data/<FREQ>/<YEAR>/<station_id>_<file_slug>_<FREQ>.csv

FREQ is one of: 1Day (24-hour averages), 1Hr, 8Hr, 15Min.

Station list (id, name, state, city, lat, lon, file_slug) comes from stations.csv,
which sits next to this script.

Usage
-----
    python download_cpcb.py                       # 1Day, years 2025 + 2026
    python download_cpcb.py --years 2024 2025 2026
    python download_cpcb.py --freq 1Hr --years 2026
    python download_cpcb.py --state Delhi --state Haryana
    python download_cpcb.py --workers 4 --out raw_data

Re-running is safe: files already present (and non-trivial in size) are skipped,
so an interrupted run just resumes. Every attempt is recorded in download_log.csv.

Requires: pip install requests
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("This script needs the 'requests' package:\n    pip install requests")

BASE = ("https://airquality.cpcb.gov.in/caaqms-common/dataRepository/"
        "download-excel-file?file_name=")
HEADERS = {
    # The endpoint is public, but a normal browser UA and referer keep it happy.
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"),
    "Referer": "https://airquality.cpcb.gov.in/ccr/",
    "Accept": "text/csv,application/octet-stream,*/*",
}
MIN_BYTES = 200          # anything smaller is an empty/placeholder response
SCRIPT_DIR = Path(__file__).resolve().parent

print_lock = threading.Lock()


def log(msg: str) -> None:
    with print_lock:
        print(msg, flush=True)


def load_stations(path: Path, states: list[str] | None,
                  cities: list[str] | None) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if states:
        wanted = {s.strip().lower() for s in states}
        rows = [r for r in rows if r["state"].strip().lower() in wanted]
    if cities:
        wanted = {c.strip().lower() for c in cities}
        rows = [r for r in rows if r["city"].strip().lower() in wanted]
    return rows


def remote_path(station: dict, year: int, freq: str) -> str:
    return f"/Raw_data/{freq}/{year}/{station['station_id']}_{station['file_slug']}_{freq}.csv"


def fetch_one(session: requests.Session, station: dict, year: int, freq: str,
              out_dir: Path, retries: int, pause: float) -> dict:
    """Download one station-year file. Returns a log record."""
    rel = remote_path(station, year, freq)
    dest = out_dir / f"{year}" / f"{station['station_id']}_{freq}_{year}.csv"
    rec = {
        "station_id": station["station_id"],
        "station_name": station["station_name"],
        "state": station["state"],
        "city": station["city"],
        "year": year,
        "freq": freq,
        "remote_file": rel,
        "local_file": str(dest.relative_to(out_dir.parent)) if dest.is_absolute() else str(dest),
        "status": "",
        "bytes": 0,
        "rows": 0,
    }

    if dest.exists() and dest.stat().st_size >= MIN_BYTES:
        rec["status"] = "skipped (already downloaded)"
        rec["bytes"] = dest.stat().st_size
        return rec

    dest.parent.mkdir(parents=True, exist_ok=True)
    url = BASE + requests.utils.quote(rel, safe="")

    last_err = ""
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=120)
            body = resp.content
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}"
            elif len(body) < MIN_BYTES:
                # CPCB answers 200 with an empty body when the file does not exist
                rec["status"] = "no data on server"
                rec["bytes"] = len(body)
                return rec
            else:
                dest.write_bytes(body)
                rec["status"] = "downloaded"
                rec["bytes"] = len(body)
                rec["rows"] = max(body.count(b"\n") - 1, 0)
                time.sleep(pause + random.uniform(0, pause))
                return rec
        except Exception as exc:                      # network hiccup, timeout, ...
            last_err = f"{type(exc).__name__}: {exc}"
        time.sleep(min(2 ** attempt, 20) + random.uniform(0, 1))

    rec["status"] = f"FAILED ({last_err})"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description="Bulk-download CPCB CAAQMS station data.")
    ap.add_argument("--stations", default=str(SCRIPT_DIR / "stations.csv"),
                    help="station master CSV (default: stations.csv next to this script)")
    ap.add_argument("--out", default=str(SCRIPT_DIR.parent / "raw_data"),
                    help="output directory (default: ../raw_data)")
    ap.add_argument("--years", nargs="+", type=int, default=[2025, 2026])
    ap.add_argument("--freq", default="1Day", choices=["1Day", "1Hr", "8Hr", "15Min"])
    ap.add_argument("--state", action="append", help="limit to a state (repeatable)")
    ap.add_argument("--city", action="append", help="limit to a city (repeatable)")
    ap.add_argument("--workers", type=int, default=6,
                    help="parallel downloads (default 6; be kind to a government server)")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--pause", type=float, default=0.3,
                    help="seconds to wait after each successful download")
    ap.add_argument("--limit", type=int, help="only the first N stations (for a test run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the URLs that would be fetched and exit")
    args = ap.parse_args()

    stations_path = Path(args.stations)
    if not stations_path.exists():
        return print(f"Station list not found: {stations_path}") or 1

    stations = load_stations(stations_path, args.state, args.city)
    if args.limit:
        stations = stations[: args.limit]
    if not stations:
        return print("No stations matched those filters.") or 1

    out_dir = Path(args.out)
    jobs = [(s, y) for s in stations for y in args.years]

    log(f"Stations: {len(stations)}   years: {args.years}   frequency: {args.freq}")
    log(f"Files to consider: {len(jobs)}   output: {out_dir}")

    if args.dry_run:
        for s, y in jobs[:20]:
            log(BASE + requests.utils.quote(remote_path(s, y, args.freq), safe=""))
        if len(jobs) > 20:
            log(f"... and {len(jobs) - 20} more")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    started = time.time()

    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(fetch_one, session, s, y, args.freq,
                            out_dir, args.retries, args.pause): (s, y)
                for s, y in jobs
            }
            for i, fut in enumerate(as_completed(futures), 1):
                rec = fut.result()
                records.append(rec)
                if i % 25 == 0 or rec["status"].startswith("FAILED"):
                    ok = sum(1 for r in records if r["status"] == "downloaded")
                    log(f"[{i}/{len(jobs)}] ok={ok}  last: {rec['station_id']} "
                        f"{rec['year']} -> {rec['status']}")

    log_path = out_dir.parent / "download_log.csv"
    with log_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    downloaded = sum(1 for r in records if r["status"] == "downloaded")
    skipped = sum(1 for r in records if r["status"].startswith("skipped"))
    missing = sum(1 for r in records if r["status"] == "no data on server")
    failed = sum(1 for r in records if r["status"].startswith("FAILED"))
    total_mb = sum(r["bytes"] for r in records) / 1e6

    log("")
    log(f"downloaded : {downloaded}")
    log(f"skipped    : {skipped}")
    log(f"no data    : {missing}")
    log(f"failed     : {failed}")
    log(f"size       : {total_mb:.1f} MB")
    log(f"elapsed    : {time.time() - started:.0f}s")
    log(f"log written to {log_path}")
    if failed:
        log("Re-run the same command to retry the failed files (finished ones are skipped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
