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
""" Import Data """

from PyQt4 import QtGui
from .datatypes import Data
from ..clust.datatypes import Clust
import numpy as np
from osgeo import gdal, osr
import struct
from .dataprep import merge
import os
# from ..ptimer import PTime


class ImportData(object):
    """
    Import Data - Interfaces with GDAL routines

    Attributes
    ----------
    name : str
        item name
    pbar : progressbar
        reference to a progress bar.
    parent : parent
        reference to the parent routine
    outdata : dictionary
        dictionary of output datasets
    ifile : str
        input file name. Used in main.py
    ext : str
        filename extension
    """
    def __init__(self, parent=None):
        self.ifile = ""
        self.name = "Import Data: "
        self.ext = ""
        self.pbar = None
        self.parent = parent
        self.indata = {}
        self.outdata = {}

    def settings(self):
        """ Settings """
        ext = \
            "ERMapper (*.ers);;" + \
            "ENVI (*.hdr);;" + \
            "GeoTiff (*.tif);;" + \
            "Geosoft (*.gxf);;" + \
            "Surfer grid (v.6) (*.grd);;" + \
            "ASCII with .hdr header (*.asc);;" + \
            "ASCII XYZ (*.xyz);;" + \
            "ArcGIS BIL (*.bil)"

        filename = QtGui.QFileDialog.getOpenFileName(
            self.parent, 'Open File', '.', ext)
        if filename == '':
            return False
        os.chdir(filename.rpartition('/')[0])
        self.ifile = str(filename)
        self.ext = filename[-3:]

        if self.ext == 'asc':
            dat = get_ascii(self.ifile)
        else:
            dat = get_raster(self.ifile)

        output_type = 'Raster'
        if 'Cluster' in dat[0].dataid:
            output_type = 'Cluster'

        self.outdata[output_type] = dat
        return True


def get_ascii(ifile):
    """
    Import ascii raster dataset

    Parameters
    ----------
    ifile : str
        filename to import

    Returns
    -------
    dat : PyGMI raster Data
        dataset imported
    """

    afile = open(ifile, 'r')
    adata = afile.read()

    adata = adata.split()
    adata = np.array(adata, dtype=float)

    hfile = open(ifile[:-3]+'hdr', 'r')
    tmp = hfile.readlines()

    xdim = float(tmp[0].split()[-1])
    ydim = float(tmp[1].split()[-1])
    ncols = int(tmp[2].split()[-1])
    nrows = int(tmp[3].split()[-1])
    nbands = int(tmp[4].split()[-1])
    ulxmap = float(tmp[5].split()[-1])
    ulymap = float(tmp[6].split()[-1])
    bandid = ifile[:-4].rsplit('/')[-1]

    adata.shape = (nrows, ncols)

    if nbands > 1:
        print('PyGMI only supports single band ASCII files')

    dat = [Data()]
    i = 0

    dat[i].data = adata

    nval = -9999.0

    dat[i].data = np.ma.masked_equal(dat[i].data, nval)
    if dat[i].data.mask.size == 1:
        dat[i].data.mask = (np.ma.make_mask_none(dat[i].data.shape) +
                            dat[i].data.mask)

    dat[i].nrofbands = nbands
    dat[i].tlx = ulxmap
    dat[i].tly = ulymap
    dat[i].dataid = bandid
    dat[i].nullvalue = nval
    dat[i].rows = nrows
    dat[i].cols = ncols
    dat[i].xdim = xdim
    dat[i].ydim = ydim

    return dat


def get_raster(ifile):
    """
    This function loads a raster dataset off the disk using the GDAL
    libraries. It returns the data in a PyGMI data object.

    Parameters
    ----------
    ifile : str
        filename to import

    Returns
    -------
    dat : PyGMI raster Data
        dataset imported
    """
    dat = []
    bname = ifile.split('/')[-1].rpartition('.')[0]+': '
    ifile = ifile[:]
    ext = ifile[-3:]
    if ext == 'hdr':
        ifile = ifile[:-4]

    dataset = gdal.Open(ifile, gdal.GA_ReadOnly)
    gtr = dataset.GetGeoTransform()
