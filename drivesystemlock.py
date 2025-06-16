"""
DriveSystemLock
===============

Module that locks down any other programmes from using the DriveSystem. This 
should be accessed by all scripts that use the DriveSystem interface!
"""
from filelock import FileLock
import os

def get_serial_port_lock():
    """
    This function returns a lock that it places in the user's home directory
    (which means it can be used on multiple computers without directory issues).
    """
    # VARIABLES
    lock_file = "drive_system_serial_port.lock"

    # CHOOSE PATH BASED ON SYSTEM
    path = os.path.expanduser('~')

    # CREATE LOCK FILE
    DRIVE_SYSTEM_LOCK = FileLock(path + '/' + lock_file, timeout=1 )
    return DRIVE_SYSTEM_LOCK