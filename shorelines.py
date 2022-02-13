#!/usr/bin/python3

import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import AutoMinorLocator
from map import Map, transform_coo
import shapely.geometry as geom


def _log(msg):
    print("shorelines: " + msg)


class ShorelineContour(object):
    """Holds data on single shoreline contour"""

    def __init__(self, points, closed=True):
        self.__points = points
        self.__closed = closed

    @property
    def points(self):
        return self.__points

    @property
    def closed(self):
        return self.__closed


class ShorelinesFinder(object):
    """Makes polygons for all shorelines presented on map"""

    def __init__(self, map, approx_error=3):
        self.__approx_error = approx_error
        self.__map = map
        pix_cnts = self.__find_contours()
        self.__coord_cnts(pix_cnts)

    def __find_contours(self):
        pix_cnts, hierarchy = cv.findContours(
            self.__map.data, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE
        )
        _log(f"found {len(pix_cnts)} shorelines")
        return pix_cnts

    def __coord_cnts(self, pix_cnts):
        _log(
            "Douglas-Peucker approximation algorithm epsilon = "
            f"{self.__approx_error}%"
        )
        self.__cnts = []
        for pix_cnt in pix_cnts:
            pix_cnt = cv.approxPolyDP(pix_cnt, self.__approx_error, True)
            if len(pix_cnt) < 3:
                continue
            coord_cnt = []
            for pix_vertice in pix_cnt:
                pix_vertice = pix_vertice[0]
                coord_vertice = self.__map.img.xy(
                    pix_vertice[1], pix_vertice[0]
                )
                coord_cnt.append(coord_vertice)
            # TODO: estimate if contour is opened
            self.__cnts.append(ShorelineContour(points=np.array(coord_cnt)))
        _log(f"added {len(self.__cnts)} shorelines")
        self.__cnts = np.array(self.__cnts)

    def get_cnt(self, coo, crs="EPSG:4326"):
        coo = transform_coo(coo, crs)
        point = geom.Point(lon, lat)
        for cnt in self.__cnts:
            polygon = geom.polygon.Polygon(cnt.points)
            if polygon.contains(point):
                return cnt
        return np.array([])

    def plot(self):
        fig, ax = plt.subplots()
        for cnt in self.contours:
            polygon = Polygon(cnt.points, fill=False, ec="blue")
            ax.add_patch(polygon)

        ax.set_xlim([self.__map.img.bounds.left, self.__map.img.bounds.right])
        ax.set_ylim([self.__map.img.bounds.bottom, self.__map.img.bounds.top])
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(axis="both", which="both")
        ax.tick_params(axis="both", which="minor", grid_linestyle="--")
        plt.grid(visible=True, which="both", axis="both", alpha=0.3)
        plt.axis("scaled")
        plt.show()

    @property
    def contours(self):
        return self.__cnts

    @property
    def map(self):
        return self.__map


if __name__ == "__main__":
    map = Map(r"water.tif")
    finder = ShorelinesFinder(map=map, approx_error=1)
    lon = 6795000
    lat = 7493000
    _log(
        f"shoreline contour for lon = {lon}; lat={lat}:\n"
        f"{finder.get_cnt(coo={'lon': lon, 'lat': lat}, crs='EPSG:3857').points}"  # noqa: E501
    )
    finder.plot()
