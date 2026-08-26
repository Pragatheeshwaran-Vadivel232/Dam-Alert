import httpx
from bs4 import BeautifulSoup
from datetime import date

DAMS_OF_INTEREST = ["AMARAVATHI", "THIRUMURTHY"]
BASE_URL = "https://tnagriculture.in/ARS/home/reservoir"

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

async def fetch_dam_data(for_date: date = None) -> list[dict]:
    url = f"{BASE_URL}/{for_date}" if for_date else BASE_URL
    print(f"Fetching data from: {url}")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table")

    if not table:
        raise ValueError("Could not find data table on page")

    rows = table.find_all("tr")
    results = []

    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cols:
            continue
        dam_name = cols[0].upper().replace("*", "").strip()
        if any(d in dam_name for d in DAMS_OF_INTEREST):
            results.append({
                "dam_name":       dam_name,
                "full_depth_ft":  safe_float(cols[1]),
                "full_cap_mcft":  safe_float(cols[2]),
                "level_ft":       safe_float(cols[3]),
                "storage_mcft":   safe_float(cols[4]),
                "inflow_cusecs":  safe_float(cols[5]),
                "outflow_cusecs": safe_float(cols[6]),
            })

    print(f"Found data for: {[r['dam_name'] for r in results]}")
    return results
