
# python tools/melt_vessels.py


import os
import json
import logging
import csv
from typing import List, Dict, Any
from datetime import datetime

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

def flatten_nested_object(obj: Dict, prefix: str = '') -> Dict:
    """Flatten nested dictionary objects into dot notation."""
    flattened = {}
    if obj is None:
        return flattened
    
    for key, value in obj.items():
        new_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and key not in ['unit']:  # Keep unit/value pairs together
            flattened.update(flatten_nested_object(value, new_key))
        else:
            flattened[new_key] = value
    return flattened

def extract_main_vessels(vessels: List[Dict]) -> List[Dict]:
    """Extract main vessel information without nested arrays."""
    main_vessels = []
    
    for vessel in vessels:
        main_vessel = {
            # Basic vessel info
            'vessel_id': vessel.get('id'),
            'product_id': vessel.get('productId'),
            'name': vessel.get('name'),
            'description': vessel.get('description'),
            'vessel_type': vessel.get('vesselType'),
            'details_as_at': vessel.get('detailsAsAt'),
            
            # Winery info
            'winery_id': vessel.get('winery', {}).get('id'),
            'winery_name': vessel.get('winery', {}).get('name'),
            'winery_business_unit': vessel.get('winery', {}).get('businessUnit'),
            
            # Wine Batch info
            'wine_batch_designated_sub_region': vessel.get('wineBatch', {}).get('designatedSubRegion'),
            'wine_batch_id': vessel.get('wineBatch', {}).get('id'),
            'wine_batch_name': vessel.get('wineBatch', {}).get('name'),
            'wine_batch_description': vessel.get('wineBatch', {}).get('description'),
            'vintage': vessel.get('wineBatch', {}).get('vintage'),
            'program': vessel.get('wineBatch', {}).get('program'),
            
            # Grading info
            'grading_scale_name': vessel.get('wineBatch', {}).get('grading', {}).get('scaleName') if vessel.get('wineBatch', {}).get('grading') else None,
            
            'product_category': vessel.get('wineBatch', {}).get('productCategory'),
            'designated_product': vessel.get('wineBatch', {}).get('designatedProduct'),
            
            # Designated Variety
            'designated_variety_id': vessel.get('wineBatch', {}).get('designatedVariety', {}).get('id'),
            'designated_variety_code': vessel.get('wineBatch', {}).get('designatedVariety', {}).get('code'),
            'designated_variety_name': vessel.get('wineBatch', {}).get('designatedVariety', {}).get('name'),
            
            # Designated Region
            'designated_region_id': vessel.get('wineBatch', {}).get('designatedRegion', {}).get('id') if vessel.get('wineBatch', {}).get('designatedRegion') else None,
            'designated_region_name': vessel.get('wineBatch', {}).get('designatedRegion', {}).get('name') if vessel.get('wineBatch', {}).get('designatedRegion') else None,
            'designated_region_code': vessel.get('wineBatch', {}).get('designatedRegion', {}).get('code') if vessel.get('wineBatch', {}).get('designatedRegion') else None,
            
            # Product State
            'product_state_id': vessel.get('productState', {}).get('id'),
            'product_state_name': vessel.get('productState', {}).get('name'),
            'expected_losses_percentage': vessel.get('productState', {}).get('expectedLossesPercentage'),
            
            # Volume metrics
            'volume_value': vessel.get('volume', {}).get('value'),
            'volume_unit': vessel.get('volume', {}).get('unit'),
            'capacity_value': vessel.get('capacity', {}).get('value'),
            'capacity_unit': vessel.get('capacity', {}).get('unit'),
            'ullage_value': vessel.get('ullage', {}).get('value'),
            'ullage_unit': vessel.get('ullage', {}).get('unit'),
            'unallocated_volume_value': vessel.get('unallocatedVolume', {}).get('value'),
            'unallocated_volume_unit': vessel.get('unallocatedVolume', {}).get('unit'),
            'unallocated_percentage_of_vessel': vessel.get('unallocatedPercentageOfVessel'),
            
            # TTB Details
            'ttb_bond_id': vessel.get('ttbDetails', {}).get('bond', {}).get('id'),
            'ttb_bond_name': vessel.get('ttbDetails', {}).get('bond', {}).get('name'),
            'ttb_tax_state': vessel.get('ttbDetails', {}).get('taxState'),
            
            # TTB Tax Class (can be null)
            'ttb_tax_class_id': vessel.get('ttbDetails', {}).get('taxClass', {}).get('id') if vessel.get('ttbDetails', {}).get('taxClass') else None,
            'ttb_tax_class_name': vessel.get('ttbDetails', {}).get('taxClass', {}).get('name') if vessel.get('ttbDetails', {}).get('taxClass') else None,
            'ttb_tax_class_federal_name': vessel.get('ttbDetails', {}).get('taxClass', {}).get('federalName') if vessel.get('ttbDetails', {}).get('taxClass') else None,
            'ttb_tax_class_state_name': vessel.get('ttbDetails', {}).get('taxClass', {}).get('stateName') if vessel.get('ttbDetails', {}).get('taxClass') else None,
            
            'ttb_alcohol_percentage': vessel.get('ttbDetails', {}).get('alcoholPercentage'),
            
            # Cost breakdown
            'cost_total': vessel.get('cost', {}).get('total'),
            'cost_fruit': vessel.get('cost', {}).get('fruit'),
            'cost_overhead': vessel.get('cost', {}).get('overhead'),
            'cost_storage': vessel.get('cost', {}).get('storage'),
            'cost_additive': vessel.get('cost', {}).get('additive'),
            'cost_bulk': vessel.get('cost', {}).get('bulk'),
            'cost_packaging': vessel.get('cost', {}).get('packaging'),
            'cost_operation': vessel.get('cost', {}).get('operation'),
            'cost_freight': vessel.get('cost', {}).get('freight'),
            'cost_other': vessel.get('cost', {}).get('other'),
            
            # Beverage Type
            'beverage_type_id': vessel.get('beverageType', {}).get('id'),
            'beverage_type_name': vessel.get('beverageType', {}).get('name'),
            
            # Owner
            'owner_id': vessel.get('owner', {}).get('id'),
            'owner_name': vessel.get('owner', {}).get('name'),
            'owner_ext_id': vessel.get('owner', {}).get('extId'),
            
            # Sparkling Info
            'sparkling_state': vessel.get('sparklingInfo', {}).get('state'),
        }
        
        main_vessels.append(main_vessel)
    
    return main_vessels

