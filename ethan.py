import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QToolBar, QSlider
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QSize, Qt
from enum import Enum

class Tools(Enum):
    PENCIL = 1
    ERASER = 2


class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel(self)
    
        # Set canvas settings
        self.canvas = QtGui.QPixmap(1100, 900)
        self.canvas.fill(color = Qt.GlobalColor.white)
        self.last_x, self.last_y = None, None
        self.label.setPixmap(self.canvas)
        self.pixmap_history = []
        self.pixmap_redohist = []
        self.tools = Tools.PENCIL
        self.color = QtGui.QColor(0, 0, 0)
        self.painter = None
        self.pp = None
        self.ppSize = 4
        
                
    def mouseMoveEvent(self, event):
        if self.last_x is None: # First event.
            self.last_x = event.x()
            self.last_y = event.y()
            return # Ignore the first time.

        self.drawStroke(event)
        
        self.last_x = event.x()
        self.last_y = event.y()
    
    def mousePressEvent(self, event):
        if len(self.pixmap_history) > 30: #20 felt weak so gave them 30, redo is limited by undo
            self.pixmap_history.pop(0)
        
        self.pixmap_history.append(self.label.pixmap().copy())
        self.pixmap_redohist.clear() #clears redo history if you draw (same as paint3d)
        
    def mouseReleaseEvent(self, event):
        self.last_x = None
        self.last_y = None
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            self.label.pixmap().fill(color = Qt.GlobalColor.white)
            self.update()
        elif event.key() == QtCore.Qt.Key_Z and event.modifiers() & Qt.Modifier.CTRL:
            self.undo()
        elif event.key() == QtCore.Qt.Key_Y and event.modifiers() & Qt.Modifier.CTRL:
            self.redo()

        event.accept()
        
    def drawStroke(self, event):
        self.painter = QtGui.QPainter(self.label.pixmap())
        self.pp = self.painter.pen()
        
        self.pp.setWidth(self.ppSize)
        # Sets the pen color to the color var if using pencil else it will set to white (erase)
        self.pp.setColor(self.color if self.tools == Tools.PENCIL else QtGui.QColor(255, 255, 255))
        self.painter.setPen(self.pp)     
        self.painter.drawLine(self.last_x, self.last_y, event.x(), event.y())
        self.painter.end()
        self.update()
    
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
            
    def setTool(self, tool):
        self.tools = tool
    
    def setPencilSize(self, value):
        self.ppSize = value
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
    
        self.setWindowTitle("PastEven")
        self.setMinimumSize(QSize(1500, 1000))
        
        self.toolBar = QToolBar()
        self.canvas = Canvas()

        # Add buttons to toolbar - undo and redo respectively
        undoButton = QPushButton("Undo")
        undoButton.clicked.connect(self.canvas.undo)
        self.toolBar.addWidget(undoButton)

        redoButton = QPushButton("Redo")
        redoButton.clicked.connect(self.canvas.redo)
        self.toolBar.addWidget(redoButton)
        
        self.toolBar.addSeparator()
        
        pencilButton = QPushButton()
        pencilButton.clicked.connect(lambda: self.canvas.setTool(Tools.PENCIL))
        pencilButton.setIcon(QtGui.QIcon("resources/pencil.png"))
        pencilButton.setCheckable(True)
        pencilButton.setChecked(True)
        self.toolBar.addWidget(pencilButton)
        
        eraserButton = QPushButton()
        eraserButton.clicked.connect(lambda: self.canvas.setTool(Tools.ERASER))
        eraserButton.setIcon(QtGui.QIcon("resources/eraser.png"))
        eraserButton.setCheckable(True)
        self.toolBar.addWidget(eraserButton)
        
        pencilButton.clicked.connect(lambda: self.toolButtonClicked(eraserButton))
        eraserButton.clicked.connect(lambda: self.toolButtonClicked(pencilButton))
        
        self.sizeSlider = QSlider()
        self.sizeSlider.setMinimum(1)
        self.sizeSlider.setMaximum(100)
        self.sizeSlider.setValue(4)
        self.toolBar.addWidget(self.sizeSlider)
        
        self.sizeLabel = QLabel(str(self.canvas.ppSize))
        self.toolBar.addWidget(self.sizeLabel)
        
        self.sizeSlider.valueChanged.connect(self.canvas.setPencilSize)
        self.sizeSlider.valueChanged.connect(lambda value: self.sizeLabel.setText(str(value)))

        # Added the label as a central widget instead of the whole thing, and added the toolbar
        self.setCentralWidget(self.canvas)
        self.addToolBar(self.toolBar)
        
    # When more tools come change other tools to a list or something idk
    # Rn it just toggles the button use when clicked more of a visual thing
    def toolButtonClicked(self, otherTools):
        sender = self.sender()
        sender.setChecked(True)
        otherTools.setChecked(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())