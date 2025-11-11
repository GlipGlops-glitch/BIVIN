"""
Vintrace Playwright Helper Functions
Reusable functions for Vintrace automation scripts with built-in selector tracking

Author: GlipGlops-glitch
Created: 2025-01-10
Last Updated: 2025-01-11

This module provides helper functions for automating Vintrace winery software
using Playwright. It includes login, navigation, report interaction, and utility functions.

Features built-in selector tracking to optimize automation scripts over time.
The module learns which selectors work best and automatically prioritizes them.
"""

import asyncio
import os
import datetime
import shutil
import json
import threading
from typing import Optional, Dict
from playwright.async_api import Page
from dotenv import load_dotenv

# Import centralized selectors
try:
    from vintrace_selectors import NewUISelectors, OldUISelectors, LoginSelectors, PopupSelectors, ReportSelectors
except ImportError:
    # Fallback if selectors module not available
    NewUISelectors = OldUISelectors = LoginSelectors = PopupSelectors = ReportSelectors = None

# ============================================================================
# CONSTANTS
# ============================================================================

# Timeout values (in milliseconds)
LARGE_TIMEOUT = 120000  # 2 minutes
DOWNLOAD_TIMEOUT_MS = 1200000  # 20 minutes for large reports
STANDARD_TIMEOUT = 30000  # 30 seconds - standard wait time
MEDIUM_TIMEOUT = 10000  # 10 seconds - medium wait time
SHORT_TIMEOUT = 5000  # 5 seconds - short wait time
QUICK_TIMEOUT = 3000  # 3 seconds - quick operations
LOADER_APPEAR_TIMEOUT = 15000  # 15 seconds - wait for loader to appear

# URLs
LOGIN_URL = "https://auth.vintrace.app/sign-in?customerCode=smwe"
OLD_URL = "https://us61.vintrace.net/smwe/2.app?oldVintrace=true"


# ============================================================================
# SELECTOR TRACKING SYSTEM
# ============================================================================

