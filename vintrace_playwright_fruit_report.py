"""
Vintrace Fruit Report Automation
Downloads fruit reports for vessels specified in unspecified_vessels.json

This script:
1. Loads vessel list from Main/data/vintrace_reports/analysis/unspecified_vessels.json
2. Logs into Vintrace
3. For each vessel:
   - Searches for the vessel in the top search bar
   - Clicks on the vessel from autocomplete results
   - Navigates to the "Fruit" tab
   - Downloads the fruit report as Excel (CSV)
4. Saves CSV files to Main/data/vintrace_reports/fruit_reports/

Usage: python vintrace_playwright_fruit_report.py

Author: GlipGlops-glitch
Created: 2025-01-11
"""
import asyncio
import os
import sys
import json
import shutil
import re
from playwright.async_api import async_playwright, Page

# Import helper functions
from vintrace_helpers import (
    load_vintrace_credentials,
    vintrace_login,
    wait_for_all_vintrace_loaders,
    get_main_iframe,
    initialize_browser,
    save_debug_screenshot,
    track_selector,
    LARGE_TIMEOUT
)

DOWNLOAD_TIMEOUT = 300_000  # 5 minutes
SEARCH_TIMEOUT = 30_000  # 30 seconds

# Input file with vessel list
VESSELS_JSON_PATH = "Main/data/vintrace_reports/analysis/unspecified_vessels.json"

# Output directory for fruit reports
FRUIT_REPORTS_DIR = "Main/data/vintrace_reports/fruit_reports/"
os.makedirs(FRUIT_REPORTS_DIR, exist_ok=True)


def load_vessel_list():
    """Load the list of vessels from JSON file"""
    if not os.path.exists(VESSELS_JSON_PATH):
        print(f"❌ ERROR: Vessel list file not found: {VESSELS_JSON_PATH}")
        return None
    
    try:
        with open(VESSELS_JSON_PATH, 'r') as f:
            data = json.load(f)
            vessels = data.get('vessels', [])
            print(f"✓ Loaded {len(vessels)} vessels from {VESSELS_JSON_PATH}")
            return vessels
    except Exception as e:
        print(f"❌ ERROR: Failed to load vessel list: {e}")
        return None


def sanitize_filename(vessel_name):
    """Sanitize vessel name for use as filename"""
    # Remove or replace characters that are invalid in filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', vessel_name)
    return sanitized


