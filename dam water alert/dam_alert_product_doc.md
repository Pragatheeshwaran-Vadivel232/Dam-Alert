# 🌊 Dam Water Level Alert System — Product Document

**Product Name:** KaLai Vivasayam Dam Alert (or "Village Dam Notifier")
**Version:** 1.0
**Date:** August 2026
**Author:** Village Admin / Project Owner

---

## 1. Executive Summary

A community-first notification platform that monitors the live water levels of **Amaravathi Dam** and **Thirumoorthi Dam** and sends automated **SMS and WhatsApp alerts** to registered farmers in the village. The goal is to help farmers make informed decisions about irrigation scheduling, crop protection, and flood preparedness — all in their native language.

---

## 2. Problem Statement

Farmers in the village currently have no reliable, real-time channel to know the water level status of the two dams that feed their irrigation channels. They rely on:
- Word of mouth from neighbors
- Occasional government announcements on radio/TV
- Physically visiting the dam or canal office

This leads to:
- **Over-irrigation** (wasting water when dam is full)
- **Under-irrigation** (crops damaged when water release is delayed)
- **Flooding of farmlands** due to unexpected sudden water release
- **Missed opportunities** to plan sowing/harvesting around water availability

---

## 3. Product Goals

| Goal | Description |
|---|---|
| **Awareness** | Notify farmers of current dam water levels daily and on threshold events |
| **Safety** | Alert farmers immediately when dam levels are critically high (flood risk) |
| **Accessibility** | Deliver alerts in Tamil (and optionally English) via SMS and WhatsApp |
| **Inclusivity** | Work even on basic feature phones (SMS fallback) |
| **Simplicity** | Zero friction for farmers — just register once, receive alerts automatically |

---

## 4. Target Users

### Primary Users
- **Registered Farmers** of the village who depend on canal water from Amaravathi or Thirumoorthi dams for irrigation

### Secondary Users
- **Village Panchayat Admin** — manages farmer registrations and system configuration
- **Irrigation Department Officer** — can push manual alerts or verify data

---

## 5. Dams Covered

| Dam | Location | River | District |
|---|---|---|---|
| **Amaravathi Dam** | Amaravathipudur, Tiruppur | Amaravathi | Tiruppur, Tamil Nadu |
| **Thirumoorthi Dam** | Udumalaipettai, Tiruppur | Thirumoorthy / Kundaru | Tiruppur, Tamil Nadu |

---

## 6. Key Features

### 6.1 Farmer Registration
- Farmers register via the Village Panchayat Office or a simple WhatsApp bot
- Data collected: **Name, Phone Number, Village, Farm Size (acres), Primary Dam (Amaravathi / Thirumoorthi / Both)**
- Registered in a central database
- Farmer receives a **welcome message** confirming registration

### 6.2 Automated Daily Water Level Alerts
- Every morning at **7:00 AM**, all registered farmers receive the current water level of their subscribed dam(s)
- Data is fetched from **tnagriculture.in** and includes: **Level (Feet)**, **Storage (M.Cft.)**, **Inflow (CuSecs)**, and **Outflow (CuSecs)**
- Message format (Tamil + English):

```
Amaravathi Dam | 13-08-2026, Kaalai 7:00
------------------------------
Neer Mattam (Level)  : 53.41 Adi (Feet)
Semippu (Storage)    : 1350 M.Cft. (33% nirampu)
Ulvaru (Inflow)      : 346 CuSecs
Veliyeeru (Outflow)  : 0 CuSecs
Nilai (Status)       : Sadhaaranam (Normal)
------------------------------
KaLai Vivasayam Dam Alert
```

> **Note on fields sourced from tnagriculture.in:**
> - **Level** — Current Year Level (Feet)
> - **Storage** — Current Year Storage (M.Cft.)
> - **Inflow** — Current Year Inflow (CuSecs)
> - **Outflow** — Current Year Outflow (CuSecs)
> - **Full Depth / Full Capacity** — used to calculate % fill and inflow-based time-to-fill

### 6.3 Threshold-Based Instant Alerts

Alert thresholds are determined by **two combined factors**:
1. **Current % fill** (Storage / Full Capacity × 100)
2. **Estimated Time-to-Fill (TTF)** — calculated from net inflow rate:

$$\text{TTF (hours)} = \frac{\text{Remaining Capacity (M.Cft.)}}{\text{Net Inflow (CuSecs)} \times 0.00028347}$$

