# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import os
import sqlite3
import DatabaseHandler

class CategoryCounts():
    pass

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
            
            categoryCounts = CategoryCounts()
            categoryCounts.stages = []
            for i in range(0, Globals.configData.TranslationStagesCount + 1):
                categoryCounts.stages.append(0)
            categoryCounts.comments = 0
            
            for item in categoryNode.Data:
                if item.IsCategory:
                    subCatCount = AddCategory( item, cat )
                    for i in range(0, Globals.configData.TranslationStagesCount + 1):
                        categoryCounts.stages[i] += subCatCount.stages[i]
                    categoryCounts.comments += subCatCount.comments
                else:
                    databaseName = GetCompletionTableDatabaseNameOfTreeNode( item )
                    tempCur.execute("SELECT Count(1) FROM StatusData WHERE Database = ?", [databaseName])
                    exists = tempCur.fetchall()[0][0]
                    if exists < Globals.configData.TranslationStagesCount + 2:
                        CalculateCompletionForDatabase( item.Name )

                    tempCur.execute("SELECT type, amount FROM StatusData WHERE Database = ?", [databaseName])
                    rows = tempCur.fetchall()

                    databaseCounts = {}
                    for row in rows:
                        type = row[0]
                        count = row[1]
                        databaseCounts[type] = count

                    for i in range(0, Globals.configData.TranslationStagesCount + 1):
                        categoryCounts.stages[i] += databaseCounts[i]
                    
                    commentamount = databaseCounts[-2]
                    categoryCounts.comments += commentamount
                    
                    for i in range(0, Globals.configData.TranslationStagesCount + 1):
                        self.totalCounts[i] += databaseCounts[i]
                    self.totalCommentCount += commentamount

                    databaseCountStrings = []
                    if databaseCounts[0] != 0:
                        for i in range(1, Globals.configData.TranslationStagesCount + 1):
                            databaseCountStrings.append( '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(databaseCounts[i])/float(databaseCounts[0])*100, databaseCounts[i], databaseCounts[0]) )
                    else:
                        for i in range(0, Globals.configData.TranslationStagesCount):
                            databaseCountStrings.append('N/A')
                   
                    rowdata = [item.Desc if item.Desc is not None else item.Name]
                    for s in databaseCountStrings:
                        rowdata.append(s)
                    rowdata.append('{0}'.format(commentamount))

                    newrow = QtGui.QTreeWidgetItem(cat, rowdata)
                    newrow.DatabaseNode = item
                    
                    progress.setValue(progress.value() + 1)
    
            for i in range(1, Globals.configData.TranslationStagesCount + 1):
                if categoryCounts.stages[0] > 0:
                    percentage = float(categoryCounts.stages[i])/float(categoryCounts.stages[0])*100
                else:
                    percentage = 100.0
                cat.setData(i, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(percentage, categoryCounts.stages[i], categoryCounts.stages[0]))
            cat.setData(i+1, 0, '{0}'.format(categoryCounts.comments))
            
            return categoryCounts

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

        databaseName = item.DatabaseNode.Name
        self.parent.JumpToEntry(databaseName, item.DatabaseNode.GetFirstEntry())

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/CompletionTable', self.saveGeometry())

def CalculateAllCompletionPercentagesForDatabase():
    for item in Globals.configData.FileList:
        CalculateCompletionForDatabase(item)

def CalculateCompletionForDatabase( databaseName ):
    #print 'Calculating percentages for ' + database + '...'
    def CalculateCompletionForDatabaseInTree( categoryNode ):
        for item in categoryNode.Data:
            if item.IsCategory:
                CalculateCompletionForDatabaseInTree( item )
            else:
                if item.Name == databaseName:
                    CalculateCompletionForDatabaseTreeNode( item )
        return

    for category in Globals.configData.FileTree.Data:
        CalculateCompletionForDatabaseInTree( category )
    return

# since subsectioned databases have different completion % on the same file, generate unique names for them
def GetCompletionTableDatabaseNameOfTreeNode( node ):
    databaseName = node.Name

    # if the database is subsectioned, extend the database name by the subsections for a unique name
    if node.Subsections:
        for sub in node.Subsections:
            databaseName += "/{0}-{1}".format(sub.Start, sub.End)

    return databaseName

def CalculateCompletionForDatabaseTreeNode( node ):

    Globals.Cache.databaseAccessRLock.acquire()

    CompletionConnection, CompletionCursor = DatabaseHandler.GetCompletionPercentageConnectionAndCursor()
    DatabaseConnection = DatabaseHandler.OpenEntryDatabase(node.Name)
    DatabaseCursor = DatabaseConnection.cursor()

    databaseName = GetCompletionTableDatabaseNameOfTreeNode( node )
    
    for i in range(0, Globals.configData.TranslationStagesCount + 1):
        if not node.Subsections:
            DatabaseCursor.execute('SELECT Count(1) FROM Text WHERE status >= {0}'.format(i))
            count = DatabaseCursor.fetchall()[0][0]
        else:
            count = 0
            for sub in node.Subsections:
                DatabaseCursor.execute('SELECT Count(1) FROM Text WHERE status >= {0} AND ID >= {1} AND ID <= {2}'.format(i, sub.Start, sub.End))
                count += int(DatabaseCursor.fetchall()[0][0])

        CompletionCursor.execute("SELECT Count(1) FROM StatusData WHERE database = ? AND type = ?", [databaseName, i])
        exists = CompletionCursor.fetchall()[0][0]
        if exists > 0:
            CompletionCursor.execute("UPDATE StatusData SET amount = ? WHERE database = ? AND type = ?", [count, databaseName, i])
        else:
            CompletionCursor.execute("INSERT INTO StatusData (database, type, amount) VALUES (?, ?, ?)", [databaseName, i, count])

    if not node.Subsections:
        DatabaseCursor.execute("SELECT Count(1) FROM Text WHERE comment != ''")
        count = DatabaseCursor.fetchall()[0][0]
    else:
        count = 0
        for sub in node.Subsections:
            DatabaseCursor.execute("SELECT Count(1) FROM Text WHERE comment != '' AND ID >= {0} AND ID <= {1}".format(sub.Start, sub.End))
            count += int(DatabaseCursor.fetchall()[0][0])

    # type == -2 for comment count
    CompletionCursor.execute("SELECT Count(1) FROM StatusData WHERE database = ? AND type = -2", [databaseName])
    exists = CompletionCursor.fetchall()[0][0]
    if exists > 0:
        CompletionCursor.execute("UPDATE StatusData SET amount = ? WHERE database = ? AND type = -2", [count, databaseName])
    else:
        CompletionCursor.execute("INSERT INTO StatusData (database, type, amount) VALUES (?, -2, ?)", [databaseName, count])
    
    CompletionConnection.commit()

    Globals.Cache.databaseAccessRLock.release()

