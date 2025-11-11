# python tools/fetch_workorders_v7_v6_WO_combine_jsons_2025.py

import os
import json
from glob import glob
from datetime import datetime
import re

# Directory containing work order JSON files
input_dir = "Main/data/GET--work_orders_paged/v6_details"
output_file = "Main/data/GET--work_orders_paged/all_workorders_with_vessels.json"

def parse_vessels(summary):
    """
    Extracts FromVessel and ToVessel lists from summaryText if possible.
    Returns (from_vessel_list, to_vessel_list) or (None, None) if not parseable.
    """
    if "From:" in summary and "To:" in summary:
        # Regex to extract content between From: and To:
        match = re.search(r"From:(.*?)(,)?\s*To:\s*(.*)", summary)
        if match:
            from_text = match.group(1).strip()
            to_text = match.group(3).strip()

            # Remove any leading volume info from from_text (e.g., "30457 gal ofCPIGCV240004 in Padfilter2")
            # Extract vessel names (words with letters/numbers/underscores, possibly separated by commas)
            # For from_text, try to extract the last "in <Vessel>" or comma-separated list
            from_vessels = []
            # Try last "in <Vessel>"
            in_match = re.search(r"in\s+([\w\d]+)", from_text)
            if in_match:
                from_vessels = [in_match.group(1)]
            else:
                # fallback: split by comma, strip
                from_vessels = [v.strip() for v in from_text.split(",") if v.strip()]

            # To vessels: split by comma, strip
            to_vessels = [v.strip() for v in to_text.split(",") if v.strip()]
            return from_vessels, to_vessels
    return None, None

# Get a sorted list of JSON files in the directory
json_files = sorted(glob(os.path.join(input_dir, "*.json")))

enriched = []
skipped = 0

for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Skip error files
            if isinstance(data, dict) and "error" in data:
                skipped += 1
                continue
            # For each job in the work order, try to extract From/To vessels
            jobs = data.get("jobs", [])
            for job in jobs:
                summary = job.get("summaryText", "")
                from_vessels, to_vessels = parse_vessels(summary)
                if from_vessels is not None and to_vessels is not None:
                    job["FromVessel"] = from_vessels
                    job["ToVessel"] = to_vessels
            enriched.append(data)
    except Exception as e:
        print(f"Failed to load {file}: {e}")
        skipped += 1

print(f"Loaded {len(enriched)} work orders, skipped {skipped} files with errors or invalid JSON.")

# Write the enriched JSON array to the output file
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(enriched, f, indent=2, ensure_ascii=False)

print(f"Enriched JSON written to {output_file}")