# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import sqlite3
import re
import DatabaseHandler
import DatabaseCache

class MassReplace(QtGui.QDialog):

    def __init__(self, parent):
        super(MassReplace, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon('icons/massreplace.png'))

        self.parent = parent

        self.setWindowModality(False)
        
        self.searches = []
        self.tabwidget = QtGui.QTabWidget()
        
        
        font = QtGui.QLabel().font()
        font.setPointSize(10)
 
        self.original = QtGui.QTextEdit()
        self.original.setAcceptRichText(False)
        self.original.setFixedHeight(50)
        self.replacement = QtGui.QTextEdit()
        self.replacement.setAcceptRichText(False)
        self.replacement.setFixedHeight(50)
        self.exceptions = QtGui.QLineEdit()
        self.fileFilter = QtGui.QLineEdit()
        self.matchJpnCheckbox = QtGui.QCheckBox('Search Japanese')
        self.matchEngCheckbox = QtGui.QCheckBox('Search English')
        self.matchEntryCheckbox = QtGui.QCheckBox('Complete Entry Only')
        self.matchEngCheckbox.setChecked(True)
        self.matchCase = QtGui.QCheckBox('Match Case')
        self.searchDebug = QtGui.QCheckBox('Include Debug')
        self.searchStartOfEntry = QtGui.QCheckBox('At Start of Entry')
        self.searchEndOfEntry = QtGui.QCheckBox('At End of Entry')

        self.matchEngCheckbox.setFont(font)
        self.matchJpnCheckbox.setFont(font)
        self.matchEntryCheckbox.setFont(font)
                
        originalLabel = QtGui.QLabel('Search for:')
        originalLabel.setFont(font)
        exceptionLabel = QtGui.QLabel('Excluding:')
        exceptionLabel.setFont(font)
        replaceLabel = QtGui.QLabel('Replace with:')
        replaceLabel.setFont(font)
        
        filterLabel = QtGui.QLabel('Filter by File:')
        filterLabel.setToolTip('Wildcards implicit, so "scene" selects all databases with "scene" anywhere in the name.')
        self.fileFilter.setToolTip('Wildcards implicit, so "scene" selects all databases with "scene" anywhere in the name.')
        filterLabel.setFont(font)
        
        self.search = QtGui.QPushButton('Search')
        self.replace = QtGui.QPushButton('Replace')

        self.checkAll = QtGui.QToolButton()
        self.checkAll.setText('Check All')
        self.checkNone = QtGui.QToolButton()
        self.checkNone.setText('Check None')
        self.removeTabButton = QtGui.QToolButton()
        self.removeTabButton.setText('Remove Tab')
        
        checkLayout = QtGui.QHBoxLayout()
        checkLayout.addWidget(self.checkAll)
        checkLayout.addWidget(self.checkNone)
        checkLayout.addWidget(self.removeTabButton)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addLayout(checkLayout)
        buttonLayout.addWidget(self.search)
        buttonLayout.addWidget(self.replace)
                
        textboxLayout = QtGui.QGridLayout()
        textboxLayout.addWidget(originalLabel    , 0, 0, 1, 1)
        textboxLayout.addWidget(replaceLabel     , 0, 1, 1, 1)
        textboxLayout.addWidget(self.original    , 1, 0, 1, 1)
        textboxLayout.addWidget(self.replacement , 1, 1, 1, 1)
        textboxLayout.setContentsMargins( QtCore.QMargins(0, 0, 0, 0) )
        textboxWidget = QtGui.QWidget()
        textboxWidget.setLayout(textboxLayout)

        optionsLayout = QtGui.QGridLayout()
        optionsLayout.addWidget(self.matchCase         , 0, 0, 1, 1)
        optionsLayout.addWidget(self.searchDebug       , 0, 1, 1, 1)
        #optionsLayout.addWidget(self.searchStartOfEntry, 0, 2, 1, 1) # don't work at the moment, maybe reimplement later
        #optionsLayout.addWidget(self.searchEndOfEntry  , 0, 3, 1, 1)
        optionsLayout.setContentsMargins( QtCore.QMargins(0, 0, 0, 0) )
        optionsWidget = QtGui.QWidget()
        optionsWidget.setLayout(optionsLayout)
                
        inputLayout = QtGui.QGridLayout()
        inputLayout.addWidget(textboxWidget    , 0, 0, 3, 2)
        inputLayout.addWidget(exceptionLabel   , 3, 0, 1, 1)
        inputLayout.addWidget(self.exceptions  , 3, 1, 1, 1)
        inputLayout.addWidget(optionsWidget    , 4, 0, 1, 2)
        inputLayout.addWidget(filterLabel      , 0, 2, 1, 1)
        inputLayout.addWidget(self.fileFilter  , 1, 2, 1, 1)
        inputLayout.addWidget(self.matchEntryCheckbox  , 2, 2, 1, 1)
        inputLayout.addWidget(self.matchJpnCheckbox  , 3, 2, 1, 1)
        inputLayout.addWidget(self.matchEngCheckbox, 4, 2, 1, 1)
        
        inputLayout.setColumnStretch(1, 1)
        
        self.search.released.connect(self.Search)
        self.replace.released.connect(self.Replace)
        self.checkAll.released.connect(self.checkingAll)
        self.checkNone.released.connect(self.checkingNone)
        self.removeTabButton.released.connect(self.closeCurrentTab)
                
        self.setWindowTitle('Mass Replace')
        layout = QtGui.QVBoxLayout()
        layout.addLayout(inputLayout)
        layout.addWidget(self.tabwidget)
        layout.addLayout(buttonLayout, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(800, 600)

        geom = Globals.Settings.value('Geometry/MassReplace')
        if geom is not None:
            self.restoreGeometry(geom)

        self.tabwidget.currentChanged.connect(self.TabChanged)
        self.replacement.textChanged.connect(self.ReplacementTextChanged)

    def generateSearchTab(self):
        treewidget = QtGui.QTreeWidget()
        
        treewidget.setColumnCount(10)
        treewidget.setHeaderLabels(['Database Desc.', 'Entry', 'Info', 'Replace?', 'Current String', 'Replace String', 'Japanese String', 'Status', 'Database Name', 'Replacement Type'])
        treewidget.setSortingEnabled(True)
        treewidget.setRootIsDecorated(False)
        
        treewidget.setColumnWidth(0, 120)
        treewidget.setColumnWidth(1, 30)
        treewidget.setColumnWidth(2, 50)
        treewidget.setColumnWidth(3, 20)
        treewidget.setColumnWidth(4, 275)
        treewidget.setColumnWidth(5, 275)
        treewidget.setColumnWidth(6, 275)
        treewidget.setColumnWidth(7, 30)
        treewidget.setColumnWidth(8, 100)
        treewidget.setColumnWidth(9, 50)
        
        treewidget.sortItems(0, QtCore.Qt.AscendingOrder)
        
        treewidget.itemDoubleClicked.connect(self.JumpToFile)
        
        return treewidget

    def checkingAll(self):
    
        Iterator = QtGui.QTreeWidgetItemIterator(self.tabwidget.currentWidget())
        while Iterator.value():

            Iterator.value().setCheckState(3, 2)
            Iterator += 1 
        
    def checkingNone(self):
    
        Iterator = QtGui.QTreeWidgetItemIterator(self.tabwidget.currentWidget())
        while Iterator.value():

            Iterator.value().setCheckState(3, 0)
            Iterator += 1 

    def closeCurrentTab(self):
        self.tabwidget.removeTab( self.tabwidget.currentIndex() )
            
    def Search(self):
        # Place all matching strings to the search into the tree widget
        self.parent.WriteDatabaseStorageToHdd()
        
        newSearchTab = self.generateSearchTab()
        matchString = unicode(self.original.toPlainText())
        exceptString = unicode(self.exceptions.text())

        if matchString.count(unicode('<', 'UTF-8')) != matchString.count(unicode('>', 'UTF-8')):
            reply = QtGui.QMessageBox.information(self, "Questionable Search Usage", "Warning:\n\nPart of a variable: Be sure you know what you're doing.")
            #return

        tabNameString = matchString
        matchString = Globals.VariableRemove(matchString)
        
        searchDebug = self.searchDebug.isChecked()
        matchCase = self.matchCase.isChecked()
        matchFullEntry = self.matchEntryCheckbox.isChecked()
        matchJapanese = self.matchJpnCheckbox.isChecked()
        matchEnglish = self.matchEngCheckbox.isChecked()

        if not matchFullEntry:
            if len(matchString) == 1:
                if ord(matchString) <= 0x20:
                    reply = QtGui.QMessageBox.question(self, "Questionable Search Usage", "Warning:\n\nYour search only consists of a space, a form feed, a newline, or a tab.\nAre you sure you want to search for this?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                    if reply != QtGui.QMessageBox.Yes:
                        return
            elif len(matchString) == 0:
                reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search can not be empty. Please enter text in the search bar.")
                return

        MatchedEntries = []
        aList = Globals.configData.FileList

        # turn on case sensitive checking
        if matchCase:
            Globals.CursorGracesJapanese.execute(u"PRAGMA case_sensitive_like = ON")

        JPmatches = set()
        if matchFullEntry:
            ReplacementType = 'Entry'
            if matchJapanese:
                Globals.CursorGracesJapanese.execute(u"SELECT ID FROM Japanese WHERE string LIKE ?", (unicode(matchString),))
                for match in Globals.CursorGracesJapanese.fetchall():
                    JPmatches.add(int(match[0]))
        else:
            ReplacementType = 'Substr'
            if matchJapanese:
                Globals.CursorGracesJapanese.execute(u"SELECT ID FROM Japanese WHERE string LIKE ?", ('%' + unicode(matchString) + '%', ))
                for match in Globals.CursorGracesJapanese.fetchall():
                    JPmatches.add(int(match[0]))

        dbFilter = unicode( self.fileFilter.text() ).lower()
        for j in range(1, len(aList)):
            for File in aList[j]:
                if dbFilter in File.lower() or dbFilter in Globals.GetDatabaseDescriptionString(File).lower():
                    data = Globals.Cache.GetDatabase(File)
                    for i in xrange(len(data)):
                        if ( matchJapanese and data[i].stringId in JPmatches ) \
                        or ( matchEnglish and matchFullEntry and data[i].english == matchString ) \
                        or ( matchEnglish and not matchFullEntry and matchCase and matchString in data[i].english ) \
                        or ( matchEnglish and not matchFullEntry and not matchCase and matchString.upper() in data[i].english.upper() > -1 ):
                            if searchDebug or data[i].status >= 0:
                                Globals.CursorGracesJapanese.execute('SELECT string FROM Japanese WHERE ID={0}'.format(data[i].stringId))
                                JPString = Globals.CursorGracesJapanese.fetchall()[0][0]
                                MatchedEntries.append( [File, i+1, data[i].english, JPString, data[i].IdentifyString, data[i].status, Globals.GetDatabaseDescriptionString(File)] )
                        
        if len(MatchedEntries) == 0:
            return

        if len(exceptString) >= 1:
            checkForExceptions = True
        else:
            checkForExceptions = False
            
        for item in MatchedEntries:
            try:
                filename = item[0]
                entryID = item[1]
                englishString = Globals.VariableReplace(item[2])
                japaneseString = Globals.VariableReplace(item[3])
                infoString = item[4]
                status = item[5]
                databaseDescriptor = item[6]
                                
                if checkForExceptions:
                    if exceptString in englishString or exceptString in japaneseString:
                        continue
                    
                treeItem = QtGui.QTreeWidgetItem([databaseDescriptor, str(entryID), str(infoString), "", englishString, englishString, japaneseString, str(int(status)), filename, ReplacementType])
                treeItem.setCheckState(3, QtCore.Qt.Checked)
                newSearchTab.addTopLevelItem(treeItem)
            except:
                Globals.MainWindow.displayStatusMessage("Mass Replace: Failed adding file [" + filename + "], entry [" + str(entryID) + "]")
        
        # turn case sensitiveness back off
        if matchCase:
            Globals.CursorGracesJapanese.execute(u"PRAGMA case_sensitive_like = OFF")
            
        self.tabwidget.addTab(newSearchTab, tabNameString)
        self.tabwidget.setCurrentIndex(self.tabwidget.count()-1)
        self.UpdateReplacementText()
        
    def Replace(self):
        self.parent.WriteDatabaseStorageToHdd()
        currentTab = self.tabwidget.currentWidget()
        if currentTab == None:
            return

        if len(self.replacement.toPlainText()) == 0:
            reply = QtGui.QMessageBox.question(self, "Questionable Replacement", "Warning:\n\nYour replacement is empty.\nDo you really want to replace with nothing?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply != QtGui.QMessageBox.Yes:
                return
                
        Iterator = QtGui.QTreeWidgetItemIterator(currentTab)
        while Iterator.value():
        
            if Iterator.value().checkState(3) == 2:
                
                databaseName = Iterator.value().data(8, 0)
                entryID = int(Iterator.value().data(1, 0))
                currentStatus = int(Iterator.value().data(7, 0))
                updateStatusValue = self.parent.FigureOutNewStatusValue(self.parent.role, currentStatus, 'ENG', False, False)
                ReplacementType = Iterator.value().data(9, 0)
                originalText = Iterator.value().data(4, 0)
                originalPartToReplace = self.tabwidget.tabText(self.tabwidget.currentIndex())
                replacementPartToReplace = self.replacement.toPlainText()

                stringWithVars = self.ReplaceInStringWithSettings(originalText, originalPartToReplace, replacementPartToReplace, ReplacementType)
                string = Globals.VariableRemove(stringWithVars)
                                
                self.parent.InsertOrUpdateEntryToWrite(DatabaseCache.UpdatedDatabaseEntry(unicode(string), None, unicode(databaseName), entryID, updateStatusValue))
                self.parent.AddDatabaseToUpdateSet(unicode(databaseName))

                Iterator.value().setData(4, 0, stringWithVars)
                Iterator.value().setData(7, 0, str(updateStatusValue)) 

            Iterator += 1 
        
        self.parent.WriteDatabaseStorageToHdd()    
        self.UpdateReplacementText()

        return

    def ReplaceInStringWithSettings(self, text, original, replacement, type):
        if type == 'Substr':
            string = unicode(text)
                    
            orig = unicode(original)
            repl = unicode(replacement)
            if self.matchCase.isChecked():
                string = string.replace(orig, repl)
            else:
                string = re.sub('(?i)' + re.escape(orig), repl, string)
                        
        elif type == 'Entry':
            string = unicode(replacement)
        else:
            string = original

        return string

    def TabChanged(self, index):
        self.UpdateReplacementText()

    def ReplacementTextChanged(self):
        self.UpdateReplacementText()

    def UpdateReplacementText(self):
        currentTab = self.tabwidget.currentWidget()
        if currentTab == None:
            return

        Iterator = QtGui.QTreeWidgetItemIterator(currentTab)
        while Iterator.value():
            ReplacementType = Iterator.value().data(9, 0)
            originalText = Iterator.value().data(4, 0)
            originalPartToReplace = self.tabwidget.tabText(self.tabwidget.currentIndex())
            replacementPartToReplace = self.replacement.toPlainText()

            string = self.ReplaceInStringWithSettings(originalText, originalPartToReplace, replacementPartToReplace, ReplacementType)
               
            Iterator.value().setData(5, 0, string) 
            Iterator += 1 
        return
        
    def JumpToFile(self, item, column):
        if item.childCount() > 0:
            return

        databaseName = item.data(8, 0)
        entryno = item.data(1, 0)
        self.parent.JumpToEntry(databaseName, entryno)
        self.parent.show()
        self.parent.raise_()
        self.parent.activateWindow()

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/MassReplace', self.saveGeometry())
