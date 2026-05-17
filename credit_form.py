#!/usr/bin/env python3
"""
AMD Developer Cloud - Step 4: Submit GPU Credit Request Form
Submits Marketo form on DigitalOcean/AMD page for each account.
Auto-generates realistic personas with unique browser fingerprints.

Usage:
  python3 credit_form.py --input amd_activated_20260517.json
  python3 credit_form.py --input amd_accounts.json --skip-done
  python3 credit_form.py --input amd_accounts.json --count 10
"""
import asyncio
import json
import random
import os
import sys
from datetime import datetime
from fingerprints import get_fingerprint

sys.stdout.reconfigure(line_buffering=True)
os.environ["DISPLAY"] = os.environ.get("DISPLAY", ":99")

try:
    import cloakbrowser
    USE_CLOAK = True
except ImportError:
    from playwright.async_api import async_playwright
    USE_CLOAK = False

# ============ CONFIG ============
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    PROXY = cfg["proxy"]
else:
    PROXY = {
        "server": os.environ.get("PROXY_SERVER", "http://proxy:port"),
        "username": os.environ.get("PROXY_USER", ""),
        "password": os.environ.get("PROXY_PASS", "")
    }

FORM_URL = "https://anchor.digitalocean.com/amd-cloud-free-credit.html"

# ============ PERSONA GENERATOR ============
COMPANIES = {
    "Independent developer": [
        "Freelance", "Self-employed", "Personal Projects", "Open Source Contributor"
    ],
    "Member of opensource project": [
        "HuggingFace", "Mozilla Foundation", "Apache Foundation", "Linux Foundation",
        "PyTorch Contributors", "TensorFlow Community"
    ],
    "Member of a start-up": [
        "NeuralForge AI", "DeepStack Labs", "Cortex Dynamics", "SynthMind",
        "Axiom ML", "VectorSpace AI", "Quantum Leap Tech", "DataPulse",
        "InferenceIO", "ModelShip", "TrainBrain", "GPUCloud Labs"
    ],
    "Member of a corporation": [
        "Siemens AG", "Samsung Electronics", "Bosch", "Philips",
        "SAP", "Infosys", "Tata Consultancy", "Accenture",
        "Deloitte", "IBM Research", "Oracle"
    ]
}

OPEN_SOURCE_PROJECTS = [
    "HuggingFace Transformers - contributing model optimization modules for AMD ROCm. https://github.com/huggingface/transformers",
    "vLLM - contributing AMD GPU inference optimizations and ROCm compatibility patches. https://github.com/vllm-project/vllm",
    "PyTorch - working on ROCm backend improvements and operator fusion. https://github.com/pytorch/pytorch",
    "LangChain - building GPU-accelerated embedding and retrieval modules. https://github.com/langchain-ai/langchain",
    "OpenFold - contributing GPU-optimized protein folding inference. https://github.com/aqlaboratory/openfold",
    "DeepSpeed - adding AMD MI300X support for distributed training. https://github.com/microsoft/DeepSpeed",
    "Ollama - adding native ROCm support for local LLM inference. https://github.com/ollama/ollama",
    "ClimaX - open-source climate modeling with GPU training. https://github.com/microsoft/ClimaX",
    "LeRobot - GPU-accelerated RL training for robotics. https://github.com/huggingface/lerobot",
    "Mozilla Common Voice - speech model training and dataset tools. https://github.com/common-voice",
]

