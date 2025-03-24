#!/opt/local/bin/python

import curses
import numpy as np
import re
import sys
import time
import threading

NUM_AXES = 7
axisnames = [ "Target carriage", "Array", "Target ladder H", "FC/ZD", "Target ladder V", "Beam blocker H", "Beam blocker V"  ]

###################################################################################################
def KILL(stdscr):
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def reset_stdout():
    sys.stdout = sys.__stdout__

###################################################################################################
class StdOutWrapper:
    # Store text -> looks like one line of statements with '\n' separating them
    text = ""

    # Define write parameter -> this is how output is written to the self.text parameter
    def write(self,txt):
        self.text += txt
        # self.text = '\n'.join(self.text.split('\n')[-30:])
    
    # Get all text sent to stdout
    def get_text(self,beg = 0, end = None):
        if end == None:
            end = len(self.text)
        return '\n'.join(self.text.split('\n')[beg:end])
    
    def flush(self):
        pass

###################################################################################################
class AxisWindow():
    box_width = 20
    box_height = 5
    x_padding = 2

    def __init__(self, y, x, axisnumber ):
        self.encoder_pos = 0
        self.status = "--"

        # Main window
        self.window = curses.newwin(self.box_height, self.box_width, y, x )
        self.window.border()
        self.window.addstr( 0, self.x_padding - 1, f" AXIS {axisnumber} ", curses.A_BOLD )
        self.window.addstr( 1, self.x_padding, axisnames[axisnumber-1])

        # Encoder position window
        self.encoder_pos_window = curses.newwin( 1, self.box_width - 2*self.x_padding, 2 + y, self.x_padding + x )
        self.update_encoder_pos()

        # Status window
        self.status_window = curses.newwin( 1, self.box_width - 2*self.x_padding, 3 + y, self.x_padding + x )
        self.update_status()
        
        
    def get_curses_window(self):
        return self.window
    
    def set_encoder_pos(self, x):
        self.encoder_pos = x
        self.update_encoder_pos()

    def set_status(self, status):
        self.status = status
        self.update_status()
        
    def update_encoder_pos(self):
        self.encoder_pos_window.addstr(0,0,str(self.encoder_pos) )
        self.encoder_pos_window.noutrefresh()

    def update_status(self):
        self.status_window.addstr(0,0,str(self.status) )
        self.status_window.noutrefresh()

    def refresh_all(self):
        self.window.noutrefresh()
        self.encoder_pos_window.noutrefresh()
        self.status_window.noutrefresh()

###################################################################################################
class AxisDisplay():
    def __init__(self):
        self.axis_window_list = []

        y_offset = 0
        i_offset = 0
        for i in range(NUM_AXES):
            if (i - i_offset + 1)*AxisWindow.box_width > curses.COLS:
                i_offset = i
                y_offset += AxisWindow.box_height
            self.axis_window_list.append( AxisWindow( y_offset, (i - i_offset)*AxisWindow.box_width, i+1 ) )
        self.height = y_offset + AxisWindow.box_height
        
        self.refresh_all()

    def get_axis_window(self, i):
        return self.axis_window_list[i]
    
    def refresh_all(self):
        for axis_win in self.axis_window_list:
            axis_win.refresh_all()

###################################################################################################
class HistoryWindow():
    def __init__(self):
        # Redirect stdout
        self.input_stdout = StdOutWrapper()
        self.output_stdout = StdOutWrapper()
        sys.stdout = self.output_stdout          # This redirects all print statements to output window 
        
        # Define pad for displaying text
        self.pad_input_w = int( 0.4*( curses.COLS - 1 ) )
        self.pad_output_w = curses.COLS - 1 - self.pad_input_w
        self.pad_height = 10 # TODO
        self.pad_offset_y = 10 # TODO
        self.pad_input = curses.newpad( 10000, self.pad_input_w )
        self.pad_output = curses.newpad( 10000, self.pad_output_w )
        self.pad_line_ctr = 0

    def add_command_to_history(self, input, output):
        self.input_stdout.write(input)
        self.output_stdout.write(output)

        # Count number of lines in input and output
        # TODO
        
        # Add to pad
        if input == None:
            input = ""
        if output == None:
            output = ""
        self.pad_input.addstr(self.pad_line_ctr, input)
        self.pad_output.addstr(self.pad_line_ctr, output)

        # Update number of lines traversed
        self.pad_line_ctr += 1 # TODO

        # Refresh pad
        current_height = np.min([self.pad_line_ctr, self.pad_height])
        pad_coord_y = np.max([0, self.pad_line_ctr - self.pad_height])
        tl_y = self.pad_offset_y + self.pad_height - current_height
        br_y = self.pad_offset_y + self.pad_height
        self.pad_input.noutrefresh( pad_coord_y, 0, tl_y, 0, br_y, self.pad_input_w )
        self.pad_output.noutrefresh( pad_coord_y, 0, tl_y, self.pad_input_w, br_y, self.pad_input_w + self.pad_output_w )
        

