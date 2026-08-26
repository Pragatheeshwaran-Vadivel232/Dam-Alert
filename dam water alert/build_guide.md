# 🚀 Step-by-Step Build Guide — KaLai Vivasayam Dam Alert System
### For First-Time Developers

**Your OS:** macOS
**Skill Level:** Beginner — everything explained from scratch

---

> ## Before You Start
> This guide walks you through building the full system in **7 phases**.
> Each phase builds on the previous one. Do them in order.
> 
> **Estimated total time:** 4–6 weeks (working 2–3 hours/day)
> 
> You will be building:
> - A **data scraper** that reads dam levels from a government website
> - An **alert engine** that decides when to send SMS
> - A **database** that stores farmer details
> - An **SMS sender** that messages farmers automatically
> - An **admin panel** website for managing farmers

---

## 📦 Phase 0 — Install Your Tools (Day 1)

These are the programs you need on your Mac before writing any code.

---

### Step 0.1 — Install Homebrew (Mac's App Installer)
Homebrew lets you install developer tools easily from Terminal.

Open **Terminal** (press `Cmd + Space`, type "Terminal", press Enter) and run:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
> **What this does:** Installs Homebrew, which you'll use to install everything else.

---

### Step 0.2 — Install Python 3.11
```bash
brew install python@3.11
```
Verify it worked:
```bash
python3 --version
# Should print: Python 3.11.x
```
> **What Python is:** The programming language we use to write the backend, scraper, and alert engine.

---

### Step 0.3 — Install PostgreSQL (Database)
```bash
brew install postgresql@15
brew services start postgresql@15
```
Verify it worked:
```bash
psql --version
# Should print: psql (PostgreSQL) 15.x
```
> **What PostgreSQL is:** A database — like a very organized Excel file — that stores all farmer phone numbers, dam readings, and SMS logs permanently.

---

### Step 0.4 — Install Redis (Task Queue)
```bash
brew install redis
brew services start redis
```
Verify:
```bash
redis-cli ping
# Should print: PONG
```
> **What Redis is:** A fast in-memory store that Celery uses to queue up SMS jobs (like a waiting list for tasks).

---

### Step 0.5 — Install Node.js (for Admin Panel)
```bash
brew install node
```
Verify:
```bash
node --version   # Should print v20.x or higher
npm --version    # Should print 10.x or higher
```
> **What Node.js is:** Used only for building the admin panel website (React). Your backend runs on Python, not Node.

---

### Step 0.6 — Install VS Code (Code Editor)
Download from: **https://code.visualstudio.com**

After installing, open VS Code and install these extensions:
- **Python** (by Microsoft)
- **Pylance** (by Microsoft)
- **SQLTools** (to view your database visually)
- **Thunder Client** (to test your API without code)
- **ES7+ React Snippets** (for admin panel)

> **What VS Code is:** The app where you write all your code. Think of it like Microsoft Word, but for code.

---

### Step 0.7 — Install Git (Version Control)
```bash
brew install git
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```
> **What Git is:** Tracks every change you make to your code, so you can go back if something breaks. Like "Undo" that never expires.

---

## 🗂️ Phase 1 — Create Your Project (Day 1–2)

### Step 1.1 — Create the Project Folder
```bash
mkdir dam-alert
cd dam-alert
mkdir backend admin-panel
```

