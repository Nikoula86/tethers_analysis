from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFileDialog)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

class Canvas2D(FigureCanvas):
 
    def __init__(self, parent=None, width=5, height=4, dpi=100, data = []):
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
            data = np.random.randint(0,2**16-1,(1000,1000))
        self.image_shown = self.axes.imshow(data, cmap='gray') 
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
        self.points = { object_id:[] for object_id in self.points_id }
        self.base_dir = ''
        self.channels = ['488nm', '561nm', 'LED']
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
        loadButton.clicked.connect(self.selectDir)

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
        TBox.valueChanged.connect(lambda: self.updateTZC('T'))

        ZBox = QSpinBox(); ZBox.setValue(0)
        ZLabel = QLabel("&Z plane:"); ZLabel.setBuddy(ZBox)
        ZBox.setKeyboardTracking(False)
        ZBox.valueChanged.connect(lambda: self.updateTZC('Z'))

        CBox = QComboBox(); CBox.addItems(self.channels)
        CLabel = QLabel("&Channel:"); CLabel.setBuddy(CBox)
        CBox.currentIndexChanged.connect(lambda: self.updateTZC('C'))
        
        chBox = [ QCheckBox(ch) for ch in self.channels ]

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
        maxValSlider.setValue(100)
        canvas2D = Canvas2D(self, width=5, height=5)


        layout = QGridLayout()
        layout.addWidget(minValSlider,0,0,1,1)
        layout.addWidget(maxValSlider,0,1,1,1)
        layout.addWidget(canvas2D,0,2,1,1)

        self.groupCanvas2DBox.setLayout(layout)
        self.widgets['groupCanvas2D'] = [minValSlider,maxValSlider,canvas2D]

    def createCanvas3DGroupBox(self):
        self.groupCanvas3DBox = QGroupBox("")

        canvas3D = Canvas3D(self, width=5, height=5)

        layout = QGridLayout()
        layout.addWidget(canvas3D,0,0,6,6)

        self.groupCanvas3DBox.setLayout(layout)
        self.widgets['groupCanvas3D'] = [canvas3D]

    #%%
    def selectDir(self):
        new_base_dir = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if new_base_dir != '':
            self.base_dir = new_base_dir
            self.stacks = self.loadStacks()
            self.setEnableState(True)

    def saveData(self):
        if self.base_dir != '':
            print('Saving data to:\n\t', self.base_dir)

    def loadStacks(self):
        print('#'*40)
        print('Loading dataset at:\n\t', self.base_dir)
        print('#'*40)

    def setEnableState(self, state):
        self.groupObjectsControl.setEnabled(state)
        self.groupTZCControl.setEnabled(state)
        self.groupCanvas2DBox.setEnabled(state)
        self.groupCanvas3DBox.setEnabled(state)
        self.widgets['groupLoadSave'][1].setEnabled(state)        

    def updateTZC(self,who):
        if who=='T':
            print('Changing time')
        elif who=='Z':
            print('Changing Z plane')
        elif who=='C':
            print('Changing channel')

 
if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    gallery = MyGUI()
    gallery.show()
    sys.exit(app.exec_()) 
