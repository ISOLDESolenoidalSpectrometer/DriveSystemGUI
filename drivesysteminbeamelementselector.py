"""
Drive system in beam element selector
=====================================

This module defines the window used to select in-beam elements and move to them.
"""

import numpy as np
import wx
from drivesystemdetectoridmapping import *

from drivesystemlib import *
from drivesystemguilib import *
import drivesystemoptions as dsopts

################################################################################
################################################################################
################################################################################
# CONSTANTS
TARGET_SIZE = 40    # Try to keep this even!
INNER_SPACING = 6  # Try to keep this even!
OUTER_SPACING = 10

# Label - ID list initialise
ID_MAP = IDMap(dsopts.OPTION_2D_LADDER_LABEL_MAP_PATH.get_value())

# Target ladder sizing
NUM_TARGETS_H_ARRAY = np.array([8,4], dtype=int)
NUM_TARGETS_V_ARRAY = np.array([1,3], dtype=int)
NUM_TARGET_FRAMES_H_ARRAY = np.array([1,2], dtype=int)
NUM_TARGET_FRAMES_V_ARRAY = np.array([1,3], dtype=int)

TARGET_FRAME_H_SIZE_ARRAY = NUM_TARGETS_H_ARRAY*TARGET_SIZE + ( NUM_TARGETS_H_ARRAY + 1 )*INNER_SPACING
TARGET_FRAME_V_SIZE_ARRAY = NUM_TARGETS_V_ARRAY*TARGET_SIZE + ( NUM_TARGETS_V_ARRAY + 1 )*INNER_SPACING
TARGET_LADDER_H_SIZE = TARGET_FRAME_H_SIZE_ARRAY[1]*NUM_TARGET_FRAMES_H_ARRAY[1] + ( NUM_TARGET_FRAMES_H_ARRAY[1] + 1 )*OUTER_SPACING
TARGET_LADDER_V_SIZE_ARRAY = TARGET_FRAME_V_SIZE_ARRAY*NUM_TARGET_FRAMES_V_ARRAY + ( NUM_TARGET_FRAMES_V_ARRAY + 1 )*OUTER_SPACING

# Tuning plate
TARGET_TUNE_PLATE = (0,0)
NUM_TUNING_FRAME_ELEMENTS_H = 3
NUM_TUNING_FRAME_ELEMENTS_V = 2
TUNING_ELEMENT_H_SIZE = ( TARGET_FRAME_H_SIZE_ARRAY[1] - ( NUM_TUNING_FRAME_ELEMENTS_H + 1 )*INNER_SPACING ) // NUM_TUNING_FRAME_ELEMENTS_H
TUNING_ELEMENT_V_SIZE = ( TARGET_FRAME_V_SIZE_ARRAY[1] - ( NUM_TUNING_FRAME_ELEMENTS_V + 1 )*INNER_SPACING ) // NUM_TUNING_FRAME_ELEMENTS_V

# Beam blocker sizing
BEAM_BLOCKER_BUTTON_H_SIZE = int( ( 5*TARGET_SIZE + 3*INNER_SPACING )/2 )
BEAM_BLOCKER_BUTTON_V_SIZE = TARGET_SIZE
BEAM_BLOCKER_BUTTON2_H_SIZE = int( (3*TARGET_SIZE + 1*INNER_SPACING)/2 )
BEAM_BLOCKER_BUTTON2_V_SIZE = 3*TARGET_SIZE + 2*INNER_SPACING
BEAM_BLOCKER_PANEL_H_SIZE = TARGET_LADDER_H_SIZE // 2
BEAM_BLOCKER_PANEL_V_SIZE = 3*BEAM_BLOCKER_BUTTON_V_SIZE + 4*INNER_SPACING + OUTER_SPACING

# Beam monitoring sizing
NUM_BEAM_MONITORING_ELEMENTS_H = 3
# BEAM_MONITORING_BUTTON_H_SIZE = (NUM_TARGETS_H_ARRAY*TARGET_SIZE + (NUM_TARGETS_H_ARRAY - 1 - 2)*INNER_SPACING ) // NUM_BEAM_MONITORING_ELEMENTS_H
BEAM_MONITORING_BUTTON_H_SIZE = ( TARGET_FRAME_H_SIZE_ARRAY[1] - (NUM_BEAM_MONITORING_ELEMENTS_H + 1 )*INNER_SPACING ) // NUM_BEAM_MONITORING_ELEMENTS_H
BEAM_MONITORING_BUTTON_V_SIZE = NUM_TARGETS_V_ARRAY[1]*TARGET_SIZE + (NUM_TARGET_FRAMES_V_ARRAY[1] - 1)*INNER_SPACING
BEAM_MONITORING_PANEL_H_SIZE = TARGET_FRAME_H_SIZE_ARRAY[1]
BEAM_MONITORING_PANEL_V_SIZE = BEAM_MONITORING_BUTTON_V_SIZE + OUTER_SPACING

# Move motor panel sizing
MOTOR_PANEL_H_SIZE = TARGET_LADDER_H_SIZE
MOTOR_PANEL_V_SIZE = TARGET_SIZE + OUTER_SPACING
MOTOR_BUTTON_H_SIZE = MOTOR_PANEL_H_SIZE - 2*OUTER_SPACING
MOTOR_BUTTON_V_SIZE = TARGET_SIZE

