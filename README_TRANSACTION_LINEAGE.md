# Transaction Lineage Analysis System

A complete Python-based system for analyzing vessel-batch transaction lineage in Vintrace. This system tracks which vessel-batches contributed gallons to other vessel-batches, enabling full traceability from source to final product.

## Overview

This system provides:
- **Transaction lineage tracking** - Trace any batch back to all contributing source batches
- **Power BI integration** - Export data in formats ready for Power BI reporting
- **API integration** - Fetch live transaction data from Vintrace API
- **Flexible analysis** - Analyze on-hand inventory or completed shipments
- **Full audit trail** - Track all operations, losses, and gains

## Files

### Core Analysis Scripts

1. **`transaction_lineage_analyzer.py`** - Main analyzer script
   - Loads transaction data from CSV
   - Builds lineage relationships
   - Generates reports and exports for Power BI
   - Tracks on-hand vs shipped batches

2. **`fetch_transactions_for_analysis.py`** - API integration script
   - Fetches transaction data from Vintrace API
   - Converts API format to analysis CSV format
   - Supports filtering by date, batch, owner, winery

3. **`Transaction_to_analysise.csv`** - Sample transaction data
   - Example transaction data with proper structure
   - Use as template for manual data entry
   - Can be replaced with API-fetched data

## Quick Start

### Option 1: Analyze Existing CSV Data

If you have a `Transaction_to_analysise.csv` file:

```bash
python transaction_lineage_analyzer.py
```

This will:
- Load all transactions from the CSV
- Build lineage relationships
- Generate reports in `lineage_reports/` directory

### Option 2: Fetch from Vintrace API

To fetch fresh transaction data from Vintrace:

```bash
# Fetch last 30 days of transactions
python fetch_transactions_for_analysis.py

# Fetch specific date range
python fetch_transactions_for_analysis.py --from-date 2024-01-01 --to-date 2024-12-31

# Filter by batch name
python fetch_transactions_for_analysis.py --batch-name "24CABSAUV*"

# Filter by winery
python fetch_transactions_for_analysis.py --winery-name "Canoe Ridge Winery"
```

Then run the analyzer:

```bash
python transaction_lineage_analyzer.py
```

## Data Structure

### Input CSV Format

The `Transaction_to_analysise.csv` file must contain these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Op Date** | Date of operation | 2024-01-15 |
| **Op Id** | Unique operation ID | OP-1001 |
| **Op Type** | Type of operation | Transfer, Blend, Receipt, On-Hand, Adjustment |
| **From Vessel** | Source vessel | Tank-A |
| **From Batch** | Source batch name | 24CABSAUV001 |
| **To Vessel** | Destination vessel | Tank-B |
| **To Batch** | Destination batch name | 24CABSAUV002 |
| **NET** | Net gallons transferred | 250.5 |
| **Loss/Gain Amount (gal)** | Amount lost or gained | 2.5 |
| **Loss/Gain Reason** | Reason for loss/gain | Evaporation, Racking Loss, etc. |
| **Winery** | Winery name | Canoe Ridge Winery |

### Operation Types

- **Transfer** - Move product from one vessel to another
- **Blend** - Combine multiple batches into one
- **Receipt** - Receive new product (e.g., from supplier)
- **Adjustment** - Adjust volume (sampling, topping, etc.)
- **On-Hand** - Current inventory snapshot

## Output Files

The analyzer generates several output files in the `lineage_reports/` directory:

### 1. `batch_lineage.csv` - All Lineage Relationships

Power BI ready format showing all batch relationships:

```csv
Destination_Batch,Source_Batch,Gallons_Contributed,Destination_Current_Volume,Destination_Is_On_Hand,Destination_Has_Left
24BLEND001-FINAL,24BLEND001,298.0,0.0,False,False
24BLEND001,24CABSAUV003,100.0,0.0,False,True
```

**Columns:**
- `Destination_Batch` - The batch receiving material
- `Source_Batch` - The batch contributing material
- `Gallons_Contributed` - Amount contributed from source to destination
- `Destination_Current_Volume` - Current volume of destination batch
- `Destination_Is_On_Hand` - Whether destination batch is currently in inventory
- `Destination_Has_Left` - Whether destination batch has left inventory

### 2. `batch_lineage_on_hand.csv` - On-Hand Batches Only

Same format as above, but filtered to only batches currently on-hand.

### 3. `all_transactions.csv` - All Transactions

Complete transaction history in the original format.

### 4. `complete_lineage.json` - Complete Data

Full lineage data in JSON format, including:
- Metadata (totals, counts)
- All batch lineage objects
- All transactions

## Using with Power BI

### Import the Data

1. Open Power BI Desktop
2. Get Data → Text/CSV
3. Load `lineage_reports/batch_lineage.csv`

### Create Relationships

Create a self-join on the batch_lineage table:
- Link `Destination_Batch` to `Source_Batch`
- This creates a recursive relationship for full lineage

