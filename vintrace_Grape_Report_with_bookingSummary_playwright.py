"""
Vintrace Grape Delivery Report Automation with Booking Summary
Downloads two variants of the Grape Delivery Report with different settings

Usage: python tools/vintrace_Grape_Report_with_bookingSummary_playwright.py

Author: GlipGlops-glitch
Created: 2025-01-10
Last Updated: 2025-01-10
"""

import os
import shutil
import asyncio
import re
from playwright.async_api import async_playwright, Page

# Import helper functions
from vintrace_helpers import (
    load_vintrace_credentials,
    vintrace_login,
    wait_for_all_vintrace_loaders,
    initialize_browser,
    navigate_to_reports_old_ui,
    click_vintage_harvest_tab_old_ui,
    cleanup_and_generate_report,
    save_debug_screenshot,
    DOWNLOAD_TIMEOUT_MS,
    LARGE_TIMEOUT
)

# Import selector tracking
from selector_tracker import track_selector

# ============================================================================
# CONSTANTS
# ============================================================================

CSV_SAVE_DIR = r"Main/data/vintrace_reports/"
REPORT_FILENAME_1 = "grape_detailz.csv"
REPORT_FILENAME_2 = "grape_delivery_report.csv"
TARGET_FILE_PATH_1 = os.path.join(CSV_SAVE_DIR, REPORT_FILENAME_1)
TARGET_FILE_PATH_2 = os.path.join(CSV_SAVE_DIR, REPORT_FILENAME_2)

# Ensure save directory exists
os.makedirs(CSV_SAVE_DIR, exist_ok=True)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_filename(s):
    """Sanitize filename by replacing invalid characters."""
    return re.sub(r'[\\/*?:"<>|]', '_', str(s))


# ============================================================================
# GRAPE DELIVERY REPORT SPECIFIC FUNCTIONS
# ============================================================================

async def find_grape_delivery_section(page: Page):
    """
    Find the Grape Delivery Report section on the page.
    
    Args:
        page: Playwright Page object
        
    Returns:
        ElementHandle or None: The reportStrip section if found
    """
    print("\n🔍 Looking for 'Grape Delivery Report' section...")
    
    # Strategy 1: Find by exact text in span
    try:
        label = await page.query_selector("xpath=//span[normalize-space(text())='Grape Delivery Report']")
        if label:
            # Find the ancestor reportStrip
            section = await label.evaluate_handle("""
                el => {
                    let node = el.parentElement;
                    while(node && !node.classList.contains('reportStrip')) {
                        node = node.parentElement;
                    }
                    return node;
                }
            """)
            
            if await section.evaluate("node => !!node"):
                print("✓ Found 'Grape Delivery Report' section")
                track_selector(
                    "find_grape_delivery_section",
                    "xpath=//span[normalize-space(text())='Grape Delivery Report']",
                    "xpath",
                    "grape_delivery_section",
                    "Grape Delivery Report section heading"
                )
                return section
    except Exception as e:
        print(f"  ✗ Failed to find section: {e}")
    
    # Strategy 2: Try alternative text selectors
    text_selectors = [
        "span:has-text('Grape Delivery Report')",
        "text='Grape Delivery Report'",
        ":text('Grape Delivery Report')",
    ]
    
    for selector in text_selectors:
        try:
            label = await page.wait_for_selector(selector, timeout=3000)
            if label:
                section = await label.evaluate_handle("""
                    el => {
                        let node = el.parentElement;
                        while(node && !node.classList.contains('reportStrip')) {
                            node = node.parentElement;
                        }
                        return node;
                    }
                """)
                
                if await section.evaluate("node => !!node"):
                    print(f"✓ Found 'Grape Delivery Report' section using: {selector}")
                    track_selector(
                        "find_grape_delivery_section",
                        selector,
                        "css",
                        "grape_delivery_section",
                        "Grape Delivery Report section heading (alternative)"
                    )
                    return section
        except Exception:
            continue
    
    print("❌ Could not find 'Grape Delivery Report' section")
    await save_debug_screenshot(page, "grape_delivery_section_not_found")
    return None


