# python tools/fetch_workorders_v6_singley.py

import os
import json
import requests
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_and_save_workorder(wo_id, url, headers, detail_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            print(f"Status Code: {response.status_code} | wo_id: {wo_id} | URL: {url}")
            if response.status_code == 200:
                with open(detail_path, "w", encoding="utf-8") as f:
                    json.dump(response.json(), f, indent=2, ensure_ascii=False)
                return True
            else:
                # Save error info for troubleshooting
                with open(detail_path, "w", encoding="utf-8") as f:
                    json.dump({"error": response.text, "status_code": response.status_code}, f, indent=2, ensure_ascii=False)
                if response.status_code == 429:
                    print("Rate limit hit, sleeping for 10 seconds.")
                    time.sleep(10)
                else:
                    time.sleep(0.5)
                return False  # Don't retry except for network errors
        except requests.RequestException as e:
            print(f"Network error for wo_id {wo_id} (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print(f"Failed to fetch wo_id {wo_id} after {max_retries} attempts.")
    return False

def main():
    load_dotenv()
    BASE_URL = os.getenv("BASE_VINTRACE_URL", "https://us61.vintrace.net")
    VINTRACE_API_TOKEN = os.getenv("VINTRACE_API_TOKEN")
    WO_IDS_PATH = "Main/data/GET--work_orders_paged/wo_ids.json"  # adjust path as needed

    if not VINTRACE_API_TOKEN:
        print("Error: VINTRACE_API_TOKEN not set in environment. Exiting.")
        return

    headers = {
        "Authorization": f"Bearer {VINTRACE_API_TOKEN}",
        "Accept": "application/json"
    }

    try:
        with open(WO_IDS_PATH, "r", encoding="utf-8") as f:
            wo_ids = json.load(f)
    except Exception as e:
        print(f"Failed to load wo_ids.json: {e}")
        return

    print(f"Loaded {len(wo_ids)} work order IDs.")

    # --- Get only the largest (most recent) 50 IDs ---
    wo_ids = sorted(wo_ids, key=lambda x: int(x), reverse=True)
    wo_ids = wo_ids[:300]                                               #-----------------------------#
    print(f"Selected {len(wo_ids)} most recent work order IDs (largest 50).")

    output_dir = "Main/data/GET--work_orders_paged/v6_details"
    os.makedirs(output_dir, exist_ok=True)

    # Fetch ALL 50 regardless of whether the files already exist
    ids_to_fetch = wo_ids
    print(f"{len(ids_to_fetch)} work orders to fetch from API (starting from largest ID).")

    max_workers = 5  # Number of concurrent API calls

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for wo_id in ids_to_fetch:
            url = f"{BASE_URL}/smwe/api/v6/workorders/{wo_id}"
            detail_path = os.path.join(output_dir, f"{wo_id}.json")
            futures.append(executor.submit(fetch_and_save_workorder, wo_id, url, headers, detail_path))

        # (Optional) You can track progress here, as_completed yields futures as they complete
        for i, future in enumerate(as_completed(futures), 1):
            _ = future.result()  # You could check the return value if you want
            if i % max_workers == 0:
                time.sleep(0.5)  # Small delay to avoid hammering the API

if __name__ == "__main__":
    main()