# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import Scripts

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.Toolbar = QtGui.QToolBar()
        
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
        
    def closeEvent(self, event):
        self.scripts2.cleanupAndQuit()
        return


class SplashScreen(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(SplashScreen, self).__init__(parent)
        
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowModality(True)        
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        self.setFixedSize(450, 350)

        self.text = 'Downloading new files...'

        self.complete = False
        self.offline = False
        
        font = self.font()
        font.setPixelSize(10)
        self.setFont(font)


    def paintEvent(self, event):
        QtGui.QWidget.paintEvent(self, event)
        
        painter = QtGui.QPainter(self)

        painter.drawPixmap(0, 0, QtGui.QPixmap('icons/Splash.png'))

        painter.drawText(350, 185, 'v10.0')
        painter.drawText(92, 185, self.text)
        
        if Globals.enchanted == False and self.offline == True:
            painter.setPen(QtGui.QColor(255, 0, 0, 255))
            painter.drawText(100, 198, 'Spell Checker not available')
            painter.drawText(112, 210, 'Offline Mode')
            painter.setPen(QtGui.QColor(0, 0, 0, 255))
        
        elif Globals.enchanted == False:
            painter.setPen(QtGui.QColor(255, 0, 0, 255))
            painter.drawText(100, 198, 'Spell Checker not available')
            painter.setPen(QtGui.QColor(0, 0, 0, 255))
            
        elif self.offline == True:
            painter.setPen(QtGui.QColor(255, 0, 0, 255))
            painter.drawText(100, 198, 'Offline Mode')
            painter.setPen(QtGui.QColor(0, 0, 0, 255))
               
                   
    def mousePressEvent(self, event):
        if self.complete == True:
            self.close()
            self.destroy(True)

    def destroyScreen(self):
        self.close()
        self.destroy(True)

