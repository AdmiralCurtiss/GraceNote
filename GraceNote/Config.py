# -*- coding: utf-8 -*-

from xml.dom import minidom

class ImageMediumStruct():
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
            
        return
