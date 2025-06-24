from prompt_toolkit import Application
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea
import drivesystemlib as dslib
import datetime as dt
import sys
import threading
import time

class DriveSystemCLI():
    PROMPT_INDICATOR = 'DriveSystem ~> '
    HELP_TEXT = """
    Help Menu
    ---------
    Type commands and press enter to execute.
    Use arrow keys to navigate history.
    Type '?' to see this help.
    """
    ################################################################################
    def __init__(self):
        # Do nothing initially so that everything else can be created
        self.is_initialised = False
        self.lock = threading.Lock()
        return

    ################################################################################
    def init_style(self):
        self.style = Style(
            [
                ("prompt", "fg:#00ff00 bold"),
                ("output-field", "fg:#ffffff"),
                ("input-field", "fg:#00ff00"),
                ("line", "#444444"),
            ]
        )
        return
    
    ################################################################################
    def init_ui(self):
        # Define areas in code
        # TOP (output)
        self.output_text_area = TextArea(style="class:output-field")

        # BOTTOM (with search bar)
        self.search_field = SearchToolbar()
        self.input_field = TextArea(
            height=1,
            prompt=self.PROMPT_INDICATOR,
            style="class:input-field",
            multiline=False,
            wrap_lines=False,
            search_field=self.search_field,
        )

        # DIVIDER
        self.divider = Window(height=1, char='─', style='class:line')

        # Define layout
        self.container = HSplit(
            [
                self.output_text_area,
                self.divider,
                self.input_field,
                self.search_field
            ]
        )
        self.layout = Layout(self.container, focused_element=self.input_field)
        return

    ################################################################################
    def init_key_bindings(self):
        self.kb = KeyBindings()

        # QUIT
        @self.kb.add("c-d")
        def _(event):
            self.delete()

        # CLEAR FIELD WITH CTRL + C
        @self.kb.add("c-c")
        def _(event):
            self.input_field.text = ""

        # PROCESS COMMANDS HERE
        def on_enter(event):
            cmd = self.input_field.text.strip()
            # Do nothing if nothing entered
            if cmd in ("",None):
                return

            # Help menu
            # if "?" in cmd:
                # Show help window

            # Quit
            if self.input_field.text in ("quit", "q"):
                self.delete()
                return
            
            # Execute command
            # Send command
            cmd_time = dt.datetime.now().strftime( '[%Y.%m.%d %H:%M:%S]' )
            axis,response = self.drivesystem.execute_command( self.drivesystem.construct_command_from_str(cmd) )
            if response == None:
                response = 'None'
            self.print_to_terminal(cmd_time + ' ' + cmd + " -> " + response.replace('\r',' ') + '\n')
            return

        # Add command processor to the input field
        self.input_field.accept_handler=on_enter
        return
    
    
    ################################################################################
    def run(self):
        self.drivesystem = dslib.DriveSystem.get_instance()
        self.init_style()
        self.init_ui()
        self.init_key_bindings()
        self.app = Application(layout=self.layout, key_bindings=self.kb, full_screen=True,mouse_support=True, style=self.style)
        self.is_initialised = True
        self.app.run()
        return
    
    ################################################################################
    def print_to_terminal(self, text : str, end='\n' ):
        with self.lock:
            mytext = self.output_text_area.text + text + end
            self.output_text_area.buffer.document = Document(
                text = mytext, cursor_position = len(mytext)
            )

    
    ################################################################################
    def delete(self):
        self.print_to_terminal("Quitting...")
        dslib.shutdown()
        self.is_initialised = False

        def exit_in_thread():
            time.sleep(2)
            self.app.exit()
        threading.Thread(target=exit_in_thread, daemon=True).start()
        return



####################################################################################################
# FACTORY to get CLI and initialise CLI
def GET_CLI() -> DriveSystemCLI:
    if not hasattr(GET_CLI, "_instance"):
        GET_CLI._instance = DriveSystemCLI()
    return GET_CLI._instance
