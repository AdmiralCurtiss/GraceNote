from PyQt4 import QtCore, QtGui
import Globals
import time
import XTextBox

class HistoryWindow(QtGui.QDialog):

    def __init__(self, parent):
        super(HistoryWindow, self).__init__()
        self.parent = parent
        self.setWindowModality(False)        
        self.setWindowTitle("History")

        self.entryList = QtGui.QListView()
        self.entryList.setWrapping(False)
        self.entryModel = QtGui.QStandardItemModel()
        self.entryList.setModel(self.entryModel)
        self.entryTextTextbox = XTextBox.XTextBox(None, self, True)
        self.entryTextTextbox.setReadOnly(True)
        self.entryCommentTextbox = QtGui.QTextEdit()
        self.entryCommentTextbox.setReadOnly(True)
        self.entryList.selectionModel().selectionChanged.connect(self.EntryModelSelectionChanged)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.entryList)
        self.layout.addWidget(self.entryTextTextbox)
        self.layout.addWidget(self.entryCommentTextbox)
        self.setLayout(self.layout)

        geom = Globals.Settings.value('Geometry/HistoryWindow')
        if geom is not None:
            self.restoreGeometry(geom)
        else:
            self.resize(350, 300)
        
    def setHistoryList(self, HistoryList, MaxId):
        # HistoryList input: SELECT ID, english, comment, status, UpdatedBy, UpdatedTimestamp FROM History ORDER BY ID ASC, UpdatedTimestamp DESC
        self.History = []
        for i in range(MaxId+1):
            self.History.append([])
        
        for entry in HistoryList:
            self.History[entry[0]].append( entry )

        return

    def displayHistoryOfEntry(self, entryId):
        self.entryId = entryId
        self.entryModel.clear()
        for entry in self.History[entryId]:
            if entry[5] is not None:
                date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry[5]))
            else:
                date = 'Unknown'
            item = QtGui.QStandardItem('[' + str(entry[3]) + '] ' + date + ' by ' + str(entry[4]))
            item.setEditable(False)
            #item.setData(entry)
            self.entryModel.appendRow(item)
        
        # display newest history entry automatically
        if self.History[entryId]:
            self.entryList.setCurrentIndex(self.entryModel.index(0, 0))
        else:
            self.clearInfo()

        return
    
    def clearInfo(self):
        self.entryTextTextbox.setText(Globals.VariableReplace(''))
        self.entryCommentTextbox.setText(Globals.VariableReplace(''))
        return

    def EntryModelSelectionChanged(self, selectedItems):
        # there HAS to be a better way to get the data behind the item but I can't figure out how!
        index = self.entryList.currentIndex()
        row = index.row()
        data = self.History[self.entryId][row]

        self.entryTextTextbox.setText(Globals.VariableReplace(data[1]))
        self.entryTextTextbox.iconToggle(data[3])
        self.entryCommentTextbox.setText(Globals.VariableReplace(data[2]))

        return

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/HistoryWindow', self.saveGeometry())
