"""
Vintrace Selector Definitions
Centralized selector repository based on actual HTML structure analysis

Author: GlipGlops-glitch
Created: 2025-01-11
Last Updated: 2025-01-11

This module contains selector definitions extracted from the Vintrace HTML files
to ensure accurate and maintainable automation. Selectors are organized by
UI version (New/Old) and functional area.
"""

# ============================================================================
# NEW UI SELECTORS (PrimeFaces based)
# ============================================================================

class NewUISelectors:
    """Selectors for the new Vintrace UI (PrimeFaces framework)"""
    
    # Iframe selectors
    IFRAME_MAIN = [
        "iframe[id^='Iframe_']",  # Primary pattern with UUID
        "iframe.iFrameMax",  # Class-based selector
        "iframe[vxiframeid]",  # Has vxiframeid attribute
    ]
    
    # Loader selectors
    LOADER_DIVS = [
        "div[id^='loader_Iframe_']",  # New UI loader pattern
    ]
    
    # Barrel/Vessel page selectors
    EXPORT_BUTTON = [
        "button#vesselsForm\\:vesselsDT\\:exportButton",  # Exact ID with escaped colon
        "button[id='vesselsForm:vesselsDT:exportButton']",  # ID via attribute selector
        "button.vin-download-btn",  # Class-based fallback
    ]
    
    BARREL_DETAILS_MENU_ITEM = [
        "li#vesselsForm\\:vesselsDT\\:printOptions-barrelDetails > a.ui-submenu-link",
        "li[id='vesselsForm:vesselsDT:printOptions-barrelDetails'] > a.ui-submenu-link",
        "li.vin-exportMenuOption:has-text('Barrel details') > a",
    ]
    
    BARREL_DETAILS_ALL_OPTION = [
        "a#vesselsForm\\:vesselsDT\\:printOptions-barrelDetails-all",
        "a[id='vesselsForm:vesselsDT:printOptions-barrelDetails-all']",
        "li#vesselsForm\\:vesselsDT\\:printOptions-barrelDetails ul li:has-text('All') a",
    ]
    
    # Reports navigation
    REPORTS_MENU = [
        "a#menuform\\:menu-reports-cs",  # Exact ID with escaped colon
        "a[id='menuform:menu-reports-cs']",  # ID with attribute selector
        "li.ui-menuitem a:has-text('Reports')",
        "a.ui-menuitem-link:has-text('Reports')",
    ]


# ============================================================================
# OLD UI SELECTORS (Echo2 framework based)
# ============================================================================

class OldUISelectors:
    """Selectors for the old/classic Vintrace UI (Echo2 framework)"""
    
    # Loader selectors
    LOADER_LONG = "#serverDelayMessageLong"
    LOADER_MAIN = "#serverDelayMessage"
    
    # Quick launch icons
    REPORTS_ICON = [
        "#c_170",
        "div[title='Reports']",
    ]
    
    # Report categories
    REPORT_CATEGORY_SPAN = "span[id$='|Text']"  # Pattern for category text elements
    
    # Report strips and controls
    REPORT_STRIP = "div.reportStrip"
    
    # Window controls
    WINDOW_CLOSE_BUTTON = [
        "div.echo2-window-pane-close",
        "div[id$='_close'].echo2-window-pane-close",
        "div.echo2-window-pane-close img[src*='close']",
    ]
    
    # Tables
    JX2_TABLE = "table.jx2table"
    
    # Generate buttons
    GENERATE_BUTTON = [
        "button:has-text('Generate')",
        "button:has-text('Generate...')",
        "input[type='button'][value*='Generate']",
        "button.inlineButton.positiveAction",
    ]
    
    # Checkbox patterns
    CHECKBOX_IMAGE = "img[src*='Checkbox']"
    CHECKBOX_STATE_ICON = "img[id*='stateicon']"
    
    # Date inputs
    DATE_INPUT = [
        "input.input-date",
        "input[type='text'][id*='c_']",
    ]


# ============================================================================
# LOGIN PAGE SELECTORS (Chakra UI)
# ============================================================================

