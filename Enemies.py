from PyQt4 import QtCore, QtGui
from ftplib import FTP
import struct

fileStruct = '>24s 2I 6f 16H 2I 2H 4h 3f 4H 2I'

# Str- ---- ---- ----
# Str- ---- Int- Int-
# Flot Flot Flot Flot
# Flot Flot StSt StSt
# StSt StSt StSt StSt
# StSt StSt Int- Int-
# StSt CCSt Int- Flot
# Flot Flot StSt StSt
# Int- Int-


class Enemies(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Enemies, self).__init__(parent)

        # Current Variables
        self.entrylist = []
 

        # Toolbar
        parent.Toolbar.clear()

        parent.Toolbar.addAction('Open', self.LocalOpen)
        parent.Toolbar.addAction('Open from Server...', self.ServerOpen)
        parent.Toolbar.addAction('Save', self.SaveAs)
        parent.Toolbar.addAction('Save to Server', self.ServerSave)

        parent.fileMenu.clear()

        parent.fileMenu.addAction('Open', self.LocalOpen, QtGui.QKeySequence('Ctrl-O'))
        parent.fileMenu.addAction('Open from Server...', self.ServerOpen, QtGui.QKeySequence('Ctrl-Shift-O'))
#        parent.fileMenu.addAction('Save', self.LocalSave, QtGui.QKeySequence('Ctrl-S'))
        parent.fileMenu.addAction('Save as...', self.SaveAs, QtGui.QKeySequence('Ctrl-S'))
        parent.fileMenu.addAction('Save to Server', self.ServerSave, QtGui.QKeySequence('Ctrl-Shift-S'))
        parent.fileMenu.addAction('Quit', quit, QtGui.QKeySequence('Ctrl-Q'))
        
    
     
        # List View of Files
        self.EnemyList = QtGui.QListWidget()

        self.EnemyList.setSortingEnabled(False)
        self.EnemyList.setFixedWidth(180)
 
