-- Invoice Extraction AI - Supabase Schema
-- Run these in order in the Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  plan TEXT DEFAULT 'free',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Format Templates ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS format_templates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  signature TEXT UNIQUE NOT NULL,
  format_data JSONB,
  use_count INTEGER DEFAULT 1,
  common_fields TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_templates_signature ON format_templates(signature);

-- ── Invoices ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoices (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  filename TEXT NOT NULL,
  file_hash TEXT NOT NULL,
  file_url TEXT,
  status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed', 'duplicate_detected')),
  extracted_data JSONB,
  format_signature TEXT REFERENCES format_templates(signature) ON DELETE SET NULL,
  vendor_name TEXT,
  total_amount NUMERIC(15,2),
  currency TEXT DEFAULT 'USD',
  invoice_date DATE,
  due_date DATE,
  confidence_score NUMERIC(4,3),
  processing_time_ms INTEGER,
  is_duplicate BOOLEAN DEFAULT FALSE,
  duplicate_of TEXT REFERENCES invoices(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor_name);
CREATE INDEX IF NOT EXISTS idx_invoices_file_hash ON invoices(file_hash);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoices_currency ON invoices(currency);
CREATE INDEX IF NOT EXISTS idx_invoices_created ON invoices(created_at DESC);

-- ── Storage Bucket ────────────────────────────────────────────────────────────
-- Run this in Supabase Dashboard > Storage
-- CREATE BUCKET invoices (public: true)

-- ── Analytics View ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vendor_analytics AS
SELECT
  vendor_name,
  COUNT(*) AS invoice_count,
  SUM(total_amount) AS total_spend,
  AVG(total_amount) AS avg_invoice_value,
  AVG(confidence_score) AS avg_confidence,
  MAX(invoice_date) AS last_invoice_date,
  currency
FROM invoices
WHERE status = 'completed' AND is_duplicate = FALSE
GROUP BY vendor_name, currency
ORDER BY total_spend DESC NULLS LAST;

CREATE OR REPLACE VIEW monthly_spend AS
SELECT
  DATE_TRUNC('month', invoice_date) AS month,
  currency,
  COUNT(*) AS invoice_count,
  SUM(total_amount) AS total_amount
FROM invoices
WHERE status = 'completed' AND invoice_date IS NOT NULL AND is_duplicate = FALSE
GROUP BY DATE_TRUNC('month', invoice_date), currency
ORDER BY month DESC;

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE format_templates ENABLE ROW LEVEL SECURITY;

-- Allow all for anon key (tighten in production with auth)
CREATE POLICY "Allow all for anon" ON invoices FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON format_templates FOR ALL USING (true);
