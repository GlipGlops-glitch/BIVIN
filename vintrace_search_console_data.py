#  python tools/vintrace_search_console_data.py
import os
import csv
import json
import re
from collections import defaultdict
from datetime import datetime

CSV_DIR = "Main/data/vintrace_reports/disp_console/"
OUT_FILE = "Main/data/vintrace_reports/disp_console/merged_all.json"
SAMPLE_OUT_FILE = "Main/data/vintrace_reports/disp_console/merged_all_sample_50.json"

FIELDS_TO_KEEP = [
    "Weigh tag #",
    "Delivery Date",
    "Percent",
    "Relative Volume"
]

def parse_csv_filename(filename):
    m = re.match(
        r"report_(\d+)_BOL_(.+?)_Date_(.+?)_Qty_(.+?)_Code_(.+)\.csv", filename
    )
    if not m:
        return None
    return {
        "idx": m.group(1),
        "bol": m.group(2),
        "date": m.group(3),
        "qty": m.group(4),
        "code": m.group(5),
        "file": filename
    }

files = [f for f in os.listdir(CSV_DIR) if f.endswith(".csv")]
groups = defaultdict(dict)
for fn in files:
    meta = parse_csv_filename(fn)
    if meta:
        key = (meta["bol"], meta["date"], meta["qty"], meta["code"])
        groups[key][meta["idx"]] = fn

merged_records = []

def filter_fields(row):
    return {k: row[k] for k in FIELDS_TO_KEEP if k in row and row[k] != ""}

def make_zd_row(row, source_label):
    filtered = filter_fields(row)
    if filtered:
        filtered["source"] = source_label
    return filtered

def date_key_sort_key(key):
    date_str = key[1]
    for fmt in ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return (datetime.strptime(date_str, fmt), key)
        except Exception:
            continue
    return (date_str, key)

sorted_keys = sorted(groups.keys(), key=date_key_sort_key, reverse=True)

for key in sorted_keys:
    pair = groups[key]
    if "1" not in pair or "2" not in pair:
        print(f"Skipping incomplete pair for {key}")
        continue

    file1 = os.path.join(CSV_DIR, pair["1"])  # bulk_csv
    file2 = os.path.join(CSV_DIR, pair["2"])  # fruit_csv

    with open(file1, newline='', encoding='utf-8') as f1:
        reader1 = list(csv.DictReader(f1))
    with open(file2, newline='', encoding='utf-8') as f2:
        reader2 = list(csv.DictReader(f2))

    # Keep only the requested fields and combine both, tagging the source
    zData = [make_zd_row(row, "Bulk") for row in reader1] + [make_zd_row(row, "Fruit") for row in reader2]
    # Remove empty dicts if a row had none of the target fields
    zData = [row for row in zData if row]

    merged_records.append({
        "bol": key[0],
        "date": key[1],
        "quantity": key[2],
        "code": key[3],
        "bulk_csv": pair["1"],
        "fruit_csv": pair["2"],
        "zData": zData
    })

with open(OUT_FILE, "w", encoding="utf-8") as out:
    json.dump(merged_records, out, indent=2)

print(f"Done! Wrote {len(merged_records)} merged records to {OUT_FILE}")

# Write a sample JSON with the most recent 50 records, or all if there are fewer
sample = merged_records[:50]
with open(SAMPLE_OUT_FILE, "w", encoding="utf-8") as out:
    json.dump(sample, out, indent=2)
print(f"Sample: wrote {len(sample)} most recent records to {SAMPLE_OUT_FILE}")