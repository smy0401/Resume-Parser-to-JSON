import os
import json
import time
import tempfile
import asyncio
import logging
import uuid
from fastapi import FastAPI, File, UploadFile, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.pipeline import run_pipeline
from src.ingest.pdf_to_text import extract_text
from src.heuristics.section_splitter import split_sections
from src.utils.privacy import redact_pii
from src.config import settings




# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------
app = FastAPI(title="CV 2 JSON", version="1.2")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Middleware for observability
# ------------------------------------------------------------
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        logger.info(f"[{request_id}] {request.method} {request.url.path}")

        response = await call_next(request)

        duration = time.time() - start
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}s"

        logger.info(f"[{request_id}] Completed in {duration:.2f}s | Status: {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)


# ------------------------------------------------------------
# Root HTML Upload UI
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def upload_form():
    return """
    <html>
    <head>
        <title>CV Parser</title>
        <style>
            body { font-family: Arial; background: #0f172a; color: white; text-align: center; padding-top: 60px; }
            form { background: #1e293b; padding: 30px; border-radius: 12px; display: inline-block; }
            #logs { margin-top: 20px; text-align: left; width: 400px; margin: auto; background: #0f172a;
                    border: 1px solid #334155; border-radius: 8px; padding: 10px; font-family: monospace;
                    font-size: 14px; max-height: 300px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <h1>CV Parser (Live Logs)</h1>
        <form id="cvForm" enctype="multipart/form-data" method="post">
            <input name="file" type="file" accept=".pdf,.docx" required><br><br>
            <input type="submit" value="Upload & Parse">
        </form>
        <div id="logs"></div>

        <script>
            const form = document.getElementById("cvForm");
            const logs = document.getElementById("logs");
            form.onsubmit = async (e) => {
                e.preventDefault();
                logs.innerHTML = "";
                const file = e.target.file.files[0];
                const formData = new FormData();
                formData.append("file", file);

                const response = await fetch("/parse_stream", { method: "POST", body: formData });
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const text = decoder.decode(value);
                    logs.innerHTML += text.replace(/data: /g, '') + "<br>";
                    logs.scrollTop = logs.scrollHeight;
                }
            };
        </script>
    </body>
    </html>
    """


# ------------------------------------------------------------
# Streaming Parse Endpoint
# ------------------------------------------------------------
@app.post("/parse_stream")
async def parse_stream(file: UploadFile = File(...)):
    # --- Read file first (before stream starts) ---
    contents = await file.read()
    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    async def event_stream():
        try:
            yield "data: Upload complete, starting pipeline...\n\n"

            # Run CPU-heavy pipeline in a background thread
            result = await asyncio.to_thread(run_pipeline, tmp_path)

            yield "data: Pipeline finished successfully.\n\n"
            yield f"data: {json.dumps(result, indent=2)}\n\n"

        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

        finally:
            if tmp_path and os.path.exists(tmp_path) and settings.AUTO_DELETE_UPLOADS:
                os.remove(tmp_path)
                logger.info(f"Temp file {tmp_path} auto-deleted.")

    return StreamingResponse(event_stream(), media_type="text/event-stream")




# ------------------------------------------------------------
# Debug View Endpoint
# ------------------------------------------------------------
@app.get("/debug", response_class=HTMLResponse)
async def debug_view(file: str = Query(...), format: str = Query("html")):
    """
    /debug?file=sample.pdf&format=html  -> visual spans
    /debug?file=sample.pdf&format=json  -> raw structured data
    """
    if not os.path.exists(file):
        return HTMLResponse(f"<h3>File not found: {file}</h3>", status_code=404)

    text = extract_text(file)
    sections = split_sections(text)
    result = run_pipeline(file)

    if format == "json":
        return JSONResponse(result)

    # Apply simple highlighting spans
    def highlight(text, items, css_class):
        for item in items:
            if isinstance(item, str) and item.strip():
                safe = item.strip()
                text = text.replace(safe, f"<span class='{css_class}'>{safe}</span>")
        return text

    html_text = text
    html_text = highlight(html_text, result.get("skills", []), "skill")
    html_text = highlight(html_text, [l for l in result.get("links", [])], "link")
    html_text = highlight(html_text, [result.get("details", {}).get("name", "")], "name")

    # Style output
    styled = f"""
    <html><head><style>
        body {{ font-family: monospace; background: #0f172a; color: white; padding: 30px; }}
        span.skill {{ background: #16a34a33; color: #4ade80; }}
        span.link {{ background: #1d4ed833; color: #60a5fa; }}
        span.name {{ background: #9333ea33; color: #c084fc; }}
        .section {{ margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
        h2 {{ color: #38bdf8; }}
    </style></head>
    <body>
        <h2>Debug View — {os.path.basename(file)}</h2>
        <div><b>Detected Sections:</b></div>
        {''.join(f"<div class='section'><pre>{s}</pre></div>" for s in sections)}
        <h3>Highlighted Text:</h3>
        <div><pre>{html_text}</pre></div>
    </body></html>
    """
    return HTMLResponse(styled)

# ------------------------------------------------------------
# Middleware with PII Redaction
# ------------------------------------------------------------
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        raw_path = str(request.url.path)
        safe_path = redact_pii(raw_path)
        logger.info(f"[{request_id}] {request.method} {safe_path}")

        response = await call_next(request)
        duration = time.time() - start
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}s"

        safe_status = redact_pii(str(response.status_code))
        logger.info(f"[{request_id}] Completed in {duration:.2f}s | Status: {safe_status}")

        return response
# ------------------------------------------------------------
# Health Check
# ------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"message": "CV Parser API running"}