### Step 1.2 — Set Up Python Virtual Environment
A virtual environment keeps your project's libraries separate from other projects.
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
```
You'll see `(venv)` appear in your terminal. This means it's active.

> **Every time you open a new Terminal tab to work on this project, run:**
> ```bash
> cd dam-alert/backend
> source venv/bin/activate
> ```

### Step 1.3 — Install All Python Libraries
Create a file called `requirements.txt` inside `backend/` and paste this:
```
fastapi==0.111.*
uvicorn[standard]==0.30.*
sqlalchemy==2.0.*
alembic==1.13.*
psycopg2-binary==2.9.*
celery[redis]==5.3.*
redis==5.0.*
httpx==0.27.*
beautifulsoup4==4.12.*
lxml==5.*
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
python-dotenv==1.0.*
pydantic==2.7.*
pydantic-settings==2.3.*
sentry-sdk[fastapi]==2.*
slowapi==0.1.*
```

Then install them:
```bash
pip install -r requirements.txt
```
> This will take 2–3 minutes. You'll see a lot of text — that's normal.

### Step 1.4 — Create the Project Folder Structure
```bash
# Inside backend/
mkdir routers models schemas services engine scraper tasks
touch main.py config.py
touch routers/__init__.py models/__init__.py
touch schemas/__init__.py services/__init__.py
touch engine/__init__.py scraper/__init__.py tasks/__init__.py
```

Your folder should now look like this:
```
dam-alert/
├── backend/
│   ├── venv/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── engine/
│   ├── scraper/
│   └── tasks/
└── admin-panel/
```

---

## 🗄️ Phase 2 — Set Up the Database (Day 2–3)

### Step 2.1 — Create the Database
```bash
psql postgres
```
Inside the PostgreSQL shell, run:
```sql
CREATE DATABASE damalert;
CREATE USER damuser WITH PASSWORD 'yourpassword123';
GRANT ALL PRIVILEGES ON DATABASE damalert TO damuser;
\q
```
> Replace `yourpassword123` with something strong. Write it down somewhere safe.

### Step 2.2 — Create Your `.env` File
Inside `backend/`, create a file named `.env`:
```ini
DATABASE_URL=postgresql://damuser:yourpassword123@localhost:5432/damalert
REDIS_URL=redis://localhost:6379/0
MSG91_AUTH_KEY=your_msg91_key_here
SMS_SENDER_ID=KLDAMT
TEMPLATE_DAILY_DIGEST=your_template_id
TEMPLATE_CAUTION=your_template_id
TEMPLATE_HIGH=your_template_id
TEMPLATE_CRITICAL=your_template_id
TEMPLATE_RELEASE=your_template_id
TEMPLATE_LEVEL=your_template_id
TEMPLATE_LOW=your_template_id
JWT_SECRET_KEY=make_this_a_long_random_string_abc123xyz
JWT_EXPIRE_HOURS=8
ADMIN_PHONE=+91XXXXXXXXXX
APP_ENV=development
```
> **Important:** Create a `.gitignore` file and add `.env` to it so you never accidentally share your passwords:
> ```
> echo ".env" >> .gitignore
> echo "venv/" >> .gitignore
> ```

### Step 2.3 — Write the Database Models
Create `models/farmer.py`:
```python
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class Farmer(Base):
    __tablename__ = "farmers"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    phone           = Column(String(15), unique=True, nullable=False)
    village         = Column(String(100))
    farm_size_acres = Column(Numeric(6, 2))
    dam_preference  = Column(String(20), default="BOTH")
    language        = Column(String(10), default="TAMIL")
    is_active       = Column(Boolean, default=True)
    registered_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