class SelectorTracker:
    """
    Tracks successful selector usage across Playwright automation runs.
    Thread-safe singleton implementation that learns which selectors work best.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.tracking_file = "selector_tracking.json"
            self.data = self._load_tracking_data()
            self.initialized = True

    def _load_tracking_data(self) -> Dict:
        """Load existing tracking data from JSON file."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ Could not load tracking data: {e}")
                return self._init_tracking_structure()
        return self._init_tracking_structure()

    def _init_tracking_structure(self) -> Dict:
        """Initialize the tracking data structure."""
        return {
            "metadata": {
                "created": datetime.datetime.now().isoformat(),
                "last_updated": datetime.datetime.now().isoformat(),
                "total_runs": 0,
                "version": "2.0.0"
            },
            "selectors": {}
        }

    def _save_tracking_data(self):
        """Save tracking data to JSON file."""
        try:
            self.data["metadata"]["last_updated"] = datetime.datetime.now().isoformat()
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠ Could not save tracking data: {e}")

    def track_success(
        self,
        function_name: str,
        selector: str,
        selector_type: str = "css",
        context: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Track a successful selector usage.

        Args:
            function_name: Name of the function where selector was used
            selector: The actual selector string that worked
            selector_type: Type of selector (css, xpath, text, etc.)
            context: Additional context (e.g., "new_ui", "old_ui", "iframe")
            notes: Any additional notes about this selector
        """
        # Create unique key for this selector
        key = f"{function_name}::{selector}"

        if key not in self.data["selectors"]:
            self.data["selectors"][key] = {
                "function": function_name,
                "selector": selector,
                "type": selector_type,
                "context": context,
                "notes": notes,
                "first_seen": datetime.datetime.now().isoformat(),
                "last_seen": datetime.datetime.now().isoformat(),
                "success_count": 0,
                "attempts": []
            }

        # Update existing entry
        entry = self.data["selectors"][key]
        entry["last_seen"] = datetime.datetime.now().isoformat()
        entry["success_count"] += 1
        entry["attempts"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "success": True
        })

        # Keep only last 10 attempts to avoid file bloat
        if len(entry["attempts"]) > 10:
            entry["attempts"] = entry["attempts"][-10:]

        self._save_tracking_data()

    def get_sorted_selectors(self, function_name: str, selectors: list) -> list:
        """
        Sort a list of selectors by their success rate, putting most successful first.

        Args:
            function_name: Name of the function requesting sorted selectors
            selectors: List of selector strings to sort

        Returns:
            list: Selectors sorted by success count (descending)
        """
        selector_scores = []

        for selector in selectors:
            key = f"{function_name}::{selector}"
            score = 0

            if key in self.data["selectors"]:
                score = self.data["selectors"][key]["success_count"]

            selector_scores.append((selector, score))

        # Sort by score (descending), then by original order
        sorted_selectors = sorted(selector_scores, key=lambda x: (-x[1], selectors.index(x[0])))

        return [sel for sel, _ in sorted_selectors]

    def generate_report(self) -> str:
        """
        Generate a human-readable report of selector usage.

        Returns:
            str: Formatted report text
        """
        report = []
        report.append("=" * 80)
        report.append("SELECTOR TRACKING REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.datetime.now().isoformat()}")
        report.append(f"Total Tracked Selectors: {len(self.data['selectors'])}")
        report.append(f"Total Automation Runs: {self.data['metadata']['total_runs']}")
        report.append("")

        # Group by function
        by_function = {}
        for key, entry in self.data["selectors"].items():
            func = entry["function"]
            if func not in by_function:
                by_function[func] = []
            by_function[func].append(entry)

        # Sort functions alphabetically
        for func in sorted(by_function.keys()):
            report.append(f"\n{'=' * 80}")
            report.append(f"Function: {func}")
            report.append('=' * 80)

            # Sort by success count (descending)
            entries = sorted(by_function[func], key=lambda x: x["success_count"], reverse=True)

            for entry in entries:
                report.append(f"\n  ✓ Selector: {entry['selector']}")
                report.append(f"    Type: {entry['type']}")
                report.append(f"    Success Count: {entry['success_count']}")
                report.append(f"    First Seen: {entry['first_seen']}")
                report.append(f"    Last Seen: {entry['last_seen']}")
                if entry.get('context'):
                    report.append(f"    Context: {entry['context']}")
                if entry.get('notes'):
                    report.append(f"    Notes: {entry['notes']}")

        report.append("\n" + "=" * 80)
        return "\n".join(report)

    def get_best_selectors(self, function_name: Optional[str] = None) -> Dict:
        """
        Get the most successful selectors, optionally filtered by function.

        Args:
            function_name: Optional function name to filter by

        Returns:
            Dict: Selectors sorted by success count
        """
        selectors = self.data["selectors"]

        if function_name:
            selectors = {k: v for k, v in selectors.items() if v["function"] == function_name}

        # Sort by success count
        sorted_selectors = sorted(
            selectors.items(),
            key=lambda x: x[1]["success_count"],
            reverse=True
        )

        return dict(sorted_selectors)

    def increment_run_count(self):
        """Increment the total run counter."""
        self.data["metadata"]["total_runs"] += 1
        self._save_tracking_data()

    def print_summary(self):
        """Print a quick summary of tracking data."""
        print("\n" + "=" * 80)
        print("SELECTOR TRACKING SUMMARY")
        print("=" * 80)
        print(f"Total Selectors Tracked: {len(self.data['selectors'])}")
        print(f"Total Runs: {self.data['metadata']['total_runs']}")
        print(f"Last Updated: {self.data['metadata']['last_updated']}")

        # Show top 5 selectors
        best = self.get_best_selectors()
        if best:
            print("\nTop 5 Most Successful Selectors:")
            for i, (key, data) in enumerate(list(best.items())[:5], 1):
                print(f"  {i}. {data['function']} - {data['selector'][:50]}... ({data['success_count']} uses)")

        print("=" * 80 + "\n")


# Global singleton instance
_tracker = SelectorTracker()


def track_selector(
    function_name: str,
    selector: str,
    selector_type: str = "css",
    context: Optional[str] = None,
    notes: Optional[str] = None
):
    """
    Convenience function to track a successful selector.

    Usage:
        track_selector("vintrace_login", "input#email", "css", "new_ui", "Primary email field")
    """
    _tracker.track_success(function_name, selector, selector_type, context, notes)


def get_sorted_selectors(function_name: str, selectors: list) -> list:
    """
    Get selectors sorted by success rate (most successful first).

    Args:
        function_name: Name of the calling function
        selectors: List of selector strings

    Returns:
        list: Selectors sorted by historical success
    """
    return _tracker.get_sorted_selectors(function_name, selectors)


# ============================================================================
# CREDENTIAL MANAGEMENT
# ============================================================================

def load_vintrace_credentials():
    """
    Load Vintrace credentials from environment variables.

    Returns:
        tuple: (username, password) or (None, None) if not found
    """
    load_dotenv()
    username = os.getenv("VINTRACE_USER")
    password = os.getenv("VINTRACE_PW")

    if not username or not password:
        print("❌ ERROR: VINTRACE_USER or VINTRACE_PW environment variables not set.")
        return None, None

    return username, password


# ============================================================================
# LOADER WAITING FUNCTIONS
# ============================================================================

async def wait_for_all_vintrace_loaders(page_or_frame, timeout=LARGE_TIMEOUT):
    """
    Wait for all Vintrace loading indicators to disappear.
    Works with both Page and Frame objects.

    Handles both:
    - New UI loaders: div[id^="loader_Iframe_"]
    - Old UI loaders: #serverDelayMessageLong, #serverDelayMessage

    Args:
        page_or_frame: Playwright Page or Frame object
        timeout: Maximum wait time in milliseconds
    """
    try:
        print("⏳ Waiting for Vintrace loaders to disappear...")
        await page_or_frame.wait_for_function(
            """
            () => {
                // Function to check if loader is hidden in a document
                function allLoadersHidden(doc) {
                    // Check for loader in iframe with specific ID pattern (new UI)
                    const loaderDivs = doc.querySelectorAll('[id^="loader_Iframe_"]');
                    for (let loader of loaderDivs) {
                        const style = window.getComputedStyle(loader);
                        // If any loader is visible, return false
                        if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                            return false;
                        }
                    }

                    // Check for the old-style loaders (classic vintrace)
                    const long = doc.getElementById('serverDelayMessageLong');
                    const main = doc.getElementById('serverDelayMessage');
                    const longHidden = !long || getComputedStyle(long).visibility === 'hidden';
                    const mainHidden = !main || getComputedStyle(main).visibility === 'hidden';

                    return longHidden && mainHidden;
                }

                return allLoadersHidden(document);
            }
            """,
            timeout=timeout
        )
        print("✓ All Vintrace loaders hidden")
    except Exception as e:
        print(f"⚠ Timeout waiting for loaders to hide (may be okay): {e}")


async def wait_for_vintrace_loaders_to_appear(page_or_frame, timeout=STANDARD_TIMEOUT):
    """
    Wait for Vintrace loading indicators to APPEAR (become visible).
    Useful to ensure a page action triggered loading before waiting for it to complete.

    Args:
        page_or_frame: Playwright Page or Frame object
        timeout: Maximum wait time in milliseconds

    Returns:
        bool: True if loader appeared, False if not
    """
    try:
        print("⏳ Waiting for Vintrace loader to appear...")

        await page_or_frame.wait_for_function(
            """
            () => {
                function hasVisibleLoader(doc) {
                    // Check for new UI loaders
                    const loaderDivs = doc.querySelectorAll('[id^="loader_Iframe_"]');
                    for (let loader of loaderDivs) {
                        const style = window.getComputedStyle(loader);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                            return true;
                        }
                    }

                    // Check for old UI loaders
                    const long = doc.getElementById('serverDelayMessageLong');
                    const main = doc.getElementById('serverDelayMessage');
                    const longVisible = long && getComputedStyle(long).visibility !== 'hidden';
                    const mainVisible = main && getComputedStyle(main).visibility !== 'hidden';

                    return longVisible || mainVisible;
                }

                return hasVisibleLoader(document);
            }
            """, timeout=timeout
        )
        print("✓ Vintrace loader appeared")
        return True
    except Exception as e:
        print(f"⚠ Loader never appeared (page might have loaded instantly): {e}")
        return False


# ============================================================================
# IFRAME MANAGEMENT
# ============================================================================

async def get_main_iframe(page: Page):
    """
    Get the main iframe that contains the Vintrace application.
    Uses smart selector ordering based on historical success.

    Args:
        page: Playwright Page object

    Returns:
        Frame or Page: The iframe if found, otherwise the page itself
    """
    print("🔍 Looking for main Vintrace iframe...")

    await asyncio.sleep(2)

    # Use centralized selectors if available, otherwise fall back to defaults
    if NewUISelectors:
        iframe_selectors = NewUISelectors.IFRAME_MAIN.copy()
    else:
        iframe_selectors = [
            "iframe[id^='Iframe_']",  # Matches "Iframe_00f9496d-ed28-4a13-9321-e95349a09c99"
            "iframe.iFrameMax",  # The class from the HTML
            "iframe[vxiframeid]",  # Has the vxiframeid attribute
        ]
    
    # Add fallback selectors
    iframe_selectors.extend([
        "iframe[src*='xhtml']",  # Source contains xhtml
        "iframe[name*='vintrace' i]",
        "iframe[src*='vintrace']",
        "iframe"  # Final fallback
    ])
    
    # Sort selectors by historical success
    iframe_selectors = get_sorted_selectors("get_main_iframe", iframe_selectors)

    for selector in iframe_selectors:
        try:
            iframe_element = await page.wait_for_selector(selector, timeout=MEDIUM_TIMEOUT, state="attached")
            if iframe_element:
                iframe = await iframe_element.content_frame()
                if iframe:
                    print(f"✓ Found iframe using selector: {selector}")
                    # Track successful selector
                    track_selector("get_main_iframe", selector, "css", "main_iframe", "Main application iframe")
                    # Wait for iframe to load
                    await iframe.wait_for_load_state("domcontentloaded", timeout=STANDARD_TIMEOUT)
                    return iframe
        except Exception as e:
            print(f"  ✗ Failed to find iframe with selector '{selector}': {e}")
            continue

    print("⚠ No iframe found, using main page")
    return page


async def get_iframe_by_src(page: Page, src_pattern: str):
    """
    Get a specific iframe by its src attribute pattern.
    Useful for finding specific pages like 'vessels.xhtml', 'reports.xhtml', etc.

    Args:
        page: Playwright Page object
        src_pattern: Pattern to match in the iframe src (e.g., 'vessels.xhtml')

    Returns:
        Frame or None: The iframe if found, None otherwise
    """
    print(f"🔍 Looking for iframe with src pattern: {src_pattern}")

    try:
        selector = f"iframe[src*='{src_pattern}']"
        iframe_element = await page.wait_for_selector(selector, timeout=MEDIUM_TIMEOUT, state="attached")
        if iframe_element:
            iframe = await iframe_element.content_frame()
            if iframe:
                print(f"✓ Found iframe with src pattern: {src_pattern}")
                track_selector(
                    "get_iframe_by_src", selector, "css",
                    f"src_pattern_{src_pattern}",
                    f"Iframe with src containing {src_pattern}"
                )
                await iframe.wait_for_load_state("domcontentloaded", timeout=STANDARD_TIMEOUT)
                return iframe
    except Exception as e:
        print(f"  ✗ Failed to find iframe with src pattern '{src_pattern}': {e}")

    return None


# ============================================================================
# POPUP MANAGEMENT
# ============================================================================

async def close_popups(page_or_frame):
    """
    Close any tour/popup dialogs that appear after login.

    Args:
        page_or_frame: Playwright Page or Frame object
    """
    print("\n🔍 Checking for and closing any popups...")

    popup_close_selectors = [
        "button[data-role='end']",
        ".popover button[data-role='end']",
        ".tour button[data-role='end']",
        "button:has-text('End tour')",
        ".popover .close",
        ".modal .close",
        "button:has-text('Close')",
        "button:has-text('×')"
    ]

    
    # Use centralized selectors if available
    if PopupSelectors:
        popup_close_selectors = PopupSelectors.CLOSE_BUTTONS.copy()
    else:
        popup_close_selectors = [
            "button[data-role='end']",
            ".popover button[data-role='end']",
            ".tour button[data-role='end']",
            "button:has-text('End tour')",
            ".popover .close",
            ".modal .close",
            "button:has-text('Close')",
            "button:has-text('×')"
        ]
    
    # Sort by historical success
    popup_close_selectors = get_sorted_selectors("close_popups", popup_close_selectors)

    popups_closed = 0
    for selector in popup_close_selectors:
        try:
            buttons = await page_or_frame.query_selector_all(selector)
            for button in buttons:
                try:
                    is_visible = await button.is_visible()
                    if is_visible:
                        await button.click()
                        popups_closed += 1
                        print(f"  ✓ Closed popup using selector: {selector}")
                        track_selector("close_popups", selector, "css", "popup_close", "Popup close button")
                        await asyncio.sleep(0.5)
                except Exception:
                    pass
        except Exception:
            pass

    if popups_closed > 0:
        print(f"✓ Closed {popups_closed} popup(s)")
    else:
        print("  No popups found to close")

    await asyncio.sleep(1)


# ============================================================================
# LOGIN FUNCTIONS
# ============================================================================

async def vintrace_login(page: Page, username: str, password: str, navigate_to_old_url: bool = True):
    """
    Login to Vintrace application.

    Args:
        page: Playwright Page object
        username: Vintrace username/email
        password: Vintrace password
        navigate_to_old_url: Whether to navigate to OLD_URL after login (default: True)

    Returns:
        bool: True if login successful, False otherwise
    """
    print("=" * 60)
    print("LOGGING IN TO VINTRACE")
    print("=" * 60)
    print(f"Navigating to login page: {LOGIN_URL}")

    await page.goto(LOGIN_URL, timeout=LARGE_TIMEOUT)
    await page.wait_for_load_state("networkidle", timeout=STANDARD_TIMEOUT)
    print("✓ Login page loaded")

    # Wait for the Login tab to be active (in case page loads on Register tab)
    if LoginSelectors:
        login_tab_selectors = LoginSelectors.LOGIN_TAB
    else:
        login_tab_selectors = [
            'button[role="tab"][aria-selected="true"]:has-text("Login")',
            'button[role="tab"]:has-text("Login")'
        ]
    
    try:
        await page.wait_for_selector(
            'button[role="tab"][aria-selected="true"]:has-text("Login")',
            timeout=SHORT_TIMEOUT
        )
        print("✓ Login tab is active")
        track_selector(
            "vintrace_login",
            'button[role="tab"][aria-selected="true"]:has-text("Login")',
            "css", "login_tab_check", "Verify login tab is active"
        )
    except Exception:
        # Click the Login tab if it's not active
        try:
            login_tab_button = await page.wait_for_selector(
                'button[role="tab"]:has-text("Login")',
                timeout=SHORT_TIMEOUT
            )
            await login_tab_button.click()
            print("✓ Clicked Login tab")
            track_selector(
                "vintrace_login",
                'button[role="tab"]:has-text("Login")',
                "css", "login_tab_click", "Click login tab if not active"
            )
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠ Could not ensure Login tab is active: {e}")

    # OPTIMIZED SELECTORS based on the actual HTML structure
    email_selectors = [
        "input#email",  # Exact ID from the login page HTML
        "input[name='email'][type='email']",
        "input[placeholder='Enter email']",
        "input[type='email']",
    ]

    password_selectors = [
        "input#password",  # Exact ID from the login page HTML
        "input[name='password'][type='password']",
        "input[placeholder='Enter password']",
        "input[type='password']",
    ]
    
    # Use centralized selectors if available
    if LoginSelectors:
        email_selectors = LoginSelectors.EMAIL_INPUT.copy()
        password_selectors = LoginSelectors.PASSWORD_INPUT.copy()
    else:
        # Fallback selectors based on actual HTML structure
        email_selectors = [
            "input#email",  # Exact ID from the login page HTML
            "input[name='email'][type='email']",
            "input[placeholder='Enter email']",
            "input[type='email']",
        ]
        
        password_selectors = [
            "input#password",  # Exact ID from the login page HTML
            "input[name='password'][type='password']",
            "input[placeholder='Enter password']",
            "input[type='password']",
        ]
    
    # Sort by historical success
    email_selectors = get_sorted_selectors("vintrace_login_email", email_selectors)
    password_selectors = get_sorted_selectors("vintrace_login_password", password_selectors)

    # Fill email/username field
    print("\nAttempting to fill email field...")
    email_filled = False
    for selector in email_selectors:
        try:
            await page.wait_for_selector(selector, timeout=SHORT_TIMEOUT, state="visible")
            await page.fill(selector, username)
            print(f"✓ Filled email using selector: {selector}")
            track_selector(
                "vintrace_login_email", selector, "css", "email_field",
                "Email/username input field on login page"
            )
            email_filled = True
            break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue

    if not email_filled:
        print("❌ ERROR: Could not find email input field")
        await save_debug_screenshot(page, "login_email_not_found")
        return False

    await asyncio.sleep(0.3)

    # Fill password field
    print("\nAttempting to fill password field...")
    password_filled = False
    for selector in password_selectors:
        try:
            await page.wait_for_selector(selector, timeout=SHORT_TIMEOUT, state="visible")
            await page.fill(selector, password)
            print(f"✓ Filled password using selector: {selector}")
            track_selector(
                "vintrace_login_password", selector, "css", "password_field",
                "Password input field on login page"
            )
            password_filled = True
            break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue

    if not password_filled:
        print("❌ ERROR: Could not find password input field")
        await save_debug_screenshot(page, "login_password_not_found")
        return False

    await asyncio.sleep(0.3)

    # Click login button
    print("\nAttempting to click login button...")
    login_btn_selectors = [
        "button[type='submit'].chakra-button:has-text('Login')",
        "button[type='submit']:has-text('Login')",
        "button.chakra-button:has-text('Login')",
        "button[type='submit']",
    ]

    if LoginSelectors:
        login_btn_selectors = LoginSelectors.LOGIN_BUTTON.copy()
    else:
        login_btn_selectors = [
            "button[type='submit'].chakra-button:has-text('Login')",
            "button[type='submit']:has-text('Login')",
            "button.chakra-button:has-text('Login')",
            "button[type='submit']",
        ]
    
    # Sort by historical success
    login_btn_selectors = get_sorted_selectors("vintrace_login_button", login_btn_selectors)

    login_clicked = False
    for selector in login_btn_selectors:
        try:
            await page.wait_for_selector(selector, timeout=SHORT_TIMEOUT, state="visible")
            login_btn = await page.query_selector(selector)
            if login_btn:
                # Ensure button is enabled
                is_disabled = await login_btn.get_attribute("disabled")
                if is_disabled:
                    print("  ⚠ Login button is disabled, waiting...")
                    await asyncio.sleep(1)

                await login_btn.scroll_into_view_if_needed()
                await login_btn.click()
                print(f"✓ Clicked login button using selector: {selector}")
                track_selector("vintrace_login_button", selector, "css", "login_button", "Submit button on login page")
                login_clicked = True
                break
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue

    if not login_clicked:
        print("❌ ERROR: Login button not found or could not be clicked")
        await save_debug_screenshot(page, "login_button_not_found")
        return False

    # Wait for navigation after login
    print("\n⏳ Waiting for login to complete and page to navigate...")
    try:
        # Wait for URL to change from login page
        await page.wait_for_url(lambda url: url != LOGIN_URL and "/sign-in" not in url, timeout=LARGE_TIMEOUT)
        print("✓ Navigated away from login page")
        print(f"  Current URL: {page.url}")

        # Wait for network to be idle
        await page.wait_for_load_state("networkidle", timeout=LARGE_TIMEOUT)
        print("✓ Network idle after login")

        # Check for login errors (Chakra UI toast notifications)
        error_indicators = [
            "text='Invalid email or password'",
            "text='Login failed'",
            "text='Incorrect username or password'",
            "text='Invalid credentials'",
            "div[role='alert']",
            "#chakra-toast-manager-top >> text=/error|invalid|failed/i",
            ".chakra-alert--error",
        ]

        for error_sel in error_indicators:
            try:
                error_elem = await page.query_selector(error_sel)
                if error_elem:
                    is_visible = await error_elem.is_visible()
                    if is_visible:
                        error_text = await error_elem.inner_text()
                        print(f"❌ ERROR: Login failed - {error_text}")
                        await save_debug_screenshot(page, "login_credentials_invalid")
                        return False
            except Exception:
                pass

    except Exception as e:
        print(f"❌ ERROR: Login may have failed - URL did not change: {e}")
        print(f"  Current URL: {page.url}")
        await save_debug_screenshot(page, "login_navigation_failed")
        return False

    # Navigate to old URL if requested (for grape/dispatch reports)
    if navigate_to_old_url:
        print(f"\n⏳ Navigating to OLD_URL: {OLD_URL}")
        await page.goto(OLD_URL, timeout=LARGE_TIMEOUT)
        print("✓ Navigated to OLD_URL")

        # Wait for the page loaders (both in main page and iframe)
        await wait_for_all_vintrace_loaders(page)

        # Also wait for iframe to load if present
        try:
            iframe = await get_main_iframe(page)
            if iframe != page:  # If we actually found an iframe
                await wait_for_all_vintrace_loaders(iframe)
        except Exception as e:
            print(f"⚠ Could not check iframe loaders: {e}")

        await asyncio.sleep(2)
    else:
        # For barrel report - wait for new UI to load
        print("\n⏳ Waiting for new Vintrace UI to load...")

        # Wait for the main page loaders
        await wait_for_vintrace_loaders_to_appear(page, timeout=LOADER_APPEAR_TIMEOUT)
        await wait_for_all_vintrace_loaders(page, timeout=LARGE_TIMEOUT)

        # Get the main iframe and wait for it to load
        iframe = await get_main_iframe(page)
        if iframe != page:  # If we found an iframe
            await wait_for_vintrace_loaders_to_appear(iframe, timeout=LOADER_APPEAR_TIMEOUT)
            await wait_for_all_vintrace_loaders(iframe, timeout=LARGE_TIMEOUT)
            await close_popups(iframe)

        await asyncio.sleep(2)

    print("\n✓ Login successful and page fully loaded!")
    print("=" * 60)
    return True


# ============================================================================
# NAVIGATION HELPERS - NEW UI
# ============================================================================

async def navigate_to_reports_new_ui(page: Page):
    """
    Navigate to the Reports section in the NEW Vintrace UI.
    This clicks the Reports menu item in the PrimeFaces sidebar.

    Args:
        page: Playwright Page object

    Returns:
        bool: True if navigation successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("NAVIGATING TO REPORTS (NEW UI)")
    print("=" * 60)

    # Multiple selector strategies for the Reports menu item
    reports_selectors = [
        "a#menuform\\:menu-reports-cs",  # Exact ID with escaped colon
        "a[id='menuform:menu-reports-cs']",  # ID with attribute selector
        "li.ui-menuitem a:has-text('Reports')",  # By text in menu item
        "a.ui-menuitem-link:has-text('Reports')",  # By class and text
        "span.ui-icon-reports",  # By icon class, then get parent link
    ]

    
    # Use centralized selectors if available
    if NewUISelectors:
        reports_selectors = NewUISelectors.REPORTS_MENU.copy()
    else:
        # Multiple selector strategies for the Reports menu item
        reports_selectors = [
            "a#menuform\\:menu-reports-cs",  # Exact ID with escaped colon
            "a[id='menuform:menu-reports-cs']",  # ID with attribute selector
            "li.ui-menuitem a:has-text('Reports')",  # By text in menu item
            "a.ui-menuitem-link:has-text('Reports')",  # By class and text
        ]
    
    # Add icon-based selector as fallback
    reports_selectors.append("span.ui-icon-reports")
    
    # Sort by historical success
    reports_selectors = get_sorted_selectors("navigate_to_reports_new_ui", reports_selectors)

    for selector in reports_selectors:
        try:
            print(f"  Trying selector: {selector}")

            # Special handling for the icon selector
            if "ui-icon-reports" in selector:
                icon = await page.wait_for_selector(selector, timeout=SHORT_TIMEOUT, state="visible")
                if icon:
                    # Get the parent <a> tag
                    link = await icon.evaluate_handle("el => el.closest('a')")
                    if link:
                        await link.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        await link.click()
                        print("✓ Clicked Reports menu using icon selector")
                        track_selector(
                            "navigate_to_reports_new_ui",
                            selector,
                            "css",
                            "new_ui_reports",
                            "Reports menu via icon in new UI"
                        )
                        await wait_for_all_vintrace_loaders(page)
                        await asyncio.sleep(2)
                        return True
            else:
                # Normal selector
                await page.wait_for_selector(selector, timeout=SHORT_TIMEOUT, state="visible")
                reports_link = await page.query_selector(selector)
                if reports_link:
                    await reports_link.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await reports_link.click()
                    print(f"✓ Clicked Reports menu using selector: {selector}")
                    track_selector(
                        "navigate_to_reports_new_ui",
                        selector,
                        "css",
                        "new_ui_reports",
                        "Reports menu item in new UI"
                    )
                    await wait_for_all_vintrace_loaders(page)
                    await asyncio.sleep(2)
                    return True

        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue

    print("❌ ERROR: Could not find or click Reports menu item")
    await save_debug_screenshot(page, "navigate_reports_new_ui_error")
    return False


