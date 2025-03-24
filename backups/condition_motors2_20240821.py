#!/usr/bin/env python3
import serial
import re
import threading
import time
import queue
import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PORTALIAS = "/dev/ttyS0"
SERIAL_PORT = serial.Serial()
SERIAL_PORT_LOCK = threading.Lock()

def get_command_result( X ):
    pattern = re.match( '.*\\r(\d*):(.*)\\r\n', X, re.IGNORECASE )

    if pattern != None:
        return pattern.group(2)
    
    outputlines = ["QUERY ALL INITIATED\r"]
    pattern = re.match('.*\\r(\d*)Mclennan(.*)', X, re.IGNORECASE)
    if pattern != None:
        line = SERIAL_PORT.readline().decode()
        endline = ''
        while line != endline:
            outputlines.append( line )
            line = SERIAL_PORT.readline().decode()
        return outputlines
    else:
        return None
    
def send_command( cmd ):
    SERIAL_PORT_LOCK.acquire()
    SERIAL_PORT.write( cmd.encode() )
    time.sleep(0.1)
    a = get_command_result( SERIAL_PORT.readline().decode() )
    time.sleep(0.1)
    SERIAL_PORT_LOCK.release()
    return a

def construct_command( axis, key, number = "" ):
    return f"{axis}{key}{number}\r"

###############################################################################
class Grafana( threading.Thread ):
    def __init__(self, axes_list, axes_name_list):
        self.is_running = True
        threading.Thread.__init__(self)
        self.axes_list = axes_list
        self.axes_name_list = axes_name_list
        self.q = queue.Queue()
        self.UPDATE_TIME = 0.5
        self.REAC_TIME = 0.1
        self.pos = [0]*len(axes_list)

    def run(self):
        while self.is_running:
            t = 0
            for i in range(0,len(self.axes_list)):
                pos = send_command( construct_command(self.axes_list[i], "oa") )
                if pos != "None" and pos != None:
                    self.q.put( [int(pos), str(self.axes_list[i]), str(self.axes_name_list[i])] )
                    self.pos[i] = pos
            
            while t < self.UPDATE_TIME:
                self.checkQ()
                time.sleep(self.REAC_TIME)
                t = t + 0.1
    
    # Only should be called by checkQ function!!
    def push_to_grafana(self, pos, axis, name ):
        payload = 'encoder,axis=' + axis + ',name=' + name + ' value=' + str(pos)
        r = requests.post( 'https://dbod-iss.cern.ch:8080/write?db=positions', data=payload, auth=("admin","issmonitor"), verify=False )

    def checkQ(self):
        while self.q.empty() == False:
            item = self.q.get()
            self.push_to_grafana( *item )
            self.q.task_done()

    def get_pos(self,axis):
        return self.pos[self.axes_list.index(axis)]