#    output_type = 'Raster'

    for i in range(dataset.RasterCount):
        rtmp = dataset.GetRasterBand(i+1)
        bandid = rtmp.GetDescription()
        nval = rtmp.GetNoDataValue()

        if 'Cluster' in bandid:
            # output_type = 'Cluster'
            dat.append(Clust())
        else:
            dat.append(Data())
        dat[i].data = rtmp.ReadAsArray()
        if dat[i].data.dtype.kind == 'i':
            if nval is None:
                nval = 999999
            nval = int(nval)
        else:
            if nval is None:
                nval = 1e+20
            nval = float(nval)
#            dtype = dat[i].data.dtype
#            if dtype != np.float64 and dtype != np.float32:
#                dat[i].data = dat[i].data.astype(np.float32)
#            if dtype == np.float64 or dtype == np.float32:
#                dat[i].data[dat[i].data == nval] = np.nan
        if ext == 'ers' and nval == -1.0e+32:
            dat[i].data[np.ma.less_equal(dat[i].data, nval)] = -1.0e+32
#                dat[i].data[np.ma.less_equal(dat[i].data, nval)] = np.nan

#            dat[i].data = np.ma.masked_invalid(dat[i].data)
# Note that because the data is stored in a masked array, the array ends up
# being double the size that it was on the disk.

        dat[i].data = np.ma.masked_equal(dat[i].data, nval)
        if dat[i].data.mask.size == 1:
            dat[i].data.mask = (np.ma.make_mask_none(dat[i].data.shape) +
                                dat[i].data.mask)

        dat[i].nrofbands = dataset.RasterCount
        dat[i].tlx = gtr[0]
        dat[i].tly = gtr[3]
        if bandid == '':
            bandid = bname+str(i+1)
        dat[i].dataid = bandid
        if bandid[-1] == ')':
            dat[i].units = bandid[bandid.rfind('(')+1:-1]

        dat[i].nullvalue = nval
        dat[i].rows = dataset.RasterYSize
        dat[i].cols = dataset.RasterXSize
        dat[i].xdim = abs(gtr[1])
        dat[i].ydim = abs(gtr[5])
        dat[i].gtr = gtr

        srs = osr.SpatialReference()
        srs.ImportFromWkt(dataset.GetProjection())
        srs.AutoIdentifyEPSG()

        dat[i].wkt = srs.ExportToWkt()

        if 'Cluster' in bandid:
            dat[i].no_clusters = int(dat[i].data.max()+1)
#                dat[i].no_clusters = np.unique(dat[i].data).count()

    return dat


class ExportData(object):
    """
    Export Data

    Attributes
    ----------
    name : str
        item name
    pbar : progressbar
        reference to a progress bar.
    parent : parent
        reference to the parent routine
    outdata : dictionary
        dictionary of output datasets
    ifile : str
        input file name. Used in main.py
    ext : str
        filename extension
    """
    def __init__(self, parent):
        self.ifile = ""
        self.name = "Export Data: "
        self.ext = ""
        self.pbar = None
        self.parent = parent
        self.indata = {}
        self.outdata = {}
