"""
Drive system options
====================

This module allows the user to specify any options to the DriveSystem.py script
through either a command-line argument or through the options file that is used
for input
"""

__version__ = '2.0'

import argparse as ap
from enum import Enum
from prompt_toolkit import print_formatted_text
from typing import Callable, TypeVar, Generic, Optional, List, Union

import drivesystemlib as dslib
################################################################################
# This file contains all the information required to run the DriveSystem.py    #
# script. Ideally, this should be independent of running a GUI.                #
################################################################################
# ABSOLUTE POSITIONS OF AXES FOR TARGETS
AXIS_POSITION_DICT = {} # Define it so it's global

################################################################################
T = TypeVar('T')
class Option( Generic[T] ):
    """
    The Option class holds all information about options used for the
    DriveSystem.py program.

    Attributes
    ----------
    keyword_in_file : str
        This is the keyword used to indicate the option in the options file.
    value : T
        This is the value assigned to the option, which can be of any type (indicated
        by T here).
    validator : Callable[[str],T]
        This is a function that validates the value passed e.g. it prevents assigning
        negative lengths for example, or numbers instead of strings.
    throw_error_if_unset : bool
        Boolean to determine whether an error should be thrown if the user DOES NOT
        set this option.
    error_message : str
        The error message to be printed if the user does not set this option.
    name : str
        This is used for the command line arguments that are not set in the option
        file. This defaults to the keyword used in the file.
    """
    ################################################################################
    def __init__(self,
                 keyword_in_file : str, 
                 value : T, 
                 validator : Callable[[str],T],
                 throw_error_if_unset : bool = False, 
                 error_message : str = '',
                 name : str = None
    ) -> None:
        """
        Option: Initialise the class based on the constructor, and adds the option to
        the list of all options.
        """
        self._keyword_in_file = keyword_in_file
        self._validator = validator
        self._value = self._validator( value )
        self._throw_error_if_unset = throw_error_if_unset
        self._error_message = error_message
        
        if name == None:
            self._name = self._keyword_in_file
        else:
            self._name = name
        
        # Add to dictionary of options
        DICT_OF_OPTIONS[self._name] = self
        return
    
    ################################################################################
    def __str__(self) -> str:
        """
        Option: Returns string representation of the class.
        """
        return f'{self._name:<35} : {self._value}'
    
    ################################################################################
    def delete(self) -> None:
        """
        Option: provides a way to delete the class, which also removes it from the
        global list of options (probably unused).
        """
        DICT_OF_OPTIONS.pop( self._keyword_in_file, None )
        del self
        return
    
    ################################################################################
    def evaluate_value(self) -> None:
        """
        Option: evaluates its current stored value and throws error if this is a
        mission-critical value to be set.
        """
        if self._value == None and self._throw_error_if_unset:
            raise ValueError(f'The value for {self._keyword_in_file} must be set!')
        
        return
    
    ################################################################################
    # SETTERS
    ################################################################################
    def set_keyword(self, keyword : str ) -> None:
        """
        Option: setter for the keyword, which also changes it in the global list.

        Parameters
        ----------
        keyword : str
            The keyword used to access the option in the file and in the dictionary
            of all options
        """
        DICT_OF_OPTIONS.pop(self._keyword_in_file, None)
        self._keyword_in_file = keyword
        DICT_OF_OPTIONS[self._keyword_in_file] = self
        return

    ################################################################################
    def set_value(self, value) -> None:
        """
        Option: setter for the value of the option.

        Parameters
        ----------
        value : any type!
            The value passed to the option. Make sure it makes sense!
        """
        self._value = self._validator(value)
        return
    
    ################################################################################
    # GETTERS
    ################################################################################
    def get_keyword(self) -> str:
        """
        Option: getter for keyword

        Returns
        -------
        _keyword_in_file : str
            Keyword to access option
        """
        return self._keyword_in_file
    
    ################################################################################
    def get_value(self):
        """
        Option: getter for value

        Returns
        -------
        _value : any type!
            The value assigned to the option
        """
        return self._value

    ################################################################################
    def get_throw_error_if_unset(self) -> bool:
        """
        Option: getter for whether to throw an error if unset

        Returns
        -------
        _throw_error_if_unset : bool
            Whether to throw an error if unset
        """
        return self._throw_error_if_unset
    
    ################################################################################
    def get_error_message(self) -> str:
        """
        Option: getter for error message

        Returns
        -------
        _error_message : str
            Error message displayed if unset
        """
        return self._error_message
    

