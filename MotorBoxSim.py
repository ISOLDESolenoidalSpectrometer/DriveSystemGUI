"""
Module for simulating the ISS motor box. Typically, a port will have to be opened using socat for using this.
"""

__version__ = 1.0

import argparse as ap
import numpy as np
import re
import threading
import time
import serial
import serialinterface

# Mock up of a motor so we can properly simulate things...
class MotorSim( threading.Thread ):
    """
    MotorSim is a thread that runs to simulate an individual motor. This can then be 
    sent off to do something and sampled at will.
    """
    TIME_STEP = 0.1

    ################################################################################
    def __init__(self, axis : int, name : str) -> None:
        """
        MotorSim: This sets up the simulation of the motor, sets some default parameters.

        Parameters
        ----------
        axis : int
            The number of the axis (for distinction from other motors)
        name : str
            The name of the motor (for distinction from other motors)
        """
        # Thread bits
        self.is_running = True
        threading.Thread.__init__(self)

        # Motor properties
        self.encoder = 0
        self.target_encoder = 0
        self.axis = axis
        self.name = name
        self.creep_speed = 100
        self.slew_speed = 2000
        self.is_aborted = False
        self.status = "STATUS"
        return
    
    ################################################################################
    def run(self) -> None:
        """
        MotorSim: this function sets up the while loop for the thread
        """
        while self.is_running:
            t0 = time.time()
            
            # Check if we need to move
            if self.target_encoder != self.encoder and self.is_aborted == False:
                # First set direction
                if self.target_encoder < self.encoder:
                    direction = -1
                else:
                    direction = 1
                
                # Calculate distance to move
                dist_step = direction*self.TIME_STEP*self.slew_speed

                # Move
                if np.abs( self.encoder - self.target_encoder ) < dist_step:
                    self.encoder = self.target_encoder
                    self.status = 'Idle (TO BE CHECKED)'
                else:
                    self.encoder = direction*self.TIME_STEP*self.slew_speed + self.encoder
            
            # If motor aborted, stop moving
            if self.is_aborted:
                self.target_encoder = self.encoder

            time_elapsed = time.time() - t0
            time.sleep( self.TIME_STEP - time_elapsed )
        
        return
    
    ################################################################################
    def move( self, new_encoder : int ) -> None:
        """
        MotorSim: this tells the motor to move somewhere new

        Parameters
        ----------
        new_encoder : int
            The desired position for the motor
        """
        self.target_encoder = new_encoder
        self.status = f'{self.axis:02d}:! MOVING TO {new_encoder}'
        return

    ################################################################################
    def set_position( self, encoder : int ) -> None:
        """
        MotorSim: this tells the motor where it is

        Parameters
        ----------
        encoder : int
            The actual position of the motor
        """
        self.encoder = encoder
        self.target_encoder = encoder
        return
    
    ################################################################################
    def abort(self) -> None:
        """
        MotorSim: this tells the motor it's not allowed to move
        """
        self.is_aborted = True
        self.status = f'{self.axis:02d}:! COMMAND ABORT'
        return
    
    ################################################################################
    def reset(self) -> None:
        """
        MotorSim: this tells the motor it's allowed to move
        """
        if self.is_aborted == False:
            self.status = f'{self.axis:02d}:! NOT ABORTED'
        else:
            self.status = f'{self.axis:02d}: RESET'
        self.is_aborted = False
        return
    
    ################################################################################
    def is_motor_aborted(self) -> bool:
        """
        MotorSim: this asks the motor if it's aborted

        Returns
        -------
        self.is_aborted : bool
            Whether the motor is aborted or not
        """
        return self.is_aborted
    

