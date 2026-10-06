#!/usr/bin/env python3
"""
Slim aqi_station_daily_qc.csv down to the columns analysis and mapping actually need.

Everything dropped is either a duplicate of another column, derivable from one, or
already held in station_coverage.csv / aqi_station_daily.csv, so nothing is lost.

Dropped (26)
  month                                   = date[:7]
  aqi                                     raw AQI; superseded by aqi_qc (the QC'd
                                          value), and kept in aqi_station_daily.csv
  si_pm25 ... si_o3               (7)     sub-indices: a fixed function of the
                                          concentration columns kept below
  pm25_hours ... o3_hours         (7)     hourly data-capture counts; already used
                                          to validate the 24 h means upstream
  district                                CPCB's district field is unreliable
                                          (internal codes, wrong entries)
  flag_flatline, flag_pm_inversion,
  flag_extreme_o3, flag_extreme_pm,
  flag_any                        (5)     collapsed into one `flag_reason` column
  station_valid_aqi_days, months_ok,
  station_flatline, station_broken,
  station_low_coverage            (5)     station-level fields: see
                                          station_coverage.csv; the two
                                          include_in_* columns carry the verdict

Also made consistent: aqi_category and prominent_pollutant are now derived from
`aqi_qc`, so a flagged row has no leftover category or pollutant label.

Usage:  python trim_qc_columns.py            (rewrites the file in place)
        python trim_qc_columns.py --out new.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "output"

KEEP = ["date", "station_id", "station_name", "city", "state",
        "latitude", "longitude",
        "aqi_qc", "aqi_category", "prominent_pollutant", "n_pollutants",
        "pm25_24h", "pm10_24h", "no2_24h", "so2_24h", "nh3_24h",
        "co_8hmax", "o3_8hmax",
        "flag_reason", "include_in_ranking", "include_in_map"]

REASONS = [("flag_flatline", "flatline"),
           ("flag_pm_inversion", "pm_inversion"),
           ("flag_extreme_o3", "extreme_o3"),
           ("flag_extreme_pm", "extreme_pm")]

CATEGORIES = [(50, "Good"), (100, "Satisfactory"), (200, "Moderate"),
              (300, "Poor"), (400, "Very Poor"), (np.inf, "Severe")]


def category(a):
    if pd.isna(a):
        return np.nan
    for hi, name in CATEGORIES:
        if a <= hi:
            return name
    return np.nan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DATA_DIR / "aqi_station_daily_qc.csv"))
    ap.add_argument("--out", default=None, help="default: overwrite --src")
    args = ap.parse_args()
    src = Path(args.src)
    out = Path(args.out) if args.out else src

    df = pd.read_csv(src, low_memory=False)
    before = df.shape
    if "flag_reason" in df.columns:
        print("already trimmed:", before)
        return 0

    # one text column instead of five booleans
    reason = pd.Series("", index=df.index, dtype=object)
    for col, label in REASONS:
        hit = df[col].astype(bool) & (reason == "")
        reason[hit] = label
    df["flag_reason"] = reason

    # keep category / prominent pollutant consistent with the QC'd AQI
    df["aqi_category"] = df["aqi_qc"].map(category)
    df["prominent_pollutant"] = df["prominent_pollutant"].where(df["aqi_qc"].notna())

    dropped = [c for c in df.columns if c not in KEEP]
    df = df[KEEP]
    df.to_csv(out, index=False, encoding="utf-8")

    print(f"{src.name}: {before[1]} -> {df.shape[1]} columns, {len(df):,} rows (unchanged)")
    print("dropped:", ", ".join(dropped))
    print("written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
