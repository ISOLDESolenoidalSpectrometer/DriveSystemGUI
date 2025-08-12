"""
DriveSystemLib
==============

This contains the core code for operating the DriveSystem. Note that all 
functionality in here should work independently of a GUI. The core components of this
module are two classes:
   1. DriveSystem - this builds upon the serialinterface module as a direct means
      for communicating with the motor box.
   2. DriveSystemThread - runs in the background and sends frequent commands to the
      motor box to keep everything else updated.
"""

import numpy as np
import time 
import re
import requests
import threading
from typing import Tuple, Optional
import urllib3

import drivesystemdutycycle
import drivesystemoptions as dsopts
import serialinterface
import drivesystemdetectoridmapping as dsdidmap

################################################################################
# Kill warnings about pushing to Grafana
urllib3.disable_warnings()

################################################################################
# CONSTANTS RELEVANT TO THIS MOTOR BOX
MM_TO_STEP = 200.0
STEP_TO_MM = 1./MM_TO_STEP
NUMBER_OF_MOTOR_AXES = 7
DEFAULT_SERIAL_PORT='/dev/ttyS0'

################################################################################
# FUNCTIONS
################################################################################
def populate_dictionary_with_default_elements() -> None:
    """
    Populates AXIS_POSITION_DICT with default elements
    """
    keys = dsdidmap.IDMap.ID_LIST
    for key in keys:
        if dsopts.AXIS_POSITION_DICT.get(key, None) == None:
            dsopts.AXIS_POSITION_DICT[key] = [0, 0]
    return

################################################################################
def read_encoder_positions_of_elements( filename : str ) -> bool:
    """
    This function populates the global object AXIS_POSITION_DICT with the assumed
    encoder positions for all the different in-beam elements from the mapping text
    file.

    Parameters
    ----------
    filename : str
        The file path to the file that contains the encoder positions of the 
        different elements. Note that these are CONTEXT-DEPENDENT, so each line 
        should have the form
        '[ID] [HORIZONTAL ENCODER] [VERTICAL ENCODER]'
        where
        - [ID] is the ID to identify which element we are using
        - [HORIZONTAL ENCODER] is the horizontal position of the element. This 
          is axis 3 for the target ladder and axis 6 for the beam blocker.
        - [VERTICAL ENCODER] is the vertical position of the element. This 
          is axis 5 for the target ladder and axis 7 for the beam blocker.
        The lines are delimited by spaces.

    Returns
    -------
    status : bool
        Whether the function succeeded
    """
    # First populate the dictionary with defaults
    populate_dictionary_with_default_elements()

    # Now fill dictionary with elements from file
    try:
        with open( filename, "r") as f:
            lines = f.readlines()
            for x in lines:
                # Parse input
                x = x.rstrip().lstrip()
                split = x.split(' ')

                # Check if it's commented
                if '#' in split[0]:
                    continue

                # Sanitise first value
                try:
                    val1 = int(split[1])
                except ValueError:
                    print(f"Could not convert first value to integer in line \"{x}\". Skipping line in mapping file \"{filename}\"...")
                    continue

                # Sanitise second value
                try:
                    val2 = int(split[2])
                except ValueError:
                    print(f"Could not convert second value to integer in line \"{x}\". Skipping line in mapping file \"{filename}\"...")
                    continue

                # Add to dictionary
                dsopts.AXIS_POSITION_DICT.update({split[0]:[val1,val2]})

            f.close()

    except FileNotFoundError:
        print(f"Couldn't open mapping file between in-beam elements and encoder position. This should be defined with the \"{dsopts.OPTION_2D_LADDER_ENCODER_POSITION_MAP_PATH.get_keyword()}\" in the options file.")
        return False
    
    return True