#        self.UnpackEnemyList()
        
        # GUI Elements
        # Use Tooltips to show hex values, maybe?
        self.name = QtGui.QLineEdit()
        self.name.setMaxLength(24)

        self.HP = QtGui.QSpinBox()
        self.HP.setRange(0, 16777215)
        self.EXP = QtGui.QSpinBox()
        self.EXP.setRange(0, 16777215)
        self.level = QtGui.QSpinBox()
        self.level.setRange(0, 65535)
        self.gald = QtGui.QSpinBox()
        self.gald.setRange(0, 65535)
        self.SP = QtGui.QSpinBox()
        self.SP.setRange(0, 65535)
        self.att = QtGui.QSpinBox()
        self.att.setRange(0, 65535)
        self.matt = QtGui.QSpinBox()
        self.matt.setRange(0, 65535)
        self.acc = QtGui.QSpinBox()
        self.acc.setRange(0, 65535)
        self.dfn = QtGui.QSpinBox()
        self.dfn.setRange(0, 65535)
        self.mdef = QtGui.QSpinBox()
        self.mdef.setRange(0, 65535)
        self.eva = QtGui.QSpinBox()
        self.eva.setRange(0, 65535)
        self.unknownA = QtGui.QSpinBox()
        self.unknownA.setRange(0, 65535)

        self.dropA = QtGui.QComboBox()
        self.dropA.addItem("-------")
        self.dropArate = QtGui.QSpinBox()
        self.dropArate.setSuffix(" %")
        self.dropB = QtGui.QComboBox()
        self.dropB.addItem("-------")
        self.dropBrate = QtGui.QSpinBox()
        self.dropBrate.setSuffix(" %")
        self.steal = QtGui.QComboBox()
        self.steal.addItem("-------")
        self.stealRate = QtGui.QSpinBox()
        self.stealRate.setSuffix(" %")
        
        # Flags represented as QCheckboxes
        self.wAa = QtGui.QCheckBox("") #0x00000001
        self.wAb = QtGui.QCheckBox("") #0x00000002
        self.wAc = QtGui.QCheckBox("") #0x00000004
        self.wAd = QtGui.QCheckBox("") #0x00000008
        
        self.wAe = QtGui.QCheckBox("Lizard") #0x0000001
        self.wAf = QtGui.QCheckBox("") #0x0000002
        self.wAg = QtGui.QCheckBox("Beast") #0x0000004
        self.wAh = QtGui.QCheckBox("") #0x0000008

        self.wBa = QtGui.QCheckBox("Dragon") #0x000001
        self.wBb = QtGui.QCheckBox("") #0x000002
        self.wBc = QtGui.QCheckBox("") #0x000004
        self.wBd = QtGui.QCheckBox("") #0x000008
        
        self.wBe = QtGui.QCheckBox("") #0x00001
        self.wBf = QtGui.QCheckBox("") #0x00002
        self.wBg = QtGui.QCheckBox("Chaos") #0x00004
        self.wBh = QtGui.QCheckBox("") #0x00008

        self.wCa = QtGui.QCheckBox("Freeze/Blow?") #0x0001
        self.wCb = QtGui.QCheckBox("") #0x0002
        self.wCc = QtGui.QCheckBox("Shoot") #0x0004
        self.wCd = QtGui.QCheckBox("") #0x0008
        
        self.wCe = QtGui.QCheckBox("") #0x001
        self.wCf = QtGui.QCheckBox("") #0x002
        self.wCg = QtGui.QCheckBox("Freeze/Blow?") #0x004
        self.wCh = QtGui.QCheckBox("") #0x008

        self.wDa = QtGui.QCheckBox("Stone") #0x01
        self.wDb = QtGui.QCheckBox("") #0x02
        self.wDc = QtGui.QCheckBox("Seal") #0x04
        self.wDd = QtGui.QCheckBox("") #0x08
        
        self.wDe = QtGui.QCheckBox("") #0x1
        self.wDf = QtGui.QCheckBox("") #0x2
        self.wDg = QtGui.QCheckBox("") #0x4
        self.wDh = QtGui.QCheckBox("") #0x8

        
        self.species = QtGui.QLabel()
        self.unknownB = QtGui.QSpinBox()
        self.unknownB.setRange(0, 16777215)

        # Unknown Stuff
        self.sizefloatA = QtGui.QDoubleSpinBox()
        self.sizefloatA.setMaximum(512)
        self.sizefloatA.setDecimals(3)
        self.sizefloatB = QtGui.QDoubleSpinBox()
        self.sizefloatB.setMaximum(512)
        self.sizefloatB.setDecimals(3)
        self.sizefloatC = QtGui.QDoubleSpinBox()
        self.sizefloatC.setMaximum(512)
        self.sizefloatC.setDecimals(3)
        self.sizefloatD = QtGui.QDoubleSpinBox()
        self.sizefloatD.setMaximum(512)
        self.sizefloatD.setDecimals(3)
        self.sizefloatE = QtGui.QDoubleSpinBox()
        self.sizefloatE.setMaximum(512)
        self.sizefloatE.setDecimals(3)
        self.sizefloatF = QtGui.QDoubleSpinBox()
        self.sizefloatF.setMaximum(512)
        self.sizefloatF.setDecimals(3)

            # These are probably actually shorts
        self.unkShortA = QtGui.QSpinBox()
        self.unkShortA.setRange(-65525, 65535)
        self.unkShortB = QtGui.QSpinBox()
        self.unkShortB.setRange(-65525, 65535)
        self.unkShortC = QtGui.QSpinBox()
        self.unkShortC.setRange(-65525, 65535)
        self.unkShortD = QtGui.QSpinBox()
        self.unkShortD.setRange(-65525, 65535)
        
            # Floats
        self.walkSpeed = QtGui.QDoubleSpinBox()
        self.walkSpeed.setDecimals(3)
        self.chaseSpeed = QtGui.QDoubleSpinBox()
        self.chaseSpeed.setDecimals(3)
        self.mapScale = QtGui.QDoubleSpinBox()
        self.mapScale.setDecimals(3)
        
            # Shorts
        self.walkTime = QtGui.QSpinBox()
        self.walkTime.setRange(0, 16777215)
        self.stayTime = QtGui.QSpinBox()
        self.stayTime.setRange(0, 16777215)
        self.unknownK = QtGui.QSpinBox()
        self.unknownK.setRange(0, 16777215)
        self.findAngle = QtGui.QSpinBox()
        self.findAngle.setRange(0, 16777215)
        
            # Ints (actually, probably more shorts)
        self.unknownM = QtGui.QSpinBox()
        self.unknownM.setRange(0, 16777215)
        self.unknownN = QtGui.QSpinBox()
        self.unknownN.setRange(0, 16777215)



        # Connections
        self.EnemyList.itemSelectionChanged.connect(self.DisplayMon)


        self.name.textEdited.connect(self.nameChange)
        self.HP.valueChanged.connect(self.HPChange)
        self.EXP.valueChanged.connect(self.EXPChange)
        self.sizefloatA.valueChanged.connect(self.sizefloatAChange)
        self.sizefloatB.valueChanged.connect(self.sizefloatBChange)
        self.sizefloatC.valueChanged.connect(self.sizefloatCChange)
        self.sizefloatD.valueChanged.connect(self.sizefloatDChange)
        self.sizefloatE.valueChanged.connect(self.sizefloatEChange)
        self.sizefloatF.valueChanged.connect(self.sizefloatFChange)
        self.level.valueChanged.connect(self.levelChange)
        self.gald.valueChanged.connect(self.galdChange)
        self.SP.valueChanged.connect(self.SPChange)
        self.att.valueChanged.connect(self.attChange)
        self.matt.valueChanged.connect(self.mattChange)
        self.acc.valueChanged.connect(self.accChange)
        self.dfn.valueChanged.connect(self.dfnChange)
        self.mdef.valueChanged.connect(self.mdefChange)
        self.eva.valueChanged.connect(self.evaChange)
        self.unknownA.valueChanged.connect(self.unknownAChange)
#        self.dropA.currentIndexChanged.connect(self.dropAChange)
        self.dropArate.valueChanged.connect(self.dropArateChange)
#        self.dropB.currentIndexChanged.connect(self.dropBChange)
        self.dropBrate.valueChanged.connect(self.dropBrateChange)
