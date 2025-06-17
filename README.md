# DriveSystemGUI
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
  * prompt_toolkit (for CLI interface)


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
  --no-gui              will just push the encoder positions to Grafana, and provide a command prompt for interaction
  --options-file file   specify the options file used to control the script

Options file arguments + defaults:
  SilencerLength                      : None
  ExperimentalMode                    : True
  GrafanaAuthentication               : None
  TargetLadderDimension               : 2
  BeamBlockerEnabled                  : True
  DisabledAxes                        : []
  TargetLadderImagePath               : None
  BeamBlockerImagePath                : None
  2DLadderLabelMapPath                : /home/isslocal/DriveSystemGUI/id_label_map.txt
  2DLadderEncoderPositionMapPath      : /home/isslocal/DriveSystemGUI/id_dist_map.txt
  ArrayTipToTargetLadderDistanceAtSpecifiedEncoderPositions : None
  EncoderAxis1                        : None
  EncoderAxis2                        : None
  TargetLadderAxis3ReferencePoint     : None
  TargetLadderAxis5ReferencePoint     : None
  TargetLadderReferencePointID        : None
  BeamBlockerAxis6ReferencePoint      : None
  BeamBlockerAxis7ReferencePoint      : None
  BeamBlockerReferencePointID         : None
  SerialPort                          : /dev/ttyS0
  OptionsFile                         : /home/isslocal/DriveSystemGUI/options.txt
  DarkMode                            : False
  MonitorResources                    : False
  NoGUI                               : False

In case of any problems, please contact Patrick MacGregor, who is almost certainly responsible for any remaining bugs.
```

## Images
The svg files for the target ladder and the beam blocker are in this repo. Edit as needed using your favourite vector-graphics software for your particular setup!

