import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QPen, QPainter
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QWidget

class PixmapCanvas(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the pixmap and graphics scene
        self.pixmap = QPixmap(400, 400)
        self.pixmap.fill(QColor(255, 255, 255))
        self.scene = QGraphicsScene(self)
        self.scene.addPixmap(self.pixmap)

        # Set up the graphics view
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setMouseTracking(True)
        self.setMouseTracking(True)
        self.view.setMouseTracking(True)
        self.view.setGeometry(10, 10, 400, 400)

        # Set up the pen and painter
        self.pen = QPen(QColor(255, 0, 0))
        self.pen.setWidth(3)
        self.painter = QPainter(self.pixmap)
        self.painter.setPen(self.pen)

        # Set up the undo stack
        self.undo_stack = []

        # Set the window properties
        self.setGeometry(300, 300, 420, 420)
        self.setWindowTitle("Pixmap Canvas")
        self.show()

    def mouseMoveEvent(self, e):
        print("gekms")
        if e.buttons() == Qt.LeftButton:
            self.painter.drawLine(e.pos(), e.pos())
            self.view.update()

        # Draw a line as the mouse is moved

    def keyPressEvent(self, event):
        print("HELP")
        # Undo the last line if the "z" key is pressed
        if event.key() == Qt.Key_Z:
            if self.undo_stack:
                self.pixmap = self.undo_stack.pop()
                self.scene.clear()
                self.scene.addPixmap(self.pixmap)
                self.view.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    canvas = PixmapCanvas()
    sys.exit(app.exec_())