#        self.steal.currentIndexChanged.connect(self.stealChange)
        self.stealRate.valueChanged.connect(self.stealRateChange)
        self.unknownB.valueChanged.connect(self.unknownBChange)
#        self.species.currentIndexChanged.connect(self.speciesChange)
#        self.unknownC.valueChanged.connect(self.unknownCChange)
        self.unkShortA.valueChanged.connect(self.unkShortAChange)
        self.unkShortB.valueChanged.connect(self.unkShortBChange)
        self.unkShortC.valueChanged.connect(self.unkShortCChange)
        self.unkShortD.valueChanged.connect(self.unkShortDChange)
        self.walkSpeed.valueChanged.connect(self.walkSpeedChange)
        self.chaseSpeed.valueChanged.connect(self.chaseSpeedChange)
        self.mapScale.valueChanged.connect(self.mapScaleChange)
        self.walkTime.valueChanged.connect(self.walkTimeChange)
        self.stayTime.valueChanged.connect(self.stayTimeChange)
        self.unknownK.valueChanged.connect(self.unknownKChange)
        self.findAngle.valueChanged.connect(self.findAngleChange)
        self.unknownM.valueChanged.connect(self.unknownMChange)
        self.unknownN.valueChanged.connect(self.unknownNChange)


        self.wAa.stateChanged.connect(self.wAaChange)
        self.wAb.stateChanged.connect(self.wAbChange)
        self.wAc.stateChanged.connect(self.wAcChange)
        self.wAd.stateChanged.connect(self.wAdChange)
        self.wAe.stateChanged.connect(self.wAeChange)
        self.wAf.stateChanged.connect(self.wAfChange)
        self.wAg.stateChanged.connect(self.wAgChange)
        self.wAh.stateChanged.connect(self.wAhChange)
        self.wBa.stateChanged.connect(self.wBaChange)
        self.wBb.stateChanged.connect(self.wBbChange)
        self.wBc.stateChanged.connect(self.wBcChange)
        self.wBd.stateChanged.connect(self.wBdChange)
        self.wBe.stateChanged.connect(self.wBeChange)
        self.wBf.stateChanged.connect(self.wBfChange)
        self.wBg.stateChanged.connect(self.wBgChange)
        self.wBh.stateChanged.connect(self.wBhChange)
        self.wCa.stateChanged.connect(self.wCaChange)
        self.wCb.stateChanged.connect(self.wCbChange)
        self.wCc.stateChanged.connect(self.wCcChange)
        self.wCd.stateChanged.connect(self.wCdChange)
        self.wCe.stateChanged.connect(self.wCeChange)
        self.wCf.stateChanged.connect(self.wCfChange)
        self.wCg.stateChanged.connect(self.wCgChange)
        self.wCh.stateChanged.connect(self.wChChange)
        self.wDa.stateChanged.connect(self.wDaChange)
        self.wDb.stateChanged.connect(self.wDbChange)
        self.wDc.stateChanged.connect(self.wDcChange)
        self.wDd.stateChanged.connect(self.wDdChange)
        self.wDe.stateChanged.connect(self.wDeChange)
        self.wDf.stateChanged.connect(self.wDfChange)
        self.wDg.stateChanged.connect(self.wDgChange)
        self.wDh.stateChanged.connect(self.wDhChange)



        #    Layouts:
        # Stats
        statsLayout = QtGui.QFormLayout()
        statsLayout.addRow("Lv.:", self.level)
        statsLayout.addRow("HP:", self.HP)
        statsLayout.addRow("SP:", self.SP)
        statsLayout.addRow("Att:", self.att)
        statsLayout.addRow("Def:", self.dfn)
        statsLayout.addRow("M.Att:", self.matt)
        statsLayout.addRow("M.Def:", self.mdef)
        statsLayout.addRow("Acc:", self.acc)
        statsLayout.addRow("Eva:", self.eva)
        statsLayout.addRow("???:", self.unknownA)
        statsBox = QtGui.QGroupBox()
        statsBox.setTitle("Statistics")
        statsBox.setLayout(statsLayout)
        
        # Name
        nameLayout = QtGui.QFormLayout()
        nameLayout.addRow("Name:", self.name)
        
        # Item
        itemLayout = QtGui.QGridLayout()
        
        itemLayout.addWidget(QtGui.QLabel("Common Drop:"), 0, 0)
        itemLayout.addWidget(QtGui.QLabel("Rare Drop:"), 1, 0)
        itemLayout.addWidget(QtGui.QLabel("Steal Item:"), 2, 0)
        
        itemLayout.addWidget(self.dropA, 0, 1)
        itemLayout.addWidget(self.dropB, 1, 1)
        itemLayout.addWidget(self.steal, 2, 1)
        
        # Rate
        itemLayout.addWidget(self.dropArate, 0, 2)
        itemLayout.addWidget(self.dropBrate, 1, 2)
        itemLayout.addWidget(self.stealRate, 2, 2)


        dropBox = QtGui.QGroupBox()
        dropBox.setTitle("Drops")
        dropBox.setLayout(itemLayout)


        # Spoils
        spoilLayout = QtGui.QFormLayout()
        spoilLayout.addRow("EXP:", self.EXP)
        spoilLayout.addRow("Gald:", self.gald)
        
        spoilBox = QtGui.QGroupBox()
        spoilBox.setTitle("Spoils")
        spoilBox.setLayout(spoilLayout)

        
        # Sizes
        sizeLayout = QtGui.QFormLayout()
        sizeLayout.addRow("Scale:", self.sizefloatA)
        sizeLayout.addRow("?:", self.sizefloatB)
        sizeLayout.addRow("?:", self.sizefloatC)
        sizeLayout.addRow("?:", self.sizefloatD)
        sizeLayout.addRow("?:", self.sizefloatE)
        sizeLayout.addRow("?:", self.sizefloatF)

        sizeBox = QtGui.QGroupBox()
        sizeBox.setTitle("Battle Model")
        sizeBox.setLayout(sizeLayout)
        
        # Species
        sLayout = QtGui.QFormLayout()
        sLayout.addRow("Species:", self.species)
        sLayout.addRow("?:", self.unknownB)

        # Weaknesses
        weakLayout = QtGui.QGridLayout()
        weakLayout.addWidget(self.wAa, 0, 0)
        weakLayout.addWidget(self.wAb, 0, 1)
        weakLayout.addWidget(self.wAc, 0, 2)
        weakLayout.addWidget(self.wAd, 0, 3)
        weakLayout.addWidget(self.wAe, 0, 4)
        weakLayout.addWidget(self.wAf, 0, 5)
        weakLayout.addWidget(self.wAg, 0, 6)
        weakLayout.addWidget(self.wAh, 0, 7)

        weakLayout.addWidget(self.wBa, 1, 0)
        weakLayout.addWidget(self.wBb, 1, 1)
        weakLayout.addWidget(self.wBc, 1, 2)
        weakLayout.addWidget(self.wBd, 1, 3)
        weakLayout.addWidget(self.wBe, 1, 4)
        weakLayout.addWidget(self.wBf, 1, 5)
        weakLayout.addWidget(self.wBg, 1, 6)
        weakLayout.addWidget(self.wBh, 1, 7)

        weakLayout.addWidget(self.wCa, 2, 0)
        weakLayout.addWidget(self.wCb, 2, 1)
        weakLayout.addWidget(self.wCc, 2, 2)
        weakLayout.addWidget(self.wCd, 2, 3)
        weakLayout.addWidget(self.wCe, 2, 4)
        weakLayout.addWidget(self.wCf, 2, 5)
        weakLayout.addWidget(self.wCg, 2, 6)
        weakLayout.addWidget(self.wCh, 2, 7)

        weakLayout.addWidget(self.wDa, 3, 0)
        weakLayout.addWidget(self.wDb, 3, 1)
        weakLayout.addWidget(self.wDc, 3, 2)
        weakLayout.addWidget(self.wDd, 3, 3)
        weakLayout.addWidget(self.wDe, 3, 4)
        weakLayout.addWidget(self.wDf, 3, 5)
        weakLayout.addWidget(self.wDg, 3, 6)
        weakLayout.addWidget(self.wDh, 3, 7)
        
        weakBox = QtGui.QGroupBox()
        weakBox.setTitle("Weaknesses")
        weakBox.setLayout(weakLayout)
       
                
        # Unknown Junk
        uLayout = QtGui.QFormLayout()
        uLayout.addRow(QtGui.QLabel("Unknown Signed Shorts"))
        uLayout.addRow("?:", self.unkShortA)
        uLayout.addRow("?:", self.unkShortB)
        uLayout.addRow("?:", self.unkShortC)
        uLayout.addRow("?:", self.unkShortD)

        uBox = QtGui.QGroupBox()
        uBox.setTitle("Unknowns")
        uBox.setLayout(uLayout)


        # Map Properties
        uLayout = QtGui.QFormLayout()
        
        uLayout.addRow("Walk Speed:", self.walkSpeed)
        uLayout.addRow("Chase Speed:", self.chaseSpeed)
        uLayout.addRow("Scale:", self.mapScale)

        MapBox = QtGui.QGroupBox()
        MapBox.setTitle("Map Properties")
        MapBox.setLayout(uLayout)


        # Map Behaviour
        uLayout = QtGui.QFormLayout()

        uLayout.addRow("Walk Time:", self.walkTime)
        uLayout.addRow("Stay Time:", self.stayTime)
        uLayout.addRow("Byte(Walk Radius), Nybble(Find Distance), Padding?:", self.unknownK)
        uLayout.addRow("Search Angle:", self.findAngle)

        BehBox = QtGui.QGroupBox()
        BehBox.setTitle("Map Behaviour")
        BehBox.setLayout(uLayout)


        # Chasing Behaviour
        uLayout = QtGui.QFormLayout()

        uLayout.addRow(QtGui.QLabel("Unknown shorts to split up group"))
        uLayout.addRow("Chase Kind/Chase Time:", self.unknownM)
        uLayout.addRow("High/SE:", self.unknownN)

        ChaseBox = QtGui.QGroupBox()
        ChaseBox.setTitle("Chase Behaviour")
        ChaseBox.setLayout(uLayout)

        
        
        # Final Layout
        layout = QtGui.QGridLayout()
        layout.addWidget(self.EnemyList, 0, 0, 6, 1)
        layout.addLayout(nameLayout, 0, 1, 1, 1)
        layout.addLayout(sLayout, 1, 1, 1, 1)
        layout.addWidget(statsBox, 0, 2, 1, 1)
        layout.addWidget(dropBox, 0, 3, 1, 1)
        layout.addWidget(uBox, 0, 4, 1, 1)
        layout.addWidget(MapBox, 1, 2, 1, 1)
        layout.addWidget(BehBox, 1, 3, 1, 1)
        layout.addWidget(ChaseBox, 1, 4, 1, 1)
        layout.addWidget(weakBox, 3, 1, 3, 4)
        layout.addWidget(sizeBox, 2, 1, 1, 1)
        layout.addWidget(spoilBox, 2, 2, 1, 1)

        self.setLayout(layout)


    def LocalOpen(self):
        fn = QtGui.QFileDialog.getOpenFileName(self, 'Choose an enemy file', 'bin000.acf', 'Enemy Data File (*.acf);;All Files(*)')
        if fn == '': return
        filename = str(fn)
    
        file = open(filename, 'rb')
        data = file.read()
        file.close()
    
        self.UnpackEnemyList(data)
        
        
        
    def ServerOpen(self):

        dlg = self.ServerOpenDialog()
        
        if dlg.exec_() == QtGui.QDialog.Accepted:
        
            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")

            self.ftp.cwd('/')    
            self.ftp.cwd('/Enemy')    

            e = open('temp', 'wb')
            self.ftp.retrbinary('RETR {0}'.format(dlg.Combo.currentText()), e.write)
            e.close()
            e = open('temp', 'rb')
            data = e.read()

            self.ftp.close()

            self.UnpackEnemyList(data)


    def LocalSave(self):
        return

    def SaveAs(self):
        fn = QtGui.QFileDialog.getSaveFileName(self, 'Choose a new filename', 'bin000.acf', '.acf Files (*.acf)')
        if fn == '': return

        fn = str(fn)
        newfile = open(fn, 'wb')


        newfile.write('FPS4')
        newfile.write(struct.pack('>9I36sI44x4s168x', 2, 0x1C, 0xA0, 0x30010F, 0, 0x7C, 0xA0, 0x91A0, 0x91A0, 'ENEMYSTATE.BIN', 0x9240, 'bind'))
        

        for entry in self.entrylist:

            writestr = struct.pack(fileStruct, entry.name.encode('SJIS', 'ignore'), entry.HP, entry.EXP, entry.sizefloatA, entry.sizefloatB, entry.sizefloatC, entry.sizefloatD, entry.sizefloatE, entry.sizefloatF, entry.level, entry.gald, entry.SP, entry.att, entry.matt, entry.acc, entry.dfn, entry.mdef, entry.eva, entry.unknownA, entry.dropA, entry.dropArate, entry.dropB, entry.dropBrate, entry.steal, entry.stealRate, int(entry.weakness), entry.unknownB, entry.species, entry.unknownC, entry.unkShortA, entry.unkShortB, entry.unkShortC, entry.unkShortD, entry.walkSpeed, entry.chaseSpeed, entry.mapScale, entry.walkTime, entry.stayTime, entry.unknownK, entry.findAngle, entry.unknownM, entry.unknownN)
            newfile.write(writestr)
        newfile.write(0x50*'\x00')
        newfile.close()
        
        
    def ServerSave(self):
        dlg = self.ServerSaveDialog()
        
        if dlg.exec_() == QtGui.QDialog.Accepted:

            newfile = open('temp', 'wb')
    
            newfile.write('FPS4')
            newfile.write(struct.pack('>9I36sI44x4s168x', 2, 0x1C, 0xA0, 0x30010F, 0, 0x7C, 0xA0, 0x91A0, 0x91A0, 'ENEMYSTATE.BIN', 0x9240, 'bind'))
            
    
            for entry in self.entrylist:
    
                writestr = struct.pack(fileStruct, entry.name.encode('SJIS', 'ignore'), entry.HP, entry.EXP, entry.sizefloatA, entry.sizefloatB, entry.sizefloatC, entry.sizefloatD, entry.sizefloatE, entry.sizefloatF, entry.level, entry.gald, entry.SP, entry.att, entry.matt, entry.acc, entry.dfn, entry.mdef, entry.eva, entry.unknownA, entry.dropA, entry.dropArate, entry.dropB, entry.dropBrate, entry.steal, entry.stealRate, int(entry.weakness), entry.unknownB, entry.species, entry.unknownC, entry.unkShortA, entry.unkShortB, entry.unkShortC, entry.unkShortD, entry.walkSpeed, entry.chaseSpeed, entry.mapScale, entry.walkTime, entry.stayTime, entry.unknownK, entry.findAngle, entry.unknownM, entry.unknownN)
                newfile.write(writestr)
            newfile.write(0x50*'\x00')
            newfile.close()
            
            fnew = open('temp', 'r+b')
            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")
            self.ftp.cwd('/')    
            self.ftp.cwd('/Enemy')    
            self.ftp.storbinary('STOR {0}'.format(dlg.Combo.currentText()), fnew)
            self.ftp.close()
            fnew.close()
    


    def UnpackEnemyList(self, data):
        
        data = data[0x128:-0x10]
        
        for i in xrange(len(data)/0x88):
            enemydat = struct.unpack_from(fileStruct, data, i*(0x88))
            self.entrylist.append(EnemyEntry(enemydat))
            self.EnemyList.addItem(enemydat[0].decode('SJIS', 'ignore').strip('\x00'))


    class ServerOpenDialog(QtGui.QDialog):
        def __init__(self, parent=None):
            super(QtGui.QDialog, self).__init__(parent)
        
            self.Combo = QtGui.QComboBox()
    
            buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)

            buttonBox.accepted.connect(self.accept)
            buttonBox.rejected.connect(self.reject)
    
            self.ftp = FTP("ftp.chronometry.ca", "graces@chronometry.ca", "DbWp5RWRd3uC")
    
            self.ftp.cwd('/')    
            self.ftp.cwd('/Enemy')    
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
    
            self.setWindowTitle("Open Enemy Data from Server")



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
            self.ftp.cwd('/Enemy')    
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
    
            self.setWindowTitle("Save Enemy Data to Server")


        def addThing(self):
            self.Combo.addItem(self.edit.text())
            self.Combo.setCurrentIndex(self.Combo.count()-1)
            

    def DisplayMon(self):
        x = self.entrylist[self.EnemyList.currentRow()]

        self.name.setText(x.name)
        self.HP.setValue(x.HP)
        self.EXP.setValue(x.EXP)
        self.level.setValue(x.level)
        self.gald.setValue(x.gald)
        self.SP.setValue(x.SP)
        self.att.setValue(x.att)
        self.matt.setValue(x.matt)
        self.acc.setValue(x.acc)
        self.dfn.setValue(x.dfn)
        self.mdef.setValue(x.mdef)
        self.eva.setValue(x.eva)
        self.unknownA.setValue(x.unknownA)

        self.dropA.setItemText(0, str(hex(x.dropA)))
        self.dropArate.setValue(x.dropArate)
        self.dropB.setItemText(0, str(hex(x.dropB)))
        self.dropBrate.setValue(x.dropBrate)
        self.steal.setItemText(0, str(hex(x.steal)))
        self.stealRate.setValue(x.stealRate)
        
        self.wAa.setChecked(x.weakness[0]) #0x00000001
        self.wAb.setChecked(x.weakness[1]) #0x00000002
        self.wAc.setChecked(x.weakness[2]) #0x00000004
        self.wAd.setChecked(x.weakness[3]) #0x00000008
        
        self.wAe.setChecked(x.weakness[4]) #0x0000001
        self.wAf.setChecked(x.weakness[5]) #0x0000002
        self.wAg.setChecked(x.weakness[6]) #0x0000004
        self.wAh.setChecked(x.weakness[7]) #0x0000008

        self.wBa.setChecked(x.weakness[8]) #0x000001
        self.wBb.setChecked(x.weakness[9]) #0x000002
        self.wBc.setChecked(x.weakness[10]) #0x000004
        self.wBd.setChecked(x.weakness[11]) #0x000008
        
        self.wBe.setChecked(x.weakness[12]) #0x00001
        self.wBf.setChecked(x.weakness[13]) #0x00002
        self.wBg.setChecked(x.weakness[14]) #0x00004
        self.wBh.setChecked(x.weakness[15]) #0x00008

        self.wCa.setChecked(x.weakness[16]) #0x0001
        self.wCb.setChecked(x.weakness[17]) #0x0002
        self.wCc.setChecked(x.weakness[18]) #0x0004
        self.wCd.setChecked(x.weakness[19]) #0x0008
        
        self.wCe.setChecked(x.weakness[20]) #0x001
        self.wCf.setChecked(x.weakness[21]) #0x002
        self.wCg.setChecked(x.weakness[22]) #0x004
        self.wCh.setChecked(x.weakness[23]) #0x008

        self.wDa.setChecked(x.weakness[24]) #0x01
        self.wDb.setChecked(x.weakness[25]) #0x02
        self.wDc.setChecked(x.weakness[26]) #0x04
        self.wDd.setChecked(x.weakness[27]) #0x08
        
        self.wDe.setChecked(x.weakness[28]) #0x1
        self.wDf.setChecked(x.weakness[29]) #0x2
        self.wDg.setChecked(x.weakness[30]) #0x4
        self.wDh.setChecked(x.weakness[31]) #0x8


        self.species.setText(str(hex(x.species)))
        self.unknownB.setValue(x.unknownB)

        # Unknown Stuff
        self.sizefloatA.setValue(x.sizefloatA)
        self.sizefloatB.setValue(x.sizefloatB)
        self.sizefloatC.setValue(x.sizefloatC)
        self.sizefloatD.setValue(x.sizefloatD)
        self.sizefloatE.setValue(x.sizefloatE)
        self.sizefloatF.setValue(x.sizefloatF)

            # Ints? Padding? Floats?
        self.unkShortA.setValue(x.unkShortA)
        self.unkShortB.setValue(x.unkShortB)
        self.unkShortC.setValue(x.unkShortC)
        self.unkShortD.setValue(x.unkShortD)
        
            # Floats
        self.walkSpeed.setValue(x.walkSpeed)
        self.chaseSpeed.setValue(x.chaseSpeed)
        self.mapScale.setValue(x.mapScale)
        
            # Shorts
        self.walkTime.setValue(x.walkTime)
        self.stayTime.setValue(x.stayTime)
        self.unknownK.setValue(x.unknownK)
        self.findAngle.setValue(x.findAngle)
        
            # Ints
        self.unknownM.setValue(x.unknownM)
        self.unknownN.setValue(x.unknownN)

    
    

    # Slots
    
    @QtCore.pyqtSlot(str)
    def nameChange(self, string):
        cur = self.EnemyList.currentRow()
        self.entrylist[cur].name = str(string)
        item = self.EnemyList.item(cur)
        item.setText(string)

    @QtCore.pyqtSlot(int)
    def HPChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].HP = int

    @QtCore.pyqtSlot(int)
    def EXPChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].EXP = int

    @QtCore.pyqtSlot(float)
    def sizefloatAChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].sizefloatA = float

    @QtCore.pyqtSlot(float)
    def sizefloatBChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].sizefloatB = float

    @QtCore.pyqtSlot(float)
    def sizefloatCChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].sizefloatC = float

    @QtCore.pyqtSlot(float)
    def sizefloatDChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].sizefloatD = float

    @QtCore.pyqtSlot(float)
    def sizefloatEChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].sizefloatE = float

    @QtCore.pyqtSlot(float)
    def sizefloatFChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].sizefloatF = float

    @QtCore.pyqtSlot(int)
    def levelChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].level = int

    @QtCore.pyqtSlot(int)
    def galdChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].gald = int

    @QtCore.pyqtSlot(int)
    def SPChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].SP = int

    @QtCore.pyqtSlot(int)
    def attChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].att = int

    @QtCore.pyqtSlot(int)
    def mattChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].matt = int

    @QtCore.pyqtSlot(int)
    def accChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].acc = int

    @QtCore.pyqtSlot(int)
    def dfnChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].dfn = int

    @QtCore.pyqtSlot(int)
    def mdefChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].mdef = int

    @QtCore.pyqtSlot(int)
    def evaChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].eva = int

    @QtCore.pyqtSlot(int)
    def unknownAChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unknownA = int

    @QtCore.pyqtSlot(int)
    def dropAChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].dropA = int

    @QtCore.pyqtSlot(int)
    def dropArateChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].dropArate = int

    @QtCore.pyqtSlot(int)
    def dropBChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].dropB = int

    @QtCore.pyqtSlot(int)
    def dropBrateChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].dropBrate = int

    @QtCore.pyqtSlot(int)
    def stealChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].steal = int

    @QtCore.pyqtSlot(int)
    def stealRateChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].stealRate = int

    @QtCore.pyqtSlot(int)
    def unknownBChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unknownB = int

    @QtCore.pyqtSlot(int)
    def speciesChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].species = int

    @QtCore.pyqtSlot(int)
    def unknownCChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unknownC = int

    @QtCore.pyqtSlot(int)
    def unkShortAChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unkShortA = int

    @QtCore.pyqtSlot(int)
    def unkShortBChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unkShortB = int

    @QtCore.pyqtSlot(int)
    def unkShortCChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unkShortC = int

    @QtCore.pyqtSlot(int)
    def unkShortDChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unkShortD = int

    @QtCore.pyqtSlot(float)
    def walkSpeedChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].walkSpeed = float

    @QtCore.pyqtSlot(float)
    def chaseSpeedChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].chaseSpeed = float

    @QtCore.pyqtSlot(float)
    def mapScaleChange(self, float):
        self.entrylist[self.EnemyList.currentRow()].mapScale = float

    @QtCore.pyqtSlot(int)
    def walkTimeChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].walkTime = int

    @QtCore.pyqtSlot(int)
    def stayTimeChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].stayTime = int

    @QtCore.pyqtSlot(int)
    def unknownKChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unknownK = int

    @QtCore.pyqtSlot(int)
    def findAngleChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].findAngle = int

    @QtCore.pyqtSlot(int)
    def unknownMChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unknownM = int

    @QtCore.pyqtSlot(int)
    def unknownNChange(self, int):
        self.entrylist[self.EnemyList.currentRow()].unknownN = int


    # Weakness bitfields
    @QtCore.pyqtSlot(int)
    def wAaChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[0] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[0] = 0

    @QtCore.pyqtSlot(int)
    def wAbChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[1] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[1] = 0

    @QtCore.pyqtSlot(int)
    def wAcChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[2] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[2] = 0

    @QtCore.pyqtSlot(int)
    def wAdChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[3] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[3] = 0

    @QtCore.pyqtSlot(int)
    def wAeChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[4] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[4] = 0

    @QtCore.pyqtSlot(int)
    def wAfChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[5] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[5] = 0

    @QtCore.pyqtSlot(int)
    def wAgChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[6] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[6] = 0

    @QtCore.pyqtSlot(int)
    def wAhChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[7] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[7] = 0

    @QtCore.pyqtSlot(int)
    def wBaChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[8] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[8] = 0

    @QtCore.pyqtSlot(int)
    def wBbChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[9] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[9] = 0

    @QtCore.pyqtSlot(int)
    def wBcChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[10] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[10] = 0

    @QtCore.pyqtSlot(int)
    def wBdChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[11] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[11] = 0

    @QtCore.pyqtSlot(int)
    def wBeChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[12] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[12] = 0

    @QtCore.pyqtSlot(int)
    def wBfChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[13] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[13] = 0

    @QtCore.pyqtSlot(int)
    def wBgChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[14] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[14] = 0

    @QtCore.pyqtSlot(int)
    def wBhChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[15] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[15] = 0

    @QtCore.pyqtSlot(int)
    def wCaChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[16] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[16] = 0

    @QtCore.pyqtSlot(int)
    def wCbChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[17] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[17] = 0

    @QtCore.pyqtSlot(int)
    def wCcChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[18] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[18] = 0

    @QtCore.pyqtSlot(int)
    def wCdChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[19] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[19] = 0

    @QtCore.pyqtSlot(int)
    def wCeChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[20] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[20] = 0

    @QtCore.pyqtSlot(int)
    def wCfChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[21] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[21] = 0

    @QtCore.pyqtSlot(int)
    def wCgChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[22] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[22] = 0

    @QtCore.pyqtSlot(int)
    def wChChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[23] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[23] = 0

    @QtCore.pyqtSlot(int)
    def wDaChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[24] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[24] = 0

    @QtCore.pyqtSlot(int)
    def wDbChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[25] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[25] = 0

    @QtCore.pyqtSlot(int)
    def wDcChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[26] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[26] = 0

    @QtCore.pyqtSlot(int)
    def wDdChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[27] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[27] = 0

    @QtCore.pyqtSlot(int)
    def wDeChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[28] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[28] = 0

    @QtCore.pyqtSlot(int)
    def wDfChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[29] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[29] = 0

    @QtCore.pyqtSlot(int)
    def wDgChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[30] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[30] = 0

    @QtCore.pyqtSlot(int)
    def wDhChange(self, int):
        if int == 2:
            self.entrylist[self.EnemyList.currentRow()].weakness[31] = 1
        else:
            self.entrylist[self.EnemyList.currentRow()].weakness[31] = 0



