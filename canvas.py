from PySide6.QtWidgets import QWidget, QLabel, QFileDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize, Qt, Signal
from PySide6 import QtGui, QtCore

from enum import Enum
from PIL import ImageQt, Image
import cv2
import numpy as np
import os

class Tools(Enum):
    PENCIL = 1
    ERASER = 2

class Canvas(QWidget):
    
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel(self)
    
        # Set canvas settings
        self.canvas = QPixmap(1500, 900)
        self.canvas.fill(fillColor = Qt.GlobalColor.white)
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
        self.last_x = event.position().x()
        self.last_y = event.position().y()
        self.drawDot(event)
        
    def mouseReleaseEvent(self, event):
        self.last_x = None
        self.last_y = None
        self.setFocus()
        self.clicked.emit()

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
        
    def drawDot(self, event):
        self.pp.setColor(self.color if self.tools == Tools.PENCIL else QtGui.QColor(255, 255, 255))
        self.pp.setWidth(self.ppSize)
        self.painter = QtGui.QPainter(self.canvas)
        self.painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.painter.setPen(self.pp)

        self.painter.drawPoint(int(event.position().x()), int(event.position().y()))
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
            path = self.saveFileDialog()
            if path:
                self.saveLoc = path
                self.label.pixmap().toImage().save(path)
        else:
            self.label.pixmap().toImage().save(self.saveLoc)
        
    def load(self):
        self.addUndo()
        path = self.openFileDialog()
        if path:
            self.canvas = QtGui.QPixmap(path)
            self.saveLoc = path
            self.label.setPixmap(self.canvas)
            self.update()
        
    def openFileDialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Load Image', "./")
        return file_name
    
    def saveFileDialog(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save Image', "./", "Image (*.png)")
        if not self.hasImgExt(file_name):
            file_name + ".png"
        return file_name
    
    def hasImgExt(self, file_name):
        image_extensions = ['.png', '.jpeg', '.jpg']
        file_extension = os.path.splitext(file_name)[1].lower()
        return file_extension in image_extensions
    
    def findBorder(self):
        pixmapAsImage = self.label.pixmap().toImage()
        width, height = pixmapAsImage.width(), pixmapAsImage.height()
        bytes_per_pixel = pixmapAsImage.depth() // 8
        temp = bytearray(pixmapAsImage.bits())
        temp = memoryview(temp)
        temp = temp.cast('B')
        temp = temp[:pixmapAsImage.sizeInBytes()]
        cv_image = np.array(temp).reshape(height, width, bytes_per_pixel)
        
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        canny_image = cv2.Canny(gray, 0, 100)
                
        contours, _ = cv2.findContours(canny_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(cv_image, contours, -1, (0, 0, 0), thickness=-1)
        
        # This was an idea to increase the size of the border whenever the pen size is large enough
        # cv2.drawContours(cv_image, contours, -1, (0, 0, 0), thickness = (self.ppSize // 30) + 1)
        
        
        # last number is for offset (MAMA!) 
        # L youre wrong it was the thickness get better - Ethan
        
        blurred_image = cv_image.copy()
        blurred_image[canny_image != 0] = cv2.GaussianBlur(blurred_image[canny_image != 0], (15, 15), 1)
    
        PIL_image = Image.fromarray(blurred_image)
        # DO NOT REMOVE THE SECOND RGB SWAP IT WILL EXPLODE PLEASE DONT I DONT WANT TO ACTUALLY DEBUG
        self.label.setPixmap(QPixmap.fromImage((ImageQt.toqimage(PIL_image)).rgbSwapped().rgbSwapped()))
        self.update()
        self.addUndo()
        self.canvas = self.label.pixmap()