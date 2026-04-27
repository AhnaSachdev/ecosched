from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter()

_jobs = {}

class JobIn(BaseModel):
    job_id: str
    name: str
    pid: Optional[int] = None
    urgency: int
    deadline_seconds: int

@router.post("/api/jobs")
def add_job(job: JobIn):
    _jobs[job.job_id] = {
        "job_id": job.job_id,
        "name": job.name,
        "pid": job.pid,
        "urgency": job.urgency,
        "deadline": time.time() + job.deadline_seconds
    }
    return {"status": "added"}

@router.get("/api/jobs")
def list_jobs():
    return list(_jobs.values())