import sys
import os

from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QToolBar, QSlider, QSizePolicy, QVBoxLayout, QFileDialog
from PyQt6 import QtGui, QtCore
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap
from enum import Enum

from PIL import ImageQt 
from PIL import Image

import cv2
import numpy as np

class Tools(Enum):
    PENCIL = 1
    ERASER = 2

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel(self)
    
        # Set canvas settings
        self.canvas = QPixmap(1500, 900)
        self.canvas.fill(color = Qt.GlobalColor.white)
        self.last_x, self.last_y = None, None
        self.label.setPixmap(self.canvas)
        self.pixmap_history = []
        self.pixmap_redohist = []
        self.tools = Tools.PENCIL
        self.color = QtGui.QColor(255, 0, 0)
        self.painter = None
        self.ppSize = 4
        self.brush = QtGui.QBrush(Qt.GlobalColor.black, Qt.BrushStyle.SolidPattern)
        self.pp = QtGui.QPen(Qt.GlobalColor.black, self.ppSize, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        self.pp.setBrush(self.brush)
        self.saveLoc = None
        
         
    def mouseMoveEvent(self, event):
        if self.last_x is None: # First event.
            self.last_x = event.position().x()
            self.last_y = event.position().y()
            return # Ignore the first time.
        self.drawStroke(event)
        
        self.last_x = event.position().x()
        self.last_y = event.position().y()
    
    def mousePressEvent(self, event):
        self.addUndo()
        
    def mouseReleaseEvent(self, event):
        self.last_x = None
        self.last_y = None
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Q:
            self.canvas.fill(color = Qt.GlobalColor.white)
            self.label.setPixmap(self.canvas)
            self.update()
        elif event.key() == QtCore.Qt.Key.Key_P:
            self.findBorder()

        event.accept()
        
    def drawStroke(self, event):
        # Sets the pen color to the color var if using pencil else it will set to white (erase)
        self.pp.setColor(self.color if self.tools == Tools.PENCIL else QtGui.QColor(255, 255, 255))
        self.pp.setWidth(self.ppSize)
        self.painter = QtGui.QPainter(self.canvas)
        self.painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.painter.setPen(self.pp)
        
        self.painter.drawLine(int(self.last_x), int(self.last_y), int(event.position().x()), int(event.position().y()))
        self.painter.end()
        self.label.setPixmap(self.canvas)
        self.update()
        
    def addUndo(self):
        if len(self.pixmap_history) > 30: #20 felt weak so gave them 30, redo is limited by undo
            self.pixmap_history.pop(0)
            
        self.pixmap_history.append(self.canvas.copy())
        self.pixmap_redohist.clear()

    def undo(self):
        if self.pixmap_history:
            self.pixmap_redohist.append(self.canvas.copy())
            self.canvas = self.pixmap_history.pop()
            self.label.setPixmap(self.canvas)
            self.update()

    def redo(self):
        if self.pixmap_redohist:
            self.pixmap_history.append(self.canvas.copy())
            self.canvas = self.pixmap_redohist.pop()
            self.label.setPixmap(self.canvas)
            self.update()
            
    def setTool(self, tool):
        self.tools = tool
    
    def setPencilSize(self, value):
        self.ppSize = value

    def sizeHint(self):
        return QSize(1500, 900)

    def save(self):
        if self.saveLoc is None:
            path = self.save_file_dialog()
            if path != "":
                self.saveLoc = path
                self.label.pixmap().toImage().save(path)
        else:
            self.label.pixmap().toImage().save(self.saveLoc)
        
    def load(self):
        self.addUndo()
        path = self.open_file_dialog()
        if path != "":
            self.canvas = QtGui.QPixmap(path)
            self.saveLoc = path
            self.label.setPixmap(self.canvas)
            self.update()
        
    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Load Image', "./")
        return file_name
    
    def save_file_dialog(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save Image', "./", "Image (*.png)")
        if not self.has_image_extension(file_name):
            file_name + ".png"
        return file_name
    
    def has_image_extension(self, file_name):
        image_extensions = ['.png', '.jpeg', '.jpg']
        file_extension = os.path.splitext(file_name)[1].lower()
        return file_extension in image_extensions
    
    def findBorder(self):
        pixmapAsImage = self.label.pixmap().toImage()
        width, height = pixmapAsImage.width(), pixmapAsImage.height()
        bytes_per_pixel = pixmapAsImage.depth() // 8
        temp = pixmapAsImage.constBits()
        temp.setsize(pixmapAsImage.sizeInBytes())
        cv_image = np.array(temp).reshape(height, width, bytes_per_pixel)
        
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        canny_image = cv2.Canny(gray, 0, 100)
                
        contours, _ = cv2.findContours(canny_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(cv_image, contours, -1, (0, 0, 0), -199)
        
        # last number is for offset (MAMA!)
        
        PIL_image = Image.fromarray(cv_image)
        # DO NOT REMOVE THE SECOND RGB SWAP IT WILL EXPLODE PLEASE DONT I DONT WANT TO ACTUALLY DEBUG
        self.label.setPixmap(QPixmap.fromImage((ImageQt.toqimage(PIL_image)).rgbSwapped().rgbSwapped()))
        self.update()
        self.addUndo()
        self.canvas = self.label.pixmap()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
    
        self.setWindowTitle("PastEven")
        self.setMinimumSize(QSize(1500, 1000))

        self.layout = QVBoxLayout()
        
        self.toolBar = QToolBar()
        self.canvas = Canvas()
        # Attempted to make a spacer may change tho
        self.spacerT = QWidget()
        self.spacerT.setFixedWidth(100)
        self.spacerT.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setStyleSheet("background: #E0FFFF")

        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.canvas.save)
        saveButton.setIcon(QtGui.QIcon("resources/icons/save.png"))
        saveButton.setShortcut('Ctrl+S')
        self.toolBar.addWidget(saveButton)

        loadButton = QPushButton("Load")
        loadButton.clicked.connect(self.canvas.load)
        loadButton.setIcon(QtGui.QIcon("resources/icons/load.png"))
        loadButton.setShortcut('Ctrl+L')
        self.toolBar.addWidget(loadButton)

        borderButton = QPushButton("Border")
        borderButton.clicked.connect(self.canvas.findBorder)
        borderButton.setIcon(QtGui.QIcon("resources/icons/border.png"))
        borderButton.setShortcut('Ctrl+P')
        self.toolBar.addWidget(borderButton)
        
        self.toolBar.addSeparator()

        # Add buttons to toolbar - undo and redo respectively
        undoButton = QPushButton("Undo")
        undoButton.clicked.connect(self.canvas.undo)
        undoButton.setShortcut('Ctrl+Z')
        self.toolBar.addWidget(undoButton)

        redoButton = QPushButton("Redo")
        redoButton.clicked.connect(self.canvas.redo)
        redoButton.setShortcut('Ctrl+Y')
        self.toolBar.addWidget(redoButton)
        
        self.toolBar.addSeparator()
        
        pencilButton = QPushButton()
        pencilButton.clicked.connect(lambda: self.canvas.setTool(Tools.PENCIL))
        pencilButton.setIcon(QtGui.QIcon("resources/icons/pencil.png"))
        pencilButton.setCheckable(True)
        pencilButton.setChecked(True)
        self.toolBar.addWidget(pencilButton)
        
        eraserButton = QPushButton()
        eraserButton.clicked.connect(lambda: self.canvas.setTool(Tools.ERASER))
        eraserButton.setIcon(QtGui.QIcon("resources/icons/eraser.png"))
        eraserButton.setCheckable(True)
        self.toolBar.addWidget(eraserButton)
        
        pencilButton.clicked.connect(lambda: self.toolButtonClicked(eraserButton))
        eraserButton.clicked.connect(lambda: self.toolButtonClicked(pencilButton))
        
        self.sizeSlider = QSlider()
        self.sizeSlider.setMinimum(1)
        self.sizeSlider.setMaximum(100)
        self.sizeSlider.setValue(4)
        self.toolBar.addWidget(self.sizeSlider)

        self.historySlider = QSlider()
        self.historySlider.setMinimum(0)
        self.historySlider.setMaximum(len(self.canvas.pixmap_history) - 1)
        self.historySlider.setValue(len(self.canvas.pixmap_history) - 1)
        self.historySlider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.historySlider.setMaximumWidth(400)
        
        self.sizeLabel = QLabel(str(self.canvas.ppSize))
        self.toolBar.addWidget(self.sizeLabel)
        self.toolBar.addSeparator()

        # added spacer to use text - improve later when i know how to like actually change the spacing
        # p.s. we should probably use some kind of organizer like a vbox or whatever its called
        self.toolBar.addWidget(self.spacerT)
        self.spacer = QLabel("History:        ")
        self.toolBar.addWidget(self.spacer)

        # gave toolbar bit of color so we can see
        self.toolBar.setStyleSheet("QToolBar { background : #E0FFFF }")
        self.toolBar.addWidget(self.historySlider)
        self.toolBar.toggleViewAction().setEnabled(False)
        # prevents hiding toolbar cuz if you remove it, you can't add it back
        
        self.sizeSlider.valueChanged.connect(self.canvas.setPencilSize)
        self.sizeSlider.valueChanged.connect(lambda value: self.sizeLabel.setText(str(value)))
        self.historySlider.sliderMoved.connect(self.actionTriggered)

        # Added the label as a central widget instead of the whole thing, and added the toolbar
        # self.setCentralWidget(self.layout)
        self.addToolBar(self.toolBar)
        self.layout.addWidget(self.canvas)
        self.layout.setAlignment(self.canvas, Qt.AlignmentFlag.AlignHCenter)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.layout)
        
    # When more tools come change other tools to a list or something idk
    # Rn it just toggles the button use when clicked more of a visual thing
    def toolButtonClicked(self, otherTools):
        sender = self.sender()
        sender.setChecked(True)
        otherTools.setChecked(False)
    
    def mousePressEvent(self, event):
        self.historySlider.setMaximum(len(self.canvas.pixmap_history) - 1)

    # had to do a bunch of research on how this signal processing works but
    # essentially if you move the slider one way it undoes, other way redoes
    def actionTriggered(self, val):
        if val > self.historySlider.value():
            self.canvas.undo()
        elif val < self.historySlider.value():
            self.canvas.redo()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())