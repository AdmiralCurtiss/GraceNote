import struct, math, shutil, os, sys
from binascii import unhexlify
from PyQt4 import QtCore, QtGui
from ftplib import FTP
import subprocess


class Font(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Font, self).__init__(parent)

        # Toolbar
        parent.Toolbar.clear()

        parent.Toolbar.addAction('Save As...', self.SaveAs)
        parent.Toolbar.addAction('Save to Server...', self.ServerSave)
        parent.Toolbar.addAction('Generate', self.Generate)

        parent.fileMenu.addAction('Save As...', self.SaveAs)
        parent.fileMenu.addAction('Save to Server...', self.ServerSave)
        parent.fileMenu.addAction('Quit', quit, QtGui.QKeySequence('Ctrl-Q'))

        self.fontMetrics = None
        self.fontMetricsPS3 = None
        self.fontMap = None
        self.fontImages = []
        self.font = None
        
        self.rangeList = [QtGui.QCheckBox('ASCII'), #0x823F - 0x829E
            QtGui.QCheckBox('Hiragana'), #0x828F - 0x82FF
            QtGui.QCheckBox('Katagana'), #0x8340 - 0x839E
            QtGui.QCheckBox('Cyrillics'), #0x839F - 0x83FF
            QtGui.QCheckBox('Greek and Box Drawings'), #0x8440 - 0x84B0
            QtGui.QCheckBox('Unknown'), #0x140 long
            QtGui.QCheckBox('Common Kanji'), #0x8890 - 0x9FFF
            QtGui.QCheckBox('Uncommon Kanji')] #0xE040 - 0xEAAF

        self.fontButton = QtGui.QPushButton('Choose Font')
        self.fontLabel = QtGui.QLabel('No font selected')

        self.button = QtGui.QPushButton('Generate')
        
        self.fontButton.released.connect(self.fontBox)
        self.button.released.connect(self.Generate)
        
        self.GeneratedLabel = QtGui.QLabel('No Font Generated')
        
        layout = QtGui.QVBoxLayout()
        for item in self.rangeList:
            layout.addWidget(item)
        layout.addWidget(self.fontButton)
        layout.addWidget(self.fontLabel)
        layout.addWidget(self.button)
        layout.addWidget(self.GeneratedLabel)

        self.setLayout(layout)
        self.adjustSize()
        

    def fontBox(self):
        tmpfont = QtGui.QFontDialog.getFont(QtGui.QFont("Gentium Book", 10), self, 'Choose a Font');
        if tmpfont[1] == True:
            self.font = tmpfont[0]
            self.fontLabel.setText('{0}, {1} pt'.format(self.font.family(), self.font.pointSize()))
            
            
    def Generate(self):

        if self.fontLabel == 'No font selected':
            return
        
        
        fontMap = ''
        fontMetrics = ''
        fontMetricsPS3 = ''
        fontTextureTiles = []
        fontPS3Tiles = []

        LatinSet = [0x20, 0x8141, 0x2E, 0x2C, 0x2E, 0x8145, 0x3A, 0x3B, 0x3F, 0x21, 0x22] #Space to Quotations
        LatinSet.extend(range(0x814B, 0x8165)) #Degree sign to half-ellipsis
        LatinSet.extend([0x27, 0x27, 0x22, 0x22, 0x28, 0x29]) #quotations and brackets
        LatinSet.extend(range(0x816B, 0x817B)) #A lot more brackets
        LatinSet.extend([0x2B, 0x2D, 0x817D, 0x817E, 0x00, 0x8180, 0x3D]) #math signs
        LatinSet.extend(range(0x8182, 0x8190)) #Symbols
        LatinSet.extend([0x24, 0x8191, 0x8192, 0x25, 0x23, 0x26]) #Monetary and Numeric signs
        LatinSet.extend(range(0x8196, 0x820F)) #symbols
        LatinSet.extend(range(0x30, 0x3A)) #Numbers
        LatinSet.extend([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        LatinSet.extend(range(0x41, 0x5B)) #Uppercase Letters
        LatinSet.extend([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        LatinSet.extend(range(0x61, 0x7B)) #Lowercase Letters
        LatinSet.extend([0x00, 0x00, 0x00, 0x00])


        BasicKanji = range(0x8890, 0x8900)
        MediumKanji = []
        SpecialKanji = []

        for i in range(0x89, 0xA0):
            BasicKanji.extend(range(i*0x100+0x40, i*0x100+0x100))

        for i in range(0xE0, 0xEA):
            MediumKanji.extend(range(i*0x100+0x40, i*0x100+0x100))

        for i in range(0xED, 0xEF):
            SpecialKanji.extend(range(i*0x100+0x40, i*0x100+0x100))

        for i in range(0xF9, 0xFD):
            SpecialKanji.extend(range(i*0x100+0x40, i*0x100+0x100))

        MediumKanji.extend(SpecialKanji)
        
        LoopPoints = [LatinSet, range(0x829F, 0x8300), range(0x8340, 0x839F), range(0x839F, 0x8400), range(0x8440, 0x8500), range(0x8740, 0x8850), BasicKanji, MediumKanji]

#        Loop = []
#
#        file = open('Resources/CP932.txt')
#        for line in file:
#            num = int(line[:6], 16)
#            Loop.append(num)
#            print hex(num)
#        file.close()
#
#
#        LoopPoints = [Loop]


        self.font.setStyleStrategy(QtGui.QFont.ForceOutline)
#        self.font.setWeight(100)

        gradient = QtGui.QLinearGradient(0, 0, 0, 100)
        gradient.setColorAt(0.0, QtGui.QColor(255, 255, 255))
        gradient.setColorAt(1.0, QtGui.QColor(208, 208, 208))

        brush = QtGui.QBrush(gradient)
        pen = QtGui.QPen(QtGui.QColor(128,128,128), 0,
                QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        fontMet = QtGui.QFontMetrics(self.font)

        i = 0
        p = 0
        for Loop in LoopPoints:
            print 'Loop: {0}'.format(p)
            
            # Wii
            for char in Loop:
                if self.rangeList[p].isChecked():
                    text = struct.unpack('>2s', struct.pack('>H', char))[0]
#                    try:
                    text = text.decode('cp932', 'ignore')
                    i += 1
                    fontMap += struct.pack('>H', i)
                    

                    image = QtGui.QImage(25, 25, QtGui.QImage.Format_ARGB32)
                    image.fill(QtCore.Qt.black)
                    painter = QtGui.QPainter(image)
                    painter.setRenderHint(QtGui.QPainter.Antialiasing)

                    painter.setBrush(brush)
                    painter.setPen(pen)

                    textPath = QtGui.QPainterPath()
                    textPath.addText(12 - (fontMet.width(text)/2), 25-fontMet.descent(), self.font, text)

                    painter.drawPath(textPath)
                    painter.end()

                    lleading = 12-(fontMet.width(text)/2)
                    rleading = 13-(fontMet.width(text)/2)
                    lbearing = lleading
                    rbearing = rleading
                    
                    lleadOutline = lleading + 1
                    rleadOutline = rleading + 1
                    lbearOutline = lbearing + 1
                    rbearOutline = rbearing + 1


                    try:
                        fontMetrics += struct.pack('>8B', lleading, rleading, lbearing, rbearing, lleadOutline, rleadOutline, lbearOutline, rbearOutline)
                        fontTextureTiles.append(image)
                        #image.save('{0}.png'.format(hex(char)))
                    except:
                        print "{0} didn't work:".format(hex(char))
                        fontMap += '\x00\x00'
                else:
                    fontMap += '\x00\x00'
            p += 1

        #PS3
        i = 0
        p = 0
       
        self.font.setPointSize(self.font.pointSize()+12)

        gradient = QtGui.QLinearGradient(0, 0, 0, 100)
        gradient.setColorAt(0.0, QtGui.QColor(255, 255, 255))
        gradient.setColorAt(1.0, QtGui.QColor(158, 158, 158))

        brush = QtGui.QBrush(gradient)
        pen = QtGui.QPen(QtGui.QColor(0,0,0), 1,
            QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)

        fontMet = QtGui.QFontMetrics(self.font)

        for Loop in LoopPoints:
            
            if p == 3:
                tmpfont = QtGui.QFontDialog.getFont(QtGui.QFont("Gentium Book", 10), self, 'Choose a Font');
                if tmpfont[1] == True:
                    self.font = tmpfont[0]
                    self.fontLabel.setText('{0}, {1} pt'.format(self.font.family(), self.font.pointSize()))
                    self.font.setPointSize(self.font.pointSize()+12)
                    fontMet = QtGui.QFontMetrics(self.font)
           
            print 'Loop: {0}'.format(p)
            for char in Loop:
                if self.rangeList[p].isChecked():
                    text = struct.unpack('>2s', struct.pack('>H', char))[0]
#                    try:
                    text = text.decode('cp932', 'ignore')
                    i += 1
                    

                    image = QtGui.QImage(32, 32, QtGui.QImage.Format_ARGB32)
                    image.fill(QtCore.Qt.black)
                    painter = QtGui.QPainter(image)
                    painter.setRenderHint(QtGui.QPainter.Antialiasing)

                    painter.setBrush(brush)
                    painter.setPen(pen)

                    textPath = QtGui.QPainterPath()
#                    textPath.addText(0, 0, self.font, text)
#                    textPath.addText(18 - (fontMet.width(text)/2), 32-fontMet.descent(), self.font, text)
                    textPath.addText(0, 32-fontMet.descent(), self.font, text)
                    print 'tile 0x{0}: '.format(hex(char)) + str(fontMet.descent())

                    painter.drawPath(textPath)
                    painter.end()

                    lleading = 0
                    rleading = 0
                    #lleading = 18-(fontMet.width(text)/2)
                    #rleading = 19-(fontMet.width(text)/2)
                    lbearing = 0
                    rbearing = 0
                    
                    lleadOutline = lleading + 1
                    rleadOutline = rleading + 1
                    lbearOutline = lbearing + 1
                    rbearOutline = rbearing + 1


                    fontMetricsPS3 += struct.pack('>8B', lleading, rleading, lbearing, rbearing, lleadOutline, rleadOutline, lbearOutline, rbearOutline)
                    fontPS3Tiles.append(image)
#                    image.save('{0}.png'.format(hex(char)))
#                    except:
#                        print "{0} didn't work:".format(hex(char))
#                        fontMap += '\x00\x00'
                else:
                    pass


            p += 1
            
        print '{0} characters total'.format(i)
#        print 'Fontmap: {0}'.format(len(fontMap)/2)
#       (0x21C0)


        # Wii
        self.fontMap = fontMap
        self.fontMetrics = fontMetrics
        self.fontMetricsPS3 = fontMetricsPS3
            
        Xoffset = 0
        Yoffset = 0
                
        tex = QtGui.QImage(1024, 1024, QtGui.QImage.Format_ARGB32)
        tex.fill(QtCore.Qt.black)
        painter = QtGui.QPainter(tex)

        p = 1
        for i in fontTextureTiles:
            painter.drawImage(Xoffset, Yoffset, i)
            Xoffset += 25
            if Xoffset >= 1024:
                Xoffset = 0
                Yoffset += 25     
            
            if Yoffset >=1024:
                painter.end()
                
                xpixel = 0
                ypixel = 0
                for xpixel in range(1024):
                    for ypixel in range(1024):
                        curVal = tex.pixel(xpixel, ypixel)

                        g = (curVal & 0xFF) * ((curVal >> 24) / 256.0)
                        g = int(g)/16*16
                        if curVal == 0x1FFFFFFF:
                            tex.setPixel(xpixel, ypixel, 0xFF << 24)
                        else:    
                            tex.setPixel(xpixel, ypixel, (0xFF << 24 | g << 16 | g << 8 | g))
                
                booli = tex.save('Font Texture {0}.png'.format(p))
                self.fontImages.append('')
                
                tex = QtGui.QImage(1024, 1024, QtGui.QImage.Format_ARGB32)
                tex.fill(QtCore.Qt.black)
                painter = QtGui.QPainter(tex)

                p += 1

                Xoffset = 0
                Yoffset = 0

        painter.end()

        xpixel = 0
        ypixel = 0
                
        for xpixel in range(1024):
            for ypixel in range(1024):
                curVal = tex.pixel(xpixel, ypixel)

                g = (curVal & 0xFF) * ((curVal >> 24) / 256.0)
                g = int(g)/16*16
                if curVal == 0x1FFFFFFF:
                    tex.setPixel(xpixel, ypixel, 0xFF << 24)
                else:    
                    tex.setPixel(xpixel, ypixel, (0xFF << 24 | g << 16 | g << 8 | g))

        booli = tex.save('Font Texture {0}.png'.format(p))
        self.fontImages.append('')


        print len(self.fontImages)
        # PS3            
        Xoffset = 0
        Yoffset = 0
                
        tex = QtGui.QImage(2048, 2048, QtGui.QImage.Format_ARGB32)
        tex.fill(QtCore.Qt.black)
        painter = QtGui.QPainter(tex)

        p = 1
        i = 0
        try:
            for z in range(16):
                if z == 0:
                    Xoffset = 0
                    Yoffset = 0
                if z == 1:
                    Xoffset = 512
                    Yoffset = 0
                if z == 2:
                    Xoffset = 0
                    Yoffset = 512
                if z == 3:
                    Xoffset = 512
                    Yoffset = 512
                if z == 4:
                    Xoffset = 1024
                    Yoffset = 0
                if z == 5:
                    Xoffset = 1536
                    Yoffset = 0
                if z == 6:
                    Xoffset = 1024
                    Yoffset = 512
                if z == 7:
                    Xoffset = 1536
                    Yoffset = 512
                if z == 8:
                    Xoffset = 0
                    Yoffset = 1024
                if z == 9:
                    Xoffset = 512
                    Yoffset = 1024
                if z == 10:
                    Xoffset = 0
                    Yoffset = 1536
                if z == 11:
                    Xoffset = 512
                    Yoffset = 1536
                if z == 12:
                    Xoffset = 1024
                    Yoffset = 1024
                if z == 13:
                    Xoffset = 1536
                    Yoffset = 1024
                if z == 14:
                    Xoffset = 1024
                    Yoffset = 1536
                if z == 15:
                    Xoffset = 1536
                    Yoffset = 1536
                    
                for y in range(16):
                    for x in range(16):
                        painter.drawImage(Xoffset + (x*32), Yoffset + (y*32), fontPS3Tiles[i])
                        i += 1
        except:
            pass
        painter.end()

        xpixel = 0
        ypixel = 0
                
        booli = tex.save('Font Texture {0} PS3.png'.format(p))



        self.GeneratedLabel.setText('Font preview available in Grace Note directory\nFont ready to save.')


#        tex = QtGui.QImage(16*25, 540*25, QtGui.QImage.Format_ARGB32)
#        tex.fill(QtCore.Qt.transparent)
#        painter = QtGui.QPainter(tex)
#        
#        Xoffset = 0
#        Yoffset = 0
#        
#        p = 0
#        for tile in fontTextureTiles:
#    
#            painter.drawImage(Xoffset, Yoffset, tile)
#            p +=1
#            
#            Xoffset += 25
#            
#            if Xoffset >= 16*24:
#                Xoffset = 0
#                Yoffset += 25
#                                    
#        painter.end()
#        tex.save('/Users/Tempus/Desktop/OutputImage.png')



    def SaveAs(self):
        if self.fontMetrics == None:
            return
    
        fn = QtGui.QFileDialog.getSaveFileName(self, 'Choose a new filename', 'FontBinary2', 'ToG Font Data File')
        if fn == '': return

        fn = str(fn)
        newfileBin = open(fn + '.bin', 'wb')

        hex(len(self.fontMetrics))[2:].zfill(8)

        newfileBin.write(unhexlify('46505334000000030000001C00000060000C00070000000000000040000000600000438000004380000043E0{0}{1}{2}0000000000000000466F6E7442696E61727900000000000000000000000000000000000000000000'.format(hex(len(self.fontMetrics))[2:].zfill(8), hex(len(self.fontMetrics)+(len(self.fontMetrics)%16))[2:].zfill(8), hex(len(self.fontMap) + len(self.fontMetrics) + (len(self.fontMetrics)%16) + 0x60)[2:].zfill(8))))

        newfileBin.write(self.fontMap)
        newfileBin.write(self.fontMetrics)
        
        newfileBin.close()
        
        
        newfileBin = open(fn + '-PS3.bin', 'wb')

        hex(len(self.fontMetricsPS3))[2:].zfill(8)

        newfileBin.write(unhexlify('46505334000000030000001C00000060000C00070000000000000040000000600000438000004380000043E0{0}{1}{2}0000000000000000466F6E7442696E61727900000000000000000000000000000000000000000000'.format(hex(len(self.fontMetricsPS3))[2:].zfill(8), hex(len(self.fontMetricsPS3)+(len(self.fontMetricsPS3)%16))[2:].zfill(8), hex(len(self.fontMap) + len(self.fontMetricsPS3) + (len(self.fontMetricsPS3)%16) + 0x60)[2:].zfill(8))))

        newfileBin.write(self.fontMap)
        newfileBin.write(self.fontMetricsPS3)
        newfileBin.close()

        
        # Make a tex!~
        basepath = os.path.dirname(os.path.abspath(sys.argv[0]))
        Graceful = basepath + os.sep + 'graceful.exe'

        l = len(self.fontImages)
        for i in xrange(l):
            shutil.copy('Font Texture {0}.png'.format(i+1), 'Resources/DummyFonts/FontTexture{0}.tex.ext/FONTTEXTURECONV{1}.png'.format(l, i))
            shutil.copy('Font Texture {0} PS3.png'.format(i+1), 'Resources/DummyFonts/FontTexture{0}.F.tex.ext/FONTTEXTURECONV{1}.png'.format(l, i))
            
        # Wii
        args = ["mono", str(Graceful), "7", str(basepath + os.sep + "Resources" + os.sep + 'DummyFonts' + os.sep + 'FontTexture{0}.tex'.format(l)), '11']
        proc = subprocess.Popen(args,shell=False)

        while proc.poll() == None:
            pass
        shutil.copy('Resources/DummyFonts/FontTexture{0}.tex.new'.format(l), fn + '.tex')
        os.remove('Resources/DummyFonts/FontTexture{0}.tex.new'.format(l))
        

        # PS3
        args = ["mono", str(Graceful), "7", str(basepath + os.sep + "Resources" + os.sep + 'DummyFonts' + os.sep + 'FontTexture{0}.F.tex'.format(l)), '11']
        proc = subprocess.Popen(args,shell=False)

        while proc.poll() == None:
            pass
        shutil.copy('Resources/DummyFonts/FontTexture{0}.F.tex.new'.format(l), fn + '-PS3.tex')
        os.remove('Resources/DummyFonts/FontTexture{0}.F.tex.new'.format(l))

        newfileBin.close()
        
        
    def ServerSave(self):
        print 'Feature not implemented'
        return
        
        
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

