"""
Drive System GUI
================

This module contains all the information required to run the GUI
"""
# MEMORY HELP
# Uncomment this line and add @profile above the function you want to examine. Then run with
# python -m memory_profiler DriveSystem.py ...
# from memory_profiler import profile

import imageio.v3 as iio
import matplotlib
matplotlib.use('WXAgg')
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator
from mpl_toolkits.axes_grid1.inset_locator import InsetPosition
from prompt_toolkit import print_formatted_text
import wx
import wx.lib.scrolledpanel

import drivesystemoptions as dsopts
from drivesystemlib import *
from drivesystemguilib import *
import drivesysteminbeamelementselector
import drivesystemplotview as dspv

ARRAY_IS_UPSTREAM = True

################################################################################
################################################################################
################################################################################
class BeamView(dspv.PlotView):
    """
    This class shows the beam elements as seen looking upstream towards the beam.
    """
    ################################################################################
    def __init__(self, panel : wx.Window):
        """
        BeamView: Initialise using method from base class

        Parameters
        ----------
        panel : wx.Window
            The parent window that owns the BeamView object
        """
        # Initialise using parent init (which calls this class's methods!)
        dspv.PlotView.__init__(self,panel,(beamview_width_inches,beamview_height_inches))

    ################################################################################
    def set_axis_limits(self):
        """
        BeamView: Define axis limits
        """
        self.ymin = -100
        self.ymax =  100
        self.xmin = -100
        self.xmax =  100

    ################################################################################
    def set_axis_options(self):
        """
        BeamView: Specify axis options once self.ax initialised
        """
        # Set colour and positions of axes
        self.ax.spines['right'].set_color('none')
        self.ax.spines['top'].set_color('none')
        self.ax.spines['left'].set_position('center')
        self.ax.spines['bottom'].set_position(('data',0))
        self.ax.set_xlabel("[mm]")
        self.ax.set_aspect('equal')
        
        # Makes the space at the sides of the diagrams smaller
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)


    ################################################################################
    def define_constants(self):
        """
        BeamView: Define constants used for drawing
        """
        # Get position of axis 3 and 5 encoder positions
        try:
            dsopts.AXIS_POSITION_DICT[dsopts.OPTION_TARGET_LADDER_REFERENCE_POINT_ID.get_value()]
            target_ladder_reference_point_id = dsopts.OPTION_TARGET_LADDER_REFERENCE_POINT_ID.get_value()
        except KeyError:
            print_formatted_text("WARNING: couldn't find a reference point on the target ladder. The GUI will assume that the chosen reference point is the alpha source. THIS MAY LEAD TO UNINTENDED CONSEQUENCES. CONSIDER YOURSELF WARNED!!!")
            target_ladder_reference_point_id = 'alpha'

        [self.encoder_target_ladder_reference_X, self.encoder_target_ladder_reference_Y] = dsopts.AXIS_POSITION_DICT[target_ladder_reference_point_id]
        self.target_ladder_offset_X = dsopts.OPTION_TARGET_LADDER_AXIS_3_REFERENCE_POINT.get_value()
        self.target_ladder_offset_Y = dsopts.OPTION_TARGET_LADDER_AXIS_5_REFERENCE_POINT.get_value()

        # Arrays to hold data coordinates of bottom-left corner of inset axes that hold images
        self.beamview_target_ladder_xy = [0,0]

        # Import images to be used for beam view
        # NOTE iio import changes imread type from float32 (LARGE) to (uint8) (LESS LARGE)
        # which helps with memory usage
        self.ladder_image = iio.imread(dsopts.OPTION_TARGET_LADDER_IMAGE_PATH.get_value() )

        # Define transformation from data coordinates to figure coordinates
        self.trans_data_to_figure_coords = self.ax.transData + self.fig.transFigure.inverted()

        # Create inset axis object for target ladder and put image inside
        tl_data_coords = [[
            self.beamview_target_ladder_xy[0], # X0
            self.beamview_target_ladder_xy[1]  # Y0
        ],[
            self.beamview_target_ladder_xy[0] + MOTOR_AXIS_DICT['TLV'].width, # X1
            self.beamview_target_ladder_xy[1] + MOTOR_AXIS_DICT['TLV'].height # Y1 
        ]]

        tl_fig_coords = self.trans_data_to_figure_coords.transform(tl_data_coords)

        # Calculate width and height in figure coordinates
        self.tl_width_fig = tl_fig_coords[1][0] - tl_fig_coords[0][0]
        self.tl_height_fig = tl_fig_coords[1][1] - tl_fig_coords[0][1]

        # Define inset axes
        self.inset_axes_target_ladder = self.ax.inset_axes([
                0, # X
                0, # Y
                self.tl_width_fig,   # width
                self.tl_height_fig   # height
            ], transform=self.fig.transFigure
        )
        self.inset_axes_target_ladder.imshow(self.ladder_image, extent=[0,MOTOR_AXIS_DICT['TLV'].width, MOTOR_AXIS_DICT['TLV'].height, 0], origin='lower') # ymin and ymax reversed as origin = lower
        self.inset_axes_target_ladder.set_xlim(0, MOTOR_AXIS_DICT['TLV'].width)
        self.inset_axes_target_ladder.set_ylim(0, MOTOR_AXIS_DICT['TLV'].height)
        self.inset_axes_target_ladder.set_aspect('equal')
        self.inset_axes_target_ladder.axis('off')

        # Write target ladder and beam blocker position
        position_text_y_offset = -0.03
        trans = self.ax.transAxes + self.ax.transData.inverted()
        self.text_target_ladder_position = self.ax.text( *trans.transform( ( 0.0, 1 - position_text_y_offset ) ), "", color=MOTOR_AXIS_DICT['TLH'].colour, ha='left', va='top' )


        if dsopts.OPTION_IS_BEAM_BLOCKER_ENABLED.get_value():
            # Get position of axis 6 and 7 encoder positions
            try:
                dsopts.AXIS_POSITION_DICT[dsopts.OPTION_BEAM_BLOCKER_REFERENCE_POINT_ID.get_value()]
                beam_blocker_reference_point_id = dsopts.OPTION_BEAM_BLOCKER_REFERENCE_POINT_ID.get_value()
            except KeyError:
                print_formatted_text("WARNING: couldn't find a reference point on the beam blocker. The GUI will assume that the chosen reference point is the middle head. THIS MAY LEAD TO UNINTENDED CONSEQUENCES. CONSIDER YOURSELF WARNED!!!")
                beam_blocker_reference_point_id = 'bb.medium'
            
            [self.encoder_beam_blocker_middle_head_X, self.encoder_beam_blocker_middle_head_Y] = dsopts.AXIS_POSITION_DICT[beam_blocker_reference_point_id]
            self.beam_blocker_offset_X = dsopts.OPTION_BEAM_BLOCKER_AXIS_6_REFERENCE_POINT.get_value()
            self.beam_blocker_offset_Y = dsopts.OPTION_BEAM_BLOCKER_AXIS_7_REFERENCE_POINT.get_value()

            # Arrays to hold data coordinates of bottom-left corner of inset axes that hold images
            self.beamview_beam_blocker_xy = [0,0]

            # Import images to be used for beam view
            # NOTE iio import changes imread type from float32 (LARGE) to (uint8) (LESS LARGE)
            # which helps with memory usage
            self.blocker_image = iio.imread(dsopts.OPTION_BEAM_BLOCKER_IMAGE_PATH.get_value() )

            # Create inset axis object for beam blocker and put image inside
            data_bb_coords = [[
                self.beamview_beam_blocker_xy[0], # X0
                self.beamview_beam_blocker_xy[1]  # Y0
            ],[
                self.beamview_beam_blocker_xy[0] + MOTOR_AXIS_DICT['BBV'].width, # X1
                self.beamview_beam_blocker_xy[1] + MOTOR_AXIS_DICT['BBV'].height # Y1 
            ]]

            fig_bb_coords = self.trans_data_to_figure_coords.transform(data_bb_coords)
            self.bb_width_fig = fig_bb_coords[1][0] - fig_bb_coords[0][0]
            self.bb_height_fig = fig_bb_coords[1][1] - fig_bb_coords[0][1]

            self.inset_axes_beam_blocker = self.ax.inset_axes([
                    fig_bb_coords[0][0],
                    fig_bb_coords[0][1],
                    self.bb_width_fig,
                    self.bb_height_fig
                ],transform=self.fig.transFigure
            )
            self.inset_axes_beam_blocker.imshow(self.blocker_image, extent=[0,MOTOR_AXIS_DICT['BBV'].width, MOTOR_AXIS_DICT['BBV'].height, 0], origin='lower') # ymin and ymax reversed as origin = lower
            self.inset_axes_beam_blocker.set_xlim(0, MOTOR_AXIS_DICT['BBV'].width)
            self.inset_axes_beam_blocker.set_ylim(0, MOTOR_AXIS_DICT['BBV'].height)
            self.inset_axes_beam_blocker.set_aspect('equal')
            self.inset_axes_beam_blocker.axis('off')

            # Write target ladder and beam blocker position
            self.text_beam_blocker_position = self.ax.text( *trans.transform( ( 0.6, 1 - position_text_y_offset ) ), "", color=MOTOR_AXIS_DICT['BBH'].colour, ha='left', va='top' )

    ################################################################################
    def draw_objects(self, pos : list):
        """
        BeamView: Function used to draw/redraw objects.

        Parameters
        ----------
        pos : list
            The positions of all of the motor axes
        """
        # Calculate positions for target ladder and beam blocker
        if self.inset_axes_target_ladder.get_visible():
            # Update coordinates
            self.beamview_target_ladder_xy = [
                ( pos[2] - self.encoder_target_ladder_reference_X)*STEP_TO_MM - self.target_ladder_offset_X,
                (-pos[4] + self.encoder_target_ladder_reference_Y)*STEP_TO_MM - self.target_ladder_offset_Y
            ]
            new_tl_coords = self.trans_data_to_figure_coords.transform(self.beamview_target_ladder_xy)

            # Change position of target ladder
            ip = InsetPosition(self.ax,[new_tl_coords[0], new_tl_coords[1], self.tl_width_fig, self.tl_height_fig])
            self.inset_axes_target_ladder.set_axes_locator(ip)

        # Edit target ladder text
        self.text_target_ladder_position.set_text( f"TLH: {self.beamview_target_ladder_xy[0]:.3f} mm\nTLV: {self.beamview_target_ladder_xy[1]:.3f} mm" )

        if dsopts.OPTION_IS_BEAM_BLOCKER_ENABLED.get_value():
            if self.inset_axes_beam_blocker.get_visible():
                # Update coordinates
                self.beamview_beam_blocker_xy = [
                    ( pos[5] - self.encoder_beam_blocker_middle_head_X)*STEP_TO_MM - self.beam_blocker_offset_X,
                    (-pos[6] + self.encoder_beam_blocker_middle_head_Y)*STEP_TO_MM - self.beam_blocker_offset_Y
                ]
                new_bb_coords = self.trans_data_to_figure_coords.transform(self.beamview_beam_blocker_xy)

                # Change position of beam blocker
                ip = InsetPosition(self.ax,[new_bb_coords[0], new_bb_coords[1], self.bb_width_fig, self.bb_height_fig])
                self.inset_axes_beam_blocker.set_axes_locator(ip)

            self.text_beam_blocker_position.set_text(  f"BBH: {self.beamview_beam_blocker_xy[0]:.3f} mm\nBBV: {self.beamview_beam_blocker_xy[1]:.3f} mm" )
        
        
    ################################################################################
    def remove_objects(self):
        """
        BeamView: Delete objects here
        """
        # NOTHING TO DO HERE!
        pass
        
    ################################################################################
    def show_target_ladder(self):
        """
        BeamView: Enables the display of the target ladder
        """
        self.inset_axes_target_ladder.set_visible(True)
        self.draw_canvas()
    
    ################################################################################
    def hide_target_ladder(self):
        """
        BeamView: Disables the display of the target ladder
        """
        self.inset_axes_target_ladder.set_visible(False)
        self.draw_canvas()
    
    ################################################################################
    def show_beam_blocker(self):
        """
        BeamView: Enables the display of the beam blocker
        """
        self.inset_axes_beam_blocker.set_visible(True)
    
    ################################################################################
    def hide_beam_blocker(self):
        """
        BeamView: Disables the display of the beam blocker
        """
        self.inset_axes_beam_blocker.set_visible(False)
   
