# Vintrace Fruit Report Automation

This directory contains scripts for automating the download and processing of fruit reports from Vintrace.

## Scripts

### 1. `vintrace_playwright_fruit_report.py`

Automates downloading fruit reports for a list of vessels from Vintrace.

**What it does:**
1. Reads a list of vessel names from `Main/data/vintrace_reports/analysis/unspecified_vessels.json`
2. Logs into Vintrace
3. For each vessel:
   - Searches for the vessel using the top bar search
   - Clicks on the vessel from autocomplete results
   - Navigates to the "Fruit" tab
   - Downloads the fruit report as Excel (CSV format)
4. Saves CSV files to `Main/data/vintrace_reports/fruit_reports/{vessel_name}.csv`

**Prerequisites:**
- Python 3.x
- Playwright for Python: `pip install playwright`
- Playwright browsers: `playwright install`
- pandas: `pip install pandas`
- python-dotenv: `pip install python-dotenv`
- Vintrace credentials in `.env` file:
  ```
  VINTRACE_USER=your_username
  VINTRACE_PW=your_password
  ```

**Usage:**
```bash
python vintrace_playwright_fruit_report.py
```

**Input JSON format:**
```json
{
  "vessels": [
    "CCAS1223787A(BG)",
    "VESSEL123",
    "ANOTHER_VESSEL"
  ]
}
```

**Output:**
- CSV files saved to `Main/data/vintrace_reports/fruit_reports/`
- Each file named after the vessel (sanitized for filesystem)
- Console output shows progress and any failures

### 2. `combine_fruit_reports.py`

Combines all downloaded fruit report CSV files into a single JSON file.

**What it does:**
1. Scans `Main/data/vintrace_reports/fruit_reports/` for CSV files
2. Reads and processes each CSV file
3. Combines all data into a structured JSON format
4. Saves to `Main/data/vintrace_reports/analysis/combined_fruit_reports.json`

**Prerequisites:**
- Python 3.x
- pandas: `pip install pandas`

**Usage:**
```bash
python combine_fruit_reports.py
```

**Output JSON structure:**
```json
{
  "metadata": {
    "generated_at": "2025-01-11T12:00:00",
    "total_vessels": 3,
    "total_records": 25,
    "successful_vessels": 3,
    "failed_vessels": 0
  },
  "vessels": {
    "VESSEL_NAME_1": {
      "vessel_name": "VESSEL_NAME_1",
      "record_count": 10,
      "fruit_data": [
        {
          "Type": "Fruit",
          "Weigh tag #": "WT001",
          "Vintage": 2024,
          "Variety": "Cabernet Sauvignon",
          "Sub AVA": "Oak Knoll",
          "Micro AVA": "Estate",
          "Block": "Block A",
          "Delivery Date": "2024-09-15",
          "Percent": 45.5,
          "Relative Volume": 1200
        }
        // ... more records
      ]
    }
    // ... more vessels
  }
}
```

## CSV Headers

The fruit reports contain the following columns:
- **Type**: Type of entry (e.g., "Fruit")
- **Weigh tag #**: Unique identifier for the weigh tag
- **Vintage**: Year of the vintage
- **Variety**: Grape variety
- **Sub AVA**: Sub-AVA designation
- **Micro AVA**: Micro-AVA designation
- **Block**: Vineyard block
- **Delivery Date**: Date of delivery
- **Percent**: Percentage value
- **Relative Volume**: Volume measurement

## Workflow

1. **Prepare vessel list:**
   ```bash
   # Edit Main/data/vintrace_reports/analysis/unspecified_vessels.json
   # Add the vessels you want to download reports for
   ```

2. **Download fruit reports:**
   ```bash
   python vintrace_playwright_fruit_report.py
   ```

3. **Combine into JSON:**
   ```bash
   python combine_fruit_reports.py
   ```

4. **Use the combined data:**
   - The combined JSON file can be used for analysis, reporting, or integration with other systems
   - Located at: `Main/data/vintrace_reports/analysis/combined_fruit_reports.json`

## Error Handling

Both scripts include comprehensive error handling:

- **vintrace_playwright_fruit_report.py**:
  - Tracks failed vessels
  - Provides detailed console output
  - Takes debug screenshots on errors
  - Continues processing remaining vessels even if some fail

- **combine_fruit_reports.py**:
  - Handles missing or empty CSV files
  - Reports processing errors per file
  - Continues processing remaining files
  - Includes summary of successes and failures

## Notes

- The scripts use the shared `vintrace_helpers.py` and `vintrace_selectors.py` modules
- Generated CSV and JSON files are excluded from git (see `.gitignore`)
- The Playwright script runs in headed mode by default for monitoring
- Download timeouts are set to 5 minutes per file
- Selector tracking helps improve automation reliability over time

## Troubleshooting

**Script can't find vessels:**
- Verify vessel names in the JSON file match exactly with Vintrace
- Check that vessels have autocomplete results in the search

**Download fails:**
- Check Vintrace credentials in `.env` file
- Ensure stable internet connection
- Verify the Fruit tab exists for the vessel
- Check browser debug screenshots in the repository root

**Combine script fails:**
- Ensure CSV files exist in `Main/data/vintrace_reports/fruit_reports/`
- Check CSV format matches expected headers
- Verify pandas is installed