class LoginSelectors:
    """Selectors for the login page"""
    
    # Login form fields
    EMAIL_INPUT = [
        "input#email",  # Primary ID
        "input[name='email'][type='email']",
        "input[placeholder='Enter email']",
        "input[type='email']",
    ]
    
    PASSWORD_INPUT = [
        "input#password",  # Primary ID
        "input[name='password'][type='password']",
        "input[placeholder='Enter password']",
        "input[type='password']",
    ]
    
    # Login button
    LOGIN_BUTTON = [
        "button[type='submit'].chakra-button:has-text('Login')",
        "button[type='submit']:has-text('Login')",
        "button.chakra-button:has-text('Login')",
        "button[type='submit']",
    ]
    
    # Tab navigation
    LOGIN_TAB = [
        'button[role="tab"][aria-selected="true"]:has-text("Login")',
        'button[role="tab"]:has-text("Login")',
    ]
    
    # Error indicators
    ERROR_INDICATORS = [
        "text='Invalid email or password'",
        "text='Login failed'",
        "text='Incorrect username or password'",
        "text='Invalid credentials'",
        "div[role='alert']",
        "#chakra-toast-manager-top >> text=/error|invalid|failed/i",
        ".chakra-alert--error",
    ]


# ============================================================================
# POPUP/MODAL SELECTORS
# ============================================================================

class PopupSelectors:
    """Selectors for popups, tours, and modals"""
    
    CLOSE_BUTTONS = [
        "button[data-role='end']",
        ".popover button[data-role='end']",
        ".tour button[data-role='end']",
        "button:has-text('End tour')",
        ".popover .close",
        ".modal .close",
        "button:has-text('Close')",
        "button:has-text('×')",
    ]


# ============================================================================
# REPORT SPECIFIC SELECTORS
# ============================================================================

class ReportSelectors:
    """Selectors specific to report configuration and generation"""
    
    # Report category navigation
    VINTAGE_HARVEST_TAB = [
        "span:text('Vintage/Harvest')",
        "div:text('Vintage/Harvest')",
        "td:text('Vintage/Harvest')",
        "tr:has-text('Vintage/Harvest')",
        "[id$='|Text']:text('Vintage/Harvest')",
    ]
    
    PRODUCT_ANALYSIS_CATEGORY = [
        "span:text('Product analysis')",
        "div:text('Product analysis')",
        "td:text('Product analysis')",
        "[id$='|Text']:text('Product analysis')",
    ]
    
    # Format selection
    FORMAT_DROPDOWN = "select"
    
    # Common checkboxes
    SHOW_ACTIVE_ONLY = [
        "div.checkbox-text:has-text('Show active only')",
        "table:has-text('Show active only') img[src*='Checkbox']",
        "*:has-text('Show active only')",
    ]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_selector_list(selector_class, attribute_name):
    """
    Get a list of selectors from a selector class attribute.
    
    Args:
        selector_class: The selector class (e.g., NewUISelectors)
        attribute_name: Name of the attribute containing selectors
        
    Returns:
        list: List of selectors, or single selector wrapped in list
    """
    selectors = getattr(selector_class, attribute_name, [])
    if isinstance(selectors, str):
        return [selectors]
    return selectors


def get_all_selectors_for_element(element_type: str, ui_version: str = "new"):
    """
    Get all possible selectors for a given element type.
    
    Args:
        element_type: Type of element (e.g., 'export_button', 'login_email')
        ui_version: UI version ('new' or 'old')
        
    Returns:
        list: List of selectors to try
    """
    element_map = {
        'new': {
            'export_button': NewUISelectors.EXPORT_BUTTON,
            'barrel_details_menu': NewUISelectors.BARREL_DETAILS_MENU_ITEM,
            'barrel_details_all': NewUISelectors.BARREL_DETAILS_ALL_OPTION,
            'reports_menu': NewUISelectors.REPORTS_MENU,
            'iframe': NewUISelectors.IFRAME_MAIN,
        },
        'old': {
            'reports_icon': OldUISelectors.REPORTS_ICON,
            'generate_button': OldUISelectors.GENERATE_BUTTON,
            'window_close': OldUISelectors.WINDOW_CLOSE_BUTTON,
        },
        'login': {
            'email': LoginSelectors.EMAIL_INPUT,
            'password': LoginSelectors.PASSWORD_INPUT,
            'button': LoginSelectors.LOGIN_BUTTON,
        }
    }
    
    return element_map.get(ui_version, {}).get(element_type, [])
