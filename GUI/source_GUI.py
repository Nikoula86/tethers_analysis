from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFileDialog, QMessageBox, QErrorMessage)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from tifffile import imread
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
import os, pickle

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
        self.plot(data=data)
        self.mpl_connect('motion_notify_event', self.hover)
        self.setMouseTracking(True)

    def leaveEvent(self, QEvent):
        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
        pass

    def hover(self, event):
        if event.inaxes == self.axes:
            (x,y) = (event.xdata,event.ydata)
            QApplication.setOverrideCursor(QCursor(Qt.BlankCursor))
            self.target[0].set_data([x-64,x+64],[y,y])
            self.target[1].set_data([x,x],[y-64,y+64])
            self.draw()
 
    def plot(self,data):
        if data == []:
            data = np.zeros((2,512,1024))
        cmap1 = LinearSegmentedColormap.from_list('mycmap', ['black', 'aqua'])
        cmap2 = LinearSegmentedColormap.from_list('mycmap', ['black', 'red'])
        cmap2._init() # create the _lut array, with rgba values
        cmap1._init() # create the _lut array, with rgba values
        alphas = np.linspace(0, .5, cmap2.N+3)
        cmap2._lut[:,-1] = alphas
        cmap1._lut[:,-1] = alphas
        colors = [cmap1,cmap2] 
        self.images_shown = [ self.axes.imshow(d, cmap=colors[i]) for i, d in enumerate(data) ]

        colors = ['#6eadd8','#ff7f0e','white','#c4c4c4']
        ms = [5,5,5,5]
        marker = ['o','o','o','o']
        self.points_scatter = []
        for i in range(4):
            line, = self.axes.plot([],[],' ',color=colors[i],ms=ms[i],marker=marker[i])
            self.points_scatter.append(line)

        self.target = [ self.axes.plot([],[],'-w',lw=.2)[0], self.axes.plot([],[],'-w',lw=.2)[0] ]
        # use self.widgets['groupCanvas2D'][2].image_shown.set_data(img); canvas2d.draw(); to update image
        self.axes.grid(False)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.axes.set_axis_off() 
        self.draw()

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
        self.plot(data=data)
 
 
    def plot(self,data):
        ms = [5,5,5,5]
        ls = [' x', ' x', ' o', '-o']
        colors = ['#6eadd8','#ff7f0e','white','#c4c4c4']
        self.lines = []
        for i in range(4):
            line, = self.axes.plot([],[],[], ls[i],ms=ms[i],color=colors[i])
            self.lines.append( line )
        self.draw()

