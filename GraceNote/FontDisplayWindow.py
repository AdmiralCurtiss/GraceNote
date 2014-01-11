﻿# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, Qt
import Globals
import re
from Config import GlyphStruct

class FontDisplayWindow(QtGui.QDialog):

    def __init__(self, parent):
        super(FontDisplayWindow, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QtGui.QIcon('icons/font.png'))
        self.parent = parent
        self.setWindowModality(False)        
        
        self.setWindowTitle("Font Display")
        self.scroll = QtGui.QScrollArea()
        self.layout = QtGui.QVBoxLayout(self.scroll)
        self.layout.setMargin(0)
        self.setLayout(self.layout)

        geom = Globals.Settings.value('Geometry/FontDisplayWindow')
        if geom is not None:
            self.restoreGeometry(geom)
        else:
            self.resize(500, 150)

        self.IsAlwaysOnTop = False

    def AlwaysOnTopToggle(self, enabled):
        if enabled:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            self.IsAlwaysOnTop = True
        else:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            self.IsAlwaysOnTop = False
        self.show()
                   
    def drawText(self, text, databaseDesc): # database desc is only passed for Dangan Ronpa!! can be removed in generic GN version
        if not Globals.configData.Fonts:
            return

        self.clearInfo()

        text = text.replace('\f', '\n')
        text = Globals.VariableReplace(text)
        for old, new in Globals.configData.FontReplacements.iteritems():
            text = text.replace(old, new)

        maxX = 0
        maxY = 0
        currentFont = Globals.configData.Fonts['default']
        
        # DANGAN RONPA SPECIFIC
        if re.match('e0[0-9]_1[0-9][0-9]_001.lin', databaseDesc):
            currentFont = Globals.configData.Fonts['nonstop']
        # END DANGAN RONPA SPECIFIC

        # calculate image size
        maxX, maxY = self.renderText(text, None, 0, currentFont)

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
        self.renderText(text, painter, maxY, currentFont)

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
        piclabel.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.layout.addWidget(piclabel)
        self.layout.addStretch()
        
        # all of these resizing things seem to add a huge overhead, sadly
        # part of the overhead might be the way I clear the window, there's probably be a better way to do that
        # best compromise right now is probably to just resize back down on database change,
        # then change the image so it's always in the top left no matter how big the window is
        #self.updateGeometry()
        #self.resize(self.sizeHint())
        #self.resize(img.width(), img.height())
    
    def renderText(self, text, painter, lineHeight, defaultFont):

        currentFont = defaultFont
        currentColor = QtGui.QColor('white')
        currentScale = 1.0
        currentX = 0
        currentY = 0
        maxX = 0
        maxY = 0
        stopDrawing = False
        stopDrawList = []

        for char in text:
            try:
                if char == '\n':
                    currentY += lineHeight
                    maxX = max(maxX, currentX)
                    currentX = 0
                    continue

                if char == '>':
                    stopDrawing = False
                    stopDrawText = ''.join(stopDrawList)

                    if Globals.configData.FontFormatting.has_key(stopDrawText):
                        fmt = Globals.configData.FontFormatting[stopDrawText]
                        currentFont = Globals.configData.Fonts[fmt.Font]

                        # DANGAN RONPA SPECIFIC
                        if stopDrawText == 'CLT':
                            currentFont = defaultFont
                        # END DANGAN RONPA SPECIFIC

                        currentColor = fmt.Color
                        currentScale = fmt.Scale
        
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

                    if currentScale != 1.0:
                        newGlyph = GlyphStruct()
                        newGlyph.img = glyph.img.copy(glyph.x, glyph.y, glyph.width, glyph.height).scaled(glyph.width * currentScale, glyph.height * currentScale, Qt.Qt.IgnoreAspectRatio, Qt.Qt.SmoothTransformation)
                        newGlyph.x = 0
                        newGlyph.y = 0
                        newGlyph.width = newGlyph.img.width()
                        newGlyph.height = newGlyph.img.height()
                        glyph = newGlyph

                    if painter is not None: # actually render
                        painter.drawImage(currentX, currentY + ( lineHeight - glyph.height ), glyph.img, glyph.x, glyph.y, glyph.width, glyph.height)
                        painter.fillRect( currentX, currentY + ( lineHeight - glyph.height ), glyph.width, glyph.height, currentColor )
                        currentX += glyph.width
                    else: # just calculate the image size
                        currentX += glyph.width
                        maxY = max(glyph.height, maxY)
            except:
                pass
        maxX = max(maxX, currentX)
        return maxX, maxY

    def clearInfo(self):
        if self.layout is not None:
            old_layout = self.layout
            for i in reversed(range(old_layout.count())):
                if old_layout.itemAt(i).widget() is not None:
                    old_layout.itemAt(i).widget().setParent(None)
            import sip
            sip.delete(old_layout)
        self.layout = QtGui.QVBoxLayout(self.scroll)
        self.layout.setMargin(0)
        self.setLayout(self.layout)

    def clearAndResize(self):
        self.clearInfo()
        self.resize(128, 32)

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/FontDisplayWindow', self.saveGeometry())
    
    def contextMenuEvent(self, event):
        rightClickMenu = QtGui.QMenu()
        
        action = QtGui.QAction('Toggle Always on Top', rightClickMenu)
        action.setChecked(self.IsAlwaysOnTop)
        action.triggered.connect(self.contextMenuClickAlwaysOnTopToggle)
        rightClickMenu.addAction(action)
    
        rightClickMenu.exec_(event.globalPos())

    def contextMenuClickAlwaysOnTopToggle(self, enabled):
        if self.IsAlwaysOnTop:
            self.AlwaysOnTopToggle(False)
        else:
            self.AlwaysOnTopToggle(True)
        return

