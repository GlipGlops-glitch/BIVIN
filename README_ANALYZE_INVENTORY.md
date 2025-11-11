# Analyzing All Inventory Lots

This guide explains how to analyze all lots currently in inventory using the `analyze_all_inventory_lots.py` script.

## Overview

The script combines two data sources to provide complete inventory analysis:

1. **Transaction Data** - Historical transactions showing how batches moved and transformed
2. **Vessel Data** (Optional) - Current snapshot of what's in inventory with volumes

## Quick Start

### Option 1: Basic Analysis (Using Only Transaction Data)

```bash
python analyze_all_inventory_lots.py
```

This will:
- Convert the transaction data to a format suitable for lineage analysis
- Analyze all batches found in transactions
- Generate reports and exports

**Note:** Without vessel data, the script can only analyze batches based on transaction history. To see current inventory, use Option 2.

### Option 2: Complete Analysis (With Vessel Data)

First, fetch and process vessel data:

```bash
# Step 1: Fetch vessel data from Vintrace API
python fetch_Vessels.py

# Step 2: Process the vessel data into separate tables
python melt_vessels.py
```

This creates the `vessels_main.json` file at `Main/data/processed_vessels/vessels_main.json`.

Then run the analysis:

```bash
python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json
```

## Understanding the Vessel Data Structure

The `vessels_main.json` file contains an array of vessel records. Each record looks like this:

```json
{
  "vessel_id": 162832,
  "product_id": 22879,
  "name": "CTOU0818PORT(BG)",
  "description": "CTOU0818PORT - 262 of 1121 gal available",
  "vessel_type": "BARREL_GROUP",
  "wine_batch_name": "CTOU0818PORT",
  "wine_batch_description": "PORT WHIDBEYS 2018",
  "vintage": "2018",
  "designated_variety_name": "Touriga Nacional",
  "volume_value": 859.0,
  "volume_unit": "gal",
  "capacity_value": 1121.000000002,
  "capacity_unit": "gal",
  "winery_name": "Canoe Ridge Winery",
  ...
}
```

The script uses `wine_batch_name` and `volume_value` to identify lots currently in inventory.

## Command Line Options

```bash
# Specify a custom transaction file
python analyze_all_inventory_lots.py --transaction-file my_transactions.csv

# Specify a custom output directory
python analyze_all_inventory_lots.py --output-dir my_analysis

# Generate detailed reports for each batch (creates individual files)
python analyze_all_inventory_lots.py --detailed-reports

# Include vessel data for complete analysis
python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json

# Only convert transaction data to simple format (for testing)
python analyze_all_inventory_lots.py --convert-only
```

## Output Files

The script generates several files in the output directory (default: `inventory_analysis_reports/`):

### 1. `inventory_summary.txt`
A human-readable summary showing:
- Total on-hand batches
- Volume for each batch
- Number of contributing batches (lineage depth)
- Cross-reference between transaction and vessel data

Example:
```
====================================================================================================
ON-HAND INVENTORY DETAILS
====================================================================================================
Batch Name                               Volume (gal)    Contributing Batches
----------------------------------------------------------------------------------------------------
CTOU0818PORT                                   859.00                     3
24BLEND001                                     500.25                     5
...
----------------------------------------------------------------------------------------------------
Total Volume:                                15234.50
====================================================================================================
```

### 2. `all_batch_lineage.csv`
Power BI compatible CSV showing all lineage relationships:

| Destination_Batch | Source_Batch | Gallons_Contributed | Destination_Current_Volume | Destination_Is_On_Hand |
|-------------------|--------------|---------------------|----------------------------|------------------------|
| 24BLEND001        | 24CABSAUV003 | 100.0              | 500.25                     | True                   |
| 24BLEND001        | 24MERLOT002  | 200.0              | 500.25                     | True                   |

### 3. `on_hand_batch_lineage.csv`
Same as above, but filtered to only batches currently on-hand.

### 4. `all_transactions.csv`
All transaction data in a simple format:

| Op Date    | Op Id  | Op Type  | From Batch    | To Batch     | NET    |
|------------|--------|----------|---------------|--------------|--------|
| 9/1/2025   | 224808 | Transfer | 24CABSAUV001  | 24CABSAUV002 | 250.5  |

### 5. `complete_lineage_data.json`
Complete analysis data in JSON format, including:
- Metadata (totals, counts)
- All batch lineage objects with full details
- All transactions

### 6. `detailed_batch_reports/` (if --detailed-reports is used)
Individual text files for each batch showing:
- Complete lineage report
- All incoming transactions
- All outgoing transactions
- Contributing batches

Example: `CTOU0818PORT_lineage.txt`

## Using the Results

### Power BI Integration

1. **Import the lineage CSV:**
   - Open Power BI Desktop
   - Get Data → Text/CSV
   - Load `all_batch_lineage.csv` or `on_hand_batch_lineage.csv`

2. **Create visualizations:**
   - Hierarchy chart showing batch relationships
   - Bar chart of contributing batches
   - Table showing current inventory volumes

3. **Example DAX measures:**
   ```dax
   Total On-Hand Volume = 
   CALCULATE(
       SUM(batch_lineage[Destination_Current_Volume]),
       batch_lineage[Destination_Is_On_Hand] = TRUE
   )
   ```

### Python Analysis

Load the JSON file for custom analysis:

