# -----------------------------------------------------------------------------
# Name:        iodefs.py (part of PyGMI)
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
"""Import Data."""

import os
import re
from io import StringIO

from PyQt5 import QtWidgets, QtCore
import numpy as np
import pandas as pd
import geopandas as gpd

from pygmi import menu_default
from pygmi.misc import ProgressBarText


class ImportLineData(QtWidgets.QDialog):
    """
    Import Line Data.

    This class imports ASCII point data.

    Attributes
    ----------
    parent : parent
        reference to the parent routine
    outdata : dictionary
        dictionary of output datasets
    ifile : str
        input file name. Used in main.py
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        if parent is None:
            self.showprocesslog = print
            self.piter = ProgressBarText().iter
        else:
            self.showprocesslog = parent.showprocesslog
            self.piter = parent.pbar.iter

        self.parent = parent
        self.indata = {}
        self.outdata = {}
        self.ifile = ''
        self.filt = ''

        self.xchan = QtWidgets.QComboBox()
        self.ychan = QtWidgets.QComboBox()
        self.nodata = QtWidgets.QLineEdit('99999')

        self.setupui()

    def setupui(self):
        """
        Set up UI.

        Returns
        -------
        None.

        """
        gridlayout_main = QtWidgets.QGridLayout(self)
        buttonbox = QtWidgets.QDialogButtonBox()
        helpdocs = menu_default.HelpButton('pygmi.vector.iodefs.'
                                           'importpointdata')
        label_xchan = QtWidgets.QLabel('X Channel:')
        label_ychan = QtWidgets.QLabel('Y Channel:')
        label_nodata = QtWidgets.QLabel('Null Value:')

        buttonbox.setOrientation(QtCore.Qt.Horizontal)
        buttonbox.setCenterButtons(True)
        buttonbox.setStandardButtons(buttonbox.Cancel | buttonbox.Ok)

        self.setWindowTitle(r'Import Point/Line Data')

        gridlayout_main.addWidget(label_xchan, 0, 0, 1, 1)
        gridlayout_main.addWidget(self.xchan, 0, 1, 1, 1)

        gridlayout_main.addWidget(label_ychan, 1, 0, 1, 1)
        gridlayout_main.addWidget(self.ychan, 1, 1, 1, 1)

        gridlayout_main.addWidget(label_nodata, 2, 0, 1, 1)
        gridlayout_main.addWidget(self.nodata, 2, 1, 1, 1)

        gridlayout_main.addWidget(helpdocs, 3, 0, 1, 1)
        gridlayout_main.addWidget(buttonbox, 3, 1, 1, 3)

        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

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
        if not nodialog:
            ext = ('Comma Delimited (*.csv);;'
                   'Geosoft XYZ (*.xyz);;'
                   'ASCII XYZ (*.xyz);;'
                   'Space Delimited (*.txt);;'
                   'Tab Delimited (*.txt)')

            self.ifile, self.filt = QtWidgets.QFileDialog.getOpenFileName(
                self.parent, 'Open File', '.', ext)
            if self.ifile == '':
                return False

        if self.filt == 'Geosoft XYZ (*.xyz)':
            gdf = self.get_GXYZ()
        elif self.filt == 'ASCII XYZ (*.xyz)':
            gdf = self.get_delimited(' ')
        elif self.filt == 'Comma Delimited (*.csv)':
            gdf = self.get_delimited(',')
        elif self.filt == 'Tab Delimited (*.txt)':
            gdf = self.get_delimited('\t')
        elif self.filt == 'Space Delimited (*.txt)':
            gdf = self.get_delimited(' ')
        else:
            return False

        if gdf is None:
            return False

        ltmp = gdf.columns.values

        xind = 0
        yind = 1

        # Check for flexible matches
        for i, tmp in enumerate(ltmp):
            tmpl = tmp.lower()
            if 'lon' in tmpl or 'x' in tmpl or 'east' in tmpl:
                xind = i
            if 'lat' in tmpl or 'y' in tmpl or 'north' in tmpl:
                yind = i
        # Check for exact matches. These take priority
        for i, tmp in enumerate(ltmp):
            tmpl = tmp.lower()
            if tmpl in ['x', 'e']:
                xind = i
            if tmpl in ['y', 'n']:
                yind = i

        self.xchan.addItems(ltmp)
        self.ychan.addItems(ltmp)

        self.xchan.setCurrentIndex(xind)
        self.ychan.setCurrentIndex(yind)

        if not nodialog:
            tmp = self.exec_()

            if tmp != 1:
                return tmp

        try:
            nodata = float(self.nodata.text())
        except ValueError:
            self.showprocesslog('Null Value error - abandoning import')
            return False

        xcol = self.xchan.currentText()
        ycol = self.ychan.currentText()

        gdf['pygmiX'] = gdf[xcol]
        gdf['pygmiY'] = gdf[ycol]
        gdf['line'] = gdf['line'].astype(str)

        if 'Line' not in self.outdata:
            self.outdata['Line'] = {}

        gdf = gdf.replace(nodata, np.nan)
        self.outdata['Line'][self.ifile] = gdf

        return True

    def loadproj(self, projdata):
        """
        Load project data into class.

        Parameters
        ----------
        projdata : dictionary
            Project data loaded from JSON project file.

        Returns
        -------
        chk : bool
            A check to see if settings was successfully run.

        """
        self.ifile = projdata['ifile']
        self.filt = projdata['filt']
        self.xchan.setCurrentText(projdata['xchan'])
        self.ychan.setCurrentText(projdata['ychan'])
        self.nodata.setText(projdata['nodata'])

        chk = self.settings(True)

        return chk

    def saveproj(self):
        """
        Save project data from class.

        Returns
        -------
        projdata : dictionary
            Project data to be saved to JSON project file.

        """
        projdata = {}

        projdata['ifile'] = self.ifile
        projdata['filt'] = self.filt
        projdata['xchan'] = self.xchan.currentText()
        projdata['ychan'] = self.ychan.currentText()
        projdata['nodata'] = self.nodata.text()

        return projdata

    def get_GXYZ(self):
        """
        Get Geosoft XYZ.

        Returns
        -------
        dat : DataFrame
            Pandas dataframe.

        """
        with open(self.ifile) as fno:
            tmp = fno.read()

        chktxt = tmp[:tmp.index('\n')].lower()

        if r'/' not in chktxt and 'line' not in chktxt and 'tie' not in chktxt:
            self.showprocesslog('Not Geosoft XYZ format')
            return None

        head = None
        while r'/' in tmp[:tmp.index('\n')]:
            head = tmp[:tmp.index('\n')]
            tmp = tmp[tmp.index('\n')+1:]
            head = head.split()
            head.pop(0)

        while r'/' in tmp:
            t1 = tmp[:tmp.index(r'/')]
            t2 = tmp[tmp.index(r'/')+1:]
            t3 = t2[t2.index('\n')+1:]
            tmp = t1+t3

        tmp = tmp.lower()
        tmp = tmp.lstrip()
        tmp = re.split('(line|tie)', tmp)
        if tmp[0] == '':
            tmp.pop(0)

        df2 = None
        dflist = []
        for i in self.piter(range(0, len(tmp), 2)):
            tmp2 = tmp[i+1]

            line = tmp[i]+' '+tmp2[:tmp2.index('\n')].strip()
            tmp2 = tmp2[tmp2.index('\n')+1:]
            if head is None:
                head = [f'Column {i+1}' for i in
                        range(len(tmp2[:tmp2.index('\n')].split()))]

            tmp2 = tmp2.replace('*', 'NaN')
            df1 = pd.read_csv(StringIO(tmp2), sep='\s+', names=head)

            df1['line'] = line
            dflist.append(df1)

            # if object in list(df1.dtypes[:-1]):
            #     breakpoint()

        # Concat in all df in one go is much faster
        df2 = pd.concat(dflist, ignore_index=True)

        return df2

    def get_delimited(self, delimiter=','):
        """
        Get a delimited line file.

        Parameters
        ----------
        delimiter : str, optional
            Delimiter type. The default is ','.

        Returns
        -------
        gdf : Dataframe
            Pandas dataframe.

        """
        with open(self.ifile) as fno:
            head = fno.readline()
            tmp = fno.read()

        head = head.split(delimiter)
        head = [i.lower() for i in head]
        tmp = tmp.lower()

        dtype = {}
        dtype['names'] = head
        dtype['formats'] = ['f4']*len(head)

        tmp = tmp.split('\n')
        tmp2 = np.genfromtxt(tmp, names=head, delimiter=delimiter, dtype=None,
                             encoding=None)
        gdf = pd.DataFrame(tmp2)

        if 'line' not in head:
            gdf['line'] = 'None'

        return gdf


class ExportLine():
    """
    Export Line Data.

    Attributes
    ----------
    parent : parent
        reference to the parent routine
    indata : dictionary
        dictionary of input datasets
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.indata = {}
        if parent is None:
            self.showprocesslog = print
        else:
            self.showprocesslog = parent.showprocesslog

    def run(self):
        """
        Run routine.

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        if 'Line' not in self.indata:
            self.showprocesslog('Error: You need to have line data first!')
            return False

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.parent, 'Save File', '.', 'csv (*.csv)')

        if filename == '':
            return False

        self.showprocesslog('Export busy...')

        os.chdir(os.path.dirname(filename))
        data = self.indata['Line']
        data = list(data.values())[0]

        dfall = data.drop(['pygmiX', 'pygmiY'], axis=1)

        dfall.to_csv(filename, index=False)

        self.showprocesslog('Export completed')

        return True


class ExportShapeData():
    """
    Export Line Data.

    Attributes
    ----------
    parent : parent
        reference to the parent routine
    indata : dictionary
        dictionary of input datasets
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.indata = {}
        if parent is None:
            self.showprocesslog = print
        else:
            self.showprocesslog = parent.showprocesslog

    def run(self):
        """
        Run routine.

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        if 'Vector' not in self.indata:
            self.showprocesslog('Error: You need to have vector data first!')
            return False

        filename, filt = QtWidgets.QFileDialog.getSaveFileName(
            self.parent, 'Save File', '.', 'shp (*.shp);;GeoJSON (*.geojson)')

        if filename == '':
            return False

        self.showprocesslog('Export busy...')

        os.chdir(os.path.dirname(filename))
        data = self.indata['Vector']
        data = list(data.values())[0]

        if filt == 'GeoJSON (*.geojson)':
            data.to_file(filename, driver='GeoJSON')
        else:
            data.to_file(filename)
#        dfall = data.drop(['pygmiX', 'pygmiY'], axis=1)

#        dfall.to_csv(filename, index=False)

        self.showprocesslog('Export completed')

        return True


class ImportShapeData():
    """
    Import Shapefile Data.

    Attributes
    ----------
    parent : parent
        reference to the parent routine
    outdata : dictionary
        dictionary of output datasets
    ifile : str
        input file name. Used in main.py
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.indata = {}
        self.outdata = {}
        self.ifile = ''
        if parent is None:
            self.showprocesslog = print
        else:
            self.showprocesslog = parent.showprocesslog

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
        if not nodialog:
            ext = 'Shapefile (*.shp);;' + 'All Files (*.*)'

            self.ifile, _ = QtWidgets.QFileDialog.getOpenFileName(self.parent,
                                                                  'Open File',
                                                                  '.', ext)
            if self.ifile == '':
                return False

        os.chdir(os.path.dirname(self.ifile))

        gdf = gpd.read_file(self.ifile)
        gdf = gdf[gdf.geometry != None]

        dat = {gdf.geom_type.iloc[0]: gdf}

        self.outdata['Vector'] = dat

        return True

    def loadproj(self, projdata):
        """
        Load project data into class.

        Parameters
        ----------
        projdata : dictionary
            Project data loaded from JSON project file.

        Returns
        -------
        chk : bool
            A check to see if settings was successfully run.

        """
        self.ifile = projdata['ifile']

        chk = self.settings(True)

        return chk

    def saveproj(self):
        """
        Save project data from class.

        Returns
        -------
        projdata : dictionary
            Project data to be saved to JSON project file.

        """
        projdata = {}

        projdata['ifile'] = self.ifile

        return projdata
