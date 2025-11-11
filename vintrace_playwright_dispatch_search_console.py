#python tools/vintrace_playwright_dispatch_search_console.py --mode recent --days 7

import asyncio
import os
import sys
import datetime
import shutil
import re
import csv
import argparse
from playwright.async_api import async_playwright, Page

# Import helper functions
from vintrace_helpers import (
    load_vintrace_credentials,
    vintrace_login,
    wait_for_all_vintrace_loaders,
    initialize_browser,
    LARGE_TIMEOUT
)

CSV_SAVE_DIR = "Main/data/vintrace_reports/disp_console/"
os.makedirs(CSV_SAVE_DIR, exist_ok=True)

ALL_DISPATCHES_CSV = "Main/data/vintrace_reports/all_dispatches.csv"
MISSING_DISPATCHES_CSV = "Main/data/vintrace_reports/disp_console/missing_dispatches.csv"
DOWNLOAD_TIMEOUT = 240000  # 4 minutes

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_filename(s):
    """Sanitize a string for use in filenames."""
    return re.sub(r'[\\/*?:"<>|]', '_', str(s))

def normalize_date(date_str):
    """Convert M/D/YYYY or MM/DD/YYYY or MM-DD-YYYY to MM-DD-YYYY."""
    date_str = date_str.strip().replace("-", "/")
    parts = date_str.split("/")
    if len(parts) == 3:
        mm = parts[0].zfill(2)
        dd = parts[1].zfill(2)
        yyyy = parts[2]
        return f"{mm}-{dd}-{yyyy}"
    return date_str

def get_date_range(days=7):
    """Returns (from_date, to_date) as MM/DD/YYYY strings for the last N days."""
    today = datetime.datetime.today()
    from_date = today - datetime.timedelta(days=days)
    return from_date.strftime("%m/%d/%Y"), today.strftime("%m/%d/%Y")

def date_to_ui_format(date_str):
    """Convert MM-DD-YYYY to MM/DD/YYYY for UI input."""
    try:
        return datetime.datetime.strptime(date_str, "%m-%d-%Y").strftime("%m/%d/%Y")
    except Exception:
        return date_str

# ============================================================================
# CSV FILE TRACKING FUNCTIONS
# ============================================================================

def check_files_exist(date, bol, quantity, code):
    """Check if both CSV files exist for a given record."""
    files = os.listdir(CSV_SAVE_DIR)
    bol_s = sanitize_filename(bol)
    date_s = sanitize_filename(date)
    qty_s = sanitize_filename(quantity)
    code_s = sanitize_filename(code)
    
    bulk_pattern = f"report_1_BOL_{bol_s}_Date_{date_s}_Qty_{qty_s}_Code_{code_s}.csv"
    fruit_pattern = f"report_2_BOL_{bol_s}_Date_{date_s}_Qty_{qty_s}_Code_{code_s}.csv"
    
    return bulk_pattern in files and fruit_pattern in files

def already_downloaded_files():
    """Returns a set of records (date, bol, quantity, code) for which both CSVs exist."""
    existing = set()
    files = os.listdir(CSV_SAVE_DIR)
    pattern = r"report_1_BOL_(.+?)_Date_(.+?)_Qty_(.+?)_Code_(.+)\.csv"
    
    for fn in files:
        m = re.match(pattern, fn)
        if m:
            bol, date, quantity, code = m.group(1), m.group(2), m.group(3), m.group(4)
            bulk_fn = f"report_1_BOL_{bol}_Date_{date}_Qty_{quantity}_Code_{code}.csv"
            fruit_fn = f"report_2_BOL_{bol}_Date_{date}_Qty_{quantity}_Code_{code}.csv"
            if bulk_fn in files and fruit_fn in files:
                existing.add((date, bol, quantity, code))
    return existing

def load_all_dispatches(csv_path):
    """Load all dispatches from CSV as list of dicts."""
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = []
        for row in reader:
            records.append({
                "date": normalize_date(row["date"].strip()),
                "bol": row["bol"].strip(),
                "quantity": row["quantity"].strip(),
                "code": row.get("code", "").strip()
            })
        return records

