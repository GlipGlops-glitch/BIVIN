"""
Vintrace Vessel Details Report Automation
Downloads vessel/barrel details CSV report and removes the first row before saving.

The Vintrace export includes an extra first row (e.g., "Exported on: DATE") before 
the actual headers. This script removes that first row so the headers (row 2 in the 
original) become the actual column headers in the saved CSV file.

Usage: python vintrace_playwright_vessels_report.py

Author: GlipGlops-glitch
Created: 2025-01-11
Last Updated: 2025-01-11
"""
import asyncio
import os
import sys
import shutil
import pandas as pd
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

# Import centralized selectors
from vintrace_selectors import NewUISelectors


DOWNLOAD_TIMEOUT = 300_000  # 5 minutes

CSV_SAVE_DIR = "Main/data/vintrace_reports/vessel_details/"
os.makedirs(CSV_SAVE_DIR, exist_ok=True)

async def download_vessel_details_report(page: Page):
    print("\n" + "=" * 60)
    print("STEP 2: DOWNLOADING VESSEL DETAILS REPORT")
    print("=" * 60)
    
    # Get the main iframe where all content is
    iframe = await get_main_iframe(page)
    
    # Wait for page to be ready
    print("⏳ Ensuring page is ready before starting download process...")
    await wait_for_all_vintrace_loaders(iframe)
    await asyncio.sleep(3)
    
    # Scroll to bottom of page to help reveal all UI elements
    print("📜 Scrolling to bottom of page...")
    try:
        await iframe.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        print("✓ Scrolled to bottom")
    except Exception as e:
        print(f"  ⚠ Could not scroll: {e}")
    
    # Step 1: Click the export button (now in iframe)
    print("\nAttempting to click export button...")
    
    # Use centralized selectors from vintrace_selectors.py
    export_btn_selectors = NewUISelectors.EXPORT_BUTTON.copy()
    
    export_clicked = False
    for selector in export_btn_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=10000, state="attached")
            export_btn = await iframe.query_selector(selector)
            if export_btn:
                await export_btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                
                is_visible = await export_btn.is_visible()
                if not is_visible:
                    print(f"  ⚠ Button found but not visible with selector: {selector}")
                    continue
                
                await export_btn.click()
                print(f"✓ Clicked export button using selector: {selector}")
                track_selector("download_vessel_details_report", selector, "css", "export_button", "Export button in vessels page")
                export_clicked = True
                await asyncio.sleep(1.5)
                break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not export_clicked:
        print("❌ ERROR: Could not click export button")
        await save_debug_screenshot(page, "export_button_error")
        return False
    
    # Step 2: Click "Barrel details" in the menu
    print("\nAttempting to click 'Barrel details' menu item...")
    
    # Use centralized selectors
    barrel_details_selectors = NewUISelectors.BARREL_DETAILS_MENU_ITEM.copy()
    
    barrel_clicked = False
    for selector in barrel_details_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=10000, state="visible")
            barrel_link = await iframe.query_selector(selector)
            
            if barrel_link:
                await barrel_link.scroll_into_view_if_needed()
                await asyncio.sleep(0.3)
                
                await barrel_link.click()
                await asyncio.sleep(1)
                print(f"✓ Clicked 'Barrel details' using selector: {selector}")
                track_selector("download_vessel_details_report", selector, "css", "barrel_details_menu", "Barrel details menu item")
                barrel_clicked = True
                break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not barrel_clicked:
        print("❌ ERROR: Could not click 'Barrel details' menu item")
        await save_debug_screenshot(page, "barrel_details_menu_error")
        return False
    
    # Step 3: Click "All" to download the report
    print("\nAttempting to click 'All' to download report...")
    
    # Use centralized selectors
    all_option_selectors = NewUISelectors.BARREL_DETAILS_ALL_OPTION.copy()
    
    download_started = False
    for selector in all_option_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=10000, state="attached")
            all_option = await iframe.query_selector(selector)
            
            if all_option:
                is_visible = await all_option.is_visible()
                if not is_visible:
                    print(f"  ⚠ 'All' option found but not visible with selector: {selector}")
                    await asyncio.sleep(1)
                    is_visible = await all_option.is_visible()
                    if not is_visible:
                        print(f"  ✗ 'All' option still not visible after wait")
                        continue
                
                await all_option.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                
                # Set up download listener on the PAGE (not iframe) before clicking
                async with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
                    await all_option.click(force=True)
                    print(f"✓ Clicked 'All' option using selector: {selector}")
                    track_selector("download_vessel_details_report", selector, "css", "barrel_all_option", "All option for barrel details")
                
                # Wait for download to complete
                download = await download_info.value
                temp_path = await download.path()
                
                # Load CSV and skip first row (headers start on row 2)
                print("📊 Processing CSV to remove first row...")
                try:
                    # Read the CSV file
                    df = pd.read_csv(temp_path, skiprows=[0])  # Skip the first row (row 0)
                    
                    # Save with custom filename
                    final_path = os.path.join(CSV_SAVE_DIR, "Vintrace_all_vessels.csv")
                    if os.path.exists(final_path):
                        os.remove(final_path)
                    
                    # Save the processed DataFrame
                    df.to_csv(final_path, index=False)
                    print(f"✓ Removed first row and saved report to: {final_path}")
                    print("=" * 60)
                    download_started = True
                    return True
                except Exception as e:
                    print(f"❌ Error processing CSV: {e}")
                    # Fallback: save original file if processing fails
                    final_path = os.path.join(CSV_SAVE_DIR, "Vintrace_all_vessels.csv")
                    if os.path.exists(final_path):
                        os.remove(final_path)
                    shutil.move(temp_path, final_path)
                    print(f"⚠ Saved original file without processing to: {final_path}")
                    return True
                
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not download_started:
        print("❌ ERROR: Could not click 'All' option or download failed")
        await save_debug_screenshot(page, "download_all_error")
        return False
    
    return True

async def main():
    # Load credentials using helper
    USERNAME, PASSWORD = load_vintrace_credentials()
    if not USERNAME or not PASSWORD:
        sys.exit(1)

    async with async_playwright() as p:
        # Initialize browser using helper
        browser, context, page = await initialize_browser(p, headless=False)

        # Login using helper (navigate_to_old_url=False for vessel report)
        success = await vintrace_login(page, USERNAME, PASSWORD, navigate_to_old_url=False)
        
        if not success:
            print("\n" + "=" * 60)
            print("❌ LOGIN FAILED - EXITING")
            print("=" * 60)
            await browser.close()
            return

        # Download vessel details report
        download_success = await download_vessel_details_report(page)
        
        if not download_success:
            print("\n" + "=" * 60)
            print("❌ DOWNLOAD FAILED - EXITING")
            print("=" * 60)
            await browser.close()
            return

        print("\n" + "=" * 60)
        print("✓ ALL STEPS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        # Keep browser open briefly for inspection
        await asyncio.sleep(5)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
