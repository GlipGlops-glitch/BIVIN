#  python tools/vintrace_playwright_work_detailz.py
import asyncio
import os
import sys
import re
import shutil
import datetime
import pandas as pd
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page

CSV_SAVE_DIR = "Main/data/vintrace_reports/work_detailz/"
os.makedirs(CSV_SAVE_DIR, exist_ok=True)

LARGE_TIMEOUT = 120_000  # 2 minutes
DOWNLOAD_TIMEOUT = 300_000  # 5 minutes

DAYS_TO_RERUN = 20  # rerun for the most recent N days (ending with today)

def sanitize_filename(s):
    return re.sub(r'[\\/*?:"<>|]', '_', str(s))

def is_xls_compound_file(filepath):
    with open(filepath, "rb") as f:
        sig = f.read(4)
    return sig == b"\xd0\xcf\x11\xe0"

def convert_xls_to_csv(xls_path, out_csv_path):
    try:
        df = pd.read_excel(xls_path, engine='xlrd')
        df.to_csv(out_csv_path, index=False)
        print(f"[INFO] Converted XLS to CSV: {out_csv_path}")
        return out_csv_path
    except Exception as e:
        print(f"[WARN] Could not convert {xls_path} as XLS: {e}")
        return None

def copy_csv_to_converted(csv_path, out_csv_path):
    try:
        shutil.copy(csv_path, out_csv_path)
        print(f"[INFO] Copied CSV to: {out_csv_path}")
        return out_csv_path
    except Exception as e:
        print(f"[WARN] Could not copy {csv_path} to {out_csv_path}: {e}")
        return None

async def wait_for_all_vintrace_loaders(page: Page, timeout=LARGE_TIMEOUT):
    """Wait for Vintrace loading indicators to disappear"""
    try:
        await page.wait_for_function(
            """
            () => {
                const long = document.getElementById('serverDelayMessageLong');
                const main = document.getElementById('serverDelayMessage');
                const longHidden = !long || getComputedStyle(long).visibility === 'hidden';
                const mainHidden = !main || getComputedStyle(main).visibility === 'hidden';
                return longHidden && mainHidden;
            }
            """, timeout=timeout
        )
        print("✓ All Vintrace loaders hidden")
    except Exception as e:
        print(f"⚠ Timeout waiting for loaders (may be okay): {e}")

