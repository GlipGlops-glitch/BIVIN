# BIVIN - Vintrace Automation & API Integration

Complete automation and API integration suite for Vintrace winery software.

## Overview

This repository contains:
1. **Playwright-based automation scripts** for downloading reports from Vintrace UI
2. **Complete Python API client** for Vintrace V6 REST API with all endpoints and data models
3. **Transaction lineage analysis** for tracing batch history and analyzing inventory lots

---

## 🆕 Inventory Lot Analysis

**NEW: Analyze all lots currently in inventory with complete lineage tracking**

```bash
# Fetch current vessel data
python fetch_Vessels.py
python melt_vessels.py

# Analyze all inventory lots
python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json
```

This generates:
- Summary reports of all on-hand inventory
- Lineage tracking showing which batches contributed to each lot
- Power BI compatible exports (CSV, JSON)
- Detailed per-batch reports

👉 **See [README_ANALYZE_INVENTORY.md](README_ANALYZE_INVENTORY.md) for complete guide**  
👉 **See [README_TRANSACTION_LINEAGE.md](README_TRANSACTION_LINEAGE.md) for lineage analysis details**

---

## 🆕 Vintrace V6 API Client

**NEW: Complete Python client for Vintrace V6 REST API**

Located in the `API/` directory, this provides programmatic access to all Vintrace data and operations.

### Quick Start

```python
from API import create_client_from_env

# Create client from .env file
client = create_client_from_env()

# Get work orders
work_orders = client.list_available_work_orders()

# Get all products (with automatic pagination)
products = client.get_all_pages(client.list_available_products)

# Search transactions
transactions = client.transaction_search(
    fromDate="2024-01-01",
    toDate="2024-12-31"
)
```

### API Client Features

- ✅ **37 API Endpoints**: Complete coverage of Vintrace V6 API
- ✅ **99 Pydantic Models**: Type-safe data validation
- ✅ **Automatic Pagination**: Built-in helper for list endpoints
- ✅ **Retry Logic**: Exponential backoff on failures
- ✅ **Authentication**: API key and basic auth support
- ✅ **Helper Utilities**: High-level functions for common tasks
- ✅ **Full Documentation**: Comprehensive guides and examples

👉 **See [API/QUICKSTART.md](API/QUICKSTART.md) for detailed usage**  
👉 **See [API/README.md](API/README.md) for complete documentation**

---

## Playwright Automation Scripts

Automated scripts for downloading reports from Vintrace using Playwright. The scripts are designed to be maintainable, with centralized selector management and intelligent selector tracking.

## Files

### Core Modules

- **`vintrace_helpers.py`** - Core helper functions for Vintrace automation
  - Login automation
  - Navigation helpers (New UI and Old UI)
  - Iframe management
  - Loader waiting functions
  - Report interaction helpers
  - Selector tracking system with machine learning
  - Browser initialization
  - Debug utilities

- **`vintrace_selectors.py`** - Centralized selector repository
  - All selectors extracted from actual HTML files
  - Organized by UI version (New/Old) and functional area
  - Makes selector updates easier and more maintainable
  - Prevents hardcoded selectors scattered across files

### Automation Scripts

- **`vintrace_playwright_Barrel_Report.py`** - Downloads barrel details CSV report
  - Uses New Vintrace UI
  - Exports all barrel details to CSV
  - Saves to: `Main/data/vintrace_reports/barrel_details/`

- **`vintrace_playwright_analysis_report.py`** - Downloads product analysis export
  - Uses Old Vintrace UI
  - Configures date range and filters
  - Saves to: `Main/data/vintrace_reports/analysis/`

### HTML Reference Files

- **`Vintrace_html/`** - Saved HTML files for selector analysis
  - Used to extract accurate selectors
  - Reference for troubleshooting
  - Documents the actual UI structure

## Key Features

### 1. Intelligent Selector Tracking

The helper module includes a sophisticated selector tracking system that:
- Records which selectors successfully locate elements
- Learns from historical usage patterns
- Automatically prioritizes the most reliable selectors
- Saves tracking data to `selector_tracking.json`

