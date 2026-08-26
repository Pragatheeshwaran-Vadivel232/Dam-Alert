import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tnagriculture import fetch_dam_data

async def main():
    print("Testing dam data scraper...")
    print("-" * 40)
    
    data = await fetch_dam_data()
    
    for dam in data:
        print(f"\n DAM: {dam['dam_name']}")
        print(f" Level    : {dam['level_ft']} ft")
        print(f" Storage  : {dam['storage_mcft']} M.Cft")
        print(f" Inflow   : {dam['inflow_cusecs']} CuSecs")
        print(f" Outflow  : {dam['outflow_cusecs']} CuSecs")
        print(f" Full Depth: {dam['full_depth_ft']} ft")
        print(f" Full Cap : {dam['full_cap_mcft']} M.Cft")

asyncio.run(main())