################################################################################
# Define dictionary of options for storing them all!
DICT_OF_OPTIONS : dict[str,Option] = {}

# Define an ENUM for deciding the recoil mode
class RecoilMode(Enum):
    """
    RecoilMode is a basic Enum class for deciding which recoil-detection setup
    is in use
    """
    NONE = 0
    SILICON = 1
    GAS = 2

################################################################################
# VALIDATORS
################################################################################
def numeric_validator(cast_type : Callable[[str],T], min_val : Optional[T] = None, max_val : Optional[T] = None) -> Callable[[str], T]:
    """
    Defines a function that is able to validate a number (int/float) between numerical limits if specified

    Parameters
    ----------
    cast_type : Callable[[str],T]
        The type of the variable (something numeric, or a string representing something numeric)
    min_val : Optional[T]
        Minimum value (can be None if not needed)
    max_val : Optional[T]
        Maximum value (can be None if not needed)
    
    Returns
    -------
    validate : Callable[[str], T]
        The function that ensures that the value passed is numeric
    """
    def validate(value : str) -> T:
        """
        Validates a numerical (T) input between certain bounds

        Parameters
        ----------
        value : str or None
            The value to be tested
        
        Returns
        -------
        val : the value if it fits within bounds, or None if input == None
        """
        # Cannot validate if NoneType, so just return None as value
        if value == None:
            return None
        
        # Convert value to number (int/float)
        val = cast_type(value)

        # Check minimum bounds if needed
        if min_val is not None and val < min_val:
            raise ValueError("Value too small")
        
        # Check maximum bounds if needed
        if max_val is not None and val > max_val:
            raise ValueError("Value too large")
        
        return val
    return validate

################################################################################
def bool_validator() -> Callable[[str], bool]:
    """
    Defines a function that is able to validate whether an object is a bool

    Returns
    -------
    validate : Callable[[str], bool]
        The function that ensures that the value passed is a bool
    """
    def validate( mystr : Union[str,bool] ) -> bool:
        """
        Validates a bool input

        Parameters
        ----------
        mystr : str or bool
        
        Returns
        -------
        val : bool
            The validated boolean, assuming it works
        """
        if type(mystr) == bool:
            return mystr
        if mystr.lower() == 'true' or mystr == '1':
            return True
        if mystr.lower() == 'false' or mystr == '0':
            return False
        else:
            raise ValueError(f'Cannot parse the string {repr(mystr)} as a bool')
    return validate
################################################################################
def numeric_csv_list_validator( cast_type : Callable[[str],T] ) -> Callable[[str], List]:
    """
    Defines a function that is able to validate whether a string of comma-separated
    values is of the right type and can be made into a list

    Parameters
    ----------
    cast_type : Callable[[str],T]
        The type of the variables in the comma-separated list
    
    Returns
    -------
    validate : Callable[[str], T]
        The function that ensures that the value passed is numeric
    """
    def validate( mystr : str ) -> List[T]:
        """
        Validates a comma-separated string input/list as a list

        Parameters
        ----------
        mystr : str or list
        
        Returns
        -------
        val : list
            The validated list, assuming it works
        """
        if mystr == None or mystr == []:
            return []
        return [ cast_type(x.strip()) for x in mystr.split(',') ]
    return validate
################################################################################
def str_validator() -> Callable[[str],str]:
    """
    Defines a function that is able to validate whether an object is a string

    Returns
    -------
    validate : Callable[[str], str]
        The function that ensures that the value passed is a string
    """
    return lambda x : str(x)