```python
# Selectors are automatically sorted by success rate
selectors = get_sorted_selectors("function_name", selector_list)

# Successful selectors are tracked
track_selector("function_name", selector, "css", "context", "notes")
```

### 2. Centralized Selector Management

All selectors are defined in `vintrace_selectors.py`:

```python
from vintrace_selectors import NewUISelectors, OldUISelectors, LoginSelectors

# Use organized selector classes
export_btn = NewUISelectors.EXPORT_BUTTON
reports_menu = NewUISelectors.REPORTS_MENU
```

### 3. Robust Error Handling

- Multiple fallback selectors for each element
- Debug screenshots automatically saved on errors
- Detailed logging of each step
- Graceful degradation when elements aren't found

### 4. Dual UI Support

Scripts support both:
- **New UI** (PrimeFaces framework) - Modern interface
- **Old UI** (Echo2 framework) - Classic interface

## Setup

### Prerequisites

```bash
pip install playwright python-dotenv pandas
playwright install chromium
```

### Environment Variables

Create a `.env` file with your Vintrace credentials:

```
VINTRACE_USER=your_email@example.com
VINTRACE_PW=your_password
```

## Usage

### Barrel Details Report

```bash
python vintrace_playwright_Barrel_Report.py
```

Downloads all barrel details to CSV format.

### Analysis Data Export

```bash
python vintrace_playwright_analysis_report.py
```

Downloads product analysis data with configurable date range.

## Selector Strategy

### HTML-Based Selector Extraction

All selectors in `vintrace_selectors.py` are extracted from actual Vintrace HTML files:

1. **Primary selectors** - Use exact IDs from HTML (most reliable)
   ```python
   "button#vesselsForm\\:vesselsDT\\:exportButton"  # Exact ID with escaped colon
   "button[id='vesselsForm:vesselsDT:exportButton']"  # Attribute selector format
   ```

2. **Class-based selectors** - Use specific class names
   ```python
   "button.vin-download-btn"
   "iframe.iFrameMax"
   ```

3. **Text-based selectors** - Use visible text (less reliable, more maintainable)
   ```python
   "button:has-text('Export')"
   "a:has-text('Reports')"
   ```

4. **Fallback selectors** - Generic selectors as last resort
   ```python
   "iframe"
   "button[type='submit']"
   ```

### Selector Tracking

The system learns which selectors work best:

```python
# Initial run - tries all selectors in order
# Subsequent runs - prioritizes previously successful selectors
# Data saved to selector_tracking.json
```

View selector statistics:
```python
from vintrace_helpers import _tracker
_tracker.print_summary()
print(_tracker.generate_report())
```

## Architecture

### Helper Function Categories

1. **Credential Management**
   - `load_vintrace_credentials()` - Load from .env file

2. **Loader Management**
   - `wait_for_all_vintrace_loaders()` - Wait for loading to complete
   - `wait_for_vintrace_loaders_to_appear()` - Wait for loading to start

3. **Iframe Management**
   - `get_main_iframe()` - Get the main application iframe
   - `get_iframe_by_src()` - Find iframe by source pattern

4. **Navigation**
   - `navigate_to_reports_new_ui()` - Navigate in new UI
   - `navigate_to_reports_old_ui()` - Navigate in old UI
   - `navigate_to_report_category()` - Click report category
   - `find_and_click_report_by_name()` - Find specific report

5. **Report Interaction**
   - `find_report_strip_by_title()` - Locate report configuration section
   - `select_report_format()` - Choose output format (CSV/PDF/Excel)
   - `set_report_checkbox()` - Configure report options
   - `select_report_dropdown_option()` - Select from dropdowns
   - `click_generate_button()` - Trigger report generation
   - `download_report_from_strip()` - Handle file download

6. **Utilities**
   - `initialize_browser()` - Set up Playwright browser
   - `save_debug_screenshot()` - Save debugging screenshots
   - `close_popups()` - Close tour/help dialogs
   - `vintrace_login()` - Complete login workflow

