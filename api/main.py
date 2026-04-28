from carbon_router import router as carbon_router
from jobs_router import router as jobs_router
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from contextlib import asynccontextmanager
from db import init_db, engine, Decision
from gemini_engine import decide
import asyncio, json, logging

ws_clients: list[WebSocket] = []
_co2_total = 0.0

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="EcoSched API", lifespan=lifespan)
app.include_router(jobs_router)
app.include_router(carbon_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/internal/decide")
async def internal_decide(payload: dict):
    global _co2_total

    result = await decide(payload)

    async with AsyncSession(engine) as session:
        d = Decision(
            job_id=payload["job_id"],
            job_name=payload["job_name"],
            action=result["action"],
            defer_score=result["defer_score"],
            co2_saved=result.get("co2_saved_grams", 0),
            carbon_ci=payload["carbon_ci"],
            reasoning=result["reasoning"],
            cpu_burst_pct=payload["cpu_burst_pct"],
            io_wait_pct=payload["io_wait_pct"]
        )
        session.add(d)
        await session.commit()

    _co2_total += result.get("co2_saved_grams", 0)

    broadcast = {
        "type": "decision",
        "job_name": payload["job_name"],
        "action": result["action"],
        "reasoning": result["reasoning"],
        "co2_saved": result.get("co2_saved_grams", 0),
        "total_co2_saved": round(_co2_total, 2),
        "carbon_ci": payload["carbon_ci"],
        "cpu_burst_pct": payload["cpu_burst_pct"],
        "io_wait_pct": payload["io_wait_pct"]
    }

    await _broadcast(broadcast)
    return result


@app.get("/api/stats")
async def get_stats():
    async with AsyncSession(engine) as session:
        total_co2 = await session.scalar(
            select(func.sum(Decision.co2_saved))
        )
        count = await session.scalar(
            select(func.count(Decision.id))
        )
        recent = await session.execute(
            select(Decision).order_by(Decision.id.desc()).limit(20)
        )
        rows = recent.scalars().all()

    return {
        "total_co2_saved_grams": round(total_co2 or 0, 2),
        "total_decisions": count or 0,
        "recent": [
            {
                "job_name": r.job_name,
                "action": r.action,
                "co2_saved": r.co2_saved,
                "reasoning": r.reasoning,
                "carbon_ci": r.carbon_ci,
                "timestamp": r.timestamp
            }
            for r in rows
        ]
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_clients.remove(ws)


async def _broadcast(data: dict):
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_json(data)
        except:
            dead.append(ws)
    for ws in dead:
        ws_clients.remove(ws)