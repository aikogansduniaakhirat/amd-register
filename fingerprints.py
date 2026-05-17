"""
Browser fingerprint profiles for AMD scripts.
Each profile simulates a different device/location combination.
Import and use: fingerprint = get_fingerprint(index_or_country)
"""
import random

# Timezone + locale combos matched to countries
FINGERPRINTS = [
    {"timezone": "America/New_York", "locale": "en-US", "viewport": {"width": 1920, "height": 1080}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "America/Los_Angeles", "locale": "en-US", "viewport": {"width": 1440, "height": 900}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "America/Chicago", "locale": "en-US", "viewport": {"width": 1366, "height": 768}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "America/Denver", "locale": "en-US", "viewport": {"width": 2560, "height": 1440}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "America/Toronto", "locale": "en-CA", "viewport": {"width": 1680, "height": 1050}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "Europe/London", "locale": "en-GB", "viewport": {"width": 1920, "height": 1080}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Europe/Paris", "locale": "fr-FR", "viewport": {"width": 1440, "height": 900}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "Europe/Berlin", "locale": "de-DE", "viewport": {"width": 1920, "height": 1200}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Europe/Madrid", "locale": "es-ES", "viewport": {"width": 1366, "height": 768}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Europe/Rome", "locale": "it-IT", "viewport": {"width": 1536, "height": 864}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Europe/Stockholm", "locale": "sv-SE", "viewport": {"width": 2560, "height": 1440}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "Europe/Copenhagen", "locale": "da-DK", "viewport": {"width": 1920, "height": 1080}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Europe/Amsterdam", "locale": "nl-NL", "viewport": {"width": 1680, "height": 1050}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Europe/Zurich", "locale": "de-CH", "viewport": {"width": 1440, "height": 900}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "Asia/Tokyo", "locale": "ja-JP", "viewport": {"width": 1920, "height": 1080}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Asia/Seoul", "locale": "ko-KR", "viewport": {"width": 1920, "height": 1080}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Asia/Shanghai", "locale": "zh-CN", "viewport": {"width": 1366, "height": 768}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Asia/Kolkata", "locale": "en-IN", "viewport": {"width": 1366, "height": 768}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Asia/Karachi", "locale": "en-PK", "viewport": {"width": 1920, "height": 1080}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Asia/Dubai", "locale": "ar-AE", "viewport": {"width": 1440, "height": 900}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "Africa/Cairo", "locale": "ar-EG", "viewport": {"width": 1366, "height": 768}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Australia/Sydney", "locale": "en-AU", "viewport": {"width": 1920, "height": 1080}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "Australia/Melbourne", "locale": "en-AU", "viewport": {"width": 1680, "height": 1050}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "America/Sao_Paulo", "locale": "pt-BR", "viewport": {"width": 1366, "height": 768}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "America/Argentina/Buenos_Aires", "locale": "es-AR", "viewport": {"width": 1920, "height": 1080}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Asia/Singapore", "locale": "en-SG", "viewport": {"width": 1440, "height": 900}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "Asia/Jerusalem", "locale": "he-IL", "viewport": {"width": 1920, "height": 1080}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Europe/Helsinki", "locale": "fi-FI", "viewport": {"width": 2560, "height": 1440}, "platform": "Win32", "ua_hint": "Windows"},
    {"timezone": "Europe/Dublin", "locale": "en-IE", "viewport": {"width": 1440, "height": 900}, "platform": "MacIntel", "ua_hint": "Macintosh"},
    {"timezone": "Europe/Oslo", "locale": "nb-NO", "viewport": {"width": 1920, "height": 1200}, "platform": "Win32", "ua_hint": "Windows"},
]

# Country code → matching timezone indices
COUNTRY_TZ_MAP = {
    "US": [0, 1, 2, 3], "CA": [4], "GB": [5], "FR": [6], "DE": [7],
    "ES": [8], "IT": [9], "SE": [10], "DK": [11], "NL": [12], "CH": [13],
    "JP": [14], "KR": [15], "CN": [16], "IN": [17], "PK": [18],
    "AE": [19], "EG": [20], "AU": [21, 22], "BR": [23], "AR": [24],
    "SG": [25], "IL": [26], "FI": [27], "IE": [28], "NO": [29],
}

# Chrome versions to rotate
CHROME_VERSIONS = [
    "124.0.6367.118", "124.0.6367.91", "125.0.6422.60", "125.0.6422.76",
    "125.0.6422.112", "126.0.6478.36", "126.0.6478.61", "126.0.6478.114",
    "127.0.6533.17", "127.0.6533.72",
]


def get_user_agent(fp):
    """Generate a realistic user agent based on fingerprint."""
    chrome_ver = random.choice(CHROME_VERSIONS)
    major = chrome_ver.split(".")[0]
    
    if fp["ua_hint"] == "Macintosh":
        mac_ver = random.choice(["10_15_7", "13_4_1", "14_0", "14_2_1", "14_4"])
        return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_ver}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36"
    else:
        win_ver = random.choice(["10.0", "10.0", "10.0", "11.0"])
        return f"Mozilla/5.0 (Windows NT {win_ver}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36"


def get_fingerprint(country_code=None, index=None):
    """
    Get a fingerprint profile matched to country, or by index, or random.
    Returns dict with: timezone, locale, viewport, user_agent, platform
    """
    if country_code and country_code in COUNTRY_TZ_MAP:
        idx = random.choice(COUNTRY_TZ_MAP[country_code])
    elif index is not None:
        idx = index % len(FINGERPRINTS)
    else:
        idx = random.randint(0, len(FINGERPRINTS) - 1)
    
    fp = FINGERPRINTS[idx].copy()
    fp["user_agent"] = get_user_agent(fp)
    return fp


def get_fingerprint_for_persona(persona, index):
    """Get fingerprint matched to persona's country."""
    country = persona.get("country", None)
    return get_fingerprint(country_code=country, index=index)