### Example DAX Measures

**Total Contributing Batches:**
```dax
Contributing Batches = 
CALCULATE(
    DISTINCTCOUNT('batch_lineage'[Source_Batch]),
    FILTER('batch_lineage', 'batch_lineage'[Source_Batch] <> "")
)
```

**Total Gallons Contributed:**
```dax
Total Gallons = SUM('batch_lineage'[Gallons_Contributed])
```

**On-Hand Volume:**
```dax
On-Hand Volume = 
CALCULATE(
    SUM('batch_lineage'[Destination_Current_Volume]),
    'batch_lineage'[Destination_Is_On_Hand] = TRUE
)
```

### Example Visualizations

1. **Lineage Tree** - Use hierarchy visualization showing batch relationships
2. **Batch Contributions** - Stacked bar chart of contributing batches
3. **Volume Flow** - Sankey diagram showing volume flow between batches
4. **Current Inventory** - Table filtered to `Destination_Is_On_Hand = TRUE`

## Python API Usage

You can also use the analyzer as a Python module:

```python
from transaction_lineage_analyzer import TransactionLineageAnalyzer

# Load and analyze
analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')

# Get lineage for a specific batch
lineage = analyzer.get_batch_lineage('24BLEND001-FINAL')
print(f"Contributing batches: {lineage.contributing_batches}")

# Get full lineage tree (recursive)
tree = analyzer.get_full_lineage_tree('24BLEND001-FINAL')

# Generate a report
report = analyzer.generate_lineage_report('24BLEND001-FINAL')
print(report)

# Get all on-hand batches
on_hand = analyzer.get_all_on_hand_batches()
for batch in on_hand:
    lineage = analyzer.get_batch_lineage(batch)
    print(f"{batch}: {lineage.current_volume} gallons")

# Export for Power BI
analyzer.export_lineage_to_csv('my_lineage.csv')
analyzer.export_to_json('my_lineage.json')
```

## Use Cases

### 1. Lot Traceability

When a lot is selected in Power BI, show all source batches that contributed to it:

```python
analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
tree = analyzer.get_full_lineage_tree('24BLEND001-FINAL')
# Use tree data in Power BI visualization
```

### 2. Current Inventory Analysis

See what's currently on-hand and what went into it:

```python
analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
analyzer.export_lineage_to_csv('on_hand.csv', batch_filter='on-hand')
# Load on_hand.csv into Power BI
```

### 3. Audit Trail

Track all operations that affected a batch:

```python
analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
lineage = analyzer.get_batch_lineage('24BLEND001')
for trans in lineage.contributing_transactions:
    print(f"{trans.op_date}: {trans.op_type} - {trans.net} gal")
```

### 4. Loss Analysis

Analyze losses across the production chain:

```python
analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
total_loss = sum(t.loss_gain_amount for t in analyzer.transactions)
print(f"Total losses: {total_loss} gallons")
```

## Advanced Features

### Recursive Lineage Tracking

The system automatically tracks lineage recursively, so you can see:
- Direct contributors (one level)
- Full lineage tree (all levels back to origin)

Example:
```
24BLEND001-FINAL
└── 24BLEND001 (298 gal)
    ├── 24CABSAUV003 (100 gal)
    │   └── 24CABSAUV002 (250.5 gal)
    │       └── 24CABSAUV001 (250.5 gal) [ORIGIN]
    └── 24MERLOT002 (200 gal)
        └── 24MERLOT001 (300 gal) [ORIGIN]
```

### Status Tracking

Each batch is tracked with status:
- **On-Hand** - Currently in inventory
- **Shipped** - Has left inventory  
- **Unknown** - No status information

### Cycle Detection

The system detects circular references (if any) in lineage tracking.

## Troubleshooting

### No data in CSV file

Make sure your CSV file has headers and data rows. See the sample `Transaction_to_analysise.csv` for format.

### API connection issues

Ensure you have a `.env` file with Vintrace credentials:
```
VINTRACE_USER=your_email@example.com
VINTRACE_PW=your_password
```

### Empty lineage reports

Check that:
1. Transactions have valid `From Batch` and `To Batch` values
2. At least one transaction is marked as `On-Hand` to show current inventory

### Incorrect lineage relationships

Verify that:
1. Batch names are consistent across transactions
2. Op Types are correctly set (Transfer, Blend, etc.)
3. NET values are positive and accurate

## Requirements

```bash
# Core Python (no external dependencies required)
python >= 3.7

# For API integration (optional):
pip install -r API/requirements.txt
```

## Related Files

- `API/examples/example_transactions.py` - Example of using the Vintrace API for transactions
- `melt_vessels.py` - Similar vessel data processing script
- `vintrace_analysis_process.py` - Analysis data processing

## Author

GlipGlops-glitch  
Created: 2025-11-11

## License

Internal use only - Ste Michelle Wine Estates
