from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import QRectF, QPointF, QCoreApplication
from PySide6.QtGui import QPen, Qt, QPainter

class RectangleSelectTool:
    def __init__(self, canvas):
        self.scene = canvas.scene
        self.canvas = canvas
        self.selectRect = None
        self.selectedArea = None
        self.selectedPixmap = None
        self.isMoving = False
        self.isResizing = False
        self.resizeEdge = None
        self.moveOffset = QPointF()
        self.isSelecting = False
        self.startPoint = None

    def startSelect(self, startPoint):
        self.selectRect = QGraphicsRectItem(QRectF(startPoint, startPoint))
        self.selectRect.setPen(QPen(Qt.black, 1, Qt.DashLine))
        self.scene.addItem(self.selectRect)

    def updateSelect(self, endPoint):
        if self.selectRect:
            rect = QRectF(self.startPoint, endPoint)
            self.selectRect.setRect(rect.normalized())

    def finalizeSelect(self, pixmap, endPoint):
        if self.selectRect:
            rect = QRectF(self.startPoint, endPoint).normalized()
            rect = rect.intersected(pixmap.rect())
            self.selectedArea = rect
            self.selectedPixmap = pixmap.copy(rect.toRect())
            self.scene.removeItem(self.selectRect)
            self.selectRect = None
            self.updateSelectedAreaVisual()

    def clearSelection(self):
        if self.selectRect:
            self.scene.removeItem(self.selectRect)
        self.selectRect = None
        self.selectedArea = None
        self.selectedPixmap = None
        self.isMoving = False
        self.isResizing = False
        self.resizeEdge = None
    
    def handleMousePress(self, startPoint):
        self.startPoint = startPoint
        if self.selectedArea and not self.selectedArea.contains(startPoint):
            self.clearSelection()
        
        if not self.selectedArea:
            self.isSelecting = True
            self.startSelect(startPoint)
        else:
            self.checkResizeStart(startPoint)
            
    def handleMouseMove(self, newPoint):
        if self.isSelecting:
            self.updateSelect(newPoint)
        elif self.isResizing:
            self.resizeSelectedArea(newPoint)
        elif self.isMoving:
            self.moveSelectedArea(newPoint)
    
    def handleMouseRelease(self, endPoint):
        if self.isSelecting:
            self.finalizeSelect(self.canvas.pixmap, endPoint)
        self.isSelecting = False
        self.finishInteraction()

    def resizeSelectedArea(self, newPos):
        if not self.selectedArea or not self.resizeEdge:
            return
        
        left, right, top, bottom = self.resizeEdge
        rect = QRectF(self.selectedArea)
        
        if left:
            rect.setLeft(min(newPos.x(), rect.right() - 10))
        if right:
            rect.setRight(max(newPos.x(), rect.left() + 10))
        if top:
            rect.setTop(min(newPos.y(), rect.bottom() - 10))
        if bottom:
            rect.setBottom(max(newPos.y(), rect.top() + 10))
        
        self.selectedArea = rect
        self.updateSelectedAreaVisual()

    def checkResizeStart(self, pos):
        if not self.selectedArea:
            return
        
        edge_threshold = 10
        rect = self.selectedArea
        
        left_edge = abs(pos.x() - rect.left()) < edge_threshold
        right_edge = abs(pos.x() - rect.right()) < edge_threshold
        top_edge = abs(pos.y() - rect.top()) < edge_threshold
        bottom_edge = abs(pos.y() - rect.bottom()) < edge_threshold
        
        if left_edge or right_edge or top_edge or bottom_edge:
            self.isResizing = True
            self.resizeEdge = (left_edge, right_edge, top_edge, bottom_edge)
            self.updateCursor(self.resizeEdge)
        else:
            self.isMoving = True
            self.moveOffset = pos - rect.topLeft()
            self.canvas.setCursor(Qt.SizeAllCursor)
            
    def handleHover(self, pos):
        if self.selectedArea:
            edge_threshold = 10
            rect = self.selectedArea
            
            left_edge = abs(pos.x() - rect.left()) < edge_threshold
            right_edge = abs(pos.x() - rect.right()) < edge_threshold
            top_edge = abs(pos.y() - rect.top()) < edge_threshold
            bottom_edge = abs(pos.y() - rect.bottom()) < edge_threshold
            
            if left_edge or right_edge or top_edge or bottom_edge:
                self.updateCursor((left_edge, right_edge, top_edge, bottom_edge))
            elif rect.contains(pos):
                self.canvas.setCursor(Qt.SizeAllCursor)
            else:
                self.canvas.setCursor(Qt.CrossCursor)
        else:
            self.canvas.setCursor(Qt.CrossCursor)
            
    def updateCursor(self, edges):
        left, right, top, bottom = edges
        if top and left:
            self.canvas.setCursor(Qt.SizeFDiagCursor)
        elif top and right:
            self.canvas.setCursor(Qt.SizeBDiagCursor)
        elif bottom and left:
            self.canvas.setCursor(Qt.SizeBDiagCursor)
        elif bottom and right:
            self.canvas.setCursor(Qt.SizeFDiagCursor)
        elif left or right:
            self.canvas.setCursor(Qt.SizeHorCursor)
        elif top or bottom:
            self.canvas.setCursor(Qt.SizeVerCursor)

    def updateSelectedAreaVisual(self):
        if self.selectedArea:
            if self.selectRect:
                self.scene.removeItem(self.selectRect)
            self.selectRect = QGraphicsRectItem(self.selectedArea)
            self.selectRect.setPen(QPen(Qt.black, 1, Qt.DashLine))
            self.scene.addItem(self.selectRect)

    def moveSelectedArea(self, newPos):
        if self.selectedArea and self.selectRect:
            if not self.isMoving:
                self.isMoving = True
                self.moveOffset = newPos - self.selectedArea.topLeft()
                self.canvas.setCursor(Qt.SizeAllCursor)
            newTopLeft = newPos - self.moveOffset
            self.selectedArea.moveTopLeft(newTopLeft)
            self.selectRect.setRect(self.selectedArea)

    def deleteSelectedArea(self, pixmap):
        if self.selectedArea:
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.eraseRect(self.selectedArea.toRect())
            painter.end()
            self.scene.removeItem(self.selectRect)
            self.selectRect = None
            self.selectedArea = None
            self.selectedPixmap = None
            return True
        return False

    def finishInteraction(self):
        self.isMoving = False
        self.isResizing = False
        self.resizeEdge = None
        self.canvas.setCursor(Qt.ArrowCursor)

    def copySelectedArea(self):
        if self.selectedPixmap:
            clipboard = QCoreApplication.instance().clipboard()
            clipboard.setPixmap(self.selectedPixmap)