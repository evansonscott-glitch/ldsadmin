# Google Service Account Setup

This guide walks you through setting up read-only access to your Google Calendar, Email, and Drive so Sam can help manage your calling.

**Time required:** ~10 minutes

---

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown (top left) → **New Project**
3. Name it something like "Sam Assistant"
4. Click **Create**

---

## Step 2: Enable APIs

In your new project:

1. Go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Google Calendar API**
   - **Google Drive API**
   - **Gmail API**

---

## Step 3: Create a Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Name it "sam-assistant"
4. Click **Create and Continue**
5. Skip the optional steps, click **Done**

---

## Step 4: Download the Key

1. Click on your new service account
2. Go to the **Keys** tab
3. Click **Add Key** → **Create New Key**
4. Choose **JSON**
5. Save the downloaded file — this is your service account credentials

---

## Step 5: Share Your Calendar

1. Open [Google Calendar](https://calendar.google.com)
2. Find your calendar in the left sidebar
3. Click the three dots → **Settings and sharing**
4. Scroll to **Share with specific people**
5. Click **Add people**
6. Paste the service account email (looks like `sam-assistant@your-project.iam.gserviceaccount.com`)
7. Set permission to **See all event details**
8. Click **Send**

---

## Step 6: Set Up Gmail Access (IMAP)

Service accounts can't access personal Gmail directly, so we use IMAP with an App Password:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already on
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** and your device
5. Click **Generate**
6. Copy the 16-character password

You'll add this to your `.env` file in Step 8.

---

## Step 7: Share Drive Folders (Optional)

If you have ward/stake documents in Google Drive:

1. Right-click the folder → **Share**
2. Add the service account email
3. Set to **Viewer**

---

## Step 8: Configure Your Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```bash
   # Gmail IMAP Access
   GMAIL_EMAIL=your.email@gmail.com
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   
   # Google Service Account
   GOOGLE_SERVICE_ACCOUNT_PATH=./credentials/google-service-account.json
   ```

3. Move your service account JSON (from Step 4) to `credentials/`:
   ```bash
   mv ~/Downloads/your-project-xxxxx.json ./credentials/google-service-account.json
   ```

4. Lock down permissions:
   ```bash
   chmod 600 .env
   chmod 600 credentials/*
   ```

**⚠️ Never commit `.env` or `credentials/` to git** — they're already in `.gitignore`.

Sam will read from these and test the connections.

---

## Troubleshooting

**"Access denied" errors:**
- Make sure you shared your calendar with the exact service account email
- Check that the APIs are enabled in your project

**Gmail not connecting:**
- Verify 2-Step Verification is enabled
- Make sure you're using an App Password, not your regular password
- Check for typos in the email address

**Need help?**
Ask Sam — he can walk you through any step that's unclear.
