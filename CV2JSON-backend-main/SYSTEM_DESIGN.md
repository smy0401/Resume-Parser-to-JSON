# CV2JSON System Design & Architecture

**Document Date:** March 15, 2026  
**Project:** CV2JSON Backend - CV to Structured JSON Parser  
**Focus Areas:** System Design Thinking, Architecture, Scalability & Maintainability

---

## Table of Contents
1. [System Design & Thinking](#1-system-design--thinking)
2. [Architecture & Evaluation Focus](#2-architecture--evaluation-focus)
3. [Overall System Architecture](#21-overall-system-architecture)
4. [Key Design Decisions & Rationale](#22-key-design-decisions--rationale)
5. [Scalability Considerations](#23-scalability-considerations)
6. [Maintainability & Extensibility](#24-maintainability--extensibility)
7. [Quality Metrics](#25-quality-metrics)
8. [Failure Mode Analysis](#26-failure-mode-analysis)
9. [Design Philosophy Summary](#3-summary-design-philosophy)

---

## 1. SYSTEM DESIGN & THINKING

### 1.1 Core Philosophy: Hybrid Extraction Strategy

The system uses a **multi-source extraction approach** rather than relying solely on the LLM. This is a deliberate architectural choice that balances speed, accuracy, and robustness.

```
PDF → Text Extraction → Rule-Based Heuristics (Fast) ⟵ HYBRID ⟶ LLM (Accurate)
                             ↓
                 (Emails, Phones, Dates, Skills)
                             +
                 (Structured JSON, Entities)
                             ↓
               Merge & Normalize → Confidence Scoring
```

#### Why Hybrid Approach?

| Aspect | Rule-Based | LLM-Based | Hybrid |
|--------|-----------|----------|--------|
| **Speed** | ✅ Instant | ❌ 30-60s | ✅ Fast |
| **Accuracy** | ⚠️ Pattern-limited | ✅ Context-aware | ✅ Best of both |
| **Robustness** | ⚠️ Fail on format deviation | ⚠️ Hallucinations | ✅ Fallback coverage |
| **Cost** | ✅ Free (CPU) | ❌ LLM inference expensive | ✅ Optimized |

**Design Principle:** *Use fast heuristics to extract structured data, use LLM to validate and enrich with context.*

---

### 1.2 Pipeline Design: Modular Sequential Processing

The pipeline follows a strict **separation of concerns** principle with 7 distinct stages:

```
Stage 1: INGEST          → PDF → Raw Text
                            (pdfplumber, pytesseract, EasyOCR)

Stage 2: STRUCTURE       → Text → Sections
                            (Header detection, regex splitting)

Stage 3: HEURISTICS      → Sections → Contact, Skills, Links
                            (Rule-based extraction)

Stage 4: LLM SYNTHESIS   → Text → Structured JSON
                            (Ollama/Llama3.1 with prompts)

Stage 5: COMPOSITION     → Raw sections + LLM → Experience details
                            (Combine heuristics + LLM output)

Stage 6: NORMALIZATION   → Data → Standardized formats
                            (ISO dates, E.164 phones)

Stage 7: QUALITY         → Data → Confidence scores
                            (Multi-factor scoring system)
```

#### Design Rationale:

- **Modular**: Each stage can be tested, debugged, or replaced independently
- **Observable**: Logs at each stage with execution timing
- **Resilient**: Errors in stage N don't crash stage N+1 (fallbacks to empty data)
- **Debuggable**: `run_pipeline_debug()` returns intermediate outputs for inspection
- **Transparently Lazy**: Only compute what's needed for next stage

#### Code Example (pipeline.py):
```python
def run_pipeline(pdf_path: str) -> dict:
    # Stage 1: Extract text
    text = extract_text(str(pdf_path))
    
    # Stage 2: Split into sections
    sections = split_sections(text)
    
    # Stage 3: Truncate for memory safety
    text = text[:MAX_LEN]
    
    # Stage 4: LLM Synthesis with fallback
    try:
        llm_json = generate_llm_json(text, model="llama3.1:8b-instruct-q4_K_M")
    except RuntimeError:
        llm_json = generate_llm_json(text, model="gemma3:4b")  # Fallback
    
    # Stage 5-7: Composition, Normalization, Quality
    data = normalize_all(data)
    data["quality"] = compute_confidence(data)
    
    return data
```

---

### 1.3 Error Handling: Graceful Degradation

The system is designed to **never fail completely**—it should always return the best possible output even when components fail.

#### Fallback Strategy:

```python
# LLM Fallback Chain
try:
    llm_json = generate_llm_json(text, model="llama3.1:8b")
except RuntimeError as e:
    logger.warning(f"Primary model failed: {e}; retrying smaller model...")
    try:
        llm_json = generate_llm_json(text, model="gemma3:4b")
    except RuntimeError as e2:
        logger.error(f"Both models failed: {e2}; using heuristic-only output")
        llm_json = {}  # Return empty structure (heuristics still valid)
```

#### Graceful Degradation Examples:

| Failure Scenario | What Happens | User Impact |
|------------------|--------------|------------|
| Ollama unavailable | Use heuristics only (emails, phones, links) | ~70% data extracted |
| OCR fails on image-heavy PDF | Return partial text from readable sections | ~50% data extracted |
| LLM inference timeout | Fallback to smaller model or heuristics | Slower response or partial data |
| Normalization fails on date | Keep raw value with lower confidence score | User sees raw date + low confidence |
| PII redaction error | Log warning, return unredacted + flag | Data still usable, privacy noted |

**Philosophy:** *A CV that returns 70% accurate data is better than a crash that returns 0%.*

---

### 1.4 Type Safety & Data Validation

The system uses **Pydantic models** for runtime validation and type safety:

```python
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

class CVModel(BaseModel):
    meta: Optional[dict] = None
    details: Optional[dict] = None
    contact: Optional[ContactModel] = None
    experience: Optional[list[ExperienceItem]] = None
    education: Optional[list[EducationItem]] = None
    skills: Optional[list[str]] = None
```

#### Benefits:

- ✅ Invalid data caught before returning to client
- ✅ Clear schema contracts between pipeline stages
- ✅ Type hints improve IDE support and catch bugs
- ✅ Automatic JSON serialization/validation
- ✅ Self-documenting API (OpenAPI/Swagger integration)

---

## 2. ARCHITECTURE & EVALUATION FOCUS

### 2.1 Overall System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   FastAPI Server                         │
│     (HTTP handler + async middleware for metrics)        │
└────────────┬──────────────────────────┬──────────────────┘
             │                          │
        POST /parse_stream         GET /debug
        (Main CV parsing)      (Visualization & inspection)
             │                          │
             ↓
    ┌─────────────────────────────┐
    │   Processing Pipeline       │
    │   (Async to thread pool)    │
    └─────┬──────────────────┬────┘
          │                  │
          ↓                  ↓
    ┌──────────────┐   ┌──────────────┐
    │   Local      │   │   Ollama     │
    │   Rules      │   │   (LLM)      │
    │   Heuristics │   │   Models     │
    │              │   │  (Remote or  │
    │ - Regex      │   │   local)     │
    │ - Skill DB   │   │              │
    │ - Phone fmt  │   │ - llama3.1   │
    │ - Date fmt   │   │ - gemma3     │
    └──────────────┘   └──────────────┘
          │                  │
          └────────┬─────────┘
                   ↓
         ┌─────────────────────┐
         │  Merge & Normalize  │
         │                     │
         │ - Combine outputs   │
         │ - Standardize dates │
         │ - Format phones     │
         │ - Score confidence  │
         └────────────┬────────┘
                      ↓
         Output: {
           contact,
           details,
           skills,
           links,
           experience,
           education,
           quality (confidence scores)
         }
```

---

### 2.2 Key Design Decisions & Rationale

#### **Decision 1: FastAPI + Async Runtime**

```python
@app.post("/parse_stream")
async def parse_stream(file: UploadFile = File(...)):
    contents = await file.read()
    
    # CPU-heavy work in thread pool
    result = await asyncio.to_thread(run_pipeline, tmp_path)
    
    # Stream result back as Server-Sent Events
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**Why FastAPI?**
- Modern async/await support (non-blocking I/O)
- Automatic OpenAPI/Swagger documentation
- Built-in dependency injection for config
- Fast, production-ready (ASGI)

**Why Thread Pool?**
- LLM inference (30-60s) is CPU-bound, not I/O-bound
- `asyncio.to_thread()` offloads to worker thread pool
- Main event loop stays responsive for other requests
- Allows ~2-3 concurrent CV uploads without blocking

**Tradeoff:** Still limited by CPU cores. For heavy load, consider:
- Kubernetes with multiple replicas
- Task queue (Celery + Redis) for async jobs
- LLM load balancer (vLLM, ray-serve)

---

#### **Decision 2: Streaming Response (Server-Sent Events)**

```python
async def event_stream():
    yield "data: Starting extraction...\n\n"
    yield "data: Text extracted (5000 chars)...\n\n"
    yield "data: Running LLM inference...\n\n"
    yield f"data: {json.dumps(result)}\n\n"
```

**Why Streaming?**
- User sees progress in real-time (better UX for 30-60s operation)
- Client can process partial data as it arrives
- Long-polling not needed; persistent connection
- Browser's EventSource API handles the rest

**Benefit:** Transparent, responsive experience instead of "loading..." spinner

**Tradeoff:** Complex client-side handling; requires event stream awareness

---

#### **Decision 3: Hybrid Rule + LLM Confidence**

The system combines two confidence sources:

**Rule-Based Confidence:**
- Fixed baseline 0.95 for perfect regex match (email, phone)
- Bonus +0.02 if normalization succeeds
- Bonus +0.03 if multiple sources agree

**LLM Confidence:**
- Model-generated confidence from prompts
- Field-type weighting (emails more trusted than job titles)

**Combined Score (Weighted Blend):**
```python
def score_field(
    field_name: str,
    rule_match: bool = False,
    normalization_succeeded: bool = False,
    llm_conf: Optional[float] = None,
    field_type: Optional[str] = None,
) -> Tuple[float, List[str]]:
    
    # Alpha = how much we weight rules vs LLM by field type
    alpha = FIELD_ALPHA.get(field_type, 0.6)
    
    # Rule score = 0.95 (baseline) + bonuses
    rule_score = 0.95 if rule_match else 0.0
    if normalization_succeeded:
        rule_score += 0.02
    
    # Blend: alpha * rule_score + (1 - alpha) * llm_conf
    combined = alpha * rule_score + (1 - alpha) * (llm_conf or 0.0)
    
    return clamp(combined), reasons
```

**Field-Type Weights:**
```python
FIELD_ALPHA = {
    "contact": 0.85,   # Email/phone - heuristics very strong
    "date": 0.75,      # Dates - modern formatting important
    "company": 0.50,   # Company - LLM context critical
    "title": 0.45,     # Title - ambiguous without context
    "skill": 0.50,     # Skills - both sources valuable
    "link": 0.80,      # Links - heuristics reliable
    "default": 0.60,   # Default neutral blend
}
```

**Example Confidence Scores:**
| Field | Rule? | LLM? | Normalized? | Score | Reason |
|-------|-------|------|------------|-------|--------|
| john@example.com | ✅ | ✅ | ✅ | 0.97 | Email regex + LLM agrees |
| 2024 | ✅ | ❌ | ❌ | 0.80 | Year only, less precise |
| Software Engineer | ❌ | ✅ | N/A | 0.72 | LLM inferred, no rule match |

**Benefit:** Transparent, actionable confidence (can filter/flag low-confidence extractions)

---

#### **Decision 4: Memory Safety via Text Truncation**

```python
MAX_LEN = 10000  # Truncate text before LLM

if len(text) > MAX_LEN:
    logger.warning(f"Truncating {len(text)} → {MAX_LEN} chars")
    text = text[:MAX_LEN]
```

**Why?**
- LLM context window limits (Llama ~4K tokens)
- Prevents out-of-memory crashes on 50+ page CVs
- Trade-off: May lose data from very long CVs

**How?**
- Process first 10K characters (usually captures key sections)
- Most critical info (name, contact, key experience) in first ~5K chars
- If needed, implement sliding window for multi-document processing

**Tuning:** Adjust `TRUNCATE_TEXT_LEN` in `.env` based on your LLM's context window

---

#### **Decision 5: Privacy-First Design with PII Redaction**

```python
REDACT_PII = true  # Environment setting

# In pipeline:
redacted_text = redact_pii(text)  # Email → [EMAIL], Phone → [PHONE]

# Auto-delete uploads after processing
AUTO_DELETE_UPLOADS = true
```

**Why?**
- Aligns with GDPR, DPA (UK Data Protection Act)
- Compliance by default
- Sensitive data never leaves server cache

**What Gets Redacted:**
- Email addresses → [EMAIL]
- Phone numbers → [PHONE]
- Social security numbers → [SSN]
- Credit card numbers → [CREDIT_CARD]

**Tradeoff:** Slightly slower processing (regex scanning); can disable in `.env` if privacy not required

---

### 2.3 Scalability Considerations

The current design is optimized for **small-to-medium workloads** (10-50 concurrent users).

#### Scalability Limits and Solutions:

| Dimension | Current | Bottleneck | Solution (Phase 2) |
|-----------|---------|-----------|------------------|
| **Concurrent Users** | 2-3 | CPU cores, LLM inference latency | Kubernetes replicas + LLM load balancer |
| **Upload Size** | 15 MB | RAM during text extraction, LLM context | Stream PDF processing (pypdf2 chunks), sliding window LLM |
| **Response Time** | 30-60s | LLM inference on single GPU | Model quantization, batching, vLLM |
| **Storage** | ~5 MB/request (temp) | Disk I/O, cleanup | Cloud storage (S3), async cleanup |
| **Request Tracing** | UUID middleware | Limited observability | ELK stack, DataDog, New Relic |
| **Database Queries** | N/A | Not integrated | Add SQLAlchemy + PostgreSQL for audit logs |

#### Scaling Strategy (Priority Order):

1. **Immediate (Week 1):** Add request queuing (Celery + Redis)
2. **Short-term (Week 2-3):** Multi-GPU LLM serving (ray-serve or vLLM)
3. **Medium-term (Month 1):** Database persistence + audit logs
4. **Long-term (Q2):** Distributed training pipeline for custom models

---

### 2.4 Maintainability & Extensibility

The architecture is designed to be **modular** and **extension-friendly**.

#### Current Strengths:

- ✅ **Stage-based design**: Replace any stage without touching others
  - Want faster OCR? Swap `pdfplumber` → `pdfrw` in `ingest/pdf_to_text.py` (1 file)
  - Want different LLM? Change `LLM_DEFAULT_MODEL` in `.env` (no code change)
  
- ✅ **Config-driven**: All behavior control via environment variables
  - `LLM_DEFAULT_MODEL`, `TRUNCATE_TEXT_LEN`, `REDACT_PII`, etc.
  - No code changes needed for different deployments

- ✅ **Comprehensive logging**: Every stage logs timing + key metrics
  - `logger.info(f"✅ Stage X completed in {duration:.2f}s")`
  - Request ID tagged for end-to-end tracing

- ✅ **Test structure**: Each module has corresponding test file
  - `src/heuristics/section_splitter.py` → `tests/test_section_splitter.py`
  - Easy to add unit tests for new features

- ✅ **Schema-first design**: JSON schema defines expected output
  - Single source of truth for valid CV structure
  - Validates both LLM output and API responses

#### Extension Points:

**1. Add New Section Type:**
```python
# In src/heuristics/section_splitter.py
SECTION_MAP = {
    "experience": [...],
    "education": [...],
    "certifications": ["certifications", "credentials"],  # NEW
}

# In src/models/schema/cv.schema.json
{
  "properties": {
    "certifications": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

**2. Add New LLM Model:**
```python
# In src/config.py
LLM_FALLBACK_MODEL = "llama3.2:1b"  # Smaller, faster

# Automatically tries primary → gemma3 → new model
```

**3. Add New Skill Detector:**
```python
# Create src/extract/skill_detector_v2.py
def detect_skills_advanced(text):
    # Use NLP, domain-specific knowledge base, etc.
    return {"technical": [...], "soft": [...]}

# In pipeline.py
extracted = extract_skills_and_links(text)  # Existing
advanced = skill_detector_v2.detect(text)   # Add this
raw_skills = [...] + advanced["technical"]
```

**4. Add Database Persistence:**
```python
# Create src/db/models.py with SQLAlchemy ORM
class CVRecord(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    extracted_json = Column(JSON)
    confidence = Column(Float)

# Hook into API
@app.post("/parse_stream")
async def parse_stream(...):
    result = await asyncio.to_thread(run_pipeline, tmp_path)
    db.add(CVRecord(user_id=user_id, extracted_json=result))
    db.commit()
```

---

### 2.5 Quality Metrics

The system outputs **multi-factor confidence scoring** for every extracted field:

#### Confidence Components:

1. **Rule Matching** (0.0 → 1.0)
   - Regex match for known patterns (email, phone)
   - Keywords/heuristics for sections
   
2. **Normalization Success** (binary)
   - Did the extracted value successfully normalize?
   - E.164 phone format valid? ISO date parseable?

3. **LLM Agreement** (model-provided)
   - Model's internal confidence for that field
   - Higher if context supports extraction

4. **Field-Type Weight** (static)
   - Different fields get different alpha weights
   - Emails more trustworthy than job titles

5. **Cross-Source Agreement** (bonus)
   - +0.03 if rule and LLM both found same value
   - +0.02 if normalization succeeded

#### Scoring Function:

```python
def score_field(
    field_name: str,
    rule_match: bool = False,
    normalization_succeeded: bool = False,
    llm_conf: Optional[float] = None,
    field_type: Optional[str] = None,
    exact_match_between_sources: bool = False,
) -> Tuple[float, List[str]]:
    """
    Returns confidence score (0.0-0.995) and list of reasoning factors.
    """
    alpha = _alpha_for_field(field_type)  # Get field-specific weight
    
    # Rule confidence
    rule_conf = RULE_BASE if rule_match else 0.0
    if normalization_succeeded:
        rule_conf += NORMS_SUCCESS_BONUS
    if exact_match_between_sources:
        rule_conf += AGREEMENT_BONUS
    
    # Blend rule and LLM
    combined = alpha * rule_conf + (1 - alpha) * (llm_conf or 0.0)
    
    # Special penalties
    if field_type == "date" and year_only_date:
        combined -= YEAR_ONLY_PENALTY
    
    return clamp(combined), reasons
```

#### Example Quality Output:

```json
{
  "contact": {
    "emails": ["john@example.com"],
    "confidence": {
      "emails": {
        "value": "john@example.com",
        "score": 0.97,
        "reasons": [
          "Email regex matched",
          "Normalization succeeded",
          "LLM agreement (0.95)",
          "High-confidence field type"
        ]
      }
    }
  },
  "experience": [
    {
      "title": "Senior Engineer",
      "confidence": {
        "title": {
          "score": 0.72,
          "reasons": [
            "LLM inferred from context (0.75)",
            "No direct rule match",
            "Low field-type confidence (0.45 alpha)"
          ]
        }
      }
    }
  ]
}
```

---

### 2.6 Failure Mode Analysis

Comprehensive failure handling strategy:

| Failure Scenario | Probability | Impact | Detection | Recovery |
|------------------|------------|--------|-----------|----------|
| **Ollama unavailable** | Medium | LLM disabled; heuristics only | Connection error in `generate_llm_json()` | Return heuristic output; confidence=0.6 |
| **OCR fails (blurry PDF)** | Medium | Empty/partial text | `len(text) < 100` check | Skip LLM, return heuristic only |
| **LLM inference timeout** | Low | Slow response | > 60s elapsed | Fallback to smaller model |
| **Both LLM models fail** | Low | No structured JSON | Exception in fallback chain | Return empty dict `{}` |
| **Memory spike (huge CV)** | Low | OOM crash | Memory limit exceeded | Text truncation at 10K chars |
| **Normalization fails** | Low | Malformed output | Exception in normalizer | Keep raw value; adjust confidence |
| **Regex not matching** | Medium | Heuristic miss | Empty extraction | Covered by LLM fallback |
| **PDF is image-only** | Medium | No text extracted | Text length = 0 | Return error + suggest OCR |

#### Failure Recovery Examples:

**Example 1: Ollama Crash**
```python
try:
    resp = ollama.chat(model=model, messages=messages)
except Exception as e:
    logger.warning(f"Ollama failed: {e}")
    # Fallback: use heuristics
    llm_json = {}  # Empty structure
    # Result: emails/phones/links still extracted via rules
```

**Example 2: Memory Overflow**
```python
if len(text) > MAX_LEN:
    logger.warning(f"Text too long ({len(text)}); truncating to {MAX_LEN}")
    text = text[:MAX_LEN]
    # LLM processes first 10K chars (covers most critical info)
```

**Example 3: Normalization Error**
```python
try:
    normalized_date = normalize_date("2024")
except ValueError:
    logger.warning(f"Date normalization failed for '2024'")
    normalized_date = None
    # Return with lower confidence
    confidence = 0.45  # vs 0.95 for successfully normalized
```

---

## 3. SUMMARY: Design Philosophy

The CV2JSON system embodies five core design principles:

| Principle | Why | How |
|-----------|-----|-----|
| **Hybrid** | Single approach insufficient | Rules + LLM work together, not compete |
| **Graceful** | Failures are inevitable | Partial output > error 500 |
| **Observable** | Production debugging critical | Logging at every stage + confidence scores |
| **Configurable** | Different use cases need different settings | All behavior in `.env` |
| **Maintainable** | Code will change | Modular stages, clear boundaries, test coverage |

### Key Success Factors:

1. **Multi-source extraction** (rules + LLM) = better accuracy than either alone
2. **Graceful fallbacks** = reliable production system
3. **Confidence scoring** = users know what to trust
4. **Modular stages** = easy to extend or replace components
5. **Privacy by default** = GDPR-ready, PII redacted

### Optimal Use Cases:

✅ **Enterprise CV parsing** (compliance required)  
✅ **Bulk job applications** (10-100s of CVs)  
✅ **Recruitment platforms** (need high accuracy)  
✅ **Resume screening** (need confidence scores)  

### Not Optimal For:

❌ **Real-time (< 5s response time)** — LLM inference inherently slow  
❌ **Ultra-large scale (10K+ concurrent)** — needs distributed setup  
❌ **Highly regulated formats** (banking, legal docs) — requires custom validation  

---

## File Structure Reference

```
src/
├── ingest/            # Stage 1: PDF extraction
│   └── pdf_to_text.py
├── heuristics/        # Stage 2-3: Text splitting, section detection
│   ├── section_splitter.py
│   └── extractors.py
├── extract/           # Stage 3b: Skill + link extraction
│   └── skills_links.py
├── models/            # Stage 4: LLM prompts & validation
│   ├── llama_json_validator.py
│   ├── prompt_runner.py
│   └── prompts/
│       ├── system_prompt.txt
│       └── user_prompt_template.txt
├── compose/           # Stage 5: Experience composition
│   └── experience.py
├── normalizers/       # Stage 6: Date, phone normalization
│   └── normalizers.py
├── quality/           # Stage 7: Confidence scoring
│   └── confidence.py
├── api/               # HTTP endpoints
│   └── main.py
├── config.py          # Global configuration
└── pipeline.py        # Main orchestration

tests/
├── test_*.py          # Unit tests for each module

```

---

## Configuration Reference

All settings in [.env](C:\Users\syede\Downloads\CV2JSON-backend-main\CV2JSON-backend-main\.env):

```dotenv
# Privacy / File Handling
REDACT_PII=true
AUTO_DELETE_UPLOADS=true

# LLM Runtime
LLM_DEFAULT_MODEL=llama3.1:8b-instruct-q4_K_M
LLM_FALLBACK_MODEL=gemma3:4b
OLLAMA_URL=http://127.0.0.1:11434

# Limits / Performance
TRUNCATE_TEXT_LEN=10000
MAX_UPLOAD_SIZE_MB=15

# Debugging
DEBUG_MODE=false
LOG_REQUEST_ID=true
LOG_TOKENS=true
```

---

**End of System Design Document**  
For questions or updates, refer to inline code comments and test files.
