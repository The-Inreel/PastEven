# TEST FILE FOR RISHAB

import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QToolBar, QToolButton, QAction
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QSize, Qt


# Changed the QWidget to QMainWindow so that it isn't treated as ust one widget
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
    
        self.setWindowTitle("PastEven")
        self.setMinimumSize(QSize(2000, 1000))
        
        self.label = QLabel(self)
        toolBar = QToolBar()
        
        # Add buttons to toolbar - undo and redo respectively
        undoButton = QPushButton("Undo")
        undoButton.clicked.connect(self.undo)
        toolBar.addWidget(undoButton)

        redoButton = QPushButton("Redo")
        redoButton.clicked.connect(self.redo)
        toolBar.addWidget(redoButton)
        
        # Set canvas settings
        self.canvas = QtGui.QPixmap(2000, 900)
        self.canvas.fill(color = Qt.GlobalColor.white)
        self.last_x, self.last_y = None, None
        self.label.setPixmap(self.canvas)
        self.pixmap_history = []
        self.pixmap_redohist = []

        # Added the label as a menu widget instead of the whole thing, and added the toolbar
        self.setMenuWidget(self.label)
        self.addToolBar(toolBar)
    
    def mouseMoveEvent(self, e):
        if self.last_x is None: # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return # Ignore the first time.

        painter = QtGui.QPainter(self.label.pixmap())
        pp = painter.pen()
        
        pp.setWidth(4)
        painter.setPen(pp)        
        painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        painter.end()
        self.update()
        
        self.last_x = e.x()
        self.last_y = e.y()
        
    def mousePressEvent(self, event):
        if len(self.pixmap_history) > 30: #20 felt weak so gave them 30, redo is limited by undo
            self.pixmap_history.pop(0)
        
        self.pixmap_history.append(self.label.pixmap().copy())
        self.pixmap_redohist.clear() #clears redo history if you draw (same as paint3d)
        
    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            self.label.pixmap().fill(color = Qt.GlobalColor.white)
            self.update()
        elif event.key() == QtCore.Qt.Key_Z and event.modifiers() & Qt.Modifier.CTRL:
            self.undo()
        elif event.key() == QtCore.Qt.Key_Y and event.modifiers() & Qt.Modifier.CTRL:
            self.redo()

        event.accept()
    
    def undo(self):
        if self.pixmap_history:
            self.pixmap_redohist.append(self.label.pixmap().copy())
            self.label.setPixmap(self.pixmap_history.pop())
            self.update()

    def redo(self):
        if self.pixmap_redohist:
            self.pixmap_history.append(self.label.pixmap().copy())
            self.label.setPixmap(self.pixmap_redohist.pop())
            self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
