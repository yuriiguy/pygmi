# -----------------------------------------------------------------------------
# Name:        ginterp.py (part of PyGMI)
#
# Author:      Patrick Cole
# E-Mail:      pcole@geoscience.org.za
#
# Copyright:   (c) 2013 Council for Geoscience
# Licence:     GPL-3.0
#
# This file is part of PyGMI
#
# PyGMI is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyGMI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
"""
Plot Raster Data.

This is the raster data interpretation module.  This module allows for the
display of raster data in a variety of modes, as well as the export of that
display to GeoTIFF format.

Currently the following is supported
 * Pseudo Colour - data mapped to a colour map
 * Contours with solid contours
 * RGB ternary images
 * CMYK ternary images
 * Sun shaded or hill shaded images

It can be very effectively used in conjunction with a GIS package which
supports GeoTIFF files.
"""

import os
import sys
import copy
from math import cos
import numpy as np
from PyQt5 import QtWidgets, QtCore
from scipy import ndimage
from matplotlib.figure import Figure
from matplotlib import gridspec
import matplotlib.colors as mcolors
import matplotlib.colorbar as mcolorbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.pyplot import colormaps
from matplotlib.colors import ListedColormap

from pygmi.misc import BasicModule
from pygmi.raster import iodefs, dataprep
from pygmi import menu_default
from pygmi.raster.modest_image import imshow
from pygmi.raster.misc import currentshader, histcomp, histeq, img2rgb
from pygmi.raster.misc import norm2, norm255, lstack


copper = np.array([[255., 236., 184.],
                   [255., 230., 172.],
                   [255., 225., 164.],
                   [255., 221., 158.],
                   [255., 218., 153.],
                   [254., 216., 149.],
                   [253., 213., 146.],
                   [252., 212., 143.],
                   [251., 210., 140.],
                   [250., 208., 138.],
                   [249., 206., 136.],
                   [248., 205., 133.],
                   [247., 203., 131.],
                   [246., 202., 129.],
                   [245., 201., 128.],
                   [245., 199., 126.],
                   [244., 198., 124.],
                   [243., 197., 122.],
                   [242., 196., 121.],
                   [241., 195., 120.],
                   [240., 194., 118.],
                   [239., 193., 117.],
                   [238., 192., 115.],
                   [238., 191., 114.],
                   [237., 190., 113.],
                   [236., 189., 112.],
                   [235., 188., 110.],
                   [234., 187., 109.],
                   [234., 186., 108.],
                   [233., 185., 107.],
                   [232., 184., 106.],
                   [231., 183., 105.],
                   [230., 182., 104.],
                   [230., 181., 103.],
                   [229., 181., 102.],
                   [228., 180., 101.],
                   [227., 179., 100.],
                   [227., 178.,  99.],
                   [226., 177.,  98.],
                   [225., 177.,  97.],
                   [224., 176.,  96.],
                   [224., 175.,  95.],
                   [223., 174.,  94.],
                   [222., 174.,  93.],
                   [222., 173.,  93.],
                   [221., 172.,  92.],
                   [220., 171.,  91.],
                   [220., 171.,  90.],
                   [219., 170.,  89.],
                   [218., 169.,  88.],
                   [217., 168.,  88.],
                   [217., 168.,  87.],
                   [216., 167.,  86.],
                   [215., 166.,  85.],
                   [215., 166.,  85.],
                   [214., 165.,  84.],
                   [213., 164.,  83.],
                   [213., 164.,  82.],
                   [212., 163.,  82.],
                   [211., 162.,  81.],
                   [211., 162.,  80.],
                   [210., 161.,  80.],
                   [210., 160.,  79.],
                   [209., 160.,  78.],
                   [208., 159.,  77.],
                   [208., 158.,  77.],
                   [207., 158.,  76.],
                   [206., 157.,  75.],
                   [206., 156.,  75.],
                   [205., 156.,  74.],
                   [204., 155.,  74.],
                   [204., 154.,  73.],
                   [203., 154.,  72.],
                   [203., 153.,  72.],
                   [202., 153.,  71.],
                   [201., 152.,  70.],
                   [201., 151.,  70.],
                   [200., 151.,  69.],
                   [199., 150.,  68.],
                   [199., 149.,  68.],
                   [198., 149.,  67.],
                   [197., 148.,  67.],
                   [197., 148.,  66.],
                   [196., 147.,  66.],
                   [196., 147.,  65.],
                   [195., 146.,  64.],
                   [194., 145.,  64.],
                   [194., 145.,  63.],
                   [193., 144.,  63.],
                   [192., 144.,  62.],
                   [192., 143.,  62.],
                   [191., 142.,  61.],
                   [190., 142.,  60.],
                   [190., 141.,  60.],
                   [189., 141.,  59.],
                   [189., 140.,  59.],
                   [188., 139.,  58.],
                   [187., 139.,  58.],
                   [187., 138.,  57.],
                   [186., 138.,  57.],
                   [186., 137.,  56.],
                   [185., 137.,  56.],
                   [184., 136.,  55.],
                   [184., 136.,  55.],
                   [183., 135.,  54.],
                   [182., 134.,  53.],
                   [182., 134.,  53.],
                   [181., 133.,  52.],
                   [181., 133.,  52.],
                   [180., 132.,  51.],
                   [179., 132.,  51.],
                   [179., 131.,  50.],
                   [178., 130.,  50.],
                   [177., 130.,  49.],
                   [177., 129.,  49.],
                   [176., 129.,  49.],
                   [176., 128.,  48.],
                   [175., 128.,  48.],
                   [174., 127.,  47.],
                   [174., 127.,  47.],
                   [173., 126.,  46.],
                   [172., 125.,  46.],
                   [172., 125.,  45.],
                   [171., 124.,  45.],
                   [170., 124.,  44.],
                   [170., 123.,  44.],
                   [169., 123.,  43.],
                   [169., 122.,  43.],
                   [168., 121.,  42.],
                   [167., 121.,  42.],
                   [167., 120.,  41.],
                   [166., 120.,  41.],
                   [165., 119.,  41.],
                   [165., 119.,  40.],
                   [164., 118.,  40.],
                   [163., 117.,  39.],
                   [163., 117.,  39.],
                   [162., 116.,  38.],
                   [161., 116.,  38.],
                   [161., 115.,  37.],
                   [160., 115.,  37.],
                   [159., 114.,  37.],
                   [159., 113.,  36.],
                   [158., 113.,  36.],
                   [157., 112.,  35.],
                   [157., 112.,  35.],
                   [156., 111.,  34.],
                   [155., 110.,  34.],
                   [155., 110.,  34.],
                   [154., 109.,  33.],
                   [153., 109.,  33.],
                   [152., 108.,  32.],
                   [152., 107.,  32.],
                   [151., 107.,  31.],
                   [150., 106.,  31.],
                   [150., 106.,  31.],
                   [149., 105.,  30.],
                   [148., 104.,  30.],
                   [147., 104.,  29.],
                   [147., 103.,  29.],
                   [146., 102.,  28.],
                   [145., 102.,  28.],
                   [144., 101.,  28.],
                   [144., 101.,  27.],
                   [143., 100.,  27.],
                   [142.,  99.,  26.],
                   [141.,  99.,  26.],
                   [140.,  98.,  26.],
                   [140.,  97.,  25.],
                   [139.,  97.,  25.],
                   [138.,  96.,  25.],
                   [137.,  95.,  24.],
                   [136.,  95.,  24.],
                   [136.,  94.,  23.],
                   [135.,  93.,  23.],
                   [134.,  93.,  23.],
                   [133.,  92.,  22.],
                   [132.,  91.,  22.],
                   [131.,  90.,  21.],
                   [131.,  90.,  21.],
                   [130.,  89.,  21.],
                   [129.,  88.,  20.],
                   [128.,  88.,  20.],
                   [127.,  87.,  20.],
                   [126.,  86.,  19.],
                   [125.,  85.,  19.],
                   [124.,  85.,  19.],
                   [123.,  84.,  18.],
                   [123.,  83.,  18.],
                   [122.,  82.,  17.],
                   [121.,  82.,  17.],
                   [120.,  81.,  17.],
                   [119.,  80.,  16.],
                   [118.,  79.,  16.],
                   [117.,  79.,  16.],
                   [116.,  78.,  15.],
                   [115.,  77.,  15.],
                   [114.,  76.,  15.],
                   [113.,  75.,  14.],
                   [112.,  75.,  14.],
                   [111.,  74.,  14.],
                   [110.,  73.,  13.],
                   [109.,  72.,  13.],
                   [108.,  71.,  12.],
                   [107.,  70.,  12.],
                   [106.,  69.,  12.],
                   [104.,  68.,  11.],
                   [103.,  68.,  11.],
                   [102.,  67.,  11.],
                   [101.,  66.,  10.],
                   [100.,  65.,  10.],
                   [99.,  64.,  10.],
                   [97.,  63.,   9.],
                   [96.,  62.,   9.],
                   [95.,  61.,   9.],
                   [94.,  60.,   8.],
                   [92.,  59.,   8.],
                   [91.,  58.,   8.],
                   [90.,  58.,   7.],
                   [89.,  57.,   7.],
                   [87.,  56.,   7.],
                   [86.,  55.,   6.],
                   [85.,  54.,   6.],
                   [83.,  53.,   6.],
                   [82.,  52.,   5.],
                   [80.,  51.,   5.],
                   [79.,  49.,   5.],
                   [77.,  48.,   4.],
                   [76.,  47.,   4.],
                   [74.,  46.,   4.],
                   [72.,  45.,   3.],
                   [71.,  43.,   3.],
                   [69.,  42.,   3.],
                   [67.,  41.,   2.],
                   [66.,  40.,   2.],
                   [64.,  38.,   2.],
                   [62.,  37.,   1.],
                   [60.,  35.,   1.],
                   [58.,  34.,   1.],
                   [56.,  32.,   0.],
                   [54.,  31.,   0.],
                   [52.,  29.,   0.],
                   [50.,  28.,   0.],
                   [47.,  26.,   0.],
                   [45.,  24.,   0.],
                   [43.,  22.,   0.],
                   [40.,  20.,   0.],
                   [37.,  19.,   0.],
                   [34.,  17.,   0.],
                   [31.,  15.,   0.],
                   [28.,  13.,   0.],
                   [24.,  10.,   0.],
                   [21.,   8.,   0.],
                   [16.,   6.,   0.],
                   [11.,   3.,   0.],
                   [0.,   0.,   0.]])


