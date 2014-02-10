from PyQt4 import QtCore, QtGui
import Globals
import os
import Config

class ProjectSelectWindow(QtGui.QDialog):
    def __init__(self):
        super(ProjectSelectWindow, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.configFileSelected = False

        self.configfile = 'Projects/config.xml'
        self.setWindowModality(False)
        
        checkLayout = QtGui.QVBoxLayout()
        self.ProjectList = QtGui.QListWidget()
        self.ProjectList.itemDoubleClicked.connect(self.OkAndClose)
        checkLayout.addWidget(self.ProjectList)
    
        buttonLayout = QtGui.QHBoxLayout()
        self.applyButton = QtGui.QPushButton('OK')
        self.cancelButton = QtGui.QPushButton('Cancel')
        buttonLayout.addWidget(self.applyButton)
        buttonLayout.addWidget(self.cancelButton)

        self.LoadProjectList()
                
        self.applyButton.released.connect(self.OkAndClose)
        self.cancelButton.released.connect(self.CancelAndClose)
                
        self.setWindowTitle('Select Project')
        layout = QtGui.QVBoxLayout()
        layout.addLayout(checkLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        #self.setMinimumSize(800, 600)

        # auto-load if only one project is available
        if self.ProjectList.count() == 1:
            self.ProjectList.setCurrentRow(0)
            self.OkAndClose()

    def LoadProjectList(self):
        try:
            files = os.listdir('Projects')
            for filename in files:
                try:
                    cfg = Config.Configuration('Projects/' + filename)
                    self.ProjectList.addItem(filename)
                    #self.ProjectList.addItem(cfg.ID + ' (' + filename + ')')
                except:
                    pass
        except:
            pass
        return

    def OkAndClose(self):
        item = self.ProjectList.currentItem()
        self.configfile = u'Projects/' + unicode(item.text())
        self.configFileSelected = True

        self.done(0)
        return

    def CancelAndClose(self):
        self.done(-1)
        return
