#!/usr/bin/env python3
"""
Gmail integration for Sam.
Uses IMAP for reading and SMTP for sending drafts.

Usage:
    python gmail.py inbox [--limit N] [--unread]
    python gmail.py search "query"
    python gmail.py read <message_id>
    python gmail.py draft --to "email" --subject "subject" --body "body"
    python gmail.py drafts
    python gmail.py test  # Test connection
"""

import argparse
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime
import json
import sys

from common import get_gmail_config


class GmailError(Exception):
    """Gmail-specific error."""
    pass


def connect_imap():
    """Connect to Gmail IMAP server with error handling."""
    config = get_gmail_config()
    try:
        imap = imaplib.IMAP4_SSL(config['imap_server'])
        imap.login(config['email'], config['password'])
        return imap
    except imaplib.IMAP4.error as e:
        raise GmailError(f"IMAP login failed: {e}. Check your email and app password.")
    except Exception as e:
        raise GmailError(f"Could not connect to Gmail: {e}")

def decode_subject(subject):
    """Decode email subject header."""
    if subject is None:
        return "(No Subject)"
    decoded = decode_header(subject)
    parts = []
    for content, charset in decoded:
        if isinstance(content, bytes):
            parts.append(content.decode(charset or 'utf-8', errors='replace'))
        else:
            parts.append(content)
    return ''.join(parts)

def parse_email(msg):
    """Parse email message into dict."""
    subject = decode_subject(msg.get('Subject'))
    from_addr = msg.get('From', '')
    to_addr = msg.get('To', '')
    date = msg.get('Date', '')
    message_id = msg.get('Message-ID', '')
    
    # Get body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='replace')
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode('utf-8', errors='replace')
    
    return {
        'message_id': message_id,
        'subject': subject,
        'from': from_addr,
        'to': to_addr,
        'date': date,
        'body': body[:2000] + ('...' if len(body) > 2000 else '')
    }

def cmd_inbox(args):
    """Fetch inbox messages."""
    imap = connect_imap()
    imap.select('INBOX')
    
    criteria = 'UNSEEN' if args.unread else 'ALL'
    _, message_numbers = imap.search(None, criteria)
    
    nums = message_numbers[0].split()
    if args.limit:
        nums = nums[-args.limit:]
    
    messages = []
    for num in reversed(nums):
        _, msg_data = imap.fetch(num, '(RFC822)')
        email_body = msg_data[0][1]
        msg = email.message_from_bytes(email_body)
        parsed = parse_email(msg)
        parsed['uid'] = num.decode()
        messages.append(parsed)
    
    imap.logout()
    
    print(json.dumps(messages, indent=2))

def cmd_search(args):
    """Search emails."""
    imap = connect_imap()
    imap.select('INBOX')
    
    # Gmail search syntax
    _, message_numbers = imap.search(None, f'(SUBJECT "{args.query}")')
    
    nums = message_numbers[0].split()[-20:]  # Last 20 matches
    
    messages = []
    for num in reversed(nums):
        _, msg_data = imap.fetch(num, '(RFC822)')
        email_body = msg_data[0][1]
        msg = email.message_from_bytes(email_body)
        parsed = parse_email(msg)
        parsed['uid'] = num.decode()
        messages.append(parsed)
    
    imap.logout()
    
    print(json.dumps(messages, indent=2))

def cmd_read(args):
    """Read a specific email by UID."""
    imap = connect_imap()
    imap.select('INBOX')
    
    _, msg_data = imap.fetch(args.uid.encode(), '(RFC822)')
    if msg_data[0] is None:
        print(json.dumps({'error': f'Message {args.uid} not found'}))
        return
    
    email_body = msg_data[0][1]
    msg = email.message_from_bytes(email_body)
    parsed = parse_email(msg)
    parsed['uid'] = args.uid
    # Get full body for single message
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    parsed['body'] = payload.decode('utf-8', errors='replace')
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            parsed['body'] = payload.decode('utf-8', errors='replace')
    
    imap.logout()
    
    print(json.dumps(parsed, indent=2))

