﻿# -*- coding: utf-8 -*-

from xml.dom import minidom
from PyQt4 import QtCore, QtGui

class ImageMediumStruct():
    def __init__(self):
        return
class GlyphStruct():
    def __init__(self):
        return

class Configuration:
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

    FileList = []
    
    def __init__(self, configfilename):
        dom = minidom.parse(configfilename)
        mainNode = dom.getElementsByTagName('GraceNoteConfig')[0]
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
            self.Font = {}
            imgs = mainNode.getElementsByTagName('Font')[0].getElementsByTagName('Image')
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
