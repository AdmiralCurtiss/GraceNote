from PyQt4 import QtCore, QtGui
import Globals

class DuplicateText(QtGui.QDialog):

    def __init__(self, parent):
        super(DuplicateText, self).__init__()

        self.setWindowModality(False)        
        
        self.parent = parent

        self.treewidget = QtGui.QTreeWidget()
        
        self.treewidget.setColumnCount(2)
        self.treewidget.setHeaderLabels(['Amount', 'Text'])
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 80)
        self.treewidget.setColumnWidth(1, 540)
        
        self.treewidget.setMinimumSize(620, 500)

        
        self.box = QtGui.QGroupBox()
        self.box.setTitle('Search:')
        
        layout = QtGui.QGridLayout()
        
        self.categories = []
        
        i = 0
        x = 0
        y = 0
        for cat in Globals.configData.FileList[0]:
            self.categories.append(QtGui.QCheckBox(cat))
            layout.addWidget(self.categories[i], y, x)
            i += 1
            x += 1
            if x > 5:
                x = 0
                y += 1
        if x != 0:
            x = 0
            y += 1
        x = 2
        self.checkall = QtGui.QPushButton('Check All')
        layout.addWidget(self.checkall, y, x)
        self.checkall.released.connect(self.CheckAll)
        x += 1
        self.checknone = QtGui.QPushButton('Check None')
        layout.addWidget(self.checknone, y, x)
        self.checknone.released.connect(self.CheckNone)
        x += 1
        self.collall = QtGui.QPushButton('Collapse All')
        layout.addWidget(self.collall, y, x)
        self.collall.released.connect(self.CollapseAll)
        x += 1
        self.uncollall = QtGui.QPushButton('Expand All')
        layout.addWidget(self.uncollall, y, x)
        self.uncollall.released.connect(self.UncollapseAll)
        
        self.exceptions = QtGui.QRadioButton('Inconsistent Translations only')
        self.dupes = QtGui.QRadioButton('All Duplicates')
        self.exceptions.setChecked(True)
        
        self.go = QtGui.QPushButton('Search')

        self.progressbar = QtGui.QProgressBar()
        self.progressbar.setRange(0, 100000)
        
        self.progressLabel = QtGui.QLabel('Pending')
        
        layoutSystemButtons = QtGui.QGridLayout()
        layoutSystemButtons.addWidget(self.exceptions, 0, 0)
        layoutSystemButtons.addWidget(self.dupes, 0, 1)
        #layoutSystemButtons.addWidget(self.progressbar, 3, 1)
        #layoutSystemButtons.addWidget(self.progressLabel, 4, 1)
        layoutSystemButtons.addWidget(self.go, 0, 2)
        layoutSystemButtons.setColumnMinimumWidth(0, 200)
        
        self.treewidget.itemDoubleClicked.connect(self.InitiateMassReplaceSearch)

        self.setWindowTitle('Duplicate Text Retriever')
        subLayout = QtGui.QVBoxLayout()
        subLayout.addLayout(layoutSystemButtons)
        subLayout.addLayout(layout)
        subLayout.addWidget(self.treewidget)
        self.setLayout(subLayout)

        self.go.released.connect(self.SearchCategories)
        
    def CheckAll(self):
        for category in self.categories:
            category.setCheckState(QtCore.Qt.Checked)
    def CheckNone(self):
        for category in self.categories:
            category.setCheckState(QtCore.Qt.Unchecked)
    def CollapseAll(self):
        self.treewidget.collapseAll()
    def UncollapseAll(self):
        self.treewidget.expandAll()
        
        
#     Two options
#        One: Search for any cloned text with more than one unique translation, and display them
#        Two: Search for any cloned text at all, and display them
    def SearchCategories(self):

        self.treewidget.clear()

        print 'Initializing container...'
        Table = []
        BlackList = []
        Globals.CursorGracesJapanese.execute('SELECT MAX(ID) FROM Japanese')
        maxid = int(Globals.CursorGracesJapanese.fetchall()[0][0])
        for i in xrange( maxid + 1 ):
            Table.append([0, set([])])
            BlackList.append(0)

        print 'Fetching debug information...'
        Globals.CursorGracesJapanese.execute('SELECT ID FROM Japanese WHERE debug=1')
        BlackListDB = Globals.CursorGracesJapanese.fetchall()
        for id in BlackListDB:
            BlackList[int(id[0])] = 1
        aList = Globals.configData.FileList

        i = 1
        print 'Processing databases...'
        for category in self.categories:
            if category.isChecked() == True:
                for filename in aList[i]:
                    #print 'Processing ' + filename + '...'

                    conC = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(filename))
                    curC = conC.cursor()
                    
                    curC.execute("SELECT StringID, English FROM Text")
                    
                    results = curC.fetchall()
                    
                    for item in results:
                        StringId = int(item[0])
                        if BlackList[StringId] == 0:
                            Table[StringId][0] += 1
                            Table[StringId][1].add(item[1])
#                    self.progressbar.setValue(self.progressbar.value() + (6250/len(Globals.configData.FileList[i])))
#                    self.progressLabel.setText("Processing {0}".format(category))
#                    self.progressLabel.update()
#            self.progressbar.setValue(i * 6250)
            i += 1
        
        print 'Displaying entries...'
        i = 0
        for item in Table:
            if (self.exceptions.isChecked() == False and item[0] > 1) or (self.exceptions.isChecked() == True and (((item[0] > 1) and (len(item[1]) >= 2)) or ((item[0] > 1) and (item[1] == set(['']))))):
                Globals.CursorGracesJapanese.execute('SELECT String FROM Japanese WHERE ID=?', (i, ))
                JP = Globals.CursorGracesJapanese.fetchall()[0][0]
            
                textOriginalJapaneseText = QtGui.QTreeWidgetItem(self.treewidget, [str(item[0]).zfill(3), Globals.VariableReplace(JP)])
                textOriginalJapaneseText.setBackgroundColor(0, QtGui.QColor(212,236,255,255))
                textOriginalJapaneseText.setBackgroundColor(1, QtGui.QColor(212,236,255,255))
                for exception in item[1]:
                    newline = QtGui.QTreeWidgetItem(textOriginalJapaneseText, ['', Globals.VariableReplace(exception)])
#           self.progressLabel.setText("Processing {0}/50000".format(i))
            i += 1
#           self.progressbar.setValue(self.progressbar.value() + 1)
#       self.progressLabel.setText('Done!')
        i = 0

#       self.progressbar.reset

    def InitiateMassReplaceSearch(self, item, column):
        parentItem = item.parent()
        searchstring = item.data(1, 0)
        self.parent.ShowMassReplace()
        if parentItem is None: # clicked on the Japanese text, just search for it
            self.parent.massDialog.original.setText(searchstring)
        else: # clicked on the English subentry, search for JP and place ENG in the replacement box
            self.parent.massDialog.original.setText(parentItem.data(1, 0))
            self.parent.massDialog.replacement.setText(searchstring)
            
        self.parent.massDialog.matchEntry.setChecked(True)
        self.parent.massDialog.Search()