async def select_csv_in_dropdown_within(section):
    """
    Select CSV format from dropdown within the report section.
    
    Args:
        section: The reportStrip element handle
        
    Returns:
        bool: True if CSV was selected, False otherwise
    """
    print("📄 Selecting CSV format...")
    
    try:
        selects = await section.query_selector_all("select")
        
        for sel in selects:
            options = await sel.query_selector_all("option")
            
            for opt in options:
                txt = (await opt.inner_text()).strip().upper()
                
                if txt == "CSV":
                    value = await opt.get_attribute("value")
                    if value:
                        await sel.select_option(value=value)
                    else:
                        await sel.select_option(label="CSV")
                    
                    print("✓ Selected 'CSV' format in dropdown")
                    track_selector(
                        "select_csv_in_dropdown_within",
                        "select option[text='CSV']",
                        "css",
                        "csv_format_option",
                        "CSV format option in Grape Delivery Report dropdown"
                    )
                    return True
        
        print("⚠ Could not find CSV option in dropdown")
        return False
        
    except Exception as e:
        print(f"❌ Error selecting CSV format: {e}")
        return False


async def set_checkbox_by_text_within(section, label_text: str, checked: bool):
    """
    Set a checkbox within the report section by its label text.
    
    Args:
        section: The reportStrip element handle
        label_text: Text label of the checkbox
        checked: True to check, False to uncheck
        
    Returns:
        bool: True if checkbox was set, False otherwise
    """
    print(f"☑️  Setting checkbox '{label_text}' to: {checked}")
    
    # Complex xpath for finding checkbox by label
    xpath = f".//div[contains(@class, 'checkbox-text')]//td[normalize-space(text())='{label_text}']/preceding-sibling::td[contains(@id, '_1')]/img | .//div[contains(@class, 'checkbox-text')]//*[text()[normalize-space()='{label_text}']]/ancestor::div[contains(@class, 'checkbox-text')]//img[contains(@id, '_stateicon')]"
    
    try:
        img = await section.query_selector(f"xpath={xpath}")
        
        if img:
            src = await img.get_attribute("src")
            is_checked = "CheckboxOn" in src if src else False
            
            # If current state doesn't match desired state, click it
            if checked and not is_checked:
                await img.scroll_into_view_if_needed()
                await img.click()
                print(f"✓ Checked '{label_text}'")
                track_selector(
                    "set_checkbox_by_text_within",
                    xpath,
                    "xpath",
                    f"checkbox_{label_text.replace(' ', '_')}",
                    f"Checkbox for: {label_text}"
                )
                return True
            elif not checked and is_checked:
                await img.scroll_into_view_if_needed()
                await img.click()
                print(f"✓ Unchecked '{label_text}'")
                track_selector(
                    "set_checkbox_by_text_within",
                    xpath,
                    "xpath",
                    f"checkbox_{label_text.replace(' ', '_')}",
                    f"Checkbox for: {label_text}"
                )
                return True
            else:
                print(f"✓ Checkbox '{label_text}' already {'checked' if checked else 'unchecked'}")
                return True
                
    except Exception as e:
        print(f"❌ Error setting checkbox '{label_text}': {e}")
    
    print(f"⚠ Could not find checkbox for '{label_text}'")
    return False


async def select_option_by_text_within(section, option_text: str):
    """
    Select a dropdown option by its text within the report section.
    
    Args:
        section: The reportStrip element handle
        option_text: Text of the option to select
        
    Returns:
        bool: True if option was selected, False otherwise
    """
    print(f"🔽 Selecting option: '{option_text}'")
    
    try:
        selects = await section.query_selector_all("select")
        
        for sel in selects:
            options = await sel.query_selector_all("option")
            
            for opt in options:
                txt = (await opt.inner_text()).strip()
                
                if txt == option_text:
                    value = await opt.get_attribute("value")
                    if value:
                        await sel.select_option(value=value)
                    else:
                        await sel.select_option(label=option_text)
                    
                    print(f"✓ Selected '{option_text}' from dropdown")
                    track_selector(
                        "select_option_by_text_within",
                        f"select option[text='{option_text}']",
                        "css",
                        f"option_{option_text.replace(' ', '_')}",
                        f"Dropdown option: {option_text}"
                    )
                    return True
        
        print(f"⚠ Could not find option '{option_text}' in dropdown")
        return False
        
    except Exception as e:
        print(f"❌ Error selecting option '{option_text}': {e}")
        return False