Create `models/dam_reading.py`:
```python
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from models.farmer import Base
from datetime import datetime, timezone

class DamReading(Base):
    __tablename__ = "dam_readings"

    id               = Column(Integer, primary_key=True, index=True)
    dam_name         = Column(String(50), nullable=False)
    reading_date     = Column(Date, nullable=False)
    full_depth_ft    = Column(Numeric(6, 2))
    full_cap_mcft    = Column(Numeric(10, 2))
    level_ft         = Column(Numeric(6, 2))
    storage_mcft     = Column(Numeric(10, 2))
    inflow_cusecs    = Column(Numeric(10, 2))
    outflow_cusecs   = Column(Numeric(10, 2))
    fill_percent     = Column(Numeric(5, 2))
    ttf_hours        = Column(Numeric(8, 1))
    alert_level      = Column(String(20))
    source           = Column(String(20), default="SCRAPER")
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### Step 2.4 — Set Up Alembic (Database Migrations)
```bash
alembic init alembic
```
Open `alembic/env.py` and find the line `target_metadata = None`, replace with:
```python
from models.farmer import Base
from models.dam_reading import DamReading  # noqa: F401
target_metadata = Base.metadata
```

Also update `alembic.ini` — find `sqlalchemy.url` and set:
```ini
sqlalchemy.url = postgresql://damuser:yourpassword123@localhost:5432/damalert
```

Now create and run the migration:
```bash
alembic revision --autogenerate -m "create initial tables"
alembic upgrade head
```
> **What this does:** Creates the actual tables in your PostgreSQL database.

Verify tables were created:
```bash
psql -U damuser -d damalert -c "\dt"
# Should list: farmers, dam_readings
```

---

## 🕷️ Phase 3 — Build the Data Scraper (Day 3–4)

### Step 3.1 — Write the Scraper
Create `scraper/tnagriculture.py`:
```python
import httpx
from bs4 import BeautifulSoup
from datetime import date

DAMS_OF_INTEREST = ["AMARAVATHI", "THIRUMURTHY"]
BASE_URL = "https://tnagriculture.in/ARS/home/reservoir"

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

async def fetch_dam_data(for_date: date = None) -> list[dict]:
    url = f"{BASE_URL}/{for_date}" if for_date else BASE_URL
    print(f"Fetching data from: {url}")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table")

    if not table:
        raise ValueError("Could not find data table on page")

    rows = table.find_all("tr")
    results = []

    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cols:
            continue
        dam_name = cols[0].upper().replace("*", "").strip()
        if any(d in dam_name for d in DAMS_OF_INTEREST):
            results.append({
                "dam_name":        dam_name,
                "full_depth_ft":   safe_float(cols[1]),
                "full_cap_mcft":   safe_float(cols[2]),
                "level_ft":        safe_float(cols[3]),
                "storage_mcft":    safe_float(cols[4]),
                "inflow_cusecs":   safe_float(cols[5]),
                "outflow_cusecs":  safe_float(cols[6]),
            })

    print(f"Found data for: {[r['dam_name'] for r in results]}")
    return results
```

### Step 3.2 — Test the Scraper
Create a quick test file `scraper/test_scraper.py`:
```python
import asyncio
from tnagriculture import fetch_dam_data

async def main():
    data = await fetch_dam_data()
    for dam in data:
        print(f"\n--- {dam['dam_name']} ---")
        print(f"Level    : {dam['level_ft']} ft")
        print(f"Storage  : {dam['storage_mcft']} M.Cft")
        print(f"Inflow   : {dam['inflow_cusecs']} CuSecs")
        print(f"Outflow  : {dam['outflow_cusecs']} CuSecs")

asyncio.run(main())
```

Run it:
```bash
cd backend/scraper
python test_scraper.py
```
You should see the dam data printed in your terminal. ✅

---

## ⚡ Phase 4 — Build the Alert Engine & API (Day 5–8)

### Step 4.1 — Write the Alert Engine
Create `engine/alert_rules.py` with the TTF logic from the tech stack doc.

### Step 4.2 — Write the FastAPI Main App
Create `main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Dam Alert API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "KaLai Dam Alert API is running ✅"}
```

### Step 4.3 — Run the API Server
```bash
cd backend
uvicorn main:app --reload
```
Open your browser: **http://localhost:8000**
You should see: `{"message": "KaLai Dam Alert API is running ✅"}`

Open **http://localhost:8000/docs** — this is the auto-generated API documentation. You can test all your endpoints here!

---

## 📱 Phase 5 — Set Up SMS (Day 9–12)

### Step 5.1 — Create a MSG91 Account
1. Go to **https://msg91.com**
2. Sign up with your phone number and email
3. Verify your account
4. Go to **Dashboard → API** → copy your Auth Key

### Step 5.2 — DLT Registration (Mandatory — Takes 3–5 Days)
TRAI requires all SMS senders in India to register:

1. Go to **https://www.trai.gov.in/dlt** (choose your telecom operator's DLT portal — Airtel, Jio, BSNL, etc.)
2. Register your **entity** (Village Panchayat name)
3. Add your **Sender ID** (e.g., `KLDAMT` — 6 characters)
4. Register each **SMS template** (the exact message text you plan to send)
   - Daily Digest template
   - Caution alert template
   - Critical alert template
   - Water release template
   - On-demand LEVEL reply template
5. Once approved (2–5 days), copy the Template IDs into your `.env` file

> ⚠️ **Without DLT registration, your SMS will be blocked by telecom operators. Do this first before building SMS features.**

### Step 5.3 — Write the SMS Service
Create `services/sms_service.py`:
```python
import httpx
from config import settings

