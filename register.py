#!/usr/bin/env python3
"""
AMD AI Developer Program - Step 1: Register accounts
Each account gets a unique browser fingerprint (timezone, locale, viewport).

Usage: python3 register.py --count 100
Output: amd_registered_<timestamp>.json
"""
import asyncio
import cloakbrowser
import os
import sys
import json
import random
from datetime import datetime
from fingerprints import get_fingerprint

sys.stdout.reconfigure(line_buffering=True)
os.environ["DISPLAY"] = os.environ.get("DISPLAY", ":99")

# ============ CONFIG ============
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    DOMAIN = cfg["domain"]
    PROXY = cfg["proxy"]
else:
    DOMAIN = os.environ.get("AMD_DOMAIN", "yourdomain.com")
    PROXY = {
        "server": os.environ.get("PROXY_SERVER", "http://proxy:port"),
        "username": os.environ.get("PROXY_USER", ""),
        "password": os.environ.get("PROXY_PASS", "")
    }

REGISTER_URL = "https://www.amd.com/en/registration/ai-dev-program-sign-up-form.html"
CUSTTARG = "aHR0cHM6Ly9kZXZlbG9wZXIuYW1kLmNvbT9SZWxheVN0YXRlPQ=="

# Country code mapping (label → 2-letter code for fingerprint matching)
COUNTRIES = {
    "United States": "US", "Canada": "CA", "United Kingdom": "GB",
    "Germany": "DE", "France": "FR", "Switzerland": "CH",
    "Japan": "JP", "Korea, Republic of": "KR", "China": "CN",
    "Australia": "AU", "Brazil": "BR", "India": "IN",
    "Mexico": "MX", "Italy": "IT", "Poland": "PL",
    "Sweden": "SE", "Denmark": "DK", "Netherlands": "NL",
    "Saudi Arabia": "SA", "Egypt": "EG", "Pakistan": "PK",
    "Singapore": "SG", "Israel": "IL", "Spain": "ES",
    "Norway": "NO", "Finland": "FI", "Ireland": "IE",
    "Turkey": "TR", "Argentina": "AR",
}

