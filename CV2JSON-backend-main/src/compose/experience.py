# src/models/experience_composer.py

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def safe_parse_date(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip()
    if re.search(r"\b(present|current|now)\b", s, flags=re.I):
        return None
    patterns = ["%Y-%m-%d", "%Y-%m", "%b %Y", "%B %Y", "%m/%Y", "%m/%d/%Y", "%d %b %Y"]
    for p in patterns:
        try:
            dt = datetime.strptime(s, p)
            if p in ("%Y-%m-%d", "%m/%d/%Y", "%d %b %Y"):
                return dt.strftime("%Y-%m-%d")
            else:
                return dt.strftime("%Y-%m")
        except Exception:
            continue
    m = re.search(r"(19|20)\d{2}", s)
    if m:
        return m.group(0)
    return s


def find_spans_for_value(value: str, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not value:
        return []
    value_norm = re.sub(r"\s+", " ", value).strip().lower()
    out = []
    for sp in spans:
        txt = sp.get("text", "")
        if value_norm in txt.lower():
            out.append(sp)
    return out


def heuristics_from_raw(raw_text: str, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates = []
    label_map = {}
    for s in spans:
        label = s.get("label", "").upper()
        label_map.setdefault(label, []).append(s)

    for comp_span in label_map.get("COMPANY", []):
        company = comp_span.get("text")
        comp_start = comp_span.get("start", 0)
        role, start_date, end_date = None, None, None

        nearest_role, nearest_date = None, None
        min_role_dist, min_date_dist = 1_000_000, 1_000_000

        for lbl in ("ROLE", "TITLE"):
            for r in label_map.get(lbl, []):
                d = abs(r.get("start", 0) - comp_start)
                if d < min_role_dist:
                    min_role_dist, nearest_role = d, r

        for dspan in label_map.get("DATE", []):
            d = abs(dspan.get("start", 0) - comp_start)
            if d < min_date_dist:
                min_date_dist, nearest_date = d, dspan

        if nearest_role:
            role = nearest_role.get("text")
        if nearest_date:
            dt_text = nearest_date.get("text", "")
            m = re.split(r"[-–—to]+", dt_text)
            if len(m) >= 1:
                start_date = m[0].strip()
            if len(m) >= 2:
                end_date = m[1].strip()

        candidate = {
            "company": company,
            "role": role,
            "start_date": safe_parse_date(start_date),
            "end_date": safe_parse_date(end_date),
            "heur_confidence": 0.6,
        }
        candidates.append(candidate)

    if not candidates:
        for m in re.finditer(
            r"(?P<role>[A-Za-z &/-]{3,50}) at (?P<company>[A-Za-z0-9 &\.-]{2,80})",
            raw_text,
            flags=re.I,
        ):
            candidates.append(
                {
                    "company": m.group("company").strip(),
                    "role": m.group("role").strip(),
                    "start_date": None,
                    "end_date": None,
                    "heur_confidence": 0.4,
                }
            )
    return candidates


def merge_entry(llm_entry: Dict[str, Any], heur_entry: Optional[Dict[str, Any]], spans: List[Dict[str, Any]]) -> Dict[str, Any]:
    out = {
        "company": None,
        "role": None,
        "start_date": None,
        "end_date": None,
        "is_current": False,
        "confidence": {},
        "source_spans": {},
        "trace": [],
    }

    llm_conf = float(llm_entry.get("confidence", 0.5))

    # --- Company
    llm_company = (llm_entry.get("company") or "").strip() or None
    heur_company = heur_entry.get("company") if heur_entry else None
    if llm_company and llm_conf >= 0.7:
        out["company"] = llm_company
        out["confidence"]["company"] = llm_conf
        out["trace"].append("company <- llm (high confidence)")
    elif heur_company:
        out["company"] = heur_company
        out["confidence"]["company"] = float(heur_entry.get("heur_confidence", 0.5))
        out["trace"].append("company <- heuristics (llm low/conf missing)")
    else:
        out["company"] = llm_company
        out["confidence"]["company"] = llm_conf
        out["trace"].append("company <- llm (fallback)")

    # --- Role
    llm_role = (llm_entry.get("role") or "").strip() or None
    heur_role = heur_entry.get("role") if heur_entry else None
    if llm_role and llm_conf >= 0.7:
        out["role"] = llm_role
        out["confidence"]["role"] = llm_conf
        out["trace"].append("role <- llm (high confidence)")
    elif heur_role:
        out["role"] = heur_role
        out["confidence"]["role"] = float(heur_entry.get("heur_confidence", 0.5))
        out["trace"].append("role <- heuristics (llm low/conf missing)")
    else:
        out["role"] = llm_role
        out["confidence"]["role"] = llm_conf
        out["trace"].append("role <- llm (fallback)")

    # --- Dates
    raw_start = llm_entry.get("start_date") or (heur_entry.get("start_date") if heur_entry else None)
    raw_end = llm_entry.get("end_date") or (heur_entry.get("end_date") if heur_entry else None)

    if isinstance(raw_end, str) and re.search(r"\b(present|current|now)\b", raw_end, flags=re.I):
        out["end_date"] = None
        out["is_current"] = True
        out["confidence"]["end_date"] = llm_conf
        out["trace"].append("end_date <- present marker -> end_date=null, is_current=true")
    else:
        out["end_date"] = safe_parse_date(raw_end)
        out["confidence"]["end_date"] = (
            llm_conf if llm_entry.get("end_date") else float(heur_entry.get("heur_confidence", 0.5)) if heur_entry else llm_conf
        )

    out["start_date"] = safe_parse_date(raw_start)
    out["confidence"]["start_date"] = (
        llm_conf if llm_entry.get("start_date") else float(heur_entry.get("heur_confidence", 0.5)) if heur_entry else llm_conf
    )

    # --- Source spans
    for fld in ("company", "role", "start_date", "end_date"):
        val = out.get(fld)
        if val:
            matched_spans = find_spans_for_value(str(val), spans)
            out["source_spans"][fld] = matched_spans
        else:
            out["source_spans"][fld] = []

    return out


def _compose_experience_core(raw_text: str, llm_json: Dict[str, Any], spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    llm_entries = llm_json.get("experiences") or llm_json.get("experience") or []
    heur_candidates = heuristics_from_raw(raw_text, spans)
    out_entries = []

    for i, le in enumerate(llm_entries):
        heur_match = None
        le_company = (le.get("company") or "").strip().lower()
        for h in heur_candidates:
            if h.get("company") and le_company and h["company"].strip().lower() == le_company:
                heur_match = h
                break
        if heur_match is None and i < len(heur_candidates):
            heur_match = heur_candidates[i]

        merged = merge_entry(le, heur_match, spans)
        out_entries.append(merged)

    if not llm_entries:
        for h in heur_candidates:
            merged = merge_entry({}, h, spans)
            out_entries.append(merged)

    return out_entries


def compose_experience(structured_json: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper for pipeline integration."""
    raw_text = structured_json.get("sections", {}).get("experience", {}).get("text", "")
    spans = structured_json.get("spans", [])
    llm_json = structured_json.get("llm_output", {})

    logger.info(f"LLM extracted experiences: {llm_json.get('experiences') or llm_json.get('experience')}")
    logger.info(f"Heuristic candidates: {len(spans)} spans -> {len(heuristics_from_raw(raw_text, spans))} heuristics")

    experiences = _compose_experience_core(raw_text, llm_json, spans)
    structured_json["experience"] = experiences
    return structured_json