USE_CASES = [
    "Training large language models for domain-specific applications. Need multi-GPU access for distributed training with DeepSpeed.",
    "Fine-tuning open-source vision models for medical imaging classification. Evaluating ROCm performance for production deployment.",
    "Running LLM inference at scale for a conversational AI platform. Benchmarking AMD MI300X throughput vs NVIDIA H100.",
    "Training multilingual NLP models. Building translation and summarization systems for underrepresented languages.",
    "Fine-tuning Llama 3 for enterprise document understanding. Evaluating ROCm compatibility with existing PyTorch pipeline.",
    "Real-time computer vision inference for autonomous systems. Need low-latency GPU inference for object detection.",
    "Fine-tuning speech recognition models for low-resource languages. Contributing to open-source ASR projects.",
    "Training recommendation models for e-commerce. Processing millions of user interactions for personalization.",
    "Fine-tuning protein structure prediction models for drug discovery applications.",
    "Real-time audio generation using diffusion models. Building low-latency synthesis engine.",
    "Training Arabic and multilingual language models for document processing and NER.",
    "Post-training optimization and quantization of language models. Applying RLHF and DPO alignment.",
    "Training reinforcement learning agents with GPU-accelerated physics simulation.",
    "Hosting image generation models for a creative platform. Running SDXL and Flux inference.",
    "Fine-tuning vision-language models for satellite imagery analysis and classification.",
    "Pre-training domain-specific language models for financial analysis.",
    "Building AI tutoring system using open-source LLMs with real-time inference.",
    "Fine-tuning video understanding models for content moderation at scale.",
    "Training weather prediction models using transformer architectures.",
    "Building privacy-focused local AI assistant with efficient GPU inference.",
]

OUTCOMES = [
    "Deploy production inference endpoint serving 10K daily requests",
    "Benchmark ROCm performance vs CUDA for research publication",
    "Compare throughput and latency metrics between MI300X and H100",
    "Train and deploy multilingual model serving 500K daily requests",
    "Validate AMD GPU compatibility for ML infrastructure migration",
    "Achieve sub-20ms inference latency for real-time applications",
    "Release fine-tuned open-source models for community use",
    "Reduce model training time by 60 percent with AMD GPUs",
    "Run protein folding inference at scale for drug screening",
    "Achieve real-time audio generation with under 50ms latency",
    "Deploy NLP pipeline processing 10K documents daily",
    "Quantize and deploy 13B parameter model with minimal quality loss",
    "Train RL policies that transfer to real hardware",
    "Serve 1000 image generation requests per hour cost-effectively",
    "Process and classify 500K images for production pipeline",
    "Launch AI assistant serving institutional clients",
    "Deploy conversational AI serving 10K concurrent users",
    "Reduce content moderation latency from 30s to under 5s",
    "Improve forecast accuracy by 15 percent over baseline",
    "Complete pre-training run for domain-specific model",
]

COMMENTS_TEMPLATES = [
    "Building {project_type}. Need GPU access to iterate on model training and run inference benchmarks. Currently using PyTorch with {framework} for {task}.",
    "Researcher working on {field}. Need to validate that our training pipeline works on AMD GPUs with ROCm. Planning to publish results.",
    "Building an open-source {tool} optimized for AMD hardware. Want to contribute ROCm optimizations back to the community.",
    "CTO of a {size}-person startup focused on {domain}. Currently spending significant budget on GPU compute. Evaluating AMD as cost-effective alternative.",
    "ML engineer evaluating AMD GPUs for {purpose}. Need to benchmark workloads before making infrastructure decisions.",
    "Engineer building {system}. Currently using NVIDIA but exploring ROCm for cost optimization. Open to contributing benchmarks.",
    "Working on {task} for {audience}. Our models will be open-sourced. Need GPU access for training experiments.",
    "Co-founder of {company_type}. Training a {model_size} parameter model. Need GPU credits to complete training run.",
    "Senior ML engineer at {company_type}. Fine-tuning models on custom datasets. Need multi-GPU setup for large-scale processing.",
    "Developer building {product} for {market}. Using open-source LLMs fine-tuned on domain content. Need cost-effective GPU inference at scale.",
]