# Alpha source panel sizing
ALPHA_PANEL_H_SIZE = TARGET_LADDER_H_SIZE
ALPHA_PANEL_V_SIZE = TARGET_SIZE + 2*INNER_SPACING + OUTER_SPACING
ALPHA_BUTTON_H_SIZE = ALPHA_PANEL_H_SIZE - 2*OUTER_SPACING - 2*INNER_SPACING
ALPHA_BUTTON_V_SIZE = TARGET_SIZE

# Colours
COLOUR_BUTTON_TEXT = "#000000"
COLOUR_TARGET_LADDER = "#FFFFFF"
COLOUR_BEAM_BLOCKER_PANEL = "#FFFFFF"
COLOUR_BEAM_MONITORING_PANEL = "#FFFFFF"
COLOUR_MOVE_MOTOR_PANEL = "#FFFFFF"
COLOUR_ALPHA_SOURCE_PANEL = "#FFFFFF"

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

COLOUR_ALPHA_SOURCE_FRAME = "#BB0000"
COLOUR_ALPHA_SOURCE_FRAME_DESELECTED = "#BB4444"
COLOUR_ALPHA_SOURCE_FRAME_SELECTED = "#FF6666"

# Button font size
FONT_SIZE = 12

################################################################################
################################################################################
################################################################################
def get_position( myint : int, spacing : int, size_of_element : int ) -> int:
    """
    Function to calculate the position of an item in a regular grid

    Parameters
    ----------
    myint : int
        The numbered position in the grid
    spacing : int
        The spacing between elements in the grid
    size_of_element : int
        The size of each element in the grid

    Returns
    -------
    pos : int
        The position of the element in the coordinate system in use
    """
    return myint*( size_of_element + spacing ) + spacing

################################################################################
def frame_number( x : int, y : int, number_of_target_frames_h : int ) -> int:
    """
    Numbers the target frames from left-to-right and top-to-bottom based on their
    position in a 2D grid

    Parameters
    ----------
    x : int
        Horizontal position in the grid (column number)
    y : int
        Vertical position in the grid (row number)
    number_of_target_frames_h : int
        Number of target frames in the horizontal direction

    Returns
    -------
    num : int
        The number of the item
    """
    return number_of_target_frames_h*y + x

################################################################################
def general_button_format( button : wx.Button, colour : str ) -> None:
    """
    target_ladder_select: Formats buttons in the same style by changing its 
    colour
    
    Parameters
    ----------
    button : wx.Button
        Button to be formatted
    colour : str
        The colour of the button
    """
    button.SetBackgroundColour(colour)
    button.SetForegroundColour( COLOUR_BUTTON_TEXT )
    return

################################################################################
def format_button_selected( button : wx.Button ) -> None:
    """
    target_ladder_select: Formats a button to indicate that it is selected

    Parameters
    ----------
    button : wx.Button
        Button to be formatted
    """
    general_button_format( button, COLOUR_MOVE_MOTOR_BUTTON_VALID )
    return

################################################################################
def format_button_deselected( button : wx.Button ) -> None:
    """
    target_ladder_select: Formats a button to indicate that it is deselected

    Parameters
    ----------
    button : wx.Button
        Button to be formatted
    """
    general_button_format(button, COLOUR_MOVE_MOTOR_BUTTON_INVALID)
    return

################################################################################
################################################################################
################################################################################
class InBeamElementSelectionWindow( wx.Frame ):
    """
    This class is how we select in-beam elements. It is the window which holds
    the downstream movement panel. It is a singleton.
    """
    instance = None     # This is the single instance
    init = False        # This determines whether the panel has already been initialised

    ################################################################################
    def __new__(self, *args, **kwargs):
        """
        InBeamElementSelectionWindow: make it a singleton so we don't have multiple
        copies floating around.

        Returns
        -------
        instance : InBeamElementSelectionWindow
            The instance of the window
        """
        if self.instance is None:
            self.instance = super().__new__(self)
        return self.instance

    ################################################################################
    def __init__(self) -> None:
        """
        InBeamElementSelectionWindow: Initialise the window (or raise the current
        instance)
        """
        # Do nothing if already initialised
        if self.init:
            self.Raise() # Moves already initialised window to the top
            return
        
        # First initialisation -> tell code that this is true
        self.init = True

        # Initialise as normal
        super().__init__( parent = None, title = "Select in-beam elements", style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX) )

        index = dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() - 1

        self.SetClientSize( TARGET_LADDER_H_SIZE, ALPHA_PANEL_V_SIZE + TARGET_LADDER_V_SIZE_ARRAY[index] + BEAM_BLOCKER_PANEL_V_SIZE + MOTOR_PANEL_V_SIZE )
        self.panel = InBeamElementSelectionPanel( self )
        self.Bind( wx.EVT_CLOSE, self.close_window)
        self.Centre()
        self.Show()
        return

    ################################################################################
    def close_window(self, event : wx.CommandEvent) -> None:
        """
        InBeamElementSelectionWindow: Close the window and allow a new one to be
        created.

        Parameters
        ----------
        event : wx.CommandEvent
            The event related to closing the window
        """
        self.init = False
        self.Destroy()
        return

    ################################################################################
    @classmethod
    def get_instance(cls):
        """
        InBeamElementSelectionWindow: Class method that returns the instance of the
        window

        Returns
        -------
        instance : InBeamElementSelectionWindow
            The instance of the window
        """
        if cls.instance == None:
            cls()
        return cls.instance

    ################################################################################
    @classmethod
    def is_drawn(cls) -> bool:
        """
        InBeamElementSelectionWindow: Class method that tells you if the window has
        been created or not

        Returns
        -------
        init : bool
            The parameter that says if the window is currently initialised
        """
        return cls.init

