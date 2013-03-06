import struct, sys
from PyQt4 import QtCore, QtGui
from ftplib import FTP


# Data structures and loops for Tales of Graces Equipment and Inventory Data



class Items(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Layouts, self).__init__(parent)

        # Current Variables
        self.CurrentLayout = None
 

        # Toolbar
        parent.Toolbar.clear()

        parent.Toolbar.addAction('Open', self.LocalOpen)
        parent.Toolbar.addAction('Open from Server...', self.ServerOpen)
        parent.Toolbar.addAction('Save', self.SaveAs)
        parent.Toolbar.addAction('Save to Server', self.ServerSave)

#        parent.fileMenu.clear()

        parent.fileMenu.addAction('Open', self.LocalOpen, QtGui.QKeySequence('Ctrl-O'))
        parent.fileMenu.addAction('Open from Server...', self.ServerOpen, QtGui.QKeySequence('Ctrl-Shift-O'))
#        parent.fileMenu.addAction('Save', self.LocalSave, QtGui.QKeySequence('Ctrl-S'))
        parent.fileMenu.addAction('Save as...', self.SaveAs, QtGui.QKeySequence('Ctrl-S'))
        parent.fileMenu.addAction('Save to Server', self.ServerSave, QtGui.QKeySequence('Ctrl-Shift-S'))
        parent.fileMenu.addAction('Quit', quit, QtGui.QKeySequence('Ctrl-Q'))
        
    

        self.treeList = QtGui.QTreeWidget()
        
        
        
        
        
        
        
        
        layout = QtGui.QGridLayout()
        
        layout.addWidget(self.window)
        
        self.setLayout(layout)
    


    def LocalOpen(self):
        fn = QtGui.QFileDialog.getOpenFileName(self, 'Choose an item file', 'item.bin', 'ToG Item Data File (*.bin);;All Files(*)')
        if fn == '': return
        filename = str(fn)
    
        file = open(filename, 'rb')
        data = file.read()
        file.close()
    
#        self.CurrentLayout = ToGLayout(data)
#    
#        widget = self.StringWidget(self.CurrentLayout)
#        self.window.setWidget(widget)
        
        
        
    def ServerOpen(self):

        dlg = self.ServerOpenDialog()
        
        if dlg.exec_() == QtGui.QDialog.Accepted:
        
            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")

            self.ftp.cwd('/')    
            self.ftp.cwd('/Item')    

            e = open('temp', 'wb')
            self.ftp.retrbinary('RETR {0}'.format(dlg.Combo.currentText()), e.write)
            e.close()
            e = open('temp', 'rb')
            data = e.read()

            self.ftp.close()

#            self.CurrentLayout = ToGLayout(data)
#        
#            widget = self.StringWidget(self.CurrentLayout)
#            self.window.setWidget(widget)


    def LocalSave(self):
        return

    def SaveAs(self):
#        if self.CurrentLayout == None:
#            return
    
        fn = QtGui.QFileDialog.getSaveFileName(self, 'Choose a new filename', 'item.bin', 'ToG Item Data File (*.bin)')
        if fn == '': return

        fn = str(fn)
        newfile = open(fn, 'wb')

#        newfile.write(self.CurrentLayout.header.data)
#        
#        for item in self.CurrentLayout.panels:
#            newfile.write(item.data)
#            
#        for item in self.CurrentLayout.strings:
#            newfile.write(struct.pack('>64s', item.string.encode('SJISx0213', 'ignore')))
#            newfile.write(item.data[64:])
#            
#        for item in self.CurrentLayout.names:
#            newfile.write(item.data)

        newfile.close()
        
        
    def ServerSave(self):
        if self.CurrentLayout == None:
            return

        dlg = self.ServerSaveDialog()
        
        if dlg.exec_() == QtGui.QDialog.Accepted:


            newfile = open('temp', 'wb')
    
#            newfile.write(self.CurrentLayout.header.data)
#            
#            for item in self.CurrentLayout.panels:
#                newfile.write(item.data)
#                
#            for item in self.CurrentLayout.strings:
#                newfile.write(struct.pack('>64s', item.string.encode('SJISx0213', 'ignore')))
#                newfile.write(item.data[64:])
#                
#            for item in self.CurrentLayout.names:
#                newfile.write(item.data)

            newfile.close()

            
            fnew = open('temp', 'r+b')
            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")
            self.ftp.cwd('/')    
            self.ftp.cwd('/Item')    
            self.ftp.storbinary('STOR {0}'.format(dlg.Combo.currentText()), fnew)
            self.ftp.close()
            fnew.close()
    

    class ServerOpenDialog(QtGui.QDialog):
        def __init__(self, parent=None):
            super(QtGui.QDialog, self).__init__(parent)
        
            self.Combo = QtGui.QComboBox()
    
            buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)

            buttonBox.accepted.connect(self.accept)
            buttonBox.rejected.connect(self.reject)
    
            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")
    
            self.ftp.cwd('/')    
            self.ftp.cwd('/Item')    
            comboList = self.ftp.nlst()
            self.ftp.close()
            comboList.pop(0)
            comboList.pop(0)

            for item in comboList:
                self.Combo.addItem(item)
            
                        
            mainLayout = QtGui.QVBoxLayout()
            mainLayout.addWidget(self.Combo)
            mainLayout.addWidget(buttonBox)
            self.setLayout(mainLayout)
    
            self.setWindowTitle("Open Item Data from Server")



    class ServerSaveDialog(QtGui.QDialog):
        def __init__(self, parent=None):
            super(QtGui.QDialog, self).__init__(parent)
    
            self.Combo = QtGui.QComboBox()
            label = QtGui.QLabel('Add New File:')
            self.edit = QtGui.QLineEdit()
            button = QtGui.QPushButton('New')

            button.released.connect(self.addThing)
            buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
    
            buttonBox.accepted.connect(self.accept)
            buttonBox.rejected.connect(self.reject)

            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")
    
            self.ftp.cwd('/')    
            self.ftp.cwd('/Item')    
            comboList = self.ftp.nlst()
            self.ftp.close()
            comboList.pop(0)
            comboList.pop(0)

            for item in comboList:
                self.Combo.addItem(item)            
                        
            minorLayout = QtGui.QHBoxLayout()
            minorLayout.addWidget(self.edit)
            minorLayout.addWidget(button)
            
            mainLayout = QtGui.QVBoxLayout()
            mainLayout.addWidget(self.Combo)
            mainLayout.addWidget(label)
            mainLayout.addLayout(minorLayout)
            mainLayout.addWidget(buttonBox)
            self.setLayout(mainLayout)
    
            self.setWindowTitle("Save Item Data to Server")


        def addThing(self):
            self.Combo.addItem(self.edit.text())
            self.Combo.setCurrentIndex(self.Combo.count()-1)





