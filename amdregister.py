#!/usr/bin/env python3
"""
AMD Cloud Credit — Full Pipeline
=================================
1. Register account at www.amd.com (CloakBrowser)
2. Fetch activation token from email (IMAP)
3. Activate account with token + password (CloakBrowser)
4. Login via Okta → Bearer token (HTTP)
5. Submit credit request (Marketo form)

Usage:
  python3 amdregister.py --count 3
  python3 amdregister.py --email user@domain.com --name "Erik Hansen" --company "MIT" --country US
"""

import asyncio, json, re, time, random, string, hashlib, base64, codecs, os, sys
import imaplib, email as em_mod, urllib.parse, requests as req
from pathlib import Path
from datetime import datetime
import cloakbrowser

# ═══════════════════════════════════════════════════════════════
# CONFIG (from config.json)
# ═══════════════════════════════════════════════════════════════
CONFIG_FILE = Path(__file__).parent / "config.json"
with open(CONFIG_FILE) as f:
    CFG = json.load(f)

PASSWORD = CFG["password"]
IMAP_HOST = CFG["imap_host"]
IMAP_USER = CFG["imap_user"]
IMAP_PW = CFG["imap_password"]

REGISTER_URL = "https://www.amd.com/en/registration/ai-dev-program-sign-up-form.html"
CUSTTARG = "aHR0cHM6Ly9kZXZlbG9wZXIuYW1kLmNvbT9SZWxheVN0YXRlPQ=="
ACTIVATE_URL = "https://www.amd.com/en/registration/activate-account.html"

OKTA = "https://login.amd.com"
DEV_AMD = "https://developer.amd.com"
CID = "0oa10nnl4wplbzM16698"
REDIR = "https://developer.amd.com/auth/callback"
EMAIL_AUTH = "aut1uh73i3v040uEU697"
CREDIT_FORM_URL = "https://anchor.digitalocean.com/amd-cloud-free-credit.html"

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SUCCESS_FILE = Path(__file__).parent / "success.txt"

FINGERPRINTS = [
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0", "platform": "Windows"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36", "platform": "macOS"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36", "platform": "Windows"},
    {"ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36", "platform": "Linux"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0", "platform": "Windows"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15", "platform": "macOS"},
]


def log(msg, icon="•"):
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] {icon} {msg}")


def gen_cv(n=64):
    return ''.join(random.choices(string.ascii_letters + string.digits + "-._~", k=n))


def gen_cc(cv):
    return base64.urlsafe_b64encode(hashlib.sha256(cv.encode()).digest()).rstrip(b'=').decode()


def gen_rd(n=16):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def find_st(html):
    idx = html.find('"stateToken":"')
    if idx < 0: return None
    start = html.index('"', html.index(':', idx)) + 1
    i = start
    while i < len(html):
        if html[i] == '\\': i += 2; continue
        if html[i] == '"': break
        i += 1
    return codecs.decode(html[start:i], 'unicode_escape')


# ═══════════════════════════════════════════════════════════════
# REALISTIC DATA
# ═══════════════════════════════════════════════════════════════
EMAIL_DOMAINS = ["richardsheingold.com"]