async def send_sms(phone: str, message: str, template_id: str) -> dict:
    """Send one SMS via MSG91."""
    # Remove + from phone if present
    phone = phone.replace("+", "")

    payload = {
        "template_id": template_id,
        "sender":      settings.SMS_SENDER_ID,
        "short_url":   "0",
        "mobiles":     phone,
        "message":     message,
    }
    headers = {
        "authkey":      settings.MSG91_AUTH_KEY,
        "content-type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.msg91.com/api/v5/flow/",
            json=payload,
            headers=headers
        )
    return resp.json()

async def send_test_sms(phone: str) -> dict:
    """Send a test SMS to verify setup."""
    return await send_sms(
        phone=phone,
        message="Test from KaLai Dam Alert. Setup successful!",
        template_id=settings.TEMPLATE_DAILY_DIGEST
    )
```

---

## 🖥️ Phase 6 — Build the Admin Panel (Day 13–18)

### Step 6.1 — Create the React App
```bash
cd dam-alert/admin-panel
npm create vite@latest . -- --template react
npm install
npm install axios react-router-dom
```

### Step 6.2 — Start the Admin Panel Dev Server
```bash
npm run dev
```
Open **http://localhost:5173** — you'll see a default React page. You'll replace this with your admin dashboard.

### Step 6.3 — Build the Main Pages
Create these page files inside `admin-panel/src/pages/`:

| File | Purpose |
|---|---|
| `Dashboard.jsx` | Overview: dam levels, alert status, farmer count |
| `Farmers.jsx` | Add/view/remove farmers |
| `DamReadings.jsx` | View scraped data + manual entry form |
| `AlertHistory.jsx` | All SMS alerts sent |
| `SendAlert.jsx` | Push a custom alert message |

> 💡 **Tip for beginners:** Start with `Farmers.jsx` first — it's the most important page. Farmers need to be in the database before any alerts can be sent.

---

## ☁️ Phase 7 — Deploy to Production (Day 19–25)

### Step 7.1 — Create Accounts You Need

| Service | Purpose | Cost | Link |
|---|---|---|---|
| **Hetzner** | VPS server hosting | ~₹350/mo | hetzner.com |
| **Namecheap / GoDaddy** | Domain name (optional) | ~₹700/yr | namecheap.com |
| **MSG91** | SMS gateway | ₹0.12–0.16/SMS | msg91.com |
| **Sentry** | Error monitoring | Free tier | sentry.io |
| **GitHub** | Store your code | Free | github.com |

### Step 7.2 — Push Code to GitHub
```bash
cd dam-alert
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/dam-alert.git
git push -u origin main
```

### Step 7.3 — Set Up the Server (Hetzner VPS)
After buying a Hetzner server (Ubuntu 22.04):
```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Install Python, Postgres, Redis, Nginx
apt update && apt upgrade -y
apt install python3.11 python3-pip postgresql redis-server nginx -y

