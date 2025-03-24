class TargetID:
    def __init__(self, **kwargs):
        self.frame = kwargs.get("frame")
        self.targetX = kwargs.get("targetX")
        self.targetY = kwargs.get("targetY")


    # Test if valid target ID
    @classmethod
    def is_valid(cls,mystr):
        # Split the string
        s = mystr.split(".")

        # Check that it has the right length, and that each element is a number
        if len(s) != 3:
            return False
        for i in range(0,3):
            if not s[i].isdigit():
                return False

        return True
    
    # Split the string into individual components that resembles target ID string
    @classmethod
    def get_list_of_id_numbers_from_string(cls, mystr):
        # Test if valid
        if cls.is_valid(mystr):
            return mystr.split(".")
        
        return None

    # Construct from string
    @classmethod
    def from_str(cls, mystr):
        string_is_valid, arr = cls.is_valid(mystr)
        if string_is_valid:
            return cls( frame = arr[0], targetX = arr[1], targetY = arr[2] )
        return None
    
    def set_frame( self, frame ):
        self.frame = frame

    def set_targetX( self, x ):
        self.targetX = x
    
    def set_targetY( self, y ):
        self.targetY = y

    def __str__(self):
        return f"{self.frame}.{self.targetX}.{self.targetY}"


class IDMap():
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

    ID_LIST = [ 
        SMALL_APERTURE_ID, LARGE_APERTURE_ID, HORZ_SLIT_ID, VERT_SLIT_ID, 
        BEAM_BLOCKER_SMALL_ID, BEAM_BLOCKER_MEDIUM_ID, BEAM_BLOCKER_LARGE_ID, BEAM_BLOCKER_CLEAR_ID,
        BEAM_MONITORING_FC_ID, BEAM_MONITORING_MIDDLE_ID, BEAM_MONITORING_ZD_ID
    ]
    LABEL_LIST = [
        SMALL_APERTURE_LABEL, LARGE_APERTURE_LABEL, HORZ_SLIT_LABEL, VERT_SLIT_LABEL, 
        BEAM_BLOCKER_SMALL_LABEL, BEAM_BLOCKER_MEDIUM_LABEL, BEAM_BLOCKER_LARGE_LABEL, BEAM_BLOCKER_CLEAR_LABEL,
        BEAM_MONITORING_FC_LABEL, BEAM_MONITORING_MIDDLE_LABEL, BEAM_MONITORING_ZD_LABEL
    ]

    def __init__(self, filename):
        # Initialise dictionary
        self.dict = {}

        # Read file + populate dictionary
        self.process_file_data(filename)


    def process_file_data(self, filename):
        # Try to open file
        myfile = open(filename, "r")
        line_ctr = 0

        if not myfile.closed:
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

                # Strip whitespace at end of first element and beginning of second element (if space around colon)
                splitline[0].rstrip()
                splitline[1].lstrip()

                # Add values to dictionary if in ID list
                key = splitline[0]
                value = splitline[1]

                # Process if target ID or in ID list
                if TargetID.is_valid(key) or key in self.ID_LIST:
                    if key in self.dict:
                        print(f"Warning: overwriting previous definition of target ID \"{key}\" from {self.dict[key]} to {value}")
                    self.dict[key] = value
                else:
                    print(f"Unrecognised key in line{line_ctr}: \"{key}\"")

                # Define remaining bits
                for i in range(0,len(self.ID_LIST)):
                    if self.ID_LIST[i] not in self.dict:
                        self.dict[self.ID_LIST[i]] = self.LABEL_LIST[i]
        else:
            print("Couldn't open file. Using defaults")

        # Close the file
        myfile.close()

    def get_label(self, id):
        return self.dict.get( id, id )
    
    