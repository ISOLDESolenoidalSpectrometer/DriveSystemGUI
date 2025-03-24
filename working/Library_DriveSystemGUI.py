from Library_DriveSystem import *
import matplotlib
from matplotlib import pyplot as plt

# WINDOW DEFINITIONS
# Panel sizes: controlView split horizontally, beamView vertically
controlViewSize = 200
beamViewSize    = 400

# Frame (window) size
frameH = 780
frameW = 1000+beamViewSize


# EDGES/SPACINGS/MISC
#
Arr_space    = axisdict['ArC'].width/2 # Space between trolley border and axis 3&4
arrayEdge_H        = axisdict['SiA'].height
arrayEdge_W        = 18.5             # Distance from end of array to edge of Si array
silencerW          = 109.1-32.6        # Total length minus depth in to array of 32.6 mm
targ_space   = 20
Det_space = 20
magL               = 2732             # Magnet length [mm]
recoil_target_dist = 246.2
blockerpos         = (magL/2)-47.0 - 6*60    # Distance of blocker from back of the magnet (From Mike Cordwell)

# FC, ZD and recoil detectors
# Radius
fcR     = 21
dER     = 20
recoilR = 50

# Blocker dimensions
blockerR     = 15
blockerPostW = 5
blockerPostH = 135

 # Assuming that target at encoder position 0 is 1234.0 mm from back of magnet (elog:2891)
blockerSoftLimit = (magL/2) - 1234.0 + 72493.0/200.0 + axisdict['TaC'].width

# encoder position of the center [mm]
dEH =  11672.0*step2mm   # just for the GUI
fcH = -12587.0*step2mm   # no need to change

# Colours
arrayEdgeCol  = axisdict['Det'].colour
silencerC     = arrayEdgeCol
recoilFCCol   = '#B2B1BA'
recoilECol    = '#15B01A'
blockerFCol   = '#B2B1BA'
blockerECol   = '#000000'
windowBackgroundCol = '#FFFFE0'


# CONTROL VIEW
# Colours
controlview_abort_all_button_colour =  "#FD3F0D"
controlview_in_beam_button_colour =    "#AA44DD"
controlview_quit_button_colour =       "#FD3F0D"
controlview_connect_button_disconnected_colour =    "#7FFF00"
controlview_disconnect_button_connected_colour =    controlview_quit_button_colour
control_view_connect_grey = "#666666"

# sizes
controlview_axis_text_box_width = 60
controlview_text_box_width = 200
controlview_button_width = 100

# 1D things
controlview_text_offset_Y = 5
controlview_button_spacing = 5
controlview_button_offset_Y = 25
controlview_send_button_offset_X = controlview_text_offset_Y*2 + controlview_text_box_width
controlview_abort_all_button_offset_X = controlview_send_button_offset_X + controlview_button_width + controlview_button_spacing
controlview_reset_all_button_offset_X = controlview_abort_all_button_offset_X + controlview_button_width + controlview_button_spacing
controlview_axis_text_offset_X = controlview_reset_all_button_offset_X + controlview_button_width + controlview_button_spacing
controlview_response_text_offset_X = controlview_axis_text_offset_X + controlview_axis_text_box_width + controlview_button_spacing
controlview_print_positions_button_offset_X = controlview_response_text_offset_X + controlview_text_box_width + controlview_button_spacing
controlview_in_beam_button_offset_X = controlview_print_positions_button_offset_X + controlview_button_width + controlview_button_spacing
controlview_null_height = -1

# POSVISPANEL
# Turn on/off certain elements
pvp_draw_si_recoil_dets = False
pvp_draw_beam_blocker = True


# Arrows drawn on DriveView panel
class ArrowAnnotation():
    def __init__( self, x1 : int, x2 : int, height : int, label : str, label_offset : int ):
        self.x1 = x1
        self.x2 = x2
        self.height = height
        self.label = label
        self.label_offset = label_offset
        self.enabled = True
        self.mpl_annotation = None
        self.mpl_text = None

    def update( self, x1 : int, x2 : int, height : int ):
        self.x1 = x1
        self.x2 = x2
        self.height = height

    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False

    def draw(self, ax ):
        if self.enabled:
            if self.mpl_annotation != None:
                self.mpl_annotation.remove()
            if self.mpl_text != None:
                self.mpl_text.remove()

            self.mpl_annotation = ax.annotate( '', (self.x1, self.height ), ( self.x2, self.height ), arrowprops={'arrowstyle':'<->'} )
            text = f"{self.label}: {self.x2 - self.x1:.3f} mm"
            self.mpl_text = ax.text( self.x1 + (self.x2 - self.x1)*0.5 - 200, self.label_offset + self.height, text )


class PositionText():
    def __init__(self, axis : tuple, x : int, y : int, position : float, colour : str ):
        self.axis = axis,
        self.x = x
        self.y = y
        self.position = position
        self.colour = colour
        self.text_object = None
    
    def update(self, position):
        self.position = position
        return

    def generate_string(self):
        return f"Position {self.axis[0]}: {self.position:.3f} mm"

    def draw(self, ax ):
        if self.text_object != None:
            self.text_object.remove()
        self.text_object = ax.text( self.x, self.y, self.generate_string(), color=self.colour )
        return