## Troubleshooting

### Selectors Not Working

1. Check `debug_screenshots/` for screenshots of failures
2. Compare HTML in `Vintrace_html/` with current live site
3. Update selectors in `vintrace_selectors.py` if UI changed
4. Check `selector_tracking.json` for historical success rates

### Login Issues

- Verify `.env` file exists and has correct credentials
- Check if login page structure changed
- Review `LoginSelectors` in `vintrace_selectors.py`

### Download Failures

- Increase timeout values if reports are large
- Check network connectivity
- Verify download directory permissions

## Maintenance

### When UI Changes

1. Save new HTML file to `Vintrace_html/`
2. Extract new selectors from HTML
3. Update `vintrace_selectors.py` with new selectors
4. Add new selectors to appropriate selector lists
5. Test scripts to verify functionality

### Adding New Reports

1. Use existing scripts as templates
2. Import helpers: `from vintrace_helpers import ...`
3. Import selectors: `from vintrace_selectors import ...`
4. Follow the pattern:
   - Login
   - Navigate to report section
   - Configure report options
   - Download report
   - Handle errors with debug screenshots

## Best Practices

### Playwright Automation
1. **Always use centralized selectors** from `vintrace_selectors.py`
2. **Track successful selectors** with `track_selector()`
3. **Use multiple fallback selectors** for reliability
4. **Save debug screenshots** on errors for troubleshooting
5. **Wait for loaders** to disappear before interacting with elements
6. **Test in non-headless mode** first to see what's happening

### API Client
1. **Use environment variables** for credentials (`.env` file)
2. **Use `get_all_pages()`** for complete data sets
3. **Use VintraceDataFetcher** for common tasks
4. **Handle errors gracefully** with try/except blocks
5. **Check response structure** - API returns paginated results
6. **Use type hints** - All methods have proper typing

## Repository Structure

```
BIVIN/
├── API/                                   # Vintrace V6 API Client
│   ├── vintrace_api_client.py             # Main API client (37 endpoints)
│   ├── vintrace_models.py                 # 99 Pydantic data models
│   ├── vintrace_api_utils.py              # Helper utilities
│   ├── generate_api_client.py             # Code generator
│   ├── requirements.txt                   # API dependencies
│   ├── README.md                          # API documentation
│   ├── QUICKSTART.md                      # Quick start guide
│   ├── IMPLEMENTATION_SUMMARY.md          # Technical details
│   └── examples/                          # 5 working examples
│       ├── example_work_orders.py
│       ├── example_export_products.py
│       ├── example_stock_details.py
│       ├── example_transactions.py
│       └── example_bulk_export.py
├── vintrace_helpers.py                    # Playwright automation helpers
├── vintrace_selectors.py                  # UI selectors
├── vintrace_playwright_Barrel_Report.py   # Barrel report automation
├── vintrace_playwright_analysis_report.py # Analysis report automation
└── Vintrace_html/                         # HTML reference files
```

## Contributing

When adding new functionality:

### For Playwright Automation:
1. Add selectors to `vintrace_selectors.py` first
2. Create helper functions in `vintrace_helpers.py` for reusable logic
3. Use the selector tracking system
4. Add debug screenshots on errors
5. Document your changes

### For API Client:
1. Update `API/vintrace-v6-apis.yaml` with new API specification
2. Run `python3 API/generate_api_client.py` to regenerate code
3. Add examples to `API/examples/` for new features
4. Update documentation in `API/README.md`
5. Test imports and basic functionality

## Related Documentation

- **[API Quick Start](API/QUICKSTART.md)** - Get started with the API client
- **[API Documentation](API/README.md)** - Complete API reference
- **[API Implementation](API/IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[OpenAPI Spec](API/vintrace-v6-apis.yaml)** - Official API specification

## License

Internal use only - Ste Michelle Wine Estates

## Author

GlipGlops-glitch
Created: 2025-01-10
Last Updated: 2025-01-11


#   git pull origin main && git add . && git commit -m "Applied Copilot agent changes" && git push origin main