###################################################################################################
class CommandWindow():
    prompt_string = ">>>"
    accepting_input = True
    
    def __init__(self):
        # Initialise prompt
        self.prompt = curses.newwin( 1, len(self.prompt_string) + 1, curses.LINES - 1, 0)
        self.prompt.addstr(0,0,self.prompt_string)

        # Initialise cursor position
        self.cursor_pos = 0
        self.cmd = ""

        # Add command region
        self.window = curses.newwin( 1, curses.COLS - len(self.prompt_string), curses.LINES - 1, len(self.prompt_string) + 1 )

        # Add history link
        self.hist_win = HistoryWindow()

        # Refresh both
        self.prompt.noutrefresh()
        self.window.noutrefresh()

        # Initialise command dictionary
        self.CMD_DICT = {}
        self.CMD_DICT = self.CMD_DICT | dict.fromkeys( ['q', 'Q', 'exit', 'quit'], self.on_quit )

    def receive_commands(self):
        self.window.nodelay(True)
        self.cmd = ""
        while self.accepting_input:
            key = self.window.getch()

            # No key pressed
            if key == -1:
                continue

            # Delete key pressed - CHECK ME
            elif key == 127:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
                    self.cmd = self.cmd[:-1]
                    self.window.addch(0, self.cursor_pos, " ")
            
            # ENTER key pressed
            elif key == 10:
                self.process_command()

            # Previous commands
            elif key == curses.KEY_UP:
                pass
            
            # Reverse previous commands
            elif key == curses.KEY_DOWN:
                pass

            # Move cursor left or right
            # Jump cursor left or right with alt/command/ctrl?
            # Reverse search?
            # elif key == Ctrl + R?
            # Tab complete?

            # ASCII printable characters - what we need
            elif key > 31 and key < 127:
                self.window.addch(0, self.cursor_pos, key)
                self.cursor_pos += 1
                self.cmd += chr(key)
    
    def get_global_cursor_pos(self):
        return tuple( map( lambda i, j: i + j, self.window.getbegyx(), (0,self.cursor_pos) ) )
    
    def process_command(self):
        # Clear window of command
        self.window.clear()

        # Check if command in dictionary TODO
        if True:
            # Do command based on dictionary defined in __init__
            input = self.cmd
            output = self.CMD_DICT.get( str.lower( self.cmd ), self.func_not_defined )()
            self.hist_win.add_command_to_history(input, output)

        # Clear and refresh window
        self.window.clear()
        self.window.noutrefresh()

        # Reset command and cursor position
        self.cmd = ""
        self.cursor_pos = 0

        # Clear window and send refresh
        self.window.clear()
        self.window.noutrefresh()


    ######## DICTIONARY COMMANDS ########
    def on_quit(self):
        self.window.addstr(0,0,f"Quitting. Goodbye!")
        self.window.noutrefresh()
        time.sleep(0.5)
        self.accepting_input = False
        return " "
    
    def func_not_defined(self):
        return "Function not defined, so ignoring"
        

###################################################################################################
class AxisDisplayThread(threading.Thread):
    is_running = False
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.is_running = True

    def run(self):
        d = AxisDisplay()
        while self.is_running:
            win1 = d.get_axis_window(0)
            win2 = d.get_axis_window(1)

            for i in range(0,100000):
                if self.is_running == False:
                    break
                win1.set_encoder_pos(100000 - i)
                win2.set_encoder_pos(i)
                time.sleep(0.02)
                if i % 100 == 0:
                    win1.set_status( f"STATUS {int(1000 - i/100)}")
                    win2.set_status( f"STATUS {int(i/100)} ")

###################################################################################################
class RefreshThread(threading.Thread):
    def __init__(self, cmd_win):
        self.is_running = True
        threading.Thread.__init__(self)
        self.cmd_win = cmd_win

    def run(self):
        while self.is_running:
            curses.setsyx(*self.cmd_win.get_global_cursor_pos())
            curses.doupdate()
            time.sleep(0.02)

###################################################################################################
def main(stdscr):
    try:
        stdscr.clear()
        # curses.curs_set(0) # Hide cursor

        # Print axis displays
        adt = AxisDisplayThread()
        adt.start()

        # Generate command line that accepts textual input
        cmd_win = CommandWindow()

        # Refresh screen thread to keep everything updated (cmd_win needed to work out where cursor goes)
        rt = RefreshThread(cmd_win)
        rt.start()

        # Process commands
        cmd_win.receive_commands()

    except KeyboardInterrupt:
        # This is when Ctrl + C is pressed
        cmd_win.on_quit()

    except:
        pass

    # Have quit the command line, close the threads and reset stdout
    rt.is_running = False
    adt.is_running = False
    reset_stdout()

        
        # d.get_axis_window(1).get_curses_window().getch()
    
    # big_window = curses.newwin( 10, 30, 0, 0 )
    # big_window.border()
    # big_window.refresh()
    # small_window = curses.newwin( 5, 15, 3, 3 )
    # small_window.border()
    # small_window.refresh()

    # for i in range(0,100):
    #     big_window.addstr( 0, 0, str(i))
    #     big_window.refresh()
    #     for j in range(0,100):
    #         small_window.addstr( 0, 0, str(j))
    #         small_window.refresh()
    #         time.sleep(0.01)
        
    # small_window.getch()

    
    # stdscr.addstr(3,2,"+13330")
    # stdscr.addstr(4,2,"Idle")
    # stdscr.addstr(5,2,"12:34:26")

    # time_win = curses.newwin(10,10,5,2)
    # axisnumber=1
    # time_win.addstr( 1, 2, f"AXIS {axisnumber}", curses.A_BOLD )
    # while True:
    #     time_win.addstr( 0, 0, time.strftime("%H:%M:%S") )
    # time_win.refresh()

    #     time.sleep(0.05)    






###################################################################################################
if __name__ == "__main__":
    curses.wrapper( main )
