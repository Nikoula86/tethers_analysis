from tifffile import imread
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QDialog, QSizePolicy, QApplication, QTableWidget, QVBoxLayout,
                            QPushButton, QColorDialog, QTableWidgetItem, QMessageBox,
                            QMainWindow, QLineEdit, QLabel)
from PyQt5.QtGui import QCursor, QColor
from PyQt5.QtCore import Qt
from matplotlib.colors import LinearSegmentedColormap
import copy, re
from ast import literal_eval

'''
# subwindow to define points
'''

class ObjectEditor(QDialog):
    def __init__(self, parent=None, 
                    objects = {'_ids': ['newobject']*4,
                        'colors': ['#6eadd8','#ff7f0e','red','#c4c4c4'],
                        'markers': ['o','o','X','-x'],
                        'ms': [3,3,5,1],
                        'is_instance': [0,1,0,1],
                        'coords': [np.array([]),np.array([[1., 1.]]),np.array([]),np.array([[1., 2.], [3., 4.]])] }):

        super(ObjectEditor, self).__init__(parent)
        QApplication.setStyle('Macintosh')

        table = QTableWidget()
        table.setRowCount(len(objects['_ids']))
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['Object name', 'Color', 'Marker', 'Marker size', 'are instances', 'coords'])
        self.table = table

        addObj = QPushButton('Add object.')
        addObj.setFocusPolicy(Qt.NoFocus)
        addObj.clicked.connect(self.addRow)

        removeObj = QPushButton('Remove object.')
        removeObj.setFocusPolicy(Qt.NoFocus)
        removeObj.clicked.connect(self.removeRow)

        saveButton = QPushButton('Save objects.')
        saveButton.setFocusPolicy(Qt.NoFocus)
        saveButton.clicked.connect(self.saveObjects)

        layout = QVBoxLayout()
        layout.addWidget(table) 
        layout.addWidget(addObj)        
        layout.addWidget(removeObj)        
        layout.addWidget(saveButton)

        self.setLayout(layout)

        self.populateTable(objects)
        table.doubleClicked.connect(self.doubleClickEvent)
        self.setWindowTitle('Objects Editor')
        self.setTableWidth()

    def setTableWidth(self):
        width = self.table.verticalHeader().width()
        width += self.table.horizontalHeader().length()
        if self.table.verticalScrollBar().isVisible():
            width += self.table.verticalScrollBar().width()
        width += self.table.frameWidth() * 2
        self.table.setFixedWidth(width)

    def populateTable(self, objects):
        (_ids,colors,markers,ms,n,coords) = ( val for key, val in objects.items() )
        self.table.setRowCount(len(_ids))
        for i in range(len(_ids)):
            self.table.setItem(i,0, QTableWidgetItem(_ids[i]))
            self.table.setItem(i,1, QTableWidgetItem()); self.table.item(i,1).setBackground(QColor(colors[i]))
            self.table.setItem(i,2, QTableWidgetItem(markers[i]))
            self.table.setItem(i,3, QTableWidgetItem(str(ms[i])))
            self.table.setItem(i,4, QTableWidgetItem(str(n[i])))
            self.table.setItem(i,5, QTableWidgetItem("%s"%(coords[i])))
            
        for j in range(self.table.rowCount()):
            self.table.setItem(j,4, QTableWidgetItem(str(n[j])))
            flags = self.table.item(j, 4).flags()
            flags &= ~Qt.ItemIsSelectable
            flags &= ~Qt.ItemIsEditable
            flags &= ~Qt.ItemIsEnabled
            self.table.item(j, 4).setFlags(flags)

    def doubleClickEvent(self, click):
        if click.column() == 1:
            color = QColorDialog.getColor()
            self.table.item(click.row(),click.column()).setBackground(QColor(color))
            return

    def addRow(self):
        self.table.insertRow(self.table.rowCount())
        i = self.table.rowCount()-1
        self.table.setItem(i,0, QTableWidgetItem('newobject'))
        color = self.table.item(i-1,1).background().color().name()
        self.table.setItem(i,1, QTableWidgetItem()); self.table.item(i,1).setBackground(QColor(color))
        self.table.setItem(i,2, QTableWidgetItem(self.table.item(i-1,2).text()))
        self.table.setItem(i,3, QTableWidgetItem(str(self.table.item(i-1,3).text())))
        self.table.setItem(i,4, QTableWidgetItem(str(0)))
        self.table.setItem(i,5, QTableWidgetItem("%s"%(np.array([]))))        

    def removeRow(self):
        if self.table.rowCount()>0:
            indices = self.table.selectedIndexes()
            index = list([i.row() for i in indices])
            index.sort()
            index = set(index)
            if len(index) == 0:
                return
            elif len(index) > 1:
                QMessageBox.warning(self,'Warning!','Please remove only one object at a time...')
            else:
                index = list(index)[0]
                if int(self.table.item(index,4).text()) == 0:
                    self.table.removeRow(index)
                else:
                    answer = QMessageBox.question(self, 'Warning!', "The object \"%s\" has instances in the image. Are you sure you want to delete it?" %(self.table.item(index,0).text()))
                    if answer == QMessageBox.Yes:
                        self.table.removeRow(index)

    def saveObjects(self):
        outobjects = {}
        outobjects['_ids'] = [self.table.item(i,0).text() for i in range(self.table.rowCount())]
        outobjects['colors'] = [self.table.item(i,1).background().color().name() for i in range(self.table.rowCount())]
        outobjects['markers'] = [self.table.item(i,2).text() for i in range(self.table.rowCount())]
        outobjects['ms'] = [self.table.item(i,3).text() for i in range(self.table.rowCount())]
        outobjects['is_instance'] = [int(self.table.item(i,4).text()) for i in range(self.table.rowCount())]
        outobjects['coords'] = []
        for i in range(self.table.rowCount()):
            val = self.table.item(i,5).text()
            outobjects['coords'].append(np.array(literal_eval(re.sub(' +', ' ',val).replace(' ',','))))
        self.outobjects = outobjects
        super().accept()

class DimensionDefiner(QDialog):
 
    def __init__(self, parent = None, shape = (1,1,1)):
        super(DimensionDefiner, self).__init__(parent)
        self.setWindowTitle('Dimension definition')
        self.shape = shape

        lbl = QLabel('Image shape: %s.\nDimension id:'%str(shape),self)
        lbl.move(28,5)

        self.textbox = QLineEdit(self)
        guess = 'TZCHW'[-len(shape):]
        self.textbox.setText(guess)
        self.textbox.move(28, 40)
        self.textbox.resize(72,20)

        button = QPushButton('Confirm', self)
        button.move(20,60)
        button.setFocusPolicy(Qt.NoFocus)
        button.clicked.connect(self.on_click)
        self.resize(190,100)

    def on_click(self):
        shape = self.shape
        text = self.textbox.text().strip().upper()
        if len(text) != len(shape):
            QMessageBox.warning(self,'Warning!','Can\'t assign dimensions ids (%s) \nto shape %s...'%(text,str(shape)))
        elif any([i not in 'TZCHW' for i in text]):
            QMessageBox.warning(self,'Warning!','(%s) is an invalid dimension id.\nValid ids are \'TZCHW\''%(text))
        elif any([text.count(_id)!=1 for _id in set(text)]):
            QMessageBox.warning(self,'Warning!','(%s) is an invalid dimension id.\nDimension ids can\'t repeat!'%(text))
        else:
            self.text = text
            super().accept()


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    gallery = DimensionDefiner()
    gallery.show()
    sys.exit(app.exec_()) 