################################################################################
################################################################################
################################################################################
class BeamViewButtons:
    """
    A class that controls the 
    """
    ################################################################################
    def __init__(self, parent : wx.Window, beamview : BeamView):
        """
        BeamViewButtons: Initialise class, which contains tickboxes and can send 
        commands to the BeamView object

        Parameters
        ----------
        parent : wx.Window
            The window containing the BeamViewButtons object
        beamview : BeamView
            The BeamView object
        """
        # Store beamview object
        self.beamview = beamview

        # Define checkboxes
        self.sizer = wx.BoxSizer( wx.VERTICAL )
        
        # Target ladder checkbox
        self.checkbox_target_ladder = wx.CheckBox( parent, wx.ID_ANY, label="Target ladder" )
        self.sizer.Add( self.checkbox_target_ladder, 0, wx.ALL, 2 )

        # Beam blocker checkbox
        self.is_beam_blocker_enabled = dsopts.OPTION_IS_BEAM_BLOCKER_ENABLED.get_value()
        if self.is_beam_blocker_enabled:
            self.checkbox_beam_blocker = wx.CheckBox( parent, wx.ID_ANY, label="Beam blocker" )
            self.sizer.Add( self.checkbox_beam_blocker, 0, wx.ALL, 2 )
        
        # Set checkbox sizer
        self.sizer.SetSizeHints(parent)
        parent.SetSizer(self.sizer)

        # Set values to true and bind options
        self.checkbox_target_ladder.SetValue( True)
        self.checkbox_target_ladder.Bind( wx.EVT_CHECKBOX, self.target_ladder_box_ticked )
        
        if self.is_beam_blocker_enabled:
            self.checkbox_beam_blocker.SetValue( True )
            self.checkbox_beam_blocker.Bind( wx.EVT_CHECKBOX, self.beam_blocker_box_ticked )

    ################################################################################
    def target_ladder_box_ticked(self, event : wx._core.CommandEvent):
        """
        BeamViewButtons: Function triggered by the checkbox_target_ladder object for
        showing/hiding the target ladder
        """
        if self.checkbox_target_ladder.IsChecked():
            self.beamview.show_target_ladder()
        else:
            self.beamview.hide_target_ladder()

    ################################################################################
    def beam_blocker_box_ticked(self, event):
        """
        BeamViewButtons: Function triggered by the checkbox_beam_blocker object for
        showing/hiding the beam blocker
        """
        if self.checkbox_beam_blocker.IsChecked():
            self.beamview.show_beam_blocker()
        else:
            self.beamview.hide_beam_blocker()



