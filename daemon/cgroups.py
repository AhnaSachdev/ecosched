import os, logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

CGROUP_ROOT = "/sys/fs/cgroup/ecosched"

def ensure_cgroup_exists():
    # On Windows, just log
    logging.info("Simulated: ensure cgroup exists")

def set_cpu_weight(job_id: str, weight: int):
    logging.info(f"[SIM] Set CPU weight {weight} for job {job_id}")

def freeze_job(job_id: str, pid: int):
    logging.info(f"[SIM] Freeze job {job_id} (pid {pid})")

def thaw_job(job_id: str):
    logging.info(f"[SIM] Thaw job {job_id}")

def throttle_job(job_id: str, pid: int, cpu_weight: int = 20):
    logging.info(f"[SIM] Throttle job {job_id} (pid {pid}) with weight {cpu_weight}")