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
import wx.lib.scrolledpanel as scrolled
import numpy as np
from Library_DriveSystem import *
from Library_DriveSystemGUI import *
from target_ladder_select import *



import queue


# # Originally called "CheckPositions", probably more accurately "DriveSystemInterface"
# # Shall leave for the time being.
# class CheckPositions(threading.Thread):
#     is_running = True
#     axis_is_aborted = np.zeros( (number_of_motor_axes), dtype = bool )

#     def __init__(self,controlView,driveSystem):
#         """
#         @param parent: The gui object that should recieve the value
#         @param value: value to 'calculate' to
#         """
#         threading.Thread.__init__(self)
#         self._parent = controlView
#         self._driveSystem=driveSystem
# #        self._XYSelect=xySelectWindow

#     def run(self):
#         """Overrides Thread.run. Don't call this directly its called internally
#         when you call Thread.start().
#         """
#         while self.is_running:
#             t = 0
#             if self._driveSystem.port_open == True:
#                 if self.axis_is_aborted.all() == False:
#                     # Check positions of axes that aren't aborted
#                     for i in range(0,number_of_motor_axes):
#                         if self.axis_is_aborted[i] == False:
#                             self._driveSystem.check_encoder_pos_axis(i+1)

#                     # self._driveSystem.check_encoder_pos()
#                     # Store positions
#                     pos = self._driveSystem.positions # Position in steps

#                     # Update posvispanel
#                     event = PosUpdateEvent(myEVT_POSUPDATE, -1, pos)
#                     wx.PostEvent(self._parent.posvispanel, event)

#                 # Check if we should print positions
#                 if self._parent.printRequest==True: # Print positions when print Button was pressed
#                     for i in range(0,number_of_motor_axes):
#                         print( f"Axis {i+1}: {pos[i]}" )
#                         self._parent.printRequest=False

#                 # Process other things before checking again
#                 while t < UPDATE_TIME:
#                     self.checkQ()
#                     time.sleep(REAC_TIME)
#                     t=t+REAC_TIME
        

#     def checkQ(self): # Whilst q isn't empty, action it. Is "q" queue?
#         while self._parent.q.empty()==False: # Parent is controlview
#             item = self._parent.q.get()
#             self.action(item)
#             self._parent.q.task_done()

#     def action(self,element): # Decide how to action depending on element
#         if element.mode=='Q':
#             self.is_running = False
#         elif element.mode=='S':
#             command=element.command
#             print("SENDING COMMAND "+command)
#             ax,answer=self._driveSystem.executeCommand(command)
# #            if ax!=None
# #                self._driveSystem.currentAx.SetValue(ax)
# #                self.currentAx.SetValue(ax)
# #                self.commandResponse.SetValue(answer)
# #
# #                self._parent.sendingCommand(element.command)
#         elif element.mode=='M+-': # Relative move
#             steps=element.command
#             self._driveSystem.move_rel(element.axis,steps)
#             print('MOVING '+str(element.axis)+' '+str(steps)+' steps')
#         elif element.mode=='H': # home
#             self._driveSystem.datum_search(element.axis)
#         elif element.mode=='C':
#             self._parent.connect()
#         elif element.mode=='D':
#             print("DISCONNECT")
#             self._driveSystem.disconnect_port()
#             event = DisConnectEvent(myEVT_DISCONNECT, -1, 0)
#             wx.PostEvent(self, event)
#         else: # For pre-determined positions
#             if re.search('[0-9].[0-9].[0-9]',str(element.mode)): # isTarget:
#                 print('TARGET SELECTED: '+str(element.mode))
#                 self._driveSystem.select_pos(axisdict['TLH'].axis_number,axisposdict[str(element.mode)][0])
#                 self._driveSystem.select_pos(axisdict['TLV'].axis_number,axisposdict[str(element.mode)][1])
#             elif re.search('\*_slit',str(element.mode)) or re.search('[*]_aperture',str(element.mode)): # isHoles
#                 # NOTE: this could be as above, as holes are just "targets"
#                 print('SLIT/APERTURES  SELECTED: '+str(element.mode))
#                 self._driveSystem.select_pos(axisdict['TLH'].axis_number,axisposdict[str(element.mode)][0])
#                 self._driveSystem.select_pos(axisdict['TLV'].axis_number,axisposdict[str(element.mode)][1])
#             elif re.search('bb.*',str(element.mode)): # isBeamblocker
#                 print('BEAM BLOCKER  SELECTED: '+str(element.mode))
#                 self._driveSystem.select_pos(axisdict['BBH'].axis_number,axisposdict[str(element.mode)][0])
#                 self._driveSystem.select_pos(axisdict['BBV'].axis_number,axisposdict[str(element.mode)][1])
#             elif re.search('bm.*',str(element.mode)): # isBeammonitor
#                 print('BEAM DETECTOR SELECTED: '+str(element.mode))
#                 self._driveSystem.select_pos(axisdict['Det'].axis_number,axisposdict[str(element.mode)][0])
#             else:
#                 print( f"??? {element.mode}" )

