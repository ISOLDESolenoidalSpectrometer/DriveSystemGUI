"""
ResourceMonitor
===============

This module is a simple resource monitoring thread for a process.
"""

import datetime
import os
import psutil
import threading
import drivesystemprint as dsp

class ResourceMonitorThread(threading.Thread):
    """
    The resource monitor thread monitors the memory usage, CPU usage, and number of
    threads that a given process uses. It prints this usage to console as well as the
    process ID and date after a set period of time.
    """
    ################################################################################
    def __init__(self, interval : int = 5) -> None:
        """
        ResourceMonitorThread: initialise the thread
        """
        super().__init__()
        self.interval = interval
        self.running = True
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)
        self.event = threading.Event()

    ################################################################################
    def run(self):
        """
        ResourceMonitorThread: start while loop for checking the 
        """
        while self.running:
            mem = self.process.memory_info().rss / 1024 / 1024  # in MB
            cpu = self.process.cpu_percent(interval=None)  # % CPU usage
            num_threads = self.process.num_threads()
            now = datetime.datetime.now().isoformat('-','seconds')
            dsp.dsprint(f"[Resource Monitor {self.pid}] {now} | Memory: {mem:.2f} MB | CPU: {cpu:.1f}% | Threads: {num_threads}")

            # for t in threading.enumerate():
            #     print(f"    Thread name: {t.name}, ID: {t.ident}, Alive: {t.is_alive()}")

            # Wait before running next iteration, but have option to cancel it prematurely through setting event
            self.event.wait( timeout=self.interval )

    ################################################################################
    def kill(self):
        """
        ResourceMonitorThread: kill the thread
        """
        self.running = False
        self.event.set()


def GET_RESOURCE_MONITOR_THREAD() -> ResourceMonitorThread:
    if not hasattr(GET_RESOURCE_MONITOR_THREAD, "_instance"):
        GET_RESOURCE_MONITOR_THREAD._instance = ResourceMonitorThread()
    return GET_RESOURCE_MONITOR_THREAD._instance