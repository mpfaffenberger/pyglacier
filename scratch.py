from landsat_image import Landsat8Image
import image_processing
import cv2
import numpy as np
import csv
import geo_utils
from db_access import MongoDBAccess
from shapely.wkt import loads as wkt_loads
import pandas as pd


def ingest():
    db = MongoDBAccess("localhost", 27017)
    count = 0
    with open("/home/mpfaffenberger/Downloads/old_scene_list", "r") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        for record in reader:
            db.insert_record(record)
            count += 1
            if count % 10000 == 0:
                print(count)


def query():
    db = MongoDBAccess("localhost", 27017)
    polystring = "POLYGON((-23.162464581562972 78.34002324953876,-16.922230206562972 78.34002324953876,-16.922230206562972 76.8502434407094,-23.162464581562972 76.8502434407094,-23.162464581562972 78.34002324953876))"
    poly = wkt_loads(polystring)
    bounds = poly.bounds
    results = db.query_box(bounds, cloud_cover=5)
    df = pd.DataFrame([item for item in results])
    df["productId"] = df["productId"].map(lambda x: "" if type(x) is not str else x)
    df = geo_utils.filter_query_results(df, poly)
    df.to_csv("/tmp/query.tsv", sep="\t")
    print(df.shape)
    frames = []
    for idx, item in df.iterrows():
        if len(item["productId"]):
            frames.append(
                write_overview(
                    create_c1_l8_image(item), item["acquisitionDate"]
                )
            )
        else:
            frames.append(
                write_overview(
                    create_l8_image(item), item["acquisitionDate"]
                )
            )
    df["frame"] = frames
    df = df.sort_values(by="acquisitionDate", ascending=True)
    make_video(df["frame"])
    print("test")


def write_overview(l8_image, timestamp):
    overview = l8_image.get_overview_tensor(0, [1]).astype(np.float64)
    # band2 = (l8_image.get_radiance_add(2), l8_image.get_radiance_mult(2))
    # band3 = (l8_image.get_radiance_add(3), l8_image.get_radiance_mult(3))
    # band4 = (l8_image.get_radiance_add(4), l8_image.get_radiance_mult(4))
    # overviews[0] = band2[1]*overviews[0] + band2[0]
    # overviews[1] = band3[1]*overviews[1] + band3[0]
    # overviews[2] = band4[1]*overviews[2] + band4[0]
    overview[0] = image_processing.clahe_rescale(overview[0])
    new_overview = overview.astype(np.uint8)
    new_overview = np.rollaxis(new_overview, 0, 3)
    new_overview = cv2.cvtColor(new_overview, cv2.COLOR_GRAY2RGB)
    new_overview = cv2.putText(
        new_overview,
        str(timestamp),
        (100, new_overview.shape[1] - 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        3,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )

    return new_overview


def make_video(frames):
    codec = cv2.VideoWriter_fourcc(*"XVID")
    video = cv2.VideoWriter("/tmp/video.avi", codec, 1.0, (2048, 2048))
    for frame in frames:
        frame = cv2.resize(frame, (2048, 2048), interpolation=cv2.INTER_LANCZOS4)
        video.write(frame)
    video.release()


def create_l8_image(record):
    s3bucket = "landsat-pds"
    s3key = "L8/" + record["path"] + "/" + record["row"]
    image_id = record["entityId"]
    l8 = Landsat8Image(s3bucket, s3key, image_id)
    return l8


def create_c1_l8_image(record):
    s3bucket = "landsat-pds"
    s3key = "c1/L8/" + record["path"] + "/" + record["row"]
    image_id = record["productId"]
    l8 = Landsat8Image(s3bucket, s3key, image_id)
    return l8


# query()
# ingest()
