# tests/test_section_splitter.py
from src.heuristics.section_splitter import split_sections


def test_split_basic():
    text = """
SUMMARY
Experienced backend engineer with 6 years.

EXPERIENCE
Company A - Backend Engineer
2017 - 2019

WORK HISTORY
Company B - Senior Engineer
2019 - Present

EDUCATION
BSc Computer Science, 2016
"""
    sections = split_sections(text)
    # Expect canonical keys
    assert "summary" in sections
    assert "experience" in sections
    assert "education" in sections

    # experience should contain Company A and Company B (merged into same canonical key)
    assert "Company A" in sections["experience"]["text"]
    assert "Company B" in sections["experience"]["text"]
