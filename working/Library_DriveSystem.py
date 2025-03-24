import time #for time.sleep()
import re #Real Expressions -> interpret the drive system's command
import requests
import urllib3
urllib3.disable_warnings()
import numpy as np
import queue
import threading
import wx
from filelock import FileLock, Timeout

from SerialInterface import *

# POD Class for holding info about GUI axes
class GUIMotorAxis:
    def __init__(self, description : str, width : float, height : float, colour : str, axis_number : int ):
        self.description = description
        self.width = width             
        self.height = height           
        self.colour = colour           
        self.axis_number = axis_number 

# ENCODER PARAMETERS
mm2step = 200
step2mm = 1./mm2step

# SOURCE DIRECTORY FOR VARIOUS THINGS
SOURCE_DIRECTORY = "/home/isslocal/DriveSystemGUI"
DRIVE_SYSTEM_LOCK = FileLock("/home/isslocal/DriveSystemGUI/.drive_system_serial_port.lock", timeout=1 )
SERIAL_PORT = "/dev/ttyS0"

# AXIS DEFINITIONS
# () = abbreviation used throughout, [] = Patrick's tape colour
# axis 1: Target carriage                   (TC)   [red]
# axis 2: Array                             (Arr)  [green]
# axis 3: Target ladder, horizontal         (TLH)  [yellow]
# axis 4: Faraday cup/Zero degree detectors (Det)  [black]
# axis 5: Target ladder, vertical           (TLV)  [brown]
# axis 6: Beam blocker, horizontal          (BBH)  [grey]
# axis 7: Beam blocker, vertical            (BBV)  [white]
number_of_motor_axes = 7
axis_labels = ['Target carriage', 
               'Array', 
               'Target ladder (H)', 
               'FC/ZD',
               'Target ladder (V)',
               'Beam blocker (H)',
               'Beam blocker (V)']

# DICTIONARY/GUI DEFINITIONS
#           'key':               'descript.',          Width  Height Colour     axis
axisdict = {'SiA': GUIMotorAxis( 'Si array',            610.0,  35.0, '#FD3F0D', 0 ),
            'TaC': GUIMotorAxis( 'Target carriage',     450.0, 270.0, '#0DE30B', 1 ),
            'ArC': GUIMotorAxis( 'Array bed',           350.0, 195.0, '#FDD11F', 2 ),
            'TLH': GUIMotorAxis( 'Targ ladder H',        80.0, 130.0, '#00A7FA', 3 ),
            'Det': GUIMotorAxis( 'Diagnostic Detectors', 80.0, 130.0, '#910BE3', 4 ),
            'TLV': GUIMotorAxis( 'Target ladder V',     217.0, 309.4, '#00A7FA', 5 ),
            'BBH': GUIMotorAxis( 'Beam blocker H',       80.0, 130.0, '#910BE3', 6 ),
            'BBV': GUIMotorAxis( 'Beam blocker V',      169.5, 123.0, '#910BE3', 7 )}

# ABSOLUTE POSITIONS OF AXES FOR TARGETS
axisposdict = {'bb.small' : [50,-90]}
#from savedpositions import axisposdict
#               'bm.fc' : ['Det',90]}

# Frequency for the positons checking (seconds)
UPDATE_TIME = 1
REAC_TIME   = 0.1

