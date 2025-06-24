#!/usr/bin/env python3
"""
DriveSystem
===========

This application contains the main() function for the DriveSystem GUI interface, 
which controls the motor within the ISS experiment at CERN. More information can
be found on the `GitHub page <https://github.com/ISOLDESolenoidalSpectrometer/DriveSystemGUI>`
"""
# Process options before everything else!
import drivesystemoptions as dsopts
dsopts.initialise_options()

from filelock import Timeout
from drivesystemlib import *
import drivesystemcli as dscli
import drivesystemgui as dsgui
import drivesystemlock as dslock
import drivesystemprint as dsp
from prompt_toolkit import print_formatted_text
import prompt_toolkit.patch_stdout as ptps
import resourcemonitor
import wx
import sys

################################################################################
################################################################################
################################################################################
def main():
    """
    This is the main script for running the motors at ISS. This reads in some 
    saved values, launches the GUI, and then this runs until the GUI is killed, 
    after which is safely closes everything. This is called with a file lock, 
    so that any other script with a similarly defined file lock will not be 
    able to open.
    """
    # Read encoder positions of everything
    if not read_encoder_positions_of_elements( dsopts.OPTION_2D_LADDER_ENCODER_POSITION_MAP_PATH.get_value() ):
        # We want this to fail because otherwise we cannot move anything with confidence!
        return

    # Initialise DriveSystem and DriveSystemThread and CLI (which does nothing if in GUI mode)
    drive_system_cli = dscli.GET_CLI()
    drive_system = DriveSystem()
    drive_system_thread = DriveSystemThread()
    drive_system_thread.start()

    # Resource monitoring
    if dsopts.CMD_LINE_ARG_MONITOR_RESOURCES.get_value():
        monitor = resourcemonitor.GET_RESOURCE_MONITOR_THREAD()
        monitor.start()

    # Launch DriveSystemGUI if desired
    if dsopts.CMD_LINE_ARG_NO_GUI.get_value() == False:
        app = wx.App()
        gui = dsgui.DriveSystemGUI(None, "ISS Drive System")
        gui.Show()
        
        # Run the loop with Ctrl + C exit capabilities
        try:
            app.MainLoop()
        except KeyboardInterrupt:
            dsp.dsprint("")

        shutdown()
    else:
        drive_system_cli.run()
    
    return



################################################################################
# Run main with file lock if serial port is in use by another program (lock should be claimed by other program!)
if __name__ == '__main__':
    try:
        with dslock.get_serial_port_lock():
            main()
    except Timeout:
        dsp.dsprint("Someone else is using the serial port to communicate with the motors. Please stop that process first before running this script.")
