# -----------------------------------------------------------------------------
# Name:        transforms.py (part of PyGMI)
#
# Author:      Patrick Cole
# E-Mail:      pcole@geoscience.org.za
#
# Copyright:   (c) 2021 Council for Geoscience
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
"""Transforms such as PCA and MNF."""

import os
import numpy as np
from PyQt5 import QtWidgets, QtCore
from sklearn.decomposition import IncrementalPCA
import numexpr as ne
import matplotlib.pyplot as plt

from pygmi.misc import BasicModule
from pygmi import menu_default
from pygmi.raster.iodefs import export_raster
from pygmi.raster.misc import lstack
from pygmi.rsense.iodefs import get_data
from pygmi.rsense.iodefs import get_from_rastermeta
from pygmi.rsense.iodefs import set_export_filename


class MNF(BasicModule):
    """Perform MNF Transform."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ev = None

        self.sb_comps = QtWidgets.QSpinBox()
        self.cb_fwdonly = QtWidgets.QCheckBox('Forward Transform Only.')
        self.rb_noise_diag = QtWidgets.QRadioButton('Noise estimated by '
                                                    'diagonal shift')
        self.rb_noise_hv = QtWidgets.QRadioButton('Noise estimated by average '
                                                  'of horizontal and vertical '
                                                  'shift')
        self.rb_noise_quad = QtWidgets.QRadioButton('Noise estimated by local '
                                                    'quadratic surface')

        self.setupui()

        self.resize(500, 350)

    def setupui(self):
        """
        Set up UI.

        Returns
        -------
        None.

        """
        gl_main = QtWidgets.QGridLayout(self)
        buttonbox = QtWidgets.QDialogButtonBox()
        helpdocs = menu_default.HelpButton('pygmi.rsense.mnf')
        lbl_comps = QtWidgets.QLabel('Number of components:')

        self.cb_fwdonly.setChecked(True)
        self.sb_comps.setMaximum(10000)
        self.sb_comps.setMinimum(1)
        self.rb_noise_hv.setChecked(True)

        buttonbox.setOrientation(QtCore.Qt.Horizontal)
        buttonbox.setCenterButtons(True)
        buttonbox.setStandardButtons(buttonbox.Cancel | buttonbox.Ok)

        self.setWindowTitle('Minimum Noise Fraction')

        gl_main.addWidget(self.cb_fwdonly, 1, 0, 1, 2)
        gl_main.addWidget(lbl_comps, 2, 0, 1, 1)
        gl_main.addWidget(self.sb_comps, 2, 1, 1, 1)
        gl_main.addWidget(self.rb_noise_hv, 3, 0, 1, 2)
        gl_main.addWidget(self.rb_noise_diag, 4, 0, 1, 2)
        gl_main.addWidget(self.rb_noise_quad, 5, 0, 1, 2)

        gl_main.addWidget(helpdocs, 6, 0, 1, 1)
        gl_main.addWidget(buttonbox, 6, 1, 1, 3)

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
        self.ev = None
        tmp = []
        if 'Raster' not in self.indata and 'RasterFileList' not in self.indata:
            self.showlog('No Satellite Data')
            return False

        if 'RasterFileList' in self.indata:
            if len(self.indata['RasterFileList'][0].bands) > 5:
                self.sb_comps.setValue(5)

        if 'Raster' in self.indata:
            indata = self.indata['Raster']
            self.sb_comps.setMaximum(len(indata))
            if len(indata) > 5:
                self.sb_comps.setValue(5)

        if not nodialog:
            tmp = self.exec()
        else:
            tmp = 1

        if tmp != 1:
            return False

        self.acceptall()

        if not nodialog and self.ev is not None:
            ncmps = self.sb_comps.value()
            xvals = range(1, ncmps+1)

            plt.figure('Explained Variance')
            plt.subplot(1, 1, 1)
            plt.plot(xvals, self.ev)
            plt.xticks(xvals)
            plt.xlabel('Component')
            plt.ylabel('Explained Variance')
            plt.grid(True)
            plt.tight_layout()

            if hasattr(plt.get_current_fig_manager(), 'window'):
                plt.get_current_fig_manager().window.setWindowIcon(self.parent.windowIcon())

            plt.show()

        return True

    def changeoutput(self):
        """
        Change the interface to reflect whether full calculation is needed.

        Returns
        -------
        None.

        """
        uienabled = not self.cb_fwdonly.isChecked()
        self.sb_comps.setEnabled(uienabled)

    def saveproj(self):
        """
        Save project data from class.

        Returns
        -------
        None.

        """
        self.saveobj(self.sb_comps)
        self.saveobj(self.cb_fwdonly)
        self.saveobj(self.rb_noise_diag)
        self.saveobj(self.rb_noise_hv)
        self.saveobj(self.rb_noise_quad)

    def acceptall(self):
        """
        Accept option.

        Updates self.outdata, which is used as input to other modules.

        Returns
        -------
        None.

        """
        if 'RasterFileList' in self.indata:
            flist = self.indata['RasterFileList']
        else:
            flist = None

        ncmps = self.sb_comps.value()
        odata = []

        if self.rb_noise_diag.isChecked():
            noise = 'diagonal'
        elif self.rb_noise_hv.isChecked():
            noise = 'hv average'
        else:
            noise = 'quad'

        if 'RasterFileList' in self.indata:
            filename = flist[0].filename
            odir = os.path.join(os.path.dirname(filename), 'MNF')

            os.makedirs(odir, exist_ok=True)
            for ifile in flist:
                filename = ifile.filename

                self.showlog('Processing '+os.path.basename(filename))

                dat = get_from_rastermeta(ifile, piter=self.piter,
                                          showlog=self.showlog)
                odata, self.ev = mnf_calc(dat, ncmps=ncmps, piter=self.piter,
                                          showlog=self.showlog,
                                          noisetxt=noise,
                                          fwdonly=self.cb_fwdonly.isChecked())

                ofile = set_export_filename(dat, odir, 'mnf')

                self.showlog('Exporting '+os.path.basename(ofile))
                export_raster(ofile, odata, drv='GTiff', piter=self.piter,
                              showlog=self.showlog)

        elif 'Raster' in self.indata:
            dat = self.indata['Raster']
            odata, self.ev = mnf_calc(dat, ncmps=ncmps, piter=self.piter,
                                      showlog=self.showlog,
                                      noisetxt=noise,
                                      fwdonly=self.cb_fwdonly.isChecked())

        self.outdata['Raster'] = odata
        return True


class PCA(BasicModule):
    """Perform PCA Transform."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ev = None

        self.sb_comps = QtWidgets.QSpinBox()
        self.cb_fwdonly = QtWidgets.QCheckBox('Forward Transform Only.')
        self.cb_fitlist = QtWidgets.QCheckBox('Fit PCA to all files.')

        self.setupui()

        self.resize(500, 350)

    def setupui(self):
        """
        Set up UI.

        Returns
        -------
        None.

        """
        gl_main = QtWidgets.QGridLayout(self)
        buttonbox = QtWidgets.QDialogButtonBox()
        helpdocs = menu_default.HelpButton('pygmi.rsense.pca')
        lbl_comps = QtWidgets.QLabel('Number of components:')

        self.cb_fwdonly.setChecked(True)
        self.cb_fitlist.setChecked(True)
        self.cb_fitlist.setVisible(False)
        self.sb_comps.setMaximum(10000)
        self.sb_comps.setMinimum(1)

        buttonbox.setOrientation(QtCore.Qt.Horizontal)
        buttonbox.setCenterButtons(True)
        buttonbox.setStandardButtons(buttonbox.Cancel | buttonbox.Ok)

        self.setWindowTitle('Principal Component Analysis')

        gl_main.addWidget(self.cb_fwdonly, 1, 0, 1, 2)
        gl_main.addWidget(lbl_comps, 2, 0, 1, 1)
        gl_main.addWidget(self.sb_comps, 2, 1, 1, 1)
        gl_main.addWidget(self.cb_fitlist, 3, 0, 1, 2)

        gl_main.addWidget(helpdocs, 6, 0, 1, 1)
        gl_main.addWidget(buttonbox, 6, 1, 1, 3)

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
        self.ev = None
        tmp = []
        if 'Raster' not in self.indata and 'RasterFileList' not in self.indata:
            self.showlog('No Satellite Data')
            return False

        if 'RasterFileList' in self.indata:
            self.cb_fitlist.setVisible(True)
            if len(self.indata['RasterFileList'][0].bands) > 5:
                self.sb_comps.setValue(5)

        if 'Raster' in self.indata:
            indata = self.indata['Raster']
            self.sb_comps.setMaximum(len(indata))
            if len(indata) > 5:
                self.sb_comps.setValue(5)

        if not nodialog:
            tmp = self.exec()
        else:
            tmp = 1

        if tmp != 1:
            return False

        self.acceptall()

        if not nodialog and self.ev is not None:
            ncmps = self.sb_comps.value()
            xvals = range(1, ncmps+1)

            plt.figure('Explained Variance')
            plt.subplot(1, 1, 1)
            plt.plot(xvals, self.ev)
            plt.xticks(xvals)
            plt.xlabel('Component')
            plt.ylabel('Explained Variance')
            plt.grid(True)
            plt.tight_layout()

            if hasattr(plt.get_current_fig_manager(), 'window'):
                plt.get_current_fig_manager().window.setWindowIcon(self.parent.windowIcon())

            plt.show()

        return True

    def changeoutput(self):
        """
        Change the interface to reflect whether full calculation is needed.

        Returns
        -------
        None.

        """
        uienabled = not self.cb_fwdonly.isChecked()
        self.sb_comps.setEnabled(uienabled)

    def saveproj(self):
        """
        Save project data from class.

        Returns
        -------
        None.

        """
        self.saveobj(self.sb_comps)
        self.saveobj(self.cb_fwdonly)
        self.saveobj(self.cb_fitlist)

    def acceptall(self):
        """
        Accept option.

        Updates self.outdata, which is used as input to other modules.

        Returns
        -------
        None.

        """
        ncmps = self.sb_comps.value()
        fitlist = self.cb_fitlist.isChecked()
        fwdonly = self.cb_fwdonly.isChecked()

        if 'RasterFileList' in self.indata:
            flist = self.indata['RasterFileList']

            sensors = [i.sensor for i in flist]
            sensors = list(set(sensors))

            if fitlist is True and len(sensors) > 1:
                self.showlog('Error: You have more than one sensor type in '
                             'your raster file list directory. Fit list is not'
                             ' possible.')
                return False

        odata = []

        if 'RasterFileList' in self.indata and fitlist is False:
            filename = flist[0].filename
            odir = os.path.join(os.path.dirname(filename), 'PCA')

            os.makedirs(odir, exist_ok=True)
            for ifile in flist:
                filename = ifile.filename

                self.showlog('Processing '+os.path.basename(filename))

                dat = get_from_rastermeta(ifile, piter=self.piter,
                                          showlog=self.showlog)
                odata, self.ev = pca_calc(dat, ncmps, piter=self.piter,
                                          showlog=self.showlog,
                                          fwdonly=fwdonly)

                ofile = set_export_filename(dat, odir, 'pca')

                self.showlog('Exporting '+os.path.basename(ofile))
                export_raster(ofile, odata, drv='GTiff', piter=self.piter,
                              showlog=self.showlog)

        elif 'RasterFileList' in self.indata and fitlist is True:
            odata, self.ev = pca_calc_fitlist(flist, ncmps, piter=self.piter,
                                              showlog=self.showlog,
                                              fwdonly=fwdonly)

        elif 'Raster' in self.indata:
            dat = self.indata['Raster']
            odata, self.ev = pca_calc(dat, ncmps, piter=self.piter,
                                      showlog=self.showlog,
                                      fwdonly=self.cb_fwdonly.isChecked())

        self.outdata['Raster'] = odata
        return True


