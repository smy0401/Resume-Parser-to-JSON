import re
from pathlib import Path

# Load curated skills list (tech + soft skills, deduped)
SKILLS_FILE = Path(__file__).parent.parent / "data" / "skills.txt"
if SKILLS_FILE.exists():
    with open(SKILLS_FILE, encoding="utf-8") as f:
        SKILLS_DICTIONARY = {line.strip().lower() for line in f if line.strip()}
else:
    SKILLS_DICTIONARY = set()  # start empty


LINK_PATTERNS_FILE = Path(__file__).parent.parent / "data" / "link_patterns.txt"
if LINK_PATTERNS_FILE.exists():
    with open(LINK_PATTERNS_FILE, encoding="utf-8") as f:
        LINK_PATTERNS = dict(
            line.strip().split(",") for line in f if "," in line.strip()
        )
else:
    LINK_PATTERNS = {}


def generate_ngrams(tokens):
    """Generate 1- to 4-grams from tokenized text."""
    ngrams = []
    N = len(tokens)
    for i in range(N):
        for n in range(1, 5):
            if i + n <= N:
                ngrams.append(" ".join(tokens[i : i + n]))
    return ngrams


def call_llama(text: str):
    """
    Stub for LLaMA/LLM fallback.
    Replace with actual HuggingFace/OpenAI integration later.
    """
    # For now: extract capitalized tokens (acts as placeholder)
    fallback = re.findall(r"\b[A-Z][a-zA-Z0-9\+\#]*\b", text)
    return [f.lower() for f in fallback if len(f) > 1]


def extract_skills(text: str):
    """Extract skills using heuristics first, then complement with LLaMA."""
    tokens = re.findall(r"\w+", text.lower())
    ngrams = generate_ngrams(tokens)

    # Dictionary lookup only (no hardcoded regex)
    found = {skill for skill in SKILLS_DICTIONARY if skill in ngrams}

    # If no skills found → call LLaMA to supplement
    if not found:
        llama_skills = call_llama(text)
        found.update(llama_skills)

    return sorted(found)


def extract_links(text: str):
    """Extract links and classify them based on external mapping."""
    out = []
    urls = re.findall(r"https?://[^\s]+", text)
    for url in urls:
        matched_type = None
        for domain, label in LINK_PATTERNS.items():
            if domain in url:
                matched_type = label
        out.append({"url": url, "type": matched_type or "other"})
    return out


def extract_skills_and_links(text: str):
    """Main entry point: extract both skills and links."""
    return {
        "skills": extract_skills(text),
        "links": extract_links(text),
    }
