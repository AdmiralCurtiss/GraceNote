# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import re
import os

class FontDisplayWindow(QtGui.QDialog):

    def __init__(self, parent):
        super(FontDisplayWindow, self).__init__()
        self.parent = parent
        self.setWindowModality(False)        
        
        self.setWindowTitle("Font Display")
        self.scroll = QtGui.QScrollArea()
        self.layout = QtGui.QVBoxLayout(self.scroll)
        self.setLayout(self.layout)
        
    def drawText(self, text, databaseDesc): # database desc is only passed for Dangan Ronpa!! can be removed in generic GN version
        self.clearInfo()

        text = text.replace('\f', '\n')
        text = Globals.VariableReplace(text)
        for old, new in Globals.configData.FontReplacements.iteritems():
            text = text.replace(old, new)

        currentX = 0
        currentY = 0
        maxX = 0
        maxY = 0
        currentFont = Globals.configData.Fonts['default']
        
        # DANGAN RONPA SPECIFIC
        if re.match('e0[0-9]_1[0-9][0-9]_001.lin', databaseDesc):
            NonstopFlag = True
            currentFont = Globals.configData.Fonts['nonstop']
        else:
            NonstopFlag = False
        # END DANGAN RONPA SPECIFIC
        
        currentColor = QtGui.QColor('white')
        
        # calculate image size
        for char in text:
            try:
                if char == '\n':
                    maxX = max(maxX, currentX)
                    currentX = 0
                    continue
                glyph = currentFont[char]
                currentX += glyph.width
                maxY = max(glyph.height, maxY)
            except:
                pass
        maxX = max(maxX, currentX)
        currentX = 0
        currentY = 0

        for line in Globals.configData.FontLines:
            maxX = max(maxX, line.x + 1)

        if maxX <= 0 or maxY <= 0:
            return

        # create image big enough to hold the text
        linecount = text.count('\n') + 1
        img = QtGui.QImage(maxX, maxY * linecount, QtGui.QImage.Format_ARGB32_Premultiplied)
        img.fill(0xFFFFFFFF)
        painter = QtGui.QPainter(img)
        painter.setCompositionMode( QtGui.QPainter.CompositionMode_Multiply )

        # draw chars into the image
        stopDrawing = False
        stopDrawList = []
        for char in text:
            try:
                if char == '\n':
                    currentY += maxY
                    currentX = 0
                    continue

                if char == '>':
                    stopDrawing = False
                    stopDrawText = ''.join(stopDrawList)

                    if Globals.configData.FontFormatting.has_key(stopDrawText):
                        fmt = Globals.configData.FontFormatting[stopDrawText]
                        currentFont = Globals.configData.Fonts[fmt.Font]

                        # DANGAN RONPA SPECIFIC
                        if stopDrawText == 'CLT' and NonstopFlag:
                            currentFont = Globals.configData.Fonts['nonstop']
                        # END DANGAN RONPA SPECIFIC

                        currentColor = fmt.Color
        
                    stopDrawList = []
                    continue
                
                if stopDrawing:
                    stopDrawList.append(char)
                    continue

                if char == '<':
                    stopDrawing = True
                    continue
                
                if not stopDrawing:
                    glyph = currentFont[char]
                    painter.drawImage(currentX, currentY + ( maxY - glyph.height ), glyph.img, glyph.x, glyph.y, glyph.width, glyph.height)
                    painter.fillRect( currentX, currentY + ( maxY - glyph.height ), glyph.width, glyph.height, currentColor )
                    currentX += glyph.width

            except:
                pass

        # draw lines into the image
        tooltip = ''
        painter.setCompositionMode( QtGui.QPainter.CompositionMode_Source )
        for line in Globals.configData.FontLines:
            try:
                if line.style == 2:
                    x1 = line.x
                    y1 = line.y
                    x2 = line.x
                    y2 = img.height() - 1
                elif line.style == 6:
                    x1 = line.x
                    y1 = line.y
                    x2 = img.width() - 1
                    y2 = line.y
                painter.setPen( line.color )
                painter.drawLine(x1, y1, x2, y2)
                tooltip += line.name + '\n'
            except:
                pass
        
        painter.end()

        piclabel = QtGui.QLabel()
        pix = QtGui.QPixmap.fromImage(img)
        piclabel.setPixmap( pix )
        piclabel.setToolTip( tooltip )
        self.layout.addWidget(piclabel)
    
    def renderText(self, text, painter):
        return

    def clearInfo(self):
        if self.layout is not None:
            old_layout = self.layout
            for i in reversed(range(old_layout.count())):
                old_layout.itemAt(i).widget().setParent(None)
            import sip
            sip.delete(old_layout)
        self.layout = QtGui.QVBoxLayout(self.scroll)
        self.setLayout(self.layout)
    
    def tempTextStuff(self):
        feedCount = text.count('\f')
        sanitizedText = re.sub('<CLT[ 0-9]+>', '', text.replace("''", "'"))
        splitOnFeeds = sanitizedText.split('\f')
        splitOnLines = sanitizedText.replace('\f', '\n').split('\n')
        longestLineChars = 0
        for s in splitOnLines:
            longestLineChars = max(longestLineChars, len(s))
        highestBoxNewlines = 0
        for s in splitOnFeeds:
            highestBoxNewlines = max(highestBoxNewlines, s.count('\n')+1)
        self.footer.setText(prepend + 'Textboxes: ' + str(feedCount+1) + ' / Highest Box: ' + str(highestBoxNewlines) + ' lines / Longest Line: ' + str(longestLineChars) + ' chars')


