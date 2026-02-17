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

### Calendar (`scripts/calendar.py`)
```bash
python scripts/calendar.py today              # Today's events
python scripts/calendar.py week               # This week
python scripts/calendar.py list --days 30     # Next 30 days
python scripts/calendar.py create --title "Ward Council" --start "2026-03-01 08:00" --end "2026-03-01 09:00"
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
│   ├── calendar.py       # Google Calendar integration
│   ├── lcr.py            # LCR browser automation
│   └── requirements.txt  # Python dependencies
├── setup/
│   └── google-setup.md   # Google service account walkthrough
└── skills/
    └── meetings/
        └── SKILL.md      # Meeting effectiveness skill
```

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
