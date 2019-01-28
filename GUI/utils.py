from tifffile import imread
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QDialog, QSizePolicy, QApplication,)
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt
from matplotlib.colors import LinearSegmentedColormap

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
    def __init__(self, points_id):
        self.ids = points_id
        self.coords = { _id: np.array([]) for _id in points_id }

    def updatePoints(self, current_id, coord, event):
        # print('Mouse clicked! ', event)
        points = self.coords[current_id]
        _idxs = np.arange(points.shape[0])

        # LEFT CLICK: add point
        if event.button == 1:
            if points.shape[0]!=0:
                self.coords[current_id] = np.append(self.coords[current_id],np.array([coord]),axis=0)
            else:
                self.coords[current_id] = np.array([coord])

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
                self.coords[current_id] = np.delete(self.coords[current_id], _idxs[i], axis=0)

        self.performSanityCheck()

    def performSanityCheck(self):
        # check that
        return

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

        colors = ['#6eadd8','#ff7f0e','red','#c4c4c4']
        ms = [5,5,5,2]
        marker = ['o','o','X','x']
        self.points_scatter = []
        for i in range(4):
            line, = self.axes.plot([],[],' ',color=colors[i],ms=ms[i],marker=marker[i])
            self.points_scatter.append(line)

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

    def updateScatter(self, t, z, points):
        i=0
        for key, ps in points.items():
            if ps.shape[0]!=0:
                ps = ps[ps[:,2].astype(np.uint16)==z,:]
                ps = ps[ps[:,3].astype(np.uint16)==t,:]
                self.points_scatter[i].set_data(ps[:,0],ps[:,1])
            else:
                self.points_scatter[i].set_data([],[])
            i+=1

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
 
 
    def plot(self,data_id,data,n_ph):
        ms = [3,3,5,1]
        ls = [' o', ' o', ' X', '-x']
        colors = ['#6eadd8','#ff7f0e','red','#c4c4c4']
        self.axes.clear()
        for ph in range(n_ph):
            for i, obj_id in enumerate( data_id ):
                p = data[obj_id]
                if p.shape[0] != 0:
                    p = p[p[:,3]==ph]
                    self.axes.plot(p[:,0],p[:,1],p[:,2], ls[i],ms=ms[i],color=colors[i])

        self.draw()
        self.flush_events()

'''
# subwindow to define points
'''

class ObjectDefiner(QDialog):
    def __init__(self, parent=None):
        super(ObjectDefiner, self).__init__(parent)

        QApplication.setStyle('Macintosh')



if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    gallery = ObjectDefiner()
    gallery.show()
    sys.exit(app.exec_()) 

