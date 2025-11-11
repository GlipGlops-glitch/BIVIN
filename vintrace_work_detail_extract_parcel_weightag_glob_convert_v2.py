#   python tools/vintrace_work_detail_extract_parcel_weightag_glob_convert_v2.py

import os
import csv
import json
import re
import pandas as pd
from glob import glob

CSV_SAVE_DIR = "Main/data/vintrace_reports/work_detailz"
OUTPUT_JSON = "Main/data/vintrace_reports/Main_WeighTag_Parcel.json"
BULK_WINE_INTAKES_CSV = "Main/data/vintrace_reports/Bulk_Wine_Intakes.csv"

def is_xls_compound_file(filepath):
    with open(filepath, "rb") as f:
        sig = f.read(4)
    return sig == b"\xd0\xcf\x11\xe0"

def convert_xls_to_csv(filepath):
    try:
        df = pd.read_excel(filepath, engine='xlrd')
        csv_path = os.path.splitext(filepath)[0] + "_converted.csv"
        df.to_csv(csv_path, index=False)
        print(f"[INFO] Converted XLS to CSV: {csv_path}")
        return csv_path
    except Exception as e:
        print(f"[WARN] Could not convert {filepath} as XLS: {e}")
        return None

def extract_grouped_fields_from_csv(csv_filename):
    events = []
    with open(csv_filename, newline='', encoding="utf-8", errors="replace") as csvfile:
        reader = csv.reader(csvfile)
        for row_idx, row in enumerate(reader):
            if not any(cell.strip() for cell in row):
                continue
            for cell in row:
                intake_match = re.search(r'Delivery intake #([A-Za-z0-9]+)', cell)
                if intake_match:
                    events.append((row_idx, "intake", intake_match.group(1)))
                delivery_match = re.search(r'Delivery #([A-Za-z0-9]+)', cell)
                if delivery_match:
                    events.append((row_idx, "delivery", delivery_match.group(1)))
    records = []
    seen_pairs = set()
    for i, (row_idx, typ, val) in enumerate(events):
        if typ == "delivery":
            nearest_intake = None
            nearest_dist = None
            for j, (other_row_idx, other_typ, other_val) in enumerate(events):
                if other_typ == "intake":
                    dist = abs(other_row_idx - row_idx)
                    if nearest_dist is None or dist < nearest_dist:
                        nearest_dist = dist
                        nearest_intake = other_val
            if nearest_intake:
                tup = (val, nearest_intake)
                if tup not in seen_pairs:
                    records.append({"Parcel": val, "WeighTag": nearest_intake, "SourceFile": "work_detailz"})
                    seen_pairs.add(tup)
    return records

def extract_unique_weightag_from_bulk_wine_intakes(bulk_csv, parcels_seen):
    extra_records = []
    try:
        with open(bulk_csv, newline='', encoding="utf-8", errors="replace") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                docket_no = row.get("Docket no.")
                docket_no = docket_no.strip() if docket_no else None
                if docket_no and docket_no not in parcels_seen:
                    extra_records.append({
                        "Parcel": docket_no,
                        "WeighTag": docket_no,
                        "SourceFile": "Bulk_Wine_Intakes"
                    })
                    parcels_seen.add(docket_no)
    except Exception as e:
        print(f"[ERROR] Could not extract from {bulk_csv}: {e}")
    return extra_records

def process_all_files_in_folder(folder, output_json, bulk_csv):
    all_records = []
    parcels_seen = set()

    files = sorted(glob(os.path.join(folder, "*")))
    print(f"[INFO] Found {len(files)} files in {folder}")

    # work_detailz
    for file in files:
        if not os.path.isfile(file):
            continue
        ext = os.path.splitext(file)[1].lower()
        print(f"[INFO] Processing {file} ...")
        if is_xls_compound_file(file):
            csv_path = convert_xls_to_csv(file)
            if not csv_path:
                print(f"[WARN] Skipping {file}, could not convert XLS.")
                continue
        elif ext == ".csv":
            csv_path = file
        else:
            print(f"[WARN] Skipping {file}: not recognized as xls or csv.")
            continue
        try:
            records = extract_grouped_fields_from_csv(csv_path)
            all_records.extend(records)
            for rec in records:
                parcel = rec.get("Parcel")
                if parcel:
                    parcels_seen.add(parcel)
        except Exception as e:
            print(f"[ERROR] Could not extract from {csv_path}: {e}")

    # bulk wine intakes
    extra_records_bulk = extract_unique_weightag_from_bulk_wine_intakes(bulk_csv, parcels_seen)
    all_records.extend(extra_records_bulk)

    # Exclude record where Parcel == "CC3411"
    all_records = [rec for rec in all_records if rec.get("Parcel") != "CC3411"]

    with open(output_json, 'w', encoding="utf-8") as jsonfile:
        json.dump(all_records, jsonfile, indent=4)
    print(f"[INFO] Wrote all paired records to {output_json}")

if __name__ == "__main__":
    process_all_files_in_folder(
        CSV_SAVE_DIR,
        OUTPUT_JSON,
        BULK_WINE_INTAKES_CSV
    )