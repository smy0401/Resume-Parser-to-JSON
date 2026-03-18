import re
from typing import Dict, List

import phonenumbers

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
URL_RE = re.compile(r"\b(?:https?://|www\.)[^\s,;()<>]+\b", re.IGNORECASE)

# months short/long for date patterns
_MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"


def extract_contacts(text: str, regions: List[str] = None) -> Dict[str, List[str]]:
    """
    Extract emails, phones (E.164), and URLs from text.
    `regions` is a list of region codes to try for phone detection (e.g. ['PK']).
    """
    if regions is None:
        # reasonable defaults; add regions that you expect commonly
        regions = ["PK"]

    results = {"emails": [], "phones": [], "urls": []}
    # emails
    results["emails"] = list(
        dict.fromkeys(EMAIL_RE.findall(text))
    )  # preserve order, dedupe

    # URLs
    raw_urls = URL_RE.findall(text)
    results["urls"] = list(dict.fromkeys(raw_urls))

    phones_set = []
    phones_seen = set()
    for region in regions:
        try:
            for match in phonenumbers.PhoneNumberMatcher(text, region):
                try:
                    e164 = phonenumbers.format_number(
                        match.number, phonenumbers.PhoneNumberFormat.E164
                    )
                    if e164 not in phones_seen:
                        phones_seen.add(e164)
                        phones_set.append(e164)
                except Exception:
                    continue
        except Exception:
            # region code might be invalid - skip
            continue

    results["phones"] = phones_set
    return results


def extract_dates(text: str) -> List[str]:
    """
    Extract date ranges and standalone dates. Returns a list of matched strings,
    ordered by appearance, de-duplicated.
    """
    patterns = [
        # Month Year - Month Year  (e.g. Jan 2020 - Mar 2022 or January 2020 to March 2022)
        rf"{_MONTHS}\s+\d{{4}}\s*(?:-|–|—|to)\s*{_MONTHS}\s+\d{{4}}",
        # Month Year - Present (e.g. Jan 2020 - Present)
        rf"{_MONTHS}\s+\d{{4}}\s*(?:-|–|—|to)\s*(?:present|now|current)",
        # numeric date ranges: 01/2018 - 03/2020 or 2018-2020
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\s*(?:-|to)\s*\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b\d{4}\s*(?:-|–|—|to)\s*(?:\d{4}|present)\b",
        # standalone Month Year (Jan 2020)
        rf"{_MONTHS}\s+\d{{4}}",
        # standalone dd/mm/yyyy or mm/dd/yyyy
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        # standalone 4-digit year
        r"\b\d{4}\b",
    ]

    combined = re.compile("|".join(patterns), re.IGNORECASE)
    seen = set()
    results = []
    for m in combined.finditer(text):
        s = m.group(0).strip()
        if s not in seen:
            seen.add(s)
            results.append(s)
    return results
