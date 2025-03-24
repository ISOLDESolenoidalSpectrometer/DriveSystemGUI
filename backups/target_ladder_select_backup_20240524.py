import numpy as np
import wx
from id_map import *

import queue
from DriveSystem import *

#import Library_DriveSystem

# CONSTANTS ================================================================= #
TARGET_SIZE = 40    # Try to keep this even!
INNER_SPACING = 6  # Try to keep this even!
OUTER_SPACING = 10

# Label - ID list initialise
ID_MAP = IDMap("/home/isslocal/DriveSystemGUI/id_label_map.txt")

# Target ladder sizing
NUM_TARGETS_H = 4
NUM_TARGETS_V = 3
TARGET_FRAME_H_SIZE = NUM_TARGETS_H*TARGET_SIZE + ( NUM_TARGETS_H + 1 )*INNER_SPACING
TARGET_FRAME_V_SIZE = NUM_TARGETS_V*TARGET_SIZE + ( NUM_TARGETS_V + 1 )*INNER_SPACING

NUM_TARGET_FRAMES_H = 2
NUM_TARGET_FRAMES_V = 3
TARGET_TUNE_PLATE = (1,1)

TARGET_LADDER_H_SIZE = TARGET_FRAME_H_SIZE*NUM_TARGET_FRAMES_H + ( NUM_TARGET_FRAMES_H + 1 )*OUTER_SPACING
TARGET_LADDER_V_SIZE = TARGET_FRAME_V_SIZE*NUM_TARGET_FRAMES_V + ( NUM_TARGET_FRAMES_V + 1 )*OUTER_SPACING

NUM_TUNING_FRAME_ELEMENTS_H = 3
NUM_TUNING_FRAME_ELEMENTS_V = 2
TUNING_ELEMENT_H_SIZE = ( TARGET_FRAME_H_SIZE - ( NUM_TUNING_FRAME_ELEMENTS_H + 1 )*INNER_SPACING ) // NUM_TUNING_FRAME_ELEMENTS_H
TUNING_ELEMENT_V_SIZE = ( TARGET_FRAME_V_SIZE - ( NUM_TUNING_FRAME_ELEMENTS_V + 1 )*INNER_SPACING ) // NUM_TUNING_FRAME_ELEMENTS_V

# Beam blocker sizing
BEAM_BLOCKER_BUTTON_H_SIZE = int( ( 5*TARGET_SIZE + 3*INNER_SPACING )/2 )
BEAM_BLOCKER_BUTTON_V_SIZE = TARGET_SIZE
BEAM_BLOCKER_BUTTON2_H_SIZE = int( (3*TARGET_SIZE + 1*INNER_SPACING)/2 )
BEAM_BLOCKER_BUTTON2_V_SIZE = 3*TARGET_SIZE + 2*INNER_SPACING
BEAM_BLOCKER_PANEL_H_SIZE = TARGET_LADDER_H_SIZE // 2
BEAM_BLOCKER_PANEL_V_SIZE = 3*BEAM_BLOCKER_BUTTON_V_SIZE + 4*INNER_SPACING + OUTER_SPACING

# Beam monitoring sizing
NUM_BEAM_MONITORING_ELEMENTS_H = 3
# BEAM_MONITORING_BUTTON_H_SIZE = (NUM_TARGETS_H*TARGET_SIZE + (NUM_TARGETS_H - 1 - 2)*INNER_SPACING ) // NUM_BEAM_MONITORING_ELEMENTS_H
BEAM_MONITORING_BUTTON_H_SIZE = ( TARGET_FRAME_H_SIZE - (NUM_BEAM_MONITORING_ELEMENTS_H + 1 )*INNER_SPACING ) // NUM_BEAM_MONITORING_ELEMENTS_H
BEAM_MONITORING_BUTTON_V_SIZE = NUM_TARGETS_V*TARGET_SIZE + (NUM_TARGET_FRAMES_V - 1)*INNER_SPACING
BEAM_MONITORING_PANEL_H_SIZE = TARGET_FRAME_H_SIZE
BEAM_MONITORING_PANEL_V_SIZE = BEAM_MONITORING_BUTTON_V_SIZE + OUTER_SPACING

# Move motor panel sizing
MOTOR_PANEL_H_SIZE = TARGET_LADDER_H_SIZE
MOTOR_PANEL_V_SIZE = TARGET_SIZE + OUTER_SPACING
MOTOR_BUTTON_H_SIZE = MOTOR_PANEL_H_SIZE - 2*OUTER_SPACING
MOTOR_BUTTON_V_SIZE = TARGET_SIZE

