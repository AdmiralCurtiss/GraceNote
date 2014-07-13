# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from PyQt4 import QtCore, QtGui
import os
import re

class ImageMediumStruct():
    pass
class GlyphStruct():
    pass
class DatabaseTreeNode():
    # if IsCategory == True, Data is a list of DatabaseTreeNodes
    # if IsCategory == False, Data is nothing
    def __init__( self, isCategory = False, name = None, data = None ):
        self.IsCategory = isCategory
        self.Name = name
        self.Data = data

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
    TranslationStagesCountMaximum = 9
    TranslationStagesNames = ['None [0]', 'Translation [1]', 'Translation Review [2]', 'Contextual Review [3]', 'Editing [4]', 'Editing [5]', 'Editing [6]', 'Editing [7]', 'Editing [8]', 'Editing [9]']
    TranslationStagesVerbs = ['Doing Nothing', 'Translating', 'Reviewing Translations', 'Reviewing Context', 'Editing [4]', 'Editing [5]', 'Editing [6]', 'Editing [7]', 'Editing [8]', 'Editing [9]']
    TranslationStagesDescs = [  'None',
                                '<b>Translation Mode</b>\n\nTranslation mode encompasses the initial phase of translation.',
                                '<b>Translation Review Mode</b>\n\nTranslation review mode is used for when a second translator reviews an entry.',
                                '<b>Contextual Review Mode</b>\n\Contextual review mode is reserved for context and localization sensitive rewrites.',
                                '<b>Editing Mode</b>\n\Editing mode involves a full grammar, structure, phrasing, tone, and consistency check.',
                                'Editing [5]', 'Editing [6]', 'Editing [7]', 'Editing [8]', 'Editing [9]'
                              ]

    
    Images = []
    Terms = []
    Fonts = {}
    FontReplacements = []
    FontLines = []
    FontFormatting = {}
    Dictionary = []

    FileList = set()
    FileTree = None
    FileDescriptions = {}
    
    def __init__(self, configfilename):
        tree = ET.parse( configfilename )
        root = tree.getroot()

        self.ConfigFileDir = os.path.dirname(os.path.realpath(configfilename))
        
        self.ID = root.attrib.get('ID', 'UnknownID')

        self.LocalDatabasePath = self.ConfigFileDir + '/' + root.attrib['LocalDatabasePath']
        self.RemoteDatabasePath = root.attrib['RemoteDatabasePath']
        self.FTPServer = root.attrib['FTPServer']
        try:
            self.FTPPort = int( root.attrib['FTPPort'] )
        except:
            self.FTPPort = 21
        self.FTPUsername = root.attrib['FTPUsername']
        self.FTPPassword = root.attrib['FTPPassword']
        
        if root.attrib.get( 'UseGracesVoiceHash' ) == 'true':
            self.UseGracesVoiceHash = True
        else:
            self.UseGracesVoiceHash = False

        try:
            self.TranslationStagesCount = int( root.attrib['TranslationStagesCount'] )
        except:
            self.TranslationStagesCount = 4

        if root.attrib.get( 'UseLegacyApostropheSettings' ) == 'true':
            self.UseLegacyApostropheSettings = True
        else:
            self.UseLegacyApostropheSettings = False

        self.VoicePathJpPrefix = self.ConfigFileDir + '/' + root.attrib['VoicePathJpPrefix']
        self.VoicePathJpPostfix = root.attrib['VoicePathJpPostfix']
        self.VoicePathEnPrefix = self.ConfigFileDir + '/' + root.attrib['VoicePathEnPrefix']
        self.VoicePathEnPostfix = root.attrib['VoicePathEnPostfix']
        self.VoiceEntryOffset = int( root.attrib['VoiceEntryOffset'] )
        
        self.root = root

        return

    def DelayedLoad(self):
        self.LoadFileList(self.root)
        self.LoadDictionary(self.root)
        self.LoadTerms(self.root)
        self.LoadFont(self.root)
        self.LoadImages(self.root)

    def LoadFileList(self, root):
        self.FileList = set()
        self.FileTree = DatabaseTreeNode( True, 'root', [] )
        self.FileDescriptions = {}

        def AddCategory( category, parentTreeNode ):
            categoryName = category.attrib['name']
            treeNode = DatabaseTreeNode( True, categoryName, [] )
            
            subCategories = category.findall('Category')
            for cat in subCategories:
                AddCategory( cat, treeNode )

            files = category.findall('File')
            for file in files:
                databaseName = file.attrib['name']
                self.FileList.add( databaseName )
                databaseDescription = file.attrib.get('desc')
                if databaseDescription != None:
                    self.FileDescriptions[databaseName] = databaseDescription
                treeNode.Data.append( DatabaseTreeNode( False, databaseName ) )

            parentTreeNode.Data.append( treeNode )
        
        categories = root.find('Categories').findall('Category')
        for category in categories:
            AddCategory( category, self.FileTree )

       
    def LoadFont(self, root):
        try:
            fonts = root.find('Fonts').findall('Font')
            self.Fonts = {}
            for font in fonts:
                imgs = font.findall('Image')
                fontname = font.attrib['name']
                currentFont = {}
                for img in imgs:
                    path = self.ConfigFileDir + '/' + img.attrib['Path']
                    image = QtGui.QImage(path)
                    glyphs = img.findall('Glyph')
                
                    for glyph in glyphs:
                        newGlyph = GlyphStruct()
                        newGlyph.img = image
                        newGlyph.x = int(glyph.attrib['x'])
                        newGlyph.y = int(glyph.attrib['y'])
                        newGlyph.width = int(glyph.attrib['width'])
                        newGlyph.height = int(glyph.attrib['height'])
                        currentFont[glyph.attrib['char']] = newGlyph

                self.Fonts[fontname] = currentFont
        except:
            self.Fonts = {}

        try:
            repls = root.find('Fonts').findall('Replacement')
            self.FontReplacements = []
            for rep in repls:
                o = rep.attrib['old']
                n = rep.attrib['new']
                type = rep.attrib['type']
                self.FontReplacements.append( (o, n, type) )
        except:
            self.FontReplacements = []

        try:
            lines = root.find('Fonts').findall('Line')
            self.FontLines = []
            for line in lines:
                newLine = GlyphStruct()
                newLine.style = int(line.attrib['style'])
                newLine.x = int(line.attrib['x'])
                newLine.y = int(line.attrib['y'])
                newLine.color = self.GetColor( line )
                newLine.name = line.attrib['name']
                self.FontLines.append(newLine)
        except:
            self.FontLines = []

        try:
            formats = root.find('Fonts').findall('Formatting')
            self.FontFormatting = {}
            for fmt in formats:
                newFormat = GlyphStruct()
                trigger = fmt.attrib['Trigger']
                newFormat.Font = fmt.attrib['Font']
                newFormat.Color = self.GetColor( fmt )
                newFormat.Scale = float(fmt.attrib.get('Scale', 1.0))
                self.FontFormatting[trigger] = newFormat
        except:
            self.FontFormatting = {}

        return

    def GetColor(self, node):
        if node.attrib.get('color'):
            return QtGui.QColor( node.attrib['color'] )
        elif node.attrib.get('colorR') and node.attrib.get('colorG') and node.attrib.get('colorB'):
            return QtGui.QColor( int(node.attrib['colorR']), int(node.attrib['colorG']), int(node.attrib['colorB']) )
        else:
            return QtGui.QColor( 'white' )

    def LoadImages(self, root):
        try:
            self.Images = []
            imgs = root.find('Images').findall('Image')
            for img in imgs:
                newImage = ImageMediumStruct()
                newImage.name = img.attrib['Name']
                newImage.var = img.attrib['Variable']
                newImage.path = self.ConfigFileDir + '/' + img.attrib['Path']
                newImage.offs = int( img.attrib['Offset'] )
                self.Images.append(newImage)
        except:
            self.Images = []

    def LoadTerms(self, root):
        try:
            self.Terms = []
            terms = root.find('Terms').findall('Term')
            for term in terms:
                newTerm = ImageMediumStruct()
                newTerm.JP = term.attrib['JP']
                newTerm.EN = term.attrib['EN']
                self.Terms.append(newTerm)
        except:
            self.Terms = []

    def LoadDictionary(self, root):
        try:
            self.Dictionary = []
            dict = root.find('Dictionary').findall('Entry')
            for entry in dict:
                word = entry.attrib['Word']
                self.Dictionary.append(word)
        except:
            self.Dictionary = []

    def ReplaceInGameString(self, text):
        for replacement in self.FontReplacements:
            old = replacement[0]
            new = replacement[1]
            type = replacement[2]
            if type == 'simple':
                text = text.replace(old, new)
            elif type == 'regex':
                text = re.sub(old, new, text)
        return text
