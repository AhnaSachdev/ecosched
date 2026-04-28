from fastapi import APIRouter
import httpx, os
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/api/carbon")
EM_KEY = os.getenv("ELECTRICITY_MAPS_API_KEY")
EM_ZONE = os.getenv("ELECTRICITY_MAPS_ZONE","IN-NO")

@router.get("/current")
async def carbon_current():
    async with httpx.AsyncClient(timeout=4) as c:
        r = await c.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest",
            params={"zone": EM_ZONE},
            headers={"auth-token": EM_KEY}
        )
    return r.json()

@router.get("/forecast")
async def carbon_forecast():
    async with httpx.AsyncClient(timeout=4) as c:
        r = await c.get(
            "https://api.electricitymap.org/v3/carbon-intensity/forecast",
            params={"zone": EM_ZONE},
            headers={"auth-token": EM_KEY}
        )
    return r.json()