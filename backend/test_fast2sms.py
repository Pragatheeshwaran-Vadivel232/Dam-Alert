import httpx
import asyncio

async def send_quick_sms(phone: str, message: str, api_key: str):
    clean_phone = phone.replace("+", "").replace("91", "", 1).strip()
    
    url = "https://www.fast2sms.com/dev/bulkV2"
    
    # We use route "q" (Quick SMS) which bypasses personal DLT requirements
    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": clean_phone
    }
    
    headers = {
        "authorization": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"📡 Sending real SMS to +91{clean_phone} via Fast2SMS Quick Route...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        print("Response Code:", response.status_code)
        print("Response Body:", response.json())

# REPLACE THESE WITH YOUR DETAILS
YOUR_API_KEY = "nO2kbwFGlUX6stcKf5Wa470TxoYQ1rSHVjZyJDmzBREPACIpL9TERj2wG6UkXWMB9ZH5LspD8crS1Ane"
YOUR_PHONE = "918973992043" # +918973992043

TEST_MESSAGE = "KaLai Dam Alert Test:\nAmaravathi level is 53.41 ft.\nInflow: 346 CuSecs.\nEverything is working!"

asyncio.run(send_quick_sms(YOUR_PHONE, TEST_MESSAGE, YOUR_API_KEY))
