#!/bin/bash
# Invoice AI - API Test Script
# Usage: ./test_api.sh [BASE_URL]
# Default BASE_URL: http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"

echo "🧾 Invoice AI API Tests"
echo "Base URL: $BASE_URL"
echo "================================"

# Health check
echo -e "\n1. Health Check"
curl -s "$BASE_URL/health" | python3 -m json.tool

# Upload single invoice
echo -e "\n2. Upload Single Invoice"
curl -s -X POST "$BASE_URL/api/invoices/upload" \
  -F "file=@sample-invoices/sample_invoice_1.png" | python3 -m json.tool

# List invoices
echo -e "\n3. List Invoices"
curl -s "$BASE_URL/api/invoices" | python3 -m json.tool

# Analytics
echo -e "\n4. Analytics"
curl -s "$BASE_URL/api/analytics" | python3 -m json.tool

# Templates
echo -e "\n5. Format Templates"
curl -s "$BASE_URL/api/templates" | python3 -m json.tool

# Duplicate detection test
echo -e "\n6. Duplicate Detection (re-upload same file)"
curl -s -X POST "$BASE_URL/api/invoices/upload" \
  -F "file=@sample-invoices/sample_invoice_1.png" | python3 -m json.tool

echo -e "\n✅ Tests complete!"
