import matplotlib
matplotlib.use('WXAgg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib import animation
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

import wx
import numpy as np
import threading
import time
import Library_DriveSystem
import queue
import os


#----------Constants-------------------
#Frame size constants
frameHeight=740
frameWidth=1000
controlViewSize=200

#Rectangles W=width, H=heigth, sidespace=space between trolley border and axis 3/4
oneW=45*10
oneH=27*10
twoW=35*10
twoH=19.5*10
arrayW=74.85*10 
arrayH=5*10
array_sidespace=2.07*10
arrayEdge_H=arrayH
arrayEdge_W=71.01 #distance from end of array to edge of Si (y+z in drawing)
threeW=8*10
threeH=13*10
fourW=8*10
fourH=13*10
target_sidespace=2*10
detector_sidespace=2*10
#one_sidespace=100

#Magnetlength
magL=273*10

#Home positions
#home1=magL/2-39.2*10+detector_sidespace-oneW-110932/200
#home2=-magL/2+115*10-74.85*10+35129/200
home2=-magL/2+1150+35129/200 #at encoder position 35129, the end of the array was at a distance of 1.15m from the magnet wall.
#homePositions=np.array([home1,home2,0,0])

#FC and dE/dx detector 
#Negative encoder position of the center
fcH=-11497.0/200
dEH=12603.0/200
#Radius
fcR=21
dER=20

#Colours
oneC='#0DE30B'#FDD11F'
twoC='#FDD11F'#E0E0E0'#FFFFE0 #'#910BE3'
threeC='#00A7FA'
fourC='#910BE3'
arrayC='#FD3F0D'
arrayEdge_C=fourC

#Frequency for the positons checking
UPDATE_TIME=1
REAC_TIME=0.1

#Element definition for the queue
class Element:
	def __init__(self, mode,ax=None,cmd=None):
		self.mode = mode
		self.axis = ax
		self.command=cmd

#-------------------Code Start-------------------

#Definitions of Events
myEVT_POSUPDATE = wx.NewEventType()
EVT_POSUPDATE = wx.PyEventBinder(myEVT_POSUPDATE, 1)
class PosUpdateEvent(wx.PyCommandEvent):
       """Event to signal that a count value is ready"""
       def __init__(self, etype, eid, value=None):
            """Creates the event object"""
            wx.PyCommandEvent.__init__(self, etype, eid)
            self._value = value
    
       def GetValue(self):
           """Returns the value from the event.
           @return: the value of this event
   
           """
           return self._value

myEVT_DISCONNECT = wx.NewEventType()
EVT_DISCONNECT = wx.PyEventBinder(myEVT_DISCONNECT, 1)
class DisConnectEvent(wx.PyCommandEvent):
       """Event to signal that a count value is ready"""
       def __init__(self, etype, eid, value=None):
            """Creates the event object"""
            wx.PyCommandEvent.__init__(self, etype, eid)
            self._value = value
    
       def GetValue(self):
           """Returns the value from the event.
           @return: the value of this event
   
           """
           return self._value

#-----------------------------------------------------------
#Thread that checks the positions regularly
class CheckPositions(threading.Thread):
	def __init__(self,controlView,driveSystem):
		"""
		@param parent: The gui object that should recieve the value
		@param value: value to 'calculate' to
		"""
		threading.Thread.__init__(self)
		self._parent = controlView
		self._driveSystem=driveSystem
		#self._updateCounter=0	#will increase after every time.sleep until it's equal to the UPDATE_TIME                          
   
	def run(self):
		"""Overrides Thread.run. Don't call this directly its called internally
		when you call Thread.start().
		"""
		while 1:
			if self._driveSystem.port_open == True and self._parent.aborted==False:
				
				self._driveSystem.check_encoder_pos()
				pos=self._driveSystem.positions
				if self._parent.printRequest==True: #Print positions when print Button was pressed
					output="Axis 1: "+str(pos[0])+"\nAxis 2: "+str(pos[1])+"\nAxis 3: "+str(pos[2])+"\nAxis 4: "+str(pos[3])
					print(output)
					self._parent.printRequest=False
				event = PosUpdateEvent(myEVT_POSUPDATE, -1, pos)
				wx.PostEvent(self._parent.matplotpanel, event)
				
				t=0
				while t<UPDATE_TIME:
					self.checkQ()
					time.sleep(REAC_TIME)
					t=t+REAC_TIME
			else:
				time.sleep(1)
		
	def checkQ(self):
		while self._parent.q.empty()==False:
			item = self._parent.q.get()
			self.action(item)
			self._parent.q.task_done()
	def action(self,element):
		if element.mode=='Q':
			self._parent.quit()
		elif element.mode=='S':
			self._parent.sendingCommand(element.command)
		
		elif element.mode=='M':
			if element.axis==1:
				self._parent.move1()
			elif element.axis==2:
				self._parent.move2()
			elif element.axis==3:
				self._parent.setTargetPos()
			elif element.axis==4:
				self._parent.setDetectorPos()
		elif element.mode=='M+-':
			steps=element.command
			self._parent.movePlusMinus(element.axis,steps)
			
		elif element.mode=='H':
			if element.axis==1:
				self._parent.home1()
			elif element.axis==2:
				self._parent.home2()
			elif element.axis==3:
				self._parent.home3()
			elif element.axis==4:
				self._parent.home4()
		elif element.mode=='C':
			self._parent.connect()
		elif element.mode=='D':
			self._parent.disconnect()



class DriveView:
	def __init__(self,panel):
		self.matplotpanel=panel

		#Defining the figure
		self.fig = plt.figure()
		self.fig.set_dpi(100)
		self.fig.set_size_inches(10, 5.3)
		
		#Setting properties of the axes
		self.ymin=-40*10
		self.ymax=40*10
		self.xmin=-magL*0.5
		self.xmax=magL*0.5
		
		#Ax design
		self.ax = plt.axes(xlim=(self.xmin, self.xmax), ylim=(self.ymin,self.ymax))
		self.ax.spines['right'].set_color('none')
		self.ax.spines['top'].set_color('none')
		self.ax.set_yticks([])
		self.ax.spines['left'].set_color('none')
		self.ax.spines['bottom'].set_position(('data',-2.765))
		majorLocator = MultipleLocator(500)
		minorLocator = MultipleLocator(100)
		self.ax.xaxis.set_major_locator(majorLocator)
		# for the minor ticks, use no labels; default NullFormatter
		self.ax.xaxis.set_minor_locator(minorLocator)
		self.ax.set_xlabel("[mm]")
		#ax.grid()
		
		#Adding the four rectangles + array which belongs to ax 2
		self.one = plt.Rectangle((self.xmax-600, -oneH/2), oneW, oneH, fc=oneC)
		self.ax.add_patch(self.one)
		self.two = plt.Rectangle((self.xmin+300, -twoH/2), twoW, twoH, fc=twoC)
		self.ax.add_patch(self.two)
		self.four = plt.Rectangle((self.xmax-600+oneW-detector_sidespace-fourW, -fourH/2), fourW, threeH, fc=fourC)
		self.ax.add_patch(self.four)
		self.three = plt.Rectangle((self.xmax-600+target_sidespace, -threeH/2), threeW, threeH, fc=threeC)
		self.ax.add_patch(self.three)
		self.array = plt.Rectangle((self.xmin+300+array_sidespace,-arrayH/2), arrayW, arrayH, fc=arrayC)
		self.ax.add_patch(self.array)
		self.arrayEdge = plt.Rectangle((self.array.get_x()+arrayW-arrayEdge_W,-arrayH/2), arrayEdge_W, arrayEdge_H, fc=arrayEdge_C)
		self.ax.add_patch(self.arrayEdge)
		#Adding FC and dE/dx detector
		self.FC=plt.Circle(xy=(self.four.get_x()+0.5*fourW,fcH),radius=fcR,fc=twoC)
		self.dE=plt.Circle(xy=(self.four.get_x()+0.5*fourW,dEH),radius=dER,fc=twoC)
		self.ax.add_patch(self.FC)
		self.ax.add_patch(self.dE)
		
		#Adding numbers to the rectangulars
		self.placeNumbers()

		#Adding information about position
		rand=2*10
		dis=70*10
		plt.rcParams.update({'font.size': 12})
		self.position1=self.ax.text(self.xmin,self.ymax-rand,"Position 1: "+str(self.one.get_x())+" mm",color=oneC)
		self.position2=self.ax.text(self.xmin+dis-5,self.ymax-rand,"Position 2: "+str(self.two.get_x())+" mm",color=arrayC)
		self.position3=self.ax.text(self.xmin+2*dis,self.ymax-rand,"Position 3: "+str(0)+" mm",color=threeC)
		self.position4=self.ax.text(self.xmin+3*dis+5,self.ymax-rand,"Position 4: "+str(0)+" mm",color=fourC)

		#Beam Arrow
		self.beamArrow=self.ax.annotate ('', (self.xmin, self.ymax-20*10), (self.xmin+30*10, self.ymax-20*10),arrowprops={'arrowstyle':'<-'} )
		text="BEAM"
		self.beamText=self.ax.text(self.xmin+7*10, self.ymax-18*10,text)

		#Conversion coefficients
		self.conversionText1=self.ax.text(self.xmin, -self.ymax+4*10,"1 mm = 200 steps")
		self.conversionText2=self.ax.text(self.xmin, -self.ymax,"1 step = 0.005 mm")
		#Arrow who shows the distance
		self.arrow=self.ax.annotate ('', (-100, 100), (100, 100), arrowprops={'arrowstyle':'<->'})
		self.distanceArrow=self.ax.text(0,0,"")
		self.drawArrow(self.three.get_x()-self.two.get_x())

		#Makes the space at the sides of the diagrams smaller
		self.fig.tight_layout()

	def get_figure(self):
		return self.fig
	def drawArrow(self,dis2_3):
		self.arrow.remove()
		self.distanceArrow.remove()
		x1=self.three.get_x()
		x2=self.array.get_x()+arrayW-30.48-40.53
		height=oneH/2+1*10
		self.arrow=self.ax.annotate ('', (x1, height), (x2, height), arrowprops={'arrowstyle':'<->'})
		#text="d = "+str((x1-x2))+" mm"
		text="d = "+str(dis2_3)+" mm"
		self.distanceArrow=self.ax.text(x1+(x2-x1)*0.5-20*10, height+3*10,text)
	def move1(self,moveDis):
		xcurr=self.one.get_x()
		self.one.set_x(xcurr+moveDis)
		self.three.set_x(self.three.get_x()+moveDis)
		self.four.set_x(self.four.get_x()+moveDis)
		self.drawArrow()
		self.changeText(1)
	def move2(self,moveDis):
		xcurr=self.two.get_x()
		self.two.set_x(xcurr+moveDis)
		self.drawArrow()
		self.changeText(2)
	def move3(self,newpos):
		self.three.set_y(newpos)
		self.changeText(3)
	def move4(self,newpos):
		self.four.set_y(newpos)
		self.changeText(4)
	def updatePositions(self,pos):
		#pos[0]=-1*pos[0]
		#pos[1]=-1*pos[1]
		rand=6
		dis=70*10
		#pos=pos
		coord2=home2-pos[1]/200 #edge of array
		dis2_3=1037.18+(pos[1]-35115+(-101708-pos[0]))/200 #distance of 1037.18 at encoder positions 35115 and -101708
		coord3=coord2+dis2_3-arrayEdge_W #left side of target
		#coord4=magL/2-392.47+(-110932-pos[0])/200 #right side of FC, FC cup at distance 392.47mm at encoder position -110932 from trolley		
		coord1=coord3-target_sidespace
		coord4=coord1+oneW-detector_sidespace
		self.position1.remove()
		#self.one.set_x(pos[0]+homePositions[0])
		self.one.set_x(coord1)
		text="Position 1: "+str(-pos[0]*0.005)+" mm"
		self.position1=self.ax.text(self.xmin,self.ymax-rand,text,color=oneC)
		
		self.position2.remove()
		text="Position 2: "+str(-pos[1]*0.005)+" mm"
		self.position2=self.ax.text(self.xmin+dis,self.ymax-rand,text,color=arrayC)
		#self.array.set_x(pos[1]+homePositions[1])
		self.array.set_x(coord2+40.53-717.5)
		self.two.set_x(self.array.get_x()-array_sidespace)
		self.arrayEdge.set_x(self.array.get_x()+arrayW-arrayEdge_W)

		pos1=self.one.get_x()
		self.position3.remove()
		text="Position 3: "+str(pos[2]*0.005)+" mm"
		self.position3=self.ax.text(self.xmin+2*dis,self.ymax-rand,text,color=threeC)
		self.three.set_y(pos[2]*0.005-threeH/2)
		#self.three.set_x(pos1+detector_sidespace)
		self.three.set_x(coord3)
		
		self.position4.remove()
		text="Position 4: "+str(pos[3]*0.005)+" mm"
		self.position4=self.ax.text(self.xmin+3*dis,self.ymax-rand,text,color=fourC)
		self.four.set_y(pos[3]*0.005-fourH/2)
		#self.four.set_x(pos1+oneW-target_sidespace-threeW)
		self.four.set_x(coord4-fourW)
		self.FC.center=self.four.get_x()+0.5*fourW,self.four.get_y()+fourH/2+fcH
		self.dE.center=self.four.get_x()+0.5*fourW,self.four.get_y()+fourH/2+dEH
		
		
		self.drawArrow(dis2_3)
		self.number1.remove()
		self.number2.remove()
		self.number3.remove()
		self.number4.remove()
		self.placeNumbers()
		self.matplotpanel.canvas.draw()
	
	def placeNumbers(self):
		nSize=18
		self.number1=self.ax.text(self.one.get_x()+oneW/2,self.one.get_y()+0.75*oneH,"1",fontsize=nSize,horizontalalignment='center')
		self.number2=self.ax.text(self.two.get_x()+twoW/2,self.two.get_y()+0.75*twoH,"2",fontsize=nSize,horizontalalignment='center')
		self.number3=self.ax.text(self.three.get_x()+threeW/2,self.three.get_y()+0.7*threeH,"3",fontsize=nSize,horizontalalignment='center')
		self.number4=self.ax.text(self.four.get_x()+fourW/2,self.four.get_y()+0.7*fourH,"4",fontsize=nSize,horizontalalignment='center')
		

class MatplotPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent,-1,size=(10,10))
		self.driveView=DriveView(self)
		self.figure=self.driveView.get_figure()
		self.canvas = FigureCanvas(self, -1, self.figure)
		#Event Handlers
		self.Bind(EVT_POSUPDATE, self.updatePositions)

	def updatePositions(self,event):
		pos=event.GetValue()		
		self.driveView.updatePositions(pos)
	def move1(self,moveDis):
		self.driveView.move1(moveDis)
		self.canvas.draw()
	def move2(self,moveDis):
		self.driveView.move2(moveDis)
		self.canvas.draw()
	def move3(self,newpos):
		self.driveView.move3(newpos)
		self.canvas.draw()
	def move4(self,newpos):
		self.driveView.move4(newpos)
		self.canvas.draw()
		

