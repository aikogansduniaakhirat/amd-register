#!/usr/bin/env python3
"""
AMD AI Developer Program - Step 2: Activate accounts
Fetches activation tokens from email (IMAP), then activates via browser.
Each activation uses a unique browser fingerprint.

Usage:
  python3 activate.py --input amd_registered_20260516.json
  python3 activate.py --email "user1@domain.com,user2@domain.com"
  python3 activate.py --wait 60 --input file.json
"""
import asyncio
import cloakbrowser
import os
import sys
import json
import random
import re
import imaplib
import email
import html as htmlmod
from datetime import datetime
from fingerprints import get_fingerprint

sys.stdout.reconfigure(line_buffering=True)
os.environ["DISPLAY"] = os.environ.get("DISPLAY", ":99")

# ============ CONFIG ============
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    IMAP_EMAIL = cfg["imap_email"]
    IMAP_PASS = cfg["imap_pass"]
    PASSWORD = cfg["password"]
    PROXY = cfg["proxy"]
else:
    IMAP_EMAIL = os.environ.get("IMAP_EMAIL", "")
    IMAP_PASS = os.environ.get("IMAP_PASS", "")
    PASSWORD = os.environ.get("AMD_PASSWORD", "YourPassword10!")
    PROXY = {
        "server": os.environ.get("PROXY_SERVER", "http://proxy:port"),
        "username": os.environ.get("PROXY_USER", ""),
        "password": os.environ.get("PROXY_PASS", "")
    }

ACTIVATE_URL = "https://www.amd.com/en/registration/activate-account.html"


# ============ STEP 1: GET TOKENS FROM EMAIL ============
def get_activation_tokens(emails):
    """Fetch activation tokens from IMAP."""
    print(f"\n=== Fetching activation tokens ===")
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(IMAP_EMAIL, IMAP_PASS)
    mail.select('INBOX')

    tokens = {}

    for email_addr in emails:
        status, messages = mail.search(None, 'TO', f'"{email_addr}"', 'SUBJECT', '"activate"')
        msg_ids = messages[0].split()

        if not msg_ids:
            print(f"  {email_addr}: no activation email yet")
            continue

        status, data = mail.fetch(msg_ids[-1], '(RFC822)')
        msg = email.message_from_bytes(data[0][1])

        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                elif part.get_content_type() == 'text/plain' and not body:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        clean = re.sub(r'<[^>]+>', '|||', body)
        clean = htmlmod.unescape(clean)
        m = re.search(r'Token is:\s*\|*\s*([A-Za-z0-9_\-]{5,30})', clean)
        if m:
            tokens[email_addr] = m.group(1)
            print(f"  {email_addr}: {m.group(1)}")
        else:
            print(f"  {email_addr}: token not found in email")

    mail.logout()
    return tokens


# ============ STEP 2: ACTIVATE ACCOUNTS ============
async def activate_batch(tokens):
    """Activate accounts with token + password. Each gets unique fingerprint."""
    print(f"\n=== Activating {len(tokens)} accounts ===")
    results = []

    for idx, (email_addr, token) in enumerate(tokens.items()):
        print(f"\n[ACT {idx+1}/{len(tokens)}] {email_addr}")

        # Unique fingerprint per activation
        fp = get_fingerprint(index=idx + 100)
        print(f"  🖥️  {fp['timezone']} | {fp['locale']} | {fp['viewport']['width']}x{fp['viewport']['height']}")

        browser = await cloakbrowser.launch_async(
            headless=True,
            args=['--no-sandbox', '--disable-gpu'],
            proxy=PROXY,
            timezone=fp['timezone'],
            locale=fp['locale']
        )
        page = await browser.new_page()
        await page.set_viewport_size(fp['viewport'])

        try:
            await page.goto(ACTIVATE_URL, wait_until='load', timeout=60000)
            await page.wait_for_selector('#form-text-30246375', state='visible', timeout=30000)

            await page.evaluate('() => { const b = document.getElementById("onetrust-accept-btn-handler"); if(b) b.click(); }')
            await page.wait_for_timeout(2000)

            # Fill activation form
            await page.fill('#form-text-30246375', token)
            await page.fill('#form-text-766004985', PASSWORD)
            await page.fill('#form-text-766004985_confirm', PASSWORD)
            await page.wait_for_timeout(1000)
            await page.evaluate('() => { const btns = document.querySelectorAll(".cmp-form-button"); for (const btn of btns) { if (btn.textContent.trim()) { btn.click(); break; } } }')

            # Wait for challenge + resubmit
            success = False
            for i in range(8):
                await page.wait_for_timeout(5000)
                text = ''
                try:
                    text = await page.inner_text('body')
                except:
                    pass
                url = page.url

                if 'developer.amd.com' in url or 'success' in text.lower() or 'activated' in text.lower() or 'congratulations' in text.lower():
                    success = True
                    break

                if len(text) > 500 and 'Access Token' in text:
                    await page.fill('#form-text-30246375', token)
                    await page.fill('#form-text-766004985', PASSWORD)
                    await page.fill('#form-text-766004985_confirm', PASSWORD)
                    await page.wait_for_timeout(1000)
                    await page.evaluate('() => { const btns = document.querySelectorAll(".cmp-form-button"); for (const btn of btns) { if (btn.textContent.trim()) { btn.click(); break; } } }')
                    await page.wait_for_timeout(15000)

                    url2 = page.url
                    text2 = ''
                    try:
                        text2 = await page.inner_text('body')
                    except:
                        pass
                    if 'developer.amd.com' in url2 or 'success' in text2.lower() or 'activated' in text2.lower():
                        success = True
                    break

            if success:
                print(f"  ✅ Activated")
                results.append({"email": email_addr, "status": "activated"})
            else:
                print(f"  ❌ Failed")
                results.append({"email": email_addr, "status": "failed"})

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:80]}")
            results.append({"email": email_addr, "status": "error"})
        finally:
            try:
                await browser.close()
            except:
                pass

        await asyncio.sleep(random.uniform(2, 5))

    return results


# ============ MAIN ============
async def main():
    import argparse
    parser = argparse.ArgumentParser(description='AMD AI Dev Program - Activate')
    parser.add_argument('--input', type=str, help='JSON file with registered accounts')
    parser.add_argument('--email', type=str, help='Comma-separated emails to activate')
    parser.add_argument('--wait', type=int, default=0, help='Seconds to wait before fetching tokens')
    args = parser.parse_args()

    # Get email list
    if args.email:
        emails = [e.strip() for e in args.email.split(',')]
    elif args.input:
        with open(args.input) as f:
            data = json.load(f)
        emails = [r['email'] for r in data if r.get('status') == 'registered']
    else:
        print("Error: provide --input or --email")
        sys.exit(1)

    print(f"=== AMD Activate — {len(emails)} accounts ===")

    if args.wait > 0:
        print(f"Waiting {args.wait}s for emails to arrive...")
        await asyncio.sleep(args.wait)

    # Fetch tokens
    tokens = get_activation_tokens(emails)
    if not tokens:
        print("No tokens found. Emails may still be arriving.")
        return

    # Activate
    results = await activate_batch(tokens)
    activated = [r for r in results if r['status'] == 'activated']

    # Save
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"amd_activated_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nActivated: {len(activated)}/{len(tokens)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
