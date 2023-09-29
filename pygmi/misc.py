# -----------------------------------------------------------------------------
# Name:        misc.py (part of PyGMI)
#
# Author:      Patrick Cole
# E-Mail:      pcole@geoscience.org.za
#
# Copyright:   (c) 2015 Council for Geoscience
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
"""Misc is a collection of routines which can be used in PyGMI in general."""

import os
import sys
import types
import time
import textwrap
import psutil
import numpy as np
from matplotlib import ticker
from PyQt5 import QtWidgets, QtCore, QtGui

PBAR_STYLE = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}

QProgressBar::chunk {
    background: qlineargradient(x1: 0.5, y1: 0, x2: 0.5, y2: 1, stop: 0 green, stop: 1 white);
    width: 10px;
}
"""

PTIME = None


class EmittingStream(QtCore.QObject):
    """Class to intercept stdout for later use in a textbox."""

    def __init__(self, textWritten):
        self.textWritten = textWritten

    def write(self, text):
        """
        Write text.

        Parameters
        ----------
        text : str
            Text to write.

        Returns
        -------
        None.

        """
        self.textWritten(str(text))

    def flush(self):
        """
        Flush.

        Returns
        -------
        None.

        """

    def fileno(self):
        """
        File number.

        Returns
        -------
        int
            Returns -1.

        """
        return -1


class BasicModule(QtWidgets.QDialog):
    """
    Basic Module.

    Attributes
    ----------
    parent : parent
        reference to the parent routine
    indata : dictionary
        dictionary of input datasets
    outdata : dictionary
        dictionary of output datasets
    ifile : str
        input file, used in IO routines and to pass filename back to main.py
    piter : function
        reference to a progress bar iterator.
    pbar : function
        reference to a progress bar.
    showlog: stdout or alternative
        reference to a way to view messages, normally stdout or a Qt text box.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is None:
            self.stdout_redirect = sys.stdout
            self.showlog = print
            self.pbar = ProgressBarText()
            self.process_is_active = lambda *args, **kwargs: None
        else:
            self.stdout_redirect = EmittingStream(parent.showlog)
            self.showlog = parent.showlog
            self.pbar = parent.pbar
            if hasattr(parent, 'process_is_active'):
                self.process_is_active = parent.process_is_active
            else:
                self.process_is_active = lambda *args, **kwargs: None

        self.piter = self.pbar.iter

        self.indata = {}
        self.outdata = {}
        self.projdata = {}
        self.parent = parent
        self.is_import = False
        self.ifile = ''
        self.ipth = os.path.dirname(__file__)+r'/images/'
        self.setWindowIcon(QtGui.QIcon(self.ipth+'logo256.ico'))

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
        return True

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
        self.projdata = projdata

        for otxt in projdata:
            if otxt not in vars(self):
                self.showlog('Cannot load project, you may be using an '
                             'old project format.')
                return False

        for otxt in projdata:
            obj = vars(self)[otxt]

            if obj is None:
                vars(self)[otxt] = projdata[otxt]

            if isinstance(obj, (float, int, bool, list, np.ndarray, tuple,
                                str)):
                vars(self)[otxt] = projdata[otxt]

            if isinstance(obj, QtWidgets.QComboBox):
                obj.blockSignals(True)
                obj.setCurrentText(projdata[otxt])
                obj.blockSignals(False)

            if isinstance(obj, (QtWidgets.QLineEdit, QtWidgets.QTextEdit)):
                obj.blockSignals(True)
                obj.setText(projdata[otxt])
                obj.blockSignals(False)

            if isinstance(obj, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox,
                                QtWidgets.QSlider)):
                obj.blockSignals(True)
                obj.setValue(projdata[otxt])
                obj.blockSignals(False)

            if isinstance(obj, (QtWidgets.QRadioButton, QtWidgets.QCheckBox)):
                obj.blockSignals(True)
                obj.setChecked(projdata[otxt])
                obj.blockSignals(False)

            if isinstance(obj, QtWidgets.QDateEdit):
                obj.blockSignals(True)
                date = obj.date().fromString(projdata[otxt])
                obj.setDate(date)
                obj.blockSignals(False)

            if isinstance(obj, QtWidgets.QListWidget):
                obj.blockSignals(True)
                obj.selectAll()
                for i in obj.selectedItems():
                    if i.text()[2:] not in self.projdata[otxt]:
                        i.setSelected(False)
                obj.blockSignals(False)

        if self.is_import is True:
            chk = self.settings(True)
        else:
            chk = False

        return chk

    def saveproj(self):
        """
        Save project data from class.

        Returns
        -------
        None.

        """

    def saveobj(self, obj):
        """
        Save an object to a dictionary.

        This is a convenience function for saving project information.

        Parameters
        ----------
        obj : variable
            A variable to be saved.

        Returns
        -------
        None.

        """
        otxt = None
        for name in vars(self):
            if id(vars(self)[name]) == id(obj):
                otxt = name
        if otxt is None:
            return

        if isinstance(obj, (float, int, bool, list, np.ndarray, tuple, str)):
            self.projdata[otxt] = obj

        if isinstance(obj, QtWidgets.QComboBox):
            self.projdata[otxt] = obj.currentText()

        if isinstance(obj, (QtWidgets.QLineEdit, QtWidgets.QTextEdit)):
            self.projdata[otxt] = obj.text()

        if isinstance(obj, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox,
                            QtWidgets.QSlider)):
            self.projdata[otxt] = obj.value()

        if isinstance(obj, (QtWidgets.QRadioButton, QtWidgets.QCheckBox)):
            self.projdata[otxt] = obj.isChecked()

        if isinstance(obj, QtWidgets.QDateEdit):
            self.projdata[otxt] = obj.date().toString()

        if isinstance(obj, QtWidgets.QListWidget):
            tmp = []
            for i in obj.selectedItems():
                tmp.append(i.text()[2:])
            self.projdata[otxt] = tmp

        return

