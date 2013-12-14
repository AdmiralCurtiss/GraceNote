# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import os
import sqlite3
import DatabaseHandler

class CompletionTable(QtGui.QDialog):

    def __init__(self, parent):
        super(CompletionTable, self).__init__()
        self.setWindowIcon(QtGui.QIcon('icons/completion.png'))

        self.parent = parent
        self.setWindowModality(False)        

        self.treewidget = QtGui.QTreeWidget()
        
        self.treewidget.setColumnCount(6)
        self.treewidget.setHeaderLabels(['Name', 'Translation', 'Editing 1', 'Editing 2', 'Editing 3', 'Comments'])
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 200)
        self.treewidget.setColumnWidth(1, 150)
        self.treewidget.setColumnWidth(2, 150)
        self.treewidget.setColumnWidth(3, 150)
        self.treewidget.setColumnWidth(4, 150)
        
        self.treewidget.setMinimumSize(620, 500)

        subLayout = QtGui.QVBoxLayout()
        subLayout.addWidget(self.treewidget)
        self.setLayout(subLayout)

        self.treewidget.itemDoubleClicked.connect(self.JumpToFile)

        progress = QtGui.QProgressDialog("Calculating percentages...", "Abort", 0, len(os.listdir(Globals.configData.LocalDatabasePath))+1)
        progress.setWindowModality(QtCore.Qt.WindowModal)

        bigTotal = 0
        bigTrans = 0

        i = 1
        aList = Globals.configData.FileList
            
            
        tempCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/CompletionPercentage')
        tempCur = tempCon.cursor()
            
        for item in aList[0]:
                        
            cat = QtGui.QTreeWidgetItem(self.treewidget, [item, '-', '-', '-', '-', '-'])
            
            catTotalDB = 0
            catTrans = 0
            catTlCheck = 0
            catRewrite = 0
            catGrammar = 0
            catTotalComments = 0
            
            for item in aList[i]:                
                try:
                    tempCur.execute("SELECT entries, translation, editing1, editing2, editing3, comments FROM Percentages WHERE Database = ?", [item])
                except:
                    CalculateCompletionForDatabase(item)
                    tempCur.execute("SELECT entries, translation, editing1, editing2, editing3, comments FROM Percentages WHERE Database = ?", [item])
                rows = tempCur.fetchall()
                totalDB = rows[0][0]
                translated = rows[0][1]
                tlCheck = rows[0][2]
                rewrite = rows[0][3]
                grammar = rows[0][4]
                commentamount = rows[0][5]
                    
                catTotalDB += totalDB
                catTotalComments += commentamount
                catTrans += translated
                catTlCheck += tlCheck
                catRewrite += rewrite
                catGrammar += grammar

                if totalDB != 0:
                    translationPercent = '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(translated)/float(totalDB)*100, translated, totalDB)
                    tlCheckPercent = '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(tlCheck)/float(totalDB)*100, tlCheck, totalDB)
                    rewritePercent = '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(rewrite)/float(totalDB)*100, rewrite, totalDB)
                    grammarPercent = '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(grammar)/float(totalDB)*100, grammar, totalDB)
                else:
                    translationPercent = 'N/A'
                    tlCheckPercent = 'N/A'
                    rewritePercent = 'N/A'
                    grammarPercent = 'N/A'
                    
                newrow = QtGui.QTreeWidgetItem(cat, [item, translationPercent, tlCheckPercent, rewritePercent, grammarPercent, '{0}'.format(commentamount)])
                    
                progress.setValue(progress.value() + 1)
    
            cat.setData(1, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(catTrans)/float(catTotalDB)*100, catTrans, catTotalDB))
            cat.setData(2, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(catTlCheck)/float(catTotalDB)*100, catTlCheck, catTotalDB))
            cat.setData(3, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(catRewrite)/float(catTotalDB)*100, catRewrite, catTotalDB)) 
            cat.setData(4, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(catGrammar)/float(catTotalDB)*100, catGrammar, catTotalDB))
            cat.setData(5, 0, '{0}'.format(catTotalComments))
            
            bigTotal += catTotalDB
            bigTrans += catTrans           
                
            i = i + 1

        self.treewidget.sortItems(0, 1)
        progress.setValue(len(os.listdir(Globals.configData.LocalDatabasePath))+1)
        
        
        geom = Globals.Settings.value('Geometry/CompletionTable')
        if geom is not None:
            self.restoreGeometry(geom)

        self.setWindowTitle('Current Phase: Translation, at {0:.2f}% completion'.format(float(bigTrans)/float(bigTotal)*100))

    def JumpToFile(self, item, column):
        if item.childCount() > 0:
            return

        databaseName = item.data(0, 0)
        self.parent.JumpToEntry(databaseName, 1)

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/CompletionTable', self.saveGeometry())

def CalculateAllCompletionPercentagesForDatabase():
    aList = Globals.configData.FileList
    
    for i in range(len(aList)-1):
        for item in aList[i+1]:
            CalculateCompletionForDatabase(item)

def CalculateCompletionForDatabase(database):
    #print 'Calculating percentages for ' + database + '...'
    
    Globals.Cache.databaseAccessRLock.acquire()

    tempCon = DatabaseHandler.OpenEntryDatabase(database)
    tempCur = tempCon.cursor()
    
    tempCur.execute("SELECT Count(1) from Text where status>=0")
    totalDB = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) from Text where status>=1")
    translated = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) from Text where status>=2")
    tlCheck = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) from Text where status>=3")
    rewrite = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) from Text where status>=4")
    grammar = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) FROM Text WHERE comment != ''")
    commentAmount = tempCur.fetchall()[0][0]
    
    tempCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/CompletionPercentage')
    tempCur = tempCon.cursor()
    
    tempCur.execute("SELECT Count(1) FROM Percentages WHERE Database = ?", [database])
    exists = tempCur.fetchall()[0][0]
    
    if exists > 0:
        tempCur.execute("UPDATE Percentages SET entries = ?, translation = ?, editing1 = ?, editing2 = ?, editing3 = ?, comments = ? WHERE Database = ?", [totalDB, translated, tlCheck, rewrite, grammar, commentAmount, database])
    else:
        tempCur.execute("INSERT INTO Percentages (entries, translation, editing1, editing2, editing3, comments, Database) VALUES (?, ?, ?, ?, ?, ?, ?)", [totalDB, translated, tlCheck, rewrite, grammar, commentAmount, database])
    tempCon.commit()

    Globals.Cache.databaseAccessRLock.release()

