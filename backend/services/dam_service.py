from sqlalchemy.orm import Session
from models.dam_reading import DamReading
from models.farmer import Farmer
from models.alert_log import AlertLog
from engine.alert_rules import (
    calculate_fill_percent,
    calculate_ttf_hours,
    evaluate_alert_level,
)
from services.sms_service import send_sms, format_daily_sms, format_alert_sms
from config import settings
from datetime import date

async def process_and_save_readings(db: Session, scraped_data: list[dict]):
    """Saves readings to DB and evaluates alerts."""
    saved_records = []
    
    for r in scraped_data:
        dam_name = r["dam_name"]
        storage = r.get("storage_mcft") or 0
        full_cap = r.get("full_cap_mcft") or 0
        inflow = r.get("inflow_cusecs") or 0
        outflow = r.get("outflow_cusecs") or 0
        level = r.get("level_ft") or 0
        full_depth = r.get("full_depth_ft") or 0
        
        fill_pct = calculate_fill_percent(storage, full_cap)
        ttf = calculate_ttf_hours(storage, full_cap, inflow, outflow)
        
        prev = (
            db.query(DamReading)
            .filter(DamReading.dam_name == dam_name)
            .order_by(DamReading.id.desc())
            .first()
        )
        prev_outflow = prev.outflow_cusecs if prev and prev.outflow_cusecs else 0
        
        alert_lvl = evaluate_alert_level(
            fill_pct=fill_pct,
            ttf_hours=ttf,
            inflow_cusecs=inflow,
            prev_outflow=float(prev_outflow),
            curr_outflow=outflow
        )
        
        reading = DamReading(
            dam_name=dam_name,
            reading_date=date.today(),
            full_depth_ft=full_depth,
            full_cap_mcft=full_cap,
            level_ft=level,
            storage_mcft=storage,
            inflow_cusecs=inflow,
            outflow_cusecs=outflow,
            fill_percent=fill_pct,
            ttf_hours=ttf,
            alert_level=alert_lvl.value,
            source="SCRAPER"
        )
        db.add(reading)
        saved_records.append(reading)
    
    db.commit()
    return saved_records

async def broadcast_dam_update(db: Session, dam_name: str, is_morning_digest: bool = True):
    """Sends SMS to registered farmers based on dam preference."""
    latest = (
        db.query(DamReading)
        .filter(DamReading.dam_name == dam_name.upper())
        .order_by(DamReading.id.desc())
        .first()
    )
    if not latest:
        return {"error": f"No readings found for {dam_name}"}
        
    farmers = (
        db.query(Farmer)
        .filter(Farmer.is_active == True)
        .filter(Farmer.dam_preference.in_([dam_name.upper(), "BOTH"]))
        .all()
    )
    
    if is_morning_digest:
        msg = format_daily_sms(
            dam_name=latest.dam_name,
            level_ft=float(latest.level_ft or 0),
            storage_mcft=float(latest.storage_mcft or 0),
            fill_pct=float(latest.fill_percent or 0),
            inflow_cusecs=float(latest.inflow_cusecs or 0),
            outflow_cusecs=float(latest.outflow_cusecs or 0),
            status=latest.alert_level or "NORMAL"
        )
        template_id = settings.TEMPLATE_DAILY_DIGEST
    else:
        msg = format_alert_sms(
            dam_name=latest.dam_name,
            level_ft=float(latest.level_ft or 0),
            fill_pct=float(latest.fill_percent or 0),
            inflow_cusecs=float(latest.inflow_cusecs or 0),
            outflow_cusecs=float(latest.outflow_cusecs or 0),
            ttf_hours=float(latest.ttf_hours) if latest.ttf_hours else None,
            alert_type=latest.alert_level or "NORMAL"
        )
        template_id = settings.TEMPLATE_CAUTION
        
    results = []
    for f in farmers:
        res = await send_sms(f.phone, msg, template_id)
        log = AlertLog(
            farmer_id=f.id,
            dam_name=latest.dam_name,
            alert_level=latest.alert_level,
            message_text=msg,
            sms_status="SENT" if res.get("status") == "success" else "FAILED",
            sms_provider_id=res.get("provider", "UNKNOWN")
        )
        db.add(log)
        results.append({"farmer": f.name, "phone": f.phone, "result": res})
        
    db.commit()
    return {"total_farmers": len(farmers), "broadcast": results}

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
