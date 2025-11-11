#   python tools/vintrace_work_detail_extract_parcel_weightag_glob_convert_v2_onHand.py

import csv
import json
from collections import defaultdict

INPUT_CSV = "Main/data/vintrace_reports/Vessel_Contents_Main.csv"
OUTPUT_JSON = "Main/data/vintrace_reports/Main_OnHand.json"

def sum_onhand_by_weightag(csv_path):
    totals = defaultdict(float)
    with open(csv_path, newline='', encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parcel = row.get("Weigh tag#")
            gallons = row.get("Composition volume (gal)")
            try:
                parcel = parcel.strip() if parcel else None
                gallons = float(gallons) if gallons else 0.0
            except Exception:
                continue
            if parcel:
                totals[parcel] += gallons
    return totals

def write_json(totals, json_path):
    output = []
    for parcel, gallons in totals.items():
        output.append({
            "Parcel": parcel,
            "OnHand_Gallons": gallons
        })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)
    print(f"[INFO] Saved output to {json_path}")

if __name__ == "__main__":
    totals = sum_onhand_by_weightag(INPUT_CSV)
    write_json(totals, OUTPUT_JSON)