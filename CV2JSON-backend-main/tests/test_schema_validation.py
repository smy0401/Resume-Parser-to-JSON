import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from src.models.llama_json_validator import (
    CVModel,
    validate_jsonschema,
    validate_pydantic,
)

valid_sample = {
    "details": {"name": "Ali Khan", "summary": "Software dev."},
    "contact": {"emails": ["ali@example.com"], "phones": ["+923001234567"]},
    "experience": [
        {
            "title": "Engineer",
            "company": "ABC",
            "start": "2020",
            "end": "2022",
            "description": "Did stuff",
        }
    ],
    "education": [{"institution": "Lahore Uni", "degree": "BS"}],
    "skills": ["Python", "ML"],
}


def test_jsonschema_valid():
    validate_jsonschema(valid_sample)  # should not raise


def test_pydantic_parse():
    model = validate_pydantic(valid_sample)
    assert isinstance(model, CVModel)
    assert model.details["name"] == "Ali Khan"