def find_missing_dispatches():
    """Compare all_dispatches.csv with downloaded files and return missing records."""
    all_dispatches = load_all_dispatches(ALL_DISPATCHES_CSV)
    fetched = already_downloaded_files()
    
    missing = []
    for rec in all_dispatches:
        key = (
            sanitize_filename(rec["date"]), 
            sanitize_filename(rec["bol"]), 
            sanitize_filename(rec["quantity"]), 
            sanitize_filename(rec["code"])
        )
        if key not in fetched:
            missing.append(rec)
    
    return all_dispatches, fetched, missing

# ============================================================================
# VINTRACE PAGE INTERACTION FUNCTIONS
# ============================================================================

async def wait_for_vintrace_loader(page: Page, timeout=LARGE_TIMEOUT):
    """Wait for specific vintrace loader to disappear."""
    is_visible = await page.evaluate("""
        () => {
            const el = document.getElementById('serverDelayMessageLong');
            return el && getComputedStyle(el).visibility === 'visible';
        }
    """)
    if is_visible:
        print("Waiting for vintrace loader to disappear...")
        await page.wait_for_function(
            """() => {
                const el = document.getElementById('serverDelayMessageLong');
                return el && getComputedStyle(el).visibility === 'hidden';
            }""",
            timeout=timeout
        )

async def show_dispatch_search_options(page: Page):
    """Click Search dropdown and Dispatch search option."""
    print("Opening Dispatch search...")
    try:
        await page.wait_for_selector('#c_32SubMenuIMG', timeout=LARGE_TIMEOUT)
        await page.click('#c_32SubMenuIMG')
        print("Clicked Search dropdown.")
    except Exception as e:
        print(f"Could not click Search dropdown: {e}")

    try:
        await page.wait_for_selector('td#c_42_td_0', timeout=LARGE_TIMEOUT)
        await page.click('td#c_42_td_0')
        print('Clicked "Dispatch search".')
    except Exception as e:
        print(f'Could not click "Dispatch search": {e}')

async def fill_dispatch_search_form(page: Page, from_date: str = None, to_date: str = None, bol: str = None):
    """Fill dispatch search form fields."""
    if from_date:
        try:
            await page.wait_for_selector('#c_353', timeout=LARGE_TIMEOUT)
            await page.fill('#c_353', from_date)
            print(f'Filled From date: {from_date}')
        except Exception as e:
            print(f"Could not fill From date: {e}")
    
    if to_date:
        try:
            await page.wait_for_selector('#c_363', timeout=LARGE_TIMEOUT)
            await page.fill('#c_363', to_date)
            print(f'Filled To date: {to_date}')
        except Exception as e:
            print(f"Could not fill To date: {e}")
    
    if bol:
        try:
            await page.wait_for_selector('#c_314', timeout=LARGE_TIMEOUT)
            await page.fill('#c_314', bol)
            print(f'Filled BOL: {bol}')
        except Exception as e:
            print(f"Could not fill BOL: {e}")

async def click_search_button(page: Page):
    """Click the Search button."""
    try:
        await page.wait_for_selector('#c_302', timeout=LARGE_TIMEOUT)
        await page.click('#c_302')
        print('Clicked Search button.')
    except Exception as e:
        print(f'Could not click Search button: {e}')

async def get_dispatch_table_keys(page: Page):
    """Extract all dispatch records from the table."""
    await page.wait_for_selector("#c_305_tbody > tr", timeout=LARGE_TIMEOUT)
    rows = await page.query_selector_all("#c_305_tbody > tr")
    keys = []
    for row in rows:
        cells = await row.query_selector_all("td")
        if len(cells) > 2:
            date_raw = (await cells[0].inner_text()).strip()
            date = normalize_date(date_raw)
            bol = (await cells[1].inner_text()).strip()
            quantity = (await cells[2].inner_text()).strip()
            keys.append((date, bol, quantity))
    return keys

