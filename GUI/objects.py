from tifffile import imread
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QDialog, QSizePolicy, QApplication, QTableWidget, QVBoxLayout,
                            QPushButton, QColorDialog, QTableWidgetItem, QMessageBox)
from PyQt5.QtGui import QCursor, QColor
from PyQt5.QtCore import Qt
from matplotlib.colors import LinearSegmentedColormap
import copy, re
from ast import literal_eval

'''
# classes
'''

class PointObjects():
    def __init__(self, points_meta):
        self.meta = points_meta        # self.meta['coords'] = [ np.array([]) for _id in points_meta['_ids'] ]

    def updatePoints(self, current_id, coord, event):
        # print('Mouse clicked! ', event)
        current_idx = self.meta['_ids'].index(current_id)
        points = self.meta['coords'][current_idx]
        _idxs = np.arange(points.shape[0])

        # LEFT CLICK: add point
        if event.button == 1:
            if points.shape[0]!=0:
                self.meta['coords'][current_idx] = np.append(self.meta['coords'][current_idx],np.array([coord]),axis=0)
            else:
                self.meta['coords'][current_idx] = np.array([coord])

        # RIGHT CLICK: remove point from the same contraction phase and focal plane
        if event.button == 3:
            new_points = []
            new_idxs = []
            for i, p in enumerate(points): # filter only points in the same focal plane and contraction phase
                if p[2] == coord[2]: # same focal plane
                    if p[3] == coord[3]: # same contraction phase
                        new_points.append(p) # save the poiont
                        new_idxs.append(i)   # save the original index
            points = np.array(new_points)
            _idxs = np.array(new_idxs)

            # now find the closest point to the click and remove it
            if len(_idxs) != 0:
                dist = [ np.linalg.norm(coord[:3]-c1) for c1 in points[:,:3] ]
                i = np.where(dist==np.min(dist))[0]
                self.meta['coords'][current_idx] = np.delete(self.meta['coords'][current_idx], _idxs[i], axis=0)

        self.updatePointMeta()
    
    def updatePointMeta(self):
        for i, ps in enumerate( self.meta['coords'] ):
            if ps.shape[0]>0:
                self.meta['is_instance'][i] = 1
            else:
                self.meta['is_instance'][i] = 0