#     def kill_thread(self):
#         element=Element('Q')
#         self._parent.q.put(element)

#     @classmethod
#     def set_axis_aborted(cls, axis):
#         cls.axis_is_aborted[axis-1] = True

#     @classmethod
#     def set_axis_reset(cls, axis):
#         cls.axis_is_aborted[axis-1] = False


#
# BEAMVIEW CLASS
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

        self.ladder_image = plt.imread(f'{SOURCE_DIRECTORY}/target_ladder_trans50.png', format='png')
        self.blockr_image = plt.imread(f'{SOURCE_DIRECTORY}/beam_blocker_trans50.png',  format='png')

        # Draw images
        # create new inset axes in data coordinates
        self.TL_xy = [0,0]
        self.BB_xy = [0,0]
        self.axtl = self.ax.inset_axes([self.TL_xy[0],self.TL_xy[1],axisdict['TLV'].width,axisdict['TLV'].height],
                           transform=self.ax.transData)
        self.axtl.imshow(self.ladder_image)
        self.axtl.axis('off')
        self.axbb = self.ax.inset_axes([self.BB_xy[0],self.BB_xy[1],axisdict['BBV'].width,axisdict['BBV'].height],
                           transform=self.ax.transData)
        self.axbb.imshow(self.blockr_image)
        self.axbb.axis('off')
        self.yoff = -10
        self.dis  = 700
        plt.rcParams.update({'font.size': 12})

        self.TL_postext=self.ax.text(self.xmin,self.ymax+self.yoff,
                         "TLH: "+"{:.3f}".format(self.TL_xy[0])+" mm\nTLV: "+"{:.3f}".format(self.TL_xy[1])+" mm",
                         color=axisdict['TLH'].colour)
        self.BB_postext=self.ax.text(self.xmin+100,self.ymax+self.yoff,
                         "BBH: "+"{:.3f}".format(self.BB_xy[0])+" mm\nBBV: "+"{:.3f}".format(self.BB_xy[1])+" mm",
                          color=axisdict['BBH'].colour)

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
        self.axtl = self.ax.inset_axes([self.TL_xy[0],self.TL_xy[1],axisdict['TLV'].width,axisdict['TLV'].width],
                           transform=self.ax.transData)
        self.axtl.imshow(self.ladder_image)
        self.axtl.axis('off')

        self.axbb.remove()
        self.axbb = self.ax.inset_axes([self.BB_xy[0],self.BB_xy[1],axisdict['BBV'].width,axisdict['BBV'].width],
                           transform=self.ax.transData)
        self.axbb.imshow(self.blockr_image)
        self.axbb.axis('off')

        self.TL_postext.remove()
        self.TL_postext=self.ax.text(self.xmin,self.ymax+self.yoff,
                         "TLH: "+"{:.3f}".format(self.TL_xy[0])+" mm\nTLV: "+"{:.3f}".format(self.TL_xy[1])+" mm",
                         color=axisdict['TLH'].colour)
        self.BB_postext.remove()
        self.BB_postext=self.ax.text(self.xmin+200,self.ymax+self.yoff,
                         "BBH: "+"{:.3f}".format(self.BB_xy[0])+" mm\nBBV: "+"{:.3f}".format(self.BB_xy[1])+" mm",
                          color=axisdict['BBH'].colour)


    def get_figure(self):
        return self.fig

