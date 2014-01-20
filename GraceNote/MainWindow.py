# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import Scripts

class MainWindow(QtGui.QMainWindow):
    displayStatusMessageSignal = QtCore.pyqtSignal(str)

    def __init__(self):
        super(MainWindow, self).__init__()

        Globals.MainWindow = self

        self.Toolbar = QtGui.QToolBar()
        self.Toolbar.setObjectName('MainToolBar')
        
        self.editMenu = QtGui.QMenu("&Edit", self)
                
        self.editMenu.addAction("Undo")
        self.editMenu.addAction("Redo")        
        self.editMenu.addSeparator()
        self.editMenu.addAction("Cut")
        self.editMenu.addAction("Copy")
        self.editMenu.addAction("Paste")
        self.editMenu.addAction("Select All")
                        
        self.menuBar().addMenu(self.editMenu)

        self.addToolBar(self.Toolbar)
        self.setUnifiedTitleAndToolBarOnMac(True)

        self.scripts2 = Scripts.Scripts2(self)
        self.setCentralWidget(self.scripts2)

        statusBar = QtGui.QStatusBar()
        self.setStatusBar(statusBar)
        self.displayStatusMessageSignal.connect(statusBar.showMessage)
        #self.displayStatusMessage("hi!")

        self.restoreStateAndGeometry()

    def displayStatusMessage(self, message):
        self.displayStatusMessageSignal.emit(message)

    def restoreStateAndGeometry(self):
        geom = Globals.Settings.value("MainWindowGeometry")
        if geom is not None:
            self.restoreGeometry(geom)
        state = Globals.Settings.value("MainWindowWindowState")
        if state is not None:
            self.restoreState(state)

    def closeEvent(self, event):
        Globals.Settings.setValue("MainWindowGeometry", self.saveGeometry())
        Globals.Settings.setValue("MainWindowWindowState", self.saveState())

        if not self.scripts2.cleanupAndQuit():
            event.ignore()

        return


class SplashScreen(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(SplashScreen, self).__init__(parent)
        
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowModality(True)        
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        self.setFixedSize(450, 350)

        self.complete = False
        self.offline = False
        
        font = self.font()
        font.setPixelSize(10)
        self.setFont(font)


    def paintEvent(self, event):
        QtGui.QWidget.paintEvent(self, event)
        
        painter = QtGui.QPainter(self)

        painter.drawPixmap(0, 0, QtGui.QPixmap('icons/Splash.png'))

        painter.drawText( 92, 185,    'Original by Tempus')
        painter.drawText(100, 185+12, 'for the Tales of Graces Translation Project')
        painter.drawText(112, 185+24, 'Modified and expanded for other games')
        painter.drawText(120, 185+36, 'by Admiral H. Curtiss')
        
        painter.setPen(QtGui.QColor(255, 0, 0, 255))
        if not Globals.enchanted:
            painter.drawText(136, 185+56, 'Spell Checker not available')
        if self.offline:
            painter.drawText(166, 185+68, 'Offline Mode')
        painter.setPen(QtGui.QColor(0, 0, 0, 255))
               
                   
    def mousePressEvent(self, event):
        if self.complete:
            self.close()
            self.destroy(True)

    def destroyScreen(self):
        self.close()
        self.destroy(True)

