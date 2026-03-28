"""
PNG Real Estate — Data Normalization Engine
============================================
Takes raw, messy text from Facebook posts or Hausples and returns
a structured JSON object with normalized fields.

Install: pip install phonenumbers
"""

import re
import json
import math
from typing import Optional
from dataclasses import dataclass, asdict

try:
    import phonenumbers
    HAS_PHONENUMBERS = True
except ImportError:
    HAS_PHONENUMBERS = False


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

SUBURB_ALIASES: dict[str, str] = {
    "waigani": "Waigani",
    "boroko": "Boroko",
    "gerehu": "Gerehu",
    "gordons": "Gordons",
    "koki": "Koki",
    "hohola": "Hohola",
    "tokarara": "Tokarara",
    "tokerara": "Tokarara",          # common typo
    "six-mile": "Six Mile",
    "six mile": "Six Mile",
    "nine mile": "Nine Mile",
    "8 mile": "Eight Mile",
    "eight mile": "Eight Mile",
    "erima": "Erima",
    "morata": "Morata",
    "badili": "Badili",
    "lawes road": "Lawes Road",
    "port moresby": "Port Moresby",
    "pom": "Port Moresby",
    "ncd": "Port Moresby",           # National Capital District
    "lae": "Lae",
    "madang": "Madang",
    "mt hagen": "Mt Hagen",
    "mount hagen": "Mt Hagen",
}

PROPERTY_TYPE_PATTERNS: list[tuple[str, str]] = [
    (r"\b(house|home|bungalow|dwelling)\b", "House"),
    (r"\b(flat|apartment|apt|unit)\b", "Apartment"),
    (r"\b(studio)\b", "Studio"),
    (r"\b(townhouse|town house|villa)\b", "Townhouse"),
    (r"\b(room|bedsit|single room)\b", "Room"),
    (r"\b(land|block|plot|allotment)\b", "Land"),
    (r"\b(commercial|office|shop|warehouse)\b", "Commercial"),
    (r"\b(compound|complex)\b", "Compound"),
]

# Middleman indicator keywords
MIDDLEMAN_KEYWORDS = [
    "agent", "real estate agent", "commission", "finder", "finder's fee",
    "i can help", "i can arrange", "contact me for details", "middleman",
    "broker", "property manager", "pm me", "message me for info",
]

# Legal & Title Keywords
TITLE_PATTERNS = {
    "State Lease": [r"state lease", r"99 year lease", r"c\.of\.t", r"certificate of title", r"formal title"],
    "Customary (ILG)": [r"customary land", r"ilg", r"incorporated land group", r"clan land"],
}

LEGAL_WARNINGS = {
    "Dispute": [r"under dispute", r"land dispute", r"court case", r"legal battle"],
    "Caveat": [r"caveat", r"restriction", r"frozen"],
    "Unclear": [r"no title", r"paperwork in progress", r"awaiting ilg"],
}

# PGK conversion factors → all to monthly
PRICE_PERIOD_MULTIPLIERS = {
    "day":    30,
    "daily":  30,
    "week":   4.333,
    "weekly": 4.333,
    "wk":     4.333,
    "w":      4.333,       # "500k/w"
    "fortnight": 2.1665,
    "fn":     2.1665,
    "month":  1,
    "monthly":1,
    "mo":     1,
    "mth":    1,
    "m":      1,
    "year":   1/12,
    "yearly": 1/12,
    "annual": 1/12,
    "pa":     1/12,
    "p.a":    1/12,
}


# ---------------------------------------------------------------------------
# DATA MODEL
# ---------------------------------------------------------------------------

@dataclass
class NormalizedListing:
    price_pgk_monthly: Optional[int]
    price_raw: str
    price_confidence: str          # "high" | "medium" | "low"
    location: Optional[str]        # raw location string
    suburb: Optional[str]          # canonical suburb name
    property_type: Optional[str]
    bedrooms: Optional[int]
    sqm: Optional[float]
    is_for_sale: bool
    contact_info: dict             # {phones: [], emails: []}
    is_middleman: bool
    middleman_flags: list[str]
    health_score: int              # 0-100 based on completeness
    is_verified: bool              # Cross-referenced with trusted registries
    source_text: str


