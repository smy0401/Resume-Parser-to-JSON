import os

class Settings:
    """
    Central configuration for the CV2JSON service.
    Reads values from environment variables so Docker, .env, or local shell can override them.
    """

    # --- Privacy / File Handling ---
    REDACT_PII = os.getenv("REDACT_PII", "true").lower() == "true"
    AUTO_DELETE_UPLOADS = os.getenv("AUTO_DELETE_UPLOADS", "true").lower() == "true"

    # --- Model / LLM Runtime ---
    LLM_DEFAULT_MODEL = os.getenv("LLM_DEFAULT_MODEL", "llama3.1:8b-instruct-q4_K_M")
    LLM_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "gemma3:4b")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

    # --- Limits / Performance ---
    TRUNCATE_TEXT_LEN = int(os.getenv("TRUNCATE_TEXT_LEN", "10000"))
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))

    # --- Debug / Observability ---
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_REQUEST_ID = os.getenv("LOG_REQUEST_ID", "true").lower() == "true"
    LOG_TOKENS = os.getenv("LOG_TOKENS", "true").lower() == "true"

settings = Settings()