def get_noise(x2d, mask, noisetype='', piter=iter):
    """
    Calculate noise dataset from original data.

    Parameters
    ----------
    x2d : numpy array
        Input array, of dimension (MxNxChannels).
    mask : numpy array
        mask of dimension (MxN).
    noisetype : str, optional
        Noise type to calculate. Can be 'diagonal', 'hv average' or ''.
        The default is ''.

    Returns
    -------
    nevals : numpy array
        Noise eigenvalues.
    nevecs : numpy array
        Noise eigenvectors.

    """
    mask = ~mask

    pbar = piter([1, 2, 3])
    next(pbar)

    if noisetype == 'diagonal':
        t1 = x2d[:-1, :-1]
        t2 = x2d[1:, 1:]
        noise = ne.evaluate('t1-t2')

        mask2 = mask[:-1, :-1]*mask[1:, 1:]
        noise = noise[mask2]

        ncov = blockwise_cov(noise.T)

    elif noisetype == 'hv average':
        t1 = x2d[:-1, :-1]
        t2 = x2d[1:, :-1]
        t3 = x2d[:-1, :-1]
        t4 = x2d[:-1, 1:]

        noise = ne.evaluate('(t1-t2+t3-t4)')

        mask2 = mask[:-1, :-1]*mask[1:, :-1]*mask[:-1, 1:]

        noise = noise[mask2]

        ncov = blockwise_cov(noise.T) / 4

    else:
        t1 = x2d[:-2, :-2]
        t2 = x2d[:-2, 1:-1]
        t3 = x2d[:-2, 2:]
        t4 = x2d[1:-1, :-2]
        t5 = x2d[1:-1, 1:-1]
        t6 = x2d[1:-1, 2:]
        t7 = x2d[2:, :-2]
        t8 = x2d[2:, 1:-1]
        t9 = x2d[2:, 2:]

        noise = ne.evaluate('(t1-2*t2+t3-2*t4+4*t5-2*t6+t7-2*t8+t9)')

        mask2 = (mask[:-2, :-2] * mask[:-2, 1:-1] * mask[:-2, 2:] *
                 mask[1:-1, :-2] * mask[1:-1, 1:-1] * mask[1:-1, 2:] *
                 mask[2:, :-2] * mask[2:, 1:-1] * mask[2:, 2:])

        noise = noise[mask2]

        ncov = blockwise_cov(noise.T) / 81

    del noise
    next(pbar)
    # Calculate evecs and evals
    nevals, nevecs = np.linalg.eig(ncov)

    next(pbar)

    return nevals, nevecs


