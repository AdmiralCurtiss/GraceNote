# -*- coding: utf-8 -*-

from xml.dom import minidom
from PyQt4 import QtCore, QtGui
import os

class ImageMediumStruct():
    def __init__(self):
        return
class GlyphStruct():
    def __init__(self):
        return

class Configuration:
    ID = 'UnknownID'

    LocalDatabasePath = ''
    RemoteDatabasePath = ''
    
    FTPServer = ''
    FTPPort = 21
    FTPUsername = ''
    FTPPassword = ''
    
    UseGracesVoiceHash = False
    UseLegacyApostropheSettings = False
    VoicePathJpPrefix = ''
    VoicePathJpPostfix = ''
    VoicePathEnPrefix = ''
    VoicePathEnPostfix = ''
    VoiceEntryOffset = 0

    TranslationStagesCount = 4
    TranslationStagesNames = ['Nothing [0]', 'Translation [1]', 'Translation Review [2]', 'Contextual Review [3]', 'Editing [4]', 'Editing [5]', 'Editing [6]', 'Editing [7]', 'Editing [8]', 'Editing [9]']
    TranslationStagesDescs = [  'Nothing',
                                '<b>Translation Mode</b>\n\nTranslation mode encompasses the initial phase of translation.',
                                '<b>Translation Review Mode</b>\n\nTranslation review mode is used for when a second translator reviews an entry.',
                                '<b>Contextual Review Mode</b>\n\Contextual review mode is reserved for context and localization sensitive rewrites.',
                                '<b>Editing Mode</b>\n\Editing mode involves a full grammar, structure, phrasing, tone, and consistency check.',
                                'Editing [5]', 'Editing [6]', 'Editing [7]', 'Editing [8]', 'Editing [9]'
                              ]
    
    Images = []
    Terms = []
    Fonts = {}
    FontReplacements = {}
    FontLines = []
    FontFormatting = {}
    Dictionary = []

    FileList = []
    
    def __init__(self, configfilename):
        dom = minidom.parse(configfilename)
        mainNode = dom.getElementsByTagName('GraceNoteConfig')[0]

        self.ConfigFileDir = os.path.dirname(os.path.realpath(configfilename))

        try:
            self.ID = mainNode.getAttribute('ID')
            if self.ID == '':
                self.ID = 'UnknownID'
        except:
            self.ID = 'UnknownID'

        self.LocalDatabasePath = self.ConfigFileDir + '/' + mainNode.getAttribute('LocalDatabasePath')
        self.RemoteDatabasePath = mainNode.getAttribute('RemoteDatabasePath')
        self.FTPServer = mainNode.getAttribute('FTPServer')
        try:
            self.FTPPort = int(mainNode.getAttribute('FTPPort'))
        except:
            self.FTPPort = 21
        self.FTPUsername = mainNode.getAttribute('FTPUsername')
        self.FTPPassword = mainNode.getAttribute('FTPPassword')
        if mainNode.getAttribute('UseGracesVoiceHash') == 'true':
            self.UseGracesVoiceHash = True
        else:
            self.UseGracesVoiceHash = False

        try:
            if mainNode.getAttribute('UseLegacyApostropheSettings') == 'true':
                self.UseLegacyApostropheSettings = True
        except:
            self.UseLegacyApostropheSettings = False

        self.VoicePathJpPrefix = self.ConfigFileDir + '/' + mainNode.getAttribute('VoicePathJpPrefix')
        self.VoicePathJpPostfix = mainNode.getAttribute('VoicePathJpPostfix')
        self.VoicePathEnPrefix = self.ConfigFileDir + '/' + mainNode.getAttribute('VoicePathEnPrefix')
        self.VoicePathEnPostfix = mainNode.getAttribute('VoicePathEnPostfix')
        self.VoiceEntryOffset = int(mainNode.getAttribute('VoiceEntryOffset'))
        
        self.mainNode = mainNode

        return

    def DelayedLoad(self):
        self.LoadFileList(self.mainNode)
        self.LoadDictionary(self.mainNode)
        self.LoadTerms(self.mainNode)
        self.LoadFont(self.mainNode)
        self.LoadImages(self.mainNode)

    def LoadFileList(self, mainNode):
        self.FileList = [ [] ]
        categories = mainNode.getElementsByTagName('Categories')[0].getElementsByTagName('Category')
        categorycounter = 0
        for category in categories:
            categorycounter = categorycounter + 1
            self.FileList[0].append(category.getAttribute('name'))
            files = category.getElementsByTagName('File')
            
            newfiles = []
            for filename in files:
                newfiles.append(filename.getAttribute('name'))
            self.FileList.append(newfiles)
        
    def LoadFont(self, mainNode):
        try:
            fonts = mainNode.getElementsByTagName('Fonts')[0].getElementsByTagName('Font')
            self.Fonts = {}
            for font in fonts:
                imgs = font.getElementsByTagName('Image')
                fontname = font.getAttribute('name')
                currentFont = {}
                for img in imgs:
                    path = self.ConfigFileDir + '/' + img.getAttribute('Path')
                    image = QtGui.QImage(path)
                    glyphs = img.getElementsByTagName('Glyph')
                
                    for glyph in glyphs:
                        newGlyph = GlyphStruct()
                        newGlyph.img = image
                        newGlyph.x = int(glyph.getAttribute('x'))
                        newGlyph.y = int(glyph.getAttribute('y'))
                        newGlyph.width = int(glyph.getAttribute('width'))
                        newGlyph.height = int(glyph.getAttribute('height'))
                        currentFont[glyph.getAttribute('char')] = newGlyph

                self.Fonts[fontname] = currentFont
        except:
            self.Fonts = {}

        try:
            repls = mainNode.getElementsByTagName('Fonts')[0].getElementsByTagName('Replacement')
            self.FontReplacements = {}
            for rep in repls:
                o = rep.getAttribute('old')
                n = rep.getAttribute('new')
                self.FontReplacements[o] = n
        except:
            self.FontReplacements = {}

        try:
            lines = mainNode.getElementsByTagName('Fonts')[0].getElementsByTagName('Line')
            self.FontLines = []
            for line in lines:
                newLine = GlyphStruct()
                newLine.style = int(line.getAttribute('style'))
                newLine.x = int(line.getAttribute('x'))
                newLine.y = int(line.getAttribute('y'))
                newLine.color = self.GetColor( line )
                newLine.name = line.getAttribute('name')
                self.FontLines.append(newLine)
        except:
            self.FontLines = []

        try:
            formats = mainNode.getElementsByTagName('Fonts')[0].getElementsByTagName('Formatting')
            self.FontFormatting = {}
            for fmt in formats:
                newFormat = GlyphStruct()
                trigger = fmt.getAttribute('Trigger')
                newFormat.Font = fmt.getAttribute('Font')
                newFormat.Color = self.GetColor(fmt)
                if fmt.hasAttribute('Scale'):
                    newFormat.Scale = float(fmt.getAttribute('Scale'))
                else:
                    newFormat.Scale = 1.0
                self.FontFormatting[trigger] = newFormat
        except:
            self.FontFormatting = {}

        return

    def GetColor(self, node):
        if node.hasAttribute('color'):
            return QtGui.QColor( node.getAttribute('color') )
        elif node.hasAttribute('colorR') and node.hasAttribute('colorG') and node.hasAttribute('colorB'):
            return QtGui.QColor( int(node.getAttribute('colorR')), int(node.getAttribute('colorG')), int(node.getAttribute('colorB')) )
        else:
            return QtGui.QColor( 'white' )

    def LoadImages(self, mainNode):
        try:
            self.Images = []
            imgs = mainNode.getElementsByTagName('Images')[0].getElementsByTagName('Image')
            for img in imgs:
                newImage = ImageMediumStruct()
                newImage.name = img.getAttribute('Name')
                newImage.var = img.getAttribute('Variable')
                newImage.path = self.ConfigFileDir + '/' + img.getAttribute('Path')
                newImage.offs = int(img.getAttribute('Offset'))
                self.Images.append(newImage)
        except:
            self.Images = []

    def LoadTerms(self, mainNode):
        try:
            self.Terms = []
            terms = mainNode.getElementsByTagName('Terms')[0].getElementsByTagName('Term')
            for term in terms:
                newTerm = ImageMediumStruct()
                newTerm.JP = term.getAttribute('JP')
                newTerm.EN = term.getAttribute('EN')
                self.Terms.append(newTerm)
        except:
            self.Terms = []

    def LoadDictionary(self, mainNode):
        try:
            self.Dictionary = []
            dict = mainNode.getElementsByTagName('Dictionary')[0].getElementsByTagName('Entry')
            for entry in dict:
                word = entry.getAttribute('Word')
                self.Dictionary.append(word)
        except:
            self.Dictionary = []

