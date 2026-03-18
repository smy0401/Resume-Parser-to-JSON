from pathlib import Path

# Base directory for this package
BASE_DIR = Path(__file__).parent

# Load prompt files as constants
SYSTEM_PROMPT = (BASE_DIR / "system_prompt.txt").read_text(encoding="utf-8")
USER_PROMPT_TEMPLATE = (BASE_DIR / "user_prompt_template.txt").read_text(encoding="utf-8")


def sectioning_prompt(sections: list[str]) -> dict:
    """
    Convert raw CV sections into structured JSON.
    For now, it's just a stub that shows we loaded the prompts correctly.
    Later, this can be replaced with actual LLM logic.
    """
    return {
        "sections": sections,
        "system_prompt_used": SYSTEM_PROMPT[:80] + "...",  # just showing it worked
        "user_prompt_template_preview": USER_PROMPT_TEMPLATE[:80] + "..."
    }
