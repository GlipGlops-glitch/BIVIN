#   python tools/vintrace_work_detail_extract_parcel_weightag_glob.py

import csv
import json
import re
import chardet
import os
from glob import glob

def detect_encoding(file_path, sample_size=4096):
    """Detect text encoding for robust CSV reading."""
    with open(file_path, 'rb') as f:
        raw = f.read(sample_size)
    result = chardet.detect(raw)
    encoding = result['encoding']
    print(f"[INFO] Detected encoding for {file_path}: {encoding}")
    return encoding if encoding else "utf-8"

def extract_grouped_fields_from_csv(csv_filename):
    encoding = detect_encoding(csv_filename)
    events = []  # List of (row_idx, type, value)
    with open(csv_filename, newline='', encoding=encoding, errors="replace") as csvfile:
        reader = csv.reader(csvfile)
        for row_idx, row in enumerate(reader):
            if not any(cell.strip() for cell in row):  # skip blank rows
                continue
            for cell in row:
                # Intake
                intake_match = re.search(r'Delivery intake #([A-Za-z0-9]+)', cell)
                if intake_match:
                    events.append((row_idx, "intake", intake_match.group(1)))
                # Delivery
                delivery_match = re.search(r'Delivery #([A-Za-z0-9]+)', cell)
                if delivery_match:
                    events.append((row_idx, "delivery", delivery_match.group(1)))

    # Now pair each delivery with the closest intake (before or after)
    records = []
    seen_pairs = set()
    for i, (row_idx, typ, val) in enumerate(events):
        if typ == "delivery":
            # Find nearest intake (before or after)
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
                    records.append({"Delivery": val, "Intake": nearest_intake, "SourceFile": os.path.basename(csv_filename)})
                    seen_pairs.add(tup)
    return records

def process_all_csvs_in_folder(folder, output_json):
    all_records = []
    csv_files = sorted(glob(os.path.join(folder, "*.csv")))
    print(f"[INFO] Found {len(csv_files)} CSV files in {folder}")
    for csv_file in csv_files:
        print(f"[INFO] Processing {csv_file} ...")
        records = extract_grouped_fields_from_csv(csv_file)
        all_records.extend(records)
    with open(output_json, 'w', encoding="utf-8") as jsonfile:
        json.dump(all_records, jsonfile, indent=4)
    print(f"[INFO] Wrote all paired records to {output_json}")

if __name__ == "__main__":
    folder_path = 'Main/data/vintrace_reports/work_detailz'
    output_path = 'Main/data/vintrace_reports/work_detailz/work_detailz_glob.json'
    process_all_csvs_in_folder(folder_path, output_path)