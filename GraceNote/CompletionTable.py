from PyQt4 import QtCore, QtGui
import Globals

class CompletionTable(QtGui.QDialog):

    def __init__(self, parent):
        super(CompletionTable, self).__init__()


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
                    rows = tempCur.fetchall()
                    totalDB = rows[0][0]
                    translated = rows[0][1]
                    tlCheck = rows[0][2]
                    rewrite = rows[0][3]
                    grammar = rows[0][4]
                    commentamount = rows[0][5]
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
        
        
        self.setWindowTitle('Current Phase: Translation, at {0:.2f}% completion'.format(float(bigTrans)/float(bigTotal)*100))

    def JumpToFile(self, item, column):
        if item.childCount() > 0:
            return

        file = item.data(0, 0)
        self.parent.JumpToEntry(file, 1)

