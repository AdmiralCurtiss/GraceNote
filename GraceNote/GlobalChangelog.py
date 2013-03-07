from PyQt4 import QtCore, QtGui
import Globals

class GlobalChangelog(QtGui.QDialog):

    def __init__(self, parent):
        super(GlobalChangelog, self).__init__()

        self.parent = parent
        
        self.setWindowModality(False)        
        self.treewidget = QtGui.QTreeWidget()
        
        self.treewidget.setColumnCount(3)
        self.treewidget.setHeaderLabels(['Date', 'Name', 'File'])
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 200)
        self.treewidget.setColumnWidth(1, 100)
        self.treewidget.setColumnWidth(2, 80)
        
        self.treewidget.setMinimumSize(450, 600)
        
        Globals.LogCur.execute("SELECT * FROM Log ORDER BY Timestamp DESC")
        templist = Globals.LogCur.fetchall()
        #templist.pop(0)
        for entry in templist:
            for filename in entry[1].split(','):
                self.treewidget.addTopLevelItem(QtGui.QTreeWidgetItem(['{0}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry[3]))), '{0}'.format(entry[2]), '{0}'.format(filename)]))
        
        self.treewidget.itemDoubleClicked.connect(self.JumpToFile)

        self.setWindowTitle('Global Changelog')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Recent Changes:'))
        layout.addWidget(self.treewidget)
        self.setLayout(layout)

    def JumpToFile(self, item, column):
        file = item.data(2, 0)
        self.parent.JumpToEntry(file, 1)

