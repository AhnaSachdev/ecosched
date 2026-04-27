import httpx, os, time, logging
from dotenv import load_dotenv
load_dotenv()

EM_KEY  = os.getenv("ELECTRICITY_MAPS_API_KEY")
EM_ZONE = os.getenv("ELECTRICITY_MAPS_ZONE", "IN-NO")
_cache  = {"value": 350, "ts": 0}   # default 350 gCO2/kWh

async def get_carbon_intensity() -> float:
    now = time.time()
    if now - _cache["ts"] < 300:     # cache 5 minutes
        return _cache["value"]
    try:
        async with httpx.AsyncClient(timeout=4) as c:
            r = await c.get(
                "https://api.electricitymap.org/v3/carbon-intensity/latest",
                params={"zone": EM_ZONE},
                headers={"auth-token": EM_KEY}
            )
            data = r.json()
            ci = data["carbonIntensity"]
            _cache.update({"value": ci, "ts": now})
            return ci
    except Exception as e:
        logging.warning(f"Carbon API failed: {e}, using cached {_cache['value']}")
        return _cache["value"]