################################################################################
def recoil_mode_validator() -> Callable[[str], RecoilMode]:
    """
    Defines a function that is able to validate whether an object is sufficient
    to be a "RecoilMode" object

    Returns
    -------
    validate : Callable[[str], str]
        The function that ensures that the value passed returns a RecoilMode object
    """
    def validate(mystr : str ) -> RecoilMode:
        """
        Validates a RecoilMode input

        Parameters
        ----------
        mystr : str or RecoilMode
        
        Returns
        -------
        val : RecoilMode
            The validated RecoilMode, assuming it works
        """
        if mystr == "silicon" or "si":
            return RecoilMode.SILICON
        if mystr == "gas":
            return RecoilMode.GAS
        return RecoilMode.NONE
    return validate

################################################################################
# OPTIONS
################################################################################
SOURCE_DIRECTORY = "/home/isslocal/DriveSystemGUI"
DEFAULT_OPTIONS_FILE =  SOURCE_DIRECTORY+ "/options.txt"

OPTION_SILENCER_LENGTH                                           = Option( 'SilencerLength', None, validator=numeric_validator(float,min_val=0.0) )
OPTION_IS_DURING_EXPERIMENT                                      = Option( 'ExperimentalMode', True, validator=bool_validator() )
OPTION_GRAFANA_AUTHENTICATION                                    = Option( 'GrafanaAuthentication', None, validator=str_validator() )
OPTION_TARGET_LADDER_DIMENSION                                   = Option( 'TargetLadderDimension', 2, validator=numeric_validator(int, min_val=1, max_val=2 ) )
OPTION_IS_BEAM_BLOCKER_ENABLED                                   = Option( 'BeamBlockerEnabled', True, validator=bool_validator() )
OPTION_DISABLED_AXES                                             = Option( 'DisabledAxes', [], validator=numeric_csv_list_validator(int) )
OPTION_TARGET_LADDER_IMAGE_PATH                                  = Option( 'TargetLadderImagePath', None, validator=str_validator() )
OPTION_BEAM_BLOCKER_IMAGE_PATH                                   = Option( 'BeamBlockerImagePath', None, validator=str_validator() )
OPTION_2D_LADDER_LABEL_MAP_PATH                                  = Option( '2DLadderLabelMapPath', SOURCE_DIRECTORY + "/id_label_map.txt", validator=str_validator() )
OPTION_2D_LADDER_ENCODER_POSITION_MAP_PATH                       = Option( '2DLadderEncoderPositionMapPath', SOURCE_DIRECTORY + "/id_dist_map.txt", validator=str_validator() )
OPTION_ARRAY_TIP_TO_TARGET_LADDER_AT_SPECIFIED_ENCODER_POSITIONS = Option( 'ArrayTipToTargetLadderDistanceAtSpecifiedEncoderPositions', None, validator=numeric_validator(float, min_val=0.0), throw_error_if_unset=True, error_message='Distance between array tip and target ladder MUST be supplied' )
OPTION_ENCODER_AXIS_ONE                                          = Option( 'EncoderAxis1', None, validator=numeric_validator(int), throw_error_if_unset=True, error_message='Encoder position for axis one MUST be supplied' )
OPTION_ENCODER_AXIS_TWO                                          = Option( 'EncoderAxis2', None, validator=numeric_validator(int), throw_error_if_unset=True, error_message='Encoder position for axis two MUST be supplied' )
OPTION_TARGET_LADDER_AXIS_3_REFERENCE_POINT                      = Option( 'TargetLadderAxis3ReferencePoint', None, validator=numeric_validator(float), throw_error_if_unset=True, error_message='Reference point for axis three MUST be supplied' )
OPTION_TARGET_LADDER_AXIS_5_REFERENCE_POINT                      = Option( 'TargetLadderAxis5ReferencePoint', None, validator=numeric_validator(float), throw_error_if_unset=True, error_message='Reference point for axis five MUST be supplied' )
OPTION_TARGET_LADDER_REFERENCE_POINT_ID                          = Option( 'TargetLadderReferencePointID', None, validator=str_validator() )
OPTION_BEAM_BLOCKER_AXIS_6_REFERENCE_POINT                       = Option( 'BeamBlockerAxis6ReferencePoint', None, validator=numeric_validator(float) )
OPTION_BEAM_BLOCKER_AXIS_7_REFERENCE_POINT                       = Option( 'BeamBlockerAxis7ReferencePoint', None, validator=numeric_validator(float) )
OPTION_BEAM_BLOCKER_REFERENCE_POINT_ID                           = Option( 'BeamBlockerReferencePointID', None, validator=str_validator() )

