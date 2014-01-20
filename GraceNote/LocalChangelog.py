# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import time

class LocalChangelog(QtGui.QDialog):

    def __init__(self, file):
        super(LocalChangelog, self).__init__()
        self.setWindowIcon(QtGui.QIcon('icons/changelog.png'))

        self.setWindowModality(False)        
        self.listwidget = QtGui.QListWidget()
        
        ChangeLogConnection, ChangeLogCursor = Globals.GetNewChangeLogConnectionAndCursor()
        ChangeLogCursor.execute("SELECT * FROM Log WHERE File='{0}'".format(file))
        templist = ChangeLogCursor.fetchall()
        ChangeLogConnection.close()
        for entry in templist:
            self.listwidget.addItem('{0} on {1}'.format(entry[2], time.strftime('%a, %B %d at %H:%M %p', time.localtime(entry[3]))))

        
        self.setWindowTitle('Changelog: {0}'.format(file))
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('File Modified By:'))
        layout.addWidget(self.listwidget)
        self.setLayout(layout)

        geom = Globals.Settings.value('Geometry/LocalChangelog')
        if geom is not None:
            self.restoreGeometry(geom)

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/LocalChangelog', self.saveGeometry())
