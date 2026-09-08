#!/usr/bin/env python3
"""Build the browser data file from a WHOOP CSV export.

Only migraine, anxiety, alcohol, caffeine and menstruation are read from Journal.
"""
import csv, json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATE = "%Y-%m-%d %H:%M:%S"
ALLOWLIST = {
    "Experienced a migraine?": "migraine",
    "Felt nervous or anxious?": "anxiety",
    "Have any alcoholic drinks?": "alcohol",
    "Consumed caffeine?": "caffeine",
    "Menstruating?": "menstruating",
}

def number(value):
    try: return float(value) if value else None
    except ValueError: return None

def day(value): return datetime.strptime(value, DATE).date().isoformat() if value else None

def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))

def main(source, output):
    source = Path(source)
    days = defaultdict(lambda: {"workouts": [], "symptoms": [], "context": []})
    for row in rows(source / "physiological_cycles.csv"):
        key = day(row["Cycle start time"])
        if not key: continue
        record = days[key]
        record.update({
            "date": key, "recoveryWhoop": number(row["Recovery score %"]),
            "rhr": number(row["Resting heart rate (bpm)"]), "hrv": number(row["Heart rate variability (ms)"]),
            "skinTemperature": number(row["Skin temp (celsius)"]), "spo2": number(row["Blood oxygen %"]),
            "respiratoryRate": number(row["Respiratory rate (rpm)"]), "averageHr": number(row["Average HR (bpm)"]),
            "maxHr": number(row["Max HR (bpm)"]), "calories": number(row["Energy burned (cal)"]),
            "strainWhoop": number(row["Day Strain"]), "sleep": {
                "onset": row["Sleep onset"] or None, "wake": row["Wake onset"] or None,
                "asleepMinutes": number(row["Asleep duration (min)"]), "inBedMinutes": number(row["In bed duration (min)"]),
                "lightMinutes": number(row["Light sleep duration (min)"]), "deepMinutes": number(row["Deep (SWS) duration (min)"]),
                "remMinutes": number(row["REM duration (min)"]), "awakeMinutes": number(row["Awake duration (min)"]),
                "needMinutes": number(row["Sleep need (min)"]), "debtMinutes": number(row["Sleep debt (min)"]),
                "efficiency": number(row["Sleep efficiency %"]), "consistency": number(row["Sleep consistency %"]),
            },
        })
    for row in rows(source / "workouts.csv"):
        key = day(row["Workout start time"])
        if key:
            days[key]["date"] = key
            days[key]["workouts"].append({"activity": row["Activity name"] or "Other", "durationMinutes": number(row["Duration (min)"]), "calories": number(row["Energy burned (cal)"]), "averageHr": number(row["Average HR (bpm)"]), "maxHr": number(row["Max HR (bpm)"]), "strainWhoop": number(row["Activity Strain"])})
    menstruation = set()
    for row in rows(source / "journal_entries.csv"):
        key, kind = day(row["Cycle start time"]), ALLOWLIST.get(row["Question text"])
        if not key or not kind or row["Answered yes"].lower() != "true": continue
        if kind == "menstruating": menstruation.add(key)
        elif kind in ("migraine", "anxiety"):
            days[key]["date"] = key; days[key]["symptoms"].append(kind)
        else:
            days[key]["date"] = key; days[key]["context"].append(kind)
    ordered = [days[key] for key in sorted(days)]
    starts, prior = [], None
    for key in sorted(menstruation):
        current = datetime.fromisoformat(key).date()
        if prior is None or (current - prior).days != 1: starts.append(key)
        prior = current
    for index, record in enumerate(ordered):
        prior_values = [d for d in ordered[max(0, index - 14):index] if d.get("rhr") is not None and d.get("hrv") is not None]
        if len(prior_values) >= 7 and record.get("rhr") is not None and record.get("hrv") is not None:
            rhr_base = sum(d["rhr"] for d in prior_values) / len(prior_values)
            hrv_base = sum(d["hrv"] for d in prior_values) / len(prior_values)
            signal = .55 * ((record["rhr"] - rhr_base) / rhr_base) + .45 * ((hrv_base - record["hrv"]) / hrv_base)
            record["stressScore"] = round(max(0, min(100, 50 + 50 * signal)), 1)
        else: record["stressScore"] = None
        preceding = [start for start in starts if start <= record["date"]]
        record["cycleDay"] = (datetime.fromisoformat(record["date"]).date() - datetime.fromisoformat(preceding[-1]).date()).days + 1 if preceding else None
    payload = {"schemaVersion": 1, "source": "whoop", "notes": "Experimental stress proxy; not a medical or WHOOP score.", "days": ordered, "cycleStarts": starts}
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

if __name__ == "__main__":
    if len(sys.argv) != 3: raise SystemExit("Usage: import_whoop.py WHOOP_FOLDER output.json")
    main(sys.argv[1], sys.argv[2])
