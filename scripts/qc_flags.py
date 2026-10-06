#!/usr/bin/env python3
"""
Add quality-control flags to the station-day AQI table.

Nothing is deleted or overwritten: the input file is read only, and three new files
are written next to it.

Inputs
------
  output/aqi_station_daily.csv         (station-day table built by compute_aqi.py)

Outputs
-------
  output/aqi_station_daily_qc.csv      same rows + QC flag columns + a clean `aqi_qc`
  output/station_coverage.csv          one row per station: coverage, flags, AQI stats
  output/qc_summary.md                 what was flagged and why

Flag definitions (all thresholds are explicit so they can be cited in the report)
--------------------------------------------------------------------------------
  flag_flatline        this station-day belongs to a run of >= 5 consecutive
                       available days with an identical daily PM2.5 (or PM10)
                       value -> stuck instrument
  flag_pm_inversion    PM2.5 > PM10 on the same day (physically impossible)
  flag_extreme_o3      8-hour O3 maximum > 400 ug/m3 (~200 ppb; implausible as an
                       8-hour mean in Indian ambient air)
  flag_extreme_pm      PM2.5 24 h mean > 600 ug/m3, or PM10 24 h mean > 1000 ug/m3
  flag_any             any of the above
  aqi_qc               `aqi` with flagged rows set to blank; use this for analysis

Station-level (in station_coverage.csv, and joined onto the row table)
  valid_aqi_days_qc    days with a CPCB-valid AQI after the row flags are applied
  months_ok            calendar months with >= 15 valid AQI days (seasonal balance)
  station_broken       >= 30 flat-lined days, or AQI standard deviation < 5
                       -> persistently faulty instrument, drop the station
  include_in_ranking   strict panel: >= 75% of days (273 of 364), >= 9 balanced
                       months, instrument not broken -> annual means, top-N rankings
  include_in_map       lenient panel: >= 50% of days (182), instrument not broken
                       -> spatial maps and hotspot surfaces

Thresholds follow the usual 75% data-capture convention for annual air-quality
statistics; a single station is never dropped for a handful of bad days, because
those days are already removed by the row-level flags.

Usage:  python qc_flags.py [--min-days 273] [--map-min-days 182]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "output"

O3_MAX = 400.0
PM25_MAX = 600.0
PM10_MAX = 1000.0
RUN_LEN = 5
BROKEN_FLATLINE_DAYS = 30      # station-level: persistently stuck instrument
MONTH_MIN_DAYS = 15            # a month "counts" at this many valid AQI days
MIN_MONTHS = 9                 # months required for the strict ranking panel


def flatline_mask(frame: pd.DataFrame, col: str, run_len: int = RUN_LEN) -> pd.Series:
    """True for rows inside a run of >= run_len identical consecutive available values."""
    mask = pd.Series(False, index=frame.index)
    for _, grp in frame.groupby("station_id", sort=False):
        s = grp[col].dropna()
        if len(s) < run_len:
            continue
        run_id = (s != s.shift()).cumsum()
        sizes = run_id.map(run_id.value_counts())
        mask.loc[s.index[sizes >= run_len]] = True
    return mask


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-days", type=int, default=273,
                    help="minimum valid-AQI days (after flags) for the ranking panel")
    ap.add_argument("--map-min-days", type=int, default=182,
                    help="minimum valid-AQI days for the map panel")
    ap.add_argument("--data-dir", default=str(DATA_DIR))
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    src = data_dir / "aqi_station_daily.csv"
    if not src.exists():
        print(f"not found: {src}")
        return 1

    df = pd.read_csv(src, encoding="utf-8-sig", low_memory=False)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["station_id", "date"]).reset_index(drop=True)
    print(f"read {len(df):,} rows, {df.station_id.nunique()} stations")

    # ---- row-level flags -------------------------------------------------
    df["flag_flatline"] = (flatline_mask(df, "pm25_24h")
                           | flatline_mask(df, "pm10_24h"))
    both_pm = df.pm25_24h.notna() & df.pm10_24h.notna()
    df["flag_pm_inversion"] = both_pm & (df.pm25_24h > df.pm10_24h)
    df["flag_extreme_o3"] = df.o3_8hmax > O3_MAX
    df["flag_extreme_pm"] = (df.pm25_24h > PM25_MAX) | (df.pm10_24h > PM10_MAX)
    flag_cols = ["flag_flatline", "flag_pm_inversion",
                 "flag_extreme_o3", "flag_extreme_pm"]
    df[flag_cols] = df[flag_cols].fillna(False).astype(bool)
    df["flag_any"] = df[flag_cols].any(axis=1)

    # clean AQI column for analysis
    df["aqi_qc"] = df["aqi"].where(~df["flag_any"])

    # ---- station-level ---------------------------------------------------
    cov = (df.groupby(["station_id", "station_name", "city", "district", "state",
                       "latitude", "longitude"], dropna=False)
             .agg(days=("date", "size"),
                  first_day=("date", "min"),
                  last_day=("date", "max"),
                  valid_aqi_days=("aqi", "count"),
                  valid_aqi_days_qc=("aqi_qc", "count"),
                  flagged_days=("flag_any", "sum"),
                  flatline_days=("flag_flatline", "sum"),
                  aqi_mean=("aqi_qc", "mean"),
                  aqi_median=("aqi_qc", "median"),
                  aqi_p95=("aqi_qc", lambda s: s.quantile(0.95)),
                  aqi_std=("aqi_qc", "std"),
                  aqi_max=("aqi_qc", "max"))
             .reset_index())
    # seasonal balance: months with enough valid days
    months = (df.dropna(subset=["aqi_qc"])
                .groupby(["station_id", "month"]).size()
                .rename("d").reset_index())
    months_ok = (months[months.d >= MONTH_MIN_DAYS]
                 .groupby("station_id").size().rename("months_ok"))
    cov = cov.merge(months_ok, on="station_id", how="left")
    cov["months_ok"] = cov.months_ok.fillna(0).astype(int)

    cov["station_flatline"] = cov.flatline_days > 0
    cov["station_broken"] = ((cov.flatline_days >= BROKEN_FLATLINE_DAYS)
                             | (cov.aqi_std < 5))
    cov["station_low_coverage"] = cov.valid_aqi_days_qc < args.min_days
    cov["include_in_ranking"] = (~cov.station_broken
                                 & (cov.valid_aqi_days_qc >= args.min_days)
                                 & (cov.months_ok >= MIN_MONTHS))
    cov["include_in_map"] = (~cov.station_broken
                             & (cov.valid_aqi_days_qc >= args.map_min_days))
    for c in ["aqi_mean", "aqi_median", "aqi_p95", "aqi_std"]:
        cov[c] = cov[c].round(1)
    cov["first_day"] = cov.first_day.dt.strftime("%Y-%m-%d")
    cov["last_day"] = cov.last_day.dt.strftime("%Y-%m-%d")

    # join the station verdict onto the row table
    df = df.merge(cov[["station_id", "valid_aqi_days_qc", "months_ok",
                       "station_flatline", "station_broken",
                       "station_low_coverage", "include_in_ranking",
                       "include_in_map"]],
                  on="station_id", how="left")
    df = df.rename(columns={"valid_aqi_days_qc": "station_valid_aqi_days"})

    # ---- write -----------------------------------------------------------
    out = df.copy()
    out["date"] = out.date.dt.strftime("%Y-%m-%d")
    for c in flag_cols + ["flag_any", "station_flatline", "station_broken",
                          "station_low_coverage", "include_in_ranking",
                          "include_in_map"]:
        out[c] = out[c].astype(int)          # 0/1 travels better into QGIS and Excel
    out["aqi_qc"] = out.aqi_qc.astype("Int64")
    qc_path = data_dir / "aqi_station_daily_qc.csv"
    out.to_csv(qc_path, index=False, encoding="utf-8")   # no BOM
    cov_path = data_dir / "station_coverage.csv"
    cov.to_csv(cov_path, index=False, encoding="utf-8")

    # ---- summary ---------------------------------------------------------
    n = len(df)
    lines = [
        "# QC summary",
        "",
        f"Source: `aqi_station_daily.csv` — {n:,} station-days, "
        f"{df.station_id.nunique()} stations, "
        f"{df.date.min():%d %b %Y} to {df.date.max():%d %b %Y}.",
        "",
        "## Row-level flags",
        "",
        "| Flag | Rule | Rows | % of rows | Stations affected |",
        "|---|---|---:|---:|---:|",
    ]
    rules = {
        "flag_flatline": f">= {RUN_LEN} identical consecutive daily PM2.5/PM10 values",
        "flag_pm_inversion": "PM2.5 > PM10 on the same day",
        "flag_extreme_o3": f"8-hour O3 max > {O3_MAX:.0f} ug/m3",
        "flag_extreme_pm": f"PM2.5 > {PM25_MAX:.0f} or PM10 > {PM10_MAX:.0f} ug/m3",
    }
    for c, rule in rules.items():
        k = int(df[c].sum())
        st = int(df.loc[df[c], "station_id"].nunique())
        lines.append(f"| `{c}` | {rule} | {k:,} | {k / n * 100:.2f}% | {st} |")
    k = int(df.flag_any.sum())
    lines += [
        f"| **`flag_any`** | any of the above | **{k:,}** | **{k / n * 100:.2f}%** | "
        f"**{int(df.loc[df.flag_any, 'station_id'].nunique())}** |",
        "",
        f"Valid AQI days before QC: {int(df.aqi.notna().sum()):,}  ->  "
        f"after QC (`aqi_qc`): {int(df.aqi_qc.notna().sum()):,} "
        f"({int(df.aqi.notna().sum()) - int(df.aqi_qc.notna().sum()):,} removed).",
        "",
        "## Station-level verdict",
        "",
        f"- stations in file: **{len(cov)}**",
        f"- any flat-lined days (run >= {RUN_LEN}): "
        f"**{int(cov.station_flatline.sum())}** (those days are flagged out, the "
        f"station is kept)",
        f"- instrument treated as broken (>= {BROKEN_FLATLINE_DAYS} flat-lined days "
        f"or AQI std < 5): **{int(cov.station_broken.sum())}**",
        f"- below {args.min_days} valid AQI days after flags: "
        f"**{int(cov.station_low_coverage.sum())}**",
        "",
        f"- **ranking panel** (>= {args.min_days} days, >= {MIN_MONTHS} months with "
        f">= {MONTH_MIN_DAYS} days, instrument sound): "
        f"**{int(cov.include_in_ranking.sum())} stations** — use for annual means "
        f"and top-N tables",
        f"- **map panel** (>= {args.map_min_days} days, instrument sound): "
        f"**{int(cov.include_in_map.sum())} stations** — use for spatial maps and "
        f"hotspot surfaces",
        "",
        "### Stations excluded even from the map panel",
        "",
        "| Station | City | State | Valid AQI days | Flat-lined days | Reason |",
        "|---|---|---|---:|---:|---|",
    ]
    ex = cov[~cov.include_in_map].sort_values("valid_aqi_days_qc")
    for r in ex.itertuples():
        why = []
        if r.station_broken:
            why.append("broken instrument")
        if r.valid_aqi_days_qc < args.map_min_days:
            why.append("coverage below 50%")
        lines.append(f"| {r.station_name} | {r.city} | {r.state} | "
                     f"{r.valid_aqi_days_qc} | {r.flatline_days} | {', '.join(why)} |")
    lines += [
        "",
        "## Notes carried over from the source data",
        "",
        "- 15 August 2026 is missing for every station: the CPCB feed carries the "
        "timestamps but all values are NA (nationwide transmission gap), so the year "
        "has 364 days.",
        "- 579 of the 605 stations in the CPCB network appear here; 16 publish no "
        "hourly file and 10 have no usable readings in the window.",
        "- AQI is blank wherever CPCB's rule is not met (fewer than three pollutants, "
        "or no PM2.5/PM10). These are genuine gaps and are not imputed.",
        "- Active stations grow from 471 (Sep 2025) to 540 (Aug 2026), so national "
        "trend lines should use a fixed station panel or city medians.",
        "- Group cities as (state, city): Aurangabad and Byrnihat each occur in two "
        "states.",
        "",
        "Written by `scripts/qc_flags.py`. Original `aqi_station_daily.csv` is "
        "unchanged; use `aqi_station_daily_qc.csv` and the `aqi_qc` column for "
        "analysis.",
    ]
    (data_dir / "qc_summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"flagged rows: {k:,} ({k / n * 100:.2f}%)")
    print(f"valid AQI days: {int(df.aqi.notna().sum()):,} -> {int(df.aqi_qc.notna().sum()):,}")
    print(f"ranking panel: {int(cov.include_in_ranking.sum())} stations | "
          f"map panel: {int(cov.include_in_map.sum())} of {len(cov)}")
    print("written:")
    for p in [qc_path, cov_path, data_dir / 'qc_summary.md']:
        print("  ", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
