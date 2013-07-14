# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import time

class LocalChangelog(QtGui.QDialog):

    def __init__(self, file):
    
        super(LocalChangelog, self).__init__()

        self.setWindowModality(False)        
        self.listwidget = QtGui.QListWidget()
        
        Globals.LogCur.execute("select * from Log where File='{0}'".format(file))
        templist = Globals.LogCur.fetchall()
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
