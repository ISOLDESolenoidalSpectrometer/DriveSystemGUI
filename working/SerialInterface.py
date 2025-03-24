import abc
import serial
import threading
import time

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
    # parityodd
    # parityeven
    # paritynone
    # bit7on
    # bit8on
    instance = None
    init = False

    ###############################################################################
    def __new__(cls):
        """
        Define new instance as singleton

        Returns
        -------
        cls.instance : SerialInterface
            The (single) instance of the class
        """
        if cls.instance is None:
            cls.instance = object.__new__(cls)
        return cls.instance
    

    ###############################################################################
    def __init__(self, portalias : str):
        """
        Initialise object setting defaults to match the ISS motor control box interface

        Parameters
        ----------
        portalias : str
            The alias for the port over which to communicate
        """
        if self.init:
                return
        self.init = True
        self.serial_port = serial.Serial()
        self.lock = threading.Lock()
        self.port_open = False
        self.portalias = portalias

        # Port option lists
        self.set_defaults()
        if self.serial_port.is_open == True:
            print("Already connected to" + self.portalias)
        else:
            self.connect_to_port()


    ###############################################################################
    def __del__(self):
        """
        Allow creation of a new instance
        """
        self.init = False


    ###############################################################################
    def read(self):
        """
        Default read command from serial port
        """
        return self.serial_port.readline().decode('utf8')
    
    ###############################################################################
    @abc.abstractmethod
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
        raise NotImplementedError
    

    ###############################################################################
    def write(self, in_cmd) -> bool:
        """
        Default write command to serial port

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


    ###############################################################################
    def serial_port_write_read_no_lock( self, in_cmd : str, print_in_cmd = True ) -> str:
        """
        Send command and receive line back *without locking port*. Optionally print command to console.

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
        if print_in_cmd:
            print( 'WRITE: ', repr(in_cmd) )
        self.write(in_cmd)
        time.sleep(0.1)
        return self.read()
        
    
    ###############################################################################
    def serial_port_write_read( self, in_cmd : str, print_in_cmd = True ) -> str:
        """
        Send command and receive line back, with port locking. Optionally print command to console.

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
    
    ###############################################################################
    def serial_port_read_write_no_lock( self, print_output = True ):
        """
        Receive command and send processed command back *without locking port*. Optionally print command to console.

        Parameters
        ----------
        print_output : bool, default: True
            Optionally print processed output to be returned to console. It does not print NoneType objects or empty objects
        """
        input = self.read()
        output = self.process_command(input)
        if print_output and output != "" and output != None:
            print( 'WRITE: ', repr(output) )
        self.write(output)
        return
        
    
    ###############################################################################
    def serial_port_read_write( self, print_output = True ):
        """
        Receive command and send processed command back that locks port. Optionally print command to console.

        Parameters
        ----------
        print_output : bool, default: True
            Optionally print processed output to be returned to console
        """
        self.lock.acquire()
        self.serial_port_read_write_no_lock(print_output)
        self.lock.release()
        return
    
    
    ###############################################################################
    def set_defaults( self ):
        """
        Sets default options for the serial port, tailored to ISS
        """
        # self.seteven()
        # self.set7()
        self.parity = serial.PARITY_EVEN
        self.nbits = serial.SEVENBITS
        self.baudrate = "9600"  # initial value
        self.timeout = 3
    

    ###############################################################################
    def connect_to_port( self ):
        """
        Connects to the serial port with the default parameters
        """
        self.port_open = False
        self.parity=self.parity
        self.serial_port.port = self.portalias              # set name of port
        self.serial_port.baudrate = int( self.baudrate )    # set baud rate
        self.serial_port.parity = self.parity               # set parity
        self.serial_port.bytesize = self.nbits              # set bytesize
        self.serial_port.timeout = self.timeout             # set timeout
        self.serial_port.open()                             # open the port
        
        if self.serial_port.is_open == True:
            print( f"Connected to {self.portalias}" )
            self.port_open = True
        else:
            print( f"Failed to connenct to {self.portalias}" )
            self.port_open = False
    

    ###############################################################################
    def check_connection( self ):
        """
        Getter for checking if the port is open
        """
        return self.port_open
    

    ###############################################################################
    def disconnect_port( self ):
        """
        Closes the port
        """
        self.port_open = False
        self.serial_port.close()# close the port
        print( "Disconnected" )

    # set the parity to even
    # def seteven( self ):
    #     self.parity=serial.PARITY_EVEN
    #     # self.parityodd=0
    #     # self.parityeven=1
    #     # self.paritynone=0
    
    # set the parity to odd
    # def setodd( self ):    
    #     self.parity=serial.PARITY_ODD
        # self.parityodd=1
        # self.parityeven=0
        # self.paritynone=0
    
    # set the parity to none
    # def setnone( self ):
    #     self.parity=serial.PARITY_NONE
        # self.parityodd=0
        # self.parityeven=0
        # self.paritynone=1
    
    # set the number of bits to 7
    # def set7( self ):
    #     self.nbits=serial.SEVENBITS
        # self.bit7on=1
        # self.bit8on=0
    
    # set the number of bits to 8
    # def set8( self ):
    #     self.nbits=serial.EIGHTBITS
        # self.bit7on=0
        # self.bit8on=1
    

    ###############################################################################
    @classmethod
    def get_instance(cls):
        """
        Returns the single instance of the class

        Returns
        -------
        instance : SerialInterface
            The single instance of this class
        """
        if cls.instance == None:
            cls()
        return cls.instance