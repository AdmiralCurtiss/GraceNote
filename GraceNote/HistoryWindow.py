from PyQt4 import QtCore, QtGui
import Globals
import time
import XTextBox

class HistoryWindow(QtGui.QDialog):

    def __init__(self, parent):
        super(HistoryWindow, self).__init__()
        self.setWindowIcon(QtGui.QIcon('icons/image-loading-2.png'))
        self.parent = parent
        self.setWindowModality(False)        
        self.setWindowTitle("History")

        self.entryList = QtGui.QTreeView()
        self.entryModel = QtGui.QStandardItemModel()
        self.entryModelHeaderLabels = ['E', 'S', 'C', 'Status', 'Time', 'Author']
        self.entryModel.setColumnCount(len(self.entryModelHeaderLabels))
        self.entryList.setModel(self.entryModel)
        self.entryTextTextbox = XTextBox.XTextBox(None, self, True)
        self.entryTextTextbox.setReadOnly(True)
        self.entryCommentTextbox = QtGui.QTextEdit()
        self.entryCommentTextbox.setReadOnly(True)
        self.entryList.selectionModel().selectionChanged.connect(self.EntryModelSelectionChanged)

        self.entryList.setRootIsDecorated(False)

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
        self.entryModel.setColumnCount(len(self.entryModelHeaderLabels))
        self.entryModel.setHorizontalHeaderLabels(self.entryModelHeaderLabels)
        self.entryList.setColumnWidth(0, 10)
        self.entryList.setColumnWidth(1, 10)
        self.entryList.setColumnWidth(2, 10)
        self.entryList.setColumnWidth(3, 10)
        self.entryList.setColumnWidth(4, 115)
        self.entryList.setColumnWidth(5, 100)

        entryCount = len( self.History[entryId] )
        for index, entry in enumerate( self.History[entryId] ):
            if entry[5] is not None:
                date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry[5]))
            else:
                date = 'Unknown'
            
            # check what was changed
            englishChanged = False
            commentChanged = False
            statusChanged = False
            if index + 1 != entryCount:
                entryNext = self.History[entryId][index + 1]
                if entry[1] != entryNext[1]:
                    englishChanged = True
                if entry[2] != entryNext[2]:
                    commentChanged = True
                if entry[3] != entryNext[3]:
                    statusChanged = True
                    
            englishChangedItem = QtGui.QStandardItem('E' if englishChanged else '')
            englishChangedItem.setEditable(False)
            commentChangedItem = QtGui.QStandardItem('C' if commentChanged else '')
            commentChangedItem.setEditable(False)
            statusChangedItem = QtGui.QStandardItem('S' if statusChanged else '')
            statusChangedItem.setEditable(False)
            statusItem = QtGui.QStandardItem(str(entry[3]))
            statusItem.setEditable(False)
            timeItem = QtGui.QStandardItem(date)
            timeItem.setEditable(False)
            authorItem = QtGui.QStandardItem(str(entry[4]))
            authorItem.setEditable(False)

            self.entryModel.appendRow([englishChangedItem, statusChangedItem, commentChangedItem, statusItem, timeItem, authorItem])
        
        # display newest history entry automatically
        if self.History[entryId]:
            self.entryList.setCurrentIndex(self.entryModel.index(0, 0))
        else:
            self.clearInfo()

        return
    
    def clearInfo(self):
        self.entryTextTextbox.setText('')
        self.entryCommentTextbox.setText('')
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