# ---------------------------------------------------------------------------
# PRICE PARSING
# ---------------------------------------------------------------------------

def parse_price(text: str) -> tuple[Optional[int], str, str]:
    """
    Returns (price_monthly_pgk, price_raw_match, confidence).

    Handles patterns like:
        "K2,500 per month"      → 2500
        "500 kina a week"       → 2167
        "PGK1200/month"         → 1200
        "1500 per fortnight"    → 3248
        "K600pw"                → 2600
        "2000K monthly"         → 2000
        "asking 800 per week"   → 3467
    """
    # Normalize text
    t = text.lower()
    t = t.replace(",", "").replace("pgk", "k").replace("kina", "k").replace("png kina", "k")

    # Pattern: optional K prefix, digits, optional K suffix, optional period
    # Groups: (prefix_k)(amount)(suffix_k)(period)
    pattern = re.compile(
        r"(?:k\s*)?(\d+(?:\.\d+)?)\s*k?\s*"           # amount (e.g. 1500, 1500k)
        r"(?:"
        r"\s*(?:per|a|p|/|-)\s*"                        # separator
        r"(day|daily|week|weekly|wk|w|fortnight|fn|month|monthly|mo|mth|m|year|yearly|annual|pa|p\.a)"
        r")?",
        re.IGNORECASE
    )

    # Also match K-prefixed patterns: K2500/month, K 1200 per week
    k_prefix_pattern = re.compile(
        r"k\s*(\d[\d,]*(?:\.\d+)?)"                    # K followed by number
        r"(?:\s*(?:per|a|p|/|-)\s*"
        r"(day|daily|week|weekly|wk|w|fortnight|fn|month|monthly|mo|mth|m|year|yearly|annual|pa|p\.a)"
        r")?",
        re.IGNORECASE
    )

    best_price = None
    best_raw = ""
    confidence = "low"

    for rx in [k_prefix_pattern, pattern]:
        for m in rx.finditer(t):
            raw_num = m.group(1).replace(",", "")
            try:
                amount = float(raw_num)
            except ValueError:
                continue

            # Sanity check — PNG rent is typically 500–50000 PGK/month
            if amount < 50 or amount > 500_000:
                continue

            period = m.group(2).lower() if m.group(2) else None
            raw_match = m.group(0)

            if period:
                multiplier = PRICE_PERIOD_MULTIPLIERS.get(period, 1)
                monthly = amount * multiplier
                conf = "high"
            else:
                # No period found — heuristic: if <= 2000, likely weekly; else monthly
                if amount <= 2000:
                    monthly = amount * 4.333
                    conf = "medium"
                else:
                    monthly = amount
                    conf = "medium"

            monthly_int = int(round(monthly))

            # Prefer the match with an explicit period
            if best_price is None or (period and confidence != "high"):
                best_price = monthly_int
                best_raw = raw_match.strip()
                confidence = conf

    return best_price, best_raw, confidence


# ---------------------------------------------------------------------------
# LOCATION PARSING
# ---------------------------------------------------------------------------

def parse_location(text: str) -> tuple[Optional[str], Optional[str]]:
    """Returns (raw_location_phrase, canonical_suburb)."""
    text_lower = text.lower()

    found_suburb = None
    for alias, canonical in SUBURB_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
            found_suburb = canonical
            break

    # Try to extract a location phrase around the suburb
    if found_suburb:
        pattern = re.compile(
            r'(?:in|at|located|location[:\s]+)?\s*'
            r'(?:' + '|'.join(re.escape(a) for a in SUBURB_ALIASES) + r')'
            r'(?:\s*,\s*[a-z ]+)?',
            re.IGNORECASE
        )
        m = pattern.search(text_lower)
        raw_loc = m.group(0).strip() if m else found_suburb
    else:
        raw_loc = None

    return raw_loc, found_suburb


# ---------------------------------------------------------------------------
# PROPERTY TYPE PARSING
# ---------------------------------------------------------------------------

def parse_property_type(text: str) -> Optional[str]:
    text_lower = text.lower()
    for pattern, label in PROPERTY_TYPE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return label
    return None


# ---------------------------------------------------------------------------
# BEDROOMS PARSING
# ---------------------------------------------------------------------------

