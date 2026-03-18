import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.quality.confidence import combine_confidences, score_field


def test_rule_only_contact():
    score, explains = score_field(
        "email", rule_match=True, normalization_succeeded=True, field_type="contact"
    )
    assert score > 0.9
    assert "rule_match" in explains


def test_llm_only_company():
    score, explains = score_field(
        "company", rule_match=False, llm_conf=0.7, field_type="company"
    )
    assert 0.4 < score < 0.8  # model drives result for company
    assert any(x.startswith("llm_conf") for x in explains)


def test_agreement_boost():
    score1, _ = score_field(
        "title",
        rule_match=True,
        normalization_succeeded=True,
        llm_conf=0.94,
        field_type="title",
    )
    # high because both sources agree
    assert score1 > 0.95


def test_year_only_penalty():
    score, explains = score_field(
        "start_date",
        rule_match=True,
        normalization_succeeded=True,
        llm_conf=0.9,
        field_type="date",
        year_only_date=True,
    )
    assert "year_only_penalty" in explains
    assert score < 0.9


def test_combine_confidences():
    comb = combine_confidences({"company": 0.9, "title": 0.8, "start_date": 0.7})
    assert 0.7 < comb < 0.9
