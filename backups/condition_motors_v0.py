#!/usr/bin/env python3
import serial
from serial.tools import list_ports
import re
import time
import requests

# Constants
AXIS = 7
AXISNAME = "TARGET LADDER VERTICAL (TEST)"
SPEED = 100
PORTALIAS = "/dev/ttyS0"

def get_move_command(sign : str ) -> str:
	return f"{AXIS}cv{sign}{SPEED}"

def get_command_result( X ):
	X.decode('utf8')
	pattern = re.match( b'.*\\r(\d*):(.*)\\r\n', X, re.IGNORECASE )
	if pattern == None:
		return None
	return pattern.group(2)


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
	serial_port.write( STATUS_CMD.encode() )
	time.sleep(0.1)
	X = get_command_result( serial_port.readline() )
	if X == None:
		X = b"NONE"
	time.sleep(0.1)
	serial_port.write( POS_CMD.encode() )
	time.sleep(0.1)
	pos = get_command_result( serial_port.readline() )
	if pos == None:
		pos = b"-20000"
	print(pos.decode(), X.decode() )
	
	# If it's idle, it's reached the end of the track, so send another command
	if X == b"Idle":
		serial_port.write( get_move_command( sign ).encode() )
		print( f"-> {get_move_command( sign )}")
		time.sleep(0.1)
		print( get_command_result( serial_port.readline() ) )
		time.sleep(0.1)
		
		# Change direction for next time
		if sign == "+":
			sign = "-"
			print("Sign changed from + to -")
			time.sleep(0.1)
		elif sign == "-":
			sign = "+"
			print("Sign changed from - to +")
			time.sleep(0.1)

	# If it's constant velocity, sleep a bit
	if X == b"Constant velocity":
		time.sleep(2)

	if X != b"! NOT ABORTED" and b"ABORT" in X:
		print("Motors aborted. Stopping for safety. Bye!")
		break

	# Send to Grafana
	#payload = 'encoder,axis=' + str(AXIS) + ',name=' + str(AXISNAME) + ' value=' + str(pos.decode())
	#r = requests.post( 'https://dbod-iss.cern.ch:8080/write?db=positions', data=payload, auth=("admin","issmonitor"), verify=False )





	#serial_port.write( STATUS_CMD.encode() )
	#time.sleep(0.1)
	#print( serial_port.readline() )

# BOTTOM = 13411
# TOP = -14359

