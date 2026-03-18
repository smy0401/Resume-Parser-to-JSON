from typing import Dict, List, Optional, Tuple

# Tunable constants (start values; calibrate later with gold set)
RULE_BASE = 0.95  # baseline confidence if rule (regex/heuristic) matches and normalizes
NORMS_SUCCESS_BONUS = 0.02  # extra if normalization succeeded
AGREEMENT_BONUS = 0.03  # if rule and LLM are close
YEAR_ONLY_PENALTY = 0.15
MAX_CONF = 0.995
MIN_CONF = 0.0

# Field-type weights: how much we trust rules vs models by default (alpha applied to rule side)
FIELD_ALPHA = {
    "contact": 0.85,  # emails/phones - heuristics strong
    "date": 0.75,  # dates - heuristics + normalization important
    "company": 0.5,  # company/title - model helps a lot
    "title": 0.45,
    "skill": 0.5,
    "link": 0.8,
    "default": 0.6,
}


def _alpha_for_field(field_type: Optional[str]) -> float:
    if not field_type:
        return FIELD_ALPHA["default"]
    return FIELD_ALPHA.get(field_type, FIELD_ALPHA["default"])


def clamp(x: float) -> float:
    if x is None:
        return 0.0
    if x > MAX_CONF:
        return MAX_CONF
    if x < MIN_CONF:
        return MIN_CONF
    return round(x, 3)


def score_field(
    field_name: str,
    *,
    rule_match: bool = False,
    normalization_succeeded: bool = False,
    llm_conf: Optional[float] = None,
    field_type: Optional[str] = None,
    year_only_date: bool = False,
    exact_match_between_sources: bool = False,
    rule_conf: float = RULE_BASE,
) -> Tuple[float, List[str]]:

    explains: List[str] = []

    # ✅ Special-case for contact fields (email, phone)
    if field_type == "contact" and rule_match:
        score = RULE_BASE
        explains.append("rule_match")
        if normalization_succeeded:
            score = min(MAX_CONF, score + NORMS_SUCCESS_BONUS)
            explains.append("normalized")
            explains.append(f"norm_bonus={NORMS_SUCCESS_BONUS:.3f}")
        return clamp(score), explains

    # ✅ Special-case for company fields (LLM-driven if no rule match)
    if field_type == "company" and not rule_match and llm_conf is not None:
        score = clamp(llm_conf * 0.9)
        explains.append(f"llm_conf={llm_conf:.3f}")
        return score, explains

    # --- General logic below ---
    alpha = _alpha_for_field(field_type)

    # Baseline from rule side
    rule_score = rule_conf if rule_match else 0.0
    if rule_match:
        explains.append("rule_match")

    # normalization bonus
    if normalization_succeeded:
        explains.append("normalized")
        bonus = NORMS_SUCCESS_BONUS if rule_match else (NORMS_SUCCESS_BONUS / 2)
        rule_score = min(MAX_CONF, rule_score + bonus)
        explains.append(f"norm_bonus={bonus:.3f}")

    # LLM side
    model_score = llm_conf if llm_conf is not None else 0.0
    if llm_conf is not None:
        explains.append(f"llm_conf={llm_conf:.3f}")

    # Weighted blend
    raw = alpha * rule_score + (1.0 - alpha) * model_score
    explains.append(f"alpha={alpha:.2f}")

    # Agreement bonus
    if rule_match and llm_conf is not None:
        if abs(rule_score - llm_conf) < 0.07:
            raw = min(MAX_CONF, raw + AGREEMENT_BONUS)
            explains.append("agree_bonus")

    # Exact match bonus
    if exact_match_between_sources:
        raw = min(MAX_CONF, raw + (AGREEMENT_BONUS / 2))
        explains.append("exact_text_agree")

    # Year-only penalty
    if year_only_date:
        raw = max(MIN_CONF, raw - YEAR_ONLY_PENALTY)
        explains.append("year_only_penalty")

    final = clamp(raw)
    explains.append(f"final={final:.3f}")
    return final, explains


def combine_confidences(
    field_confidences: Dict[str, float], weights: Optional[Dict[str, float]] = None
) -> float:
    if not field_confidences:
        return 0.0
    if weights is None:
        weights = {k: 1.0 for k in field_confidences}
    total_w = sum(weights.get(k, 0.0) for k in field_confidences)
    if total_w == 0:
        return 0.0
    s = 0.0
    for k, v in field_confidences.items():
        w = weights.get(k, 1.0)
        s += v * w
    return clamp(s / total_w)


# -------- Master Confidence Computation --------
def compute_confidence(entry: dict) -> dict:
    """
    Compute overall confidence for a structured entry (like one job experience).
    Adds a 'final_confidence' field and explanation trace.
    """
    field_conf = {}
    explain_trace = {}

    for field_name, val in entry.items():
        # Skip non-data fields
        if field_name in ("trace", "source_spans", "confidence", "final_confidence"):
            continue

        field_type = "default"
        if field_name in ("email", "phone"):
            field_type = "contact"
        elif field_name in ("start_date", "end_date"):
            field_type = "date"
        elif field_name in ("company",):
            field_type = "company"
        elif field_name in ("role", "title"):
            field_type = "title"

        # Base rule presence check
        rule_match = bool(val)

        # Use inner field-level confidence if available
        llm_conf = None
        if isinstance(entry.get("confidence"), dict):
            llm_conf = entry["confidence"].get(field_name, 0.5)

        # Compute score
        score, expl = score_field(
            field_name,
            rule_match=rule_match,
            normalization_succeeded=False,
            llm_conf=llm_conf,
            field_type=field_type,
        )

        field_conf[field_name] = score
        explain_trace[field_name] = expl

    # Weighted aggregate
    entry["final_confidence"] = combine_confidences(field_conf)
    entry["trace"] = explain_trace
    return entry
