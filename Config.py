from xml.dom import minidom

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
        
        self.FileList = [ [] ]
        categories = mainNode.getElementsByTagName('Categories')[0].getElementsByTagName('Category')
        categorycounter = 0
        for category in categories:
            categorycounter = categorycounter + 1
            self.FileList[0].append(category.getAttribute('name'))
            files = category.getElementsByTagName('File')
            
            newfiles = []
            for file in files:
                newfiles.append(file.getAttribute('name'))
            self.FileList.append(newfiles)
            
        return
