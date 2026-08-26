# 🛠️ Tech Stack Document — KaLai Vivasayam Dam Alert System

**Product:** KaLai Vivasayam Dam Alert
**Version:** 1.0
**Date:** August 2026
**Related Doc:** [Product Document](file:///Users/praga/.gemini/antigravity/brain/0dbc2770-1a01-4577-ad94-f4758480a7c1/dam_alert_product_doc.md)

---

## 1. System Overview

The system has **five core layers** that work together:

```
┌────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — DATA SCRAPER                                            │
│  Fetches dam data daily from tnagriculture.in                      │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────┐
│  LAYER 2 — ALERT RULE ENGINE                                       │
│  Computes % Fill + Time-to-Fill (TTF), evaluates thresholds        │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────┐
│  LAYER 3 — BACKEND API + DATABASE                                  │
│  FastAPI REST API + PostgreSQL (farmer registry, logs, readings)   │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────┐
│  LAYER 4 — SMS DISPATCHER                                          │
│  MSG91 Bulk SMS — sends alerts, handles LEVEL/STOP/START replies   │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────┐
│  LAYER 5 — ADMIN PANEL                                             │
│  React web UI — farmer registration, manual entry, alert history   │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. Full Tech Stack at a Glance

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Language | **Python** | 3.11+ | Backend, scraper, alert engine |
| Web Framework | **FastAPI** | 0.111+ | REST API server |
| Database | **PostgreSQL** | 15+ | Farmer registry, readings, logs |
| ORM | **SQLAlchemy** | 2.0+ | DB models and queries |
| Migrations | **Alembic** | 1.13+ | Schema versioning |
| Task Queue | **Celery** | 5.3+ | Async SMS dispatch, scrape jobs |
| Message Broker | **Redis** | 7.0+ | Celery broker + result backend |
| Scheduler | **Celery Beat** | 5.3+ | Cron-like periodic task runner |
| HTML Scraper | **httpx + BeautifulSoup4** | latest | Scrape tnagriculture.in |
| SMS Gateway | **MSG91** | API v5 | Bulk SMS India, DLT compliant |
| Admin Frontend | **React + Vite** | React 18 | Admin panel UI |
| Hosting | **Ubuntu VPS** | 22.04 LTS | DigitalOcean / Hetzner (~₹500/mo) |
| Process Manager | **systemd** | — | Auto-restart services on crash |
| Reverse Proxy | **Nginx** | 1.24+ | HTTPS, static files, API proxy |
| SSL | **Let's Encrypt (Certbot)** | — | Free HTTPS |
| Env Config | **python-dotenv** | — | Secrets management |
| Logging | **Python logging + Sentry** | — | Error tracking |

---

## 3. Layer 1 — Data Scraper

### What it does
- Hits `https://tnagriculture.in/ARS/home/reservoir/YYYY-MM-DD` every day at **9:00 AM**
- Parses the HTML table using BeautifulSoup
- Extracts rows for **AMARAVATHI** and **Thirumurthy**
- Saves the data to PostgreSQL `dam_readings` table

### Libraries
```
httpx==0.27.*          # Async HTTP client (faster than requests)
beautifulsoup4==4.12.* # HTML parsing
lxml==5.*              # Fast HTML parser backend for BS4
```

### Scraper Module: `scraper/tnagriculture.py`
```python
import httpx
from bs4 import BeautifulSoup
from datetime import date

DAMS_OF_INTEREST = ["AMARAVATHI", "THIRUMURTHY"]
BASE_URL = "https://tnagriculture.in/ARS/home/reservoir"

async def fetch_dam_data(for_date: date = None) -> list[dict]:
    url = f"{BASE_URL}/{for_date}" if for_date else BASE_URL
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table")
    rows = table.find_all("tr")

    results = []
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cols:
            continue
        dam_name = cols[0].upper().strip("*")
        if any(d in dam_name for d in DAMS_OF_INTEREST):
            results.append({
                "dam_name":       dam_name,
                "full_depth_ft":  safe_float(cols[1]),
                "full_cap_mcft":  safe_float(cols[2]),
                "level_ft":       safe_float(cols[3]),
                "storage_mcft":   safe_float(cols[4]),
                "inflow_cusecs":  safe_float(cols[5]),
                "outflow_cusecs": safe_float(cols[6]),
                "last_yr_level":  safe_float(cols[7]),
                "last_yr_storage":safe_float(cols[8]),
            })
    return results

def safe_float(val: str) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
```

### Failure Handling
| Failure Scenario | System Response |
|---|---|
| Website is down / times out | Retry 3 times with 5-min gap; notify admin via SMS if all retries fail |
| Data row missing for a dam | Log warning; use previous day's reading for alert context; mark as stale |
| Unexpected HTML structure | Catch parse error; alert admin; trigger manual entry mode |

---

## 4. Layer 2 — Alert Rule Engine

### What it does
- Takes the scraped dam reading
- Computes **% Fill** and **Time-to-Fill (TTF)**
- Compares against threshold rules
- Decides what alert level to trigger and who to notify

### Module: `engine/alert_rules.py`

#### % Fill Calculation
```python
def calculate_fill_percent(storage_mcft: float, full_cap_mcft: float) -> float:
    if not full_cap_mcft:
        return 0.0
    return round((storage_mcft / full_cap_mcft) * 100, 2)
```

#### Time-to-Fill (TTF) Calculation
```python
# Conversion: 1 CuSec for 1 hour = 0.00028347 M.Cft
CUSEC_TO_MCFT_PER_HOUR = 0.00028347

def calculate_ttf_hours(
    storage_mcft: float,
    full_cap_mcft: float,
    inflow_cusecs: float,
    outflow_cusecs: float
) -> float | None:
    """Returns estimated hours until dam reaches full capacity."""
    net_inflow = (inflow_cusecs or 0) - (outflow_cusecs or 0)
    if net_inflow <= 0:
        return None  # Not filling — no TTF applicable
    remaining = full_cap_mcft - storage_mcft
    ttf = remaining / (net_inflow * CUSEC_TO_MCFT_PER_HOUR)
    return round(ttf, 1)
```

#### Alert Level Evaluation
```python
from enum import Enum

class AlertLevel(str, Enum):
    NORMAL   = "NORMAL"
    CAUTION  = "CAUTION"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"
    LOW      = "LOW"
    RELEASE  = "RELEASE"

def evaluate_alert_level(
    fill_pct: float,
    ttf_hours: float | None,
    inflow_cusecs: float,
    prev_outflow: float,
    curr_outflow: float,
) -> AlertLevel:
    # Water release detected: outflow switched from 0 to > 0
    if prev_outflow == 0 and curr_outflow > 0:
        return AlertLevel.RELEASE

    # Drought / low water risk
    if fill_pct < 20 and (inflow_cusecs or 0) < 50:
        return AlertLevel.LOW

    # Critical — level-based OR inflow-based
    if fill_pct > 95 or (ttf_hours is not None and ttf_hours < 6):
        return AlertLevel.CRITICAL

    # High
    if fill_pct > 85 or (ttf_hours is not None and ttf_hours < 24):
        return AlertLevel.HIGH

    # Caution
    if fill_pct > 70 or (ttf_hours is not None and ttf_hours < 48):
        return AlertLevel.CAUTION

    return AlertLevel.NORMAL
```

#### Alert Dispatch Frequency Rules
```python
ALERT_FREQUENCY = {
    AlertLevel.NORMAL:   "daily_only",    # Only morning digest
    AlertLevel.CAUTION:  "on_threshold",  # Once when level crossed
    AlertLevel.HIGH:     "every_6h",      # Every 6 hours
    AlertLevel.CRITICAL: "every_2h",      # Every 2 hours
    AlertLevel.LOW:      "on_threshold",
    AlertLevel.RELEASE:  "immediate",     # Instant
}
```

---

## 5. Layer 3 — Backend API + Database

### Framework: FastAPI

```
backend/
├── main.py               # FastAPI app entrypoint
├── routers/
│   ├── farmers.py        # CRUD: register, list, update, delete
│   ├── dams.py           # Manual dam reading entry
│   ├── alerts.py         # Alert log, manual push
│   └── sms.py            # Inbound SMS webhook (LEVEL/STOP/START)
├── models/               # SQLAlchemy ORM models
│   ├── farmer.py
│   ├── dam_reading.py
│   └── alert_log.py
├── schemas/              # Pydantic request/response schemas
├── services/
│   ├── scraper_service.py
│   ├── alert_service.py
│   └── sms_service.py
├── engine/
│   └── alert_rules.py    # TTF + threshold logic
├── scraper/
│   └── tnagriculture.py
├── tasks/
│   └── celery_tasks.py   # Celery task definitions
└── config.py             # Settings via .env
```

### Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/farmers/register` | Register a new farmer |
| `GET` | `/farmers` | List all farmers (admin) |
| `PUT` | `/farmers/{id}` | Update farmer details |
| `DELETE` | `/farmers/{id}` | Remove farmer |
| `GET` | `/dams/readings` | Get latest dam readings |
| `POST` | `/dams/readings/manual` | Admin manually enters reading |
| `GET` | `/alerts/logs` | View all sent alert history |
| `POST` | `/alerts/push` | Admin manually pushes a custom alert |
| `POST` | `/sms/inbound` | Webhook: handles LEVEL/STOP/START replies |

---

## 6. Database Schema (PostgreSQL)

### Table: `farmers`
```sql
CREATE TABLE farmers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)        NOT NULL,
    phone           VARCHAR(15)         UNIQUE NOT NULL,   -- E.164 format: +9194XXXXXXXX
    village         VARCHAR(100),
    farm_size_acres NUMERIC(6,2),
    dam_preference  VARCHAR(20)         DEFAULT 'BOTH',    -- AMARAVATHI | THIRUMURTHY | BOTH
    language        VARCHAR(10)         DEFAULT 'TAMIL',   -- TAMIL | ENGLISH
    is_active       BOOLEAN             DEFAULT TRUE,
    registered_at   TIMESTAMPTZ         DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         DEFAULT NOW()
);
```

### Table: `dam_readings`
```sql
CREATE TABLE dam_readings (
    id               SERIAL PRIMARY KEY,
    dam_name         VARCHAR(50)     NOT NULL,   -- 'AMARAVATHI' | 'THIRUMURTHY'
    reading_date     DATE            NOT NULL,
    full_depth_ft    NUMERIC(6,2),
    full_cap_mcft    NUMERIC(10,2),
    level_ft         NUMERIC(6,2),
    storage_mcft     NUMERIC(10,2),
    inflow_cusecs    NUMERIC(10,2),
    outflow_cusecs   NUMERIC(10,2),
    fill_percent     NUMERIC(5,2),   -- computed: (storage/full_cap)*100
    ttf_hours        NUMERIC(8,1),   -- computed TTF; NULL if not filling
    alert_level      VARCHAR(20),    -- NORMAL | CAUTION | HIGH | CRITICAL | LOW | RELEASE
    source           VARCHAR(20)     DEFAULT 'SCRAPER',   -- SCRAPER | MANUAL
    created_at       TIMESTAMPTZ     DEFAULT NOW(),
    UNIQUE(dam_name, reading_date)
);
```

### Table: `alert_logs`
```sql
CREATE TABLE alert_logs (
    id              SERIAL PRIMARY KEY,
    farmer_id       INTEGER         REFERENCES farmers(id),
    dam_name        VARCHAR(50),
    alert_level     VARCHAR(20),
    message_text    TEXT,
    sms_status      VARCHAR(20),    -- QUEUED | SENT | DELIVERED | FAILED
    sms_provider_id VARCHAR(100),   -- MSG91 message ID for tracking
    sent_at         TIMESTAMPTZ     DEFAULT NOW()
);
```

### Table: `admin_users`
```sql
CREATE TABLE admin_users (
    id           SERIAL PRIMARY KEY,
    username     VARCHAR(50)   UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,   -- bcrypt
    created_at   TIMESTAMPTZ   DEFAULT NOW()
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_farmers_phone ON farmers(phone);
CREATE INDEX idx_farmers_active ON farmers(is_active);
CREATE INDEX idx_readings_dam_date ON dam_readings(dam_name, reading_date DESC);
CREATE INDEX idx_alert_logs_farmer ON alert_logs(farmer_id);
CREATE INDEX idx_alert_logs_sent_at ON alert_logs(sent_at DESC);
```

---

## 7. Layer 4 — SMS Dispatcher

### Provider: MSG91

**Why MSG91:**
- India-focused; DLT (Distributed Ledger Technology) pre-registration for promotional/transactional SMS
- Supports inbound SMS webhooks (for LEVEL/STOP/START replies)
- Tamil Unicode support
- Competitive pricing: ₹0.12–₹0.16/SMS on bulk plans
- Reliable delivery reports via webhook

### DLT Registration (Mandatory for India)
Before sending any SMS in India, you must register with TRAI's DLT portal:

| Item | Details |
|---|---|
| **Entity Registration** | Register Village Panchayat as sender entity |
| **Header (Sender ID)** | e.g., `KLDAMT` (6-char alphanumeric) |
| **Template Registration** | Each SMS template must be pre-approved |
| **Template Type** | Transactional (not promotional) |
| **Time to Approve** | 2–5 working days |

### SMS Service Module: `services/sms_service.py`
```python
import httpx
from config import settings

MSG91_API_URL = "https://api.msg91.com/api/v5/flow/"

async def send_sms(phone: str, message: str, template_id: str) -> dict:
    """
    Send a single SMS via MSG91.
    phone: E.164 format without '+', e.g. '919400000000'
    """
    payload = {
        "template_id": template_id,
        "sender":      settings.SMS_SENDER_ID,    # e.g. 'KLDAMT'
        "short_url":   "0",
        "mobiles":     phone,
        "message":     message,
    }
    headers = {
        "authkey":      settings.MSG91_AUTH_KEY,
        "content-type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(MSG91_API_URL, json=payload, headers=headers)
    return response.json()

async def send_bulk_sms(farmers: list[dict], message_fn) -> None:
    """Send personalized SMS to a list of farmers concurrently."""
    import asyncio
    tasks = [
        send_sms(f["phone"], message_fn(f), f["template_id"])
        for f in farmers
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
```

### Inbound SMS Webhook: `routers/sms.py`
```python
@router.post("/inbound")
async def handle_inbound_sms(payload: dict):
    phone   = payload.get("mobile")
    keyword = payload.get("message", "").strip().upper()

    if keyword == "LEVEL":
        reading = await get_latest_readings()
        msg = format_on_demand_sms(reading)
        await send_sms(phone, msg, template_id=settings.TEMPLATE_LEVEL)

    elif keyword == "STOP":
        await deactivate_farmer(phone)
        await send_sms(phone, "You have been unsubscribed from Dam Alerts.", ...)

    elif keyword == "START":
        await activate_farmer(phone)
        await send_sms(phone, "You are now subscribed to Dam Alerts again.", ...)

    elif keyword == "HELP":
        await send_sms(phone, "Reply: LEVEL=Current levels, STOP=Unsubscribe, START=Resubscribe", ...)

    return {"status": "ok"}
```

---

## 8. Layer 4b — Task Scheduler (Celery + Redis)

### Why Celery?
- Handles bulk SMS sending asynchronously (200 farmers = 200 SMS jobs queued)
- Prevents FastAPI request timeouts on large sends
- Retry logic built-in
- Celery Beat handles cron-like scheduling

### Scheduled Tasks

| Task | Schedule | Description |
|---|---|---|
| `scrape_and_store` | Daily at **9:00 AM** | Fetch tnagriculture.in, store reading |
| `evaluate_and_alert` | Daily at **9:15 AM** | Run alert rules on new reading |
| `send_morning_digest` | Daily at **9:30 AM** | Send morning SMS to all active farmers |
| `check_high_alerts` | Every **2 hours** | Re-alert if still HIGH or CRITICAL |
| `check_scrape_health` | Daily at **9:45 AM** | Verify today's data was scraped; alert admin if not |

### Celery Config: `tasks/celery_tasks.py`
```python
from celery import Celery
from celery.schedules import crontab

app = Celery("dam_alert", broker="redis://localhost:6379/0")

app.conf.beat_schedule = {
    "scrape-daily": {
        "task":     "tasks.scrape_and_store",
        "schedule": crontab(hour=9, minute=0),
    },
    "evaluate-alerts": {
        "task":     "tasks.evaluate_and_alert",
        "schedule": crontab(hour=9, minute=15),
    },
    "morning-digest": {
        "task":     "tasks.send_morning_digest",
        "schedule": crontab(hour=9, minute=30),
    },
    "high-alert-check": {
        "task":     "tasks.check_high_alerts",
        "schedule": crontab(minute=0),   # Every hour
    },
}

@app.task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_and_store(self):
    import asyncio
    from scraper.tnagriculture import fetch_dam_data
    from services.db_service import save_dam_readings
    try:
        data = asyncio.run(fetch_dam_data())
        save_dam_readings(data)
    except Exception as exc:
        raise self.retry(exc=exc)
```

---

## 9. Layer 5 — Admin Panel

### Stack: React 18 + Vite + Vanilla CSS

```
admin-panel/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx      # Quick stats: farmers, last reading, alert level
│   │   ├── Farmers.jsx        # Table: add, edit, activate/deactivate
│   │   ├── DamReadings.jsx    # View today's reading + manual entry form
│   │   ├── AlertHistory.jsx   # Paginated log of all sent SMS alerts
│   │   └── SendAlert.jsx      # Manual custom alert push
│   ├── components/
│   │   ├── DamCard.jsx        # Shows Level, Storage, Inflow, Outflow, TTF
│   │   ├── AlertBadge.jsx     # Color-coded NORMAL/CAUTION/HIGH/CRITICAL badge
│   │   └── FarmerTable.jsx
│   └── api/                   # Axios API client pointing to FastAPI backend
```

### Admin Panel Pages

| Page | Key Functions |
|---|---|
| **Dashboard** | Today's dam levels, alert status for both dams, active farmer count |
| **Farmers** | Add new farmer, view all registered farmers, activate/deactivate |
| **Dam Readings** | View scraped data; manually enter level/storage/inflow/outflow if scrape failed |
| **Alert History** | Filter by dam / date / alert level; view delivery status per farmer |
| **Send Alert** | Type a custom message + select dam + send to all/subset of farmers |

### Admin Authentication
- Simple **JWT-based login** (username + password)
- Single admin account — no roles needed for v1
- Token stored in `localStorage`, expires in 8 hours

---

## 10. Environment Configuration

### `.env` file (never committed to git)
```ini
# Database
DATABASE_URL=postgresql://damuser:password@localhost:5432/damalert

# Redis
REDIS_URL=redis://localhost:6379/0

# MSG91 SMS
MSG91_AUTH_KEY=your_msg91_auth_key
SMS_SENDER_ID=KLDAMT

# DLT-approved Template IDs
TEMPLATE_DAILY_DIGEST=your_template_id_1
TEMPLATE_CAUTION=your_template_id_2
TEMPLATE_HIGH=your_template_id_3
TEMPLATE_CRITICAL=your_template_id_4
TEMPLATE_RELEASE=your_template_id_5
TEMPLATE_LEVEL=your_template_id_6
TEMPLATE_LOW=your_template_id_7

# Admin panel
JWT_SECRET_KEY=a_long_random_secret_string
JWT_EXPIRE_HOURS=8

# Sentry (error tracking)
SENTRY_DSN=https://your_sentry_dsn

# App
APP_ENV=production
ADMIN_PHONE=+91XXXXXXXXXX   # Admin's phone for system health alerts
```

---

## 11. Hosting & Deployment

### Server: Ubuntu 22.04 VPS (DigitalOcean / Hetzner)

| Service | RAM | Estimated Cost |
|---|---|---|
| DigitalOcean Droplet 1GB | 1 GB | ~₹500/month |
| Hetzner CX11 | 2 GB | ~₹350/month ✅ Recommended |

### Services Running on Server

```
systemd services:
├── damalert-api.service       # FastAPI (via uvicorn)
├── damalert-worker.service    # Celery worker
├── damalert-beat.service      # Celery beat (scheduler)
├── redis.service              # Redis server
└── postgresql.service         # PostgreSQL database
```

### Nginx Config (reverse proxy)
```nginx
server {
    listen 80;
    server_name yourdomain.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.in;
    ssl_certificate /etc/letsencrypt/live/yourdomain.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.in/privkey.pem;

    # Admin panel (React static files)
    location / {
        root /var/www/dam-admin/dist;
        try_files $uri /index.html;
    }

    # FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # MSG91 inbound SMS webhook
    location /sms/inbound {
        proxy_pass http://127.0.0.1:8000/sms/inbound;
    }
}
```

### Deployment Checklist
- [ ] Provision VPS, SSH key set up
- [ ] Install Python 3.11, PostgreSQL 15, Redis 7, Nginx
- [ ] Clone repo, set `.env` variables
- [ ] Run `alembic upgrade head` (create DB tables)
- [ ] Build admin panel: `npm run build` → copy to `/var/www/dam-admin/dist`
- [ ] Set up systemd services + enable on boot
- [ ] Configure Nginx + SSL (Certbot)
- [ ] Register with MSG91, complete DLT registration
- [ ] Whitelist MSG91 webhook IP in firewall
- [ ] Test end-to-end: scrape → alert rule → SMS

---

## 12. Logging & Monitoring

### Application Logs
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("/var/log/damalert/app.log"),
        logging.StreamHandler()
    ]
)
```

### Log Rotation
```bash
# /etc/logrotate.d/damalert
/var/log/damalert/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

