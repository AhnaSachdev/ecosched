import psutil, time, os

def get_process_snapshot():
    snapshot = []
    for proc in psutil.process_iter(['pid','name','status',
                                     'cpu_percent','memory_info',
                                     'io_counters','num_threads']):
        try:
            p = proc.info
            io = p['io_counters']
            mem = p['memory_info']
            snapshot.append({
                "pid":         p['pid'],
                "name":        p['name'],
                "status":      p['status'],
                "cpu_pct":     p['cpu_percent'],
                "mem_rss_mb":  round(mem.rss / 1024**2, 2),
                "mem_vms_mb":  round(mem.vms / 1024**2, 2),
                "io_read_mb":  round(io.read_bytes/1024**2,2) if io else 0,
                "io_write_mb": round(io.write_bytes/1024**2,2) if io else 0,
                "threads":     p['num_threads'],
                "timestamp":   time.time()
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return snapshot

def compute_io_wait_pct():
    cpu_times = psutil.cpu_times_percent(interval=0.1)
    return round(getattr(cpu_times, "iowait", 0.0), 2)

def compute_mem_pressure():
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    return {
        "used_pct":  round(vm.percent, 1),
        "available_mb": round(vm.available/1024**2, 1),
        "swap_used_mb": round(sw.used/1024**2, 1)
    }