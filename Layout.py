from ftplib import FTP
import os, struct
from PyQt4 import QtCore, QtGui


# Data structures and loops for Tales of Graces Layout files




class Layouts(QtGui.QWidget):
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
        
    
        self.window = QtGui.QScrollArea()
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.window)
        self.setLayout(layout)
    
    
    class StringWidget(QtGui.QWidget):
        def __init__(self, CurrentLayout, parent=None):    
            super(QtGui.QWidget, self).__init__(parent)
        
        
            layout = QtGui.QVBoxLayout()
            strbox = []
        
            i = 0
            for stringClass in CurrentLayout.strings:
                
                strbox.append(QtGui.QLineEdit())
                layout.addWidget(QtGui.QLabel(stringClass.name + ':'))
                layout.addWidget(strbox[i])
                
                strbox[i].setText(stringClass.string)
                strbox[i].setMaxLength(64)
                strbox[i].setMinimumWidth(600)
                
                def updateClass(text):
                    index = strbox.index(self.focusWidget())

                    CurrentLayout.strings[index].string = unicode(text)
                    
                strbox[i].textEdited.connect(updateClass)
                
                i += 1
                
            self.setLayout(layout)


    def LocalOpen(self):
        fn = QtGui.QFileDialog.getOpenFileName(self, 'Choose a layout file', 'llayout.bin', 'ToG Layout File (*.bin);;All Files(*)')
        if fn == '': return
        filename = str(fn)
    
        file = open(filename, 'rb')
        data = file.read()
        file.close()
    
        self.CurrentLayout = ToGLayout(data)
    
        widget = self.StringWidget(self.CurrentLayout)
        self.window.setWidget(widget)
        
        
        
    def ServerOpen(self):

        dlg = self.ServerOpenDialog()
        
        if dlg.exec_() == QtGui.QDialog.Accepted:
        
            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")

            self.ftp.cwd('/')    
            self.ftp.cwd('/Layout')    

            e = open('temp', 'wb')
            self.ftp.retrbinary('RETR {0}'.format(dlg.Combo.currentText()), e.write)
            e.close()
            e = open('temp', 'rb')
            data = e.read()

            self.ftp.close()

            self.CurrentLayout = ToGLayout(data)
        
            widget = self.StringWidget(self.CurrentLayout)
            self.window.setWidget(widget)


    def LocalSave(self):
        return

    def SaveAs(self):
        if self.CurrentLayout == None:
            return
    
        fn = QtGui.QFileDialog.getSaveFileName(self, 'Choose a new filename', 'layout.bin', '.bin Files (*.bin)')
        if fn == '': return

        fn = str(fn)
        newfile = open(fn, 'wb')

        newfile.write(self.CurrentLayout.header.data)
        
        for item in self.CurrentLayout.panels:
            newfile.write(item.data)
            
        for item in self.CurrentLayout.strings:
            newfile.write(struct.pack('>64s', item.string.encode('SJISx0213', 'ignore')))
            newfile.write(item.data[64:])
            
        for item in self.CurrentLayout.names:
            newfile.write(item.data)

        newfile.close()
        
        
    def ServerSave(self):
        if self.CurrentLayout == None:
            return

        dlg = self.ServerSaveDialog()
        
        if dlg.exec_() == QtGui.QDialog.Accepted:


            newfile = open('temp', 'wb')
    
            newfile.write(self.CurrentLayout.header.data)
            
            for item in self.CurrentLayout.panels:
                newfile.write(item.data)
                
            for item in self.CurrentLayout.strings:
                newfile.write(struct.pack('>64s', item.string.encode('SJISx0213', 'ignore')))
                newfile.write(item.data[64:])
                
            for item in self.CurrentLayout.names:
                newfile.write(item.data)

            newfile.close()

            
            fnew = open('temp', 'r+b')
            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")
            self.ftp.cwd('/')    
            self.ftp.cwd('/Layout')    
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
            self.ftp.cwd('/Layout')    
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
    
            self.setWindowTitle("Open Layout Data from Server")



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
            self.ftp.cwd('/Layout')    
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
    
            self.setWindowTitle("Save Layout Data to Server")


        def addThing(self):
            self.Combo.addItem(self.edit.text())
            self.Combo.setCurrentIndex(self.Combo.count()-1)


class ToGLayout():
    def __init__(self, data):    
    
        offset = 0
        
        self.header = self.Header(data[offset:offset + 0x30])
        offset += 0x30    
        
        
        self.panels = []
        for num in xrange(self.header.panelCount):
            self.panels.append(self.Panel(data[offset:offset + 0x1C0]))
            offset += 0x1C0
    
    
        self.strings = []
        for num in xrange(self.header.stringCount):
            self.strings.append(self.String(data[offset:offset + 0x94]))
            offset += 0x94
    
        self.names = []
        rangeNum = self.header.pnameCount + self.header.pname2Count + self.header.pname3Count + self.header.pname4Count + self.header.pname5Count + self.header.pname6Count + self.header.pname7Count + self.header.pname8Count + self.header.pname9Count + self.header.pname10Count + self.header.snameCount + self.header.sname12Count + self.header.sname13Count + self.header.sname14Count + self.header.sname15Count + self.header.sname16Count + self.header.sname17Count + self.header.sname18Count + self.header.sname19Count + self.header.sname20Count

        for num in xrange(rangeNum):
            self.names.append(self.PanelName(data[offset:offset + 0xA4]))
            offset += 0xA4
            

    class Header():
        def __init__(self, data):

            t = struct.unpack('>f22H', data)
            
            self.data = data
            
            self.version = t[0]
            
            self.panelCount = t[1]
            self.stringCount = t[2]
            
            self.pnameCount = t[3]
            self.pname2Count = t[4]
            
            self.pname3Count = t[5]
            self.pname4Count = t[6]
            
            self.pname5Count = t[7]
            self.pname6Count = t[8]
            
            
            self.pname7Count = t[9]
            self.pname8Count = t[10]
            
            self.pname9Count = t[11]
            self.pname10Count = t[12]
            
            self.snameCount = t[13]
            self.sname12Count = t[14]
            
            self.sname13Count = t[15]
            self.sname14Count = t[16]
            
            
            self.sname15Count = t[17]
            self.sname16Count = t[18]
            
            self.sname17Count = t[19]
            self.sname18Count = t[20]
            
            self.sname19Count = t[21]
            self.sname20Count = t[22]
            
        
        
        
    class Panel(): # length 0x1C0 -- t[1]
        def __init__(self, data):
        
            self.data = data

        
    class String(): # length 0x94 -- t[2]
        def __init__(self, data):
        
            t = struct.unpack('>64s12B4f16x6f16s', data)
            
            self.data = data
            
            self.string = t[0].decode('SJISx0213', 'ignore')
            
            self.byteArray = t[1:12]
            self.floatArray = t[13:-2]
            
            self.name = t[-1].decode('SJISx0213', 'ignore')
            

    class PanelName(): # length 0xA4 -- t[3:12]
        def __init__(self, data):
        
            self.data = data


    class StringName(): # length 0xA4 -- t[13:22]
        def __init__(self, data):
        
            self.data = data
        
        
        
        