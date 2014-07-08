# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import sqlite3
import DatabaseCache

class DuplicateText(QtGui.QDialog):

    def __init__(self, parent):
        super(DuplicateText, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon('icons/ruta.png'))

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
        
        self.categoryGridLayout = QtGui.QGridLayout()
        
        self.categories = []
        self.categoryTreeItems = []
        
        def AddCategory( categoryNode, i ):
            self.categories.append( QtGui.QCheckBox( categoryNode.Name ) )
            self.categoryTreeItems.append( categoryNode )
            self.categoryGridLayout.addWidget( self.categories[i], i / 6, i % 6 )
            i += 1
            for subCategoryNode in categoryNode.Data:
                if subCategoryNode.IsCategory:
                    i = AddCategory( subCategoryNode, i )
            return i
        
        i = 0
        for cat in Globals.configData.FileTree.Data:
            i = AddCategory( cat, i )

        y = i / 6
        if i % 6 != 0:
            y += 1
        self.checkall = QtGui.QPushButton('Check All')
        self.categoryGridLayout.addWidget(self.checkall, y, 2)
        self.checkall.released.connect(self.CheckAll)
        self.checknone = QtGui.QPushButton('Check None')
        self.categoryGridLayout.addWidget(self.checknone, y, 3)
        self.checknone.released.connect(self.CheckNone)
        self.collall = QtGui.QPushButton('Collapse All')
        self.categoryGridLayout.addWidget(self.collall, y, 4)
        self.collall.released.connect(self.CollapseAll)
        self.uncollall = QtGui.QPushButton('Expand All')
        self.categoryGridLayout.addWidget(self.uncollall, y, 5)
        self.uncollall.released.connect(self.UncollapseAll)
        
        self.radioInconsistentTranslationOrStatus = QtGui.QRadioButton('Inconsistent Translation or Status')
        self.radioInconsistentTranslationOnly = QtGui.QRadioButton('Inconsistent Translation')
        self.radioAllDuplicates = QtGui.QRadioButton('All Duplicates')
        self.radioInconsistentTranslationOrStatus.setChecked(True)
        
        self.go = QtGui.QPushButton('Search')

        layoutSystemButtons = QtGui.QGridLayout()
        layoutSystemButtons.addWidget(self.radioInconsistentTranslationOrStatus, 0, 0)
        layoutSystemButtons.addWidget(self.radioInconsistentTranslationOnly, 0, 1)
        layoutSystemButtons.addWidget(self.radioAllDuplicates, 0, 2)
        layoutSystemButtons.addWidget(self.go, 0, 3)
        layoutSystemButtons.setColumnMinimumWidth(0, 100)
        
        self.treewidget.itemDoubleClicked.connect(self.InitiateMassReplaceSearch)

        self.setWindowTitle('Duplicate Text Retriever')
        subLayout = QtGui.QVBoxLayout()
        subLayout.addLayout(layoutSystemButtons)
        subLayout.addLayout(self.categoryGridLayout)
        subLayout.addWidget(self.treewidget)
        self.setLayout(subLayout)

        self.go.released.connect(self.SearchCategories)

        geom = Globals.Settings.value('Geometry/DuplicateText')
        if geom is not None:
            self.restoreGeometry(geom)
        
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

        Globals.MainWindow.displayStatusMessage( 'Duplicate Text: Initializing container...' )
        Table = []
        BlackList = []
        Globals.CursorGracesJapanese.execute('SELECT MAX(ID) FROM Japanese')
        maxid = int(Globals.CursorGracesJapanese.fetchall()[0][0])
        # TODO: This loop has terrible performance, find a better way to handle.
        for i in xrange( maxid + 1 ):
            Table.append([0, set([])]) # stores number of occurances, set of english+status
            BlackList.append(0)

        Globals.MainWindow.displayStatusMessage( 'Duplicate Text: Fetching debug information...' )
        Globals.CursorGracesJapanese.execute('SELECT ID FROM Japanese WHERE debug=1')
        BlackListDB = Globals.CursorGracesJapanese.fetchall()
        for ID in BlackListDB:
            BlackList[int(ID[0])] = 1
        
        Globals.MainWindow.displayStatusMessage( 'Duplicate Text: Processing databases...' )

        self.databasesToSearch = set()
        def AddCategoryToSearch( categoryNode ):
            for node in categoryNode.Data:
                if node.IsCategory:
                    AddCategoryToSearch( node )
                else:
                    self.databasesToSearch.add( node.Name )
        
        for i, category in enumerate( self.categories ):
            if category.isChecked():
                AddCategoryToSearch( self.categoryTreeItems[i] )
        
        for filename in self.databasesToSearch:
            results = Globals.Cache.GetDatabase(filename)
            for item in results:
                StringId = item.stringId
                if BlackList[StringId] == 0:
                    Table[StringId][0] += 1
                    if not self.radioInconsistentTranslationOnly.isChecked():
                        Table[StringId][1].add((item.english, item.status))
                    else:
                        # set status to something constant to remove check against that
                        Table[StringId][1].add((item.english, 0))
        
        showAllDupes = self.radioAllDuplicates.isChecked()
        showOnlyInconsistencies = self.radioInconsistentTranslationOrStatus.isChecked() or self.radioInconsistentTranslationOnly.isChecked() 

        Globals.MainWindow.displayStatusMessage( 'Duplicate Text: Displaying entries...' )
        i = 0
        for item in Table:
            if (
                    ((showAllDupes) and item[0] > 1) or
                    ((showOnlyInconsistencies) and (((item[0] > 1) and (len(item[1]) >= 2)) or ((item[0] > 1) and (item[1] == set([''])))))
                ):
                Globals.CursorGracesJapanese.execute('SELECT String FROM Japanese WHERE ID=?', (i, ))
                JP = Globals.CursorGracesJapanese.fetchall()[0][0]
                JPvarReplaced = Globals.VariableReplace(JP)

                textOriginalJapaneseText = QtGui.QTreeWidgetItem(self.treewidget, [str(item[0]).zfill(3), '[' + JPvarReplaced + ']' ])
                textOriginalJapaneseText.setBackgroundColor(0, QtGui.QColor(212,236,255,255))
                textOriginalJapaneseText.setBackgroundColor(1, QtGui.QColor(212,236,255,255))
                textOriginalJapaneseText.GraceNoteText = JPvarReplaced
                for exception in item[1]:
                    ENvarReplaced = Globals.VariableReplace(exception[0])
                    if not self.radioInconsistentTranslationOnly.isChecked():
                        englishDisplayText = '[' + str(exception[1]) + '] [' + ENvarReplaced +']'
                    else:
                        englishDisplayText = '[' + ENvarReplaced +']'
                    newline = QtGui.QTreeWidgetItem(textOriginalJapaneseText, ['',  englishDisplayText])
                    newline.GraceNoteText = ENvarReplaced
            i += 1
        i = 0

        Globals.MainWindow.displayStatusMessage( 'Duplicate Text: Done!' )

    def InitiateMassReplaceSearch(self, item, column):
        parentItem = item.parent()
        searchstring = item.GraceNoteText
        self.parent.ShowMassReplace()
        if parentItem is None: # clicked on the Japanese text, just search for it
            self.parent.massDialog.original.setText(searchstring)
        else: # clicked on the English subentry, search for JP and place ENG in the replacement box
            self.parent.massDialog.original.setText(parentItem.GraceNoteText)
            self.parent.massDialog.replacement.setText(searchstring)
            
        # make sure settings are correct
        self.parent.massDialog.matchEngCheckbox.setChecked(False)
        self.parent.massDialog.matchJpnCheckbox.setChecked(True)
        self.parent.massDialog.matchEntryCheckbox.setChecked(True)
        self.parent.massDialog.matchCase.setChecked(True)
        self.parent.massDialog.searchDebug.setChecked(False)
        self.parent.massDialog.fileFilter.setText('')
        self.parent.massDialog.exceptions.setText('')

        self.parent.massDialog.Search()

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/DuplicateText', self.saveGeometry())
