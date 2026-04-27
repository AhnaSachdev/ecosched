import subprocess, sys, time

def start_cpu_hog(name: str, duration_secs: int = 300):
    """Launches a CPU-burning process. Returns its PID."""
    script = f"""
import time, math
end = time.time() + {duration_secs}
while time.time() < end:
    [math.sqrt(i) for i in range(10000)]
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print(f"Started job '{name}' with PID {proc.pid}")
    return proc.pid

if __name__ == "__main__":
    pid1 = start_cpu_hog("ml-training-job", 600)
    pid2 = start_cpu_hog("backup-compress-job", 600)
    print(f"Jobs running. PIDs: {pid1}, {pid2}")
    input("Press Enter to kill all jobs...")