### Error Tracking: Sentry
```python
import sentry_sdk
sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
```
- Automatically captures unhandled exceptions
- Alerts via email when scraper or SMS dispatch fails

### Health Checks
- Celery beat sends a **daily self-test SMS** to the admin phone at 9:45 AM confirming scrape success
- If scrape fails 2 days in a row → admin receives: `[SYSTEM ALERT] Dam data scrape failed. Please enter readings manually.`

---

## 13. Security Considerations

| Risk | Mitigation |
|---|---|
| Unauthorized admin access | JWT auth + HTTPS only |
| MSG91 webhook spoofing | Validate `X-Msg91-Signature` header; IP whitelist |
| Farmer data exposure | No public API endpoints for farmer data; admin auth required |
| SQL injection | SQLAlchemy ORM with parameterized queries |
| `.env` secrets leak | `.gitignore` enforced; secrets never committed |
| DDoS on API | Rate limiting via `slowapi` (FastAPI middleware) |
| VPS access | SSH key only; password auth disabled; UFW firewall |

---

## 14. Python Dependencies Summary

```txt
# requirements.txt

# Web framework
fastapi==0.111.*
uvicorn[standard]==0.30.*

# Database
sqlalchemy==2.0.*
alembic==1.13.*
psycopg2-binary==2.9.*

# Task queue
celery[redis]==5.3.*
redis==5.0.*

# HTTP + scraping
httpx==0.27.*
beautifulsoup4==4.12.*
lxml==5.*

# Auth
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*

# Config
python-dotenv==1.0.*

# Validation
pydantic==2.7.*
pydantic-settings==2.3.*

# Monitoring
sentry-sdk[fastapi]==2.*

# Rate limiting
slowapi==0.1.*
```

