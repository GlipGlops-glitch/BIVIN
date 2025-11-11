# Quick Start: Analyzing All Inventory Lots

This guide provides a quick walkthrough for analyzing all lots in your inventory.

## What You Asked For

You wanted to know how to run a Python file to analyze all lots in inventory, where vessel data is in `vessels_main.json` with the structure you provided (vessel_id, wine_batch_name, volume_value, etc.).

## The Solution

I've created **`analyze_all_inventory_lots.py`** - a comprehensive script that:
1. Reads your transaction data
2. Optionally reads vessel inventory data from `vessels_main.json`
3. Analyzes the lineage of all lots (which batches contributed to each lot)
4. Generates reports in multiple formats

## How to Run It

### Step 1: Get Vessel Data (Creates vessels_main.json)

```bash
# Fetch all vessels from Vintrace API
python fetch_Vessels.py

# Process into vessels_main.json and related files
python melt_vessels.py
```

This creates `Main/data/processed_vessels/vessels_main.json` with your vessel data.

### Step 2: Analyze All Lots

```bash
python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json
```

That's it! The script will:
- Load all vessels from `vessels_main.json`
- Find all batches with volume > 0 (current inventory)
- Trace the complete lineage for each batch
- Generate comprehensive reports

## What You Get

The script creates a folder `inventory_analysis_reports/` with these files:

1. **`inventory_summary.txt`** - Human-readable summary
   ```
   Batch Name                               Volume (gal)    Contributing Batches
   ----------------------------------------------------------------------------
   CTOU0818PORT                                   859.00                     3
   ```

2. **`all_batch_lineage.csv`** - Power BI ready data
   - Import this into Power BI to visualize lineage
   - Shows which batches contributed to which

3. **`on_hand_batch_lineage.csv`** - Only current inventory
   - Filtered to batches currently on-hand

4. **`complete_lineage_data.json`** - Full data for custom analysis

5. **`all_transactions.csv`** - All transaction history

## Command Options

```bash
# Basic usage (transaction data only)
python analyze_all_inventory_lots.py

# With vessel data (RECOMMENDED)
python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json

# Generate detailed reports for each batch
python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json --detailed-reports

# Custom output directory
python analyze_all_inventory_lots.py --output-dir my_reports

# Get help
python analyze_all_inventory_lots.py --help
```

## Understanding the Vessel Data

Your `vessels_main.json` has records like:
```json
{
  "vessel_id": 162832,
  "wine_batch_name": "CTOU0818PORT",
  "volume_value": 859.0,
  "volume_unit": "gal",
  ...
}
```

The script:
- Looks at `wine_batch_name` to identify each lot
- Checks `volume_value` to find lots with inventory (> 0)
- Cross-references with transaction data to show lineage

## Example Workflow

```bash
# Morning routine - check current inventory
python fetch_Vessels.py
python melt_vessels.py
python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json

# Review the summary
cat inventory_analysis_reports/inventory_summary.txt

# Open in Power BI
# Import inventory_analysis_reports/on_hand_batch_lineage.csv
```

## Related Files

I also reviewed the files you mentioned:

- **`example_lineage_usage.py`** - Shows 8 examples of using the lineage analyzer
- **`transaction_lineage_analyzer.py`** - The engine that traces lineage

You can use these directly if you want more control, but `analyze_all_inventory_lots.py` is designed specifically for your use case of analyzing all inventory lots.

## For More Details

See the comprehensive guide: **`README_ANALYZE_INVENTORY.md`**

It includes:
- Detailed explanations
- Power BI integration examples
- Troubleshooting tips
- Advanced workflows

## Need Help?

```bash
python analyze_all_inventory_lots.py --help
```

Or check `README_ANALYZE_INVENTORY.md` for the full documentation.
