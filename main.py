"""
Invoice Extraction AI - FastAPI Backend
Extracts structured data from invoice images/PDFs using LLM + OCR pipeline
"""

import os
import json
import hashlib
import base64
import asyncio
from datetime import datetime, date
from typing import Optional, List
from io import BytesIO

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
import uvicorn

# ── App Setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Invoice Extraction AI",
    description="AI-powered invoice data extraction, storage, and analytics",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ────────────────────────────────────────────────────────────────────

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}
MAX_FILE_SIZE_MB = 10

# ── Pydantic Models ───────────────────────────────────────────────────────────

class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None

class ExtractedInvoice(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    client_name: Optional[str] = None
    client_address: Optional[str] = None
    line_items: List[LineItem] = []
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    discount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "USD"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    confidence_score: float = 0.0
    extraction_warnings: List[str] = []

class InvoiceResponse(BaseModel):
    id: str
    filename: str
    status: str
    extracted_data: Optional[ExtractedInvoice] = None
    file_url: Optional[str] = None
    format_template_id: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    processing_time_ms: int = 0
    created_at: str

# ── Supabase Client ───────────────────────────────────────────────────────────

class SupabaseClient:
    """Minimal async Supabase REST client"""

    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def insert(self, table: str, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                json=data,
            )
            r.raise_for_status()
            result = r.json()
            return result[0] if isinstance(result, list) else result

    async def select(self, table: str, query: str = "") -> list:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.url}/rest/v1/{table}?{query}",
                headers=self.headers,
            )
            r.raise_for_status()
            return r.json()

    async def update(self, table: str, match: str, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.patch(
                f"{self.url}/rest/v1/{table}?{match}",
                headers={**self.headers, "Prefer": "return=representation"},
                json=data,
            )
            r.raise_for_status()
            result = r.json()
            return result[0] if isinstance(result, list) and result else {}

    async def upload_file(self, bucket: str, path: str, content: bytes, content_type: str) -> str:
        storage_headers = {
            "apikey": self.headers["apikey"],
            "Authorization": self.headers["Authorization"],
            "Content-Type": content_type,
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.url}/storage/v1/object/{bucket}/{path}",
                headers=storage_headers,
                content=content,
            )
            r.raise_for_status()
        return f"{self.url}/storage/v1/object/public/{bucket}/{path}"


db = SupabaseClient(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# ── LLM Extraction ────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are an expert invoice data extraction system. Extract ALL available information from this invoice image/document.

Return ONLY valid JSON matching this exact schema (no markdown, no explanation):
{
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "vendor_email": "string or null",
  "vendor_phone": "string or null",
  "client_name": "string or null",
  "client_address": "string or null",
  "line_items": [
    {
      "description": "string",
      "quantity": number_or_null,
      "unit_price": number_or_null,
      "amount": number_or_null
    }
  ],
  "subtotal": number_or_null,
  "tax_amount": number_or_null,
  "tax_rate": number_or_null,
  "discount": number_or_null,
  "total_amount": number_or_null,
  "currency": "ISO 4217 code e.g. USD, EUR, INR",
  "payment_terms": "string or null",
  "notes": "string or null",
  "confidence_score": 0.0_to_1.0,
  "extraction_warnings": ["list of any data quality issues or ambiguities"]
}

Rules:
- All monetary values must be numbers (not strings)
- Dates must be in YYYY-MM-DD format
- confidence_score: 0.9+ = clear invoice, 0.7-0.9 = some issues, below 0.7 = significant problems
- If a field is truly not present, use null
- Normalize vendor names (e.g. "ACME Corp." -> "ACME Corp")
- For currency, infer from symbols ($ = USD, € = EUR, £ = GBP, ₹ = INR) or text
"""

FORMAT_DETECTION_PROMPT = """Analyze this invoice and return a JSON fingerprint for format detection:
{
  "layout_type": "single_column|two_column|table_heavy|minimal|complex",
  "has_logo": boolean,
  "has_line_items_table": boolean,
  "header_position": "top|left|right",
  "estimated_vendor_type": "freelancer|enterprise|retail|saas|contractor",
  "format_signature": "a short string describing the unique layout characteristics"
}
Return ONLY the JSON, no explanation."""


async def extract_with_claude(image_b64: str, media_type: str, template: Optional[dict] = None) -> dict:
    """Extract invoice data using Claude Vision API"""
    template_hint = ""
    if template:
        template_hint = f"\n\nHINT: This invoice appears to match a known format: {template.get('format_signature', '')}. Pay special attention to these fields which are typically present: {template.get('common_fields', [])}."

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": EXTRACTION_PROMPT + template_hint},
            ],
        }
    ]

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 2000,
                "messages": messages,
            },
        )
        r.raise_for_status()
        data = r.json()

    raw_text = data["content"][0]["text"].strip()
    # Strip markdown fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    return json.loads(raw_text)


async def detect_format(image_b64: str, media_type: str) -> dict:
    """Detect invoice format/template fingerprint"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": FORMAT_DETECTION_PROMPT},
            ],
        }
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 400,
                "messages": messages,
            },
        )
        r.raise_for_status()
        data = r.json()

    raw_text = data["content"][0]["text"].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    return json.loads(raw_text)