def extract_compositions(vessels: List[Dict]) -> List[Dict]:
    """Extract composition data linked to vessel_id."""
    compositions = []
    
    for vessel in vessels:
        vessel_id = vessel.get('id')
        composition_list = vessel.get('composition', [])
        
        for idx, comp in enumerate(composition_list):
            composition = {
                'vessel_id': vessel_id,
                'composition_index': idx,  # To maintain order and uniqueness
                'weighting': comp.get('weighting'),
                'percentage': comp.get('percentage'),
                'component_volume_value': comp.get('componentVolume', {}).get('value'),
                'component_volume_unit': comp.get('componentVolume', {}).get('unit'),
                'vintage': comp.get('vintage'),
                
                # Block info
                'block_id': comp.get('block', {}).get('id'),
                'block_name': comp.get('block', {}).get('name'),
                'block_ext_id': comp.get('block', {}).get('extId'),
                
                # Region info
                'region_id': comp.get('region', {}).get('id'),
                'region_name': comp.get('region', {}).get('name'),
                'region_code': comp.get('region', {}).get('code'),
                
                # Variety info
                'variety_id': comp.get('variety', {}).get('id'),
                'variety_name': comp.get('variety', {}).get('name'),
                'variety_code': comp.get('variety', {}).get('code'),
                
                # SubRegion info
                'sub_region_id': comp.get('subRegion', {}).get('id'),
                'sub_region_name': comp.get('subRegion', {}).get('name'),
                'sub_region_code': comp.get('subRegion', {}).get('code'),
            }
            
            compositions.append(composition)
    
    return compositions

