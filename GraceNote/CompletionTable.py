# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import os
import sqlite3
import DatabaseHandler

class CompletionTable(QtGui.QDialog):

    def __init__(self, parent):
        super(CompletionTable, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon('icons/completion.png'))

        self.parent = parent
        self.setWindowModality(False)        

        self.treewidget = QtGui.QTreeWidget()
        
        self.treewidget.setColumnCount( Globals.configData.TranslationStagesCount + 2 )
        labels = ['Name']
        for i in range(1, Globals.configData.TranslationStagesCount + 1):
            labels.append( Globals.configData.TranslationStagesNames[i] )
        labels.append( 'Comments' )
        self.treewidget.setHeaderLabels(labels)
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 200)
        for i in range(1, Globals.configData.TranslationStagesCount + 1):
            self.treewidget.setColumnWidth(i, 140)
        
        self.treewidget.setMinimumSize(620, 500)

        subLayout = QtGui.QVBoxLayout()
        subLayout.addWidget(self.treewidget)
        self.setLayout(subLayout)

        self.treewidget.itemDoubleClicked.connect(self.JumpToFile)

        progressMax = len(os.listdir(Globals.configData.LocalDatabasePath))+1
        progress = QtGui.QProgressDialog("Calculating percentages...", "Abort", 0, progressMax)
        progress.setWindowModality(QtCore.Qt.WindowModal)

        self.totalCounts = []
        for i in range(0, Globals.configData.TranslationStagesCount + 1):
            self.totalCounts.append(0)
        self.totalCommentCount = 0

        tempCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/CompletionPercentage')
        tempCur = tempCon.cursor()
            
        def AddCategory( categoryNode, treeWidgetItem ):
            cat = QtGui.QTreeWidgetItem(treeWidgetItem, [categoryNode.Name])
            
            translationStageCounts = []
            for i in range(0, Globals.configData.TranslationStagesCount + 1):
                translationStageCounts.append(0)
            commentCount = 0
            
            for item in categoryNode.Data:
                if item.IsCategory:
                    AddCategory( item, cat )
                else:
                    tempCur.execute("SELECT Count(1) FROM StatusData WHERE Database = ?", [item.Name])
                    exists = tempCur.fetchall()[0][0]
                    if exists < Globals.configData.TranslationStagesCount + 2:
                        CalculateCompletionForDatabase(item.Name)

                    tempCur.execute("SELECT type, amount FROM StatusData WHERE Database = ?", [item.Name])
                    rows = tempCur.fetchall()

                    databaseCounts = {}
                    for row in rows:
                        type = row[0]
                        count = row[1]
                        databaseCounts[type] = count

                    for i in range(0, Globals.configData.TranslationStagesCount + 1):
                        translationStageCounts[i] += databaseCounts[i]
                    
                    commentamount = databaseCounts[-2]
                    commentCount += commentamount
                    self.totalCommentCount += commentamount

                    databaseCountStrings = []
                    if databaseCounts[0] != 0:
                        for i in range(1, Globals.configData.TranslationStagesCount + 1):
                            databaseCountStrings.append( '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(databaseCounts[i])/float(databaseCounts[0])*100, databaseCounts[i], databaseCounts[0]) )
                    else:
                        for i in range(0, Globals.configData.TranslationStagesCount):
                            databaseCountStrings.append('N/A')
                   
                    rowdata = [item.Name]
                    for s in databaseCountStrings:
                        rowdata.append(s)
                    rowdata.append('{0}'.format(commentamount))

                    newrow = QtGui.QTreeWidgetItem(cat, rowdata)
                    
                    progress.setValue(progress.value() + 1)
    
            for i in range(1, Globals.configData.TranslationStagesCount + 1):
                cat.setData(i, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(translationStageCounts[i])/float(translationStageCounts[0])*100, translationStageCounts[i], translationStageCounts[0]))
            cat.setData(i+1, 0, '{0}'.format(commentCount))
            
            for i in range(0, Globals.configData.TranslationStagesCount + 1):
                self.totalCounts[i] += translationStageCounts[i]

        for category in Globals.configData.FileTree.Data:
            AddCategory( category, self.treewidget )

        # add a list entry for total
        cat = QtGui.QTreeWidgetItem(self.treewidget, ['--- Total ---'])
        for i in range(1, Globals.configData.TranslationStagesCount + 1):
            cat.setData(i, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(self.totalCounts[i])/float(self.totalCounts[0])*100, self.totalCounts[i], self.totalCounts[0]))
        cat.setData(i+1, 0, '{0}'.format(self.totalCommentCount))

        self.treewidget.sortItems(0, 0)
        progress.setValue(progressMax)
        
        geom = Globals.Settings.value('Geometry/CompletionTable')
        if geom is not None:
            self.restoreGeometry(geom)

        for i in range(1, Globals.configData.TranslationStagesCount + 1):
            self.setWindowTitle('Current Phase: ' + Globals.configData.TranslationStagesNames[i] + ', at {0:.2f}% completion'.format(float(self.totalCounts[i])/float(self.totalCounts[0])*100))
            if self.totalCounts[0] != self.totalCounts[i]:
                break

    def JumpToFile(self, item, column):
        if item.childCount() > 0:
            return

        databaseName = item.data(0, 0)
        self.parent.JumpToEntry(databaseName, 1)

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/CompletionTable', self.saveGeometry())

def CalculateAllCompletionPercentagesForDatabase():
    for item in Globals.configData.FileList:
        CalculateCompletionForDatabase(item)

def CalculateCompletionForDatabase(database):
    #print 'Calculating percentages for ' + database + '...'
    
    Globals.Cache.databaseAccessRLock.acquire()

    CompletionConnection, CompletionCursor = DatabaseHandler.GetCompletionPercentageConnectionAndCursor()
    DatabaseConnection = DatabaseHandler.OpenEntryDatabase(database)
    DatabaseCursor = DatabaseConnection.cursor()

    for i in range(0, Globals.configData.TranslationStagesCount + 1):
        DatabaseCursor.execute('SELECT Count(1) FROM Text WHERE status >= {0}'.format(i))
        count = DatabaseCursor.fetchall()[0][0]

        CompletionCursor.execute("SELECT Count(1) FROM StatusData WHERE database = ? AND type = ?", [database, i])
        exists = CompletionCursor.fetchall()[0][0]
        if exists > 0:
            CompletionCursor.execute("UPDATE StatusData SET amount = ? WHERE database = ? AND type = ?", [count, database, i])
        else:
            CompletionCursor.execute("INSERT INTO StatusData (database, type, amount) VALUES (?, ?, ?)", [database, i, count])

    DatabaseCursor.execute("SELECT Count(1) FROM Text WHERE comment != ''")
    count = DatabaseCursor.fetchall()[0][0]

    CompletionCursor.execute("SELECT Count(1) FROM StatusData WHERE database = ? AND type = -2", [database])
    exists = CompletionCursor.fetchall()[0][0]
    if exists > 0:
        CompletionCursor.execute("UPDATE StatusData SET amount = ? WHERE database = ? AND type = -2", [count, database])
    else:
        CompletionCursor.execute("INSERT INTO StatusData (database, type, amount) VALUES (?, -2, ?)", [database, count])
    
    CompletionConnection.commit()

    Globals.Cache.databaseAccessRLock.release()