async def navigate_to_report_category(page: Page, category_name: str):
    """
    Click on a specific report category in the Reports section.

    Available categories:
    - Custom reports
    - Loss
    - Product analysis
    - Product history
    - Fruit samples
    - Fermentation
    - Label integrity
    - Government reports
    - WSA reports
    - DSP reports
    - Equipment
    - Task completion
    - Bulk wine
    - Inventory
    - Vintage/Harvest
    - Operations
    - System audit
    - Sales
    - Allocations
    - Grower contracts

    Args:
        page: Playwright Page object
        category_name: Name of the report category to click (case-sensitive)

    Returns:
        bool: True if category found and clicked, False otherwise
    """
    print(f"\n🔍 Looking for report category: '{category_name}'")

    # Wait for the report categories table to load
    try:
        await page.wait_for_selector("table.jx2table", timeout=MEDIUM_TIMEOUT)
        print("✓ Report categories loaded")
    except Exception as e:
        print(f"❌ Report categories table not found: {e}")
        return False

    # Strategy 1: Find by exact text match in span with pattern id="c_XXX|Text"
    try:
        # Look for all spans with the |Text pattern in their ID
        spans = await page.query_selector_all("span[id$='|Text']")
        for span in spans:
            text = await span.inner_text()
            if text.strip() == category_name:
                # Get the parent div or td to click
                parent = await span.evaluate_handle("el => el.closest('div.label-normal') || el.closest('td')")
                if parent:
                    await parent.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await parent.click()
                    print(f"✓ Clicked category '{category_name}' using span|Text selector")
                    track_selector(
                        "navigate_to_report_category",
                        "span[id$='|Text']",
                        "css",
                        f"category_{category_name}",
                        f"Report category: {category_name}"
                    )
                    await wait_for_all_vintrace_loaders(page)
                    await asyncio.sleep(1)
                    return True
    except Exception as e:
        print(f"  ✗ Failed with span|Text strategy: {e}")

    # Strategy 2: Find by div.label-normal containing the exact text
    selectors = [
        f"div.label-normal:has-text('{category_name}')",
        f"span:has-text('{category_name}')",
        f"td:has-text('{category_name}')",
    ]

    for selector in selectors:
        try:
            element = await page.wait_for_selector(selector, timeout=QUICK_TIMEOUT, state="visible")
            if element:
                # Check if text matches exactly
                text = await element.inner_text()
                if text.strip() == category_name:
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await element.click()
                    print(f"✓ Clicked category '{category_name}' using selector: {selector}")
                    track_selector(
                        "navigate_to_report_category",
                        selector,
                        "css",
                        f"category_{category_name}",
                        f"Report category: {category_name}"
                    )
                    await wait_for_all_vintrace_loaders(page)
                    await asyncio.sleep(1)
                    return True
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue

    # Strategy 3: Find in table rows by exact text (looking at table#c_21)
    try:
        rows = await page.query_selector_all("table#c_21 tbody tr, table.jx2table tbody tr")
        for row in rows:
            text = await row.inner_text()
            if text.strip() == category_name:
                await row.scroll_into_view_if_needed()
                await asyncio.sleep(0.3)
                await row.click()
                print(f"✓ Clicked category '{category_name}' by row text match")
                track_selector(
                    "navigate_to_report_category",
                    "table row text match",
                    "text",
                    f"category_{category_name}",
                    f"Report category: {category_name}"
                )
                await wait_for_all_vintrace_loaders(page)
                await asyncio.sleep(1)
                return True
    except Exception as e:
        print(f"  ✗ Failed to find category by row text: {e}")

    print(f"❌ Could not find report category: '{category_name}'")
    await save_debug_screenshot(page, f"category_{category_name.replace(' ', '_')}_error")
    return False


