"""
SerialInterface
===============

This creates an easy-to-use (hopefully!) interface for a motor-controlling
device that needs to connect over a serial port. This is the foundation for
both the DriveSystem class and the MotorBoxSim class.
"""
import abc
from prompt_toolkit import print_formatted_text
import serial
import threading
import time
from typing import Union, List

# Serial interface class
class SerialInterface:
    """
    Interface class for serial port communication. Tailored to match ISS motor box.

    Attributes
    ----------
    instance : SerialInterface (static variable)
        The single instance of the class
    init : bool
        Says if the single instance has been initialised
    serial_port : serial.Serial
        The serial object used for communication
    lock : threading.Lock
        A lock placed on the serial port so that multiple communications cannot happen simultaneously
    baudrate : str (of an integer)
        Something to do with serial ports
    parity : str
        Parity for the serial port. Use serial.PARITYEVEN (or similar) for this
    timeout : int
        How long before the serial port times out in seconds
    nbits : int
        The number of bits used in the serial port. Use serial.SEVENBITS (or similar) for this.
    port_open : bool
        Says if the port is open or closed
    """

    instance = None
    init = False
    sleep_time = 0.1

    ################################################################################
    @classmethod
    def get_instance(cls):
        """
        SerialInterface: Returns the single instance of the class

        Returns
        -------
        instance : SerialInterface
            The single instance of this class
        """
        if cls.instance == None:
            cls()
        return cls.instance

    ################################################################################
    def __init__(self, portalias : str) -> None:
        """
        SerialInterface: Initialise object setting defaults to match the ISS motor 
        control box interface

        Parameters
        ----------
        portalias : str
            The alias for the port over which to communicate
        """

        if self.instance != None:
            return
        
        SerialInterface.instance = self
        self.lock = threading.Lock()
        self.portalias = portalias

        # Port option lists
        self.set_defaults()
        self.serial_port = serial.Serial(
            self.portalias, 
            baudrate=self.baudrate, 
            bytesize=self.nbits, 
            parity=self.parity, 
            timeout=self.timeout
        )

        if self.serial_port.is_open == False:
            self.connect_to_port()

        return
    
    ################################################################################
    def __str__(self):
        """
        SerialInterface: Cast object to string
        """
        return f"SerialInterface object at {self.portalias}. Port is {'open' if self.serial_port.is_open else 'closed'}."

    ################################################################################
    # def __del__(self):
    #     """
    #     SerialInterface: Allow creation of a new instance
    #     """
    #     self.init = False
    #     return

    ################################################################################
    def connect_to_port( self ):
        """
        SerialInterface: Connects to the serial port with the default parameters
        """

        if self.serial_port.is_open == False:
            self.lock.acquire()
            self.serial_port.open()   
            self.lock.release()  
        
        if self.serial_port.is_open == True:
            print_formatted_text( f"Connected to {self.portalias}" )
        else:
            print_formatted_text( f"Failed to connenct to {self.portalias}" )
    

    ################################################################################
    def read(self) -> str:
        """
        SerialInterface: Default read command from serial port

        Returns
        -------
        return_value : str
            The output sent back from the serial port
        """
        return self.serial_port.readline().decode('utf8')
    
    ################################################################################
    def read_multiple_lines(self, print_each_line : bool = False) -> list[str]:
        """
        SerialInterface: Read multiple lines from the serial port

        Returns
        -------
        return_value : list[str]
            A list of strings that represent the output on the serial port.
        
        """
        return_value = []
        endline = ('').encode()
        ctr = 0
        while True:
            outputline = self.serial_port.readline()
            if outputline != endline:
                x = outputline.decode('utf8')
                if print_each_line:
                    print_formatted_text(x.rstrip('\n'))
                return_value.append(x)
            else:
                break
            ctr += 1
        return return_value
        
    
    ################################################################################
    @abc.abstractmethod
    def process_command(self, input : str) -> Union[List[str],str]:
        """
        SerialInterface: Processes an input and returns an output

        Parameters
        ----------
        input : str
            The input received from the serial port

        Returns
        -------
        output : str | list[str]
            The data to be sent over the serial port (this function does not send this!)
        """
        raise NotImplementedError
    

    ################################################################################
    def write(self, in_cmd) -> bool:
        """
        SerialInterface: Default write command to serial port

        Parameters
        ----------
        in_cmd : str
            Tne command to be written

        Returns
        -------
        function_success : bool
            False if input command is None or empty. True if it writes.
        """
        if in_cmd == None or in_cmd == "":
            return False
        self.serial_port.write( in_cmd.encode() )
        return True


    ################################################################################
    def serial_port_write_read_no_lock( self, in_cmd : str, print_in_cmd = True ) -> str:
        """
        SerialInterface: Send command and receive line back *without locking port*. 
        Optionally print command to console.

        Parameters
        ----------
        in_cmd : str
            The command to be sent over the serial port
        print_in_cmd : bool, default: True
            Optionally print command to console.
        
        Returns
        -------
        outputline : str
            The result from the serial port as a string
        """
        if self.serial_port.is_open:
            if print_in_cmd:
                print_formatted_text( 'WRITE: ', repr(in_cmd) )
            self.write(in_cmd)
            time.sleep(self.sleep_time)
            return self.read()
        else:
            return ""
        
    ################################################################################
    def serial_port_read_multiple_lines_no_lock( self, print_out_result : bool = False ) -> list[str]:
        """
        SerialInterface: Send command and receive multiple lines back *without 
        locking port*. 
        Optionally print command to console.

        Parameters
        ----------
        print_out_result : bool, default : False
            Optionally print result to console
        
        Returns
        -------
        output_list : str
            The result from the serial port as a string
        """
        if self.serial_port.is_open:
            return self.read_multiple_lines(print_out_result)
        else:
            return [""]
        
    ################################################################################
    def serial_port_read_multiple_lines( self, print_out_result : bool = False ) -> list[str]:
        """
        SerialInterface: Send command and receive multiple lines back with port
        locking
        Optionally print command to console.

        Parameters
        ----------
        print_out_result : bool, default : False
            Optionally print result to console
        
        Returns
        -------
        output_list : str
            The result from the serial port as a string
        """
        self.lock.acquire()
        output_list = self.serial_port_read_multiple_lines_no_lock( print_out_result )
        self.lock.release()
        return output_list
        
    ################################################################################
    def serial_port_write_read( self, in_cmd : str, print_in_cmd = True ) -> str:
        """
        SerialInterface: Send command and receive line back, with port locking. 
        Optionally print command to console.

        Parameters
        ----------
        in_cmd : str
            The command to be sent over the serial port
        print_in_cmd : bool, default: True
            Optionally print command to console.
        
        Returns
        -------
        outputline : str
            The result from the serial port as a string
        
        """
        self.lock.acquire()
        outputline = self.serial_port_write_read_no_lock( in_cmd, print_in_cmd )
        self.lock.release()
        return outputline
    
    ################################################################################
    def serial_port_write_read_batch( self, in_cmd_list : list[str], print_in_cmd = True, print_out_cmd = True ) -> list:
        """
        SerialInterface: Acquires the lock, then writes a series of things to the
        serial port

        Parameters
        ----------
        in_cmd_list : list[str]
            List of strings for things to write to the serial port
        print_in_cmd : bool
            Determines whether the input to the serial port is printed to the 
            console
        print_out_cmd : bool
            Determines whether the response from the serial port is printed to
            the console

        Returns
        -------
        output_list: list[str]
            The list of responses from the serial port
        """
        output_list = []
        self.lock.acquire()
        for i in range(0,len(in_cmd_list)):
            output_list.append( self.serial_port_write_read_no_lock( in_cmd_list[i], print_in_cmd ) )
            if print_out_cmd == True:
                print_formatted_text(output_list[i])

        self.lock.release()
        return output_list
    
    ################################################################################
    def serial_port_read_write_no_lock( self, print_output = True ):
        """
        SerialInterface: Receive command and send processed command back *without
        locking port*. Optionally print command to console.

        Parameters
        ----------
        print_output : bool, default: True
            Optionally print processed output to be returned to console. It does not print NoneType objects or empty objects
        """
        input = self.read()
        output = self.process_command(input)
        if type(output) == list:
            for i in range(0,len(output)):
                if print_output and output[i] != "" and output[i] != None:
                    print_formatted_text('WRITE: ', repr(output[i]))
                self.write(output[i])
                time.sleep(self.sleep_time)
        else:
            if print_output and output != "" and output != None:
                print_formatted_text( 'WRITE: ', repr(output) )
            self.write(output)
        return
        
    
    ################################################################################
    def serial_port_read_write( self, print_output = True ):
        """
        SerialInterface: Receive command and send processed command back that locks 
        port. Optionally print command to console.

        Parameters
        ----------
        print_output : bool, default: True
            Optionally print processed output to be returned to console
        """
        self.lock.acquire()
        self.serial_port_read_write_no_lock(print_output)
        self.lock.release()
        return
    
    
    ################################################################################
    def set_defaults( self ):
        """
        SerialInterface: Sets default options for the serial port, tailored to ISS
        """
        self.parity = serial.PARITY_EVEN
        self.nbits = serial.SEVENBITS
        self.baudrate = "9600"  # initial value
        self.timeout = 3
    
    ################################################################################
    def check_connection( self ):
        """
        SerialInterface: Getter for checking if the port is open, which acquires the
        lock first, so that nothing can close it simultaneously.
        """
        self.lock.acquire()
        X = self.serial_port.is_open
        self.lock.release()
        return X
    

    ################################################################################
    def disconnect_port( self ):
        """
        SerialInterface: Closes the port
        """
        self.lock.acquire()
        if self.serial_port.is_open == True:
            self.serial_port.close()# close the port
        self.lock.release()

        if self.serial_port.is_open == False:
            print_formatted_text( f"Disconnected from {self.portalias}" )
        else:
            print_formatted_text(f"Failed to close {self.portalias}")
    

    