async def vintrace_login_and_navigate(page: Page, username: str, password: str, login_url: str, old_url: str):
    print("=" * 60)
    print("STEP 1: LOGGING IN")
    print("=" * 60)
    print(f"Navigating to login page: {login_url}")
    await page.goto(login_url, timeout=LARGE_TIMEOUT)
    
    # Wait for page to be fully loaded
    await page.wait_for_load_state("networkidle", timeout=30000)
    print("✓ Login page loaded")
    
    # Updated login selectors with multiple fallback strategies
    email_selectors = [
        "input[type='email']",
        "input[name='email']",
        "input[placeholder*='email' i]",
        "input[autocomplete='email']",
        "#email"
    ]
    password_selectors = [
        "input[type='password']",
        "input[name='password']",
        "input[placeholder*='password' i]",
        "input[autocomplete*='password']",
        "#password"
    ]
    
    # Fill email field
    print("\nAttempting to fill email field...")
    email_filled = False
    for selector in email_selectors:
        try:
            await page.wait_for_selector(selector, timeout=5000, state="visible")
            await page.fill(selector, username)
            print(f"✓ Filled email using selector: {selector}")
            email_filled = True
            break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not email_filled:
        print("❌ ERROR: Could not find email input field")
        print("Taking screenshot for debugging...")
        await page.screenshot(path="login_error_email.png")
        return False
    
    # Small delay to simulate human behavior
    await asyncio.sleep(0.5)
    
    # Fill password field
    print("\nAttempting to fill password field...")
    password_filled = False
    for selector in password_selectors:
        try:
            await page.wait_for_selector(selector, timeout=5000, state="visible")
            await page.fill(selector, password)
            print(f"✓ Filled password using selector: {selector}")
            password_filled = True
            break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not password_filled:
        print("❌ ERROR: Could not find password input field")
        print("Taking screenshot for debugging...")
        await page.screenshot(path="login_error_password.png")
        return False
    
    # Small delay to simulate human behavior
    await asyncio.sleep(0.5)
    
    # Click login button with multiple strategies
    print("\nAttempting to click login button...")
    login_btn_selectors = [
        "button[type='submit']:has-text('Login')",
        "button[type='submit']:has-text('Sign in')",
        "button:has-text('Login')",
        "button:has-text('Sign in')",
        "input[type='submit'][value*='Login' i]",
        "button[type='submit']"
    ]
    
    login_clicked = False
    for selector in login_btn_selectors:
        try:
            await page.wait_for_selector(selector, timeout=5000, state="visible")
            login_btn = await page.query_selector(selector)
            if login_btn:
                await login_btn.scroll_into_view_if_needed()
                await login_btn.click()
                print(f"✓ Clicked login button using selector: {selector}")
                login_clicked = True
                break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not login_clicked:
        print("❌ ERROR: Login button not found")
        print("Taking screenshot for debugging...")
        await page.screenshot(path="login_error_button.png")
        return False
    
    # Wait for navigation after login - THIS IS CRITICAL
    print("\n⏳ Waiting for login to complete and page to navigate...")
    try:
        # Wait for URL to change from login page
        await page.wait_for_url(lambda url: url != login_url, timeout=LARGE_TIMEOUT)
        print(f"✓ Navigated away from login page")
        print(f"  Current URL: {page.url}")
        
        # Wait for network to be idle
        await page.wait_for_load_state("networkidle", timeout=3000000)
        print("✓ Network idle after login")
        
        # Additional wait for any redirects
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ ERROR: Login may have failed - URL did not change: {e}")
        print(f"  Current URL: {page.url}")
        print("Taking screenshot for debugging...")
        await page.screenshot(path="login_error_navigation.png")
        return False
    
    # Check if we're actually logged in by looking for error messages
    error_indicators = [
        "text='Invalid email or password'",
        "text='Login failed'",
        "text='Incorrect username or password'",
        ".error:visible",
        ".alert-danger:visible"
    ]
    
    for error_sel in error_indicators:
        try:
            error_elem = await page.query_selector(error_sel)
            if error_elem:
                error_text = await error_elem.inner_text()
                print(f"❌ ERROR: Login failed - {error_text}")
                await page.screenshot(path="login_error_credentials.png")
                return False
        except:
            pass
    
    print("\n✓ Login appears successful!")
    print("=" * 60)
    print("STEP 2: NAVIGATING TO OLD VINTRACE")
    print("=" * 60)
    print(f"Navigating to: {old_url}")
    
    try:
        await page.goto(old_url, timeout=LARGE_TIMEOUT)
        print("✓ Navigation initiated")
        
        # Wait for page to load
        await page.wait_for_load_state("networkidle", timeout=30000)
        print("✓ Page loaded")
        
        # Wait for Vintrace-specific loaders
        await wait_for_all_vintrace_loaders(page)
        
        print(f"✓ Arrived at old vintrace URL: {page.url}")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Could not navigate to old Vintrace URL: {e}")
        print("Taking screenshot for debugging...")
        await page.screenshot(path="navigation_error.png")
        return False

async def open_reports_from_consoles_menu(page: Page, LARGE_TIMEOUT=LARGE_TIMEOUT):
    print("\n" + "=" * 60)
    print("STEP 3: OPENING REPORTS MENU")
    print("=" * 60)
    
    # Wait a moment for page to stabilize
    await asyncio.sleep(1)
    
    print("Attempting to click Consoles drop-down to show more options...")
    
    # Updated selector strategies for Consoles dropdown
    consoles_dropdown_selectors = [
        "img[id*='SubMenuIMG']:near(:text('Consoles'))",
        "[id*='SubMenu'][id*='IMG']:near(:text('Consoles'))",
        "img[src*='dropdown']:near(:text('Consoles'))",
        "img[src*='arrow']:near(:text('Consoles'))",
        '#c_46SubMenuIMG'  # Fallback to ID
    ]
    
    clicked_dropdown = False
    for selector in consoles_dropdown_selectors:
        try:
            await page.wait_for_selector(selector, timeout=10000, state="visible")
            await page.click(selector)
            print(f"✓ Clicked the Consoles row drop-down using selector: {selector}")
            clicked_dropdown = True
            await asyncio.sleep(1)  # Wait for menu to expand
            break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not clicked_dropdown:
        print("❌ ERROR: Could not click the Consoles drop-down")
        await page.screenshot(path="consoles_dropdown_error.png")
        return False

    print('\nAttempting to click "Reports..." in Consoles menu...')
    
    # Updated selector strategies for Reports option
    reports_selectors = [
        "td:has-text('Reports...'):visible",
        "td:has-text('Reports'):visible",
        "[role='menuitem']:has-text('Reports')",
        "td:text-is('Reports...')",
        "a:has-text('Reports')",
        "td#c_62_td_0"  # Fallback to ID
    ]
    
    clicked_reports = False
    for selector in reports_selectors:
        try:
            await page.wait_for_selector(selector, timeout=5000, state="visible")
            await page.click(selector)
            print(f'✓ Clicked "Reports..." using selector: {selector}')
            clicked_reports = True
            await asyncio.sleep(1)  # Wait for reports window to open
            break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    if not clicked_reports:
        print('❌ ERROR: Could not click "Reports..."')
        await page.screenshot(path="reports_menu_error.png")
        return False
    
    print("=" * 60)
    return True