async def find_and_click_report_by_name(page: Page, report_name: str):
    """
    Find and click a specific report by its name in the current category.

    Args:
        page: Playwright Page object
        report_name: Name of the report to find and click

    Returns:
        bool: True if report found and clicked, False otherwise
    """
    print(f"\n🔍 Looking for report: '{report_name}'")

    # Wait for reports to load in the right panel
    try:
        await page.wait_for_selector("div.report-content", timeout=MEDIUM_TIMEOUT)
        print("✓ Report content area loaded")
    except Exception as e:
        print(f"❌ Report content area not found: {e}")
        return False

    # Strategy 1: Find by button label text
    selectors = [
        f"div.btn-lbl-bold:has-text('{report_name}')",
        f"div.btn-lbl-normal:has-text('{report_name}')",
        f"div[id*='c_']:has-text('{report_name}')",
    ]

    for selector in selectors:
        try:
            element = await page.wait_for_selector(selector, timeout=QUICK_TIMEOUT, state="visible")
            if element:
                # Check if text matches exactly
                text = await element.inner_text()
                if text.strip() == report_name:
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await element.click()
                    print(f"✓ Clicked report '{report_name}' using selector: {selector}")
                    track_selector(
                        "find_and_click_report_by_name",
                        selector,
                        "css",
                        f"report_{report_name}",
                        f"Report: {report_name}"
                    )
                    await wait_for_all_vintrace_loaders(page)
                    await asyncio.sleep(1)
                    return True
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue

    # Strategy 2: Find the "Run report" icon next to the report name
    try:
        # Find all report rows
        report_rows = await page.query_selector_all("table.jx2table tbody tr")
        for row in report_rows:
            text = await row.inner_text()
            # Check if this row contains the report name
            if report_name in text:
                # Look for the "Run report" icon (search icon) in this row
                run_icon = await row.query_selector("img[src*='search-grey.png']")
                if run_icon:
                    # Click the parent div/link
                    run_button = await run_icon.evaluate_handle("el => el.closest('div.link')")
                    if run_button:
                        await run_button.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        await run_button.click()
                        print(f"✓ Clicked 'Run' button for report '{report_name}'")
                        track_selector(
                            "find_and_click_report_by_name",
                            "img[src*='search-grey.png']",
                            "css",
                            f"report_{report_name}_run",
                            f"Run button for report: {report_name}"
                        )
                        await wait_for_all_vintrace_loaders(page)
                        await asyncio.sleep(1)
                        return True
    except Exception as e:
        print(f"  ✗ Failed to find report by run icon: {e}")

    print(f"❌ Could not find report: '{report_name}'")
    await save_debug_screenshot(page, f"report_{report_name.replace(' ', '_')}_error")
    return False


