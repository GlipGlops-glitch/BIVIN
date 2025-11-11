# python tools/upload_workorders_v7.py

import json
import os
from datetime import datetime

from utils.helpers import safe_get_path, safe_get

JSON_PATH = os.getenv("WO_JSON", "Main/data/GET--work_orders_paged/work_orders_paged.json")
OUT_DIR = os.getenv("WO_SPLIT_DIR", "Main/data/GET--wo/tables")
ID_OUT_DIR = "Main/data/id_tables"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ID_OUT_DIR, exist_ok=True)

wo_table = []
wo_jobs_table = []
wo_jobs_submitted_table = []
wo_assignedTo_table = {}
wo_issuedBy_table = {}

def format_epoch_ms(epoch_ms):
    """Convert epoch ms to 'M/D/YYYY' format (UTC)."""
    if epoch_ms is None:
        return None
    try:
        dt = datetime.utcfromtimestamp(int(epoch_ms) / 1000)
        return dt.strftime("%-m/%-d/%Y") if os.name != "nt" else dt.strftime("%#m/%#d/%Y")
        # %-m and %-d work on Unix, %#m and %#d on Windows
    except Exception:
        return str(epoch_ms)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    work_orders = json.load(f)

for wo in work_orders:
    wo_id = safe_get(wo.get("id"))
    wo_name = safe_get(wo.get("name"))
    wo_status = safe_get(wo.get("status"))
    wo_summary = safe_get(wo.get("summary"))
    wo_scheduledTime = safe_get(wo.get("scheduledTime"))

    # AssignedTo Table
    assignedTo = safe_get(wo.get("assignedTo"))
    assignedTo_id = safe_get_path(wo, ["assignedTo", "id"])
    if assignedTo_id:
        wo_assignedTo_table[assignedTo_id] = {
            "assignedTo_id": assignedTo_id,
            "assignedTo_name": safe_get_path(wo, ["assignedTo", "name"]),
            "assignedTo_extId": safe_get_path(wo, ["assignedTo", "extId"])
        }

    # IssuedBy Table
    issuedBy = safe_get(wo.get("issuedBy"))
    issuedBy_id = safe_get_path(wo, ["issuedBy", "id"])
    if issuedBy_id:
        wo_issuedBy_table[issuedBy_id] = {
            "issuedBy_id": issuedBy_id,
            "issuedBy_name": safe_get_path(wo, ["issuedBy", "name"]),
            "issuedBy_extId": safe_get_path(wo, ["issuedBy", "extId"])
        }

    wo_row = {
        "wo_id": wo_id,
        "wo_name": wo_name,
        "wo_status": wo_status,
        "wo_summary": wo_summary,
        "wo_scheduledTime": wo_scheduledTime,
        "wo_assignedTo_id": assignedTo_id,
        "wo_issuedBy_id": issuedBy_id,
    }
    wo_table.append(wo_row)

    # Jobs Table
    jobs = safe_get(wo.get("jobs")) or []
    for job in jobs:
        job_id = safe_get(job.get("id"))
        job_type = safe_get(job.get("type"))
        job_jobNumber = safe_get(job.get("jobNumber"))
        job_status = safe_get(job.get("status"))
        job_scheduledTime = safe_get(job.get("scheduledTime"))
        job_finishedTime = safe_get(job.get("finishedTime"))
        job_link = safe_get(job.get("link"))
        job_operationType = safe_get(job.get("operationType"))
        job_row = {
            "wo_id": wo_id,
            "job_id": job_id,
            "job_type": job_type,
            "job_jobNumber": job_jobNumber,
            "job_status": job_status,
            "job_scheduledTime": job_scheduledTime,
            "job_scheduledTime_formatted": format_epoch_ms(job_scheduledTime),
            "job_finishedTime": job_finishedTime,
            "job_link": job_link,
            "job_operationType": job_operationType,
        }
        wo_jobs_table.append(job_row)

        # Only add to submitted table if job_status == "SUBMITTED"
        if job_status == "SUBMITTED":
            wo_jobs_submitted_table.append(job_row)

# --- Write to JSON files (table outputs) ---
with open(os.path.join(OUT_DIR, "wo.json"), "w", encoding="utf-8") as f:
    json.dump(wo_table, f, indent=2)
with open(os.path.join(OUT_DIR, "wo_jobs.json"), "w", encoding="utf-8") as f:
    json.dump(wo_jobs_table, f, indent=2)
with open(os.path.join(OUT_DIR, "wo_jobs_submitted.json"), "w", encoding="utf-8") as f:
    json.dump(wo_jobs_submitted_table, f, indent=2)

# --- Write to JSON files (ID tables for linking) ---
with open(os.path.join(ID_OUT_DIR, "wo_assignedTo.json"), "w", encoding="utf-8") as f:
    json.dump(list(wo_assignedTo_table.values()), f, indent=2)
with open(os.path.join(ID_OUT_DIR, "wo_issuedBy.json"), "w", encoding="utf-8") as f:
    json.dump(list(wo_issuedBy_table.values()), f, indent=2)

print("Split complete! JSON tables written to", OUT_DIR, "and", ID_OUT_DIR)