```python
import json

with open('inventory_analysis_reports/complete_lineage_data.json') as f:
    data = json.load(f)

# Access metadata
print(f"Total batches: {data['metadata']['total_batches']}")
print(f"On-hand batches: {data['metadata']['on_hand_batches']}")

# Access specific batch lineage
batch_data = data['batches']['CTOU0818PORT']
print(f"Contributing batches: {batch_data['contributing_batches']}")
```

### Excel Analysis

1. Open Excel
2. Data → From Text/CSV
3. Load any of the CSV files
4. Create pivot tables, charts, etc.

## Understanding the Analysis

### What is "Lineage"?

Lineage shows which source batches contributed to a destination batch. For example:

```
24BLEND001-FINAL (298 gallons)
└── Contributing from:
    ├── 24CABSAUV003 (100 gallons)
    │   └── 24CABSAUV002 (250.5 gallons)
    │       └── 24CABSAUV001 (250.5 gallons) [ORIGIN]
    └── 24MERLOT002 (200 gallons)
        └── 24MERLOT001 (300 gallons) [ORIGIN]
```

This means:
- The final blend has 298 gallons
- It came from two source batches: CABSAUV (100 gal) and MERLOT (200 gal)
- Each of those came from earlier batches
- You can trace back to the original source batches

### Transaction Types

The script analyzes various transaction types:
- **Transfer** - Move product from one vessel to another
- **Blend** - Combine multiple batches
- **Multi transfer** - Complex transfers (one-to-many or many-to-one)
- **Analysis** - Testing/sampling
- **Treatment** - Processing steps
- **Measurement** - Volume adjustments

### Identifying On-Hand Inventory

There are two ways to identify what's currently on-hand:

1. **From Transaction Data:**
   - Look for "On-Hand" operation type transactions
   - These represent inventory snapshots

2. **From Vessel Data (Recommended):**
   - Use `vessels_main.json` which shows current vessel contents
   - Filters to batches with `volume_value > 0`
   - More accurate and up-to-date

## Workflow Examples

### Example 1: Daily Inventory Report

```bash
# Fetch latest vessel data
python fetch_Vessels.py

# Process vessel data
python melt_vessels.py

# Generate inventory analysis
python analyze_all_inventory_lots.py \
  --vessels-file Main/data/processed_vessels/vessels_main.json \
  --output-dir daily_reports/$(date +%Y-%m-%d)
```

### Example 2: Specific Batch Investigation

```bash
# Generate detailed report for all batches
python analyze_all_inventory_lots.py \
  --vessels-file Main/data/processed_vessels/vessels_main.json \
  --detailed-reports

# Find your batch in detailed_batch_reports/
cat inventory_analysis_reports/detailed_batch_reports/CTOU0818PORT_lineage.txt
```

### Example 3: Power BI Data Refresh

```bash
# Update transaction data (last 90 days)
python fetch_transactions_for_analysis.py --from-date 2025-06-01 --to-date 2025-09-01

# Update vessel data
python fetch_Vessels.py
python melt_vessels.py

# Generate fresh analysis
python analyze_all_inventory_lots.py \
  --vessels-file Main/data/processed_vessels/vessels_main.json \
  --output-dir powerbi_data

# Power BI will automatically refresh when you open the report
```

## Troubleshooting

### No on-hand batches found

**Problem:** The summary shows 0 on-hand batches.

**Solution:** 
- Make sure you're using the `--vessels-file` option
- Verify that `vessels_main.json` exists and has data
- Check that vessels have `volume_value > 0`

### Batches in vessel data but not in transactions

**Problem:** Warning about batches only in vessel data.

**Explanation:** These batches exist in current inventory but don't have transaction history in your transaction data file. This can happen if:
- Transaction data is from a limited date range
- Batches were created before the transaction data starts
- Data sync issues

**Solution:**
- Fetch a wider date range of transactions
- Accept that some batches won't have complete lineage

### Transaction file format errors

**Problem:** Error converting transaction CSV.

**Solution:**
- Verify your CSV has the expected columns (see Transaction_to_analysise.csv)
- Check for encoding issues (should be UTF-8)
- Try the `--convert-only` option to debug the conversion

### Large output files

**Problem:** Reports are very large.

**Solution:**
- Don't use `--detailed-reports` unless needed
- Filter transaction data to a specific date range before analysis
- Use `--vessels-file` to focus on only current inventory

## Related Scripts

- **example_lineage_usage.py** - Examples of using the lineage analyzer module
- **transaction_lineage_analyzer.py** - The core analysis engine
- **fetch_Vessels.py** - Fetch vessel data from Vintrace API
- **melt_vessels.py** - Process vessel data into separate tables
- **fetch_transactions_for_analysis.py** - Fetch transaction data from API

## Getting Help

To see all options:
```bash
python analyze_all_inventory_lots.py --help
```

For issues or questions, refer to:
- `README_TRANSACTION_LINEAGE.md` - Details on lineage analysis
- `example_lineage_usage.py` - Example code
- This file - Complete usage guide

## Summary

**Minimum steps to analyze inventory:**

```bash
# 1. Get vessel data
python fetch_Vessels.py
python melt_vessels.py

# 2. Run analysis
python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json

# 3. Review results
cat inventory_analysis_reports/inventory_summary.txt
```

That's it! The script will generate all the reports and exports you need for inventory lot analysis.