################################################################################
################################################################################
################################################################################
# This class interfaces directly with the motor serial port
class DriveSystem(serialinterface.SerialInterface):
    """
    A SerialInterface for the motor serial port at ISS.
    """
    DEFAULT_PORTALIAS = DEFAULT_SERIAL_PORT
    COMMANDS_ALWAYS_PERMITTED = ['co', 'oa', 'qa', 'ab']
    ################################################################################
    def __init__(self) -> None:
        """
        DriveSystem: Initialises object
        """
        # Use parent constructor
        super().__init__(dsopts.CMD_LINE_ARG_SERIAL_PORT.get_value())

        # Store positions and axis names for Grafana
        self.positions = np.zeros( NUMBER_OF_MOTOR_AXES, dtype=int )
        self.grafana_axis_name = ['Trolley', 'Array', 'TargetH', 'FC', 'TargetV', 'BlockerV', 'BlockerH']
        self.push_to_grafana = False
        self.grafana_username = None
        self.grafana_password = None
        self.grafana_url = None
        self.disabled_axes = dsopts.OPTION_DISABLED_AXES.get_value()
        self.paused_axes = [] # Stores any axes that need to be paused because of their duty cycle
        self.movement_commands = ['ma', 'mr', 'cv', 'hd', 'md'] # List of commands causing movement on a motor axis
        self.duty_cycles = [
            # dutycycle.DutyCycle( , )
        ]
        self.selected_in_beam_element = None # Use this to store ID of in beam element selected

        # Try and get authentication details for Grafana
        self.get_grafana_authentication()

        # Define a bool to be set to True while slit scanning
        self.is_slit_scanning = False
        self.slit_scanning_check_encoder_position_timer = threading.Event()
        self.slit_scanning_wait_at_position_timer = threading.Event()
        return
    
    ################################################################################
    @staticmethod
    def construct_command( axis : int, cmd : str, number = "" ) -> str:
        """
        DriveSystem: A static method for formatting a command to send to the motor 
        box.

        Parameters
        ----------
        axis : int
            The axis number
        cmd : str
            The command to be sent
        number : int
            (Optional) The number that follows the command

        Returns
        -------
        command : str
            The command that can be directly sent to the motor box
        """
        return f"{axis}{cmd}{number}\r"
    
    ################################################################################
    @staticmethod
    def construct_command_from_str( cmd : str ) -> str:
        """
        DriveSystem: A static method for formatting a command to send to the motor 
        box.

        Parameters
        ----------
        cmd : str
            The FULL command to be sent

        Returns
        -------
        command : str
            The command that can be directly sent to the motor box
        """
        return f"{cmd}\r"
    
    ################################################################################
    @staticmethod
    def deconstruct_command_from_str( command : str ) -> Tuple[Optional[int], Optional[str], Optional[int]]:
        """
        DriveSystem: A static method for deconstructing a command to return the
        axis, command, and any numbers attached

        Parameters
        ----------
        command : str
            The command that could be sent to the motor box

        Returns
        -------
        axis : int
            The axis number
        cmd  : str
            The command
        num  : int
            The (optional) number, defaults to None
        """
        # Define initial values
        axis = None
        cmd = None
        num = None
        
        # Match pattern
        pattern = re.match('([0-9]+)([a-z]+)([0-9]?)\r?', command )

        # No matches
        if pattern == None:
            return axis, cmd, num

        # Group 1
        if pattern.group(1) != '':
            try:
                axis = int(pattern.group(1))
            except:
                print(f'Could not parse axis from command {command}')
        
        # Group 2
        if pattern.group(2) != '':
            try:
                cmd = pattern.group(2)
            except:
                print(f'Could not parse command from command {command}')

        # Group 3
        if pattern.group(3) != '':
            try:
                num = int(pattern.group(3))
            except:
                print(f'Could not parse final number from command {command}')

        return axis, cmd, num

    ################################################################################
    def check_if_valid_command( self, command : str ) -> bool:
        """
        DriveSystem: checks if a given command is valid based on its structure. This
        DOES not check if the motor box will receive it - only if it follows the basic
        pattern of commands being sent to the motor box

        Parameters
        ----------
        command : str
            The command to be checked

        Returns
        -------
        command_validity : bool
            The command's status
        """
        # Check command
        cmd_axis, cmd, num  = DriveSystem.deconstruct_command_from_str(command)

        # Reject command if it's invalid
        if cmd_axis == None:
            print(f"The command {repr(command)} is not valid. Ignoring...")
            return False

        if cmd_axis < 0 or cmd_axis > NUMBER_OF_MOTOR_AXES:
            print(f"The command {repr(command)} does not have a well-defined axis. Ignoring...")
            return False

        if cmd_axis in self.disabled_axes and cmd not in DriveSystem.COMMANDS_ALWAYS_PERMITTED:
            print(f"The command {repr(command)} cannot be used as axis {cmd_axis} is disabled. Ignoring...")
            return False
        
        return True

    ################################################################################
    def abort_all(self) -> None:
        """
        DriveSystem: Sends a command to abort all the motors
        """
        print( "Abort command on all axes")
        in_cmd_list = []
        for i in range(1,NUMBER_OF_MOTOR_AXES+1):
            in_cmd_list.append( self.construct_command( i, 'ab' ) )
        self.execute_several_commands(in_cmd_list,False,True)
        return

    ################################################################################
    def reset_all(self) -> None:
        """
        DriveSystem: Sends a reset command to all axes
        """
        print( "Reset commmand on all axes")
        in_cmd_list = []
        for i in range(1,NUMBER_OF_MOTOR_AXES+1):
            in_cmd_list.append( self.construct_command( i, 'rs' ) )
        self.execute_several_commands(in_cmd_list,False,True)
        return

    ################################################################################
    def reset_axis( self, axis : int ) -> None:
        """
        DriveSystem: Sends reset command to a given axis

        Parameters
        ----------
        axis : int
            The number of the axis to be reset
        """
        in_cmd = self.construct_command( axis, 'rs' )
        answer = self.execute_command( in_cmd, False, True )
        return

    ################################################################################
    def abort_axis( self, axis : int ) -> None:
        """
        DriveSystem: Sends abort command to a given axis
        
        Parameters
        ----------
        axis : int
            The number of the axis to be aborted
        """
        in_cmd = self.construct_command( axis, 'ab' )
        self.execute_command( in_cmd, False, True )
        return

    ################################################################################
    def move_absolute( self, axis : int, encoder : int ) -> None:
        """
        DriveSystem: sends move absolute command to a given axis

        Parameters
        ----------
        axis : int
            The number of the axis to be moved
        encoder : int
            The encoder position to move to
        """
        in_cmd = self.construct_command( axis, 'ma', encoder )
        self.execute_command( in_cmd, False, True )
        return

    ################################################################################
    # move relative
    def move_relative( self, axis : int, steps : int ) -> None:
        """
        DriveSystem: sends move relative command to a given axis

        Parameters
        ----------
        axis : int
            The number of the axis to be moved
        
        steps : int
            The number of encoder steps to move
        """
        print( "Moving ", steps," on axis ",str(axis) )
        in_cmd = self.construct_command( axis, 'mr', steps )
        self.execute_command( in_cmd, False, True )
        return
    
    ################################################################################
    # datum search
    def datum_search( self, axis : int ) -> None:
        """
        DriveSystem: commences a search for the datum using the in-built
        home-to-datum function

        Parameters
        ----------
        axis : int
            The number of the axis to be datum'ed
        """
        # Set this to true during experiments in case the datum is pressed accidentally
        disable = dsopts.OPTION_IS_DURING_EXPERIMENT.get_value()
        
        if disable == True:
            print(f"DATUM DISABLED. The function datum_search() is disabled. You can change this in the options file with the key \"{dsopts.OPTION_IS_DURING_EXPERIMENT.get_keyword()}\"")
            return
        
        # Start searching for the datum
        print( "Datum search on axis", axis )
    
        # Set datum mode
        # See page 7-15 of Mclennan manual
        # 00101000 -> abcdefgh
        #  a: 0 = encoder index input polarity is normal
        #  b: 0 = datum point is captured only once (i.e. after hd command)
        #  c: 1 = datum position is set to home position (SH) after datum search (HD)
        #  d: 0 = automatic direction search disabled
        #  e: 0 = automatic opposite limit search disabled
        #  f: 0 = reserved for future use
        #  g: 0 = reserved for future use
        #  h: 0 = reserved for future use
        in_cmd = self.construct_command( axis, 'dm', '00101000' )
        axis, answer = self.execute_command( in_cmd )
        print( axis, ':', answer )
    
        # Go home to datum
        in_cmd = self.construct_command( axis, 'hd' )
        axis, answer = self.execute_command( in_cmd )
        print( axis, ':', answer )

        # Display current operation
        in_cmd = self.construct_command( axis, 'co' )
        axis, answer = self.execute_command( in_cmd )
        print( axis, ':', answer )
    
        return

    ################################################################################
    def execute_command( self, in_cmd : str, format_response = True, print_output = False ) -> Tuple[Optional[str], Optional[str]]:
        """
        DriveSystem: Sends a given command to the motor control box - all commands 
        sent to motor box must go through this or "execute_several_commands"!

        Parameters
        ----------
        in_cmd : str
            The command to be sent (not formatted, as this is done automatically)
        format_response : bool (default True)
            Will apply regex to the response to separate out the axis and the answer
            from the motor box. This can slow things down somewhat...
        print_output: bool (default False)
            Will print the output from the motor control box if true

        Returns
        -------
        axis : str
            The axis number (as a string) returned by the motor control box
        response : str
            Additional information sent from the motor control box
        """
        # Check the axis is in use
        axis, cmd, num = self.deconstruct_command_from_str( in_cmd )

        # Check if axis is disabled for non-special commands
        if axis in self.disabled_axes and cmd not in DriveSystem.COMMANDS_ALWAYS_PERMITTED:
            print(f"Movement on axis {axis} disabled. Ignoring command {repr(in_cmd)}")
            return None, None
        
        # Check if axis has been paused by duty cycle
        elif axis in self.paused_axes and cmd in self.movement_commands:
            if print_output:
                print(f"Movement commands on axis {axis} are paused. Ignoring command {repr(in_cmd)}")
            return None, None

        # Send the command to the motor box
        outputline = self.serial_port_write_read( in_cmd, False )

        # Format the command if desired
        if format_response:
            # Standard command output
            pattern = re.match('.*\\r(\d*):(.*)\\r\\n', outputline, re.IGNORECASE)

            # Normal command pattern
            if pattern is not None:
                # Check if sequence
                if "Sequence" in pattern.group(2):
                    print( f"{pattern.group(1)} -> {pattern.group(2)}" )
                    self.serial_port_read_multiple_lines(True)
                    return pattern.group(1), 'See terminal'
                
                # Normal command
                if print_output:
                    print( f"{pattern.group(1)} -> {pattern.group(2)}" )
                return pattern.group(1),pattern.group(2)

            
            # Query all command pattern
            pattern = re.match('.*\\r(\d*)Mclennan(.*)', outputline, re.IGNORECASE)
            if pattern is not None:
                self.serial_port_read_multiple_lines(True)
                return pattern.group(1),'See terminal'
            
            # No response sent
            print("No response was sent")
            return None, None
                
        # Print to console if desired
        if print_output:
            print(outputline.strip('\n'))
        
        # Return command output if not formattted
        return None, outputline
            
    # ################################################################################
    def execute_several_commands( self, in_cmd_list : list, format_response = True, print_output = False ) -> Tuple[ Optional[list[str]], Optional[list[str]] ]:
        """
        DriveSystem: Sends several commands to the motor control box - all commands 
        sent to motor box must go through this or "execute_command"!

        Parameters
        ----------
        in_cmd_list : list
            The command list to be sent (not formatted, as this is done automatically)
        format_response : bool (default True)
            Will apply regex to the response to separate out the axis and the answer
            from the motor box. This can slow things down somewhat...
        print_output: bool (default False)
            Will print the output from the motor control box if true

        Returns
        -------
        axis_list : list
            The axis number (as a string) returned by the motor control box (this is
            None if unformatted)
        response_list : str
            Additional information sent from the motor control box
        """

        # Check the axis is in use
        in_cmd_decon_list = [ self.deconstruct_command_from_str(x) for x in in_cmd_list ]

        for i in range(0,len(in_cmd_decon_list)):
            # Check if axis is disabled
            if in_cmd_decon_list[i][0] in self.disabled_axes and in_cmd_decon_list[i][1] not in DriveSystem.COMMANDS_ALWAYS_PERMITTED:
                if print_output:
                    print(f"Commands on axis {in_cmd_decon_list[i][0]} disabled. Ignoring command {repr(in_cmd_list[i])}")
            # Check if axis has been paused by duty cycle
            elif in_cmd_decon_list[i][0] in self.paused_axes and in_cmd_decon_list[i][1] in self.movement_commands:
                if print_output:
                    print(f"Movement commands on axis {in_cmd_decon_list[i][0]} are paused. Ignoring command {repr(in_cmd_list[i])}")
        
        # Filter the command list
        in_cmd_list = [cmd for cmd, axis in zip(in_cmd_list, [ x[0] for x in in_cmd_decon_list ]) if axis not in self.disabled_axes ]
    
        output_list = self.serial_port_write_read_batch( in_cmd_list, False, False )
        if format_response:
            axis_list = []
            answer_list = []
            for i in range(0,len(output_list)):
                pattern = re.match('.*\\r(\d*):(.*)\\r\\n', output_list[i], re.IGNORECASE)

                if pattern is not None:
                    axis_list.append( pattern.group(1) )
                    answer_list.append( pattern.group(2) )

                else:
                    pattern = re.match('.*\\r(\d*)Mclennan(.*)', output_list[i], re.IGNORECASE)
                    if pattern is not None:
                        self.serial_port_read_multiple_lines(True)
                        # outputline = self.serial_port.readline()
                        # endline = ('').encode()
                        # while outputline != endline:
                        #     print( outputline )
                        #     outputline = self.serial_port.readline()
                        axis_list.append(pattern.group(1))
                        answer_list.append('See terminal')
                    else:
                        print("No response was sent!!!")
                        axis_list.append(None)
                        answer_list.append(None)
            if print_output:
                print("\n".join([ f"{x} -> {y}" for x,y in zip(axis_list,answer_list) ]))
            return axis_list, answer_list
        
        if print_output:
            print("".join(output_list))
        return None, output_list
    
    ################################################################################
    def print_axis_unreadable_warning( self, true_false_list : list ) -> None:
        """
        DriveSystem: static method that prints a warning if it cannot read some/all 
        of the motor axes

        Parameters
        ----------
        true_false_list : list
            A list of booleans marking whether the axis can be read (True) or cannot
            (False)
        """
        
        # Convert to list of axes - don't bother printing if axis disabled
        axis_list = [ str(i+1) for i in range(0,len(true_false_list)) if true_false_list[i] == False and i+1 not in self.disabled_axes ]
        if len(axis_list) == 0:
            return
        
        if len(axis_list) == 1:
            print(f"Could not read position of axis {axis_list[0]}")
            return
        
        comma_list_text = ", ".join( list( axis_list[0:-1] ) )
        print(f"Could not read positions of axes {comma_list_text}, and {axis_list[-1]}")
        return

    ################################################################################
    def check_encoder_pos_axis( self, axis : int ) -> bool:
        """
        DriveSystem: Sends a command to the motor box to get the current position of
        the motor. This is then sent to Grafana

        Parameters
        ----------
        axis : int
            The number of the axis to be located
        
        Returns
        -------
        axis_can_be_read : bool
            True if the axis can be read from the motor box. False otherwise.
        """
        in_cmd = self.construct_command( axis, 'oa' )
        axis, answer = self.execute_command( in_cmd )

        if answer is not None:
            self.positions[axis-1] = int( answer )
            self.send_to_influx( axis, int( answer ) )
            return True
        else:
            return False
    
    ################################################################################
    def check_encoder_pos_batch( self, selected_axes : list[int] = None ) -> list[bool]:
        """
        DriveSystem: Sends several commands to the motor box to get the current 
        position of all the motor axes. These are then sent to Grafana.

        Returns
        -------
        axis_can_be_read_list : bool
            A list where the element is True if the axis can be read from the motor
            box, and False otherwise. 
        """
        if selected_axes == None:
            axes = range(1,NUMBER_OF_MOTOR_AXES+1)
        else:
            axes = selected_axes

        in_cmd_list = [ self.construct_command(x, 'oa') for x in axes ]
        axis_list = [None]*NUMBER_OF_MOTOR_AXES
        answer_list = [None]*NUMBER_OF_MOTOR_AXES
        axis_can_be_read_list = [ False ]*NUMBER_OF_MOTOR_AXES
        
        for i in range(0,len(in_cmd_list)):
            # Check connection in case someone disconnects partway through...
            if self.check_connection():
                axis, answer = self.execute_command( in_cmd_list[i] )
                axis_list[int(axis)-1] = axis
                answer_list[int(axis)-1]= answer

        for i in range(0,len(axis_list)):
            if axis_list[i] != None and answer_list[i] != None:
                self.positions[i] = answer_list[i]
                self.send_to_influx( i+1, int( answer_list[i] ) )
                axis_can_be_read_list[i] = True
            else:
                axis_can_be_read_list[i] =  False
        
        return axis_can_be_read_list


    ################################################################################
    def send_to_influx( self, axis : int, encoder : list ) -> None:
        """
        DriveSystem: Sends an encoder position to Grafana for a given axis (if not 
        a simulation!)

        Parameters
        ----------
        axis : int
            The axis number of the motor
        encoder : int
            The encoder position of the motor
        """
        if self.push_to_grafana:
            payload = 'encoder,axis=' + str(axis) + ',name=' + str(self.grafana_axis_name[axis-1].replace(" ", "_")) + ' value=' + str(encoder)
            r = requests.post( self.grafana_url, data=payload, auth=(self.grafana_username,self.grafana_password), verify=False )
        else:
            pass

        return
    
    ################################################################################
    def get_positions(self) -> np.ndarray:
        """
        DriveSystem: A getter for the current positions of the motors

        Returns
        -------
        positions : np.ndarray
            An array of encoder positions for each motor
        """
        return self.positions

    ################################################################################
    def get_grafana_authentication(self) -> None:
        """
        DriveSystem: Gets the authentication for sending axis positions to Grafana. 
        Also checks we're not in the simulation by checking against the serial port.
        """
        # Check if we're using a simulated motor box
        if self.portalias != DEFAULT_SERIAL_PORT:
            print("Grafana disabled because this is a simulation?")
            return

        # Check we have credentials for Grafana
        if dsopts.OPTION_GRAFANA_AUTHENTICATION.get_value() == None:
            print("Could not authenticate Grafana. Will not push to Grafana.")
            return
        
        # Open the file and read each line
        try:
            with open(dsopts.OPTION_GRAFANA_AUTHENTICATION.get_value(), 'r') as file:
                # Check we capture all 3 needed items
                have_username = False
                have_password = False
                have_url = False

                # Loop over lines
                for line in file:
                    line = line.strip()
                    if line.count('->') != 1:
                        continue
                    
                    # Split at -> delimeter
                    split = line.split('->')
                    key = split[0].strip()
                    value = split[1].strip()

                    # Store authentication details
                    if key == 'username':
                        if have_username == True:
                            print('Ignoring duplicate username...')
                            continue
                        self.grafana_username = value
                        have_username = True

                    elif key == 'password':
                        if have_password == True:
                            print('Ignoring duplicate password...')
                            continue
                        self.grafana_password = value
                        have_password = True

                    elif key == 'url':
                        if have_url == True:
                            print('Ignoring duplicate url...')
                            continue
                        self.grafana_url = value
                        have_url = True
                    else:
                        print(f'Could not parse line \"{line}\"')

                # Check we have all 3 options after the end of the file
                if have_username and have_password and have_url:
                    self.push_to_grafana = True
            
                return
        
        except FileNotFoundError:
            # Print error message if file not found
            print("Could not open Grafana authentication file. Will not push to Grafana.")
        
        return

    ################################################################################
    def slit_scan_launch_threads(self, is_horz_scan = True) -> None:
        """
        TODO
        """
        # Check if we can do it if axes are disabled
        if 3 in self.disabled_axes or 5 in self.disabled_axes:
            print("Cannot slit scan when one or both axes are disabled!")
            return
        
        # First pause the DriveSystemThread, which reads ALL encoder positions every second - want some better precision on target ladder encoders
        DriveSystemThread.get_instance().pause_thread()

        # Abort everything else and only enable target ladder axes
        self.abort_all()
        print("Reset target-ladder axes")
        self.reset_axis(3)
        self.reset_axis(5)

        # Reset timers
        self.slit_scanning_check_encoder_position_timer.clear()
        self.slit_scanning_wait_at_position_timer.clear()

        # Start a thread to check the encoder positions
        self.is_slit_scanning = True
        check_encoder_pos_target_ladder_thread = threading.Thread( target=self.slit_scan_check_encoder_pos_target_ladder_thread_func )
        check_encoder_pos_target_ladder_thread.start()

        # Now run the script to move the motors on the horz/vert slit
        self.slit_scan_steps(is_horz_scan)

        # Stop the slit scan and scanning the encoder positions
        self.is_slit_scanning = False
        check_encoder_pos_target_ladder_thread.join()

        # Resume the DriveSystemThread
        DriveSystemThread.get_instance().resume_thread()
        return
    
    ################################################################################
    def slit_scan_check_encoder_pos_target_ladder_thread_func(self) -> None:
        """
        TODO
        """
        update_time = 0.2
        while self.is_slit_scanning:
            t = time.time()
            self.check_encoder_pos_batch([3,5])
            elapsed_time = time.time() - t
            self.slit_scanning_check_encoder_position_timer.wait( np.max([ update_time - elapsed_time, 0.0 ]) )
        return


    ################################################################################
    @staticmethod
    def slit_scan_read_file() -> tuple:
        """
        TODO
        """
        # Check if file exists. Return defaults if it doesn't
        filepath = dsopts.OPTION_SLIT_SCAN_PARAMETER_FILE.get_value()

        # Defaults
        mydict = {
            'OFFSET_IN_MM' : [6, False],
            'STEP_SIZE_IN_MM' : [0.1, False],
            'WAIT_TIME_IN_SECONDS': [0.5,False]
        }

        try:
            with open( filepath, 'r') as file:
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
                        print(f'SLIT SCAN OPTION ERROR: line {line_ctr} does not contain a valid option -> [{line}]')
                        continue

                    # Split line at colon
                    splitline = line.split(':')
                    key = splitline[0].strip()
                    value = splitline[1].strip()

                    # Check key and value are not empty
                    if len(key) == 0:
                        print(f'SLIT SCAN OPTION ERROR: line {line_ctr} does not contain a valid key -> [{line}]')
                        continue

                    if len(value) == 0:
                        print(f'SLIT SCAN OPTION ERROR: line {line_ctr} does not contain a valid value -> [{line}]')
                        continue

                    # Strip any comments
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    
                    # Check key exists already
                    if key not in mydict:
                        print(f'SLIT SCAN OPTION ERROR: key {key} unknown')
                        continue

                    # Warn if duplicate keys
                    if mydict[key][1]:
                        print(f'SLIT SCAN OPTION WARNING: option already set for {key}. Overwriting...')

                    # Store all found keys
                    try:
                        mydict[key] = [ float(value), True ]
                    except TypeError:
                        print(f'SLIT SCAN OPTION: could not convert {value} to a float. Will use the defaul for item {key}...')

                
        except FileNotFoundError:
            print(f"Cannot find slit scan parameters in file {repr(filepath)}. Using defaults...")

        for k, v in mydict.items():
            if v[1] == False:
                print('SLIT SCAN OPTION WARNING: option not set for {k}. Using default...')

        offset_in_mm = mydict['OFFSET_IN_MM'][0]
        step_size_in_mm = mydict['STEP_SIZE_IN_MM'][0]
        wait_time_in_seconds = mydict['WAIT_TIME_IN_SECONDS'][0]
        
        return (offset_in_mm, step_size_in_mm, wait_time_in_seconds)


    ################################################################################
    def slit_scan_steps(self, is_horz_scan = True) -> None:
        """
        TODO
        """
        # Get information from file
        offset_in_mm, step_size_in_mm, wait_time_in_seconds = self.slit_scan_read_file()

        # Set the slit as the focused element
        if is_horz_scan:
            self.selected_in_beam_element = dsdidmap.IDMap.VERT_SLIT_ID
        else:
            self.selected_in_beam_element = dsdidmap.IDMap.HORZ_SLIT_ID

        # I.E. scanning horizontally (on vertical slit)
        if is_horz_scan:
            axis_to_move = 3
            other_axis = 5
            axis_index = 0
            slit_name = 'vert_slit'
        
        # I.E. scanning vertically (on horizontal slit)
        else:
            axis_to_move = 5
            other_axis = 3
            axis_index = 1
            slit_name = 'horz_slit'
        
        # First get the location of the middle of the slit
        middle = dsopts.AXIS_POSITION_DICT[slit_name]

        # Calculate encoder positions to visit while scanning across the slit
        start_position = middle[axis_index] - offset_in_mm*MM_TO_STEP
        end_position = middle[axis_index] + offset_in_mm*MM_TO_STEP
        step_size = step_size_in_mm*MM_TO_STEP
        number_of_values = int( np.abs( (start_position - end_position)/step_size ) + 1 )
        encoder_positions = np.linspace( start_position, end_position, number_of_values, dtype=int )

        # Move to right place on axis we're not wanting to move during operation
        cmd_on_axis_that_wont_move = self.construct_command(other_axis, 'ma', middle[(axis_index + 1) % 2] )
        self.execute_command(cmd_on_axis_that_wont_move)

        # Move to starting position on axis we will move during operation
        cmd_on_axis_that_will_move = self.construct_command(axis_to_move, 'ma', encoder_positions[0] )
        self.execute_command(cmd_on_axis_that_will_move)

        # Check we make it to the starting position to begin slit scanning
        ctr_wont_move = 0
        ctr_will_move = 0
        move_axis_running = True
        no_move_axis_running = True

        print('===== PREPARING TO SCAN SLITS... ====')
        while move_axis_running or no_move_axis_running:
            # Axis that will move during slit scan - get to the right position
            if self.positions[axis_to_move-1] != encoder_positions[0] and move_axis_running:
                ctr_will_move += 1
                if ctr_will_move % 10 == 0:
                    print(f'Still moving to get to correct {"horizontal" if is_horz_scan else "vertical" } position to begin slit scanning...')
            else:
                move_axis_running = False
            
            # Axis that won't move during slit scan - get to the right position
            if self.positions[other_axis-1] != middle[(axis_index + 1) % 2] and no_move_axis_running:
                ctr_wont_move += 1
                if ctr_wont_move % 10 == 0:
                    print(f'Still moving to get to correct {"horizontal" if not is_horz_scan else "vertical" } position to begin slit scanning...')
            else:
                no_move_axis_running = False

            # Break if we've made it
            if move_axis_running == False and no_move_axis_running == False:
                break

            # Kill if we cannot move
            if ctr_wont_move >= 50 or ctr_will_move >= 50:
                print("Timeout: cannot complete slit scan as the target ladder will not move to the starting position (did you abort a motor?)")
                print('======= SLIT SCANNING FAILED ========')
                self.kill_slit_scan()
                return

            # Sleep if we've not made it yet
            time.sleep(0.2)

        # Now start visiting all the places
        print('===== SLIT SCANNING IN PROGRESS =====')
        for i in range(0,len(encoder_positions)):
            if self.is_slit_scanning:
                cmd = self.construct_command(axis_to_move, 'ma', encoder_positions[i] )
                self.execute_command(cmd)
                ctr = 0

                # While loop to try and move to the position for the next scan
                while True:
                    if self.positions[axis_to_move-1] != encoder_positions[i] or self.positions[other_axis-1] != middle[(axis_index + 1) % 2]:
                        time.sleep(0.1)
                        ctr += 1
                        if ctr % 5 == 0:
                            # Tell the user we're trying to move and re-issue the command
                            print(f'Trying to move to {slit_name} {self.slit_scan_offset_string(encoder_positions[i], middle[axis_index])}')
                            self.execute_command(cmd)
                        if ctr > 50:
                            print("Cannot complete slit scan as nothing is moving (did you abort a motor?). Stopping...")
                            print('======= SLIT SCANNING FAILED ========')
                            self.kill_slit_scan()
                            return
                    else:
                        break
                
                # Now do the scan = sitting and doing nothing
                print(f'Moved to {slit_name} {self.slit_scan_offset_string(encoder_positions[i], middle[axis_index])}')
                self.slit_scanning_wait_at_position_timer.wait(wait_time_in_seconds)
            else:
                # Essentially exit this function if someone kills the slit scan
                return
        
        print('====== SLIT SCANNING COMPLETE =======')

        return
    
    ################################################################################
    @staticmethod
    def slit_scan_offset_string( current_pos : int, slit_pos : int ):
        """
        TODO
        """
        if current_pos == slit_pos:
            return ""
        return f'{"+" if current_pos > slit_pos else "-"} {np.round( np.abs( current_pos - slit_pos )*STEP_TO_MM, 2)} mm'

    ################################################################################
    def kill_slit_scan(self) -> None:
        """
        TODO
        """
        self.is_slit_scanning = False
        self.slit_scanning_check_encoder_position_timer.set()
        self.slit_scanning_wait_at_position_timer.set()
        return
    
    ################################################################################
    def set_in_beam_element( self, id : str ) -> None:
        """
        TODO
        """
        self.selected_in_beam_element = id
        return
    ################################################################################
    def get_in_beam_element( self ) -> str:
        """
        TODO
        """
        return self.selected_in_beam_element
        


