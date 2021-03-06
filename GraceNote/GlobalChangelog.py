﻿# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import time

class GlobalChangelog(QtGui.QDialog):

    def __init__(self, parent):
        super(GlobalChangelog, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon('icons/global.png'))

        self.parent = parent
        
        self.setWindowModality(False)        
        self.treewidget = QtGui.QTreeWidget()
        self.treewidget.setRootIsDecorated(False)
        
        self.treewidget.setColumnCount(3)
        self.treewidget.setHeaderLabels(['Date', 'Name', 'File'])
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 200)
        self.treewidget.setColumnWidth(1, 100)
        self.treewidget.setColumnWidth(2, 80)
        
        self.treewidget.setMinimumSize(450, 600)
        
        ChangeLogConnection, ChangeLogCursor = Globals.GetNewChangeLogConnectionAndCursor()
        ChangeLogCursor.execute("SELECT * FROM Log ORDER BY Timestamp DESC")
        templist = ChangeLogCursor.fetchall()
        ChangeLogConnection.close()

        #templist.pop(0)
        for entry in templist:
            for filename in entry[1].split(','):
                self.treewidget.addTopLevelItem(QtGui.QTreeWidgetItem(['{0}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry[3]))), '{0}'.format(entry[2]), '{0}'.format(filename)]))
        
        self.treewidget.itemDoubleClicked.connect(self.JumpToFile)

        self.setWindowTitle('Global Changelog')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Recent Changes:'))
        layout.addWidget(self.treewidget)
        self.setLayout(layout)

        geom = Globals.Settings.value('Geometry/GlobalChangelog')
        if geom is not None:
            self.restoreGeometry(geom)

    def JumpToFile(self, item, column):
        databaseName = item.data(2, 0)
        self.parent.JumpToEntry(databaseName, 1)

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/GlobalChangelog', self.saveGeometry())
