from PyQt4 import Qt, QtCore, QtGui
import Globals
import time
import XTextBox

class HistoryDataHelper():
    englishTextBox = None
    commentTextBox = None
    statusIconLabel = None

class HistoryWindow(QtGui.QDialog):

    def __init__(self, parent):
        super(HistoryWindow, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon('icons/image-loading-2.png'))
        self.parent = parent
        self.setWindowModality(False)        
        self.setWindowTitle("History")

        self.entryList = QtGui.QTreeView()
        self.entryModel = QtGui.QStandardItemModel()
        self.entryModelHeaderLabels = ['E', 'S', 'C', 'Status', 'Time', 'Author']
        self.entryModel.setColumnCount(len(self.entryModelHeaderLabels))
        self.entryList.setModel(self.entryModel)
        self.entryTextTextbox = XTextBox.XTextBox(self, 'ENG', True)
        self.entryTextTextbox.setReadOnly(True)
        self.entryCommentTextbox = QtGui.QTextEdit()
        self.entryCommentTextbox.setReadOnly(True)
        self.entryList.selectionModel().selectionChanged.connect(self.EntryModelSelectionChanged)

        self.viewAllButton = QtGui.QPushButton( 'View All' )
        self.viewAllButton.released.connect( self.ShowFullHistory )
        self.viewDetailButton = QtGui.QPushButton( 'View Detail' )
        self.viewDetailButton.released.connect( self.ShowDetailedHistory )
        self.detailLayout = QtGui.QVBoxLayout()
        self.detailLayout.addWidget(self.viewDetailButton)

        self.entryList.setRootIsDecorated(False)

        self.listLayout = QtGui.QVBoxLayout()
        self.listLayout.addWidget(self.viewAllButton)
        self.listLayout.addWidget(self.entryList)
        self.listLayout.addWidget(self.entryTextTextbox)
        self.listLayout.addWidget(self.entryCommentTextbox)

        self.listAreaWidget = QtGui.QWidget()
        self.listAreaWidget.setLayout(self.listLayout)
        self.detailAreaWidget = QtGui.QWidget()
        self.detailAreaWidget.setLayout(self.detailLayout)

        self.stackedWidget = QtGui.QStackedWidget()
        self.stackedWidget.addWidget(self.listAreaWidget)
        self.stackedWidget.addWidget(self.detailAreaWidget)

        self.expandedAreaTextboxsWidget = QtGui.QWidget()
        # my eternal nemesis: scroll bars
        mainWidget = QtGui.QWidget(self);
        self.vLayout = QtGui.QVBoxLayout(mainWidget);
        scrollArea = QtGui.QScrollArea(mainWidget);
        scrollArea.setWidgetResizable(False);
        self.scrollAreaGridLayout = QtGui.QGridLayout();
        scrollAreaWidgetContents = QtGui.QWidget();
        scrollAreaWidgetContents.setLayout(self.scrollAreaGridLayout);
        self.scrollAreaGridLayout.setSizeConstraint(Qt.QLayout.SetFixedSize);
        scrollArea.setWidget(scrollAreaWidgetContents);
        self.vLayout.addWidget(scrollArea);
        self.expandedAreaTextboxsWidget.setLayout(self.vLayout)
        self.detailLayout.addWidget(self.expandedAreaTextboxsWidget) 
        # scroll bars end

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.stackedWidget)
        self.setLayout(self.layout)

        self.detailHistoryLabels = []

        self.StatusIcons = {}
        self.StatusIcons[-1] = QtGui.QPixmap('icons/status/debugOn.png').scaled(13, 13, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation);
        self.StatusIcons[0] = QtGui.QPixmap('icons/status/1.png').scaled(13, 13, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation);
        for i in range( 1, Globals.configData.TranslationStagesCountMaximum + 1 ):
            self.StatusIcons[i] = QtGui.QPixmap('icons/status/{0}g.png'.format(i)).scaled(13, 13, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation);

        self.scrollAreaGridLayout.addWidget( QtGui.QLabel("User"), 0, 1 )
        self.scrollAreaGridLayout.addWidget( QtGui.QLabel("English"), 0, 2 )
        self.scrollAreaGridLayout.addWidget( QtGui.QLabel("Comment"), 0, 3 )

        self.ShowFullHistory()

        geom = Globals.Settings.value('Geometry/HistoryWindow')
        if geom is not None:
            self.restoreGeometry(geom)
        else:
            self.resize(350, 300)
        
    def setHistoryList(self, HistoryList, MaxId, EntryList):
        # HistoryList input: SELECT ID, english, comment, status, UpdatedBy, UpdatedTimestamp FROM History ORDER BY ID ASC, UpdatedTimestamp DESC
        # EntryList input: SELECT ID, StringID, english, comment, updated, status, IdentifyString, UpdatedBy, UpdatedTimestamp FROM Text ORDER BY ID ASC
        self.History = []
        for i in range(MaxId+1):
            self.History.append([])
        
        for entry in EntryList:
            newEntry = []
            newEntry.append( entry[0] )
            newEntry.append( entry[2] )
            newEntry.append( entry[3] )
            newEntry.append( entry[5] )
            newEntry.append( entry[7] )
            newEntry.append( entry[8] )
            self.History[entry[0]].append( newEntry )

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
        if not self.History[entryId]:
            self.clearInfo()
        elif len( self.History[entryId] ) >= 2:
            self.entryList.setCurrentIndex(self.entryModel.index(1, 0))
        else:
            self.entryList.setCurrentIndex(self.entryModel.index(0, 0))

        self.ShowExpandedHistoryOfEntry(entryId)

        return

    def ShowExpandedHistoryOfEntry(self, entryId):
        existingBoxCount = len( self.detailHistoryLabels )
        for d in self.detailHistoryLabels:
            d.englishTextBox.hide()
            d.commentTextBox.hide()
            d.authorTextBox.hide()
            d.statusIconLabel.hide()

        for index, entry in enumerate( self.History[entryId] ):
            text = Globals.VariableReplace( entry[1] ).replace( '\n', '' ).replace( '<Feed>', '<Feed>\n' )
            comment = Globals.VariableReplace( entry[2] )
            icon = self.StatusIcons[entry[3]]
            author = str( entry[4] )[:4]

            if index < existingBoxCount:
                self.detailHistoryLabels[index].englishTextBox.setText( text )
                self.detailHistoryLabels[index].englishTextBox.show()
                self.detailHistoryLabels[index].commentTextBox.setText( comment )
                self.detailHistoryLabels[index].commentTextBox.show()
                self.detailHistoryLabels[index].authorTextBox.setText( author )
                self.detailHistoryLabels[index].authorTextBox.show()
                self.detailHistoryLabels[index].statusIconLabel.setPixmap( icon )
                self.detailHistoryLabels[index].statusIconLabel.show()
            else:
                textbox = QtGui.QLabel( text )
                commentbox = QtGui.QLabel( comment )
                authorbox = QtGui.QLabel( author )
                statusIconLabel = QtGui.QLabel()
                statusIconLabel.setPixmap( icon )

                self.scrollAreaGridLayout.addWidget( statusIconLabel, index + 1, 0 )
                self.scrollAreaGridLayout.addWidget( authorbox, index + 1, 1 )
                self.scrollAreaGridLayout.addWidget( textbox, index + 1, 2 )
                self.scrollAreaGridLayout.addWidget( commentbox, index + 1, 3 )
                
                d = HistoryDataHelper()
                d.englishTextBox = textbox
                d.commentTextBox = commentbox
                d.authorTextBox = authorbox
                d.statusIconLabel = statusIconLabel
                self.detailHistoryLabels.append( d )
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

    def ShowDetailedHistory(self):
        self.stackedWidget.setCurrentIndex(0)
        return

    def ShowFullHistory(self):
        self.stackedWidget.setCurrentIndex(1)
        return

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/HistoryWindow', self.saveGeometry())