#
# DRIVEVIEW CLASS
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
        self.ax = plt.axes( xlim=(self.xmin, self.xmax), ylim=(self.ymin,self.ymax) )
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
        self.TaC_rect = plt.Rectangle((self.xmax-600,-axisdict['TaC'].height/2),
                          axisdict['TaC'].width, axisdict['TaC'].height,
                          fc=axisdict['TaC'].colour)
        self.ax.add_patch(self.TaC_rect)
        
        # ARRAY CARRIAGE
        self.ArC_rect = plt.Rectangle((self.xmin+300, -axisdict['ArC'].height/2),
                          axisdict['ArC'].width, axisdict['ArC'].height,
                          fc=axisdict['ArC'].colour)
        self.ax.add_patch(self.ArC_rect)
        
        # DETECTORS
        self.Det_rect = plt.Rectangle((self.xmax-600+axisdict['TaC'].width-Det_space-axisdict['Det'].width, -axisdict['Det'].height/2),
                          axisdict['Det'].width, axisdict['TLH'].height,
                          fc=axisdict['Det'].colour)
        self.ax.add_patch(self.Det_rect)
        
        # TARGET LADDER
        self.TLH_rect = plt.Rectangle((self.xmax-600+targ_space, -axisdict['TLH'].height/2),
                          axisdict['TLH'].width, axisdict['TLH'].height,
                          fc=axisdict['TLH'].colour)
        self.ax.add_patch(self.TLH_rect)
        
        # ARRAY
        self.SiA_rect = plt.Rectangle((self.xmin+300+Arr_space,-axisdict['SiA'].height/2),
                          axisdict['SiA'].width, axisdict['SiA'].height,
                          fc=axisdict['SiA'].colour)
        self.ax.add_patch(self.SiA_rect)
        
        # ARRAY EDGE
        self.arrayEdge_rect = plt.Rectangle((self.SiA_rect.get_x()+axisdict['SiA'].width,-axisdict['SiA'].height/2),
                            arrayEdge_W, arrayEdge_H,
                            fc=arrayEdgeCol)
        self.ax.add_patch(self.arrayEdge_rect)
        
        # SILENCER
        self.silencer_rect = plt.Rectangle((self.SiA_rect.get_x()+axisdict['SiA'].width+arrayEdge_W,-axisdict['SiA'].height/4),
                           silencerW, arrayEdge_H/2,
                           fc=silencerC)
        self.ax.add_patch(self.silencer_rect)

        # FC CIRCLE
        self.FC_circ = plt.Circle(xy=(self.Det_rect.get_x()+0.5*axisdict['Det'].width,fcH),
                      radius=fcR,
                      fc=axisdict['ArC'].colour)
        self.ax.add_patch(self.FC_circ)
        
        # DE CIRCLE
        self.dE_circ = plt.Circle(xy=(self.Det_rect.get_x()+0.5*axisdict['Det'].width,dEH),
                      radius=dER,
                      fc=axisdict['ArC'].colour)
        self.ax.add_patch(self.dE_circ)

        # RECOIL CIRCLE
        self.recoil_circle = plt.Circle(xy=(self.TLH_rect.get_x()+recoil_target_dist,0),
                        radius=recoilR,
                        fc=recoilFCCol,
                        ec=recoilECol,lw=2.5,hatch='X')
        
        if pvp_draw_si_recoil_dets:
            self.ax.add_patch(self.recoil_circle)
        
        # BEAM BLOCKER
        self.beam_blocker_rect = plt.Rectangle( (blockerpos,-axisdict['BBH'].height/2), axisdict['BBH'].width, axisdict['BBH'].height, fc=axisdict['BBH'].colour )

        if pvp_draw_beam_blocker:
            self.ax.add_patch( self.beam_blocker_rect )
            self.beam_blocker_sl = plt.plot([ blockerSoftLimit, blockerSoftLimit ], [0.5*self.ymin,0.5*self.ymax])
            self.beam_blocker_text = self.ax.text( blockerSoftLimit, 0.5*self.ymax + 20, "BBSL", color='#000000', ha='center' )

        # Label the encoder axes
        self.placeAxisNumbers()

        # Add FC and ZD labels
        self.placeFCZD()

        # Adding information about position
        rand = 20
        dis  = 700
        plt.rcParams.update({'font.size': 12})
        self.postition_text_dict = {
            1 : PositionText( 1, self.xmin, self.ymax - rand, self.TaC_rect.get_x(), axisdict['TaC'].colour ),
            2 : PositionText( 2, self.xmin + dis - 5, self.ymax - rand, self.ArC_rect.get_x(), axisdict['SiA'].colour ),
            3 : PositionText( 3, self.xmin + 2*dis, self.ymax - rand, 0, axisdict['TLH'].colour ),
            4 : PositionText( 4, self.xmin + 3*dis + 5, self.ymax-rand, 0, axisdict['Det'].colour ),
        }

        # Beam Arrow
        self.beamArrow=self.ax.annotate ('', (self.xmin, self.ymax-20*10),
                         (self.xmin+30*10, self.ymax-20*10),
                         arrowprops={'arrowstyle':'<-'} )
        self.beamText=self.ax.text(self.xmin+7*10, self.ymax-18*10,'BEAM')

        # Conversion coefficients
        self.mm2stepsText=self.ax.text(self.xmin, -self.ymax+40,"1 mm = 200 steps")
        self.steps2mmText=self.ax.text(self.xmin, -self.ymax,"1 step = 0.005 mm")

        # Define list of arrows
        self.arrowdict = {
            'd_tip' : ArrowAnnotation(0, 0, 0, 'd_tip', 30),
            'd_recoil' : ArrowAnnotation(0, 0, 0, 'd_recoil', 80),
            'd_si' : ArrowAnnotation(0, 0, 0, 'd_si', -30)
        }

        self.arrowdict['d_recoil'].disable()

        #Makes the space at the sides of the diagrams smaller
        self.fig.tight_layout()

        # ---------- END DRIVEVIEW INIT ------------

    def get_figure(self):
        return self.fig

    def updatePositions(self,pos):
        rand = 6
        dis = 700

        # this is 2023 value from Survey on May 2024
        dis2_3  =  49.4 # this is distance at axis1 = 32577 and axis2 = -40122 from target to silicon
        dis2_3 -=  -40122*step2mm # this is measurement position of axis2
        dis2_3 += 32577*step2mm # this is measurement position of axis1
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

        coord2 = coord3 - dis2_3 - axisdict['SiA'].width - arrayEdge_W - silencerW

        coord1 = coord3 - targ_space
        coord4 = coord1 + axisdict['TaC'].width - Det_space

        # Update position text
        i = 0
        for pos_text in self.postition_text_dict.values():
            if pos_text.axis == 3 or pos_text.axis == 4:
                factor = 1
            else:
                factor = -1
            pos_text.update( factor*pos[i]*0.005 )
            pos_text.draw(self.ax)
            i += 1

        # >>>> AXIS 1 - trolley
        self.TaC_rect.set_x( coord1 )

        # >>>> AXIS 2 - array
        self.SiA_rect.set_x( coord2 )
        self.ArC_rect.set_x( self.SiA_rect.get_x() - Arr_space )
        self.arrayEdge_rect.set_x( self.SiA_rect.get_x() + axisdict['SiA'].width )
        self.silencer_rect.set_x( self.SiA_rect.get_x() + axisdict['SiA'].width + arrayEdge_W )
        # pos1=self.TaC_rect.get_x()


        # >>>> AXIS 3 - target ladder
        self.TLH_rect.set_y( pos[2]*0.005 - axisdict['TLH'].height/2 )
        self.TLH_rect.set_x(coord3)


        # >>>> AXIS 4 - FC/ZD
        self.Det_rect.set_y(pos[3]*0.005-axisdict['Det'].height/2)
        self.Det_rect.set_x(coord4-axisdict['Det'].width)
        self.FC_circ.center=self.Det_rect.get_x()+0.5*axisdict['Det'].width,self.Det_rect.get_y()+axisdict['Det'].height/2+fcH
        self.dE_circ.center=self.Det_rect.get_x()+0.5*axisdict['Det'].width,self.Det_rect.get_y()+axisdict['Det'].height/2+dEH

        # >>>> SILICON RECOIL
        self.recoil_circle.center = self.TLH_rect.get_x() + ( recoil_target_dist, 0 )

        # >>>> BEAM BLOCKER
        

        # ARROWS
        self.arrowdict['d_tip'].update( self.SiA_rect.get_x() + axisdict['SiA'].width + arrayEdge_W + silencerW, self.TLH_rect.get_x(), axisdict['TaC'].height/2 + 10 )
        self.arrowdict['d_recoil'].update( self.TLH_rect.get_x(), self.TLH_rect.get_x() + recoil_target_dist, axisdict['TaC'].height/2 + 10 )
        self.arrowdict['d_si'].update( self.SiA_rect.get_x() + axisdict['SiA'].width, self.TLH_rect.get_x(), -1*( axisdict['TaC'].height/2 + 10 ) )

        for key in self.arrowdict.keys():
            self.arrowdict[key].draw(self.ax)



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
        #self.axisindex=self.ax.text(self.TaC_rect.get_x()+axisdict['TaC'].width/2,self.TaC_rect.get_y()+0.75*axisdict['TaC'].height,
                      #"1",fontsize=nSize,horizontalalignment='center') THIS WAS WHERE THE WEIRD NUMBER ONE WAS COMING FROM - IS IT NEEDED?

        self.number1=self.ax.text(self.TaC_rect.get_x()+axisdict['TaC'].width/2,self.TaC_rect.get_y()+0.75*axisdict['TaC'].height,
                      "1",fontsize=nSize,horizontalalignment='center')
        self.number2=self.ax.text(self.ArC_rect.get_x()+axisdict['ArC'].width/2,self.ArC_rect.get_y()+0.75*axisdict['ArC'].height,
                      "2",fontsize=nSize,horizontalalignment='center')
        self.number3=self.ax.text(self.TLH_rect.get_x()+axisdict['TLH'].width/2,self.TLH_rect.get_y()+0.5*axisdict['TLH'].height,
                      "3",fontsize=nSize,horizontalalignment='center')
        self.number4=self.ax.text(self.Det_rect.get_x()+axisdict['Det'].width/2,self.Det_rect.get_y()+0.5*axisdict['Det'].height,
                      "4",fontsize=nSize,horizontalalignment='center')

    def placeFCZD(self):
        fSize=10
        self.fc=self.ax.text(self.Det_rect.get_x()+axisdict['Det'].width/2,self.Det_rect.get_y()+1.1*axisdict['Det'].height,
                     "FC",fontsize=fSize,horizontalalignment='center')
        self.zd=self.ax.text(self.Det_rect.get_x()+axisdict['Det'].width/2,self.Det_rect.get_y()-0.3*axisdict['Det'].height,
                     "ZD",fontsize=fSize,horizontalalignment='center')