async def click_generate_button_within(section):
    """
    Click the Generate button within the report section.
    
    Args:
        section: The reportStrip element handle
        
    Returns:
        bool: True if button was clicked, False otherwise
    """
    print("🔘 Clicking 'Generate...' button...")
    
    # Strategy 1: CSS selector
    css_selector = "button:has-text('Generate...'), input[type='button'][value*='Generate']"
    try:
        btn = await section.query_selector(css_selector)
        if btn:
            await btn.scroll_into_view_if_needed()
            await asyncio.sleep(0.3)
            await btn.click()
            print("✓ Clicked 'Generate...' button")
            track_selector(
                "click_generate_button_within",
                css_selector,
                "css",
                "generate_button",
                "Generate button in Grape Delivery Report"
            )
            return True
    except Exception as e:
        print(f"  ✗ CSS selector failed: {e}")
    
    # Strategy 2: XPath
    xpath_selector = ".//button[normalize-space(text())='Generate...']"
    try:
        btn = await section.query_selector(f"xpath={xpath_selector}")
        if btn:
            await btn.scroll_into_view_if_needed()
            await asyncio.sleep(0.3)
            await btn.click()
            print("✓ Clicked 'Generate...' button (xpath)")
            track_selector(
                "click_generate_button_within",
                xpath_selector,
                "xpath",
                "generate_button",
                "Generate button in Grape Delivery Report (xpath)"
            )
            return True
    except Exception as e:
        print(f"  ✗ XPath selector failed: {e}")
    
    print("❌ Could not find or click 'Generate...' button")
    return False


async def download_report(
    page: Page,
    section,
    filename: str,
    show_delivery_detail: bool,
    summarize_bookings: bool
):
    """
    Configure and download a Grape Delivery Report with specific settings.
    
    Args:
        page: Playwright Page object
        section: The reportStrip element handle
        filename: Target filename for the downloaded report
        show_delivery_detail: Whether to show delivery details
        summarize_bookings: Whether to summarize bookings
        
    Returns:
        str or None: Path to downloaded file, or None if failed
    """
    print("\n" + "=" * 60)
    print(f"DOWNLOADING REPORT: {filename}")
    print(f"  Show delivery detail: {show_delivery_detail}")
    print(f"  Summarize bookings: {summarize_bookings}")
    print("=" * 60)
    
    # Select CSV format
    await select_csv_in_dropdown_within(section)
    await wait_for_all_vintrace_loaders(page)
    await asyncio.sleep(0.5)
    
    # Set checkboxes
    await set_checkbox_by_text_within(section, "Show delivery detail", show_delivery_detail)
    await wait_for_all_vintrace_loaders(page)
    
    await set_checkbox_by_text_within(section, "Summarize bookings", summarize_bookings)
    await wait_for_all_vintrace_loaders(page)
    await asyncio.sleep(0.5)
    
    # Download the report
    try:
        async with page.expect_download(timeout=DOWNLOAD_TIMEOUT_MS) as download_info:
            await click_generate_button_within(section)
        
        download = await download_info.value
        temp_path = await download.path()
        suggested_name = download.suggested_filename
        
        # Verify it's a CSV file
        if suggested_name.lower().endswith('.csv'):
            target_path = os.path.join(CSV_SAVE_DIR, filename)
            
            # Remove existing file if present
            if os.path.exists(target_path):
                os.remove(target_path)
                print(f"  Removed existing file: {target_path}")
            
            # Move downloaded file to target location
            shutil.move(temp_path, target_path)
            
            print(f"✓ Downloaded and saved: {target_path}")
            print("=" * 60)
            return target_path
        else:
            print(f"⚠ Unexpected download filename: {suggested_name}")
            print("=" * 60)
            return None
            
    except Exception as e:
        print(f"❌ Error downloading report ({filename}): {e}")
        await save_debug_screenshot(page, f"download_failed_{filename.replace('.', '_')}")
        print("=" * 60)
        return None


