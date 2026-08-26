from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.database import get_db
from models.alert_log import AlertLog
from models.farmer import Farmer
from services.dam_service import broadcast_dam_update
from services.sms_service import send_sms
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/alerts", tags=["Alerts"])

class CustomBroadcastRequest(BaseModel):
    dam_name: str
    message_text: str

@router.get("/logs")
def get_alert_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = (
        db.query(
            AlertLog.id,
            AlertLog.dam_name,
            AlertLog.alert_level,
            AlertLog.message_text,
            AlertLog.sms_status,
            AlertLog.sms_provider_id,
            AlertLog.sent_at,
            Farmer.name.label("farmer_name"),
            Farmer.phone.label("farmer_phone"),
            Farmer.village.label("farmer_village")
        )
        .outerjoin(Farmer, AlertLog.farmer_id == Farmer.id)
        .order_by(AlertLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "dam_name": l.dam_name,
            "alert_level": l.alert_level,
            "message_text": l.message_text,
            "sms_status": l.sms_status,
            "sms_provider_id": l.sms_provider_id,
            "sent_at": l.sent_at.isoformat() if l.sent_at else None,
            "farmer_name": l.farmer_name or "N/A",
            "farmer_phone": l.farmer_phone or "N/A",
            "farmer_village": l.farmer_village or "N/A"
        }
        for l in logs
    ]

@router.post("/broadcast/dam/{dam_name}")
async def trigger_dam_broadcast(dam_name: str, is_morning_digest: bool = True, db: Session = Depends(get_db)):
    result = await broadcast_dam_update(db, dam_name, is_morning_digest=is_morning_digest)
    return result

@router.post("/broadcast/custom")
async def send_custom_broadcast(req: CustomBroadcastRequest, db: Session = Depends(get_db)):
    query = db.query(Farmer).filter(Farmer.is_active == True)
    if req.dam_name != "BOTH":
        query = query.filter(Farmer.dam_preference.in_([req.dam_name, "BOTH"]))
    
    farmers = query.all()
    if not farmers:
        raise HTTPException(status_code=400, detail="No active farmers found for this filter")
        
    dispatches = []
    for f in farmers:
        res = await send_sms(f.phone, req.message_text)
        log = AlertLog(
            farmer_id=f.id,
            dam_name=req.dam_name,
            alert_level="CUSTOM",
            message_text=req.message_text,
            sms_status="SENT" if res.get("status") == "success" else "FAILED",
            sms_provider_id=res.get("provider", "UNKNOWN")
        )
        db.add(log)
        dispatches.append({"farmer": f.name, "phone": f.phone, "result": res})
        
    db.commit()
    return {"total_sent": len(farmers), "broadcast": dispatches}

@router.post("/broadcast/combined")
async def trigger_combined_broadcast(db: Session = Depends(get_db)):
    from services.dam_service import broadcast_combined_update
    result = await broadcast_combined_update(db)
    return result