> *(1 CuSec flowing for 1 hour ≈ 0.00028347 M.Cft. — conversion factor used internally)*

This allows the system to warn farmers well in advance based on **how fast** the dam is filling, not just current level.

| Level | Trigger Condition | Alert Type |
|---|---|---|
| 🟢 **Normal** | Fill < 70% AND TTF > 72 hours | Daily 7 AM digest only |
| 🟡 **Caution** | Fill 70%–85% OR TTF < 48 hours | Alert at threshold crossing + daily digest |
| 🟠 **High** | Fill 85%–95% OR TTF < 24 hours | Alert every 6 hours |
| 🔴 **Critical / Flood Risk** | Fill > 95% OR TTF < 6 hours OR outflow spike | Immediate alert + every 2 hours |
| 💧 **Water Release** | Outflow > 0 CuSecs after being 0 (canal opened) | Immediate advance notice to farmers |
| ⬇️ **Low / Drought Risk** | Fill < 20% AND inflow < 50 CuSecs | Alert to manage irrigation expectations |

**Example scenario:**
> Dam is at 80% full. Inflow = 800 CuSecs, Outflow = 0. Remaining = 20% of capacity.
> TTF = ~18 hours → 🟠 **High Alert** triggered even though level alone is 80%.

### 6.4 Water Release Advance Notice
- When water is about to be released into the canals, farmers receive:
  - **12 hours in advance**: "Water release expected tomorrow at [time]"
  - **2 hours in advance**: "Water release starting soon — prepare your fields"

### 6.5 Canal Water Schedule Alerts
- Weekly canal schedule shared every Sunday at 6:00 AM
- Farmers know which days water will reach their section of the canal

### 6.6 Opt-In / Opt-Out
- Farmers can reply **"STOP"** to unsubscribe from all alerts
- Farmers can reply **"START"** to re-subscribe
- Farmers can reply **"LEVEL"** anytime to get current dam levels on demand

---

## 7. Notification Channel

### 7.1 SMS (Only Channel)
- **Provider**: MSG91, Textlocal, or Twilio SMS
- Reaches **all** mobile phones including basic 2G feature phones — no smartphone or app required
- Messages sent as Tamil / bilingual plaintext
- Delivery receipt tracked per farmer
- Supports **inbound keyword replies** from farmers:

| Farmer Replies | Action |
|---|---|
| `LEVEL` | System sends current dam level instantly |
| `STOP` | Unsubscribes farmer from all alerts |
| `START` | Re-subscribes farmer |
| `HELP` | Sends a list of available keywords |

> **Why SMS only?** SMS works on every mobile network and device — no internet needed. This maximizes reach for all farmers in the village regardless of smartphone ownership.

---

## 8. Data Sources

