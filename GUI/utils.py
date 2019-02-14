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
import copy, re, sys
from ast import literal_eval
import subWindows as sw

def loadStacks5D(file_name, app=False):
    print('#'*40)
    print('Loading dataset at:\n\t', file_name)
    stacks = imread(file_name)
    target_id = 'TZCHW'

    # append dimensions if necessary
    if not app:
        app = QApplication(sys.argv)
    ddef = sw.DimensionDefiner(shape=stacks.shape)
    ddef.show()
    if ddef.exec_() == QDialog.Accepted:
        input_id = ddef.text
        # find the missing id
        missing_id = copy.deepcopy(target_id)
        for i in input_id:
            missing_id = missing_id.replace(i,'')
        # append dimension
        for i in range(len(target_id)-len(input_id)):
            stacks = np.expand_dims(stacks,-1)
            input_id = input_id+missing_id[i]
    else:
        return

    # reorder dimensions to match 'TZCHW'
    if input_id != target_id:
        for i in target_id:
            f = input_id.index(i)
            t = target_id.index(i)
            stacks = np.moveaxis(stacks,f,t)
            input_id = input_id.replace(i,'')
            input_id = input_id[:t]+i+input_id[t:]
            
    # adjust channel dimension to 2
    if stacks.shape[2]==1:
      stacks = np.concatenate([stacks,np.zeros(stacks.shape)],axis=2)

    # compute maximum values
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

if __name__ == '__main__':

    f = '../test_unwrap_heart/4D_merged_small.tif'
    loadStacks5D(f)