async def close_report_window(page: Page):
    """
    Close the "Winery reports" window/modal.
    Looks for the close button in the window title bar.

    Args:
        page: Playwright Page object

    Returns:
        bool: True if window closed, False otherwise
    """
    print("\n🔍 Attempting to close report window...")

    close_selectors = [
        "div.echo2-window-pane-close",  # The close div
        "div[id$='_close'].echo2-window-pane-close",  # More specific with ID pattern
        "div.echo2-window-pane-close img[src*='close']",  # The close icon
        "div.echo2-window-pane-title ~ div[id$='_close']",  # Sibling of title
    ]

    # Sort by historical success
    close_selectors = get_sorted_selectors("close_report_window", close_selectors)

    for selector in close_selectors:
        try:
            close_btn = await page.wait_for_selector(selector, timeout=SHORT_TIMEOUT, state="visible")
            if close_btn:
                await close_btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.3)
                await close_btn.click()
                print(f"✓ Clicked close button using selector: {selector}")
                track_selector(
                    "close_report_window",
                    selector,
                    "css",
                    "close_report_window",
                    "Close button for report window"
                )
                await wait_for_all_vintrace_loaders(page)
                await asyncio.sleep(1)
                return True
        except Exception as e:
            print(f"  ✗ Failed with selector '{selector}': {e}")
            continue

    print("⚠ Could not find close button, window might be already closed")
    return False


