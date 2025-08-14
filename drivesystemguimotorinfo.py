"""
DriveSystem GUI Motor Info
==========================

Stores all graphical information about each motor axis. This information should 
be initialised before the GUI is initialised.
"""

import drivesystemmotorinfo as dsmi

################################################################################
# CONSTANTS
# Physical distances that will not change
ARRAY_SILICON_TO_TIP_DISTANCE = 18.5 # [mm]
ARRAY_SUPPORT_TO_END_OF_SILICON = 626.1 - ARRAY_SILICON_TO_TIP_DISTANCE # See elog:6071 for length of array
MAGNET_LENGTH = 2732 # Magnet length [mm]

################################################################################
def store_graphics_info_about_motors() -> None:
    """
    Store information in the MOTOR_AXIS_DICT about each axis
    """
    #                                                    Width, Height, Colour
    dsmi.MOTOR_AXIS_DICT['SiA'].init_graphics_properties( ARRAY_SUPPORT_TO_END_OF_SILICON,  35.0, '#FD3F0D'), # The width was changed from 610.0 after elog:6071
    dsmi.MOTOR_AXIS_DICT['TaC'].init_graphics_properties( 450.0, 270.0, '#0DE30B' ), # PlotView
    dsmi.MOTOR_AXIS_DICT['ArC'].init_graphics_properties( 350.0, 195.0, '#FDD11F' ), # PlotView
    dsmi.MOTOR_AXIS_DICT['TLH'].init_graphics_properties(  80.0, 130.0, '#00A7FA' ), # PlotView
    dsmi.MOTOR_AXIS_DICT['Det'].init_graphics_properties(  80.0, 130.0, '#910BE3' ), # PlotView
    dsmi.MOTOR_AXIS_DICT['TLV'].init_graphics_properties( 308.5, 194.0, '#00A7FA' ), # BeamView
    dsmi.MOTOR_AXIS_DICT['BBV'].init_graphics_properties( 173.0, 118.0, '#910BE3' ), # BeamView
    dsmi.MOTOR_AXIS_DICT['BBH'].init_graphics_properties(  80.0, 130.0, '#910BE3' )  # PlotView
    return