# ── File Utilities ────────────────────────────────────────────────────────────

def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_format_signature(format_data: dict) -> str:
    sig = f"{format_data.get('layout_type')}-{format_data.get('header_position')}-{format_data.get('has_line_items_table')}"
    return hashlib.md5(sig.encode()).hexdigest()[:12]


# ── In-Memory Fallback Store (when Supabase not configured) ──────────────────

_invoices_store: dict = {}
_templates_store: dict = {}
_file_hashes_store: dict = {}


async def store_invoice(invoice_data: dict) -> str:
    """Store invoice in Supabase or memory"""
    if db:
        try:
            result = await db.insert("invoices", invoice_data)
            return result.get("id", invoice_data["id"])
        except Exception as e:
            print(f"Supabase error: {e}, falling back to memory")
    _invoices_store[invoice_data["id"]] = invoice_data
    return invoice_data["id"]


async def get_all_invoices() -> list:
    if db:
        try:
            return await db.select("invoices", "order=created_at.desc")
        except Exception as e:
            print(f"Supabase error: {e}")
    return list(_invoices_store.values())


async def find_duplicate(file_hash: str) -> Optional[dict]:
    if db:
        try:
            results = await db.select("invoices", f"file_hash=eq.{file_hash}&limit=1")
            return results[0] if results else None
        except Exception:
            pass
    return _file_hashes_store.get(file_hash)


async def find_template(signature: str) -> Optional[dict]:
    if db:
        try:
            results = await db.select("format_templates", f"signature=eq.{signature}&limit=1")
            return results[0] if results else None
        except Exception:
            pass
    return _templates_store.get(signature)


async def upsert_template(signature: str, template_data: dict):
    if db:
        try:
            existing = await find_template(signature)
            if existing:
                await db.update("format_templates", f"signature=eq.{signature}", {
                    "use_count": existing.get("use_count", 0) + 1,
                    "updated_at": datetime.utcnow().isoformat(),
                })
            else:
                await db.insert("format_templates", {
                    "signature": signature,
                    "format_data": json.dumps(template_data),
                    "use_count": 1,
                    "created_at": datetime.utcnow().isoformat(),
                })
            return
        except Exception as e:
            print(f"Template upsert error: {e}")
    _templates_store[signature] = template_data


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "Invoice Extraction AI",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "upload": "POST /api/invoices/upload",
            "upload_batch": "POST /api/invoices/batch",
            "list": "GET /api/invoices",
            "get": "GET /api/invoices/{id}",
            "analytics": "GET /api/analytics",
            "health": "GET /health",
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "supabase": "connected" if db else "not configured (using memory)",
        "llm": "claude" if ANTHROPIC_API_KEY else "not configured",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/invoices/upload")