###############################################################################
class ConditionMotorsThread( threading.Thread ):
    sign = "+"

    def __init__(self,axisnumber, axisname, print_indent = ""):
        self.is_running = True
        threading.Thread.__init__(self)
        self.AXIS = axisnumber
        self.AXISNAME = axisname
        self.STATUS_CMD = construct_command( self.AXIS, "co" )
        self.POS_CMD = construct_command( self.AXIS, "oa" )
        self.RESET_CMD = construct_command( self.AXIS, "rs" )
        self.print_indent = print_indent

        self.negative_limit = None
        self.positive_limit = None
        self.creep_speed_negative = None
        self.creep_speed_positive = None
        self.slew_speed_negative = None
        self.slew_speed_positive = None
        self.grafana_thread = None
        
        self.print = False
    
    def set_speeds( self, creep, slew, creep2 = None, slew2 = None ):
        self.creep_speed_positive = creep
        self.slew_speed_positive = slew
        if creep2 == None:
            self.creep_speed_negative = creep
        else:
            self.creep_speed_positive = creep2

        if slew2 == None:
            self.slew_speed_negative = slew
        else:
            self.slew_speed_negative = slew2

    def set_limits( self, neg_lim, pos_lim ):
        self.negative_limit = neg_lim
        self.positive_limit = pos_lim

    def get_move_command(self) -> str:
        if self.sign == "+":
            return construct_command( self.AXIS, "ma", self.negative_limit )
        elif self.sign == "-":
            return construct_command( self.AXIS, "ma", self.positive_limit )

    def get_creep_speed_command(self) -> str:
        if self.sign == "+":
            return construct_command( self.AXIS, "sc", self.creep_speed_positive )
        elif self.sign == "-":
            return construct_command( self.AXIS, "sc", self.creep_speed_negative )

    def get_slew_speed_command(self) -> str:
        if self.sign == "+":
            return construct_command( self.AXIS, "sv", self.slew_speed_positive )
        elif self.sign == "-":
            return construct_command( self.AXIS, "sv", self.slew_speed_positive )
        
    def set_grafana_location(self, grafana ):
        self.grafana_thread = grafana
    
    def set_print(self):
        self.print = True

    
    @staticmethod
    def get_opposite_sign( mysign ):
        if mysign == "+":
            return "-"
        if mysign == "-":
            return "+"
        return None


    def flip_sign( self, message = "" ):
        if self.print:
            print(f"{self.print_indent}{self.AXIS}: Sign changed from {self.sign} to {self.get_opposite_sign(self.sign)} {message}")
        self.sign = self.get_opposite_sign(self.sign)


    def wait_until_idle(self):
        while True:
            self.pos = send_command( self.POS_CMD )
            try:
                self.pos = int(self.pos)
            except:
                pass
            self.status = send_command( self.STATUS_CMD )
            print(f"{self.print_indent}{self.AXIS}: {self.pos}, {self.status}")
            if self.status == "Idle":
                return self.status
            
            if "ABORT" in self.status:
                return self.status
            
            time.sleep(0.5)

    def check_ready(self):
        if self.slew_speed_negative == None:
            return False
        if self.slew_speed_positive == None:
            return False
        if self.creep_speed_negative == None:
            return False
        if self.creep_speed_positive == None:
            return False
        if self.positive_limit == None:
            return False
        if self.negative_limit == None:
            return False
        return True

    def run(self):
        if self.check_ready() == False:
            if self.print:
                print(f"{self.print_indent}{self.AXIS}: NOT READY! Speeds/limits not set")
            return
        
        # Send initial reset command
        send_command( self.RESET_CMD )

        stall_ctr = 0
        stall_direction = None
        stall_position = None
        STALL_LIMIT = 3
        TRACKING_LIMIT = 3
        TRACKING_INITIAL_STEPS = 1000
        first_time = True

        # Main while loop
        while self.is_running:
            # Get current status
            self.status = send_command( self.STATUS_CMD )
            if self.status == None:
                self.status = "UNKNOWN"

            self.pos = self.grafana_thread.get_pos(self.AXIS)
            if self.print:
                print( f"{self.print_indent}{self.AXIS}: {self.pos}, {self.status}" )
            
            ###########################################################################
            # If it's idle, it's reached the end of the track, so send another command
            if self.status == "Idle":
                # Change speed (if they're different)
                if self.creep_speed_positive != self.creep_speed_negative or first_time == True:
                    creep_result = send_command( self.get_creep_speed_command() )
                    if self.print:
                        print( f"{self.print_indent}-> {self.get_creep_speed_command()}" )
                        print( self.print_indent + creep_result)

                if self.slew_speed_positive != self.slew_speed_negative or first_time == True:
                    slew_result = send_command( self.get_slew_speed_command() )
                    if self.print:
                        print( f"{self.print_indent}-> {self.get_slew_speed_command()}" )
                        print( self.print_indent + slew_result )
                
                if first_time == True:
                    first_time = False

                # Move to the upper or lower limit depending on the sign
                self.current_move_command = self.get_move_command()
                move_result = send_command( self.current_move_command )
                if self.print:
                    print( f"-> {self.current_move_command}" )
                    print( self.print_indent + move_result )

                self.flip_sign()

                # Check if it's been succesful after a stall (i.e. started moving in opposite direction to stall)
                if stall_ctr > 0 and self.sign != stall_direction and abs(int(self.pos) - int(stall_position)) > 100 and ( ( stall_direction == "+" and int(self.pos) > int(stall_position) ) or ( stall_direction == "-" and int(self.pos) < int(stall_position) ) ):
                    if self.print:
                        print(f"{self.print_indent}{self.AXIS}: I overcame a stall! Setting counter to zero again...")
                    stall_ctr = 0
                    stall_direction = None
                    stall_position = None
                elif stall_ctr > 0:
                    print(f"stall_ctr = {stall_ctr}, sign = {self.sign}, stall_direction = {stall_direction}, pos = {int(self.pos)}, stall_position = {stall_position}")
                    print( f"{self.sign == stall_direction} && {int(self.pos) - int(stall_position)} > 100 && { stall_direction == '+' and int(self.pos) > int(stall_position) } or { stall_direction == '-' and int(self.pos) < int(stall_position) }" )

                
            ###########################################################################
            elif self.status == "! STALL ABORT":
                if stall_direction != self.sign and stall_direction != None:
                    if self.print:
                        print(f"{self.print_indent}{self.AXIS}: STALLING IN BOTH DIRECTIONS - I need a human to fix this...")
                    break

                stall_ctr += 1

                if stall_ctr >= STALL_LIMIT:
                    if self.print:
                        print(f"{self.print_indent}{self.AXIS}: STALL LIMIT REACHED - I need a human to fix this...")
                    break

                if self.print:
                    print(f"{self.print_indent}{self.AXIS}: STALL ABORT - trying to fix (pos {self.pos})")
                stall_direction = self.sign
                stall_position = self.pos

                # Essentially just reset, turn around, and try again
                send_command( self.RESET_CMD )

            ###########################################################################
            elif self.status == "! TRACKING ABORT":
                # Try to move down and up a bit in progressively larger steps
                if self.print:
                    print(f"{self.print_indent}{self.AXIS}: TRACKING ABORT - trying to fix")
                reset_flag = True
                for i in range(0,TRACKING_LIMIT):
                    if reset_flag == True:
                        reset_flag = False
                        if self.print:
                            print( self.print_indent + send_command(self.RESET_CMD) )
                            print( f"{self.print_indent}{self.AXIS}mr{self.get_opposite_sign(self.sign)}{(2*i+1)*TRACKING_INITIAL_STEPS}" )
                            print( self.print_indent + send_command( f"{self.AXIS}mr{self.get_opposite_sign(self.sign)}{(2*i+1)*TRACKING_INITIAL_STEPS}\r") )
                        if "ABORT" in self.wait_until_idle():
                            if self.print:
                                print(f"{self.print_indent}{self.AXIS}: Stalls in both directions. Help!")
                            break
                        if self.print:
                            print( f"{self.print_indent}{self.AXIS}: Trying to move in opposite direction now...")
                            print(f"{self.print_indent}{self.AXIS}mr{self.sign}{(2*i+2)*TRACKING_INITIAL_STEPS}")
                        send_command( f"{self.print_indent}{self.AXIS}mr{self.sign}{(2*i+2)*TRACKING_INITIAL_STEPS}\r")
                        if "ABORT" in self.wait_until_idle():
                            reset_flag = True
                        else:
                            print(f"{self.print_indent}{self.AXIS}:I think tracking abort fix worked!")
                            break
                
                if reset_flag == True:
                    if self.print:
                        print(f"{self.print_indent}{self.AXIS}: Couldn't fix tracking abort - human intervention needed")
                    break
                if self.print:
                    print(f"{self.print_indent}{self.AXIS}: Resuming after tracking abort....")
                move_result = send_command( self.current_move_command )
                if self.print:
                    print( f"{self.print_indent}-> {self.current_move_command}" )
                    print( self.print_indent + move_result )

            ###########################################################################
            elif self.status != "! NOT ABORTED" and "ABORT" in self.status:
                if self.print:
                    print(f"{self.print_indent}{self.AXIS}: Motors aborted. Stopping for safety.")
                break

            time.sleep(1.0)
        
        self.is_running = False
