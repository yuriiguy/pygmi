# -----------------------------------------------------------------------------
# Name:        show_table.py (part of PyGMI)
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
"""Routine which displays a table graphically with various stats."""

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
import numpy as np
import scipy.stats.mstats as st

from pygmi.misc import ContextModule


class BasicStats(ContextModule):
    """Show a summary of basic stats."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(640, 320)

        self.cmb_1 = QtWidgets.QComboBox()
        self.tablewidget = QtWidgets.QTableWidget()
        self.pushbutton_save = QtWidgets.QPushButton('Save')

        self.setupui()
        self.bands = None
        self.cols = None
        self.data = None

    def setupui(self):
        """
        Set up UI.

        Returns
        -------
        None.

        """
        hbl = QtWidgets.QHBoxLayout(self)
        vbl = QtWidgets.QVBoxLayout()

        vbl.addWidget(self.pushbutton_save)
        vbl.addWidget(self.cmb_1)

        hbl.addWidget(self.tablewidget)
        hbl.addLayout(vbl)

        self.setWindowTitle('Basic Statistics')

        self.cmb_1.currentIndexChanged.connect(self.combo)
        self.pushbutton_save.clicked.connect(self.save)

    def combo(self):
        """
        Combo.

        Returns
        -------
        None.

        """
        i = self.cmb_1.currentIndex()
        data = self.data[i][:, 1:]

        # for row in range(data.shape[0]):
        #     for col in range(data.shape[1]):
        #         self.tablewidget.setCellWidget(
        #             row, col, QtWidgets.QLabel(str(data[row, col])))

        # self.tablewidget.resizeColumnsToContents()

        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                txt = f' {data[row, col]:,.5f}'
                txt = QtWidgets.QLabel(txt)
                txt.setAlignment(Qt.AlignRight)

                self.tablewidget.setCellWidget(row, col, txt)

        self.tablewidget.resizeColumnsToContents()

    def run(self):
        """
        Run.

        Returns
        -------
        None.

        """
        data = self.indata['Raster']
        self.bands, self.cols, self.data = basicstats_calc(data)

        data = self.data[0][:, 1:]
        rows = self.data[0][:, 0]
        cols = self.cols[1:]

        if len(self.data) == 1:
            self.cmb_1.hide()

        self.cmb_1.addItems(self.bands)
        self.tablewidget.setRowCount(data.shape[0])
        self.tablewidget.setColumnCount(data.shape[1])
        self.tablewidget.setHorizontalHeaderLabels(cols)
        self.tablewidget.setVerticalHeaderLabels(rows)

        for i, _ in enumerate(cols):
            item = self.tablewidget.horizontalHeaderItem(i)
            fnt = item.font()
            fnt.setBold(True)
            item.setFont(fnt)

        for i, _ in enumerate(rows):
            item = self.tablewidget.verticalHeaderItem(i)
            fnt = item.font()
            fnt.setBold(True)
            item.setFont(fnt)

        self.combo()
        self.show()

    def save(self):
        """
        Save Table.

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        ext = 'CSV Format (*.csv)'
        ifile, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Table',
                                                         '.', ext)
        if ifile == '':
            return False

        savetable(ifile, self.bands, self.cols, self.data)

        return True


def basicstats_calc(data):
    """
    Calculate statistics.

    Parameters
    ----------
    data : PyGMI Data.
        PyGMI raster dataset.

    Returns
    -------
    bands : list
        Band list, currently only 'Data Column'
    cols : list
        Columns for the table
    dattmp : list
        List of arrays containing statistics.

    """
# Minimum, maximum, mean, std dev, median, median abs deviation
# no samples, no samples in x dir, no samples in y dir, band
    stats = []
    for i in data:
        srow = []
        dtmp = i.data.compressed()
        srow.append(dtmp.min())
        srow.append(dtmp.max())
        srow.append(dtmp.mean())
        srow.append(dtmp.std())
        srow.append(np.median(dtmp))
        srow.append(np.median(abs(dtmp - srow[-1])))
        srow.append(i.data.size)
        srow.append(i.data.shape[1])
        srow.append(i.data.shape[0])
        srow.append(st.skew(dtmp))
        srow.append(st.kurtosis(dtmp))
        srow = np.array(srow).tolist()
        stats.append([i.dataid] + srow)

    bands = ['Data Column']
    cols = ['Band', 'Minimum', 'Maximum', 'Mean', 'Std Dev', 'Median',
            'Median Abs Dev', 'No Samples', 'No cols (samples in x-dir)',
            'No rows (samples in y-dir)', 'Skewness', 'Kurtosis']
    dattmp = [np.array(stats, dtype=object)]
    return bands, cols, dattmp