# Ideas for the future...
# OPTION_IS_ARRAY_UPSTREAM                                         = Option( 'ArrayIsUpstream', True, validator=bool_validator() )
# OPTION_RECOIL_MODE                                               = Option( 'RecoilMode', RecoilMode.NONE, validator=recoil_mode_validator() )
# OPTION_ATMOSPHERE = Option( 'Atmosphere', xxx, validator=xxx() )

CMD_LINE_ARG_SERIAL_PORT = Option( None, '/dev/ttyS0', name='SerialPort', validator=str_validator() )
CMD_LINE_ARG_OPTIONS_FILE_PATH = Option( None, SOURCE_DIRECTORY + "/options.txt", name='OptionsFile', validator=str_validator())
CMD_LINE_ARG_DARK_MODE = Option( None, False, name='DarkMode', validator=bool_validator() )
CMD_LINE_ARG_MONITOR_RESOURCES = Option( None, False, name='MonitorResources', validator=bool_validator() )
CMD_LINE_ARG_NO_GUI = Option( None, False, name='NoGUI', validator=bool_validator())


################################################################################
# FUNCTIONS
################################################################################
def list_to_str( object ) -> str:
    """
    This function converts a list (of length 1 only unless you want errors!) into
    a string. There seems to be some discrepancy in the arparse library in Python
    3.9 (at least) when used on different OS's so that arguments are sometimes
    strings or a list containing a string e.g. 'option' v.s. ['option']
    """
    if type(object) == str:
        return object
    
    if type(object) != list:
        raise TypeError(f'Object must be a list, not a {type(object)}')
    
    if len(object) > 1:
        raise IndexError('Cannot decide between elements!')
    
    if len(object) == 0:
        raise IndexError('Cannot use empty list!')
    
    return object[0]

################################################################################
def parse_command_line_arguments() -> None:
    """
    Parse the command line arguments for the DriveSystem.py script
    """
    desc = """DriveSystem.py is the main script for controlling the motors within the \
ISS experiment at CERN. It communicates with the motor box through the \
PySerial library, and allows the user to make easy changes through a \
non-scary interface. A GUI is drawn to show the precise positioning of \
all of the motors inside the magnet, assuming you have done the alignment \
correctly."""
    epilogue="""
Options file arguments + defaults:
"""
    for key in DICT_OF_OPTIONS.keys():
        epilogue+='  ' + str(DICT_OF_OPTIONS[key]) + '\n'
    epilogue+="""
In case of any problems, please contact Patrick MacGregor, who is almost \
certainly responsible for any remaining bugs.
"""

    parser = ap.ArgumentParser(prog='DriveSystem.py', description=desc, epilog=epilogue, formatter_class=ap.RawTextHelpFormatter)
    parser.add_argument('--version', action='version', version=f'%(prog)s version {__version__}')
    parser.add_argument('-p', '--port', nargs=1, type=str, help='choose the serial port through which to connect. This is useful if you have replaced the motor box with a simulation', metavar='port', default=dslib.DEFAULT_SERIAL_PORT)
    parser.add_argument('-m', '--monitor', action='store_true', default=False, help='this will print CPU, memory, and thread information periodically to the console to help diagnose memory leaks')
    parser.add_argument('-d','--dark-mode',action='store_true',default=False, help='puts GUI in dark mode')
    parser.add_argument('--no-gui', action='store_true', default=False, help='will just push the encoder positions to Grafana')
    parser.add_argument('--options-file', nargs=1, type=str, help='specify the options file used to control the script', metavar='file', default=DEFAULT_OPTIONS_FILE)
    args = parser.parse_args()

    # Now change things based on values
    CMD_LINE_ARG_SERIAL_PORT.set_value( list_to_str(args.port) )
    CMD_LINE_ARG_OPTIONS_FILE_PATH.set_value( list_to_str(args.options_file) )
    CMD_LINE_ARG_MONITOR_RESOURCES.set_value( args.monitor )
    CMD_LINE_ARG_DARK_MODE.set_value( args.dark_mode )
    CMD_LINE_ARG_NO_GUI.set_value( args.no_gui )
    return

