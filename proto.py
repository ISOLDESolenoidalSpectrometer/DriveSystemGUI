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
import queues

#----------Constants-------------------
#Frame size constants
frameHeight=740
frameWidth=1000
controlViewSize=200

#Rectangles
oneW=70
oneH=65
twoW=70
twoH=30
threeW=10
threeH=15
fourW=10
fourH=15
target_sidespace=10
detector_sidespace=10
one_sidespace=100
#Colours

oneC='y'
twoC='r'
threeC='g'
fourC='b'

#Frequency por the positons checking
UPDATE_TIME=2

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
		while self._driveSystem.port_open == True :
			self._driveSystem.check_encoder_pos()
			pos=self._driveSystem.positions
			event = PosUpdateEvent(myEVT_POSUPDATE, -1, pos)
			wx.PostEvent(self._parent.matplotpanel, event)
			time.sleep(UPDATE_TIME)
			print("Check")
			self.checkQ()
	def checkQ(self):
		element=self._parent.q.root
		while(element!=None):
			self.action(element)
			e=element.next
			self._parent.q.remove(element)
			element=e
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
		self.ymin=-40
		self.ymax=60
		self.xmin=-200
		self.xmax=200
		
		self.ax = plt.axes(xlim=(self.xmin, self.xmax), ylim=(self.ymin,self.ymax))
		self.ax.spines['right'].set_color('none')
		self.ax.spines['top'].set_color('none')
		#ax.set_xticks(np.arange(-500, 500, step=100))
		self.ax.set_yticks([])
		self.ax.spines['left'].set_color('none')
		self.ax.spines['bottom'].set_position(('data',0))
		majorLocator = MultipleLocator(100)
		#majorFormatter = FormatStrFormatter('%d')
		minorLocator = MultipleLocator(10)
		self.ax.xaxis.set_major_locator(majorLocator)
		#ax.xaxis.set_major_formatter(majorFormatter)

		# for the minor ticks, use no labels; default NullFormatter
		self.ax.xaxis.set_minor_locator(minorLocator)
		#ax.grid()
		
		#Adding the four rectangles
		self.one = plt.Rectangle((self.xmin, -oneH/2), oneW, oneH, fc=oneC)
		self.ax.add_patch(self.one)
		self.two = plt.Rectangle((self.xmax-twoW-30, -twoH/2), twoW, twoH, fc=twoC)
		self.ax.add_patch(self.two)
		self.four = plt.Rectangle((self.xmin+detector_sidespace, -threeH/2), threeW, threeH, fc=fourC)
		self.ax.add_patch(self.four)
		self.three = plt.Rectangle((self.xmin+oneW-target_sidespace-threeW, -threeH/2), threeW, threeH, fc=threeC)
		self.ax.add_patch(self.three)

		#Adding information about position
		dis=90
		rand=2
		plt.rcParams.update({'font.size': 12})
		self.position1=self.ax.text(self.xmin,self.ymax-rand,"Position 1: "+str(self.one.get_x()),color=oneC)
		self.position2=self.ax.text(self.xmin+dis-5,self.ymax-rand,"Position 2: "+str(self.two.get_x()),color=twoC)
		self.position3=self.ax.text(self.xmin+2*dis,self.ymax-rand,"Position 3: "+str(self.three.get_y()),color=threeC)
		self.position4=self.ax.text(self.xmin+3*dis+5,self.ymax-rand,"Position 4: "+str(self.four.get_y()),color=fourC)
		
		#self.targetPos=self.ax.text(xmin+2*dis,ymax-10,"Target Position: "+str(1),color=threeC)
		#self.detectorPos=self.ax.text(xmin+3*dis,ymax-10,"Detector Position: dE or dE/dx",color=fourC)

		#Arrow who shows the distance
		self.arrow=self.ax.annotate ('', (-100, 100), (100, 100), arrowprops={'arrowstyle':'<->'})
		self.distanceArrow=self.ax.text(0,0,"")
		self.drawArrow()

		#Makes the space at the sides of the diagrams smaller
		self.fig.tight_layout()

		

	def get_figure(self):
		return self.fig
	def drawArrow(self):
		self.arrow.remove()
		self.distanceArrow.remove()
		x1=self.three.get_x()+threeW
		x2=self.two.get_x()
		height=twoH/2
		self.arrow=self.ax.annotate ('', (x1, height), (x2, height), arrowprops={'arrowstyle':'<->'})
		text="d = "+str(x2-x1)+" mm"
		self.distanceArrow=self.ax.text(x1+(x2-x1)*0.5-20, height+3,text)
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
		rand=2
		dis=90
		pos=pos*0.005
		self.position1.remove()
		if pos[0]==None:
			text="Position 1: 0"
			self.one.set_x(0)
		else:
			self.one.set_x(pos[0])
			text="Position 1: "+str(pos[0])
		self.position1=self.ax.text(self.xmin,self.ymax-rand,text,color=oneC)
		
		
		self.position2.remove()
		text="Position 2: "+str(pos[1])
		self.position2=self.ax.text(self.xmin+dis,self.ymax-rand,text,color=twoC)
		self.two.set_x(pos[1])		

		pos1=self.one.get_x()
		self.position3.remove()
		text="Position 3: "+str(pos[2])
		self.position3=self.ax.text(self.xmin+2*dis,self.ymax-rand,text,color=threeC)
		self.three.set_y(pos[2])
		self.three.set_x(pos1+oneW-target_sidespace-threeW)
		
		self.position4.remove()
		text="Position 4: "+str(pos[3])
		self.position4=self.ax.text(self.xmin+3*dis,self.ymax-rand,text,color=fourC)
		self.four.set_y(pos[3])
		self.four.set_x(pos1+detector_sidespace)
		self.drawArrow()
		self.matplotpanel.canvas.draw()
		
	
	def changeText(self,number):
		rand=2
		dis=80
		if number==1:
			self.position1.remove()
			self.position3.remove()
			self.position4.remove()
			text="Position 1: "+str(self.one.get_x())
			self.position1=self.ax.text(self.xmin,self.ymax-rand,text,color=oneC)
			text="Position 3: "+str(self.three.get_y())
			self.position3=self.ax.text(self.xmin+2*dis,self.ymax-rand,text,color=threeC)
			text="Position 4: "+str(self.four.get_y())
			self.position4=self.ax.text(self.xmin+3*dis,self.ymax-rand,text,color=fourC)
		if number==2:
			self.position2.remove()
			text="Position 2: "+str(self.two.get_x())
			self.position2=self.ax.text(self.xmin+dis,self.ymax-rand,text,color=twoC)
		if number==3:
			self.position3.remove()
			text="Position 3: "+str(self.three.get_y())
			self.position3=self.ax.text(self.xmin+2*dis,self.ymax-rand,text,color=threeC)
		if number==4:
			self.position4.remove()
			text="Position 4: "+str(self.four.get_y())
			self.position4=self.ax.text(self.xmin+3*dis,self.ymax-rand,text,color=fourC)

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
		self.currentAxis = wx.StaticText(self, -1, "Axis:", (5,58),style=wx.ALIGN_LEFT)
		self.responseText = wx.StaticText(self, -1, "Response:", (65,58),style=wx.ALIGN_LEFT)
		self.currentAx = wx.TextCtrl(self, wx.ID_ANY, "", (5,78),size=(60, -1), style=wx.ALIGN_LEFT|wx.TE_READONLY)
		self.commandResponse = wx.TextCtrl(self, wx.ID_ANY, "", (65,78),size=(200, -1), style=wx.ALIGN_LEFT|wx.TE_READONLY)

		#Connec/Disconnect Buttons
		space=30
		offset=100
		h=-70
		buttonW=110
		sizey=(sizeY+offset)/4
		self.connectButton = wx.Button(self, wx.ID_ANY, "CONNECT", (frameWidth-buttonW,0),(buttonW,sizey))
		self.connectButton.Bind(wx.EVT_BUTTON, self.connectB)
		 

		self.disconnectButton = wx.Button(self, wx.ID_ANY, "DISCONNECT", (frameWidth-buttonW,sizey),(buttonW,sizey))
		self.disconnectButton.Bind(wx.EVT_BUTTON, self.disconnectB)
		

		self.quitButton = wx.Button(self, wx.ID_ANY, "QUIT", (frameWidth-buttonW,sizey*3),(buttonW,sizey))
		self.quitButton.Bind(wx.EVT_BUTTON, self.quitB)
		self.quitButton.SetBackgroundColour("#FF3030")# #DC143C

		if self.driveSystem.checkConnection()==True:
			self.disconnectButton.SetBackgroundColour("#EE4000") 
			self.connectButton.Enable(False)
		else:
			self.connectButton.SetBackgroundColour("#7FFF00")
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
		self.move1Insert = wx.TextCtrl(self, wx.ID_ANY, "", (0,disy))
		self.move1Button = wx.Button(self, wx.ID_ANY, "Move 1", (100, disy))
		self.move1Button.Bind(wx.EVT_BUTTON, self.move1B)
		self.move2Insert = wx.TextCtrl(self, wx.ID_ANY, "", (dis,disy))
		self.move2Button = wx.Button(self, wx.ID_ANY, "Move 2", (dis+100, disy))
		self.move2Button.Bind(wx.EVT_BUTTON, self.move2B)

		#Target Position Selection
		self.TargetPos = wx.StaticText(self, -1, "Target Position:", (2*dis,disy+5))
		self.targetChoice=wx.Choice(self, wx.ID_ANY, pos=(2*dis+120,disy-3), size=(50,-1),choices=["1","2","3","4","5"])
		self.targetChoice.SetSelection(1)
		self.targetChoice.Bind(wx.EVT_CHOICE, self.setTargetPosB)

		#Detector Option
		self.detectorList=["dE","dE/dx"]
		self.detectorChoice = wx.RadioBox(self, -1, "Detector Position:", (3*dis,disy-5), wx.DefaultSize,self.detectorList, 2, wx.RA_SPECIFY_COLS)		
		self.Bind(wx.EVT_RADIOBOX, self.setDetectorPosB, self.detectorChoice)


		#Positions Constants
		self.detectorPositions=np.array([-threeH/2,0])
		self.targetPositions=np.array([-15,-fourH/2,-5,0,5,10])

		#Create the queue that the Thread checks
		self.q=queues.SingleQueue()

		#Start Thread which checks continously the positions
		self.positionsChecker=CheckPositions(self,self.driveSystem)#
		self.positionsChecker.start()
		
		
	def sendingCommandB(self,event):
		command = self.writeCommand.GetValue() + '\r'
		command = bytes( command.encode('ascii') )
		element=queues.Element('S',0,command)
		self.q.add(element)

	def sendingCommand(self,cmd):
		command=cmd
		print("Send command "+command.decode())
		ax,answer=self.driveSystem.executeCommand(command)
		self.currentAx.SetValue(ax)
		self.commandResponse.SetValue(answer)

	def connectB(self,event):
		print("Connect")
		self.driveSystem.connect_to_port()
		self.positionsChecker=None
		self.connectButton.SetBackgroundColour("grey") 
		self.disconnectButton.Enable(True)
		self.disconnectButton.SetBackgroundColour("#EE4000")
		self.connectButton.Enable(False)
		self.positionsChecker=CheckPositions(self,self.driveSystem)
		self.positionsChecker.start()
		#element=queues.Element('C')
		#self.q.add(element)
	def connect(self):
		#nothing
		print("connect")

	def disconnectB(self,event):
		element=queues.Element('D')
		self.q.add(element)
	def disconnect(self):
		print("Disconnect")
		self.driveSystem.disconnect_port()
		self.disconnectButton.SetBackgroundColour("grey") 
		self.connectButton.Enable(True)
		self.connectButton.SetBackgroundColour("#7FFF00")
		self.disconnectButton.Enable(False)

	def quitB(self,event):
		element=queues.Element('Q')
		self.q.add(element)
	def quit(self):
		print("Quit")
		self.frame.closeProgram()
	
	def home1B(self,event):
		element=queues.Element('H',1)
		self.q.add(element)
	def home1(self):
		print("Home 1")
		self.driveSystem.datum_search(1)

	def home2B(self,event):
		element=queues.Element('H',2)
		self.q.add(element)
	def home2(self):
		print("Home 2")
		self.driveSystem.datum_search(2)
		
	def home3B(self,event):
		element=queues.Element('H',3)
		self.q.add(element)
	def home3(self):
		print("Home 3")
		self.driveSystem.datum_search(3)

	def home4B(self,event):
		element=queues.Element('H',4)
		self.q.add(element)
	def home4(self):
		print("Home 4")
		self.driveSystem.datum_search(4)
	
	def move1B(self,event):
		element=queues.Element('M',1)
		self.q.add(element)
	def move1(self):
		moveDis = float(self.move1Insert.GetValue())
		print("Move 1")
		self.matplotpanel.move1(moveDis)
	
	def move2B(self,event):
		element=queues.Element('M',2)
		self.q.add(element)
	def move2(self):
		moveDis = float(self.move2Insert.GetValue())
		print("Move 2")
		self.matplotpanel.move2(moveDis)

	def setTargetPosB(self,event):
		element=queues.Element('M',3)
		self.q.add(element)
	def setTargetPos(self):
		newposition=self.targetChoice.GetSelection()
		print("Target position changed to position "+str(newposition+1))
		self.matplotpanel.move3(self.targetPositions[newposition])

	def setDetectorPosB(self,event):
		element=queues.Element('M',4)
		self.q.add(element)
	def setDetectorPos(self):
		newposition=self.detectorChoice.GetSelection()
		if newposition==0:
			print("Detector position changed to position dE")
		else:
			print("Detector position changed to position dE/dx")
		self.matplotpanel.move4(self.detectorPositions[newposition])

	def settingConstants(self,event):
		secondwindow=SettingsWindow(self, "Setting Positions")
		secondwindow.Show()

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
		for i in range(5):
			pos+=[str(self.parent.targetPositions[i])]
		targTitle = wx.StaticText(self.panel, wx.ID_ANY, 'Target Positions')
		targ1label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 1')
		self.targ1input = wx.TextCtrl(self.panel, wx.ID_ANY, pos[0])
		targ2label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 2')
		self.targ2input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[1])
		targ3label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 3')
		self.targ3input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[2])
		targ4label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 4')
		self.targ4input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[3])
		targ5label = wx.StaticText(self.panel, wx.ID_ANY, 'Pos 5')
		self.targ5input = wx.TextCtrl(self.panel, wx.ID_ANY,  pos[4])

		#Detector Positions
		detTitle = wx.StaticText(self.panel, wx.ID_ANY, 'Detector Positions')
		det1label = wx.StaticText(self.panel, wx.ID_ANY, 'dE')
		pos1=str(self.parent.detectorPositions[0])
		self.det1input = wx.TextCtrl(self.panel, wx.ID_ANY, pos1)
		det2label = wx.StaticText(self.panel, wx.ID_ANY, 'dE/dx')
		pos2=str(self.parent.detectorPositions[1])
		self.det2input = wx.TextCtrl(self.panel, wx.ID_ANY, pos2)
		
		#Ok and Cancel Buttons
		okBtn = wx.Button(self.panel, wx.ID_ANY, 'OK')
		cancelBtn = wx.Button(self.panel, wx.ID_ANY, 'Cancel')
		self.Bind(wx.EVT_BUTTON, self.onOK, okBtn)
		self.Bind(wx.EVT_BUTTON, self.onCancel, cancelBtn)

		#Defining the boxes		
		topSizer        = wx.BoxSizer(wx.VERTICAL)
		targTitleSizer      = wx.BoxSizer(wx.HORIZONTAL)
		targ1Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ2Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ3Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ4Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		targ5Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		detTitleSizer      = wx.BoxSizer(wx.HORIZONTAL)
		det1Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		det2Sizer   = wx.BoxSizer(wx.HORIZONTAL)
		btnSizer        = wx.BoxSizer(wx.HORIZONTAL)

		#Adding the items to the boxes
		targTitleSizer.Add(targTitle, 0, wx.ALL, 5)
		targ1Sizer.Add(targ1label, 0, wx.ALL, 5)
		targ1Sizer.Add(self.targ1input, 1, wx.ALL|wx.EXPAND, 5)
		targ2Sizer.Add(targ2label, 0, wx.ALL, 5)
		targ2Sizer.Add(self.targ2input, 1, wx.ALL|wx.EXPAND, 5)
		targ3Sizer.Add(targ3label, 0, wx.ALL, 5)
		targ3Sizer.Add(self.targ3input, 1, wx.ALL|wx.EXPAND, 5)
		targ4Sizer.Add(targ4label, 0, wx.ALL, 5)
		targ4Sizer.Add(self.targ4input, 1, wx.ALL|wx.EXPAND, 5)
		targ5Sizer.Add(targ5label, 0, wx.ALL, 5)
		targ5Sizer.Add(self.targ5input, 1, wx.ALL|wx.EXPAND, 5)
		detTitleSizer.Add(detTitle, 0, wx.ALL, 5)
		det1Sizer.Add(det1label, 0, wx.ALL, 5)
		det1Sizer.Add(self.det1input, 1, wx.ALL|wx.EXPAND, 5)
		det2Sizer.Add(det2label, 0, wx.ALL, 5)
		det2Sizer.Add(self.det2input, 1, wx.ALL|wx.EXPAND, 5)
		btnSizer.Add(okBtn, 0, wx.ALL, 5)
		btnSizer.Add(cancelBtn, 0, wx.ALL, 5)

		#Adding the horizontal boxes to the vertical box
		topSizer.Add(targTitleSizer, 0, wx.CENTER)
		topSizer.Add(wx.StaticLine(self.panel,), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ1Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ2Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ3Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ4Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(targ5Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(detTitleSizer, 0, wx.CENTER)
		topSizer.Add(wx.StaticLine(self.panel,), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(det1Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(det2Sizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(btnSizer, 0, wx.ALL|wx.CENTER, 5)

		self.panel.SetSizer(topSizer)
		topSizer.Fit(self)

	def onOK(self, event):
		# Do something
		print ("onOK handler")
		self.parent.detectorPositions[0]=float(self.det1input.GetValue())
		self.parent.detectorPositions[1]=float(self.det2input.GetValue())
		self.parent.targetPositions[0]=float(self.targ1input.GetValue())
		self.parent.targetPositions[1]=float(self.targ2input.GetValue())
		self.parent.targetPositions[2]=float(self.targ3input.GetValue())
		self.parent.targetPositions[3]=float(self.targ4input.GetValue())
		self.parent.targetPositions[4]=float(self.targ5input.GetValue())
		self.closeProgram()
	
	def onCancel(self, event):
		self.closeProgram()

	def closeProgram(self):
		self.Close()



def main():		
	app = wx.App()
	gui = DriveSystemGUI(None, "Drive System")
	gui.Show()
	app.MainLoop()


if __name__ == '__main__':
	main()