NAMES = [
    # Asia
    ("Hiroshi", "Tanaka", "JP", "University of Tokyo"),
    ("Yuki", "Watanabe", "JP", "Kyoto University"),
    ("Wei", "Chen", "CN", "Tsinghua University"),
    ("Li", "Zhang", "CN", "Peking University"),
    ("Priya", "Sharma", "IN", "IIT Bombay"),
    ("Ravi", "Kumar", "IN", "IISc Bangalore"),
    ("Min-Jun", "Kim", "KR", "KAIST"),
    ("Ji-Hoon", "Lee", "KR", "Seoul National University"),
    ("Putu", "Wijaya", "ID", "ITB Bandung"),
    ("Made", "Suryana", "ID", "Universitas Indonesia"),
    ("Budi", "Santoso", "ID", "UGM Yogyakarta"),
    ("Rizki", "Pratama", "ID", "ITS Surabaya"),
    ("Dewi", "Lestari", "ID", "Universitas Gadjah Mada"),
    ("Siti", "Rahmawati", "ID", "UI Jakarta"),
    ("Ahmad", "Hidayat", "ID", "ITB Bandung"),
    ("Thanh", "Nguyen", "VN", "VNU Hanoi"),
    # Europe
    ("Erik", "Hansen", "DK", "Technical University of Denmark"),
    ("Lars", "Eriksson", "SE", "KTH Royal Institute"),
    ("Henrik", "Johansson", "SE", "Uppsala University"),
    ("Sophie", "Dubois", "FR", "Sorbonne University"),
    ("Marco", "Bianchi", "IT", "Politecnico di Milano"),
    ("Lena", "Muller", "DE", "TU Munich"),
    ("Felix", "Schmidt", "DE", "RWTH Aachen"),
    ("Pablo", "Garcia", "ES", "Universidad Complutense"),
    ("Emma", "Wilson", "GB", "University of Oxford"),
    ("James", "Thompson", "GB", "Imperial College London"),
    ("Isabella", "De Jong", "NL", "TU Delft"),
    ("Viktor", "Petrov", "RU", "Skoltech"),
    ("Stefan", "Kowalski", "PL", "University of Warsaw"),
    ("Nikolai", "Andersen", "FI", "Aalto University"),
    # Africa
    ("Ahmed", "Mansour", "EG", "Cairo University"),
    ("Fatima", "Zahra", "EG", "AUC"),
    ("Ali", "Reza", "SA", "KAUST"),
    ("Aisha", "Okafor", "NG", "University of Lagos"),
    ("Lerato", "Ndlovu", "ZA", "University of Cape Town"),
    ("Samir", "Benali", "MA", "Mohammed V University"),
    # Americas
    ("Michael", "Johnson", "US", "MIT"),
    ("Sarah", "Williams", "US", "Stanford University"),
    ("David", "Martinez", "US", "Carnegie Mellon University"),
    ("Roberto", "Ferreira", "BR", "UNICAMP"),
    ("Sofia", "Mendez", "MX", "UNAM"),
    ("Chloe", "Tremblay", "CA", "University of Toronto"),
]

COUNTRY_LABELS = {
    "JP": "Japan", "CN": "China", "IN": "India", "KR": "Korea, Republic of",
    "ID": "Indonesia", "VN": "Vietnam", "DK": "Denmark", "SE": "Sweden",
    "FR": "France", "IT": "Italy", "DE": "Germany", "ES": "Spain",
    "GB": "United Kingdom", "NL": "Netherlands", "RU": "Russian Federation",
    "PL": "Poland", "FI": "Finland", "EG": "Egypt", "SA": "Saudi Arabia",
    "NG": "Nigeria", "ZA": "South Africa", "MA": "Morocco", "US": "United States",
    "BR": "Brazil", "MX": "Mexico", "CA": "Canada",
}

