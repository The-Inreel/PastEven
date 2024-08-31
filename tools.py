from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import QRectF, QPointF, QCoreApplication
from PySide6.QtGui import QPen, Qt, QPainter, QBrush

class Tool:
    def __init__(self, canvas):
        self.canvas = canvas
        self.scene = canvas.scene

    def handleMousePress(self, event):
        pass

    def handleMouseMove(self, event):
        pass

    def handleMouseRelease(self, event):
        pass

class PenTool(Tool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.lastPoint = None
        self.drawing = False

    def handleMousePress(self, event):
        if event.button() == Qt.LeftButton:
            self.lastPoint = self.canvas.mapToScene(event.position().toPoint())
            self.drawing = True
            self.canvas.undoStack.append(self.canvas.pixmap.copy())
            self.canvas.redoStack.clear()
            self.drawSinglePoint(self.lastPoint)

    def handleMouseMove(self, event):
        if self.drawing:
            newPoint = self.canvas.mapToScene(event.position().toPoint())
            self.drawLineTo(newPoint)
            self.lastPoint = newPoint

    def handleMouseRelease(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def drawLineTo(self, endPoint):
        painter = QPainter(self.canvas.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.canvas.color, self.canvas.ppSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.lastPoint, endPoint)
        painter.end()
        self.canvas.pixmapItem.setPixmap(self.canvas.pixmap)

    def drawSinglePoint(self, point):
        painter = QPainter(self.canvas.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self.canvas.color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(self.canvas.color))
        painter.drawEllipse(point, self.canvas.ppSize / 2, self.canvas.ppSize / 2)
        painter.end()
        self.canvas.pixmapItem.setPixmap(self.canvas.pixmap)
        
class EraserTool(Tool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.lastPoint = None
        self.erasing = False

    def handleMousePress(self, event):
        if event.button() == Qt.LeftButton:
            self.lastPoint = self.canvas.mapToScene(event.position().toPoint())
            self.erasing = True
            self.canvas.undoStack.append(self.canvas.pixmap.copy())
            self.canvas.redoStack.clear()
            self.eraseSinglePoint(self.lastPoint)

    def handleMouseMove(self, event):
        if self.erasing:
            newPoint = self.canvas.mapToScene(event.position().toPoint())
            self.eraseLineTo(newPoint)
            self.lastPoint = newPoint

    def handleMouseRelease(self, event):
        if event.button() == Qt.LeftButton:
            self.erasing = False

    def eraseLineTo(self, endPoint):
        painter = QPainter(self.canvas.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(Qt.transparent, self.canvas.ppSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.setPen(pen)
        painter.drawLine(self.lastPoint, endPoint)
        painter.end()
        self.canvas.pixmapItem.setPixmap(self.canvas.pixmap)

    def eraseSinglePoint(self, point):
        painter = QPainter(self.canvas.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.setPen(QPen(Qt.transparent, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(Qt.transparent))
        painter.drawEllipse(point, self.canvas.ppSize / 2, self.canvas.ppSize / 2)
        painter.end()
        self.canvas.pixmapItem.setPixmap(self.canvas.pixmap)

class RectangleSelectTool(Tool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.selectRect = None
        self.selectedArea = None
        self.selectedPixmap = None
        self.isMoving = False
        self.isResizing = False
        self.resizeEdge = None
        self.moveOffset = QPointF()
        self.isSelecting = False
        self.startPoint = None
        self.edge_threshold = 10

    def startSelect(self, startPoint):
        self.startPoint = startPoint
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
    
    def handleMousePress(self, event):
        startPoint = self.canvas.mapToScene(event.position().toPoint())
        if event.button() == Qt.LeftButton:
            if self.selectedArea and not self.selectedArea.contains(startPoint):
                self.clearSelection()
            
            if not self.selectedArea:
                self.isSelecting = True
                self.startSelect(startPoint)
            else:
                self.checkResizeStart(startPoint)
            
    def handleMouseMove(self, event):
        newPoint = self.canvas.mapToScene(event.position().toPoint())
        if self.isSelecting:
            self.updateSelect(newPoint)
        elif self.isResizing:
            self.resizeSelectedArea(newPoint)
        elif self.isMoving:
            self.moveSelectedArea(newPoint)
        else:
            self.handleHover(newPoint)
    
    def handleMouseRelease(self, event):
        endPoint = self.canvas.mapToScene(event.position().toPoint())
        if event.button() == Qt.LeftButton:
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

    def isNearEdge(self, pos, rect):
        left_edge = abs(pos.x() - rect.left()) <= self.edge_threshold
        right_edge = abs(pos.x() - rect.right()) <= self.edge_threshold
        top_edge = abs(pos.y() - rect.top()) <= self.edge_threshold
        bottom_edge = abs(pos.y() - rect.bottom()) <= self.edge_threshold
        return left_edge, right_edge, top_edge, bottom_edge
    
    def checkResizeStart(self, pos):
        if not self.selectedArea:
            return
        
        rect = self.selectedArea
        expanded_rect = rect.adjusted(-self.edge_threshold, -self.edge_threshold, 
                                      self.edge_threshold, self.edge_threshold)
        
        if expanded_rect.contains(pos):
            edges = self.isNearEdge(pos, rect)
            if any(edges):
                self.isResizing = True
                self.resizeEdge = edges
                self.updateCursor(self.resizeEdge)
            else:
                self.isMoving = True
                self.moveOffset = pos - rect.topLeft()
                self.canvas.setCursor(Qt.SizeAllCursor)
        
    def handleHover(self, pos):
        if self.selectedArea:
            rect = self.selectedArea
            expanded_rect = rect.adjusted(-self.edge_threshold, -self.edge_threshold, 
                                          self.edge_threshold, self.edge_threshold)
            
            if expanded_rect.contains(pos):
                edges = self.isNearEdge(pos, rect)
                if any(edges):
                    self.updateCursor(edges)
                else:
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