# 📄 CV2JSON Backend

> **Intelligent CV/Resume Parser** — Convert PDFs and DOCX files to structured, machine-readable JSON with high accuracy, using a hybrid approach combining rule-based heuristics and Large Language Models (LLMs).

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [CLI Usage](#cli-usage)
  - [REST API Usage](#rest-api-usage)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Testing](#testing)
- [Contributing](#contributing)
- [Privacy & Security](#privacy--security)
- [Troubleshooting](#troubleshooting)

---

## Overview

**CV2JSON** is a backend service that automatically extracts structured information from CVs (resumes) in PDF or DOCX formats and converts them into clean, validated JSON. It's designed to handle real-world, messy resume formats while maintaining high accuracy and providing confidence scores for extracted data.

### Use Cases

- **Recruitment Platforms**: Automated resume parsing for job applications
- **HR Systems**: CV data ingestion for applicant tracking systems (ATS)
- **Data Analysis**: Extract and analyze employment history, skills, education
- **Backup & Archival**: Create digital archives of CVs in structured format
- **Research**: Analyze employment trends and skill distributions

---

## Features

### 🎯 Core Capabilities

- **Multi-Format Support**: Parse PDF and DOCX files
- **Hybrid Extraction**: Combines rule-based heuristics + LLM for optimal accuracy
- **Contact Extraction**: Emails, phone numbers, locations, LinkedIn/portfolio URLs
- **Experience Parsing**: Job titles, companies, dates, descriptions, and achievements
- **Skills Extraction**: Automatic skill identification and normalization
- **Education Recognition**: Degrees, institutions, graduation dates
- **Data Normalization**: Standardized formats (ISO 8601 dates, E.164 phone numbers)
- **Confidence Scoring**: Multi-factor confidence metrics for each extracted field
- **PII Redaction**: Optional privacy-preserving mode with automatic data masking

### 🚀 Performance & Scale

- **Fast Processing**: ~30-60 seconds per CV with LLM, <5 seconds with heuristics-only
- **Graceful Degradation**: System continues working if LLM unavailable
- **Memory Efficient**: Truncates text at 10K characters for inference
- **Async API**: Non-blocking REST endpoints for concurrent requests

### 🛡️ Reliability

- **Error Handling**: Multi-stage fallback mechanisms (primary model → fallback model → heuristics)
- **Timeout Protection**: Configurable timeouts prevent hanging requests
- **Validation**: Schema validation at every pipeline stage
- **Observability**: Execution logs with timing, request IDs, and status tracking

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                   User Input (PDF/DOCX)                 │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 1: INGEST                                        │
│  Extract raw text using pdfplumber, pytesseract, OCR   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 2: STRUCTURE                                     │
│  Split into sections (contact, experience, education)  │
└─────────────────────────────────────────────────────────┘
                           ↓
           ┌──────────────────────────────┐
           │  HYBRID EXTRACTION PIPELINE  │
           └──────────────────────────────┘
           /                              \
          ↓                                ↓
    HEURISTICS (Fast)              LLM SYNTHESIS (Accurate)
    • Regex patterns                • Structured JSON generation
    • Rule-based extraction         • Context-aware parsing
    • Link detection                • Relationship inference
          \                                /
           └──────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 5: COMPOSITION                                   │
│  Merge heuristics + LLM outputs                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 6: NORMALIZATION                                 │
│  Standardize dates, phone numbers, formats             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 7: QUALITY ASSESSMENT                            │
│  Compute confidence scores & validation flags          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               Output (Structured JSON)                  │
└─────────────────────────────────────────────────────────┘
```

### Why Hybrid Approach?

| Aspect | Rule-Based | LLM-Based | Hybrid |
|--------|-----------|----------|--------|
| **Speed** | ✅ Instant | ❌ 30-60s | ✅ Fast |
| **Accuracy** | ⚠️ Pattern-limited | ✅ Context-aware | ✅ Best of both |
| **Robustness** | ⚠️ Format fragile | ⚠️ Hallucinations | ✅ Fallback coverage |
| **Cost** | ✅ Free (CPU) | ❌ Expensive | ✅ Optimized |

**Design Principle**: Use fast heuristics for structured data, use LLM to validate and enrich with context.

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Git**
- **Docker & Docker Compose** (for containerized deployment)
- **Ollama** (for LLM inference) - Optional, heuristics-only mode works without it

### 1-Minute Setup (CLI)

```bash
# Clone the repository
git clone https://github.com/your-repo/CV2JSON-backend.git
cd CV2JSON-backend/CV2JSON-backend-main

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Parse a CV
python -m src.cli.main path/to/cv.pdf -o output.json
```

### 1-Minute Setup (Docker)

```bash
# Build and start services
make rebuild

# Access the web UI at http://localhost:8000
# Or use the API endpoint at http://localhost:8000/parse
```

---

## Installation

### Option 1: Local Development (Recommended for Development)

#### 1. Clone Repository

```bash
git clone https://github.com/your-repo/CV2JSON-backend.git
cd CV2JSON-backend/CV2JSON-backend-main
```

#### 2. Create Virtual Environment

```bash
# Using venv (built-in)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n cv2json python=3.10
conda activate cv2json
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: On Windows with CPU-only PyTorch, you may need to install PyTorch separately:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

#### 4. Verify Installation

```bash
python -c "import fastapi, pydantic, ollama; print('✅ All dependencies installed')"
```

### Option 2: Docker Deployment (Recommended for Production)

See [Docker Deployment](#docker-deployment) section below.

---

## Usage

### CLI Usage

#### Parse a Single CV

```bash
python -m src.cli.main input.pdf -o output.json
```

**Options:**
- `input_file`: Path to PDF or DOCX file (required)
- `-o, --output`: Path to save JSON output (optional; prints to stdout if omitted)

**Example:**

```bash
python -m src.cli.main ~/Downloads/resume.pdf -o ~/resume.json
cat ~/resume.json | jq '.experience[0]'
```

**Output Structure:**

```json
{
  "contact": {
    "name": "John Doe",
    "emails": ["john@example.com"],
    "phones": ["+1-555-0123"],
    "location": "San Francisco, CA",
    "urls": ["https://linkedin.com/in/johndoe", "https://github.com/johndoe"]
  },
  "experience": [
    {
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "start_date": "2020-01",
      "end_date": "2024-01",
      "current": false,
      "description": "Led development of microservices platform...",
      "achievements": ["Built scalable API", "Mentored 5+ engineers"],
      "confidence": 0.95
    }
  ],
  "education": [
    {
      "institution": "University of California",
      "degree": "Bachelor of Science",
      "field": "Computer Science",
      "graduation_date": "2020-05",
      "confidence": 0.98
    }
  ],
  "skills": ["Python", "AWS", "Docker", "FastAPI"],
  "quality": {
    "overall_confidence": 0.92,
    "completeness": 0.88,
    "validation_status": "passed"
  }
}
```

### REST API Usage

#### 1. Start the API Server

```bash
cd src/api
uvicorn main:app --reload --port 8000
```

Or with Docker:

```bash
docker compose up
```

#### 2. Upload and Parse a CV

**Endpoint**: `POST /parse`

```bash
curl -X POST -F "file=@resume.pdf" http://localhost:8000/parse | jq .
```

**Response**: Same JSON structure as CLI output

#### 3. Stream Live Logs

**Endpoint**: `POST /parse_stream`

```bash
# Browser: Navigate to http://localhost:8000
# Or use curl with streaming:
curl -X POST -F "file=@resume.pdf" http://localhost:8000/parse_stream
```

This endpoint streams logs in real-time as the pipeline processes the CV.

#### 4. Health Check

**Endpoint**: `GET /health`

```bash
curl http://localhost:8000/health
```

**Response**:

```json
{
  "status": "healthy",
  "ollama_available": true,
  "models": ["llama3.1:8b-instruct-q4_K_M", "gemma3:4b"]
}
```

#### 5. Batch Processing

Process multiple files with proper error handling:

```bash
for file in *.pdf; do
  echo "Processing $file..."
  curl -X POST -F "file=@$file" http://localhost:8000/parse > "output_${file%.pdf}.json"
done
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root or set environment variables:

```makefile
# ============================================
# Privacy & File Handling
# ============================================

# Automatically mask PII (emails, phones, SSNs)
REDACT_PII=true

# Delete uploaded files after processing
AUTO_DELETE_UPLOADS=true

# ============================================
# LLM Configuration
# ============================================

# Primary LLM model to use (must be installed in Ollama)
LLM_DEFAULT_MODEL=llama3.1:8b-instruct-q4_K_M

# Fallback model if primary fails
LLM_FALLBACK_MODEL=gemma3:4b

# Ollama server URL
OLLAMA_URL=http://127.0.0.1:11434

# ============================================
# Performance Tuning
# ============================================

# Max characters to send to LLM (prevents OOM)
TRUNCATE_TEXT_LEN=10000

# Max upload file size in MB
MAX_UPLOAD_SIZE_MB=15

# ============================================
# Debugging & Observability
# ============================================

# Enable debug mode (verbose logging)
DEBUG_MODE=false

# Log request IDs in output
LOG_REQUEST_ID=true

# Log token counts for API calls
LOG_TOKENS=true
```

### Accessing Configuration

In Python code:

```python
from src.config import settings

print(settings.REDACT_PII)  # true
print(settings.LLM_DEFAULT_MODEL)  # "llama3.1:8b-instruct-q4_K_M"
print(settings.OLLAMA_URL)  # "http://127.0.0.1:11434"
```

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Build and start all services
make rebuild

# Or manually:
docker compose build
docker compose up
```

This starts:
- **Ollama Runtime** on port 11434
- **CV2JSON API** on port 8000
- Connected via internal Docker network

### Access the Application

- **Web UI**: http://localhost:8000
- **API Endpoint**: http://localhost:8000/parse
- **Health Check**: http://localhost:8000/health

### Stopping Services

```bash
make down
# Or: docker compose down
```

### Service Architecture

```yaml
services:
  ollama-runtime:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"  # LLM inference server
    volumes:
      - ~/.ollama:/root/.ollama  # Persist downloaded models
    networks:
      - cvnet

  cv2json-api:
    build: .  # Uses Dockerfile
    ports:
      - "8000:8000"  # REST API
    environment:
      - OLLAMA_HOST=http://ollama-runtime:11434
    depends_on:
      - ollama-runtime
    networks:
      - cvnet
```

### Building Custom Docker Image

```bash
docker build -t cv2json:latest .
docker run -p 8000:8000 -e OLLAMA_URL=http://host.docker.internal:11434 cv2json:latest
```

---

## Project Structure

```
CV2JSON-backend-main/
├── src/                          # Main application code
│   ├── api/
│   │   ├── main.py              # FastAPI application, endpoints
│   │   └── __init__.py
│   │
│   ├── cli/
│   │   ├── main.py              # Command-line interface
│   │   └── __init__.py
│   │
│   ├── ingest/
│   │   ├── pdf_to_text.py       # PDF/DOCX text extraction
│   │   └── __init__.py
│   │
│   ├── heuristics/
│   │   ├── extractors.py        # Rule-based extraction (emails, phones, etc.)
│   │   ├── section_splitter.py  # CV section detection
│   │   └── __init__.py
│   │
│   ├── extract/
│   │   ├── skills_links.py      # Skill and URL extraction
│   │   ├── resources/
│   │   │   ├── skills.txt       # Dictionary of known skills
│   │   │   └── link_pattern.txt # URL pattern rules
│   │   └── __init__.py
│   │
│   ├── compose/
│   │   ├── experience.py        # Experience data composition
│   │   └── __init__.py
│   │
│   ├── models/
│   │   ├── prompt_runner.py     # LLM interface and prompts
│   │   ├── llama_json_validator.py  # Output validation
│   │   ├── prompts/             # Prompt templates
│   │   ├── schema/              # JSON schema definitions
│   │   └── __init__.py
│   │
│   ├── normalizers/
│   │   ├── normalizers.py       # Data format standardization
│   │   └── __init__.py
│   │
│   ├── quality/
│   │   ├── confidence.py        # Confidence scoring system
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── privacy.py           # PII redaction utilities
│   │   └── __init__.py
│   │
│   ├── config.py                # Configuration management
│   ├── pipeline.py              # Main processing pipeline
│   └── __init__.py
│
├── tests/                        # Test suite
│   ├── test_*.py               # Unit tests for each module
│   └── __init__.py
│
├── evaluation/
│   ├── evaluate.py             # Evaluation metrics
│   └── report.csv              # Benchmark results
│
├── predictions/                 # Sample predictions
│   ├── cv*.json                # Example output JSONs
│   └── run_predictions.py
│
├── gold_data/                   # Ground truth test data
│   ├── labels/                 # Annotated reference JSONs
│   └── pdfs/                   # Reference PDF files
│
├── tools/
│   └── cv.gbnf                 # Grammar for structured output
│
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata
├── setup.py                    # Package installation script
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container image spec
├── Makefile                    # Build automation
├── SYSTEM_DESIGN.md            # Architecture documentation
├── README.md                   # Basic README
└── .gitignore
```

---

## How It Works

### Step-by-Step Pipeline

#### 1. **INGEST**: Extract Text from File

**File**: `src/ingest/pdf_to_text.py`

```python
def extract_text(file_path: str) -> str:
    """
    Extract text from PDF or DOCX using multiple strategies.
    
    Tries in order:
    1. pdfplumber (fast, works for most PDFs)
    2. pytesseract (for image-heavy PDFs)
    3. EasyOCR (fallback, highest accuracy but slowest)
    """
```

- Uses `pdfplumber` for standard PDFs (fast)
- Falls back to `pytesseract` for scanned documents (image-based)
- Final fallback to `EasyOCR` for maximum accuracy

**Output**: Raw text string

#### 2. **STRUCTURE**: Split into Sections

**File**: `src/heuristics/section_splitter.py`

```python
def split_sections(text: str) -> dict:
    """
    Detect and split CV into logical sections:
    - Contact Information
    - Professional Summary
    - Experience
    - Education
    - Skills
    - Certifications
    - etc.
    """
```

Uses heuristic patterns (headers like "Experience", "Education") to segment CV.

**Output**: Dictionary of sections

#### 3. **HEURISTICS**: Rule-Based Extraction

**File**: `src/heuristics/extractors.py`

- **Email**: RFC 5322 regex pattern
- **Phone**: `phonenumbers` library with country detection
- **Location**: Named entity recognition
- **URLs**: Regex for links, LinkedIn profiles, GitHub repos

```python
def extract_emails(text: str) -> list[str]:
    """Extract emails using RFC 5322 pattern with validation"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    return [email for email in emails if is_valid_email(email)]
```

**Output**: Structured contact data with validation

#### 4. **LLM SYNTHESIS**: Generate Structured JSON

**File**: `src/models/prompt_runner.py`

Sends CV text to Llama3.1 (or fallback model) with structured prompt:

```
Extract the following from the CV and return valid JSON:
{
  "experience": [
    {
      "title": "...",
      "company": "...",
      "dates": "YYYY-MM to YYYY-MM",
      "description": "..."
    }
  ],
  "education": [...],
  "skills": [...]
}
```

**Output**: LLM-generated JSON with structured fields

#### 5. **COMPOSITION**: Merge Results

**File**: `src/compose/experience.py`

Combines outputs from heuristics and LLM:

```python
def compose_data(heuristics_data, llm_data):
    """
    Merge rule-based and LLM outputs:
    - Heuristics for contact (high precision)
    - LLM for experience, education (context-aware)
    - Union of skills from both sources
    """
```

#### 6. **NORMALIZATION**: Standardize Formats

**File**: `src/normalizers/normalizers.py`

- **Dates**: Convert to ISO 8601 (YYYY-MM-DD)
- **Phone**: Standardize to E.164 format (+1-555-0123)
- **Location**: Normalize to consistent format
- **Skills**: De-duplicate, normalize capitalization

```python
def normalize_date(date_str: str) -> str:
    """Convert any date format to ISO 8601"""
    # "Jan 2020" → "2020-01"
    # "01/15/2020" → "2020-01-15"
```

#### 7. **QUALITY**: Compute Confidence Scores

**File**: `src/quality/confidence.py`

Multi-factor confidence scoring:

```python
def compute_confidence(field_name: str, extracted_data: dict) -> float:
    """
    Confidence = (source_score + validation_score + consistency_score) / 3
    
    Factors:
    - Source: Was it from heuristics (0.7), LLM (0.9), or both (1.0)?
    - Validation: Does it match schema and pass validation?
    - Consistency: Does it match other fields logically?
    """
```

**Output**: JSON with confidence scores for each field

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Suite

```bash
# Test PDF extraction
pytest tests/test_pdf_to_text.py -v

# Test experience composition
pytest tests/test_experience.py -v

# Test normalizers
pytest tests/test_normalizers.py -v

# Test confidence scoring
pytest tests/test_confidence.py -v

# Test schema validation
pytest tests/test_schema_validation.py -v
```

### Test Coverage

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Generate Benchmark Reports

```bash
python evaluation/evaluate.py
cat evaluation/report.csv
```

---

## Contributing

### Development Workflow

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make changes and test**

```bash
# Add your code to appropriate module
# Write tests in tests/
# Run tests to verify
pytest tests/ -v
```

3. **Commit and push**

```bash
git add .
git commit -m "feat: Add support for [feature]"
git push origin feature/your-feature-name
```

4. **Submit pull request**

### Code Style

- Follow PEP 8 (use `black` for formatting)
- Add docstrings to all functions
- Write type hints for all parameters and returns
- Keep functions small and focused

```python
# Good example:
def extract_emails(text: str, validate: bool = True) -> list[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Input text to search
        validate: Whether to validate extracted emails
        
    Returns:
        List of valid email addresses
        
    Raises:
        ValueError: If text is not a string
    """
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    return [email for email in emails if not validate or is_valid_email(email)]
```

### Adding New Extractors

1. Create new function in appropriate module
2. Add tests in `tests/test_*.py`
3. Document with docstring and examples
4. Update this README with new functionality

---

## Privacy & Security

### PII Redaction

The system can automatically mask personally identifiable information:

```bash
export REDACT_PII=true
python -m src.cli.main resume.pdf -o output.json
```

**What Gets Redacted:**
- Email addresses → `[EMAIL]`
- Phone numbers → `[PHONE]`
- Social security numbers → `[SSN]`
- Dates of birth → `[DOB]`
- Home addresses → `[ADDRESS]`

### Data Handling

- Uploaded files are **automatically deleted** after processing (configurable)
- No data is stored or logged in production
- All processing happens locally (no external APIs except Ollama)

### Security Best Practices

1. **Use .env files** for sensitive configuration in development
2. **Never commit** `.env` or output files with PII
3. **Update dependencies** regularly

```bash
pip list --outdated
pip install -U -r requirements.txt
```

4. **Run in Docker** for production to isolate processes
5. **Enable REDACT_PII** in production environments

---

## Troubleshooting

### Common Issues

#### Issue: "Ollama connection refused"

**Problem**: LLM service not running

**Solution**:

```bash
# Check if Ollama is running
curl http://127.0.0.1:11434/api/tags

# Start Ollama
ollama serve

# Or with Docker
docker compose up ollama-runtime
```

#### Issue: "Model not found: llama3.1:8b-instruct-q4_K_M"

**Problem**: LLM model not downloaded

**Solution**:

```bash
ollama pull llama3.1:8b-instruct-q4_K_M
# Or use smaller fallback
ollama pull gemma3:4b
```

#### Issue: "CUDA out of memory" / "Torch out of memory"

**Problem**: Model too large for GPU

**Solution**:

```bash
# Use quantized (smaller) model
ollama pull llama3.1:8b-instruct-q4_K_M  # Quantized version

# Or use CPU-only
export OLLAMA_CPU_ONLY=1
ollama serve
```

#### Issue: "PDF extraction returns empty text"

**Problem**: PDF is scanned image (not OCR'd)

**Solution**:

Edit `src/ingest/pdf_to_text.py` and ensure OCR fallback is enabled:

```python
def extract_text(file_path: str) -> str:
    # Try pdfplumber first
    # - If fails, try pytesseract
    # - If fails, try EasyOCR (slowest but most thorough)
```

Run with debug mode to see which method was used:

```bash
DEBUG_MODE=true python -m src.cli.main resume.pdf -o output.json
```

#### Issue: "API returns 413 Payload Too Large"

**Problem**: File exceeds upload limit

**Solution**:

Increase limit in `.env`:

```makefile
MAX_UPLOAD_SIZE_MB=30
```

#### Issue: "Tests fail with import errors"

**Problem**: Dependencies not installed

**Solution**:

```bash
# Reinstall in development mode
pip install -e .
pip install -r requirements.txt

# Run tests from project root
cd [project-root]
pytest tests/
```

### Debug Mode

Enable verbose logging:

```bash
DEBUG_MODE=true python -m src.cli.main resume.pdf -o output.json 2>&1 | grep -i debug
```

### Getting Help

1. Check logs: `docker logs cv2json-api`
2. Check health endpoint: `curl http://localhost:8000/health`
3. Review [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md) for architecture details
4. Open an issue on GitHub with:
   - Error message
   - CV file (if possible)
   - System info (OS, Python version)
   - Configuration settings

---

## Performance Benchmarks

Results from `evaluation/evaluate.py`:

| Metric | Value |
|--------|-------|
| Average Processing Time | 45 seconds |
| Contact Extraction Accuracy | 95% |
| Experience Extraction Accuracy | 87% |
| Skills Extraction Accuracy | 92% |
| Overall Confidence (Avg) | 0.89 |
| Memory Usage (Peak) | 2.5 GB |

Full report: `evaluation/report.csv`

---

## License

MIT License - See LICENSE file for details

---

## Support & Contact

- **Issues**: GitHub Issues
- **Documentation**: See `/docs` folder
- **Architecture**: See [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md)

---

## Roadmap

- [ ] Support for additional document formats (PPTX, DOC)
- [ ] Multi-language CV support
- [ ] Continuous learning from corrections
- [ ] Batch processing optimization
- [ ] GraphQL API
- [ ] Web dashboard for result review
- [ ] Integration with popular ATS platforms

---

## Acknowledgments

- **Ollama** for local LLM inference
- **pdfplumber** for PDF extraction
- **Pydantic** for data validation
- **FastAPI** for web framework

---

**Made with ❤️ by the CV2JSON Team**
