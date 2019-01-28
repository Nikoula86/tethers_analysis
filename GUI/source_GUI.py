from PyQt5.QtGui import QCursor, QPixmap, QColor,QPainter
from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFileDialog, QMessageBox, QErrorMessage)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from tifffile import imread
import pandas as pd
import os, pickle, time
import utils as ut

class MyGUI(QDialog):
    def __init__(self, parent=None):
        super(MyGUI, self).__init__(parent)

        self.points_id = ['tether_Atrium','tether_Ventricle','AVCanal','Midline']
        self.points_colors = ['#1f77b4','#ff7f0e','black','grey']
        self.points = ut.PointObjects(self.points_id)
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

        # objectIDBox = QPushButton('Manage objects');
        # objectLabel = QLabel("&Object ID:"); objectLabel.setBuddy(objectIDBox)  

        layout = QGridLayout()
        layout.addWidget(objectLabel,0,0)
        layout.addWidget(objectIDBox,0,1)

        self.groupObjectsControl.setLayout(layout)
        self.groupObjectsControl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.widgets['groupObjects'] = [objectIDBox]

    def createTZCControlGroupBox(self):
        self.groupTZCControl = QGroupBox("")

        TBox = QSpinBox(); TBox.setValue(0)
        self.TLabel = QLabel("&Contraction phase\n(0-?)"); self.TLabel.setBuddy(TBox)
        TBox.setKeyboardTracking(False)
        TBox.valueChanged.connect(self.updateCanvas2D)

        ZBox = QSpinBox(); ZBox.setValue(0)
        self.ZLabel = QLabel("&Z plane\n(0-?)"); self.ZLabel.setBuddy(ZBox)
        ZBox.setKeyboardTracking(False)
        ZBox.valueChanged.connect(self.updateCanvas2D)

        CBox = QComboBox(); CBox.addItems(self.channels)
        CLabel = QLabel("&Channel:"); CLabel.setBuddy(CBox)
        CBox.currentIndexChanged.connect(self.updateCcontrolled)
        
        swapChannelButton = QPushButton("Swap channel colors")
        swapChannelButton.setFocusPolicy(Qt.NoFocus)
        swapChannelButton.clicked.connect(self.swapColors)

        chBox = [ QCheckBox(ch) for ch in self.channels ]
        [ box.stateChanged.connect(self.updateCanvas2D) for box in chBox ]
        [ box.setCheckState(False) for box in chBox ]
        self.chVal = [ [0,2**16-1] for ch in self.channels ]

        layout = QGridLayout()
        layout.addWidget(self.TLabel,0,0); layout.addWidget(TBox,0,1)
        layout.addWidget(self.ZLabel,1,0); layout.addWidget(ZBox,1,1)
        layout.addWidget(CLabel,2,0); layout.addWidget(CBox,2,1)
        layout.addWidget(swapChannelButton,3,0,1,2);
        for i, b in enumerate( chBox ):
            layout.addWidget(b,i+4,0)

        self.groupTZCControl.setLayout(layout)
        self.widgets['groupTZC'] = [TBox,ZBox,CBox,*chBox]

    def createCanvas2DGroupBox(self):
        self.groupCanvas2DBox = QGroupBox("")

        minValSlider = QSlider(Qt.Vertical)
        maxValSlider = QSlider(Qt.Vertical)
        maxValSlider.setValue(2**16-1)
        maxValSlider.setMaximum(2**16-1)
        minValSlider.setMaximum(2**16-1)
        canvas2D = ut.Canvas2D(self, width=10, height=5)

        navi_toolbar = NavigationToolbar(canvas2D, self)
        navi_toolbar.setFocusPolicy(Qt.NoFocus)
        navi_toolbar.setMaximumHeight(30)

        layout = QGridLayout()
        layout.addWidget(minValSlider,1,0,1,1)
        layout.addWidget(maxValSlider,1,1,1,1)
        layout.addWidget(canvas2D,1,2,1,1)
        layout.addWidget(navi_toolbar,0,2,1,1)

        self.groupCanvas2DBox.setLayout(layout)
        self.widgets['groupCanvas2D'] = [minValSlider,maxValSlider,canvas2D]

        minValSlider.valueChanged.connect(self.updateBCslider)
        maxValSlider.valueChanged.connect(self.updateBCslider)
        self.press = False
        self.move = False
        canvas2D.mpl_connect('button_press_event', self.onpress)
        canvas2D.mpl_connect('motion_notify_event', self.onmove)
        canvas2D.mpl_connect('button_release_event', self.mouseClick)

    def createCanvas3DGroupBox(self):
        self.groupCanvas3DBox = QGroupBox("")

        isplot = QCheckBox('Show live 3D plot')
        isphase = QCheckBox('Show only current contraction phase')
        canvas3D = ut.Canvas3D(self, width=2, height=2)

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
    def getTZC(self):
        t = int( self.widgets['groupTZC'][0].value() )
        z = int( self.widgets['groupTZC'][1].value() )
        c = int( self.widgets['groupTZC'][2].currentIndex() )
        return (t, z, c)

    def selectImageFile(self):
        new_file,_ = QFileDialog.getOpenFileName(self, "Select Merged File")
        if new_file.split('.')[-1] not in ['tif','tiff']:
            QMessageBox.warning(self,'Warning, invalid input file!','Only \".tif\"" file implemented so far')
            return
        if new_file != '':
            self.setEnableState(True)
            self.file_name = new_file
            self.stacks, self._maxval = ut.loadStacks(self.file_name)

            self.widgets['groupTZC'][0].setMaximum(self.stacks.shape[0]-1)
            self.widgets['groupTZC'][1].setMaximum(self.stacks.shape[1]-1)
            self.widgets['groupCanvas2D'][0].setMaximum(self._maxval[0,0])
            self.widgets['groupCanvas2D'][1].setMaximum(self._maxval[0,0])
            self.widgets['groupCanvas2D'][1].setValue(self._maxval[0,0])

            self.TLabel.setText("&Contraction phase\n(0-%s)"%str(self.stacks.shape[0]))
            self.ZLabel.setText("&Z plane\n(0-%s)"%str(self.stacks.shape[1]))

            self.widgets['groupCanvas3D'][0].plot(self.points_id,self.points.coords,self.stacks.shape[0])

            for i in range(self.stacks.shape[2]):
                self.widgets['groupTZC'][i+3].setChecked(True)
            for i in range(2):
                self.widgets['groupTZC'][2].setCurrentIndex(i)
                self.updateBCslider()
            self.updateCanvas2D()

    def selectPointsFile(self):
        new_file,_ = QFileDialog.getOpenFileName(self, "Select Merged File")
        if new_file != '':
            if new_file.split('.')[-1] not in ['p','pickle']:
                QMessageBox.warning(self,'Warning, invalid input file!','Only pickle file implemented so far:\n please choose a valid \".p\" file')
            else:
                self.points.coords = pickle.load(open(new_file,'rb'))
                (t, z, c) = self.getTZC()
                self.widgets['groupCanvas2D'][2].updateScatter(t, z, self.points.coords)
                self.updateCanvas3D()

    def saveData(self):
        save_file_name, _ = QFileDialog.getSaveFileName(self,"Save file")
        if save_file_name != '':
            if (save_file_name[-2:]=='.p') and (len(save_file_name)>2):
                print('#'*40)
                print('Saving data to:\n\t', save_file_name)
                pickle.dump(self.points.coords,open(save_file_name,'wb'))
                print('Done')
            else:
                QMessageBox.warning(self,'Warning, invalid file name!','Only pickle file saving is implemented so far:\n please chose a \".p\" file name')

    def swapColors(self):
        self.stacks, self._maxval = ut.swapAxes( self.stacks, self._maxval, ax=2 )
        self.updateCanvas2D()

    def setEnableState(self, state):
        self.groupObjectsControl.setEnabled(state)
        self.groupTZCControl.setEnabled(state)
        self.groupCanvas2DBox.setEnabled(state)
        self.groupCanvas3DBox.setEnabled(state)
        self.widgets['groupLoadSave'][1].setEnabled(state)       
        self.widgets['groupLoadSave'][2].setEnabled(state)       

    def updateCanvas2D(self):
        (t, z, c) = self.getTZC()
        # print('Current TZC: ',t,z)
        self.widgets['groupCanvas2D'][2].reshowImg(self.stacks[t,z], self.widgets['groupTZC'][3:], self.chVal)
        self.widgets['groupCanvas2D'][2].updateScatter(t, z, self.points.coords)

    def updateCanvas3D(self):
        if not self.widgets['groupCanvas3D'][1].checkState():
            return
        (t, z, c) = self.getTZC()
        point_plot = { _id: self.points.coords[_id] for _id in self.points_id }

        # only show the current contraction phase
        if self.widgets['groupCanvas3D'][2].checkState():
            for _id in self.points_id:
                if point_plot[_id].shape[0] > 0:
                    point_plot[_id] = point_plot[_id][point_plot[_id][:,3]==t]

        # update all lines
        self.widgets['groupCanvas3D'][0].plot(self.points_id,point_plot,self.stacks.shape[0])

    def updateCcontrolled(self):
        (t, z, c) = self.getTZC()

        self.widgets['groupCanvas2D'][0].setMaximum(self._maxval[t,c])
        self.widgets['groupCanvas2D'][1].setMaximum(self._maxval[t,c])

        self.widgets['groupCanvas2D'][0].blockSignals(True)
        self.widgets['groupCanvas2D'][1].blockSignals(True)
        self.widgets['groupCanvas2D'][0].setValue(self.chVal[c][0])
        self.widgets['groupCanvas2D'][1].setValue(self.chVal[c][1])
        self.widgets['groupCanvas2D'][0].blockSignals(False)
        self.widgets['groupCanvas2D'][1].blockSignals(False)

        self.updateBCslider()

    def updateBCslider(self):
        (t, z, c) = self.getTZC()

        vmin = int( self.widgets['groupCanvas2D'][0].value() )
        vmax = int( self.widgets['groupCanvas2D'][1].value() )

        self.chVal[c] = [ vmin, vmax ]

        if self.widgets['groupCanvas2D'][0].value() >= self.widgets['groupCanvas2D'][1].value():
            self.widgets['groupCanvas2D'][0].setValue(self.widgets['groupCanvas2D'][1].value()-1)
            vmin = int( self.widgets['groupCanvas2D'][0].value() )

        self.updateCanvas2D()

        # self.widgets['groupCanvas2D'][2].images_shown[c].set_clim([vmin,vmax])
        # self.widgets['groupCanvas2D'][2].draw()

    def onpress(self,event):
        self.start = time.time()
        self.press = True

    def onmove(self,event):
        if self.press:
            self.move = True

    def mouseClick(self, event):
        lagtime = time.time() - self.start
        if self.press and ( (not self.move) or (lagtime<.05) ):
            # print('Mouse clicked! ', event)
            obj_id = self.widgets['groupObjects'][0].currentText()
            (t, z, c) = self.getTZC()
            click_coord = np.array([np.rint(event.xdata),np.rint(event.ydata),z,t])
            self.points.updatePoints(self.widgets['groupObjects'][0].currentText(),click_coord,event)
            self.widgets['groupCanvas2D'][2].updateScatter(t, z, self.points.coords)
            self.updateCanvas3D()
        self.press = False
        self.move = False

# if __name__ == '__main__':

import sys

app = QApplication(sys.argv)
gallery = MyGUI()
gallery.show()
sys.exit(app.exec_()) 
