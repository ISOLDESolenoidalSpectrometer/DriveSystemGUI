import prompt_toolkit.patch_stdout
import drivesystemlib as dslib
import prompt_toolkit

# TODO MAKE MORE SOPHISTICATED WITH CURSES?
def cli_loop():
    drivesystem = dslib.DriveSystem.get_instance()
    prompt_session = prompt_toolkit.PromptSession("DriveSystem >>> ")
    
    try:
        with prompt_toolkit.patch_stdout.patch_stdout():
            while True:
                # Ask for input
                cmd = prompt_session.prompt()
                
                # Check commands
                if cmd == "quit" or cmd == "q":
                    break
                
                # Send command
                output = drivesystem.execute_command( f"{cmd}\r" )
                
                # Print return value
                print(f"{cmd} : AXIS {output[0]} -> {output[1]}")
    except (EOFError, KeyboardInterrupt):
        print("")