async def search_and_select_vessel(page: Page, vessel_name: str):
    """
    Search for a vessel in the top search bar and select it
    
    Args:
        page: Playwright Page object
        vessel_name: Name of the vessel to search for
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"SEARCHING FOR VESSEL: {vessel_name}")
    print('=' * 60)
    
    # Get the main iframe
    iframe = await get_main_iframe(page)
    
    # Wait for page to be ready
    await wait_for_all_vintrace_loaders(iframe)
    await asyncio.sleep(2)
    
    # Step 1: Find and click the search input
    print("🔍 Finding search bar...")
    
    search_input_selectors = [
        "input#topBarForm\\:quicksearchAC_input",
        "input[id='topBarForm:quicksearchAC_input']",
        "input.vx-autocomplete-input",
        "input.ui-autocomplete-input"
    ]
    
    search_input = None
    for selector in search_input_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=SEARCH_TIMEOUT, state="visible")
            search_input = await iframe.query_selector(selector)
            if search_input:
                print(f"✓ Found search input using selector: {selector}")
                track_selector("search_and_select_vessel", selector, "css", "search_input", "Top bar search input")
                break
        except Exception as e:
            continue
    
    if not search_input:
        print("❌ ERROR: Could not find search input")
        await save_debug_screenshot(page, f"search_input_error_{vessel_name}")
        return False
    
    # Step 2: Clear and type vessel name
    print(f"⌨️  Typing vessel name: {vessel_name}")
    try:
        await search_input.click()
        await asyncio.sleep(0.5)
        await search_input.fill("")
        await asyncio.sleep(0.3)
        await search_input.type(vessel_name, delay=100)  # Type with delay
        await asyncio.sleep(2)  # Wait for autocomplete to populate
        print(f"✓ Typed vessel name")
    except Exception as e:
        print(f"❌ ERROR: Failed to type vessel name: {e}")
        return False
    
    # Step 3: Wait for autocomplete panel to appear and select the vessel
    print("⏳ Waiting for autocomplete results...")
    
    autocomplete_panel_selectors = [
        "span#topBarForm\\:quicksearchAC_panel",
        "span[id='topBarForm:quicksearchAC_panel']",
        "span.ui-autocomplete-panel"
    ]
    
    autocomplete_panel = None
    for selector in autocomplete_panel_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=SEARCH_TIMEOUT, state="visible")
            autocomplete_panel = await iframe.query_selector(selector)
            if autocomplete_panel:
                print(f"✓ Found autocomplete panel using selector: {selector}")
                track_selector("search_and_select_vessel", selector, "css", "autocomplete_panel", "Autocomplete panel")
                break
        except Exception as e:
            continue
    
    if not autocomplete_panel:
        print("❌ ERROR: Autocomplete panel did not appear")
        await save_debug_screenshot(page, f"autocomplete_error_{vessel_name}")
        return False
    
    # Step 4: Click on the first autocomplete result
    print("🖱️  Clicking on vessel from autocomplete...")
    
    # Try to find the autocomplete item
    autocomplete_item_selectors = [
        "tr.ui-autocomplete-item",
        "tr[data-item-value*='VESSEL']",
        "tr.ui-state-highlight"
    ]
    
    vessel_clicked = False
    for selector in autocomplete_item_selectors:
        try:
            items = await autocomplete_panel.query_selector_all(selector)
            if items and len(items) > 0:
                # Click the first item
                await items[0].click()
                print(f"✓ Clicked vessel from autocomplete using selector: {selector}")
                track_selector("search_and_select_vessel", selector, "css", "autocomplete_item", "Autocomplete item")
                vessel_clicked = True
                await asyncio.sleep(3)  # Wait for page to load
                break
        except Exception as e:
            continue
    
    if not vessel_clicked:
        print("❌ ERROR: Could not click vessel from autocomplete")
        await save_debug_screenshot(page, f"autocomplete_click_error_{vessel_name}")
        return False
    
    # Wait for vessel page to load
    await wait_for_all_vintrace_loaders(iframe)
    await asyncio.sleep(2)
    
    print(f"✓ Successfully navigated to vessel: {vessel_name}")
    return True


async def download_fruit_report(page: Page, vessel_name: str):
    """
    Download the fruit report for the currently loaded vessel
    
    Args:
        page: Playwright Page object
        vessel_name: Name of the vessel (for filename)
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"DOWNLOADING FRUIT REPORT FOR: {vessel_name}")
    print('=' * 60)
    
    # Get the main iframe
    iframe = await get_main_iframe(page)
    
    # Wait for page to be ready
    await wait_for_all_vintrace_loaders(iframe)
    await asyncio.sleep(2)
    
    # Step 1: Click on the "Fruit" tab
    print("🔍 Looking for 'Fruit' tab...")
    
    fruit_tab_selectors = [
        "li.ui-tabmenuitem:has-text('Fruit')",
        "li.ui-tabmenuitem a:has-text('Fruit')",
        "a.ui-menuitem-link:has-text('Fruit')",
        "li[role='tab'] a:has-text('Fruit')"
    ]
    
    fruit_tab_clicked = False
    for selector in fruit_tab_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=SEARCH_TIMEOUT, state="visible")
            fruit_tab = await iframe.query_selector(selector)
            
            if fruit_tab:
                await fruit_tab.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await fruit_tab.click()
                print(f"✓ Clicked 'Fruit' tab using selector: {selector}")
                track_selector("download_fruit_report", selector, "css", "fruit_tab", "Fruit tab")
                fruit_tab_clicked = True
                await asyncio.sleep(2)  # Wait for tab content to load
                break
        except Exception as e:
            continue
    
    if not fruit_tab_clicked:
        print("❌ ERROR: Could not find or click 'Fruit' tab")
        await save_debug_screenshot(page, f"fruit_tab_error_{vessel_name}")
        return False
    
    # Wait for fruit tab content to load
    await wait_for_all_vintrace_loaders(iframe)
    await asyncio.sleep(2)
    
    # Step 2: Click the export button
    print("📥 Clicking export button...")
    
    export_button_selectors = [
        "button#productsForm\\:fruitDT\\:exportButton",
        "button[id='productsForm:fruitDT:exportButton']",
        "button.vin-download-btn",
        "button:has-text('') >> nth=0"  # Button with download icon
    ]
    
    export_clicked = False
    for selector in export_button_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=SEARCH_TIMEOUT, state="visible")
            export_btn = await iframe.query_selector(selector)
            
            if export_btn:
                await export_btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await export_btn.click()
                print(f"✓ Clicked export button using selector: {selector}")
                track_selector("download_fruit_report", selector, "css", "export_button", "Fruit export button")
                export_clicked = True
                await asyncio.sleep(1.5)  # Wait for menu to appear
                break
        except Exception as e:
            continue
    
    if not export_clicked:
        print("❌ ERROR: Could not click export button")
        await save_debug_screenshot(page, f"export_button_error_{vessel_name}")
        return False
    
    # Step 3: Click "Excel" in the menu to trigger slide animation
    print("📊 Clicking 'Excel' menu item to trigger slide menu...")
    
    excel_menu_selectors = [
        "li.vin-exportMenuOption:has-text('Excel') > a",
        "li.ui-menu-parent:has-text('Excel') > a",
        "a.ui-menuitem-link:has-text('Excel')",
        "span.ui-menuitem-text:has-text('Excel')"
    ]
    
    excel_clicked = False
    for selector in excel_menu_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=SEARCH_TIMEOUT, state="visible")
            excel_item = await iframe.query_selector(selector)
            
            if excel_item:
                await excel_item.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                
                # Click to trigger the slide menu animation (not hover)
                await excel_item.click()
                print(f"✓ Clicked 'Excel' menu item using selector: {selector}")
                track_selector("download_fruit_report", selector, "css", "excel_menu", "Excel menu item")
                
                # Wait for slide animation to complete and submenu to appear
                # The submenu should have display: block when visible
                await asyncio.sleep(2)  # Wait for animation to complete
                
                # Verify submenu is visible
                submenu_selectors = [
                    "li.vin-exportMenuOption:has-text('Excel') ul.ui-menu-child",
                    "ul.ui-menu-child[style*='display: block']",
                    "ul.ui-slidemenu-content"
                ]
                
                submenu_visible = False
                for submenu_selector in submenu_selectors:
                    try:
                        submenu = await iframe.query_selector(submenu_selector)
                        if submenu and await submenu.is_visible():
                            print(f"✓ Submenu appeared using selector: {submenu_selector}")
                            submenu_visible = True
                            break
                    except Exception:
                        continue
                
                if submenu_visible or True:  # Proceed even if we can't verify submenu
                    excel_clicked = True
                    break
        except Exception as e:
            continue
    
    if not excel_clicked:
        print("❌ ERROR: Could not find or click 'Excel' menu item")
        await save_debug_screenshot(page, f"excel_menu_error_{vessel_name}")
        return False
    
    # Step 4: Click "All" option with retry mechanism
    print("📥 Clicking 'All' option to download...")
    
    # More specific selectors targeting the Excel submenu items
    all_option_selectors = [
        "li.vin-exportMenuOption:has-text('Excel') ul.ui-menu-child li:has-text('All') a",
        "ul.ui-menu-child li:has-text('All') a",
        "li.ui-menuitem:has-text('All') a",
        "a.ui-menuitem-link:has-text('All')",
        "span.ui-menuitem-text:has-text('All')",
        "li[role='menuitem']:has-text('All') a"
    ]
    
    download_started = False
    max_attempts = 2
    
    for attempt in range(1, max_attempts + 1):
        print(f"📥 Attempt {attempt}/{max_attempts} to click 'All' option...")
        
        # Re-click Excel menu if this is a retry attempt
        if attempt > 1:
            print(f"🔄 Re-clicking Excel menu before attempt {attempt}...")
            for selector in excel_menu_selectors:
                try:
                    excel_item = await iframe.query_selector(selector)
                    if excel_item:
                        await excel_item.click()
                        await asyncio.sleep(2)  # Wait for submenu animation to complete
                        print(f"✓ Re-clicked 'Excel' menu item for attempt {attempt}")
                        break
                except Exception as e:
                    continue
        
        for selector in all_option_selectors:
            try:
                await iframe.wait_for_selector(selector, timeout=SEARCH_TIMEOUT, state="visible")
                all_option = await iframe.query_selector(selector)
                
                if all_option:
                    is_visible = await all_option.is_visible()
                    if not is_visible:
                        print(f"  ⚠ Attempt {attempt}: 'All' option found but not visible with selector: {selector}")
                        await asyncio.sleep(1)
                        is_visible = await all_option.is_visible()
                        if not is_visible:
                            print(f"  ✗ Attempt {attempt}: 'All' option still not visible after wait")
                            continue
                    
                    await all_option.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    
                    # Set up download listener on the PAGE (not iframe) before clicking
                    try:
                        async with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
                            await all_option.click(force=True)
                            print(f"✓ Attempt {attempt}: Clicked 'All' option using selector: {selector}")
                            track_selector("download_fruit_report", selector, "css", "all_option", "All option for fruit export")
                        
                        # Wait for download to complete
                        download = await download_info.value
                        temp_path = await download.path()
                        
                        # Save with vessel name
                        sanitized_name = sanitize_filename(vessel_name)
                        final_path = os.path.join(FRUIT_REPORTS_DIR, f"{sanitized_name}.csv")
                        
                        if os.path.exists(final_path):
                            os.remove(final_path)
                        
                        shutil.move(temp_path, final_path)
                        print(f"✓ Downloaded and saved fruit report to: {final_path}")
                        download_started = True
                        return True
                    except Exception as download_error:
                        print(f"  ⚠ Attempt {attempt}: Download timeout or error with selector '{selector}': {download_error}")
                        if attempt < max_attempts:
                            print(f"  🔄 Will retry (attempt {attempt + 1}/{max_attempts})...")
                            break  # Break from selector loop to retry with re-hover
                        else:
                            print(f"  ✗ Final attempt {attempt} failed")
                            continue
                    
            except Exception as e:
                print(f"  ✗ Attempt {attempt}: Failed with selector '{selector}': {e}")
                continue
        
        # If download started successfully, exit the retry loop
        if download_started:
            break
    
    if not download_started:
        print(f"❌ ERROR: Could not click 'All' option or download failed after {max_attempts} attempts")
        await save_debug_screenshot(page, f"download_all_error_{vessel_name}")
        return False
    
    return True


