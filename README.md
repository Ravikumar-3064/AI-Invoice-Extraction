AI Invoice Extraction & Analytics System

An AI-powered full-stack application that extracts structured data from invoices and generates analytics automatically.

🚀 Overview

The AI Invoice Extraction & Analytics System processes invoice documents (PDF/JPG/PNG) and converts them into structured data using OCR + LLM parsing.
The extracted data is stored in a database and visualized through an analytics dashboard to provide business insights like vendor spend and monthly trends.

This solution supports multiple invoice formats, handles noisy OCR output, and detects duplicate invoices.

🏗️ System Architecture
Frontend (React)
      ↓
FastAPI Backend
      ↓
OCR (Tesseract)
      ↓
LLM Parsing (OpenAI/Gemini)
      ↓
Validation Layer
      ↓
Supabase Database
      ↓
Analytics Dashboard
✨ Key Features

📤 Upload invoice (PDF / JPG / PNG)
🔍 OCR text extraction
🧠 AI-powered JSON parsing
🗄️ Supabase database storage
📊 Analytics dashboard
🏢 Vendor-wise spend tracking
📅 Monthly spend trends
🔁 Duplicate invoice detection
⚡ Batch invoice processing
🧩 Format detection & reuse

🧰 Tech Stack

Frontend

React
Axios

Backend

FastAPI
Python

AI & OCR

Tesseract OCR
OpenAI / Gemini

Database & Storage

Supabase (PostgreSQL)
Supabase Storage

Deployment

Vercel / Render
🗃️ Database Design
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
🧠 AI/ML Approach

The system uses OCR to extract raw invoice text and LLM parsing to convert unstructured text into structured JSON fields.
Prompt engineering and validation logic ensure consistent extraction across different invoice formats.

This removes manual template creation and improves flexibility.

📊 Analytics

The dashboard provides:

Total spend by vendor
Monthly spend trends
Number of invoices processed
Currency-wise totals
⚠️ Assumptions
Invoices are semi-structured
OCR accuracy depends on image quality
English invoices supported
🚧 Limitations
Handwritten invoices not supported
OCR noise may affect parsing accuracy
Basic format learning
🔮 Future Improvements
Confidence score
Auto template learning
Multi-language invoices
Field highlighting
Real-time analytics
Email invoice ingestion
▶️ Run Locally
Backend
pip install -r requirements.txt
uvicorn main:app --reload
Frontend
npm install
npm start
🎯 Project Highlights

✅ AI/ML Thinking
✅ Full Stack Development
✅ Database Design
✅ Analytics Dashboard
✅ Scalable ArchitectureAI Invoice Extraction & Analytics System

An AI-powered full-stack application that extracts structured data from invoices and generates analytics automatically.

🚀 Overview

The AI Invoice Extraction & Analytics System processes invoice documents (PDF/JPG/PNG) and converts them into structured data using OCR + LLM parsing.
The extracted data is stored in a database and visualized through an analytics dashboard to provide business insights like vendor spend and monthly trends.

This solution supports multiple invoice formats, handles noisy OCR output, and detects duplicate invoices.

🏗️ System Architecture
Frontend (React)
      ↓
FastAPI Backend
      ↓
OCR (Tesseract)
      ↓
LLM Parsing (OpenAI/Gemini)
      ↓
Validation Layer
      ↓
Supabase Database
      ↓
Analytics Dashboard
✨ Key Features

📤 Upload invoice (PDF / JPG / PNG)
🔍 OCR text extraction
🧠 AI-powered JSON parsing
🗄️ Supabase database storage
📊 Analytics dashboard
🏢 Vendor-wise spend tracking
📅 Monthly spend trends
🔁 Duplicate invoice detection
⚡ Batch invoice processing
🧩 Format detection & reuse

🧰 Tech Stack

Frontend

React
Axios

Backend

FastAPI
Python

AI & OCR

Tesseract OCR
OpenAI / Gemini

Database & Storage

Supabase (PostgreSQL)
Supabase Storage

Deployment

Vercel / Render
🗃️ Database Design
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
🧠 AI/ML Approach

The system uses OCR to extract raw invoice text and LLM parsing to convert unstructured text into structured JSON fields.
Prompt engineering and validation logic ensure consistent extraction across different invoice formats.

This removes manual template creation and improves flexibility.

📊 Analytics

The dashboard provides:

Total spend by vendor
Monthly spend trends
Number of invoices processed
Currency-wise totals
⚠️ Assumptions
Invoices are semi-structured
OCR accuracy depends on image quality
English invoices supported
🚧 Limitations
Handwritten invoices not supported
OCR noise may affect parsing accuracy
Basic format learning
🔮 Future Improvements
Confidence score
Auto template learning
Multi-language invoices
Field highlighting
Real-time analytics
Email invoice ingestion
▶️ Run Locally
Backend
pip install -r requirements.txt
uvicorn main:app --reload
Frontend
npm install
npm start
🎯 Project Highlights

✅ AI/ML Thinking
✅ Full Stack Development
✅ Database Design
✅ Analytics Dashboard
✅ Scalable Architecture
