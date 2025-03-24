#!/usr/bin/env python3

#
# Development notes (23042024):
# ------------------
# - Consolidated the multiple "arrows" function
# - Now have some movement added for target ladder and beam blocker in beamView
# - Next jobs, are to save positions, load positons, and link Patrick's buttons
#global globalpos
import matplotlib
matplotlib.use('WXAgg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib import animation
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from mpl_toolkits.axes_grid1.inset_locator import InsetPosition
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

#import Image
import matplotlib.image as mpimg
import wx
import numpy as np
import threading
import time
import Library_DriveSystem
import queue
import os
import re

from target_ladder_select import *

#
# ENCODER PARAMETERS
#
mm2step = 200
step2mm = 1./mm2step

# Storage for saved parameters, format of x.x.x

#
# AXIS DEFINITIONS
#
# () = abbreviation used throughout, [] = Patrick's tape colour
# axis 1: Target carriage                   (TC)   [red]
# axis 2: Array                             (Arr)
# axis 3: Target ladder, horizontal         (TLH)  [yellow]
# axis 4: Faraday cup/Zero degree detectors (Det)  [black]
# axis 5: Target ladder, vertical           (TLV)  [brown]
# axis 6: Beam blocker, horizontal          (BBH)  [grey]
# axis 7: Beam blocker, vertical            (BBV)  [white]
nAxes = 7
axislabels = ['TargCarr', 'Array', 'TargLadH', 'FC/ZD','TargLadV','beamblockH','beamblockV']

#
# WINDOW DEFINITIONS
#
# Panel sizes: controlView split horizontally, beamView vertically
controlViewSize = 200
beamViewSize    = 400

# Frame (window) size
frameH = 780
frameW = 1000+beamViewSize

#
# DIAGRAM DEFINITIONS
#
#           'key': ['descript.',   Wid. Hei. Colour     axis
axisdict = {'SiA': ['Si arrray',   610,  35, '#FD3F0D', 0],
            'TaC': ['TargCarr',    450, 270, '#0DE30B', 1],
            'ArC': ['Array bed',   350, 195, '#FDD11F', 2],
            'TLH': ['Targ ladd H', 80,  130, '#00A7FA', 3],
            'Det': ['Detectors',   80,  130, '#910BE3', 4],
            'TLV': ['Targ ladd V', 217, 309.4,'#00A7FA', 5],
            'BBH': ['Beam blck H', 80,  130, '#910BE3', 6],
            'BBV': ['Beam blck V', 169.5,123.0, '#910BE3', 7]}

#
# ABSOLUTE POSITIONS OF AXES FOR TARGETS
#
axisposdict = {'bb.small' : [50,-90]}
#from savedpositions import axisposdict
#               'bm.fc' : ['Det',90]}
#
# EDGES/SPACINGS/MISC
#
Arr_space    = axisdict['ArC'][1]/2 # Space between trolley border and axis 3&4
arrayEdge_H        = axisdict['SiA'][2]
arrayEdge_W        = 18.5             # Distance from end of array to edge of Si array
silencerW          = 68.4-32.6        # Total length minus depth in to array of 32.6 mm
targ_space   = 20
Det_space = 20
magL               = 2732             # Magnet length [mm]
recoil_target_dist = 246.2
blockerpos         = (magL/2)-47.0    # Distance of blocker from back of the magnet (From Mike Cordwell)

# FC, ZD and recoil detectors
# Radius
fcR     = 21
dER     = 20
recoilR = 50

# Blocker dimensions
blockerR     = 15
blockerPostW = 5
blockerPostH = 135

# encoder position of the center [mm]
dEH =  11672.0*step2mm   # just for the GUI
fcH = -12587.0*step2mm   # no need to change

# Colours
arrayEdgeCol  = axisdict['Det'][3]
silencerC     = arrayEdgeCol
recoilFCCol   = '#B2B1BA'
recoilECol    = '#15B01A'
blockerFCol   = '#B2B1BA'
blockerECol   = '#000000'

# Frequency for the positons checking (seconds)
UPDATE_TIME = 1
REAC_TIME   = 0.1

# Element definition for the queue
class Element:
        def __init__(self, mode,ax=None,cmd=None):
                self.mode = mode
                self.axis = ax
                self.command=cmd

        # =========== CLASS ELEMENT =============

# Definitions of Events
# position update:
myEVT_POSUPDATE = wx.NewEventType()
EVT_POSUPDATE   = wx.PyEventBinder(myEVT_POSUPDATE, 1)
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


# disconnect
myEVT_DISCONNECT = wx.NewEventType()
EVT_DISCONNECT   = wx.PyEventBinder(myEVT_DISCONNECT, 1)
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

        # =========== END EVENT CLASS DEFS ===============

# Originally called "CheckPositions", probably more accurately "DriveSystemInterface"
# Shall leave for the time being.
class CheckPositions(threading.Thread):
        def __init__(self,controlView,driveSystem):
                """
                @param parent: The gui object that should recieve the value
                @param value: value to 'calculate' to
                """
                threading.Thread.__init__(self)
                self._parent = controlView
                self._driveSystem=driveSystem
#                self._XYSelect=xySelectWindow

        def run(self):
                """Overrides Thread.run. Don't call this directly its called internally
                when you call Thread.start().
                """
                while 1:
                        if self._driveSystem.port_open == True and self._parent.aborted==False:

                                self._driveSystem.check_encoder_pos()
                                pos=self._driveSystem.positions # Position in steps
                                if self._parent.printRequest==True: # Print positions when print Button was pressed
                                        for axis in range(1,nAxes):
                                                print("Axis "+str(axis)+": "+str(pos[axis]))
                                                self._parent.printRequest=False

                                event = PosUpdateEvent(myEVT_POSUPDATE, -1, pos)
                                wx.PostEvent(self._parent.posvispanel, event)

                                t = 0
                                while t<UPDATE_TIME:
                                        self.checkQ()
                                        time.sleep(REAC_TIME)
                                        t=t+REAC_TIME
                        else:
                                time.sleep(1)

        def checkQ(self): # Whilst q isn't empty, action it. Is "q" queue?
                while self._parent.q.empty()==False: # Parent is controlview
                        item = self._parent.q.get()
                        self.action(item)
                        self._parent.q.task_done()

        def action(self,element): # Decide how to action depending on element
                if element.mode=='Q':
                        self._parent.quit()
                elif element.mode=='S':
                        command=element.command
                        print("SENDING COMMAND "+command.decode())
                        ax,answer=self._driveSystem.executeCommand(command)
#                        if ax!=None
#                                self._driveSystem.currentAx.SetValue(ax)
#                                self.currentAx.SetValue(ax)
#                                self.commandResponse.SetValue(answer)
#
#                                self._parent.sendingCommand(element.command)
                elif element.mode=='M+-': # Relative move
                        steps=element.command
                        self._driveSystem.move_rel(element.axis,steps)
                        print('MOVING '+str(element.axis)+' '+str(steps)+' steps')
                elif element.mode=='H': # home
                        self._driveSystem.datum_search(element.axis)
                elif element.mode=='C':
                        self._parent.connect()
                elif element.mode=='D':
                        print("DISCONNECT")
                        self._driveSystem.disconnect_port()
                        event = DisConnectEvent(myEVT_DISCONNECT, -1, 0)
                        wx.PostEvent(self, event)
                else: # For pre-determined positions
                        if re.search('[0-9].[0-9].[0-9]',str(element.mode)): # isTarget:
                                print('TARGET: '+str(element.mode))
                                self._driveSystem.select_pos(axisdict['TLH'][4],axisposdict[str(element.mode)][0])
                                self._driveSystem.select_pos(axisdict['TLV'][4],axisposdict[str(element.mode)][1])
                        elif re.search('\*_slit',str(element.mode)) or re.search('[*]_aperture',str(element.mode)): # isHoles
                                # NOTE: this could be as above, as holes are just "targets"
                                print('SLIT/APERTURES'+str(element.mode))
                                self._driveSystem.select_pos(axisdict['TLH'][4],axisposdict[str(element.mode)][0])
                                self._driveSystem.select_pos(axisdict['TLV'][4],axisposdict[str(element.mode)][1])
                        elif re.search('bb.*',str(element.mode)): # isBeamblocker
                                print('BEAM BLOCKER'+str(element.mode))
                                self._driveSystem.select_pos(axisdict['BBH'][4],axisposdict[str(element.mode)][0])
                                self._driveSystem.select_pos(axisdict['BBV'][4],axisposdict[str(element.mode)][1])
                        elif re.search('bm.*',str(element.mode)): # isBeammonitor
                                print('BEAM DETECTOR'+str(element.mode))
                                self._driveSystem.select_pos(axisdict['Det'][4],axisposdict[str(element.mode)][0])


#
# BEAMVIEW CLASS
#
class BeamView: # - For the looking at X-Y plane as the beam
        def __init__(self,panel):
                self.posvispanel=panel

                # Defining the figure
                self.fig = plt.figure()
                self.fig.set_dpi(100)
                self.fig.set_size_inches(4, 5.3)

                # Setting properties of the axes
                self.ymin = -100
                self.ymax =  100
                self.xmin = -100
                self.xmax =  100

                # Axis design
                self.ax = plt.axes(xlim=(self.xmin, self.xmax), ylim=(self.ymin,self.ymax))
                self.ax.spines['right'].set_color('none')
                self.ax.spines['top'].set_color('none')
                self.ax.spines['left'].set_position('center')
                self.ax.spines['bottom'].set_position(('data',-2.765))
                self.ax.set_xlabel("[mm]")

                self.ladder_image = plt.imread('/home/isslocal/DriveSystemGUI/target_ladder_trans50.png', format='png')
                self.blockr_image = plt.imread('/home/isslocal/DriveSystemGUI/beam_blocker_trans50.png',  format='png')

                # Draw images
                # create new inset axes in data coordinates
                self.TL_xy = [0,0]
                self.BB_xy = [0,0]
                self.axtl = self.ax.inset_axes([self.TL_xy[0],self.TL_xy[1],axisdict['TLV'][1],axisdict['TLV'][2]],
                                               transform=self.ax.transData)
                self.axtl.imshow(self.ladder_image)
                self.axtl.axis('off')
                self.axbb = self.ax.inset_axes([self.BB_xy[0],self.BB_xy[1],axisdict['BBV'][1],axisdict['BBV'][2]],
                                               transform=self.ax.transData)
                self.axbb.imshow(self.blockr_image)
                self.axbb.axis('off')
                self.yoff = -10
                self.dis  = 700
                plt.rcParams.update({'font.size': 12})

                self.TL_postext=self.ax.text(self.xmin,self.ymax+self.yoff,
                                             "TLH: "+"{:.3f}".format(self.TL_xy[0])+" mm\nTLV: "+"{:.3f}".format(self.TL_xy[1])+" mm",
                                             color=axisdict['TLH'][3])
                self.BB_postext=self.ax.text(self.xmin+100,self.ymax+self.yoff,
                                             "BBH: "+"{:.3f}".format(self.BB_xy[0])+" mm\nBBV: "+"{:.3f}".format(self.BB_xy[1])+" mm",
                                              color=axisdict['BBH'][3])

        # Function to change positions of above
        def updatePositions(self,pos):
                # Take updated positions from pos[3]==TLH, pos[5]==TLV, pos[6]==BBH, pos[7]==BBV
                # mostly for debugging here
                self.TL_xy_off = [pos[2]*step2mm,pos[4]*step2mm]
                self.BB_xy_off = [pos[5]*step2mm,pos[6]*step2mm]
                # For repositioning, want the old position and then move it by amount
                for iTL in range(2):
                        self.TL_xy[iTL] = self.TL_xy_off[iTL]
                for iBB in range (2):
                        self.BB_xy[iBB] = self.BB_xy_off[iBB]

                self.axtl.remove()
                self.axtl = self.ax.inset_axes([self.TL_xy[0],self.TL_xy[1],axisdict['TLV'][1],axisdict['TLV'][1]],
                                               transform=self.ax.transData)
                self.axtl.imshow(self.ladder_image)
                self.axtl.axis('off')

                self.axbb.remove()
                self.axbb = self.ax.inset_axes([self.BB_xy[0],self.BB_xy[1],axisdict['BBV'][1],axisdict['BBV'][1]],
                                               transform=self.ax.transData)
                self.axbb.imshow(self.blockr_image)
                self.axbb.axis('off')

                self.TL_postext.remove()
                self.TL_postext=self.ax.text(self.xmin,self.ymax+self.yoff,
                                             "TLH: "+"{:.3f}".format(self.TL_xy[0])+" mm\nTLV: "+"{:.3f}".format(self.TL_xy[1])+" mm",
                                             color=axisdict['TLH'][3])
                self.BB_postext.remove()
                self.BB_postext=self.ax.text(self.xmin+200,self.ymax+self.yoff,
                                             "BBH: "+"{:.3f}".format(self.BB_xy[0])+" mm\nBBV: "+"{:.3f}".format(self.BB_xy[1])+" mm",
                                              color=axisdict['BBH'][3])


        def get_figure(self):
                return self.fig

#
# DRIVEVIEW CLASS
#
class DriveView: # - For top down view of beam axis
        def __init__(self,panel):
                self.posvispanel=panel

                # Defining the figure
                self.fig = plt.figure()
                self.fig.set_dpi(100)
                self.fig.set_size_inches(10, 5.3)

                # Setting properties of the axes
                self.ymin = -400
                self.ymax =  400
                self.xmin = -magL*0.5
                self.xmax =  magL*0.5

                # Axis design
                self.ax = plt.axes(xlim=(self.xmin, self.xmax), ylim=(self.ymin,self.ymax))
                self.ax.spines['right'].set_color('none')
                self.ax.spines['top'].set_color('none')
                self.ax.set_yticks([])
                self.ax.spines['left'].set_color('none')
                self.ax.spines['bottom'].set_position(('data',-2.765))
                majorLocator = MultipleLocator(500)
                minorLocator = MultipleLocator(100)
                self.ax.xaxis.set_major_locator(majorLocator)
                # For the minor ticks, use no labels; default NullFormatter
                self.ax.xaxis.set_minor_locator(minorLocator)
                self.ax.set_xlabel("[mm]")

                # Adding the four rectangles + array which belongs to ax 2
                # Rectangle( (anchor point), width, height, colour)
                # TARGET CARRIAGE
                self.TaC_rect = plt.Rectangle((self.xmax-600,-axisdict['TaC'][2]/2),
                                              axisdict['TaC'][1], axisdict['TaC'][2],
                                              fc=axisdict['TaC'][3])
                self.ax.add_patch(self.TaC_rect)
                # ARRAY CARRIAGE
                self.ArC_rect = plt.Rectangle((self.xmin+300, -axisdict['ArC'][2]/2),
                                              axisdict['ArC'][1], axisdict['ArC'][2],
                                              fc=axisdict['ArC'][3])
                self.ax.add_patch(self.ArC_rect)
                # DETECTORS
                self.Det_rect = plt.Rectangle((self.xmax-600+axisdict['TaC'][1]-Det_space-axisdict['Det'][1], -axisdict['Det'][2]/2),
                                              axisdict['Det'][1], axisdict['TLH'][2],
                                              fc=axisdict['Det'][3])
                self.ax.add_patch(self.Det_rect)
                # TARGET LADDER
                self.TLH_rect = plt.Rectangle((self.xmax-600+targ_space, -axisdict['TLH'][2]/2),
                                              axisdict['TLH'][1], axisdict['TLH'][2],
                                              fc=axisdict['TLH'][3])
                self.ax.add_patch(self.TLH_rect)
                # ARRAY
                self.SiA_rect = plt.Rectangle((self.xmin+300+Arr_space,-axisdict['SiA'][2]/2),
                                              axisdict['SiA'][1], axisdict['SiA'][2],
                                              fc=axisdict['SiA'][3])
                self.ax.add_patch(self.SiA_rect)
                # ARRAY EDGE
                self.arrayEdge_rect = plt.Rectangle((self.SiA_rect.get_x()+axisdict['SiA'][1],-axisdict['SiA'][2]/2),
                                                    arrayEdge_W, arrayEdge_H,
                                                    fc=arrayEdgeCol)
                self.ax.add_patch(self.arrayEdge_rect)
                # SILENCER
                self.silencer_rect = plt.Rectangle((self.SiA_rect.get_x()+axisdict['SiA'][1]+arrayEdge_W,-axisdict['SiA'][2]/4),
                                                   silencerW, arrayEdge_H/2,
                                                   fc=silencerC)
                self.ax.add_patch(self.silencer_rect)

                # FC CIRCLE
                self.FC_circ = plt.Circle(xy=(self.Det_rect.get_x()+0.5*axisdict['Det'][1],fcH),
                                          radius=fcR,
                                          fc=axisdict['ArC'][3])
                self.ax.add_patch(self.FC_circ)
                # DE CIRCLE
                self.dE_circ = plt.Circle(xy=(self.Det_rect.get_x()+0.5*axisdict['Det'][1],dEH),
                                          radius=dER,
                                          fc=axisdict['ArC'][3])
                self.ax.add_patch(self.dE_circ)

                # RECOIL CIRCLE
                self.recoil_circle = plt.Circle(xy=(self.TLH_rect.get_x()+recoil_target_dist,0),
                                                radius=recoilR,
                                                fc=recoilFCCol,
                                                ec=recoilECol,lw=2.5,hatch='X')
                self.ax.add_patch(self.recoil_circle)

                # Label the encoder axes
                self.placeAxisNumbers()

                # Add FC and ZD labels
                self.placeFCZD()

                # Adding information about position
                rand = 20
                dis  = 700
                plt.rcParams.update({'font.size': 12})
                self.position1=self.ax.text(self.xmin,self.ymax-rand,
                                            "Position 1: "+"{:.3f}".format(self.TaC_rect.get_x())+" mm",
                                            color=axisdict['TaC'][3])
                self.position2=self.ax.text(self.xmin+dis-5,self.ymax-rand,
                                            "Position 2: "+"{:.3f}".format(self.ArC_rect.get_x())+" mm",
                                            color=axisdict['SiA'][3])
                self.position3=self.ax.text(self.xmin+2*dis,self.ymax-rand,
                                            "Position 3: "+"{:.3f}".format(0)+" mm",
                                            color=axisdict['TLH'][3])
                self.position4=self.ax.text(self.xmin+3*dis+5,self.ymax-rand,
                                            "Position 4: "+"{:.3f}".format(0)+" mm",
                                            color=axisdict['Det'][3])

                # Beam Arrow
                self.beamArrow=self.ax.annotate ('', (self.xmin, self.ymax-20*10),
                                                 (self.xmin+30*10, self.ymax-20*10),
                                                 arrowprops={'arrowstyle':'<-'} )
                self.beamText=self.ax.text(self.xmin+7*10, self.ymax-18*10,'BEAM')

                # Conversion coefficients
                self.mm2stepsText=self.ax.text(self.xmin, -self.ymax+40,"1 mm = 200 steps")
                self.steps2mmText=self.ax.text(self.xmin, -self.ymax,"1 step = 0.005 mm")

                # Define list of arrows
                self.arrowlist = [] # [arrow, arrow label]
                for iarrow in range(3):
                        self.arrowlist.append( [self.ax.annotate('',(-1,1),(-1,1)),
                                                self.ax.text(0,0,'')] )

                #Makes the space at the sides of the diagrams smaller
                self.fig.tight_layout()

                # ---------- END DRIVEVIEW INIT ------------

        def get_figure(self):
                return self.fig

        def drawArrow(self,i,x1,x2,height,label,label_offset):
                self.arrowlist[i][0].remove()
                self.arrowlist[i][1].remove()
                self.arrowlist[i][0] = self.ax.annotate ('', (x1, height), (x2, height),arrowprops={'arrowstyle':'<->'})
                text = label+" {:.3f}".format(x2-x1)+" mm"
                label_offset += height
                self.arrowlist[i][1]=self.ax.text(x1+(x2-x1)*0.5-200, label_offset,text)

        # Here the numbers after "move" refer to the axes being move, I presume.
        def move1(self,moveDis): # Moves everything on TaC? Why not recoil?
                self.TaC_rect.set_x(self.TaC_rect.get_x()+moveDis)
                self.TLH_rect.set_x(self.TLH_rect.get_x()+moveDis)
                self.Det_rect.set_x(self.Det_rect.get_x()+moveDis)
                self.changeText(1)

        def move2(self,moveDis): # Move array carriage, why not array?
                xcurr=self.ArC_rect.get_x()
                self.ArC_rect.set_x(xcurr+moveDis)
                self.changeText(2)

        def move3(self,newpos): # Moves target ladder up and down in driveView plot
                self.TLH_rect.set_y(newpos)
                self.changeText(3)

        def move4(self,newpos): # moves detector rail up and down
                self.Det_rect.set_y(newpos)
                self.changeText(4)

        def updatePositions(self,pos):
                rand = 6
                dis = 700

                # this is 2023 value from Survey on October 2023 (elog:3752)
                dis2_3  =  579.0 # this is distance at axis1 = -77397 and axis2 = 1000 from target to silicon
                dis2_3 -=  1000*step2mm # this is measurement position of axis2
                dis2_3 += -77397*step2mm # this is measurement position of axis1
                dis2_3 += pos[1]*step2mm # add on distance of array from encoder = 1
                dis2_3 -= pos[0]*step2mm # add on distance of target from encoder = 0
                dis_ta  = dis2_3 # this is the distance for physics (end of silicon)
                dis2_3 -= silencerW + arrayEdge_W # length of the silencer

                # this is 2023 value from Survey on 25th October 2023 (elog:3752)
                recoil_pos = pos[0]*step2mm + recoil_target_dist # now on the axis 1 carriage

                # Assuming that target at encoder position 0 is 1234.0 mm from back of magnet (elog:2891)
                coord3  = magL/2 - 1234.0
                coord3 -= pos[0]*step2mm

                # blocker not used in 2023 so far
                blocker_target_dist = blockerpos - coord3

                coord2 = coord3 - dis2_3 - axisdict['SiA'][1] - arrayEdge_W - silencerW

                coord1 = coord3-targ_space
                coord4 = coord1+axisdict['TaC'][1]-Det_space

                # TEXT POSITIONS
                self.position1.remove()
                self.TaC_rect.set_x(coord1)
                text="Position 1: "+"{:.3f}".format(-pos[0]*0.005)+" mm"
                self.position1=self.ax.text(self.xmin,self.ymax-rand,text,color=axisdict['TaC'][3])

                self.position2.remove()
                text="Position 2: "+"{:.3f}".format(-pos[1]*0.005)+" mm"
                self.position2=self.ax.text(self.xmin+dis,self.ymax-rand,text,color=axisdict['SiA'][3])
                self.SiA_rect.set_x(coord2)
                self.ArC_rect.set_x(self.SiA_rect.get_x()-Arr_space)
                self.arrayEdge_rect.set_x(self.SiA_rect.get_x()+axisdict['SiA'][1])
                self.silencer_rect.set_x(self.SiA_rect.get_x()+axisdict['SiA'][1]+arrayEdge_W)
                pos1=self.TaC_rect.get_x()

                self.position3.remove()
                text="Position 3: "+"{:.3f}".format(pos[2]*0.005)+" mm"
                self.position3=self.ax.text(self.xmin+2*dis,self.ymax-rand,text,color=axisdict['TLH'][3])
                self.TLH_rect.set_y(pos[2]*0.005-axisdict['TLH'][2]/2)
                self.TLH_rect.set_x(coord3)

                self.position4.remove()
                text="Position 4: "+"{:.3f}".format(pos[3]*0.005)+" mm"
                self.position4=self.ax.text(self.xmin+3*dis,self.ymax-rand,text,color=axisdict['Det'][3])
                self.Det_rect.set_y(pos[3]*0.005-axisdict['Det'][2]/2)
                self.Det_rect.set_x(coord4-axisdict['Det'][1])
                self.FC_circcenter=self.Det_rect.get_x()+0.5*axisdict['Det'][1],self.Det_rect.get_y()+axisdict['Det'][2]/2+fcH
                self.dE_circ.center=self.Det_rect.get_x()+0.5*axisdict['Det'][1],self.Det_rect.get_y()+axisdict['Det'][2]/2+dEH
                self.recoil_circle.center=self.TLH_rect.get_x()+recoil_target_dist,0

                # ARROWS
                self.x1 = [self.TLH_rect.get_x(),
                           self.TLH_rect.get_x(),
                           self.TLH_rect.get_x()]
                self.x2 = [self.SiA_rect.get_x()+axisdict['SiA'][1]+arrayEdge_W+silencerW,
                           self.TLH_rect.get_x()+recoil_target_dist,
                           self.SiA_rect.get_x()+axisdict['SiA'][1]]
                self.height = [axisdict['TaC'][2]/2+10,axisdict['TaC'][2]/2+10,-1*(axisdict['TaC'][2]/2+10)]
                self.label = ['d_tip','d_recoil','d_si']
                self.label_offset = [30,80,-30]
                # drawArrow(x1,x2,height, label, label_offset)
                for iArrow in range(len(self.x1)):
                        self.drawArrow(iArrow,self.x1[iArrow],self.x2[iArrow],self.height[iArrow],
                                       self.label[iArrow],self.label_offset[iArrow])



                self.number1.remove()
                self.number2.remove()
                self.number3.remove()
                self.number4.remove()
                self.fc.remove() #FC label
                self.zd.remove() #ZD label
                self.placeAxisNumbers()
                self.placeFCZD()
                self.posvispanel.canvas.draw()
                self.posvispanel.canvasBeam.draw()

                # ---------- END UPDATEPOSITIONS -----------------

        def placeAxisNumbers(self):
                nSize=18
                self.axisindex=self.ax.text(self.TaC_rect.get_x()+axisdict['TaC'][1]/2,self.TaC_rect.get_y()+0.75*axisdict['TaC'][2],
                                          "1",fontsize=nSize,horizontalalignment='center')

                self.number1=self.ax.text(self.TaC_rect.get_x()+axisdict['TaC'][1]/2,self.TaC_rect.get_y()+0.75*axisdict['TaC'][2],
                                          "1",fontsize=nSize,horizontalalignment='center')
                self.number2=self.ax.text(self.ArC_rect.get_x()+axisdict['ArC'][1]/2,self.ArC_rect.get_y()+0.75*axisdict['ArC'][2],
                                          "2",fontsize=nSize,horizontalalignment='center')
                self.number3=self.ax.text(self.TLH_rect.get_x()+axisdict['TLH'][1]/2,self.TLH_rect.get_y()+0.5*axisdict['TLH'][2],
                                          "3",fontsize=nSize,horizontalalignment='center')
                self.number4=self.ax.text(self.Det_rect.get_x()+axisdict['Det'][1]/2,self.Det_rect.get_y()+0.5*axisdict['Det'][2],
                                          "4",fontsize=nSize,horizontalalignment='center')

        def placeFCZD(self):
                fSize=10
                self.fc=self.ax.text(self.Det_rect.get_x()+axisdict['Det'][1]/2,self.Det_rect.get_y()+1.1*axisdict['Det'][2],
                                     "FC",fontsize=fSize,horizontalalignment='center')
                self.zd=self.ax.text(self.Det_rect.get_x()+axisdict['Det'][1]/2,self.Det_rect.get_y()-0.3*axisdict['Det'][2],
                                     "ZD",fontsize=fSize,horizontalalignment='center')


class PosVisPanel(wx.Panel):
        def __init__(self, parent):
                wx.Panel.__init__(self, parent,-1,size=(frameW,frameH-controlViewSize))

                self.winSplitter=wx.SplitterWindow(self,size=(frameW,frameH-controlViewSize))#size=parent.GetSize())
                self.winSplitter.SetBackgroundColour("#FF0000")

                self.drivePanel=wx.Panel(self.winSplitter,size=(frameW-beamViewSize,frameH-controlViewSize))
                self.beamPanel=wx.Panel(self.winSplitter,size=(beamViewSize,frameH-controlViewSize))

                self.drivePanel.SetBackgroundColour("#00FF00")
                self.beamPanel.SetBackgroundColour("#0000FF")

                # DRIVE VIEW
                self.driveView=DriveView(self)
                self.figure=self.driveView.get_figure()
                self.canvas = FigureCanvas(self.drivePanel, -1, self.figure)

                # BEAM VIEW
                self.beamView=BeamView(self)
                self.figureBeam=self.beamView.get_figure()
                self.canvasBeam=FigureCanvas(self.beamPanel,-1,self.figureBeam)

                # Panel splitting
                self.winSplitter.SplitVertically(self.drivePanel,self.beamPanel,0)

                #Event Handlers
                self.Bind(EVT_POSUPDATE, self.updatePositions)

        def updatePositions(self,event):
                pos=event.GetValue()
                print(pos)
                self.driveView.updatePositions(pos)
                self.beamView.updatePositions(pos)
                self.canvas.draw()
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

        def __init__(self,parent,posvispanel,frame):
                self.driveSystem=Library_DriveSystem.DriveSystem()
#                self.ladderselect=MoveMotorPanel()

                self.frame=frame
                sizeX = 100
                sizeY = 100
                wx.Panel.__init__(self, parent, size=(sizeX,sizeY))
                self.SetBackgroundColour('#FFFFE0')

                self.posvispanel=posvispanel

                #Text Entries and Buttons
                #Sending Command
                writeSize = 200
                a = 25
                self.sendText = wx.StaticText(self, -1, "Send any command:", (5,5),style=wx.ALIGN_LEFT)
                self.writeCommand = wx.TextCtrl(self, -1, "", (5,a),size=(writeSize, -1))
                self.sendCommand = wx.Button(self, wx.ID_ANY, "Send", (writeSize+15, a))
                self.sendCommand.Bind(wx.EVT_BUTTON, self.sendingCommandB)
                self.sendCommand.SetDefault()
                self.currentAxis = wx.StaticText(self, -1, "Axis:", (520,5),style=wx.ALIGN_LEFT)
                self.responseText = wx.StaticText(self, -1, "Response:", (580,5),style=wx.ALIGN_LEFT)
                self.currentAx = wx.TextCtrl(self, wx.ID_ANY, "", (520,30),size=(60, -1), style=wx.ALIGN_LEFT|wx.TE_READONLY)
                self.commandResponse = wx.TextCtrl(self, wx.ID_ANY, "", (580,30),size=(200, -1), style=wx.ALIGN_LEFT|wx.TE_READONLY)

                #Abort/Reset Buttons
                self.aborted=False
                self.abortAllButton = wx.Button(self, wx.ID_ANY, "ABORT", (writeSize+15+100, a))
                self.abortAllButton.SetBackgroundColour("#FD3F0D")
                self.abortAllButton.Bind(wx.EVT_BUTTON, self.abortAll)

                self.resetAllButton = wx.Button(self, wx.ID_ANY, "RESET", (writeSize+15+200, a))
                self.resetAllButton.Bind(wx.EVT_BUTTON, self.resetAll)

                #Print Encoder positions
                self.printPos = wx.Button(self, wx.ID_ANY, "Print Pos.", (writeSize+580, 30))
                self.printPos.Bind(wx.EVT_BUTTON, self.printPosB)
                self.printRequest=False

                # Target change button
                self.XYElementChange = wx.Button(self, wx.ID_ANY, "IN-BEAM", (writeSize+750, 30))
                self.XYElementChange.SetBackgroundColour("#AA44DD")
                self.XYElementChange.Bind(wx.EVT_BUTTON, self.XYElementChangeWindow )

                self.XYElementMove = wx.Button(self, wx.ID_ANY, "MOVE", (writeSize+750, 60))
                self.XYElementMove.Bind(wx.EVT_BUTTON, self.XYElementMoveAction)

                #Connect/Disconnect Buttons
                offset  =  100
                buttonW =  110
                sizey   = (sizeY+offset)/5

                self.connectButton = wx.Button(self, wx.ID_ANY, "CONNECT", (int(frameW-buttonW),int(0)),(int(buttonW),int(sizey)))
                self.connectButton.Bind(wx.EVT_BUTTON, self.connectB)

                self.disconnectButton = wx.Button(self, wx.ID_ANY, "DISCONNECT", (int(frameW-buttonW),int(sizey)),(buttonW,int(sizey)))
                self.disconnectButton.Bind(wx.EVT_BUTTON, self.disconnectB)

                self.quitButton = wx.Button(self, wx.ID_ANY, "QUIT", (int(frameW-buttonW),int(sizey*4)),(int(buttonW),int(sizey)))
                self.quitButton.Bind(wx.EVT_BUTTON, self.quitB)
                self.quitButton.SetBackgroundColour("#FD3F0D")

                self.helpButton = wx.Button(self, wx.ID_ANY, "HELP", (int(frameW-buttonW),int(sizey*3)),(int(buttonW),int(sizey)))
                self.helpButton.Bind(wx.EVT_BUTTON, self.openHelp)

                if self.driveSystem.checkConnection()==True:
                        self.disconnectButton.SetBackgroundColour("#FD3F0D")
                        self.connectButton.Enable(False)
                else:
                        self.connectButton.SetBackgroundColour("#7FFF00")
                        self.disconnectButton.Enable(False)


                # Encoder movement buttons
                dx  =  (frameW-buttonW)/7
                dy  =  29
                dis =  dx
                disy = sizeY+30
                self.datumButton = []
                self.targetlabel = []
                self.textcontrol = []
                self.moveplus    = []
                self.moveminus   = []
                for i in range(nAxes):
                        self.datumButton.append(wx.Button(self,wx.ID_ANY,'Datum '+str(i+1),(int(i*dis),int(sizeY)),(int(dx),int(dy))))
                        self.datumButton[i].Bind(wx.EVT_BUTTON, lambda evt,temp=i+1, : self.datumButtonAction(evt,temp))

                        self.targetlabel.append(wx.StaticText(self, -1, "("+str(i+1)+"):\n"+axislabels[i], (int(i*dis),int(disy-70))))
                        self.textcontrol.append(wx.TextCtrl(self, wx.ID_ANY, "", (int(i*dis+40),int(disy)),size=(int(55),-1)))
                        self.moveplus.append(wx.Button( self, wx.ID_ANY, "+", (int(i*dis+80),int(disy)),size=(int(40),-1)))
                        self.moveminus.append(wx.Button(self, wx.ID_ANY, "-", (int(i*dis),   int(disy)),size=(int(40),-1)))
                        self.moveplus[i].Bind(wx.EVT_BUTTON,  lambda evt,temp=i+1, : self.moveplusAction(evt,temp))
                        self.moveminus[i].Bind(wx.EVT_BUTTON, lambda evt,temp=i+1, : self.moveminusAction(evt,temp))


                #Create the queue that the Thread checks
                self.q=queue.Queue()

                #Event Handlers
                self.Bind(EVT_DISCONNECT, self.changeViewDisconnect)
                #Start Thread which checks continously the positions
                self.positionsChecker=CheckPositions(self,self.driveSystem)
                self.positionsChecker.start()
#                self.window = XYElementSelectWindow("TITLE")
                # ---------- END CONTROLEVIEW INIT ---------------

        # Makes disconnect button red if not connected
        def changeViewDisconnect(self,event):
                value=event.GetValue()
                if value==1:
                        self.disconnectButton.SetBackgroundColour("#EE4000")
                        self.connectButton.Enable(False)
                        self.connectButton.SetBackgroundColour("grey")
                        self.disconnectButton.Enable(True)
                else:
                        self.connectButton.SetBackgroundColour("#7FFF00")
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

        def connectB(self,event):
                print("Connect")
                self.driveSystem.connect_to_port()
                event = DisConnectEvent(myEVT_DISCONNECT, -1, 1)
                wx.PostEvent(self, event)

        def disconnectB(self,event):
                element=Element('D')
                self.q.put(element)
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

        def datumButtonAction(self,event,axis):
                element=Element('H',axis)
                self.q.put(element)

        # Patrick's ladder
        def XYElementChangeWindow(self,event):
                self.window = XYElementSelectWindow("TITLE")

        def XYElementMoveAction(self,event):
                element=Element(str(self.window.panel.get_move_motor_panel().globalpos))
#                element=Element('M')
                self.q.put(element)
                print(element)

#        self.ladderselect.get_movement_selection()
        #print(self.ladder_opt)
        # Keep as two functions, as by the time put in if statement, don't save that much space.
        def moveplusAction(self,event,axis):
                disMM = float(self.textcontrol[axis-1].GetValue())
                element=Element('M+-',axis,int(disMM*mm2step))
                self.q.put(element)
        def moveminusAction(self,event,axis):
                disMM = -1*float(self.textcontrol[axis-1].GetValue())
                element=Element('M+-',axis,int(disMM*mm2step))
                self.q.put(element)

        def openHelp(self,event):
                secondwindow=HelpWindow(self, "Help")
                secondwindow.Show()

        def abortAll(self,event):
                self.driveSystem.abortAll()
                self.aborted=False
        def resetAll(self,event):
                self.driveSystem.resetAll()
                self.aborted=False


class DriveSystemGUI(wx.Frame):
        def __init__(self, parent, mytitle):
                super(DriveSystemGUI, self).__init__(parent, title=mytitle,size=(frameW,frameH))
                self.InitUI()
                self.Centre()

        def InitUI(self):
                self.split_win = wx.SplitterWindow(self)
                self.bottom_split = PosVisPanel(self.split_win)
                self.top_split = ControlView(self.split_win,self.bottom_split,self)
                self.split_win.SplitHorizontally(self.top_split, self.bottom_split, controlViewSize)

        def closeProgram(self):
                self.Destroy()
                self.Close()


class HelpWindow(wx.Frame):
        def __init__(self, parent, mytitle):
                self.width=430
                self.height=500
                super(HelpWindow, self).__init__(parent, title=mytitle,size=(self.width,self.height))
                self.InitUI()
                self.Centre()

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
                text1="This is a GUI for controlling the Drive System.\nThe Drive System contains four axes:\n\nAxis 1: Trolley\nAxis 2: Array\nAxis 3: Target\nAxis 4: Faraday cup and ZD detector\n\nwhich are represented by the four colored\nrectangulars.\nThe coordinate system of the GUI is in millimeters,\nand is centered around the middle of the magnet.\nThis means, that the limits are +-2730/2 mm = +-1365 mm.\nThe GUI allows to move the objects on the axes in the unit\nof millimeters by inserting the desired value and clicking on\nthe corresponding button (Move1, Move2 ,+/-).\nThe smallest step is 0.005 mm = 1/200 mm. The positions on\nthe axes are checked and updated in the GUI every second."
                text2="In the case of axis 3 and axis 4, it is possible to choose\nbetween eight target positions and two detector positions\nrespectiveley. The corresponding encoder positions can be\nchanged via the window 'Settings'. By clicking on the 'Ok'\nButton, the new positions will be saved.\nThe arrow indicates the distance between the end of\nthe silicon and the target.\n\nOther actions the GUI offers are:\n- Abort command on all axes\n- Reset all axes\n- Connect/Disconnect to the port\n- Quit: this will close the GUI\n- Datum search: The datum/zero position on the axis will be\nsearched. When the datum position is found,\ncheck with the command OD if the datum position is\nequal to zero. If not use DA-x with x being the datum position\nto set it to zero."
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

        # Read saved vals
        f=open('/home/isslocal/DriveSystemGUI/id_dist_map.txt',"r")
        lines=f.readlines()
        for x in lines:
                axisposdict.update({x.split(' ')[0]:[int(x.split(' ')[1]),int(x.split(' ')[2])]})


        f.close()
        gui.Show()
        app.MainLoop()


if __name__ == '__main__':
        main()