COUNTRIES_POOL = [
    ("US", "94105"), ("US", "98101"), ("US", "02139"), ("US", "10001"), ("US", "60601"),
    ("GB", "EC1A 1BB"), ("GB", "SW1A 1AA"),
    ("DE", "80333"), ("DE", "10115"), ("DE", "60311"),
    ("FR", "75008"), ("FR", "69001"),
    ("IN", "400076"), ("IN", "560001"), ("IN", "110001"),
    ("CA", "M5V 3L9"), ("CA", "V6B 1A1"),
    ("AU", "3000"), ("AU", "2000"),
    ("JP", "100-0001"), ("KR", "06164"),
    ("BR", "05508-010"), ("BR", "01310-100"),
    ("SE", "11456"), ("DK", "2100"), ("NL", "1012 AB"),
    ("IT", "00185"), ("ES", "28001"),
    ("SG", "018956"), ("IL", "6100000"),
    ("PK", "44000"), ("EG", "11511"), ("AE", "00000"),
    ("CN", "100084"), ("CH", "8001"),
]

TYPES = ["Independent developer", "Member of opensource project", "Member of a start-up", "Member of a corporation"]
TEAMS = ["Yes, I am an advanced user", "Yes, I am an advanced user", "Yes, I am an advanced user", "Yes, I am a beginner"]
GPU_USES = ["Training", "Finetuning", "Inference", "Inference end point only", "Post training"]


def generate_persona(email_addr):
    """Generate a realistic persona from an email address."""
    prefix = email_addr.split("@")[0]
    parts = prefix.replace("-", ".").split(".")

    if len(parts) >= 2:
        first = parts[0].capitalize()
        last_raw = parts[1]
        last = ''.join(c for c in last_raw if not c.isdigit()).capitalize()
        if not last:
            last = last_raw.capitalize()
    else:
        first = parts[0].capitalize()
        last = "Dev"

    full_name = f"{first} {last}"
    dev_type = random.choice(TYPES)
    country, postal = random.choice(COUNTRIES_POOL)
    company = random.choice(COMPANIES[dev_type])
    github = f"{first.lower()}{last.lower()}-{random.choice(['ml', 'ai', 'dev', 'research', 'eng', 'labs'])}"

    persona = {
        "name": full_name,
        "country": country,
        "postal": postal,
        "company": company,
        "github": github,
        "linkedin": f"https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.choice(['ml', 'ai', 'dev'])}",
        "type": dev_type,
        "team": random.choice(TEAMS),
        "gpu_use": random.choice(GPU_USES),
        "use_case": random.choice(USE_CASES),
        "outcome": random.choice(OUTCOMES),
        "comments": random.choice(COMMENTS_TEMPLATES).format(
            project_type=random.choice(["an AI-powered platform", "a machine learning pipeline", "a deep learning system"]),
            framework=random.choice(["DeepSpeed", "FSDP", "Megatron", "Accelerate"]),
            task=random.choice(["distributed training", "model parallelism", "gradient accumulation"]),
            field=random.choice(["computer vision", "NLP", "speech processing", "reinforcement learning"]),
            tool=random.choice(["inference server", "training framework", "model optimizer"]),
            size=random.choice(["8", "12", "15", "20", "30"]),
            domain=random.choice(["AI infrastructure", "language technology", "computer vision", "healthcare AI"]),
            purpose=random.choice(["data center expansion", "cloud migration", "cost optimization"]),
            system=random.choice(["autonomous systems", "real-time inference", "batch processing pipeline"]),
            audience=random.choice(["enterprise clients", "public sector", "education", "healthcare"]),
            company_type=random.choice(["an AI startup", "a tech company", "a research lab"]),
            model_size=random.choice(["3B", "7B", "13B"]),
            product=random.choice(["AI tutoring system", "content moderation tool", "recommendation engine"]),
            market=random.choice(["emerging markets", "enterprise", "education sector", "healthcare"]),
        ),
    }

    # Conditional fields
    if dev_type == "Member of opensource project":
        persona["openText"] = random.choice(OPEN_SOURCE_PROJECTS)
    elif dev_type == "Member of a corporation":
        persona["Company__c"] = company
        persona["business_email"] = f"{first.lower()}.{last.lower()}@{company.lower().replace(' ', '').replace(',', '')}.com"

    return persona


