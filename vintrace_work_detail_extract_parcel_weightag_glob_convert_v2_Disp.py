#   python tools/vintrace_work_detail_extract_parcel_weightag_glob_convert_v2_Disp.py

import json
import csv
from collections import defaultdict

INPUT_JSON = "Main/data/vintrace_reports/disp_console/merged_all.json"
INTER_WINERY_CSV = "Main/data/vintrace_reports/Inter-Winery-Disp.csv"
OUTPUT_JSON = "Main/data/vintrace_reports/Main_BOL_WeighTag_RelVol.json"
OUTPUT_SUM_JSON = "Main/data/vintrace_reports/Main_WeighTag_SumRelVol.json"

def load_bol_exclusions(csv_path):
    bol_set = set()
    with open(csv_path, newline='', encoding="utf-8", errors="replace") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bol_val = row.get("BOL#")
            if bol_val is not None:
                bol_set.add(bol_val.strip())
    return bol_set

def extract_fields(input_path, excluded_bols):
    output = []
    sum_by_weigh_tag = defaultdict(float)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for entry in data:
            bol = entry.get("bol")
            if bol is not None and bol.strip() in excluded_bols:
                continue
            zdata = entry.get("zData", [])
            for zd in zdata:
                weigh_tag = zd.get("Weigh tag #")
                rel_vol = zd.get("Relative Volume")
                source = zd.get("source") or "Unknown"  # propagate if present, else mark Unknown
                try:
                    rel_vol_float = float(str(rel_vol).replace(",", "")) if rel_vol not in (None, "") else 0.0
                except (TypeError, ValueError):
                    rel_vol_float = 0.0
                output.append({
                    "bol": bol,
                    "Weigh tag #": weigh_tag,
                    "Relative Volume": rel_vol,
                    "source": source
                })
                if weigh_tag:
                    sum_by_weigh_tag[weigh_tag] += rel_vol_float
    return output, sum_by_weigh_tag

def write_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[INFO] Saved output to {output_path}")

if __name__ == "__main__":
    bol_exclusions = load_bol_exclusions(INTER_WINERY_CSV)
    detailed, sum_by_weigh_tag = extract_fields(INPUT_JSON, bol_exclusions)
    write_json(detailed, OUTPUT_JSON)
    sum_list = [
        {"Weigh tag #": wt, "Sum Relative Volume": vol}
        for wt, vol in sum_by_weigh_tag.items()
    ]
    write_json(sum_list, OUTPUT_SUM_JSON)