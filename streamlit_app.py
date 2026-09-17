import streamlit as st
import asyncio
import sys
import os
from datetime import datetime

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))

from scraper.tnagriculture import fetch_dam_data
from services.database import SessionLocal
from models.farmer import Farmer
from models.dam_reading import DamReading
from services.sms_service import send_sms, format_daily_sms, format_combined_sms
from services.dam_service import process_and_save_readings

# Page config
st.set_page_config(page_title="KaLai Vivasayam", page_icon="💧", layout="wide")

st.markdown("""
<style>
.stProgress > div > div { border-radius: 99px; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("## 💧 KaLai Vivasayam – Dam Alert Dashboard")
st.markdown("Real-time water level monitoring for Amaravathi & Thirumoorthi Dams")
st.divider()

def alert_emoji(level):
    return {"NORMAL":"🟢","CAUTION":"🟡","HIGH":"🔴","CRITICAL":"🚨","LOW":"🔵","RELEASE":"🟣"}.get(level,"🟢")

tab1, tab2, tab3, tab4 = st.tabs(["🌊 Dam Dashboard", "👨‍🌾 Farmers", "📢 Broadcast SMS", "🤖 Smart Advisory"])

# ─── TAB 1: DAM DASHBOARD ────────────────────────────────────────────────────
with tab1:
    col_btn, col_time = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Sync Live Data", type="primary", use_container_width=True):
            with st.spinner("Fetching live data from tnagriculture.in ..."):
                try:
                    raw = asyncio.run(fetch_dam_data())
                    db = SessionLocal()
                    asyncio.run(process_and_save_readings(db, raw))
                    db.close()
                    st.success("✅ Data synced successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Sync failed: {e}")
    with col_time:
        st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

    db = SessionLocal()
    dams = {}
    for name in ["AMARAVATHI", "THIRUMURTHY"]:
        dams[name] = db.query(DamReading).filter(DamReading.dam_name == name).order_by(DamReading.id.desc()).first()
    db.close()

    if not any(dams.values()):
        st.warning("⚠️ No data yet. Click **Sync Live Data** above to fetch live dam data!")
    else:
        col1, col2 = st.columns(2)
        for i, (dam_name, d) in enumerate(dams.items()):
            col = col1 if i == 0 else col2
            with col:
                if d:
                    fill = float(d.fill_percent or 0)
                    level = d.alert_level or "NORMAL"
                    st.markdown(f"### {alert_emoji(level)} {dam_name} DAM &nbsp; `{level}`")
                    st.caption(f"Capacity: {d.full_depth_ft} ft | {d.full_cap_mcft} M.Cft")
                    st.progress(min(fill / 100, 1.0), text=f"💧 {fill:.1f}% Full")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Water Level", f"{d.level_ft} ft")
                    m2.metric("Storage", f"{d.storage_mcft} M.Cft")
                    m3.metric("🔵 Inflow", f"{d.inflow_cusecs or 0}")
                    m4.metric("🟠 Outflow", f"{d.outflow_cusecs or 0}")
                    if d.ttf_hours:
                        st.info(f"⏱️ Est. Time to Full: ~{d.ttf_hours} hours")
                    st.divider()
                else:
                    st.warning(f"No data for {dam_name}. Please sync.")

# ─── TAB 2: FARMERS ──────────────────────────────────────────────────────────
with tab2:
    st.subheader("👨‍🌾 Registered Village Farmers")
    db = SessionLocal()
    farmers = db.query(Farmer).order_by(Farmer.id).all()
    db.close()

    if not farmers:
        st.info("No farmers registered yet. Add one below!")
    else:
        import pandas as pd
        df = pd.DataFrame([{
            "ID": f.id, "Name": f.name, "Phone": f.phone,
            "Village": f.village, "Farm (acres)": float(f.farm_size_acres or 0),
            "Dam": f.dam_preference, "Status": "✅ Active" if f.is_active else "❌ Inactive"
        } for f in farmers])
        st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("➕ Register New Farmer")
    with st.form("farmer_form"):
        c1, c2 = st.columns(2)
        f_name  = c1.text_input("Full Name *")
        f_phone = c2.text_input("Mobile Number *")
        f_vil   = c1.text_input("Village")
        f_acre  = c2.number_input("Farm Size (acres)", min_value=0.0, step=0.5)
        f_dam   = st.selectbox("Dam Preference", ["BOTH", "AMARAVATHI", "THIRUMURTHY"])
        if st.form_submit_button("Register Farmer", type="primary"):
            if not f_name or not f_phone:
                st.error("Name and Phone are required!")
            else:
                db = SessionLocal()
                db.add(Farmer(name=f_name, phone=f_phone, village=f_vil, farm_size_acres=f_acre, dam_preference=f_dam, is_active=True))
                db.commit()
                db.close()
                st.success(f"✅ {f_name} registered successfully!")
                st.rerun()

# ─── TAB 3: BROADCAST SMS ─────────────────────────────────────────────────────
with tab3:
    st.subheader("📢 Broadcast SMS to Farmers")
    db = SessionLocal()
    active_count = db.query(Farmer).filter(Farmer.is_active == True).count()
    db.close()
    st.info(f"📱 {active_count} active farmers will receive this SMS")

    sms_type = st.radio("SMS Type", ["Combined (Both Dams)", "Single Dam"], horizontal=True)

    if sms_type == "Combined (Both Dams)":
        if st.button("🚀 Send Combined SMS to ALL Farmers", type="primary", use_container_width=True):
            with st.spinner("Sending..."):
                db = SessionLocal()
                am = db.query(DamReading).filter(DamReading.dam_name == "AMARAVATHI").order_by(DamReading.id.desc()).first()
                tm = db.query(DamReading).filter(DamReading.dam_name == "THIRUMURTHY").order_by(DamReading.id.desc()).first()
                farmers_list = db.query(Farmer).filter(Farmer.is_active == True).all()
                if not am or not tm:
                    st.error("❌ Sync dam data first!")
                else:
                    msg = format_combined_sms(am, tm)
                    st.code(msg, language=None)
                    import pandas as pd
                    results = [{"Farmer": f.name, "Phone": f.phone, "Status": asyncio.run(send_sms(f.phone, msg)).get("status")} for f in farmers_list]
                    db.close()
                    st.dataframe(pd.DataFrame(results), use_container_width=True)
                    st.success(f"✅ Sent to {len(results)} farmers!")
    else:
        dam_sel = st.selectbox("Select Dam", ["AMARAVATHI", "THIRUMURTHY"])
        custom  = st.text_area("Custom Message (optional)")
        if st.button(f"📢 Send {dam_sel} Update", type="primary", use_container_width=True):
            with st.spinner("Sending..."):
                db = SessionLocal()
                latest = db.query(DamReading).filter(DamReading.dam_name == dam_sel).order_by(DamReading.id.desc()).first()
                farmers_list = db.query(Farmer).filter(Farmer.is_active == True).filter(Farmer.dam_preference.in_([dam_sel, "BOTH"])).all()
                if not latest:
                    st.error("❌ Sync dam data first!")
                else:
                    msg = custom.strip() or format_daily_sms(latest.dam_name, float(latest.level_ft or 0), float(latest.storage_mcft or 0), float(latest.fill_percent or 0), float(latest.inflow_cusecs or 0), float(latest.outflow_cusecs or 0), latest.alert_level or "NORMAL")
                    st.code(msg, language=None)
                    import pandas as pd
                    results = [{"Farmer": f.name, "Phone": f.phone, "Status": asyncio.run(send_sms(f.phone, msg)).get("status")} for f in farmers_list]
                    db.close()
                    st.dataframe(pd.DataFrame(results), use_container_width=True)
                    st.success(f"✅ Sent to {len(results)} farmers!")

# ─── TAB 4: SMART ADVISORY ────────────────────────────────────────────────────
with tab4:
    st.subheader("🤖 AI Smart Advisory System")
    db = SessionLocal()
    am = db.query(DamReading).filter(DamReading.dam_name == "AMARAVATHI").order_by(DamReading.id.desc()).first()
    db.close()

    if not am:
        st.warning("⚠️ Sync dam data first to generate advisories.")
    else:
        fill   = float(am.fill_percent or 0)
        inflow = float(am.inflow_cusecs or 0)
        ttf    = float(am.ttf_hours) if am.ttf_hours else None
        advisories = []
        if fill > 75:
            advisories.append(("🌾", "Safe to Sow – Water Security", f"💧 KaLai Advisory: Amaravathi Dam is at {fill:.0f}% capacity. Canal water is secured. Safe to sow water-intensive crops like Paddy. 🌾"))
        if inflow > 3000 and fill < 90:
            advisories.append(("⚠️", "Catchment Rain – Flash Flood Risk", f"⚠️ KaLai Alert: Massive inflow ({inflow:.0f} CuSecs) detected. Water levels rising fast. Avoid crossing rivers and secure livestock."))
        if fill < 20 and inflow < 100:
            advisories.append(("🏜️", "Drought / Scarcity Warning", f"🏜️ KaLai Advisory: Dam storage critically low ({fill:.0f}%). Expect water rationing. Switch to drip irrigation or short-duration crops."))
        if ttf and ttf < 72:
            advisories.append(("🌊", "Dam Filling Rapidly", f"🌊 KaLai Update: Dam will reach 100% in ~{ttf:.0f} hours. Clear your drainage canals now!"))

        if not advisories:
            st.success("✅ All conditions normal. No special advisory at this time.")
        else:
            for icon, title, msg in advisories:
                with st.expander(f"{icon} {title}", expanded=True):
                    st.write(msg)
                    if st.button(f"📲 Send this Advisory via SMS", key=title):
                        with st.spinner("Sending..."):
                            db = SessionLocal()
                            farmers_list = db.query(Farmer).filter(Farmer.is_active == True).all()
                            import pandas as pd
                            results = [{"Farmer": f.name, "Status": asyncio.run(send_sms(f.phone, msg)).get("status")} for f in farmers_list]
                            db.close()
                            st.dataframe(pd.DataFrame(results), use_container_width=True)
                            st.success(f"✅ Advisory sent to {len(results)} farmers!")