async def click_operations_tab(page: Page):
    print("\n" + "=" * 60)
    print("STEP 4: CLICKING OPERATIONS TAB")
    print("=" * 60)
    
    # Wait for any animations/transitions
    await asyncio.sleep(1)
    
    print("Attempting to click the 'Operations' tab/menu...")
    selectors = [
        "span:text('Operations'):visible",
        "div:text('Operations'):visible",
        "td:text('Operations'):visible",
        "tr:has-text('Operations') td:visible",
        "[role='tab']:has-text('Operations')",
        "[id$='|Text']:text('Operations')",
    ]
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=5000, state="visible")
            el = await page.query_selector(sel)
            if el:
                await el.scroll_into_view_if_needed()
                await el.click()
                print(f"✓ Clicked 'Operations' using selector: {sel}")
                await asyncio.sleep(1)  # Wait for tab content to load
                print("=" * 60)
                return True
        except Exception as e:
            print(f"  ✗ Failed with selector '{sel}': {e}")
            continue
    
    # Try xpath as fallback
    try:
        el = await page.query_selector("xpath=//*[text()='Operations']")
        if el:
            await el.scroll_into_view_if_needed()
            await el.click()
            print("✓ Clicked 'Operations' using xpath.")
            await asyncio.sleep(1)
            print("=" * 60)
            return True
    except Exception as e:
        print(f"  ✗ Failed with xpath: {e}")
    
    print("❌ ERROR: Could not find and click 'Operations' tab/menu.")
    await page.screenshot(path="operations_tab_error.png")
    print("=" * 60)
    return False

async def find_work_detail_section(page: Page):
    label = await page.query_selector("xpath=//span[normalize-space(text())='Work Detail Report']")
    if not label:
        print("Could not find 'Work Detail Report' section.")
        return None
    section = await label.evaluate_handle("""
        el => {
            let node = el.parentElement;
            while(node && !node.classList.contains('reportStrip')) {
                node = node.parentElement;
            }
            return node;
        }
    """)
    if not await section.evaluate("node => !!node"):
        print("Could not find ancestor '.reportStrip' for Work Detail Report.")
        return None
    print("Found 'Work Detail Report' section.")
    return section

