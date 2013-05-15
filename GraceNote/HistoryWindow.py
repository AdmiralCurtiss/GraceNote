from PyQt4 import QtCore, QtGui
#import Globals

class HistoryWindow(QtGui.QDialog):

    def __init__(self, parent):
        super(HistoryWindow, self).__init__()
        self.parent = parent
        self.setWindowModality(False)        
        self.setWindowTitle("History")

        self.entryList = QtGui.QListView()
        self.entryList.setWrapping(False)
        self.entry = QtGui.QTextEdit()

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.entryList)
        self.layout.addWidget(self.entry)
        self.setLayout(self.layout)
        
    def refreshInfo(self, text):
        return
    
    def clearInfo(self):
        return