def mnf_calc(dat, *, ncmps=None, noisetxt='hv average', showlog=print, piter=iter,
             fwdonly=True):
    """
    MNF Calculation.

    Parameters
    ----------
    dat : list of PyGMI Data.
        List of PyGMI Data.
    ncmps : int or None, optional
        Number of components to use for filtering. The default is None
        (meaning all).
    noisetxt : txt, optional
        Noise type. Can be 'diagonal', 'hv average' or 'quad'. The default is
        'hv average'.
    showlog : function, optional
        Function for printing text. The default is print.
    piter : function, optional
        Iteration function, used for progress bars. The default is iter.
    fwdonly : bool, optional
        Option to perform forward calculation only. The default is True.

    Returns
    -------
    odata : list of PyGMI Data.
        Output list of PyGMI Data. Can be forward or inverse transformed data.
    ev : numpy array
        Explained variance, from PCA.

    """
    x2d = []
    maskall = []
    dat = lstack(dat, piter=piter, showlog=showlog, commonmask=True)

    for j in dat:
        x2d.append(j.data)
        maskall.append(j.data.mask)

    maskall = np.moveaxis(maskall, 0, -1)
    x2d = np.moveaxis(x2d, 0, -1)
    x2dshape = list(x2d.shape)

    for i in dat:
        i.data = None

    mask = maskall[:, :, 0]

    showlog('Calculating noise data...')
    nevals, nevecs = get_noise(x2d, mask, noisetxt, piter)

    showlog('Calculating MNF...')
    Ln = np.power(nevals, -0.5)
    Ln = np.diag(Ln)

    W = np.dot(Ln, nevecs.T)

    x = x2d[~mask]
    del x2d

    Pnorm = blockwise_dot(x, W.T)

    pca = IncrementalPCA(n_components=ncmps)

    iold = 0
    showlog('Fitting PCA')
    for i in piter(np.linspace(0, Pnorm.shape[0], 20, dtype=int)):
        if i == 0:
            continue
        pca.partial_fit(Pnorm[iold: i])
        iold = i

    showlog('Calculating PCA transform...')

    x2 = np.zeros((Pnorm.shape[0], pca.n_components_))
    iold = 0
    for i in piter(np.linspace(0, Pnorm.shape[0], 20, dtype=int)):
        if i == 0:
            continue
        x2[iold: i] = pca.transform(Pnorm[iold: i])
        iold = i

    del Pnorm
    ev = pca.explained_variance_
    evr = pca.explained_variance_ratio_

    if fwdonly is False:
        showlog('Calculating inverse MNF...')
        Winv = np.linalg.inv(W)
        P = pca.inverse_transform(x2)
        x2 = blockwise_dot(P, Winv.T)
        del P
    else:
        x2dshape[-1] = ncmps
        maskall = maskall[:, :, :ncmps]

    datall = np.zeros(x2dshape, dtype=np.float32)
    datall[~mask] = x2
    datall = np.ma.array(datall, mask=maskall)

    del x2

    if fwdonly:
        odata = [i.copy(True) for i in dat[:ncmps]]
    else:
        odata = [i.copy() for i in dat]

    for j, band in enumerate(odata):
        band.data = datall[:, :, j]
        if fwdonly is True:
            band.dataid = (f'MNF{j+1} Explained Variance Ratio '
                           f'{evr[j]*100:.2f}%')

    del datall

    return odata, ev


