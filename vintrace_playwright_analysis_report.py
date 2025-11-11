#  python tools/vintrace_playwright_analysis_report.py



import asyncio
import os
import sys
import shutil
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright, Page

# Import helper functions
from vintrace_helpers import (
    load_vintrace_credentials,
    vintrace_login,
    wait_for_all_vintrace_loaders,
    get_main_iframe,
    initialize_browser,
    navigate_to_reports_old_ui,
    find_report_strip_by_title,
    save_debug_screenshot,
    LARGE_TIMEOUT,
    OLD_URL
)

# Use LARGE_TIMEOUT from helpers for consistency
DOWNLOAD_TIMEOUT = LARGE_TIMEOUT
SELECTOR_TIMEOUT = LARGE_TIMEOUT

ANALYSIS_SAVE_DIR = "Main/data/vintrace_reports/analysis/"
os.makedirs(ANALYSIS_SAVE_DIR, exist_ok=True)

async def download_analysis_report(page: Page):
    print("\n" + "=" * 60)
    print("STEP 2: DOWNLOADING ANALYSIS DATA EXPORT REPORT")
    print("=" * 60)
    
    # Verify we're on the old Vintrace URL
    current_url = page.url
    print(f"Current URL: {current_url}")
    if "oldVintrace=true" in current_url:
        print("✓ Confirmed: Using OLD Vintrace UI")
    else:
        print("⚠ WARNING: May not be on old Vintrace UI")
    
    # Get the main iframe where all content is
    iframe = await get_main_iframe(page)
    
    # Wait for page to be ready
    print("⏳ Ensuring page is ready before starting...")
    await wait_for_all_vintrace_loaders(iframe)
    await asyncio.sleep(3)
    
    # Step 1: Navigate to Reports section using helper
    success = await navigate_to_reports_old_ui(iframe)
    if not success:
        print("❌ ERROR: Could not navigate to Reports section")
        await save_debug_screenshot(page, "reports_section_error")
        return False
    
    # Step 2: Click on "Product analysis" category
    print("\n🔍 Navigating to 'Product analysis' category...")
    product_analysis_selectors = [
        "span:text('Product analysis')",
        "div:text('Product analysis')",
        "td:text('Product analysis')",
        "[id$='|Text']:text('Product analysis')",
    ]
    
    clicked_product_analysis = False
    for selector in product_analysis_selectors:
        try:
            await iframe.wait_for_selector(selector, timeout=SELECTOR_TIMEOUT, state="visible")
            element = await iframe.query_selector(selector)
            
            if element:
                # Verify exact text match
                text = await element.inner_text()
                if text.strip() == "Product analysis":
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await element.click()
                    print(f"✓ Clicked 'Product analysis' using selector: {selector}")
                    clicked_product_analysis = True
                    await wait_for_all_vintrace_loaders(iframe)
                    await asyncio.sleep(2)
                    break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    # Fallback: xpath
    if not clicked_product_analysis:
        try:
            element = await iframe.query_selector("xpath=//*[text()='Product analysis']")
            if element:
                await element.scroll_into_view_if_needed()
                await element.click()
                print("✓ Clicked 'Product analysis' using xpath")
                clicked_product_analysis = True
                await wait_for_all_vintrace_loaders(iframe)
                await asyncio.sleep(2)
        except Exception as e:
            print(f"  ✗ XPath also failed: {e}")
    
    if not clicked_product_analysis:
        print("❌ ERROR: Could not navigate to 'Product analysis' category")
        await save_debug_screenshot(page, "product_analysis_error")
        return False
    
    # Step 3: Find the "Analysis data export" report strip
    print("\n🔍 Looking for 'Analysis data export' report...")
    report_strip = await find_report_strip_by_title(iframe, "Analysis data export")
    
    if not report_strip:
        print("❌ ERROR: Could not find 'Analysis data export' report")
        await save_debug_screenshot(page, "analysis_report_not_found")
        return False
    
    print("✓ Found 'Analysis data export' report strip")
    
    # Step 4: Set the "From" date to 8/1/25
    print("\n📅 Setting 'From' date to 08/01/2025...")
    
    # Find all date inputs in the report strip
    date_inputs = await report_strip.query_selector_all("input.input-date, input[type='text'][id*='c_']")
    
    from_date_set = False
    if len(date_inputs) > 0:
        try:
            date_input = date_inputs[0]  # First date input is "From"
            
            # Clear and fill
            await date_input.click()
            await asyncio.sleep(0.3)
            await date_input.fill("")
            await asyncio.sleep(0.3)
            await date_input.fill("08/01/2025")
            await asyncio.sleep(0.5)
            await date_input.press("Tab")
            await asyncio.sleep(0.5)
            
            print(f"✓ Set 'From' date to 08/01/2025")
            from_date_set = True
        except Exception as e:
            print(f"  ✗ Failed to set 'From' date: {e}")
    
    if not from_date_set:
        print("⚠ WARNING: Could not set 'From' date, continuing with default...")
    
    # Step 5: Set the "To" date to today
    today = datetime.now().strftime("%m/%d/%Y")
    print(f"\n📅 Setting 'To' date to {today}...")
    
    to_date_set = False
    if len(date_inputs) > 1:
        try:
            date_input = date_inputs[1]  # Second date input is "To"
            
            await date_input.click()
            await asyncio.sleep(0.3)
            await date_input.fill("")
            await asyncio.sleep(0.3)
            await date_input.fill(today)
            await asyncio.sleep(0.5)
            await date_input.press("Tab")
            await asyncio.sleep(0.5)
            
            print(f"✓ Set 'To' date to {today}")
            to_date_set = True
        except Exception as e:
            print(f"  ✗ Failed to set 'To' date: {e}")
    
    if not to_date_set:
        print("⚠ WARNING: Could not set 'To' date, continuing with default...")
    
    # Step 6: Check "Show active only" checkbox
    print("\n☑️  Checking 'Show active only' checkbox...")
    
    checkbox_selectors = [
        "div.checkbox-text:has-text('Show active only')",
        "table:has-text('Show active only') img[src*='Checkbox']",
        "*:has-text('Show active only')"
    ]
    
    checkbox_checked = False
    for selector in checkbox_selectors:
        try:
            # Find elements with the checkbox text
            elements = await report_strip.query_selector_all(selector)
            
            for element in elements:
                text = await element.inner_text()
                if "Show active only" in text:
                    # Look for checkbox image nearby
                    checkbox_img = await element.query_selector("img[src*='Checkbox'], img[id*='stateicon']")
                    
                    if not checkbox_img:
                        # Try parent/ancestor
                        parent = await element.evaluate_handle("el => el.closest('tr') || el.closest('div') || el.closest('td')")
                        if parent:
                            checkbox_img = await parent.query_selector("img[src*='Checkbox'], img[id*='stateicon']")
                    
                    if checkbox_img:
                        img_src = await checkbox_img.get_attribute("src")
                        
                        if img_src and "CheckboxOff" in img_src:
                            # Click the checkbox (or its parent div)
                            checkbox_parent = await checkbox_img.evaluate_handle("el => el.closest('div.checkbox-text') || el.parentElement")
                            if checkbox_parent:
                                await checkbox_parent.scroll_into_view_if_needed()
                                await asyncio.sleep(0.3)
                                await checkbox_parent.click()
                                await asyncio.sleep(0.5)
                                print(f"✓ Checked 'Show active only'")
                            else:
                                await checkbox_img.click()
                                print(f"✓ Checked 'Show active only' (clicked image)")
                        else:
                            print(f"✓ 'Show active only' already checked")
                        
                        checkbox_checked = True
                        break
            
            if checkbox_checked:
                break
                
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not checkbox_checked:
        print("⚠ WARNING: Could not check 'Show active only', continuing anyway...")
    
    # Wait for form to update
    await asyncio.sleep(1)
    
    # Step 7: Click the "Generate..." button
    print("\n📊 Clicking 'Generate...' button...")
    generate_button_selectors = [
        "button:has-text('Generate')",
        "button:has-text('Generate...')",
        "input[type='button'][value*='Generate']",
        "button.inlineButton.positiveAction",
    ]
    
    clicked_generate = False
    for selector in generate_button_selectors:
        try:
            button = await report_strip.query_selector(selector)
            
            if button:
                await button.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                
                # Set up download listener on the PAGE (not iframe)
                async with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
                    await button.click()
                    print(f"✓ Clicked 'Generate...' button using selector: {selector}")
                
                # Wait for download to complete
                download = await download_info.value
                temp_path = await download.path()
                
                # Save directly to final location (no processing needed)
                final_path = os.path.join(ANALYSIS_SAVE_DIR, "Vintrace_analysis_export.csv")
                
                if os.path.exists(final_path):
                    os.remove(final_path)
                
                shutil.move(temp_path, final_path)
                print(f"✓ Downloaded file")
                print(f"✓ Report saved to: {final_path}")
                print("=" * 60)
                clicked_generate = True
                return True
                
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not clicked_generate:
        print("❌ ERROR: Could not click 'Generate...' button or download failed")
        await save_debug_screenshot(page, "generate_button_error")
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

        # Login using helper - navigate_to_old_url=TRUE to use old Vintrace interface
        print("\n🔄 Logging in and navigating to OLD Vintrace UI...")
        success = await vintrace_login(page, USERNAME, PASSWORD, navigate_to_old_url=True)
        
        if not success:
            print("\n" + "=" * 60)
            print("❌ LOGIN FAILED - EXITING")
            print("=" * 60)
            await browser.close()
            return

        # Download analysis report
        download_success = await download_analysis_report(page)
        
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