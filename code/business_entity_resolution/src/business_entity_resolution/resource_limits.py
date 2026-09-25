"""Windows working-set and wall-time guard."""
import ctypes
import os
import time


class Counters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def rss():
    if os.name != "nt":
        return 0
    counters = Counters(); counters.cb = ctypes.sizeof(counters)
    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.argtypes = []
    get_process.restype = ctypes.c_void_p
    get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    get_memory.restype = ctypes.c_int
    if not get_memory(get_process(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.WorkingSetSize)


class Guard:
    def __init__(self, max_bytes, max_seconds):
        self.max_bytes, self.max_seconds = max_bytes, max_seconds
        self.start, self.cpu_start, self.peak = time.perf_counter(), time.process_time(), 0
        self.checks = 0
        self.check()

    def check(self):
        elapsed = time.perf_counter() - self.start
        memory = rss(); self.peak = max(self.peak, memory); self.checks += 1
        if memory > self.max_bytes:
            raise RuntimeError(f"Memory limit exceeded: {memory}")
        if elapsed > self.max_seconds:
            raise RuntimeError(f"Runtime limit exceeded: {elapsed:.2f}s")

    def report(self):
        self.check()
        wall, cpu = time.perf_counter() - self.start, time.process_time() - self.cpu_start
        return {"wall_seconds": wall, "cpu_seconds": cpu, "cpu_to_wall_ratio": cpu / wall, "peak_working_set_bytes": self.peak, "checks": self.checks}
