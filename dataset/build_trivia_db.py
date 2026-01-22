#!/usr/bin/env python3
"""
Build a nested "trivia facts" database from Gapminder Systema Globalis DDF datapoints.

Input:
  - countries-etc-datapoints/*.csv  (each: geo,time,<indicator>)
  - ddf--entities--geo--country.csv (maps country code -> country name, plus is--country flag)

Output (JSON):
  {
    "Afghanistan": {
      "People & Society": { "population_total": 40218234, ... },
      "Economy": { ... },
      "Health": { ... },
      "Environment": { ... },
      "Geography & Physical": { ... }
    },
    ...
  }

Also writes a provenance version with year:
  indicator: { "value": ..., "year": ... }

Run:
  python build_trivia_db.py \
    --datapoints_dir "/path/to/countries-etc-datapoints" \
    --entities_csv "/path/to/ddf--entities--geo--country.csv" \
    --out_json "country_trivia_db.json"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple, Optional

import pandas as pd


# -----------------------------
# Category partition (5 buckets)
# -----------------------------
CATEGORIES = [
    "People & Society",
    "Economy",
    "Health",
    "Environment",
    "Geography & Physical",
]

# Keyword rules for auto-categorization.
# You can tune this over time; it’s meant to be a decent starting partition.
KEYWORDS = {
    "Health": [
        "life_expectancy", "mortality", "death", "disease", "tuberculosis", "hiv",
        "malaria", "stunting", "wasting", "nutrition", "vacc", "immun",
        "birth", "fertility", "maternal", "infant", "child",
        "health", "hospital", "doctor",
    ],
    "Economy": [
        "gdp", "income", "wage", "salary", "price", "inflation", "trade", "export", "import",
        "debt", "aid", "tax", "employment", "unemployment", "labour", "labor",
        "industry", "manufact", "service", "productivity", "poverty",
        "bank", "finance", "investment",
    ],
    "Environment": [
        "co2", "emission", "carbon", "energy", "renew", "electric", "fuel",
        "forest", "deforest", "climate", "temperature", "pollution", "pm25",
        "water_use", "water_withdrawal", "freshwater", "biodiversity",
        "land_use", "agriculture",
    ],
    "Geography & Physical": [
        "area", "land", "surface", "density", "elevation", "latitude", "longitude",
        "coast", "island", "terrain",
        "urban", "rural", "population_density",
        "landlocked",
    ],
    "People & Society": [
        "population", "education", "school", "literacy",
        "women", "men", "gender", "inequality",
        "internet", "mobile", "phone",
        "migration", "refugee",
        "democracy", "rights", "crime", "homicide",
        "age_", "aged_", "youth", "elderly",
        "housing", "electricity_access", "water_access", "sanitation",
    ],
}

def categorize_indicator(indicator: str) -> str:
    """
    Assign indicator to one of the 5 categories based on keywords.
    Priority order matters for overlaps.
    """
    s = indicator.lower()
    priority = ["Health", "Economy", "Environment", "Geography & Physical", "People & Society"]
    for cat in priority:
        for kw in KEYWORDS[cat]:
            if kw in s:
                return cat
    return "People & Society"


# ---------------------------------------
# Load country mapping from entities file
# ---------------------------------------
def load_country_mapping(entities_csv: str) -> Dict[str, str]:
    """
    Loads mapping from ddf--entities--geo--country.csv

    - code column: 'country' (e.g., afg)
    - name column: typically 'name' (if not, first column containing 'name')
    - filter: if 'is--country' exists, keep only TRUE
    """
    df = pd.read_csv(entities_csv)
    df.columns = [c.strip() for c in df.columns]

    if "country" not in df.columns:
        raise ValueError(f"Expected 'country' column in entities file. Found: {list(df.columns)}")

    # find name column
    if "name" in df.columns:
        name_col = "name"
    else:
        name_like = [c for c in df.columns if "name" in c.lower()]
        if not name_like:
            raise ValueError(
                "Could not find a name column. Expected 'name' or a column containing 'name'. "
                f"Found: {list(df.columns)}"
            )
        name_col = name_like[0]

    # filter official countries when possible
    if "is--country" in df.columns:
        df = df[df["is--country"].astype(str).str.upper() == "TRUE"]

    mapping: Dict[str, str] = {}
    for _, row in df[["country", name_col]].dropna().iterrows():
        code = str(row["country"]).strip().lower()
        name = str(row[name_col]).strip()
        if code and name:
            mapping[code] = name

    return mapping


# ---------------------------------------------------------
# Extract latest value per geo for one datapoints CSV file
# ---------------------------------------------------------
def latest_per_geo_for_file(csv_path: Path) -> Tuple[str, Dict[str, Tuple[int, float]]]:
    """
    Returns:
      (indicator_name, {geo: (latest_year, latest_value)})

    Assumes columns: geo,time,<indicator>
    """
    head = pd.read_csv(csv_path, nrows=0)
    cols = list(head.columns)

    if "geo" not in cols or "time" not in cols:
        raise ValueError(f"Missing required columns geo/time. Found: {cols}")

    value_cols = [c for c in cols if c not in ("geo", "time")]
    if len(value_cols) != 1:
        raise ValueError(f"Expected exactly 1 value column, found {len(value_cols)}: {value_cols}")

    indicator = value_cols[0]
    usecols = ["geo", "time", indicator]

    best: Dict[str, Tuple[int, float]] = {}

    # chunked read so it works even if some CSVs are big
    for chunk in pd.read_csv(csv_path, usecols=usecols, chunksize=200_000):
        chunk["geo"] = chunk["geo"].astype(str).str.strip().str.lower()
        chunk["time"] = pd.to_numeric(chunk["time"], errors="coerce").astype("Int64")
        chunk = chunk.dropna(subset=["geo", "time", indicator])

        # pick row with max year per geo in this chunk
        idx = chunk.groupby("geo")["time"].idxmax()
        sub = chunk.loc[idx, ["geo", "time", indicator]]

        for geo, t, v in sub.itertuples(index=False):
            t_int = int(t)
            v_float = float(v)
            prev = best.get(geo)
            if prev is None or t_int > prev[0]:
                best[geo] = (t_int, v_float)

    return indicator, best


# -----------------------------
# Build nested trivia database
# -----------------------------
def build_db(datapoints_dir: str, entities_csv: str) -> Tuple[dict, dict]:
    """
    Returns:
      db_values:     {country_name: {category: {indicator: value}}}
      db_with_year:  {country_name: {category: {indicator: {value, year}}}}
    """
    code_to_country = load_country_mapping(entities_csv)
    official_codes = set(code_to_country.keys())

    # pre-init so every official country exists even if missing some stats
    db_values = {
        code_to_country[code]: {cat: {} for cat in CATEGORIES}
        for code in code_to_country
    }
    db_with_year = {
        code_to_country[code]: {cat: {} for cat in CATEGORIES}
        for code in code_to_country
    }

    dp_dir = Path(datapoints_dir)
    csv_files = sorted(dp_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No datapoints CSV files found in: {datapoints_dir}")

    skipped = 0
    processed = 0

    for csv_path in csv_files:
        try:
            indicator, latest = latest_per_geo_for_file(csv_path)
        except Exception as e:
            skipped += 1
            print(f"[SKIP] {csv_path.name}: {e}")
            continue

        category = categorize_indicator(indicator)

        # fill stats for official countries only
        count_used = 0
        for geo, (year, value) in latest.items():
            if geo not in official_codes:
                continue
            country = code_to_country[geo]
            db_values[country][category][indicator] = value
            db_with_year[country][category][indicator] = {"value": value, "year": year}
            count_used += 1

        processed += 1
        print(f"[OK] {csv_path.name} -> {indicator} [{category}] | used geos: {count_used}")

    print(f"\nDone. Processed files: {processed}, skipped files: {skipped}, countries: {len(db_values)}")
    return db_values, db_with_year


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datapoints_dir", required=True, help="Path to countries-etc-datapoints folder")
    ap.add_argument("--entities_csv", required=True, help="Path to ddf--entities--geo--country.csv")
    ap.add_argument("--out_json", default="country_trivia_db.json", help="Output JSON path")
    ap.add_argument(
        "--out_json_with_year",
        default="country_trivia_db_with_year.json",
        help="Output JSON path including latest year per value (debug/provenance)",
    )
    args = ap.parse_args()

    db_values, db_with_year = build_db(args.datapoints_dir, args.entities_csv)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(db_values, f, ensure_ascii=False, indent=2)

    with open(args.out_json_with_year, "w", encoding="utf-8") as f:
        json.dump(db_with_year, f, ensure_ascii=False, indent=2)

    print(f"\nWrote:\n  - {args.out_json}\n  - {args.out_json_with_year}")


if __name__ == "__main__":
    main()
