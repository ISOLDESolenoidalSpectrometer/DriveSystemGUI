"""
DriveSystem Motor Info
======================

Contains all the necessary information for accessing motor axis information from 
anywhere. Primarily stored in a dictionary, with each key corresponding to a POD 
object that has member variables with information. Additional information is 
added if running in GUI mode.
"""

import drivesystemlib as dslib
import drivesystemoptions as dsopts

# This is a global variable! But cannot initialise or type hint as it requires circular imports
MOTOR_AXIS_DICT = {}

################################################################################
class MotorAxisBase:
    """
    Class to hold information about a motor axis. POD class.
    """
    ################################################################################
    def __init__(self, axis_label : str, grafana_name : str ):
        """
        MotorAxisBase: contains information about the motor axes
        """
        self.axis_label = axis_label
        self.grafana_name = grafana_name
        self.axis_number = None
        return
    ################################################################################
    def set_axis_number(self, axis_number : int ):
        """
        MotorAxisBase: set the axis number of a given axis
        """
        self.axis_number = axis_number
        return
    ################################################################################
    def __str__(self):
        """
        MotorAxisBase: conversion to string
        """
        return f"MotorAxisBase: axis label = {self.axis_label}, grafana name = {self.grafana_name}, axis number = {self.axis_number}"


################################################################################
################################################################################
################################################################################
class MotorAxisInfoGraphics(MotorAxisBase):
    """
    Extends MotorAxisBase class to include graphical information
    """
    def __init__(self, axis_label : str, grafana_name : str):
        """
        MotorAxisInfoGraphics: Initialise the class
        """
        super().__init__(axis_label, grafana_name)
        self.width = None
        self.height = None
        self.colour = None
        return

    ################################################################################
    def init_graphics_properties(self, width : float, height : float, colour : str):
        """
        MotorAxisInfoGraphics: set the graphical properties - cannot call in 
        constructor as we don't know if we're using graphical mode when the
        MOTOR_AXIS_DICT elements are initialised
        """
        self.width = width
        self.height = height
        self.colour = colour
        return
    ################################################################################
    def __str__(self):
        """
        MotorAxisInfoGraphics: conversion to string
        """
        return super().__str__() + f"\nMotorAxisInfoGraphics: width = {self.width}, height = {self.height}, colour = {self.colour}"
    

################################################################################
################################################################################
################################################################################
def MotorAxisInfo( axis_label : str, grafana_name : str ) -> MotorAxisBase:
    """
    This function constructs the object based on whether the GUI is used or not
    """
    if dsopts.CMD_LINE_ARG_NO_GUI.get_value():
        return MotorAxisBase( axis_label, grafana_name )
    else:
        return MotorAxisInfoGraphics( axis_label, grafana_name )

################################################################################
def init_motor_properties():
    """
    Initialise the motors in the right place so you don't get circular imports
    - called by the main function
    """
    MOTOR_AXIS_DICT['SiA'] = MotorAxisInfo( 'Si array',          None )
    MOTOR_AXIS_DICT['TaC'] = MotorAxisInfo( 'Target carriage',   'Trolley' )
    MOTOR_AXIS_DICT['ArC'] = MotorAxisInfo( 'Array bed',         'Array' ) 
    MOTOR_AXIS_DICT['TLH'] = MotorAxisInfo( 'Target ladder (H)', 'TargetH' )
    MOTOR_AXIS_DICT['Det'] = MotorAxisInfo( 'FC/ZD',             'FC' ) 
    MOTOR_AXIS_DICT['TLV'] = MotorAxisInfo( 'Target ladder (V)', 'TargetV' )
    MOTOR_AXIS_DICT['BBH'] = MotorAxisInfo( 'Beam blocker (H)',  'BlockerH' )
    MOTOR_AXIS_DICT['BBV'] = MotorAxisInfo( 'Beam blocker (V)',  'BlockerV' )
    return

################################################################################
def set_axis_mapping() -> bool:
    """
    Store the axis mapping based on what was sent in the options file (if nothing
    defined there, the defaults will be used). Then check for duplicate mappings
    as that will not end well.
    """
    MOTOR_AXIS_DICT['SiA'].set_axis_number(None)
    MOTOR_AXIS_DICT['TaC'].set_axis_number( dsopts.OPTION_TROLLEY_AXIS_NUMBER.get_value() )
    MOTOR_AXIS_DICT['ArC'].set_axis_number( dsopts.OPTION_ARRAY_AXIS_NUMBER.get_value() )
    MOTOR_AXIS_DICT['TLH'].set_axis_number( dsopts.OPTION_TARGET_HORIZONTAL_AXIS_NUMBER.get_value() )
    MOTOR_AXIS_DICT['Det'].set_axis_number( dsopts.OPTION_FC_AXIS_NUMBER.get_value() )
    MOTOR_AXIS_DICT['TLV'].set_axis_number( dsopts.OPTION_TARGET_VERTICAL_AXIS_NUMBER.get_value() )
    MOTOR_AXIS_DICT['BBV'].set_axis_number( dsopts.OPTION_BLOCKER_VERTICAL_AXIS_NUMBER.get_value() )
    MOTOR_AXIS_DICT['BBH'].set_axis_number( dsopts.OPTION_BLOCKER_HORIZONTAL_AXIS_NUMBER.get_value() )

    # Check there are no duplicates
    axis_check = [False]*dslib.NUMBER_OF_MOTOR_AXES
    for key in MOTOR_AXIS_DICT.keys():
        if MOTOR_AXIS_DICT[key].axis_number != None:
            if axis_check[ MOTOR_AXIS_DICT[key].axis_number - 1 ] == False:
                axis_check[ MOTOR_AXIS_DICT[key].axis_number - 1 ] = True
            else:
                # Send failure flag
                print("DUPLICATE AXIS NUMBER MAPPING DETECTED!")
                return False
    
    # Send success flag
    return True

################################################################################
def get_motor_axis_dict_property_as_array( property : str ):
    """
    Allows creating arrays of mootr properties with the elements corresponding
    to the axis number (-1)
    """
    arr = [None]*dslib.NUMBER_OF_MOTOR_AXES
    for key in MOTOR_AXIS_DICT.keys():
        if MOTOR_AXIS_DICT[key].axis_number != None:
            arr[ MOTOR_AXIS_DICT[key].axis_number - 1 ] = getattr( MOTOR_AXIS_DICT[key], property )
    
    return arr