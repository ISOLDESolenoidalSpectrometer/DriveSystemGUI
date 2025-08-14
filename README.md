# DriveSystemGUI v2.1
A GUI to control the motor drive system inside the ISOLDE Solenoidal Spectrometer (ISS) at CERN.

## Dependencies
This has been tested using Python 3.9.21.

You will need to install:
  * numpy
  * requests
  * pyserial (NOT serial)
  * filelock
  * imageio
  * matplotlib
  * wxPython
  * psutil (if using resource monitoring)

## Usage
More information about the use of this can be found at https://twiki.cern.ch/ISS/DriveSystem. However, brief usage information can be found using
```python DriveSystem.py -h``` or ```python DriveSystem.py --help```

which produces

```
usage: DriveSystem.py [-h] [--version] [-p port] [-m] [-d] [--no-gui] [--options-file file]

DriveSystem.py is the main script for controlling the motors within the ISS experiment at CERN. It communicates with the motor box through the PySerial library, and allows the user to make easy changes through a non-scary interface. A GUI is drawn to show the precise positioning of all of the motors inside the magnet, assuming you have done the alignment correctly.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -p port, --port port  choose the serial port through which to connect. This is useful if you have replaced the motor box with a simulation
  -m, --monitor         this will print CPU, memory, and thread information periodically to the console to help diagnose memory leaks
  -d, --dark-mode       puts GUI in dark mode
  --no-gui              will just push the encoder positions to Grafana
  --options-file file   specify the options file used to control the script

Options file arguments + defaults + comments:
  SilencerLength                                            : None (in mm)
  SlitScanOptionsFilePath                                   : None
  ExperimentalMode                                          : True (disables some functionality if experiment is running to prevent accidental actions)
  GrafanaAuthentication                                     : None (path to file used to authenticate pushing to Grafana - see below)
  TargetLadderDimension                                     : 2
  BeamBlockerEnabled                                        : True
  DisabledAxes                                              : []
  TargetLadderImagePath                                     : None
  BeamBlockerImagePath                                      : None
  2DLadderLabelMapPath                                      : /home/isslocal/DriveSystemGUI/id_label_map.txt
  2DLadderEncoderPositionMapPath                            : /home/isslocal/DriveSystemGUI/id_dist_map.txt
  ArrayTipToTargetLadderDistanceAtSpecifiedEncoderPositions : None
  EncoderAxis1                                              : None
  EncoderAxis2                                              : None
  TargetLadderAxis3ReferencePoint                           : None
  TargetLadderAxis5ReferencePoint                           : None
  TargetLadderReferencePointID                              : None
  BeamBlockerAxis6ReferencePoint                            : None
  BeamBlockerAxis7ReferencePoint                            : None
  BeamBlockerReferencePointID                               : None
  TuningFrameIsTritiumFrame                                 : False
  BeamBlockerTrolleyAxisSoftLimit                           : None
  TargetLadderThickness                                     : 10.0
  TrolleyAxisNumber                                         : 1
  ArrayAxisNumber                                           : 2
  TargetHAxisNumber                                         : 3
  FCAxisNumber                                              : 4
  TargetVAxisNumber                                         : 5
  BlockerHAxisNumber                                        : 6
  BlockerVAxisNumber                                        : 7

Command line arguments + defaults
  -p, --port                          : /dev/ttyS0
  -d, --dark-mode                     : False
  -m, --monitor                       : False
  --options-file                      : /home/isslocal/DriveSystemGUI/options.txt
  --no-gui                            : False

In case of any problems, please contact Patrick MacGregor, who is almost certainly responsible for any remaining bugs.
```
## Grafana
The script is able to push the positions to Grafana. However, to prevent doxxing the ISS details, these are read from a file which has the form
```
username -> XXX
password -> XXX
url -> XXX
```
and the script will use this information to push the data to Grafana (https://iss-status.web.cern.ch)

## Mapping positions and labels
See the attached files for a list of supported in-beam elements. They can also be found in the drivesystemdetectoridmapping.py:IDMap class.

### id_label_map.txt
This file maps the IDs of various in-beam elements to their labels in the GUI, and should have the form:
```
# Comments can be used with the '#' symbol
beam_element: label
...
```

### id_dist_map.txt
This file maps the IDs of various in-beam elements to their encoder positions, and should have the form:
```
# Comments can be used with the '#' symbol
beam_element 0000 0000
....
```
Note that these are written horizontally, then vertical, *no matter what the axis mapping is*.


## Images
The svg files for the target ladder and the beam blocker are in this repo. Edit as needed using your favourite vector-graphics software for your particular setup!

