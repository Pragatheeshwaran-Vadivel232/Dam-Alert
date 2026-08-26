import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import SessionLocal
from services.sms_service import send_sms, format_daily_sms
from services.dam_service import broadcast_dam_update, process_and_save_readings
from scraper.tnagriculture import fetch_dam_data

async def main():
    print("\n🚀 Testing Step 5.3 - Dam Data Fetch & SMS Broadcast...")
    db = SessionLocal()
    
    # 1. Fetch live dam data
    print("1. Fetching latest data from tnagriculture.in...")
    data = await fetch_dam_data()
    
    # 2. Save readings to database
    print("2. Saving readings to PostgreSQL...")
    saved = await process_and_save_readings(db, data)
    for s in saved:
        print(f"   ✓ {s.dam_name}: {s.level_ft} ft | {s.fill_percent}% Full | Alert Level: {s.alert_level}")
        
    # 3. Test sending SMS broadcast to registered farmers
    print("\n3. Testing SMS Broadcast for AMARAVATHI Dam...")
    result = await broadcast_dam_update(db, "AMARAVATHI", is_morning_digest=True)
    print(f"   ✓ Broadcast completed for {result.get('total_farmers')} farmer(s)!")
    
    db.close()
    print("\n🎉 Step 5.3 verification completed successfully!\n")

if __name__ == "__main__":
    asyncio.run(main())
