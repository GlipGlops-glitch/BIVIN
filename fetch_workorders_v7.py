# python tools/fetch_workorders_v7.py

import os
import json
import logging
from dotenv import load_dotenv
from datetime import datetime
from utils.endpoint_caller import EndpointCaller, setup_error_logger, setup_metrics_logger

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    return logging.getLogger(__name__)

logger = setup_logging()
metrics_logger = setup_metrics_logger("metrics.log")
error_logger = setup_error_logger("error.log")

def setup_all_logger(logfile="Log_All.log"):
    all_logger = logging.getLogger("all_logger")
    all_logger.setLevel(logging.INFO)
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith(logfile) for h in all_logger.handlers):
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(formatter)
        all_logger.addHandler(fh)
    return all_logger

all_logger = setup_all_logger("Log_All.log")

def ensure_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def date_to_epoch_ms(date_str):
    """
    Convert a date string (YYYY-MM-DD) to epoch milliseconds.
    If the date string is already epoch ms, return as int.
    """
    try:
        if date_str and date_str.isdigit() and len(date_str) > 8:
            return int(date_str)
        dt_format = "%Y-%m-%d"
        dt = datetime.strptime(date_str, dt_format)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(dt.timestamp() * 1000)
    except Exception as e:
        logger.error(f"❌ Could not convert date '{date_str}' to epoch ms: {e}")
        all_logger.error(f"❌ Could not convert date '{date_str}' to epoch ms: {e}")
        return None

def extract_ids(work_orders):
    wo_ids = []
    job_ids = []
    for wo in work_orders:
        # Work order ID
        if "id" in wo:
            wo_ids.append(wo["id"])
        # Jobs may be a list in wo['jobs']
        for job in wo.get("jobs", []):
            if "id" in job:
                job_ids.append(job["id"])
    return wo_ids, job_ids

if __name__ == "__main__":
    load_dotenv()
    VINTRACE_API_TOKEN = os.getenv("VINTRACE_API_TOKEN")
    BASE_URL = os.getenv("BASE_VINTRACE_URL", "https://us61.vintrace.net")

    endpoint_path = "/smwe/api/v7/operation/work-orders"
    url = BASE_URL + endpoint_path

    output_dir = "Main/data/GET--work_orders_paged"
    ensure_dir(output_dir)

    headers = {}
    if VINTRACE_API_TOKEN:
        headers["Authorization"] = f"Bearer {VINTRACE_API_TOKEN}"

    limit = int(os.getenv("WORK_ORDER_LIMIT", "100"))
    offset = 0
    max_offset = int(os.getenv("WORK_ORDER_MAX_OFFSET", "10000"))

    scheduled_since = os.getenv("WORK_ORDER_SCHEDULED_SINCE", "2025-08-25")
    scheduled_since_val = date_to_epoch_ms(scheduled_since) if scheduled_since else None

    logger.info(f"Fetching work orders paged using limit/offset and scheduledSince. limit={limit}, max_offset={max_offset}, scheduledSince={scheduled_since_val}")
    all_logger.info(f"Fetching work orders paged using limit/offset and scheduledSince. limit={limit}, max_offset={max_offset}, scheduledSince={scheduled_since_val}")

    endpoint_caller = EndpointCaller(
        logger=logger,
        metrics_logger=metrics_logger,
        error_logger=error_logger
    )

    all_work_orders = []
    more_data = True

    while more_data and offset < max_offset:
        params = {
            "limit": limit,
            "offset": offset,
            "scheduledSince": scheduled_since_val if scheduled_since_val else None
        }
        params = {k: v for k, v in params.items() if v is not None}
        try:
            result = endpoint_caller.call(url, headers=headers, params=params)
            work_orders = result.get("results", [])
            logger.info(f"Retrieved {len(work_orders)} work orders [offset {offset}]")
            all_logger.info(
                f"✅ {len(work_orders)} work orders [offset {offset}] | Endpoint: {url} | Params: {params}"
            )
            all_work_orders.extend(work_orders)
            if len(work_orders) < limit:
                more_data = False
            else:
                offset += limit
        except Exception as e:
            logger.error(f"❌ Error fetching work orders (offset {offset}): {e}")
            all_logger.error(
                f"❌ Error fetching work orders (offset {offset}): {e} | Endpoint: {url} | Params: {params}"
            )
            more_data = False

    output_path = os.path.join(output_dir, "work_orders_paged.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_work_orders, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Saved {len(all_work_orders)} work orders to {output_path}")
    all_logger.info(f"✅ Saved {len(all_work_orders)} work orders to {output_path} | Endpoint: {url}")

    # Extract wo_ids and job_ids lists
    wo_ids, job_ids = extract_ids(all_work_orders)
    wo_ids_path = os.path.join(output_dir, "wo_ids.json")
    job_ids_path = os.path.join(output_dir, "job_ids.json")

    with open(wo_ids_path, "w", encoding="utf-8") as f:
        json.dump(wo_ids, f, indent=2, ensure_ascii=False)
    with open(job_ids_path, "w", encoding="utf-8") as f:
        json.dump(job_ids, f, indent=2, ensure_ascii=False)

    print(f"Saved work order IDs ({len(wo_ids)}) to: {wo_ids_path}")
    print(f"Saved job IDs ({len(job_ids)}) to: {job_ids_path}")