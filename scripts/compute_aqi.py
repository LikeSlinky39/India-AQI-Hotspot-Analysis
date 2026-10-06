#!/usr/bin/env python3
"""
Build a station-day AQI table (CPCB National AQI method) from the hourly CAAQMS files.

Input : ../raw_data/<year>/<station_id>_1Hr_<year>.csv   (from download_cpcb.py --freq 1Hr)
        stations.csv                                      (station master with coordinates)
Output: ../output/aqi_station_daily.csv

Method (CPCB National Air Quality Index, 2014)
----------------------------------------------
* PM2.5, PM10, NO2, SO2, NH3 : 24-hour (calendar-day) mean of hourly values,
                               valid only if >= 16 of 24 hours are present.
* CO, O3                     : maximum of the rolling 8-hour means within the day,
                               each 8-hour window valid only if >= 6 of 8 hours present.
* Sub-index by linear interpolation between CPCB breakpoints.
* AQI = max sub-index, reported only if >= 3 pollutants have a sub-index and at
  least one of them is PM2.5 or PM10. Prominent pollutant = the one giving the max.
* Above the "Severe" threshold the band is extrapolated with the upper limits commonly
  used by CPCB's AQI calculator, and the index is capped at 500.

Cleaning: negative values dropped; PM values of exactly 0 dropped (instrument
fault); physically implausible hourly spikes dropped (PM2.5 > 1000, PM10 > 2000 ug/m3,
CO > 50 mg/m3, others > 2000 ug/m3).

Usage:  python compute_aqi.py [--start 2025-09-01] [--end 2026-08-31]
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
RAW = SCRIPT_DIR.parent / "raw_data"
OUT = SCRIPT_DIR.parent / "output"

# raw column -> short name
COLS = {
    "PM2.5 (µg/m³)": "pm25",
    "PM10 (µg/m³)": "pm10",
    "NO2 (µg/m³)": "no2",
    "SO2 (µg/m³)": "so2",
    "NH3 (µg/m³)": "nh3",
    "CO (mg/m³)": "co",
    "Ozone (µg/m³)": "o3",
}
MAX_VALID = {"pm25": 1000, "pm10": 2000, "no2": 2000, "so2": 2000,
             "nh3": 2000, "co": 50, "o3": 2000}

# Concentration breakpoints (upper edge of each band); index bands are
# 0-50, 50-100, 100-200, 200-300, 300-400, 400-500.
BP = {
    "pm10": [0, 50, 100, 250, 350, 430, 510],
    "pm25": [0, 30, 60, 90, 120, 250, 380],
    "no2":  [0, 40, 80, 180, 280, 400, 520],
    "o3":   [0, 50, 100, 168, 208, 748, 1000],
    "co":   [0, 1.0, 2.0, 10, 17, 34, 51],
    "so2":  [0, 40, 80, 380, 800, 1600, 2400],
    "nh3":  [0, 200, 400, 800, 1200, 1800, 2400],
}
IDX = [0, 50, 100, 200, 300, 400, 500]
POLLUTANTS = ["pm25", "pm10", "no2", "so2", "nh3", "co", "o3"]
LABEL = {"pm25": "PM2.5", "pm10": "PM10", "no2": "NO2", "so2": "SO2",
         "nh3": "NH3", "co": "CO", "o3": "O3"}
CATEGORIES = [(50, "Good"), (100, "Satisfactory"), (200, "Moderate"),
              (300, "Poor"), (400, "Very Poor"), (np.inf, "Severe")]


def sub_index(conc: pd.Series, pol: str) -> pd.Series:
    si = np.interp(conc.to_numpy(dtype=float), BP[pol], IDX, right=500)
    return pd.Series(np.where(conc.isna(), np.nan, np.round(si)), index=conc.index)


def category(aqi: float) -> str:
    if pd.isna(aqi):
        return ""
    for hi, name in CATEGORIES:
        if aqi <= hi:
            return name
    return ""


def load_hourly(station_id: str) -> pd.DataFrame | None:
    frames = []
    for f in sorted(glob.glob(str(RAW / "*" / f"{station_id}_1Hr_*.csv"))):
        df = pd.read_csv(f, usecols=lambda c: c == "Timestamp" or c in COLS,
                         na_values=["NA", "None", ""], encoding="utf-8")
        frames.append(df.reindex(columns=["Timestamp", *COLS]))  # some stations lack gases
    if not frames:
        return None
    df = pd.concat(frames).rename(columns=COLS)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = (df.dropna(subset=["Timestamp"])
            .drop_duplicates("Timestamp")
            .set_index("Timestamp").sort_index())
    for p in POLLUTANTS:
        s = pd.to_numeric(df[p], errors="coerce")
        s = s.where((s >= 0) & (s <= MAX_VALID[p]))
        if p in ("pm25", "pm10"):
            s = s.where(s > 0)
        df[p] = s
    # regular hourly grid so rolling windows are time-true
    full = pd.date_range(df.index.min().floor("D"), df.index.max().ceil("D"),
                         freq="h", inclusive="left")
    return df.reindex(full)


def daily_for_station(h: pd.DataFrame) -> pd.DataFrame:
    day = h.index.floor("D")
    out = pd.DataFrame(index=pd.DatetimeIndex(sorted(set(day)), name="date"))
    for p in ["pm25", "pm10", "no2", "so2", "nh3"]:
        g = h[p].groupby(day)
        mean, n = g.mean(), g.count()
        out[f"{p}_24h"] = mean.where(n >= 16).round(2)
        out[f"{p}_hours"] = n
    for p in ["co", "o3"]:
        roll = h[p].rolling(8, min_periods=6).mean()
        out[f"{p}_8hmax"] = roll.groupby(day).max().round(3 if p == "co" else 2)
        out[f"{p}_hours"] = h[p].groupby(day).count()
    return out


def add_aqi(d: pd.DataFrame) -> pd.DataFrame:
    conc_col = {p: (f"{p}_8hmax" if p in ("co", "o3") else f"{p}_24h") for p in POLLUTANTS}
    si = pd.DataFrame({p: sub_index(d[conc_col[p]], p) for p in POLLUTANTS}, index=d.index)
    for p in POLLUTANTS:
        d[f"si_{p}"] = si[p]
    n = si.notna().sum(axis=1)
    has_pm = si["pm25"].notna() | si["pm10"].notna()
    valid = (n >= 3) & has_pm
    aqi = si.max(axis=1)
    d["n_pollutants"] = n
    d["aqi"] = aqi.where(valid)
    prom = si.fillna(-1).idxmax(axis=1).map(LABEL)
    d["prominent_pollutant"] = prom.where(valid, "")
    d["aqi_category"] = d["aqi"].map(category)
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-09-01")
    ap.add_argument("--end", default="2026-08-31")
    args = ap.parse_args()
    start, end = pd.Timestamp(args.start), pd.Timestamp(args.end)

    stations = pd.read_csv(SCRIPT_DIR / "stations.csv", dtype=str)
    meta_cols = ["station_id", "station_name", "city", "district", "state",
                 "latitude", "longitude"]
    parts, missing = [], []
    for i, st in enumerate(stations.itertuples(index=False), 1):
        h = load_hourly(st.station_id)
        if h is None:
            missing.append(st.station_id)
            continue
        h = h.loc[(h.index >= start - pd.Timedelta(hours=8)) & (h.index < end + pd.Timedelta(days=1))]
        if h.empty:
            continue
        d = daily_for_station(h)
        d = d.loc[(d.index >= start) & (d.index <= end)]
        conc = [c for c in d.columns if c.endswith(("_24h", "_8hmax"))]
        d = d.dropna(how="all", subset=conc)
        if d.empty:
            continue
        d = add_aqi(d).reset_index()
        for c in meta_cols:
            d[c] = getattr(st, c)
        parts.append(d)
        if i % 50 == 0:
            print(f"{i}/{len(stations)} stations processed", flush=True)

    df = pd.concat(parts, ignore_index=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["month"] = df["date"].str[:7]
    order = (["date", "month", *meta_cols,
              "aqi", "aqi_category", "prominent_pollutant", "n_pollutants"]
             + [f"{p}_24h" for p in ["pm25", "pm10", "no2", "so2", "nh3"]]
             + ["co_8hmax", "o3_8hmax"]
             + [f"si_{p}" for p in POLLUTANTS]
             + [f"{p}_hours" for p in POLLUTANTS])
    df = df[order].sort_values(["state", "city", "station_id", "date"])
    for c in ["aqi", "n_pollutants", *[f"si_{p}" for p in POLLUTANTS],
              *[f"{p}_hours" for p in POLLUTANTS]]:
        df[c] = df[c].astype("Int64")

    OUT.mkdir(exist_ok=True)
    path = OUT / "aqi_station_daily.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"\nrows: {len(df):,}   stations: {df.station_id.nunique()}   "
          f"with valid AQI: {df.aqi.notna().sum():,}")
    if missing:
        print(f"no hourly file for {len(missing)} stations: {', '.join(missing[:10])}...")
    print(f"written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
