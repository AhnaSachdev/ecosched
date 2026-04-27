import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Job:
    job_id:    str
    name:      str
    pid:       Optional[int]
    urgency:   int          # 1 (batch) to 5 (real-time)
    deadline:  float        # unix timestamp of hard deadline
    state:     str = "running"  # running | throttled | deferred
    co2_saved: float = 0.0
    submitted: float = field(default_factory=time.time)

    def deadline_seconds(self) -> float:
        return max(0, self.deadline - time.time())

    def is_expired(self) -> bool:
        return time.time() > self.deadline

class JobRegistry:
    def __init__(self):
        self._jobs: dict[str, Job] = {}

    def add(self, job: Job):
        self._jobs[job.job_id] = job

    def get_all(self) -> list[Job]:
        return list(self._jobs.values())

    def update_state(self, job_id: str, state: str):
        if job_id in self._jobs:
            self._jobs[job_id].state = state

    def add_co2_saved(self, job_id: str, grams: float):
        if job_id in self._jobs:
            self._jobs[job_id].co2_saved += grams