class MyMplCanvas(FigureCanvasQTAgg):
    """
    Canvas for the actual plot.

    Attributes
    ----------
    htype : str
        string indicating the histogram stretch to apply to the data
    hstype : str
        string indicating the histogram stretch to apply to the sun data
    cbar : matplotlib colour map
        colour map to be used for pseudo colour bars
    data : list of PyGMI Data
        list of PyGMI raster data objects - used for colour images
    sdata : list of PyGMI Data
        list of PyGMI raster data objects - used for shaded images
    gmode : str
        string containing the graphics mode - Contour, Ternary, Sunshade,
        Single Colour Map.
    argb : list
        list of matplotlib subplots. There are up to three.
    hhist : list
        matplotlib hist associated with argb
    hband: list
        list of strings containing the band names to be used.
    htxt : list
        list of strings associated with hhist, denoting a raster value (where
        mouse is currently hovering over on image)
    image : imshow
        imshow instance - this is the primary way of displaying an image.
    cnt : matplotlib contour
        contour instance - used for the contour image
    cntf : matplotlib contourf
        contourf instance - used for the contour image
    background : matplotlib bounding box
        image bounding box - used in blitting
    bbox_hist_red :  matplotlib bounding box
        red histogram bounding box
    bbox_hist_green :  matplotlib bounding box
        green histogram bounding box
    bbox_hist_blue :  matplotlib bounding box
        blue histogram bounding box
    axes : matplotlib axes
        axes for the plot
    pinit : numpy array
        calculated with aspect - used in sunshading
    qinit : numpy array
        calculated with aspect - used in sunshading
    phi : float
        azimuth (sunshading)
    theta : float
        sun elevation (sunshading)
    cell : float
        between 1 and 100 - controls sunshade detail.
    alpha : float
        how much incident light is reflected (0 to 1)
    kval : float
        k value for CMYK mode
    """

    def __init__(self, parent=None):
        fig = Figure()
        super().__init__(fig)

        # figure stuff
        self.htype = 'Linear'
        self.hstype = 'Linear'
        self.cbar = colormaps['jet']
        self.newcmp = self.cbar
        self.fullhist = False
        self.data = []
        self.sdata = []
        self.gmode = None
        self.argb = [None, None, None]
        self.bgrgb = [None, None, None]
        self.hhist = [[], [], []]
        self.hband = [None, None, None, None]
        self.htxt = [None, None, None]
        self.image = None
        self.cnt = None
        self.cntf = None
        self.background = None
        self.bbox_hist_red = None
        self.bbox_hist_green = None
        self.bbox_hist_blue = None
        self.shade = False
        self.ccbar = None
        self.clippercu = {}
        self.clippercl = {}
        self.flagresize = False
        self.clipvalu = [None, None, None]
        self.clipvall = [None, None, None]

        gspc = gridspec.GridSpec(3, 4)
        self.axes = fig.add_subplot(gspc[0:, 1:])
        self.axes.xaxis.set_visible(False)
        self.axes.yaxis.set_visible(False)

        for i in range(3):
            self.argb[i] = fig.add_subplot(gspc[i, 0])
            self.argb[i].xaxis.set_visible(False)
            self.argb[i].yaxis.set_visible(False)
            self.argb[i].autoscale(False)

        fig.subplots_adjust(bottom=0.05)
        fig.subplots_adjust(top=.95)
        fig.subplots_adjust(left=0.05)
        fig.subplots_adjust(right=.95)
        fig.subplots_adjust(wspace=0.05)
        fig.subplots_adjust(hspace=0.05)

        self.setParent(parent)

        FigureCanvasQTAgg.setSizePolicy(self,
                                        QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)

        self.figure.canvas.mpl_connect('motion_notify_event', self.move)
        self.cid = self.figure.canvas.mpl_connect('resize_event', self.revent)

        # sun shading stuff
        self.pinit = None
        self.qinit = None
        self.phi = -np.pi/4.
        self.theta = np.pi/4.
        self.cell = 100.
        self.alpha = .0

        # cmyk stuff
        self.kval = 0.01

    def revent(self, event):
        """
        Resize event.

        Parameters
        ----------
        event : matplotlib.backend_bases.ResizeEvent
            Resize event.

        Returns
        -------
        None.

        """
        self.flagresize = True

    def init_graph(self):
        """
        Initialize the graph.

        Returns
        -------
        None.

        """
        if self.ccbar is not None:
            self.ccbar.remove()
            self.ccbar = None

        self.figure.canvas.mpl_disconnect(self.cid)

        self.axes.clear()
        for i in range(3):
            self.argb[i].clear()

        x_1, x_2, y_1, y_2 = self.data[0].extent

        self.axes.set_xlim(x_1, x_2)
        self.axes.set_ylim(y_1, y_2)
        self.axes.set_aspect('equal')

        self.figure.canvas.draw()

        self.bgrgb[0] = self.figure.canvas.copy_from_bbox(self.argb[0].bbox)
        self.bgrgb[1] = self.figure.canvas.copy_from_bbox(self.argb[1].bbox)
        self.bgrgb[2] = self.figure.canvas.copy_from_bbox(self.argb[2].bbox)

        self.background = self.figure.canvas.copy_from_bbox(self.axes.bbox)

        tmp = np.ma.array([[np.nan]])
        self.image = imshow(self.axes, tmp, origin='upper',
                            extent=(x_1, x_2, y_1, y_2))

        # This line prevents imshow from generating colour values on the
        # toolbar
        self.image.format_cursor_data = lambda x: ""
        self.update_graph()

        self.cid = self.figure.canvas.mpl_connect('resize_event', self.revent)

    def move(self, event):
        """
        Mouse is moving over canvas.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            Mouse event.

        Returns
        -------
        None.

        """
        if not self.data or self.gmode == 'Contour':
            return

        if event.inaxes == self.axes:
            if self.flagresize is True:
                self.flagresize = False

                self.update_graph()

            zval = [-999, -999, -999]
            for i in self.data:
                itlx = i.extent[0]
                itly = i.extent[-1]
                for j in range(3):
                    if i.dataid == self.hband[j]:
                        col = int((event.xdata - itlx)/i.xdim)
                        row = int((itly - event.ydata)/i.ydim)
                        zval[j] = i.data[row, col]

            if self.gmode == 'Single Colour Map':
                bnum = self.update_hist_single(zval[0])
                self.figure.canvas.restore_region(self.bbox_hist_red)
                self.argb[0].draw_artist(self.htxt[0])
                self.argb[0].draw_artist(self.hhist[0][2][bnum])
                self.argb[0].draw_artist(self.clipvalu[0])
                self.argb[0].draw_artist(self.clipvall[0])
                self.figure.canvas.update()

            if 'Ternary' in self.gmode:
                bnum = self.update_hist_rgb(zval)
                self.figure.canvas.restore_region(self.bbox_hist_red)
                self.figure.canvas.restore_region(self.bbox_hist_green)
                self.figure.canvas.restore_region(self.bbox_hist_blue)

                for j in range(3):
                    self.argb[j].draw_artist(self.htxt[j])
                    self.argb[j].draw_artist(self.hhist[j][2][bnum[j]])
                    if self.clipvalu[j] is not None:
                        self.argb[j].draw_artist(self.clipvalu[j])
                    if self.clipvall[j] is not None:
                        self.argb[j].draw_artist(self.clipvall[j])

                self.figure.canvas.update()

    def update_contour(self):
        """
        Update contours.

        Returns
        -------
        None.

        """
        x1, x2, y1, y2 = self.data[0].extent
        self.image.set_visible(False)
        clippercu = self.clippercu[self.hband[0]]
        clippercl = self.clippercl[self.hband[0]]

        for i in self.data:
            if i.dataid == self.hband[0]:
                dat = i.data.copy()

        if self.htype == 'Histogram Equalization':
            dat = histeq(dat)
        elif clippercl > 0. or clippercu > 0.:
            dat, _, _ = histcomp(dat, perc=clippercl,
                                 uperc=clippercu)

        xdim = (x2-x1)/dat.data.shape[1]/2
        ydim = (y2-y1)/dat.data.shape[0]/2
        xi = np.linspace(x1+xdim, x2-xdim, dat.data.shape[1])
        yi = np.linspace(y2-ydim, y1+ydim, dat.data.shape[0])

        self.cnt = self.axes.contour(xi, yi, dat, extent=(x1, x2, y1, y2),
                                     linewidths=1, colors='k',
                                     linestyles='solid')
        self.cntf = self.axes.contourf(xi, yi, dat, extent=(x1, x2, y1, y2),
                                       cmap=self.cbar)

        self.ccbar = self.figure.colorbar(self.cntf, ax=self.axes)
        self.figure.canvas.draw()

    def update_graph(self):
        """
        Update plot.

        Returns
        -------
        None.

        """
        if self.ccbar is not None:
            self.ccbar.remove()
            self.ccbar = None

        if not self.data or self.gmode is None:
            return

        for i in range(3):
            self.argb[i].clear()

        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

        self.bgrgb[0] = self.figure.canvas.copy_from_bbox(self.argb[0].bbox)
        self.bgrgb[1] = self.figure.canvas.copy_from_bbox(self.argb[1].bbox)
        self.bgrgb[2] = self.figure.canvas.copy_from_bbox(self.argb[2].bbox)

        if self.gmode == 'Single Colour Map':
            self.update_single_color_map()

        if self.gmode == 'Contour':
            self.update_contour()

        if 'Ternary' in self.gmode:
            self.update_rgb()

        if self.gmode == 'Sunshade':
            self.update_shade_plot()

    def update_hist_rgb(self, zval):
        """
        Update the rgb histograms.

        Parameters
        ----------
        zval : numpy array
            Data values.

        Returns
        -------
        bnum : list
            Bin numbers.

        """
        hcol = ['r', 'g', 'b']
        if 'CMY' in self.gmode:
            hcol = ['c', 'm', 'y']

        hst = self.hhist
        bnum = []

        for i in range(3):
            bins, patches = hst[i][1:]
            for j in patches:
                j.set_color(hcol[i])

            if np.ma.is_masked(zval[i]) is True or zval[i] is None:
                bnum.append(0)
                self.update_hist_text(self.htxt[i], None)
                continue

            binnum = (bins < zval[i]).sum()-1

            if (-1 < binnum < len(patches) and
                    self.htype != 'Histogram Equalization'):
                patches[binnum].set_color('k')
                bnum.append(binnum)
            else:
                bnum.append(0)
            self.update_hist_text(self.htxt[i], zval[i])
        return bnum

    def update_hist_single(self, zval=None, hno=0):
        """
        Update the colour on a single histogram.

        Parameters
        ----------
        zval : float
            Data value.
        hno : int, optional
            Histogram number. The default is 0.

        Returns
        -------
        binnum : int
            Number of bins.

        """
        hst = self.hhist[hno]
        bins, patches = hst[1:]
        binave = np.arange(0, 1, 1/(bins.size-2))

        if hno == 0:
            bincol = self.newcmp(binave)
        else:
            bincol = colormaps['gray'](binave)

        for j, patchesj in enumerate(patches):
            patchesj.set_color(bincol[j])

        # This section draws the black line.
        if zval is None or np.ma.is_masked(zval) is True:
            self.update_hist_text(self.htxt[hno], None)
            return 0

        binnum = (bins < zval).sum()-1
        if binnum < 0 or binnum >= len(patches):
            self.update_hist_text(self.htxt[hno], zval)
            return 0

        self.update_hist_text(self.htxt[hno], zval)
        if self.htype == 'Histogram Equalization':
            return 0
        patches[binnum].set_color('k')

        return binnum

    def update_hist_text(self, hst, zval):
        """
        Update the value on the histogram.

        Parameters
        ----------
        hst : histogram
            Histogram.
        zval : float
            Data value.

        Returns
        -------
        None.

        """
        xmin, xmax, ymin, ymax = hst.axes.axis()
        xnew = 0.95*(xmax-xmin)+xmin
        ynew = 0.95*(ymax-ymin)+ymin
        hst.set_position((xnew, ynew))

        if zval is None:
            hst.set_text('')
        else:
            hst.set_text(f'{zval:.4f}')

    def update_rgb(self):
        """
        Update the RGB Ternary Map.

        Returns
        -------
        None.

        """
        self.clipvalu = [None, None, None]
        self.clipvall = [None, None, None]

        self.image.rgbmode = self.gmode
        self.image.kval = self.kval

        sun = None
        dat = [None, None, None]
        for i in self.data:
            if i.dataid == self.hband[3]:
                sun = i.data
            for j in range(3):
                if i.dataid == self.hband[j]:
                    dat[j] = i.data

        self.image.set_shade(self.shade, self.cell, self.theta, self.phi,
                             self.alpha)

        if self.shade is True:
            dat.append(sun)

        dat = np.ma.array(dat)

        dat = np.moveaxis(dat, 0, -1)

        self.image.set_data(dat)
        self.image._scale_to_res()

        if self.image._A.ndim == 3:
            dat = self.image._A
        else:
            dat = self.image._A[:, :, :3]

        lclip = [0, 0, 0]
        uclip = [0, 0, 0]

        if self.htype == 'Histogram Equalization':
            self.image.dohisteq = True
        else:
            self.image.dohisteq = False
            clippercu = self.clippercu[self.hband[0]]
            clippercl = self.clippercl[self.hband[0]]
            lclip[0], uclip[0] = np.percentile(dat[:, :, 0].compressed(),
                                               [clippercl, 100-clippercu])
            clippercu = self.clippercu[self.hband[1]]
            clippercl = self.clippercl[self.hband[1]]
            lclip[1], uclip[1] = np.percentile(dat[:, :, 1].compressed(),
                                               [clippercl, 100-clippercu])
            clippercu = self.clippercu[self.hband[2]]
            clippercl = self.clippercl[self.hband[2]]
            lclip[2], uclip[2] = np.percentile(dat[:, :, 2].compressed(),
                                               [clippercl, 100-clippercu])

            self.image.rgbclip = [[lclip[0], uclip[0]],
                                  [lclip[1], uclip[1]],
                                  [lclip[2], uclip[2]]]

        for i in range(3):
            hdata = dat[:, :, i]
            clippercu = self.clippercu[self.hband[i]]
            clippercl = self.clippercl[self.hband[i]]

            if ((clippercu > 0. or clippercl > 0.) and
                    self.fullhist is True and
                    self.htype != 'Histogram Equalization'):
                self.hhist[i] = self.argb[i].hist(hdata.compressed(), 50,
                                                  ec='none')
                self.clipvall[i] = self.argb[i].axvline(lclip[i], ls='--')
                self.clipvalu[i] = self.argb[i].axvline(uclip[i], ls='--')

            elif self.htype == 'Histogram Equalization':
                hdata = histeq(hdata)
                hdata = hdata.compressed()
                self.hhist[i] = self.argb[i].hist(hdata, 50, ec='none')
            else:
                self.hhist[i] = self.argb[i].hist(hdata.compressed(), 50,
                                                  ec='none',
                                                  range=(lclip[i], uclip[i]))
            self.htxt[i] = self.argb[i].text(0., 0., '', ha='right', va='top')

            self.argb[i].set_xlim(self.hhist[i][1].min(),
                                  self.hhist[i][1].max())
            self.argb[i].set_ylim(0, self.hhist[i][0].max()*1.2)

        self.figure.canvas.restore_region(self.bgrgb[0])
        self.figure.canvas.restore_region(self.bgrgb[1])
        self.figure.canvas.restore_region(self.bgrgb[2])

        self.update_hist_rgb([None, None, None])

        self.axes.draw_artist(self.image)

        for j in range(3):
            for i in self.hhist[j][2]:
                self.argb[j].draw_artist(i)

        self.figure.canvas.update()

        self.bbox_hist_red = self.figure.canvas.copy_from_bbox(
            self.argb[0].bbox)
        self.bbox_hist_green = self.figure.canvas.copy_from_bbox(
            self.argb[1].bbox)
        self.bbox_hist_blue = self.figure.canvas.copy_from_bbox(
            self.argb[2].bbox)

        for j in range(3):
            self.argb[j].draw_artist(self.htxt[j])
            if self.clipvalu[j] is not None:
                self.argb[j].draw_artist(self.clipvalu[j])
            if self.clipvall[j] is not None:
                self.argb[j].draw_artist(self.clipvall[j])

        self.figure.canvas.update()
        self.figure.canvas.flush_events()

    def update_single_color_map(self):
        """
        Update the single colour map.

        Returns
        -------
        None.

        """
        self.clipvalu = [None, None, None]
        self.clipvall = [None, None, None]
        self.image.rgbmode = self.gmode

        clippercu = self.clippercu[self.hband[0]]
        clippercl = self.clippercl[self.hband[0]]

        sun = None
        for i in self.data:
            if i.dataid == self.hband[0]:
                pseudo = i.data
            if i.dataid == self.hband[3]:
                sun = i.data

        self.image.set_shade(self.shade, self.cell, self.theta, self.phi,
                             self.alpha)
        if self.shade is True:
            pseudo = np.ma.stack([pseudo, sun])
            pseudo = np.moveaxis(pseudo, 0, -1)

        self.image.set_data(pseudo)
        self.image._scale_to_res()

        if self.image._A.ndim == 2:
            pseudo = self.image._A
        else:
            pseudo = self.image._A[:, :, 0]

        lclip = None
        uclip = None
        if self.htype == 'Histogram Equalization':
            self.image.dohisteq = True
            pseudo = histeq(pseudo)
            pseudoc = pseudo.compressed()
            lclip = pseudoc.min()
            uclip = pseudoc.max()
        else:
            self.image.dohisteq = False
            pseudoc = pseudo.compressed()
            lclip, uclip = np.percentile(pseudoc, [clippercl, 100-clippercu])

        self.image.cmap = self.cbar
        self.image.set_clim(lclip, uclip)
        self.image.set_clim(lclip, uclip)

        self.newcmp = self.cbar
        if ((clippercu > 0. or clippercl > 0.) and
                self.fullhist is True and
                self.htype != 'Histogram Equalization'):
            self.hhist[0] = self.argb[0].hist(pseudoc, 50, ec='none')
            tmp = self.hhist[0][1]
            filt = (tmp > lclip) & (tmp < uclip)
            bcnt = np.sum(filt)

            cols = self.cbar(np.linspace(0, 1, bcnt))
            tmp = np.nonzero(filt)

            tmp1 = cols.copy()
            if tmp[0][0] > 0:
                tmp1 = np.vstack(([cols[0]]*tmp[0][0], tmp1))
            if tmp[0][-1] < 49:
                tmp1 = np.vstack((tmp1, [cols[-1]]*(49-tmp[0][-1])))
            self.newcmp = ListedColormap(tmp1)
        else:
            self.hhist[0] = self.argb[0].hist(pseudoc, 50, ec='none',
                                              range=(lclip, uclip))

        self.htxt[0] = self.argb[0].text(0.0, 0.0, '', ha='right', va='top')
        self.argb[0].set_xlim(self.hhist[0][1].min(), self.hhist[0][1].max())
        self.argb[0].set_ylim(0, self.hhist[0][0].max()*1.2)

        self.clipvall[0] = self.argb[0].axvline(lclip, ls='--')
        self.clipvalu[0] = self.argb[0].axvline(uclip, ls='--')

        self.figure.canvas.restore_region(self.bgrgb[0])
        self.update_hist_single()
        self.axes.draw_artist(self.image)

        for i in self.hhist[0][2]:
            self.argb[0].draw_artist(i)

        self.figure.canvas.update()

        self.bbox_hist_red = self.figure.canvas.copy_from_bbox(
            self.argb[0].bbox)

        self.argb[0].draw_artist(self.htxt[0])
        self.argb[0].draw_artist(self.clipvalu[0])
        self.argb[0].draw_artist(self.clipvall[0])
        self.figure.canvas.update()

    def update_shade(self):
        """
        Update sun shade plot.

        Returns
        -------
        None.

        """
        pseudo = self.image._full_res
        sun = None

        for i in self.data:
            if i.dataid == self.hband[3]:
                sun = i.data

        if pseudo.ndim == 2:
            tmp = np.ma.stack([pseudo, sun])
            tmp = np.moveaxis(tmp, 0, -1)
            self.image.set_data(tmp)
            self.image.set_data(tmp)
        elif pseudo.ndim == 2 and pseudo.shape[-1] == 3:
            tmp = np.ma.concatenate((pseudo, sun), axis=-1)
            self.image.set_data(tmp)
        else:
            pseudo[:, :, -1] = sun
            self.image.set_data(pseudo)

        self.image.set_shade(True, self.cell, self.theta, self.phi, self.alpha)
        self.axes.draw_artist(self.image)
        self.figure.canvas.update()

    def update_shade_plot(self):
        """
        Update shade plot for export.

        Returns
        -------
        numpy array
            Sunshader data.

        """
        if self.shade is not True:
            return 1

        sun = None
        for i in self.sdata:
            if i.dataid == self.hband[3]:
                sun = i.data

        sunshader = currentshader(sun.data, self.cell, self.theta,
                                  self.phi, self.alpha)

        snorm = norm2(sunshader)

        return snorm


