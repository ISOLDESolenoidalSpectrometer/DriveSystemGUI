import drivesystemlib as dslib

# TODO MAKE MORE SOPHISTICATED WITH CURSES?
def cli_loop():
    drivesystem = dslib.DriveSystem.get_instance()
    
    try:
        while True:
            # Ask for input
            cmd = str(input("Input command: "))
            
            # Check commands
            if cmd == "quit" or cmd == "q":
                break
            
            # Send command
            output = drivesystem.execute_command( f"{cmd}\r" )
            
            # Print return value
            print(output)
    except KeyboardInterrupt:
        print("")