#  python tools/vintrace_playwright_Barrel_Report.py
import asyncio
import os
import sys
import shutil
from playwright.async_api import async_playwright, Page

# Import helper functions
from vintrace_helpers import (
    load_vintrace_credentials,
    vintrace_login,
    wait_for_all_vintrace_loaders,
    get_main_iframe,
    initialize_browser,
    LARGE_TIMEOUT
)


DOWNLOAD_TIMEOUT = 300_000  # 5 minutes

CSV_SAVE_DIR = "Main/data/vintrace_reports/barrel_details/"
os.makedirs(CSV_SAVE_DIR, exist_ok=True)

async def download_barrel_details_report(page: Page):
    print("\n" + "=" * 60)
    print("STEP 2: DOWNLOADING BARREL DETAILS REPORT")
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
    export_btn_selectors = [
        "button#vesselsForm\\:vesselsDT\\:exportButton",
        "button[id='vesselsForm:vesselsDT:exportButton']",
        "button.vin-download-btn",
        "button[name='vesselsForm:vesselsDT:exportButton']"
    ]
    
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
                export_clicked = True
                await asyncio.sleep(1.5)
                break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not export_clicked:
        print("❌ ERROR: Could not click export button")
        await page.screenshot(path="export_button_error.png")
        return False
    
    # Step 2: Click "Barrel details" in the menu
    print("\nAttempting to click 'Barrel details' menu item...")
    barrel_details_selectors = [
        "li#vesselsForm\\:vesselsDT\\:printOptions-barrelDetails > a.ui-submenu-link",
        "li[id='vesselsForm:vesselsDT:printOptions-barrelDetails'] > a.ui-submenu-link",
        "li.vin-exportMenuOption:has-text('Barrel details') > a",
        ".ui-menu-parent:has-text('Barrel details') > a.ui-submenu-link"
    ]
    
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
                barrel_clicked = True
                break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not barrel_clicked:
        print("❌ ERROR: Could not click 'Barrel details' menu item")
        await page.screenshot(path="barrel_details_menu_error.png")
        return False
    
    # Step 3: Click "All" to download the report
    print("\nAttempting to click 'All' to download report...")
    all_option_selectors = [
        "a#vesselsForm\\:vesselsDT\\:printOptions-barrelDetails-all",
        "a[id='vesselsForm:vesselsDT:printOptions-barrelDetails-all']",
        "li#vesselsForm\\:vesselsDT\\:printOptions-barrelDetails ul li:has-text('All') a",
        ".ui-menu-child a:has-text('All')"
    ]
    
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
                
                # Wait for download to complete
                download = await download_info.value
                temp_path = await download.path()
                
                # Save with custom filename
                final_path = os.path.join(CSV_SAVE_DIR, "Vintrace_all_barrels.csv")
                if os.path.exists(final_path):
                    os.remove(final_path)
                shutil.move(temp_path, final_path)
                print(f"✓ Report saved to: {final_path}")
                print("=" * 60)
                download_started = True
                return True
                
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not download_started:
        print("❌ ERROR: Could not click 'All' option or download failed")
        await page.screenshot(path="download_all_error.png")
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

        # Login using helper (navigate_to_old_url=False for barrel report)
        success = await vintrace_login(page, USERNAME, PASSWORD, navigate_to_old_url=False)
        
        if not success:
            print("\n" + "=" * 60)
            print("❌ LOGIN FAILED - EXITING")
            print("=" * 60)
            await browser.close()
            return

        # Download barrel details report
        download_success = await download_barrel_details_report(page)
        
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