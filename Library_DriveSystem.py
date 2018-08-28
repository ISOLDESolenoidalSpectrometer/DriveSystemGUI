import serial
import time
import re
from serial.tools import list_ports
import requests
import urllib3
import numpy as np
import urllib3
urllib3.disable_warnings()


class DriveSystem():
	def __init__(self):
		self.serial_port = serial.Serial()
		self.port_open = False
		self.parity=int(1)
		self.positions=np.zeros(4)
		self.axis_name = [ 'Trolley', 'Array', 'Target', 'FC' ]
		
		
		# Port option lists
		self.set_defaults()
		if self.serial_port.is_open == True:
			print("Already connected to"+ self.portalias)
		else:
			self.connect_to_port()
		#self.set_defaultMovingOptions()
		
	
	############
	# Defaults #
	############
	
	def set_defaults( self ):
		self.seteven()
		self.set7()
		self.baudrate= "9600"  # initial value
		self.portalias="/dev/ttyS0"	# initial value

	def set_defaultMovingOptions(self):
		# Set acceleration
		in_cmd = ( str(axis) + 'sa500\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Set deceleration
		in_cmd = ( str(axis) + 'sd1000\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Set velocity
		in_cmd = ( str(axis) + 'sv1000\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Set creep
		in_cmd = ( str(axis) + 'sc200\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	

	###########
	# Actions #
	###########

	
	# Create serial port
	def connect_to_port( self ):
		self.serial_port.port = self.portalias			# set name of port
		self.serial_port.baudrate = int( self.baudrate )	# set baud rate
		self.serial_port.parity = serial.PARITY_EVEN			# set parity
		self.serial_port.bytesize = serial.SEVENBITS			# set bytesize
		self.serial_port.timeout = 3							# set timeout to 3 seconds
		self.serial_port.open()									# open the port
		
		if self.serial_port.is_open == True:
			
			tmpStr = "Connected to " + self.portalias
			#self.out_now.set( tmpStr )
			print( tmpStr )
			self.port_open = True
		else:
		
			tmpStr = "Failed to connect to " + self.portalias.get()
			#self.out_now.set( tmpStr )
			print( tmpStr )
	
	def checkConnection(self):
		return self.port_open

	# Disconnect from serial port
	def disconnect_port( self ):
		self.port_open = False
		#time.sleep(0.1)
		self.serial_port.close()# close the port
		print( "Disconnected" )
		#time.sleep(0.1)

	def abortAll(self):
		print( "Abort command on all axes")
		for i in range(4):
			axis=i=1
			in_cmd = ( str(axis) + 'ab'+ '\r' ).encode()
			print( in_cmd )
			self.serial_port.write( in_cmd )
			time.sleep(0.1)
			outputline = self.serial_port.readline()
			print( outputline )
	def resetAll(self):
		print( "Reset all axes")
		for i in range(4):
			axis=i=1
			in_cmd = ( str(axis) + 'rs'+ '\r' ).encode()
			print( in_cmd )
			self.serial_port.write( in_cmd )
			time.sleep(0.1)
			outputline = self.serial_port.readline()
			print( outputline )

	# go to position 1 (move absolute)
	def select_pos( self, axis,pos ):
		print( "Moving to position ", pos,"on axis ",str(axis) )
		in_cmd = ( str(axis) + 'ma'+str(pos)+ '\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )

	# move relative
	def move_rel( self, axis,steps):
		print( "Moving ", steps," on axis ",str(axis) )
		in_cmd = ( str(axis) + 'mr\r'+str(steps) ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		
	# datum search
	def datum_search( self, axis ):
		
		print( "Datum search on axis", axis )
		
		# Set acceleration
		in_cmd = ( str(axis) + 'sa500\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Set deceleration
		in_cmd = ( str(axis) + 'sd1000\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Set velocity
		in_cmd = ( str(axis) + 'sv1000\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Set creep
		in_cmd = ( str(axis) + 'sc200\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Set datum mode
		in_cmd = ( str(axis) + 'dm00101000\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Go home to datum
		in_cmd = ( str(axis) + 'hd\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)

		# Check position
		self.check_encoder_pos_axis(axis)

		# Display current operation
		in_cmd = ( str(axis) + 'co\r' ).encode()
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		time.sleep(0.1)
	
		# Check position
		self.check_encoder_pos_axis(axis)

	# write info
	def executeCommand( self, command):
	
		in_cmd = command
		print( in_cmd )
		self.serial_port.write( in_cmd )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		print( outputline )
		outputline.decode('utf8')
		pattern = re.match(b'.*\\r(\d*):(.*)\\r\\n', outputline, re.IGNORECASE)

		if pattern is not None:
			#self.axis_now.set( pattern.group(1) )
			#self.out_now.set( pattern.group(2) )
			return pattern.group(1),pattern.group(2)
		#self.check_encoder_pos()

	# check encoder positions
	def check_encoder_pos( self ):
		pos=[]
		for i in range(4):
			self.check_encoder_pos_axis(i+1)
		return self.positions

	# check encoder positions
	def check_encoder_pos_axis( self, axis ):

		in_cmd = ( '%doa\r' % axis ).encode()
		self.serial_port.write( bytes(in_cmd) )
		time.sleep(0.1)
		outputline = self.serial_port.readline()
		outputline.decode('utf8')
		#outputline = "3oa\\r03:0\\r\\n"
		print( outputline )
		pattern = re.match(b'.*\\r(\d*):(-?\d*).*\\r\\n', outputline, re.IGNORECASE)
		#print( pattern )
		if pattern is not None:
			self.positions[axis-1] = int( pattern.group(2) )
			#self.enc_disp_txt[axis-1].set( ('%d: %d' % ( axis, int( pattern.group(2) ) ) ) )
			self.send_to_influx( axis, int( pattern.group(2) ) )
		else:
			print("Could not read position of axis "+str(axis))


	# send positions to InfluxDB
	def send_to_influx( self, axis, pos ):

		payload = 'encoder,axis=' + str(axis) + ',name=' + str(self.axis_name[axis-1]) + ' value=' + str(pos)
		r = requests.post( 'https://dbod-iss.cern.ch:8080/write?db=positions', data=payload, auth=("admin","issmonitor"), verify=False )


	
	# set the parity to even
	def seteven( self ):
		self.parity=serial.PARITY_EVEN
		self.parityodd=0
		self.parityeven=1
		self.paritynone=0
	
	# set the parity to odd
	def setodd( self ):	
		self.parity=serial.PARITY_ODD
		self.parityodd=1
		self.parityeven=0
		self.paritynone=0
	
	# set the parity to none
	def setnone( self ):
		self.parity=serial.PARITY_NONE
		self.parityodd=0
		self.parityeven=0
		self.paritynone=1
	
	# set the number of bits to 7
	def set7( self ):
		self.nbits=serial.SEVENBITS
		self.bit7on=1
		self.bit8on=0
	
	# set the number of bits to 8
	def set8( self ):
		self.nbits=serial.EIGHTBITS
		self.bit7on=0
		self.bit8on=1