################################################################################
################################################################################
################################################################################
class DriveView(dspv.PlotView):
    ################################################################################
    def __init__(self, panel):
        """
        DriveView: Initialise using method from base class

        Parameters
        ----------
        panel : wx.Panel
            The parent panel that owns the DriveView object
        """
        # Initialise using parent init (which calls this class's methods!)
        dspv.PlotView.__init__(self,panel,(driveview_width_inches,driveview_height_inches))

    ################################################################################
    def set_axis_limits(self):
        """
        DriveView: Define axis limits
        """
        self.ymin = -400
        self.ymax =  400
        self.xmin = -MAGNET_LENGTH*0.5
        self.xmax =  MAGNET_LENGTH*0.5

    ################################################################################
    def set_axis_options(self):
        """
        DriveView: Specify axis options once self.ax initialised
        """
        # Colour the axes
        self.ax.spines['right'].set_color('none')
        self.ax.spines['top'].set_color('none')
        self.ax.spines['left'].set_color('none')
        self.ax.spines['bottom'].set_position(('data',-2.765))
        
        # Remove vertical ticks
        self.ax.set_yticks([])

        # Define tick spacing for x axis
        majorLocator = MultipleLocator(500)
        minorLocator = MultipleLocator(100)
        self.ax.xaxis.set_major_locator(majorLocator)
        
        # For the minor ticks, use no labels; default NullFormatter
        self.ax.xaxis.set_minor_locator(minorLocator)
        self.ax.set_xlabel("[mm]")

        # Makes the space at the sides of the diagrams smaller
        self.fig.tight_layout()

    ################################################################################
    def define_constants(self):
        """
        DriveView: Define constants used for drawing. All elements are drawn in 
        their nominal positions.
        """
        # Adding the four rectangles + array which belongs to ax 2
        # Rectangle( (anchor point in bottom left - set to zero if it will be updated), width, height, colour)

        # Get physical lengths from options and define some new ones here
        self.silencer_length_from_tip = dsopts.get_silencer_length_from_tip()
        self.array_carriage_to_target_length = 20
        self.array_carriage_to_ancillary_length = 20
        self.faraday_cup_encoder_position = dsopts.AXIS_POSITION_DICT.get("bm.fc",[None])[0]
        self.zd_encoder_position = dsopts.AXIS_POSITION_DICT.get("bm.zd",[None])[0]

        # Define shapes
        self.rectangle_ArC = plt.Rectangle((0, -MOTOR_AXIS_DICT['ArC'].height/2), MOTOR_AXIS_DICT['ArC'].width, MOTOR_AXIS_DICT['ArC'].height, fc=MOTOR_AXIS_DICT['ArC'].colour) # Array carriage
        self.rectangle_TaC = plt.Rectangle((0,-MOTOR_AXIS_DICT['TaC'].height/2), MOTOR_AXIS_DICT['TaC'].width, MOTOR_AXIS_DICT['TaC'].height, fc=MOTOR_AXIS_DICT['TaC'].colour)  # Target carriage
        self.rectangle_Det = plt.Rectangle((0,0), MOTOR_AXIS_DICT['Det'].width, MOTOR_AXIS_DICT['TLH'].height, fc=MOTOR_AXIS_DICT['Det'].colour)                          # Ancillary detectors (FC/ZD)
        self.rectangle_TLH = plt.Rectangle((0,0), MOTOR_AXIS_DICT['TLH'].width, MOTOR_AXIS_DICT['TLH'].height,fc=MOTOR_AXIS_DICT['TLH'].colour)                           # Horizontal target ladder
        self.rectangle_SiA = plt.Rectangle((0,-MOTOR_AXIS_DICT['SiA'].height/2), MOTOR_AXIS_DICT['SiA'].width, MOTOR_AXIS_DICT['SiA'].height, fc=MOTOR_AXIS_DICT['SiA'].colour)  # Silicon array
        self.rectangle_array_not_silicon = plt.Rectangle((0,-MOTOR_AXIS_DICT['SiA'].height/2), ARRAY_SILICON_TO_TIP_DISTANCE, MOTOR_AXIS_DICT['SiA'].height, fc=arrayEdgeCol)                   # Array "edge" (non-silicon part)
        self.silencer_rect = plt.Rectangle((0,-MOTOR_AXIS_DICT['SiA'].height/4), self.silencer_length_from_tip, MOTOR_AXIS_DICT['SiA'].height/2, fc=silencerC)                                    # Silencer
        self.circle_faraday_cup = plt.Circle(xy=(0,0), radius=21, fc=MOTOR_AXIS_DICT['ArC'].colour)                                                        # FC circle
        self.circle_zd = plt.Circle(xy=(0,0), radius=20, fc=MOTOR_AXIS_DICT['ArC'].colour)            # ZD circle
        self.circle_si_recoil = plt.Circle(xy=(self.rectangle_TLH.get_x()+recoil_target_dist,0),radius=50, fc=recoilFCCol, ec=recoilECol,lw=2.5,hatch='X') # Si recoil circle
        self.rectangle_BBH = plt.Rectangle( (blockerpos,-MOTOR_AXIS_DICT['BBH'].height/2), MOTOR_AXIS_DICT['BBH'].width, MOTOR_AXIS_DICT['BBH'].height, fc=MOTOR_AXIS_DICT['BBH'].colour ) # Beam blocker

        # Add shapes to drawing (in correct order!)
        self.ax.add_patch(self.rectangle_TaC)  # Target carriage
        self.ax.add_patch(self.rectangle_ArC)  # Array carriage
        self.ax.add_patch(self.rectangle_Det)  # Ancillary detectors (FC/ZD)
        self.ax.add_patch(self.rectangle_TLH)  # Target ladder
        self.ax.add_patch(self.rectangle_SiA)  # Silicon array
        self.ax.add_patch(self.rectangle_array_not_silicon) # Array "edge" (non-silicon part)
        self.ax.add_patch(self.silencer_rect)  # Silencer
        self.ax.add_patch(self.circle_faraday_cup) # FC circle
        self.ax.add_patch(self.circle_zd)          # ZD circle
        if pvp_draw_si_recoil_dets:
            self.ax.add_patch(self.circle_si_recoil) # Si recoil circle
        if pvp_draw_beam_blocker:
            self.ax.add_patch( self.rectangle_BBH ) # Beam blocker
            self.line_BBH_soft_limit = plt.plot([ blockerSoftLimit, blockerSoftLimit ], [0.5*self.ymin,0.5*self.ymax])
            self.text_BBH = self.ax.text( blockerSoftLimit, 0.5*self.ymax + 20, "BBSL", color='#000000', ha='center' )

        # Define list of arrows
        # ArrowAnnotation(x1, x2, height, label, label_offset)
        self.arrowdict : dict[str,ArrowAnnotation] = {
            'd_tip' :    ArrowAnnotation(0, 0, 0, 'd_tip',    30),
            'd_recoil' : ArrowAnnotation(0, 0, 0, 'd_recoil', 80),
            'd_si' :     ArrowAnnotation(0, 0, 0, 'd_si',    -30)
        }

        # Enable/disable arrows
        self.arrowdict['d_recoil'].disable()

        # Text objects that show positions - transform from "axes" coordinates to "data" coordinates with trans
        # https://matplotlib.org/stable/users/explain/artists/transforms_tutorial.html
        trans = self.ax.transAxes + self.ax.transData.inverted()
        position_text_y_offset = -0.01
        position_text_spacing = 0.25

        self.position_text_dict : dict[int,PositionText]= {
            1 : PositionText( 1, *trans.transform( ( 0*position_text_spacing, 1 - position_text_y_offset) ), 0, MOTOR_AXIS_DICT['TaC'].colour ),
            2 : PositionText( 2, *trans.transform( ( 1*position_text_spacing, 1 - position_text_y_offset) ), 0, MOTOR_AXIS_DICT['SiA'].colour ),
            3 : PositionText( 3, *trans.transform( ( 2*position_text_spacing, 1 - position_text_y_offset) ), 0, MOTOR_AXIS_DICT['TLH'].colour ),
            4 : PositionText( 4, *trans.transform( ( 3*position_text_spacing, 1 - position_text_y_offset) ), 0, MOTOR_AXIS_DICT['Det'].colour ),
        }

        # Encoder positive direction arrows
        if ARRAY_IS_UPSTREAM:
            arrow_type = '<-'
            arrow_encoder_positive_along_beam_X_start = self.xmin + 100
            arrow_encoder_positive_along_beam_X_end = self.xmin
            arrow_encoder_positive_along_beam_Y = self.ymin + 100
        else:
            arrow_encoder_positive_along_beam_X_start = self.xmin
            arrow_encoder_positive_along_beam_X_end = self.xmin + 100
            arrow_encoder_positive_along_beam_Y = self.ymin + 100 + 100*driveview_height_inches/driveview_width_inches
            arrow_type = '->'

        # Beam arrow
        self.arrow_beam_direction = self.ax.annotate ('', (self.xmin, self.ymax-20*10), (self.xmin+30*10, self.ymax-20*10), arrowprops={'arrowstyle':arrow_type} )
        self.text_beam_direction = self.ax.text(self.xmin+7*10, self.ymax-18*10,'BEAM')

        # Encoder positive direction
        self.arrow_encoder_positive_along_beam = self.ax.annotate('',(arrow_encoder_positive_along_beam_X_start,arrow_encoder_positive_along_beam_Y), (arrow_encoder_positive_along_beam_X_end,arrow_encoder_positive_along_beam_Y),arrowprops={'arrowstyle':arrow_type})
        self.arrow_encoder_positive_perpendicular_to_beam = self.ax.annotate('',(self.xmin+100,self.ymin + 100), (self.xmin+100,self.ymin + 100 + 100*driveview_height_inches/driveview_width_inches),arrowprops={'arrowstyle':arrow_type})
        self.text_encoder_positive_label = self.ax.text(self.xmin + 120,self.ymin + 100,'Encoder +ve')

        # Conversion coefficients
        self.text_mm_to_steps = self.ax.text(self.xmin, -self.ymax + 40, "1 mm = 200 steps")
        self.text_steps_to_mm = self.ax.text(self.xmin, -self.ymax, "1 step = 0.005 mm")

        # Axis numbers
        axis_number_font_size=18
        self.text_axis_1_label=self.ax.text( 0, 0, "1", fontsize=axis_number_font_size, horizontalalignment='center')
        self.text_axis_2_label=self.ax.text( 0, 0, "2", fontsize=axis_number_font_size, horizontalalignment='center')
        self.text_axis_3_label=self.ax.text( 0, 0, "3", fontsize=axis_number_font_size, horizontalalignment='center')
        self.text_axis_4_label=self.ax.text( 0, 0, "4", fontsize=axis_number_font_size, horizontalalignment='center')

        # FC and ZD labels
        fczd_label_font_size=10
        self.text_fc_label=self.ax.text( 0, 0, "FC", fontsize=fczd_label_font_size, horizontalalignment='center' )
        self.text_zd_label=self.ax.text( 0, 0, "ZD", fontsize=fczd_label_font_size, horizontalalignment='center' )

    ################################################################################
    def draw_objects(self, pos : list):
        """
        DriveView: Function used to draw/redraw objects

        Parameters
        ----------
        pos : list
            The positions of all of the motor axes
        """
        # Calculate the distance between the end of the silencer and the target ladder
        silencer_target_distance = dsopts.OPTION_ARRAY_TIP_TO_TARGET_LADDER_AT_SPECIFIED_ENCODER_POSITIONS.get_value()  # this is initial distance between tip of the array (no silencer) to the target ladder
        silencer_target_distance -= dsopts.OPTION_ENCODER_AXIS_TWO.get_value()*STEP_TO_MM # this is measurement encoder position of axis 2
        silencer_target_distance += dsopts.OPTION_ENCODER_AXIS_ONE.get_value()*STEP_TO_MM # this is measurement encoder position of axis 1
        silencer_target_distance += pos[1]*STEP_TO_MM # add on distance of array from encoder axis 2
        silencer_target_distance -= pos[0]*STEP_TO_MM # add on distance of target from encoder axis 1
        silencer_target_distance -= self.silencer_length_from_tip # length of the silencer

        # TODO this is 2023 value from Survey on 25th October 2023 (elog:3752)
        recoil_pos = pos[0]*STEP_TO_MM + recoil_target_dist # now on the axis 1 carriage

        # Assuming that target at encoder position 0 is 1234.0 mm from back of magnet (elog:2891)
        coord3  = MAGNET_LENGTH/2 - 1234.0 - pos[0]*STEP_TO_MM # This is top-left corner of target ladder rectangle
        coord2 = coord3 - silencer_target_distance - MOTOR_AXIS_DICT['SiA'].width - ARRAY_SILICON_TO_TIP_DISTANCE - self.silencer_length_from_tip # This is top left corner of silicon array
        coord1 = coord3 - self.array_carriage_to_target_length # This is top left corner of trolley axis
        coord4 = coord1 + MOTOR_AXIS_DICT['TaC'].width - self.array_carriage_to_ancillary_length # This is top right corner of FC/ZD rectangle

        # Update position text
        i = 0
        for pos_text in self.position_text_dict.values():
            if pos_text.axis == 3 or pos_text.axis == 4:
                factor = 1
            else:
                factor = -1
            pos_text.update( factor*pos[i]*STEP_TO_MM )
            pos_text.draw( self.ax )
            i += 1

        # >>>> AXIS 1 - trolley
        self.rectangle_TaC.set_x( coord1 )

        # >>>> AXIS 2 - array
        self.rectangle_SiA.set_x( coord2 )
        self.rectangle_ArC.set_x( self.rectangle_SiA.get_x() - MOTOR_AXIS_DICT['ArC'].width/2 )
        self.rectangle_array_not_silicon.set_x( self.rectangle_SiA.get_x() + MOTOR_AXIS_DICT['SiA'].width )
        self.silencer_rect.set_x( self.rectangle_SiA.get_x() + MOTOR_AXIS_DICT['SiA'].width + ARRAY_SILICON_TO_TIP_DISTANCE )

        # >>>> AXIS 3 - target ladder
        self.rectangle_TLH.set_y( pos[2]*STEP_TO_MM - MOTOR_AXIS_DICT['TLH'].height/2 )
        self.rectangle_TLH.set_x(coord3)

        # >>>> AXIS 4 - FC/ZD
        self.rectangle_Det.set_y( pos[3]*STEP_TO_MM - MOTOR_AXIS_DICT['Det'].height/2 )
        self.rectangle_Det.set_x( coord4 - MOTOR_AXIS_DICT['Det'].width )
        self.circle_faraday_cup.center = (self.rectangle_Det.get_x() + 0.5*MOTOR_AXIS_DICT['Det'].width, self.rectangle_Det.get_y() + MOTOR_AXIS_DICT['Det'].height/2 - self.faraday_cup_encoder_position*STEP_TO_MM )
        self.circle_zd.center = (self.rectangle_Det.get_x() + 0.5*MOTOR_AXIS_DICT['Det'].width, self.rectangle_Det.get_y() + MOTOR_AXIS_DICT['Det'].height/2 - self.zd_encoder_position*STEP_TO_MM )

        # >>>> SILICON RECOIL
        # self.circle_si_recoil.center = self.rectangle_TLH.get_x() + ( recoil_target_dist, 0 )

        # >>>> BEAM BLOCKER
        

        # ARROWS
        self.arrowdict['d_tip'].update( self.rectangle_SiA.get_x() + MOTOR_AXIS_DICT['SiA'].width + ARRAY_SILICON_TO_TIP_DISTANCE + self.silencer_length_from_tip, self.rectangle_TLH.get_x(), MOTOR_AXIS_DICT['TaC'].height/2 + 10 )
        self.arrowdict['d_recoil'].update( self.rectangle_TLH.get_x(), self.rectangle_TLH.get_x() + recoil_target_dist, MOTOR_AXIS_DICT['TaC'].height/2 + 10 )
        self.arrowdict['d_si'].update( self.rectangle_SiA.get_x() + MOTOR_AXIS_DICT['SiA'].width, self.rectangle_TLH.get_x(), -1*( MOTOR_AXIS_DICT['TaC'].height/2 + 10 ) )

        for key in self.arrowdict.keys():
            self.arrowdict[key].draw(self.ax)


        # Axis labels - update X and Y
        self.text_axis_1_label.set_x( self.rectangle_TaC.get_x() + MOTOR_AXIS_DICT['TaC'].width/2 )
        self.text_axis_2_label.set_x( self.rectangle_ArC.get_x() + MOTOR_AXIS_DICT['ArC'].width/2 )
        self.text_axis_3_label.set_x( self.rectangle_TLH.get_x() + MOTOR_AXIS_DICT['TLH'].width/2 )
        self.text_axis_4_label.set_x( self.rectangle_Det.get_x() + MOTOR_AXIS_DICT['Det'].width/2 )

        self.text_axis_1_label.set_y( self.rectangle_TaC.get_y() + 0.75*MOTOR_AXIS_DICT['TaC'].height )
        self.text_axis_2_label.set_y( self.rectangle_ArC.get_y() + 0.75*MOTOR_AXIS_DICT['ArC'].height )
        self.text_axis_3_label.set_y( self.rectangle_TLH.get_y() + 0.5*MOTOR_AXIS_DICT['TLH'].height )
        self.text_axis_4_label.set_y( self.rectangle_Det.get_y() + 0.5*MOTOR_AXIS_DICT['Det'].height )


        # Add FC and ZD labels
        self.text_fc_label.set_x( self.rectangle_Det.get_x() + MOTOR_AXIS_DICT['Det'].width/2 )
        self.text_zd_label.set_x( self.rectangle_Det.get_x() + MOTOR_AXIS_DICT['Det'].width/2 )

        self.text_fc_label.set_y( self.rectangle_Det.get_y() + 1.1*MOTOR_AXIS_DICT['Det'].height )
        self.text_zd_label.set_y( self.rectangle_Det.get_y() - 0.3*MOTOR_AXIS_DICT['Det'].height )

    ################################################################################
    def remove_objects(self):
        """
        DriveView: Delete objects here
        """
        # NOTHING TO DO HERE!
        pass

