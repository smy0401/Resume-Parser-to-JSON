import pytest

from src.normalizers.normalizers import (
    normalize_date,
    normalize_location,
    normalize_phone,
)


# -------- Date Tests --------
@pytest.mark.parametrize(
    "input_date,expected",
    [
        ("2025-09-16", "2025-09-16"),  # ISO format
        ("16-09-2025", "2025-09-16"),  # DD-MM-YYYY
        ("16/09/2025", "2025-09-16"),  # DD/MM/YYYY
        ("2025/09/16", "2025-09-16"),  # YYYY/MM/DD
        ("2025.09.16", "2025-09-16"),  # YYYY.MM.DD
        ("2025", "2025-01-01"),  # Year only
        ("2025-09", "2025-09-01"),  # Year-Month
        ("", None),  # Empty
        ("invalid", None),  # Non-date string
    ],
)
def test_normalize_date(input_date, expected):
    assert normalize_date(input_date) == expected


# -------- Phone Tests --------
@pytest.mark.parametrize(
    "input_phone,expected",
    [
        ("+92 300 1234567", "+923001234567"),  # Already E.164 valid
        ("0300-1234567", "+923001234567"),  # Local PK number
        ("(042) 12345678", "+924212345678"),
        ("051 2345678", "+92512345678"),  # Lahore landline
        ("051 2345678", "+92512345678"),  # Islamabad landline
        ("021-9876543", "+92219876543"),  # Karachi landline
        ("(091) 7654321", "+92917654321"),  # Peshawar landline
        ("12345", None),  # Invalid
        ("", None),  # Empty
    ],
)
def test_normalize_phone(input_phone, expected):
    assert normalize_phone(input_phone) == expected


# -------- Location Tests --------
@pytest.mark.parametrize(
    "input_line,expected",
    [
        (
            "I live in Karachi",
            {"city": "Karachi", "region": "Sindh", "country": "Pakistan"},
        ),
        (
            "Address: Lahore Cantt",
            {"city": "Lahore", "region": "Punjab", "country": "Pakistan"},
        ),
        (
            "Islamabad, PK",
            {"city": "Islamabad", "region": "ICT", "country": "Pakistan"},
        ),
        ("Pakistan Zindabad", {"country": "Pakistan"}),
        ("Unknown City", {"raw": "unknown city"}),
        ("", None),
    ],
)
def test_normalize_location(input_line, expected):
    assert normalize_location(input_line) == expected