class Consumables():
    def __init__(self, data):    

        self.data = data

        t = struct.unpack('>IIIHHHHBBBBBBBBIHH', data[offset:offset + 0x24])

        self.pname = t[0]
        self.pdescription = t[1]

        self.name = ''
        self.description = ''
        
        self.price = t[2]
        
        self.dualizeA = t[3]
        self.dualizeB = t[4]
        self.duallizeCost = t[5]
        
        self.COunkA = t[6]
        
        self.bitfA = bf(t[7])
        self.quality = t[8]
        
        self.category = t[9]
        self.aclass = t[10]
        
        self.bitfB = bf(t[11])
        self.bitfC = bf(t[12])
        self.COunkB = t[13]
       
        self.foodGroup = t[14]
        
        self.firstEffect = t[15]        
        self.secondEffect = t[16]
        self.thirdEffect = t[17]
        

class Materials():
    def __init__(self, data):    

        self.data = data

        t = struct.unpack('>IIIHHHHBBBBBBBBIHH', data[offset:offset + 0x24])

        self.pname = t[0]
        self.pdescription = t[1]

        self.name = ''
        self.description = ''
        
        self.price = t[2]
        
        self.dualizeA = t[3]
        self.dualizeB = t[4]
        self.duallizeCost = t[5]
        
        self.MAunkA = t[6]
        
        self.bitfA = bf(t[7])
        self.quality = t[8]
        
        self.category = t[9]
        self.aclass = t[10]
        
        self.bitfB = bf(t[11])
        self.bitfC = bf(t[12])
        self.MAunkB = t[13]
       
        self.foodGroup = t[14]
        
        self.firstEffect = t[15]        
        self.secondEffect = t[16]
        self.thirdEffect = t[17]


class Fragments():
    def __init__(self, data):    

        self.data = data
        
        t = struct.unpack('>IIIHHHHBBBBHH', data[offset:offset + 0x1C])

        self.pname = t[0]
        self.pdescription = t[1]

        self.name = ''
        self.description = ''
        
        self.price = t[2]
        
        self.dualizeA = t[3]
        self.dualizeB = t[4]
        self.duallizeCost = t[5]
        
        self.FRunkA = t[6]
        self.bitfA = bf(t[7])
        self.quality = t[8]
        
        self.category = t[9]
        self.aclass = t[10]
        
        self.fragmentType = t[11]
        self.FRunkB = t[12]
       

class Equipment():
    def __init__(self, data):    

        self.data = data

        t = struct.unpack('>IIIHH2H4B2HH2B4B2B2B', data[offset:offset + 0x28])

        self.pname = t[0]
        self.pdescription = t[1]

        self.name = ''
        self.description = ''
        
        self.price = t[2]
        
        self.dualizeA = t[3]
        self.dualizeB = t[4]
        self.duallizeCost = t[5]
        
        self.EQunkA = t[6]
        self.EQunkB = t[7]
        self.EQunkC = t[8]
        
        self.category = t[9]
        self.aclass = t[10]
        
        self.physStat = t[11]
        self.techStat = t[12]
        self.accStat = t[13]
        
        self.ccmin = t[14]
        self.ccmax = t[15]
        
        self.specialEffect = t[16]
        self.effectQuantity = t[17]
        
        self.EQunkD = t[18]
        
        self.property = t[19]
        self.model = t[20]
        
        self.rank = t[21]

        self.EQunkE = t[22]
        self.EQunkF = t[23]


class CategoryE():
    def __init__(self, data):    

        self.data = data

class CategoryF():
    def __init__(self, data):    

        self.data = data

class CategoryG():
    def __init__(self, data):    

        self.data = data

class CategoryH():
    def __init__(self, data):    

        self.data = data




class ItemItem(QtGui.QTreeWidgetItem):
    def __init__(self, aclass, data, parent=None):
        super(QtGui.QDialog, self).__init__(parent)

        self.itemClass = aclass(data)



class bf(object):
    def __init__(self,value=0):
        self._d = value

    def __getitem__(self, index):
        return (self._d >> index) & 1 

    def __setitem__(self,index,value):
        value    = (value&1L)<<index
        mask     = (1L)<<index
        self._d  = (self._d & ~mask) | value

    def __getslice__(self, start, end):
        mask = 2L**(end - start) -1
        return (self._d >> start) & mask

    def __setslice__(self, start, end, value):
        mask = 2L**(end - start) -1
        value = (value & mask) << start
        mask = mask << start
        self._d = (self._d & ~mask) | value
        return (self._d >> start) & mask

    def __int__(self):
        return self._d



Categories = []

Classes = ['Recovery', 'Status', 'Food', 'Stat Increasing', 'Holy/Dark Bottle']