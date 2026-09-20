import streamlit as st
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import os

st.set_page_config(page_title="KaLai Vivasayam", page_icon="💧", layout="wide")
st.markdown("## 💧 KaLai Vivasayam – Dam Alert Dashboard")
st.markdown("Real-time monitoring for **Amaravathi** & **Thirumoorthi** Dams")
st.divider()

DAMS = ["AMARAVATHI", "THIRUMURTHY"]
URL  = "https://tnagriculture.in/ARS/home/reservoir"

def safe_float(val):
    try: return float(val)
    except: return 0.0

def fetch_dams():
    r = httpx.get(URL, timeout=30, follow_redirects=True)
    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table")
    if not table:
        return {}, "No table found on government website"
    results = {}
    for row in table.find_all("tr"):
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cols: continue
        name = cols[0].upper().replace("*","").strip()
        if not any(d in name for d in DAMS): continue
        key      = "AMARAVATHI" if "AMARAVATHI" in name else "THIRUMURTHY"
        full_cap = safe_float(cols[2])
        storage  = safe_float(cols[4])
        inflow   = safe_float(cols[5])
        outflow  = safe_float(cols[6])
        fill     = round((storage/full_cap)*100,1) if full_cap else 0.0
        net      = inflow - outflow
        ttf      = round((full_cap-storage)/(net*0.00028347),1) if net>0 else None
        if fill>95 or (ttf and ttf<6):    alert="🚨 CRITICAL"
        elif fill>85 or (ttf and ttf<24): alert="🔴 HIGH"
        elif fill>70 or (ttf and ttf<48): alert="🟡 CAUTION"
        elif fill<20 and inflow<50:        alert="🔵 LOW"
        else:                             alert="🟢 NORMAL"
        results[key] = {"name":name,"full_depth":safe_float(cols[1]),"full_cap":full_cap,
                        "level":safe_float(cols[3]),"storage":storage,"inflow":inflow,
                        "outflow":outflow,"fill":fill,"ttf":ttf,"alert":alert}
    return results, None

def send_sms(phone, msg):
    key = st.secrets.get("FAST2SMS_API_KEY","") or os.getenv("FAST2SMS_API_KEY","")
    if not key: return "❌ No API key"
    try:
        r = httpx.post("https://www.fast2sms.com/dev/bulkV2",
            json={"route":"q","message":msg,"language":"unicode","flash":0,"numbers":phone.replace("+91","").strip()},
            headers={"authorization":key}, timeout=15)
        d = r.json()
        return "✅ SMS Sent!" if d.get("return") else f"❌ {d}"
    except Exception as e:
        return f"❌ Error: {e}"

tab1, tab2, tab3 = st.tabs(["🌊 Dam Dashboard","📢 Send SMS","🤖 Smart Advisory"])

# ── TAB 1 ──────────────────────────────────────────────────────────────
with tab1:
    if st.button("🔄 Fetch Live Data", type="primary"):
        with st.spinner("Fetching from tnagriculture.in ..."):
            try:
                data, err = fetch_dams()
                if err: st.error(f"❌ {err}")
                else:
                    st.session_state["dams"] = data
                    st.success("✅ Data loaded!")
            except Exception as e:
                st.error(f"❌ {e}")

    dams = st.session_state.get("dams")
    if not dams:
        st.info("👆 Click **Fetch Live Data** to load real-time dam information.")
    else:
        c1, c2 = st.columns(2)
        for i,(key,d) in enumerate(dams.items()):
            with (c1 if i==0 else c2):
                st.markdown(f"### {d['alert']}  {key} DAM")
                st.caption(f"Capacity: {d['full_depth']} ft | {d['full_cap']} M.Cft")
                st.progress(min(d["fill"]/100,1.0), text=f"💧 {d['fill']}% Full")
                m1,m2,m3,m4 = st.columns(4)
                m1.metric("Level",    f"{d['level']} ft")
                m2.metric("Storage",  f"{d['storage']} M.Cft")
                m3.metric("🔵 Inflow",  f"{d['inflow']}")
                m4.metric("🟠 Outflow", f"{d['outflow']}")
                if d["ttf"]: st.info(f"⏱️ Est. Time to Full: ~{d['ttf']} hours")
                st.divider()

# ── TAB 2 ──────────────────────────────────────────────────────────────
with tab2:
    st.subheader("📢 Send SMS Alert")
    dams = st.session_state.get("dams")
    if not dams:
        st.warning("⚠️ Fetch live data first!")
    else:
        phone   = st.text_input("Farmer Phone Number (10 digits)")
        dam_sel = st.selectbox("Select Dam", list(dams.keys()))
        d       = dams[dam_sel]
        msg     = st.text_area("Message", value=(
            f"💧 KaLai Vivasayam Update 💧\n"
            f"Date: {datetime.now().strftime('%d-%m-%Y')}\n"
            f"Dam: {dam_sel}\nLevel: {d['level']} ft ({d['fill']}% Full)\n"
            f"Inflow: {d['inflow']} | Outflow: {d['outflow']} CuSecs\n"
            f"Status: {d['alert']}\n🌾 Happy Farming!"
        ), height=180)
        if st.button("📱 Send SMS", type="primary"):
            if len(phone) < 10: st.error("Enter valid 10-digit number!")
            else:
                with st.spinner("Sending..."): st.write(send_sms(phone, msg))

# ── TAB 3 ──────────────────────────────────────────────────────────────
with tab3:
    st.subheader("🤖 AI Smart Advisory")
    dams = st.session_state.get("dams")
    if not dams:
        st.warning("⚠️ Fetch live data first!")
    else:
        d      = dams.get("AMARAVATHI",{})
        fill   = d.get("fill",0)
        inflow = d.get("inflow",0)
        ttf    = d.get("ttf")
        found  = False
        if fill>75:
            st.success(f"🌾 **Safe to Sow:** Dam is {fill}% full. Canal water secured. Safe to sow water-intensive crops like Paddy! 🌾")
            found = True
        if inflow>3000 and fill<90:
            st.warning(f"⚠️ **Flash Flood Risk:** Massive inflow ({inflow} CuSecs). Avoid river crossings. Secure livestock!")
            found = True
        if fill<20 and inflow<100:
            st.error(f"🏜️ **Drought Warning:** Storage critically low ({fill}%). Switch to drip irrigation or short-duration crops.")
            found = True
        if ttf and ttf<72:
            st.info(f"🌊 **Filling Fast:** Dam will reach 100% in ~{ttf} hours. Clear drainage canals now!")
            found = True
        if not found:
            st.success("✅ All conditions normal. No special advisory at this time.")
