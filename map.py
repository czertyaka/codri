#!/usr/bin/python3

import rasterio as rsio
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from pyproj import Transformer, Geod


def _log(msg):
    print("map: " + msg)


class Map(object):
    """Contains geospatial data for area of interest"""

    def __init__(self, filename):
        self.__img = rsio.open(filename)
        _log(
            f"opened image '{filename}'; bounds = {self.__img.bounds}, "
            f"crs = {self.__img.crs}, width = {self.__img.width} pix, height "
            f"= {self.__img.height} pix"
        )
        self.__data = np.uint8(self.__img.read(1))
        ret, self.__data = cv.threshold(
            self.__data, 2, 0, cv.THRESH_TOZERO_INV
        )
        if not ret:
            _log("failed to reduce cloud/shadow/snow/ice areas")
            exit()
        ret, self.__data = cv.threshold(self.__data, 1, 255, cv.THRESH_BINARY)
        if not ret:
            _log("failed to make image binary")
            exit()

    def plot(self):
        plt.imshow(self.__data)
        plt.show()

    @property
    def img(self):
        return self.__img

    @property
    def data(self):
        return self.__data


def transform_coo(coo, crs="EPSG:4326"):
    if crs == "EPSG:4326":
        return coo
    transformer = Transformer.from_crs(crs, "EPSG:4326")
    coo["lat"], coo["lon"] = transformer.transform(
        yy=coo["lat"], xx=coo["lon"]
    )
    return coo


def distance(coo0, coo1, crs="EPSG:4326"):
    coo0 = transform_coo(coo0, crs)
    coo1 = transform_coo(coo1, crs)
    geod = Geod(ellps="WGS84")
    return geod.line_length(
        [coo0["lon"], coo1["lon"]], [coo0["lat"], coo1["lat"]]
    )


if __name__ == "__main__":
    map = Map(r"water.tif")
    height = distance(
        {"lon": map.img.bounds.left, "lat": map.img.bounds.top},
        {"lon": map.img.bounds.left, "lat": map.img.bounds.bottom},
        crs=map.img.crs,
    )
    width = distance(
        {"lon": map.img.bounds.left, "lat": map.img.bounds.top},
        {"lon": map.img.bounds.right, "lat": map.img.bounds.top},
        crs=map.img.crs,
    )
    _log(f"height = {height:.3f} m, width = {width:.3f} m")
    map.plot()
