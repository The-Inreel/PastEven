from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog, QGraphicsRectItem
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QPainterPath, QBrush, QImage
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6 import QtCore

from enum import Enum
from PIL import ImageQt, Image
from tools import RectangleSelectTool, PenTool, EraserTool
import cv2
import numpy as np
import os

class Tools(Enum):
    PENCIL = 1
    ERASER = 2
    RECTANGLE_SELECT = 3

class Canvas(QGraphicsView):
    
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.canvasColor = Qt.GlobalColor.transparent
        self.setMouseTracking(True)
        # Set canvas settings
        self.canvasSize = (1500, 900)
        self.pixmap = QPixmap(*self.canvasSize)
        self.pixmap.fill(Qt.transparent)
        self.pixmapItem = self.scene.addPixmap(self.pixmap)
        
        self.border = self.scene.addRect(self.pixmap.rect(), QPen(Qt.gray, 2))
        
        self.color = QColor(255, 0, 0)
        self.ppSize = 4
        self.tools = Tools.PENCIL
        self.penTool = PenTool(self)
        self.eraserTool = EraserTool(self)
        self.rectangleSelectTool = RectangleSelectTool(self)
        self.currentTool = self.penTool
        
        self.undoStack = []
        self.redoStack = []
        self.saveLoc = None
    
    # Initializes drawing on mouse press
    def mousePressEvent(self, event):
        self.currentTool.handleMousePress(event)
        self.clicked.emit()
            
    # Handles mouse movement drawing
    def mouseMoveEvent(self, event):
        self.currentTool.handleMouseMove(event)
    
    # Finalizes drawing on mouse release
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.currentTool.handleMouseRelease(event)
        
    # Handles key presses
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Q:
            self.clearCanvas()
        elif event.key() == QtCore.Qt.Key.Key_Delete:
            self.deleteSelectedArea()
        elif event.key() == QtCore.Qt.Key.Key_C and event.modifiers() & QtCore.Qt.ControlModifier:
            self.copySelectedArea()
        event.accept()

    # Clears all drawings from the canvas
    def clearCanvas(self):
        self.scene.clear()
        self.pixmap.fill(Qt.GlobalColor.transparent)
        self.pixmapItem = self.scene.addPixmap(self.pixmap)
        self.border = self.scene.addRect(self.pixmap.rect(), QPen(Qt.gray, 2))
        self.update()

    def deleteSelectedArea(self):
        if self.rectangleSelectTool.deleteSelectedArea(self.pixmap):
            self.undoStack.append(self.pixmap.copy())
            self.redoStack.clear()
            self.pixmapItem.setPixmap(self.pixmap)
            self.update()

    def copySelectedArea(self):
        self.rectangleSelectTool.copySelectedArea()
        
    # Undoes the last action
    def undo(self):
        if self.undoStack:
            self.redoStack.append(self.pixmap.copy())
            self.pixmap = self.undoStack.pop()
            self.pixmapItem.setPixmap(self.pixmap)

    # Redoes the last undone action
    def redo(self):
        if self.redoStack:
            self.undoStack.append(self.pixmap.copy())
            self.pixmap = self.redoStack.pop()
            self.pixmapItem.setPixmap(self.pixmap)
    
    # Sets the current drawing tool
    def setTool(self, tool):
        self.tools = tool
        if tool == Tools.PENCIL:
            self.currentTool = self.penTool
        elif tool == Tools.ERASER:
            self.currentTool = self.eraserTool
        elif tool == Tools.RECTANGLE_SELECT:
            self.currentTool = self.rectangleSelectTool
        self.setCursor(Qt.CrossCursor if isinstance(self.currentTool, RectangleSelectTool) else Qt.ArrowCursor)
    
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
    
    # Detects and adds borders in the current selected region
    def findBorder(self):
        if not self.rectangleSelectTool.selectedArea:
            print("No area selected. Please select an area first with rectangle tool.")
            return

        selected_rect = self.rectangleSelectTool.selectedArea.toRect()
        image = self.pixmap.toImage()
        selected_image = image.copy(selected_rect)
        
        # Convert QImage to numpy array
        width, height = selected_image.width(), selected_image.height()
        bytes_per_line = selected_image.bytesPerLine()
        ptr = selected_image.constBits()
        arr = np.array(ptr).reshape(height, bytes_per_line // 4, 4)
        
        bgr_image = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # RETR_EXTERNAL only if we want outside edge
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros(bgr_image.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, contours, -1, (255), 3)
        
        # This was an idea to increase the size of the border whenever the pen size is large enough
        # cv2.drawContours(cv_image, contours, -1, (0, 0, 0), thickness = (self.ppSize // 30) + 1)
        
        # last number is for offset (MAMA!) 
        # L youre wrong it was the thickness get better - Ethan
        
        borderOverlay = np.zeros_like(arr)
        borderOverlay[:, :, 3] = mask
        borderOverlay[mask == 255] = [0, 0, 0, 255]

        borderImage = QImage(borderOverlay.data, borderOverlay.shape[1], borderOverlay.shape[0], borderOverlay.strides[0], QImage.Format_RGBA8888)
        borderPixmap = QPixmap.fromImage(borderImage)
        
        # Draw the mask onto the transparent pixmap
        painter = QPainter(self.pixmap)
        painter.drawPixmap(selected_rect.topLeft(), borderPixmap)
        painter.end()
        
        # Update the pixmap item
        self.pixmapItem.setPixmap(self.pixmap)
        self.update()
        self.undoStack.append(self.pixmap.copy())
        self.redoStack.clear()