class MyGUI(QDialog):
    def __init__(self, parent=None):
        super(MyGUI, self).__init__(parent)

        self.points_id = ['tether_Atrium','tether_Ventricle','AVCanal','Midline']
        self.points_colors = ['#1f77b4','#ff7f0e','black','grey']
        self.points = { object_id: np.array([]) for object_id in self.points_id }
        self.file_name = ''
        self.stacks = np.zeros((10,10,2,512,1024))
        self.channels = ['channel 0', 'channel 1']
        self.widgets = {}

        self.createLoadSaveGroupBox()
        self.createObjectsControlGroupBox()
        self.createTZCControlGroupBox()
        self.createCanvas2DGroupBox()
        self.createCanvas3DGroupBox()

        self.setEnableState(False)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.groupLoadSave, 0, 0, 1, 3)
        mainLayout.addWidget(self.groupObjectsControl, 1, 0)
        mainLayout.addWidget(self.groupTZCControl, 2, 0)
        mainLayout.addWidget(self.groupCanvas2DBox, 1, 1, 2, 1)
        mainLayout.addWidget(self.groupCanvas3DBox, 1, 2, 2, 1)

        self.setLayout(mainLayout)
        self.resize(1.2*960, 1.2*413)
        QApplication.setStyle('Macintosh')

    def createLoadSaveGroupBox(self):
        self.groupLoadSave = QGroupBox("")
        
        loadImageButton = QPushButton("Load Image data")
        loadImageButton.setFocusPolicy(Qt.NoFocus)
        loadImageButton.clicked.connect(self.selectImageFile)

        loadPointsButton = QPushButton("Load Points data")
        loadPointsButton.setFocusPolicy(Qt.NoFocus)
        loadPointsButton.clicked.connect(self.selectPointsFile)

        saveButton = QPushButton("Save data")
        saveButton.setFocusPolicy(Qt.NoFocus)
        saveButton.clicked.connect(self.saveData)

        layout = QHBoxLayout()
        layout.addWidget(loadImageButton)
        layout.addWidget(loadPointsButton)
        layout.addWidget(saveButton)

        self.groupLoadSave.setLayout(layout)
        self.groupLoadSave.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.widgets['groupLoadSave'] = [loadImageButton,loadPointsButton,saveButton]

    def createObjectsControlGroupBox(self):
        self.groupObjectsControl = QGroupBox("")

        objectIDBox = QComboBox(); objectIDBox.addItems(self.points_id)
        objectLabel = QLabel("&Object ID:"); objectLabel.setBuddy(objectIDBox)  

        layout = QGridLayout()
        layout.addWidget(objectLabel,0,0)
        layout.addWidget(objectIDBox,0,1)

        self.groupObjectsControl.setLayout(layout)
        self.groupObjectsControl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.widgets['groupObjects'] = [objectIDBox]

    def createTZCControlGroupBox(self):
        self.groupTZCControl = QGroupBox("")

        TBox = QSpinBox(); TBox.setValue(0)
        TLabel = QLabel("&Contraction phase:"); TLabel.setBuddy(TBox)
        TBox.setKeyboardTracking(False)
        TBox.valueChanged.connect(self.updateCanvas2D)

        ZBox = QSpinBox(); ZBox.setValue(0)
        ZLabel = QLabel("&Z plane:"); ZLabel.setBuddy(ZBox)
        ZBox.setKeyboardTracking(False)
        ZBox.valueChanged.connect(self.updateCanvas2D)

        CBox = QComboBox(); CBox.addItems(self.channels)
        CLabel = QLabel("&Channel:"); CLabel.setBuddy(CBox)
        CBox.currentIndexChanged.connect(self.updateBC)
        
        chBox = [ QCheckBox(ch) for ch in self.channels ]
        [ box.stateChanged.connect(self.updateCanvas2D) for box in chBox ]
        [ box.setCheckState(False) for box in chBox ]

        layout = QGridLayout()
        layout.addWidget(TLabel,0,0); layout.addWidget(TBox,0,1)
        layout.addWidget(ZLabel,1,0); layout.addWidget(ZBox,1,1)
        layout.addWidget(CLabel,2,0); layout.addWidget(CBox,2,1)
        for i, b in enumerate( chBox ):
            layout.addWidget(b,i+3,0)

        self.groupTZCControl.setLayout(layout)
        self.widgets['groupTZC'] = [TBox,ZBox,CBox,*chBox]

    def createCanvas2DGroupBox(self):
        self.groupCanvas2DBox = QGroupBox("")

        minValSlider = QSlider(Qt.Vertical)
        maxValSlider = QSlider(Qt.Vertical)
        maxValSlider.setValue(2**16-1)
        maxValSlider.setMaximum(2**16-1)
        minValSlider.setMaximum(2**16-1)
        canvas2D = Canvas2D(self, width=10, height=5)

        layout = QGridLayout()
        layout.addWidget(minValSlider,0,0,1,1)
        layout.addWidget(maxValSlider,0,1,1,1)
        layout.addWidget(canvas2D,0,2,1,1)

        self.groupCanvas2DBox.setLayout(layout)
        self.widgets['groupCanvas2D'] = [minValSlider,maxValSlider,canvas2D]

        minValSlider.valueChanged.connect(self.updateBC)
        maxValSlider.valueChanged.connect(self.updateBC)
        canvas2D.mpl_connect('button_press_event', self.mouseClick)

    def createCanvas3DGroupBox(self):
        self.groupCanvas3DBox = QGroupBox("")

        isplot = QCheckBox('Show live 3D plot')
        isphase = QCheckBox('Show only current contraction phase')
        canvas3D = Canvas3D(self, width=2, height=2)

        layout = QGridLayout()
        layout.addWidget(isplot,0,0)
        layout.addWidget(isphase,1,0)
        layout.addWidget(canvas3D,2,0)

        sp = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.groupCanvas3DBox.heightForWidth(1)
        canvas3D.setSizePolicy(sp)
        self.groupCanvas3DBox.setLayout(layout)
        self.widgets['groupCanvas3D'] = [canvas3D,isplot,isphase]

        isplot.stateChanged.connect(self.updateCanvas3D)
        isphase.stateChanged.connect(self.updateCanvas3D)

    #%%
    def selectImageFile(self):
        new_file,_ = QFileDialog.getOpenFileName(self, "Select Merged File")
        if new_file.split('.')[-1] not in ['tif','tiff']:
            QMessageBox.warning(self,'Warning!','This is not a tif file!')
            return
        if new_file != '':
            self.setEnableState(True)
            self.file_name = new_file
            self.stacks, self._maxval = self.loadStacks()

            self.widgets['groupTZC'][0].setMaximum(self.stacks.shape[0]-1)
            self.widgets['groupTZC'][1].setMaximum(self.stacks.shape[1]-1)
            self.widgets['groupCanvas2D'][0].setMaximum(self._maxval[0,0])
            self.widgets['groupCanvas2D'][1].setMaximum(self._maxval[0,0])
            self.widgets['groupCanvas2D'][1].setValue(self._maxval[0,0])

            ms = [3,3,3,5]
            ls = [' o', ' o', ' o', '-o']
            colors = ['#6eadd8','#ff7f0e','white','#c4c4c4']
            self.widgets['groupCanvas3D'][0].lines = []
            for ph in range(self.stacks.shape[0]):
                for i, obj_id in enumerate( self.points_id ):
                    line, = self.widgets['groupCanvas3D'][0].axes.plot([0],[0],[0], ls[i],ms=ms[i],color=colors[i])
                    self.widgets['groupCanvas3D'][0].lines.append(line)
            self.widgets['groupCanvas3D'][0].draw()

            for i in range(self.stacks.shape[2]):
                self.widgets['groupTZC'][i+3].setChecked(True)
            for i in range(2):
                self.widgets['groupTZC'][2].setCurrentIndex(i)
                self.updateBC()
            self.updateCanvas2D()

    def selectPointsFile(self):
        new_file,_ = QFileDialog.getOpenFileName(self, "Select Merged File")
        if new_file.split('.')[-1] not in ['p','pickle']:
            QMessageBox.warning(self,'Warning!','This is not an invalid points file!')
            return
        if new_file != '':
            self.points = pickle.load(open(new_file,'rb'))
            self.updateScatter()
            self.updateCanvas3D()

    def saveData(self):
        if self.file_name != '':
            save_file_name, _ = QFileDialog.getSaveFileName(self,"Save file")
            if save_file_name != '':
                print('#'*40)
                print('Saving data to:\n\t', save_file_name)
                pickle.dump(self.points,open(save_file_name,'wb'))
                print('Done')

    def loadStacks(self):
        print('#'*40)
        print('Loading dataset at:\n\t', self.file_name)
        stacks = imread(self.file_name)[:,:,::-1,:,:]
        _maxval = np.zeros((stacks.shape[0],stacks.shape[2]))
        for i in range(stacks.shape[0]):
            for j in range(stacks.shape[2]):
                _maxval[i,j] = np.max(stacks[i,:,j,:,:])
        print('Stack shape (TZCHW):', stacks.shape)
        print('Done')
        return stacks, _maxval

    def setEnableState(self, state):
        self.groupObjectsControl.setEnabled(state)
        self.groupTZCControl.setEnabled(state)
        self.groupCanvas2DBox.setEnabled(state)
        self.groupCanvas3DBox.setEnabled(state)
        self.widgets['groupLoadSave'][1].setEnabled(state)       
        self.widgets['groupLoadSave'][2].setEnabled(state)       

    def updateCanvas2D(self):
        t = int( self.widgets['groupTZC'][0].value() )
        z = int( self.widgets['groupTZC'][1].value() )
        # print('Current TZC: ',t,z)

        show_one=False
        for i, b in enumerate( self.widgets['groupTZC'][3:] ):
            if b.checkState():
                show_one = True
                self.widgets['groupCanvas2D'][2].images_shown[i].set_data(self.stacks[t,z,i])
            else:
                self.widgets['groupCanvas2D'][2].images_shown[i].set_data(self.stacks[t,z,i]*0)

        self.widgets['groupCanvas2D'][2].draw()
        self.widgets['groupCanvas2D'][2].flush_events()
        self.updateScatter()

    def updateCanvas3D(self):
        if not self.widgets['groupCanvas3D'][1].checkState():
            return
        # only show the current contraction phase
        t = int( self.widgets['groupTZC'][0].value() )
        point_plot = { _id: self.points[_id] for _id in self.points_id }
        if self.widgets['groupCanvas3D'][2].checkState():
            for _id in self.points_id:
                if point_plot[_id].shape[0] > 0:
                    point_plot[_id] = point_plot[_id][point_plot[_id][:,3]==t]

        # update all lines
        ms = [3,3,3,5]
        ls = [' o', ' o', ' o', '-o']
        colors = ['#6eadd8','#ff7f0e','white','#c4c4c4']
        self.widgets['groupCanvas3D'][0].axes.clear()
        idx = 0
        for ph in range(self.stacks.shape[0]):
            for i, obj_id in enumerate( self.points_id ):
                p = point_plot[obj_id]
                if p.shape[0] != 0:
                    p = p[p[:,3]==ph]
                    line, = self.widgets['groupCanvas3D'][0].axes.plot(p[:,0],p[:,1],p[:,2], ls[i],ms=ms[i],color=colors[i])
                    self.widgets['groupCanvas3D'][0].lines[idx] = line
                idx += 1

        self.widgets['groupCanvas3D'][0].draw()
        self.widgets['groupCanvas3D'][0].flush_events()

    def updateBC(self):
        t = int( self.widgets['groupTZC'][0].value() )
        z = int( self.widgets['groupTZC'][1].value() )
        c = int( self.widgets['groupTZC'][2].currentIndex() )

        self.widgets['groupCanvas2D'][0].setMaximum(self._maxval[t,c])
        self.widgets['groupCanvas2D'][1].setMaximum(self._maxval[t,c])

        vmin = int( self.widgets['groupCanvas2D'][0].value() )
        vmax = int( self.widgets['groupCanvas2D'][1].value() )

        if self.widgets['groupCanvas2D'][0].value() >= self.widgets['groupCanvas2D'][1].value():
            self.widgets['groupCanvas2D'][0].setValue(self.widgets['groupCanvas2D'][1].value()-1)
            vmin = int( self.widgets['groupCanvas2D'][0].value() )

        self.widgets['groupCanvas2D'][2].images_shown[c].set_clim([vmin,vmax])
        self.widgets['groupCanvas2D'][2].draw()

    def updateScatter(self):
        t = int( self.widgets['groupTZC'][0].value() )
        z = int( self.widgets['groupTZC'][1].value() )

        for i, obj_id in enumerate(self.points_id):
            ps = self.points[obj_id]
            if ps.shape[0]!=0:
                ps = ps[ps[:,2].astype(np.uint16)==z,:]
                ps = ps[ps[:,3].astype(np.uint16)==t,:]
                self.widgets['groupCanvas2D'][2].points_scatter[i].set_data(ps[:,0],ps[:,1])
            else:
                self.widgets['groupCanvas2D'][2].points_scatter[i].set_data([],[])

        self.widgets['groupCanvas2D'][2].draw()

    def mouseClick(self, event):
        # print('Mouse clicked! ', event)
        obj_id = self.widgets['groupObjects'][0].currentText()
        t = int( self.widgets['groupTZC'][0].value() )
        z = int( self.widgets['groupTZC'][1].value() )
        c = np.array([np.rint(event.xdata),np.rint(event.ydata),z,t])
        points = self.points[obj_id]
        _idxs = np.arange(points.shape[0])

        # LEFT CLICK: add point
        if event.button == 1:
            if points.shape[0]!=0:
                self.points[obj_id] = np.append(self.points[obj_id],np.array([c]),axis=0)
            else:
                self.points[obj_id] = np.array([c])

        # RIGHT CLICK: remove point from the same contraction phase and focal plane
        if event.button == 3:
            new_points = []
            new_idxs = []
            for i, p in enumerate(points): # filter only points in the same focal plane and contraction phase
                if p[2] == c[2]: # same focal plane
                    if p[3] == c[3]: # same contraction phase
                        new_points.append(p) # save the poiont
                        new_idxs.append(i)   # save the original index
            points = np.array(new_points)
            _idxs = np.array(new_idxs)

            # now find the closest point to the click and remove it
            if len(_idxs) != 0:
                dist = [ np.linalg.norm(c[:3]-c1) for c1 in points[:,:3] ]
                i = np.where(dist==np.min(dist))[0]
                self.points[obj_id] = np.delete(self.points[obj_id], _idxs[i], axis=0)
        self.updateScatter()
        self.updateCanvas3D()

# if __name__ == '__main__':

import sys

app = QApplication(sys.argv)
gallery = MyGUI()
gallery.show()
sys.exit(app.exec_()) 
