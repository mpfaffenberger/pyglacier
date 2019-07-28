from spatial_image import SpatialImage
import dateutil.parser
import gdal
import numpy as np


class Landsat8Image(SpatialImage):
    def __init__(self, s3bucket, s3key, image_id):
        self.path_prefix = (
            "/vsis3/" + s3bucket + "/" + s3key + "/" + image_id + "/" + image_id
        )
        self.s3bucket = s3bucket
        self.s3key = s3key
        self.image_id = image_id
        super(Landsat8Image, self).__init__(self.path_prefix + "_B1.TIF")
        self.metadata = gdal.Dataset.GetMetadata(self.image, "IMD")
        self.num_bands = 8
        self.datasets = [self.get_band(i) for i in range(0, self.num_bands)]
        self.bands = [self.datasets[i][1] for i in range(0, self.num_bands)]
        self.dtype = np.ushort

    def get_band(self, num):
        dataset = gdal.Open(self.path_prefix + "_B" + str(num + 1) + ".TIF")
        band = dataset.GetRasterBand(1)
        return [dataset, band]

    def get_band_overview(self, band_num, overview_num):
        return self.bands[band_num - 1].GetOverview(overview_num)

    def get_projection(self):
        return self.image.GetProjection()

    def get_x_size(self):
        return self.image.RasterXSize

    def get_y_size(self):
        return self.image.RasterYSize

    def get_radiance_add(self, band):
        return float(
            self.metadata[
                "L1_METADATA_FILE.RADIOMETRIC_RESCALING.RADIANCE_ADD_BAND_" + str(band)
            ]
        )

    def get_radiance_mult(self, band):
        return float(
            self.metadata[
                "L1_METADATA_FILE.RADIOMETRIC_RESCALING.RADIANCE_MULT_BAND_" + str(band)
            ]
        )

    def get_n_bands(self):
        return 1

    def get_datetime(self):
        datestring = self.metadata["L1_METADATA_FILE.METADATA_FILE_INFO.FILE_DATE"]
        return dateutil.parser.parse(datestring)

    def get_sensor_model(self):
        return self.image.GetGeoTransform()

    def get_cloud_cover(self):
        return float(self.metadata["L1_METADATA_FILE.IMAGE_ATTRIBUTES.CLOUD_COVER"])

    def get_pixel_tensor(self, band_list):
        bands = [self.bands[i] for i in band_list]
        return self.make_pixel_tensor(bands, self.get_x_size(), self.get_y_size())

    def get_overview_tensor(self, overview_num, band_list):
        ovr = self.get_band_overview(1, overview_num)
        ovr_x = ovr.XSize
        ovr_y = ovr.YSize
        ovrs = [self.get_band_overview(i, overview_num) for i in band_list]
        return self.make_pixel_tensor(ovrs, ovr_x, ovr_y)

    def make_pixel_tensor(self, bands, x_size, y_size):
        tensor = np.empty([len(bands), y_size, x_size], self.dtype)
        for i in range(0, len(bands)):
            data = bands[i].ReadAsArray()
            tensor[i] = data
        return tensor.reshape([len(bands), y_size, x_size])

    @staticmethod
    def get_rgb_band_list():
        return [4, 3, 2]

    def close(self):
        self.image = None
        self.bands = None