#        self.dirname = ""

    def run(self):
        """ Show Info """
        if 'Cluster' in self.indata:
            data = self.indata['Cluster']
        elif 'Raster' in self.indata:
            data = self.indata['Raster']
        else:
            self.parent.showprocesslog('No raster data')
            return

        ext = \
            "ENVI (*.hdr);;" + \
            "ERMapper (*.ers);;" + \
            "GeoTiff (*.tif);;" + \
            "Geosoft (*.gxf);;" + \
            "Surfer grid (v.6) (*.grd);;" + \
            "ArcInfo ASCII (*.asc);;" + \
            "ASCII XYZ (*.xyz);;" + \
            "ArcGIS BIL (*.bil)"

        filename = QtGui.QFileDialog.getSaveFileName(
            self.parent, 'Save File', '.', ext)
        if filename == '':
            return False
        os.chdir(filename.rpartition('/')[0])

        self.ifile = str(filename)
        self.ext = filename[-3:]

    # Pop up save dialog box
        if self.ext == 'ers':
            self.export_gdal(data, 'ERS')
        if self.ext == 'gxf':
            self.export_gxf(data)
        if self.ext == 'grd':
            self.export_surfer(data)
        if self.ext == 'asc':
            self.export_ascii(data)
        if self.ext == 'xyz':
            self.export_ascii_xyz(data)
        if self.ext == 'tif':
            self.export_gdal(data, 'GTiff')
        if self.ext == 'hdr':
            self.export_gdal(data, 'ENVI')
        if self.ext == 'bil':
            self.export_gdal(data, 'EHdr')

        self.parent.showprocesslog('Finished!')

    def export_gdal(self, dat, drv):
        """
        Export to GDAL format

        Parameters
        ----------
        dat : PyGMI raster Data
            dataset to export
        drv : str
            name of the GDAL driver to use
        """

        data = merge(dat)
        xmin = data[0].tlx
        ymax = data[0].tly

        driver = gdal.GetDriverByName(drv)
        dtype = data[0].data.dtype

        if dtype == np.uint8:
            fmt = gdal.GDT_Byte
        elif dtype == np.int32:
            fmt = gdal.GDT_Int32
        elif dtype == np.float64:
            fmt = gdal.GDT_Float64
        else:
            fmt = gdal.GDT_Float32

        tmp = self.ifile.rpartition('.')

        if drv == 'GTiff':
            tmpfile = tmp[0] + '.tif'
        elif drv == 'EHdr':
            fmt = gdal.GDT_Float32
            dtype = np.float32
            tmpfile = tmp[0] + '.bil'
#        elif drv == 'VRT':
#            tmpfile = tmp[0] + '.vrt'
        else:
            tmpfile = tmp[0]

        out = driver.Create(tmpfile, int(data[0].cols),
                            int(data[0].rows), len(data), fmt)
        out.SetGeoTransform([xmin, data[0].xdim, 0, ymax, 0, -data[0].ydim])
#        orig = osr.SpatialReference()
#        orig.SetWellKnownGeogCS('WGS84')
#        orig.ImportFromEPSG(4222)  # Cape
#        orig.SetTM(0.0, 31.0, 1.0, 0.0, 0.0)
#        out.SetProjection(orig.ExportToWkt())

        out.SetProjection(data[0].wkt)

        for i in range(len(data)):
            rtmp = out.GetRasterBand(i+1)
            rtmp.SetDescription(data[i].dataid)

            dtmp = np.ma.array(data[i].data).astype(dtype)

            # This section tries to overcome null values with round off error
            # in 32-bit numbers.
            if dtype == np.float32:
                data[i].nullvalue = np.float64(np.float32(data[i].nullvalue))
                if data[i].data.min() > -1e+10:
                    data[i].nullvalue = np.float64(np.float32(-1e+10))
                elif data[i].data.max() < 1e+10:
                    data[i].nullvalue = np.float64(np.float32(1e+10))

            elif dtype == np.float or dtype == np.float64:
                data[i].nullvalue = np.float64(dtmp.fill_value)

            dtmp.set_fill_value(data[i].nullvalue)
            dtmp = dtmp.filled()

            if drv != 'GTiff':
                rtmp.SetNoDataValue(data[i].nullvalue)
            elif len(data) == 1:
                rtmp.SetNoDataValue(data[i].nullvalue)
            rtmp.WriteArray(dtmp)

        out = None  # Close File
        if drv == 'ENVI':
            with open(tmpfile+'.hdr', 'a') as myfile:
                myfile.write('data ignore value = ' + str(data[0].nullvalue))

    def export_gxf(self, data):
        """
        Export GXF data

        Parameters
        ----------
        data : PyGMI raster Data
            dataset to export
        """
        for k in data:
            file_out = self.get_filename(k, 'gxf')
            fno = open(file_out, 'w')

            xmin = k.tlx
#            xmax = k.tlx + k.cols*k.xdim
            ymin = k.tly - k.rows*k.ydim
