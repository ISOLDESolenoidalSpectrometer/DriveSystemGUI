"""
Drive system detector ID mapping
================================

This module contains all necessary code for labelling all the different elements
inside the motor system
"""
from typing import Union

class TargetID:
    """
    A class that holds information about a target frame based on its frame number, 
    and position in a 2D (or 1D) grid.

    Attributes
    ----------
    _frame : int
        The frame number (starting from 0)
    _targetX : int
        The position of the target horizontally as measured from the left column
        (starting from 0)
    _targetY : int
        The position of the target vertically as measured from the top row
        (starting from 0)
    """
    ################################################################################
    def __init__(self, **kwargs) -> None:
        """
        TargetID: Initialise based on keyword arguments

        Parameters
        ----------
        kwargs : various
            Keyword arguments for initialisation. This class is looking for:
            - "frame" - the frame number of the target.
            - "targetX" - the X position of the target.
            - "targetY" - the Y position of the target.
        """
        self._frame = kwargs.get("frame")
        self._targetX = kwargs.get("targetX")
        self._targetY = kwargs.get("targetY")
        return

    ################################################################################
    # Test if valid target ID
    @classmethod
    def is_valid(cls, mystr : str) -> bool:
        """
        TargetID: test if a string matches the TargetID pattern

        Parameters
        ----------
        mystr : str
            The string to be tested

        Returns
        -------
        result : bool
            True if mystr is a valid ID, false otherwise
        """
        # Check if None
        if mystr == None:
            return False
        
        # Split the string
        s = mystr.split(".")

        # Check that it has the right length
        if len(s) != 3:
            return False
        
        # Check each element is a number
        for i in range(0,3):
            if not s[i].isdigit():
                return False

        return True
    
    ################################################################################
    @classmethod
    def get_list_of_id_numbers_from_string(cls, mystr : str) -> Union[list[str], None]:
        """
        TargetID: returns the list of elements based on a string form of TargetID

        Parameters
        ----------
        mystr : str
            The proposed TargetID
        
        Returns
        -------
        mylist : list
            A list of the form [frame, targetX, targetY] if valid, None otherwise
        """
        # Test if valid
        if cls.is_valid(mystr):
            return mystr.split(".")
        
        return None

    ################################################################################

    @classmethod
    def from_str(cls, mystr : str):
        """
        TargetID: constructs a TargetID object from a string

        Parameters
        ----------
        mystr : str
            The proposed TargetID

        Returns
        -------
        target_id : TargetID
            A valid TargetID if mystr is valid, None otherwise
        """
        string_is_valid, arr = cls.is_valid(mystr)
        if string_is_valid:
            return cls( frame = arr[0], targetX = arr[1], targetY = arr[2] )
        return None
    ################################################################################
    def set_frame( self, frame : int ) -> None:
        """
        TargetID: basic setter for the TargetID object - frame

        Parameters
        ----------
        frame : int
            The frame number
        """
        self._frame = frame
        return
    ################################################################################
    def set_targetX( self, x : int ) -> None:
        """
        TargetID: basic setter for the TargetID object - targetX

        Parameters
        ----------
        x : int
            The x position in the frame
        """
        self._targetX = x
        return
    ################################################################################
    def set_targetY( self, y : int ) -> None:
        """
        TargetID: basic setter for the TargetID object - targetY

        Parameters
        ----------
        y : int
            The y position in the frame
        """
        self._targetY = y
        return
    ################################################################################
    def __str__(self) -> str:
        """
        TargetID: a method for getting the string form of the TargetID
        """
        return f"{self._frame}.{self._targetX}.{self._targetY}"