# ============================================================================
# NAVIGATION HELPERS - OLD UI
# ============================================================================

async def navigate_to_reports_old_ui(page: Page):
    """
    Navigate to Reports in the OLD Vintrace UI.
    Clicks the Reports quick launch icon.

    Args:
        page: Playwright Page object

    Returns:
        bool: True if navigation successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("NAVIGATING TO REPORTS (OLD UI)")
    print("=" * 60)

    # Click Reports icon - try by ID first, then by title
    reports_clicked = False

    selectors = [
        "#c_170",
        "div[title='Reports']"
    ]

    
    # Click Reports icon - use centralized selectors if available
    reports_clicked = False
    
    if OldUISelectors:
        selectors = OldUISelectors.REPORTS_ICON.copy()
    else:
        selectors = [
            "#c_170",
            "div[title='Reports']"
        ]
    
    # Sort by historical success
    selectors = get_sorted_selectors("navigate_to_reports_old_ui", selectors)

    for selector in selectors:
        try:
            await page.wait_for_selector(selector, timeout=MEDIUM_TIMEOUT)
            reports_icon = await page.query_selector(selector)
            if reports_icon:
                await reports_icon.scroll_into_view_if_needed()
                await reports_icon.click()
                reports_clicked = True
                print(f"✓ Clicked the 'Reports' quick launch icon using: {selector}")
                track_selector(
                    "navigate_to_reports_old_ui",
                    selector,
                    "css",
                    "old_ui_reports",
                    "Reports icon in old UI"
                )
                break
        except Exception as e:
            print(f"  ✗ Could not click Reports icon with selector '{selector}': {e}")

    if not reports_clicked:
        print("❌ ERROR: Could not click Reports icon")
        await save_debug_screenshot(page, "navigate_reports_old_error")
        return False

    await wait_for_all_vintrace_loaders(page)
    await asyncio.sleep(1)
    print("✓ Reports section loaded")
    return True


async def click_vintage_harvest_tab_old_ui(page: Page):
    """
    Click the Vintage/Harvest tab in the OLD Vintrace UI Reports section.

    Args:
        page: Playwright Page object

    Returns:
        bool: True if tab clicked, False otherwise
    """
    print("\n🔍 Clicking 'Vintage/Harvest' tab...")

    selectors = [
        "span:text('Vintage/Harvest')",
        "div:text('Vintage/Harvest')",
        "td:text('Vintage/Harvest')",
        "tr:has-text('Vintage/Harvest')",
        "[id$='|Text']:text('Vintage/Harvest')",
    ]

    # Sort by historical success
    selectors = get_sorted_selectors("click_vintage_harvest_tab_old_ui", selectors)

    for selector in selectors:
        try:
            await page.wait_for_selector(selector, timeout=SHORT_TIMEOUT)
            element = await page.query_selector(selector)
            if element:
                await element.scroll_into_view_if_needed()
                await element.click()
                print(f"✓ Clicked 'Vintage/Harvest' using selector: {selector}")
                track_selector(
                    "click_vintage_harvest_tab_old_ui",
                    selector,
                    "css",
                    "vintage_harvest_tab",
                    "Vintage/Harvest tab in old UI"
                )
                await wait_for_all_vintrace_loaders(page)
                await asyncio.sleep(1)
                return True
        except Exception:
            continue

    # Fallback: xpath
    try:
        element = await page.query_selector("xpath=//*[text()='Vintage/Harvest']")
        if element:
            await element.scroll_into_view_if_needed()
            await element.click()
            print("✓ Clicked 'Vintage/Harvest' using xpath")
            track_selector(
                "click_vintage_harvest_tab_old_ui",
                "//*[text()='Vintage/Harvest']",
                "xpath",
                "vintage_harvest_tab",
                "Vintage/Harvest tab via xpath"
            )
            await wait_for_all_vintrace_loaders(page)
            await asyncio.sleep(1)
            return True
    except Exception as e:
        print(f"❌ Could not click 'Vintage/Harvest': {e}")

    await save_debug_screenshot(page, "vintage_harvest_tab_error")
    return False


# ============================================================================
# REPORT INTERACTION HELPERS
# ============================================================================

async def find_report_strip_by_title(page: Page, report_title: str):
    """
    Find a specific report strip section by its title.
    Report strips are the sections that contain report configuration and generation.

    Args:
        page: Playwright Page object
        report_title: Title of the report (e.g., "Bulk Stock Report")

    Returns:
        ElementHandle or None: The reportStrip div if found, None otherwise
    """
    print(f"\n🔍 Looking for report strip: '{report_title}'")

    try:
        # Wait for report strips to load
        await page.wait_for_selector("div.reportStrip", timeout=MEDIUM_TIMEOUT)

        # Find all report strips
        report_strips = await page.query_selector_all("div.reportStrip")

        for strip in report_strips:
            # Get all text content in this strip
            text_content = await strip.inner_text()

            # Check if the title is in this strip
            if report_title in text_content:
                print(f"✓ Found report strip for '{report_title}'")
                track_selector(
                    "find_report_strip_by_title",
                    "div.reportStrip",
                    "css",
                    f"strip_{report_title}",
                    f"Report strip for: {report_title}"
                )
                return strip

        print(f"❌ Could not find report strip for '{report_title}'")
        return None

    except Exception as e:
        print(f"❌ Error finding report strip: {e}")
        return None


async def select_report_format(report_strip, format_type: str = "CSV"):
    """
    Select the output format for a report (PDF, CSV, Excel).

    Args:
        report_strip: The reportStrip element handle
        format_type: Format to select - "PDF", "CSV", or "Excel" (default: "CSV")

    Returns:
        bool: True if format selected, False otherwise
    """
    print(f"📄 Selecting report format: {format_type}")

    format_type = format_type.upper()

    try:
        # Find all select dropdowns within this report strip
        selects = await report_strip.query_selector_all("select")

        for select in selects:
            # Get all options
            options = await select.query_selector_all("option")

            for option in options:
                option_text = (await option.inner_text()).strip().upper()

                # Check if this option matches our desired format
                if format_type in option_text or option_text == format_type:
                    value = await option.get_attribute("value")
                    if value:
                        await select.select_option(value=value)
                    else:
                        await select.select_option(label=await option.inner_text())

                    print(f"✓ Selected format: {format_type}")
                    track_selector(
                        "select_report_format",
                        "select option",
                        "css",
                        f"format_{format_type}",
                        f"Report format: {format_type}"
                    )
                    await asyncio.sleep(0.5)
                    return True

        print(f"⚠ Could not find {format_type} format option")
        return False

    except Exception as e:
        print(f"❌ Error selecting format: {e}")
        return False


async def set_report_checkbox(report_strip, checkbox_label: str, checked: bool):
    """
    Set a checkbox within a report strip by its label text.

    Args:
        report_strip: The reportStrip element handle
        checkbox_label: Text label near the checkbox
        checked: True to check, False to uncheck

    Returns:
        bool: True if checkbox set successfully, False otherwise
    """
    print(f"☑️  Setting checkbox '{checkbox_label}' to: {checked}")

    try:
        # Strategy 1: Look for checkbox images (Vintrace uses images for checkboxes)
        # Find the checkbox by looking for the label text and then finding nearby checkbox image

        # Find all elements containing the label text
        label_elements = await report_strip.query_selector_all(f"*:has-text('{checkbox_label}')")

        for label_elem in label_elements:
            # Check if the text matches exactly or closely
            label_text = await label_elem.inner_text()
            if checkbox_label in label_text:
                # Look for checkbox image in parent or nearby elements
                # Vintrace checkboxes have images with src containing "CheckboxOn" or "CheckboxOff"
                parent = await label_elem.evaluate_handle(
                    "el => el.closest('tr') || el.closest('div') || "
                    "el.closest('table') || el.parentElement"
                )

                if parent:
                    checkbox_imgs = await parent.query_selector_all("img[src*='Checkbox'], img[id*='stateicon']")

                    for img in checkbox_imgs:
                        src = await img.get_attribute("src")
                        is_checked = "CheckboxOn" in src if src else False

                        # If current state doesn't match desired state, click it
                        if (checked and not is_checked) or (not checked and is_checked):
                            await img.scroll_into_view_if_needed()
                            await img.click()
                            print(f"✓ {'Checked' if checked else 'Unchecked'} '{checkbox_label}'")
                            track_selector(
                                "set_report_checkbox",
                                "img[src*='Checkbox']",
                                "css",
                                f"checkbox_{checkbox_label}",
                                f"Checkbox: {checkbox_label}"
                            )
                            await asyncio.sleep(0.3)
                            return True
                        else:
                            print(f"✓ Checkbox '{checkbox_label}' already in desired state")
                            return True

        # Strategy 2: Look for actual input[type="checkbox"] elements
        checkboxes = await report_strip.query_selector_all("input[type='checkbox']")
        for checkbox in checkboxes:
            # Find associated label
            checkbox_id = await checkbox.get_attribute("id")
            if checkbox_id:
                label = await report_strip.query_selector(f"label[for='{checkbox_id}']")
                if label:
                    label_text = await label.inner_text()
                    if checkbox_label in label_text:
                        is_checked = await checkbox.is_checked()
                        if (checked and not is_checked) or (not checked and is_checked):
                            await checkbox.click()
                            print(f"✓ {'Checked' if checked else 'Unchecked'} '{checkbox_label}'")
                            track_selector(
                                "set_report_checkbox",
                                "input[type='checkbox']",
                                "css",
                                f"checkbox_{checkbox_label}",
                                f"Checkbox: {checkbox_label}"
                            )
                            await asyncio.sleep(0.3)
                            return True

        print(f"⚠ Could not find checkbox for '{checkbox_label}'")
        return False

    except Exception as e:
        print(f"❌ Error setting checkbox: {e}")
        return False


async def select_report_dropdown_option(report_strip, option_text: str, dropdown_index: int = 0):
    """
    Select an option from a dropdown within a report strip.

    Args:
        report_strip: The reportStrip element handle
        option_text: Text of the option to select
        dropdown_index: Which dropdown to use if there are multiple (0-indexed, default: 0)

    Returns:
        bool: True if option selected, False otherwise
    """
    print(f"🔽 Selecting dropdown option: '{option_text}' (dropdown #{dropdown_index})")

    try:
        # Find all select elements in the report strip
        selects = await report_strip.query_selector_all("select")

        if dropdown_index >= len(selects):
            print(f"⚠ Dropdown index {dropdown_index} out of range (found {len(selects)} dropdowns)")
            return False

        select = selects[dropdown_index]

        # Find the option with matching text
        options = await select.query_selector_all("option")
        for option in options:
            text = (await option.inner_text()).strip()
            if text == option_text or option_text in text:
                value = await option.get_attribute("value")
                if value:
                    await select.select_option(value=value)
                else:
                    await select.select_option(label=text)

                print(f"✓ Selected '{option_text}'")
                track_selector(
                    "select_report_dropdown_option",
                    "select option",
                    "css",
                    f"dropdown_{option_text}",
                    f"Dropdown option: {option_text}"
                )
                await asyncio.sleep(0.3)
                return True

        print(f"⚠ Could not find option '{option_text}'")
        return False

    except Exception as e:
        print(f"❌ Error selecting dropdown option: {e}")
        return False


async def click_generate_button(report_strip):
    """
    Click the "Generate" or "Generate..." button within a report strip.

    Args:
        report_strip: The reportStrip element handle

    Returns:
        bool: True if button clicked, False otherwise
    """
    print("🔘 Clicking 'Generate' button...")

    generate_selectors = [
        "button:has-text('Generate')",
        "input[type='button'][value*='Generate']",
        "button:has-text('Generate...')",
        "input[value='Generate']",
    ]

    # Sort by historical success
    generate_selectors = get_sorted_selectors("click_generate_button", generate_selectors)

    for selector in generate_selectors:
        try:
            btn = await report_strip.query_selector(selector)
            if btn:
                await btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.3)
                await btn.click()
                print("✓ Clicked 'Generate' button")
                track_selector(
                    "click_generate_button",
                    selector,
                    "css",
                    "generate_button",
                    "Generate button for report"
                )
                await asyncio.sleep(0.5)
                return True
        except Exception:
            continue

    # Fallback: XPath search for Generate button
    try:
        btn = await report_strip.query_selector(
            "xpath=.//button[contains(text(), 'Generate')] | "
            ".//input[@type='button' and contains(@value, 'Generate')]"
        )
        if btn:
            await btn.scroll_into_view_if_needed()
            await asyncio.sleep(0.3)
            await btn.click()
            print("✓ Clicked 'Generate' button (xpath)")
            track_selector(
                "click_generate_button",
                ".//button[contains(text(), 'Generate')]",
                "xpath",
                "generate_button",
                "Generate button via xpath"
            )
            await asyncio.sleep(0.5)
            return True
    except Exception as e:
        print(f"❌ Could not click 'Generate' button: {e}")

    print("❌ Could not find 'Generate' button")
    return False


async def download_report_from_strip(page: Page, report_strip, save_dir: str, timeout_ms: int = DOWNLOAD_TIMEOUT_MS):
    """
    Trigger report download and save the file.

    Args:
        page: Playwright Page object (needed for download handling)
        report_strip: The reportStrip element handle
        save_dir: Directory to save the downloaded file
        timeout_ms: Download timeout in milliseconds

    Returns:
        str or None: Path to downloaded file, or None if failed
    """
    print("⬇️  Starting download...")

    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)

    try:
        # Click generate and wait for download
        async with page.expect_download(timeout=timeout_ms) as download_info:
            await click_generate_button(report_strip)

        download = await download_info.value
        temp_path = await download.path()
        filename = download.suggested_filename

        # Move to target directory
        target_path = os.path.join(save_dir, filename)

        if os.path.exists(target_path):
            os.remove(target_path)

        shutil.move(temp_path, target_path)

        print(f"✓ Downloaded: {filename}")
        print(f"  Saved to: {target_path}")

        return target_path

    except Exception as e:
        print(f"❌ Download failed: {e}")
        await save_debug_screenshot(page, "download_failed")
        return None


# ============================================================================
# COMBINED WORKFLOW HELPER
# ============================================================================

async def save_debug_screenshot(page: Page, name: str):
    """
    Save a debug screenshot with a timestamp.

    Args:
        page: Playwright Page object
        name: Base name for the screenshot file

    Returns:
        str: Path to the saved screenshot
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debug_{name}_{timestamp}.png"
    screenshots_dir = "screenshots"

    # Create screenshots directory if it doesn't exist
    os.makedirs(screenshots_dir, exist_ok=True)

    filepath = os.path.join(screenshots_dir, filename)

    try:
        await page.screenshot(path=filepath, full_page=True)
        print(f"📸 Debug screenshot saved: {filepath}")
        return filepath
    except Exception as e:
        print(f"⚠ Could not save screenshot: {e}")
        return None