# Colours
COLOUR_TARGET_LADDER = "#FFFFFF"
COLOUR_BEAM_BLOCKER_PANEL = "#FFFFFF"
COLOUR_BEAM_MONITORING_PANEL = "#FFFFFF"
COLOUR_MOVE_MOTOR_PANEL = "#FFFFFF"

COLOUR_MOVE_MOTOR_BUTTON_INVALID = "#777777"
COLOUR_MOVE_MOTOR_BUTTON_VALID = "#FF0000"

COLOUR_TARGET_FRAME = "#555555"
COLOUR_TARGET_DESELECTED = "#777777"
COLOUR_TARGET_SELECTED = "#FF0000"

COLOUR_TUNING_FRAME = "#006600"
COLOUR_TUNING_DESELECTED = "#229922"
COLOUR_TUNING_SELECTED = "#44AA44"

COLOUR_BEAM_BLOCKER_FRAME = "#660099"
COLOUR_BEAM_BLOCKER_DESELECTED = "#8822BB"
COLOUR_BEAM_BLOCKER_SELECTED = "#AA44DD"

COLOUR_BEAM_MONITORING_FRAME = "#0000BB"
COLOUR_BEAM_MONITORING_DESELECTED = "#2222DD"
COLOUR_BEAM_MONITORING_SELECTED = "#4444FF"

# Button font size
FONT_SIZE = 12

dummyval = 0

# FUNCTIONS ================================================================= #
def get_position( myint, spacing, size_of_element ):
    return myint*( size_of_element + spacing ) + spacing

def frame_number( x, y ):
    return NUM_TARGET_FRAMES_H*y + x

def general_button_format( button, colour ):
    button.SetBackgroundColour(colour)
    return

def format_button_selected(button):
    general_button_format( button, COLOUR_MOVE_MOTOR_BUTTON_VALID )
    return

def format_button_deselected(button):
    general_button_format(button, COLOUR_MOVE_MOTOR_BUTTON_INVALID)
    return

###############################################################################
# GUI for motor movement
class XYElementSelectWindow( wx.Frame ):
     def __init__(self,title):
        super().__init__( parent = None, title = "Select targets/beam blockers/beam monitoring", style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX) )
        self.SetClientSize( TARGET_LADDER_H_SIZE,TARGET_LADDER_V_SIZE + BEAM_BLOCKER_PANEL_V_SIZE + MOTOR_PANEL_V_SIZE )
        self.panel = DownstreamMovementPanel( self )
        self.Centre()
        self.Show()

