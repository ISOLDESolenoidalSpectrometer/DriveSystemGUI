"""
ResourceMonitor
===============

This module is a simple resource monitoring thread for a process.
"""

import datetime
import os
from prompt_toolkit import print_formatted_text
import psutil
import threading

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
            print_formatted_text(f"[Resource Monitor {self.pid}] {now} | Memory: {mem:.2f} MB | CPU: {cpu:.1f}% | Threads: {num_threads}")

            # for t in threading.enumerate():
            #     print_formatted_text(f"    Thread name: {t.name}, ID: {t.ident}, Alive: {t.is_alive()}")

            # Wait before running next iteration, but have option to cancel it prematurely through setting event
            self.event.wait( timeout=self.interval )

    ################################################################################
    def kill(self):
        """
        ResourceMonitorThread: kill the thread
        """
        self.running = False
        self.event.set()