async def main():
    # Load vessel list
    vessels = load_vessel_list()
    if not vessels:
        print("❌ No vessels to process")
        sys.exit(1)
    
    print(f"\n{'=' * 60}")
    print(f"PROCESSING {len(vessels)} VESSELS")
    print('=' * 60)
    for i, vessel in enumerate(vessels, 1):
        print(f"  {i}. {vessel}")
    print('=' * 60)
    
    # Load credentials
    USERNAME, PASSWORD = load_vintrace_credentials()
    if not USERNAME or not PASSWORD:
        sys.exit(1)
    
    async with async_playwright() as p:
        # Initialize browser
        browser, context, page = await initialize_browser(p, headless=False)
        
        # Login (navigate_to_old_url=False for new UI)
        success = await vintrace_login(page, USERNAME, PASSWORD, navigate_to_old_url=False)
        
        if not success:
            print("\n" + "=" * 60)
            print("❌ LOGIN FAILED - EXITING")
            print("=" * 60)
            await browser.close()
            return
        
        # Process each vessel
        successful_downloads = 0
        failed_vessels = []
        
        for i, vessel in enumerate(vessels, 1):
            print(f"\n\n{'#' * 60}")
            print(f"PROCESSING VESSEL {i}/{len(vessels)}: {vessel}")
            print('#' * 60)
            
            # Search and select vessel
            search_success = await search_and_select_vessel(page, vessel)
            
            if not search_success:
                print(f"❌ Failed to search/select vessel: {vessel}")
                failed_vessels.append(vessel)
                continue
            
            # Download fruit report
            download_success = await download_fruit_report(page, vessel)
            
            if download_success:
                successful_downloads += 1
                print(f"✓ Successfully downloaded fruit report for: {vessel}")
            else:
                print(f"❌ Failed to download fruit report for: {vessel}")
                failed_vessels.append(vessel)
            
            # Small delay between vessels
            await asyncio.sleep(2)
        
        # Summary
        print("\n\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total vessels: {len(vessels)}")
        print(f"Successful downloads: {successful_downloads}")
        print(f"Failed: {len(failed_vessels)}")
        
        if failed_vessels:
            print("\nFailed vessels:")
            for vessel in failed_vessels:
                print(f"  ❌ {vessel}")
        
        print("=" * 60)
        
        # Keep browser open briefly for inspection
        await asyncio.sleep(5)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