###############################################################################
class DownstreamMovementPanel( wx.Panel ):
    def __init__(self,parent):
        # Initialise panel
        super().__init__( parent = parent )

        # Initialise selected item for movement + ID
        self.selected_item_id = None
        self.selected_item = None

        # Order here is important! Must be target ladder + beam blocker buttons, and then move motor buttons
        self.target_ladder = TargetLadder( parent = self,
                                           pos = (0, 0),
                                           size = (TARGET_LADDER_H_SIZE, TARGET_LADDER_V_SIZE) )
        self.beam_blocker_panel = BeamBlockerPanel( parent = self,
                                                    pos = (0, TARGET_LADDER_V_SIZE ),
                                                    size = (BEAM_BLOCKER_PANEL_H_SIZE, BEAM_BLOCKER_PANEL_V_SIZE) )
        self.beam_monitoring_panel = BeamMonitoringPanel( parent = self,
                                                          pos = (TARGET_LADDER_H_SIZE // 2, TARGET_LADDER_V_SIZE ),
                                                          size = (BEAM_BLOCKER_PANEL_H_SIZE, BEAM_BLOCKER_PANEL_V_SIZE) )
        self.move_motor_panel = MoveMotorPanel( parent = self,
                                                pos = (0, TARGET_LADDER_V_SIZE+BEAM_BLOCKER_PANEL_V_SIZE ),
                                                size = (MOTOR_PANEL_H_SIZE, MOTOR_PANEL_V_SIZE) )

    def get_target_ladder(self):
        return self.target_ladder

    def get_beam_blocker_panel(self):
        return self.beam_blocker_panel

    def get_beam_monitoring_panel(self):
        return self.beam_monitoring_panel

    def get_move_motor_panel(self):
        return self.move_motor_panel

    def get_selected_item(self):
        return self.selected_item

    def get_selected_item_id(self):
        return self.selected_item_id

    def change_selected_item(self, new_item, new_item_id ):
        if self.selected_item != None:
            # Toggle previous switch
            self.selected_item.SetValue(False)
            self.selected_item.format_button_deselected()

        # Assign new selected targets
        self.selected_item = new_item
        self.selected_item_id = new_item_id

###############################################################################
class MoveMotorPanel( wx.Panel ):
    def __init__(self,parent,**kwargs):
        super().__init__(parent = parent, id = wx.ID_ANY, **kwargs)
        self.SetBackgroundColour(COLOUR_MOVE_MOTOR_PANEL)
        self.downstream_movement_panel = parent
        self.target_ladder = self.downstream_movement_panel.get_target_ladder()
        self.beam_blocker_panel = self.downstream_movement_panel.get_beam_blocker_panel()
#        self.control_view = ControlView(self.downstream_movement_panel,self.)
        # Make a panel for holding the buttons
        # self.panel = wx.Panel( parent = self, id = wx.ID_ANY, size = (MOTOR_PANEL_H_SIZE), pos = (int(0.5*OUTER_SPACING),0))
        # self.panel.SetBackgroundColour(COLOUR_TARGET_FRAME)
        self.q=queue.Queue()
        # Make a button for moving targets
        self.button_targets = wx.Button( parent = self,
                                 id = wx.ID_ANY,
                                 pos = ( OUTER_SPACING, 0 ),
                                 size = (MOTOR_BUTTON_H_SIZE, MOTOR_BUTTON_V_SIZE),
                                 label = "MOVE")
        format_button_deselected( self.button_targets )
        self.button_targets.Bind( wx.EVT_BUTTON, self.move_motors )


    # A functions for moving targets
    def move_motors(self,e):
        # Do nothing if no selected item to move
        if self.downstream_movement_panel.get_selected_item_id() == None:
            print("Pressing this button will do nothing if nothing is selected.")
            return
        else:
            # TODO THIS SECTION NEEDS TO ACTUALLY MOVE MOTORS
            print(f"Move motors to {self.downstream_movement_panel.get_selected_item_id()}")
            self.globalpos=self.downstream_movement_panel.get_selected_item_id()
            print('You have selected: '+str(self.globalpos))
            format_button_deselected( self.button_targets )
            self.downstream_movement_panel.change_selected_item(None, None)
#            print(ID_MAP.'1.0.1')


    # Getters
    def get_button_targets(self):
        return self.button_targets

    def get_button_beam_blockers(self):
        return self.button_beam_blockers

    def get_downstream_movement_panel(self):
        return self.downstream_movement_panel

    def get_movement_selection(self):
        return self.downstream_movement_panel.get_selected_item_id()
#    # These are for the moving to speciic positions
#    # I think these can go into Patrick's ladder
#    def move1(self):
#        moveDis = -1*float(self.move1Insert.GetValue())
#        self.driveSystem.move_rel(1,int(moveDis*200))
#
#    def move2(self):
#        moveDis = -1*float(self.move2Insert.GetValue())
#        print("Move 2")
#        self.driveSystem.move_rel(2,int(moveDis*200))
#
#    def setTargetPos(self):
#        newposition=self.targetChoice.GetSelection()
#        print("Target position changed to position "+str(newposition+1))
#        self.driveSystem.select_pos(3,self.targetPositions[newposition]*200)
#
#    def setDetectorPos(self):
#        newposition=self.detectorChoice.GetSelection()
#        if newposition==0:
#            print("Detector position change to position ZD")
#        elif newposition==1:
#            print("Detector position change to position Faraday cup")
#        elif newposition==2:
#            print("ZD detector and FC moves out of the way")
#            self.driveSystem.select_pos(4,self.detectorPositions[newposition]*200)
#

###############################################################################
class BeamBlockerPanel( wx.Panel ):
    def __init__( self, parent, **kwargs ):
        # Initialise
        super().__init__( parent = parent, id = wx.ID_ANY, **kwargs )
        self.SetBackgroundColour(COLOUR_BEAM_BLOCKER_PANEL)

        self.downstream_movement_panel = parent

        # Members
        self.panel = wx.Panel( parent = self, id = wx.ID_ANY, pos = (OUTER_SPACING, 0), size = (TARGET_FRAME_H_SIZE,TARGET_FRAME_V_SIZE))
        self.panel.SetBackgroundColour(COLOUR_BEAM_BLOCKER_FRAME)
        self.button_bb_small = BeamBlockerButton( parent = self,
                                                  id = wx.ID_ANY,
                                                  pos = (OUTER_SPACING + INNER_SPACING,INNER_SPACING),
                                                  size = (BEAM_BLOCKER_BUTTON_H_SIZE, BEAM_BLOCKER_BUTTON_V_SIZE),
                                                  toggle_button_id = ID_MAP.BEAM_BLOCKER_SMALL_ID)
        self.button_bb_medium = BeamBlockerButton( parent = self,
                                                  id = wx.ID_ANY,
                                                  pos = ( OUTER_SPACING + INNER_SPACING, 2*INNER_SPACING + BEAM_BLOCKER_BUTTON_V_SIZE),
                                                  size = (BEAM_BLOCKER_BUTTON_H_SIZE, BEAM_BLOCKER_BUTTON_V_SIZE),
                                                  toggle_button_id = ID_MAP.BEAM_BLOCKER_MEDIUM_ID )
        self.button_bb_large = BeamBlockerButton( parent = self,
                                                  id = wx.ID_ANY,
                                                  pos = ( OUTER_SPACING + INNER_SPACING,3*INNER_SPACING + 2*BEAM_BLOCKER_BUTTON_V_SIZE ),
                                                  size = (BEAM_BLOCKER_BUTTON_H_SIZE, BEAM_BLOCKER_BUTTON_V_SIZE),
                                                  toggle_button_id = ID_MAP.BEAM_BLOCKER_LARGE_ID)
        self.button_bb_clear = BeamBlockerButton( parent = self,
                                                  id = wx.ID_ANY,
                                                  pos = ( OUTER_SPACING + 2*INNER_SPACING + BEAM_BLOCKER_BUTTON_H_SIZE,INNER_SPACING ),
                                                  size = (BEAM_BLOCKER_BUTTON2_H_SIZE, BEAM_BLOCKER_BUTTON2_V_SIZE ),
                                                  toggle_button_id = ID_MAP.BEAM_BLOCKER_CLEAR_ID)

    def get_downstream_movement_panel(self):
        return self.downstream_movement_panel

###############################################################################
class BeamMonitoringPanel( wx.Panel ):
    def __init__( self, parent, **kwargs ):
        # Initialise
        super().__init__( parent = parent, id = wx.ID_ANY, **kwargs )
        self.SetBackgroundColour(COLOUR_BEAM_MONITORING_PANEL)

        self.downstream_movement_panel = parent

        # Members
        self.panel = wx.Panel( parent = self, id = wx.ID_ANY, pos = (OUTER_SPACING//2, 0), size = (TARGET_FRAME_H_SIZE,TARGET_FRAME_V_SIZE))
        self.panel.SetBackgroundColour(COLOUR_BEAM_MONITORING_FRAME)
        self.button_fc = BeamMonitoringButton( parent = self,
                                               id = wx.ID_ANY,
                                               pos = (OUTER_SPACING//2 + INNER_SPACING,INNER_SPACING),
                                               size = (BEAM_MONITORING_BUTTON_H_SIZE, BEAM_MONITORING_BUTTON_V_SIZE),
                                               toggle_button_id = ID_MAP.BEAM_MONITORING_FC_ID)
        self.button_middle = BeamMonitoringButton( parent = self,
                                                   id = wx.ID_ANY,
                                                   pos = ( OUTER_SPACING//2 + 2*INNER_SPACING + BEAM_MONITORING_BUTTON_H_SIZE, INNER_SPACING ),
                                                   size = (BEAM_MONITORING_BUTTON_H_SIZE, BEAM_MONITORING_BUTTON_V_SIZE),
                                                   toggle_button_id = ID_MAP.BEAM_MONITORING_MIDDLE_ID )
        self.button_zd = BeamMonitoringButton( parent = self,
                                               id = wx.ID_ANY,
                                               pos = ( OUTER_SPACING//2 + 3*INNER_SPACING + 2*BEAM_MONITORING_BUTTON_H_SIZE,INNER_SPACING ),
                                               size = (BEAM_MONITORING_BUTTON_H_SIZE, BEAM_MONITORING_BUTTON_V_SIZE),
                                               toggle_button_id = ID_MAP.BEAM_MONITORING_ZD_ID)

    def get_downstream_movement_panel(self):
        return self.downstream_movement_panel



###############################################################################
# Define target ladder class -> wx.Panel
class TargetLadder( wx.Panel ):
    def __init__(self, parent, **kwargs):
        # Initialise
        super().__init__( parent = parent, id = wx.ID_ANY, **kwargs )

        # Members
        self.downstream_movement_panel = parent
        # self.selected_target_id = None
        # self.selected_target = None
        self.target_frames = np.empty( (NUM_TARGET_FRAMES_H, NUM_TARGET_FRAMES_V), dtype=object )

        # Format
        self.SetBackgroundColour( COLOUR_TARGET_LADDER )

        # Populate
        for i in range(0, NUM_TARGET_FRAMES_H):
            for j in range(0, NUM_TARGET_FRAMES_V):
                if (i,j) != TARGET_TUNE_PLATE:
                    self.target_frames[i][j] = TargetFrame( self,
                                                       id = wx.ID_ANY,
                                                       pos = ( get_position( i, OUTER_SPACING, TARGET_FRAME_H_SIZE ), get_position( j, OUTER_SPACING, TARGET_FRAME_V_SIZE ) ),
                                                       frame_id = frame_number( i, j ) )
                    self.target_frames[i][j].SetBackgroundColour( COLOUR_TARGET_FRAME )
                else:
                    self.target_frames[i][j] = TuningFrame( self,
                                                           id = wx.ID_ANY,
                                                           pos = ( get_position( i, OUTER_SPACING, TARGET_FRAME_H_SIZE ), get_position( j, OUTER_SPACING, TARGET_FRAME_V_SIZE ) )
                                                           )
                    self.target_frames[i][j].SetBackgroundColour( COLOUR_TUNING_FRAME )

    def get_downstream_movement_panel(self):
        return self.downstream_movement_panel

###############################################################################
# Define a general frame
class TargetLadderFrame( wx.Panel ):
    def __init__( self, parent, **kwargs ):
        # Members
        self.target_ladder = parent
        self.downstream_movement_panel = self.target_ladder.get_downstream_movement_panel()
        self.frame_id = kwargs.get("frame_id")
        kwargs.pop("frame_id",None)

        # Initialise
        super().__init__( parent = parent, **kwargs, size = (TARGET_FRAME_H_SIZE, TARGET_FRAME_V_SIZE ) )

    # Getters
    def get_target_ladder(self):
        return self.target_ladder

    def get_frame_id(self):
        return self.frame_id

    def get_downstream_movement_panel(self):
        return self.downstream_movement_panel


###############################################################################
# Define target frame
class TargetFrame( TargetLadderFrame ):
    def __init__(self, parent, **kwargs ):
        # Members
        self.targets = np.empty( (NUM_TARGETS_H, NUM_TARGETS_V), dtype=object )
        self.target_ladder = parent
        self.downstream_movement_panel = self.target_ladder.get_downstream_movement_panel()

        # Initialise
        super().__init__( parent, **kwargs )

        # Populate
        for i in range(0,NUM_TARGETS_H):
            for j in range(0,NUM_TARGETS_V):
                toggle_button_id = TargetID( frame = self.frame_id, targetX = i, targetY = j )
                self.targets[i][j] =  TargetButton( self,
                                         id = wx.ID_ANY,
                                         pos=( get_position( i, INNER_SPACING, TARGET_SIZE ), get_position( j, INNER_SPACING, TARGET_SIZE ) ),
                                         size = (TARGET_SIZE,TARGET_SIZE),
                                         toggle_button_id = toggle_button_id )
    def get_target_ladder(self):
        return self.target_ladder

    def get_downstream_movement_panel(self):
        return self.downstream_movement_panel

###############################################################################
class TuningFrame( TargetLadderFrame ):
    def __init__(self,parent,**kwargs):
        # Initialise
        super().__init__( parent = parent, **kwargs )

        # Draw 4 buttons: 2 apertures, 2 slits
        self.small_aperture = TuningButton( parent = self,
                                            id = wx.ID_ANY,
                                            pos = (get_position(0, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(0, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                            size = (TUNING_ELEMENT_H_SIZE,TUNING_ELEMENT_V_SIZE),
                                            toggle_button_id = ID_MAP.SMALL_APERTURE_ID )

        self.large_aperture = TuningButton( parent = self,
                                            id = wx.ID_ANY,
                                            pos = (get_position(0, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(1, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                            size = (TUNING_ELEMENT_H_SIZE,TUNING_ELEMENT_V_SIZE),
                                            toggle_button_id = ID_MAP.LARGE_APERTURE_ID )

        self.horz_slit = TuningButton( parent = self,
                                       id = wx.ID_ANY,
                                       pos = (get_position(1, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(0, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                       size = (TUNING_ELEMENT_H_SIZE,2*TUNING_ELEMENT_V_SIZE + INNER_SPACING),
                                       toggle_button_id = ID_MAP.HORZ_SLIT_ID )

        self.vert_slit = TuningButton( parent = self,
                                       id = wx.ID_ANY,
                                       pos = (get_position(2, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(0, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                       size = (TUNING_ELEMENT_H_SIZE,2*TUNING_ELEMENT_V_SIZE + INNER_SPACING),
                                       toggle_button_id = ID_MAP.VERT_SLIT_ID )

    # Getters
    def get_small_aperture(self):
        return self.small_aperture

    def get_large_aperture(self):
        return self.large_aperture

    def get_horz_slit(self):
        return self.horz_slit

    def get_vert_slit(self):
        return self.vert_slit


###############################################################################
# NOTE: Parent class must always have def get_downstream_movement_panel() function
class CustomToggleButton( wx.ToggleButton ):
    button_colour_selected = None
    button_colour_deselected = None

    def __init__( self, parent, **kwargs ):
        self.toggle_button_id = kwargs.get("toggle_button_id")
        kwargs.pop("toggle_button_id",None)
        self.parent = parent

        self.downstream_movement_panel = parent.get_downstream_movement_panel()

        super().__init__( parent = parent, label = "", **kwargs )
        self.format_button_deselected()
        self.Bind( wx.EVT_TOGGLEBUTTON, self.OnToggle )

    # Format buttons
    def format_button_selected(self):
        self.SetBackgroundColour( self.button_colour_selected )
        self.SetFont( wx.Font( wx.FontInfo(FONT_SIZE).Underlined() ) )

    def format_button_deselected(self):
        # Formatting
        # Set label
        self.SetLabel( ID_MAP.get_label( str(self.toggle_button_id) ) )

        # Background colour
        self.SetBackgroundColour( self.button_colour_deselected )
        self.SetFont( wx.Font( wx.FontInfo(FONT_SIZE) ) )

    # What happens when you click
    def OnToggle( self, e ):
        toggle = e.GetEventObject()
        toggle.format_button_selected()
        select_colour = toggle.get_colour_selected()

        downstream_movement_panel = self.parent.get_downstream_movement_panel()
        move_motor_panel = downstream_movement_panel.get_move_motor_panel()

        # Change selected item in panel if nothing picked
        if downstream_movement_panel.get_selected_item_id() == None:
            downstream_movement_panel.change_selected_item(toggle, self.toggle_button_id)
            general_button_format( move_motor_panel.get_button_targets(), select_colour )
        # Deselect self if clicked again
        elif downstream_movement_panel.get_selected_item_id() == self.toggle_button_id:
            downstream_movement_panel.change_selected_item(None, None)
            general_button_format( move_motor_panel.get_button_targets(), COLOUR_TARGET_DESELECTED )
        # Change if different target picked
        elif downstream_movement_panel.get_selected_item_id() != None:
            downstream_movement_panel.change_selected_item(toggle, self.toggle_button_id)
            general_button_format( move_motor_panel.get_button_targets(), select_colour )

        move_motor_panel.Refresh()

    def get_colour_selected(self):
        return self.button_colour_selected

    def get_colour_deselected(self):
        return self.button_colour_deselected

###############################################################################
class TargetButton( CustomToggleButton ):
    button_colour_selected = COLOUR_TARGET_SELECTED
    button_colour_deselected = COLOUR_TARGET_DESELECTED
###############################################################################
class TuningButton( CustomToggleButton ):
    button_colour_selected = COLOUR_TUNING_SELECTED
    button_colour_deselected = COLOUR_TUNING_DESELECTED
###############################################################################
class BeamBlockerButton( CustomToggleButton ):
    button_colour_deselected = COLOUR_BEAM_BLOCKER_DESELECTED
    button_colour_selected = COLOUR_BEAM_BLOCKER_SELECTED
###############################################################################
class BeamMonitoringButton( CustomToggleButton ):
    button_colour_deselected = COLOUR_BEAM_MONITORING_DESELECTED
    button_colour_selected = COLOUR_BEAM_MONITORING_SELECTED
###############################################################################
###############################################################################
###############################################################################
# MAIN
def main():
    app = wx.App()
    gui = XYElementSelectWindow( "TITLE" )
    app.MainLoop()

if __name__ == "__main__":
    main()
