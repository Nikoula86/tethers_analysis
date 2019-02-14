from tifffile import imread
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QWidget, QDialog, QSizePolicy, QApplication, QTableWidget, QVBoxLayout,
                            QPushButton, QColorDialog, QTableWidgetItem, QMessageBox, QAbstractScrollArea)
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtGui import QCursor, QColor
from PyQt5.QtCore import Qt
from matplotlib.colors import LinearSegmentedColormap
import copy, re, time
import matplotlib as mpl
from ast import literal_eval

'''
# classes
'''

class Canvas2D(QWidget):
 
    def __init__(self, parent=None, width=10, height=5, dpi=100, data = []):
        super().__init__(parent)
        self.setParent(parent)
        plt.style.use('dark_background')
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1.)

        self.press = False
        self.move = False
 
        figure = FigureCanvas(fig)
        figure.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.figure = figure

        navi_toolbar = NavigationToolbar(figure, self)
        navi_toolbar.setFocusPolicy(Qt.NoFocus)
        navi_toolbar.setMaximumHeight(30)

        layout = QVBoxLayout()
        layout.addWidget(navi_toolbar)
        layout.addWidget(figure)
        self.setLayout(layout)

#        self.initialize(data=data)
        self.figure.mpl_connect('button_press_event', self.onpress)
        self.figure.mpl_connect('motion_notify_event', self.hover)
        self.cmaps = [ LinearSegmentedColormap.from_list('mycmap1', ['black', 'aqua'],N=2**16-1),
                        LinearSegmentedColormap.from_list('mycmap2', ['black', 'red'],N=2**16-1) ]
        self.figure.cursor = mpl.widgets.Cursor(self.axes,useblit=True,lw=1, alpha=.5)
        self.figure.setCursor(QCursor(Qt.CrossCursor))

    def onpress(self,event):
        self.start = time.time()
        self.press = True

    def hover(self, event):
        self.figure.setCursor(QCursor(Qt.CrossCursor))
        if self.press:
            self.move = True
 
    def initialize(self,data):
#        if data == []:
#            data = np.zeros((2,512,1024))
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
        self.figure.draw()

    def reshowImg(self, stacks, chButton, chVal):
        # print('Current TZC: ',t,z)
        rgba_img = np.zeros((*stacks.shape[1:],3))
        for i, b in enumerate( chButton ):
            if b.checkState():
                lims = chVal[i]
                channel = np.clip(stacks[i,...],lims[0],lims[1])
                channel = (channel-np.min(channel))/(np.max(channel)-np.min(channel))
                rgba_img += self.cmaps[i](channel)[:,:,:3]
        self.images_shown.set_data(rgba_img)

        self.figure.draw()
        self.figure.flush_events()

    def updateScatter(self, t, z, meta):
        [l.remove() for l in self.points_scatter]
        self.points_scatter = []
        for i, ps in enumerate( meta['coords'] ):
            if meta['is_instance'][i] == 1:
                ps_plot = ps[ (ps[:,2].astype(np.uint16)==z), : ]
                ps_plot = ps_plot[ (ps_plot[:,3].astype(np.uint16)==t) ,: ]
                self.points_scatter.append( self.axes.plot(ps_plot[:,0],ps_plot[:,1],meta['markers'][i],
                    color=meta['colors'][i],ms=meta['ms'][i])[0] )

        self.figure.draw()
        self.figure.flush_events()

class Canvas3D(FigureCanvas):
 
    def __init__(self, parent=None, width=5, height=4, dpi=100,data=[]):
        plt.style.use('dark_background')
        fig = Figure(figsize=(width, height), dpi=dpi)
 
        FigureCanvas.__init__(self, fig)
        self.axes = self.figure.add_subplot(111, projection='3d')
        fig.subplots_adjust(left=.02,bottom=.1,right=.93,top=1.)
        self.axes.grid(False)
        self.setParent(parent)
        self.axes.set_xlim(auto=True)
        self.axes.set_ylim(auto=True)
        self.axes.set_zlim(auto=True)
        # mpl.rcParams['lines.linewidth'] = 0
        self.axes.xaxis.pane.fill = False
        self.axes.yaxis.pane.fill = False
        self.axes.zaxis.pane.fill = False
        self.axes.xaxis.pane.set_edgecolor('gray')
        self.axes.yaxis.pane.set_edgecolor('gray')
        self.axes.zaxis.pane.set_edgecolor('gray')

        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        FigureCanvas.updateGeometry(self)
    
    def heightForWidth(self, width):
        return width 

    def plot(self,meta,n_ph):
        self.axes.clear()
        self.axes.grid(False)
        # mpl.rcParams['lines.linewidth'] = 0
        for ph in range(n_ph):
            for i, obj_id in enumerate( meta['_ids'] ):
                if meta['is_instance'][i] == 1:
                    p = meta['coords'][i]
                    p = p[p[:,3]==ph]
                    self.axes.plot(p[:,0],p[:,1],p[:,2], meta['markers'][i],
                        ms=meta['ms'][i],color=meta['colors'][i])

        self.draw()
        self.flush_events()

class Overview(QTableWidget):
    def __init__(self, parent = None, n_ph = 5, meta = {'_ids': ['newobject']*4,
                        'colors': ['#6eadd8','#ff7f0e','red','#c4c4c4'],
                        'markers': ['o','o','X','-x'],
                        'ms': [3,3,5,1],
                        'is_instance': [0,1,0,1],
                        'coords': [np.array([]),np.array([[1., 1.]]),np.array([]),np.array([[1., 2.], [3., 4.]])] }):
        super(Overview, self).__init__(parent)
        self.setParent(parent)
        self.setRowCount(n_ph)
        self.setColumnCount(len(meta['_ids']))
        self.setHorizontalHeaderLabels(meta['_ids'])
    
    def populateTable(self, n_ph, meta):
        self.setRowCount(n_ph)
        self.setColumnCount(len(meta['_ids']))
        self.setHorizontalHeaderLabels(meta['_ids'])
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                points = meta['coords'][j]
                self.setItem(i,j, QTableWidgetItem())
                if points.shape[0]>0:
                    points = points[points[:,3]==i]
                    if points.shape[0] > 0:
                        color = '#b1fc99'
                        self.item(i,j).setBackground(QColor(color))
                    else:
                        color = '#db5856'
                        self.item(i,j).setBackground(QColor(color))
                else:
                    color = '#db5856'
                    self.item(i,j).setBackground(QColor(color))