async def configure_and_download_report(
    page: Page,
    report_title: str,
    save_dir: str,
    format_type: str = "CSV",
    checkboxes: dict = None,
    dropdown_options: list = None
):
    """
    Complete workflow to find, configure, and download a report.

    Args:
        page: Playwright Page object
        report_title: Title of the report to find
        save_dir: Directory to save downloaded file
        format_type: Report format - "PDF", "CSV", or "Excel"
        checkboxes: Dict of checkbox labels and their desired states (True/False)
        dropdown_options: List of tuples (option_text, dropdown_index) for dropdown selections

    Returns:
        str or None: Path to downloaded file, or None if failed
    """
    print("\n" + "=" * 60)
    print(f"CONFIGURING AND DOWNLOADING REPORT: {report_title}")
    print("=" * 60)

    # Find the report strip
    report_strip = await find_report_strip_by_title(page, report_title)
    if not report_strip:
        print(f"❌ Could not find report: {report_title}")
        await save_debug_screenshot(page, f"report_{report_title.replace(' ', '_')}_not_found")
        return None

    # Select format
    if not await select_report_format(report_strip, format_type):
        print(f"⚠ Could not set format to {format_type}, continuing anyway...")

    # Set checkboxes
    if checkboxes:
        for label, checked in checkboxes.items():
            await set_report_checkbox(report_strip, label, checked)

    # Select dropdown options
    if dropdown_options:
        for option_text, dropdown_index in dropdown_options:
            await select_report_dropdown_option(report_strip, option_text, dropdown_index)

    # Download the report
    downloaded_file = await download_report_from_strip(page, report_strip, save_dir)

    if downloaded_file:
        print(f"✓ Report downloaded successfully: {downloaded_file}")
        print("=" * 60)
        return downloaded_file
    else:
        print("❌ Report download failed")
        print("=" * 60)
        return None


