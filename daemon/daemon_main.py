import asyncio, httpx, os, logging
from telemetry import get_process_snapshot, compute_io_wait_pct, compute_mem_pressure
from carbon import get_carbon_intensity
from cgroups import freeze_job, thaw_job, throttle_job
from jobs import JobRegistry

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [DAEMON] %(message)s")

API_URL = "http://localhost:8000"
registry = JobRegistry()

async def run_cycle():
    ci = await get_carbon_intensity()
    io_wait = compute_io_wait_pct()
    mem = compute_mem_pressure()
    procs = get_process_snapshot()

    for job in registry.get_all():
        if job.is_expired() and job.state != "running":
            thaw_job(job.job_id)
            registry.update_state(job.job_id, "running")
            continue

        proc_data = next((p for p in procs if p["pid"]==job.pid), None)
        cpu_burst = proc_data["cpu_pct"] if proc_data else 0

        payload = {
            "job_id":         job.job_id,
            "job_name":       job.name,
            "cpu_burst_pct":  cpu_burst,
            "io_wait_pct":    io_wait,
            "mem_pressure_mb": mem["swap_used_mb"],
            "carbon_ci":      ci,
            "urgency":        job.urgency,
            "deadline_seconds": job.deadline_seconds(),
            "current_state":  job.state
        }

        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.post(f"{API_URL}/internal/decide", json=payload)
                decision = r.json()

            action = decision["action"]
            co2   = decision.get("co2_saved_grams", 0)

            if action == "defer" and job.pid:
                freeze_job(job.job_id, job.pid)
                registry.update_state(job.job_id, "deferred")
            elif action == "throttle" and job.pid:
                throttle_job(job.job_id, job.pid)
                registry.update_state(job.job_id, "throttled")
            elif action == "run":
                thaw_job(job.job_id)
                registry.update_state(job.job_id, "running")

            registry.add_co2_saved(job.job_id, co2)
            logging.info(f"{job.name} → {action} | CO2 saved: {co2:.1f}g | CI: {ci}")

        except Exception as e:
            logging.error(f"Cycle error for {job.name}: {e}")

async def main():
    import time
    from jobs import Job

    # 🔥 TEMP: manually add jobs
    registry.add(Job(
        job_id="job1",
        name="ml-training-job",
        pid=None,
        urgency=2,
        deadline=time.time() + 300
    ))

    registry.add(Job(
        job_id="job2",
        name="backup-job",
        pid=None,
        urgency=1,
        deadline=time.time() + 600
    ))

    while True:
        await run_cycle()
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())