# ============ FORM SUBMISSION ============
async def submit_one(email_addr, persona, idx, total):
    """Submit GPU credit form with unique browser fingerprint."""
    fp = get_fingerprint(country_code=persona['country'], index=idx)
    print(f"\n[{idx}/{total}] {persona['name']} | {email_addr}")
    print(f"  🖥️  {fp['timezone']} | {fp['locale']} | {fp['viewport']['width']}x{fp['viewport']['height']}")

    if USE_CLOAK:
        browser = await cloakbrowser.launch_async(
            headless=True,
            args=['--no-sandbox', '--disable-gpu'],
            proxy=PROXY,
            timezone=fp['timezone'],
            locale=fp['locale']
        )
        page = await browser.new_page()
        await page.set_viewport_size(fp['viewport'])
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True, proxy={"server": PROXY["server"], "username": PROXY["username"], "password": PROXY["password"]})
        context = await browser.new_context(
            viewport=fp['viewport'],
            user_agent=fp['user_agent'],
            locale=fp['locale'],
            timezone_id=fp['timezone']
        )
        page = await context.new_page()

    try:
        await page.goto(FORM_URL, wait_until='networkidle', timeout=60000)
        await page.wait_for_function('typeof MktoForms2 !== "undefined" && MktoForms2.allForms().length > 0', timeout=30000)
        await page.wait_for_timeout(2000)

        # Build form values
        form_values = {
            "FirstName": persona['name'],
            "Email": email_addr,
            "githubHandle": persona['github'],
            "company_linkedin_handle__c_lead": persona['linkedin'],
            "Country": persona['country'],
            "PostalCode": persona['postal'],
            "Type__c": persona['type'],
            "Company": persona['company'],
            "Contact_Sales_Use_Case__c_lead": persona['use_case'],
            "technicalteam": persona['team'],
            "h100sUseCase": persona['gpu_use'],
            "Desired_Outcome__c": persona['outcome'],
            "Marketing_Comments__c": persona['comments']
        }

        # Conditional fields
        if persona['type'] == "Member of opensource project" and 'openText' in persona:
            form_values["openText"] = persona['openText']
        if persona['type'] == "Member of a corporation":
            form_values["Company__c"] = persona.get('Company__c', persona['company'])
            form_values["DaScoopComposer__Email_2__c"] = persona.get('business_email', email_addr)

        # Set Type first to trigger conditional fields
        await page.evaluate('(vals) => { MktoForms2.allForms()[0].setValues({"Type__c": vals.Type__c}); }', form_values)
        await page.evaluate('''(val) => {
            const el = document.getElementById("Type__c");
            if (el) { el.value = val; el.dispatchEvent(new Event("change", {bubbles: true})); }
        }''', form_values['Type__c'])
        await page.wait_for_timeout(1500)

        # Set all values
        await page.evaluate('(vals) => { MktoForms2.allForms()[0].setValues(vals); }', form_values)
        await page.wait_for_timeout(1000)

        # Set DOM selects explicitly
        for sel_id in ['Country', 'Type__c', 'technicalteam', 'h100sUseCase']:
            await page.evaluate(f'''(val) => {{
                const el = document.getElementById("{sel_id}");
                if (el) {{ el.value = val; el.dispatchEvent(new Event("change", {{bubbles: true}})); }}
            }}''', form_values[sel_id])

        await page.wait_for_timeout(500)

        # Validate
        is_valid = await page.evaluate('() => MktoForms2.allForms()[0].validate()')
        if not is_valid:
            print(f"  ⚠️  Validation failed, fixing...")
            invalid = await page.evaluate('''() => {
                const els = document.querySelectorAll(".mktoInvalid");
                return Array.from(els).map(e => e.id || e.name);
            }''')
            print(f"     Invalid: {invalid}")
            for field_id in invalid:
                if field_id in form_values:
                    tag = await page.evaluate(f'() => document.getElementById("{field_id}")?.tagName')
                    if tag == 'SELECT':
                        await page.select_option(f'#{field_id}', form_values[field_id])
                    else:
                        await page.fill(f'#{field_id}', form_values[field_id])
            await page.wait_for_timeout(500)
            await page.evaluate('(vals) => { MktoForms2.allForms()[0].setValues(vals); }', form_values)
            await page.wait_for_timeout(500)

        # Submit
        await page.evaluate('() => MktoForms2.allForms()[0].submit()')

        # Wait for redirect
        try:
            await page.wait_for_url('**/devcloud.amd.com/**', timeout=30000)
            print(f"  ✅ Success")
            return {"email": email_addr, "status": "success"}
        except:
            current_url = page.url
            if 'devcloud' in current_url:
                print(f"  ✅ Success")
                return {"email": email_addr, "status": "success"}
            else:
                print(f"  ❌ Failed — {current_url}")
                return {"email": email_addr, "status": "failed", "url": current_url}

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:120]}")
        return {"email": email_addr, "status": "error", "error": str(e)[:200]}
    finally:
        try:
            await browser.close()
        except:
            pass
        if not USE_CLOAK:
            await pw.stop()