### Primary Source — TN Agriculture Reservoir Portal (Live)
- **URL**: [https://tnagriculture.in/ARS/home/reservoir](https://tnagriculture.in/ARS/home/reservoir)
- **Published by**: Tamil Nadu Department of Agriculture (ARS — Agro-meteorological Research Station)
- **Update Frequency**: Daily — data typically published by 9:00 AM (verified live as of 13-08-2026)
- **Access method**: HTTP scraping of the HTML table (no API key required)
- **Date-specific URL format**: `https://tnagriculture.in/ARS/home/reservoir/YYYY-MM-DD`

**Fields available for both Amaravathi and Thirumurthy dams:**

| Field | Column Name on Site | Unit |
|---|---|---|
| Full Depth | Full Depth | Feet |
| Full Capacity | Full Capacity | M.Cft. |
| Current Level | Current Year Level | Feet |
| Current Storage | Current Year Storage | M.Cft. |
| Current Inflow | Current Year Inflow | CuSecs |
| Current Outflow | Current Year Outflow | CuSecs |
| Last Year Level | Last Year Level | Feet |
| Last Year Storage | Last Year Storage | M.Cft. |

**Live data sample (13-08-2026):**

| Dam | Full Depth | Full Cap. | Level | Storage | Inflow | Outflow |
|---|---|---|---|---|---|---|
| AMARAVATHI | 90 ft | 4047 M.Cft | 53.41 ft | 1350 M.Cft | 346 CuSecs | — |
| Thirumurthy | 60 ft | 1744 M.Cft | 34.4 ft | 779 M.Cft | — | 21 CuSecs |

### Fallback — Manual Entry
- If the tnagriculture.in site is down or data is missing, the Panchayat Admin enters values manually via the admin panel
- System logs a scraping failure alert to the admin dashboard automatically

### Future — IoT Sensor (Phase 4)
- Ultrasonic/pressure sensor at dam outflow
- Transmits readings via GPRS/LoRa every hour for real-time automation

---

## 9. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          DATA SOURCES                            │
│  [tnagriculture.in/ARS/home/reservoir]   [Manual Admin Entry]   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ (daily scrape + fallback)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                        BACKEND SERVER                            │
│   • Scheduled data fetcher (cron — 6 AM daily + every 2h)       │
│   • Alert rule engine (% fill + inflow TTF threshold checks)     │
│   • Farmer database (registration store)                         │
│   • Message queue (bulk SMS dispatch)                            │
│   • Admin dashboard API                                          │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
               ┌───────────────────────────┐
               │       SMS Gateway         │
               │  (MSG91 / Textlocal /     │
               │   Twilio SMS)             │
               └──────────────┬────────────┘
                              │
                              ▼
              ┌─────────────────────────────┐
              │      FARMERS' PHONES        │
              │  (Any mobile — SMS only)    │
              └─────────────────────────────┘

                              +
              ┌─────────────────────────────┐
              │      ADMIN WEB PANEL        │
              │  (Register, View, Push)     │
              └─────────────────────────────┘
```

---

## 10. Admin Panel Features

| Feature | Description |
|---|---|
| **Farmer Registration** | Add, edit, remove farmers; view registered list |
| **Manual Data Entry** | Enter today's dam level in 2 clicks |
| **Manual Alert Push** | Send custom message to all / subset of farmers |
| **Alert Logs** | View history of all messages sent, delivery status |
| **Dam Level History** | Graph of water levels over past 30/90 days |
| **Subscriber Stats** | How many active vs. unsubscribed farmers |

---

## 11. Message Templates (SMS Format)

> SMS messages are kept under 160 characters per part where possible. Tamil Unicode SMS uses GSM extended encoding.

### Daily Morning Alert
```
AMARVTHI DAM 13-08-2026
Level: 53.41 ft (59% Full)
Storage: 1350 MCft
Inflow: 346 CuSecs
Outflow: 0 CuSecs
Status: NORMAL
Reply LEVEL for update.
-KaLai Dam Alert
```

### Caution Alert (70–85% fill OR TTF < 48 hrs)
```
[CAUTION] AMARVTHI DAM
Level: 74 ft | 82% Full
Inflow: 920 CuSecs | Out: 0
Est. Time to Full: ~31 hrs
Monitor your canal. Prepare fields.
-KaLai Dam Alert
```

### Critical / Flood Risk Alert (TTF < 6 hrs or >95%)
```
[FLOOD WARNING] AMARVTHI DAM
Level: 88 ft | 97% Full!
Inflow: 2100 CuSecs | Out: 800
Est. Full in: ~4 hrs
Protect your fields NOW.
Dist. Office: 0422-XXXXXXX
-KaLai Dam Alert
```

### Water Release / Canal Opened Alert
```
[WATER RELEASE] AMARVTHI
Outflow started: 346 CuSecs
Canal water expected soon.
Prepare your fields!
-KaLai Dam Alert
```

### On-Demand Reply (Farmer sends LEVEL)
```
AMARVTHI: 53.41ft|33%Full
In:346 CuSecs Out:0 CuSecs
THIRUMRTHY: 34.4ft|45%Full
In:0 CuSecs Out:21 CuSecs
Time:13-08-2026 10:32
-KaLai Dam Alert
```

---

## 12. Registration Flow

```
Farmer → Visits Panchayat Office
         OR
         Sends WhatsApp to Village Bot Number
         
         ↓
Bot / Admin Collects:
  • பெயர் (Name)
  • கைபேசி எண் (Phone Number)
  • கிராமம் (Village / Hamlet)
  • சர்வே எண் / நிலம் (Survey No / Land details) [optional]
  • எந்த அணை? (Which dam? Amaravathi / Thirumoorthi / Both)
  • மொழி விருப்பம் (Language: Tamil / English)
  
         ↓
Farmer added to database
Welcome message sent:
"வணக்கம் [Name]! நீங்கள் Dam Alert கணினியில் பதிவு செய்யப்பட்டீர்கள். தினமும் காலை 7 மணிக்கு அணை நிலை தகவல் கிடைக்கும். 🙏"
```

---

## 13. Technology Stack (Recommended)

| Layer | Technology |
|---|---|
| **Backend** | Python (FastAPI) or Node.js |
| **Database** | PostgreSQL (farmer registry + alert logs) |
| **Scheduler** | Cron (Linux) or Celery Beat |
| **SMS Gateway** | MSG91 / Textlocal / Twilio SMS |
| **Admin Frontend** | Simple HTML/JS or React |
| **Hosting** | Render, Railway, or a cheap VPS (₹300–500/month) |
| **Data Scraping** | Python `requests` + `BeautifulSoup` (tnagriculture.in) |
| **TTF Calculation** | Python — in-memory calculation (no extra library needed) |

---

## 14. Cost Estimate (Monthly)

| Item | Estimated Cost |
|---|---|
| Server / Hosting | ₹300–₹600 |
| SMS (per message) | ₹0.10–₹0.25 per message |
| **Scenario: 200 farmers, 1 msg/day** | ~₹600–₹1,500/month |
| **Scenario: 200 farmers, 2 msgs/day** | ~₹1,200–₹3,000/month |
| **Critical alert days (extra SMS)** | +₹200–₹500 on heavy rainfall months |

> 💡 **Cost tip**: Use a bulk SMS DLT-registered sender ID for Tamil Nadu — MSG91 and Textlocal offer routes at ₹0.12–₹0.16/SMS for transactional messages.

---

## 15. Privacy & Data Protection

- Farmers' phone numbers are stored securely and never shared with third parties
- Database is password-protected and access-restricted to Admin only
- Farmers can request deletion of their data at any time
- No financial data is collected
- Compliant with India's IT Act 2000 and PDPB guidelines

---

## 16. Rollout Plan

| Phase | Timeline | Milestone |
|---|---|---|
| **Phase 0 — Research** | Week 1 | Confirm data source (TN WRD API/scraping), get WhatsApp Business API access |
| **Phase 1 — MVP Build** | Week 2–3 | Backend + SMS alerts working, manual data entry, 20 pilot farmers |
| **Phase 2 — Pilot** | Week 4 | Run for 30 days, gather farmer feedback, fix bugs |
| **Phase 3 — Expansion** | Month 2 | Add WhatsApp, admin dashboard, onboard all farmers |
| **Phase 4 — Automation** | Month 3+ | Auto-fetch data from govt portal, optional IoT sensor |

---

## 17. Success Metrics

| Metric | Target |
|---|---|
| Farmer registration rate | >80% of eligible farmers in village |
| Message delivery success rate | >95% |
| Farmer satisfaction (survey) | >4/5 stars |
| Response to water release notice | Farmer acknowledges / prepares in time |
| Flood false-alarm rate | <5% |

---

## 18. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| TN WRD website structure changes (scraping breaks) | Add manual entry fallback; alert admin on scrape failure |
| WhatsApp API approval delays | Start with SMS only; add WhatsApp after approval |
| Farmers ignore messages | Use Tamil language + practical message format; educate during registration |
| Incorrect dam level data sent | Admin review step before sending critical alerts |
| Cost overrun | Cap daily messages; use free tier where possible |

---

## 19. Future Enhancements

- 🌦️ **Rain forecast integration** — alert when IMD predicts heavy rainfall upstream
- 🚜 **Crop-based advisory** — link water levels to crop watering schedules
- 📊 **Historical trend charts** — shareable via WhatsApp
- 🗺️ **Canal section mapping** — notify only farmers whose canal branch is affected
- 🤝 **Integration with Panchayat portal** — digital register synced automatically
- 📱 **Simple mobile app** — for farmers with smartphones who want a visual interface
- 🔔 **IVRS (Interactive Voice Call)** — for farmers without WhatsApp or basic literacy

---

## 20. Contacts & Ownership

| Role | Responsibility |
|---|---|
| **Project Owner** | Village Admin / Panchayat President |
| **Technical Lead** | Developer (TBD) |
| **Data Coordinator** | Irrigation Department Liaison / Panchayat Staff |
| **Support Contact** | Designated village volunteer who can help farmers register |

---

*Document Version 1.0 — KaLai Vivasayam Dam Alert System*
*For internal use by Village Panchayat and Development Team*
