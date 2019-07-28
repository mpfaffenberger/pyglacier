import gdal
from gdal import gdalconst
import numpy as np


class SpatialImage(object):
    gdal.AllRegister()

    def __init__(self, path):
        self.image = gdal.Open(path)
        self.gdal2nump = dict()
        self.gdal2nump[gdalconst.GDT_Byte] = np.ubyte
        self.gdal2nump[gdalconst.GDT_UInt16] = np.ushort
        self.gdal2nump[gdalconst.GDT_Int16] = np.short
        self.gdal2nump[gdalconst.GDT_UInt32] = np.uint32
        self.gdal2nump[gdalconst.GDT_Float32] = np.float32

    def get_projection(self):
        return gdal.Dataset.GetProjection(self.image)

    def get_x_size(self):
        return gdal.Dataset.RasterXSize(self.image)

    def get_y_size(self):
        return gdal.Dataset.RasterYSize(self.image)

    def get_n_bands(self):
        return gdal.Dataset.RasterCount(self.image)

    def get_datetime(self):
        pass

    def get_sensor_model(self):
        pass

    def close(self):
        self.image = None