# This class interfaces directly with the motor serial port
class DriveSystem(SerialInterface):
    NUM_AXES = 7
    def __init__(self):
        SerialInterface.__init__(self, SERIAL_PORT)
        self.positions = np.zeros( self.NUM_AXES, dtype=int )
        self.grafana_axis_name = ['Trolley', 'Array', 'Target H', 'FC', 'Target V', 'Blocker H', 'Blocker V']
        self.motor_options = [ MotorOptions(x) for x in range(0,self.NUM_AXES)]

        # SerialInterface.__init__("/dev/ttyS0")
    
    @staticmethod
    def construct_command( axis, key, number = "" ):
        return f"{axis}{key}{number}\r"

    def abort_all(self):
        print( "Abort command on all axes")
        in_cmd_list = []
        for i in range(7):
            axis=i+1
            in_cmd_list.append( self.construct_command( axis, 'ab' ) )
        self.serial_port_write_read_batch( in_cmd_list, False, True )

    def reset_all(self):
        print( "Reset commmand on all axes")
        in_cmd_list = []
        for i in range(7):
            axis=i+1
            in_cmd_list.append( self.construct_command( axis, 'rs' ) )
        self.serial_port_write_read_batch( in_cmd_list, False, True )

    def reset_axis( self, axis ):
        in_cmd = self.construct_command( axis, 'rs' )
        outputline = self.serial_port_write_read( in_cmd )
        print( outputline )

    def abort_axis( self, axis ):
        in_cmd = self.construct_command( axis, 'ab' )
        outputline = self.serial_port_write_read( in_cmd )
        print( outputline )

    def move_absolute( self, axis, pos ):
        in_cmd = self.construct_command( axis, 'ma', pos )
        outputline = self.serial_port_write_read( in_cmd, False )
        print( in_cmd.rstrip('\r') + f": Moving to position {pos} on axis {axis} -> {outputline}" )

    # move relative
    def move_relative( self, axis, steps ):
        print( "Moving ", steps," on axis ",str(axis) )
        in_cmd = self.construct_command( axis, 'mr', steps )
        outputline = self.serial_port_write_read( in_cmd, False )
        print( outputline )
        
    # datum search
    def datum_search( self, axis ):
        
        #Set this to true during experiments in case the datum is pressed accidentally.
        disable = False                
        
        if disable == True:
            print( "DISABLED.\nThe function datum_search() is disabled.\nYou can change this in ~/DriveSystem/Library_DriveSystem.py ")
        
        elif disable == False:
            print( "Datum search on axis", axis )
            
            # Set acceleration
            in_cmd = self.construct_command( axis, 'sa', 500 )
            outputline = self.serial_port_write_read( in_cmd )
            print( outputline )
            time.sleep(0.1)
        
            # Set deceleration
            in_cmd = self.construct_command( axis, 'sd', 1000 )
            outputline = self.serial_port_write_read( in_cmd )
            print( outputline )
            time.sleep(0.1)
        
            # Set velocity
            in_cmd = self.construct_command( axis, 'sv', 1000 )
            outputline = self.serial_port_write_read( in_cmd )
            print( outputline )
            time.sleep(0.1)
        
            # Set creep
            in_cmd = self.construct_command( axis, 'sc', 200 )
            outputline = self.serial_port_write_read( in_cmd )
            print( outputline )
            time.sleep(0.1)
        
            #Set datum mode
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
            outputline = self.serial_port_write_read( in_cmd )
            print( outputline )
            time.sleep(0.1)
        
            # Go home to datum
            in_cmd = self.construct_command( axis, 'hd' )
            outputline = self.serial_port_write_read( in_cmd )
            print( outputline )
            time.sleep(0.1)

            # Check position
            self.check_encoder_pos_axis(axis)

            # Display current operation
            in_cmd = self.construct_command( axis, 'co' )
            outputline = self.serial_port_write_read( in_cmd )
            print( outputline )
            time.sleep(0.1)
        
            # Check position
            self.check_encoder_pos_axis(axis)

    # write info
    # Returns axis and answer
    def execute_command( self, in_cmd ):
    
        outputline = self.serial_port_write_read( in_cmd, False )
        print( "RECEIVED OUTPUT: " + repr(outputline) )
#        outputline = "7co\r07:! ENCODER ABORT\r\n"
        pattern = re.match('.*\\r(\d*):(.*)\\r\\n', outputline, re.IGNORECASE)

        if pattern is not None:
            #self.axis_now.set( pattern.group(1) )
            #self.out_now.set( pattern.group(2) )
            return pattern.group(1),pattern.group(2)

        else:
            pattern = re.match('.*\\r(\d*)Mclennan(.*)', outputline, re.IGNORECASE)
            if pattern is not None:
                outputline = self.serial_port.readline()
                endline = ('').encode()
                while outputline != endline:
                    print( outputline )
                    outputline = self.serial_port.readline()
                return pattern.group(1),'info in terminal'
            else:
                print("No response was sent")
                return None,None
            
    @staticmethod
    def print_axis_unreadable_warning( true_false_list ):
        # Convert to list of axes
        axis_list = [ str(i+1) for i in range(0,len(true_false_list)) if true_false_list[i] == False ]
        if len(axis_list) == 0:
            return
        
        if len(axis_list) == 1:
            print(f"Could not read position of axis {axis_list[[0]]}")
            return
        
        comma_list_text = ", ".join( list( axis_list[0:-1] ) )
        print(f"Could not read positions of axes {comma_list_text}, and {axis_list[-1]}")

    # check encoder positions
    def check_encoder_pos( self ):
        axis_unreadable = []
        for i in range(0,number_of_motor_axes):
            if self.check_encoder_pos_axis(i+1) == False:
                axis_unreadable.append( i+1 )
        
        self.print_axis_unreadable_warning(axis_unreadable)

        return self.positions

    # check encoder positions - returns True if it works, False if it doesn't
    def check_encoder_pos_axis( self, axis ):
        dummy_response = False
        in_cmd = '%doa\r' % axis

        if dummy_response:
            self.lock.acquire()
            outputline = str(axis) + "oa\\r0" + str(axis) + ":0.\\r\\n"
            self.lock.release()
        else:
            outputline = self.serial_port_write_read( in_cmd, False )

        pattern = re.match('.*\\r(\d*):(-?\d*).*\\r\\n', outputline, re.IGNORECASE)

        if pattern is not None:
            # print(outputline, pattern.groups())
            self.positions[axis-1] = int( pattern.group(2) )
            #self.enc_disp_txt[axis-1].set( ('%d: %d' % ( axis, int( pattern.group(2) ) ) ) )
            self.send_to_influx( axis, int( pattern.group(2) ) )
            return True
        else:
            return False

    # send positions to InfluxDB
    def send_to_influx( self, axis, pos ):
        if self.portalias == "/dev/ttyS0":
            payload = 'encoder,axis=' + str(axis) + ',name=' + str(self.grafana_axis_name[axis-1].replace(" ", "_")) + ' value=' + str(pos)
            r = requests.post( 'https://dbod-iss.cern.ch:8080/write?db=positions', data=payload, auth=("admin","issmonitor"), verify=False )
        else:
            pass


    

