from tifffile import imread
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QDialog, QSizePolicy, QApplication, QTableWidget, QVBoxLayout,
                            QPushButton, QColorDialog, QTableWidgetItem)
from PyQt5.QtGui import QCursor, QColor
from PyQt5.QtCore import Qt
from matplotlib.colors import LinearSegmentedColormap
import copy

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

'''
# classes
'''

class PointObjects():
    def __init__(self, points_meta):
        self.meta = points_meta
        self.meta['coords'] = [ np.array([]) for _id in points_meta['_ids'] ]

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
                dist = [ np.linalg.norm(c[:3]-c1) for c1 in points[:,:3] ]
                i = np.where(dist==np.min(dist))[0]
                self.meta['coords'][current_idx] = np.delete(self.meta['coords'][current_idx], _idxs[i], axis=0)

        self.updatePointMeta()
    
    def updatePointMeta(self):
        for i, ps in enumerate( self.meta['coords'] ):
            if ps.shape[0]>0:
                self.meta['is_instance'][i] = 1

class Canvas2D(FigureCanvas):
 
    def __init__(self, parent=None, width=10, height=5, dpi=100, data = []):
        plt.style.use('dark_background')
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1.)
 
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
 
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        # self.gray2rgb(data=data)
        self.initialize(data=data)
        self.mpl_connect('motion_notify_event', self.hover)
        self.cursor = self.axes.plot([0], [0], visible=False, marker = '+',color='white',ms=10000,lw=.5,alpha=.5)[0]
        self.cmaps = [ LinearSegmentedColormap.from_list('mycmap1', ['black', 'aqua'],N=2**16-1),
                        LinearSegmentedColormap.from_list('mycmap2', ['black', 'red'],N=2**16-1) ]
        

    def leaveEvent(self, QEvent):
        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
        pass

    def hover(self, event):
        if event.inaxes == self.axes:
            QApplication.setOverrideCursor(QCursor(Qt.BlankCursor))
            self.cursor.set_data([event.xdata], [event.ydata])
            self.cursor.set_visible(True)
        else:
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            self.cursor.set_visible(False)
        self.draw()
 
    def initialize(self,data):
        if data == []:
            data = np.zeros((2,512,1024))
        if data == []:
            data = np.zeros((2,512,1024))
        cmap1 = LinearSegmentedColormap.from_list('mycmap', ['black', 'aqua'])
        rgba_img = cmap1(data[0])[:,:,:3]
        cmap2 = LinearSegmentedColormap.from_list('mycmap', ['black', 'red'])
        rgba_img += cmap2(data[1])[:,:,:3]

        self.images_shown = self.axes.imshow(rgba_img)

        self.points_scatter = [self.axes.plot([],[])[0]]

        self.axes.grid(False)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.axes.set_axis_off() 
        self.draw()

    def reshowImg(self, stacks, chButton, chVal):
        # print('Current TZC: ',t,z)
        rgba_img = np.zeros((512,1024,3))
        for i, b in enumerate( chButton ):
            if b.checkState():
                lims = chVal[i]
                channel = np.clip(stacks[i,...],lims[0],lims[1])
                channel = (channel-np.min(channel))/(np.max(channel)-np.min(channel))
                rgba_img += self.cmaps[i](channel)[:,:,:3]
        self.images_shown.set_data(rgba_img)

        self.draw()
        self.flush_events()

    def updateScatter(self, t, z, meta):
        [l.remove() for l in self.points_scatter]
        self.points_scatter = []
        for i, ps in enumerate( meta['coords'] ):
            if meta['is_instance'][i] == 1:
                ps_plot = ps[ (ps[:,2].astype(np.uint16)==z), : ]
                ps_plot = ps_plot[ (ps_plot[:,3].astype(np.uint16)==t) ,: ]
                self.points_scatter.append( self.axes.plot(ps_plot[:,0],ps_plot[:,1],meta['markers'][i],
                    color=meta['colors'][i],ms=meta['ms'][i])[0] )

        self.draw()
        self.flush_events()

class Canvas3D(FigureCanvas):
 
    def __init__(self, parent=None, width=5, height=4, dpi=100,data=[]):
        plt.style.use('dark_background')
        fig = Figure(figsize=(width, height), dpi=dpi)
 
        FigureCanvas.__init__(self, fig)
        self.axes = self.figure.add_subplot(111, projection='3d')
        fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1.)
        self.axes.grid(False)
        self.setParent(parent)
        self.axes.set_xlim(auto=True)
        self.axes.set_ylim(auto=True)
        self.axes.set_zlim(auto=True)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
 
 
    def plot(self,meta,n_ph):
        self.axes.clear()
        for ph in range(n_ph):
            for i, obj_id in enumerate( meta['_ids'] ):
                if meta['is_instance'][i] == 1:
                    p = meta['coords'][i]
                    p = p[p[:,3]==ph]
                    self.axes.plot(p[:,0],p[:,1],p[:,2], meta['markers'][i],
                        ms=meta['ms'][i],color=meta['colors'][i])

        self.draw()
        self.flush_events()

'''
# subwindow to define points
'''