def pca_calc(dat, ncmps=None,  showlog=print, piter=iter, fwdonly=True):
    """
    PCA Calculation.

    Parameters
    ----------
    dat : list of PyGMI Data.
        List of PyGMI Data.
    ncmps : int or None, optional
        Number of components to use for filtering. The default is None
        (meaning all).
    showlog : function, optional
        Function for printing text. The default is print.
    piter : function, optional
        Iteration function, used for progress bars. The default is iter.
    fwdonly : bool, optional
        Option to perform forward calculation only. The default is True.

    Returns
    -------
    odata : list of PyGMI Data.
        Output list of PyGMI Data. Can be forward or inverse transformed data.
    ev : numpy array
        Explained variance, from PCA.

    """
    x2d = []
    maskall = []
    dat = lstack(dat, piter=piter, commonmask=True, showlog=showlog)

    for j in dat:
        x2d.append(j.data)
        maskall.append(j.data.mask)

    maskall = np.moveaxis(maskall, 0, -1)
    x2d = np.moveaxis(x2d, 0, -1)
    x2dshape = list(x2d.shape)

    for i in dat:
        i.data = None

    mask = maskall[:, :, 0]

    x2d = x2d[~mask]

    pca = IncrementalPCA(n_components=ncmps)

    iold = 0
    showlog('Fitting PCA')
    for i in piter(np.linspace(0, x2d.shape[0], 20, dtype=int)):
        if i == 0:
            continue
        pca.partial_fit(x2d[iold: i])
        iold = i

    showlog('Calculating PCA transform...')

    x2 = np.zeros((x2d.shape[0], pca.n_components_))
    iold = 0
    for i in piter(np.linspace(0, x2d.shape[0], 20, dtype=int)):
        if i == 0:
            continue
        x2[iold: i] = pca.transform(x2d[iold: i])
        iold = i

    del x2d
    ev = pca.explained_variance_
    evr = pca.explained_variance_ratio_

    if fwdonly is False:
        showlog('Calculating inverse PCA...')
        x2 = pca.inverse_transform(x2)
    else:
        x2dshape[-1] = ncmps
        maskall = maskall[:, :, :ncmps]

    datall = np.zeros(x2dshape, dtype=np.float32)

    datall[~mask] = x2
    datall = np.ma.array(datall, mask=maskall)

    del x2

    if fwdonly:
        odata = [i.copy(True) for i in dat]
        odata = odata[:ncmps]
    else:
        odata = [i.copy() for i in dat]

    for j, band in enumerate(odata):
        band.data = datall[:, :, j]
        if fwdonly is True:
            band.dataid = (f'PCA{j+1} Explained Variance Ratio '
                           f'{evr[j]*100:.2f}%')
    del datall

    return odata, ev