---

## 15. Phased Delivery Plan

| Phase | Scope | Effort Estimate |
|---|---|---|
| **Phase 1 — Core MVP** | Scraper + DB + Daily SMS digest | 1.5 weeks |
| **Phase 2 — Alert Engine** | TTF logic + threshold alerts + LEVEL reply | 1 week |
| **Phase 3 — Admin Panel** | React UI for farmer management + manual entry | 1 week |
| **Phase 4 — Production** | VPS deploy, Nginx, SSL, DLT registration | 3–5 days |
| **Phase 5 — Hardening** | Logging, Sentry, health checks, retry logic | 3 days |

**Total estimated build time: ~4–5 weeks** for one developer

---

## 16. Folder Structure (Full Project)

```
dam-alert/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── alembic/            # DB migration scripts
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── engine/
│   ├── scraper/
│   └── tasks/
├── admin-panel/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
├── .env                    # NOT in git
├── .env.example            # Template for .env
├── .gitignore
├── nginx.conf
└── README.md
```

---

*Tech Stack Document v1.0 — KaLai Vivasayam Dam Alert System*
*Paired with: [Product Document](file:///Users/praga/.gemini/antigravity/brain/0dbc2770-1a01-4577-ad94-f4758480a7c1/dam_alert_product_doc.md)*