class ControlView(wx.Panel):	
	"""
	Class that displays the upper part of the GUI with the buttons
	"""
   
	def __init__(self,parent,matplotpanel,frame):
		self.driveSystem=Library_DriveSystem.DriveSystem()
		
		self.frame=frame
		sizeX=100
		sizeY=100
		wx.Panel.__init__(self, parent, size=(sizeX,sizeY))
		self.SetBackgroundColour('#FFFFE0')
		self.matplotpanel=matplotpanel

		#Text Entries and Buttons
		#Sending Command
		writeSize=200
		a=25
		self.sendText = wx.StaticText(self, -1, "Send any command:", (5,5),style=wx.ALIGN_LEFT)
		self.writeCommand = wx.TextCtrl(self, -1, "", (5,a),size=(writeSize, -1))
		self.sendCommand = wx.Button(self, wx.ID_ANY, "Send", (writeSize+15, a))
		self.sendCommand.Bind(wx.EVT_BUTTON, self.sendingCommandB)
		self.sendCommand.SetDefault()
		self.currentAxis = wx.StaticText(self, -1, "Axis:", (5,58),style=wx.ALIGN_LEFT)
		self.responseText = wx.StaticText(self, -1, "Response:", (65,58),style=wx.ALIGN_LEFT)
		self.currentAx = wx.TextCtrl(self, wx.ID_ANY, "", (5,78),size=(60, -1), style=wx.ALIGN_LEFT|wx.TE_READONLY)
		self.commandResponse = wx.TextCtrl(self, wx.ID_ANY, "", (65,78),size=(200, -1), style=wx.ALIGN_LEFT|wx.TE_READONLY)

		#Abort/Reset Buttons
		self.aborted=False
		self.abortAllButton = wx.Button(self, wx.ID_ANY, "ABORT", (writeSize+15+100, a))
		self.abortAllButton.SetBackgroundColour("#FD3F0D") 
		self.abortAllButton.Bind(wx.EVT_BUTTON, self.abortAll)
		
		self.resetAllButton = wx.Button(self, wx.ID_ANY, "RESET", (writeSize+15+200, a)) 
		self.resetAllButton.Bind(wx.EVT_BUTTON, self.abortAll)

		#Print Encoder positions
		#self.printPos = wx.Button(self, wx.ID_ANY, "Print Pos.", (writeSize+15+300, a))
		self.printPos = wx.Button(self, wx.ID_ANY, "Print Pos.", (writeSize+15+60, 78)) 
		self.printPos.Bind(wx.EVT_BUTTON, self.printPosB)
		self.printRequest=False

		#Connect/Disconnect Buttons
		space=30
		offset=100
		h=-70
		buttonW=110
		sizey=(sizeY+offset)/5
		self.connectButton = wx.Button(self, wx.ID_ANY, "CONNECT", (frameWidth-buttonW,0),(buttonW,sizey))
		self.connectButton.Bind(wx.EVT_BUTTON, self.connectB)
		 

		self.disconnectButton = wx.Button(self, wx.ID_ANY, "DISCONNECT", (frameWidth-buttonW,sizey),(buttonW,sizey))
		self.disconnectButton.Bind(wx.EVT_BUTTON, self.disconnectB)
		

		self.quitButton = wx.Button(self, wx.ID_ANY, "QUIT", (frameWidth-buttonW,sizey*4),(buttonW,sizey))
		self.quitButton.Bind(wx.EVT_BUTTON, self.quitB)
		self.quitButton.SetBackgroundColour("#FD3F0D")# #DC143C #FF3030

		self.helpButton = wx.Button(self, wx.ID_ANY, "HELP", (frameWidth-buttonW,sizey*3),(buttonW,sizey))
		self.helpButton.Bind(wx.EVT_BUTTON, self.openHelp)

		if self.driveSystem.checkConnection()==True:
			self.disconnectButton.SetBackgroundColour("#FD3F0D") #EE4000
			self.connectButton.Enable(False)
		else:
			self.connectButton.SetBackgroundColour("#7FFF00")#'#0DE30B'
			self.disconnectButton.Enable(False)
		
		#Settings
		self.settingsButton = wx.Button(self, wx.ID_ANY, "Settings", (frameWidth-buttonW,sizey*2),(buttonW,sizey))
		self.settingsButton.Bind(wx.EVT_BUTTON, self.settingConstants)

		#Home Buttons		
		h=-70
		dx=(frameWidth-buttonW)/4
		dy=29
		dis=dx
		self.Home1Button = wx.Button(self, wx.ID_ANY, "DATUM 1", (0,sizeY-h),(dx,dy))
		self.Home1Button.Bind(wx.EVT_BUTTON, self.home1B)
		self.Home2Button = wx.Button(self, wx.ID_ANY, "DATUM 2", (dis,sizeY-h),(dx,dy))
		self.Home2Button.Bind(wx.EVT_BUTTON, self.home2B)
		self.Home3Button = wx.Button(self, wx.ID_ANY, "DATUM 3", (2*dis,sizeY-h),(dx,dy))
		self.Home3Button.Bind(wx.EVT_BUTTON, self.home3B)
		self.Home4Button = wx.Button(self, wx.ID_ANY, "DATUM 4", (3*dis,sizeY-h),(dx,dy))
		self.Home4Button.Bind(wx.EVT_BUTTON, self.home4B)

		
		disy=sizeY+30
		#Move 1 and 2
		self.move1Insert = wx.TextCtrl(self, wx.ID_ANY, "", (5,disy))
		self.move1Button = wx.Button(self, wx.ID_ANY, "Move 1 \n [mm]", (105, disy-12))
		self.move1Button.Bind(wx.EVT_BUTTON, self.move1B)
		self.move2Insert = wx.TextCtrl(self, wx.ID_ANY, "", (dis,disy))
		self.move2Button = wx.Button(self, wx.ID_ANY, "Move 2 \n [mm]", (dis+100, disy-12))
		self.move2Button.Bind(wx.EVT_BUTTON, self.move2B)

		#Target Position Selection
		self.TargetPos = wx.StaticText(self, -1, "Target Position:", (2*dis,disy+5-40))
		#alpha=r'$\alpha_i$'
		self.targetChoice=wx.Choice(self, wx.ID_ANY, pos=(2*dis+110,disy-3-40), size=(80,-1),choices=["alpha","1","2","3","4","5","6","7","8"])
		self.targetChoice.Bind(wx.EVT_CHOICE, self.setTargetPosB)
		self.move3Insert = wx.TextCtrl(self, wx.ID_ANY, "", (2*dis+45,disy),size=(55, -1))
		self.movePlus3Button = wx.Button(self, wx.ID_ANY, "+", (2*dis+105,disy),size=(40, -1))
		self.UnitText3 = wx.StaticText(self, -1, "[mm]", pos=(2*dis+105+50,disy+10))
		self.moveMinus3Button = wx.Button(self, wx.ID_ANY, "-", (2*dis,disy),size=(40, -1))
		self.movePlus3Button.Bind(wx.EVT_BUTTON, self.movePlus3B)
		self.moveMinus3Button.Bind(wx.EVT_BUTTON, self.moveMinus3B)

		#Detector Option
		self.detectorList=["dE/dx","FC","Center"]
		self.detectorChoice = wx.RadioBox(self, -1, "Detector Position:", (3*dis,disy-5-45), wx.DefaultSize,self.detectorList, 3, wx.RA_SPECIFY_COLS)		
		self.detectorChoice.SetSelection(2)
		self.Bind(wx.EVT_RADIOBOX, self.setDetectorPosB, self.detectorChoice)
		self.move4Insert = wx.TextCtrl(self, wx.ID_ANY, "", (3*dis+45,disy),size=(55, -1))
		self.movePlus4Button = wx.Button(self, wx.ID_ANY, "+", (3*dis+105,disy),size=(40, -1))
		self.UnitText4 = wx.StaticText(self, -1, "[mm]", pos=(3*dis+105+50,disy+10))
		self.moveMinus4Button = wx.Button(self, wx.ID_ANY, "-", (3*dis,disy),size=(40, -1))
		self.movePlus4Button.Bind(wx.EVT_BUTTON, self.movePlus4B)
		self.moveMinus4Button.Bind(wx.EVT_BUTTON, self.moveMinus4B)


		#Positions Constants
		data=np.genfromtxt('Positions.txt')
		self.detectorPositions=data[:,1]
		self.targetPositions=data[:,0]
		self.checkPositionsOn34()

		'''
		with open(os.path.expanduser('~.positions.txt'),'r') as f:
			data=np.genfromtxt(f,skip_header=0)
			#self.detectorPositions=data[:,1]
			#self.targetPositions=data[:,0]
			print(data[:,1])
		f.close()
		'''
		#Create the queue that the Thread checks
		self.q=queue.Queue()

		#Event Handlers
		self.Bind(EVT_DISCONNECT, self.changeViewDisconnect)
		#Start Thread which checks continously the positions
		self.positionsChecker=CheckPositions(self,self.driveSystem)#
		self.positionsChecker.start()
		
	
	def changeViewDisconnect(self,event):
		value=event.GetValue()
		if value==1:
			self.disconnectButton.SetBackgroundColour("#EE4000") 
			self.connectButton.Enable(False)
			self.connectButton.SetBackgroundColour("grey") 
			self.disconnectButton.Enable(True)
		else:
			self.connectButton.SetBackgroundColour("#7FFF00")#'#0DE30B'
			self.disconnectButton.Enable(False)
			self.disconnectButton.SetBackgroundColour("grey") 
			self.connectButton.Enable(True)

	def printPosB(self,event):
		self.printRequest=True
	
	def sendingCommandB(self,event):
		command = self.writeCommand.GetValue() + '\r'
		command = bytes( command.encode('ascii') )
		element=Element('S',0,command)
		self.q.put(element)

	def sendingCommand(self,cmd):
		command=cmd
		print("Send command "+command.decode())
		ax,answer=self.driveSystem.executeCommand(command)
		if ax!=None:
			self.currentAx.SetValue(ax)
			self.commandResponse.SetValue(answer)

	def connectB(self,event):
		print("Connect")
		self.driveSystem.connect_to_port()
		event = DisConnectEvent(myEVT_DISCONNECT, -1, 1)
		wx.PostEvent(self, event)
	
	def disconnectB(self,event):
		element=Element('D')
		self.q.put(element)
	def disconnect(self):
		print("Disconnect")
		self.driveSystem.disconnect_port()
		event = DisConnectEvent(myEVT_DISCONNECT, -1, 0)
		wx.PostEvent(self, event)
	def quitB(self,event):
		if self.driveSystem.checkConnection()==True:
			element=Element('Q')
			self.q.put(element)
		else:
			self.quit()
		
	def quit(self):
		print("Quit")
		self.frame.Destroy()
		self.frame.closeProgram()
		exit()
	
	def home1B(self,event):
		element=Element('H',1)
		self.q.put(element)
	def home1(self):
		print("Home 1")
		self.driveSystem.datum_search(1)

	def home2B(self,event):
		element=Element('H',2)
		self.q.put(element)
	def home2(self):
		print("Home 2")
		self.driveSystem.datum_search(2)
		
	def home3B(self,event):
		element=Element('H',3)
		self.q.put(element)
	def home3(self):
		print("Home 3")
		self.driveSystem.datum_search(3)

	def home4B(self,event):
		element=Element('H',4)
		self.q.put(element)
	def home4(self):
		print("Home 4")
		self.driveSystem.datum_search(4)
	
	def move1B(self,event):
		element=Element('M',1)
		self.q.put(element)
	def move1(self):
		moveDis = -1*float(self.move1Insert.GetValue())
		print("The motor of axis 1 is defect")
		#if the motor works again:
		#self.driveSystem.move_rel(1,int(moveDis*200))
	
	def move2B(self,event):
		element=Element('M',2)
		self.q.put(element)
	def move2(self):
		moveDis = -1*float(self.move2Insert.GetValue())
		print("Move 2")
		#assume that moveDis is in mm
		self.driveSystem.move_rel(2,int(moveDis*200))

	def setTargetPosB(self,event):
		element=Element('M',3)
		self.q.put(element)
	def setTargetPos(self):
		newposition=self.targetChoice.GetSelection()
		print("Target position changed to position "+str(newposition+1))
		self.driveSystem.select_pos(3,self.targetPositions[newposition]*200)

	def setDetectorPosB(self,event):
		element=Element('M',4)
		self.q.put(element)
	def setDetectorPos(self):
		newposition=self.detectorChoice.GetSelection()
		if newposition==0:
			print("Detector position change to position dE/dx")
		elif newposition==1:
			print("Detector position change to position Faraday cup")
		elif newposition==2:
			print("dE/dx detector and FC moves out of the way")
		self.driveSystem.select_pos(4,self.detectorPositions[newposition]*200)
	
	def movePlus3B(self,event):
		disMM = float(self.move3Insert.GetValue())
		#Multiply distance in mm with 200 to obtain number of steps
		element=Element('M+-',3,int(disMM*200))
		self.q.put(element)
	
	def moveMinus3B(self,event):
		disMM = -1*float(self.move3Insert.GetValue())
		element=Element('M+-',3,int(disMM*200))
		self.q.put(element)

	
	def movePlus4B(self,event):
		disMM = float(self.move4Insert.GetValue())
		element=Element('M+-',4,int(disMM*200))
		self.q.put(element)
	
	def moveMinus4B(self,event):
		disMM = -1*float(self.move4Insert.GetValue())
		element=Element('M+-',4,int(disMM*200))
		self.q.put(element)
	

	def movePlusMinus(self,axis,steps):
		self.driveSystem.move_rel(axis,steps)
	
	def settingConstants(self,event):
		secondwindow=SettingsWindow(self, "Setting Positions")
		secondwindow.Show()
	def openHelp(self,event):
		secondwindow=HelpWindow(self, "Help")
		secondwindow.Show()

	def abortAll(self,event):
		self.driveSystem.abortAll()
		self.aborted=True
	def resetAll(self,event):
		self.driveSystem.resetAll()
		self.aborted=False
	def checkPositionsOn34(self):
		self.driveSystem.check_encoder_pos_axis( 3 )
		self.driveSystem.check_encoder_pos_axis( 4 )
		pos3=self.driveSystem.positions[2]
		pos4=self.driveSystem.positions[3]
		for i in range(9):
			if (pos3/200) < (self.targetPositions[i]+0.1) and (pos3/200) > (self.targetPositions[i]-0.1):
				self.targetChoice.SetSelection(i)
				break
		for i in range(3):
			if (pos4/200) < (self.detectorPositions[i]+0.1) and (pos4/200) > (self.detectorPositions[i]-0.1):
				self.detectorChoice.SetSelection(i)
				break
		
		

