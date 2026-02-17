#!/usr/bin/env python3
"""
LCR (Leader and Clerk Resources) integration for Sam.
Browser automation for Church tools.

Usage:
    python lcr.py members [--unit UNIT_NUMBER]
    python lcr.py callings [--org ORG_NAME]
    python lcr.py ministering
    python lcr.py action-items
    
Note: Requires playwright. Install with: pip install playwright && playwright install chromium
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright required", file=sys.stderr)
    print("Run: pip install playwright && playwright install chromium", file=sys.stderr)
    sys.exit(1)

from common import get_lds_credentials

LCR_URL = "https://lcr.churchofjesuschrist.org"
LOGIN_URL = "https://id.churchofjesuschrist.org"

def create_browser(headless=True):
    """Create browser instance."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return playwright, browser, page

def login(page):
    """Login to Church account."""
    creds = get_lds_credentials()
    
    page.goto(LOGIN_URL)
    time.sleep(2)
    
    # Enter username
    page.fill('input[name="username"]', creds['username'])
    page.click('button[type="submit"]')
    time.sleep(2)
    
    # Enter password
    page.fill('input[name="password"]', creds['password'])
    page.click('button[type="submit"]')
    time.sleep(3)
    
    # Wait for redirect to LCR or home
    page.wait_for_load_state('networkidle')
    
    return True

def cmd_members(args):
    """Get member list."""
    playwright, browser, page = create_browser()
    
    try:
        login(page)
        page.goto(f"{LCR_URL}/records/member-list")
        time.sleep(3)
        
        # Wait for member table to load
        page.wait_for_selector('table', timeout=10000)
        
        # Extract member data
        members = page.evaluate('''() => {
            const rows = document.querySelectorAll('table tbody tr');
            return Array.from(rows).map(row => {
                const cells = row.querySelectorAll('td');
                return {
                    name: cells[0]?.innerText || '',
                    age: cells[1]?.innerText || '',
                    phone: cells[2]?.innerText || '',
                    email: cells[3]?.innerText || ''
                };
            }).filter(m => m.name);
        }''')
        
        print(json.dumps(members, indent=2))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
    finally:
        browser.close()
        playwright.stop()

def cmd_callings(args):
    """Get callings/organizations."""
    playwright, browser, page = create_browser()
    
    try:
        login(page)
        page.goto(f"{LCR_URL}/orgs/callings-and-டகளிங்ஸ்")
        time.sleep(3)
        
        # Get organization structure
        orgs = page.evaluate('''() => {
            const orgElements = document.querySelectorAll('.organization-card, .org-item');
            return Array.from(orgElements).map(org => {
                const name = org.querySelector('.org-name, h3, h4')?.innerText || '';
                const members = Array.from(org.querySelectorAll('.member-item, .calling-item')).map(m => ({
                    calling: m.querySelector('.calling-name')?.innerText || '',
                    name: m.querySelector('.member-name')?.innerText || ''
                }));
                return { organization: name, callings: members };
            });
        }''')
        
        print(json.dumps(orgs, indent=2))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
    finally:
        browser.close()
        playwright.stop()

def cmd_ministering(args):
    """Get ministering assignments."""
    playwright, browser, page = create_browser()
    
    try:
        login(page)
        page.goto(f"{LCR_URL}/ministering")
        time.sleep(3)
        
        # Get ministering data
        data = page.evaluate('''() => {
            const assignments = [];
            const sections = document.querySelectorAll('.district-section, .companionship');
            
            sections.forEach(section => {
                const ministers = section.querySelectorAll('.minister-name');
                const households = section.querySelectorAll('.household-name');
                
                assignments.push({
                    ministers: Array.from(ministers).map(m => m.innerText),
                    households: Array.from(households).map(h => h.innerText)
                });
            });
            
            return assignments;
        }''')
        
        print(json.dumps(data, indent=2))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
    finally:
        browser.close()
        playwright.stop()

def cmd_action_items(args):
    """Get action items/to-dos from LCR dashboard."""
    playwright, browser, page = create_browser()
    
    try:
        login(page)
        page.goto(LCR_URL)
        time.sleep(3)
        
        # Get action items from dashboard
        items = page.evaluate('''() => {
            const actionItems = [];
            const cards = document.querySelectorAll('.action-item, .todo-item, .alert-card');
            
            cards.forEach(card => {
                const title = card.querySelector('.title, h3, h4')?.innerText || '';
                const desc = card.querySelector('.description, .body, p')?.innerText || '';
                const count = card.querySelector('.count, .badge')?.innerText || '';
                
                if (title) {
                    actionItems.push({ title, description: desc, count });
                }
            });
            
            return actionItems;
        }''')
        
        print(json.dumps(items, indent=2))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
    finally:
        browser.close()
        playwright.stop()

def cmd_discover_calling(args):
    """Discover user's current calling from LCR."""
    playwright, browser, page = create_browser()
    
    try:
        login(page)
        page.goto(f"{LCR_URL}")
        time.sleep(3)
        
        # Try to find user's calling from the dashboard or profile
        calling_info = page.evaluate('''() => {
            // Look for calling info in various places
            const callingElements = document.querySelectorAll('.my-calling, .current-calling, .user-calling');
            const sidebarItems = document.querySelectorAll('.sidebar .calling, nav .calling');
            const dashboardItems = document.querySelectorAll('.dashboard-card .calling');
            
            let calling = '';
            let organization = '';
            
            // Check each possible location
            for (const el of [...callingElements, ...sidebarItems, ...dashboardItems]) {
                const text = el.innerText?.trim();
                if (text && text.length > 2) {
                    calling = text;
                    break;
                }
            }
            
            // Also check permissions/role indicators
            const roleIndicators = document.querySelectorAll('[class*="role"], [class*="permission"]');
            const roles = Array.from(roleIndicators).map(r => r.innerText).filter(r => r);
            
            return { calling, roles, raw: document.title };
        }''')
        
        print(json.dumps(calling_info, indent=2))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
    finally:
        browser.close()
        playwright.stop()

def main():
    parser = argparse.ArgumentParser(description='LCR integration for Sam')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # members
    members_parser = subparsers.add_parser('members', help='Get member list')
    members_parser.add_argument('--unit', help='Unit number')
    members_parser.set_defaults(func=cmd_members)
    
    # callings
    callings_parser = subparsers.add_parser('callings', help='Get callings')
    callings_parser.add_argument('--org', help='Organization name filter')
    callings_parser.set_defaults(func=cmd_callings)
    
    # ministering
    ministering_parser = subparsers.add_parser('ministering', help='Get ministering assignments')
    ministering_parser.set_defaults(func=cmd_ministering)
    
    # action-items
    action_parser = subparsers.add_parser('action-items', help='Get action items')
    action_parser.set_defaults(func=cmd_action_items)
    
    # discover-calling
    discover_parser = subparsers.add_parser('discover-calling', help='Discover user calling')
    discover_parser.set_defaults(func=cmd_discover_calling)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
