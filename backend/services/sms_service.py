import httpx
import logging
from config import settings
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")

logger = logging.getLogger(__name__)

def format_daily_sms(dam_name: str, level_ft: float, storage_mcft: float, 
                     fill_pct: float, inflow_cusecs: float, outflow_cusecs: float, 
                     status: str) -> str:
    date_str = datetime.now().strftime("%d-%m-%Y")
    return (
        f"💧 KaLai Vivasayam Update 💧\n"
        f"Date: {date_str}\n"
        f"Dam: {dam_name.upper()}\n"
        f"Level: {level_ft} ft ({fill_pct}% Full)\n"
        f"Storage: {storage_mcft} M.Cft\n"
        f"Inflow: {inflow_cusecs} CuSecs\n"
        f"Outflow: {outflow_cusecs} CuSecs\n"
        f"Status: {status}\n"
        f"🌾 Happy Farming!"
    )

def format_alert_sms(dam_name: str, level_ft: float, fill_pct: float, 
                     inflow_cusecs: float, outflow_cusecs: float, 
                     ttf_hours: float | None, alert_type: str) -> str:
    if alert_type == "RELEASE":
        return (
            f"🌊 WATER RELEASE ALERT 🌊\n"
            f"Dam: {dam_name.upper()}\n"
            f"Outflow Started: {outflow_cusecs} CuSecs\n"
            f"Canal water will reach your area soon. Please prepare your fields!\n"
            f"- KaLai Alert System"
        )
    elif alert_type == "CRITICAL":
        ttf_str = f"approx {ttf_hours} hours" if ttf_hours else "very soon"
        return (
            f"🚨 FLOOD WARNING 🚨\n"
            f"{dam_name.upper()} DAM is {fill_pct}% FULL!\n"
            f"Level: {level_ft} ft\n"
            f"Inflow is dangerously high ({inflow_cusecs} CuSecs).\n"
            f"Dam may fill in {ttf_str}. Protect your crops NOW.\n"
            f"- KaLai Alert System"
        )
    elif alert_type in ["HIGH", "CAUTION"]:
        ttf_str = f"in {ttf_hours} hrs" if ttf_hours else "N/A"
        return (
            f"⚠️ CAUTION LEVEL ⚠️\n"
            f"{dam_name.upper()} DAM is filling up ({fill_pct}%).\n"
            f"Level: {level_ft} ft\n"
            f"Inflow: {inflow_cusecs} CuSecs\n"
            f"Please monitor your canal.\n"
            f"- KaLai Alert System"
        )
    return format_daily_sms(dam_name, level_ft, 0, fill_pct, inflow_cusecs, outflow_cusecs, alert_type)


def format_combined_sms(amaravathi, thirumoorthi) -> str:
    date_str = datetime.now().strftime("%d-%m-%Y")
    return (
        f"💧 KaLai Combined Update 💧\n"
        f"Date: {date_str}\n\n"
        f"🏞 AMARAVATHI:\n"
        f"Lvl: {float(amaravathi.level_ft or 0)}ft ({float(amaravathi.fill_percent or 0)}%)\n"
        f"In: {float(amaravathi.inflow_cusecs or 0)} | Out: {float(amaravathi.outflow_cusecs or 0)}\n\n"
        f"🏞 THIRUMOORTHI:\n"
        f"Lvl: {float(thirumoorthi.level_ft or 0)}ft ({float(thirumoorthi.fill_percent or 0)}%)\n"
        f"In: {float(thirumoorthi.inflow_cusecs or 0)} | Out: {float(thirumoorthi.outflow_cusecs or 0)}\n\n"
        f"🌾 Happy Farming!"
    )

async def send_sms(phone: str, message: str, template_id: str = "") -> dict:
    clean_phone = phone.replace("+", "").replace("91", "", 1).strip()
    
    if FAST2SMS_API_KEY and FAST2SMS_API_KEY != "fill_this_later":
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "q",
            "message": message,
            "language": "unicode", # Allows emojis and Tamil text!
            "flash": 0,
            "numbers": clean_phone
        }
        headers = {
            "authorization": FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                data = response.json()
                logger.info(f"Fast2SMS dispatch to {clean_phone}: {data}")
                return {"status": "success", "provider": "FAST2SMS", "details": data}
        except Exception as e:
            logger.error(f"Error calling Fast2SMS API: {e}")
            return {"status": "error", "provider": "FAST2SMS", "error": str(e)}
    else:
        print("\n" + "=" * 50)
        print(f"📱 [SIMULATED SMS DISPATCH]")
        print(f"To Phone   : +91{clean_phone}")
        print("-" * 50)
        print(message)
        print("=" * 50 + "\n")
        return {"status": "success", "provider": "SIMULATED", "message": "SMS simulated."}
