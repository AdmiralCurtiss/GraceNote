# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, Qt
import Globals
import re
import os

class ImageViewerWindow(QtGui.QDialog):

    def __init__(self, parent, image):
        super(ImageViewerWindow, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon('icons/image-x-generic.png'))
        self.parent = parent
        self.medium = image
        self.setWindowModality(False)        
        self.setWindowTitle(image.name)
        
        # i am afraid to touch this part now that the scrollbar works
        mainWidget = QtGui.QWidget(self);
        self.vLayout = QtGui.QVBoxLayout(mainWidget);
        scrollArea = QtGui.QScrollArea(mainWidget);
        scrollArea.setWidgetResizable(False);
        self.scrollAreaVLayout = QtGui.QVBoxLayout();
        scrollAreaWidgetContents = QtGui.QWidget();
        scrollAreaWidgetContents.setLayout(self.scrollAreaVLayout);
        self.scrollAreaVLayout.setSizeConstraint(Qt.QLayout.SetFixedSize);
        scrollArea.setWidget(scrollAreaWidgetContents);
        self.vLayout.addWidget(scrollArea);
        self.setLayout(self.vLayout)

        # keep a list of labels for images, so we're not deleting and recreating them all the time
        self.labels = []

        geom = Globals.Settings.value('Geometry/ImageViewerWindow_' + self.medium.name)
        if geom is not None:
            self.restoreGeometry(geom)
        else:
            self.resize(300, 200)

    def refreshInfo(self, text):
        search = '<' + self.medium.var + ': (.*?)>'
        parameters = re.findall(search, text, re.DOTALL)
        self.clearInfo()
        
        for i, param in enumerate(parameters):
            splitparams = param.split(' ')
            
            # create a new label if our list doesn't have enough
            if i >= len(self.labels):
                self.labels.append(QtGui.QLabel())
                self.scrollAreaVLayout.addWidget(self.labels[i])

            pixmap = QtGui.QPixmap( self.medium.path.format(*splitparams) )
            self.labels[i].setPixmap(pixmap)
    
    def clearInfo(self):
        for l in self.labels:
            l.clear()

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/ImageViewerWindow_' + self.medium.name, self.saveGeometry())
