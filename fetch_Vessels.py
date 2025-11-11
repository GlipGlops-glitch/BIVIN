# python tools/fetch_Vessels.py

import os
import json
import logging
from dotenv import load_dotenv
import requests

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def ensure_dir(dir_path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def fetch_vessels_page(url, headers, params):
    """Fetch a single page of vessels with error handling."""
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

def fetch_barrel_group_details(base_url, headers, barrel_group_id):
    """Fetch detailed information for a specific barrel group."""
    endpoint = f"/smwe/api/v7/vessel/barrel-groups/{barrel_group_id}"
    url = base_url + endpoint
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Request timed out for barrel group {barrel_group_id}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch barrel group {barrel_group_id}: {e}")
        return None

if __name__ == "__main__":
    load_dotenv()
    VINTRACE_API_TOKEN = os.getenv("VINTRACE_API_TOKEN")
    BASE_URL = os.getenv("BASE_VINTRACE_URL", "https://us61.vintrace.net")

    if not VINTRACE_API_TOKEN:
        logger.error("No VINTRACE_API_TOKEN found in environment. Exiting.")
        exit(1)

    endpoint_path = "/smwe/api/v7/report/vessel-details-report"
    url = BASE_URL + endpoint_path

    output_dir = "Main/data/GET--vessels"
    ensure_dir(output_dir)
    output_path = os.path.join(output_dir, "vessels.json")

    headers = {
        "Authorization": f"Bearer {VINTRACE_API_TOKEN}"
    }

    # Extra fields to include in the API response
    extra_fields = "composition,allocations,livemetrics"

    # First, get totalResults
    params = {
        "limit": 1,
        "offset": 0,
        "extraFields": extra_fields
    }
    
    logger.info(f"Getting total number of vessels from {url} ...")
    try:
        result = fetch_vessels_page(url, headers, params)
        total_results = result.get("totalResults", 0)
        logger.info(f"Total vessels to fetch: {total_results}")
    except Exception as e:
        logger.error(f"❌ Error fetching totalResults: {e}")
        exit(1)

    # Now, fetch all vessels in batches
    limit = 200
    offset = 0
    all_vessels = []

    logger.info(f"Fetching all vessels ({total_results}) from {url} with paginated params")

    while offset < total_results:
        params = {
            "extraFields": extra_fields,
            "limit": limit,
            "offset": offset,
        }
        logger.info(f"Requesting offset {offset} (Progress: {offset}/{total_results})")
        try:
            result = fetch_vessels_page(url, headers, params)
            vessels = result.get("results", [])
            
            if not vessels:
                logger.info("No more vessels returned, stopping pagination.")
                break

            all_vessels.extend(vessels)
            logger.info(f"Retrieved {len(vessels)} vessels at offset {offset}")

            offset += limit

        except Exception as e:
            logger.error(f"❌ Error fetching vessels at offset {offset}: {e}")
            logger.warning(f"Partial data saved: {len(all_vessels)} vessels collected so far")
            break

    # Save all vessels
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_vessels, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Saved {len(all_vessels)} vessels to {output_path}")
    except IOError as e:
        logger.error(f"❌ Error writing vessels file: {e}")
        exit(1)

    # Write first 10 records to a sample file
    sample_output_path = os.path.join(output_dir, "vessels_sample.json")
    sample_vessels = all_vessels[:10] if len(all_vessels) >= 10 else all_vessels
    try:
        with open(sample_output_path, "w", encoding="utf-8") as f:
            json.dump(sample_vessels, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Saved {len(sample_vessels)} sample vessels to {sample_output_path}")
    except IOError as e:
        logger.error(f"❌ Error writing sample file: {e}")

    # ========================================
    # NEW: Fetch barrel group details
    # ========================================
    logger.info("\n" + "="*60)
    logger.info("FETCHING BARREL GROUP DETAILS")
    logger.info("="*60)
    
    # Filter vessels to find barrel groups
    barrel_groups = [v for v in all_vessels if v.get("vesselType") == "BARREL_GROUP"]
    logger.info(f"Found {len(barrel_groups)} barrel groups")
    
    if barrel_groups:
        barrel_group_details = []
        
        for idx, barrel_group in enumerate(barrel_groups, 1):
            barrel_group_id = barrel_group.get("id")
            barrel_group_name = barrel_group.get("name")
            
            logger.info(f"Fetching barrel group {idx}/{len(barrel_groups)}: ID={barrel_group_id}, Name={barrel_group_name}")
            
            details = fetch_barrel_group_details(BASE_URL, headers, barrel_group_id)
            
            if details:
                barrel_group_details.append(details)
                logger.info(f"  ✅ Successfully fetched details for barrel group {barrel_group_id}")
            else:
                logger.warning(f"  ⚠️ Failed to fetch details for barrel group {barrel_group_id}")
        
        # Save barrel group details
        barrel_output_path = os.path.join(output_dir, "barrel_groups.json")
        try:
            with open(barrel_output_path, "w", encoding="utf-8") as f:
                json.dump(barrel_group_details, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved {len(barrel_group_details)} barrel group details to {barrel_output_path}")
        except IOError as e:
            logger.error(f"❌ Error writing barrel groups file: {e}")
        
        # Save sample barrel groups (first 5)
        if barrel_group_details:
            barrel_sample_path = os.path.join(output_dir, "barrel_groups_sample.json")
            sample_barrels = barrel_group_details[:5] if len(barrel_group_details) >= 5 else barrel_group_details
            try:
                with open(barrel_sample_path, "w", encoding="utf-8") as f:
                    json.dump(sample_barrels, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Saved {len(sample_barrels)} sample barrel groups to {barrel_sample_path}")
            except IOError as e:
                logger.error(f"❌ Error writing barrel groups sample file: {e}")
    else:
        logger.info("No barrel groups found in the vessel data")
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("FETCH SUMMARY")
    logger.info("="*60)
    logger.info(f"Total vessels fetched: {len(all_vessels)}")
    logger.info(f"Barrel groups found: {len(barrel_groups)}")
    if barrel_groups:
        logger.info(f"Barrel group details fetched: {len(barrel_group_details)}")
    logger.info("="*60)