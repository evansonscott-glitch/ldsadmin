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

### 4. Point OpenClaw to Sam

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

### 5. Start Talking

Open a chat with Sam. He'll walk you through:
- Setting up your LDS account access
- Connecting your Google calendar, email, and drive
- Learning about your calling and what you need help with

## File Structure

```
├── SOUL.md           # Sam's personality and approach
├── AGENTS.md         # Operating instructions
├── BOOTSTRAP.md      # First-run onboarding (deletes itself after)
├── USER.md.template  # Your info (created during onboarding)
├── TOOLS.md.template # Credentials config (created during onboarding)
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
