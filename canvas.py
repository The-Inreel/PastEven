from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog, QGraphicsPathItem
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QPainterPath
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

class Canvas(QGraphicsView):
    
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.canvasColor = Qt.GlobalColor.white
        # Set canvas settings
        self.setSceneRect(0, 0, 1500, 900)
        self.setBackgroundBrush(self.canvasColor)
        
        self.last_point = None
        self.drawing = False
        self.current_path = None
        self.color = QColor(255, 0, 0)
        self.ppSize = 4
        self.tools = Tools.PENCIL
        
        self.undo_stack = []
        self.redo_stack = []
        self.saveLoc = None
    
    # Updates the brush color
    def updatePen(self):
        if self.tools == Tools.PENCIL:
            self.pp.setColor(self.color)
        else:  # Eraser
            self.pp.setColor(QColor(255, 255, 255))
        self.painter.setPen(self.pp)
            
    # Handles mouse movement drawing
    def mouseMoveEvent(self, event):
        if self.drawing:
            new_point = self.mapToScene(event.position().toPoint())
            self.current_path.lineTo(new_point)
            self.drawLineTo(new_point)
            self.last_point = new_point
    
    # Initializes drawing on mouse press
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = self.mapToScene(event.position().toPoint())
            self.current_path = QPainterPath()
            self.current_path.moveTo(self.last_point)
            self.clicked.emit()
    
    # Finalizes drawing on mouse release
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.finalizePath()

    # Clears the canvas on 'Q' key press
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Q:
            self.canvas.fill(color = Qt.GlobalColor.white)
            self.label.setPixmap(self.canvas)
            self.update()

        event.accept()
        
    def drawLineTo(self, end_point):
        if self.current_path:
            color = self.color if self.tools == Tools.PENCIL else Qt.white
            pen = QPen(color, self.ppSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            path_item = QGraphicsPathItem(self.current_path)
            path_item.setPen(pen)
            self.scene.addItem(path_item)
            self.current_path = QPainterPath(end_point)
    
    # Adds the current state to undo history
    def finalizePath(self):
        self.undo_stack.append(self.scene.items())
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            for item in self.undo_stack.pop():
                self.scene.removeItem(item)
            self.redo_stack.append(self.scene.items())
            self.update()

    def redo(self):
        if self.redo_stack:
            for item in self.redo_stack.pop():
                self.scene.addItem(item)
            self.undo_stack.append(self.scene.items())
            self.update()
    
    # Sets the current drawing tool (e.g., pencil or eraser)
    def setTool(self, tool):
        self.tools = tool
        
    def setColor(self, color):
        self.color = color
    
    def setPencilSize(self, size):
        self.ppSize = size
    
    # Sets the canvas color
    def setCanvasColor(self, color):
        self.canvas.fill(color)
        self.update()

    # Suggests the initial size for the widget
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
    
    # Checks if the file name has a valid image extension
    def hasImgExt(self, file_name):
        image_extensions = ['.png', '.jpeg', '.jpg']
        file_extension = os.path.splitext(file_name)[1].lower()
        return file_extension in image_extensions
    
    # Detects and adds borders in the current canvas image
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