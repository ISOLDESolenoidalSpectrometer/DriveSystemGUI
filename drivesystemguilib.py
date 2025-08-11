"""
Drive System GUI Library
====================

This contains all the constants and useful functions for defining the GUI

"""
from drivesystemlib import *
import drivesystemoptions as dsopts
import matplotlib.pyplot as plt
import matplotlib.patches

# CONSTANTS
# Physical distances that will not change
ARRAY_SILICON_TO_TIP_DISTANCE = 18.5 # [mm]
ARRAY_SUPPORT_TO_END_OF_SILICON = 626.1 - ARRAY_SILICON_TO_TIP_DISTANCE # See elog:6071 for length of array
MAGNET_LENGTH = 2732 # Magnet length [mm]

################################################################################
################################################################################
################################################################################
class MotorAxisInfo:
    """
    Class to hold information about a motor axis. POD class
    """
    ################################################################################
    def __init__(self, description : str, width : float, height : float, colour : str, axis_number : int):
        """
        MotorAxisInfo: contains information about the motor axes for the GUI
        """
        self.description = description
        self.width = width
        self.height = height
        self.colour = colour
        self.axis_number = axis_number
        return

################################################################################
# AXIS DEFINITIONS
# () = abbreviation used throughout, [] = Patrick's tape colour
# axis 1: Target carriage                   (TC)   [red]
# axis 2: Array                             (Arr)  [green]
# axis 3: Target ladder, horizontal         (TLH)  [yellow]
# axis 4: Faraday cup/Zero degree detectors (Det)  [black]
# axis 5: Target ladder, vertical           (TLV)  [brown]
# axis 6: Beam blocker, horizontal          (BBH)  [grey]
# axis 7: Beam blocker, vertical            (BBV)  [white]
AXIS_LABELS = ['Target carriage', 
               'Array', 
               'Target ladder (H)', 
               'FC/ZD',
               'Target ladder (V)',
               'Beam blocker (V)',
               'Beam blocker (H)'
               ]

# DICTIONARY/GUI DEFINITIONS
#   'key':               'descript.',                                Width  Height Colour     axis
MOTOR_AXIS_DICT = {
    'SiA': MotorAxisInfo( 'Si array', ARRAY_SUPPORT_TO_END_OF_SILICON,  35.0, '#FD3F0D', 0 ), # The width was changed from 610.0 after elog:6071
    'TaC': MotorAxisInfo( 'Target carriage',                           450.0, 270.0, '#0DE30B', 1 ), # PlotView
    'ArC': MotorAxisInfo( 'Array bed',                                 350.0, 195.0, '#FDD11F', 2 ), # PlotView
    'TLH': MotorAxisInfo( 'Targ ladder H',                              80.0, 130.0, '#00A7FA', 3 ), # PlotView
    'Det': MotorAxisInfo( 'Diagnostic Detectors',                       80.0, 130.0, '#910BE3', 4 ), # PlotView
    'TLV': MotorAxisInfo( 'Target ladder V',                           308.5, 194.0, '#00A7FA', 5 ), # BeamView
    'BBV': MotorAxisInfo( 'Beam blocker V',                            173.0, 118.0, '#910BE3', 6 ),  # BeamView
    'BBH': MotorAxisInfo( 'Beam blocker H',                             80.0, 130.0, '#910BE3', 7 ) # PlotView
}

# Wrapped in a function to make dark mode work!
def drivesystem_window_background_colour():
    if dsopts.CMD_LINE_ARG_DARK_MODE.get_value():
        return '#333333'
    return '#FFFFE0'


# WINDOW DEFINITIONS
# Panel sizes: controlView split horizontally, beamView vertically
controlview_height = 210
driveview_width = 1000
posvispanel_height = 580
posvispanel_footer_height = 50
beamview_width = posvispanel_height - posvispanel_footer_height

# Frame (window) size
drive_system_gui_height = posvispanel_height + controlview_height
drive_system_gui_width = driveview_width + beamview_width

