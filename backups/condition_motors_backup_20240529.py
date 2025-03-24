#!/usr/bin/env python3
import serial
from serial.tools import list_ports
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

def get_move_command(sign : str ) -> str:
	if sign is "+":
		return f"{AXIS}ma{UPPERLIMIT}\r"
	elif sign is "-":
		return f"{AXIS}ma{LOWERLIMIT}\r"


def get_creep_speed_command( sign : str ) -> str:
	if sign is "+":
		return f"{AXIS}sc{CREEP_SPEED_DOWN}\r"
	elif sign is "-":
		return f"{AXIS}sc{CREEP_SPEED_UP}\r"

def get_slew_speed_command( sign : str ) -> str:
	if sign is "+":
		return f"{AXIS}sv{SLEW_SPEED_DOWN}\r"
	elif sign is "-":
		return f"{AXIS}sv{SLEW_SPEED_UP}\r"

def get_command_result( X ):
	#X.decode('utf8')
	pattern = re.match( b'.*\\r(\d*):(.*)\\r\n', X, re.IGNORECASE )
	if pattern == None:
		return b"None"
	return pattern.group(2)
	
def send_command( cmd ):
	serial_port.write( cmd.encode() )
	time.sleep(0.1)
	return get_command_result( serial_port.readline() )



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
sign = "+"

# Send command to reset the motors
RESET_CMD = f"{AXIS}rs\r"
send_command( RESET_CMD )


while True:

	# Get current status
	X = send_command( STATUS_CMD )
	if X == None:
		X = b"UNKNOWN"
	time.sleep(0.1)

	pos = send_command( POS_CMD )
	if pos == b"None":
		pos = b"-20000"
	print( pos.decode(), X.decode() )
	time.sleep(0.1)
	
	# If it's idle, it's reached the end of the track, so send another command
	if X == b"Idle":
		# Change speed
		creep_result = send_command( get_creep_speed_command( sign ) )
		print( f"-> {get_creep_speed_command( sign )}" )
		print( creep_result.decode() )
		time.sleep(0.1)

		slew_result = send_command( get_slew_speed_command( sign ) )
		print( f"-> {get_slew_speed_command( sign )}" )
		print( slew_result.decode() )
		time.sleep(0.1)

		# Move to the upper or lower limit depending on the sign
		move_result = send_command( get_move_command( sign ) )
		print( f"-> {get_move_command( sign )}" )
		print( move_result.decode() )
		time.sleep(0.1)

		# Change direction it for the next pass
		if sign == "+":
			sign = "-"
			print("Sign changed from + to -")
		elif sign == "-":
			sign = "+"
			print("Sign changed from - to +")

	if X != b"! NOT ABORTED" and b"ABORT" in X:
		print("Motors aborted. Stopping for safety. Bye!")
		break

	# Send to Grafana
	payload = 'encoder,axis=' + str(AXIS) + ',name=' + str(AXISNAME) + ' value=' + str(pos.decode())
	r = requests.post( 'https://dbod-iss.cern.ch:8080/write?db=positions', data=payload, auth=("admin","issmonitor"), verify=False )

	# Wait a little while before moving again
	time.sleep(1.0)


