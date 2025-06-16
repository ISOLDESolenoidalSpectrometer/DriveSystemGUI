"""
Drive System GUI Library
====================

This contains all the constants and useful functions for defining the GUI

"""
from drivesystemlib import *
import drivesystemoptions as dsopts
import matplotlib.pyplot as plt

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
               'Beam blocker (H)',
               'Beam blocker (V)']

# DICTIONARY/GUI DEFINITIONS
#   'key':               'descript.',                                Width  Height Colour     axis
MOTOR_AXIS_DICT = {
    'SiA': MotorAxisInfo( 'Si array', ARRAY_SUPPORT_TO_END_OF_SILICON,  35.0, '#FD3F0D', 0 ), # The width was changed from 610.0 after elog:6071
    'TaC': MotorAxisInfo( 'Target carriage',                           450.0, 270.0, '#0DE30B', 1 ),
    'ArC': MotorAxisInfo( 'Array bed',                                 350.0, 195.0, '#FDD11F', 2 ),
    'TLH': MotorAxisInfo( 'Targ ladder H',                              80.0, 130.0, '#00A7FA', 3 ),
    'Det': MotorAxisInfo( 'Diagnostic Detectors',                       80.0, 130.0, '#910BE3', 4 ),
    'TLV': MotorAxisInfo( 'Target ladder V',                           309.4, 217.0, '#00A7FA', 5 ),
    'BBH': MotorAxisInfo( 'Beam blocker H',                             80.0, 130.0, '#910BE3', 6 ),
    'BBV': MotorAxisInfo( 'Beam blocker V',                            169.5, 123.0, '#910BE3', 7 )
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
recoil_target_dist = 246.2
blockerpos         = (MAGNET_LENGTH/2)-47.0 - 6*60    # Distance of blocker from back of the magnet (From Mike Cordwell)

 # Assuming that target at encoder position 0 is 1234.0 mm from back of magnet (elog:2891)
blockerSoftLimit = (MAGNET_LENGTH/2) - 1234.0 + 72493.0/200.0 + MOTOR_AXIS_DICT['TaC'].width

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


################################################################################
################################################################################
################################################################################
class ArrowAnnotation():
    """
    These are the double-tipped arrows drawn on the PlotView surfaces to 
    indicate distances between two elements
    """
    ################################################################################
    def __init__( self, x1 : int, x2 : int, height : int, label : str, label_offset : int ) -> None:
        """
        ArrowAnnotation: initialise the class
        """
        self.x1 = x1
        self.x2 = x2
        self.height = height
        self.label = label
        self.label_offset = label_offset
        self.enabled = True
        self.mpl_annotation = None
        self.mpl_text = None
        return

    ################################################################################
    def update( self, x1 : int, x2 : int, height : int ) -> None:
        """
        ArrowAnnotation: update the internal numbers
        """
        self.x1 = x1
        self.x2 = x2
        self.height = height
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
            # Draw if not initialised
            if self.mpl_annotation == None:
                self.mpl_annotation = ax.annotate( '', (self.x1, self.height ), ( self.x2, self.height ), arrowprops={'arrowstyle':'<->'} )
            
            # Update if initialised
            else:
                self.mpl_annotation.xy = (self.x1, self.height)

            # Update text
            text = f"{self.label}: {self.x2 - self.x1:.3f} mm"
            
            # Draw if not initialised
            if self.mpl_text == None:
                self.mpl_text = ax.text( self.x1 + (self.x2 - self.x1)*0.5 - 200, self.label_offset + self.height, text )
            
            # Update if initialised
            else:
                self.mpl_text.set_text(text)
                self.mpl_text.set_x(self.x1 + (self.x2 - self.x1)*0.5 - 200)
                self.mpl_text.set_y( self.label_offset + self.height)

        return


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
    



