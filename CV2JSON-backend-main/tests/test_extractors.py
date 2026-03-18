from src.heuristics.extractors import extract_contacts, extract_dates


def test_contacts_and_phones():
    text = "Reach me at test.user@example.com or visit https://github.com/devsterlabs. Phone: +92 300-1234567 or 021 1234567"
    contacts = extract_contacts(text, regions=["PK"])
    assert "test.user@example.com" in contacts["emails"]
    assert any(p.startswith("+92") for p in contacts["phones"])
    assert "https://github.com/devsterlabs" in contacts["urls"]


def test_dates():
    text = (
        "Worked from Jan 2020 - Mar 2022. Graduation: 12/05/2018. Internship 2016-2017"
    )
    dates = extract_dates(text)
    assert any("2020" in d for d in dates)
    assert any("2018" in d for d in dates)
    assert any("2016" in d for d in dates)
