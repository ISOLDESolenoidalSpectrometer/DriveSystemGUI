from SerialInterface import *
import re

# Mock up of a motor so we can properly simulate things...TODO
class MotorSim:
    pass


class MotorBoxSim(SerialInterface):
    """
    Simulation of the ISS motor box - all behaviour goes in the "process_command" function
    """
    ###############################################################################
    def __init__(self):
        """
        Initialises object, which only requires the (hard-coded) port alias
        """
        SerialInterface.__init__( self, "/dev/ttys011" )

    ###############################################################################
    # Overwritten from base class - timeout changed to make it speedier
    def set_defaults( self ):
        """
        Sets default options for the serial port, tailored to ISS
        """
        # self.seteven()
        # self.set7()
        self.parity = serial.PARITY_EVEN
        self.nbits = serial.SEVENBITS
        self.baudrate = "9600"  # initial value
        self.timeout = 0.05

    ###############################################################################
    def process_command(self, input : str) -> str:
        """
        Processes an input and returns an output

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
        pattern = re.match('(\d*)(\D\D)(\d*)\\r', input, re.IGNORECASE)
        cmd_ret = "00:! UNKNOWN COMMAND RECEIVED BY SIMULATION!"

        if len(pattern.groups()) == 3:
            axis = int(pattern.group(1))
            cmd = pattern.group(2)
            arg = pattern.group(3)
        
            if cmd == 'oa':
                cmd_ret = f'{axis:02d}:1000        '
            

        # TODO - more patterns to match based on motor box commands...
        
        return input + cmd_ret + "\r\n"



def main():
    """
    Simulates the ISS motor box by just opening a serial port and sending replies when it receives anything
    """
    try:
        m = MotorBoxSim()

        while True:
            m.serial_port_read_write()

    except KeyboardInterrupt:
        print("")

    print("BYE")

if __name__ == '__main__':
    main()


#'6oa\r06:2065        \r\n'