# Use cases are intentionally varied — different domains, tones, lengths,
# specific tool/framework mentions, regional context, casual vs formal.
# Avoid AI/ML-only entries; mix HPC, scientific computing, game dev,
# audio, robotics, indie/side projects, students, production engineering.
USE_CASES = [
    # ── LLM / NLP — specific & concrete ───────────────────────────────
    "fine-tuning a 7B model on our internal docs, mostly checking if FSDP stays stable on ROCm across long runs",
    "comparing vLLM throughput on MI300X vs H100 for a RAG service we ship next month",
    "porting an in-house Triton kernel to HIP, looking for performance parity with our CUDA build",
    "training a small language model for Vietnamese legal text, dataset is ~80GB and I keep running out of VRAM on my 4090",
    "quantizing Llama 3.1 70B with AWQ, want to verify INT4 inference latency on MI300X before recommending it to the team",
    "evaluating FlashAttention-2 backward on ROCm 6.2 for our 13B training run",
    "building a multilingual embeddings pipeline for customer support search, eight languages, fine-tuning on domain data",
    "trying to get llama.cpp to run a 70B Q4 on MI300X without falling over on context lengths past 8k",
    "we hit a known bug with llama.cpp + ROCm 6.2 on MI250, would like to verify the fix on MI300X hardware",
    "running continued pretraining of a 1.5B model on Indonesian news corpus, batch size keeps being the bottleneck",

    # ── Vision / multimodal ────────────────────────────────────────────
    "training a 3D pose estimation model for a gymnastics coaching app, mostly 6-8 hour jobs overnight",
    "real-time semantic segmentation for a dashcam product, INT8 deployment, latency budget is 35ms",
    "doing data augmentation for medical CT scans with MONAI, need the extra VRAM for full-resolution volumes",
    "fine-tuning YOLOv9 on a custom industrial defect dataset, about 40k labeled images",
    "open-vocabulary detection research, evaluating GroundingDINO on AMD because of cost",
    "trying to port a diffusion-based image colorization model I wrote in PyTorch, getting weird results with bf16 on ROCm",
    "video instance segmentation on surgical footage, ~4hr clips, batch size 1 but I need the memory headroom",

    # ── Audio / speech ────────────────────────────────────────────────
    "real-time speech recognition at 48kHz for a hearing aid prototype, on-device inference",
    "training a U-Net for music source separation, mostly experimenting with different loss functions",
    "running Whisper-large batch transcription across our podcast archive, ~50k hours",
    "voice conversion model for a film dubbing project, needs to preserve prosody across languages",
    "fine-tuning a VAD model for noisy factory floor recordings",

    # ── Robotics / embodied AI ────────────────────────────────────────
    "Isaac Sim sim-to-real for a warehouse picking robot, ~1000 parallel environments",
    "drone flight controller RL pipeline, small policy nets but lots of parallel rollouts",
    "ROS 2 navigation stack with semantic segmentation, currently testing edge inference on a custom carrier board",
    "training a locomotion policy for a quadruped, curriculum learning over terrain difficulty",
    "legged robot locomotion in MuJoCo, parallel env rollout bottleneck is currently GPU memory bandwidth",

    # ── Scientific HPC ────────────────────────────────────────────────
    "OpenFOAM simulations for a wind farm layout optimization, sweeping ~50 design parameters",
    "GROMACS molecular dynamics for protein folding, 100ns trajectories take 2 weeks on our local cluster",
    "FEniCS finite element analysis of cardiac blood flow, want to push mesh resolution up",
    "NAMD simulations of ion channel permeation, currently memory-bandwidth bound",
    "LAMMPS molecular dynamics for polymer crystallization studies, mostly equilibrations over days",
    "computational fluid dynamics for an aerospace startup, mostly steady-state RANS",
    "WRF weather model runs for regional climate research, need higher resolution grids",
    "quantum chemistry calculations with PySCF, doing CASSCF on transition metal complexes",
    "ANSYS Fluent on a parametric study of heat exchanger designs, 200+ variants",
    "geophysical seismic inversion with Devito, full-waveform inversion on field data",
    "lattice QCD calculations, my group needs more compute than what the department cluster provides",
    "astrophysical N-body simulations for galaxy formation, particle counts in the billions",

    # ── Graphics / rendering ──────────────────────────────────────────
    "porting a Unity game to HIP for cross-platform rendering on AMD hardware",
    "ray tracing benchmarks on RDNA 3 vs RTX 4090 for an indie game shipping Q2",
    "Blender Cycles farm rendering for a freelance animation project, deadline-driven",
    "evaluating Mesh shader support on AMD for a procedural terrain engine I'm writing",
    "real-time path tracing demo for a graphics course I'm teaching",
    "GPU video encoding pipeline using FFmpeg + Vulkan compute for a streaming service",

    # ── Quant / Finance ───────────────────────────────────────────────
    "Monte Carlo pricing of exotic options on a rates vol surface, ~10M paths per scenario",
    "training a transformer-based alpha factor model for equity prediction",
    "backtesting a market-making strategy with limit order book simulation at tick level",

    # ── Crypto / Web3 ─────────────────────────────────────────────────
    "zk-SNARK proof generation for a privacy L2, the proving step is the bottleneck",
    "training a mev-search bot policy with PPO, mostly short rollouts",
    "evaluating ROCm for accelerating BLS signature aggregation in a validator setup",

    # ── Indie / side project / curious ────────────────────────────────
    "trying to figure out if I can run Stable Diffusion XL locally on MI300X, no serious project, just curious",
    "indie dev working on a small game, would like to do GPU lightmap baking without renting a beefy machine",
    "personal project: training a music recommendation model on my own listening history",
    "I make educational videos about ML, would like to actually run the demos I show on screen",
    "weekend project: building a local voice assistant for my smart home, no cloud dependency",
    "have a side project on protein structure prediction, only need compute occasionally so paying for a dedicated GPU doesn't make sense",

    # ── Students / academia ───────────────────────────────────────────
    "PhD student in computational biology, need occasional large GPU jobs for my dissertation chapter",
    "doing a Kaggle competition, dataset is too big for my laptop's GPU",
    "master's thesis on RL for resource allocation, my advisor suggested I try ROCm",
    "undergraduate research assistant, mostly running small ablations but sometimes I need a bigger box",
    "summer research project on graph neural networks for drug discovery, the lab's shared GPU is always full",
    "preparing a benchmark paper for a workshop, need reproducible runs on multiple GPU vendors",

    # ── Production engineering / migration ────────────────────────────
    "our team is migrating from CUDA-only to ROCm for cost reasons, need to validate our inference stack on MI300X",
    "evaluating AMD for a new recommendation service, current infra is all NVIDIA",
    "productionizing a Triton model server, want to benchmark it on AMD before committing to the procurement",
    "we serve a RAG API at ~5k QPS, looking at MI300X as a cost-effective alternative to H100",
    "MLOps team, building CI/CD pipelines for model training, need a stable AMD environment to test against",
    "data platform team, our dbt + Spark pipeline is getting expensive, looking at GPU-accelerated alternatives",
    "running Stable Diffusion at scale for an e-commerce product photography pipeline",

    # ── Specific questions to AMD ─────────────────────────────────────
    "is there an ETA for FP4 support in upstream PyTorch on ROCm?",
    "any guidance on NCCL-equivalent (RCCL) tuning for all-reduce across MI300X nodes?",
    "what's the recommended way to profile kernel-level stalls on MI300X? rocprof or something else?",
    "does ROCm 6.3 ship with pre-built wheels for JAX, or do I still need to compile from source?",
    "any chance of getting the full ROCm profiler integrated with PyTorch profiler by default?",

    # ── Genuinely casual / brief ──────────────────────────────────────
    "just curious, want to try AMD before I commit to a workstation purchase",
    "evaluating for future purchase, mostly reading docs and running small examples",
    "I'm a CS student and would like to learn GPU programming outside of CUDA",
    "doing a comparison for a blog post, no production workload, just want real numbers",
    "small consultancy, sometimes we need GPU compute for client deliverables but not every day",
    "want to see if my open-source library works on ROCm before claiming AMD support in the README",
    "freelance ML engineer, my clients are starting to ask about AMD compatibility, need to keep up",
    "I'm migrating off Google Colab because the free tier keeps timing out, looking for alternatives",
    "saw your MI300X announcement, would like to put one through its paces for our internal tooling",
    "writing a technical blog post comparing MI300X vs H100 for LLM inference, need access to real hardware",
    "just want to try AMD because I keep hearing good things about ROCm lately",
    "my team is small and we can't afford an H100 cluster, looking at AMD as a viable alternative",
    "trying to decide between MI300X and H100 for a startup, the credit would help a lot",
    "comparing cost-per-token across providers for a thesis chapter on inference economics",
]

