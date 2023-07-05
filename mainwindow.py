from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QLabel, QToolBar, QSlider, QSizePolicy, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from PySide6 import QtGui, QtCore

from canvas import Canvas, Tools

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
    
        self.setWindowTitle("PastEven")
        
        # TODO: Make Icon
        self.setWindowIcon(QIcon("resources/pencil.png"))
        self.setMinimumSize(QSize(1500, 1000))

        self.layout = QVBoxLayout()
        
        self.toolBar = QToolBar()
        self.canvas = Canvas()
        self.canvas.clicked.connect(self.moveSlider)
        # Attempted to make a spacer may change tho
        self.spacerT = QWidget()
        self.spacerT.setFixedWidth(100)
        self.spacerT.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setStyleSheet("background: #E0FFFF")

        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.canvas.save)
        saveButton.setIcon(QtGui.QIcon("resources/icons/save.png"))
        saveButton.setShortcut('Ctrl+S')
        self.toolBar.addWidget(saveButton)

        loadButton = QPushButton("Load")
        loadButton.clicked.connect(self.canvas.load)
        loadButton.setIcon(QtGui.QIcon("resources/icons/load.png"))
        loadButton.setShortcut('Ctrl+L')
        self.toolBar.addWidget(loadButton)

        borderButton = QPushButton("Border")
        borderButton.clicked.connect(self.canvas.findBorder)
        borderButton.setIcon(QtGui.QIcon("resources/icons/border.png"))
        borderButton.setShortcut('Ctrl+P')
        self.toolBar.addWidget(borderButton)
        
        self.toolBar.addSeparator()

        # Add buttons to toolbar - undo and redo respectively
        undoButton = QPushButton("Undo")
        undoButton.clicked.connect(self.canvas.undo)
        undoButton.clicked.connect(lambda: self.historySlider.setValue(self.historySlider.value() + 1))
        undoButton.setShortcut('Ctrl+Z')
        self.toolBar.addWidget(undoButton)

        redoButton = QPushButton("Redo")
        redoButton.clicked.connect(self.canvas.redo)
        redoButton.clicked.connect(lambda: self.historySlider.setValue(self.historySlider.value() - 1))
        redoButton.setShortcut('Ctrl+Y')
        self.toolBar.addWidget(redoButton)
        
        self.toolBar.addSeparator()
        
        pencilButton = QPushButton()
        pencilButton.clicked.connect(lambda: self.canvas.setTool(Tools.PENCIL))
        pencilButton.setIcon(QtGui.QIcon("resources/icons/pencil.png"))
        pencilButton.setCheckable(True)
        pencilButton.setChecked(True)
        self.toolBar.addWidget(pencilButton)
        
        eraserButton = QPushButton()
        eraserButton.clicked.connect(lambda: self.canvas.setTool(Tools.ERASER))
        eraserButton.setIcon(QtGui.QIcon("resources/icons/eraser.png"))
        eraserButton.setCheckable(True)
        self.toolBar.addWidget(eraserButton)
        
        pencilButton.clicked.connect(lambda: self.toolButtonClicked(eraserButton))
        eraserButton.clicked.connect(lambda: self.toolButtonClicked(pencilButton))
        
        self.sizeSlider = QSlider()
        self.sizeSlider.setMinimum(1)
        self.sizeSlider.setMaximum(100)
        self.sizeSlider.setValue(4)
        self.toolBar.addWidget(self.sizeSlider)

        self.historySlider = QSlider()
        self.historySlider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.historySlider.setInvertedAppearance(True)
        self.historySlider.setMinimum(0)
        self.historySlider.setMaximum(1)
        self.historySlider.setMaximumWidth(400)
        self.historySlider.setEnabled(False)
        self.historySlider.setValue(0)        
        
        self.sizeLabel = QLabel(str(self.canvas.ppSize))
        self.toolBar.addWidget(self.sizeLabel)
        self.toolBar.addSeparator()

        # added spacer to use text - improve later when i know how to like actually change the spacing
        # p.s. we should probably use some kind of organizer like a vbox or whatever its called
        self.toolBar.addWidget(self.spacerT)
        self.spacer = QLabel("History:        ")
        self.toolBar.addWidget(self.spacer)

        # gave toolbar bit of color so we can see
        self.toolBar.setStyleSheet("QToolBar { background : #E0FFFF }")
        self.toolBar.addWidget(self.historySlider)
        self.toolBar.toggleViewAction().setEnabled(False)
        # prevents hiding toolbar cuz if you remove it, you can't add it back
        
        self.sizeSlider.valueChanged.connect(self.canvas.setPencilSize)
        self.sizeSlider.valueChanged.connect(lambda value: self.sizeLabel.setText(str(value)))
        self.historySlider.sliderMoved.connect(self.actionTriggered)

        # Added the label as a central widget instead of the whole thing, and added the toolbar
        # self.setCentralWidget(self.layout)
        self.addToolBar(self.toolBar)
        self.layout.addWidget(self.canvas)
        self.layout.setAlignment(self.canvas, Qt.AlignmentFlag.AlignHCenter)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.layout)
        
    # When more tools come change other tools to a list or something idk
    # Rn it just toggles the button use when clicked more of a visual thing
    def toolButtonClicked(self, otherTools):
        sender = self.sender()
        sender.setChecked(True)
        otherTools.setChecked(False)
    
    def mousePressEvent(self, event):
        self.historySlider.setMaximum(len(self.canvas.pixmap_history) - 1)

    # had to do a bunch of research on how this signal processing works but
    # essentially if you move the slider one way it undoes, other way redoes
    def actionTriggered(self, val):
        if val > self.historySlider.value():
            self.canvas.undo()
        elif val < self.historySlider.value():
            self.canvas.redo()
            
    def moveSlider(self):
        if not self.historySlider.isEnabled():
            self.historySlider.setEnabled(True)
        if self.historySlider.value() == self.historySlider.maximum():
            self.historySlider.setMaximum(len(self.canvas.pixmap_history))
            self.historySlider.setValue(len(self.canvas.pixmap_history))
        else:
            self.historySlider.setMaximum(len(self.canvas.pixmap_history))
    
        
        
            