def extract_live_metrics(vessels: List[Dict]) -> List[Dict]:
    """Extract live metrics data linked to vessel_id."""
    live_metrics = []
    
    for vessel in vessels:
        vessel_id = vessel.get('id')
        metrics_list = vessel.get('liveMetrics', [])
        
        for metric in metrics_list:
            metric_data = {
                'vessel_id': vessel_id,
                'metric_name': metric.get('name'),
                'value': metric.get('value'),
                'non_numeric_value': metric.get('nonNumericValue'),
                'interface_mapped_name': metric.get('interfaceMappedName'),
            }
            
            live_metrics.append(metric_data)
    
    return live_metrics

def extract_allocations(vessels: List[Dict]) -> List[Dict]:
    """Extract allocation data linked to vessel_id."""
    allocations = []
    
    for vessel in vessels:
        vessel_id = vessel.get('id')
        allocation_list = vessel.get('allocations', [])
        
        for idx, alloc in enumerate(allocation_list):
            allocation = {
                'vessel_id': vessel_id,
                'allocation_index': idx,
            }
            # Flatten all allocation fields (structure may vary)
            allocation.update(flatten_nested_object(alloc))
            allocations.append(allocation)
    
    return allocations

def write_to_json(data: List[Dict], filepath: str):
    """Write data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Wrote {len(data)} records to {filepath}")

def write_to_csv(data: List[Dict], filepath: str):
    """Write data to CSV file."""
    if not data:
        logger.warning(f"No data to write to {filepath}")
        return
    
    keys = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    logger.info(f"✅ Wrote {len(data)} records to {filepath}")

if __name__ == "__main__":
    # Input and output paths
    input_file = "Main/data/GET--vessels/vessels.json"
    output_dir = "Main/data/processed_vessels"
    ensure_dir(output_dir)
    
    # Load vessels data
    logger.info(f"Loading vessels from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            vessels = json.load(f)
        logger.info(f"✅ Loaded {len(vessels)} vessels")
    except FileNotFoundError:
        logger.error(f"❌ File not found: {input_file}")
        exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing JSON: {e}")
        exit(1)
    
    # Extract data
    logger.info("Extracting main vessel information...")
    main_vessels = extract_main_vessels(vessels)
    
    logger.info("Extracting composition data...")
    compositions = extract_compositions(vessels)
    
    logger.info("Extracting live metrics data...")
    live_metrics = extract_live_metrics(vessels)
    
    logger.info("Extracting allocation data...")
    allocations = extract_allocations(vessels)
    
    # Write to JSON files
    logger.info("Writing JSON files...")
    write_to_json(main_vessels, os.path.join(output_dir, "vessels_main.json"))
    write_to_json(compositions, os.path.join(output_dir, "vessels_composition.json"))
    write_to_json(live_metrics, os.path.join(output_dir, "vessels_live_metrics.json"))
    write_to_json(allocations, os.path.join(output_dir, "vessels_allocations.json"))

    
    # Summary statistics
    logger.info("\n" + "="*50)
    logger.info("PROCESSING SUMMARY")
    logger.info("="*50)
    logger.info(f"Total vessels processed: {len(vessels)}")
    logger.info(f"Main vessel records: {len(main_vessels)}")
    logger.info(f"Composition records: {len(compositions)}")
    logger.info(f"Live metrics records: {len(live_metrics)}")
    logger.info(f"Allocation records: {len(allocations)}")
    logger.info("="*50)
    
    # Show sample vessel IDs for reference
    if main_vessels:
        logger.info(f"\nSample vessel IDs: {[v['vessel_id'] for v in main_vessels[:5]]}")