def pca_calc_fitlist(flist, ncmps=None,  showlog=print, piter=iter,
                     fwdonly=True):
    """
    PCA Calculation with using list of files in common fit.

    Parameters
    ----------
    dat : list of PyGMI Data.
        List of PyGMI Data.
    ncmps : int or None, optional
        Number of components to use for filtering. The default is None
        (meaning all).
    showlog : function, optional
        Function for printing text. The default is print.
    piter : function, optional
        Iteration function, used for progress bars. The default is iter.
    fwdonly : bool, optional
        Option to perform forward calculation only. The default is True.

    Returns
    -------
    odata : list of PyGMI Data.
        Output list of PyGMI Data.Can be forward or inverse transformed data.
    ev : numpy array
        Explained variance, from PCA.

    """
    if isinstance(flist[0], list):
        filename = flist[0][0].filename
    else:
        filename = flist[0].filename

    odir = os.path.join(os.path.dirname(filename), 'PCA')
    os.makedirs(odir, exist_ok=True)

    for ifile in flist:
        if isinstance(ifile, list):
            filename = ifile[0].filename
        else:
            filename = ifile.filename

        showlog('Fitting '+os.path.basename(filename))

        dat = get_from_rastermeta(ifile, piter=piter, showlog=showlog)

        x2d = []
        maskall = []
        dat = lstack(dat, piter=piter, commonmask=True, showlog=showlog)

        for j in dat:
            x2d.append(j.data)
            maskall.append(np.ma.getmaskarray(j.data))

        maskall = np.moveaxis(maskall, 0, -1)
        x2d = np.moveaxis(x2d, 0, -1)
        x2dshape = list(x2d.shape)

        mask = maskall[:, :, 0]

        x2d = x2d[~mask]

        pca = IncrementalPCA(n_components=ncmps)

        iold = 0
        for i in piter(np.linspace(0, x2d.shape[0], 20, dtype=int)):
            if i == 0:
                continue
            pca.partial_fit(x2d[iold: i])
            iold = i

    for ifile in flist:
        if isinstance(ifile, list):
            filename = ifile[0].filename
        else:
            filename = ifile.filename

        showlog('Transforming '+os.path.basename(filename))

        dat = get_from_rastermeta(ifile, piter=piter, showlog=showlog)

        x2d = []
        maskall = []
        dat = lstack(dat, piter=piter, showlog=showlog)

        for j in dat:
            x2d.append(j.data)
            maskall.append(np.ma.getmaskarray(j.data))

        maskall = np.moveaxis(maskall, 0, -1)
        x2d = np.moveaxis(x2d, 0, -1)
        x2dshape = list(x2d.shape)

        mask = maskall[:, :, 0]

        x2d = x2d[~mask]

        x2 = np.zeros((x2d.shape[0], pca.n_components_))
        iold = 0
        for i in piter(np.linspace(0, x2d.shape[0], 20, dtype=int)):
            if i == 0:
                continue
            x2[iold: i] = pca.transform(x2d[iold: i])
            iold = i

        del x2d
        ev = pca.explained_variance_
        evr = pca.explained_variance_ratio_

        if fwdonly is False:
            showlog('Calculating inverse PCA...')
            x2 = pca.inverse_transform(x2)
        else:
            x2dshape[-1] = ncmps
            maskall = maskall[:, :, :ncmps]

        datall = np.zeros(x2dshape, dtype=np.float32)

        datall[~mask] = x2
        datall = np.ma.array(datall, mask=maskall)

        del x2

        if fwdonly:
            odata = [i.copy(True) for i in dat]
            odata = odata[:ncmps]
        else:
            odata = [i.copy() for i in dat]

        for j, band in enumerate(odata):
            band.data = datall[:, :, j]
            if fwdonly is True:
                band.dataid = (f'PCA{j+1} Explained Variance Ratio '
                               f'{evr[j]*100:.2f}%')
        del datall

        ofile = set_export_filename(dat, odir, 'pca')

        showlog('Exporting '+os.path.basename(ofile))
        export_raster(ofile, odata, drv='GTiff', piter=piter, compression='ZSTD',
                      showlog=showlog)

    return odata, ev