class EnemyEntry():
    def __init__(self, enemydat):
       
        i = 0
        self.name = enemydat[i].decode('SJIS', 'ignore').strip('\x00')
        i += 1
        
        self.HP = enemydat[i]
        i += 1
        self.EXP = enemydat[i]
        i += 1

        self.sizefloatA = enemydat[i]
        i += 1
        self.sizefloatB = enemydat[i]
        i += 1
        self.sizefloatC = enemydat[i]
        i += 1
        self.sizefloatD = enemydat[i]
        i += 1
        self.sizefloatE = enemydat[i]
        i += 1
        self.sizefloatF = enemydat[i]
        i += 1

        self.level = enemydat[i]
        i += 1
        self.gald = enemydat[i]
        i += 1
        self.SP = enemydat[i]
        i += 1
        self.att = enemydat[i]
        i += 1
        self.matt = enemydat[i]
        i += 1
        self.acc = enemydat[i]
        i += 1
        self.dfn = enemydat[i]
        i += 1
        self.mdef = enemydat[i]
        i += 1
        self.eva = enemydat[i]
        i += 1
        self.unknownA = enemydat[i]
        i += 1
        self.dropA = enemydat[i]
        i += 1
        self.dropArate = enemydat[i]
        i += 1
        self.dropB = enemydat[i]
        i += 1
        self.dropBrate = enemydat[i]
        i += 1
        self.steal = enemydat[i]
        i += 1
        self.stealRate = enemydat[i]
        i += 1
        
        self.weakness = bf(enemydat[i])
        i += 1
        self.unknownB = enemydat[i]
        i += 1
        
        self.species = enemydat[i]
        i += 1
        self.unknownC = enemydat[i]
        i += 1

        # Ints? Padding? Floats?
        i += 1
        self.unkShortA = enemydat[i]
        i += 1
        self.unkShortB = enemydat[i]
        i += 1
        self.unkShortC = enemydat[i]
        i += 1
        self.unkShortD = enemydat[i]
        i += 1
        
        # Floats
        self.walkSpeed = enemydat[i]
        i += 1
        self.chaseSpeed = enemydat[i]
        i += 1
        self.mapScale = enemydat[i]
        i += 1
        
        # Shorts
        self.walkTime = enemydat[i]
        i += 1
        self.stayTime = enemydat[i]
        i += 1
        self.unknownK = enemydat[i]
        i += 1
        self.findAngle = enemydat[i]
        i += 1
        
        # Ints
        self.unknownM = enemydat[i]
        i += 1
        self.unknownN = enemydat[i]
        i += 1


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