# Clone your code
git clone https://github.com/yourusername/dam-alert.git
cd dam-alert/backend
pip install -r requirements.txt

# Set up .env on the server (copy from your Mac)
nano .env   # paste your env variables

# Run migrations
alembic upgrade head

# Start the API
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🧪 How to Test Everything (Checklist)

Run through this checklist before telling anyone to use the system:

| Test | How to Check |
|---|---|
| ✅ Scraper works | Run `python test_scraper.py` — see dam data printed |
| ✅ Database saves data | Check `psql` → `SELECT * FROM dam_readings;` |
| ✅ Alert engine gives correct level | Test with known fill % + inflow values |
| ✅ SMS sends successfully | Send test SMS to your own phone first |
| ✅ Farmer can be registered | Use admin panel to add yourself as a test farmer |
| ✅ LEVEL reply works | Reply LEVEL to a test SMS — get instant data back |
| ✅ STOP/START works | Reply STOP → verify farmer marked inactive in DB |
| ✅ Celery scheduled tasks run | Check Celery logs at 9:00 AM for scrape confirmation |
| ✅ Admin can push manual alert | Use "Send Alert" page in admin panel |

---

## 📚 Learning Resources (If You Get Stuck)

| Topic | Best Free Resource |
|---|---|
| Python basics | **https://docs.python.org/3/tutorial** |
| FastAPI | **https://fastapi.tiangolo.com/tutorial** (best docs ever) |
| SQLAlchemy | **https://docs.sqlalchemy.org/en/20/orm/quickstart.html** |
| React basics | **https://react.dev/learn** |
| PostgreSQL | **https://www.postgresqltutorial.com** |
| Celery | **https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html** |
| Git basics | **https://www.atlassian.com/git/tutorials** |

---

## 🆘 Common Errors & Fixes

| Error | What It Means | Fix |
|---|---|---|
| `ModuleNotFoundError` | Library not installed | Run `pip install <library-name>` |
| `Connection refused (PostgreSQL)` | Database not running | Run `brew services start postgresql@15` |
| `Connection refused (Redis)` | Redis not running | Run `brew services start redis` |
| `(venv)` missing from terminal | Virtual env not active | Run `source venv/bin/activate` |
| `alembic: command not found` | Alembic not installed or venv not active | Activate venv first |
| Website scrape returns empty | tnagriculture.in may have updated HTML | Print `soup.prettify()` and inspect structure |
| SMS not delivered | DLT not approved yet, or wrong Template ID | Check MSG91 dashboard for delivery report |

---

## 📅 Suggested Week-by-Week Timeline

| Week | Focus | Goal |
|---|---|---|
| **Week 1** | Phase 0 + 1 + 2 | Tools installed, database running, tables created |
| **Week 2** | Phase 3 + start 4 | Scraper working, basic FastAPI running |
| **Week 3** | Finish Phase 4 | Full alert engine + all API endpoints working |
| **Week 4** | Phase 5 | DLT approved, SMS sending, inbound replies working |
| **Week 5** | Phase 6 | Admin panel built and connected to API |
| **Week 6** | Phase 7 | Deployed on server, tested end-to-end with real farmers |

---

## 💬 Getting Help

When you're stuck, the best way to get help is to share:
1. **What you were trying to do**
2. **The exact error message** (copy-paste the full red text from terminal)
3. **The code you wrote** (the file and the function)

You can ask here anytime — I'll walk you through it step by step. 🙏

---

*Build Guide v1.0 — KaLai Vivasayam Dam Alert System*
*[Product Doc](file:///Users/praga/.gemini/antigravity/brain/0dbc2770-1a01-4577-ad94-f4758480a7c1/dam_alert_product_doc.md) | [Tech Stack Doc](file:///Users/praga/.gemini/antigravity/brain/0dbc2770-1a01-4577-ad94-f4758480a7c1/tech_stack_doc.md)*