def parse_bedrooms(text: str) -> Optional[int]:
    patterns = [
        r'(\d+)\s*(?:bed(?:room)?s?|br|bdrm)',
        r'(\d+)\s*b/r',
        r'(?:bed(?:room)?s?|br|bdrm)\s*[:\-]?\s*(\d+)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 20:
                return n
    return None

def parse_sqm(text: str) -> Optional[float]:
    pattern = r'(\d+(?:\.\d+)?)\s*(?:sqm|sq\.m|m2|m²|square\s*meters?)'
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        try:
            val = float(m.group(1))
            return val if 5 <= val <= 50000 else None
        except ValueError:
            return None
    return None

def parse_is_sale(text: str) -> bool:
    t = text.lower()
    if any(kw in t for kw in ["for sale", "selling", "/sale/", "price on application", "poa"]):
        if any(kw in t for kw in ["for rent", "to let", "/rent/"]):
            # ambiguous, but "sale" is often more specific if mentioned
            return "for sale" in t or "/sale/" in t
        return True
    return False

# ---------------------------------------------------------------------------
# CONTACT INFO PARSING
# ---------------------------------------------------------------------------

def parse_contact_info(text: str) -> dict:
    phones = []
    emails = []

    # PNG phone patterns: 7xxx xxxx (mobile), 3xx xxxx (landline), +675...
    phone_patterns = [
        r'\+675[\s\-]?\d{3,4}[\s\-]?\d{3,4}',
        r'\b675[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b',
        r'\b7\d{3}[\s\-]?\d{4}\b',          # PNG mobile: 7xxx xxxx
        r'\b3\d{2}[\s\-]?\d{4}\b',          # PNG landline
    ]
    for p in phone_patterns:
        phones.extend(re.findall(p, text))

    if HAS_PHONENUMBERS:
        validated = []
        for raw in phones:
            try:
                parsed = phonenumbers.parse(raw, "PG")
                if phonenumbers.is_valid_number(parsed):
                    validated.append(phonenumbers.format_number(
                        parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    ))
            except Exception:
                validated.append(raw.strip())
        phones = list(dict.fromkeys(validated))  # dedup, preserve order
    else:
        phones = list(dict.fromkeys(p.strip() for p in phones))

    # Emails
    email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = list(dict.fromkeys(re.findall(email_pattern, text)))

    return {"phones": phones, "emails": emails}


# ---------------------------------------------------------------------------
# MIDDLEMAN DETECTION
# ---------------------------------------------------------------------------

def detect_middleman(text: str) -> tuple[bool, list[str]]:
    text_lower = text.lower()
    flags = [kw for kw in MIDDLEMAN_KEYWORDS if kw in text_lower]
    return len(flags) > 0, flags

def classify_title_status(text: str) -> str:
    """Identify if the land is State Lease, Customary, or Unknown."""
    t = text.lower()
    for status, patterns in TITLE_PATTERNS.items():
        if any(re.search(p, t) for p in patterns):
            return status
    return "Unknown / TBC"

def detect_legal_flags(text: str) -> list[str]:
    """Detect red flags related to land disputes or missing paperwork."""
    t = text.lower()
    flags = []
    for label, patterns in LEGAL_WARNINGS.items():
        if any(re.search(p, t) for p in patterns):
            flags.append(label)
    return flags

# ---------------------------------------------------------------------------
# MAIN NORMALIZER
# ---------------------------------------------------------------------------

def calculate_health_score(price, suburb, p_type, beds, sqm, contacts, text) -> int:
    """Assign a score (0-100) based on data completeness and descriptive quality."""
    score = 0
    if price: score += 25
    if suburb: score += 15
    if p_type: score += 15
    if beds: score += 10
    if sqm: score += 10
    if contacts.get("phones"): score += 15
    if len(text) > 150: score += 10
    return min(100, score)

# Known business landlines and trusted agency numbers in PNG
TRUSTED_REGISTRY = [
    "+675 320 0222", # Strickland
    "+675 321 4088", # Professionals
    "+675 320 0651", # Ray White
    "+675 321 2121", # Century 21
    "+675 325 2544", # DAC
]

def check_verification(contacts: dict) -> bool:
    """Verify listing by cross-referencing contact info with known business registries."""
    phones = contacts.get("phones", [])
    for p in phones:
        # Normalize for comparison
        p_clean = p.replace(" ", "").replace("-", "")

        # 1. Exact or cleaned match against registry
        if p in TRUSTED_REGISTRY or any(p_clean == tr.replace(" ","").replace("-","") for tr in TRUSTED_REGISTRY):
            return True

        # 2. Heuristic: PNG landlines (3xx xxxx) are highly credible
        if p_clean.startswith("+6753") and len(p_clean) == 12:
            return True
        if p_clean.startswith("3") and len(p_clean) == 7:
            return True

    return False

def normalize(raw_text: str) -> dict:
    """
    Core normalization function with Trust & Verification enhancements.

    Input : raw string from Facebook post or scraped listing.
    Output: structured dict ready for MongoDB insertion.
    """
    price_monthly, price_raw, price_confidence = parse_price(raw_text)
    location_raw, suburb = parse_location(raw_text)
    property_type = parse_property_type(raw_text)
    bedrooms = parse_bedrooms(raw_text)
    sqm = parse_sqm(raw_text)
    is_sale = parse_is_sale(raw_text)
    contact_info = parse_contact_info(raw_text)
    is_middleman, middleman_flags = detect_middleman(raw_text)

    health_score = calculate_health_score(
        price_monthly, suburb, property_type, bedrooms, sqm, contact_info, raw_text
    )
    is_verified = check_verification(contact_info)

    listing = NormalizedListing(
        price_pgk_monthly=price_monthly,
        price_raw=price_raw,
        price_confidence=price_confidence,
        location=location_raw,
        suburb=suburb,
        property_type=property_type,
        bedrooms=bedrooms,
        sqm=sqm,
        is_for_sale=is_sale,
        contact_info=contact_info,
        is_middleman=is_middleman,
        middleman_flags=middleman_flags,
        health_score=health_score,
        is_verified=is_verified,
        source_text=raw_text[:500],   # truncate for storage
    )
    return asdict(listing)


# ---------------------------------------------------------------------------
# TEST CASES
# ---------------------------------------------------------------------------

TEST_CASES = [
    # (description, raw_text)
    (
        "Weekly kina with contact",
        "3 bedroom house in Boroko. K500 per week. Call 71234567. Available now."
    ),
    (
        "Monthly with K prefix ambiguous suburb",
        "Nice 2bdrm flat Waigani. K2,500/month. Email landlord@gmail.com"
    ),
    (
        "Ambiguous no period — Facebook style",
        "House for rent 4 bedrooms gerehu stage 3. 1800 kina. PM me 72012345"
    ),
    (
        "Fortnightly price with agent flag",
        "Luxury apartment Gordons. PGK3200 per fortnight. Contact our agent: commission applies. +675 321 1234"
    ),
    (
        "Room only, no suburb, annual price",
        "Single room available. K12,000 per year. Tokarara area. Whatsapp 70987654"
    ),
    (
        "500 kina a week variant",
        "500 kina a week, 2br unit, Hohola, ring me on 71111222"
    ),
    (
        "No price found — graceful degradation",
        "House for rent in Boroko. Serious inquiries only. 71234567"
    ),
]


def run_tests():
    print("=" * 70)
    print("PNG Real Estate Normalizer — Test Run")
    print("=" * 70)
    for label, text in TEST_CASES:
        print(f"\n[ {label} ]")
        print(f"  Input: {text[:80]}...")
        result = normalize(text)
        print(f"  price_pgk_monthly : {result['price_pgk_monthly']} ({result['price_confidence']})")
        print(f"  suburb            : {result['suburb']}")
        print(f"  property_type     : {result['property_type']}")
        print(f"  bedrooms          : {result['bedrooms']}")
        print(f"  contacts          : {result['contact_info']}")
        print(f"  is_middleman      : {result['is_middleman']} {result['middleman_flags']}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_tests()

    # Also show a pretty JSON dump of one result
    sample = "3 bedroom house in Boroko available for rent. K500 per week. Call 71234567. Clean and spacious."
    print("\nFull JSON output for sample:")
    print(json.dumps(normalize(sample), indent=2))