OUTCOMES = [
    "validate MI300X against H100 for our LLM inference workload",
    "see if ROCm 6.x is stable enough for production training runs",
    "measure end-to-end throughput on a real customer workload, not just microbenchmarks",
    "get a sense of the MI300X memory bandwidth advantage for our embedding-heavy model",
    "figure out if we can drop CUDA and ship HIP-only without losing customers",
    "compare $/token across providers before our next infra renewal",
    "find a stable ROCm build for our finetuning pipeline (we keep hitting edge cases)",
    "verify that our custom kernels port cleanly before committing engineering time",
    "see real numbers for FP8 training throughput on a non-NVIDIA stack",
    "understand the actual software maturity gap — rumors vs reality",
    "get a feel for multi-node scaling efficiency on MI300X",
    "make a procurement recommendation to my team with data, not vibes",
    "try AMD before we sign a 3-year H100 contract",
    "decide if our indie game engine should officially support AMD GPUs",
    "see if I can stop renting A100s for occasional training jobs",
    "graduate from Colab Pro to something with more stability",
    "write a fair comparison for our internal tech radar",
    "get hardware access to finish my dissertation on time",
    "ship a paper with reproducible numbers on both vendors",
    "make a decision about AMD support in our open-source library",
    "build confidence in ROCm before our team commits to the migration",
    "test if the developer experience matches what AMD markets",
]