# ============ PEOPLE GENERATOR ============
def generate_people(count):
    """Generate realistic people. Supports 100+ unique combos."""
    first_names = [
        "James", "Emma", "Hiroshi", "Priya", "Lars", "Chen", "Marco", "Sarah", "Ahmed", "Julia",
        "Kenji", "Ana", "Viktor", "Lisa", "Ravi", "Olga", "David", "Fatima", "Michael", "Yuki",
        "Roberto", "Nina", "Ali", "Sophie", "Tom", "Ingrid", "Pablo", "Mika", "Hassan", "Rachel",
        "Alexander", "Maria", "Dmitri", "Aisha", "Henrik", "Mei", "Carlos", "Anna", "Omar", "Erik",
        "Lena", "Nathan", "Isabella", "Daniel", "Lucas", "Sophia", "Andrei", "Yuna", "Felix", "Nadia",
        "Oscar", "Hana", "Stefan", "Leila", "Mateo", "Chloe", "Ivan", "Amara", "Leo", "Zara",
        "Nikolai", "Sakura", "Gabriel", "Ines", "Arjun", "Elise", "Tariq", "Freya", "Sven", "Mina",
        "Hugo", "Daria", "Kai", "Lucia", "Oleg", "Noor", "Finn", "Yara", "Anton", "Ava",
        "Maxim", "Isla", "Romain", "Ananya", "Tobias", "Camila", "Jens", "Layla", "Ruben", "Emilia",
        "Akira", "Petra", "Samir", "Vera", "Liam", "Rina", "Emir", "Clara", "Theo", "Mira",
    ]
    last_names = [
        "Wilson", "Thompson", "Yamamoto", "Sharma", "Eriksson", "Wei", "Bianchi", "Brien", "Mansour", "Schneider",
        "Nakamura", "Garcia", "Petrov", "Berg", "Kumar", "Novak", "Park", "Zahra", "Brown", "Sato",
        "Ferreira", "Johansson", "Reza", "Dubois", "Mitchell", "Larsen", "Rodriguez", "Virtanen", "Ali", "Green",
        "Kowalski", "Hansen", "Kim", "Brooks", "Rossi", "Hassan", "Zhang", "Silva", "Nguyen", "Hoffmann",
        "Mendez", "Khan", "Anderson", "Martin", "Patel", "Chen", "Muller", "Tanaka", "Santos", "Ivanov",
        "Okafor", "Lindqvist", "Moreau", "Takahashi", "Gupta", "Volkov", "Fernandez", "Watanabe", "Singh", "Fischer",
        "Costa", "Yamada", "Popov", "Suzuki", "Morozov", "Almeida", "Ito", "Sokolov", "Oliveira", "Kato",
        "Kozlov", "Pereira", "Mori", "Novikov", "Ribeiro", "Hayashi", "Fedorov", "Carvalho", "Ogawa", "Barros",
        "Kimura", "Sorokin", "Martins", "Shimizu", "Kuznetsov", "Gomes", "Fujita", "Lebedev", "Lopes", "Endo",
        "Smirnov", "Dias", "Ishida", "Orlov", "Rocha", "Matsuda", "Pavlov", "Araujo", "Volkov", "Nunes",
    ]
    companies = [
        "Stanford University", "Imperial College London", "University of Tokyo", "IIT Bombay",
        "KTH Royal Institute", "Peking University", "Sapienza University", "Trinity College Dublin",
        "AUC", "TU Munich", "Kyoto University", "Universidad Complutense", "Skoltech",
        "TU Delft", "IISc Bangalore", "Seoul National University", "Mohammed V University",
        "MIT", "Osaka University", "UNICAMP", "Uppsala University", "Sharif University",
        "Ecole Polytechnique", "University of Toronto", "NTNU", "Universidad de Buenos Aires",
        "Aalto University", "NUST", "University of Melbourne", "ETH Zurich",
        "Carnegie Mellon University", "University of Cambridge", "Tsinghua University",
        "NUS Singapore", "KAIST", "University of Sydney", "TU Berlin", "Politecnico di Milano",
        "University of Edinburgh", "McGill University", "Technion", "University of Cape Town",
        "EPFL", "Georgia Tech", "UC Berkeley", "Caltech",
        "University of Oxford", "Harvard University", "Princeton University",
        "DeepMind Research", "Meta AI", "Microsoft Research", "NVIDIA Research",
        "Hugging Face", "Lightning AI", "Databricks", "Scale AI",
        "Anyscale", "Modal Labs", "Together AI", "Mistral AI",
        "NeuralForge AI", "Cortex Dynamics", "SynthMind Labs", "VectorSpace",
        "Siemens AG", "Samsung Electronics", "Bosch AI", "Philips Research",
        "SAP Labs", "Infosys AI", "Tata Research", "Accenture Labs",
    ]
    countries = [
        "United States", "United Kingdom", "Germany", "France", "Japan",
        "India", "Canada", "Australia", "Brazil", "Sweden",
        "Korea, Republic of", "China", "Italy", "Spain", "Netherlands",
        "Switzerland", "Denmark", "Finland", "Norway", "Ireland",
        "Israel", "Singapore", "Pakistan", "Egypt", "Turkey",
        "Argentina", "Saudi Arabia", "Poland",
    ]

    pool = []
    used_combos = set()
    random.shuffle(first_names)
    random.shuffle(last_names)

    for i in range(min(count, len(first_names))):
        first = first_names[i]
        last = last_names[i % len(last_names)]
        combo = f"{first}_{last}"
        if combo in used_combos:
            last = last_names[(i + 50) % len(last_names)]
            combo = f"{first}_{last}"
        used_combos.add(combo)
        pool.append({
            "first": first, "last": last,
            "company": random.choice(companies),
            "country": random.choice(countries)
        })

    random.shuffle(pool)
    return pool[:count]


