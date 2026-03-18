import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

SECTION_MAP = {
    "experience": [
        "experience",
        "work experience",
        "work history",
        "professional experience",
        "employment",
        "employment history",
    ],
    "education": [
        "education",
        "academic background",
        "qualifications",
        "education & training",
    ],
    "skills": ["skills", "technical skills", "key skills", "core competencies"],
    "summary": ["summary", "profile", "about me", "objective", "professional summary"],
    "contact": ["contact", "contact information", "personal details", "contact info"],
    "projects": ["projects", "project experience", "portfolio", "personal projects"],
}


def _clean(s: str) -> str:
    """Lowercase, remove punctuation so comparisons are simpler."""
    return re.sub(r"[^a-z0-9\s]", "", (s or "").lower()).strip()


def normalize_section(header: str) -> Optional[str]:
    """
    Return canonical section name if header text matches any known variant.
    Flexible substring/token matching.
    """
    if not header:
        return None
    h = _clean(header)
    for canonical, variants in SECTION_MAP.items():
        # include canonical itself as a candidate
        for v in [canonical] + variants:
            v_clean = _clean(v)

            if v_clean and (v_clean in h or h in v_clean):
                return canonical
    return None


def _looks_like_header(line: str) -> bool:
    """
    Heuristic: consider a line a header if:
      - it ends with ':' OR
      - it is ALL CAPS (typical resume headers) OR
      - it is short (<=5 words) and not a sentence (no period) and starts with a capital
    """
    s = (line or "").strip()
    if not s:
        return False
    if s.endswith(":"):
        return True
    # all-caps (ignore numbers/punctuation)
    letters = [c for c in s if c.isalpha()]
    if letters and all(c.isupper() for c in letters) and len(s) <= 80:
        return True
    # short title-like line
    words = s.split()
    if len(words) <= 6 and "." not in s and len(s) <= 80:
        # treat as possible header if first word capitalized (Title case or single word)
        if words[0][0].isalpha() and words[0][0].isupper():
            return True
    return False


def split_sections(text: str) -> Dict[str, Dict[str, object]]:
    """
    Split resume/plain text into canonical sections.

    Returns dict where keys are canonical section names and values are:
      {"text": <section text>, "spans": [(start_line, end_line), ...]}
    Spans use 0-based line indices.
    """
    lines = text.splitlines()
    sections: Dict[str, Dict[str, object]] = {}
    current_key: Optional[str] = None
    current_buffer: List[str] = []
    current_start: Optional[int] = None

    for i, raw_line in enumerate(lines):
        line = raw_line.rstrip()
        # consider blank lines as separators but keep them in buffer (do not drop)
        if _looks_like_header(line):
            normalized = normalize_section(line)
            if normalized:
                # flush existing section
                if current_key and current_buffer:
                    entry = sections.get(current_key)
                    block_text = "\n".join(current_buffer).strip()
                    if entry:
                        # append additional span/text for repeated sections
                        entry["spans"].append((current_start, i - 1))
                        entry["text"] = (entry["text"] + "\n\n" + block_text).strip()
                    else:
                        sections[current_key] = {
                            "text": block_text,
                            "spans": [(current_start, i - 1)],
                        }
                    current_buffer = []

                # begin new section
                current_key = normalized
                current_start = i + 1  # section content starts after header line
                continue
            else:
                # header-like but not a canonical header; don't start a canonical section
                # treat as normal text unless inside a canonical block
                if current_key:
                    current_buffer.append(line)
                continue

        # regular content line
        if current_key:
            current_buffer.append(line)

    # flush final
    if current_key and current_buffer:
        entry = sections.get(current_key)
        block_text = "\n".join(current_buffer).strip()
        start = current_start if current_start is not None else 0
        end = len(lines) - 1
        if entry:
            entry["spans"].append((start, end))
            entry["text"] = (entry["text"] + "\n\n" + block_text).strip()
        else:
            sections[current_key] = {"text": block_text, "spans": [(start, end)]}

    return sections