class ContextModule(QtWidgets.QDialog):
    """
    Context Module.

    Attributes
    ----------
    parent : parent
        reference to the parent routine
    indata : dictionary
        dictionary of input datasets
    outdata : dictionary
        dictionary of output datasets
    piter : function
        reference to a progress bar iterator.
    pbar : function
        reference to a progress bar.
    showlog: stdout or alternative
        reference to a way to view messages, normally stdout or a Qt text box.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        if parent is None:
            self.stdout_redirect = sys.stdout
            self.showlog = print
            self.pbar = ProgressBarText()
            self.process_is_active = lambda *args, **kwargs: None
        else:
            self.stdout_redirect = EmittingStream(parent.showlog)
            self.showlog = parent.showlog
            self.pbar = parent.pbar
            self.process_is_active = parent.process_is_active

        self.piter = self.pbar.iter

        self.indata = {}
        self.outdata = {}
        self.parent = parent

        self.ipth = os.path.dirname(__file__)+r'/images/'
        self.setWindowIcon(QtGui.QIcon(self.ipth+'logo256.ico'))

    def run(self):
        """
        Run context menu item.

        Returns
        -------
        None.

        """


class QLabelVStack:
    """QLabelVStack."""

    def __init__(self, parent=None):
        self.layout = QtWidgets.QGridLayout(parent)
        self.layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.indx = 0

    def addWidget(self, widget1, widget2):
        """
        Add two widgets on a row, widget1 can also be text.

        Parameters
        ----------
        widget1 : str or QWidget
            First Widget or Label on the row.
        widget2 : QWidget
            Last Widget.

        Returns
        -------
        None.

        """
        if isinstance(widget1, str):
            widget1 = QtWidgets.QLabel(widget1)

        self.layout.addWidget(widget1, self.indx, 0)
        self.layout.addWidget(widget2, self.indx, 1)
        self.indx += 1


class PTime():
    """
    PTime class.

    Main class in the ptimer module. Once activated, this class keeps track
    of all time since activation. Times are stored whenever its methods are
    called.

    Attributes
    ----------
    tchk : list
        List of times generated by the time.perf_counter routine.
    """

    def __init__(self):
        self.tchk = [time.perf_counter()]

    def since_first_call(self, msg='since first call', show=True):
        """
        Time lapsed since first call.

        This function prints out a message and lets you know the time
        passed since the first call.

        Parameters
        ----------
        msg : str
            Optional message
        """
        self.tchk.append(time.perf_counter())
        tdiff = self.tchk[-1] - self.tchk[0]
        if show:
            if tdiff < 60:
                print(msg, 'time (s):', tdiff)
            else:
                mins = int(tdiff/60)
                secs = tdiff-mins*60
                print(msg, 'time (s): ', mins, ' minutes ', secs, ' seconds')
        return tdiff

    def since_last_call(self, msg='since last call', show=True):
        """
        Time lapsed since last call.

        This function prints out a message and lets you know the time
        passed since the last call.

        Parameters
        ----------
        msg : str
            Optional message
        """
        self.tchk.append(time.perf_counter())
        tdiff = self.tchk[-1] - self.tchk[-2]
        if show:
            print(msg, 'time(s):', tdiff, 'since last call')
        return tdiff


class ProgressBar(QtWidgets.QProgressBar):
    """
    Progress bar.

    Progress Bar routine which expands the QProgressBar class slightly so that
    there is a time function as well as a convenient of calling it via an
    iterable.

    Attributes
    ----------
    otime : integer
        This is the original time recorded when the progress bar starts.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimum(0)
        self.setValue(0)
        self.otime = 0
        self.setStyleSheet(PBAR_STYLE)
        self.total = 100

    def iter(self, iterable):
        """Iterate Routine."""
        if not isinstance(iterable, types.GeneratorType):
            self.total = len(iterable)

        self.setMaximum(self.total)
        self.setMinimum(0)
        self.setValue(0)

        self.otime = time.perf_counter()
        time1 = self.otime
        time2 = self.otime

        i = 0
        for obj in iterable:
            yield obj
            i += 1

            time2 = time.perf_counter()
            if time2-time1 > 1:
                self.setValue(i)
                tleft = (self.total-i)*(time2-self.otime)/i
                if tleft > 60:
                    tleft = int(tleft // 60)
                    self.setFormat('%p% '+str(tleft)+'min left ')
                else:
                    tleft = int(tleft)
                    self.setFormat('%p% '+str(tleft)+'s left   ')
                QtWidgets.QApplication.processEvents()
                time1 = time2

        self.setFormat('%p%')
        self.setValue(self.total)

    def to_max(self):
        """Set the progress to maximum."""
        self.setMaximum(self.total)
        self.setMinimum(0)
        self.setValue(self.total)
        QtWidgets.QApplication.processEvents()


class ProgressBarText():
    """Text Progress bar."""

    def __init__(self):
        self.otime = 0
        self.total = 100
        self.decimals = 1
        self.length = 40
        self.fill = '#'
        self.prefix = 'Progress:'

    def iter(self, iterable):
        """Iterate Routine."""
        if not isinstance(iterable, types.GeneratorType):
            self.total = len(iterable)

        if self.total == 0:
            self.total = 1

        self.otime = time.perf_counter()
        time1 = self.otime
        time2 = self.otime

        i = 0
        oldval = 0
        gottototal = False
        for obj in iterable:
            yield obj
            i += 1

            time2 = time.perf_counter()
            if time2-time1 > 1 and int(i*100/self.total) > oldval:
                oldval = int(i*100/self.total)

                tleft = (self.total-i)*(time2-self.otime)/i
                if tleft > 60:
                    timestr = f' {tleft // 60:.0f} min left '
                else:
                    timestr = f' {tleft:.1f} sec left '
                timestr += f' {time2-self.otime:.1f} sec total      '

                self.printprogressbar(i, suffix=timestr)
                time1 = time2
                if i == self.total:
                    gottototal = True

        if not gottototal:
            self.printprogressbar(self.total)

    def printprogressbar(self, iteration, suffix=''):
        """
        Call in a loop to create terminal progress bar.

        Code by Alexander Veysov. (https://gist.github.com/snakers4).

        Parameters
        ----------
        iteration : int
            current iteration
        suffix : str, optional
            Suffix string. The default is ''.

        Returns
        -------
        None.

        """
        perc = 100*(iteration/float(self.total))
        percent = f'{perc:.{self.decimals}f}'
        filledlength = int(self.length*iteration//self.total)
        pbar = self.fill*filledlength + '-'*(self.length - filledlength)
        pbar = f'\r{self.prefix} |{pbar}| {percent}% {suffix}'
        print(pbar, end='\r')
        # Print New Line on Complete
        if iteration == self.total:
            print()

    def to_max(self):
        """Set the progress to maximum."""
        self.printprogressbar(self.total)


def getinfo(txt=None, reset=False):
    """
    Get time and memory info.

    Parameters
    ----------
    txt : str/int/float, optional
        Descriptor used for headings. The default is None.
    reset : bool
        Flag used to reset the time difference to zero.

    Returns
    -------
    None.

    """
    global PTIME

    timebefore = PTIME
    PTIME = time.perf_counter()

    if timebefore is None or reset is True:
        tdiff = 0.
    else:
        tdiff = PTIME - timebefore

    if txt is not None:
        heading = '===== '+str(txt)+': '
    else:
        heading = '===== Info: '

    mem = psutil.virtual_memory()
    memtxt = f'RAM memory used: {mem.used:,.1f} B ({mem.percent}%)'

    print(heading+memtxt+f' Time(s): {tdiff:.3f}')


def textwrap2(text, width, placeholder='...', max_lines=None):
    """
    Provide slightly different placeholder functionality to textwrap.

    Placeholders will be a part of last line, instead of replacing it.

    Parameters
    ----------
    text : str
        Text to wrap.
    width : int
        Maximum line length.
    placeholder : sre, optional
        Placeholder when lines exceed max_lines. The default is '...'.
    max_lines : int, optional
        Maximum number of lines. The default is None.

    Returns
    -------
    text2 : str
        Output wrapped text.

    """
    text2 = textwrap.wrap(text, width=width)

    if max_lines is not None and text2:
        text2 = text2[:max_lines]
        if len(text2[-1]) == width:
            text2[-1] = text2[-1][:-len(placeholder)] + placeholder

    text2 = '\n'.join(text2)

    return text2


def tick_formatter(x, pos):
    """
    Format thousands separator in ticks for plots.

    Parameters
    ----------
    x : float/int
        Number to be formatted.
    pos : int
        Position of tick.

    Returns
    -------
    newx : str
        Formatted coordinate.

    """
    if np.ma.is_masked(x):
        return '--'

    newx = f'{x:,.5f}'.rstrip('0').rstrip('.')

    return newx


frm = ticker.FuncFormatter(tick_formatter)


def _testfn():
    """Test function."""
    app = QtWidgets.QApplication(sys.argv)

    tmp = BasicModule()
    tmp.ifile = QtWidgets.QLineEdit('test')
    tmp.saveobj(tmp.ifile)

    print(tmp.projdata)


if __name__ == "__main__":
    _testfn()