async def upload_invoice(file: UploadFile = File(...)):
    """Upload and extract data from a single invoice"""
    start_time = datetime.utcnow()

    # Validate file type
    if file.content_type not in SUPPORTED_FORMATS:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}. Supported: JPEG, PNG, PDF")

    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(503, "LLM not configured. Set ANTHROPIC_API_KEY environment variable.")

    # Generate ID and check for duplicate
    invoice_id = f"inv_{hashlib.md5(content + str(datetime.utcnow().timestamp()).encode()).hexdigest()[:12]}"
    file_hash = compute_file_hash(content)

    duplicate = await find_duplicate(file_hash)
    if duplicate:
        return {
            "id": invoice_id,
            "filename": file.filename,
            "status": "duplicate_detected",
            "is_duplicate": True,
            "duplicate_of": duplicate.get("id"),
            "extracted_data": json.loads(duplicate.get("extracted_data", "{}")),
            "message": "This invoice was already processed. Returning cached results.",
            "created_at": datetime.utcnow().isoformat(),
        }

    # Convert to base64 for vision API
    media_type = file.content_type
    if media_type == "application/pdf":
        # For PDF, use as document type
        image_b64 = base64.standard_b64encode(content).decode()
        # Treat as image/jpeg for now - in prod use pdf2image
        media_type = "image/jpeg"
    else:
        image_b64 = base64.standard_b64encode(content).decode()

    # Detect format and find template
    try:
        format_data = await detect_format(image_b64, media_type)
        format_sig = compute_format_signature(format_data)
        template = await find_template(format_sig)
        await upsert_template(format_sig, {**format_data, "signature": format_sig})
    except Exception as e:
        format_data = {}
        format_sig = None
        template = None
        print(f"Format detection failed: {e}")

    # Extract invoice data
    try:
        raw_extracted = await extract_with_claude(image_b64, media_type, template)
    except json.JSONDecodeError as e:
        raise HTTPException(422, f"LLM returned invalid JSON: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"LLM API error: {e.response.status_code}")

    # Validate and build response
    try:
        extracted = ExtractedInvoice(**raw_extracted)
    except Exception as e:
        # Partial data - still return what we have
        extracted = ExtractedInvoice(
            extraction_warnings=[f"Validation error: {e}"] + raw_extracted.get("extraction_warnings", []),
            confidence_score=raw_extracted.get("confidence_score", 0.3),
        )

    processing_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    # Upload file to storage
    file_url = None
    if db:
        try:
            file_url = await db.upload_file(
                "invoices",
                f"{invoice_id}/{file.filename}",
                content,
                file.content_type,
            )
        except Exception as e:
            print(f"File storage error: {e}")

    # Store in database
    invoice_record = {
        "id": invoice_id,
        "filename": file.filename,
        "file_hash": file_hash,
        "file_url": file_url,
        "status": "completed",
        "extracted_data": json.dumps(extracted.dict()),
        "format_signature": format_sig,
        "vendor_name": extracted.vendor_name,
        "total_amount": extracted.total_amount,
        "currency": extracted.currency,
        "invoice_date": extracted.invoice_date,
        "confidence_score": extracted.confidence_score,
        "processing_time_ms": processing_ms,
        "is_duplicate": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    await store_invoice(invoice_record)
    _file_hashes_store[file_hash] = invoice_record

    return {
        **invoice_record,
        "extracted_data": extracted.dict(),
        "format_template_reused": template is not None,
        "format_signature": format_sig,
    }


@app.post("/api/invoices/batch")
async def upload_batch(files: List[UploadFile] = File(...)):
    """Process multiple invoices concurrently"""
    if len(files) > 10:
        raise HTTPException(400, "Maximum 10 files per batch")

    results = []
    tasks = []

    for f in files:
        tasks.append(upload_invoice(f))

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for i, resp in enumerate(responses):
        if isinstance(resp, Exception):
            results.append({
                "filename": files[i].filename,
                "status": "error",
                "error": str(resp),
            })
        else:
            results.append(resp)

    return {
        "total": len(files),
        "successful": sum(1 for r in results if r.get("status") != "error"),
        "failed": sum(1 for r in results if r.get("status") == "error"),
        "results": results,
    }


@app.get("/api/invoices")
async def list_invoices(
    vendor: Optional[str] = None,
    currency: Optional[str] = None,
    limit: int = 50,
):
    """List all processed invoices with optional filters"""
    invoices = await get_all_invoices()

    if vendor:
        invoices = [i for i in invoices if vendor.lower() in (i.get("vendor_name") or "").lower()]
    if currency:
        invoices = [i for i in invoices if i.get("currency") == currency.upper()]

    # Parse extracted_data if stored as string
    for inv in invoices:
        if isinstance(inv.get("extracted_data"), str):
            try:
                inv["extracted_data"] = json.loads(inv["extracted_data"])
            except Exception:
                pass

    return {"invoices": invoices[:limit], "total": len(invoices)}


@app.get("/api/invoices/{invoice_id}")
async def get_invoice(invoice_id: str):
    """Get a specific invoice by ID"""
    invoices = await get_all_invoices()
    for inv in invoices:
        if inv["id"] == invoice_id:
            if isinstance(inv.get("extracted_data"), str):
                inv["extracted_data"] = json.loads(inv["extracted_data"])
            return inv
    raise HTTPException(404, "Invoice not found")


@app.get("/api/analytics")
async def get_analytics():
    """Compute analytics across all processed invoices"""
    invoices = await get_all_invoices()

    vendor_spend: dict = {}
    monthly_spend: dict = {}
    currency_totals: dict = {}
    total_processed = len(invoices)
    total_value = 0.0
    avg_confidence = 0.0
    confidence_count = 0

    for inv in invoices:
        data = inv.get("extracted_data") or {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        vendor = inv.get("vendor_name") or data.get("vendor_name") or "Unknown"
        amount = inv.get("total_amount") or data.get("total_amount") or 0
        currency = inv.get("currency") or data.get("currency") or "USD"
        inv_date = inv.get("invoice_date") or data.get("invoice_date")
        confidence = inv.get("confidence_score") or data.get("confidence_score") or 0

        if amount:
            total_value += float(amount)
            vendor_spend[vendor] = vendor_spend.get(vendor, 0) + float(amount)
            currency_totals[currency] = currency_totals.get(currency, 0) + float(amount)

        if confidence:
            avg_confidence += float(confidence)
            confidence_count += 1

        if inv_date:
            try:
                month_key = inv_date[:7]  # YYYY-MM
                monthly_spend[month_key] = monthly_spend.get(month_key, 0) + float(amount or 0)
            except Exception:
                pass

    # Sort and format
    top_vendors = sorted(vendor_spend.items(), key=lambda x: x[1], reverse=True)[:10]
    monthly_trend = sorted(monthly_spend.items())

    return {
        "summary": {
            "total_invoices_processed": total_processed,
            "total_value_usd": round(total_value, 2),
            "average_confidence_score": round(avg_confidence / confidence_count if confidence_count else 0, 3),
            "unique_vendors": len(vendor_spend),
            "currencies_detected": list(currency_totals.keys()),
        },
        "vendor_spend": [
            {"vendor": v, "total_amount": round(a, 2)} for v, a in top_vendors
        ],
        "monthly_trend": [
            {"month": m, "total_amount": round(a, 2)} for m, a in monthly_trend
        ],
        "currency_totals": [
            {"currency": c, "total_amount": round(a, 2)} for c, a in currency_totals.items()
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }


@app.get("/api/templates")
async def list_templates():
    """List detected invoice format templates"""
    if db:
        try:
            templates = await db.select("format_templates", "order=use_count.desc")
            return {"templates": templates}
        except Exception:
            pass
    return {"templates": list(_templates_store.values())}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
