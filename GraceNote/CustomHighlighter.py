# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import re

class State():
    Normal = -1
    SpellCheckFail = 1
    Tag = 2
    Parameter = 3

class CustomHighlighter( QtGui.QSyntaxHighlighter ):

    WORDS = u'(?iu)[\w\']+'
    
    def __init__( self, parent ):
        QtGui.QSyntaxHighlighter.__init__( self, parent )
        self.dict = None
        self.parent = parent
        self.Formats = {}

        #init formats
        defaultFormat = QtGui.QTextCharFormat()
        self.setFormatFor( State.Normal, defaultFormat )

        tagFormat = QtGui.QTextCharFormat()
        tagFormat.setForeground( QtGui.QColor("darkGreen") )
        tagFormat.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor( State.Tag, tagFormat )

        parameterFormat = QtGui.QTextCharFormat()
        parameterFormat.setForeground( QtGui.QColor("darkBlue") )
        parameterFormat.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor( State.Parameter, parameterFormat )

        spellCheckFormat = QtGui.QTextCharFormat()
        spellCheckFormat.setUnderlineColor( QtCore.Qt.red )
        spellCheckFormat.setUnderlineStyle( QtGui.QTextCharFormat.SpellCheckUnderline )
        self.setFormatFor( State.SpellCheckFail, spellCheckFormat )

        # DANGAN RONPA COLORS
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setForeground( QtGui.QColor(141, 22, 220) )
        self.setFormatFor( 1001, cltFormat )
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setForeground( QtGui.QColor(111, 40, 165) )
        self.setFormatFor( 1002, cltFormat )
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setForeground( QtGui.QColor(240, 120, 0) )
        self.setFormatFor( 1003, cltFormat )
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setForeground( QtGui.QColor(22, 130, 152) )
        self.setFormatFor( 1004, cltFormat )
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor( 1008, cltFormat )
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setForeground( QtGui.QColor(255, 150, 0) )
        cltFormat.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor( 1009, cltFormat )
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setForeground( QtGui.QColor(55, 140, 34) )
        self.setFormatFor( 1023, cltFormat )
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setForeground( QtGui.QColor(255, 80, 255) )
        cltFormat.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor( 1026, cltFormat )
        cltFormat = QtGui.QTextCharFormat()
        cltFormat.setForeground( QtGui.QColor(243, 32, 0) )
        self.setFormatFor( 1027, cltFormat )

    def highlightBlock( self, text ):
        length = text.length()
        pos = 0
        lastTagStart = 0
        state = self.previousBlockState()

        while pos < length:
            c = text.mid(pos, 1)
            if c == u'<': # a tag
                self.setFormat(lastTagStart, pos - lastTagStart, self.Formats[state])
                lastTagStart = pos
                state = State.Tag
            elif c == u':' and state == State.Tag: # a tag's parameter
                self.setFormat(lastTagStart, pos - lastTagStart + 1, self.Formats[state]) # format start of tag until this ':', including the ':'
                lastTagStart = pos + 1 # next start has to be after the current ':'
                state = State.Parameter
            elif c == u'>': # the end of a tag
                self.setFormat(lastTagStart, pos - lastTagStart, self.Formats[state]) # format text since last tag
                self.setFormat(pos, 1, self.Formats[State.Tag]) # format this '>'
                lastTagStart = pos + 1
                state = State.Normal

                # DANGAN RONPA SPECIFIC, generalizable if we have a generic "tag name" for color though
                # Colors text between <CLT> tags <CLT 0> <CLT 00>
                try:
                    clt = text.mid(pos - 6, 4)
                    number = -1
                    if clt == '<CLT':
                        number = int(text.mid(pos - 1, 1))
                    elif clt == 'CLT ':
                        number = int(text.mid(pos - 2, 2))
                    number += 1000
                    if self.Formats.has_key(number):
                        state = number
                except:
                    state = State.Normal
                # DANGAN RONPA SPECIFIC END

            pos += 1
        self.setFormat(lastTagStart, length - lastTagStart, self.Formats[state])
        self.setCurrentBlockState(state)

        if Globals.enchanted:
            if not self.dict:
                return
     
            text = unicode(text)
     
            for word_object in re.finditer(self.WORDS, text):
                if ord(word_object.group()[0]) > 0x79:
                    continue
                if not self.dict.check(word_object.group()):
                    self.setFormat(word_object.start(), word_object.end() - word_object.start(), self.Formats[State.SpellCheckFail])

                
                
    def setFormatFor( self, key, fmt ):
        self.Formats[key] = fmt
        self.rehighlight()


    def getFormatFor( self, key ):
        return self.Formats[key]


    def setDict(self, dict):
        self.dict = dict

