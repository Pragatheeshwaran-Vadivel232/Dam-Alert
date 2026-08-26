import httpx
import asyncio
from config import settings

async def send_live_test_otp(phone: str, template_id: str):
    # Remove + from phone if present
    clean_phone = phone.replace("+", "").strip()
    
    # MSG91 OTP API Endpoint
    url = "https://control.msg91.com/api/v5/otp/send"
    
    params = {
        "template_id": template_id,
        "mobile": clean_phone,
        "authkey": settings.MSG91_AUTH_KEY,
        "otp": "123456" # Custom test OTP code to send
    }
    
    print(f"📡 Sending real live test to +{clean_phone} using template: {template_id}...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params)
        print("Response Code:", response.status_code)
        print("Response Body:", response.json())

# Replace with your actual phone number and the Template ID from Step 1
YOUR_PHONE = "+918973992043" 
YOUR_TEMPLATE_ID = "PASTE_TEMPLATE_ID_HERE"

asyncio.run(send_live_test_otp(YOUR_PHONE, YOUR_TEMPLATE_ID))