async def fill_work_detail_dates(section, from_date, to_date):
    """
    Fill date inputs using descriptive selectors instead of hardcoded IDs.
    Looks for input fields based on their class, position, and context.
    """
    print(f"Attempting to fill dates: From={from_date}, To={to_date}")
    
    # Strategy 1: Find all inputs with class 'input-date' within the section
    # This is the most reliable since both inputs share this class
    try:
        date_inputs = await section.query_selector_all("input.input-date")
        if len(date_inputs) >= 2:
            print(f"Found {len(date_inputs)} date inputs with class 'input-date'")
            
            # Clear and fill first input
            await date_inputs[0].click()
            await date_inputs[0].fill("")
            await date_inputs[0].fill(from_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'From' date (first .input-date) with: {from_date}")
            
            # Clear and fill second input
            await date_inputs[1].click()
            await date_inputs[1].fill("")
            await date_inputs[1].fill(to_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'To' date (second .input-date) with: {to_date}")
            return True
    except Exception as e:
        print(f"Strategy 1 failed (input.input-date by position): {e}")
    
    # Strategy 2: Find by class and filter by proximity to label text
    try:
        # Look for the input-date class near "From" text
        from_input = await section.query_selector("input.input-date:near(:text('From'))")
        if from_input:
            await from_input.click()
            await from_input.fill("")
            await from_input.fill(from_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'From' date using :near selector with: {from_date}")
        
        # Look for the input-date class near "To" text
        to_input = await section.query_selector("input.input-date:near(:text('To'))")
        if to_input:
            await to_input.click()
            await to_input.fill("")
            await to_input.fill(to_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'To' date using :near selector with: {to_date}")
        
        if from_input and to_input:
            return True
    except Exception as e:
        print(f"Strategy 2 failed (input.input-date with :near): {e}")
    
    # Strategy 3: Use more generic date input selectors by position
    try:
        date_inputs = await section.query_selector_all(
            "input[type='text'][class*='date'], input[type='date'], input.input-date"
        )
        if len(date_inputs) >= 2:
            print(f"Found {len(date_inputs)} date-like inputs (generic strategy)")
            await date_inputs[0].click()
            await date_inputs[0].fill("")
            await date_inputs[0].fill(from_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'From' date (first date input) with: {from_date}")
            
            await date_inputs[1].click()
            await date_inputs[1].fill("")
            await date_inputs[1].fill(to_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'To' date (second date input) with: {to_date}")
            return True
    except Exception as e:
        print(f"Strategy 3 failed (generic date inputs): {e}")
    
    # Strategy 4: Find by tabindex order (assuming sequential tabindex)
    try:
        all_inputs = await section.query_selector_all("input.input-date[tabindex]")
        if len(all_inputs) >= 2:
            # Sort by tabindex to ensure correct order
            sorted_inputs = []
            for inp in all_inputs:
                tabindex = await inp.get_attribute("tabindex")
                sorted_inputs.append((int(tabindex) if tabindex else 999, inp))
            sorted_inputs.sort(key=lambda x: x[0])
            
            await sorted_inputs[0][1].click()
            await sorted_inputs[0][1].fill("")
            await sorted_inputs[0][1].fill(from_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'From' date (by tabindex) with: {from_date}")
            
            await sorted_inputs[1][1].click()
            await sorted_inputs[1][1].fill("")
            await sorted_inputs[1][1].fill(to_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'To' date (by tabindex) with: {to_date}")
            return True
    except Exception as e:
        print(f"Strategy 4 failed (by tabindex): {e}")
    
    # Strategy 5: Fallback to hardcoded IDs (last resort)
    print("⚠ Falling back to hardcoded IDs...")
    from_filled = False
    to_filled = False
    
    try:
        # Try new IDs first, then old IDs
        from_input = await section.query_selector("input#c_551, input#c_654")
        if from_input:
            await from_input.click()
            await from_input.fill("")
            await from_input.fill(from_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'From' date (by ID fallback) with: {from_date}")
            from_filled = True
    except Exception as e:
        print(f"Could not find 'From' date input: {e}")
    
    try:
        # Try new IDs first, then old IDs
        to_input = await section.query_selector("input#c_558, input#c_661")
        if to_input:
            await to_input.click()
            await to_input.fill("")
            await to_input.fill(to_date)
            await asyncio.sleep(0.3)
            print(f"✓ Filled 'To' date (by ID fallback) with: {to_date}")
            to_filled = True
    except Exception as e:
        print(f"Could not find 'To' date input: {e}")
    
    return from_filled and to_filled

async def click_generate_button_in_section(section):
    """
    Click the Generate button using descriptive selectors instead of hardcoded ID.
    """
    generate_btn_selectors = [
        "button:has-text('Generate'):visible",
        "button:text-is('Generate...')",
        "input[type='submit'][value*='Generate' i]",
        "button[type='submit']:has-text('Generate')",
        "button#c_632"  # Fallback to ID
    ]
    
    for selector in generate_btn_selectors:
        try:
            generate_btn = await section.query_selector(selector)
            if generate_btn:
                await generate_btn.scroll_into_view_if_needed()
                await generate_btn.click()
                print(f"Clicked 'Generate...' button using selector: {selector}")
                return True
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue
    
    print("Could not find 'Generate...' button in Work Detail Report section.")
    return False

async def download_report_for_day(
        page, section, from_date, to_date, save_dir, existing_converted):
    base_name = f"work_detailz_{sanitize_filename(from_date)}_to_{sanitize_filename(to_date)}"
    converted_name = f"{base_name}_converted.csv"
    orig_path = os.path.join(save_dir, f"{base_name}.csv")
    out_csv = os.path.join(save_dir, converted_name)
    
    await fill_work_detail_dates(section, from_date, to_date)
    await wait_for_all_vintrace_loaders(page)
    
    try:
        async with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
            await click_generate_button_in_section(section)
        download = await download_info.value
        temp_path = await download.path()
        if os.path.exists(orig_path):
            os.remove(orig_path)
        shutil.move(temp_path, orig_path)
        print(f"Saved raw report: {orig_path}")
        await wait_for_all_vintrace_loaders(page)
        
        # Convert or copy, then delete original
        if is_xls_compound_file(orig_path):
            csv_path = convert_xls_to_csv(orig_path, out_csv)
        else:
            csv_path = copy_csv_to_converted(orig_path, out_csv)
        if csv_path:
            print(f"[INFO] Only keeping converted file: {out_csv}")
            os.remove(orig_path)
            existing_converted.add(converted_name)
        else:
            print(f"[WARN] Could not produce converted CSV for {orig_path}")
    except Exception as e:
        print(f"Error downloading report for {from_date} to {to_date}: {e}")

def date_range(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += datetime.timedelta(days=1)

async def main():
    load_dotenv()
    USERNAME = os.getenv("VINTRACE_USER")
    PASSWORD = os.getenv("VINTRACE_PW")
    LOGIN_URL = "https://auth.vintrace.app/sign-in?customerCode=smwe"
    OLD_URL = "https://us61.vintrace.net/smwe/app?oldVintrace=true"

    if not USERNAME or not PASSWORD:
        print("VINTRACE_USER or VINTRACE_PW environment variables not set.")
        sys.exit(1)

    # Load all _converted.csv file names in advance
    existing_converted = set(f for f in os.listdir(CSV_SAVE_DIR) if f.endswith("_converted.csv"))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        # Step 1: Login and navigate to old vintrace
        success = await vintrace_login_and_navigate(page, USERNAME, PASSWORD, LOGIN_URL, OLD_URL)
        if not success:
            print("\n" + "=" * 60)
            print("❌ LOGIN FAILED - EXITING")
            print("=" * 60)
            await browser.close()
            return

        # Step 2: Open Reports from Consoles menu
        opened = await open_reports_from_consoles_menu(page)
        if not opened:
            print("Could not open Reports via Consoles menu. Exiting.")
            await browser.close()
            return
        await wait_for_all_vintrace_loaders(page)

        # Step 3: Click the Operations tab/menu
        ops_clicked = await click_operations_tab(page)
        if not ops_clicked:
            print("Could not click Operations tab. Exiting.")
            await browser.close()
            return
        await wait_for_all_vintrace_loaders(page)

        # Step 4: Download daily reports for all specified date ranges
        print("\n" + "=" * 60)
        print("STEP 5: DOWNLOADING REPORTS")
        print("=" * 60)
        
        date_ranges = [
            ("08/01/2023", "11/15/2023"),
            ("08/01/2024", "11/15/2024"),
            ("08/26/2025", datetime.datetime.now().strftime("%m/%d/%Y")),
        ]
        # Compute the set of most recent DAYS_TO_RERUN dates (as strings, including today)
        today = datetime.datetime.now()
        rerun_days = set(
            (today - datetime.timedelta(days=i)).strftime("%m/%d/%Y")
            for i in range(DAYS_TO_RERUN)
        )

        for start_str, end_str in date_ranges:
            start = datetime.datetime.strptime(start_str, "%m/%d/%Y")
            end = datetime.datetime.strptime(end_str, "%m/%d/%Y")
            for day in date_range(start, end):
                day_str = day.strftime("%m/%d/%Y")
                base_name = f"work_detailz_{sanitize_filename(day_str)}_to_{sanitize_filename(day_str)}"
                converted_name = f"{base_name}_converted.csv"
                # If the day is in the most recent rerun_days, force rerun
                if converted_name in existing_converted and day_str not in rerun_days:
                    print(f"[SKIP] Already present: {converted_name}")
                    continue
                elif converted_name in existing_converted and day_str in rerun_days:
                    print(f"[FORCE RERUN] Re-running for recent file: {converted_name}")
                
                section = await find_work_detail_section(page)
                if not section:
                    print(f"Could not find Work Detail Report section for {day_str}; skipping.")
                    continue
                    
                await download_report_for_day(
                    page, section, day_str, day_str, CSV_SAVE_DIR, existing_converted)
                await asyncio.sleep(2)

        print("\n" + "=" * 60)
        print("✓ All reports downloaded and converted as needed.")
        print("=" * 60)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())