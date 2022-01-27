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
        self.img = rsio.open(filename)
        _log(f"opened image '{filename}'; bounds = {self.img.bounds}, crs = {self.img.crs}, "
            f"width = {self.img.width} pix, height = {self.img.height} pix")
        self.data = np.uint8(self.img.read(1))
        ret, self.data = cv.threshold(self.data, 2, 0, cv.THRESH_TOZERO_INV)
        if not ret:
            _log("failed to reduce cloud/shadow/snow/ice areas")
            exit()
        ret, self.data = cv.threshold(self.data, 1, 255, cv.THRESH_BINARY)
        if not ret:
            _log("failed to make image binary")
            exit()

    def plot(self):
        plt.imshow(self.data)
        plt.show()

def distance(coo0, coo1, crs='EPSG:3857'):
    transformer = Transformer.from_crs(crs, 'EPSG:4326')
    coo0['lat'], coo0['lon'] = transformer.transform(yy = coo0['lat'], xx = coo0['lon'])
    coo1['lat'], coo1['lon'] = transformer.transform(yy = coo1['lat'], xx = coo1['lon'])
    geod = Geod(ellps="WGS84")
    return geod.line_length([coo0['lon'], coo1['lon']], [coo0['lat'], coo1['lat']])

if __name__ == '__main__':
    map = Map(r'water.tif')
    height = distance({'lon': map.img.bounds.left, 'lat': map.img.bounds.top},
        {'lon': map.img.bounds.left, 'lat': map.img.bounds.bottom}, crs = map.img.crs)
    width = distance({'lon': map.img.bounds.left, 'lat': map.img.bounds.top},
        {'lon': map.img.bounds.right, 'lat': map.img.bounds.top}, crs = map.img.crs)
    _log(f"height = {height:.3f} m, width = {width:.3f} m")
    map.plot()