#!/usr/bin/env python3
import serial
from serial.tools import list_ports
import re
import time
import requests

# Constants
AXIS = 7
AXISNAME = "Target_vertical"
SPEED = 100
PORTALIAS = "/dev/ttyS0"
UPPERLIMIT = -1400
LOWERLIMIT = 1300

def get_move_command(sign : str ) -> str:
	if sign is "+":
		return f"{AXIS}ma{UPPERLIMIT}"
	elif sign is "-":
		return f"{AXIS}ma{LOWERLIMIT}"

def get_command_result( X ):
	X.decode('utf8')
	pattern = re.match( b'.*\\r(\d*):(.*)\\r\n', X, re.IGNORECASE )
	if pattern == None:
		return None
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
serial_port.write( RESET_CMD.encode() )
time.sleep(0.1)
serial_port.readline()

while True:

	# Get current status
	X = send_command( STATUS_CMD )
	if X == None:
		X = b"NONE"
	time.sleep(0.1)

	pos = send_command( POS_CMD )
	if pos == None:
		pos = b"-20000"
	print( pos.decode(), X.decode() )
	time.sleep(0.1)
	
	# If it's idle, it's reached the end of the track, so send another command
	if X == b"Idle":

		# Move to the upper or lower limit depending on the sign
		#move_result = send_command( get_move_command( sign ))
		#print( move_result)
		#print( f"-> {get_move_command( sign )}")
		#time.sleep(0.1)

		serial_port.write( get_move_command( sign ).encode() )
		print( f"-> {get_move_command( sign )}")
		time.sleep(0.1)
		print( get_command_result( serial_port.readline() ) )
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
	# payload = 'encoder,axis=' + str(AXIS) + ',name=' + str(AXISNAME) + ' value=' + str(pos.decode())
	#r = requests.post( 'https://dbod-iss.cern.ch:8080/write?db=positions', data=payload, auth=("admin","issmonitor"), verify=False )

	# Wait a little while before moving again
	time.sleep(1.0)

# BOTTOM = 13397
# TOP = -14512