async def select_dispatch_row(page: Page, target_date: str, target_bol: str, target_quantity: str):
    """Select a specific dispatch row and return its info."""
    await wait_for_all_vintrace_loaders(page)
    await page.wait_for_selector("#c_305_tbody > tr", timeout=LARGE_TIMEOUT)
    rows = await page.query_selector_all("#c_305_tbody > tr")
    
    for i, row in enumerate(rows):
        cells = await row.query_selector_all("td")
        if len(cells) > 4:
            date_raw = (await cells[0].inner_text()).strip()
            date = normalize_date(date_raw)
            bol = (await cells[1].inner_text()).strip()
            quantity = (await cells[2].inner_text()).strip()
            
            if date == target_date and bol == target_bol and quantity == target_quantity:
                await row.scroll_into_view_if_needed()
                await wait_for_all_vintrace_loaders(page)
                await row.click()
                print(f"Selected row: Date={date}, BOL={bol}, Qty={quantity}")
                await page.wait_for_timeout(2000)
                code = (await cells[4].inner_text()).strip()
                return {
                    "date": date,
                    "bol": bol,
                    "quantity": quantity,
                    "code": code
                }
    
    print(f"Row not found: Date={target_date}, BOL={target_bol}, Qty={target_quantity}")
    return None

async def click_view_wine_details(page: Page):
    """Click the View wine details button."""
    try:
        await page.wait_for_selector('button:has-text("View wine details")', timeout=LARGE_TIMEOUT)
        await page.click('button:has-text("View wine details")')
        print('Clicked "View wine details".')
        await page.wait_for_timeout(2000)
        return True
    except Exception as e:
        print(f'Could not click "View wine details": {e}')
        return False

async def click_fruit_tab(page: Page):
    """Click the Fruit tab in the wine details window."""
    try:
        # Check if loader is visible before clicking
        is_visible = await page.evaluate("""
            () => {
                const el = document.getElementById('serverDelayMessageLong');
                return el && getComputedStyle(el).visibility === 'visible';
            }
        """)
        if is_visible:
            print("Loader visible, waiting 6 seconds...")
            await page.wait_for_timeout(6000)
        
        await page.wait_for_selector('div.tabInactive, div.tabActive', timeout=LARGE_TIMEOUT)
        tabs = await page.query_selector_all('div.tabInactive, div.tabActive')
        
        for tab in tabs:
            tab_text = (await tab.inner_text()).strip()
            if tab_text.lower() == "fruit":
                await tab.scroll_into_view_if_needed()
                await tab.click()
                print('Clicked "Fruit" tab.')
                
                # Wait for tab to become active
                await page.wait_for_function(
                    """(el) => el.className.includes('tabActive')""",
                    arg=tab,
                    timeout=200000
                )
                await wait_for_vintrace_loader(page)
                
                # Wait for CSV buttons to appear
                for _ in range(10):
                    csv_buttons = await page.query_selector_all('button:visible')
                    csv_count = sum(1 for btn in csv_buttons if (await btn.inner_text()).strip() == "CSV")
                    if csv_count >= 2:
                        break
                    await page.wait_for_timeout(500)
                
                return True
        
        print('Could not find "Fruit" tab.')
        return False
    except Exception as e:
        print(f'Error clicking "Fruit" tab: {e}')
        return False