# PlotView parameters
plot_view_dpi = 100
beamview_width_inches = (beamview_width - 1)/plot_view_dpi
beamview_height_inches = (posvispanel_height-posvispanel_footer_height)/plot_view_dpi
driveview_width_inches = (driveview_width-1)/plot_view_dpi
driveview_height_inches = beamview_height_inches
plot_view_position_label_offset = 20

# EDGES/SPACINGS/MISC
recoil_target_dist = 246.2 # This should be fixed...

 # Assuming that target at encoder position 0 is 1234.0 mm from back of magnet (elog:2891)
driveview_distance_from_trolley_axis_to_target_ladder = 20
driveview_distance_from_trolley_axis_to_beam_monitoring_axis = 20
beam_blocker_soft_limit = (MAGNET_LENGTH/2) - 1234.0 - dsopts.OPTION_BEAM_BLOCKER_TO_TROLLEY_AXIS_SOFT_LIMIT.get_value()/MM_TO_STEP + MOTOR_AXIS_DICT['TaC'].width - driveview_distance_from_trolley_axis_to_target_ladder

# Colours
arrayEdgeCol  = MOTOR_AXIS_DICT['Det'].colour
silencerC     = arrayEdgeCol
recoilFCCol   = '#B2B1BA'
recoilECol    = '#15B01A'
blockerFCol   = '#B2B1BA'
blockerECol   = '#000000'


# CONTROL VIEW
# Colours
controlview_abort_all_button_colour =  "#FD3F0D"
controlview_reset_all_button_colour =  "#000000"
controlview_in_beam_button_colour =    "#AA44DD"
controlview_slit_scan_button_colour =  "#00AA00"
controlview_quit_button_colour =       "#FD3F0D"
controlview_connect_button_disconnected_colour =    "#7FFF00"
controlview_disconnect_button_connected_colour =    controlview_quit_button_colour
controlview_connect_grey = "#666666"
controlview_divider_colour = "#000000"
controlview_send_command_panel_colour = drivesystem_window_background_colour()
controlview_datum_and_move_relative_panel_colour = drivesystem_window_background_colour()
controlview_gui_buttons_panel_colour = drivesystem_window_background_colour()

# sizes
# General widths and heights
controlview_axis_text_box_width = 60
controlview_text_box_width = 300
controlview_button_width = 110
controlview_button_height = 29
controlview_gui_button_width = controlview_button_width
controlview_gui_button_height = 40
controlview_margin = 5

# Panel widths
controlview_gui_buttons_panel_width = controlview_button_width
controlview_gui_buttons_panel_height = controlview_height
controlview_send_command_panel_width = drive_system_gui_width - controlview_gui_buttons_panel_width - controlview_margin
controlview_send_command_panel_height = 60
controlview_datum_and_move_relative_panel_width = controlview_send_command_panel_width
controlview_datum_and_move_relative_panel_height = controlview_height - controlview_send_command_panel_height - controlview_margin

# Panel X's and Y's
controlview_gui_buttons_panel_X = controlview_send_command_panel_width + controlview_margin
controlview_gui_buttons_panel_Y = 0
controlview_datum_and_move_relative_panel_X = 0
controlview_datum_and_move_relative_panel_Y = controlview_send_command_panel_height + controlview_margin
controlview_send_command_panel_X = 0
controlview_send_command_panel_Y = 0

# Send command panel offsets
controlview_button_offset_Y = 25
controlview_axispanel_offset_Y = controlview_button_offset_Y + controlview_button_height + 1
controlview_send_button_offset_X = controlview_margin*2 + controlview_text_box_width
controlview_abort_all_button_offset_X = controlview_send_button_offset_X + controlview_button_width + controlview_margin
controlview_reset_all_button_offset_X = controlview_abort_all_button_offset_X + controlview_button_width + controlview_margin
controlview_axis_text_offset_X = controlview_reset_all_button_offset_X + controlview_button_width + controlview_margin
controlview_response_text_offset_X = controlview_axis_text_offset_X + controlview_axis_text_box_width + controlview_margin
controlview_print_positions_button_offset_X = controlview_response_text_offset_X + controlview_text_box_width + controlview_margin
controlview_in_beam_button_offset_X = controlview_print_positions_button_offset_X + controlview_button_width + controlview_margin
controlview_slit_scan_button_offset_X = controlview_in_beam_button_offset_X + controlview_button_width + controlview_margin
controlview_null_height = -1