################################################################################
################################################################################
################################################################################
class IDMap:
    """
    A singleton class that reads the inputted labels and axis positions, and then
    stores them so that it can be used by the InBeamElementSelectionWindow to
    move the motors

    Attributes
    ----------
    init : bool
        Determines whether the object has been initialised already
    """
    # Singleton properties
    instance = None # This is the single instance
    init = False    # This determines whether the object has already been initialised

    # CONSTANTS FOR DEFAULTS
    # DEFAULTS
    # IDs + Labels for buttons
    HORZ_SLIT_ID = "horz_slit"
    HORZ_SLIT_LABEL = "Horizontal slit"
    VERT_SLIT_ID = "vert_slit"
    VERT_SLIT_LABEL = "Vertical slit"
    SMALL_APERTURE_ID = "small_aperture"
    SMALL_APERTURE_LABEL = "3 mm aperture"
    LARGE_APERTURE_ID = "large_aperture"
    LARGE_APERTURE_LABEL = "10 mm aperture"

    BEAM_BLOCKER_SMALL_ID = "bb.small"
    BEAM_BLOCKER_SMALL_LABEL = "BB: 6 mm"
    BEAM_BLOCKER_MEDIUM_ID = "bb.medium"
    BEAM_BLOCKER_MEDIUM_LABEL = "BB: 10 mm"
    BEAM_BLOCKER_LARGE_ID = "bb.large"
    BEAM_BLOCKER_LARGE_LABEL = "BB: 20 mm"
    BEAM_BLOCKER_CLEAR_ID = "bb.clear"
    BEAM_BLOCKER_CLEAR_LABEL = "No BB"

    BEAM_MONITORING_FC_ID = "bm.fc"
    BEAM_MONITORING_FC_LABEL = "Faraday cup"
    BEAM_MONITORING_MIDDLE_ID = "bm.mid"
    BEAM_MONITORING_MIDDLE_LABEL = "Middle"
    BEAM_MONITORING_ZD_ID = "bm.zd"
    BEAM_MONITORING_ZD_LABEL = "Zero degree"

    ALPHA_SOURCE_ID = "alpha"
    ALPHA_SOURCE_LABEL = "α"

    # Store a list of IDs
    ID_LIST_LADDER = [
        SMALL_APERTURE_ID, LARGE_APERTURE_ID, HORZ_SLIT_ID, VERT_SLIT_ID, ALPHA_SOURCE_ID
    ]
    ID_LIST = ID_LIST_LADDER + [ 
        BEAM_BLOCKER_SMALL_ID, BEAM_BLOCKER_MEDIUM_ID, BEAM_BLOCKER_LARGE_ID, BEAM_BLOCKER_CLEAR_ID,
        BEAM_MONITORING_FC_ID, BEAM_MONITORING_MIDDLE_ID, BEAM_MONITORING_ZD_ID
    ]

    # Store a list of labels
    LABEL_LIST = [
        SMALL_APERTURE_LABEL, LARGE_APERTURE_LABEL, HORZ_SLIT_LABEL, VERT_SLIT_LABEL, ALPHA_SOURCE_LABEL,
        BEAM_BLOCKER_SMALL_LABEL, BEAM_BLOCKER_MEDIUM_LABEL, BEAM_BLOCKER_LARGE_LABEL, BEAM_BLOCKER_CLEAR_LABEL,
        BEAM_MONITORING_FC_LABEL, BEAM_MONITORING_MIDDLE_LABEL, BEAM_MONITORING_ZD_LABEL
    ]

    ################################################################################
    def __new__(cls, *args, **kwargs):
        """
        IDMap: Returns singleton or creates new one if uninitialised
        """
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    ################################################################################
    def __init__(self, filename : str):
        """
        IDMap: Creates the IDMap object by creating its internal dictionary and then
        filling it

        Parameters
        ----------
        filename : str
            The location of the ID map file
        """
        # Do nothing if already initialised
        if self.init:
            return
        
        # Specify that it's been initialised
        self.init = True
        super().__init__()
        
        # Initialise dictionary
        self.dict = {}

        # Read file + populate dictionary
        self.process_file_data(filename)

    ################################################################################
    def process_file_data(self, filename : str) -> None:
        """
        IDMap: reads in data from the file and assigns the label based on what is
        in the file
        
        Parameters
        ----------
        filename : str
            The file path for the label file, which should have lines of the form
            '[ID] : [LABEL]'
            where [ID] is the ID for the element that needs to be labelled, and
            [LABEL] is the label for the element
        """
        # See if file exists
        try:
            # Open the file
            with open(filename, "r") as myfile:
                # Line counter initialised
                line_ctr = 0

                # Loop over lines and process
                for line in myfile:
                    # Increment line counter
                    line_ctr += 1
                    
                    # Strip whitespace at beginning and end + newline character
                    mod_line = line.rstrip("\n").rstrip().lstrip()
                    
                    # Skip empty lines
                    if len(mod_line) == 0:
                        continue
                    
                    # Skip lines beginning with "#""
                    if mod_line[0] == "#":
                        continue

                    # Split line at first colon
                    splitline = mod_line.split( ":", maxsplit = 1 )

                    # Skip lines that don't have colon
                    if len(splitline) < 2:
                        print(f"ID-label map WARNING: line {line_ctr} ignored as no key-value pair found: \"{mod_line}\"")
                        continue

                    # Strip whitespace at beginning and end of strings (if space around colon)
                    splitline = [ x.strip() for x in splitline ]

                    # Add values to dictionary if in ID list
                    key = splitline[0]
                    value = splitline[1]

                    # Process if target ID or in ID list
                    if TargetID.is_valid(key) or key in self.ID_LIST:
                        if key in self.dict and key not in self.ID_LIST:
                            print(f"Warning: overwriting previous definition of target ID \"{key}\" from {self.dict[key]} to {value}")
                        self.dict[key] = value
                    else:
                        print(f"Unrecognised key in line{line_ctr}: \"{key}\"")

                    # Define remaining bits
                    for i in range(0,len(self.ID_LIST)):
                        if self.ID_LIST[i] not in self.dict:
                            self.dict[self.ID_LIST[i]] = self.LABEL_LIST[i]
        # Couldn't open file
        except FileNotFoundError:
            print(f"Couldn't open file {filename}. Using defaults")
        
        return


    ################################################################################
    def get_label(self, id : str) -> str:
        """
        IDMap: simple getter for the label

        Returns
        -------
        label : str
            The desired label. If it cannot find the element with ID, it will just
            return the ID
        """
        return self.dict.get( id, id )
    
    ################################################################################
    @classmethod
    def get_instance(cls):
        """
        IDMap: returns the single instance of the class
        """
        if cls.instance == None:
            cls()
        return cls.instance
    
    
    
    