# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import sqlite3
import re
import DatabaseHandler
import DatabaseCache
import enchant
import enchant.tokenize

class MassSpellcheck(QtGui.QDialog):

    def __init__(self, parent):
        super(MassSpellcheck, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon('icons/massreplace.png'))

        self.parent = parent

        self.dict = enchant.Dict("en_US")
        for word in Globals.configData.Dictionary:
            self.dict.add_to_session(word.strip())
        self.tokenizer = enchant.tokenize.get_tokenizer( "en_US", chunkers=(enchant.tokenize.HTMLChunker,) )

        self.setWindowModality(False)
        
        self.tabwidget = QtGui.QTabWidget()
        
        font = QtGui.QLabel().font()
        font.setPointSize(10)
 
        self.fileFilter = QtGui.QLineEdit()
        self.searchDebug = QtGui.QCheckBox('Include Debug')

        filterLabel = QtGui.QLabel('Filter by File:')
        filterLabel.setToolTip('Wildcards implicit, so "scene" selects all databases with "scene" anywhere in the name.')
        self.fileFilter.setToolTip('Wildcards implicit, so "scene" selects all databases with "scene" anywhere in the name.')
        filterLabel.setFont(font)
        
        self.search = QtGui.QPushButton('Search')

        self.removeTabButton = QtGui.QToolButton()
        self.removeTabButton.setText('Close Tab')
        
        checkLayout = QtGui.QHBoxLayout()
        checkLayout.addWidget(self.removeTabButton)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addLayout(checkLayout)
        buttonLayout.addWidget(self.search)
                
        textboxLayout = QtGui.QGridLayout()
        textboxLayout.setContentsMargins( QtCore.QMargins(0, 0, 0, 0) )

        optionsLayout = QtGui.QGridLayout()
        optionsLayout.addWidget(self.searchDebug, 0, 0, 1, 1)
        optionsLayout.setContentsMargins( QtCore.QMargins(0, 0, 0, 0) )
        optionsWidget = QtGui.QWidget()
        optionsWidget.setLayout(optionsLayout)
                
        inputLayout = QtGui.QGridLayout()
        inputLayout.addWidget(optionsWidget    , 0, 0, 1, 1)
        inputLayout.addWidget(filterLabel      , 0, 1, 1, 1)
        inputLayout.addWidget(self.fileFilter  , 1, 1, 1, 1)
        
        inputLayout.setColumnStretch(1, 1)
        
        self.search.released.connect(self.Search)
        self.removeTabButton.released.connect(self.closeCurrentTab)
                
        self.setWindowTitle('Mass Spellcheck')
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

    def generateSearchTab(self):
        treewidget = QtGui.QTreeWidget()
        
        treewidget.setColumnCount(7)
        treewidget.setHeaderLabels(['Database Desc.', 'Entry', 'Info', 'Current String', 'Misspelled Word', 'Status', 'Database Name'])
        treewidget.setSortingEnabled(True)
        treewidget.setRootIsDecorated(False)
        
        treewidget.setColumnWidth(0, 120)
        treewidget.setColumnWidth(1, 30)
        treewidget.setColumnWidth(2, 50)
        treewidget.setColumnWidth(3, 275)
        treewidget.setColumnWidth(4, 275)
        treewidget.setColumnWidth(5, 30)
        treewidget.setColumnWidth(6, 100)
        
        treewidget.sortItems(0, QtCore.Qt.AscendingOrder)
        
        treewidget.itemDoubleClicked.connect(self.JumpToFile)
        
        return treewidget

    def closeCurrentTab(self):
        self.tabwidget.removeTab( self.tabwidget.currentIndex() )

    def Search(self):
        self.parent.WriteDatabaseStorageToHdd()
        
        newSearchTab = self.generateSearchTab()

        dbFilter = unicode( self.fileFilter.text() ).lower()
        tabNameString = dbFilter
        
        searchDebug = self.searchDebug.isChecked()

        sortedfiles = []
        for File in Globals.configData.FileList:
            sortedfiles.append(File)
        sortedfiles.sort()

        MatchedEntries = []
        for File in sortedfiles:
            if dbFilter in File.lower() or dbFilter in Globals.GetDatabaseDescriptionString(File).lower():
                data = Globals.Cache.GetDatabase(File)
                for i in xrange(len(data)):
                    if searchDebug or data[i].status >= 0:
                        for word in self.tokenizer( Globals.VariableReplace(data[i].english) ):
                            if not self.dict.check( word[0] ):
                                MatchedEntries.append( [File, i+1, data[i].english, word[0], data[i].IdentifyString, data[i].status, Globals.GetDatabaseDescriptionString(File)] )
                        
        if len(MatchedEntries) == 0:
            return

        def html_escape(text):
            """Produce entities within text."""
            html_escape_table = {
                 "&": "&amp;",
                 '"': "&quot;",
                 "'": "&apos;",
                 ">": "&gt;",
                 "<": "&lt;",
                 }
            return "".join(html_escape_table.get(c,c) for c in text)

        html = open('spellcheck.html', 'w')
        html.write('<html>')
        html.write('<head>')
        html.write('<style>')
        html.write('body { background-color: #68504F; color: #EFD1AE; font-size: 16; }')
        html.write('table, tr, td, th { padding: 0px 4px 0px 0px; border-spacing: 0px; }')
        html.write('td, td > a { padding-right: 16px; padding-bottom: 16px; }')
        html.write('span.mis { font-weight: bold; text-decoration: underline; }')
        html.write('</style>')
        html.write('</head>')
        html.write('<body>')
        html.write('<table>')
        html.write('\n')

        MisWords = {}
        for item in MatchedEntries:
            try:
                filename = item[0]
                entryID = item[1]
                englishString = Globals.VariableReplace(item[2])
                misspelledWord = Globals.VariableReplace(item[3])
                infoString = item[4]
                status = item[5]
                databaseDescriptor = item[6]
                                
                treeItem = QtGui.QTreeWidgetItem([databaseDescriptor, str(entryID), str(infoString), englishString, misspelledWord, str(int(status)), filename])
                newSearchTab.addTopLevelItem(treeItem)

            except:
                Globals.MainWindow.displayStatusMessage("Mass Spellcheck: Failed adding file [" + filename + "], entry [" + str(entryID) + "]")

            html.write('<tr>')
            html.write('<td>' + html_escape(unicode(filename)) + '</td>')
            html.write('<td>' + html_escape(unicode(databaseDescriptor)) + '</td>')
            html.write('<td>' + html_escape(unicode(entryID)) + '</td>')
            html.write('<td>' + html_escape(unicode(infoString)) + '</td>')
            html.write('<td>' + html_escape(unicode(status)) + '</td>')
            html.write('<td>' + html_escape(unicode(misspelledWord)).encode('utf8') + '</td>')
            html.write('<td>' + html_escape(unicode(englishString)).replace(html_escape(misspelledWord), '<span class="mis">' + html_escape(misspelledWord) + '</span>').encode('utf8') + '</td>')
            html.write('</tr>')
            html.write('\n')

            if misspelledWord not in MisWords:
                MisWords[misspelledWord] = 1
            else:
                MisWords[misspelledWord] += 1
        
        html.write('</table>')
        html.write('</body>')
        html.write('</html>')
        html.close()
        xml = open('dictionary.xml', 'w')

        import operator
        for misspelledWord, count in sorted(MisWords.items(), key=operator.itemgetter(1), reverse=True):
            xml.write('\t\t<!-- ' + str(count) + ' --> <Entry Word="' + html_escape(unicode(misspelledWord)).encode('utf8') + '" />\n')
        xml.close()

        self.tabwidget.addTab(newSearchTab, tabNameString)
        self.tabwidget.setCurrentIndex(self.tabwidget.count()-1)
        
    def TabChanged(self, index):
        return

    def JumpToFile(self, item, column):
        if item.childCount() > 0:
            return

        databaseName = item.data(6, 0)
        entryno = item.data(1, 0)
        self.parent.JumpToEntry(databaseName, entryno)
        self.parent.show()
        self.parent.raise_()
        self.parent.activateWindow()

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/MassReplace', self.saveGeometry())
