"""
Drive System Plot View
======================

This is the base class for the side view and head-on view used to visualise what is
happening inside the ISS magnet when the motors move
"""

from matplotlib import pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import wx
from abc import ABC, abstractmethod

import drivesystemoptions as dsopts
from drivesystemlib import *
from drivesystemguilib import *

class PlotView(ABC):
    """
    Base class for derived viewpoint classes. This holds the basic
    functionality of a "view" class, which is then updated by derived classes
    """
    ################################################################################
    def __init__(self, panel : wx.Window, figure_size_inches : tuple):
        """
        PlotView: initialises view in a general way

        Parameters
        ----------
        panel : wx.Window
            The parent window that owns the PlotView object
        figure_size_inches : tuple
            The size of the figure on the canvas in inches in the form (width,height)
        """
        self.panel = panel

        # Define the figure
        self.fig = plt.figure()
        self.fig.set_dpi(plot_view_dpi)
        self.fig.set_size_inches(*figure_size_inches)
        plt.rcParams.update({'font.size': 12})

        # Define a canvas
        self.canvas = FigureCanvas(self.panel, wx.ID_ANY, self.fig)

        # Axis design
        self.set_axis_limits()
        self.ax = plt.axes(xlim=(self.xmin, self.xmax), ylim=(self.ymin,self.ymax))
        self.set_axis_options()

        # Draw objects (initially)!
        self.define_constants()
        self.draw_objects([0]*NUMBER_OF_MOTOR_AXES)

    ################################################################################
    @abstractmethod
    def set_axis_limits(self):
        """
        PlotView: You MUST define xmin, xmax, ymin and ymax here.
        """
        pass
    ################################################################################
    @abstractmethod
    def set_axis_options(self):
        """
        PlotView: Here is where any further axis options are specified.
        """
        pass
    ################################################################################
    @abstractmethod
    def define_constants(self):
        """
        PlotView: define constants that won't change for the class
        """
        pass
    ################################################################################
    @abstractmethod
    def draw_objects(self, pos : list):
        """
        PlotView: All objects should be drawn in this function.

        Parameters
        ----------
        pos : list
            The positions of all of the motor axes
        """
        pass
    ################################################################################
    @abstractmethod
    def remove_objects(self):
        """
        PlotView: All objects should be removed in this function.
        """
        pass
    ################################################################################
    def update_positions(self, pos : list):
        """
        PlotView: Removes and draws objects.

        Parameters
        ----------
        pos : list
            The positions of all of the motor axes
        """
        self.remove_objects()
        self.draw_objects(pos)
    ################################################################################
    def draw_canvas(self):
        """
        PlotView: Allows external users to redraw the canvas.
        """
        self.canvas.draw()
        self.panel.Refresh()
        self.panel.Update()