class ClusterStats(ContextModule):
    """Show a summary of basic statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cmb_1 = QtWidgets.QComboBox()
        self.tablewidget = QtWidgets.QTableWidget()
        self.pushbutton_save = QtWidgets.QPushButton('Save')

        self.setupui()
        self.data = None
        self.cols = None
        self.bands = None

    def setupui(self):
        """
        Set up UI.

        Returns
        -------
        None.

        """
        hbl = QtWidgets.QHBoxLayout(self)
        vbl = QtWidgets.QVBoxLayout()

        vbl.addWidget(self.pushbutton_save)
        vbl.addWidget(self.cmb_1)

        hbl.addWidget(self.tablewidget)
        hbl.addLayout(vbl)

        self.setWindowTitle(
            'Cluster Statistics (Mean Value : Std Deviation)')

        self.cmb_1.currentIndexChanged.connect(self.combo)
        self.pushbutton_save.clicked.connect(self.save)

    def combo(self):
        """
        Combo.

        Returns
        -------
        None.

        """
        i = self.cmb_1.currentIndex()
        data = self.data[i]

        self.tablewidget.setRowCount(len(data))
        rows = ['Class '+str(j+1) for j in range(len(data))]
        self.tablewidget.setVerticalHeaderLabels(rows)

        for row, _ in enumerate(data):
            for col, _ in enumerate(data[0]):
                self.tablewidget.setCellWidget(
                    row, col, QtWidgets.QLabel(str(data[row][col])))

        self.tablewidget.resizeColumnsToContents()

    def run(self):
        """
        Run.

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        self.show()
        data = self.indata['Cluster']

        self.bands = ['Clusters: ' + str(i.metadata['Cluster']['no_clusters'])
                      for i in data]

        if 'input_type' not in data[0].metadata['Cluster']:
            self.showlog('Your dataset does not qualify')
            return False

        self.cols = list(data[0].metadata['Cluster']['input_type'])
        self.data = []

        for i in data:
            val = i.metadata['Cluster']['center'].tolist()
            std = i.metadata['Cluster']['center_std'].tolist()

            for j, _ in enumerate(val):
                for k, _ in enumerate(val[0]):
                    val[j][k] = f'{val[j][k]:,.4f} : {std[j][k]:,.4f}'
            self.data.append(val)

        data = self.data[0]
        rows = ['Class '+str(j+1) for j in range(len(data))]
        cols = self.cols

        if len(self.data) == 1:
            self.cmb_1.hide()

        self.cmb_1.addItems(self.bands)
        self.tablewidget.setRowCount(len(data))
        self.tablewidget.setColumnCount(len(data[0]))
        self.tablewidget.setHorizontalHeaderLabels(cols)
        self.tablewidget.setVerticalHeaderLabels(rows)

        for i, _ in enumerate(cols):
            item = self.tablewidget.horizontalHeaderItem(i)
            fnt = item.font()
            fnt.setBold(True)
            item.setFont(fnt)

        for i, _ in enumerate(rows):
            item = self.tablewidget.verticalHeaderItem(i)
            fnt = item.font()
            fnt.setBold(True)
            item.setFont(fnt)

        self.combo()
        return True

    def save(self):
        """
        Save Table.

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        ext = 'CSV Format (*.csv)'
        ifile, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Table',
                                                         '.', ext)
        if ifile == '':
            return False

        savetable(ifile, self.bands, self.cols, self.data)

        return True


def savetable(ofile, bands, cols, data):
    """
    Save tabular data.

    Parameters
    ----------
    ofile : str
        Output file name.
    bands : list
        List of bands.
    cols : list
        List of column headings.
    data : list
        List of arrays containing statistics.

    Returns
    -------
    None.

    """
    with open(ofile, 'a', encoding='utf-8') as fobj:
        htmp = cols[0]
        for i in cols[1:]:
            htmp += ',' + i

        for k, bandsk in enumerate(bands):
            fobj.write(bandsk+'\n')
            fobj.write(htmp+'\n')
            for i, _ in enumerate(data[k]):
                rtmp = str(data[k][i][0])
                for j in range(1, len(data[k][0])):
                    rtmp += ','+str(data[k][i][j])
                fobj.write(rtmp+'\n')
            fobj.write('\n')
