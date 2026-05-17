# AMD AI Developer Program - Auto Register & GPU Credits

Automated pipeline for AMD AI Developer Program: register accounts, activate, confirm opt-in, and request free GPU credits on AMD Developer Cloud.

## Features

- **Mass registration** — 100+ unique accounts per run
- **Browser fingerprinting** — each account gets unique timezone, locale, viewport, and user agent
- **Akamai bypass** — CloakBrowser stealth + residential proxy
- **Auto-activation** — fetches tokens from email (IMAP), activates via browser
- **GPU credit requests** — auto-fills Marketo form on DigitalOcean/AMD with realistic personas
- **Conditional form handling** — detects and fills dynamic fields (opensource project, corporation)
- **Config-based** — credentials in `config.json`, no hardcoded secrets

## Scripts

| Script | Step | Description |
|--------|------|-------------|
| `register.py` | 1 | Register accounts (bypasses Akamai Bot Manager) |
| `activate.py` | 2 | Fetch tokens from email + activate accounts |
| `verifyotc.py` | 3 | Confirm opt-in marketing emails |
| `credit_form.py` | 4 | Submit GPU credit request form (Marketo) |
| `fingerprints.py` | — | Browser fingerprint profiles (30 unique combos) |

## Requirements

- Python 3.10+
- CloakBrowser (`pip install cloakbrowser`)
- Residential proxy (for Akamai/bot detection bypass)
- IMAP access to catch-all email domain
- Xvfb running on `:99` (for headless browser)

## Setup

```bash
pip install cloakbrowser requests
```

Create `config.json`:

```json
{
  "domain": "yourdomain.com",
  "imap_email": "your-catchall@gmail.com",
  "imap_pass": "your-app-password",
  "password": "YourPassword10!",
  "proxy": {
    "server": "http://proxy:port",
    "username": "user",
    "password": "pass"
  }
}
```

## Usage

### Step 1: Register

```bash
python3 register.py --count 100
```

Outputs `amd_registered_<timestamp>.json`. Each account gets a unique browser fingerprint matched to its country.

### Step 2: Activate

Wait 1-2 minutes for activation emails, then:

```bash
python3 activate.py --input amd_registered_20260517.json
# or with wait
python3 activate.py --wait 60 --input amd_registered_20260517.json
# or specific emails
python3 activate.py --email "user1@domain.com,user2@domain.com"
```

### Step 3: Confirm Opt-In

Wait 5-15 minutes after activation:

```bash
python3 verifyotc.py --all
python3 verifyotc.py --email "user1@domain.com"
```

### Step 4: Request GPU Credits

```bash
python3 credit_form.py --input amd_registered_20260517.json
# skip already submitted
python3 credit_form.py --input amd_accounts.json --skip-done
# limit count
python3 credit_form.py --input amd_accounts.json --count 10
# custom delay
python3 credit_form.py --input amd_accounts.json --delay-min 8 --delay-max 15
```

### Full Pipeline

```bash
python3 register.py --count 50
# wait 2 min
python3 activate.py --wait 120 --input amd_registered_*.json
# wait 10 min
python3 verifyotc.py --all
# submit credit form
python3 credit_form.py --input amd_registered_*.json
```

## Browser Fingerprinting

Each account uses a unique browser profile via `fingerprints.py`:

- **30 fingerprint profiles** covering US, EU, Asia, LATAM, Middle East, Oceania
- **Timezone** matched to persona country (America/New_York, Europe/Paris, Asia/Tokyo, etc.)
- **Locale** matched (en-US, fr-FR, ja-JP, de-DE, etc.)
- **Viewport** randomized (1920x1080, 1440x900, 1366x768, 2560x1440, etc.)
- **User Agent** rotated (Chrome 124-127, Windows/Mac mix)
- **Platform** varied (Win32/MacIntel)

## GPU Credit Form Details

The credit form (`credit_form.py`) handles:

- **Marketo form** (ID 1908) with client-side checksum — must submit via browser JS
- **Progressive profiling** — conditional fields based on developer type:
  - "Member of opensource project" → asks for project name/link
  - "Member of a corporation" → asks for company name + business email
- **Auto-generated personas** with realistic use cases, outcomes, and technical details
- **Validation retry** — detects invalid fields and fixes them before resubmit

## Technical Notes

- AMD uses Akamai Bot Manager with crypto challenges — pure HTTP requests are blocked
- Registration flow: submit form → Akamai challenge (~30s) → form reappears → resubmit → success
- Activation tokens are 20 chars (alphanumeric + `-` and `_`)
- Password requires minimum 10 characters
- Opt-in confirmation is a simple HTTP GET to `visit.amd.com/dc/...` tracking link
- Credit form uses Marketo (munchkinId: 113-DTN-266) — requires browser-side JS submission
- Successful credit form submission redirects to `devcloud.amd.com/login`

## Disclaimer

For educational purposes only. Use responsibly.