# ============ REGISTER ============
async def register_batch(people):
    """Register accounts using browser (Akamai challenge requires it)."""
    results = []

    for idx, person in enumerate(people):
        email_addr = f"{person['first'].lower()}.{person['last'].lower()}{random.randint(10,99)}@{DOMAIN}"
        print(f"\n[REG {idx+1}/{len(people)}] {person['first']} {person['last']} | {email_addr}")

        # Get country-matched fingerprint
        country_code = COUNTRIES.get(person['country'], 'US')
        fp = get_fingerprint(country_code=country_code, index=idx)
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
            await page.goto(f"{REGISTER_URL}?custtarg={CUSTTARG}", wait_until='load', timeout=60000)
            await page.wait_for_selector('#form-text-1444782869', state='visible', timeout=30000)

            # Dismiss cookie
            await page.evaluate('() => { const b = document.getElementById("onetrust-accept-btn-handler"); if(b) b.click(); }')
            await page.wait_for_timeout(2000)

            # Fill form
            await page.fill('#form-text-1444782869', person['first'])
            await page.fill('#form-text-1891447162', person['last'])
            await page.fill('#form-text-1830320319', email_addr)
            await page.fill('#form-text-417351009', person['company'])
            await page.select_option('#country-dropdown-1299606956', label=person['country'])
            try:
                await page.select_option('#language-dropdown-765462299', label='English')
            except:
                pass
            await page.evaluate('() => { document.querySelectorAll("#new_form input[type=checkbox]").forEach(cb => { if(!cb.checked) cb.click(); }); }')
            await page.wait_for_timeout(1000)

            # Submit (triggers Akamai challenge)
            await page.evaluate('() => document.getElementById("form-button-1857186030").click()')

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

                if 'activate' in url.lower():
                    success = True
                    break

                if len(text) > 500 and 'First Name' in text:
                    await page.fill('#form-text-1444782869', person['first'])
                    await page.fill('#form-text-1891447162', person['last'])
                    await page.fill('#form-text-1830320319', email_addr)
                    await page.fill('#form-text-417351009', person['company'])
                    await page.select_option('#country-dropdown-1299606956', label=person['country'])
                    try:
                        await page.select_option('#language-dropdown-765462299', label='English')
                    except:
                        pass
                    await page.evaluate('() => { document.querySelectorAll("#new_form input[type=checkbox]").forEach(cb => { if(!cb.checked) cb.click(); }); }')
                    await page.wait_for_timeout(1000)
                    await page.evaluate('() => document.getElementById("form-button-1857186030").click()')
                    await page.wait_for_timeout(15000)
                    if 'activate' in page.url.lower():
                        success = True
                    break

            if success:
                print(f"  ✅ Registered")
                results.append({"email": email_addr, "person": person, "status": "registered"})
            else:
                print(f"  ❌ Failed")
                results.append({"email": email_addr, "person": person, "status": "failed"})

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:80]}")
            results.append({"email": email_addr, "person": person, "status": "error"})
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
    parser = argparse.ArgumentParser(description='AMD AI Dev Program - Register')
    parser.add_argument('--count', type=int, default=5, help='Number of accounts to register')
    args = parser.parse_args()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"amd_registered_{timestamp}.json"

    people = generate_people(args.count)
    print(f"=== AMD Auto Register — {len(people)} accounts ===")
    print(f"Domain: @{DOMAIN}\n")

    reg_results = await register_batch(people)
    registered = [r for r in reg_results if r['status'] == 'registered']

    with open(output_file, 'w') as f:
        json.dump(reg_results, f, indent=2)

    print(f"\nRegistered: {len(registered)}/{len(people)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