async def download_csv_files(page: Page, info: dict):
    """Download both CSV files from the Fruit tab."""
    try:
        await page.wait_for_selector('button:visible', timeout=LARGE_TIMEOUT)
        
        # Find CSV buttons
        csv_buttons = []
        for button in await page.query_selector_all('button:visible'):
            text = (await button.inner_text()).strip()
            if text == "CSV":
                csv_buttons.append(button)
        
        # Retry finding buttons if needed
        retries = 0
        while len(csv_buttons) < 2 and retries < 10:
            await page.wait_for_timeout(500)
            csv_buttons = []
            for button in await page.query_selector_all('button:visible'):
                text = (await button.inner_text()).strip()
                if text == "CSV":
                    csv_buttons.append(button)
            retries += 1
        
        if len(csv_buttons) != 2:
            print(f"Expected 2 CSV buttons, found {len(csv_buttons)}.")
            return False
        
        # Download both files
        for idx, button in enumerate(csv_buttons):
            async with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
                await button.click()
                print(f'Clicked CSV button #{idx+1}')
            
            download = await download_info.value
            temp_path = await download.path()
            
            # Build filename
            bol = sanitize_filename(info['bol'])
            date = sanitize_filename(info['date'])
            code = sanitize_filename(info['code'])
            quantity = sanitize_filename(info['quantity'])
            
            filename = f"report_{idx+1}_BOL_{bol}_Date_{date}_Qty_{quantity}_Code_{code}.csv"
            save_path = os.path.join(CSV_SAVE_DIR, filename)
            
            shutil.move(temp_path, save_path)
            print(f"Saved: {filename}")
        
        return True
    except Exception as e:
        print(f"Error downloading CSV files: {e}")
        return False

async def close_wine_details_window(page: Page):
    """Close the wine details window."""
    try:
        await page.wait_for_selector('div[id$="_close"].echo2-window-pane-close', timeout=LARGE_TIMEOUT)
        close_buttons = await page.query_selector_all('div[id$="_close"].echo2-window-pane-close')
        
        for button in close_buttons:
            if await button.is_visible():
                await button.scroll_into_view_if_needed()
                await button.click()
                await page.wait_for_timeout(1000)
                
                # Check if window closed
                try:
                    visible = await button.is_visible()
                except Exception:
                    visible = False
                
                if not visible:
                    print("Closed wine details window.")
                    break
        
        await wait_for_all_vintrace_loaders(page)
        await page.wait_for_selector("#c_305_tbody > tr", state="visible", timeout=LARGE_TIMEOUT)
        await page.wait_for_timeout(500)
        return True
    except Exception as e:
        print(f"Error closing window: {e}")
        return False

# ============================================================================
# MAIN WORKFLOW FUNCTIONS
# ============================================================================

async def process_single_dispatch(page: Page, record: dict, search_first: bool = False):
    """
    Process a single dispatch record.
    
    Args:
        page: Playwright page object
        record: Dict with keys: date, bol, quantity, code (optional)
        search_first: If True, perform search before selecting row
    
    Returns:
        True if successful, False otherwise
    """
    date = record['date']
    bol = record['bol']
    quantity = record['quantity']
    code = record.get('code', '')
    
    print(f"\n{'='*60}")
    print(f"Processing: Date={date}, BOL={bol}, Qty={quantity}")
    print(f"{'='*60}")
    
    # Check if files already exist
    if code and check_files_exist(date, bol, quantity, code):
        print("✓ Files already exist, skipping.")
        return True
    
    try:
        # Search if needed (for fetch mode)
        if search_first:
            date_ui = date_to_ui_format(date)
            await fill_dispatch_search_form(page, from_date=date_ui, to_date=date_ui, bol=bol)
            await click_search_button(page)
            await page.wait_for_timeout(1000)
        
        # Select the row
        info = await select_dispatch_row(page, date, bol, quantity)
        if not info:
            print("✗ Could not select row.")
            return False
        
        # Open wine details
        if not await click_view_wine_details(page):
            print("✗ Could not open wine details.")
            return False
        
        # Click Fruit tab
        if not await click_fruit_tab(page):
            print("✗ Could not open Fruit tab.")
            await close_wine_details_window(page)
            return False
        
        # Download CSV files
        success = await download_csv_files(page, info)
        
        # Close window
        await close_wine_details_window(page)
        
        if success:
            print("✓ Successfully downloaded both CSV files.")
            return True
        else:
            print("✗ Failed to download CSV files.")
            return False
            
    except Exception as e:
        print(f"✗ Error processing dispatch: {e}")
        return False

