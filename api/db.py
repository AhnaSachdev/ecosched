from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, Text
import datetime, os
from dotenv import load_dotenv
load_dotenv()

engine = create_async_engine(
    os.getenv("DATABASE_URL","sqlite+aiosqlite:///./ecosched.db"))

class Base(DeclarativeBase): pass

class Decision(Base):
    __tablename__ = "decisions"
    id:            Mapped[int]   = mapped_column(Integer,primary_key=True)
    job_id:        Mapped[str]   = mapped_column(String(64))
    job_name:      Mapped[str]   = mapped_column(String(128))
    action:        Mapped[str]   = mapped_column(String(16))
    defer_score:   Mapped[float] = mapped_column(Float)
    co2_saved:     Mapped[float] = mapped_column(Float)
    carbon_ci:     Mapped[float] = mapped_column(Float)
    reasoning:     Mapped[str]   = mapped_column(Text)
    cpu_burst_pct: Mapped[float] = mapped_column(Float)
    io_wait_pct:   Mapped[float] = mapped_column(Float)
    timestamp:     Mapped[str]   = mapped_column(
        String(32),
        default=lambda: datetime.datetime.utcnow().isoformat())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)