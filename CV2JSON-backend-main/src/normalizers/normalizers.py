import re
from datetime import datetime

import phonenumbers


# -------- Date Normalizer --------
def normalize_date(token: str) -> str | None:
    """
    Normalize date string into ISO format (YYYY-MM-DD).
    If month/day missing, fallback to 01.
    """
    if not token:
        return None

    # Try multiple date formats
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y.%m.%d"]

    for fmt in formats:
        try:
            dt = datetime.strptime(token, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # If token looks like just year or year-month
    year_match = re.match(r"^(\d{4})([-/]?)(\d{1,2})?$", token)
    if year_match:
        year = int(year_match.group(1))
        month = int(year_match.group(3)) if year_match.group(3) else 1
        return f"{year:04d}-{month:02d}-01"

    return None


# -------- Phone Normalizer --------
def normalize_phone(raw: str, default_country: str = "PK") -> str | None:
    """
    Normalize phone number to E.164 format.
    """
    try:
        parsed = phonenumbers.parse(raw, default_country)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
    except Exception:
        return None
    return None


# -------- Location Normalizer --------
def normalize_location(line: str) -> dict | None:

    if not line:
        return None

    line = line.lower()
    gazetteer = {
        "pakistan": {"country": "Pakistan"},
        # Sindh
        "sindh": {"region": "Sindh", "country": "Pakistan"},
        "karachi": {
            "city": "Karachi",
            "district": "Karachi",
            "region": "Sindh",
            "country": "Pakistan",
        },
        "korangi": {
            "city": "Karachi",
            "district": "Korangi",
            "region": "Sindh",
            "country": "Pakistan",
        },
        "hyderabad": {
            "city": "Hyderabad",
            "district": "Hyderabad",
            "region": "Sindh",
            "country": "Pakistan",
        },
        # Punjab
        "punjab": {"region": "Punjab", "country": "Pakistan"},
        "lahore": {
            "city": "Lahore",
            "district": "Lahore",
            "region": "Punjab",
            "country": "Pakistan",
        },
        "faisalabad": {
            "city": "Faisalabad",
            "district": "Faisalabad",
            "region": "Punjab",
            "country": "Pakistan",
        },
        # KPK
        "khyber pakhtunkhwa": {"region": "Khyber Pakhtunkhwa", "country": "Pakistan"},
        "peshawar": {
            "city": "Peshawar",
            "district": "Peshawar",
            "region": "KPK",
            "country": "Pakistan",
        },
        "mardan": {
            "city": "Mardan",
            "district": "Mardan",
            "region": "KPK",
            "country": "Pakistan",
        },
        # Balochistan
        "balochistan": {"region": "Balochistan", "country": "Pakistan"},
        "quetta": {
            "city": "Quetta",
            "district": "Quetta",
            "region": "Balochistan",
            "country": "Pakistan",
        },
        # ICT
        "islamabad": {
            "city": "Islamabad",
            "district": "Islamabad",
            "region": "ICT",
            "country": "Pakistan",
        },
        # Gilgit-Baltistan
        "gilgit": {
            "city": "Gilgit",
            "district": "Gilgit",
            "region": "Gilgit-Baltistan",
            "country": "Pakistan",
        },
        # Azad Jammu & Kashmir
        "muzaffarabad": {
            "city": "Muzaffarabad",
            "district": "Muzaffarabad",
            "region": "AJK",
            "country": "Pakistan",
        },
    }

    for key, val in gazetteer.items():
        if key in line:
            return val

    return {"raw": line}
# -------- Master Normalizer --------
def normalize_all(data: dict) -> dict:
    """
    Normalize all major fields in the structured resume dictionary.
    """
    contacts = data.get("contacts", {})
    if "phone" in contacts:
        contacts["phone"] = normalize_phone(contacts["phone"])
    if "address" in contacts:
        loc = normalize_location(contacts["address"])
        if loc:
            contacts["location"] = loc

    data["contacts"] = contacts

    # Normalize dates inside experience
    for exp in data.get("experience", []):
        if "start_date" in exp:
            exp["start_date"] = normalize_date(exp["start_date"])
        if "end_date" in exp:
            exp["end_date"] = normalize_date(exp["end_date"])

    return data
