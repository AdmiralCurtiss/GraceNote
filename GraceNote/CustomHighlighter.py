# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import re

class CustomHighlighter( QtGui.QSyntaxHighlighter ):

    WORDS = u'(?iu)[\w\']+'
    
    def __init__( self, parent, theme ):
        self.dict = None
        QtGui.QSyntaxHighlighter.__init__( self, parent )
        self.parent = parent
        self.stateDic={'normalState':-1,'inPrefix':0,'inPostfix':1,'inName':2}
        self.m_formats= {'othtag':0,'postfix':1,'prefix':2,'name':3}
        #init formats
        darkBlue = QtGui.QColor()
        darkBlue.setNamedColor("darkBlue")
        darkRed = QtGui.QColor()
        darkRed.setNamedColor("darkRed")
        darkGreen = QtGui.QColor()
        darkGreen.setNamedColor("darkGreen")
        entityFmt = QtGui.QTextCharFormat()
        entityFmt.setForeground( darkBlue )
        entityFmt.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor('othtag',entityFmt)
        tagFmt = QtGui.QTextCharFormat()
        tagFmt.setForeground( darkGreen )
        tagFmt.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor('postfix',tagFmt)
        commentFmt = QtGui.QTextCharFormat()
        commentFmt.setForeground( darkRed )
        commentFmt.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor('prefix',commentFmt)
        nameFmt = QtGui.QTextCharFormat()
        nameFmt.setForeground( darkRed )
        nameFmt.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor('name',entityFmt)


    def highlightBlock( self, text ):
        state = self.previousBlockState()
        length = text.length()
        start = 0
        pos = 0
        while pos < length:
            if state == self.stateDic['normalState']:
                while pos < length:
                    if  text.mid(pos, 1) == u'<':
                        if text.mid(pos, 2) == u'<C':
                            state = self.stateDic['inPrefix']
                        else:
                            state = self.stateDic['inPostfix']
                        break
                    else:
                        pos=pos+1
                continue
            if state == self.stateDic['inPrefix']:
                start = pos
                while pos < length:
                    if  text.mid(pos, 1) == u'>' :
                        pos=pos+1
                        state = self.stateDic['inName']
                        break
                    else:
                        pos=pos+1
                self.setFormat(start, pos - start, self.m_formats['prefix'])
                continue
            if state == self.stateDic['inPostfix']:
                start = pos
                while pos < length :
                    if  text.mid(pos, 1) == u'>':
                        pos=pos+1
                        state = self.stateDic['normalState']
                        break
                    else :
                        pos=pos+1
                self.setFormat(start, pos - start, self.m_formats['postfix'])
                continue
            if  state==self.stateDic['inName'] :
                start = pos
                while pos < length :
                    if  text.mid(pos, 1) == u'<':
                        if text.mid(pos, 2) == u'<C' :
                            state = self.stateDic['inPrefix']
                        else :
                            state = self.stateDic['inPostfix']
                        break
                    else :
                        pos=pos+1
                self.setFormat(start, pos - start, self.m_formats['name'])
                continue
        self.setCurrentBlockState(state)

        if Globals.enchanted:
            if not self.dict:
                return
     
            text = unicode(text)
     
            charFormat = QtGui.QTextCharFormat()
            charFormat.setUnderlineColor(QtCore.Qt.red)
            charFormat.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
          
            for word_object in re.finditer(self.WORDS, text):
                if ord(word_object.group()[0]) > 0x79:
                    continue
                if not self.dict.check(word_object.group()):
                    self.setFormat(word_object.start(),
                        word_object.end() - word_object.start(), charFormat)

                
                
    def setFormatFor( self,cons,qformat):
        self.m_formats[cons]=qformat
        self.rehighlight()


    def getFormatFor( self, cons):
        return self.m_formats[cons]


    def setDict(self, dict):
        self.dict = dict