async def mode_recent(page: Page, days: int = 7):
    """Download dispatches from the last N days (skip existing)."""
    print(f"\n{'='*60}")
    print(f"MODE: RECENT (last {days} days)")
    print(f"{'='*60}\n")
    
    from_date, to_date = get_date_range(days)
    
    # Perform search
    await fill_dispatch_search_form(page, from_date=from_date, to_date=to_date)
    await click_search_button(page)
    await page.wait_for_timeout(1000)
    
    # Get all records
    keys = await get_dispatch_table_keys(page)
    print(f"\nFound {len(keys)} dispatches in date range.")
    
    # Process each record
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, (date, bol, quantity) in enumerate(keys, 1):
        print(f"\n--- Record {i}/{len(keys)} ---")
        record = {"date": date, "bol": bol, "quantity": quantity}
        
        # We don't have code yet, so we can't check file existence perfectly
        # Just try to process and let it handle duplicates
        result = await process_single_dispatch(page, record, search_first=False)
        
        if result:
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {success_count} succeeded, {skip_count} skipped, {fail_count} failed")
    print(f"{'='*60}\n")

async def mode_fetch(page: Page, csv_path: str):
    """Download dispatches from a CSV list."""
    print(f"\n{'='*60}")
    print(f"MODE: FETCH from {csv_path}")
    print(f"{'='*60}\n")
    
    records = load_all_dispatches(csv_path)
    print(f"Loaded {len(records)} records from CSV.")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, record in enumerate(records, 1):
        print(f"\n--- Record {i}/{len(records)} ---")
        result = await process_single_dispatch(page, record, search_first=True)
        
        if result:
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {success_count} succeeded, {skip_count} skipped, {fail_count} failed")
    print(f"{'='*60}\n")

def mode_missing():
    """Identify missing dispatches and create CSV."""
    print(f"\n{'='*60}")
    print(f"MODE: MISSING (analyze only)")
    print(f"{'='*60}\n")
    
    all_dispatches, fetched, missing = find_missing_dispatches()
    
    print(f"Total dispatches in {ALL_DISPATCHES_CSV}: {len(all_dispatches)}")
    print(f"Already fetched: {len(fetched)}")
    print(f"Missing: {len(missing)}")
    
    if missing:
        with open(MISSING_DISPATCHES_CSV, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["date", "bol", "quantity", "code"])
            writer.writeheader()
            writer.writerows(missing)
        print(f"\n✓ Wrote missing dispatches to: {MISSING_DISPATCHES_CSV}")
        print(f"  Run with --mode fetch --csv {MISSING_DISPATCHES_CSV} to download them.")
    else:
        print("\n✓ No missing dispatches!")
    
    print(f"\n{'='*60}\n")

# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="Vintrace Dispatch Search Console - Download dispatch CSV reports"
    )
    parser.add_argument(
        '--mode',
        choices=['recent', 'missing', 'fetch'],
        default='recent',
        help='Operation mode: recent (last N days), missing (find missing), fetch (from CSV)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (for recent mode, default: 7)'
    )
    parser.add_argument(
        '--csv',
        type=str,
        help='CSV file path (for fetch mode)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    args = parser.parse_args()
    
    # Mode: missing (no browser needed)
    if args.mode == 'missing':
        mode_missing()
        return
    
    # Mode: fetch (require CSV path)
    if args.mode == 'fetch' and not args.csv:
        print("Error: --csv is required for fetch mode")
        sys.exit(1)
    
    # Load credentials
    USERNAME, PASSWORD = load_vintrace_credentials()
    if not USERNAME or not PASSWORD:
        sys.exit(1)
    
    # Initialize browser
    async with async_playwright() as p:
        browser, context, page = await initialize_browser(p, headless=args.headless)
        
        try:
            # Login (navigate to old UI)
            print("Logging in...")
            success = await vintrace_login(page, USERNAME, PASSWORD, navigate_to_old_url=True)
            if not success:
                print("✗ Login failed.")
                return
            
            # Open Dispatch Search
            await show_dispatch_search_options(page)
            
            # Run appropriate mode
            if args.mode == 'recent':
                await mode_recent(page, days=args.days)
            elif args.mode == 'fetch':
                await mode_fetch(page, args.csv)
            
            print("✓ Done.")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())