def generate_person():
    first, last, country, company = random.choice(NAMES)
    domain = random.choice(EMAIL_DOMAINS)
    num = random.randint(10, 99)
    email = f"{first.lower()}.{last.lower()}{num}@{domain}"
    github = f"{first.lower()}{last.lower()}{num}"
    return {
        "first": first, "last": last, "email": email, "github": github,
        "company": company, "country_code": country,
        "country_label": COUNTRY_LABELS.get(country, "United States"),
        "use_case": random.choice(USE_CASES), "outcome": random.choice(OUTCOMES),
    }


# ═══════════════════════════════════════════════════════════════
# STEP 1: REGISTER (CloakBrowser)
# ═══════════════════════════════════════════════════════════════
async def step1_register(page, person):
    log(f"Registering: {person['email']}")

    await page.goto(f"{REGISTER_URL}?custtarg={CUSTTARG}", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(5000)

    # Dismiss cookie
    await page.evaluate('() => { const b = document.getElementById("onetrust-accept-btn-handler"); if(b) b.click(); }')
    await page.wait_for_timeout(2000)

    # Fill form
    await page.fill('#form-text-1444782869', person['first'])
    await page.fill('#form-text-1891447162', person['last'])
    await page.fill('#form-text-1830320319', person['email'])
    await page.fill('#form-text-417351009', person['company'])
    await page.select_option('#country-dropdown-1299606956', label=person['country_label'])
    try:
        await page.select_option('#language-dropdown-765462299', label='English')
    except: pass

    # Checkboxes
    await page.evaluate('() => { document.querySelectorAll("#new_form input[type=checkbox]").forEach(cb => { if(!cb.checked) cb.click(); }); }')
    await page.wait_for_timeout(1000)

    # Submit
    await page.evaluate('() => document.getElementById("form-button-1857186030").click()')

    # Wait for redirect
    for i in range(8):
        await page.wait_for_timeout(5000)
        url = page.url
        if "activate" in url.lower():
            log("Registered!", "✅")
            return True
        text = ""
        try: text = await page.inner_text("body")
        except: pass
        if "First Name" in text and len(text) > 500:
            # Retry fill
            await page.fill('#form-text-1444782869', person['first'])
            await page.fill('#form-text-1891447162', person['last'])
            await page.fill('#form-text-1830320319', person['email'])
            await page.fill('#form-text-417351009', person['company'])
            await page.select_option('#country-dropdown-1299606956', label=person['country_label'])
            await page.evaluate('() => { document.querySelectorAll("#new_form input[type=checkbox]").forEach(cb => { if(!cb.checked) cb.click(); }); }')
            await page.evaluate('() => document.getElementById("form-button-1857186030").click()')
            await page.wait_for_timeout(15000)
            if "activate" in page.url.lower():
                log("Registered (retry)!", "✅")
                return True
            break

    log("Registration failed", "❌")
    return False


# ═══════════════════════════════════════════════════════════════
# STEP 2: FETCH ACTIVATION TOKEN (IMAP)
# ═══════════════════════════════════════════════════════════════
def step2_fetch_token(email_addr, timeout=120):
    log(f"Waiting for activation email ({timeout}s)...")
    start = time.time()
    seen = set()

    while time.time() - start < timeout:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST)
            mail.login(IMAP_USER, IMAP_PW)
            mail.select('INBOX')
            _, nums = mail.search(None, 'TO', f'"{email_addr}"', 'SUBJECT', '"activate"')
            if nums[0]:
                for n in nums[0].split():
                    if n in seen: continue
                    seen.add(n)
                    _, d = mail.fetch(n, '(RFC822)')
                    msg = em_mod.message_from_bytes(d[0][1])
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
                    import html as htmlmod
                    clean = re.sub(r'<[^>]+>', '|||', htmlmod.unescape(body))
                    m = re.search(r'Access Token is:[\s|]+([A-Za-z0-9_\-]{5,30})', clean)
                    if m:
                        log(f"Token: {m.group(1)}", "✅")
                        mail.logout()
                        return m.group(1)
            mail.logout()
        except: pass
        time.sleep(10)

    log("Token timeout", "❌")
    return None


