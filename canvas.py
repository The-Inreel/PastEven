from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QPainterPath, QBrush, QImage
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6 import QtCore

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
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.canvasColor = Qt.GlobalColor.white
        # Set canvas settings
        self.setSceneRect(0, 0, 1500, 900)
        self.setBackgroundBrush(self.canvasColor)
        
        self.last_point = None
        self.drawing = False
        self.singlePoint = True
        self.currentPath = None
        self.pathItem = None
        self.color = QColor(255, 0, 0)
        self.ppSize = 4
        self.tools = Tools.PENCIL
        
        self.undoStack = []
        self.redoStack = []
        self.saveLoc = None
    
    # Updates the brush color
    def updatePen(self):
        if self.tools == Tools.PENCIL:
            self.pp.setColor(self.color)
        else:  # Eraser
            self.pp.setColor(QColor(255, 255, 255))
        self.painter.setPen(self.pp)
    
    # Initializes drawing on mouse press
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.singlePoint = True
            self.last_point = self.mapToScene(event.position().toPoint())
            self.currentPath = QPainterPath()
            self.currentPath.moveTo(self.last_point)
            self.pathItem = None
            self.clicked.emit()
            
    # Handles mouse movement drawing
    def mouseMoveEvent(self, event):
        if self.drawing:
            self.singlePoint = False
            new_point = self.mapToScene(event.position().toPoint())
            self.currentPath.quadTo(self.last_point, (self.last_point + new_point) / 2)
            self.drawLineTo(new_point)
            self.last_point = new_point
    
    # Finalizes drawing on mouse release
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            if self.singlePoint:
                self.drawSinglePoint(self.last_point)
            self.drawing = False
            self.finalizePath()

    # Clears the canvas on 'Q' key press
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Q:
            self.canvas.fill(color = Qt.GlobalColor.white)
            self.label.setPixmap(self.canvas)
            self.update()

        event.accept()
    
    # Draws a line to the given end point
    def drawLineTo(self, end_point):
        if self.currentPath:
            color = self.color if self.tools == Tools.PENCIL else Qt.white
            pen = QPen(color, self.ppSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            if self.pathItem is None:
                self.pathItem = self.scene.addPath(self.currentPath, pen)
            else:
                self.pathItem.setPath(self.currentPath)
    
    # Draws a single point at the specified location   
    def drawSinglePoint(self, point):
        color = self.color if self.tools == Tools.PENCIL else Qt.white
        pen = QPen(color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        brush = QBrush(color)
        ellipse_size = self.ppSize
        ellipse = QRectF(point.x() - ellipse_size / 2, point.y() - ellipse_size / 2, 
                         ellipse_size, ellipse_size)
        self.pathItem = self.scene.addEllipse(ellipse, pen, brush)
    
    # Adds the current state to undo history
    def finalizePath(self):
        if self.pathItem:
            self.undoStack.append([self.pathItem])
            self.redoStack.clear()
            self.pathItem = None

    # Undoes the last action
    def undo(self):
        if self.undoStack:
            action = self.undoStack.pop()
            redo_action = []
            for item in action:
                self.scene.removeItem(item)
                redo_action.append(item)
            self.redoStack.append(redo_action)
            self.update()

    # Redoes the last undone action
    def redo(self):
        if self.redoStack:
            action = self.redoStack.pop()
            undo_action = []
            for item in action:
                self.scene.addItem(item)
                undo_action.append(item)
            self.undoStack.append(undo_action)
            self.update()
    
    # Sets the current drawing tool (e.g., pencil or eraser)
    def setTool(self, tool):
        self.tools = tool
    
    # Sets the current drawing color
    def setColor(self, color):
        self.color = color
    
    # Sets the size of the pencil/eraser
    def setPencilSize(self, size):
        self.ppSize = size
    
    # Sets the canvas color
    def setCanvasColor(self, color):
        self.canvas.fill(color)
        self.update()

    # Saves the current image to a file
    def save(self):
        if self.saveLoc is None:
            path = self.saveFileDialog()
            if path:
                self.saveLoc = path
                self.saveImage(path)
        else:
            self.saveImage(self.saveLoc)

    # Loads an image from a file
    def load(self):
        path = self.openFileDialog()
        if path:
            self.loadImage(path)
            self.saveLoc = path
    
    # Helper that saves the current scene to an image file
    def saveImage(self, path):
        image = QImage(self.sceneRect().size().toSize(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()
        image.save(path)

    # Helper that loads an image from a file and displays it on the canvas
    def loadImage(self, path):
        image = QImage(path)
        if not image.isNull():
            self.scene.clear()
            self.undoStack.clear()
            self.redoStack.clear()
            pixmap = QPixmap.fromImage(image)
            self.scene.addPixmap(pixmap)
            self.setSceneRect(pixmap.rect())
            self.update()
    
    # Opens a file dialog to select an image to load
    def openFileDialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Load Image', "./")
        return file_name
    
    # Opens a file dialog to save the current image
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
    # TODO: Fix this
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