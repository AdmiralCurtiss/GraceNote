#!/usr/bin/env python

# This is only needed for Python v2 but is harmless for Python v3.
import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui
import sys, os

#from Scripts import Scripts
from Enemies import Enemies
from Layout import Layouts
from Item import Items
from Font import Font


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.Toolbar = QtGui.QToolBar()
        
        self.fileMenu = QtGui.QMenu("&File", self)
        self.editMenu = QtGui.QMenu("&Edit", self)
        self.modeMenu = QtGui.QMenu("&Mode", self)
                
        self.modeMenu.addAction('Enemies', self.EnemiesSwitch, QtGui.QKeySequence('Ctrl+1'))
        self.modeMenu.addAction('Layout', self.LayoutSwitch, QtGui.QKeySequence('Ctrl+2'))
        self.modeMenu.addAction('Items', self.ItemsSwitch, QtGui.QKeySequence('Ctrl+3'))
        self.modeMenu.addAction('Font', self.FontSwitch, QtGui.QKeySequence('Ctrl+4'))
        self.modeMenu.addAction('Skills', self.SkillsSwitch, QtGui.QKeySequence('Ctrl+5'))
        self.modeMenu.addAction('Titles', self.TitlesSwitch, QtGui.QKeySequence('Ctrl+6'))
        self.modeMenu.addAction('Artes', self.ArtesSwitch, QtGui.QKeySequence('Ctrl+7'))
        self.modeMenu.addAction('Characters', self.CharSwitch, QtGui.QKeySequence('Ctrl+8'))
        
        self.editMenu.addAction("Undo")
        self.editMenu.addAction("Redo")        
        self.editMenu.addSeparator()
        self.editMenu.addAction("Cut")
        self.editMenu.addAction("Copy")
        self.editMenu.addAction("Paste")
        self.editMenu.addAction("Select All")
                        
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.editMenu)
        self.menuBar().addMenu(self.modeMenu)

        self.addToolBar(self.Toolbar)
        self.setUnifiedTitleAndToolBarOnMac(True)
        
        self.setCentralWidget(Font(self))
        
        self.setWindowTitle("Tales of Graces Tools")


    def EnemiesSwitch(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Warning", "Are you sure you want to change? Any data not saved will be lost.", QtGui.QMessageBox.NoButton, self)
        msgBox.addButton("&Cancel", QtGui.QMessageBox.AcceptRole)
        msgBox.addButton("Con&tinue", QtGui.QMessageBox.RejectRole)
        
        if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
            return
        else:
            self.setCentralWidget(Enemies(self))

    def LayoutSwitch(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Warning", "Are you sure you want to change? Any data not saved will be lost.", QtGui.QMessageBox.NoButton, self)
        msgBox.addButton("&Cancel", QtGui.QMessageBox.AcceptRole)
        msgBox.addButton("Con&tinue", QtGui.QMessageBox.RejectRole)
        
        if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
            return
        else:
            self.setCentralWidget(Layouts(self))
        
    def ItemsSwitch(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Warning", "Are you sure you want to change? Any data not saved will be lost.", QtGui.QMessageBox.NoButton, self)
        msgBox.addButton("&Cancel", QtGui.QMessageBox.AcceptRole)
        msgBox.addButton("Con&tinue", QtGui.QMessageBox.RejectRole)
        
        if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
            return
        else:
            self.setCentralWidget(Items(self))

    def FontSwitch(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Warning", "Are you sure you want to change? Any data not saved will be lost.", QtGui.QMessageBox.NoButton, self)
        msgBox.addButton("&Cancel", QtGui.QMessageBox.AcceptRole)
        msgBox.addButton("Con&tinue", QtGui.QMessageBox.RejectRole)
        
        if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
            return
        else:
            self.setCentralWidget(Font(self))

    def SkillsSwitch(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Warning", "Feature not implemented.", QtGui.QMessageBox.NoButton, self)
        msgBox.exec_()

    def TitlesSwitch(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Warning", "Feature not implemented.", QtGui.QMessageBox.NoButton, self)
        msgBox.exec_()

    def ArtesSwitch(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Warning", "Feature not implemented.", QtGui.QMessageBox.NoButton, self)
        msgBox.exec_()

    def CharSwitch(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Warning", "Feature not implemented.", QtGui.QMessageBox.NoButton, self)
        msgBox.exec_()


if __name__ == '__main__':

    print "Grace Tools v8.0 - Coded by Tempus for the Tales of Graces Translation Project\n    - irc.freenode.net  #Graces"

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())