# ═══════════════════════════════════════════════════════════════
# STEP 3: ACTIVATE (CloakBrowser)
# ═══════════════════════════════════════════════════════════════
async def step3_activate(page, token):
    log("Activating account...")
    await page.goto(ACTIVATE_URL, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(5000)

    await page.evaluate('() => { const b = document.getElementById("onetrust-accept-btn-handler"); if(b) b.click(); }')
    await page.wait_for_timeout(2000)

    await page.fill('#form-text-30246375', token)
    await page.fill('#form-text-766004985', PASSWORD)
    await page.fill('#form-text-766004985_confirm', PASSWORD)
    await page.wait_for_timeout(1000)
    await page.evaluate('() => { const btn = document.getElementById("form-button-531128439"); if(btn) btn.click(); else { const btns = document.querySelectorAll(".cmp-form-button"); for (const b of btns) { if (b.textContent.trim()) { b.click(); break; } } } }')

    for i in range(10):
        await page.wait_for_timeout(5000)
        url = page.url
        if "developer.amd.com" in url:
            log("Activated!", "✅")
            return True
        text = ""
        try: text = await page.inner_text("body")
        except: pass
        if "success" in text.lower() or "activated" in text.lower() or "congratulations" in text.lower():
            log("Activated!", "✅")
            return True
        if "Access Token" in text and len(text) > 500:
            await page.fill('#form-text-30246375', token)
            await page.fill('#form-text-766004985', PASSWORD)
            await page.fill('#form-text-766004985_confirm', PASSWORD)
            await page.evaluate('() => { const btn = document.getElementById("form-button-531128439"); if(btn) btn.click(); else { const btns = document.querySelectorAll(".cmp-form-button"); for (const b of btns) { if (b.textContent.trim()) { b.click(); break; } } } }')
            await page.wait_for_timeout(15000)
            if "developer.amd.com" in page.url:
                log("Activated (retry)!", "✅")
                return True
            break

    log("Activation failed", "❌")
    return False


# ═══════════════════════════════════════════════════════════════
# STEP 4: LOGIN → BEARER TOKEN (HTTP)
# ═══════════════════════════════════════════════════════════════
def step4_login(email_addr):
    log("Logging in via Okta...")
    s = req.Session()
    fp = random.choice(FINGERPRINTS)
    s.headers.update({"user-agent": fp["ua"]})
    verifier = gen_cv()

    r = s.get(f"{OKTA}/oauth2/default/v1/authorize", params={
        "client_id": CID, "redirect_uri": REDIR, "response_type": "code",
        "scope": "openid profile email", "state": gen_rd(), "nonce": gen_rd(),
        "code_challenge": gen_cc(verifier), "code_challenge_method": "S256", "response_mode": "query",
    })
    st = find_st(r.text)
    if not st: log("stateToken not found", "❌"); return None

    r1 = s.post(f"{OKTA}/idp/idx/identify", json={
        "identifier": email_addr, "credentials": {"passcode": PASSWORD}, "stateHandle": st,
    }, headers={"accept": "application/json; okta-version=1.0.0", "content-type": "application/json",
                "x-okta-user-agent-extended": "okta-auth-js/6.9.0 okta-signin-widget-6.9.0 okta-hosted"})
    d1 = r1.json()

    # Check if already authenticated (no OTP needed)
    redir = d1.get("success", {}).get("href", "")
    if redir:
        log("Already authenticated, skipping OTP", "✅")
    else:
        sh = d1.get("stateHandle", "")
        if not sh: log("Login failed", "❌"); return None

        r2 = s.post(f"{OKTA}/idp/idx/challenge", json={
            "authenticator": {"id": EMAIL_AUTH, "methodType": "email"}, "stateHandle": sh,
        }, headers={"accept": "application/json; okta-version=1.0.0", "content-type": "application/json",
                    "x-okta-user-agent-extended": "okta-auth-js/6.9.0 okta-signin-widget-6.9.0 okta-hosted"})
        d2 = r2.json()
        sh2 = d2.get("stateHandle", "")
        if not sh2: log("Challenge failed", "❌"); return None

        log("OTP sent, fetching...")
        otp = None
        start_otp = time.time()
        seen = set()
        while time.time() - start_otp < 120:
            try:
                mail = imaplib.IMAP4_SSL(IMAP_HOST)
                mail.login(IMAP_USER, IMAP_PW)
                mail.select('INBOX')
                _, nums = mail.search(None, 'FROM', '"account.help@amd.com"', 'UNSEEN')
                if nums[0]:
                    for n in nums[0].split():
                        if n in seen: continue
                        seen.add(n)
                        _, d = mail.fetch(n, '(RFC822)')
                        msg = em_mod.message_from_bytes(d[0][1])
                        if email_addr.lower() not in msg.get("To", "").lower(): continue
                        body = ""
                        if msg.is_multipart():
                            for p in msg.walk():
                                if p.get_content_type() == "text/plain":
                                    body = p.get_payload(decode=True).decode("utf-8", errors="replace"); break
                        else:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                        cm = re.search(r"(\d{6})", body)
                        if cm: otp = cm.group(1); mail.logout(); break
                mail.logout()
                if otp: break
            except: pass
            time.sleep(5)

        if not otp: log("No OTP", "❌"); return None
        log(f"OTP: {otp}")

        r3 = s.post(f"{OKTA}/idp/idx/challenge/answer", json={
            "credentials": {"passcode": otp}, "stateHandle": sh2,
        }, headers={"accept": "application/json; okta-version=1.0.0", "content-type": "application/json",
                    "x-okta-user-agent-extended": "okta-auth-js/6.9.0 okta-signin-widget-6.9.0 okta-hosted"})
        redir = r3.json().get("success", {}).get("href", "")
        if not redir: log("No redirect", "❌"); return None

    # Follow redirect → auth code → token
    r4 = s.get(redir, allow_redirects=False)
    loc = r4.headers.get("Location", "")
    code = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query).get("code", [None])[0]
    if not code: log("No auth code", "❌"); return None

    r5 = req.post(f"{OKTA}/oauth2/default/v1/token", data={
        "grant_type": "authorization_code", "redirect_uri": REDIR,
        "code": code, "code_verifier": verifier, "client_id": CID,
    }, headers={"accept": "application/json", "content-type": "application/x-www-form-urlencoded"})
    bearer = r5.json().get("access_token", "")
    if bearer: log(f"Bearer OK", "✅"); return bearer
    log("Token failed", "❌"); return None


