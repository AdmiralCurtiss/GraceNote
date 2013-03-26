# -*- coding: utf-8 -*-

from xml.dom import minidom
from PyQt4 import QtCore, QtGui

class ImageMediumStruct():
    def __init__(self):
        return
class GlyphStruct():
    def __init__(self):
        return

class Configuration:
    ID = 'Graces'

    LocalDatabasePath = ''
    RemoteDatabasePath = ''
    
    FTPServer = ''
    FTPUsername = ''
    FTPPassword = ''
    
    UseGracesVoiceHash = False
    VoicePathJpPrefix = ''
    VoicePathJpPostfix = ''
    VoicePathEnPrefix = ''
    VoicePathEnPostfix = ''
    VoiceEntryOffset = 0
    
    Images = []
    Terms = []
    Font = {}
    FontReplacements = {}
    FontLines = []

    FileList = []
    
    def __init__(self, configfilename):
        dom = minidom.parse(configfilename)
        mainNode = dom.getElementsByTagName('GraceNoteConfig')[0]

        try:
            self.ID = mainNode.getAttribute('ID')
        except:
            self.ID = 'Graces'

        self.LocalDatabasePath = mainNode.getAttribute('LocalDatabasePath')
        self.RemoteDatabasePath = mainNode.getAttribute('RemoteDatabasePath')
        self.FTPServer = mainNode.getAttribute('FTPServer')
        self.FTPUsername = mainNode.getAttribute('FTPUsername')
        self.FTPPassword = mainNode.getAttribute('FTPPassword')
        if mainNode.getAttribute('UseGracesVoiceHash') == 'true':
            self.UseGracesVoiceHash = True
        else:
            self.UseGracesVoiceHash = False
        self.VoicePathJpPrefix = mainNode.getAttribute('VoicePathJpPrefix')
        self.VoicePathJpPostfix = mainNode.getAttribute('VoicePathJpPostfix')
        self.VoicePathEnPrefix = mainNode.getAttribute('VoicePathEnPrefix')
        self.VoicePathEnPostfix = mainNode.getAttribute('VoicePathEnPostfix')
        self.VoiceEntryOffset = int(mainNode.getAttribute('VoiceEntryOffset'))
        
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
        
        self.mainNode = mainNode
        
        return

    def DelayedLoad(self):
        self.LoadTerms(self.mainNode)
        self.LoadFont(self.mainNode)
        self.LoadImages(self.mainNode)
        
    def LoadFont(self, mainNode):
        try:
            imgs = mainNode.getElementsByTagName('Font')[0].getElementsByTagName('Image')
            self.Font = {}
            for img in imgs:
                path = img.getAttribute('Path')
                image = QtGui.QImage(path)
                glyphs = img.getElementsByTagName('Glyph')
                
                for glyph in glyphs:
                    newGlyph = GlyphStruct()
                    newGlyph.img = image
                    newGlyph.x = int(glyph.getAttribute('x'))
                    newGlyph.y = int(glyph.getAttribute('y'))
                    newGlyph.width = int(glyph.getAttribute('width'))
                    newGlyph.height = int(glyph.getAttribute('height'))
                    self.Font[glyph.getAttribute('char')] = newGlyph
        except:
            self.Font = {}

        try:
            repls = mainNode.getElementsByTagName('Font')[0].getElementsByTagName('Replacement')
            self.FontReplacements = {}
            for rep in repls:
                o = rep.getAttribute('old')
                n = rep.getAttribute('new')
                self.FontReplacements[o] = n
        except:
            self.FontReplacements = {}

        try:
            lines = mainNode.getElementsByTagName('Font')[0].getElementsByTagName('Line')
            self.FontLines = []
            for line in lines:
                #Line style="|" x="200" y="0" color="red" name="Textbox End" />
                newLine = GlyphStruct()
                newLine.style = int(line.getAttribute('style'))
                newLine.x = int(line.getAttribute('x'))
                newLine.y = int(line.getAttribute('y'))
                newLine.color = line.getAttribute('color')
                newLine.name = line.getAttribute('name')
                self.FontLines.append(newLine)
        except:
            self.FontLines = []

        return

    def LoadImages(self, mainNode):
        try:
            self.Images = []
            imgs = mainNode.getElementsByTagName('Images')[0].getElementsByTagName('Image')
            for img in imgs:
                newImage = ImageMediumStruct()
                newImage.name = img.getAttribute('Name')
                newImage.var = img.getAttribute('Variable')
                newImage.path = img.getAttribute('Path')
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
