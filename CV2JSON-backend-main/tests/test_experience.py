# tests/test_experience.py
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.compose.experience import compose_experience


def test_compose_basic_present():
    raw = "Acme Corp\nSoftware Engineer\nMay 2019 - Present\n"
    llm_json = {
        "experiences": [
            {
                "company": "Acme Corp",
                "role": "Software Engineer",
                "start_date": "May 2019",
                "end_date": "Present",
                "confidence": 0.92,
            }
        ]
    }
    spans = [
        {"label": "COMPANY", "text": "Acme Corp", "start": 0, "end": 9},
        {"label": "ROLE", "text": "Software Engineer", "start": 10, "end": 27},
        {"label": "DATE", "text": "May 2019 - Present", "start": 28, "end": 47},
    ]
    out = compose_experience(raw, llm_json, spans)
    assert len(out) == 1
    e = out[0]
    assert e["company"] == "Acme Corp"
    assert e["role"] == "Software Engineer"
    # present marker should set is_current true and end_date None
    assert e["is_current"] is True
    assert e["end_date"] is None
    assert isinstance(e["start_date"], str)
    assert "company" in e["source_spans"] and e["source_spans"]["company"]
