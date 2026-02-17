# Sam — LDS Calling Assistant

Sam helps members of The Church of Jesus Christ of Latter-day Saints manage their callings more effectively. He handles the administrative work so you can focus on the ministry.

## What Sam Does

- **Discovers your calling** by logging into your Church account
- **Connects to your calendar, email, and drive** to help with scheduling and coordination
- **Learns what's fulfilling vs. tedious** about your calling — handles the admin, leaves you the meaningful stuff
- **Drafts agendas, sends reminders, tracks action items** for any meetings you run
- **Answers questions** about Church policies, handbooks, and procedures

## Quick Start

### 1. Install OpenClaw

Follow the setup guide at [openclaw.ai](https://openclaw.ai)

### 2. Clone This Repo

```bash
git clone https://github.com/YOUR_USERNAME/sam-lds-assistant.git
cd sam-lds-assistant
```

### 3. Set Up Credentials

```bash
cp .env.example .env
# Edit .env with your credentials (see setup/google-setup.md)
chmod 600 .env
```

### 4. Install Script Dependencies

```bash
cd scripts
pip install -r requirements.txt
playwright install chromium  # For LCR browser automation
```

### 5. Point OpenClaw to Sam

Add Sam as an agent in your `openclaw.json`:

```json
{
  "agents": {
    "sam": {
      "workspaceDir": "/path/to/sam-lds-assistant"
    }
  }
}
```

### 6. Start Talking

Open a chat with Sam. He'll walk you through:
- Setting up your LDS account access
- Connecting your Google calendar, email, and drive
- Learning about your calling and what you need help with

## Integration Scripts

Sam comes with ready-to-use integration scripts:

### Gmail (`scripts/gmail.py`)
```bash
python scripts/gmail.py inbox --limit 10      # Fetch recent emails
python scripts/gmail.py inbox --unread        # Unread only
python scripts/gmail.py search "ward council" # Search emails
python scripts/gmail.py read <uid>            # Read specific email
python scripts/gmail.py draft --to "..." --subject "..." --body "..."
python scripts/gmail.py drafts                # List drafts
```

### Calendar (`scripts/gcal.py`)
```bash
python scripts/gcal.py today              # Today's events
python scripts/gcal.py week               # This week
python scripts/gcal.py list --days 30     # Next 30 days
python scripts/gcal.py create --title "Ward Council" --start "2026-03-01 08:00" --end "2026-03-01 09:00"
```

### LCR (`scripts/lcr.py`)
```bash
python scripts/lcr.py members                 # Member list
python scripts/lcr.py callings                # Callings/orgs
python scripts/lcr.py ministering             # Ministering assignments
python scripts/lcr.py action-items            # Dashboard to-dos
python scripts/lcr.py discover-calling        # Find user's calling
```

All scripts output JSON for easy parsing by Sam.

## File Structure

```
├── SOUL.md           # Sam's personality and approach
├── AGENTS.md         # Operating instructions
├── BOOTSTRAP.md      # First-run onboarding (deletes itself after)
├── USER.md.template  # Your info (created during onboarding)
├── TOOLS.md.template # Credentials config (created during onboarding)
├── scripts/
│   ├── common.py         # Shared utilities, .env loading
│   ├── gmail.py          # Gmail IMAP integration
│   ├── gcal.py       # Google Calendar integration
│   ├── lcr.py            # LCR browser automation
│   └── requirements.txt  # Python dependencies
├── setup/
│   └── google-setup.md   # Google service account walkthrough
└── skills/
    └── meetings/
        └── SKILL.md      # Meeting effectiveness skill
```

## Troubleshooting

### LCR Issues
- **Timeout errors**: Church login can be slow. Try again or check your internet.
- **"Display not set"**: The `--debug` flag opens a visible browser window. On servers without a display, omit `--debug` to run headless.
- **Login loop**: Delete `.sessions/lcr_session.json` and try again.
- **Selectors changed**: LCR's UI updates periodically. Open an issue if scripts break.

### Google API Issues
- **"Service account not found"**: Make sure `credentials/google-service-account.json` exists.
- **"Insufficient permission"**: Enable the Gmail/Calendar API in Google Cloud Console.
- **Calendar not showing**: Share your calendar with the service account email (found in the JSON).

### General
- Check `.env` has all required values (compare with `.env.example`)
- Run scripts directly with `python scripts/xyz.py` to see raw errors
- Update dependencies: `pip install -r scripts/requirements.txt --upgrade`

## Privacy & Security

- Credentials stored in `.env` (local only, never committed)
- `.gitignore` excludes `.env`, `credentials/`, and all sensitive files
- Run `chmod 600 .env` to restrict file permissions
- Sam only accesses what you explicitly grant

**Enable the credential safety hook:**
```bash
git config core.hooksPath .githooks
```
This blocks commits containing plaintext passwords in JSON files.

## Contributing

PRs welcome! Ideas for improvements:
- Additional skills for specific callings
- Better handbook integration
- Stake-level coordination features

## License

MIT — use freely, help others serve.