# ============================================================================
# BROWSER INITIALIZATION
# ============================================================================

async def initialize_browser(playwright_instance, headless: bool = False):
    """
    Initialize a Playwright browser with standard settings.
    
    Args:
        playwright_instance: Playwright instance from async_playwright()
        headless: Whether to run in headless mode (default: False)
        
    Returns:
        tuple: (browser, context, page)
    """
    print("🌐 Initializing browser...")
    
    # Launch browser with standard options
    browser = await playwright_instance.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox'
        ]
    )
    
    # Create context with realistic viewport
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    # Create page
    page = await context.new_page()
    
    # Set longer default timeouts
    page.set_default_timeout(60000)  # 60 seconds
    
    print("✓ Browser initialized")
    return browser, context, page


# ============================================================================
# DEBUG UTILITIES
# ============================================================================

async def save_debug_screenshot(page_or_frame, filename_prefix: str):
    """
    Save a debug screenshot with timestamp.
    
    Args:
        page_or_frame: Playwright Page or Frame object
        filename_prefix: Prefix for the screenshot filename
        
    Returns:
        str: Path to saved screenshot
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.png"
    
    # Save to debug directory
    debug_dir = "debug_screenshots"
    os.makedirs(debug_dir, exist_ok=True)
    
    filepath = os.path.join(debug_dir, filename)
    
    try:
        await page_or_frame.screenshot(path=filepath, full_page=True)
        print(f"📸 Debug screenshot saved: {filepath}")
        return filepath
    except Exception as e:
        print(f"⚠ Could not save debug screenshot: {e}")
        return None
