import re

def redact_pii(text: str) -> str:
    """
    Redacts common personally identifiable information (PII)
    like emails, phone numbers, and addresses from text.
    """
    if not text:
        return text

    # Mask emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED_EMAIL]', text)

    # Mask phone numbers
    text = re.sub(r'\b\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b', '[REDACTED_PHONE]', text)

    # Mask addresses (very generic)
    text = re.sub(r'\d+\s+\w+\s+(Street|St|Road|Rd|Avenue|Ave|Block|Sector)\b', '[REDACTED_ADDRESS]', text, flags=re.IGNORECASE)

    return text