# CONTROLVIEWAXISPANEL
# Widths
controlview_axispanel_width  =  int( np.floor( ( controlview_datum_and_move_relative_panel_width - (NUMBER_OF_MOTOR_AXES - 1)*controlview_margin )/NUMBER_OF_MOTOR_AXES ) )
controlview_axispanel_height = controlview_datum_and_move_relative_panel_height

# POSVISPANEL
# Turn on/off certain elements
pvp_draw_si_recoil_dets = False
pvp_draw_beam_blocker = True

# INBEAMELEMENT PANEL
inbeamelement_target_radius = 4 # mm
inbeamelement_slit_width = 1 # mm
inbeamelement_slit_height = 12 # mm
inbeamelement_smallaperture_radius = 1.5 # mm
inbeamelement_largeaperture_radius = 1.5 # mm
inbeamelement_alpha_radius = 11.5
inbeamelement_tritiumtarget_width = 10.5 # mm
inbeamelement_tritiumtarget_height = 15 # mm

inbeamelement_target_colour = '#CCCCCC'
inbeamelement_horzslit_colour = '#CCCCCC'
inbeamelement_vertslit_colour = '#CCCCCC'
inbeamelement_smallaperture_colour = '#CCCCCC'
inbeamelement_largeaperture_colour = '#CCCCCC'
inbeamelement_alpha_colour = '#FFFFFF'
inbeamelement_tritiumtarget_colour = '#CCCCCC'

inbeamelement_axislimit = 6.5
inbeamelement_beamspot_colour = '#FF0000'
# inbeamelement_
# inbeamelement_
# inbeamelement_