################################################################################
################################################################################
################################################################################
class PosVisPanel(wx.Window):
    """
    Class that displays the lower part showing the relative positions of 
    the motorised elements within ISS. There are two parts:
      - DriveView - shows positions of drives as looking perpendicular to the 
        beam axis.
      - BeamView - shows positions of elements along the beam axis.
    """
    ################################################################################
    def __init__(self, parent):
        """
        PosVisPanel: This initialises the position visualisation panel, and creates
        the children DriveView and BeamView objects.
        """
        # Call parent constructor
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=(drive_system_gui_width,posvispanel_height))

        # Define splitter window for containing DriveView and BeamView objects
        self.splitter_window = wx.SplitterWindow(self,size=(drive_system_gui_width,posvispanel_height), style=wx.SP_THIN_SASH)
        self.splitter_window.SetBackgroundColour(drivesystem_window_background_colour())

        # Define panels for holding DriveView and BeamView objects
        self.driveview_panel = wx.Panel(self.splitter_window,size=(driveview_width,posvispanel_height))
        self.beamview_splitter=wx.SplitterWindow(self.splitter_window,size=(beamview_width,posvispanel_height), style=wx.SP_THIN_SASH)

        # Split BeamView panel into top and bottom
        self.beamview_panel = wx.Panel(self.beamview_splitter,size=(beamview_width,posvispanel_height - posvispanel_footer_height))
        self.beamview_buttons_panel = wx.Panel(self.beamview_splitter,size=(beamview_width,posvispanel_footer_height))

        # Create DriveView and BeamView objects
        self.driveview = DriveView(self.driveview_panel)
        self.beamview = BeamView(self.beamview_panel)
        self.beamview_buttons = BeamViewButtons(self.beamview_buttons_panel, self.beamview)

        # Define what goes in the panel split
        self.splitter_window.SplitVertically(self.driveview_panel,self.beamview_splitter,0)
        self.beamview_splitter.SplitHorizontally( self.beamview_panel, self.beamview_buttons_panel, 0)


    ################################################################################
    def update_positions(self,pos):
        """
        PosVisPanel: Calls update positions on the separate elements and redraws
        """
        # Get new positions

        # Update the positions for the two views
        self.driveview.update_positions(pos)
        self.beamview.update_positions(pos)

        # Redraw the canvases
        self.driveview.draw_canvas()
        self.beamview.draw_canvas()

