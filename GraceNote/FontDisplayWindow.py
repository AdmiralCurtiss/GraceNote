# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
#import re
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
        
    def drawText(self, text):
        self.clearInfo()

        img = QtGui.QImage(400, 100, QtGui.QImage.Format_ARGB32_Premultiplied)
        img.fill(0xFFFFFFFF)
        painter = QtGui.QPainter(img)
        currentX = 0
        currentY = 0
        for char in text:
            try:
                glyph = Globals.configData.Font[char]
                painter.drawImage(currentX, currentY, glyph.img, glyph.x, glyph.y, glyph.width, glyph.height)
                currentX += glyph.width
            except:
                pass
        painter.end()

        piclabel = QtGui.QLabel()
        piclabel.setPixmap(QtGui.QPixmap.fromImage(img))
        self.layout.addWidget(piclabel)
    
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


