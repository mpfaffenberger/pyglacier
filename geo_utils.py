from shapely.geometry import Polygon, MultiPoint, Point
from shapely.wkt import loads as wkt_loads
from geographiclib.geodesic import Geodesic
from sklearn.cluster import DBSCAN
from typing import List, Tuple
import pandas as pd


def create_polygon(coords):
    polygon = Polygon(coords)
    return polygon


def create_bbox_polygon(min_lon, min_lat, max_lon, max_lat):
    ul = (min_lon, max_lat)
    ur = (max_lon, max_lat)
    lr = (max_lon, min_lat)
    ll = (min_lon, min_lat)
    coords = [ul, ur, lr, ll, ul]
    return create_polygon(coords)


def filter_query_results(image_metadata: pd.DataFrame, query: Polygon) -> pd.DataFrame:
    coords = image_metadata["wkt"].map(lambda wkt: wkt_loads(wkt).centroid.coords[0])
    clusters, cluster_centroids = cluster_entities(list(coords))
    query_center = query.centroid
    geodesic = Geodesic.WGS84
    distances = []
    for clst in cluster_centroids:
        distance = geodesic.Inverse(query_center.y, query_center.x, clst.y, clst.x)
        distances.append(distance["s12"])
    centroid_df = pd.DataFrame()
    centroid_df["centroid"] = cluster_centroids
    centroid_df["distance"] = distances
    centroid_df["idx"] = centroid_df.index
    centroid_df = centroid_df.sort_values(by="distance", ascending=True)
    winner = list(centroid_df["idx"])[0]
    image_metadata["cluster"] = clusters
    return image_metadata[image_metadata["cluster"] == winner]


def cluster_entities(coords: List[Tuple[float]]) -> Tuple[List[int], List[Point]]:
    xs = [item[0] for item in coords]
    ys = [item[1] for item in coords]
    dbscan = DBSCAN()
    clusters = dbscan.fit_predict(coords)
    cdf = pd.DataFrame()
    cdf["x"] = xs
    cdf["y"] = ys
    cdf["cluster"] = clusters
    cluster_centroids = []
    for cluster in set(cdf.cluster) - {0}:
        points = cdf[cdf.cluster == cluster]
        geom_collection = MultiPoint([Point(i) for i in zip(points.x, points.y)])
        cluster_centroids.append(geom_collection.convex_hull.centroid)
    return clusters, cluster_centroids
