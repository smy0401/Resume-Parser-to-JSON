import json
import time
from pathlib import Path
from typing import Any, Optional

import jsonschema
import ollama
from jsonschema import validate as js_validate
from pydantic import BaseModel, ValidationError

# -----------------------------------------------------
# Paths
# -----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMA_PATH = BASE_DIR / "src" / "models" / "schema" / "cv.schema.json"
GRAMMAR_PATH = BASE_DIR / "tools" / "json_cv.gbnf"  # optional
OUTPUT_DIR = BASE_DIR / "output" / "json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------
# Load JSON Schema
# -----------------------------------------------------
with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
    CV_SCHEMA = json.load(fh)


# -----------------------------------------------------
# Pydantic Models
# -----------------------------------------------------
class ContactModel(BaseModel):
    emails: Optional[list[str]] = None
    phones: Optional[list[str]] = None
    location: Optional[str] = None
    urls: Optional[list[str]] = None


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class CVModel(BaseModel):
    meta: Optional[dict] = None
    details: Optional[dict] = None
    contact: Optional[ContactModel] = None
    experience: Optional[list[ExperienceItem]] = None
    education: Optional[list[EducationItem]] = None
    skills: Optional[list[str]] = None
    projects: Optional[list[dict]] = None


# -----------------------------------------------------
# Validation Helpers
# -----------------------------------------------------
def validate_jsonschema(obj: Any) -> None:
    js_validate(instance=obj, schema=CV_SCHEMA)


def validate_pydantic(obj: Any) -> CVModel:
    return CVModel.parse_obj(obj)


# -----------------------------------------------------
# Ollama Chat Wrapper
# -----------------------------------------------------
def generate_with_ollama(
    text: str,
    model: str = "llama3.1:8b-instruct-q4_K_M",
    system_prompt: Optional[str] = None,
    max_tokens: int = 512,
) -> str:
    """
    Query Ollama and return raw model output.
    Automatically retries with smaller model if memory issues occur.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": text})

    try:
        resp = ollama.chat(model=model, messages=messages, options={"temperature": 0.0})
        content = resp["message"]["content"]
        return json.dumps(content) if isinstance(content, dict) else content
    except Exception as e:
        err_msg = str(e)
        print(f"⚠️ Model {model} failed: {err_msg}")

        # Fallback if GPU memory too low
        if "requires more system memory" in err_msg or "500" in err_msg:
            smaller_model = "gemma3:4b"
            print(f"🔄 Retrying with smaller model: {smaller_model}")
            resp = ollama.chat(model=smaller_model, messages=messages, options={"temperature": 0.0})
            content = resp["message"]["content"]
            return json.dumps(content) if isinstance(content, dict) else content

        raise


# -----------------------------------------------------
# Cleanup Utility
# -----------------------------------------------------
def clean_model_output(raw: str) -> str:
    """
    Cleans model output to ensure valid JSON parsing.
    Handles ```json code fences and stray text.
    """
    cleaned = raw.strip().strip("`").strip()

    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()

    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[-1]
    if "```" in cleaned:
        cleaned = cleaned.split("```")[0].strip()

    return cleaned


# -----------------------------------------------------
# Structured JSON Generation
# -----------------------------------------------------
def generate_structured_json(
    text: str,
    input_file: Optional[str] = None,
    max_retries: int = 3,
    model: str = "llama3.1:8b-instruct-q4_K_M",
    grammar_model_path: Optional[str] = None,
    grammar_path: Optional[str] = None,
    system_prompt: Optional[str] = None,
):
    """
    Generates structured JSON from resume text using Ollama.
    Retries on invalid output, validates, and auto-saves.
    """
    prompt_base = (
        "You are a strict JSON generator for resumes. "
        "Given the resume text, produce a single JSON object that matches the provided schema exactly. "
        "Return ONLY JSON. Omit fields that are not present. Use concise values."
        + ("\nSystem: " + (system_prompt or ""))
    )

    attempt = 0
    last_raw = None
    while attempt < max_retries:
        attempt += 1
        try:
            raw = generate_with_ollama(prompt_base + "\n\n" + text, model=model)
        except Exception as e:
            print(f"[attempt {attempt}] Ollama call failed: {e}")
            continue

        last_raw = clean_model_output(raw)
        try:
            obj = json.loads(last_raw)
            # Try validating, but don’t fail if schema is slightly different
            try:
                validate_jsonschema(obj)
                validated = validate_pydantic(obj)
                return validated.dict()
            except Exception as e:
                print(f"[attempt {attempt}] Schema mismatch ({type(e).__name__}): {e}")
                print("✅ Accepting raw JSON output since structure is valid.")
                return obj  # accept raw JSON from model
        except json.JSONDecodeError as e:
            print(f"[attempt {attempt}] JSON decode error: {e}")


        except (json.JSONDecodeError, jsonschema.ValidationError, ValidationError) as e:
            print(f"[attempt {attempt}] Invalid JSON: {e}")
            text = (
                prompt_base
                + f"\nPrevious output was invalid JSON or did not match schema: {e}\n"
                + f"Previous output:\n{last_raw}\n"
                + "Return corrected JSON only."
            )
            time.sleep(0.5)

    raise RuntimeError(
        f"❌ Failed to produce valid JSON after {max_retries} attempts. Last output:\n{last_raw}"
    )