################################################################################
################################################################################
################################################################################
class ControlViewAxisPanel(wx.Panel):
    """
    ControlViewAxisPanel is a class that contains all the buttons needed for each
    individual axis. This is then tiled in the ControlView object for the number
    of axes available. It also can be disabled or paused as needed
    """
    ################################################################################
    def __init__(self, parent : wx.Panel, axis : int, *args, **kwargs) -> None:
        """
        ControlViewAxisPanel: Initialise the panel
        """
        # Get the instance of the serial interface so that commands can be sent via the buttons
        self.drive_system = DriveSystem.get_instance()

        # Initialise the parent constructor
        wx.Panel.__init__(self, parent, *args, **kwargs )
        size = self.GetSize()

        # Labels for axis label
        self.textlist_axis_label = wx.StaticText(self, wx.ID_ANY, "("+str(axis)+"):\n"+AXIS_LABELS[axis-1], (0,0))
        
        # Check if this is a disabled panel
        if axis in dsopts.OPTION_DISABLED_AXES.get_value():
            self.disabled_panel = wx.StaticText(self, wx.ID_ANY, "AXIS DISABLED", (0, 0.25*size[1]), (size[0],0.5*size[1]), wx.ALIGN_CENTRE_HORIZONTAL )
            self.disabled_panel.SetBackgroundColour("#FF0000")
            return

        # Dimensions
        plus_minus_button_width = 40
        horzpadding = 5
        button_offset_Y = 40
        mr_offset_Y = button_offset_Y + controlview_button_height + horzpadding
        textwindowwidth = size[0] - 2*horzpadding - 2*plus_minus_button_width
        axis_button_width = int( np.floor(size[0]/3))

        
        # # Abort button
        self.button_abort = wx.Button( self, wx.ID_ANY, 'ABORT', (0,button_offset_Y), (int(axis_button_width), int(controlview_button_height) ) )
        self.button_abort.Bind( wx.EVT_BUTTON, lambda evt, : self.button_func_abort(evt,axis) )
        self.button_abort.SetToolTip(f"Abort axis {axis}")
        self.button_abort.SetBackgroundColour(controlview_abort_all_button_colour)

        # # Datum button
        self.button_datum = wx.Button( self, wx.ID_ANY, 'DATUM', (axis_button_width,button_offset_Y), (axis_button_width, controlview_button_height ))
        self.button_datum.Bind(wx.EVT_BUTTON, lambda evt, : self.button_func_datum(evt,axis))
        self.button_datum.SetToolTip(f"Search for datum on axis {axis} and set as home position")

        # # Reset button
        self.button_reset = wx.Button( self, wx.ID_ANY, 'RESET', (2*axis_button_width, button_offset_Y ), (axis_button_width, controlview_button_height ) )
        self.button_reset.Bind( wx.EVT_BUTTON, lambda evt, : self.button_func_reset(evt,axis) )
        self.button_reset.SetToolTip(f"Reset axis {axis}")
        self.button_reset.SetBackgroundColour(controlview_reset_all_button_colour)

        # Move relative input box
        self.textctrl_move_relative_input = wx.TextCtrl(self, wx.ID_ANY, "", (int(plus_minus_button_width + horzpadding),mr_offset_Y),size=(int(textwindowwidth),controlview_button_height))
        self.textctrl_move_relative_input.SetHint(f"{axis}mr (mm)")

        # # Move plus button
        self.button_move_plus = wx.Button( self, wx.ID_ANY, "+", (0,mr_offset_Y),size=(plus_minus_button_width,controlview_button_height))
        self.button_move_plus.Bind(wx.EVT_BUTTON,  lambda evt, : self.button_func_move_plus(evt,axis))
        self.button_move_plus.SetToolTip("Move this many mm in the positive direction")
        
        # # Move minus button
        self.button_move_minus = wx.Button(self, wx.ID_ANY, "-", (size[0]-plus_minus_button_width,mr_offset_Y),size=(plus_minus_button_width,controlview_button_height))
        self.button_move_minus.Bind(wx.EVT_BUTTON, lambda evt, : self.button_func_move_minus(evt,axis))
        self.button_move_minus.SetToolTip("Move this many mm in the negative direction")

        # Define a boolean to determine if motion is paused
        self.pause_panel = wx.StaticText(self, wx.ID_ANY, "AXIS PAUSED", (0, 0.25*size[1]), (size[0],0.5*size[1]), wx.ALIGN_CENTRE_HORIZONTAL )
        self.pause_panel.Hide()
        self.pause_panel.SetBackgroundColour("#FFFF00")        

    ################################################################################
    def button_func_datum(self,event, axis : int) -> None:
        """
        ControlViewAxisPanel: Function triggered by button_datum[axis] to datum the axes
        """
        self.drive_system.datum_search(axis)
        return
        
    ################################################################################
    def button_func_move_plus(self,event,axis : int) -> None:
        """
        ControlViewAxisPanel: Function triggered by button_move_plus[axis] that moves
        the motor in the positive direction along the given axis
        """
        distance_in_mm = float(self.textctrl_move_relative_input.GetValue())
        distance_in_steps = int(distance_in_mm*MM_TO_STEP)
        self.drive_system.move_relative(axis,distance_in_steps)
        print_formatted_text('MOVING '+str(axis)+' '+str(distance_in_steps)+' steps')

    ################################################################################
    def button_func_move_minus(self,event,axis : int) -> None:
        """
        ControlViewAxisPanel: Function triggered by button_move_minus[axis] that moves
        the motor in the negative direction along the given axis
        """
        distance_in_mm = -1.0*float(self.textctrl_move_relative_input.GetValue())
        distance_in_steps = int(distance_in_mm*MM_TO_STEP)
        self.drive_system.move_relative(axis,distance_in_steps)
        print_formatted_text('MOVING '+str(axis)+' '+str(distance_in_steps)+' steps')
    
    ################################################################################
    def button_func_abort(self,event, axis : int) -> None:
        """
        ControlViewAxisPanel: Function triggered by buttonlist_abort that aborts one motor
        axis
        """
        self.drive_system.abort_axis(axis)
        return

    ################################################################################
    def button_func_reset(self,event,axis) -> None:
        """
        ControlViewAxisPanel: Function triggered by button_reset that resets one motor 
        axis
        """
        self.drive_system.reset_axis(axis)
        return

    ################################################################################
    def panel_is_paused(self) -> None:
        self.pause_panel.IsShown()
        return

    ################################################################################
    def show_pause_panel(self) -> None:
        self.pause_panel.Show()
        return

    ################################################################################
    def hide_pause_panel(self) -> None:
        self.pause_panel.Hide()
        return




