#!/usr/bin/env python3
"""
Google Calendar integration for Sam.
Uses service account for read/write access.

Usage:
    python gcal.py list [--days N]
    python gcal.py today
    python gcal.py week
    python gcal.py create --title "title" --start "YYYY-MM-DD HH:MM" --end "YYYY-MM-DD HH:MM" [--desc "description"]
    python gcal.py delete <event_id>
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    print("Error: google-auth and google-api-python-client required", file=sys.stderr)
    print("Run: pip install google-auth google-api-python-client", file=sys.stderr)
    sys.exit(1)

from common import get_google_service_account, get_env

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Get authenticated Calendar service."""
    sa_path = get_google_service_account()
    
    # Resolve relative path
    if not Path(sa_path).is_absolute():
        sa_path = Path(__file__).parent.parent / sa_path
    
    if not Path(sa_path).exists():
        print(f"Error: Service account file not found: {sa_path}", file=sys.stderr)
        sys.exit(1)
    
    credentials = service_account.Credentials.from_service_account_file(
        sa_path, scopes=SCOPES
    )
    
    return build('calendar', 'v3', credentials=credentials)

def get_calendar_id():
    """Get the calendar ID to use (from env or default)."""
    return get_env('GOOGLE_CALENDAR_ID', required=False) or 'primary'

def format_event(event):
    """Format event for output."""
    start = event.get('start', {})
    end = event.get('end', {})
    
    # Handle all-day vs. timed events
    start_time = start.get('dateTime', start.get('date', ''))
    end_time = end.get('dateTime', end.get('date', ''))
    
    return {
        'id': event.get('id'),
        'title': event.get('summary', '(No title)'),
        'start': start_time,
        'end': end_time,
        'location': event.get('location', ''),
        'description': event.get('description', ''),
        'link': event.get('htmlLink', '')
    }

def cmd_list(args):
    """List upcoming events."""
    service = get_calendar_service()
    calendar_id = get_calendar_id()
    
    now = datetime.now(timezone.utc)
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=args.days)).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        maxResults=50,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    formatted = [format_event(e) for e in events]
    
    print(json.dumps(formatted, indent=2))

def cmd_today(args):
    """List today's events."""
    service = get_calendar_service()
    calendar_id = get_calendar_id()
    
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_of_day.isoformat() + 'Z',
        timeMax=end_of_day.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    formatted = [format_event(e) for e in events]
    
    print(json.dumps(formatted, indent=2))

def cmd_week(args):
    """List this week's events."""
    args.days = 7
    cmd_list(args)

def cmd_create(args):
    """Create a calendar event."""
    service = get_calendar_service()
    calendar_id = get_calendar_id()
    
    # Parse times
    try:
        start_dt = datetime.strptime(args.start, '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(args.end, '%Y-%m-%d %H:%M')
    except ValueError:
        print(json.dumps({
            'status': 'error',
            'message': 'Invalid date format. Use YYYY-MM-DD HH:MM'
        }))
        return
    
    event = {
        'summary': args.title,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': get_env('TIMEZONE', required=False) or 'America/Denver',
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': get_env('TIMEZONE', required=False) or 'America/Denver',
        },
    }
    
    if args.desc:
        event['description'] = args.desc
    
    if args.location:
        event['location'] = args.location
    
    created = service.events().insert(calendarId=calendar_id, body=event).execute()
    
    print(json.dumps({
        'status': 'success',
        'event': format_event(created)
    }, indent=2))

def cmd_delete(args):
    """Delete a calendar event."""
    service = get_calendar_service()
    calendar_id = get_calendar_id()
    
    try:
        service.events().delete(calendarId=calendar_id, eventId=args.event_id).execute()
        print(json.dumps({
            'status': 'success',
            'message': f'Event {args.event_id} deleted'
        }))
    except Exception as e:
        print(json.dumps({
            'status': 'error',
            'message': str(e)
        }))

def cmd_test(args):
    """Test Calendar API connection."""
    try:
        service = get_calendar_service()
        calendar_id = get_calendar_id()
        
        # Try to get calendar info
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        
        print(json.dumps({
            'status': 'success',
            'calendar': calendar.get('summary', calendar_id),
            'timezone': calendar.get('timeZone', 'Unknown'),
            'message': 'Calendar connection working'
        }, indent=2))
        
    except Exception as e:
        print(json.dumps({
            'status': 'error',
            'message': str(e)
        }))
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Google Calendar integration for Sam')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # list
    list_parser = subparsers.add_parser('list', help='List upcoming events')
    list_parser.add_argument('--days', type=int, default=14, help='Days ahead to show')
    list_parser.set_defaults(func=cmd_list)
    
    # today
    today_parser = subparsers.add_parser('today', help="Today's events")
    today_parser.set_defaults(func=cmd_today)
    
    # week
    week_parser = subparsers.add_parser('week', help="This week's events")
    week_parser.set_defaults(func=cmd_week)
    
    # create
    create_parser = subparsers.add_parser('create', help='Create event')
    create_parser.add_argument('--title', required=True, help='Event title')
    create_parser.add_argument('--start', required=True, help='Start time (YYYY-MM-DD HH:MM)')
    create_parser.add_argument('--end', required=True, help='End time (YYYY-MM-DD HH:MM)')
    create_parser.add_argument('--desc', help='Description')
    create_parser.add_argument('--location', help='Location')
    create_parser.set_defaults(func=cmd_create)
    
    # delete
    delete_parser = subparsers.add_parser('delete', help='Delete event')
    delete_parser.add_argument('event_id', help='Event ID')
    delete_parser.set_defaults(func=cmd_delete)
    
    # test
    test_parser = subparsers.add_parser('test', help='Test connection')
    test_parser.set_defaults(func=cmd_test)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
