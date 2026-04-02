AI Invoice Extraction & Analytics System
Overview

This project is an AI-powered invoice processing system that extracts structured data from invoice documents (PDF/JPG/PNG) using OCR and Large Language Models. The system converts unstructured invoice text into structured JSON, stores the data in a database, and provides analytics for business insights.

The solution is designed to handle multiple invoice formats, noisy OCR output, and missing fields while maintaining scalability and accuracy.

System Architecture
React UI → FastAPI → OCR → LLM Parsing → Validation → Database → Analytics
Key Features
Upload invoices (PDF, JPG, PNG)
OCR-based text extraction
LLM-powered structured JSON parsing
Database storage with file metadata
Vendor-wise spend analytics
Monthly spend trends
Duplicate invoice detection
Format detection & reuse
Batch invoice processing
Tech Stack

Frontend: React
Backend: FastAPI (Python)
OCR: Tesseract
LLM: OpenAI / Gemini
Database: Supabase (PostgreSQL)
Storage: Supabase Storage
Deployment: Vercel / Render

Database Design

Invoices

vendor_name
invoice_number
invoice_date
total_amount
currency

Files

invoice_id
file_url

Vendors

vendor_name
normalized_name
AI/ML Approach

The system uses OCR to extract raw text from invoices and an LLM to intelligently parse the text into structured fields. Prompt engineering and validation logic ensure consistent JSON output across different invoice formats.

This approach removes the need for manual templates and improves flexibility.

Analytics

The dashboard provides:

Total spend by vendor
Monthly spend trends
Invoice count
Currency-wise totals
Assumptions
Invoices are semi-structured
OCR accuracy depends on image quality
English invoices supported
Limitations
Handwritten invoices not supported
OCR noise may affect accuracy
Basic template learning
Future Improvements
Confidence score
Auto template learning
Multi-language invoices
Field highlighting
Real-time analytics
Run Locally

Backend

pip install -r requirements.txt
uvicorn main:app --reload

Frontend

npm install
npm start
