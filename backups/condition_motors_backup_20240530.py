#!/usr/bin/env python3
import serial
import re
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
AXIS = 5
AXISNAME = "Target_vertical"
CREEP_SPEED_DOWN = 100
CREEP_SPEED_UP = CREEP_SPEED_DOWN
SLEW_SPEED_DOWN = 400
SLEW_SPEED_UP = SLEW_SPEED_DOWN
PORTALIAS = "/dev/ttyS0"
UPPERLIMIT = -14200
LOWERLIMIT = 13600
sign = "+"

def get_move_command() -> str:
	if sign == "+":
		return f"{AXIS}ma{UPPERLIMIT}\r"
	elif sign == "-":
		return f"{AXIS}ma{LOWERLIMIT}\r"

def get_creep_speed_command() -> str:
	if sign == "+":
		return f"{AXIS}sc{CREEP_SPEED_DOWN}\r"
	elif sign == "-":
		return f"{AXIS}sc{CREEP_SPEED_UP}\r"

def get_slew_speed_command() -> str:
	if sign == "+":
		return f"{AXIS}sv{SLEW_SPEED_DOWN}\r"
	elif sign == "-":
		return f"{AXIS}sv{SLEW_SPEED_UP}\r"

def get_command_result( X ):
	pattern = re.match( '.*\\r(\d*):(.*)\\r\n', X, re.IGNORECASE )
	if pattern == None:
		return "None"
	return pattern.group(2)
	
def send_command( cmd ):
	serial_port.write( cmd.encode() )
	time.sleep(0.1)
	a = get_command_result( serial_port.readline().decode() )
	time.sleep(0.1)
	return a

def get_opposite_sign( mysign ):
	if mysign == "+":
		return "-"
	if mysign == "-":
		return "+"
	return None

def flip_sign( message = "" ):
	global sign
	print(f"Sign changed from {sign} to {get_opposite_sign(sign)} {message}")
	sign = get_opposite_sign(sign)


def wait_until_idle():
	while True:
		pos = send_command( POS_CMD )
		status = send_command( STATUS_CMD )
		print("    ", pos, status)
		if status == "Idle":
			return status
		
		if "ABORT" in status:
			return status
		
		time.sleep(0.5)



serial_port = serial.Serial()
serial_port.port = PORTALIAS
serial_port.baudrate = 9600
serial_port.parity = serial.PARITY_EVEN
serial_port.bytesize = serial.SEVENBITS
serial_port.timeout = 3
serial_port.open()

if not serial_port.is_open:
	print(f"Couldn't open {PORTALIAS}. Exiting...")

STATUS_CMD = f"{AXIS}co\r"
POS_CMD = f"{AXIS}oa\r"

# Send command to reset the motors
RESET_CMD = f"{AXIS}rs\r"
send_command( RESET_CMD )

stall_ctr = 0
stall_direction = None
stall_position = None
STALL_LIMIT = 3
tracking_ctr = 0
TRACKING_LIMIT = 3
TRACKING_INITIAL_STEPS = 1000

while True:
	# Get current status
	status = send_command( STATUS_CMD )
	if status == None:
		status = "UNKNOWN"

	pos = send_command( POS_CMD )
	print( pos, status )
	
	###########################################################################
	# If it's idle, it's reached the end of the track, so send another command
	if status == "Idle":
		# Change speed (if they're different)
		if CREEP_SPEED_DOWN != CREEP_SPEED_UP:
			creep_result = send_command( get_creep_speed_command() )
			print( f"-> {get_creep_speed_command()}" )
			print( creep_result)

		if SLEW_SPEED_DOWN != SLEW_SPEED_UP:
			slew_result = send_command( get_slew_speed_command() )
			print( f"-> {get_slew_speed_command()}" )
			print( slew_result )

		# Move to the upper or lower limit depending on the sign
		move_result = send_command( get_move_command() )
		print( f"-> {get_move_command()}" )
		print( move_result )

		flip_sign()

		# Check if it's been succesful after a stall
		if stall_ctr > 0 and sign == stall_direction and abs(int(pos) - int(stall_position)) > 200 and ( ( stall_direction == "+" and pos > stall_position ) or ( stall_direction == "-" and pos < stall_position ) ):
			print("I overcame a stall! Setting counter to zero again...")
			small_ctr = 0
			stall_direction = None
			stall_position = None

		
	###########################################################################
	elif status == "! STALL ABORT":
		if stall_direction != sign and stall_direction != None:
			print("STALLING IN BOTH DIRECTIONS - I need a human to fix this...")
			break

		stall_ctr += 1

		if stall_ctr >= STALL_LIMIT:
			print("STALL LIMIT REACHED - I need a human to fix this...")
			break

		print(f"STALL ABORT - trying to fix (pos {pos})")
		stall_direction = sign
		stall_position = pos

		# Essentially just reset, turn around, and try again
		send_command( RESET_CMD )

	###########################################################################
	elif status == "! TRACKING ABORT":
		# Try to move down and up a bit in progressively larger steps
		print("TRACKING ABORT - trying to fix")
		reset_flag = True
		for i in range(0,TRACKING_LIMIT):
			if reset_flag == True:
				reset_flag = False
				print( "    " + send_command(RESET_CMD) )
				print( f"    {AXIS}mr{get_opposite_sign(sign)}{(2*i+1)*TRACKING_INITIAL_STEPS}" )
				print( "    " + send_command( f"{AXIS}mr{get_opposite_sign(sign)}{(2*i+1)*TRACKING_INITIAL_STEPS}\r") )
				if "ABORT" in wait_until_idle():
					print("    Stalls in both directions. Help!")
					break
				print( "    Trying to move in opposite direction now...")
				print(f"    {AXIS}mr{sign}{(2*i+2)*TRACKING_INITIAL_STEPS}")
				send_command( f"    {AXIS}mr{sign}{(2*i+2)*TRACKING_INITIAL_STEPS}\r")
				if "ABORT" in wait_until_idle():
					reset_flag = True
				else:
					print("    I think it worked!")
					break

		print("Resuming after tracking abort....")




	###########################################################################
	elif status != "! NOT ABORTED" and "ABORT" in status:
		print("Motors aborted. Stopping for safety. Bye!")
		break

	# Send to Grafana
	if str(pos) != None:
		payload = 'encoder,axis=' + str(AXIS) + ',name=' + str(AXISNAME) + ' value=' + str(pos)
		r = requests.post( 'https://dbod-iss.cern.ch:8080/write?db=positions', data=payload, auth=("admin","issmonitor"), verify=False )

	# Wait a little while before checking again
	time.sleep(1.0)