################################################################################
################################################################################
################################################################################
class InBeamElementSelectionPanel( wx.Panel ):
    """
    InBeamElementSelectionPanel: This panel occupies the InBeamElementSelectionWindow
    and holds the different elements for moving elements into/out of the beam
    """
    ################################################################################
    def __init__(self,parent : InBeamElementSelectionWindow) -> None:
        """
        InBeamElementSelectionPanel: Initialise the various elements

        Parameters
        ----------
        parent : InBeamElementSelectionWindow
            The parent window that holds the panel
        """
        # Initialise panel
        super().__init__( parent = parent )

        # Initialise selected item for movement + ID
        self.selected_object = None     # The object that is being selected on a given panel
        self.selected_object_id = None  # The ID of the item that is being selected by the object on a given panel

        # Order here is important! Must be target ladder + beam blocker buttons, and then move motor buttons
        index = dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() - 1
        
        self.alpha_panel = AlphaSourcePanel( parent = self, pos = (0,0), size = (ALPHA_PANEL_H_SIZE, ALPHA_PANEL_V_SIZE) )
        self.target_ladder = TargetLadderPanel( parent = self, pos = (0, ALPHA_PANEL_V_SIZE), size = (TARGET_LADDER_H_SIZE, TARGET_LADDER_V_SIZE_ARRAY[index]) )
        self.beam_blocker_panel = BeamBlockerPanel( parent = self, pos = (0, TARGET_LADDER_V_SIZE_ARRAY[index] + ALPHA_PANEL_V_SIZE ), size = (BEAM_BLOCKER_PANEL_H_SIZE, BEAM_BLOCKER_PANEL_V_SIZE) )
        self.beam_monitoring_panel = BeamMonitoringPanel( parent = self, pos = (TARGET_LADDER_H_SIZE // 2, TARGET_LADDER_V_SIZE_ARRAY[index] + ALPHA_PANEL_V_SIZE ), size = (BEAM_BLOCKER_PANEL_H_SIZE, BEAM_BLOCKER_PANEL_V_SIZE) )
        self.move_motor_panel = MoveMotorPanel( parent = self, pos = (0, TARGET_LADDER_V_SIZE_ARRAY[index]+BEAM_BLOCKER_PANEL_V_SIZE + ALPHA_PANEL_V_SIZE), size = (MOTOR_PANEL_H_SIZE, MOTOR_PANEL_V_SIZE) )
        
    ################################################################################
    def get_target_ladder(self):
        """
        InBeamElementSelectionPanel: Simple getter for TargetLadderPanel object
        """
        return self.target_ladder

    ################################################################################
    def get_beam_blocker_panel(self):
        """
        InBeamElementSelectionPanel: Simple getter for BeamBlockerPanel object
        """
        return self.beam_blocker_panel

    ################################################################################
    def get_beam_monitoring_panel(self):
        """
        InBeamElementSelectionPanel: Simple getter for BeamMonitoringPanel object
        """
        return self.beam_monitoring_panel

    ################################################################################
    def get_move_motor_panel(self):
        """
        InBeamElementSelectionPanel: Simple getter for MoveMotorPanel object
        """
        return self.move_motor_panel

    ################################################################################
    def get_selected_object(self):
        """
        InBeamElementSelectionPanel: Simple getter for the object that has been
        selected
        """
        return self.selected_object

    ################################################################################
    def get_selected_object_id(self):
        """
        InBeamElementSelectionPanel: Simple getter for the ID of the object that has
        been selected
        """
        return self.selected_object_id

    ################################################################################
    def change_selected_item(self, new_object, new_object_id ):
        """
        InBeamElementSelectionPanel: Method for changing the element that has been
        selected

        Parameters
        ----------
        new_object : some kind of button
            This is the object that is selected in the InBeamElementSelectionWindow
        new_object_id : str or TargetID
            This is the ID of the object that is selected
        """
        if self.selected_object != None:
            # Toggle previous switch
            self.selected_object.SetValue(False)
            self.selected_object.format_button_deselected()

        # Assign new selected targets
        self.selected_object = new_object
        self.selected_object_id = new_object_id
        return

################################################################################
################################################################################
################################################################################
class AlphaSourcePanel( wx.Panel ):
    """
    This class holds a button that moves the alpha source into position
    """
    ################################################################################
    def __init__(self, parent : InBeamElementSelectionPanel, **kwargs ):
        """
        AlphaSourcePanel: Initialise the button + background panel used for this

        Parameters
        ----------
        parent : InBeamElementSelectionWindow
            The parent window that holds the panel
        kwargs
            Keyword arguments to be passed to the wx.Panel constructor
        """
       # Initialise
        super().__init__( parent = parent, id = wx.ID_ANY, **kwargs )
        self.SetBackgroundColour(COLOUR_ALPHA_SOURCE_PANEL)
        self.in_beam_element_selection_panel = parent

        # Members
        self.background_panel = wx.Panel( parent = self, id = wx.ID_ANY, pos = (OUTER_SPACING, OUTER_SPACING), size = (ALPHA_PANEL_H_SIZE-2*OUTER_SPACING,ALPHA_PANEL_V_SIZE - OUTER_SPACING))
        self.background_panel.SetBackgroundColour(COLOUR_ALPHA_SOURCE_FRAME)

        self.button = AlphaButton(parent = self,
                                  id = wx.ID_ANY,
                                  pos = (OUTER_SPACING + INNER_SPACING,OUTER_SPACING + INNER_SPACING),
                                  size = (ALPHA_BUTTON_H_SIZE, ALPHA_BUTTON_V_SIZE),
                                  toggle_button_id = ID_MAP.ALPHA_SOURCE_ID)

        return
    
    ################################################################################
    def get_in_beam_element_selection_panel(self):
        """
        AlphaSourcePanel: All classes containing CustomToggleButton objects must
        have this getter

        Returns
        -------
        in_beam_element_selection_panel : InBeamElementSelectionPanel
            The selection panel where objects are selected
        """
        return self.in_beam_element_selection_panel


################################################################################
################################################################################
################################################################################
class MoveMotorPanel( wx.Panel ):
    """
    This panel holds the move button and tells the DriveSystem object to move 
    the motors selected in the InBeamElementSelectionPanel
    """
    ################################################################################
    def __init__(self, parent : InBeamElementSelectionPanel, **kwargs):
        """
        MoveMotorPanel: Initialise the movement button
        """
        # Call parent constructor
        super().__init__(parent = parent, id = wx.ID_ANY, **kwargs)

        # Format the panel
        self.SetBackgroundColour(COLOUR_MOVE_MOTOR_PANEL)

        # Store the parent panel
        self.in_beam_element_selection_panel = parent

        # Create the move button
        self.button_move = wx.Button( parent = self, id = wx.ID_ANY, pos = ( OUTER_SPACING, 0 ), size = (MOTOR_BUTTON_H_SIZE, MOTOR_BUTTON_V_SIZE), label = "MOVE" )
        format_button_deselected( self.button_move )
        self.button_move.Bind( wx.EVT_BUTTON, self.move_motors )

        # Get DriveSystem object for movement
        self.drive_system = DriveSystem.get_instance()
        return

    ################################################################################
    # A functions for moving targets
    def move_motors(self, e : wx.CommandEvent):
        """
        MoveMotorPanel: This function tells the DriveSystem object to move the
        motors after pressing the move button. We also need to update the selected
        in-beam element.

        Parameters
        ----------
        e : wx.CommandEvent
            Allows this function to be bound to the move button
        """
        # Do nothing if no selected item to move
        if self.in_beam_element_selection_panel.get_selected_object_id() == None:
            print("Pressing this button will do nothing if nothing is selected.")
            return
    
        # Store the ID and deselect the button
        globalpos = self.in_beam_element_selection_panel.get_selected_object_id()
        format_button_deselected( self.button_move )
        self.in_beam_element_selection_panel.change_selected_item(None, None)

        # Check whether we are moving in 2D or not

        # Tell motors to move with move absolute commands
        # Move 2D targets
        if re.search('[0-9].[0-9].[0-9]', str(globalpos)):
            print('TARGET: ' + str(globalpos))
            self.drive_system.move_absolute( MOTOR_AXIS_DICT['TLH'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][0] )
            if dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() == 2:
                self.drive_system.move_absolute( MOTOR_AXIS_DICT['TLV'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][1] )

        # Move alpha source
        elif re.search('alpha', str(globalpos)):
            print('ALPHA SOURCE: ' + str(globalpos))
            self.drive_system.move_absolute( MOTOR_AXIS_DICT['TLH'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][0] )
            if dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() == 2:
                self.drive_system.move_absolute( MOTOR_AXIS_DICT['TLV'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][1] )
        
        # Move slits/apertures
        elif re.search('[a-zA-Z]_slit',str(globalpos)) or re.search('[a-zA-Z]_aperture',str(globalpos)):
            print('SLIT/APERTURES: ' + str(globalpos))
            self.drive_system.move_absolute( MOTOR_AXIS_DICT['TLH'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][0] )
            if dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() == 2:
                self.drive_system.move_absolute( MOTOR_AXIS_DICT['TLV'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][1] )
        
        # Move beam blocker
        elif re.search('bb.*',str(globalpos)): # beam blocker
            self.drive_system.move_absolute( MOTOR_AXIS_DICT['BBV'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][0] )
            self.drive_system.move_absolute( MOTOR_AXIS_DICT['BBH'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][1] )

        # Move beam monitoring detectors
        elif re.search('bm.*',str(globalpos)): # beam monitor
            self.drive_system.move_absolute( MOTOR_AXIS_DICT['Det'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][0] )

        # Move tritium targets
        elif re.search('ti_target[0-9]', str(globalpos)):
            print('Ti TARGET: ' + str(globalpos))
            self.drive_system.move_absolute( MOTOR_AXIS_DICT['TLH'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][0] )
            if dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() == 2:
                self.drive_system.move_absolute( MOTOR_AXIS_DICT['TLV'].axis_number, dsopts.AXIS_POSITION_DICT[ str( globalpos ) ][1] )
        
        # Tell user their selected action didn't work
        else:
            print("Wasn't able to move - I don't recognise the element...")

        # Regardless, store the element
        self.drive_system.set_in_beam_element( str(globalpos) )
        
        return

    ################################################################################
    def get_button_move(self):
        """
        MoveMotorPanel: A simple getter for getting the move button
        """
        return self.button_move


################################################################################
################################################################################
################################################################################
class BeamBlockerPanel( wx.Panel ):
    """
    This panel holds the controls for moving the beam blocker
    """
    ################################################################################
    def __init__( self, parent, **kwargs ):
        """
        BeamBlockerPanel: Initialise with the relevant BeamBlockerButton objects
        """
        # Initialise
        super().__init__( parent = parent, id = wx.ID_ANY, **kwargs )
        self.SetBackgroundColour(COLOUR_BEAM_BLOCKER_PANEL)
        self.in_beam_element_selection_panel = parent

        # Members
        self.background_panel = wx.Panel( parent = self, id = wx.ID_ANY, pos = (OUTER_SPACING, 0), size = (TARGET_FRAME_H_SIZE_ARRAY[1],TARGET_FRAME_V_SIZE_ARRAY[1]))
        self.background_panel.SetBackgroundColour(COLOUR_BEAM_BLOCKER_FRAME)

        # Check if we're creating buttons (if beam blocker in use)
        if dsopts.OPTION_IS_BEAM_BLOCKER_ENABLED.get_value():
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
        else:
            self.text = wx.StaticText( parent = self.background_panel,
                                       id = wx.ID_ANY,
                                       label = "BEAM BLOCKER NOT IN USE",
                                       pos = (0, int(0.4*TARGET_FRAME_V_SIZE_ARRAY[1])),
                                       size = (TARGET_FRAME_H_SIZE_ARRAY[1], TARGET_FRAME_V_SIZE_ARRAY[1]),
                                       style =wx.ALIGN_CENTRE_HORIZONTAL )
        return

    ################################################################################
    def get_in_beam_element_selection_panel(self):
        """
        BeamBlockerPanels: All classes containing CustomToggleButton objects must
        have this getter
        """
        return self.in_beam_element_selection_panel

################################################################################
################################################################################
################################################################################
class BeamMonitoringPanel( wx.Panel ):
    """
    Panel controlling the beam-monitoring elements
    """
    ################################################################################
    def __init__( self, parent, **kwargs ):
        """
        BeamMonitoringPanel: Initialise the various beam-monitoring elements
        """
        # Initialise
        super().__init__( parent = parent, id = wx.ID_ANY, **kwargs )
        self.SetBackgroundColour(COLOUR_BEAM_MONITORING_PANEL)
        self.in_beam_element_selection_panel = parent

        # Members
        self.background_panel = wx.Panel( parent = self, id = wx.ID_ANY, pos = (OUTER_SPACING//2, 0), size = (TARGET_FRAME_H_SIZE_ARRAY[1],TARGET_FRAME_V_SIZE_ARRAY[1]))
        self.background_panel.SetBackgroundColour(COLOUR_BEAM_MONITORING_FRAME)
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
        
        return

    ################################################################################
    def get_in_beam_element_selection_panel(self):
        """
        BeamMonitoringPanel: All classes containing CustomToggleButton objects must
        have this getter
        """
        return self.in_beam_element_selection_panel



################################################################################
################################################################################
################################################################################
class TargetLadderPanel( wx.Panel ):
    """
    Contains the elements for moving the target ladder
    """
    ################################################################################
    def __init__(self, parent, **kwargs):
        """
        TargetLadderPanel: Initialise the target frames for 1D or 2D target ladder.
        Also initialised the tuning frame it it is used
        """
        # Initialise
        super().__init__( parent = parent, id = wx.ID_ANY, **kwargs )
        self.in_beam_element_selection_panel = parent

        # Format
        self.SetBackgroundColour( COLOUR_TARGET_LADDER )

        # Work out what style to use - 1D or 2D
        index = dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() - 1

        # Change spacing if 1D so that ladder is centred in window
        if index == 0:
            outer_spacing = OUTER_SPACING + ( TARGET_LADDER_H_SIZE - 2*OUTER_SPACING - ( NUM_TARGETS_H_ARRAY[index] + 1)*INNER_SPACING - NUM_TARGETS_H_ARRAY[index]*TARGET_SIZE )//2
        else:
            outer_spacing = OUTER_SPACING

        # Members
        self.target_frames = np.empty( (NUM_TARGET_FRAMES_H_ARRAY[index], NUM_TARGET_FRAMES_V_ARRAY[index]), dtype=object )

        # Populate
        for i in range(0, NUM_TARGET_FRAMES_H_ARRAY[index]):
            for j in range(0, NUM_TARGET_FRAMES_V_ARRAY[index]):
                # Make target frames
                if (i,j) != TARGET_TUNE_PLATE or index == 0:
                    self.target_frames[i][j] = TargetFrame( self,
                                                    id = wx.ID_ANY,
                                                    pos = ( get_position( i, outer_spacing, TARGET_FRAME_H_SIZE_ARRAY[index] ), get_position( j, OUTER_SPACING, TARGET_FRAME_V_SIZE_ARRAY[index] ) ),
                                                    frame_id = frame_number( i, j, NUM_TARGET_FRAMES_H_ARRAY[index] ) )
                    self.target_frames[i][j].SetBackgroundColour( COLOUR_TARGET_FRAME )
                
                # Make tuning frame
                else:
                    if index == 1:
                        if dsopts.OPTION_TUNING_FRAME_IS_TRITIUM_TUNING_FRAME.get_value():
                            self.target_frames[i][j] = TuningFrameTritium( self,
                                                                id = wx.ID_ANY,
                                                                pos = ( get_position( i, outer_spacing, TARGET_FRAME_H_SIZE_ARRAY[index] ), get_position( j, OUTER_SPACING, TARGET_FRAME_V_SIZE_ARRAY[index] ) )
                                                                )
                        else:
                            self.target_frames[i][j] = TuningFrame( self,
                                                                id = wx.ID_ANY,
                                                                pos = ( get_position( i, outer_spacing, TARGET_FRAME_H_SIZE_ARRAY[index] ), get_position( j, OUTER_SPACING, TARGET_FRAME_V_SIZE_ARRAY[index] ) )
                                                                )
                        self.target_frames[i][j].SetBackgroundColour( COLOUR_TUNING_FRAME )
        return

    ################################################################################
    def get_in_beam_element_selection_panel(self):
        """
        TargetLadderPanel: simple getter for the InBeamSelectionPanel object. This
        must be defined due to requirements in the CustomToggleButton class
        """
        return self.in_beam_element_selection_panel

################################################################################
################################################################################
################################################################################
# Define a general frame
class TargetLadderPanelFrame( wx.Panel ):
    """
    General class for a target ladder frame, forming the base for the
    TargetLadderFrame and TuningFrame classes
    """
    ################################################################################
    def __init__( self, parent, **kwargs ):
        """
        TargetLadderPanelFrame: initialise 
        """
        # Members
        self.target_ladder = parent
        self.in_beam_element_selection_panel = self.target_ladder.get_in_beam_element_selection_panel()
        self.frame_id = kwargs.get("frame_id")
        kwargs.pop("frame_id",None)

        index = dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() - 1
        super().__init__( parent = parent, **kwargs, size = (TARGET_FRAME_H_SIZE_ARRAY[index], TARGET_FRAME_V_SIZE_ARRAY[index] ) )
        
        return

    ################################################################################
    def get_target_ladder(self):
        """
        TargetLadderPanelFrame: simple getter for the target ladder
        """
        return self.target_ladder

    ################################################################################
    def get_frame_id(self):
        """
        TargetLadderPanelFrame: Simple getter for the ID of the frame
        """
        return self.frame_id

    ################################################################################
    def get_in_beam_element_selection_panel(self):
        """
        TargetLadderPanelFrame: simple getter for the InBeamSelectionPanel object.
        This must be defined due to requirements in the CustomToggleButton class.
        """
        return self.in_beam_element_selection_panel


################################################################################
################################################################################
################################################################################
# Define target frame
class TargetFrame( TargetLadderPanelFrame ):
    """
    A small panel that holds a set of targets. In 1D, this is the whole ladder,
    but in 2D, this is one of the plates containing multiple targets.
    """
    ################################################################################
    def __init__(self, parent : TargetLadderPanel, **kwargs ):
        """
        TargetFrame: initialise the target buttons in the frame depending on whether
        it's 1D or 2D.

        Parameters
        ----------
        parent : TargetLadderPanel
            The TargetLadderPanel object that holds the target frame.
        kwargs : various
            Keyword arguments for the parent TargetLadderPanelFrame (wx.Panel)
            constructor.
        
        """
        # Members
        self.target_ladder = parent
        self.in_beam_element_selection_panel = self.target_ladder.get_in_beam_element_selection_panel()

        # Initialise
        super().__init__( parent, **kwargs )

        # Populate
         # Work out what style to use - 1D or 2D
        index = dsopts.OPTION_TARGET_LADDER_DIMENSION.get_value() - 1

        # Create targets array
        self.targets = np.empty( (NUM_TARGETS_H_ARRAY[index], NUM_TARGETS_V_ARRAY[index]), dtype=object )

        # Populate targets array
        for i in range(0,NUM_TARGETS_H_ARRAY[index]):
            for j in range(0,NUM_TARGETS_V_ARRAY[index]):
                toggle_button_id = TargetID( frame = self.frame_id, targetX = i, targetY = j )
                self.targets[i][j] =  TargetButton( self,
                                        id = wx.ID_ANY,
                                        pos=( get_position( i, INNER_SPACING, TARGET_SIZE ), get_position( j, INNER_SPACING, TARGET_SIZE ) ),
                                        size = (TARGET_SIZE,TARGET_SIZE),
                                        toggle_button_id = toggle_button_id )
        return
                

################################################################################
################################################################################
################################################################################
class TuningFrame( TargetLadderPanelFrame ):
    """
    A small panel that holds elements for tuning on the 2D ladder.
    """
    ################################################################################
    def __init__(self, parent : TargetLadderPanel, **kwargs):
        """
        TuningFrame: Initialise the four tuning elements in the panel

        Parameters
        ----------
        parent : TargetLadderPanel
            The TargetLadderPanel object that holds the target frame.
        kwargs : various
            Keyword arguments for the parent TargetLadderPanelFrame (wx.Panel)
            constructor.
        """
        # Initialise
        super().__init__( parent = parent, **kwargs )

        # Draw 4 buttons: 2 apertures, 2 slits
        self.small_aperture = TuningButton( parent = self,
                                            id = wx.ID_ANY,
                                            pos = (get_position(2, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(0, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                            size = (TUNING_ELEMENT_H_SIZE,TUNING_ELEMENT_V_SIZE),
                                            toggle_button_id = ID_MAP.SMALL_APERTURE_ID )

        self.large_aperture = TuningButton( parent = self,
                                            id = wx.ID_ANY,
                                            pos = (get_position(2, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(1, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                            size = (TUNING_ELEMENT_H_SIZE,TUNING_ELEMENT_V_SIZE),
                                            toggle_button_id = ID_MAP.LARGE_APERTURE_ID )

        self.horz_slit = TuningButton( parent = self,
                                       id = wx.ID_ANY,
                                       pos = (get_position(1, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(0, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                       size = (TUNING_ELEMENT_H_SIZE,2*TUNING_ELEMENT_V_SIZE + INNER_SPACING),
                                       toggle_button_id = ID_MAP.HORZ_SLIT_ID )

        self.vert_slit = TuningButton( parent = self,
                                       id = wx.ID_ANY,
                                       pos = (get_position(0, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(0, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                       size = (TUNING_ELEMENT_H_SIZE,2*TUNING_ELEMENT_V_SIZE + INNER_SPACING),
                                       toggle_button_id = ID_MAP.VERT_SLIT_ID )
        
        return
    
################################################################################
################################################################################
################################################################################
class TuningFrameTritium( TargetLadderPanelFrame ):
    """
    A small panel that holds elements for tuning on the 2D ladder, with space
    for tritium targets.
    """
    ################################################################################
    def __init__(self, parent : TargetLadderPanel, **kwargs):
        """
        TuningFrameTritium: Initialise the four tuning elements in the panel

        Parameters
        ----------
        parent : TargetLadderPanel
            The TargetLadderPanel object that holds the target frame.
        kwargs : various
            Keyword arguments for the parent TargetLadderPanelFrame (wx.Panel)
            constructor.
        """
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

        self.ti_target_frame1 = TuningButton( parent = self,
                                       id = wx.ID_ANY,
                                       pos = (get_position(1, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(0, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                       size = (TUNING_ELEMENT_H_SIZE,2*TUNING_ELEMENT_V_SIZE + INNER_SPACING),
                                       toggle_button_id = ID_MAP.TI_TARGET_1_ID )

        self.ti_target_frame2 = TuningButton( parent = self,
                                       id = wx.ID_ANY,
                                       pos = (get_position(2, INNER_SPACING, TUNING_ELEMENT_H_SIZE),get_position(0, INNER_SPACING, TUNING_ELEMENT_V_SIZE) ),
                                       size = (TUNING_ELEMENT_H_SIZE,2*TUNING_ELEMENT_V_SIZE + INNER_SPACING),
                                       toggle_button_id = ID_MAP.TI_TARGET_2_ID )
        
        return


################################################################################
################################################################################
################################################################################
# NOTE: Owner of this object must always have def get_in_beam_element_selection_panel() function
class CustomToggleButton( wx.ToggleButton ):
    """
    A base class for toggled buttons based on the wx.ToggleButton class. The
    functionality built here allows further classes to be defined simply by
    specifying their colour. Note that this class MUST have a method that 
    returns the InBeamElementSelectionPanel object called 
    "get_in_beam_element_selection_panel" in order to communicate with it.
    """
    button_colour_selected = None
    button_colour_deselected = None

    ################################################################################
    def __init__( self, parent, **kwargs ):
        """
        CustomToggleButton: initialise by binding function to toggle and specifying
        ID etc.

        Parameters
        ----------
        parent : various
            The parent object that holds the CustomToggleButton object.
        kwargs : various
            Keyword arguments for the parent object (probably wx.Panel)
            constructor.
        """
        # Get the ID from the keyword arguments
        self.toggle_button_id = kwargs.get("toggle_button_id")
        kwargs.pop("toggle_button_id",None)

        # Define parent and in_beam_element_selection_panel
        self.parent = parent
        self.in_beam_element_selection_panel : InBeamElementSelectionPanel = parent.get_in_beam_element_selection_panel()

        # Initialise the wx.ToggleButton parent class with the other keyword arguments
        super().__init__( parent = parent, label = "", **kwargs )
        
        # Set label and make sure it's deselected
        self.SetLabel( ID_MAP.get_label( str(self.toggle_button_id) ) )
        self.format_button_deselected()

        # Bind the toggle function to the button being selected
        self.Bind( wx.EVT_TOGGLEBUTTON, self.on_toggle )

        return

    ################################################################################
    # Format buttons
    def format_button_selected(self):
        """
        CustomToggleButton: format the button when it is selected
        """
        self.SetBackgroundColour( self.button_colour_selected )
        self.SetFont( wx.Font( wx.FontInfo(FONT_SIZE).Underlined() ) )
        return

    ################################################################################
    def format_button_deselected(self):
        """
        CustomToggleButton: format the button when it is deselected
        """
        # Background colour
        self.SetBackgroundColour( self.button_colour_deselected )
        self.SetFont( wx.Font( wx.FontInfo(FONT_SIZE) ) )
        return

    ################################################################################
    # What happens when you click
    def on_toggle( self, e : wx.CommandEvent ):
        """
        CustomToggleButton: state what happens when toggled

        Parameters
        ----------
        e : wx.CommandEvent
            An event that allows the function to be bound by wx
        """
        # Get the button that was toggled
        toggle : CustomToggleButton = e.GetEventObject()

        # Format the button to mark it as selected
        toggle.format_button_selected()

        # Get the colour of the button now it is selected
        select_colour = toggle.get_colour_selected()

        # Get the selection panel and the move motor panel to update their elements - NOTE that these cannot be defined earlier because the objects won't have been created yet...
        in_beam_element_selection_panel : InBeamElementSelectionPanel = self.parent.get_in_beam_element_selection_panel()
        move_motor_panel : MoveMotorPanel = in_beam_element_selection_panel.get_move_motor_panel()

        # Change selected item in panel if nothing picked
        if in_beam_element_selection_panel.get_selected_object_id() == None:
            in_beam_element_selection_panel.change_selected_item(toggle, self.toggle_button_id)
            general_button_format( move_motor_panel.get_button_move(), select_colour )
        
        # Deselect self if clicked again
        elif in_beam_element_selection_panel.get_selected_object_id() == self.toggle_button_id:
            in_beam_element_selection_panel.change_selected_item(None, None)
            general_button_format( move_motor_panel.get_button_move(), COLOUR_TARGET_DESELECTED )
        
        # Change if different target picked
        elif in_beam_element_selection_panel.get_selected_object_id() != None:
            in_beam_element_selection_panel.change_selected_item(toggle, self.toggle_button_id)
            general_button_format( move_motor_panel.get_button_move(), select_colour )

        # Update the move_motor_panel
        move_motor_panel.Refresh()

        return

    ################################################################################
    def get_colour_selected(self):
        """
        CustomToggleButton: get the colour of the button when selected
        """
        return self.button_colour_selected

    ################################################################################
    def get_colour_deselected(self):
        """
        CustomToggleButton: get the colour of the button when deselected
        """
        return self.button_colour_deselected

################################################################################
################################################################################
################################################################################
class TargetButton( CustomToggleButton ):
    """
    Class based on CustomToggleButton for targets
    """
    button_colour_selected = COLOUR_TARGET_SELECTED
    button_colour_deselected = COLOUR_TARGET_DESELECTED

################################################################################
class TuningButton( CustomToggleButton ):
    """
    Class based on CustomToggleButton for tuning elements
    """
    button_colour_selected = COLOUR_TUNING_SELECTED
    button_colour_deselected = COLOUR_TUNING_DESELECTED

################################################################################
class BeamBlockerButton( CustomToggleButton ):
    """
    Class based on CustomToggleButton for beam blocker elements
    """
    button_colour_deselected = COLOUR_BEAM_BLOCKER_DESELECTED
    button_colour_selected = COLOUR_BEAM_BLOCKER_SELECTED

################################################################################
class BeamMonitoringButton( CustomToggleButton ):
    """
    Class based on CustomToggleButton for beam-monitoring elements
    """
    button_colour_deselected = COLOUR_BEAM_MONITORING_DESELECTED
    button_colour_selected = COLOUR_BEAM_MONITORING_SELECTED

################################################################################
class AlphaButton( CustomToggleButton ):
    """
    Class based on CustomToggleButton for the alpha source
    """
    button_colour_deselected = COLOUR_ALPHA_SOURCE_FRAME_DESELECTED
    button_colour_selected = COLOUR_ALPHA_SOURCE_FRAME_SELECTED

################################################################################
###############################################################################
################################################################################

# MAIN
# def main():
#     # Process options for GUI
#     DriveSystemOptions(f'{SOURCE_DIRECTORY}/options.txt')
#     app = wx.App()
#     gui = InBeamElementSelectionWindow()
#     app.MainLoop()

# if __name__ == "__main__":
#     main()