# ============ MAIN ============
async def main():
    import argparse
    import glob
    parser = argparse.ArgumentParser(description='AMD Developer Cloud - GPU Credit Form')
    parser.add_argument('--input', type=str, required=True, help='JSON file with accounts')
    parser.add_argument('--count', type=int, default=0, help='Limit submissions (0 = all)')
    parser.add_argument('--skip-done', action='store_true', help='Skip previously submitted accounts')
    parser.add_argument('--delay-min', type=float, default=5, help='Min delay between submissions')
    parser.add_argument('--delay-max', type=float, default=12, help='Max delay between submissions')
    args = parser.parse_args()

    # Load accounts
    with open(args.input) as f:
        accounts = json.load(f)

    emails = []
    for acc in accounts:
        if isinstance(acc, dict) and 'email' in acc:
            emails.append(acc['email'])
        elif isinstance(acc, str):
            emails.append(acc)

    # Skip already done
    done_emails = set()
    if args.skip_done:
        for f in glob.glob("amd_credit_results_*.json"):
            try:
                with open(f) as fh:
                    results = json.load(fh)
                for r in results:
                    if r.get('status') == 'success':
                        done_emails.add(r['email'])
            except:
                pass
        if done_emails:
            print(f"Skipping {len(done_emails)} already submitted accounts")

    emails = [e for e in emails if e not in done_emails]
    if args.count > 0:
        emails = emails[:args.count]

    print(f"=== AMD Developer Cloud GPU Credits ===")
    print(f"Accounts: {len(emails)}")
    print(f"Form: {FORM_URL}")
    print(f"Method: {'CloakBrowser' if USE_CLOAK else 'Playwright'} + Proxy")
    print(f"Time: {datetime.now().isoformat()}")

    if not emails:
        print("\nNo accounts to process.")
        return

    results = []
    success_count = 0

    for idx, email_addr in enumerate(emails, 1):
        persona = generate_persona(email_addr)
        result = await submit_one(email_addr, persona, idx, len(emails))
        results.append(result)

        if result["status"] == "success":
            success_count += 1

        if idx < len(emails):
            delay = random.uniform(args.delay_min, args.delay_max)
            print(f"  ⏳ Waiting {delay:.1f}s...")
            await asyncio.sleep(delay)

    # Save results
    output_file = f"amd_credit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*50}")
    print(f"=== DONE ===")
    print(f"Success: {success_count}/{len(results)}")
    print(f"Failed: {len(results) - success_count}/{len(results)}")
    print(f"Results: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
