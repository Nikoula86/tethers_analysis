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

def loadStacks(file_name):
    print('#'*40)
    print('Loading dataset at:\n\t', file_name)
    stacks = imread(file_name)[:,:,::-1,:,:]
    _maxval = np.zeros((stacks.shape[0],stacks.shape[2]))
    for i in range(stacks.shape[0]):
        for j in range(stacks.shape[2]):
            _maxval[i,j] = np.max(stacks[i,:,j,:,:])
    print('Stack shape (TZCHW):', stacks.shape)
    print('Done')
    return stacks, _maxval

def swapAxes(stacks, _maxval, ax = 0):
    stacks = np.flip( stacks, axis = ax )
    _maxval = np.flip(_maxval,axis = ax-2)
    return stacks, _maxval

def convertPoints(oldData):
    new = {'_ids': ['tether_Atrium','tether_Ventricle','AVCanal','Midline'],
                        'colors': ['#6eadd8','#ff7f0e','red','#c4c4c4'],
                        'markers': ['o','o','X','-x'],
                        'ms': [3,3,5,1],
                        'is_instance': [0,0,0,0],
                        'coords': [np.array([])]*4 }
    for key in oldData:
        i = new['_ids'].index(key)
        new['coords'][i] = oldData[key]
        if oldData[key].shape[0]>0:
            new['is_instance'][i] = 1
    return new