################################################################################
################################################################################
################################################################################
class MotorBoxSim(serialinterface.SerialInterface):
    """
    Simulation of the ISS motor box - all behaviour goes in the "process_command"
    function
    """
    ################################################################################
    def __init__(self, portalias = None) -> None:
        """
        Initialises object, which only requires the (hard-coded) port alias

        Parameters
        ----------
        portalias : str
            The name of the port used for communication.
        """
        if portalias == None:
            raise ValueError("Port alias must be given to proceed")
        
        super().__init__( portalias )
        self.motor_list = {
            1: MotorSim( 1, "Trolley" ),
            2: MotorSim( 2, "Array" ),
            3: MotorSim( 3, "TargetH" ),
            4: MotorSim( 4, "FC" ),
            5: MotorSim( 5, "TargetV" ),
            6: MotorSim( 6, "BlockerH" ),
            7: MotorSim( 7, "BlockerV" ),
        }

        # Start simulating motors
        for motor in self.motor_list.values():
            motor.start()
        
        return
    ################################################################################
    def get_motor( self, axis : int ) -> MotorSim:
        """
        MotorBoxSim: getter for the motors

        Parameters
        ----------
        axis : int
            The axis whose motor we wish to get

        Returns
        -------
        motor : MotorSim
            The requested motor from axis
        """
        return self.motor_list.get(axis)
    
    ################################################################################
    def set_initial_encoder_positions( self, encoder_list : list[int] ) -> None:
        """
        MotorBoxSim: sets the initial encoder positions on all the motors
        
        Parameters
        encoder_list : list[int]
            List of integers denoting encoder positions for the motors. This list
            must be the same length as the number of motors in the GUI!
        """
        
        if len(encoder_list) != len( self.motor_list.keys() ):
            raise 
            
        for motor, encoder in zip( self.motor_list.values(), encoder_list ):
            motor.set_position(encoder)
        
        return

    ################################################################################
    # Overwritten from base class - timeout changed to make it speedier
    def set_defaults( self ) -> None:
        """
        MotorBoxSim: Sets default options for the serial port, tailored to ISS
        """
        self.parity = serial.PARITY_EVEN
        self.nbits = serial.SEVENBITS
        self.baudrate = "9600"  # initial value
        self.timeout = 0.1

    ################################################################################
    def process_command(self, input : str) -> str:
        """
        MotorBoxSim: Processes an input and returns an output

        Parameters
        ----------
        input : str
            The input received from the serial port

        Returns
        -------
        output : str
            The data to be sent over the serial port (this function does not send this!)
        """
        if input == None or input == "":
            return None
        
        # PATTERN-MATCH COMMON COMMANDS
        pattern = re.match('(\d*)(\D\D)(-?\d*)\\r', input, re.IGNORECASE)
        cmd_ret = "00:! UNKNOWN COMMAND RECEIVED BY SIMULATION!"
        if pattern != None:
            if len(pattern.groups()) == 3:
                axis = int(pattern.group(1))
                cmd = pattern.group(2)
                arg = pattern.group(3)
                motor = self.get_motor(axis)
            
                # OUTPUT ACTUAL POSITION (OA)
                if cmd == 'oa':
                    cmd_ret = f'{axis:02d}:{int(motor.encoder)}' + ' '*( 12 - len(str(motor.encoder)))
                
                # MOVE ABSOLUTE (MA)
                if cmd == 'ma':
                    if motor.is_motor_aborted():
                        cmd_ret = motor.status
                    else:
                        cmd_ret = motor.status
                        motor.move(int(arg))
                
                # MOVE RELATIVE (MR)
                if cmd == 'mr':
                    if motor.is_motor_aborted():
                        cmd_ret = motor.status
                    else:
                        cmd_ret = motor.status
                        motor.move( int(arg) + motor.encoder)
                
                # ABSOLUTE POSITION (AP)
                if cmd == 'ap':
                    motor.set_position(int(arg))
                    cmd_ret = f'{axis:02d}:! OK'
                
                # ABORT (AB)
                if cmd == 'ab':
                    motor.abort()
                    cmd_ret = motor.status

                # RESET (RS)
                if cmd == 'rs':
                    if motor.is_motor_aborted():
                        motor.reset()
                    cmd_ret = motor.status
                
                # QUERY ALL (QA)
                if cmd == 'qa':
                    query_all_list = [
                        f"{axis:02d}qa\rMclennan Digiloop Motor Controller V1.04   Servo mode\r\n",
                        f"Input command: {axis}qa\r\n",
                        f"Address = {axis}                          Privilege level = 8\r\n",
                        f"Mode = {motor.status}\r\n",
                        f"Kf = ?         Kp = ????      Ks = ???       Kv = ??        Kx = ?\r\n",
                        f"Deadband = 0                         \r\n",
                        f"Slew speed = {motor.slew_speed}                     Limit decel = 20000000\r\n",
                        f"Acceleration = 1000                  Deceleration = 1500\r\n",
                        f"Creep speed = {motor.creep_speed}                    Creep steps = 0\r\n",
                        f"Jog speed = 500                      Fast jog speed = 1000\r\n",
                        f"Joystick speed = 10000               Jog Velocity Timeout = 2000\r\n",
                        f"Settling time = 100                  Backoff steps = 0\r\n",
                        f"Window = 4                           Threshold = 50 %\r\n",
                        f"Tracking = 4000                      Timeout = 8000\r\n",
                        f"Lower soft limit = -113933           Upper soft limit = 10000000\r\n",
                        f"Lower hard limit on                  Upper hard limit on\r\n",
                        f"Jog enabled                          Joystick disabled\r\n",
                        f"Gearbox ratio =     1/1              Encoder ratio = -1/1\r\n",
                        f"Display ratio =     1/1              Display Decimal Point = 0\r\n",
                        f"Command pos = 0                      Actual pos = 0\r\n",
                        f"Input pos = 0                        Home pos = 0\r\n",
                        f"Pos error = 0                        Datum pos = None\r\n",
                        f"Valid sequences: none (Autoexec disabled)\r\n",
                        f"Valid cams: none\r\n",
                        f"Valid profiles: none\r\n",
                        f"Read port: 00000000                  Last write: 00000000\r\n",
                    ]
                    return query_all_list





        # TODO - more patterns to match based on motor box commands...
        return input + cmd_ret + "\r\n"
    
    ################################################################################
    def kill(self) -> None:
        """
        MotorBoxSim: Kills all the motors so that they effectively pop out of existence
        """
        for motor in self.motor_list.values():
            motor.is_running = False


################################################################################
################################################################################
################################################################################
def parse_command_line_arguments() -> None:
    """
    Returns port number and adds a bit of structure to the script for options 
    (help and version number)

    Returns
    -------
    port : str
        The port that will be opened with which the simulation will communicate
    """
    parser = ap.ArgumentParser(prog='MotorBoxSim.py', description='Simulation of ISS motor box packaged up as a convenient python script', epilog='Could be more sophisticated...')
    parser.add_argument('--version', action='version', version=f'%(prog)s version {__version__}')
    parser.add_argument('port', nargs=1, type=str, help='This is a port address, usually something like /dev/ttyXXX', metavar='port')
    args = parser.parse_args()

    return args.port[0]
################################################################################
def main():
    """
    Simulates the ISS motor box by just opening a serial port and sending replies
    when it receives anything
    """

    port = parse_command_line_arguments()

    try:
        m = MotorBoxSim(port)
        m.set_initial_encoder_positions([  19459,-40120, 12246,-12587,     0,  2066, 14926 ])

        while True:
            m.serial_port_read_write()

    except KeyboardInterrupt:
        print("")
    
    m.kill()

    print("BYE")

if __name__ == '__main__':
    main()


#'6oa\r06:2065        \r\n'