################################################################################
################################################################################
################################################################################
class DriveSystemThread(threading.Thread):
    """
    This class is a thread that checks the positions according to 
    DriveSystemOptions.update_time and runs in the background. It also pushes 
    these positions to Grafana, and  tells the GUI to update every time the position 
    is captured.
    """
    UPDATE_TIME = 1

    # Singleton properties
    instance = None
    init = False

    ################################################################################
    def __new__(self):
        """
        DriveSystemThread: Singleton class so that multiple threads are not created
        """
        if self.instance is None:
            self.instance = super().__new__(self)
        return self.instance

    ################################################################################
    def __init__(self) -> None:
        """
        DriveSystemThread: Set up the thread properties
        """
        # Return if already initialised
        if self.init:
            return
        
        # Ensure we register singleton exists
        self.init = True

        # Call parent Thread constructor
        threading.Thread.__init__(self)

        # Get instance of DriveSystem (which interfaces with motor box)
        self._driveSystem = DriveSystem.get_instance()

        # Define self as running
        self.is_running = True

        # Define a pause boolean for pausing the thread to allow other processes to take place
        self.is_paused = False

        # Check axis is readable
        self.axis_is_readable = np.zeros( (NUMBER_OF_MOTOR_AXES), dtype = bool )

        # Define an event used to kill the loop
        self.event = threading.Event()

        return

    ################################################################################
    def __del__(self) -> None:
        """
        DriveSystemThread: Delete the thread
        """
        self.init = False
        return

    ################################################################################
    def run(self) -> None:
        """
        DriveSystemThread: this is called by Thread.start(), so no need to call 
        directly. This contains the processes that take place while the thread is 
        running
        """
        # Loop while defined to be running
        while self.is_running:
            # Only send commands while the serial port is open AND the thread is not paused
            if self._driveSystem.check_connection() and self.is_paused == False:
                # Get the current time
                t = time.time()
                
                # Get the encoder positions for all the motors
                self.axis_is_readable = self._driveSystem.check_encoder_pos_batch()

                # Print warning if we cannot access a particular axis
                self._driveSystem.print_axis_unreadable_warning( self.axis_is_readable )

                # Get updated positions
                pos = self._driveSystem.get_positions() # Position in steps

                # Print positions to console
                # print( "[", ",".join( [ f'{pos[i]:>6}' if i+1 not in self._driveSystem.disabled_axes else f'{"None":>6}' for i in range(0,len(pos)) ] ), "]" )
                print( "[", ",".join( [ f'{pos[i]:>7}' if i+1 not in self._driveSystem.disabled_axes else f'{pos[i]:>6}*' for i in range(0,len(pos)) ] ), "]" )

                # Check how much time is left in which to sleep before we repeat again.
                time_elapsed = time.time() - t
                self.event.wait( np.max([self.UPDATE_TIME - time_elapsed, 0 ]) )
            else:
                # Keep thread alive but sleep if disconnected
                self.event.wait(1)
        
        return

    ################################################################################
    def kill_thread(self) -> None:
        """
        DriveSystemThread: kill the thread
        """
        self.event.set()
        self.is_running = False
        return

    ################################################################################
    @classmethod
    def get_instance(cls):
        """
        DriveSystemThread: get an instance of the singleton
        """
        if cls.instance == None:
            cls()
        return cls.instance
    
    ################################################################################
    def pause_thread(self):
        self.is_paused = True
        return
    
    ################################################################################
    def resume_thread(self):
        self.is_paused = False
        return