#            ymax = k.tly

            fno.write("#TITLE\n")
            fno.write(self.name)
            fno.write("\n#POINTS\n")
            fno.write(str(k.cols))
            fno.write("\n#ROWS\n")
            fno.write(str(k.rows))
            fno.write("\n#PTSEPARATION\n")
            fno.write(str(k.xdim))
            fno.write("\n#RWSEPARATION\n")
            fno.write(str(k.ydim))
            fno.write("\n#XORIGIN\n")
            fno.write(str(xmin))
            fno.write("\n#YORIGIN\n")
            fno.write(str(ymin))
            fno.write("\n#SENSE\n")
            fno.write("1")
            fno.write("\n#DUMMY\n")
            fno.write(str(k.nullvalue))
            fno.write("\n#GRID\n")
            tmp = k.data.filled(k.nullvalue)

            for i in range(k.data.shape[0]-1, -1, -1):
                kkk = 0
# write only 5 numbers in a row
                for j in range(k.data.shape[1]):
                    if kkk == 5:
                        kkk = 0
                    if kkk == 0:
                        fno.write("\n")

                    fno.write(str(tmp[i, j]) + "  ")
                    kkk += 1

            fno.close()

    def export_surfer(self, data):
        """
        Export a surfer binary grid

        Parameters
        ----------
        data : PyGMI raster Data
            dataset to export
        """
        for k in data:
            file_out = self.get_filename(k, 'grd')
            fno = open(file_out, 'wb')

            xmin = k.tlx
            xmax = k.tlx + k.cols*k.xdim
            ymin = k.tly - k.rows*k.ydim
            ymax = k.tly

            bintmp = struct.pack('cccchhdddddd', b'D', b'S', b'B', b'B',
                                 k.cols, k.rows,
                                 xmin, xmax,
                                 ymin, ymax,
                                 np.min(k.data),
                                 np.max(k.data))
            fno.write(bintmp)

            ntmp = 1.701410009187828e+38
            tmp = (k.data.filled(ntmp)).astype('f')
            tmp = tmp[::-1]
            fno.write(tmp.tostring())

            fno.close()

    def export_ascii(self, data):
        """
        Export Ascii file

        Parameters
        ----------
        data : PyGMI raster Data
            dataset to export
        """
        for k in data:
            file_out = self.get_filename(k, 'asc')
            fno = open(file_out, 'w')

            xmin = k.tlx
#            xmax = k.tlx + k.cols*k.xdim
            ymin = k.tly - k.rows*k.ydim
#            ymax = k.tly

            fno.write("ncols \t\t\t" + str(k.cols))
            fno.write("\nnrows \t\t\t" + str(k.rows))
            fno.write("\nxllcorner \t\t\t" + str(xmin))
            fno.write("\nyllcorner \t\t\t" + str(ymin))
            fno.write("\ncellsize \t\t\t" + str(k.xdim))
            fno.write("\nnodata_value \t\t" + str(k.nullvalue))

            tmp = k.data.filled(k.nullvalue)

            for j in range(k.rows):
                fno.write("\n")
                for i in range(k.cols):
                    fno.write(str(tmp[j, i]) + " ")
                    # fno.write(str(data[0].data[j].data[i]) + " ")

            fno.close()

    def export_ascii_xyz(self, data):
        """
        Export and xyz file

        Parameters
        ----------
        data : PyGMI raster Data
            dataset to export
        """
        for k in data:
            file_out = self.get_filename(k, 'xyz')
            fno = open(file_out, 'w')

            tmp = k.data.filled(k.nullvalue)

            xmin = k.tlx
#            xmax = k.tlx + k.cols*k.xdim
#            ymin = k.tly - k.rows*k.ydim
            ymax = k.tly

            for j in range(k.rows):
                for i in range(k.cols):
                    fno.write(str(xmin+i*k.xdim) + " " +
                              str(ymax-j*k.ydim) + " " +
                              str(tmp[j, i]) + "\n")
            fno.close()

    def get_filename(self, data, ext):
        """
        Gets a valid filename

        Parameters
        ----------
        data : PyGMI raster Data
            dataset to get filename from
        ext : str
            filename extension to use
        """
        file_band = data.dataid.split('_')[0].strip('"')
        file_band = file_band.replace('/', '')
        file_band = file_band.replace(':', '')
        file_out = self.ifile.rpartition(".")[0]+"_"+file_band+'.'+ext

        return file_out