################################################################################
################################################################################
################################################################################
class ArrowAnnotation():
    """
    These are the double-tipped arrows drawn on the PlotView surfaces to 
    indicate distances between two elements
    """
    ################################################################################
    MIN_DISTANCE = 65
    ARROWHEADLENGTH = 4 # pt
    ARROWHEADWIDTH = 2 # pt
    def __init__( self, x1 : int, x2 : int, y : int, label : str, label_offset : int ) -> None:
        """
        ArrowAnnotation: initialise the class
        """
        self.x1 = x1
        self.x2 = x2
        self.y = y
        self.label = label
        self.label_offset = label_offset
        self.enabled = True
        self.left_arrow = None
        self.right_arrow = None
        self.double_arrow = None
        self.text = None
        self.arrow_head_offset = None
        return

    ################################################################################
    def update( self, x1 : int, x2 : int ) -> None:
        """
        ArrowAnnotation: update the internal numbers
        """
        self.x1 = x1
        self.x2 = x2
        return

    ################################################################################
    def enable(self) -> None:
        """
        ArrowAnnotation: enable the drawing of the arrow
        """
        self.enabled = True
        return

    ################################################################################
    def disable(self) -> None:
        """
        ArrowAnnotation: disable the drawing of the arrow
        """
        self.enabled = False
        return

    ################################################################################
    def draw(self, ax : plt.Axes ) -> None:
        """
        ArrowAnnotation: generic draw function
        """
        if self.enabled:
            if self.arrow_head_offset == None:
                self.arrow_head_offset = self.points_to_data(ax,self.ARROWHEADLENGTH - 1) # THIS HAS BEEN FUDGED

            # Initialise if not created
            if self.left_arrow == None:
                self.left_arrow = matplotlib.patches.FancyArrowPatch( (self.x1, self.y), ( (self.x2 - self.x1)/2.0, self.y), arrowstyle=f'<|-, head_length={self.ARROWHEADLENGTH}, head_width={self.ARROWHEADWIDTH}', facecolor='black')
                self.left_arrow.set_visible(False)
                ax.add_patch(self.left_arrow)
            if self.right_arrow == None:
                self.right_arrow = matplotlib.patches.FancyArrowPatch( (self.x1, self.y), ( (self.x2 - self.x1)/2.0, self.y), arrowstyle=f'-|>, head_length={self.ARROWHEADLENGTH}, head_width={self.ARROWHEADWIDTH}', facecolor='black')
                self.right_arrow.set_visible(False)
                ax.add_patch(self.right_arrow)
            if self.double_arrow == None:
                self.double_arrow = matplotlib.patches.FancyArrowPatch( (self.x1 - self.arrow_head_offset, self.y), ( self.x2 + self.arrow_head_offset, self.y), arrowstyle='<|-|>, head_length=4, head_width=2', facecolor='black')
                self.double_arrow.set_visible(False)
                ax.add_patch(self.double_arrow)
            
            # Now work out which ones to draw
            if (self.x2 - self.x1) < self.MIN_DISTANCE:
                # Draw left and right arrows
                self.left_arrow.set_visible(True)
                self.right_arrow.set_visible(True)
                self.double_arrow.set_visible(False)
                self.left_arrow.set_positions( (self.x2 - self.arrow_head_offset, self.y), (self.x2 + 50, self.y))
                self.right_arrow.set_positions( (self.x1 - 50, self.y), (self.x1 + self.arrow_head_offset, self.y))
            else:
                self.left_arrow.set_visible(False)
                self.right_arrow.set_visible(False)
                self.double_arrow.set_visible(True)
                self.double_arrow.set_positions( (self.x1 - self.arrow_head_offset, self.y), (self.x2 + self.arrow_head_offset, self.y))
                
            # Update text
            text = f"{self.label}: {self.x2 - self.x1:.3f} mm"
            
            # Draw if not initialised
            if self.text == None:
                self.text = ax.text( self.x1 + (self.x2 - self.x1)*0.5 - MM_TO_STEP, self.label_offset + self.y, text )
            
            # Update if initialised
            else:
                self.text.set_text(text)
                self.text.set_x(self.x1 + (self.x2 - self.x1)*0.5 - MM_TO_STEP)
                self.text.set_y( self.label_offset + self.y)

        return
    
    @staticmethod
    def points_to_data( ax : plt.Axes, length_pts : float ):
        POINTS_PER_INCH = 72 # pt/in

        # Convert distance to inches
        length_in = length_pts/POINTS_PER_INCH

        # Get width of figure in data points
        width_in_data_points = ( ax.get_xlim()[1] - ax.get_xlim()[0] )/ax.get_position().width

        # Get figure size in inches
        fig_width_inches = ax.get_figure().get_size_inches()[0]

        # Now convert length to data points
        return width_in_data_points*( length_in/fig_width_inches )


################################################################################
################################################################################
################################################################################
class PositionText():
    """
    This is the text used to indicate where the element is in the magnet in mm
    for a numbered axis
    """
    ################################################################################
    def __init__(self, axis : tuple, x : int, y : int, position : float, colour : str ) -> None:
        """
        PositionText: initialise the object
        """
        self.axis = axis,
        self.x = x
        self.y = y
        self.position = position
        self.colour = colour
        self.text_object = None
        return
    
    ################################################################################
    def update(self, position : float) -> None:
        """
        PositionText: updates the internal position
        """
        self.position = position
        return

    ################################################################################
    def generate_string(self) -> str:
        """
        PositionText: generates the text to show on the thing
        """
        return f"Axis {self.axis[0]}: {self.position:.3f} mm"

    ################################################################################
    def draw(self, ax : plt.Axes ) -> None:
        """
        PositionText: this draw command either initialises the object, or updates
        its text
        """
        if self.text_object == None:
            self.text_object = ax.text( self.x, self.y, self.generate_string(), color=self.colour, ha='left', va='top' )
        else:
            self.text_object.set_text( self.generate_string() )
        return
    



