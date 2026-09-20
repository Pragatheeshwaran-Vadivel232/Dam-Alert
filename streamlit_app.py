import streamlit as st
import httpx
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import os

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="KaLai Vivasayam", page_icon="💧", layout="wide")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 💧 KaLai Vivasayam – Dam Alert Dashboard")
st.markdown("Real-time water level monitoring for **Amaravathi** & **Thirumoorthi** Dams")
st.divider()

# ── Scraper (Standalone — no backend import needed) ───────────────────────────
DAMS_OF_INTEREST = ["AMARAVATHI", "THIRUMURTHY"]
BASE_URL = "https://tnagriculture.in/ARS/home/reservoir"

def safe_float(val):
    try:
        return float(val)
    except:
        return 0.0

def fetch_dam_data():
    try:
        r = httpx.get(BASE_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table")
        if not table:
            return None, "Could not find data table on government website."
        rows = table.find_all("tr")
        results = {}
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cols:
                continue
            dam_name = cols[0].upper().replace("*", "").strip()
            if any(d in dam_name for d in DAMS_OF_INTEREST):
                full_cap = safe_float(cols[2])
                storage  = safe_float(cols[4])
                inflow   = safe_float(cols[5])
                outflow  = safe_float(cols[6])
                fill_pct = round((storage / full_cap) * 100, 1) if full_cap else 0.0
                net      = inflow - outflow
                ttf      = round((full_cap - storage) / (net * 0.00028347), 1) if net > 0 else None

                if fill_pct > 95 or (ttf and ttf < 6):   alert = "🚨 CRITICAL"
                elif fill_pct > 85 or (ttf and ttf < 24): alert = "🔴 HIGH"
                elif fill_pct > 70 or (ttf and ttf < 48): alert = "🟡 CAUTION"
                elif fill_pct < 20 and inflow < 50:        alert = "🔵 LOW"
                else:                                      alert = "🟢 NORMAL"

                key = "AMARAVATHI" if "AMARAVATHI" in dam_name else "THIRUMURTHY"
                results[key] = {
                    "dam_name": dam_name,
                    "full_depth_ft": safe_float(cols[1]),
                    "full_cap_mcft": full_cap,
                    "level_ft": safe_float(cols[3]),
                    "storage_mcft": storage,
                    "inflow_cusecs": inflow,
                    "outflow_cusecs": outflow,
                    "fill_percent": fill_pct,
                    "ttf_hours": ttf,
                    "alert": alert,
                }
        return results, None
    except Exception as e:
        return None, str(e)

# ── SMS Sender ────────────────────────────────────────────────────────────────
def send_sms_fast2sms(phone, message):
    api_key = st.secrets.get("FAST2SMS_API_KEY", os.getenv("FAST2SMS_API_KEY", ""))
    if not api_key:
        return "❌ No API key found"
    try:
        r = httpx.post(
            "https://www.fast2sms.com/dev/bulkV2",
            json={"route":"q","message":message,"language":"unicode","flash":0,"numbers":phone.replace("+91","")},
            headers={"authorization": api_key},
            timeout=15
        )
        data = r.json()
        return "✅ Sent" if data.get("return") else f"❌ {data}"
    except Exception as e:
        return f"❌ Error: {e}"

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🌊 Dam Dashboard", "📢 Send SMS Alert", "🤖 Smart Advisory"])

# ═══════════════════════════════════════════════════════
# TAB 1: DAM DASHBOARD
# ═══════════════════════════════════════════════════════
with tab1:
    col_btn, col_time = st.columns([1, 3])
    with col_btn:
        fetch_btn = st.button("🔄 Fetch Live Data", type="primary", use_container_width=True)
    with col_time:
        st.caption(f"Updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

    if "dams" not in st.session_state:
        st.session_state.dams = None

    if fetch_btn:
        with st.spinner("Fetching live data from tnagriculture.in ..."):
            data, err = fetch_dam_data()
            if err:
                st.error(f"❌ Failed: {err}")
            else:
                st.session_state.dams = data
                st.success("✅ Live data fetched successfully!")

    dams = st.session_state.dams
    if not dams:
        st.info("👆 Click **Fetch Live Data** to load real-time dam information from the government website.")
    else:
        col1, col2 = st.columns(2)
        for i, (key, d) in enumerate(dams.items()):
            col = col1 if i == 0 else col2
            with col:
                fill = d["fill_percent"]
                st.markdown(f"### {d['alert']} &nbsp; {key} DAM")
                st.caption(f"Capacity: {d['full_depth_ft']} ft | {d['full_cap_mcft']} M.Cft")
                st.progress(min(fill / 100, 1.0), text=f"💧 {fill:.1f}% Full")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Level", f"{d['level_ft']} ft")
                m2.metric("Storage", f"{d['storage_mcft']} M.Cft")
                m3.metric("🔵 Inflow", f"{d['inflow_cusecs']}")
                m4.metric("🟠 Outflow", f"{d['outflow_cusecs']}")
                if d["ttf_hours"]:
                    st.info(f"⏱️ Est. Time to Full: ~{d['ttf_hours']} hours")
                st.divider()

# ═══════════════════════════════════════════════════════
# TAB 2: SEND SMS
# ═══════════════════════════════════════════════════════
with tab2:
    st.subheader("📢 Send SMS Alert")
    dams = st.session_state.get("dams")
    if not dams:
        st.warning("⚠️ Fetch live data first from the Dashboard tab!")
    else:
        phone = st.text_input("Enter Farmer Phone Number (10 digits)", placeholder="9876543210")
        dam_sel = st.selectbox("Select Dam", list(dams.keys()))
        d = dams[dam_sel]
        date_str = datetime.now().strftime("%d-%m-%Y")
        auto_msg = (
            f"💧 KaLai Vivasayam Update 💧\n"
            f"Date: {date_str}\n"
            f"Dam: {dam_sel}\n"
            f"Level: {d['level_ft']} ft ({d['fill_percent']}% Full)\n"
            f"Inflow: {d['inflow_cusecs']} | Outflow: {d['outflow_cusecs']} CuSecs\n"
            f"Status: {d['alert']}\n"
            f"🌾 Happy Farming!"
        )
        msg = st.text_area("Message", value=auto_msg, height=200)
        if st.button("📱 Send SMS", type="primary"):
            if not phone or len(phone) < 10:
                st.error("Enter a valid 10-digit phone number!")
            else:
                with st.spinner("Sending..."):
                    result = send_sms_fast2sms(phone, msg)
                    st.write(result)

# ═══════════════════════════════════════════════════════
# TAB 3: SMART ADVISORY
# ═══════════════════════════════════════════════════════
with tab3:
    st.subheader("🤖 AI Smart Advisory System")
    dams = st.session_state.get("dams")
    if not dams:
        st.warning("⚠️ Fetch live data first from the Dashboard tab!")
    else:
        am = dams.get("AMARAVATHI", {})
        fill   = am.get("fill_percent", 0)
        inflow = am.get("inflow_cusecs", 0)
        ttf    = am.get("ttf_hours")
        advisories = []

        if fill > 75:
            advisories.append(("🌾", "Safe to Sow – Water Security", "success",
                f"💧 KaLai Advisory: Amaravathi Dam is at {fill:.0f}% capacity. Canal water is secured for this season. Safe to begin sowing water-intensive crops like Paddy. 🌾 Happy Farming!"))
        if inflow > 3000 and fill < 90:
            advisories.append(("⚠️", "Catchment Rain – Flash Flood Risk", "warning",
                f"⚠️ KaLai Alert: Massive inflow ({inflow:.0f} CuSecs) detected. Water levels rising fast. Avoid crossing connected rivers and secure livestock immediately!"))
        if fill < 20 and inflow < 100:
            advisories.append(("🏜️", "Drought / Scarcity Warning", "error",
                f"🏜️ KaLai Advisory: Dam storage critically low ({fill:.0f}%). Expect strict water rationing soon. Switch to drip irrigation or short-duration crops (Millets/Maize) this month."))
        if ttf and ttf < 72:
            advisories.append(("🌊", "Dam Filling Rapidly", "info",
                f"🌊 KaLai Update: At the current inflow rate, Amaravathi Dam will reach 100% in approximately {ttf:.0f} hours. Clear your drainage canals now!"))

        if not advisories:
            st.success("✅ All dam conditions are normal. No special advisory needed right now.")
        else:
            for icon, title, kind, msg in advisories:
                with st.expander(f"{icon} {title}", expanded=True):
                    getattr(st, kind)(msg)