################################################################################
def read_options_from_file() -> None:
    """
    Reads the options from the file and stores them in the global variables
    in the drivesystemoptions.py file
    """
    # Open the file
    with open(CMD_LINE_ARG_OPTIONS_FILE_PATH.get_value(), 'r') as file:
        line_ctr = 0
        # Read each line in the file
        for line in file:
            line_ctr += 1
            # Strip whitespace from left and right of line
            line = line.strip()

            # Ignore if line is empty
            if len(line) == 0:
                continue

            # Check to see if it begins with a comment, and ignore if it does
            if line[0] == '#':
                continue
            
            # Now check to see if line contains 0 or > 2 colon - this indicates it is an option. Print an error if not
            if line.count(':') != 1:
                print_formatted_text(f'OPTION ERROR: line {line_ctr} does not contain a valid option -> [{line}]')
                continue

            # Split line at colon
            splitline = line.split(':')
            key = splitline[0].strip()
            value = splitline[1].strip()

            # Check key and value are not empty
            if len(key) == 0:
                print_formatted_text(f'OPTION ERROR: line {line_ctr} does not contain a valid key -> [{line}]')
                continue

            if len(value) == 0:
                print_formatted_text(f'OPTION ERROR: line {line_ctr} does not contain a valid value -> [{line}]')
                continue

            # Strip any comments
            if '#' in value:
                value = value.split('#')[0].strip()
            
            # Check key exists already = known option
            if DICT_OF_OPTIONS.get(key, 'NOKEY') == 'NOKEY':
                print_formatted_text(f'ERROR: key {key} is unknown. Ignoring...')
                continue

            # Key exists. Process and store
            DICT_OF_OPTIONS[key].set_value(value)
    return

################################################################################
def throw_error_if_arguments_empty() -> None:
    """
    This loops over all options and checks if they've all had their values
    assigned. This ensures the code does not run without some complaint if there
    are issues.
    """
    message = ""
    for key in DICT_OF_OPTIONS.keys():
        if DICT_OF_OPTIONS[key].get_value() == None and DICT_OF_OPTIONS[key].get_throw_error_if_unset():
            message += "   * " + DICT_OF_OPTIONS[key].get_error_message() + "\n"

    if message == "":
        return
    
    raise LookupError("\n" + message)

################################################################################
def initialise_options() -> None:
    """
    This MUST be called every time you want some options processed. It'll call 
    the necessary functions in order (see function for details)
    """
    parse_command_line_arguments()
    read_options_from_file()
    throw_error_if_arguments_empty()
    return

################################################################################
def print_options() -> None:
    """
    A diagnostic that prints all options
    """
    for key in DICT_OF_OPTIONS.keys():
        print_formatted_text( str(DICT_OF_OPTIONS[key] ))
    return

################################################################################
def get_blocking_distance() -> float:
    """
    Returns
    -------
    This is the total blocking distance of the silencer
    """
    # 32.6 mm of silencer sticks into array, 18.5 mm distance from tip to silicon
    return OPTION_SILENCER_LENGTH.get_value() + 18.5 - 32.6

################################################################################
def get_silencer_length_from_tip() -> float:
    """
    Returns
    -------
    The physical length of the silencer from the tip of the array to its end (i.e.
    subtracted the part inside the array)
    """
    return max( OPTION_SILENCER_LENGTH.get_value() - 32.6, 0.0 )