class ObjectDefiner(QDialog):
    def __init__(self, parent=None, 
                    objects = {'_ids': ['newobject']*4,
                        'colors': ['#6eadd8','#ff7f0e','red','#c4c4c4'],
                        'markers': ['o','o','X','-x'],
                        'ms': [3,3,5,1],
                        'is_instance': [0,0,0,0],
                        'coords': [np.array([])]*4 }):

        super(ObjectDefiner, self).__init__(parent)
        self.objects = objects
        self.outobjects = copy.deepcopy(self.objects)

        QApplication.setStyle('Macintosh')

        table = QTableWidget()
        table.setRowCount(len(self.objects['_ids']))
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Object name', 'Color', 'Marker', 'Marker size', 'are istances'])
        self.table = table

        addObj = QPushButton('Add object.')
        addObj.setFocusPolicy(Qt.NoFocus)
        addObj.clicked.connect(self.addObject)

        removeObj = QPushButton('Remove object.')
        removeObj.setFocusPolicy(Qt.NoFocus)
        removeObj.clicked.connect(self.removeObject)

        saveButton = QPushButton('Save objects.')
        saveButton.setFocusPolicy(Qt.NoFocus)
        saveButton.clicked.connect(self.saveObjects)

        layout = QVBoxLayout()
        layout.addWidget(table) 
        layout.addWidget(addObj)        
        layout.addWidget(removeObj)        
        layout.addWidget(saveButton)

        self.setLayout(layout)

        self.populateTable()
        table.doubleClicked.connect(self.doubleClickEvent)
        table.itemChanged.connect(self.changeObjects)

    def populateTable(self):
        (_ids,colors,markers,ms,n,coords) = self.unpackObjects()
        self.table.setRowCount(len(_ids))
        for i in range(len(_ids)):
            self.table.setItem(i,0, QTableWidgetItem(_ids[i]))
            self.table.setItem(i,1, QTableWidgetItem()); self.table.item(i,1).setBackground(QColor(colors[i]))
            self.table.setItem(i,2, QTableWidgetItem(markers[i]))
            self.table.setItem(i,3, QTableWidgetItem(str(ms[i])))
            
        for j in range(self.table.rowCount()):
            self.table.setItem(j,4, QTableWidgetItem(str(n[j])))
            self.table.item(j,4).setFlags(Qt.ItemIsEnabled)

    def unpackObjects(self):
        return ( val for key, val in self.objects.items() )

    def changeObjects(self):
        self.objects['_ids'] = [self.table.item(i,0).text() for i in range(self.table.rowCount()) if self.table.item(i,0)]
        self.objects['markers'] = [self.table.item(i,2).text() for i in range(self.table.rowCount()) if self.table.item(i,2)]
        self.objects['ms'] = [self.table.item(i,3).text() for i in range(self.table.rowCount()) if self.table.item(i,3)]
        self.objects['is_instance'] = [self.table.item(i,4).text() for i in range(self.table.rowCount()) if self.table.item(i,4)]

    def doubleClickEvent(self, click):
        if click.column() == 1:
            self.pickColor(click)
            return

    def pickColor(self, click):
        color = QColorDialog.getColor()
        # self.table.item(i,1).setBackground(QColor(color))
        self.objects['colors'][click.row()] = color.name()
        self.populateTable()

    def addObject(self):
        self.objects['_ids'].append('newobject')
        if len(self.objects['colors'])>0:
            self.objects['colors'].append(self.objects['colors'][-1])
            self.objects['markers'].append(self.objects['markers'][-1])
            self.objects['ms'].append(self.objects['ms'][-1])
            self.objects['is_instance'].append(0)
            self.objects['coords'].append(np.array([]))
        else:
            self.objects['colors'] = ['#6eadd8']
            self.objects['markers'] = ['o']
            self.objects['ms'] = [3]
            self.objects['is_instance'] = [0]
            self.objects['coords'].append(np.array([]))
        self.populateTable()

    def removeObject(self):
        if len(self.objects['_ids'])>0:
            idxs = [i for i, x in enumerate(self.objects['is_instance']) if x == 0]
            if len(idxs)>0:
                i = idxs[-1]
                self.objects['_ids'].pop(i)
                self.objects['colors'].pop(i)
                self.objects['markers'].pop(i)
                self.objects['ms'].pop(i)
                self.objects['is_instance'].pop(i)
                self.objects['coords'].pop(i)
                self.populateTable()

    def saveObjects(self):
        outobjects = {}
        outobjects['_ids'] = [self.table.item(i,0).text() for i in range(self.table.rowCount())]
        outobjects['colors'] = [self.table.item(i,1).background().color().name() for i in range(self.table.rowCount())]
        outobjects['markers'] = [self.table.item(i,2).text() for i in range(self.table.rowCount())]
        outobjects['ms'] = [self.table.item(i,3).text() for i in range(self.table.rowCount())]
        outobjects['is_instance'] = [int(self.table.item(i,4).text()) for i in range(self.table.rowCount())]
        outobjects['coords'] = self.objects['coords']
        self.outobjects = outobjects
        super().accept()


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    gallery = ObjectDefiner()
    gallery.show()
    sys.exit(app.exec_()) 

