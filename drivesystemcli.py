import prompt_toolkit as pt
from prompt_toolkit import print_formatted_text
import prompt_toolkit.key_binding as ptkb
import prompt_toolkit.widgets as ptw
import prompt_toolkit.layout as ptl
import drivesystemlib as dslib
import prompt_toolkit
import datetime as dt

################################################################################
def show_help_window():
    help_text="""
+-----------+
| HELP MENU |
+-----------+
TODO

(Press Enter to return)
"""
    help_area = ptw.TextArea(text=help_text, focusable=False)
    layout = ptl.Layout( ptl.containers.HSplit([help_area]))

    kb = ptkb.KeyBindings()

    @kb.add('enter')
    @kb.add('escape')
    def exit_(event):
        event.app.exit()

    app = pt.Application( layout, key_bindings=kb, full_screen=True, erase_when_done=False )
    app.run(in_thread=True)


################################################################################
def cli_interface():
    drivesystem = dslib.DriveSystem.get_instance()
    prompt_session = pt.PromptSession("DriveSystem >>> ")
    
    try:
        while True:
            # Ask for input
            cmd = prompt_session.prompt()
            
            # Check commands
            if cmd.strip() in ("quit", "q"):
                break

            # Help menu
            if "?" in cmd:
                show_help_window()
                continue
            
            # Send command
            dt.datetime.now().strftime
            cmd_time = dt.datetime.now().strftime( '%Y.%m.%d %H:%M:%S' )
            output = drivesystem.execute_command( f"{cmd}\r" )
            
            # Print return value
            print_formatted_text(f"[{cmd_time}] {cmd} : AXIS {output[0]} ->{output[1]}")
    except (EOFError, KeyboardInterrupt):
        pass
    