# ============================================================================
# MAIN AUTOMATION WORKFLOW
# ============================================================================

async def run():
    """Main automation workflow for downloading Grape Delivery Reports."""
    
    print("\n" + "=" * 80)
    print("VINTRACE GRAPE DELIVERY REPORT AUTOMATION")
    print("=" * 80)
    
    # Load credentials using helper
    USERNAME, PASSWORD = load_vintrace_credentials()
    if not USERNAME or not PASSWORD:
        print("❌ Missing credentials, aborting")
        return

    async with async_playwright() as p:
        # Initialize browser using helper (increments run counter)
        browser, context, page = await initialize_browser(p, headless=False)
        
        try:
            # Login using helper (navigate_to_old_url=True for this script)
            print("\n" + "=" * 80)
            print("STEP 1: LOGIN")
            print("=" * 80)
            success = await vintrace_login(page, USERNAME, PASSWORD, navigate_to_old_url=True)
            if not success:
                print("❌ Login failed, aborting")
                return
            
            # Navigate to Reports section using helper
            print("\n" + "=" * 80)
            print("STEP 2: NAVIGATE TO REPORTS")
            print("=" * 80)
            if not await navigate_to_reports_old_ui(page):
                print("❌ Could not navigate to Reports, aborting")
                return
            
            # Click Vintage/Harvest tab using helper
            print("\n" + "=" * 80)
            print("STEP 3: NAVIGATE TO VINTAGE/HARVEST")
            print("=" * 80)
            if not await click_vintage_harvest_tab_old_ui(page):
                print("❌ Could not navigate to Vintage/Harvest, aborting")
                return
            
            # Find Grape Delivery Report section
            print("\n" + "=" * 80)
            print("STEP 4: FIND GRAPE DELIVERY REPORT SECTION")
            print("=" * 80)
            section = await find_grape_delivery_section(page)
            if not section:
                print("❌ Could not find Grape Delivery Report section, aborting")
                return
            
            # Download first report variant
            print("\n" + "=" * 80)
            print("STEP 5: DOWNLOAD FIRST REPORT (WITH DETAILS AND SUMMARY)")
            print("=" * 80)
            result1 = await download_report(
                page, 
                section, 
                REPORT_FILENAME_1, 
                show_delivery_detail=True, 
                summarize_bookings=True
            )
            
            await wait_for_all_vintrace_loaders(page)
            await asyncio.sleep(1)
            
            # Download second report variant
            print("\n" + "=" * 80)
            print("STEP 6: DOWNLOAD SECOND REPORT (WITHOUT DETAILS OR SUMMARY)")
            print("=" * 80)
            result2 = await download_report(
                page, 
                section, 
                REPORT_FILENAME_2, 
                show_delivery_detail=False, 
                summarize_bookings=False
            )
            
            await wait_for_all_vintrace_loaders(page)
            
            # Print summary
            print("\n" + "=" * 80)
            print("DOWNLOAD SUMMARY")
            print("=" * 80)
            
            if result1:
                print(f"✓ Report 1: {TARGET_FILE_PATH_1}")
            else:
                print(f"✗ Report 1: FAILED")
            
            if result2:
                print(f"✓ Report 2: {TARGET_FILE_PATH_2}")
            else:
                print(f"✗ Report 2: FAILED")
            
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ FATAL ERROR: {e}")
            await save_debug_screenshot(page, "fatal_error")
            
        finally:
            # Cleanup and generate tracking report
            await cleanup_and_generate_report(browser)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    asyncio.run(run())