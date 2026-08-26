import os

# 1. Update backend/services/sms_service.py
sms_path = "backend/services/sms_service.py"
with open(sms_path, "r") as f:
    sms_code = f.read()

if "format_combined_sms" not in sms_code:
    combined_func = """
def format_combined_sms(amaravathi, thirumoorthi) -> str:
    date_str = datetime.now().strftime("%d-%m-%Y")
    return (
        f"💧 KaLai Combined Update 💧\\n"
        f"Date: {date_str}\\n\\n"
        f"🏞 AMARAVATHI:\\n"
        f"Lvl: {float(amaravathi.level_ft or 0)}ft ({float(amaravathi.fill_percent or 0)}%)\\n"
        f"In: {float(amaravathi.inflow_cusecs or 0)} | Out: {float(amaravathi.outflow_cusecs or 0)}\\n\\n"
        f"🏞 THIRUMOORTHI:\\n"
        f"Lvl: {float(thirumoorthi.level_ft or 0)}ft ({float(thirumoorthi.fill_percent or 0)}%)\\n"
        f"In: {float(thirumoorthi.inflow_cusecs or 0)} | Out: {float(thirumoorthi.outflow_cusecs or 0)}\\n\\n"
        f"🌾 Happy Farming!"
    )
"""
    sms_code = sms_code.replace("async def send_sms", combined_func + "\nasync def send_sms")
    with open(sms_path, "w") as f:
        f.write(sms_code)

# 2. Update backend/services/dam_service.py
dam_svc_path = "backend/services/dam_service.py"
with open(dam_svc_path, "r") as f:
    dam_svc = f.read()

if "broadcast_combined_update" not in dam_svc:
    combined_update = """
async def broadcast_combined_update(db: Session):
    am = db.query(DamReading).filter(DamReading.dam_name == 'AMARAVATHI').order_by(DamReading.id.desc()).first()
    tm = db.query(DamReading).filter(DamReading.dam_name == 'THIRUMURTHY').order_by(DamReading.id.desc()).first()
    
    if not am or not tm:
        return {"error": "Missing dam data for one or both dams"}
        
    farmers = db.query(Farmer).filter(Farmer.is_active == True).all()
    
    from services.sms_service import format_combined_sms
    msg = format_combined_sms(am, tm)
    
    results = []
    for f in farmers:
        res = await send_sms(f.phone, msg)
        log = AlertLog(
            farmer_id=f.id,
            dam_name="BOTH",
            alert_level="NORMAL",
            message_text=msg,
            sms_status="SENT" if res.get("status") == "success" else "FAILED",
            sms_provider_id=res.get("provider", "UNKNOWN")
        )
        db.add(log)
        results.append({"farmer": f.name, "phone": f.phone, "result": res})
        
    db.commit()
    return {"total_farmers": len(farmers), "broadcast": results}
"""
    dam_svc += combined_update
    with open(dam_svc_path, "w") as f:
        f.write(dam_svc)

# 3. Update backend/routers/alerts.py
alerts_path = "backend/routers/alerts.py"
with open(alerts_path, "r") as f:
    alerts_code = f.read()

if "/broadcast/combined" not in alerts_code:
    combined_alert = """
@router.post("/broadcast/combined")
async def trigger_combined_broadcast(db: Session = Depends(get_db)):
    from services.dam_service import broadcast_combined_update
    result = await broadcast_combined_update(db)
    return result
"""
    alerts_code += combined_alert
    with open(alerts_path, "w") as f:
        f.write(alerts_code)

# 4. Update admin-panel/src/App.jsx
app_path = "admin-panel/src/App.jsx"
with open(app_path, "r") as f:
    app_code = f.read()

if "triggerCombinedBroadcast" not in app_code:
    func_insert = """
  const triggerCombinedBroadcast = async () => {
    try {
      const response = await fetch(`http://localhost:8000/alerts/broadcast/combined`, { method: 'POST' });
      const data = await response.json();
      alert(`Sent combined SMS to ${data.total_farmers || 0} farmers!`);
      fetchLogs();
    } catch (error) {
      console.error("Error triggering combined broadcast:", error);
    }
  };
"""
    app_code = app_code.replace("const triggerBroadcast = async (damName) => {", func_insert + "\n  const triggerBroadcast = async (damName) => {")

    btn_insert = """
            <button onClick={triggerCombinedBroadcast} className="btn btn-primary" style={{ marginBottom: "1rem", width: "100%", padding: "1rem", fontSize: "1.1rem", background: "linear-gradient(135deg, #0984e3, #6c5ce7)" }}>
              📢 Send Combined Daily SMS (Both Dams in One Message)
            </button>
            
            <div className="dam-cards">
"""
    app_code = app_code.replace('<div className="dam-cards">', btn_insert)
    
    with open(app_path, "w") as f:
        f.write(app_code)

print("SUCCESS")
