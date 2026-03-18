import json
import time
import logging
from pathlib import Path
import copy  

from src.ingest.pdf_to_text import extract_text
from src.heuristics.section_splitter import split_sections
from src.extract.skills_links import extract_skills_and_links
from src.compose.experience import compose_experience
from src.normalizers.normalizers import normalize_all
from src.quality.confidence import compute_confidence
from src.models.llama_json_validator import generate_structured_json as generate_llm_json

# ---------------------------------------------------------
# Logging setup
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------
def run_pipeline(pdf_path: str) -> dict:
    pdf_path = Path(pdf_path)
    logger.info(f" Starting pipeline for file: {pdf_path.name}")
    t0 = time.time()

    # 1️⃣ Extract text
    t1 = time.time()
    text = extract_text(str(pdf_path))
    logger.info(f" Extracted text ({len(text)} chars) in {time.time() - t1:.2f}s")

    # 2️⃣ Split into sections
    t1 = time.time()
    sections = split_sections(text)
    logger.info(f" Split into {len(sections)} sections in {time.time() - t1:.2f}s")

    # 3️⃣ Truncate text for memory safety
    MAX_LEN = 10000
    if len(text) > MAX_LEN:
        logger.warning(f" Truncating text from {len(text)} → {MAX_LEN}")
        text = text[:MAX_LEN]

    # 4️⃣ Generate structured JSON using LLM
    t1 = time.time()
    try:
        llm_json = generate_llm_json(text, model="llama3.1:8b-instruct-q4_K_M")
    except RuntimeError as e:
        logger.warning(f" Model llama3.1:8b-instruct-q4_K_M failed ({e}); retrying with smaller model gemma3:4b...")
        try:
            llm_json = generate_llm_json(text, model="gemma3:4b")
        except RuntimeError as e2:
            logger.error(f" Both models failed ({e2}); using empty JSON structure.")
            llm_json = {}
    logger.info(f" LLM JSON generated in {time.time() - t1:.2f}s")

    # ---------------------------------------------------------
    # Critical Fix — robust skills & links parsing
    # ---------------------------------------------------------
    t1 = time.time()
    extracted = extract_skills_and_links(text)

    skills_field = llm_json.get("skills", [])
    if isinstance(skills_field, dict):
        skills_field = [
            s for v in skills_field.values() if isinstance(v, list) for s in v
        ]
    elif not isinstance(skills_field, list):
        skills_field = [str(skills_field)]

    raw_skills = skills_field + extracted.get("skills", [])
    skills = sorted(set(str(s).strip() for s in raw_skills if isinstance(s, (str, int, float))))

    raw_links = llm_json.get("links", []) + extracted.get("links", [])
    links = sorted(set(str(l).strip() for l in raw_links if isinstance(l, str)))

    logger.info(f"✅ Extracted {len(skills)} skills and {len(links)} links in {time.time() - t1:.2f}s")

    # ---------------------------------------------------------
    # 6️ Compose experience section
    # ---------------------------------------------------------
    t1 = time.time()
    try:
        experience = compose_experience(sections, llm_json, spans={})
    except Exception as e:
        logger.warning(f"⚠️ compose_experience failed ({e}); using LLM experience if available.")
        experience = llm_json.get("experience", [])
    logger.info(f"✅ Experience composed in {time.time() - t1:.2f}s")

    # ---------------------------------------------------------
    # 7️ Merge final structured data safely
    # ---------------------------------------------------------
    details = llm_json.get("details", {})
    contact = llm_json.get("contact", {})

    if not details:
        details = {"name": "Unknown", "summary": "Not provided"}
        logger.warning("⚠️ Missing 'details' in LLM output — added fallback fields.")

    data = {
        "details": details,
        "contact": contact,
        "skills": skills,
        "links": links,
        "experience": experience or [],
        "education": llm_json.get("education", []),
        "projects": llm_json.get("projects", []),
    }

    # ---------------------------------------------------------
    # 8️ Normalize and compute confidence
    # ---------------------------------------------------------
    t1 = time.time()
    data = normalize_all(data)
    data["quality"] = compute_confidence(copy.deepcopy(data))  # break circular refs
    logger.info(f"✅ Normalization + confidence in {time.time() - t1:.2f}s")

    logger.info(f"🎯 Pipeline completed successfully in {time.time() - t0:.2f}s")
    return copy.deepcopy(data)  

# ---------------------------------------------------------
# Debug pipeline with intermediate outputs
# ---------------------------------------------------------

def run_pipeline_debug(pdf_path: str) -> dict:
    """
    Debug version of the pipeline that returns intermediate data for visualization.
    """
    from src.ingest.pdf_to_text import extract_text
    from src.heuristics.section_splitter import split_sections
    import time, copy

    t0 = time.time()
    debug_data = {}

    # 1️⃣ Extract text
    text = extract_text(pdf_path)
    debug_data["raw_text"] = text

    # 2️⃣ Split into sections
    sections = split_sections(text)
    debug_data["sections"] = sections

    # 3️⃣ Run normal pipeline for final structured JSON
    result = run_pipeline(pdf_path)

    debug_data["skills"] = result.get("skills", [])
    debug_data["links"] = result.get("links", [])
    debug_data["experience"] = result.get("experience", [])
    debug_data["education"] = result.get("education", [])
    debug_data["projects"] = result.get("projects", [])
    debug_data["final_json"] = result

    debug_data["runtime_sec"] = round(time.time() - t0, 2)

    return copy.deepcopy(debug_data)



# ---------------------------------------------------------
# CLI entry
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.pipeline <pdf_path>")
    else:
        pdf_path = sys.argv[1]
        result = run_pipeline(pdf_path)

        # 🩹 Safe JSON dump (handles circular refs & weird objects)
        def safe_json(obj):
            try:
                return json.dumps(obj, indent=2)
            except ValueError:
                return json.dumps(json.loads(json.dumps(obj, default=str)), indent=2)

        print("\n Final JSON Output:\n")
        print(safe_json(result))
