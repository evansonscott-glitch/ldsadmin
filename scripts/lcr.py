#!/usr/bin/env python3
"""
LCR (Leader and Clerk Resources) integration for Sam.
Browser automation for Church tools.

Usage:
    python lcr.py login              # Test login, save session
    python lcr.py members            # Get member list
    python lcr.py callings           # Get callings/organizations  
    python lcr.py ministering        # Get ministering assignments
    python lcr.py action-items       # Get dashboard action items
    python lcr.py discover-calling   # Find user's calling
    
Requirements: 
    pip install playwright
    playwright install chromium

Note: LCR's UI changes periodically. If scripts break, selectors may need updating.
      Run with --debug flag to see browser and diagnose issues.
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: playwright required", file=sys.stderr)
    print("Run: pip install playwright && playwright install chromium", file=sys.stderr)
    sys.exit(1)

from common import get_lds_credentials

# URLs
LCR_BASE = "https://lcr.churchofjesuschrist.org"
LOGIN_URL = "https://id.churchofjesuschrist.org"

# Session storage path
SESSION_DIR = Path(__file__).parent.parent / ".sessions"
SESSION_FILE = SESSION_DIR / "lcr_session.json"

# Timeouts (ms)
DEFAULT_TIMEOUT = 45000
NAV_TIMEOUT = 90000
PAGE_LOAD_WAIT = 5  # seconds to wait after navigation


class LCRClient:
    """LCR browser automation client with session persistence."""
    
    def __init__(self, headless=True, debug=False):
        self.headless = headless
        self.debug = debug
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, *args):
        self.stop()
        
    def start(self):
        """Start browser with optional saved session."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=100 if self.debug else 0
        )
        
        # Try to load saved session
        if SESSION_FILE.exists():
            try:
                self.context = self.browser.new_context(
                    storage_state=str(SESSION_FILE)
                )
                if self.debug:
                    print("Loaded saved session", file=sys.stderr)
            except Exception as e:
                if self.debug:
                    print(f"Could not load session: {e}", file=sys.stderr)
                self.context = self.browser.new_context()
        else:
            self.context = self.browser.new_context()
            
        self.page = self.context.new_page()
        self.page.set_default_timeout(DEFAULT_TIMEOUT)
        
    def stop(self):
        """Close browser and save session."""
        if self.context:
            try:
                SESSION_DIR.mkdir(parents=True, exist_ok=True)
                self.context.storage_state(path=str(SESSION_FILE))
                if self.debug:
                    print("Saved session", file=sys.stderr)
            except Exception as e:
                if self.debug:
                    print(f"Could not save session: {e}", file=sys.stderr)
                    
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
            
    def is_logged_in(self):
        """Check if we're logged into LCR."""
        try:
            self.page.goto(LCR_BASE, timeout=NAV_TIMEOUT)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Check page title - LCR dashboard has specific title
            title = self.page.title()
            if "Leader and Clerk Resources" in title:
                return True
            
            # Also check for user-specific content on page
            content = self.page.content()
            if "Actions and Messages" in content or "Member List" in content:
                return True
                
            return False
        except Exception:
            return False
            
    def login(self):
        """Login to Church account."""
        creds = get_lds_credentials()
        
        if self.debug:
            print(f"Logging in as {creds['username']}...", file=sys.stderr)
            
        # Go to LCR which will redirect to login
        self.page.goto(LCR_BASE, timeout=NAV_TIMEOUT)
        self.page.wait_for_load_state("networkidle")
        
        # Check if already logged in - must check page content, not URL
        # (URL may contain lcr.churchofjesuschrist.org in redirect_uri param)
        title = self.page.title()
        if "Leader and Clerk Resources" in title:
            if self.debug:
                print("Already logged in (detected from page title)", file=sys.stderr)
            return True
            
        try:
            # Wait for and fill username
            # The Church uses Okta - look for the username field
            username_selectors = [
                'input[name="identifier"]',
                'input[name="username"]', 
                'input[id="okta-signin-username"]',
                'input[type="text"][autocomplete="username"]',
                '#username'
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = self.page.wait_for_selector(selector, timeout=5000)
                    if username_field:
                        break
                except PlaywrightTimeout:
                    continue
                    
            if not username_field:
                raise Exception("Could not find username field")
                
            username_field.fill(creds['username'])
            
            # Click next/submit
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'button:has-text("Next")',
                'button:has-text("Sign In")',
                '.button--primary'
            ]
            
            for selector in submit_selectors:
                try:
                    btn = self.page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        break
                except Exception:
                    continue
                    
            self.page.wait_for_load_state("networkidle")
            
            # Wait for and fill password
            password_selectors = [
                'input[name="credentials.passcode"]',
                'input[name="password"]',
                'input[id="okta-signin-password"]',
                'input[type="password"]',
                '#password'
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.page.wait_for_selector(selector, timeout=5000)
                    if password_field:
                        break
                except PlaywrightTimeout:
                    continue
                    
            if not password_field:
                raise Exception("Could not find password field")
                
            password_field.fill(creds['password'])
            
            # Submit password
            for selector in submit_selectors:
                try:
                    btn = self.page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        break
                except Exception:
                    continue
                    
            # Wait for LCR to load - check page content instead of URL
            # (OAuth redirects can be tricky with URL checks)
            import time
            time.sleep(3)  # Give OAuth redirect time to complete
            self.page.wait_for_load_state("networkidle", timeout=NAV_TIMEOUT)
            
            # Verify we're actually in LCR by checking page title/content
            title = self.page.title()
            if "Leader and Clerk Resources" in title:
                if self.debug:
                    print("Login successful", file=sys.stderr)
                return True
            
            # Check content as backup
            content = self.page.content()
            if "Actions and Messages" in content:
                if self.debug:
                    print("Login successful", file=sys.stderr)
                return True
                
            raise Exception(f"Login may have failed - unexpected page: {title}")
            
        except Exception as e:
            if self.debug:
                print(f"Login failed: {e}", file=sys.stderr)
                # Save screenshot for debugging
                self.page.screenshot(path="/tmp/lcr_login_failed.png")
                print("Screenshot saved to /tmp/lcr_login_failed.png", file=sys.stderr)
            raise
            
    def ensure_logged_in(self):
        """Ensure we're logged in, login if needed."""
        # Check current page first before navigating
        title = self.page.title()
        if "Leader and Clerk Resources" in title:
            return  # Already on LCR
            
        # Otherwise do full login
        self.login()
            
    def get_members(self):
        """Get member list."""
        import time
        self.ensure_logged_in()
        
        self.page.goto(f"{LCR_BASE}/records/member-list", timeout=NAV_TIMEOUT)
        self.page.wait_for_load_state("networkidle", timeout=NAV_TIMEOUT)
        time.sleep(PAGE_LOAD_WAIT)  # Extra wait for dynamic content
        
        # Wait for the member table to load - try multiple selectors
        table_loaded = False
        selectors_to_try = [
            'table tbody tr',
            '[data-testid="member-list"]',
            '.member-row',
            '[class*="member"]'
        ]
        
        for selector in selectors_to_try:
            try:
                self.page.wait_for_selector(selector, timeout=10000)
                table_loaded = True
                if self.debug:
                    print(f"Found members with selector: {selector}", file=sys.stderr)
                break
            except PlaywrightTimeout:
                continue
                
        if not table_loaded and self.debug:
            print("Warning: Could not find member table selector", file=sys.stderr)
                
        # Extract member data
        members = self.page.evaluate('''() => {
            const results = [];
            
            // Try multiple possible table structures
            const rows = document.querySelectorAll('table tbody tr, .member-row, [data-testid="member-row"]');
            
            rows.forEach(row => {
                const cells = row.querySelectorAll('td, .cell');
                const nameEl = row.querySelector('.member-name, td:first-child a, td:first-child');
                const phoneEl = row.querySelector('.phone, [data-field="phone"], td:nth-child(3)');
                const emailEl = row.querySelector('.email, [data-field="email"], td:nth-child(4)');
                
                const name = nameEl?.innerText?.trim() || '';
                if (name && name.length > 1) {
                    results.push({
                        name: name,
                        phone: phoneEl?.innerText?.trim() || '',
                        email: emailEl?.innerText?.trim() || ''
                    });
                }
            });
            
            return results;
        }''')
        
        return members
        
    def get_callings(self):
        """Get callings and organizations."""
        self.ensure_logged_in()
        
        self.page.goto(f"{LCR_BASE}/orgs/members-with-callings", timeout=NAV_TIMEOUT)
        self.page.wait_for_load_state("networkidle")
        
        # Wait for content
        try:
            self.page.wait_for_selector('.org-name, .organization, table', timeout=DEFAULT_TIMEOUT)
        except PlaywrightTimeout:
            pass
            
        orgs = self.page.evaluate('''() => {
            const results = [];
            
            // Try to find organization sections
            const sections = document.querySelectorAll('.organization-section, .org-card, [data-testid="organization"]');
            
            if (sections.length > 0) {
                sections.forEach(section => {
                    const orgName = section.querySelector('.org-name, h3, h4')?.innerText?.trim() || '';
                    const callings = [];
                    
                    section.querySelectorAll('.calling-row, .member-calling, tr').forEach(row => {
                        const calling = row.querySelector('.calling-name, td:first-child')?.innerText?.trim() || '';
                        const name = row.querySelector('.member-name, td:nth-child(2)')?.innerText?.trim() || '';
                        if (calling || name) {
                            callings.push({ calling, name });
                        }
                    });
                    
                    if (orgName || callings.length > 0) {
                        results.push({ organization: orgName, callings });
                    }
                });
            } else {
                // Fallback: try to parse any table
                const rows = document.querySelectorAll('table tbody tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        results.push({
                            organization: 'Unknown',
                            callings: [{
                                name: cells[0]?.innerText?.trim() || '',
                                calling: cells[1]?.innerText?.trim() || ''
                            }]
                        });
                    }
                });
            }
            
            return results;
        }''')
        
        return orgs
        
    def get_ministering(self):
        """Get ministering assignments."""
        self.ensure_logged_in()
        
        self.page.goto(f"{LCR_BASE}/ministering", timeout=NAV_TIMEOUT)
        self.page.wait_for_load_state("networkidle")
        
        # Wait for content
        try:
            self.page.wait_for_selector('.district, .companionship, table', timeout=DEFAULT_TIMEOUT)
        except PlaywrightTimeout:
            pass
            
        data = self.page.evaluate('''() => {
            const assignments = [];
            
            // Look for companionship sections
            const companionships = document.querySelectorAll('.companionship, .assignment-group, [data-testid="companionship"]');
            
            if (companionships.length > 0) {
                companionships.forEach(comp => {
                    const ministers = Array.from(comp.querySelectorAll('.minister, .companion-name'))
                        .map(el => el.innerText?.trim()).filter(Boolean);
                    const households = Array.from(comp.querySelectorAll('.household, .assignment'))
                        .map(el => el.innerText?.trim()).filter(Boolean);
                    
                    if (ministers.length > 0 || households.length > 0) {
                        assignments.push({ ministers, households });
                    }
                });
            }
            
            return assignments;
        }''')
        
        return data
        
    def get_action_items(self):
        """Get action items from dashboard."""
        self.ensure_logged_in()
        
        self.page.goto(LCR_BASE, timeout=NAV_TIMEOUT)
        self.page.wait_for_load_state("networkidle")
        
        items = self.page.evaluate('''() => {
            const results = [];
            
            // Look for action item cards/alerts
            const cards = document.querySelectorAll('.action-card, .alert, .notification, [data-testid="action-item"]');
            
            cards.forEach(card => {
                const title = card.querySelector('.title, h3, h4, .heading')?.innerText?.trim() || '';
                const desc = card.querySelector('.description, .body, p')?.innerText?.trim() || '';
                const count = card.querySelector('.count, .badge, .number')?.innerText?.trim() || '';
                
                if (title) {
                    results.push({ title, description: desc, count });
                }
            });
            
            return results;
        }''')
        
        return items
        
    def discover_calling(self):
        """Try to discover user's calling from LCR."""
        self.ensure_logged_in()
        
        # Only navigate if not already on LCR dashboard
        if "Leader and Clerk Resources" not in self.page.title():
            self.page.goto(LCR_BASE, timeout=NAV_TIMEOUT)
            self.page.wait_for_load_state("networkidle")
        
        info = self.page.evaluate('''() => {
            // Parse calling info from page content
            const body = document.body.innerText;
            const lines = body.split('\\n').map(l => l.trim()).filter(l => l);
            
            let calling = '';
            let name = '';
            let unit = '';
            
            // LCR shows format like:
            // Communication Specialist (2135280)
            // Lehi Utah Holbrook Farms Stake (2135280)
            // Scott Brandon Evanson
            // Communication Specialist
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                
                // Find name (usually has Evanson or similar family name)
                if (line.includes('Evanson') || (line.split(' ').length >= 2 && !line.includes('('))) {
                    if (!name && line.length < 50) name = line;
                }
                
                // Find unit (Stake or Ward)
                if ((line.includes('Stake') || line.includes('Ward')) && line.includes('(')) {
                    unit = line.replace(/\\s*\\(\\d+\\)/, '').trim();
                }
                
                // Find calling - look for common calling keywords
                const callingKeywords = ['Specialist', 'President', 'Counselor', 'Secretary', 
                                        'Clerk', 'Teacher', 'Leader', 'Director', 'Coordinator'];
                for (const kw of callingKeywords) {
                    if (line.includes(kw) && !line.includes('(') && !calling) {
                        calling = line;
                        break;
                    }
                }
            }
            
            return { 
                name,
                calling, 
                unit,
                pageTitle: document.title,
                url: window.location.href
            };
        }''')
        
        return info


def cmd_login(args):
    """Test login and save session."""
    with LCRClient(headless=not args.debug, debug=args.debug) as client:
        try:
            client.login()
            print(json.dumps({
                'status': 'success',
                'message': 'Login successful, session saved'
            }))
        except Exception as e:
            print(json.dumps({
                'status': 'error',
                'message': str(e)
            }))
            sys.exit(1)

def cmd_members(args):
    """Get member list."""
    with LCRClient(headless=not args.debug, debug=args.debug) as client:
        try:
            members = client.get_members()
            print(json.dumps(members, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            sys.exit(1)

def cmd_callings(args):
    """Get callings."""
    with LCRClient(headless=not args.debug, debug=args.debug) as client:
        try:
            callings = client.get_callings()
            print(json.dumps(callings, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            sys.exit(1)

def cmd_ministering(args):
    """Get ministering assignments."""
    with LCRClient(headless=not args.debug, debug=args.debug) as client:
        try:
            data = client.get_ministering()
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            sys.exit(1)

def cmd_action_items(args):
    """Get action items."""
    with LCRClient(headless=not args.debug, debug=args.debug) as client:
        try:
            items = client.get_action_items()
            print(json.dumps(items, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            sys.exit(1)

def cmd_discover_calling(args):
    """Discover user's calling."""
    with LCRClient(headless=not args.debug, debug=args.debug) as client:
        try:
            info = client.discover_calling()
            print(json.dumps(info, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='LCR integration for Sam')
    parser.add_argument('--debug', action='store_true', help='Show browser, verbose output')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # login
    login_parser = subparsers.add_parser('login', help='Test login')
    login_parser.set_defaults(func=cmd_login)
    
    # members
    members_parser = subparsers.add_parser('members', help='Get member list')
    members_parser.set_defaults(func=cmd_members)
    
    # callings
    callings_parser = subparsers.add_parser('callings', help='Get callings')
    callings_parser.set_defaults(func=cmd_callings)
    
    # ministering
    ministering_parser = subparsers.add_parser('ministering', help='Get ministering')
    ministering_parser.set_defaults(func=cmd_ministering)
    
    # action-items
    action_parser = subparsers.add_parser('action-items', help='Get action items')
    action_parser.set_defaults(func=cmd_action_items)
    
    # discover-calling
    discover_parser = subparsers.add_parser('discover-calling', help='Discover calling')
    discover_parser.set_defaults(func=cmd_discover_calling)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
