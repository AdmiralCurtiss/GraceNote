﻿# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, Qt
import Globals
import re
from Config import GlyphStruct

class FontFormattingModes:
    # forces the output to be formatted to be <=, but as close as possible to, the preferred width
    MaximumWidth_AnyLinecount = 0
    # tries to format <= width, but will exceed it if more lines than the preferred linecount would be necessary for that
    AllowExceedWidth_MaximumLinecount = 1
    # tries to format in such a way that the resulting text is a more-or-less nice "block" and all lines are more-or-less the same length
    AutoWidth_ExactLinecount = 2

def formatText(text, font, preferredWidth, preferredLinecount, fontFormattingMode):
    treatWidthAsMaximum = True
    unformattedText = re.sub('[ \r\n]+', ' ', text).rstrip()
    if preferredLinecount < 1:
        preferredLinecount = 1

    if fontFormattingMode == FontFormattingModes.AutoWidth_ExactLinecount:
        # in this mode, figure out the rough target width by getting the width of the entire text on a single line divided by linecount
        preferredWidth = renderText( Globals.configData.ReplaceInGameString(unformattedText), None, 1, font)[0]
        preferredWidth /= preferredLinecount
        treatWidthAsMaximum = False

    unformattedtextAsCharList = []
    for char in unformattedText:
        unformattedtextAsCharList.append(char)

    # key == start of the replacement, value == (char length of replacement, horizontal pixel size of replacement)
    # used to format newlines according to how the text shows up in game, with name variables and stuff
    replacementDict = {}
        
    for replacement in Globals.configData.FontReplacements:
        old = replacement[0]
        new = replacement[1]
        type = replacement[2]
        if type == 'simple':
            idx = text.find(old, 0)
            while idx != -1:
                replacementDict[idx] = (len(old), renderText(new, None, 1, font)[0])
                idx = text.find(old, idx + len(old))
        elif type == 'regex':
            r = re.compile(old)
            match = r.search(text, pos = 0)
            while match:
                replacementDict[match.start()] = (match.end() - match.start(), renderText(new, None, 1, font)[0])
                match = r.search(text, pos = match.end() + 1)

    formattedtextAsCharList, currentWidth, currentLinecount = formatText_PlaceNewlines(unformattedtextAsCharList, font, replacementDict, preferredWidth, treatWidthAsMaximum)

    if fontFormattingMode == FontFormattingModes.AllowExceedWidth_MaximumLinecount and currentLinecount > preferredLinecount:
        # not the most efficient way to handle this but should work
        while currentLinecount > preferredLinecount:
            preferredWidth += 1
            formattedtextAsCharList, currentWidth, currentLinecount = formatText_PlaceNewlines(unformattedtextAsCharList, font, replacementDict, preferredWidth, treatWidthAsMaximum)
        
    return ''.join(formattedtextAsCharList)

def formatText_PlaceNewlines(unformattedtextAsCharList, font, replacementDict, preferredWidth, treatWidthAsMaximum):
    currentWidth = 0
    currentLinecount = 1
    lastSpaceAt = -1
    s = unformattedtextAsCharList[:] # copy the input list

    # Algorithm for this:
    # Step through newline-free string one-by-one, keep track of location of last space as well as the current width of the line
    # When current width exceeds max line length, go back to last space, replace it with newline, reset width to 0, and continue

    i = 0
    while i < len(s):
        if replacementDict.get(i) == None:
            # no replace-string here, do default character lookup
            char = s[i]

            if char == ' ':
                lastSpaceAt = i

            glyph = font.get(char)
            if glyph == None:
                glyph = font['_fallback_']
            currentWidth += glyph.width
        else:
            # skip past the replace-string
            rep = replacementDict[i]
            i += rep[0] - 1
            currentWidth += rep[1]
            char = ''

        if currentWidth > preferredWidth:
            if (treatWidthAsMaximum or char == ' ') and lastSpaceAt >= 0:
                s[lastSpaceAt] = '\n'
                currentWidth = 0
                i = lastSpaceAt
                lastSpaceAt = -1
                currentLinecount += 1

        i += 1

    return (s, currentWidth, currentLinecount)


def renderText(text, painter, lineHeight, defaultFont):

    currentFont = defaultFont
    currentColor = QtGui.QColor('white')
    currentScale = 1.0
    currentX = 0
    currentY = 0
    maxX = 0
    maxY = 0
    stopDrawing = False
    stopDrawList = []
    linecount = 1

    for char in text:
        try:
            if char == u'\u21B5': # that ↵ return symbol
                continue

            if char == '\n':
                currentY += lineHeight
                maxX = max(maxX, currentX)
                currentX = 0
                linecount += 1
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
                else:
                    # if variable doesn't exist, write it as if it was normal text
                    currentX, maxY = renderChar('<', currentFont, painter, currentX, currentY, currentScale, currentColor, lineHeight, maxY)
                    for c in stopDrawList:
                        currentX, maxY = renderChar(c, currentFont, painter, currentX, currentY, currentScale, currentColor, lineHeight, maxY)
                    currentX, maxY = renderChar('>', currentFont, painter, currentX, currentY, currentScale, currentColor, lineHeight, maxY)
        
                stopDrawList = []
                continue
                
            if stopDrawing:
                stopDrawList.append(char)
                continue

            if char == '<':
                stopDrawing = True
                continue
                
            if not stopDrawing:
                currentX, maxY = renderChar(char, currentFont, painter, currentX, currentY, currentScale, currentColor, lineHeight, maxY)
        except:
            pass
    maxX = max(maxX, currentX)
    return maxX, maxY

