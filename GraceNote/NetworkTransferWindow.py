from PyQt4 import QtCore, QtGui
import Globals

class NetworkTransferWindow(QtGui.QDialog):

    allowCloseSignal = QtCore.pyqtSignal()

    def __init__(self):
        super(NetworkTransferWindow, self).__init__()
        self.setWindowIcon(QtGui.QIcon('icons/openfromserver.png'))
        self.setWindowModality(False)        
        self.setWindowTitle("FTP Transfers")

        self.entryList = QtGui.QTreeView()
        self.entryModel = QtGui.QStandardItemModel()
        self.entryModelHeaderLabels = ['File', 'Status']
        self.clearInfo()        
        self.entryList.setModel(self.entryModel)
        self.entryList.setRootIsDecorated(False)

        self.closeButton = QtGui.QPushButton('Close')
        self.closeButton.setEnabled(False)
        self.autoCloseCheckbox = QtGui.QCheckBox('Automatically close when transfers have finished')

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.entryList)
        self.layout.addWidget(self.autoCloseCheckbox)
        self.layout.addWidget(self.closeButton)
        self.setLayout(self.layout)

        self.accepted.connect(self.StoreSettings)

        geom = Globals.Settings.value('Geometry/NetworkTransferWindow')
        if geom is not None:
            self.restoreGeometry(geom)
        else:
            self.resize(480, 320)

        autocheck = Globals.Settings.value('NetworkTransferWindowAutoClose')
        if autocheck == 'True':
            self.autoCloseCheckbox.setChecked(True)

        self.allowCloseSignal.connect(self.AllowClose)
        
    def addListEntry(self, status, name):
        statusItem = QtGui.QStandardItem(status)
        statusItem.setEditable(False)
        nameItem = QtGui.QStandardItem(name)
        nameItem.setEditable(False)

        self.entryModel.appendRow([nameItem, statusItem])
        return self.entryModel.rowCount() - 1

    def modifyListEntryStatus(self, index, status):
        self.entryModel.setData( self.entryModel.index(index, 1), status )
        return
    
    def clearInfo(self):
        self.entryModel.clear()
        self.entryModel.setColumnCount(len(self.entryModelHeaderLabels))
        self.entryModel.setHorizontalHeaderLabels(self.entryModelHeaderLabels)
        self.entryList.setColumnWidth(0, 100)
        self.entryList.header().setStretchLastSection(True)
        return

    def closeEvent(self, event):
        self.StoreSettings()

    def StoreSettings(self):
        Globals.Settings.setValue('Geometry/NetworkTransferWindow', self.saveGeometry())
        Globals.Settings.setValue('NetworkTransferWindowAutoClose', 'True' if self.autoCloseCheckbox.isChecked() else 'False')

    def AllowClose(self):
        self.closeButton.setEnabled(True)
        self.closeButton.clicked.connect(self.accept)
        if self.autoCloseCheckbox.isChecked():
            self.accept()
        return


