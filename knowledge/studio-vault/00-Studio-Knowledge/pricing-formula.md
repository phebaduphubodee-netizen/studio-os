---
type: studio-knowledge
last-updated: 2026-05-15
---

# Pricing Formula

> วิธีคำนวณราคา quotation — สูตรที่ Claude Code ใช้ทำ BOQ

## Master formula

```
Final Quote = (Material + Labor + Design Fee) × (1 + Margin) × (1 + Contingency)
                                                                 + VAT (7%)
```

## Step-by-step

### Step 1 — Material cost
```
Material = Σ (quantity × unit_price)   for each line item
```
อ้างอิงราคาจาก `[[rate-card]]` หรือ supplier quote ปัจจุบัน

### Step 2 — Labor cost
```
Labor per trade = man_days × daily_rate
Total Labor = Σ (Labor per trade)
```

### Step 3 — Design fee
ใช้แบบใดแบบหนึ่ง (เลือกตอน contract):
- **Per sqm**: `area_sqm × rate_per_sqm`
- **% of total**: `(Material + Labor) × design_percentage`
- **Flat fee**: ตามที่ตกลง

### Step 4 — Margin (กำไรสตูดิโอ)
```
Margin % = [X]%   (default ของสตูดิโอ)
```

Margin ปรับตาม:
- ขนาดงาน (งานใหญ่ % ลดลงได้)
- ความเสี่ยง (รีโนเวทเก่า → margin สูงขึ้น)
- Lead time (รีบ → margin สูงขึ้น)

### Step 5 — Contingency
```
Contingency % = 
  - 10% สำหรับ concept stage (เผื่อแบบเปลี่ยน)
  -  7% สำหรับ detail design ผ่านแล้ว
  -  5% สำหรับ construction phase
```

### Step 6 — VAT
7% ของ subtotal (ถ้าจดทะเบียน VAT)

## Worked example

```
Project: คอนโด 65 sqm Sukhumvit
Style: Japandi mid-range

Material:                      ฿850,000
Labor:                         ฿380,000
Subtotal:                    ฿1,230,000

Design fee (฿2,500/sqm × 65):  ฿162,500
Pre-margin total:            ฿1,392,500

Margin (15%):                  ฿208,875
Pre-contingency total:       ฿1,601,375

Contingency (7%):              ฿112,096
Pre-tax total:               ฿1,713,471

VAT (7%):                      ฿119,943
─────────────────────────────────────────
FINAL QUOTE:                 ฿1,833,414
```

## When to NOT use this formula

- Single-piece consultation → flat hourly
- Small touch-up work → fixed quote
- งาน goodwill / referral → กรณีพิเศษ

## Discount policy

- Friends & family: max [10]%
- Repeat client: [5]%
- Project size > ฿[X]M: negotiable up to [5]%
- **Never discount design fee** — only material/labor margin

## Payment milestones (default)

| Milestone | % | When |
|-----------|---|------|
| Design fee | 50% | Contract signing |
| Design fee balance | 50% | Design approval |
| Construction 1 | 30% | Construction start |
| Construction 2 | 30% | 50% progress |
| Construction 3 | 30% | 90% progress |
| Handover | 10% | Final handover |

---

*ปรับแต่งตามจริงของสตูดิโอ*