# ═══════════════════════════════════════════════════════════════
# STEP 5: SUBMIT CREDIT REQUEST (CloakBrowser)
# ═══════════════════════════════════════════════════════════════
async def step5_credit(page, person):
    log("Submitting credit request...")
    await page.goto(CREDIT_FORM_URL, wait_until="networkidle", timeout=60000)
    await page.wait_for_function('typeof MktoForms2 !== "undefined" && MktoForms2.allForms().length > 0', timeout=30000)
    await page.wait_for_timeout(2000)

    form_values = {
        "FirstName": person["first"],
        "Email": person["email"],
        "githubHandle": person["github"],
        "company_linkedin_handle__c_lead": "",
        "Country": person["country_code"],
        "PostalCode": str(random.randint(10000, 99999)),
        "Type__c": random.choice(["Independent developer", "Member of opensource project", "Member of a corporation"]),
        "Company": person["company"],
        "Company__c": person["company"],
        "DaScoopComposer__Email_2__c": person["email"],
        "Contact_Sales_Use_Case__c_lead": person["use_case"],
        "technicalteam": random.choice(["No", "Yes, I am a beginner", "Yes, I am an advanced user"]),
        "h100sUseCase": random.choice(["Inference end point only", "Inference", "Finetuning", "Training"]),
        "Desired_Outcome__c": person["outcome"],
        "Marketing_Comments__c": person["use_case"],
    }

    dev_type = form_values["Type__c"]
    if dev_type == "Member of opensource project":
        form_values["openText"] = f"Contributing to {person['company']} open-source projects. Working on GPU optimization and ROCm compatibility."
    if dev_type == "Member of a corporation":
        form_values["Company__c"] = person["company"]
        form_values["DaScoopComposer__Email_2__c"] = person["email"]

    # Set Type first to trigger conditional fields
    await page.evaluate('(vals) => { MktoForms2.allForms()[0].setValues({"Type__c": vals.Type__c}); }', form_values)
    await page.evaluate('''(val) => {
        const el = document.getElementById("Type__c");
        if (el) { el.value = val; el.dispatchEvent(new Event("change", {bubbles: true})); }
    }''', form_values["Type__c"])
    await page.wait_for_timeout(1500)

    # Set all values via Marketo API
    await page.evaluate('(vals) => { MktoForms2.allForms()[0].setValues(vals); }', form_values)
    await page.wait_for_timeout(1000)

    # Set DOM selects explicitly
    for sel_id in ["Country", "Type__c", "technicalteam", "h100sUseCase"]:
        await page.evaluate(f'''(val) => {{
            const el = document.getElementById("{sel_id}");
            if (el) {{ el.value = val; el.dispatchEvent(new Event("change", {{bubbles: true}})); }}
        }}''', form_values[sel_id])

    await page.wait_for_timeout(500)

    # Validate and fix errors
    is_valid = await page.evaluate('() => MktoForms2.allForms()[0].validate()')
    if not is_valid:
        invalid = await page.evaluate('''() => {
            const els = document.querySelectorAll(".mktoInvalid");
            return Array.from(els).map(e => e.id || e.name);
        }''')
        log(f"Fixing invalid: {invalid}", "⚠️")
        for field_id in invalid:
            if field_id in form_values:
                tag = await page.evaluate(f'() => document.getElementById("{field_id}")?.tagName')
                if tag == "SELECT":
                    await page.select_option(f"#{field_id}", form_values[field_id])
                else:
                    await page.fill(f"#{field_id}", form_values[field_id])
        await page.wait_for_timeout(500)
        await page.evaluate('(vals) => { MktoForms2.allForms()[0].setValues(vals); }', form_values)

    # Submit via Marketo API
    await page.evaluate('() => MktoForms2.allForms()[0].submit()')

    # Wait for redirect
    try:
        await page.wait_for_url("**/devcloud.amd.com/**", timeout=30000)
        log("Credit request submitted!", "✅")
        return True
    except:
        if "devcloud" in page.url:
            log("Credit request submitted!", "✅")
            return True

    log("Credit may have failed", "⚠️")
    return False