###############################################################################
def main():
    # Initialise serial port
    SERIAL_PORT.port = PORTALIAS
    SERIAL_PORT.baudrate = 9600
    SERIAL_PORT.parity = serial.PARITY_EVEN
    SERIAL_PORT.bytesize = serial.SEVENBITS
    SERIAL_PORT.timeout = 3
    SERIAL_PORT.open()

    if not SERIAL_PORT.is_open:
        print(f"Couldn't open {PORTALIAS}. Exiting...")

    # -------- CHANGE WHICH AXES ARE MOVED -------- #
    AXIS_LIST = [1,2,3,4,5]
    AXISNAME = ['Trolley', 'Array', 'TargetH', 'FC', 'BlockerV']

    # Output to Grafana
    g = Grafana( AXIS_LIST, AXISNAME )
    g.start()

    # -------- EDIT BELOW HERE TO CHANGE HOW THE MOTORS MOVE -------- #
    cmt_axis = ConditionMotorsThread(AXIS_LIST[4], AXISNAME[4], "" ) # Setup a thread to move the motors
    cmt_axis.set_speeds( 50, 200 )     # First one is creep speed (slow speed), second one is slew speed (normal speed)
    cmt_axis.set_limits( -13500, 16700) # Limits of the range - this only works if axis has been datum'ed
    cmt_axis.set_grafana_location(g)    # Can ignore this
    cmt_axis.set_print()                # Print to console
    cmt_axis.start()                    # Start moving!

    # Main loop
    while True:
        # Ask for input
        cmd = str(input("Input command: "))
        
        # Check commands
        if cmd == "quit" or cmd == "q":
            break

        if cmd == "":
            continue

        output = send_command( f"{cmd}\r" )
        if type(output) == list:
            print( "".join(output))
        else:
            print(f"~> {output}")
            print("")

    print("BYE")
    cmt_axis.is_running = False
    g.is_running = False

    
if __name__ == "__main__":
    main()