################################################################################
################################################################################
################################################################################
class ControlView(wx.Panel):
    """
    Class that displays the upper part of the GUI with the buttons.
    """
    ################################################################################
    def __init__(self,parent,drive_system_gui):
        """
        ControlView: This initialises the ControlView class and all the buttons
        that are contained within it

        Parameters
        ----------
        parent : wx.SplitterWindow
            This is the wx.SplitterWindow defined by the DriveSystemGUI
        drive_system_gui : DriveSystemGUI
            This is the DriveSystemGUI main frame
        """
        # Get the instance of the serial interface so that commands can be sent via the buttons
        self.drive_system = DriveSystem.get_instance()

        # Get the instance of the GUI so that commands can be sent to it from buttons defined in the ControlView panel
        self.drive_system_gui = drive_system_gui

        # Call parent constructor and set options
        wx.Panel.__init__(self, parent, size=(drive_system_gui_width, controlview_height), pos=(0,0))
        self.SetBackgroundColour(drivesystem_window_background_colour())

        # Initialise UI
        self.init_ui()


    ################################################################################
    def init_ui(self):
        """
        ControlView: Initialises the UI for the ControlView - creates buttons,
        entry fields etc.
        """
        # Create the buttons at the top
        self.InitSendCommandUI()

        # Create the datum and move relative buttons
        self.InitDatumAndMoveRelativeUI()

        # Create the buttons on the side that control the GUI
        self.InitControlViewGUIButtons()


    ################################################################################
    def InitSendCommandUI(self):
        """
        ControlView: This function creates the button and fields for the buttons at
        the top of the ControlView panel
        """
        # PANEL
        self.send_command_panel = wx.Panel( self, id=wx.ID_ANY,
                                           size = (controlview_send_command_panel_width,controlview_send_command_panel_height),
                                           pos = (controlview_send_command_panel_X,controlview_send_command_panel_Y),
                                           name="send_command_panel" )
        self.send_command_panel.SetBackgroundColour(controlview_send_command_panel_colour)

        # SEND COMMANDS
        # ... Label
        self.text_send_command = wx.StaticText(self.send_command_panel, wx.ID_ANY, "Send any command:", (controlview_margin,controlview_margin), style=wx.ALIGN_LEFT)

        # ... Text box
        self.textctrl_command_input = wx.TextCtrl(self.send_command_panel, wx.ID_ANY, "", (controlview_margin,controlview_button_offset_Y), size=(controlview_text_box_width, controlview_null_height))
        self.textctrl_command_input.SetHint("Write any command...")

        # ... Button
        self.button_send_command = wx.Button(self.send_command_panel, wx.ID_ANY, "Send", ( controlview_send_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height ) )
        self.button_send_command.Bind(wx.EVT_BUTTON, self.button_func_send_command)
        self.button_send_command.SetToolTip("Send the command in the box to the left to the motor control box")
        self.button_send_command.SetDefault() # Set this as the default button for the window

        # CURRENT AXIS
        # ... Labels
        self.text_current_axis = wx.StaticText(self.send_command_panel, wx.ID_ANY, "Axis:", (controlview_axis_text_offset_X, controlview_margin),style=wx.ALIGN_LEFT)
        self.text_response = wx.StaticText(self.send_command_panel, wx.ID_ANY, "Response:", (controlview_response_text_offset_X, controlview_margin),style=wx.ALIGN_LEFT)

        # ... Text boxes
        self.textctrl_current_axis = wx.TextCtrl(self.send_command_panel, wx.ID_ANY, "", (controlview_axis_text_offset_X,controlview_button_offset_Y),size=(controlview_axis_text_box_width, controlview_null_height), style=wx.ALIGN_LEFT|wx.TE_READONLY)
        self.textctrl_command_response = wx.TextCtrl(self.send_command_panel, wx.ID_ANY, "", (controlview_response_text_offset_X,controlview_button_offset_Y),size=(controlview_text_box_width, controlview_null_height), style=wx.ALIGN_LEFT|wx.TE_READONLY)

        # BUTTONS
        # ... Abort All
        self.button_abort_all = wx.Button(self.send_command_panel, wx.ID_ANY, "ABORT ALL", (controlview_abort_all_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.button_abort_all.SetBackgroundColour(controlview_abort_all_button_colour)
        self.button_abort_all.Bind(wx.EVT_BUTTON, self.button_func_abort_all)
        self.button_abort_all.SetToolTip("Aborts all the motors. Do this in emergencies and before collecting data!")

        # ... Reset all
        self.button_reset_all = wx.Button(self.send_command_panel, wx.ID_ANY, "RESET ALL", (controlview_reset_all_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.button_reset_all.SetBackgroundColour(controlview_reset_all_button_colour)
        self.button_reset_all.Bind(wx.EVT_BUTTON, self.button_func_reset_all)
        self.button_reset_all.SetToolTip("Resets all the motors. Tread carefully!")

        # ... Print encoder positions
        self.button_print_positions = wx.Button(self.send_command_panel, wx.ID_ANY, "Print Pos.", (controlview_print_positions_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.button_print_positions.Bind(wx.EVT_BUTTON, self.button_func_print_positions)
        self.button_print_positions.SetToolTip("Prints all the positions to the console, one axis per line")

        # ... Change in-beam elements
        self.button_in_beam_element_change = wx.Button(self.send_command_panel, wx.ID_ANY, "IN-BEAM", (controlview_in_beam_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.button_in_beam_element_change.SetBackgroundColour(controlview_in_beam_button_colour)
        self.button_in_beam_element_change.Bind(wx.EVT_BUTTON, self.button_func_in_beam_element_change )
        self.button_in_beam_element_change.SetToolTip("Access the in-beam elements menu to move these into position!")

        # ... Slit scan
        self.button_slit_scan = wx.Button( self.send_command_panel, wx.ID_ANY, "SLIT SCAN", (controlview_slit_scan_button_offset_X, controlview_button_offset_Y), size=(controlview_button_width, controlview_null_height))
        self.button_slit_scan.SetBackgroundColour(controlview_slit_scan_button_colour)
        self.button_slit_scan.Bind(wx.EVT_BUTTON, self.button_func_slit_scan )
        self.button_slit_scan.SetToolTip("Scan the slits horizontally or vertically. Please don't try to do anything else while this is going on...")

    ################################################################################
    def InitDatumAndMoveRelativeUI(self):
        """
        ControlView: This creates the datum and move-relative buttons 
        """
        # Create panel
        self.datum_and_move_relative_panel = wx.Panel( self, wx.ID_ANY,
                                                       size = (controlview_datum_and_move_relative_panel_width,controlview_datum_and_move_relative_panel_height),
                                                       pos = (controlview_datum_and_move_relative_panel_X,controlview_datum_and_move_relative_panel_Y),
                                                       name="datum_and_move_relative_panel")
        self.datum_and_move_relative_panel.SetBackgroundColour(controlview_datum_and_move_relative_panel_colour)

        # Encoder movement button dimensions

        # # Create empty lists
        self.controlviewaxispanellist = []
        self.linelist_dividers = []


        # Loop over the number of axes
        for i in range(NUMBER_OF_MOTOR_AXES):
            self.controlviewaxispanellist.append( ControlViewAxisPanel( self.datum_and_move_relative_panel, i+1, 
                                                                        pos=(i*(controlview_axispanel_width + controlview_margin),0),
                                                                        size=(controlview_axispanel_width,controlview_axispanel_height)))
            # Line dividers
            if i != 0:
                self.linelist_dividers.append( wx.Panel(self.datum_and_move_relative_panel, wx.ID_ANY,
                                                        pos=( int( i*( controlview_axispanel_width + controlview_margin) - controlview_margin/2 - 0.5 ),0),
                                                        size=(1,controlview_datum_and_move_relative_panel_height)))
                self.linelist_dividers[-1].SetBackgroundColour(controlview_divider_colour)

            

    ################################################################################
    def InitControlViewGUIButtons(self):
        """
        ControlView: This creates the four buttons down the side of the right hand
        side of the ControlView panel
        """
        # Create panel
        self.gui_buttons_panel = wx.Panel( self, wx.ID_ANY,
                                           pos=(controlview_gui_buttons_panel_X, controlview_gui_buttons_panel_Y),
                                           size = (controlview_gui_buttons_panel_width, controlview_gui_buttons_panel_height),
                                           name="gui_buttons_panel" )
        self.gui_buttons_panel.SetBackgroundColour(controlview_gui_buttons_panel_colour)

        # Connect button
        self.button_connect = wx.Button(self.gui_buttons_panel, wx.ID_ANY, "CONNECT",
                                        pos=(0,0),
                                        size=(controlview_gui_button_width,controlview_gui_button_height))
        self.button_connect.Bind(wx.EVT_BUTTON, self.button_func_connect)
        self.button_connect.SetToolTip("Connect to the serial port")

        # Disconnect button
        self.button_disconnect = wx.Button(self.gui_buttons_panel, wx.ID_ANY, "DISCONNECT", 
                                           pos=(0, 1*( controlview_gui_button_height + controlview_margin )),
                                           size=(controlview_gui_button_width,controlview_gui_button_height))
        self.button_disconnect.Bind(wx.EVT_BUTTON, self.button_func_disconnect)
        self.button_disconnect.SetToolTip("Disconnect from the serial port")
        
        # Help button
        self.button_help = wx.Button(self.gui_buttons_panel, wx.ID_ANY, "HELP", 
                                     pos=(0,2*( controlview_gui_button_height + controlview_margin )),
                                     size=(controlview_gui_button_width,controlview_gui_button_height))
        self.button_help.Bind(wx.EVT_BUTTON, self.button_func_open_help_window)
        self.button_help.SetToolTip("Press this if you need help!")

        # Quit button
        self.button_quit = wx.Button(self.gui_buttons_panel, wx.ID_ANY, "QUIT", 
                                     pos=(0,3*( controlview_gui_button_height + controlview_margin )),
                                     size=(controlview_gui_button_width,controlview_gui_button_height))
        self.button_quit.Bind(wx.EVT_BUTTON, self.button_func_quit)
        self.button_quit.SetBackgroundColour(controlview_quit_button_colour)
        self.button_quit.SetToolTip("Quit the program and close the window")

        # Change the colour of the connect and disconnect buttons based on the current connection status
        if self.drive_system.check_connection() == True:
            self.button_disconnect.SetBackgroundColour(controlview_disconnect_button_connected_colour)
            self.button_connect.Enable(False)
        else:
            self.button_connect.SetBackgroundColour(controlview_connect_button_disconnected_colour)
            self.button_disconnect.Enable(False)

    ################################################################################
    def change_connect_disconnect_button_colours(self,value):
        """
        ControlView: Changes the colour of the connect/disconnect button
        """
        # Get value of event
        # value = event.GetValue()

        # We are connected
        if value == 1:
            self.button_disconnect.SetBackgroundColour(controlview_disconnect_button_connected_colour)
            self.button_disconnect.Enable(True)
            self.button_connect.SetBackgroundColour(controlview_connect_grey)
            self.button_connect.Enable(False)
        # We are not connected
        else:
            self.button_connect.SetBackgroundColour(controlview_connect_button_disconnected_colour)
            self.button_connect.Enable(True)
            self.button_disconnect.SetBackgroundColour(controlview_connect_grey)
            self.button_disconnect.Enable(False)

    ################################################################################
    def button_func_print_positions(self,event):
        """
        ControlView: Function triggered by button_print_positions being pressed, 
        that prints the positions to the console
        """
        pos = self.drive_system.get_positions()
        for i in range(0,NUMBER_OF_MOTOR_AXES):
            print_formatted_text( f"Axis {i+1}: {pos[i]}" )

    ################################################################################
    def button_func_send_command(self,event):
        """
        ControlView: Function triggered by button_send_command to send command to 
        the DriveSystem serial interface object
        """
        # Construct command
        command = self.drive_system.construct_command_from_str( self.textctrl_command_input.GetValue() )
        
        if self.drive_system.check_if_valid_command(command) == False:
            return
        
        print_formatted_text("SENDING COMMAND: " + repr(command))

        # Send command and get axis + answer from response
        axis,answer=self.drive_system.execute_command(command,True,True)

        # Update textctrl object with response (if any)
        if axis != None:
            self.textctrl_current_axis.SetValue(axis)
            self.textctrl_current_axis.Update()
        if answer != None:
            self.textctrl_command_response.SetValue(answer)
            self.textctrl_command_response.Update()
        else:
            self.textctrl_command_response.SetValue("NO RESPONSE")
            self.textctrl_command_response.Update()
        
        # Refresh GUI
        self.refresh()

    ################################################################################
    def button_func_connect(self,event):
        """
        ControlView: Function triggered by button_connect to connect to the serial
        port to communicate with the motor box
        """
        # Cannot mirror disconnect function as the thread stops when the serial port is disconnected...
        self.drive_system.connect_to_port()
        self.change_connect_disconnect_button_colours(1)

    ################################################################################
    def button_func_disconnect(self,event):
        """
        ControlView: Function triggered by button_disconnect to connect to the 
        serial port to communicate with the motor box
        """
        self.drive_system.disconnect_port()
        self.change_connect_disconnect_button_colours(0)

    ################################################################################
    def button_func_quit(self,event):
        """
        ControlView: Function triggered by button_quit to quit the GUI
        """
        self.drive_system_gui.close_program(event)

    ################################################################################
    def button_func_in_beam_element_change(self,event):
        """
        ControlView: Function triggered by button_in_beam_element_change to change
        the elements that are placed in the path of the beam
        """
        if drivesysteminbeamelementselector.InBeamElementSelectionWindow.is_drawn() == False:
            drivesysteminbeamelementselector.InBeamElementSelectionWindow()

    ################################################################################
    def button_func_open_help_window(self,event):
        """
        ControlView: Function triggered by button_help that opens the help window
        for the GUI
        """
        if HelpWindow.is_drawn() == False:
            HelpWindow(self, "Help")

    ################################################################################
    def button_func_abort_all(self,event):
        """
        ControlView: Function triggered by button_abort_all that aborts all the
        motor axes
        """
        self.drive_system.abort_all()

    ################################################################################
    def button_func_reset_all(self,event):
        """
        ControlView: Function triggered by button_reset_all that resets all the
        motor axes
        """
        self.drive_system.reset_all()

    ################################################################################
    def button_func_slit_scan(self,event):
        """
        ControlView: Function triggered by button_scan_slit that...TODO
        """
        menu = wx.Menu()
        horz_scan = menu.Append(wx.ID_ANY, "Horizontal scan (using vertical slit)")
        vert_scan = menu.Append(wx.ID_ANY, "Vertical scan (using horizontal slit)")
        
        self.Bind(wx.EVT_MENU, lambda evt: self.start_slit_scan(True), horz_scan)
        self.Bind(wx.EVT_MENU, lambda evt: self.start_slit_scan(False), vert_scan)

        self.PopupMenu(menu)
        menu.Destroy()
        return
    
    ################################################################################
    def start_slit_scan(self, is_horz_scan : bool = True ):
        t = threading.Thread( target=self.drive_system.slit_scan_launch_threads, args=(is_horz_scan,) )
        t.start()
        return

    ################################################################################
    def refresh(self):
        """
        ControlView: Refreshes ControlView UI elements that should be updated
        automatically. Uses wx.CallAfter to push UI updates to the main thread.
        """
        wx.CallAfter( self.textctrl_command_response.Refresh )
        wx.CallAfter( self.textctrl_current_axis.Refresh )
    
    ################################################################################
    ################################################################################
    def show_or_hide_pause_panel(self, value):
        # value = event.GetValue()
        axis = value[0]
        is_paused = value[1]

        # Get the right object
        panel : ControlViewAxisPanel = self.controlviewaxispanellist[axis-1]

        if is_paused:
            panel.show_pause_panel()
        else:
            panel.hide_pause_panel()
        wx.CallAfter( self.Refresh )
        wx.CallAfter( self.Update )

################################################################################
################################################################################
################################################################################
class DriveSystemGUI(wx.Frame):
    """
    This is the main class for the whole GUI. It is the main window which contains everything else. At a surface level, it contains:
      - ControlView - this is the top panel in the GUI with all the buttons
      - PosVisPanel - this helps visualise the elements from the side, but also along the beam axis.
      - DriveSystemthread - this controls the starting of the thread.
    """
    ################################################################################
    def __init__(self, parent, mytitle):
        """
        DriveSystemGUI: This initialises the instance of the GUI.
        """
        # Call parent constructor and set options
        super(DriveSystemGUI, self).__init__( parent, title=mytitle, size=(drive_system_gui_width,drive_system_gui_height), style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX) )

        # Bind close button to destructor function
        self.Bind( wx.EVT_CLOSE, self.close_program )

        # Initialise UI
        self.init_ui()

        # Place self at centre of the display
        self.Centre()

        # Raise it to the top of the windows
        self.Raise()

        # Create a thread to keep the GUI running
        self._drivesystem = DriveSystem.get_instance()
        self.gui_refresh_timer = threading.Event()
        self.is_gui_running = True
        self.UPDATE_TIME = 0.5
        self.thread = threading.Thread( target=self.refresh_gui_thread )
        self.thread.start()

    ################################################################################
    def init_ui(self):
        """
        DriveSystemGUI: Initialises the UI by splitting the window, and creating the 
        PosVisPanel and the ControlView panel.
        """
        self.split_win = wx.SplitterWindow(self)
        self.posvispanel = PosVisPanel(self.split_win)
        self.controlview = ControlView(self.split_win, self)
        self.split_win.SplitHorizontally(self.controlview, self.posvispanel, controlview_height)
        self.split_win.SetSashInvisible()

    ################################################################################
    def close_program(self, event):
        """
        DriveSystemGUI: This closes the GUI and kills the background thread
        """
        print_formatted_text("Exiting GUI...")

        # Tell thread to stop doing things to the GUI
        self.is_gui_running = False
        
        # Close all top level windows
        for item in wx.GetTopLevelWindows():
            if not isinstance(item, DriveSystemGUI):
                item.Destroy()

        # Self-destruct!
        self.Destroy()

    ################################################################################
    def update_positions(self, pos : list):
        # CallAfter forces the main thread to do this!
        wx.CallAfter( self.posvispanel.update_positions, pos )

    ################################################################################
    def update_paused_axis( self, axis : int, is_paused : bool):
        wx.CallAfter( self.show_or_hide_pause_panel, args=(axis, is_paused) )

    ################################################################################
    def refresh_gui_thread(self):
        while self.is_gui_running:
            t = time.time()
            pos = self._drivesystem.get_positions()
            wx.CallAfter( self.update_positions, pos )
            time_elapsed = time.time() - t
            self.gui_refresh_timer.wait( np.max([self.UPDATE_TIME - time_elapsed, 0 ]) )




################################################################################
################################################################################
################################################################################
class HelpWindow(wx.Frame):
    """
    This is the help window that guides the user through the main features of the GUI.
    """
    instance = None # This is the single instance
    init = False    # This determines whether the panel has already been initialised

    ################################################################################
    def __new__(self, *args, **kwargs):
        """
        HelpWindow: Treat as a singleton so multiple instances are not created
        """
        if self.instance is None:
            self.instance = super().__new__(self)
        return self.instance

    ################################################################################
    def __init__(self, parent, mytitle):
        """
        HelpWindow: Initialise the help window
        """
        # Do nothing if already initialised
        if self.init:
            self.Raise() # Moves already initialised window to the top
            return
        
        # First initialisation -> tell code that this is true
        self.init = True

        # Define the width and height of the window
        self.width = 430
        self.height = 500

        # Call the parent constructor with the width and height
        super().__init__(parent, title=mytitle,size=(self.width,self.height))

        # Tell it how to close
        self.Bind( wx.EVT_CLOSE, self.on_close)

        # Initialise the UI
        self.init_ui()

        # Centre the window and show it
        self.Centre()
        self.Show()

    ################################################################################
    def init_ui(self):
        """
        HelpWindow: Initialise all the UI features in the window
        """
        # Create a ScrolledPanel object
        self.panel = wx.lib.scrolledpanel.ScrolledPanel( self, wx.ID_ANY, size=(self.width,self.height ) )
        self.panel.SetupScrolling()
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(vbox)

        # Define lines to be printed in the HelpWindow
        lines = [
            "See https://twiki.cern.ch/twiki/bin/view/ISS/DriveSystem for more information.\n\n"
            "This is a GUI for controlling the ISS Drive System.\n",
            f"The Drive System contains {NUMBER_OF_MOTOR_AXES} axes:",
        ]
        for i in range(0,NUMBER_OF_MOTOR_AXES):
            lines.append( f"  • Axis {i+1}: {AXIS_LABELS[i]}" )
        
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

        # Join the lines together
        text = "\n".join(lines)
        desc = wx.StaticText(self.panel, wx.ID_ANY, text)
        desc.Wrap(self.width - 50)
        vbox.Add(desc, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL )

    ################################################################################
    def on_close(self, e):
        """
        HelpWindow: Closes the window
        """
        self.init = False
        self.Destroy()

    ################################################################################
    @classmethod
    def get_instance(cls):
        """
        HelpWindow: returns the single instance of the class
        """
        if cls.instance == None:
            cls()
        return cls.instance

    ################################################################################
    @classmethod
    def is_drawn(cls):
        """
        HelpWindow: determine if the HelpWindow has been drawn or not
        """
        return cls.init