def renderChar(char, currentFont, painter, currentX, currentY, currentScale, currentColor, lineHeight, maxY):
    glyph = currentFont.get(char, None)
    if glyph == None:
        glyph = currentFont['_fallback_']

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

    return currentX, maxY

class FontDisplayWindow(QtGui.QDialog):

    def __init__(self, parent):
        super(FontDisplayWindow, self).__init__(None, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon('icons/font.png'))
        self.parent = parent
        self.setWindowModality(False)        
        
        self.setWindowTitle("Font Display")
        self.imagelabel = QtGui.QLabel()
        self.imagelabel.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.scroll = QtGui.QScrollArea()
        self.scroll.setWidget(self.imagelabel)
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.scroll)
        self.layout.setMargin(0)
        self.setLayout(self.layout)

        geom = Globals.Settings.value('Geometry/FontDisplayWindow')
        if geom is not None:
            self.restoreGeometry(geom)
        else:
            self.resize(500, 150)

        self.IsAlwaysOnTop = False
        self.ShowingJpnDimensions = True

    def AlwaysOnTopToggle(self, enabled):
        if enabled:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            self.IsAlwaysOnTop = True
        else:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            self.IsAlwaysOnTop = False
        self.show()
                   
    def drawText(self, text, japaneseText = None, databaseDesc = None): # database desc is only passed for Dangan Ronpa!! can be removed in generic GN version
        if not Globals.configData.Fonts:
            return

        text = text.replace('\f', '\n')
        text = Globals.VariableReplace(text)
        text = Globals.configData.ReplaceInGameString(text)

        if japaneseText != None:
            japaneseText = japaneseText.replace('\f', '\n')
            japaneseText = Globals.VariableReplace(japaneseText)
            japaneseText = Globals.configData.ReplaceInGameString(japaneseText)

        maxX = 0
        maxY = 0
        currentFont = Globals.configData.Fonts['default']
        
        # DANGAN RONPA SPECIFIC
        if re.match('e0[0-9]_1[0-9][0-9]_001.lin', databaseDesc):
            currentFont = Globals.configData.Fonts['nonstop']
        # END DANGAN RONPA SPECIFIC

        # calculate image size
        maxX, maxY = renderText(text, None, 0, currentFont)

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
        renderText(text, painter, maxY, currentFont)

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

        # if japanese text was given, mark its dimensions in the image as well
        if japaneseText != None and self.ShowingJpnDimensions:
            jpnX, jpnY = renderText( japaneseText, None, 0, currentFont )
            jpnY *= (japaneseText.count('\n') + 1)
            painter.setPen( Qt.QColor( 'magenta' ) )
            painter.drawLine( jpnX - 1, 0, jpnX - 1, img.height() - 1 )
            painter.drawLine( 0, jpnY - 1, img.width() - 1, jpnY - 1 )
            tooltip += 'Magenta: Dimensions of original Japanese string (might not be accurate)'

        
        painter.end()

        pix = QtGui.QPixmap.fromImage( img )
        self.imagelabel.setPixmap( pix )
        self.imagelabel.setFixedSize( pix.size() )
        self.imagelabel.setToolTip( tooltip )
        self.imagelabel.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.imagelabel.update()
   
    def clearInfo(self):
        self.imagelabel.clear()
        return

    def closeEvent(self, event):
        Globals.Settings.setValue('Geometry/FontDisplayWindow', self.saveGeometry())
    
    def contextMenuEvent(self, event):
        rightClickMenu = QtGui.QMenu()
        
        actionAlwaysOnTop = QtGui.QAction('Always on Top', rightClickMenu)
        actionAlwaysOnTop.setCheckable(True)
        actionAlwaysOnTop.setChecked(self.IsAlwaysOnTop)
        actionAlwaysOnTop.triggered.connect(self.contextMenuClickAlwaysOnTopToggle)
        rightClickMenu.addAction(actionAlwaysOnTop)

        actionShowJpnDimensions = QtGui.QAction('Japanese Dimensions (Magenta)', rightClickMenu)
        actionShowJpnDimensions.setCheckable(True)
        actionShowJpnDimensions.setChecked(self.ShowingJpnDimensions)
        actionShowJpnDimensions.triggered.connect(self.contextMenuClickShowJpnDimensionsToggle)
        rightClickMenu.addAction(actionShowJpnDimensions)
    
        rightClickMenu.exec_(event.globalPos())

    def contextMenuClickAlwaysOnTopToggle(self, enabled):
        if self.IsAlwaysOnTop:
            self.AlwaysOnTopToggle(False)
        else:
            self.AlwaysOnTopToggle(True)
        return

    def contextMenuClickShowJpnDimensionsToggle(self, enabled):
        if self.ShowingJpnDimensions:
            self.ShowingJpnDimensions = False
        else:
            self.ShowingJpnDimensions = True
        return