class MySunCanvas(FigureCanvasQTAgg):
    """
    Canvas for the sunshading tool.

    Attributes
    ----------
    sun: matplotlib plot instance
        plot of a circle 'o' showing where the sun is
    axes: matplotlib axes instance
        axes on which the sun is drawn
    """

    def __init__(self, parent=None):
        fig = Figure(layout='constrained')
        super().__init__(fig)

        self.sun = None
        self.axes = fig.add_subplot(111, polar=True)

        self.setParent(parent)
        self.setMaximumSize(200, 200)
        self.setMinimumSize(120, 120)

    def init_graph(self):
        """
        Initialise graph.

        Returns
        -------
        None.

        """
        self.axes.clear()
        self.axes.tick_params(labelleft=False, labelright=False)
        self.axes.set_autoscaley_on(False)
        self.axes.set_rmax(1.0)
        self.axes.set_rmin(0.0)
        self.axes.set_xticklabels([])

        self.sun, = self.axes.plot(np.pi/4., cos(np.pi/4.), 'o')
        self.figure.canvas.draw()


class PlotInterp(BasicModule):
    """
    The primary class for the raster data interpretation module.

    The main interface is set up from here, as well as monitoring of the mouse
    over the sunshading.

    The PlotInterp class allows for the display of raster data in a variety of
    modes, as well as the export of that display to GeoTIFF format.

    Attributes
    ----------
    self.mmc : pygmi.raster.ginterp.MyMplCanvas, FigureCanvas
        main canvas containing the image
    self.msc : pygmi.raster.ginterp.MySunCanvas, FigureCanvas
        small canvas containing the sunshading control
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.units = {}
        self.clippercu = {}
        self.clippercl = {}

        self.mmc = MyMplCanvas(self)
        self.msc = MySunCanvas(self)
        self.btn_saveimg = QtWidgets.QPushButton('Save GeoTIFF')
        self.cb_histtype = QtWidgets.QCheckBox('Full histogram with clip '
                                               'lines')
        self.cmb_dtype = QtWidgets.QComboBox()
        self.cmb_band1 = QtWidgets.QComboBox()
        self.cmb_band2 = QtWidgets.QComboBox()
        self.cmb_band3 = QtWidgets.QComboBox()
        self.cmb_bands = QtWidgets.QComboBox()
        self.cmb_bandh = QtWidgets.QComboBox()
        self.cmb_htype = QtWidgets.QComboBox()
        self.le_lineclipu = QtWidgets.QLineEdit()
        self.le_lineclipl = QtWidgets.QLineEdit()
        self.cmb_cbar = QtWidgets.QComboBox(self)
        self.kslider = QtWidgets.QSlider(QtCore.Qt.Horizontal)  # CMYK
        self.sslider = QtWidgets.QSlider(QtCore.Qt.Horizontal)  # sunshade
        self.aslider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.lbl_4 = QtWidgets.QLabel('Sunshade Data:')
        self.lbl_s = QtWidgets.QLabel('Sunshade Detail')
        self.lbl_a = QtWidgets.QLabel('Light Reflectance')
        self.lbl_c = QtWidgets.QLabel('Colour Bar:')
        self.lbl_k = QtWidgets.QLabel('K value:')
        self.gbox_sun = QtWidgets.QGroupBox('Sunshading')

        self.btn_allclipperc = QtWidgets.QPushButton('Set current exclusion %'
                                                     ' to all bands')

        if 'MarineCopper' not in colormaps():
            newcmp = ListedColormap(copper/255, 'MarineCopper')
            colormaps.register(newcmp)

        self.setupui()

        txt = str(self.cmb_cbar.currentText())
        self.mmc.cbar = colormaps[txt]

        self.setFocus()

        self.mmc.gmode = 'Single Colour Map'
        self.mmc.argb[0].set_visible(True)
        self.mmc.argb[1].set_visible(False)
        self.mmc.argb[2].set_visible(False)

        self.cmb_band1.show()
        self.cmb_band2.hide()
        self.cmb_band3.hide()
        self.sslider.hide()
        self.aslider.hide()
        self.kslider.hide()
        self.msc.hide()
        self.lbl_a.hide()
        self.lbl_s.hide()
        self.lbl_k.hide()
        self.lbl_4.hide()
        self.cmb_bands.hide()

    def setupui(self):
        """
        Set up UI.

        Returns
        -------
        None.

        """
        helpdocs = menu_default.HelpButton('pygmi.raster.ginterp')
        btn_apply = QtWidgets.QPushButton('Apply Histogram')

        self.btn_allclipperc.setDefault(False)
        self.btn_allclipperc.setAutoDefault(False)

        gbox_1 = QtWidgets.QGroupBox('Display Type')
        vbl_1 = QtWidgets.QVBoxLayout()
        gbox_1.setLayout(vbl_1)

        gbox_2 = QtWidgets.QGroupBox('Data Bands')
        vbl_2 = QtWidgets.QVBoxLayout()
        gbox_2.setLayout(vbl_2)

        gbox_3 = QtWidgets.QGroupBox('Histogram Stretch')
        vbl_3 = QtWidgets.QVBoxLayout()
        gbox_3.setLayout(vbl_3)

        gbox_1.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                             QtWidgets.QSizePolicy.Preferred)
        gbox_2.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                             QtWidgets.QSizePolicy.Preferred)
        gbox_3.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                             QtWidgets.QSizePolicy.Preferred)
        self.gbox_sun.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                    QtWidgets.QSizePolicy.Preferred)

        vbl_4 = QtWidgets.QVBoxLayout()
        self.gbox_sun.setLayout(vbl_4)
        self.gbox_sun.setCheckable(True)
        self.gbox_sun.setChecked(False)

        vbl_raster = QtWidgets.QVBoxLayout()
        hbl_all = QtWidgets.QHBoxLayout(self)
        vbl_right = QtWidgets.QVBoxLayout()

        mpl_toolbar = NavigationToolbar2QT(self.mmc, self)
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Fixed,
                                       QtWidgets.QSizePolicy.Expanding)
        self.sslider.setMinimum(1)
        self.sslider.setMaximum(100)
        self.sslider.setValue(25)
        self.aslider.setMinimum(1)
        self.aslider.setMaximum(100)
        self.aslider.setSingleStep(1)
        self.aslider.setValue(75)
        self.kslider.setMinimum(1)
        self.kslider.setMaximum(100)
        self.kslider.setValue(1)

        self.le_lineclipu.setPlaceholderText('% of high values to exclude')
        self.le_lineclipl.setPlaceholderText('% of low values to exclude')
        self.btn_saveimg.setAutoDefault(False)
        helpdocs.setAutoDefault(False)
        btn_apply.setAutoDefault(False)

        tmp = sorted(m for m in colormaps())

        self.cmb_cbar.addItem('jet')
        self.cmb_cbar.addItem('viridis')
        self.cmb_cbar.addItem('terrain')
        self.cmb_cbar.addItem('MarineCopper')
        self.cmb_cbar.addItems(tmp)
        self.cmb_dtype.addItems(['Single Colour Map', 'Contour',
                                 'RGB Ternary', 'CMY Ternary'])
        self.cmb_htype.addItems(['Linear with Percent Clip',
                                 'Histogram Equalization'])

        self.setWindowTitle('Raster Data Display')

        vbl_1.addWidget(self.cmb_dtype)
        vbl_1.addWidget(self.lbl_k)
        vbl_1.addWidget(self.kslider)
        vbl_raster.addWidget(gbox_1)

        vbl_2.addWidget(self.cmb_band1)
        vbl_2.addWidget(self.cmb_band2)
        vbl_2.addWidget(self.cmb_band3)
        vbl_raster.addWidget(gbox_2)

        vbl_3.addWidget(self.cmb_htype)
        vbl_3.addWidget(self.cmb_bandh)
        vbl_3.addWidget(self.le_lineclipl)
        vbl_3.addWidget(self.le_lineclipu)
        vbl_3.addWidget(self.cb_histtype)
        vbl_3.addWidget(self.btn_allclipperc)
        vbl_3.addWidget(btn_apply)
        vbl_3.addWidget(self.lbl_c)
        vbl_3.addWidget(self.cmb_cbar)
        vbl_raster.addWidget(gbox_3)

        vbl_raster.addWidget(self.gbox_sun)
        vbl_4.addWidget(self.lbl_4)
        vbl_4.addWidget(self.cmb_bands)
        vbl_4.addWidget(self.msc)
        vbl_4.addWidget(self.lbl_s)
        vbl_4.addWidget(self.sslider)
        vbl_4.addWidget(self.lbl_a)
        vbl_4.addWidget(self.aslider)
        vbl_raster.addItem(spacer)
        vbl_raster.addWidget(self.btn_saveimg)
        vbl_raster.addWidget(helpdocs)
        vbl_right.addWidget(self.mmc)
        vbl_right.addWidget(mpl_toolbar)

        hbl_all.addLayout(vbl_raster)
        hbl_all.addLayout(vbl_right)

        self.cmb_cbar.currentIndexChanged.connect(self.change_cbar)
        self.cmb_dtype.currentIndexChanged.connect(self.change_dtype)
        self.cmb_htype.currentIndexChanged.connect(self.change_htype)

        self.sslider.sliderReleased.connect(self.change_sunsliders)
        self.aslider.sliderReleased.connect(self.change_sunsliders)
        self.kslider.sliderReleased.connect(self.change_kval)
        self.msc.figure.canvas.mpl_connect('button_press_event', self.move)
        self.btn_saveimg.clicked.connect(self.save_img)
        self.gbox_sun.clicked.connect(self.change_sun_checkbox)
        btn_apply.clicked.connect(self.change_lclip)
        self.cb_histtype.clicked.connect(self.change_dtype)
        self.btn_allclipperc.clicked.connect(self.change_allclip)

        if self.parent is not None:
            self.resize(self.parent.width(), self.parent.height())

    def change_allclip(self):
        """
        Change all clip percentages to the current one.

        Returns
        -------
        None.

        """
        utxt = self.le_lineclipu.text()
        ltxt = self.le_lineclipl.text()
        dattxt = self.cmb_bandh.currentText()

        try:
            lclip = float(ltxt)
        except ValueError:
            lclip = self.clippercl[dattxt]

        try:
            uclip = float(utxt)
        except ValueError:
            uclip = self.clippercu[dattxt]

        for key in self.clippercl:
            self.clippercl[key] = lclip
            self.clippercu[key] = uclip

        self.mmc.clippercu = self.clippercu
        self.mmc.clippercl = self.clippercl

    def change_blue(self):
        """
        Change the blue or third display band.

        Returns
        -------
        None.

        """
        txt = str(self.cmb_band3.currentText())
        self.cmb_bandh.setCurrentText(txt)
        self.mmc.hband[2] = txt
        self.mmc.init_graph()

    def change_cbar(self):
        """
        Change the colour map for the colour bar.

        Returns
        -------
        None.

        """
        txt = str(self.cmb_cbar.currentText())
        self.mmc.cbar = colormaps[txt]
        self.mmc.update_graph()

    def change_clipband(self):
        """
        Change the clip percentage band.

        Returns
        -------
        None.

        """
        dattxt = self.cmb_bandh.currentText()
        self.le_lineclipl.setText(str(self.clippercl[dattxt]))
        self.le_lineclipu.setText(str(self.clippercu[dattxt]))

    def change_dtype(self):
        """
        Change display type.

        Returns
        -------
        None.

        """
        self.mmc.figure.canvas.mpl_disconnect(self.mmc.cid)

        txt = str(self.cmb_dtype.currentText())
        self.mmc.gmode = txt
        self.cmb_band1.show()
        self.mmc.fullhist = self.cb_histtype.isChecked()

        if txt == 'Single Colour Map':
            self.lbl_c.show()
            self.lbl_k.hide()
            self.cmb_band2.hide()
            self.cmb_band3.hide()
            self.cmb_cbar.show()
            self.mmc.argb[0].set_visible(True)
            self.mmc.argb[1].set_visible(False)
            self.mmc.argb[2].set_visible(False)
            self.sslider.hide()
            self.aslider.hide()
            self.kslider.hide()

        if txt == 'Contour':
            self.lbl_k.hide()
            self.lbl_c.show()
            self.cmb_band2.hide()
            self.cmb_band3.hide()
            self.cmb_cbar.show()
            self.mmc.argb[0].set_visible(False)
            self.mmc.argb[1].set_visible(False)
            self.mmc.argb[2].set_visible(False)
            self.sslider.hide()
            self.aslider.hide()
            self.kslider.hide()
            self.gbox_sun.setChecked(False)

        if 'Ternary' in txt:
            self.lbl_k.hide()
            self.lbl_c.hide()
            self.cmb_band2.show()
            self.cmb_band3.show()
            self.cmb_cbar.hide()
            self.mmc.argb[0].set_visible(True)
            self.mmc.argb[1].set_visible(True)
            self.mmc.argb[2].set_visible(True)
            self.sslider.hide()
            self.aslider.hide()
            self.kslider.hide()
            if 'CMY' in txt:
                self.kslider.show()
                self.lbl_k.show()
                self.mmc.kval = float(self.kslider.value())/100.

        if self.gbox_sun.isChecked():
            self.msc.show()
            self.lbl_4.show()
            self.cmb_bands.show()
            self.sslider.show()
            self.aslider.show()
            self.lbl_a.show()
            self.lbl_s.show()
            self.mmc.cell = self.sslider.value()
            self.mmc.alpha = float(self.aslider.value())/100.
            self.mmc.shade = True
            self.msc.init_graph()
        else:
            self.msc.hide()
            self.lbl_a.hide()
            self.lbl_s.hide()
            self.lbl_4.hide()
            self.cmb_bands.hide()
            self.mmc.shade = False

        self.mmc.cid = self.mmc.figure.canvas.mpl_connect('resize_event',
                                                          self.mmc.revent)
        self.mmc.init_graph()

    def change_green(self):
        """
        Change the green or second band.

        Returns
        -------
        None.

        """
        txt = str(self.cmb_band2.currentText())
        self.cmb_bandh.setCurrentText(txt)
        self.mmc.hband[1] = txt
        self.mmc.init_graph()

    def change_htype(self):
        """
        Change the histogram stretch to apply to the normal data.

        Returns
        -------
        None.

        """
        txt = str(self.cmb_htype.currentText())

        if txt == 'Histogram Equalization':
            self.le_lineclipl.hide()
            self.le_lineclipu.hide()
            self.cmb_bandh.hide()
            self.btn_allclipperc.hide()
        else:
            self.le_lineclipl.show()
            self.le_lineclipu.show()
            self.cmb_bandh.show()
            self.btn_allclipperc.show()

        self.mmc.htype = txt
        self.mmc.update_graph()

    def change_kval(self):
        """
        Change the CMYK K value.

        Returns
        -------
        None.

        """
        self.mmc.kval = float(self.kslider.value())/100.
        self.mmc.update_graph()

    def change_lclip(self):
        """
        Change the linear clip percentage.

        Returns
        -------
        None.

        """
        txt = self.le_lineclipu.text()
        dattxt = self.cmb_bandh.currentText()

        try:
            uclip = float(txt)
        except ValueError:
            if txt == '':
                uclip = 0.0
            else:
                uclip = self.mmc.clippercu[dattxt]
            self.le_lineclipu.setText(str(uclip))

        if uclip < 0.0 or uclip >= 100.0:
            uclip = self.mmc.clippercu[dattxt]
            self.le_lineclipu.setText(str(uclip))

        txt = self.le_lineclipl.text()
        try:
            lclip = float(txt)
        except ValueError:
            if txt == '':
                lclip = 0.0
            else:
                lclip = self.mmc.clippercl[dattxt]
            self.le_lineclipl.setText(str(lclip))

        if lclip < 0.0 or lclip >= 100.0:
            lclip = self.mmc.clippercl[dattxt]
            self.le_lineclipl.setText(str(lclip))

        if (lclip+uclip) >= 100.:
            clip = self.mmc.clippercu[dattxt]
            self.le_lineclipu.setText(str(clip))
            clip = self.mmc.clippercl[dattxt]
            self.le_lineclipl.setText(str(clip))
            return

        self.clippercl[dattxt] = lclip
        self.clippercu[dattxt] = uclip
        self.mmc.clippercu = self.clippercu
        self.mmc.clippercl = self.clippercl

        self.change_dtype()

    def change_red(self):
        """
        Change the red or first band.

        Returns
        -------
        None.

        """
        txt = str(self.cmb_band1.currentText())
        self.cmb_bandh.setCurrentText(txt)
        self.mmc.hband[0] = txt
        self.mmc.init_graph()

    def change_sun(self):
        """
        Change the sunshade band.

        Returns
        -------
        None.

        """
        txt = str(self.cmb_bands.currentText())
        self.mmc.hband[3] = txt
        self.mmc.update_graph()

    def change_sun_checkbox(self):
        """
        Use when sunshading checkbox is clicked.

        Returns
        -------
        None.

        """
        self.mmc.figure.canvas.mpl_disconnect(self.mmc.cid)

        if self.gbox_sun.isChecked():
            self.msc.show()
            self.lbl_4.show()
            self.cmb_bands.show()
            self.sslider.show()
            self.aslider.show()
            self.lbl_a.show()
            self.lbl_s.show()
            self.mmc.cell = self.sslider.value()
            self.mmc.alpha = float(self.aslider.value())/100.
            self.mmc.shade = True
            self.msc.init_graph()
            QtWidgets.QApplication.processEvents()
        else:
            self.msc.hide()
            self.lbl_a.hide()
            self.lbl_s.hide()
            self.lbl_4.hide()
            self.cmb_bands.hide()
            self.sslider.hide()
            self.aslider.hide()
            self.mmc.shade = False
            QtWidgets.QApplication.processEvents()
        self.mmc.update_graph()

        self.mmc.cid = self.mmc.figure.canvas.mpl_connect('resize_event',
                                                          self.mmc.revent)

    def change_sunsliders(self):
        """
        Change the sun shading sliders.

        Returns
        -------
        None.

        """
        self.mmc.cell = self.sslider.value()
        self.mmc.alpha = float(self.aslider.value())/100.
        self.mmc.update_shade()

    def data_init(self):
        """
        Initialise Data.

        Entry point into routine. This entry point exists for
        the case  where data must be initialised before entering at the
        standard 'settings' sub module.

        Returns
        -------
        None.

        """
        if 'Cluster' in self.indata:
            self.indata = copy.deepcopy(self.indata)
            self.indata = dataprep.cluster_to_raster(self.indata)

        if 'Raster' not in self.indata:
            return

        # Get rid of RGB bands.
        indata = []
        for i in self.indata['Raster']:
            if i.isrgb is True:
                continue
            indata.append(i)

        if not indata:
            return

        indata = lstack(indata, showlog=self.showlog, piter=self.piter)

        # Add membership data.
        if 'Cluster' in self.indata:
            newdat = copy.copy(indata)
            for i in self.indata['Cluster']:
                if 'memdat' not in i.metadata['Cluster']:
                    continue
                for j, val in enumerate(i.metadata['Cluster']['memdat']):
                    tmp = copy.deepcopy(i)
                    tmp.memdat = None
                    tmp.data = val
                    tmp.dataid = ('Membership of class ' + str(j+1)
                                  + ': '+tmp.dataid)
                    newdat.append(tmp)
            data = newdat
            sdata = newdat
        else:
            data = indata
            sdata = indata

        for i in data:
            self.units[i.dataid] = i.units

        self.mmc.data = data
        self.mmc.sdata = sdata
        self.mmc.hband[0] = data[0].dataid
        self.mmc.hband[1] = data[0].dataid
        self.mmc.hband[2] = data[0].dataid
        self.mmc.hband[3] = data[0].dataid

        blist = []
        self.clippercu = {}
        self.clippercl = {}

        for i in data:
            blist.append(i.dataid)
            self.clippercu[i.dataid] = 0.0
            self.clippercl[i.dataid] = 0.0

        self.mmc.clippercu = self.clippercu
        self.mmc.clippercl = self.clippercl

        try:
            self.cmb_band1.currentIndexChanged.disconnect()
            self.cmb_band2.currentIndexChanged.disconnect()
            self.cmb_band3.currentIndexChanged.disconnect()
            self.cmb_bands.currentIndexChanged.disconnect()
            self.cmb_bandh.currentIndexChanged.disconnect()
        except TypeError:
            pass

        self.cmb_band1.clear()
        self.cmb_band2.clear()
        self.cmb_band3.clear()
        self.cmb_bands.clear()
        self.cmb_bandh.clear()
        self.cmb_band1.addItems(blist)
        self.cmb_band2.addItems(blist)
        self.cmb_band3.addItems(blist)
        self.cmb_bands.addItems(blist)
        self.cmb_bandh.addItems(blist)

        self.cmb_band1.currentIndexChanged.connect(self.change_red)
        self.cmb_band2.currentIndexChanged.connect(self.change_green)
        self.cmb_band3.currentIndexChanged.connect(self.change_blue)
        self.cmb_bands.currentIndexChanged.connect(self.change_sun)
        self.cmb_bandh.currentIndexChanged.connect(self.change_clipband)

    def move(self, event):
        """
        Move event is used to track changes to the sunshading.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            Mouse event.

        Returns
        -------
        None.

        """
        if event.inaxes == self.msc.axes:
            self.msc.sun.set_xdata([event.xdata])
            self.msc.sun.set_ydata([event.ydata])
            self.msc.figure.canvas.draw()

            phi = -event.xdata
            theta = np.pi/2. - np.arccos(event.ydata)
            self.mmc.phi = phi
            self.mmc.theta = theta
            self.mmc.update_shade()

    def run(self):
        """Run the module as a context menu."""
        self.data_init()
        self.settings()

    def save_img(self):
        """
        Save image as a GeoTIFF.

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        snorm = self.mmc.update_shade_plot()

        ext = 'GeoTIFF (*.tif)'
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.parent, 'Save File', '.', ext)
        if filename == '':
            return False

        text, okay = QtWidgets.QInputDialog.getText(
            self, 'Colorbar', 'Enter length in inches:',
            QtWidgets.QLineEdit.Normal, '4')

        if not okay:
            return False

        try:
            blen = float(text)
        except ValueError:
            QtWidgets.QMessageBox.warning(self.parent, 'Error',
                                          'Invalid value.',
                                          QtWidgets.QMessageBox.Ok)
            return False

        bwid = blen/16.

        dtype = str(self.cmb_dtype.currentText())

        rtext = 'Red'
        gtext = 'Green'
        btext = 'Blue'

        if 'Ternary' not in dtype:
            text, okay = QtWidgets.QInputDialog.getText(
                self, 'Colorbar', 'Enter colorbar unit label:',
                QtWidgets.QLineEdit.Normal,
                self.units[str(self.cmb_band1.currentText())])

            if not okay:
                return False
        else:
            units = str(self.cmb_band1.currentText())
            rtext, okay = QtWidgets.QInputDialog.getText(
                self, 'Ternary Colorbar', 'Enter red/cyan label:',
                QtWidgets.QLineEdit.Normal, units)

            if not okay:
                return False

            units = str(self.cmb_band2.currentText())
            gtext, okay = QtWidgets.QInputDialog.getText(
                self, 'Ternary Colorbar', 'Enter green/magenta label:',
                QtWidgets.QLineEdit.Normal, units)

            if not okay:
                return False

            units = str(self.cmb_band3.currentText())
            btext, okay = QtWidgets.QInputDialog.getText(
                self, 'Ternary Colorbar', 'Enter blue/yelow label:',
                QtWidgets.QLineEdit.Normal, units)

            if not okay:
                return False

        htype = str(self.cmb_htype.currentText())
        cmin = None
        cmax = None

        if dtype == 'Single Colour Map':
            clippercu = self.mmc.clippercu[self.mmc.hband[0]]
            clippercl = self.mmc.clippercl[self.mmc.hband[0]]
            for i in self.mmc.data:
                if i.dataid == self.mmc.hband[0]:
                    pseudo = i.data

            if htype == 'Histogram Equalization':
                pseudo = histeq(pseudo)
            elif clippercl > 0. or clippercu > 0.:
                pseudo, _, _ = histcomp(pseudo, perc=clippercl,
                                        uperc=clippercu)

            cmin = pseudo.min()
            cmax = pseudo.max()

            # The function below normalizes as well.
            img = img2rgb(pseudo, self.mmc.cbar)
            pseudo = None

            img[:, :, 0] = img[:, :, 0]*snorm  # red
            img[:, :, 1] = img[:, :, 1]*snorm  # green
            img[:, :, 2] = img[:, :, 2]*snorm  # blue
            img = img.astype(np.uint8)

        elif 'Ternary' in dtype:
            dat = [None, None, None]
            for i in self.mmc.data:
                for j in range(3):
                    if i.dataid == self.mmc.hband[j]:
                        dat[j] = i.data

            red = dat[0]
            green = dat[1]
            blue = dat[2]

            mask = np.logical_and(red.mask, green.mask)
            mask = np.logical_and(mask, blue.mask)
            mask = np.logical_not(mask)

            if htype == 'Histogram Equalization':
                red = histeq(red)
                green = histeq(green)
                blue = histeq(blue)
            else:
                clippercu = self.mmc.clippercu[self.mmc.hband[0]]
                clippercl = self.mmc.clippercl[self.mmc.hband[0]]
                red, _, _ = histcomp(red, perc=clippercl, uperc=clippercu)
                clippercu = self.mmc.clippercu[self.mmc.hband[1]]
                clippercl = self.mmc.clippercl[self.mmc.hband[1]]
                green, _, _ = histcomp(green, perc=clippercl, uperc=clippercu)
                clippercu = self.mmc.clippercu[self.mmc.hband[2]]
                clippercl = self.mmc.clippercl[self.mmc.hband[2]]
                blue, _, _ = histcomp(blue, perc=clippercl, uperc=clippercu)

            red = red.filled(red.min())
            green = green.filled(green.min())
            blue = blue.filled(blue.min())
            red = np.ma.array(red, mask=dat[0].mask)
            green = np.ma.array(green, mask=dat[1].mask)
            blue = np.ma.array(blue, mask=dat[2].mask)

            img = np.zeros((red.shape[0], red.shape[1], 4), dtype=np.uint8)
            img[:, :, 3] = mask*254+1

            if 'CMY' in dtype:
                img[:, :, 0] = (1-norm2(red))*254+1
                img[:, :, 1] = (1-norm2(green))*254+1
                img[:, :, 2] = (1-norm2(blue))*254+1
            else:
                img[:, :, 0] = norm255(red)
                img[:, :, 1] = norm255(green)
                img[:, :, 2] = norm255(blue)

            img[:, :, 0] = img[:, :, 0]*snorm  # red
            img[:, :, 1] = img[:, :, 1]*snorm  # green
            img[:, :, 2] = img[:, :, 2]*snorm  # blue
            img = img.astype(np.uint8)

        elif dtype == 'Contour':
            clippercu = self.mmc.clippercu[self.mmc.hband[0]]
            clippercl = self.mmc.clippercl[self.mmc.hband[0]]

            pseudo = self.mmc.image._full_res.copy()
            if htype == 'Histogram Equalization':
                pseudo = histeq(pseudo)
            elif clippercl > 0. or clippercu > 0.:
                pseudo, _, _ = histcomp(pseudo, perc=clippercl,
                                        uperc=clippercu)

            cmin = pseudo.min()
            cmax = pseudo.max()

            if self.mmc.ccbar is not None:
                self.mmc.ccbar.remove()
                self.mmc.ccbar = None

            self.mmc.figure.set_frameon(False)
            self.mmc.axes.set_axis_off()
            tmpsize = self.mmc.figure.get_size_inches()
            self.mmc.figure.set_size_inches(tmpsize*3)
            self.mmc.figure.canvas.draw()
            img = np.frombuffer(self.mmc.figure.canvas.tostring_argb(),
                                dtype=np.uint8)
            w, h = self.mmc.figure.canvas.get_width_height()

            self.mmc.figure.set_size_inches(tmpsize)
            self.mmc.figure.set_frameon(True)
            self.mmc.axes.set_axis_on()
            self.mmc.figure.canvas.draw()

            img.shape = (h, w, 4)
            img = np.roll(img, 3, axis=2)

            cmask = np.ones(img.shape[1], dtype=bool)
            for i in range(img.shape[1]):
                if img[:, i, 3].mean() == 0:
                    cmask[i] = False
            img = img[:, cmask]
            rmask = np.ones(img.shape[0], dtype=bool)
            for i in range(img.shape[0]):
                if img[i, :, 3].mean() == 0:
                    rmask[i] = False
            img = img[rmask]

            mask = img[:, :, 3]

        os.chdir(os.path.dirname(filename))

        newimg = [copy.deepcopy(self.mmc.data[0]),
                  copy.deepcopy(self.mmc.data[0]),
                  copy.deepcopy(self.mmc.data[0]),
                  copy.deepcopy(self.mmc.data[0])]

        newimg[0].data = img[:, :, 0]
        newimg[1].data = img[:, :, 1]
        newimg[2].data = img[:, :, 2]
        newimg[3].data = img[:, :, 3]

        mask = img[:, :, 3]
        newimg[0].data[newimg[0].data == 0] = 1
        newimg[1].data[newimg[1].data == 0] = 1
        newimg[2].data[newimg[2].data == 0] = 1

        newimg[0].data[mask <= 1] = 0
        newimg[1].data[mask <= 1] = 0
        newimg[2].data[mask <= 1] = 0

        newimg[0].nodata = 0
        newimg[1].nodata = 0
        newimg[2].nodata = 0
        newimg[3].nodata = 0

        newimg[0].dataid = rtext
        newimg[1].dataid = gtext
        newimg[2].dataid = btext
        newimg[3].dataid = 'Alpha'

        iodefs.export_raster(str(filename), newimg, drv='GTiff',
                             piter=self.piter, bandsort=False,
                             updatestats=True,
                             showlog=self.showlog, compression='DEFLATE')

        # Section for colorbars
        if 'Ternary' not in dtype:
            txt = str(self.cmb_cbar.currentText())
            cmap = colormaps[txt]
            norm = mcolors.Normalize(vmin=cmin, vmax=cmax)

            # Horizontal Bar
            fig = Figure(layout='tight')
            canvas = FigureCanvasQTAgg(fig)
            fig.set_figwidth(blen)
            fig.set_figheight(bwid+0.75)
            ax = fig.gca()

            cb = mcolorbar.ColorbarBase(ax, cmap=cmap, norm=norm,
                                        orientation='horizontal')
            cb.set_label(text)

            fname = filename[:-4]+'_hcbar.png'
            canvas.print_figure(fname, dpi=300)

            # Vertical Bar
            fig = Figure(layout='tight')
            canvas = FigureCanvasQTAgg(fig)
            fig.set_figwidth(bwid+1)
            fig.set_figheight(blen)
            ax = fig.gca()

            cb = mcolorbar.ColorbarBase(ax, cmap=cmap, norm=norm,
                                        orientation='vertical')
            cb.set_label(text)

            fname = filename[:-4]+'_vcbar.png'
            canvas.print_figure(fname, dpi=300)
        else:
            fig = Figure(figsize=[blen, blen], layout='tight')
            canvas = FigureCanvasQTAgg(fig)

            tmp = np.array([[list(range(255))]*255])
            tmp.shape = (255, 255)
            tmp = np.transpose(tmp)

            red = ndimage.rotate(tmp, 0)
            green = ndimage.rotate(tmp, 120)
            blue = ndimage.rotate(tmp, -120)

            tmp = np.zeros((blue.shape[0], 90))
            blue = np.hstack((tmp, blue))
            green = np.hstack((green, tmp))

            rtmp = np.zeros_like(blue)
            j = 92
            rtmp[:255, j:j+255] = red
            red = rtmp

            if 'RGB' in dtype:
                red = red.max()-red
                green = green.max()-green
                blue = blue.max()-blue

            data = np.transpose([red.flatten(),
                                 green.flatten(),
                                 blue.flatten()])
            data.shape = (red.shape[0], red.shape[1], 3)

            data = data[:221, 90:350]

            ax = fig.gca()
            ax.set_xlim((-100, 355))
            ax.set_ylim((-100, 322))

            path = Path([[0, 0], [127.5, 222], [254, 0], [0, 0]])
            patch = PathPatch(path, facecolor='none')
            ax.add_patch(patch)

            data = data.astype(int)

            im = ax.imshow(data, extent=(0, 255, 0, 222), clip_path=patch,
                           clip_on=True)
            im.set_clip_path(patch)

            ax.text(0, -5, gtext, horizontalalignment='center',
                    verticalalignment='top')
            ax.text(254, -5, btext, horizontalalignment='center',
                    verticalalignment='top')
            ax.text(127.5, 225, rtext, horizontalalignment='center')
            ax.tick_params(top='off', right='off', bottom='off', left='off',
                           labelbottom='off', labelleft='off')

            ax.axis('off')
            fname = filename[:-4]+'_tern.png'
            canvas.print_figure(fname, dpi=300)

        QtWidgets.QMessageBox.information(self, 'Information',
                                          'Save to GeoTIFF is complete!',
                                          QtWidgets.QMessageBox.Ok)

        return True

    def settings(self, nodialog=False):
        """
        Entry point into item.

        Parameters
        ----------
        nodialog : bool, optional
            Run settings without a dialog. The default is False.

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        if nodialog:
            return True

        if 'Raster' not in self.indata:
            self.showlog('No Raster Data.')
            return False

        if self.indata['Raster'][0].isrgb:
            self.showlog('RGB images cannot be used in this module.')
            return False

        self.show()
        self.mmc.init_graph()
        self.msc.init_graph()

        tmp = self.exec()

        if tmp == 0:
            return False

        return True

    def saveproj(self):
        """
        Save project data from class.

        Returns
        -------
        None.

        """
        self.saveobj(self.cmb_dtype)
        self.saveobj(self.cmb_band1)
        self.saveobj(self.cmb_band2)
        self.saveobj(self.cmb_band3)
        self.saveobj(self.cmb_bands)
        self.saveobj(self.cmb_htype)
        self.saveobj(self.le_lineclipu)
        self.saveobj(self.le_lineclipl)
        self.saveobj(self.cmb_cbar)
        self.saveobj(self.kslider)
        self.saveobj(self.sslider)
        self.saveobj(self.aslider)


def _testfn():
    """Test routine."""
    import matplotlib
    matplotlib.interactive(False)

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 '..//..')))
    app = QtWidgets.QApplication(sys.argv)

    ifile = r'd:\WorkData\testdata.hdr'
    data = iodefs.get_raster(ifile)

    tmp = PlotInterp()
    tmp.indata['Raster'] = data
    tmp.data_init()

    tmp.settings()


if __name__ == "__main__":
    _testfn()
