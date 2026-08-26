from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.database import get_db
from models.farmer import Farmer
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/farmers", tags=["Farmers"])

# What data we need to register a farmer
class FarmerCreate(BaseModel):
    name: str
    phone: str
    village: Optional[str] = None
    farm_size_acres: Optional[float] = None
    dam_preference: Optional[str] = "BOTH"
    language: Optional[str] = "TAMIL"

# Register a new farmer
@router.post("/register")
def register_farmer(farmer: FarmerCreate, db: Session = Depends(get_db)):
    # Check if phone already registered
    existing = db.query(Farmer).filter(
        Farmer.phone == farmer.phone
    ).first()
    if existing:
        raise HTTPException(status_code=400,
                          detail="Phone number already registered")

    new_farmer = Farmer(**farmer.model_dump())
    db.add(new_farmer)
    db.commit()
    db.refresh(new_farmer)
    return {"message": "Farmer registered successfully!",
            "farmer_id": new_farmer.id}

# Get all farmers
@router.get("/")
def get_all_farmers(db: Session = Depends(get_db)):
    farmers = db.query(Farmer).all()
    return farmers

# Deactivate a farmer (STOP)
@router.put("/{farmer_id}/deactivate")
def deactivate_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    farmer.is_active = False
    db.commit()
    return {"message": "Farmer deactivated"}
# Activate a farmer (START)
@router.put("/{farmer_id}/activate")
def activate_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    farmer.is_active = True
    db.commit()
    return {"message": "Farmer activated"}

# Delete a farmer
@router.delete("/{farmer_id}")
def delete_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    db.delete(farmer)
    db.commit()
    return {"message": "Farmer deleted successfully"}
