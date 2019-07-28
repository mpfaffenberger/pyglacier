from pymongo import MongoClient
import dateutil.parser
import geo_utils


class DBAccess(object):
    def insert_record(self, record):
        pass

    def query(self, min_lon, min_lat, max_lon, max_lat, cloud_cover):
        pass


class MongoDBAccess(DBAccess):
    def __init__(self, hostname, port):
        self.client = MongoClient(hostname, port)

    def insert_record(self, record):
        record["acquisitionDate"] = dateutil.parser.parse(record["acquisitionDate"])
        record["cloudCover"] = float(record["cloudCover"])
        record["path"] = record["path"].zfill(3)
        record["row"] = record["row"].zfill(3)
        record["min_lat"] = float(record["min_lat"])
        record["min_lon"] = float(record["min_lon"])
        record["max_lat"] = float(record["max_lat"])
        record["max_lon"] = float(record["max_lon"])
        polygon = geo_utils.create_bbox_polygon(
            record["min_lon"], record["min_lat"], record["max_lon"], record["max_lat"]
        )
        record["wkt"] = polygon.wkt
        centroid = polygon.centroid.xy
        record["centroid"] = {
            "type": "Point",
            "coordinates": [centroid[0][0], centroid[1][0]],
        }
        self.client.ls8.images.insert_one(record)

    def query(self, min_lon, min_lat, max_lon, max_lat, cloud_cover):
        q = self.client.ls8.images.find(
            {
                "centroid": {
                    "$within": {"$box": [[min_lon, min_lat], [max_lon, max_lat]]}
                },
                "cloudCover": {"$lte": cloud_cover},
            }
        )
        return q

    def query_box(self, box, cloud_cover=10):
        return self.query(box[0], box[1], box[2], box[3], cloud_cover)