class DriveSystemGUI(wx.Frame):
	def __init__(self, parent, mytitle):
		super(DriveSystemGUI, self).__init__(parent, title=mytitle,size=(frameWidth,frameHeight))
		self.InitUI()
		self.Centre()

	def InitUI(self):
		self.split_win = wx.SplitterWindow(self)
		self.bottom_split = MatplotPanel(self.split_win) 
		self.top_split = ControlView(self.split_win,self.bottom_split,self)
		self.split_win.SplitHorizontally(self.top_split, self.bottom_split, controlViewSize)
	def closeProgram(self):
		self.Destroy()
		self.Close()
		

class SettingsWindow(wx.Frame):
	def __init__(self, parent, mytitle):
		#super(SettingsWindow, self).__init__(parent, title=mytitle,size=(200,700))
		wx.Frame.__init__(self, None, wx.ID_ANY, title=mytitle)
		self.parent=parent
		self.InitUI()
		self.Centre()
	def InitUI(self):
		self.panel=wx.Panel(self,wx.ID_ANY)

		#Target Positions
		pos=[]
		for i in range(9):
			pos+=[str(self.parent.targetPositions[i])]
		targTitle = wx.StaticText(self.panel, wx.ID_ANY, 'Target Positions\n[mm]',style=wx.ALIGN_CENTRE_HORIZONTAL)
		targ0label = wx.StaticText(self.panel, wx.ID_ANY, 'Alpha\nsource')
		self.targ0input = wx.TextCtrl(self.panel, wx.ID_ANY, pos[0])
		targ1label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 1')
		self.targ1input = wx.TextCtrl(self.panel, wx.ID_ANY, pos[1])
		targ2label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 2')
		self.targ2input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[2])
		targ3label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 3')
		self.targ3input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[3])
		targ4label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 4')
		self.targ4input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[4])
		targ5label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 5')
		self.targ5input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[5])
		targ6label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 6')
		self.targ6input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[6])
		targ7label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 7')
		self.targ7input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[7])
		targ8label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 8')
		self.targ8input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[8])

		#Detector Positions
		detTitle = wx.StaticText(self.panel, wx.ID_ANY, 'Detector Positions\n[mm]',style=wx.ALIGN_CENTRE_HORIZONTAL)
		det0label = wx.StaticText(self.panel, wx.ID_ANY, 'dE/dx')
		pos0=str(self.parent.detectorPositions[0])
		self.det0input = wx.TextCtrl(self.panel, wx.ID_ANY, pos0)
		det1label = wx.StaticText(self.panel, wx.ID_ANY, 'FC')
		pos1=str(self.parent.detectorPositions[1])
		self.det1input = wx.TextCtrl(self.panel, wx.ID_ANY, pos1)
		det2label = wx.StaticText(self.panel, wx.ID_ANY, 'Center')
		pos2=str(self.parent.detectorPositions[2])
		self.det2input = wx.TextCtrl(self.panel, wx.ID_ANY, pos2)
		
		#Ok and Cancel Buttons
		okBtn = wx.Button(self.panel, wx.ID_ANY, 'OK')
		cancelBtn = wx.Button(self.panel, wx.ID_ANY, 'Cancel')
		self.Bind(wx.EVT_BUTTON, self.onOK, okBtn)
		self.Bind(wx.EVT_BUTTON, self.onCancel, cancelBtn)

		#Defining the boxes		
		topSizer        = wx.BoxSizer(wx.VERTICAL)
		targTitleSizer      = wx.BoxSizer(wx.HORIZONTAL)
		targ0Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ1Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ2Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ3Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ4Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ5Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ6Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ7Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ8Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		detTitleSizer      = wx.BoxSizer(wx.HORIZONTAL)
		det0Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		det1Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		det2Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		btnSizer        = wx.BoxSizer(wx.HORIZONTAL)

		#Adding the items to the boxes
		targTitleSizer.Add(targTitle, 0, wx.ALL, 5)
		targ0Sizer.Add(targ0label, 0, wx.ALL, 5)
		targ0Sizer.Add(self.targ0input, 1, wx.ALL|wx.EXPAND, 5)
		targ1Sizer.Add(targ1label, 0, wx.ALL, 5)
		targ1Sizer.Add(self.targ1input, 1, wx.ALL|wx.EXPAND, 5)
		#targ1Sizer.Add(targ1unit, 0, wx.ALL, 5)
		targ2Sizer.Add(targ2label, 0, wx.ALL, 5)
		targ2Sizer.Add(self.targ2input, 1, wx.ALL|wx.EXPAND, 5)
		targ3Sizer.Add(targ3label, 0, wx.ALL, 5)
		targ3Sizer.Add(self.targ3input, 1, wx.ALL|wx.EXPAND, 5)
		targ4Sizer.Add(targ4label, 0, wx.ALL, 5)
		targ4Sizer.Add(self.targ4input, 1, wx.ALL|wx.EXPAND, 5)
		targ5Sizer.Add(targ5label, 0, wx.ALL, 5)
		targ5Sizer.Add(self.targ5input, 1, wx.ALL|wx.EXPAND, 5)
		targ6Sizer.Add(targ6label, 0, wx.ALL, 5)
		targ6Sizer.Add(self.targ6input, 1, wx.ALL|wx.EXPAND, 5)
		targ7Sizer.Add(targ7label, 0, wx.ALL, 5)
		targ7Sizer.Add(self.targ7input, 1, wx.ALL|wx.EXPAND, 5)
		targ8Sizer.Add(targ8label, 0, wx.ALL, 5)
		targ8Sizer.Add(self.targ8input, 1, wx.ALL|wx.EXPAND, 5)
		detTitleSizer.Add(detTitle, 0, wx.ALL, 5)
		det0Sizer.Add(det0label, 0, wx.ALL, 5)
		det0Sizer.Add(self.det0input, 1, wx.ALL|wx.EXPAND, 5)
		det1Sizer.Add(det1label, 0, wx.ALL, 5)
		det1Sizer.Add(self.det1input, 1, wx.ALL|wx.EXPAND, 5)
		det2Sizer.Add(det2label, 0, wx.ALL, 5)
		det2Sizer.Add(self.det2input, 1, wx.ALL|wx.EXPAND, 5)
		btnSizer.Add(okBtn, 0, wx.ALL, 5)
		btnSizer.Add(cancelBtn, 0, wx.ALL, 5)

		#Adding the horizontal boxes to the vertical box
		topSizer.Add(targTitleSizer, 0, wx.CENTER)
		topSizer.Add(wx.StaticLine(self.panel,), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ0Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ1Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ2Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ3Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ4Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ5Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ6Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ7Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ8Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(detTitleSizer, 0, wx.CENTER)
		topSizer.Add(wx.StaticLine(self.panel,), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(det0Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(det1Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(det2Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(btnSizer, 0, wx.ALL|wx.CENTER, 5)

		self.panel.SetSizer(topSizer)
		topSizer.Fit(self)

	def onOK(self, event):
		# Do something
		print("Saved new positions")
		self.parent.detectorPositions[0]=float(self.det0input.GetValue())
		self.parent.detectorPositions[1]=float(self.det1input.GetValue())
		self.parent.detectorPositions[2]=float(self.det2input.GetValue())
		self.parent.targetPositions[0]=float(self.targ0input.GetValue())
		self.parent.targetPositions[1]=float(self.targ1input.GetValue())
		self.parent.targetPositions[2]=float(self.targ2input.GetValue())
		self.parent.targetPositions[3]=float(self.targ3input.GetValue())
		self.parent.targetPositions[4]=float(self.targ4input.GetValue())
		self.parent.targetPositions[5]=float(self.targ5input.GetValue())
		self.parent.targetPositions[6]=float(self.targ6input.GetValue())
		self.parent.targetPositions[7]=float(self.targ7input.GetValue())
		self.parent.targetPositions[8]=float(self.targ8input.GetValue())

		'''
		#Write values to a hidden file
		with open(os.path.expanduser('~.positions.txt'),'w') as f:
			for i in range(8):
				f.write(str(self.parent.targetPositions[i])+' '+str(self.parent.detectorPositions[i])+'\n')
		f.close()
		'''
		#Write values to a file
		f=open("Positions.txt","w")
		for i in range(9):
			f.write(str(self.parent.targetPositions[i])+' '+str(self.parent.detectorPositions[i])+'\n')
		self.Destroy()
		self.Close()
	
	def onCancel(self, event):
		self.Close()
		print("No changes in positions were made")

class HelpWindow(wx.Frame):
	def __init__(self, parent, mytitle):
		self.width=430
		self.height=500
		super(HelpWindow, self).__init__(parent, title=mytitle,size=(self.width,self.height))
		self.InitUI()
		self.Centre()
		'''
		#wx.Frame.__init__(self, None, wx.ID_ANY, title=mytitle)
		self.parent=parent
		self.InitUI()
		self.Centre()
		'''
	def InitUI(self):
		self.panel=TestPanel(self)
	def onClose(self):
		self.Close()
		self.Destroy()

import wx.lib.scrolledpanel as scrolled

class TestPanel(scrolled.ScrolledPanel):

	def __init__(self, parent):

		scrolled.ScrolledPanel.__init__(self, parent, -1)
		self.parent=parent
	
		vbox = wx.BoxSizer(wx.VERTICAL)
		text1="This is a GUI for controlling the Drive System.\nThe Drive System contains four axes:\n\nAxis 1: Trolley\nAxis 2: Array\nAxis 3: Target\nAxis 4: Faraday cup and dE/dx detector\n\nwhich are represented by the four colored\nrectangulars.\nThe coordinate system of the GUI is in millimeters,\nand is centered around the middle of the magnet.\nThis means, that the limits are +-2730/2 mm = +-1365 mm.\nThe GUI allows to move the objects on the axes in the unit\nof millimeters by inserting the desired value and clicking on\nthe corresponding button (Move1, Move2 ,+/-).\nThe smallest step is 0.005 mm = 1/200 mm. The positions on\nthe axes are checked and updated in the GUI every second."
		text2="In the case of axis 3 and axis 4, it is possible to choose\nbetween eight target positions and two detector positions\nrespectiveley. The corresponding encoder positions can be\nchanged via the window 'Settings'. By clicking on the 'Ok'\nButton, the new positions will be saved.\nThe arrow indicates the distance between the end of\nthe array and the target.\n\nOther actions the GUI offers are:\n- Abort command on all axes\n- Reset all axes\n- Connect/Disconnect to the port\n- Quit: this will close the GUI\n- Datum search: The datum/zero position on the axis will be\nsearched. When the datum position is found,\ncheck with the command OD if the datum position is\nequal to zero. If not use DA-x with x being the datum position\nto set it to zero."
		text3="\n\nFurthermore in the top left corner of the GUI, there is the\nopportunity to send any kind of command (all available\ncommands can be found in the Drive System's handbook)."
		text4="IMPORTANT NOTE: "
		text5="If you want to move axes 1 and 2 via the 'Send' button or the\ncontrol stick in the experimental hall,\nplease note that the GUI's coordinate system is only correct\nfor axes 3 and 4. For axes 1 and 2, it is in the opposite direc-\ntion, so if you want to move them according to the GUI's\ncoordinate system you have to enter the negative value."
		text=text1+'\n'+text2+text3
		desc1 = wx.StaticText(self, -1, text)
		desc1.SetForegroundColour("Blue")
		desc2 = wx.StaticText(self, -1, text4)
		desc2.SetForegroundColour("Red")
		desc3 = wx.StaticText(self, -1, text5)
		desc3.SetForegroundColour("Blue")
		closeButton = wx.Button(self, wx.ID_ANY, 'Close')
		self.Bind(wx.EVT_BUTTON, self.onClose, closeButton)
	
		
		vbox.Add(desc1, 0, wx.ALIGN_LEFT | wx.ALL, 5)
		vbox.Add(desc2, 0, wx.ALIGN_LEFT | wx.ALL, 5)
		vbox.Add(desc3, 0, wx.ALIGN_LEFT | wx.ALL, 5)
		vbox.Add(wx.StaticLine(self, -1, size=(1024, -1)), 0, wx.ALL, 5)
		vbox.Add(closeButton)
		vbox.Add((20, 20))
		
		self.SetSizer(vbox)
		self.SetupScrolling()
	
	def onClose(self, event):
		self.parent.onClose()





def main():		
	app = wx.App()
	gui = DriveSystemGUI(None, "Drive System")
	gui.Show()
	app.MainLoop()


if __name__ == '__main__':
	main()