def cmd_draft(args):
    """Create a draft email (saves to Drafts folder)."""
    config = get_gmail_config()
    
    msg = MIMEMultipart()
    msg['From'] = config['email']
    msg['To'] = args.to
    msg['Subject'] = args.subject
    msg.attach(MIMEText(args.body, 'plain'))
    
    # Connect to IMAP and save to Drafts
    imap = connect_imap()
    imap.select('[Gmail]/Drafts')
    
    result = imap.append(
        '[Gmail]/Drafts',
        '\\Draft',
        None,
        msg.as_bytes()
    )
    
    imap.logout()
    
    if result[0] == 'OK':
        print(json.dumps({
            'status': 'success',
            'message': f'Draft created: "{args.subject}" to {args.to}'
        }))
    else:
        print(json.dumps({
            'status': 'error',
            'message': f'Failed to create draft: {result}'
        }))

def cmd_drafts(args):
    """List drafts."""
    try:
        imap = connect_imap()
        imap.select('[Gmail]/Drafts')
        
        _, message_numbers = imap.search(None, 'ALL')
        nums = message_numbers[0].split()[-10:]  # Last 10 drafts
        
        drafts = []
        for num in reversed(nums):
            _, msg_data = imap.fetch(num, '(RFC822)')
            if msg_data[0]:
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)
                parsed = parse_email(msg)
                parsed['uid'] = num.decode()
                drafts.append(parsed)
        
        imap.logout()
        
        print(json.dumps(drafts, indent=2))
    except GmailError as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': f'Unexpected error: {e}'}))
        sys.exit(1)

def cmd_test(args):
    """Test Gmail connection."""
    try:
        config = get_gmail_config()
        print(f"Testing connection for {config['email']}...", file=sys.stderr)
        
        imap = connect_imap()
        status, folders = imap.list()
        
        if status == 'OK':
            imap.select('INBOX')
            _, messages = imap.search(None, 'ALL')
            count = len(messages[0].split()) if messages[0] else 0
            imap.logout()
            
            print(json.dumps({
                'status': 'success',
                'email': config['email'],
                'inbox_count': count,
                'message': 'Gmail connection working'
            }, indent=2))
        else:
            print(json.dumps({
                'status': 'error',
                'message': 'Could not list folders'
            }))
            sys.exit(1)
            
    except GmailError as e:
        print(json.dumps({'status': 'error', 'message': str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'status': 'error', 'message': f'Unexpected error: {e}'}))
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Gmail integration for Sam')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # inbox
    inbox_parser = subparsers.add_parser('inbox', help='Fetch inbox')
    inbox_parser.add_argument('--limit', type=int, default=10, help='Number of messages')
    inbox_parser.add_argument('--unread', action='store_true', help='Only unread')
    inbox_parser.set_defaults(func=cmd_inbox)
    
    # search
    search_parser = subparsers.add_parser('search', help='Search emails')
    search_parser.add_argument('query', help='Search query')
    search_parser.set_defaults(func=cmd_search)
    
    # read
    read_parser = subparsers.add_parser('read', help='Read specific email')
    read_parser.add_argument('uid', help='Message UID')
    read_parser.set_defaults(func=cmd_read)
    
    # draft
    draft_parser = subparsers.add_parser('draft', help='Create draft')
    draft_parser.add_argument('--to', required=True, help='Recipient')
    draft_parser.add_argument('--subject', required=True, help='Subject')
    draft_parser.add_argument('--body', required=True, help='Body text')
    draft_parser.set_defaults(func=cmd_draft)
    
    # drafts
    drafts_parser = subparsers.add_parser('drafts', help='List drafts')
    drafts_parser.set_defaults(func=cmd_drafts)
    
    # test
    test_parser = subparsers.add_parser('test', help='Test connection')
    test_parser.set_defaults(func=cmd_test)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
