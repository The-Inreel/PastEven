from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QLabel, QToolBar, QSlider, QSizePolicy, QVBoxLayout, QButtonGroup, QLineEdit, QScrollArea, QColorDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from PySide6 import QtGui

from canvas import Canvas, Tools

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PastEven")
        # TODO: Make Icon
        self.setWindowIcon(QIcon("resources/pencil.png"))
        self.setMinimumSize(QSize(1500, 1000))
        # self.setStyleSheet("background: #050B0D")
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        
        layout = QVBoxLayout(centralWidget)
        
        self.canvas = Canvas()
        self.canvas.clicked.connect(self.updateHistorySlider)
        
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self.canvas)
        
        layout.addWidget(scrollArea)
        
        self.createToolbar()
    
    # Creates the toolbar with all the tools and stuff
    def createToolbar(self):
        toolbar = QToolBar()
        toolbar.setStyleSheet("QToolBar { background : #5b5b5b }")
        toolbar.toggleViewAction().setEnabled(False)
        self.addToolBar(toolbar)

        self.createFileActions(toolbar)
        toolbar.addSeparator()
        self.createHistoryActions(toolbar)
        toolbar.addSeparator()
        self.createTools(toolbar)
        self.createSizeControls(toolbar)
        self.createColorPicker(toolbar)
        toolbar.addSeparator()
        self.createHistorySlider(toolbar)
    
    # Adds the file action buttons (Save, Load, Border) to the toolbar
    def createFileActions(self, toolbar):
        saveButton = self.createButton("Save", self.canvas.save, 'Ctrl+S', "resources/icons/save.png")
        loadButton = self.createButton("Load", self.canvas.load, 'Ctrl+L', "resources/icons/load.png")
        borderButton = self.createButton("Border", self.canvas.findBorder, 'Ctrl+P', "resources/icons/border.png")
        
        toolbar.addWidget(saveButton)
        toolbar.addWidget(loadButton)
        toolbar.addWidget(borderButton)
    
    # Adds undo and redo buttons to the toolbar as well as keybinds
    def createHistoryActions(self, toolbar):
        undoButton = self.createButton("Undo", self.undoAction, 'Ctrl+Z')
        redoButton = self.createButton("Redo", self.redoAction, 'Ctrl+Y')
        
        toolbar.addWidget(undoButton)
        toolbar.addWidget(redoButton)
    
    # Adds tool selection buttons (Pencil, Eraser) to the toolbar
    def createTools(self, toolbar):
        self.toolButtons = QButtonGroup()
        
        penButton = self.createToolButton("Pencil", Tools.PENCIL, "resources/icons/pencil.png", True)
        eraserButton = self.createToolButton("Eraser", Tools.ERASER, "resources/icons/eraser.png")
        
        toolbar.addWidget(penButton)
        toolbar.addWidget(eraserButton)
    
    # Adds size control slider and number box to the toolbar
    def createSizeControls(self, toolbar):
        self.sizeSlider = QSlider(Qt.Horizontal)
        self.sizeSlider.setRange(1, 100)
        self.sizeSlider.setValue(4)
        self.sizeSlider.valueChanged.connect(self.updatePenSize)
        
        self.sizeBox = QLineEdit()
        self.sizeBox.setText(str(self.canvas.ppSize))
        self.sizeBox.textChanged.connect(self.updatePenSizeBox)
        self.sizeBox.setMaximumWidth(40)
        
        toolbar.addWidget(self.sizeSlider)
        toolbar.addWidget(self.sizeBox)
    
    # Adds the color picker button to the toolbar
    def createColorPicker(self, toolbar):
        colorButton = self.createButton("Color", self.openColorPicker)
        toolbar.addWidget(colorButton)
    
    # Adds the history slider to the toolbar
    def createHistorySlider(self, toolbar):
        spacer = QWidget()
        spacer.setFixedWidth(10)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        toolbar.addWidget(QLabel("History:     "))
        
        self.historySlider = QSlider(Qt.Horizontal)
        self.historySlider.setInvertedAppearance(True)
        self.historySlider.setRange(0, 1)
        self.historySlider.setMaximumWidth(400)
        self.historySlider.setEnabled(False)
        self.historySlider.sliderMoved.connect(self.handleHistoryDelta)
        
        toolbar.addWidget(self.historySlider)
    
    # Generic button template for the toolbar
    def createButton(self, text, slot, shortcut=None, icon=None):
        button = QPushButton(text)
        button.clicked.connect(slot)
        if shortcut:
            button.setShortcut(shortcut)
        if icon:
            button.setIcon(QtGui.QIcon(icon))
        return button
    
    # Creates a tool button (used for pens rn) for the toolbar 
    def createToolButton(self, name, tool, icon, checked=False):
        button = QPushButton()
        button.setCheckable(True)
        button.setChecked(checked)
        button.clicked.connect(lambda: self.setTool(tool))
        button.setIcon(QtGui.QIcon(icon))
        self.toolButtons.addButton(button)
        return button
    
    # Sets the current drawing tool (Pencil or Eraser)
    def setTool(self, tool):
        self.canvas.setTool(tool)
        for button in self.toolButtons.buttons():
            button.setChecked(button == self.sender())
    
    # Updates the pen size when the slider value changes
    def updatePenSize(self, value):
        self.canvas.setPencilSize(value)
        self.sizeBox.setText(str(value))
    
    # Updates the pencil size when the size box value changes
    def updatePenSizeBox(self, text):
        try:
            value = int(text)
            if 1 <= value <= 100:
                self.sizeSlider.setValue(value)
                self.canvas.setPencilSize(value)
            elif value > 100:
                self.sizeBox.setText('100')
                self.sizeSlider.setValue(100)
                self.canvas.setPencilSize(100)
        except ValueError:
            print("Invalid size value")

    # Updates the history slider to reflect the undo stack size
    def updateHistorySlider(self):
        max = len(self.canvas.undoStack)
        self.historySlider.setMaximum(max)
        self.historySlider.setValue(max)
        self.historySlider.setEnabled(max > 0)
    
    # Handles changes in the history slider position
    def handleHistoryDelta(self, value):
        current = self.historySlider.maximum() - self.historySlider.value()
        target = self.historySlider.maximum() - value
        diff = target - current
        
        if diff > 0:
            for _ in range(diff):
                self.canvas.undo()
        elif diff < 0:
            for _ in range(-diff):
                self.canvas.redo()
    
    # Performs an undo action and updates the history slider
    def undoAction(self):
        self.canvas.undo()
        self.updateHistorySlider()

    # Performs a redo action and updates the history slider
    def redoAction(self):
        self.canvas.redo()
        self.updateHistorySlider()
        
    # Simply sets the color of the pen
    def openColorPicker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.setColor(color)

    # Updates the history slider when the mouse is pressed
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.updateHistorySlider()