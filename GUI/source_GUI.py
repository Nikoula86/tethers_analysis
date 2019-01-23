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
 
 
    def plot(self,data):
        if data == []:
            data = np.random.randint(0,2**16-1,(2,512,1024))
        cmap1 = LinearSegmentedColormap.from_list('mycmap', ['black', 'aqua'])
        cmap2 = LinearSegmentedColormap.from_list('mycmap', ['black', 'red'])
        cmap2._init() # create the _lut array, with rgba values
        alphas = np.linspace(0, 1., cmap2.N+3)
        cmap2._lut[:,-1] = alphas
        colors = [cmap1,cmap2] 
        self.images_shown = [ self.axes.imshow(d, cmap=colors[i]) for i, d in enumerate(data) ]
        colors = ['#1f77b4','#ff7f0e','white','gray']
        ms = [5,5,5,5]
        marker = ['x','x','o','o']
        self.points_scatter = []
        for i in range(4):
            line, = self.axes.plot([],[],' ',color=colors[i],ms=ms[i],marker=marker[i])
            self.points_scatter.append(line)
        # use self.widgets['groupCanvas2D'][2].image_shown.set_data(img); canvas2d.draw(); to update image
        self.axes.grid(False)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.axes.set_axis_off() 
        self.draw()

class Canvas3D(FigureCanvas):
 
    def __init__(self, parent=None, width=5, height=4, dpi=100,data=[]):
        fig = Figure(figsize=(width, height), dpi=dpi)
 
        FigureCanvas.__init__(self, fig)
        self.axes = self.figure.add_subplot(111, projection='3d')
        self.setParent(parent)
 
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot(data=data)
 
 
    def plot(self,data):
        if data == []:
            x = np.linspace(0,10,100)
            y = np.sin(x)*np.cos(x)
            z = (x**2+y**2)/100+np.cos(x)*np.sin(y)
        self.lines, = self.axes.plot(x,y,z, '-')
        self.draw()

class MyGUI(QDialog):
    def __init__(self, parent=None):
        super(MyGUI, self).__init__(parent)

        self.points_id = ['tether_Atrium','tether_Ventricle','AVCanal','Midline']
        self.points_colors = ['#1f77b4','#ff7f0e','black','grey']
        self.points = { object_id: np.array([]) for object_id in self.points_id }
        self.file_name = ''
        self.stacks = np.random.randint(0,2**16-1,(10,10,2,512,1024))
        self.channels = ['488nm', '561nm']
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
        
        loadButton = QPushButton("Load data")
        loadButton.setFocusPolicy(Qt.NoFocus)
        loadButton.clicked.connect(self.selectFile)

        saveButton = QPushButton("Save data")
        saveButton.setFocusPolicy(Qt.NoFocus)
        saveButton.clicked.connect(self.saveData)

        layout = QHBoxLayout()
        layout.addWidget(loadButton)
        layout.addWidget(saveButton)

        self.groupLoadSave.setLayout(layout)
        self.groupLoadSave.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.widgets['groupLoadSave'] = [loadButton,saveButton]

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

        canvas3D = Canvas3D(self, width=5, height=5)

        layout = QGridLayout()
        layout.addWidget(canvas3D,0,0,6,6)

        self.groupCanvas3DBox.setLayout(layout)
        self.widgets['groupCanvas3D'] = [canvas3D]

    #%%
    def selectFile(self):
        new_file,_ = QFileDialog.getOpenFileName(self, "Select Merged File")
        if new_file.split('.')[-1] not in ['tif','tiff']:
            QMessageBox.warning(self,'Warning!','This is not a tif file!')
            return
        if new_file != '':
            self.setEnableState(True)
            self.file_name = new_file
            self.stacks = self.loadStacks()
            if os.path.exists(os.path.join(*self.file_name.split('.')[:-1])+'_points.p'):
                print('Good news! You clicked on this dataset already')
                self.points = pickle.load(open(os.path.join(*self.file_name.split('.')[:-1])+'_points.p','rb'))
            else:
                print('First time you look at this dataset. New points object created')
                self.points = { object_id: np.array([]) for object_id in self.points_id }

            self.widgets['groupTZC'][0].setMaximum(self.stacks.shape[0]-1)
            self.widgets['groupTZC'][1].setMaximum(self.stacks.shape[1]-1)
            for i in range(self.stacks.shape[2]):
                self.widgets['groupTZC'][i+3].setChecked(True)
            self.updateCanvas2D()
            self.widgets['groupCanvas2D'][1].setValue(int(np.max(self.stacks[:,:,1,:,:])/2))
            self.widgets['groupTZC'][2].setCurrentIndex(1)
            self.widgets['groupCanvas2D'][1].setValue(int(np.max(self.stacks[:,:,0,:,:])/2))
            self.widgets['groupTZC'][2].setCurrentIndex(0)

    def saveData(self):
        if self.file_name != '':
            print('Saving data to:\n\t', os.path.join(*self.file_name.split('.')[:-1])+'_points.p')
            pickle.dump(self.points,open(os.path.join(*self.file_name.split('.')[:-1])+'_points.p','wb'))
            # df = pd.DataFrame.from_dict(self.points)
            # print(df.head())
            # df.to_csv(os.path.join(*self.file_name.split('.')[:-1])+'_points.csv')

    def loadStacks(self):
        print(self.file_name)
        stack = imread(self.file_name)[:,:,::-1,:,:]
        self._maxval = np.zeros((self.stacks.shape[0],self.stacks.shape[1],self.stacks.shape[2]))
        for i in range(self.stacks.shape[0]):
            for k in range(self.stacks.shape[1]):
                for j in range(self.stacks.shape[2]):
                    self._maxval[i,k,j] = np.percentile(self.stacks[i,k,j,:,:],10)
        print('#'*40)
        print('Loading dataset at:\n\t', self.file_name)
        print('Stack shape (TZCHW):', stack.shape)
        print('#'*40)
        return stack

    def setEnableState(self, state):
        self.groupObjectsControl.setEnabled(state)
        self.groupTZCControl.setEnabled(state)
        self.groupCanvas2DBox.setEnabled(state)
        self.groupCanvas3DBox.setEnabled(state)
        self.widgets['groupLoadSave'][1].setEnabled(state)        

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
        self.updateScatter()

    def updateBC(self):
        t = int( self.widgets['groupTZC'][0].value() )
        z = int( self.widgets['groupTZC'][1].value() )
        c = int( self.widgets['groupTZC'][2].currentIndex() )

        self.widgets['groupCanvas2D'][0].setMaximum(self._maxval[t,z,c])
        self.widgets['groupCanvas2D'][1].setMaximum(self._maxval[t,z,c])

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
        c = np.array([np.rint(event.xdata),np.rint(event.ydata),self.widgets['groupTZC'][1].value(),self.widgets['groupTZC'][0].value()])
        if event.button == 1:
            if self.points[obj_id].shape[0]!=0:
                self.points[obj_id] = np.append(self.points[obj_id],np.array([c]),axis=0)
            else:
                self.points[obj_id] = np.array([c])
        if event.button == 3:
            if self.points[obj_id].shape[0] != 0:
                dist = [ np.linalg.norm(c[:3]-c1) for c1 in self.points[obj_id][:,:3] ]
                i = np.where(dist==np.min(dist))[0]
                self.points[obj_id] = np.delete(self.points[obj_id], i, axis=0)
        self.updateScatter()

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    gallery = MyGUI()
    gallery.show()
    sys.exit(app.exec_()) 
