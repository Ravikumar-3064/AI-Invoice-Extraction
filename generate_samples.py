#!/usr/bin/env python3
"""
Generate sample invoice images for testing the extraction pipeline.
Run: python generate_samples.py
Requires: pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os, random
from datetime import datetime, timedelta

OUTPUT_DIR = "sample-invoices"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VENDORS = [
    {"name": "Acme Technologies Inc.", "address": "123 Silicon Valley Blvd\nSan Francisco, CA 94105", "email": "billing@acmetech.com"},
    {"name": "GlobalServ Solutions", "address": "88 Business Park, Tower B\nNew York, NY 10001", "email": "invoices@globalserv.io"},
    {"name": "Rapid Cloud Services", "address": "42 Cloud Drive\nSeattle, WA 98101", "email": "accounts@rapidcloud.com"},
]

CLIENTS = [
    {"name": "Pinnacle Corp", "address": "500 Enterprise Ave\nChicago, IL 60601"},
    {"name": "StartupXYZ Pvt Ltd", "address": "7 Innovation Hub\nBengaluru, KA 560001"},
]

def random_date(start_days_ago=90):
    d = datetime.today() - timedelta(days=random.randint(0, start_days_ago))
    return d.strftime("%Y-%m-%d"), (d + timedelta(days=30)).strftime("%Y-%m-%d")

def draw_invoice(vendor, client, inv_num, items, currency="USD"):
    W, H = 794, 1123  # A4 @ 96dpi
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        font_lg = font_md = font_sm = font_bold = ImageFont.load_default()

    # Header bar
    draw.rectangle([0, 0, W, 80], fill=(30, 30, 60))
    draw.text((40, 25), vendor["name"], fill="white", font=font_lg)

    # Invoice label
    draw.text((W - 200, 25), "INVOICE", fill=(200, 200, 255), font=font_lg)

    # Vendor info
    y = 110
    draw.text((40, y), "From:", fill=(100, 100, 100), font=font_sm)
    y += 20
    for line in [vendor["name"], vendor["address"], vendor["email"]]:
        for subline in line.split("\n"):
            draw.text((40, y), subline, fill=(30, 30, 30), font=font_md)
            y += 18
    y += 10

    # Client info
    cx = 400
    draw.text((cx, 110), "Bill To:", fill=(100, 100, 100), font=font_sm)
    cy = 130
    for line in [client["name"], client["address"]]:
        for subline in line.split("\n"):
            draw.text((cx, cy), subline, fill=(30, 30, 30), font=font_md)
            cy += 18

    # Invoice meta
    inv_date, due_date = random_date()
    meta_y = 240
    draw.text((40, meta_y), f"Invoice No: {inv_num}", fill=(30, 30, 30), font=font_bold)
    draw.text((40, meta_y + 22), f"Invoice Date: {inv_date}", fill=(30, 30, 30), font=font_md)
    draw.text((40, meta_y + 44), f"Due Date: {due_date}", fill=(30, 30, 30), font=font_md)
    draw.text((40, meta_y + 66), f"Payment Terms: Net 30", fill=(30, 30, 30), font=font_md)

    # Line items table
    ty = 360
    draw.rectangle([30, ty, W - 30, ty + 30], fill=(230, 230, 250))
    headers = ["Description", "Qty", "Unit Price", "Amount"]
    col_x = [40, 400, 500, 640]
    for h, x in zip(headers, col_x):
        draw.text((x, ty + 8), h, fill=(30, 30, 60), font=font_bold)

    ty += 30
    subtotal = 0
    for desc, qty, unit in items:
        amount = qty * unit
        subtotal += amount
        draw.rectangle([30, ty, W - 30, ty + 28], fill=(248, 248, 252) if subtotal % 2 == 0 else (255, 255, 255))
        draw.text((40, ty + 7), desc, fill=(30, 30, 30), font=font_md)
        draw.text((400, ty + 7), str(qty), fill=(30, 30, 30), font=font_md)
        draw.text((500, ty + 7), f"{currency} {unit:,.2f}", fill=(30, 30, 30), font=font_md)
        draw.text((640, ty + 7), f"{currency} {amount:,.2f}", fill=(30, 30, 30), font=font_md)
        ty += 28

    # Totals
    ty += 20
    draw.line([450, ty, W - 30, ty], fill=(200, 200, 200), width=1)
    ty += 10
    tax_rate = 0.1
    tax = subtotal * tax_rate
    total = subtotal + tax

    for label, val in [("Subtotal", subtotal), (f"Tax ({int(tax_rate*100)}%)", tax), ("TOTAL", total)]:
        is_total = label == "TOTAL"
        f = font_bold if is_total else font_md
        color = (30, 30, 30) if not is_total else (30, 30, 60)
        if is_total:
            draw.rectangle([450, ty - 2, W - 30, ty + 22], fill=(230, 230, 250))
        draw.text((460, ty), label, fill=color, font=f)
        draw.text((580, ty), f"{currency} {val:,.2f}", fill=color, font=f)
        ty += 26

    # Footer
    draw.line([30, H - 80, W - 30, H - 80], fill=(200, 200, 200), width=1)
    draw.text((40, H - 65), "Thank you for your business!", fill=(100, 100, 100), font=font_sm)
    draw.text((40, H - 48), f"Questions? Contact {vendor['email']}", fill=(100, 100, 100), font=font_sm)

    return img, {
        "invoice_number": inv_num,
        "vendor_name": vendor["name"],
        "client_name": client["name"],
        "subtotal": round(subtotal, 2),
        "tax_amount": round(tax, 2),
        "tax_rate": tax_rate * 100,
        "total_amount": round(total, 2),
        "currency": currency,
        "invoice_date": inv_date,
        "due_date": due_date,
    }


SAMPLE_ITEMS = [
    [
        ("Software Development - Sprint 1", 1, 4500.00),
        ("UI/UX Design Services", 2, 1200.00),
        ("DevOps & Infrastructure Setup", 1, 800.00),
    ],
    [
        ("Cloud Hosting - Monthly", 3, 299.00),
        ("SSL Certificate", 1, 89.00),
        ("Domain Registration (2 years)", 1, 45.00),
        ("CDN Services", 1, 150.00),
    ],
    [
        ("Data Analytics Consulting", 8, 250.00),
        ("Dashboard Development", 1, 3500.00),
        ("Training & Onboarding", 4, 175.00),
    ],
]

if __name__ == "__main__":
    generated = []
    for i, (vendor, client, items) in enumerate(zip(
        VENDORS,
        [CLIENTS[0], CLIENTS[1], CLIENTS[0]],
        SAMPLE_ITEMS,
    )):
        inv_num = f"INV-2024-{100 + i:03d}"
        img, meta = draw_invoice(vendor, client, inv_num, items)
        path = f"{OUTPUT_DIR}/sample_invoice_{i+1}.png"
        img.save(path, "PNG")
        print(f"✅ Generated: {path}")
        print(f"   Vendor: {meta['vendor_name']}")
        print(f"   Total: {meta['currency']} {meta['total_amount']:,}")
        generated.append((path, meta))

    print(f"\n✅ {len(generated)} sample invoices saved to ./{OUTPUT_DIR}/")
    print("\nTo test extraction:")
    print("  curl -X POST http://localhost:8000/api/invoices/upload \\")
    print(f"       -F 'file=@{OUTPUT_DIR}/sample_invoice_1.png'")