# position update:
myEVT_POSUPDATE = wx.NewEventType()
EVT_POSUPDATE   = wx.PyEventBinder(myEVT_POSUPDATE, 1)
class PosUpdateEvent(wx.PyCommandEvent):
    """Event to signal that a count value is ready"""
    def __init__(self, etype, eid, value=None):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """Returns the value from the event.
        @return: the value of this event

        """
        return self._value
        
# disconnect
myEVT_DISCONNECT = wx.NewEventType()
EVT_DISCONNECT   = wx.PyEventBinder(myEVT_DISCONNECT, 1)
class DisConnectEvent(wx.PyCommandEvent):
    """Event to signal that a count value is ready"""
    def __init__(self, etype, eid, value=None):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """Returns the value from the event.
        @return: the value of this event

        """
        return self._value



# Element definition for the queue
class Element:
    def __init__(self, mode,ax=None,cmd=None):
        self.mode = mode
        self.axis = ax
        self.command=cmd
    
    def __str__(self):
        return f"ELEMENT -> Mode: {self.mode} • Axis: {self.axis} • Command: {self.command}"


# This class is a thread that checks the positions according to UPDATE_TIME
class DriveSystemThread(threading.Thread):
        instance = None
        init = False
        q = queue.Queue()
        q_lock = threading.Lock()

        def __new__(self):
            if self.instance is None:
                self.instance = super().__new__(self)
            return self.instance

        def __init__(self):
            """
            @param parent: The gui object that should recieve the value
            @param value: value to 'calculate' to
            """
            if self.init:
                return
            
            self.init = True
            threading.Thread.__init__(self)
            self._driveSystem = DriveSystem.get_instance()
            self.is_running = True
            self.axis_is_aborted = np.zeros( (number_of_motor_axes), dtype = bool )
            self.axis_is_readable = np.zeros( (number_of_motor_axes), dtype = bool )
            self.is_gui_running = False
            
            self.print_request = False

        def __del__(self):
            self.init = False

        def run(self):
            """Overrides Thread.run. Don't call this directly its called internally
            when you call Thread.start().
            """
            while self.is_running:
                t = 0
                # Only run while serial port is open
                if self._driveSystem.check_connection():
                    if self.axis_is_aborted.all() == False:
                        # Check positions of axes that aren't aborted
                        for i in range(0,number_of_motor_axes):
                                if self.axis_is_aborted[i] == False:
                                        self.axis_is_readable[i] = self._driveSystem.check_encoder_pos_axis(i+1)

                        # Print warning if we cannot access axis
                        self._driveSystem.print_axis_unreadable_warning( self.axis_is_readable )

                        # Store updated positions
                        pos = self._driveSystem.positions # Position in steps

                        # Update posvispanel in GUI
                        if self.is_gui_running:
                            event = PosUpdateEvent(myEVT_POSUPDATE, wx.ID_ANY, pos)
                            wx.PostEvent(self.posvispanel, event)

                    # Check if we should print positions
                    if self.print_request == True: # Print positions when print Button was pressed
                        for i in range(0,number_of_motor_axes):
                            print( f"Axis {i+1}: {pos[i]}" )
                            self.print_request = False

                    # Process other things before checking again
                    while t < UPDATE_TIME:
                        self.checkQ()
                        time.sleep(REAC_TIME)
                        t=t+REAC_TIME
                else:
                    # Keep thread alive but sleep if disconnected
                    time.sleep(1)
                

        def checkQ(self): # Whilst q isn't empty, action it. Is "q" queue?
            while self.q.empty()==False:
                item = self.q.get()
                self.action(item)
                self.q.task_done()
        
        def add_to_queue(self,element):
            with self.q_lock:
                self.q.put(element)

        def action(self,element): # Decide how to action depending on element
            if element.mode=='Q':
                self.is_running = False

            elif element.mode=='S':
                command = element.command
                print("SENDING COMMAND " + repr(command))
                ax,answer=self._driveSystem.execute_command(command)
                if ax != None:
                    # self._driveSystem.currentAx.SetValue(ax) ##What is this???
                    self.controlview.currentAx.SetValue(ax)
                    self.controlview.currentAx.Update()
                if answer != None:
                    self.controlview.commandResponse.SetValue(answer)
                    self.controlview.commandResponse.Update()
                else:
                    self.controlview.commandResponse.SetValue("NO RESPONSE")
                    self.controlview.commandResponse.Update()

                    #self._parent.sendingCommand(element.command) ## What is this???

            elif element.mode=='M+-': # Relative move
                steps=element.command
                self._driveSystem.move_relative(element.axis,steps)
                print('MOVING '+str(element.axis)+' '+str(steps)+' steps')

            elif element.mode=='H': # home
                self._driveSystem.datum_search(element.axis)

            elif element.mode=='C':
                self._driveSystem.connect_to_port()
                event = DisConnectEvent(myEVT_DISCONNECT, -1, 1)
                wx.PostEvent(self.controlview, event)

            elif element.mode=='D':
                self._driveSystem.disconnect_port()
                event = DisConnectEvent(myEVT_DISCONNECT, -1, 0)
                wx.PostEvent(self.controlview, event)

            else: # For pre-determined positions
                if re.search('[0-9].[0-9].[0-9]',str(element.mode)): # isTarget:
                    print('TARGET SELECTED: '+str(element.mode))
                    self._driveSystem.move_absolute(axisdict['TLH'].axis_number,axisposdict[str(element.mode)][0])
                    self._driveSystem.move_absolute(axisdict['TLV'].axis_number,axisposdict[str(element.mode)][1])
                elif re.search('\*_slit',str(element.mode)) or re.search('[*]_aperture',str(element.mode)): # isHoles
                    # NOTE: this could be as above, as holes are just "targets"
                    print('SLIT/APERTURES  SELECTED: '+str(element.mode))
                    self._driveSystem.move_absolute(axisdict['TLH'].axis_number,axisposdict[str(element.mode)][0])
                    self._driveSystem.move_absolute(axisdict['TLV'].axis_number,axisposdict[str(element.mode)][1])
                elif re.search('bb.*',str(element.mode)): # isBeamblocker
                    print('BEAM BLOCKER  SELECTED: '+str(element.mode))
                    self._driveSystem.move_absolute(axisdict['BBH'].axis_number,axisposdict[str(element.mode)][0])
                    self._driveSystem.move_absolute(axisdict['BBV'].axis_number,axisposdict[str(element.mode)][1])
                elif re.search('bm.*',str(element.mode)): # isBeammonitor
                    print('BEAM DETECTOR SELECTED: '+str(element.mode))
                    self._driveSystem.move_absolute(axisdict['Det'].axis_number,axisposdict[str(element.mode)][0])
                else:
                    print( f"??? {element.mode}" )

        def kill_thread(self):
            element=Element('Q')
            self.add_to_queue(element)

        def set_axis_aborted(self, axis):
            self.axis_is_aborted[axis-1] = True

        def set_axis_reset(self, axis):
            self.axis_is_aborted[axis-1] = False
        
        @classmethod
        def get_q(cls):
            return cls.q
        
        def send_print_request(self):
            self.print_request = True

        # GUI-specific
        def set_posvispanel(self, posvispanel ):
            self.posvispanel = posvispanel

        def set_controlview(self, controlview ):
            self.controlview = controlview

        @classmethod
        def get_instance(cls):
            if cls.instance == None:
                cls()
            return cls.instance

class MotorOptions():
    def __init__(self, axis):
        self.creep_speed = None
        self.slew_speed = None
        self.acceleration = None
        self.deceleration = None
        self.axis = None

    def set_creep_speed( self, x : int ):
        self.creep_speed = x
    def set_slew_speed( self, x : int ):
        self.slew_speed = x
    def set_slew_speed( self, x : int ):
        self.slew_speed = x
    def set_acceleration( self, x : int ):
        self.acceleration = x
    def set_deceleration( self, x : int ):
        self.deceleration = x

    def get_creep_speed( self ) -> int:
        return self.creep_speed
    def get_slew_speed( self ) -> int:
        return self.slew_speed
    def get_slew_speed( self ) -> int:
        return self.slew_speed
    def get_acceleration( self ) -> int:
        return self.acceleration
    def get_deceleration( self ) -> int:
        return self.deceleration
        