def _block_slices(dim_size, block_size):
    """
    Generate slice objects.

    Generator that yields slice objects for indexing into
    sequential blocks of an array along a particular axis.

    from: https://stackoverflow.com/questions/20983882/efficient-dot-products-of-large-memory-mapped-arrays

    Parameters
    ----------
    dim_size : int
        Dimension size.
    block_size : int
        Block size.

    Yields
    ------
    slice
        Slice to be used in blockwise_dot.
    """
    count = 0
    while True:
        yield slice(count, count + block_size, 1)
        count += block_size
        if count > dim_size:
            break


def blockwise_cov(A):
    """
    Blockwise covariance.

    Parameters
    ----------
    A : numpy array
        Matrix.

    Returns
    -------
    ncov : numpy array
        Covariance matrix.

    """
    A = A - np.mean(A, axis=1, keepdims=True)
    ncov = blockwise_dot(A, A.T) / (A.shape[1] - 1)

    return ncov


def blockwise_dot(A, B, max_elements=int(2**27)):
    """
    Compute the dot product of two matrices in a block-wise fashion.

    Only blocks of `A` with a maximum size of `max_elements` will be
    processed simultaneously.

    from : https://stackoverflow.com/questions/20983882/efficient-dot-products-of-large-memory-mapped-arrays

    Parameters
    ----------
    A : numpy array
        MxN matrix.
    B : Numpy array
        NxO matrix.
    max_elements : int, optional
        Maximum number of elements in a block. The default is int(2**27).

    Returns
    -------
    out : numpy array
        Output dot product.

    """
    m,  n = A.shape
    n1, o = B.shape

    if n1 != n:
        raise ValueError('matrices are not aligned')

    if A.flags.f_contiguous:
        # prioritize processing as many columns of A as possible
        max_cols = max(1, max_elements // m)
        max_rows = max_elements // max_cols

    else:
        # prioritize processing as many rows of A as possible
        max_rows = max(1, max_elements // n)
        max_cols = max_elements // max_rows

    out = np.empty((m, o), dtype=np.result_type(A, B))

    for mm in _block_slices(m, max_rows):
        out[mm, :] = 0
        for nn in _block_slices(n, max_cols):
            A_block = A[mm, nn].copy()  # copy to force a read
            out[mm, :] += np.dot(A_block, B[nn, :])
            del A_block

    return out


def _testfn():
    """Test routine."""
    ifile = r"D:\Workdata\PyGMI Test Data\Remote Sensing\Import\hyperion\EO1H1760802013198110KF_1T.ZIP"
    ifile = r"D:\Sentinel2\S2B_MSIL2A_20220428T073609_N0400_R092_T36JTN_20220428T105528.zip"

    ncmps = 5

    dat = get_data(ifile)

    pmnf, _ = mnf_calc(dat, ncmps=ncmps, fwdonly=False)

    for i, dati in enumerate(dat):  # [0, 5, 10, 13, 14, 15, 20, 25]:
        vmax = dati.data.max()
        vmin = dati.data.min()

        plt.figure(dpi=150)
        plt.title('█████████████████Old dat2 band'+str(i))
        plt.imshow(dati.data, vmin=vmin, vmax=vmax)
        plt.colorbar()
        plt.show()

        plt.figure(dpi=150)
        plt.title('New MNF denoised band'+str(i))
        plt.imshow(pmnf[i].data, vmin=vmin, vmax=vmax)
        plt.colorbar()
        plt.show()


def _testfn2():
    import sys
    from matplotlib import rcParams
    from pygmi.rsense.iodefs import ImportData

    rcParams['figure.dpi'] = 150

    ifile = r"D:\Workdata\PyGMI Test Data\Remote Sensing\Import\Sentinel-2\S2A_MSIL2A_20210305T075811_N0214_R035_T35JML_20210305T103519.zip"

    app = QtWidgets.QApplication(sys.argv)  # Necessary to test Qt Classes

    os.chdir(os.path.dirname(ifile))

    tmp = ImportData()
    tmp.settings()

    dat = tmp.outdata['Raster']

    tmp = PCA()
    # tmp = MNF()
    tmp.indata['Raster'] = dat
    try:
        tmp.settings()
    except MemoryError:
        print("error")
        return

    outdat = tmp.outdata['Raster']

    for i, dat in enumerate(outdat):

        plt.subplot(121)
        plt.title(dat.dataid)
        vmin = dat.data.mean()-dat.data.std()*2
        vmax = dat.data.mean()+dat.data.std()*2
        plt.imshow(dat.data, vmin=vmin, vmax=vmax)
        plt.show()


def _testfn3():
    import sys
    from pygmi.rsense.iodefs import ImportBatch

    idir = r'd:\aster'
    os.chdir(r'D:\\')

    app = QtWidgets.QApplication(sys.argv)

    tmp1 = ImportBatch()
    tmp1.idir = idir
    tmp1.settings()

    dat = tmp1.outdata

    # tmp2 = PCA()
    tmp2 = MNF()
    tmp2.indata = dat
    tmp2.settings()


if __name__ == "__main__":
    _testfn2()