class PosVisPanel(wx.Panel):
    """
    Class that displays the lower part showing the relative positions of drives. There are two parts:
        * DriveView - shows positions of drives as looking perpendicular to beam axis
        * BeamView - shows positions of elements along the beam axis
    """
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
        pos = event.GetValue()
        print( "[", ",".join([ '%6d' % x for x in pos ]), "]" )
        self.driveView.updatePositions(pos)
        self.beamView.updatePositions(pos)
        self.canvas.draw()

    # def move_axis( self, axis, move_distance ):
    #     self.driveView.move_axis( axis, move_distance )
    #     self.canvas.draw()

    # def move1(self,moveDis):
    #     self.driveView.move1(moveDis)
    #     self.canvas.draw()

    # def move2(self,moveDis):
    #     self.driveView.move2(moveDis)
    #     self.canvas.draw()

    # def move3(self,newpos):
    #     self.driveView.move3(newpos)
    #     self.canvas.draw()
        
    # def move4(self,newpos):
    #     self.driveView.move4(newpos)
    #     self.canvas.draw()


class ControlView(wx.Panel):
    """
    Class that displays the upper part of the GUI with the buttons.
    """

    def __init__(self,parent,posvispanel,frame):
        self.driveSystem = DriveSystem.get_instance()

        self.frame=frame
        sizeX = 100 # Horizontal size of the panel (in pixels?!)
        sizeY = 100 # Vertical size of the panel (in pixels?!)
        wx.Panel.__init__(self, parent, size=(sizeX,sizeY))
        self.SetBackgroundColour(windowBackgroundCol)

        self.posvispanel=posvispanel

        #Text Entries and Buttons
        #Sending Command

        # SEND COMMANDS
        # ... Label
        self.sendText = wx.StaticText(self, wx.ID_ANY, "Send any command:", (controlview_text_offset_Y,controlview_text_offset_Y), style=wx.ALIGN_LEFT)

        # ... Text box
        self.writeCommand = wx.TextCtrl(self, wx.ID_ANY, "", (controlview_text_offset_Y,controlview_button_offset_Y), size=(controlview_text_box_width, controlview_null_height))
        self.writeCommand.SetHint("Write any command...")

        # ... Button
        self.sendCommand = wx.Button(self, wx.ID_ANY, "Send", ( controlview_send_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height ) )
        self.sendCommand.Bind(wx.EVT_BUTTON, self.sendingCommandB)
        self.sendCommand.SetToolTip("Send the command in the box to the left to the motor control box")
        self.sendCommand.SetDefault() # Set this as the default button for the window

        # CURRENT AXIS
        # ... Labels
        self.currentAxis = wx.StaticText(self, wx.ID_ANY, "Axis:", (controlview_axis_text_offset_X, controlview_text_offset_Y),style=wx.ALIGN_LEFT)
        self.responseText = wx.StaticText(self, wx.ID_ANY, "Response:", (controlview_response_text_offset_X, controlview_text_offset_Y),style=wx.ALIGN_LEFT)

        # ... Text boxes
        self.currentAx = wx.TextCtrl(self, wx.ID_ANY, "", (controlview_axis_text_offset_X,controlview_button_offset_Y),size=(controlview_axis_text_box_width, controlview_null_height), style=wx.ALIGN_LEFT|wx.TE_READONLY)
        self.commandResponse = wx.TextCtrl(self, wx.ID_ANY, "", (controlview_response_text_offset_X,controlview_button_offset_Y),size=(controlview_text_box_width, controlview_null_height), style=wx.ALIGN_LEFT|wx.TE_READONLY)

        # ABORT/RESET ALL BUTTONS
        self.abortAllButton = wx.Button(self, wx.ID_ANY, "ABORT ALL", (controlview_abort_all_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.abortAllButton.SetBackgroundColour(controlview_abort_all_button_colour)
        self.abortAllButton.Bind(wx.EVT_BUTTON, self.abortAll)
        self.abortAllButton.SetToolTip("Aborts all the motors. Do this in emergencies and before collecting data!")

        self.resetAllButton = wx.Button(self, wx.ID_ANY, "RESET ALL", (controlview_reset_all_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.resetAllButton.Bind(wx.EVT_BUTTON, self.resetAll)
        self.resetAllButton.SetToolTip("Resets all the motors. Tread carefully!")

        #Print Encoder positions
        self.printPos = wx.Button(self, wx.ID_ANY, "Print Pos.", (controlview_print_positions_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.printPos.Bind(wx.EVT_BUTTON, self.printPosB)
        self.printPos.SetToolTip("Prints all the positions to the console, one axis per line")

        # Target change button
        self.XYElementChange = wx.Button(self, wx.ID_ANY, "IN-BEAM", (controlview_in_beam_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.XYElementChange.SetBackgroundColour(controlview_in_beam_button_colour)
        self.XYElementChange.Bind(wx.EVT_BUTTON, self.XYElementChangeWindow )
        self.XYElementChange.SetToolTip("Access the in-beam elements menu to move these into position!")

        #Connect/Disconnect Buttons
        offset  =  100
        buttonW =  110
        sizey   = (sizeY+offset)/5

        self.connectButton = wx.Button(self, wx.ID_ANY, "CONNECT", (int(frameW-buttonW),int(0)),(int(buttonW),int(sizey)))
        self.connectButton.Bind(wx.EVT_BUTTON, self.connectB)
        self.connectButton.SetToolTip("Connect to the serial port")

        self.disconnectButton = wx.Button(self, wx.ID_ANY, "DISCONNECT", (int(frameW-buttonW),int(sizey)),(buttonW,int(sizey)))
        self.disconnectButton.Bind(wx.EVT_BUTTON, self.disconnectB)
        self.disconnectButton.SetToolTip("Disconnect from the serial port")

        self.quitButton = wx.Button(self, wx.ID_ANY, "QUIT", (int(frameW-buttonW),int(sizey*3)),(int(buttonW),int(sizey)))
        self.quitButton.Bind(wx.EVT_BUTTON, self.quitB)
        self.quitButton.SetBackgroundColour(controlview_quit_button_colour)
        self.quitButton.SetToolTip("Quit the program and close the window")

        self.helpButton = wx.Button(self, wx.ID_ANY, "HELP", (int(frameW-buttonW),int(sizey*2)),(int(buttonW),int(sizey)))
        self.helpButton.Bind(wx.EVT_BUTTON, self.openHelp)
        self.helpButton.SetToolTip("Press this if you need help!")

        if self.driveSystem.check_connection()==True:
            self.disconnectButton.SetBackgroundColour(controlview_disconnect_button_connected_colour)
            self.connectButton.Enable(False)
        else:
            self.connectButton.SetBackgroundColour(controlview_connect_button_disconnected_colour)
            self.disconnectButton.Enable(False)


        # Encoder movement buttons
        dx  =  (frameW-buttonW)/7 # Width allowed for each datum button
        dy  =  29         # Height allowed for each datum button
        dis =  dx         # 
        disy = sizeY+30
        plusminusbuttonwidth = 40
        horzpadding = 5
        textwindowwidth = dx - 4*horzpadding - 2*plusminusbuttonwidth
        self.datumButton = []
        self.targetlabel = []
        self.textcontrol = []
        self.moveplus    = []
        self.moveminus   = []
        for i in range(number_of_motor_axes):
            self.datumButton.append( wx.Button( self, wx.ID_ANY, 'Datum ' + str(i+1), (int(i*dis), int(sizeY)), (int(dx), int(dy) )) )
            self.datumButton[i].Bind(wx.EVT_BUTTON, lambda evt,temp=i+1, : self.datumButtonAction(evt,temp))
            self.datumButton[i].SetToolTip(f"Search for datum on axis {i+1} and set as home position")

            self.targetlabel.append(wx.StaticText(self, -1, "("+str(i+1)+"):\n"+axis_labels[i], (int(i*dis),int(disy-70))))
            self.textcontrol.append(wx.TextCtrl(self, wx.ID_ANY, "", (int(i*dis+plusminusbuttonwidth + 2*horzpadding),int(disy)),size=(int(textwindowwidth),-1)))
            self.moveplus.append(wx.Button( self, wx.ID_ANY, "+", (int((i+1)*dis-plusminusbuttonwidth-horzpadding),int(disy)),size=(int(plusminusbuttonwidth),-1)))
            self.moveminus.append(wx.Button(self, wx.ID_ANY, "-", (int(i*dis + horzpadding),   int(disy)),size=(int(plusminusbuttonwidth),-1)))

            self.textcontrol[i].SetHint(f"{i+1}mr (mm)")
            self.moveplus[i].Bind(wx.EVT_BUTTON,  lambda evt,temp=i+1, : self.moveplusAction(evt,temp))
            self.moveplus[i].SetToolTip("Move this many mm in the positive direction")
            self.moveminus[i].Bind(wx.EVT_BUTTON, lambda evt,temp=i+1, : self.moveminusAction(evt,temp))
            self.moveminus[i].SetToolTip("Move this many mm in the negative direction")


        # Access the queue used by the DriveSystemThread
        self.drive_system_thread = DriveSystemThread.get_instance()

        #Event Handlers
        self.Bind(EVT_DISCONNECT, self.changeViewDisconnect)
        
        # Start Thread which checks the positions continuously
        self.positionsCheckerThread = DriveSystemThread.get_instance()
        self.positionsCheckerThread.set_controlview(self)
        self.positionsCheckerThread.set_posvispanel(posvispanel)
        # ---------- END CONTROLVIEW INIT ---------------

    # Makes disconnect button red if not connected
    def changeViewDisconnect(self,event):
        value = event.GetValue()
        if value == 1:
            self.disconnectButton.SetBackgroundColour(controlview_disconnect_button_connected_colour)
            self.connectButton.Enable(False)
            self.connectButton.SetBackgroundColour(control_view_connect_grey)
            self.disconnectButton.Enable(True)
        else:
            self.connectButton.SetBackgroundColour(controlview_connect_button_disconnected_colour)
            self.disconnectButton.Enable(False)
            self.disconnectButton.SetBackgroundColour(control_view_connect_grey)
            self.connectButton.Enable(True)

    def printPosB(self,event):
        self.positionsCheckerThread.send_print_request()

    def sendingCommandB(self,event):
        command = self.writeCommand.GetValue() + '\r'
        element = Element('S', 0, command)
        self.drive_system_thread.add_to_queue(element)

    def connectB(self,event):
        # Cannot mirror disconnect function as the thread stops when the serial port is disconnected...
        self.driveSystem.connect_to_port()
        event = DisConnectEvent(myEVT_DISCONNECT, -1, 1)
        wx.PostEvent(self, event)

    def disconnectB(self,event):
        element=Element('D')
        self.drive_system_thread.add_to_queue(element)
    
    def quitB(self,event):
        self.frame.closeProgram(event)

    def datumButtonAction(self,event,axis):
        element=Element('H',axis)
        self.drive_system_thread.add_to_queue(element)

    # Patrick's ladder
    def XYElementChangeWindow(self,event):
        if XYElementSelectWindow.is_drawn() == False:
            XYElementSelectWindow(self)
        self.window = XYElementSelectWindow.get_instance()
        
    # Motion to do on motor panel -> called directly from the target ladder window select!
    def XYElementMoveAction(self,event):
        element=Element( str( self.window.panel.get_move_motor_panel().globalpos ) )
        self.drive_system_thread.add_to_queue(element)

#    self.ladderselect.get_movement_selection()
    #print(self.ladder_opt)
    # Keep as two functions, as by the time put in if statement, don't save that much space.
    def moveplusAction(self,event,axis):
        disMM = float(self.textcontrol[axis-1].GetValue())
        element=Element('M+-',axis,int(disMM*mm2step))
        self.drive_system_thread.add_to_queue(element)
    def moveminusAction(self,event,axis):
        disMM = -1*float(self.textcontrol[axis-1].GetValue())
        element=Element('M+-',axis,int(disMM*mm2step))
        self.drive_system_thread.add_to_queue(element)

    def openHelp(self,event):
        if HelpWindow.is_drawn() == False:
            HelpWindow(self, "Help")

    def abortAxis( self, event, axis ):
        self.driveSystem.abort_axis(axis)
    
    def resetAxis( self, event, axis ):
        self.driveSystem.reset_axis(axis)

    def abortAll(self,event):
        self.driveSystem.abort_all()
        
    def resetAll(self,event):
        self.driveSystem.reset_all()

    # ----- END CONTROL VIEW CLASS ------


class DriveSystemGUI(wx.Frame):
    def __init__(self, parent, mytitle):
        super(DriveSystemGUI, self).__init__( parent, title=mytitle, size=(frameW,frameH), style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX) )
        self.Bind( wx.EVT_CLOSE, self.closeProgram )
        self.InitUI()
        self.Centre()

    def InitUI(self):
        DriveSystemThread.get_instance().is_gui_running = True
        self.split_win = wx.SplitterWindow(self)
        self.bottom_split = PosVisPanel(self.split_win)
        self.top_split = ControlView(self.split_win,self.bottom_split,self)
        self.split_win.SplitHorizontally(self.top_split, self.bottom_split, controlViewSize)

    def closeProgram(self, event):
        print("Exiting GUI...")

        # Tell thread to stop doing things to the GUI
        DriveSystemThread.get_instance().is_gui_running = False
        
        # Close all top level windows
        for item in wx.GetTopLevelWindows():
            if not isinstance(item, DriveSystemGUI):
                item.Destroy()

        # Self-destruct!
        self.Destroy()

class HelpWindow(wx.Frame):
    instance = None # This is the single instance
    init = False    # This determines whether the panel has already been initialised

    def __new__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = super().__new__(self)
        return self.instance

    def __init__(self, parent, mytitle):
        # Do nothing if already initialised
        if self.init:
            self.Raise() # Moves already initialised window to the top
            return
        
        # First initialisation -> tell code that this is true
        self.init = True
        self.width=430
        self.height=500
        super().__init__(parent, title=mytitle,size=(self.width,self.height))
        self.Bind( wx.EVT_CLOSE, self.onClose)
        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):
        self.panel = wx.lib.scrolledpanel.ScrolledPanel( self, wx.ID_ANY, size=(self.width,self.height ) )
        self.panel.SetupScrolling()
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(vbox)
        lines = [
            "This is a GUI for controlling the ISS Drive System.\n",
            f"The Drive System contains {number_of_motor_axes} axes:",
        ]
        for i in range(0,number_of_motor_axes):
            lines.append( f"  • Axis {i+1}: {axis_labels[i]}" )
        
        lines = lines + [
            "",
            "These axes are represented by the shapes in the bottom panels, labelled by number where appropriate. The coordinate system of the GUI is in millimetres, and is centred around the middle of the magnet. This means, that the limits are ± 2730/2 mm = ± 1365 mm. The smallest step is 0.005 mm = 1/200 mm. The positions on the axes are checked and updated in the GUI every second. The buttons at the top describe the most common actions used, and hovering over the buttons gives a description of what each button does.",
            "",
            "The purple \"IN-BEAM\" button controls the in-beam elements, and can be used for changing target ladder, adding beam-monitoring elements, and adding a downstream beam-blocker.",
            "",
            "Commands can be sent directly to the motor control box using the input window in the top left.",
            "",
            "Some common commands are, where 'n' represents the axis number and 'XXX' represents the encoder position:",
            "  • nmaXXX - move to an absolute encoder position (Move Absolute)",
            "  • nmrXXX - move relative to your current encoder position (Move Relative)",
            "  • ncoXXX - get the status of the motor (Current Operation)",
            "  • nodXXX - get the datum position (Output Datum)",
            "  • noaXXX - get the current axis position (Output Axis)",
            "  • ndaXXX - change the datum position by adding XXX onto its current position (DAtum)"
        ]
        text = "\n".join(lines)
        desc = wx.StaticText(self.panel, wx.ID_ANY, text)
        desc.Wrap(self.width - 50)
        vbox.Add(desc, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL )

    def onClose(self, e):
        self.init = False
        self.Destroy()

    @classmethod
    def get_instance(cls):
        if cls.instance == None:
            cls()
        return cls.instance

    @classmethod
    def is_drawn(cls):
        return cls.init


def main():
    app = wx.App()

    # Initialise DriveSystemThread
    positionsCheckerThread = DriveSystemThread()
   
    # Launch DriveSystemGUI
    gui = DriveSystemGUI(None, "Drive System")

    # Launch CLI? TODO

    # Start thread
    positionsCheckerThread.start()

    # Read saved vals
    f=open(f'{SOURCE_DIRECTORY}/id_dist_map.txt',"r")
    lines=f.readlines()
    for x in lines:
        axisposdict.update({x.split(' ')[0]:[int(x.split(' ')[1]),int(x.split(' ')[2])]})

    f.close()
    gui.Show()
    app.MainLoop()
    positionsCheckerThread.kill_thread()


if __name__ == '__main__':
    try:
        with DRIVE_SYSTEM_LOCK:
            main()
    except Timeout:
        print("Someone else is using the serial port to communicate with the motors. Please stop that process first before running this script.")
