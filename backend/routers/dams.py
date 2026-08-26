from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services.database import get_db
from models.dam_reading import DamReading
from scraper.tnagriculture import fetch_dam_data
from services.dam_service import process_and_save_readings

router = APIRouter(prefix="/dams", tags=["Dams"])

@router.get("/latest")
def get_latest_readings(db: Session = Depends(get_db)):
    dams = ["AMARAVATHI", "THIRUMURTHY"]
    results = {}
    for dam in dams:
        latest = (
            db.query(DamReading)
            .filter(DamReading.dam_name == dam)
            .order_by(DamReading.id.desc())
            .first()
        )
        results[dam] = latest
    return results

@router.post("/sync")
async def sync_live_data(db: Session = Depends(get_db)):
    """Manually triggers live scrape from tnagriculture.in and saves to DB."""
    data = await fetch_dam_data()
    saved = await process_and_save_readings(db, data)
    return {"message": "Dams synced successfully", "records_updated": len(saved)}