# ═══════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════
async def run_pipeline(person):
    email = person["email"]
    print(f"\n{'='*60}")
    print(f"  {person['first']} {person['last']} | {email}")
    print(f"  {person['company']} | {person['country_label']}")
    print(f"{'='*60}")

    # Launch CloakBrowser
    browser = await cloakbrowser.launch_async(headless=True, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    page = await browser.new_page()

    try:
        # Step 1: Register
        if not await step1_register(page, person):
            return {"email": email, "status": "REGISTER_FAILED"}

        # Step 2: Fetch token
        await asyncio.sleep(15)
        token = step2_fetch_token(email, timeout=90)
        if not token:
            return {"email": email, "status": "NO_TOKEN"}

        # Step 3: Activate
        if not await step3_activate(page, token):
            return {"email": email, "status": "ACTIVATE_FAILED"}

        # Step 4: Login (HTTP)
        await asyncio.sleep(5)
        bearer = step4_login(email)
        if not bearer:
            return {"email": email, "status": "LOGIN_FAILED"}

        # Step 5: Credit request
        if not await step5_credit(page, person):
            return {"email": email, "status": "CREDIT_FAILED"}

        with open(SUCCESS_FILE, "a") as f:
            f.write(f"{email}:{PASSWORD}:{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        return {"email": email, "status": "SUCCESS"}
    finally:
        await browser.close()


async def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--email")
    p.add_argument("--name")
    p.add_argument("--company", default="MIT")
    p.add_argument("--country", default="US")
    args = p.parse_args()

    if args.email:
        parts = (args.name or args.email.split("@")[0]).split()
        person = {
            "first": parts[0], "last": parts[-1] if len(parts) > 1 else "User",
            "email": args.email, "github": args.email.split("@")[0].replace(".", ""),
            "company": args.company, "country_code": args.country,
            "country_label": COUNTRY_LABELS.get(args.country, "United States"),
            "use_case": random.choice(USE_CASES), "outcome": random.choice(OUTCOMES),
        }
        result = await run_pipeline(person)
        print(f"\n  {result['status']}: {result['email']}")
    else:
        print(f"\n🚀 AMD Full Pipeline — {args.count} accounts\n")
        results = []
        for i in range(args.count):
            person = generate_person()
            result = await run_pipeline(person)
            results.append(result)
            await asyncio.sleep(random.uniform(3, 7))

        print(f"\n{'='*60}")
        ok = sum(1 for r in results if r["status"] == "SUCCESS")
        for r in results:
            icon = "✅" if r["status"] == "SUCCESS" else "❌"
            print(f"  {icon} {r['email']:45s} → {r['status']}")
        print(f"\n  Success: {ok}/{len(results)}")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
