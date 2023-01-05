import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QSize, Qt


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
    
        self.memory = []
        self.setWindowTitle("PastEven")
        self.setMinimumSize(QSize(600, 600))
        
        self.label = QLabel(self)
        self.canvas = QtGui.QPixmap(500, 500)
        self.canvas.fill(color = Qt.GlobalColor.white)
        self.last_x, self.last_y = None, None
        self.label.setPixmap(self.canvas)
    
        
    def add_palette_buttons(self, layout):
        for c in COLORS:
            b = QPaletteButton(c)
            b.pressed.connect(lambda c=c: self.canvas.set_pen_color(c))
            layout.addWidget(b)
    
    def mouseMoveEvent(self, e):
        if self.last_x is None: # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return # Ignore the first time.

        painter = QtGui.QPainter(self.label.pixmap())
        pp = painter.pen()
        
        pp.setWidth(4)
        painter.setPen(pp)

        self.memory.append([self.last_x, self.last_y, e.x(), e.y()])
        
        painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        painter.end()
        self.update()
        
        self.last_x = e.x()
        self.last_y = e.y()
        
    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            self.label.pixmap().fill(color = Qt.GlobalColor.white)
            self.update()
        elif event.key() == QtCore.Qt.Key_Z:

            painter = QtGui.QPainter(self.label.pixmap())
            pp = painter.pen()

            pp.setColor(Qt.GlobalColor.white)
            pp.setWidth(4)
            painter.setPen(pp)

            if len(self.memory) != 0:
                arr = self.memory.pop(len(self.memory) - 1)
                painter.drawLine(arr[0], arr[1], arr[2], arr[3])
            
            painter.end()
            self.update()

            
        event.accept()


COLORS = [
# 17 undertones https://lospec.com/palette-list/17undertones
'#000000', '#141923', '#414168', '#3a7fa7', '#35e3e3', '#8fd970', '#5ebb49',
'#458352', '#dcd37b', '#fffee5', '#ffd035', '#cc9245', '#a15c3e', '#a42f3b',
'#f45b7a', '#c24998', '#81588d', '#bcb0c2', '#ffffff',
]

class QPaletteButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(24,24))
        self.color = color


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
