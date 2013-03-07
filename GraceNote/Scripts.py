﻿# -*- coding: utf-8 -*-

# This is only needed for Python v2 but is harmless for Python v3.
import sip
sip.setapi('QVariant', 2)


################################################
# Things to do:
#
#   - Toolbar Customization
#   - Status Bar (last edited, shows mode?, shows role?)
#   - Fix enemy parsing, item parsing
#   
#   - Auto-check the database folder for integrity
#   - Duplicate checking feature
#
################################################

import Globals
Globals.commentsAvailableLabel = False


from PyQt4 import QtCore, QtGui
import sqlite3
import os, sys, re, time, struct, platform
import shutil, base64
import ftplib
from ftplib import FTP
from binascii import hexlify, unhexlify
import subprocess
import codecs
from Config import *
from collections import deque
import filecmp

from XTextBox import *
from CustomHighlighter import *
from MassReplace import *
from GlobalChangelog import *
from LocalChangelog import *
from Statistics import *
from DuplicateText import *
from CompletionTable import *
from ImageViewerWindow import *

# load config
try:
    Globals.configfile = sys.argv[1]
except:
    Globals.configfile = 'config.xml'
print 'Loading configuration: ' + Globals.configfile
Globals.configData = Configuration(Globals.configfile)

# load graces folder config if it's available
try:
    Globals.configDataGracesFolders = Configuration('config_graces_byfolder.xml').FileList
except:
    Globals.configDataGracesFolders = [[]]

if os.path.exists('hashtable.py'):
    from hashtable import hashtable
    Globals.HashTableExists = True
else:
    Globals.HashTableExists = False

# create CompletionPercentage if it doesn't exist
if not os.path.exists(Globals.configData.LocalDatabasePath + '/CompletionPercentage'):
    CreateConnection = sqlite3.connect(Globals.configData.LocalDatabasePath + '/CompletionPercentage')
    CreateCursor = CreateConnection.cursor()
    CreateCursor.execute("CREATE TABLE Percentages (Database TEXT PRIMARY KEY, entries INT, translation INT, editing1 INT, editing2 INT, editing3 INT, comments INT)")
    CreateConnection.commit()

try:
    import enchant
    Globals.enchanted = True
except ImportError:
    Globals.enchanted = False
    print 'No pyenchant found. Spell checking will not be available.'


os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

Globals.ConnectionGracesJapanese = sqlite3.connect(Globals.configData.LocalDatabasePath + '/GracesJapanese')
Globals.CursorGracesJapanese = Globals.ConnectionGracesJapanese.cursor()

Globals.LogCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/ChangeLog')
Globals.LogCur = Globals.LogCon.cursor()

Globals.EnglishVoiceLanguageFlag = False
Globals.UpdateLowerStatusFlag = False
Globals.ModeFlag = 'Semi-Auto'
Globals.AmountEditingWindows = 5
Globals.WriteDatabaseStorageToHddOnEntryChange = False
Globals.FooterVisibleFlag = False

class SpellAction(QtGui.QAction):
    correct = QtCore.pyqtSignal(unicode)
 
    def __init__(self, *args):
        QtGui.QAction.__init__(self, *args)
 
        self.triggered.connect(lambda x: self.correct.emit(
            unicode(self.text())))

class SearchAction(QtGui.QAction):
 
    jumpTo = QtCore.pyqtSignal(unicode, int)
 
    def __init__(self, *args):
        QtGui.QAction.__init__(self, *args)
 
        self.triggered.connect(lambda x: self.jumpTo.emit(self.data()[0], self.data()[1]))

class DatabaseEntryStruct():
    def __init__(self, cleanString, databaseName, entry, role, state):
        #string cleanString; // this is the actual entry text
        self.cleanString = cleanString
        #string database;
        self.databaseName = databaseName
        #int entry;
        self.entry = entry
        #int role;
        self.role = role
        #string state; // "ENG" or "COM", defines which column in the database to update
        self.state = state
        self.timestamp = time.clock()

class Scripts2(QtGui.QWidget):

    def __init__(self, parent=None):
        super(Scripts2, self).__init__(parent)
        
        self.parent = parent

        self.splashScreen = SplashScreen()

        self.splashScreen.show()
        self.splashScreen.raise_()
        self.splashScreen.activateWindow()
        

        # Current Variables
        self.state = 'ENG'
        self.text = []

        # True Entries Translated Count
#        TrueCount()
             
        # Settings
        self.settings = QtCore.QSettings("GracesTranslation", "Grace Note")
        if not self.settings.contains('author'):
            text, ok = QtGui.QInputDialog.getText(self, "Enter your Name", "Author name:", QtGui.QLineEdit.Normal)
            if ok and text != '':
                self.settings.setValue('author', text)

        self.author = self.settings.value('author')
        self.update = self.settings.value('update')
        self.databaseWriteStorage = deque()
        
        #self.update = ['DRBO2397','DRBO2400','DRBO2403','DRBO2408','DRBO2411','DRBO2414','DRBO2417','DRBO2420','DRBO2602','DRBO2605','DRBO2610','DRBO2613','DRBO2616','DRBO2619','DRBO2624','DRBO2627','DRBO2630','DRBO2893','DRBO2898','DRBO2901','DRBO2906','DRBO2909','DRBO2912','DRBO2915','DRBO2918','DRBO2921','DRBO2924','DRBO2927','DRBO3079','DRBO3082','DRBO3085','DRBO3090','DRBO3097','DRBO3100','DRBO3105','DRBO3108','DRBO3353','DRBO3356','DRBO3363','DRBO3368','DRBO3371','DRBO3374','DRBO3377','DRBO3380','DRBO3385','DRBO3526','DRBO3531','DRBO3534','DRBO3537','DRBO3540','DRBO3547','DRBO3550','DRBO3565','DRBO3569','DRBO3576']

        if self.update == None:
            self.update = set()

        if not isinstance(self.update, set):
            print "That's weird, your update log has gotten corrupted.\nAttempting to retrieve whatever possible."
            try:
                a = set()
                for x in self.update:
                    a.add(str(x))
                self.update = a
            except:
                self.update = set()
        print str(len(self.update)) + ' files retained from last session: ', ''.join(["%s, " % (k) for k in self.update])[:-2]

        if self.settings.contains('role'):
            self.role = int(self.settings.value('role'))
        else:
            self.role = 1

        if self.settings.contains('mode'):
            Globals.ModeFlag = self.settings.value('mode')
        else:
            self.settings.setValue('mode', 'Semi-Auto')
            Globals.ModeFlag = 'Semi-Auto'
        
        if self.settings.contains('voicelanguage'):
            Globals.EnglishVoiceLanguageFlag = self.settings.value('voicelanguage') == 'EN'
        else:
            self.settings.setValue('voicelanguage', 'JP')
            Globals.EnglishVoiceLanguageFlag = False
        
        if self.settings.contains('updatelowerstatus'):
            Globals.UpdateLowerStatusFlag = self.settings.value('updatelowerstatus') == 'True'
        else:
            self.settings.setValue('updatelowerstatus', 'False')
            Globals.UpdateLowerStatusFlag = False
        
        if self.settings.contains('writeonentrychange'):
            Globals.WriteDatabaseStorageToHddOnEntryChange = self.settings.value('writeonentrychange') == 'True'
        else:
            self.settings.setValue('writeonentrychange', 'False')
            Globals.WriteDatabaseStorageToHddOnEntryChange = False
        
        if self.settings.contains('footervisible'):
            Globals.FooterVisibleFlag = self.settings.value('footervisible') == 'True'
        else:
            self.settings.setValue('footervisible', 'False')
            Globals.FooterVisibleFlag = False
        
        if self.settings.contains('editpane_amount'):
            Globals.AmountEditingWindows = int(self.settings.value('editpane_amount'))
        else:
            self.settings.setValue('editpane_amount', '5')
            Globals.AmountEditingWindows = 5
        if Globals.AmountEditingWindows < 3 or Globals.AmountEditingWindows > 25:
            Globals.AmountEditingWindows = 5

        self.roletext = ['', 'Translating', 'Reviewing Translations', 'Reviewing Context', 'Editing']

        self.parent.setWindowTitle("Grace Note - {0} in {1} mode".format(self.roletext[self.role] , Globals.ModeFlag))
        #>>> Globals.CursorGracesJapanese.execute('create table Log(ID int primary key, File text, Name text, Timestamp int)')


        # Grab the changes
        self.RetrieveModifiedFiles(self.splashScreen)

        self.splashScreen.destroyScreen()
        
        
        # List View of Files
        self.tree = QtGui.QTreeView()
        self.treemodel = QtGui.QStandardItemModel()

        self.tree.setAnimated(True)
        self.tree.setIndentation(10)
        self.tree.setSortingEnabled(False)
        #self.tree.setFixedWidth(190)
        self.tree.sortByColumn(1, 0)
        self.tree.setHeaderHidden(True)
        
        self.PopulateModel(Globals.configData.FileList)

#        self.treemodel = QtGui.QSortFilterProxyModel()
#        self.treemodel.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)


#        self.treemodel.setSourceModel(self.treemodel)
        self.tree.setModel(self.treemodel)


        # List View of Entries
        self.entry = QtGui.QListView()
        self.entry.setWrapping(False)
        self.entrymodel = QtGui.QStandardItemModel()

        #self.entry.setFixedWidth(180)
 
        self.entrysort = QtGui.QSortFilterProxyModel()
        self.entrysort.setSourceModel(self.entrymodel)
        self.entry.setModel(self.entrysort)


        # Text Edits
        self.regularEditingTextBoxes = []
        self.twoupEditingTextBoxes = []
        self.textEditingBoxes = []
        self.textEditingFooters = []
        self.twoupEditingFooters = []
        for i in range(Globals.AmountEditingWindows):
            # create text boxes, set defaults
            tb1 = XTextBox(None, self)
            tb2 = XTextBox('jp', self)
            tb2.hide()
            tb2.setReadOnly(True)
            CustomHighlighter(tb2, 'something')
            if self.settings.contains('font'):
                size = int(self.settings.value('font'))
                tb1.setFontPointSize(size)
                tb2.setFontPointSize(size)
            self.regularEditingTextBoxes.append(tb1)
            self.twoupEditingTextBoxes.append(tb2)
            
            footer = QtGui.QLabel('')
            self.textEditingFooters.append(footer)
            tb1.setFooter(footer)
            footer2 = QtGui.QLabel('')
            self.twoupEditingFooters.append(footer2)
            tb2.setFooter(footer2)
            
            # create layout
            tmplayout = QtGui.QGridLayout()
            tmplayout.addWidget(tb1, 1, 1, 1, 1)
            tmplayout.addWidget(tb2, 1, 2, 1, 1)
            if Globals.FooterVisibleFlag:
                tmplayout.addWidget(footer, 2, 1, 1, 2)
                tmplayout.addWidget(footer2, 3, 1, 1, 2)
            
            # create QGroupBox
            tmpqgrpbox = QtGui.QGroupBox()
            tmpqgrpbox.setLayout(tmplayout)
            tmpqgrpbox.setTitle("-----")
            if Globals.FooterVisibleFlag:
                tmpqgrpbox.setFlat(True)
            self.textEditingBoxes.append(tmpqgrpbox)
            
        # ------------------------------------------------------ #

        # Filter Input
        self.filter = QtGui.QLineEdit()
        self.filter.setFixedWidth(200)
        self.jumptobox = QtGui.QLineEdit()
        self.jumptobox.setFixedWidth(120)
        
        self.debug = QtGui.QAction(QtGui.QIcon('icons/debugoff.png'), 'Display Debug', None)
        self.debug.setCheckable(True)
        self.debug.setChecked(0)
        
        # Connections
        self.tree.selectionModel().selectionChanged.connect(self.PopulateEntryList)
        self.entry.selectionModel().selectionChanged.connect(self.PopulateTextEdit)
        self.entry.clicked.connect(self.UpdateDebug)
        #self.entry.pressed.connect(self.UpdateDebug)
        for editbox in self.regularEditingTextBoxes:
            editbox.manualEdit.connect(self.UpdateTextGenericFunc)
        self.debug.toggled.connect(self.DebugFilter)
        self.filter.returnPressed.connect(self.LiveSearch)
        self.jumptobox.returnPressed.connect(self.JumpToDatabase)

        # Toolbar
        FlexibleSpace = QtGui.QLabel('')
        FlexibleSpace.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        
        
        self.engAct = QtGui.QAction(QtGui.QIcon('icons/globe.png'), 'English', None)
        self.engAct.triggered.connect(self.SwapEnglish)
        self.engAct.setShortcut(QtGui.QKeySequence('Ctrl+1'))
        
        self.jpAct = QtGui.QAction(QtGui.QIcon('icons/japan.png'), 'Japanese', None)
        self.jpAct.triggered.connect(self.SwapJapanese)
        self.jpAct.setShortcut(QtGui.QKeySequence('Ctrl+2'))

        self.comAct = QtGui.QAction(QtGui.QIcon('icons/comment.png'), 'Comments', None)
        self.comAct.triggered.connect(self.SwapComment)
        self.comAct.setShortcut(QtGui.QKeySequence('Ctrl+3'))

        self.playCentralAudio = QtGui.QAction('Play Audio (Center Panel)', None)
        self.playCentralAudio.triggered.connect(self.PlayCentralAudio)
        self.playCentralAudio.setShortcut(QtGui.QKeySequence('Ctrl+-'))

        self.reportAct = QtGui.QAction(QtGui.QIcon('icons/report.png'), 'Reports', None)
        self.reportAct.triggered.connect(self.ShowStats)
        self.reportAct.setShortcut(QtGui.QKeySequence('Ctrl+R'))

        self.massAct = QtGui.QAction(QtGui.QIcon('icons/massreplace.png'), 'Mass &Replace', None)
        self.massAct.triggered.connect(self.ShowMassReplace)
        self.massAct.setShortcut(QtGui.QKeySequence('Ctrl+M'))

        self.compAct = QtGui.QAction(QtGui.QIcon('icons/completion.png'), 'Completion', None)
        self.compAct.triggered.connect(self.ShowCompletionTable)
        self.compAct.setShortcut(QtGui.QKeySequence('Ctrl+%'))

        self.conDebugAct = QtGui.QAction('Consolidate Debug', None)
        self.conDebugAct.triggered.connect(self.ConsolidateDebug)

        self.fullcopyAct = QtGui.QAction('Full-Text Copy', None)
        self.fullcopyAct.triggered.connect(self.FullTextCopy)
        self.fullcopyAct.setShortcut(QtGui.QKeySequence('Ctrl+T'))

        self.saveAsPngAct = QtGui.QAction('Save Text as Image', None)
        self.saveAsPngAct.triggered.connect(self.SaveAsPng)
        self.saveAsPngAndOpenAct = QtGui.QAction('Save Text as Image and open', None)
        self.saveAsPngAndOpenAct.triggered.connect(self.SaveAsPngAndOpen)
        self.saveAsPngAndOpenAct.setShortcut(QtGui.QKeySequence('Ctrl+I'))
        self.saveAsMultiplePngAct = QtGui.QAction('Save Text as multiple Images', None)
        self.saveAsMultiplePngAct.triggered.connect(self.SaveAsMultiplePng)
        
        
        self.saveAct = QtGui.QAction(QtGui.QIcon('icons/upload.png'), 'Save', None)
        self.saveAct.triggered.connect(self.SavetoServer)
        self.saveAct.setShortcut(QtGui.QKeySequence('Ctrl+S'))

        self.revertAct = QtGui.QAction(QtGui.QIcon('icons/save.png'), 'Revert', None)
        self.revertAct.triggered.connect(self.RevertFromServer)
        
        self.updateAct = QtGui.QAction(QtGui.QIcon('icons/save.png'), 'Update', None)
        self.updateAct.triggered.connect(self.RetrieveModifiedFiles)
        self.updateAct.setShortcut(QtGui.QKeySequence('Ctrl+U'))

        self.refreshCompleteAct = QtGui.QAction(QtGui.QIcon('icons/refresh.png'), 'Refresh Completion Database', None)
        self.refreshCompleteAct.triggered.connect(self.RefreshCompletion)
        self.refreshCompleteAct.setShortcut(QtGui.QKeySequence('Ctrl+W'))
        
        self.recalcFilesToBeUploadedAct = QtGui.QAction(QtGui.QIcon('icons/refresh.png'), 'Find Unsaved Databases', None)
        self.recalcFilesToBeUploadedAct.triggered.connect(self.RecalculateFilesToBeUploaded)

        self.patchAct = QtGui.QAction(QtGui.QIcon('icons/patch.png'), 'Patch Live', None)
        self.patchAct.triggered.connect(self.SavetoPatch)
        self.patchAct.setShortcut(QtGui.QKeySequence('Ctrl+P'))

        self.patchdolAct = QtGui.QAction(QtGui.QIcon('icons/patchdol.png'), 'Patch Embedded Strings', None)
        self.patchdolAct.triggered.connect(self.PatchDol)
        self.patchdolAct.setShortcut(QtGui.QKeySequence('Ctrl+Alt+P'))

        self.patchzeroAct = QtGui.QAction(QtGui.QIcon('icons/patchv0.png'), 'Patch XML', None)
        self.patchzeroAct.triggered.connect(self.SavetoXML)
        self.patchzeroAct.setShortcut(QtGui.QKeySequence('Ctrl+Shift+P'))

        self.patchtwoAct = QtGui.QAction(QtGui.QIcon('icons/patchv2.png'), 'Patch Bugfix XML', None)
        self.patchtwoAct.triggered.connect(self.SavetoBugfixXML)
        self.patchtwoAct.setShortcut(QtGui.QKeySequence('Ctrl+Shift+Alt+P'))

        self.patchfDemoAct = QtGui.QAction(QtGui.QIcon('icons/patchv0.png'), 'Patch Graces f Demo XML', None)
        self.patchfDemoAct.triggered.connect(self.SavetoGracesfDemoXML)
        self.patchfDemoAct.setShortcut(QtGui.QKeySequence('Ctrl+Alt+F'))

        self.globalAct = QtGui.QAction(QtGui.QIcon('icons/global.png'), 'Global Changelog', None)
        self.globalAct.triggered.connect(self.ShowGlobalChangelog)
        self.globalAct.setShortcut(QtGui.QKeySequence('Ctrl+G'))

        self.changeAct = QtGui.QAction(QtGui.QIcon('icons/changelog.png'), 'Changelog', None)
        self.changeAct.triggered.connect(self.ShowChangelog)
        self.changeAct.setShortcut(QtGui.QKeySequence('Ctrl+Shift+G'))

        self.dupeAct = QtGui.QAction(QtGui.QIcon('icons/ruta.png'), 'Duplicate Text', None)
        self.dupeAct.triggered.connect(self.ShowDuplicateText)
        self.dupeAct.setShortcut(QtGui.QKeySequence('Ctrl+D'))

        self.quitAct = QtGui.QAction('Quit', None)
        self.quitAct.triggered.connect(self.cleanupAndQuit)
        self.quitAct.setShortcut(QtGui.QKeySequence('Ctrl-Q'))

        self.twoupAct = QtGui.QAction(QtGui.QIcon('icons/twoup.png'), 'Two-up', None)
        self.twoupAct.setCheckable(True)
        self.twoupAct.setChecked(0)
        self.twoupAct.toggled.connect(self.toggleIcon)
        self.twoupAct.setShortcut(QtGui.QKeySequence('Ctrl-U'))


        self.iconSizes = [12, 16, 18, 24, 36, 48, 64]
        self.iconSizeActs = []
        i = 0
        for size in self.iconSizes:
            self.iconSizeActs.append(QtGui.QAction('{0} x {0}'.format(size), None))
            i += 1

        self.noIconAct = QtGui.QAction('Only Text', None)
        self.noTextAct = QtGui.QAction('Only Icon', None)
        self.textDownAct = QtGui.QAction('Beneath Icon', None)
        self.textLeftAct = QtGui.QAction('Beside Icon', None)

        self.tmode = QtGui.QAction(QtGui.QIcon('icons/tlon.png'), 'Translation', None)
        self.tmode.setToolTip('<b>Translation Mode</b>\n\nTranslation mode encompasses the initial phase of translation.')
        self.tmode.setShortcut(QtGui.QKeySequence('Ctrl-Shift-1'))

        self.tlcheckmode = QtGui.QAction(QtGui.QIcon('icons/oneon.png'), 'Translation Review', None)
        self.tlcheckmode.setToolTip('<b>Translation Review Mode</b>\n\nTranslation review mode is used for when a second translator reviews an entry.')
        self.tlcheckmode.setShortcut(QtGui.QKeySequence('Ctrl-Shift-2'))

        self.rewritemode = QtGui.QAction(QtGui.QIcon('icons/twoon.png'), 'Contextual Review', None)
        self.rewritemode.setToolTip('<b>Contextual Review Mode</b>\n\Contextual review mode is reserved for context and localization sensitive rewrites.')
        self.rewritemode.setShortcut(QtGui.QKeySequence('Ctrl-Shift-3'))

        self.grammarmode = QtGui.QAction(QtGui.QIcon('icons/threeon.png'), 'Editing', None)
        self.grammarmode.setToolTip('<b>Editing Mode</b>\n\Editing mode involves a full grammar, structure, phrasing, tone, and consistency check.')
        self.grammarmode.setShortcut(QtGui.QKeySequence('Ctrl-Shift-4'))

        self.reloadConfigAct = QtGui.QAction('Reload Config', None)
        self.reloadConfigAct.triggered.connect(self.ReloadConfiguration)
        self.reloadConfigAct.setShortcut(QtGui.QKeySequence('Ctrl-Shift-Alt-R'))
        
        if Globals.EnglishVoiceLanguageFlag:
            self.voiceLangAct = QtGui.QAction('English Voices', None)
        else:
            self.voiceLangAct = QtGui.QAction('Japanese Voices', None)
        self.voiceLangAct.triggered.connect(self.VoiceLanguageSwap)
        self.voiceLangAct.setShortcut(QtGui.QKeySequence('Ctrl-Shift-Alt-E'))
        
        if Globals.UpdateLowerStatusFlag:
            self.updateLowerStatusAct = QtGui.QAction('Updating lower status', None)
        else:
            self.updateLowerStatusAct = QtGui.QAction('Not updating lower status', None)
        self.updateLowerStatusAct.triggered.connect(self.UpdateLowerStatusSwap)
        
        if Globals.FooterVisibleFlag:
            self.displayFooterAct = QtGui.QAction('Footer enabled', None)
        else:
            self.displayFooterAct = QtGui.QAction('Footer disabled', None)
        self.displayFooterAct.triggered.connect(self.DisplayFooterSwap)
        
        self.changeEditingWindowAmountAct = QtGui.QAction('Change Editing Window Amount', None)
        self.changeEditingWindowAmountAct.triggered.connect(self.ChangeEditingWindowAmountDisplay)
        
        if Globals.WriteDatabaseStorageToHddOnEntryChange:
            self.writeDatabaseStorageToHddAct = QtGui.QAction('Writing on Entry change', None)
        else:
            self.writeDatabaseStorageToHddAct = QtGui.QAction('Not writing on Entry change', None)
        self.writeDatabaseStorageToHddAct.triggered.connect(self.ChangeWriteDatabaseStorageToHddBehavior)
        
        
        
        self.autoAct = QtGui.QAction('Auto', None)
        self.semiAct = QtGui.QAction('Semi-Auto', None)
        self.manuAct = QtGui.QAction('Manual', None)
        

        self.scrollUpAct = QtGui.QAction('Scroll Up', None)
        self.scrollUpAct.triggered.connect(self.scrollUp)
        self.scrollUpAct.setShortcut(QtGui.QKeySequence('Ctrl+Up'))

        self.scrollUpAct2 = QtGui.QAction('Scroll Up', None)
        self.scrollUpAct2.triggered.connect(self.scrollUp)
        self.scrollUpAct2.setShortcut(QtGui.QKeySequence('Alt+Up'))

        self.scrollDownAct = QtGui.QAction('Scroll Down', None)
        self.scrollDownAct.triggered.connect(self.scrollDown)
        self.scrollDownAct.setShortcut(QtGui.QKeySequence('Ctrl+Down'))
        
        self.scrollDownAct2 = QtGui.QAction('Scroll Down', None)
        self.scrollDownAct2.triggered.connect(self.scrollDown)
        self.scrollDownAct2.setShortcut(QtGui.QKeySequence('Alt+Down'))
        
        self.reopenMediaWinAct = QtGui.QAction('Reopen Media Windows', None)
        self.reopenMediaWinAct.triggered.connect(self.openMediumWindows)


        roleMenu = QtGui.QMenu('Role', self)

        roleMenu.addAction(self.tmode)
        roleMenu.addAction(self.tlcheckmode)
        roleMenu.addAction(self.rewritemode)
        roleMenu.addAction(self.grammarmode)

        roleMenu.triggered.connect(self.setRole)


        self.Toolbar = parent.Toolbar
        self.Toolbar.clear()
        
        self.Toolbar.addAction(self.engAct)
        self.Toolbar.addAction(self.jpAct)
        self.Toolbar.addAction(self.comAct)
        self.Toolbar.addAction(self.twoupAct)
        self.Toolbar.addAction(self.reportAct)
        self.Toolbar.addAction(self.massAct)
        self.Toolbar.addAction(self.compAct)
        self.Toolbar.addAction(self.dupeAct)
        self.Toolbar.addWidget(FlexibleSpace)
        self.Toolbar.addSeparator()
        
        tmp1 = QtGui.QVBoxLayout()
        tmp2 = QtGui.QVBoxLayout()
        tmp1.addWidget( QtGui.QLabel('Jump To') )
        tmp1.addWidget( QtGui.QLabel('Search') )
        tmp2.addWidget( self.jumptobox )
        tmp2.addWidget( self.filter )
        tmp1b = QtGui.QGroupBox()
        tmp1b.setLayout(tmp1)
        tmp2b = QtGui.QGroupBox()
        tmp2b.setLayout(tmp2)
        self.Toolbar.addWidget(tmp1b)
        self.Toolbar.addWidget(tmp2b)
        
        
        self.Toolbar.addAction(self.debug)
        self.Toolbar.setToolButtonStyle(3)
        
        
        if self.settings.contains('toolicon'):
            self.Toolbar.setIconSize(QtCore.QSize(self.settings.value('toolicon'), self.settings.value('toolicon')))
        if self.settings.contains('toolstyle'):
            self.Toolbar.setToolButtonStyle(self.settings.value('toolstyle'))
        
        parent.menuBar().clear()
        
        parent.editMenu.addSeparator()
        parent.editMenu.addAction(self.fullcopyAct)
        parent.editMenu.addAction(self.saveAsPngAndOpenAct)
        parent.editMenu.addAction(self.saveAsPngAct)
        parent.editMenu.addAction(self.saveAsMultiplePngAct)
        
        fileMenu = QtGui.QMenu("File", self)
        
        fileMenu.addAction(self.saveAct)
        fileMenu.addAction(self.updateAct)
        fileMenu.addAction(self.refreshCompleteAct)
        fileMenu.addAction(self.recalcFilesToBeUploadedAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.patchAct)
        fileMenu.addAction(self.patchdolAct)
        fileMenu.addAction(self.patchzeroAct)
        fileMenu.addAction(self.patchtwoAct)
        fileMenu.addAction(self.patchfDemoAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.revertAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.quitAct)
        
        
        viewMenu = QtGui.QMenu("View", self)
        
        viewMenu.addAction(self.globalAct)
        viewMenu.addAction(self.changeAct)
        viewMenu.addSeparator()
        viewMenu.addAction(self.twoupAct)
        viewMenu.addAction(self.engAct)
        viewMenu.addAction(self.jpAct)
        viewMenu.addAction(self.comAct)
        viewMenu.addSeparator()
        viewMenu.addAction(self.playCentralAudio)
        viewMenu.addSeparator()
        viewMenu.addAction(self.scrollUpAct)
        viewMenu.addAction(self.scrollDownAct)
        viewMenu.addAction(self.scrollUpAct2)
        viewMenu.addAction(self.scrollDownAct2)
        viewMenu.addSeparator()
        viewMenu.addAction(self.reopenMediaWinAct)
        viewMenu.addSeparator()
        iconSizeMenu = QtGui.QMenu("Toolbar Icon Size", self)
        for action in self.iconSizeActs:
            iconSizeMenu.addAction(action)
        textMenu = QtGui.QMenu("Toolbar Style", self)
        textMenu.addAction(self.noTextAct)
        textMenu.addAction(self.noIconAct)
        textMenu.addAction(self.textDownAct)
        textMenu.addAction(self.textLeftAct)
        viewMenu.addMenu(textMenu)
        viewMenu.addMenu(iconSizeMenu)

        fontSizeMenu = QtGui.QMenu("Font Size", self)
        fontSizeMenu.addAction('8')
        fontSizeMenu.addAction('9')
        fontSizeMenu.addAction('10')
        fontSizeMenu.addAction('12')
        fontSizeMenu.addAction('14')
        fontSizeMenu.addAction('18')
        fontSizeMenu.addAction('24')
        fontSizeMenu.addAction('36')
        viewMenu.addMenu(fontSizeMenu)
        
        fontSizeMenu.triggered.connect(self.fontChange)
        iconSizeMenu.triggered.connect(self.setToolbariconsize)
        textMenu.triggered.connect(self.setToolbartext)
        
        
        toolsMenu = QtGui.QMenu("Tools", self)
        
        toolsMenu.addAction(self.massAct)
        toolsMenu.addAction(self.reportAct)
        toolsMenu.addAction(self.compAct)
        toolsMenu.addAction(self.dupeAct)
        toolsMenu.addAction(self.conDebugAct)
        
        
        modeMenu = QtGui.QMenu("Mode", self)
        
        modeMenu.addAction(self.autoAct)
        modeMenu.addAction(self.semiAct)
        modeMenu.addAction(self.manuAct)
        modeMenu.triggered.connect(self.setMode)
        

        optionsMenu = QtGui.QMenu("Options", self)
        optionsMenu.addAction(self.reloadConfigAct)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.voiceLangAct)
        optionsMenu.addAction(self.updateLowerStatusAct)
        optionsMenu.addAction(self.displayFooterAct)
        optionsMenu.addAction(self.writeDatabaseStorageToHddAct)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.changeEditingWindowAmountAct)

        parent.menuBar().addMenu(fileMenu)
        parent.menuBar().addMenu(parent.editMenu)
        parent.menuBar().addMenu(viewMenu)
        parent.menuBar().addMenu(roleMenu)
        parent.menuBar().addMenu(modeMenu)
        parent.menuBar().addMenu(toolsMenu)
        parent.menuBar().addMenu(optionsMenu)


        # Layout
        Globals.commentsAvailableLabel = QtGui.QLabel("-")
        
        FileListSubLayout = QtGui.QVBoxLayout()
        FileListSubLayout.addWidget(Globals.commentsAvailableLabel)
        FileListSubLayout.addWidget(self.tree)
        
        EditingWindowSubLayoutSplitter = QtGui.QSplitter()
        EditingWindowSubLayoutSplitter.setOrientation(QtCore.Qt.Vertical)
        for i in range(len(self.textEditingBoxes)):
            EditingWindowSubLayoutSplitter.addWidget(self.textEditingBoxes[i])
        
        layout = QtGui.QSplitter()
        FileListSubLayoutWidget = QtGui.QWidget()
        FileListSubLayoutWidget.setLayout(FileListSubLayout)
        layout.addWidget(FileListSubLayoutWidget)
        #EditingWindowSubLayoutWidget = QtGui.QWidget()
        #EditingWindowSubLayoutWidget.setLayout(EditingWindowSubLayout)
        layout.addWidget(EditingWindowSubLayoutSplitter)
        layout.addWidget(self.entry)
        #layout.setColumnStretch(1,1)
        
        layout.setSizes( [200, 400, 200] )
        
        layoutWidgetAdapter = QtGui.QVBoxLayout()
        layoutWidgetAdapter.addWidget(layout)
        self.setLayout(layoutWidgetAdapter)

        self.massDialogOpened = False
        self.globalChangelogOpened = False
        self.statsDialogOpened = False
        self.duplicateTextDialogOpened = False
        
        self.openMediumWindows()
        
    def openMediumWindows(self):
        self.media = {}
        self.openImageWindows()
            
    def openImageWindows(self):
        for img in Globals.configData.Images:
            self.openImageWindow(img)
    
    def openImageWindow(self, img):
        self.media[img.name] = ImageViewerWindow(self, img)
        self.media[img.name].show()
        self.media[img.name].raise_()
        self.media[img.name].activateWindow()

    def cleanupAndQuit(self):
        self.WriteDatabaseStorageToHdd()
        self.settings.setValue('update', set(self.update))
        print str(len(self.update)) + ' files retained for next session: ', ''.join(["%s, " % (k) for k in self.update])[:-2]
        self.settings.sync()
        self.close()
        quit()
        

    def scrollUp(self, action):
        try:
            index = self.entry.currentIndex()
            row = index.row()
    
            sortIndex = index.sibling(row-1, 0)

            if index == None or row == -1 or row == 0:
                sortIndex = self.entrysort.index(self.entrysort.rowCount()-1,0)                
    
            self.entry.setCurrentIndex(sortIndex)
            self.entry.selectionModel().select(sortIndex, QtGui.QItemSelectionModel.SelectionFlags(3))
    
            return
        except:
            print 'scroll up failed'


    def scrollDown(self, action):
        try:
            index = self.entry.currentIndex()
            row = index.row()
    
            if index == None or row == -1 or row == 0:
                index = self.entrysort.index(0,0)
                
            sortIndex = index.sibling(row+1, 0)
    
            self.entry.setCurrentIndex(sortIndex)
            self.entry.selectionModel().select(sortIndex, QtGui.QItemSelectionModel.SelectionFlags(3))
    
            return
        except:
            print 'scroll down failed'



    def fontChange(self, action):
        size = int(action.iconText())

        for box in self.regularEditingTextBoxes:
            box.setFontPointSize(size)
        for box in self.twoupEditingTextBoxes:
            box.setFontPointSize(size)

        self.PopulateTextEdit()
        self.settings.setValue('font', size)


    def setRole(self, action):
        if action == self.tmode:
            self.role = 1
        if action == self.tlcheckmode:
            self.role = 2
        if action == self.rewritemode:
            self.role = 3
        if action == self.grammarmode:
            self.role = 4

        try:
            self.settings.setValue('role', int(self.role))
        except:
            self.settings.setValue('role', 1)
        self.parent.setWindowTitle("Grace Note - {0} in {1} mode".format(self.roletext[self.role] , Globals.ModeFlag))
        self.PopulateEntryList()


    def setMode(self, action):
        if action == self.autoAct:
            mode = 'Auto'
        if action == self.semiAct:
            mode = 'Semi-Auto'
        if action == self.manuAct:
            mode = 'Manual'
            
        self.settings.setValue('mode', mode)
        Globals.ModeFlag = mode

        self.parent.setWindowTitle("Grace Note - {0} in {1} mode".format(self.roletext[self.role] , Globals.ModeFlag))


    def ReloadConfiguration(self):
        self.WriteDatabaseStorageToHdd()
        
        Globals.configData = Configuration(Globals.configfile)
        self.PopulateModel(Globals.configData.FileList)
        
    def VoiceLanguageSwap(self):
        if Globals.EnglishVoiceLanguageFlag == True:
            self.voiceLangAct.setText('Japanese Voices')
            Globals.EnglishVoiceLanguageFlag = False
            self.settings.setValue('voicelanguage', 'JP')
        else:
            self.voiceLangAct.setText('English Voices')
            Globals.EnglishVoiceLanguageFlag = True
            self.settings.setValue('voicelanguage', 'EN')
        
    def UpdateLowerStatusSwap(self):
        if Globals.UpdateLowerStatusFlag == True:
            self.updateLowerStatusAct.setText('Not updating lower status')
            Globals.UpdateLowerStatusFlag = False
            self.settings.setValue('updatelowerstatus', 'False')
        else:
            self.updateLowerStatusAct.setText('Updating lower status')
            Globals.UpdateLowerStatusFlag = True
            self.settings.setValue('updatelowerstatus', 'True')
            
    def DisplayFooterSwap(self):
        if Globals.FooterVisibleFlag == True:
            self.displayFooterAct.setText('Footer disabled')
            Globals.FooterVisibleFlag = False
            self.settings.setValue('footervisible', 'False')
        else:
            self.displayFooterAct.setText('Footer enabled')
            Globals.FooterVisibleFlag = True
            self.settings.setValue('footervisible', 'True')

    def ChangeWriteDatabaseStorageToHddBehavior(self):
        if Globals.WriteDatabaseStorageToHddOnEntryChange == True:
            self.writeDatabaseStorageToHddAct.setText('Not writing on Entry change')
            Globals.WriteDatabaseStorageToHddOnEntryChange = False
            self.settings.setValue('writeonentrychange', 'False')
        else:
            self.writeDatabaseStorageToHddAct.setText('Writing on Entry change')
            Globals.WriteDatabaseStorageToHddOnEntryChange = True
            self.settings.setValue('writeonentrychange', 'True')
            
    def ChangeEditingWindowAmountDisplay(self):
        text, ok = QtGui.QInputDialog.getText(self, "Enter new window amount", "New amount: (restart GN after entering!)", QtGui.QLineEdit.Normal)
        if ok and text != '':
            tmp = int(text)
            if tmp >= 3 and tmp <= 25:
                self.settings.setValue('editpane_amount', text)
                Globals.AmountEditingWindows = tmp

    def setToolbariconsize(self, action):
        i = 0
        for size in self.iconSizes:
            if action == self.iconSizeActs[i]:
                self.Toolbar.setIconSize(QtCore.QSize(size, size))
                self.settings.setValue('toolicon', size)
                if self.Toolbar.toolButtonStyle() == 1:
                    self.Toolbar.setToolButtonStyle(3)
            i += 1
            
            
    def setToolbartext(self, action):

        if action == self.noIconAct:
            self.Toolbar.setToolButtonStyle(1)
            self.settings.setValue('toolstyle', 1)

        if action == self.noTextAct:
            self.Toolbar.setToolButtonStyle(0)
            self.settings.setValue('toolstyle', 0)
        
        if action == self.textDownAct:
            self.Toolbar.setToolButtonStyle(3)
            self.settings.setValue('toolstyle', 3)
        
        if action == self.textLeftAct:
            self.Toolbar.setToolButtonStyle(2)
            self.settings.setValue('toolstyle', 2)
        
    def toggleIcon(self, bool):
        if bool == True:
            self.twoupAct.setIcon(QtGui.QIcon('icons/oneup.png'))
            self.twoupAct.setText('One up')

            for box in self.twoupEditingTextBoxes:
                box.show()
            
            self.PopulateTextEdit()

        else:
            self.twoupAct.setIcon(QtGui.QIcon('icons/twoup.png'))
            self.twoupAct.setText('Two up')

            for box in self.twoupEditingTextBoxes:
                box.hide()

    def ConsolidateDebug(self):
        self.WriteDatabaseStorageToHdd()
        
        # Applies the debug status in GracesJapanese to all databases
            
        i = 1
        aList = Globals.configData.FileList
            
        for item in aList[0]:
            print item
            for filename in aList[i]:

                print "Processing: {0}".format(filename)
            
                UpdateCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(filename))
                UpdateCur = UpdateCon.cursor()
                        
                UpdateCur.execute("select ID, StringID, status from Text")
                
                for entry in UpdateCur.fetchall():                        
                    Globals.CursorGracesJapanese.execute("select debug from Japanese where ID=?", (entry[1],))
            
                    try:
                        if Globals.CursorGracesJapanese.fetchall()[0][0] == 1:
                            UpdateCur.execute("update Text set status=-1 where ID=? AND status != -1", (entry[0],))
                        else:
                            if entry[2] == -1:
                                UpdateCur.execute("update Text set status = 0 where ID=? AND status != 0", (entry[0],))
                    except:
                        pass
                        
                UpdateCon.commit()
                
            i += 1

    def ReverseConsolidateDebug(self):
        self.WriteDatabaseStorageToHdd()
        
        # Applies the debug status in Databases to GracesJapanese
        
        i = 1
        aList = Globals.configData.FileList
            
        for item in aList[0]:
            print item
            for filename in aList[i]:

                print "Processing: {0}".format(filename)
            
                UpdateCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(filename))
                UpdateCur = UpdateCon.cursor()
                        
                UpdateCur.execute("SELECT StringID FROM Text WHERE status = -1")
                
                for entry in UpdateCur.fetchall():
                    Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 1 WHERE ID=?", (entry[0],))
                UpdateCon.rollback()
                
            i += 1
        Globals.ConnectionGracesJapanese.commit()

    def RetrieveModifiedFiles(self, splash):
        self.WriteDatabaseStorageToHdd()
        
        # Nab the online changelog
        try:
            splash.text = 'Downloading updated files...'
        except:
            pass
        print 'Downloading updated files...'
            
        # loop to prevent crashes during FTP stuff
        for i in range( 0, 20 ):    # range( start, stop, step )
            try:
                
                try:
                    ftp = FTP(Globals.configData.FTPServer, Globals.configData.FTPUsername, Globals.configData.FTPPassword, "", 15)
                except:
                    if i == 20:
                        print '20 errors is enough, this is not gonna work'
                        try:
                            splash.text = 'Grace Note Loaded'.format(self.roletext[self.role], Globals.ModeFlag)
                            splash.complete = True
                            splash.offline = True
                        except:
                            pass
                        return
                    print 'Failed connecting to FTP, retrying...'
                    continue
                    
                ftp.cwd('/')
                ftp.cwd(Globals.configData.RemoteDatabasePath)
                        
                changes = self.DownloadFile(ftp, 'ChangeLog', 'NewChangeLog')
                
                if changes == False:
                    "This isn't going to work, is it? Try again later."
                    self.cleanupAndQuit() 


                # Get any new entries
                Globals.LogCur.execute('select ID, File from Log ORDER BY ID')
                results = Globals.LogCur.fetchall()
                LogSet = set(results)

                NewLogCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/NewChangeLog")
                NewLogCur = NewLogCon.cursor()
                
                NewLogCur.execute('select ID, File from Log ORDER BY ID')
                newResults = NewLogCur.fetchall()
                newLogSet = set(newResults)
                
                DownloaderSet = LogSet.symmetric_difference(newLogSet)
                Downloader = []
                        
                for item in DownloaderSet:
                    itemList = item[1].split(',')
                    for subitem in itemList:
                        if subitem in self.update:
                            print '{0} was skipped because you have local save data which needs uploading.'.format(subitem)
                            continue
                        Downloader.append(subitem)
                
                # by pika: remove possible duplicates from list, so it doesn't download the same file multiple times
                Downloader = list(set(Downloader))
                
                #Downloader.sort()
                for item in set(Downloader):
                    Globals.CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [item])
                    exists = Globals.CursorGracesJapanese.fetchall()[0][0]
                    if exists > 0:
                        Globals.CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [item])
                        desc = Globals.CursorGracesJapanese.fetchall()[0][0]
                        print 'Downloading ' + desc + ' [' + item + ']...'
                    else:
                        print 'Downloading ' + item + '...'
                    
                    
                    
                    self.DownloadFile(ftp, item, item)
                    WipeUpdateCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(item))
                    WipeUpdateCur = WipeUpdateCon.cursor()
            
                    WipeUpdateCur.execute(u"update Text set updated=0")
                    WipeUpdateCon.commit()
                    
                    CompletionTable.CalculateCompletionForDatabase(item)

                                
                old = open(Globals.configData.LocalDatabasePath + '/ChangeLog', 'wb')
                new = open(Globals.configData.LocalDatabasePath + '/NewChangeLog', 'rb')
                old.write(new.read())
                new.close()
                old.close()

                ftp.close()
                
                break
                
            except ftplib.all_errors:
                if i == 20:
                    print '20 errors is enough, this is not gonna work'
                    break
                print 'Error during FTP transfer, retrying...'
                continue
                
        try:
            splash.text = 'Grace Note now {0} in {1} Mode'.format(self.roletext[self.role], Globals.ModeFlag)
            splash.complete = True
        except:
            pass
        print 'Downloaded updated files!'


    def DownloadFile(self, ftp, source, dest):
        self.WriteDatabaseStorageToHdd()
                
        save = open(Globals.configData.LocalDatabasePath + '/{0}'.format(dest), 'wb')
        ftp.retrbinary('RETR {0}'.format(source), save.write)
        save.close()

        size = ftp.size('{0}'.format(source))

        check = open(Globals.configData.LocalDatabasePath + '/{0}'.format(dest), 'rb')
        localsize = len(check.read())
        check.close()
        
        if size != localsize:
            success = False
            for i in range(3):
                print 'Problem Downloading {0}. Retry #{1}'.format(source, i+1)
                
                e = open(Globals.configData.LocalDatabasePath + '/{0}'.format(dest), 'wb')
                ftp.retrbinary('RETR {0}'.format(source), e.write)
                e.close()
        
                e = open(Globals.configData.LocalDatabasePath + '/{0}'.format(dest), 'rb')
                localsize = len(e.read())
                e.close()

                if size == localsize:
                    success = True
                    break
            if success == False:
                "Looks like {0} won't download. Moving on, I suppose.".format(source)
                return False
                
        
        return True
        

    def UploadFile(self, ftp, source, dest, confirmUpload=False):
        self.WriteDatabaseStorageToHdd()
        
        source = str(source)
        dest = str(dest)
    
        check = open(Globals.configData.LocalDatabasePath + '/{0}'.format(source), 'rb')
        localsize = len(check.read())
        check.close()
        
        success = False
        for i in range(6):
            fnew = open(Globals.configData.LocalDatabasePath + '/{0}'.format(source), 'rb')
            UploadString = str('STOR ' + dest)
            ftp.storbinary(UploadString, fnew)
            fnew.close()
            size = ftp.size(dest)
            if size == localsize:
                if confirmUpload == True:
                    self.DownloadFile(ftp, dest, 'uploadConfirmTemp')
                    success = filecmp.cmp(Globals.configData.LocalDatabasePath + '/{0}'.format(source), Globals.configData.LocalDatabasePath + '/uploadConfirmTemp')
                else:
                    success = True
                    break
            else:
                print 'Failed uploading {0}, retrying...'.format(dest)
        if success == False:
            "Looks like {0} won't upload. Better talk to Tempus about it.".format(dest)
            return dest
            
        
        return True

    def PopulateModel(self, FileList):
        self.WriteDatabaseStorageToHdd()
        
        self.treemodel.clear()
        
        PercentageConnection = sqlite3.connect(Globals.configData.LocalDatabasePath + "/CompletionPercentage")
        PercentageCursor = PercentageConnection.cursor()
        
        i = 1
        for item in FileList[0]:
            cat = QtGui.QStandardItem(item)
            self.treemodel.appendRow(cat)
            for item in FileList[i]:
                newrow = QtGui.QStandardItem()
                newrow.setStatusTip(item)
                newrow.setText(Globals.GetDatabaseDescriptionString(item))
                
                # color based on completion / comments exist
                PercentageCursor.execute("SELECT Count(1) FROM Percentages WHERE Database = ?", [item])
                exists = PercentageCursor.fetchall()[0][0]
                if exists > 0:
                    PercentageCursor.execute("SELECT entries, translation, editing1, editing2, editing3, comments FROM Percentages WHERE Database = ?", [item])
                    rows = PercentageCursor.fetchall()
                    totalDB = rows[0][0]
                    translated = rows[0][self.role]
                    phase1 = rows[0][1]
                    phase2 = rows[0][2]
                    phase3 = rows[0][3]
                    phase4 = rows[0][4]
                    commentAmount = rows[0][5]
                    
                    if translated >= totalDB:
                        newrow.setBackground(QtGui.QBrush(QtGui.QColor(160, 255, 160)));
                    else:
                        newrow.setBackground(QtGui.QBrush(QtGui.QColor(255, 160, 160)));
                    
                    dbPhase = 0
                    if totalDB == phase1:
                        if totalDB == phase2:
                            if totalDB == phase3:
                                if totalDB == phase4:
                                    dbPhase = dbPhase + 1
                                dbPhase = dbPhase + 1
                            dbPhase = dbPhase + 1
                        dbPhase = dbPhase + 1
                        
                    if commentAmount > 0:
                        newrow.setText('[' + str(dbPhase) + 'C] ' + newrow.text())
                    else:
                        newrow.setText('[' + str(dbPhase) + '] ' + newrow.text())
                # color/comments end
                
                cat.appendRow(newrow)
            i = i + 1

                
    def PopulateEntryList(self):
        self.WriteDatabaseStorageToHdd()
        
        containsComments = False
    
        for editbox in self.regularEditingTextBoxes:
            editbox.iconToggle(0)

        self.entrymodel.clear()
        
        self.text = []

        for editbox in self.regularEditingTextBoxes:
            editbox.setText('')
        for txtbox in self.textEditingBoxes:
            txtbox.setTitle('-----')
        for footer in self.textEditingFooters:
            footer.setText('')
        for footer in self.twoupEditingFooters:
            footer.setText('')

        index = self.tree.currentIndex()
        parent = self.treemodel.data(self.tree.currentIndex().parent())

        if self.treemodel.hasChildren(index) == True:
            return

        databasefilename = self.treemodel.itemFromIndex(index).statusTip()
        self.currentlyOpenDatabase = databasefilename
        SaveCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(databasefilename))
        SaveCur = SaveCon.cursor()
        
        try:
            SaveCur.execute("select ID, StringID, english, comment, updated, status, IdentifyString from Text")
            TempList = SaveCur.fetchall()
            ContainsIDString = True
            
        except:
            SaveCur.execute("select ID, StringID, english, comment, updated, status from Text")
            TempList = SaveCur.fetchall()
            ContainsIDString = False
            
        for i in xrange(len(TempList)):
            Globals.CursorGracesJapanese.execute("select * from Japanese where ID={0}".format(TempList[i][1]))
            TempString = Globals.CursorGracesJapanese.fetchall() 
            TempJPN = TempString[0][1]
            TempDebug = TempString[0][2]

            TempENG = TempList[i][2]
            TempCOM = TempList[i][3]
            TempStatus = TempList[i][5]

            if TempENG == '':
                TempENG = TempJPN

            entryDisplayString = 'Entry ' + str(i+1).zfill(5) + ' [' + str(TempStatus) + ']'
            
            identifyString = ''
            if ContainsIDString == True:
                try:
                    tmp = str(TempList[i][6])
                    identifyString = tmp
                    entryDisplayString = entryDisplayString + ' ' + identifyString
                except:
                    pass
            
            if TempCOM == None:
                TempCOM = 'None'
            if TempCOM != '':
                entryDisplayString = entryDisplayString + ' [Comment]'
                containsComments = True
            
            additem = QtGui.QStandardItem(entryDisplayString)
            additem.setCheckable(True)
            additem.setStatusTip(identifyString)
            
            if TempStatus >= self.role:
                additem.setBackground(QtGui.QBrush(QtGui.QColor(220, 255, 220)))
                if self.author == 'ruta':
                    additem.setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))
                elif self.author == 'Pikachu025':
                    additem.setBackground(QtGui.QBrush(QtGui.QColor(0, 150, 0)))

            if TempStatus == -1:
                additem.setBackground(QtGui.QBrush(QtGui.QColor(255, 220, 220)))
                if self.author == 'ruta':
                    additem.setBackground(QtGui.QBrush(QtGui.QColor(255,225,180)))             
    
            if (TempDebug == 1) and (self.debug.isChecked() == False):
                pass
            elif (TempDebug == 1) and (self.debug.isChecked() == True):
                additem.setCheckState(QtCore.Qt.Checked)
                additem.setWhatsThis("d") #debug
                self.entrymodel.appendRow(additem)
            else:
                additem.setWhatsThis("n") #not debug
                self.entrymodel.appendRow(additem)
            
            if TempStatus != -1 and TempDebug == 1:
                SaveCur.execute("update Text set status=-1 where ID=?", (TempString[0][0],))
                SaveCon.commit()
                
            self.text.append([TempENG, TempJPN, TempCOM, TempDebug, TempStatus, identifyString])
            
        if containsComments == True:
            Globals.commentsAvailableLabel.setText(databasefilename + " | Comments exist!")
        else:
            Globals.commentsAvailableLabel.setText(databasefilename)
            
        if self.entrysort.rowCount() != 1:
            index = self.entrysort.index(1, 0)
        else:
            index = self.entrysort.index(0, 0)
        self.entry.setCurrentIndex(index)
        self.entry.selectionModel().select(index, QtGui.QItemSelectionModel.SelectionFlags(3))
        
    def GetFullText(self, replaceVariables):
        string = ''
        i = 1
        for entry in self.text:
            if entry[3] == 0 or self.debug.isChecked() == True:
                string = string + 'Entry {0}\n'.format(i)
                if replaceVariables == True:
                    string = string + Globals.VariableReplace(entry[0])
                else:
                    string = string + entry[0]
                string = string + "\n\n\n"
            
            i += 1
        return string

    def FullTextCopy(self):
        string = self.GetFullText(True)
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(string)
        return

    def SaveAsPng(self):
        string = self.GetFullText(False)
        txtfile = open('text.txt', 'w')
        txtfile.write( codecs.BOM_UTF8 )
        txtfile.write( string.encode( "utf-8" ) )
        txtfile.close()
        args = ['FontDisplay.exe', '-fontinfofile', 'ffinfo.bin', '-fontinfofiletype', 'fontinfo', '-textfile', 'text.txt', '-mode', 'png', '-font', 'FONTTEX10.TXV', '-fontblock', '0', '-outfile', 'text.png']
        proc=subprocess.Popen(args)
        proc.wait()
        return

    def SaveAsMultiplePng(self):
        try:
            databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        except:
            return
            
        string = self.GetFullText(False)
        txtfile = open('text.txt', 'w')
        txtfile.write( codecs.BOM_UTF8 )
        txtfile.write( string.encode( "utf-8" ) )
        txtfile.close()
        
        if databasefilename.startsWith("VScenario") or databasefilename.startsWith("VBattle"):
            args = ['FontDisplay.exe', '-fontinfofile', 'ffinfo.bin', '-fontinfofiletype', 'fontinfo', '-textfile', 'text.txt', '-mode', 'png', '-font', 'FONTTEX10.TXV', '-fontblock', '0', '-outfile', 'text.png', '-boxbybox', '-dialoguebubble']
        else:
            args = ['FontDisplay.exe', '-fontinfofile', 'ffinfo.bin', '-fontinfofiletype', 'fontinfo', '-textfile', 'text.txt', '-mode', 'png', '-font', 'FONTTEX10.TXV', '-fontblock', '0', '-outfile', 'text.png', '-boxbybox']
        proc=subprocess.Popen(args)
        proc.wait()
        return
        
    def SaveAsPngAndOpen(self):
        self.SaveAsPng()
        os.startfile('text.png')
        return

    def JumpToDatabase(self):
        jumpto = self.jumptobox.text()
        self.JumpToEntry(jumpto, 0)
    
    def LiveSearch(self):
        self.WriteDatabaseStorageToHdd()
        
        matchString = self.filter.text()

        # Check to make sure people aren't idiots
        if matchString.count(unicode('<', 'UTF-8')) != matchString.count(unicode('>', 'UTF-8')):
            
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYou can not search for part of a variable. Please be sure to include the entire variable tag.")
            return


        matchString = Globals.VariableRemove(matchString)
        
        if len(matchString) == 0:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search can not be empty. Please enter text in the search bar.")
            return


        popup_menu = QtGui.QMenu()


        # For an Exact match to the string at any point                        
        try:
            Globals.CursorGracesJapanese.execute(u"select ID from Japanese where debug=0 AND string LIKE ?", ('%' + unicode(matchString) + '%', ))
            JPmatches = set(Globals.CursorGracesJapanese.fetchall())
        except:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search returned too many results, try something with more letters or use the mass replace.")
            return

        MatchedEntries = []

        aList = Globals.configData.FileList

        for i in range(1, len(aList)):
            for File in aList[i]:
                FilterCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(File))
                FilterCur = FilterCon.cursor()
                
                ORIDString = ''
                for match in JPmatches:
                    ORIDString = ORIDString + " OR StringID='" + str(match[0]) + "'"
                    
                try:
                    if self.debug.isChecked() == True:
                        FilterCur.execute(u"select ID, English, StringID from Text where english LIKE ? {0}".format(ORIDString), ('%' + unicode(matchString) + '%', ))
                    else:
                        FilterCur.execute(u"select ID, English, StringID from Text where status>=0 AND english LIKE ? {0}".format(ORIDString), ('%' + unicode(matchString) + '%', ))
                except:
                    reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search returned too many results, try something with more letters or use the mass replace.")
                    return
                
                TempList = FilterCur.fetchall()
                                        
                for item in TempList:
                    if item[1] == '':
                        Globals.CursorGracesJapanese.execute('select string from Japanese where ID={0}'.format(item[2]))
                        String = Globals.CursorGracesJapanese.fetchall()[0][0]
                    else:
                        String = item[1]
                    MatchedEntries.append((File, item[0], String))
        
        #No matches found case
        if len(MatchedEntries) == 0:
            popup_menu.addAction('No Matches Found')

        
        if platform.uname()[0] != 'Darwin':
            ResultLen = 20
            MatchedEntries = MatchedEntries[:20]
        else:
            ResultLen = 50
            MatchedEntries = MatchedEntries[:50]

        #Matches found case
        for item in MatchedEntries:
            newString = Globals.VariableReplace(item[2])
            if len(newString) > 45:
                string = newString[:42] + '...'
#                stringPos = item[2].index(unicode(matchString))
#                if stringPos == 0:
#                    string = item[2][:12] + '...'
#                else:
#                    string = '...' + item[2][stringPos:stringPos+9] + '...'
            else:
                string = newString
            action = SearchAction(item[0] + ': ' + string, popup_menu)
            action.setData(item[:2])
            action.jumpTo.connect(self.JumpToEntry)
            popup_menu.addAction(action)
        
        popup_menu.addAction('------Limited to {0} Results------'.format(ResultLen))
        
        popup_menu.exec_(self.filter.mapToGlobal(QtCore.QPoint(0,self.filter.height())))


    def JumpToEntry(self, file, entry):
        self.WriteDatabaseStorageToHdd()
        
        if file == '':
            file = self.currentlyOpenDatabase
        self.tree.collapseAll()
        for i in xrange(self.treemodel.rowCount()):
            category = self.treemodel.item(i)

            for p in xrange(category.rowCount()):
            
                if category.child(p).statusTip() == file:
                    treeExpand = self.treemodel.indexFromItem(category)
                    self.tree.expand(treeExpand)
                    treeIndex = self.treemodel.indexFromItem(category.child(p))
                            
                    self.tree.setCurrentIndex(treeIndex)
                    self.tree.selectionModel().select(treeIndex, QtGui.QItemSelectionModel.SelectionFlags(3))

                    try:
                        entryItem = self.entrymodel.findItems(str(entry).zfill(5), QtCore.Qt.MatchContains)[0]
                        entryIndex = self.entrymodel.indexFromItem(entryItem)
                        sortIndex = self.entrysort.mapFromSource(entryIndex)

                        self.entry.setCurrentIndex(sortIndex)
                        self.entry.selectionModel().select(sortIndex, QtGui.QItemSelectionModel.SelectionFlags(3))
                    except:
                        pass

                    return


    def DebugFilter(self, bool):
        self.PopulateEntryList()
        if bool == True:
            self.debug.setIcon(QtGui.QIcon('icons/debugon.png'))
        else:
            self.debug.setIcon(QtGui.QIcon('icons/debugoff.png'))
        
    
    
    def ShowChangelog(self):
        self.LogDialog = LocalChangelog(self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip())

        self.LogDialog.show()
        self.LogDialog.raise_()
        self.LogDialog.activateWindow()

    def ShowGlobalChangelog(self):
        #if self.globalChangelogOpened == False:
        self.gLogDialog = GlobalChangelog(self)
        #    self.globalChangelogOpened = True

        self.gLogDialog.show()
        self.gLogDialog.raise_()
        self.gLogDialog.activateWindow()

    def ShowStats(self):
        #if self.statsDialogOpened == False:
        self.statDialog = Statistics()
        #    self.statsDialogOpened = True

        self.statDialog.show()
        self.statDialog.raise_()
        self.statDialog.activateWindow()


    def ShowMassReplace(self):
        self.WriteDatabaseStorageToHdd()
        
        if self.massDialogOpened == False:
            self.massDialog = MassReplace(self)
            self.massDialogOpened = True
        self.massDialog.show()
        self.massDialog.raise_()
        self.massDialog.activateWindow()


    def ShowCompletionTable(self):
        self.WriteDatabaseStorageToHdd()
        
        self.comDialog = CompletionTable(self)

        self.comDialog.show()
        self.comDialog.raise_()
        self.comDialog.activateWindow()

    def RefreshCompletion(self):
        self.WriteDatabaseStorageToHdd()
        
        CompletionTable.CalculateAllCompletionPercentagesForDatabase()

    def PlayCentralAudio(self):
        self.regularEditingTextBoxes[1].playAudio()
        
    def ShowDuplicateText(self):
        self.WriteDatabaseStorageToHdd()
        
        if self.duplicateTextDialogOpened == False:
            self.dupeDialog = DuplicateText(self)
            self.duplicateTextDialogOpened = True

        self.dupeDialog.show()
        self.dupeDialog.raise_()
        self.dupeDialog.activateWindow()
        


    def UpdateDebug(self):
        index = self.entry.currentIndex()
        if self.entrymodel.item(index.row()).checkState() == 0:
            if self.entrymodel.item(index.row()).whatsThis() == "n":
                return # no change, was already not debug
            DebugState = False
        else:
            if self.entrymodel.item(index.row()).whatsThis() == "d":
                return # no change, was already debug
            DebugState = True
        
        #print("updateDebug")
        self.WriteDatabaseStorageToHdd()
        
        selectedRow = int(self.entrysort.data(index)[6:11])-1
        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        SaveCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(databasefilename))
        SaveCur = SaveCon.cursor()
        SaveCur.execute("select StringID from Text where ID={0}".format(selectedRow+1))
        NextID = SaveCur.fetchall()[0][0]
        if DebugState == True:
            Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 1 WHERE ID = {0} AND debug != 1".format(NextID))
            SaveCur.execute("UPDATE Text SET status = -1, updated = 1 WHERE ID = {0} AND status != -1".format(selectedRow+1))
            self.entrymodel.item(index.row()).setWhatsThis("d")
        else:
            Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 0 WHERE ID = {0} AND debug != 0".format(NextID))
            SaveCur.execute("UPDATE Text SET status =  0, updated = 1 WHERE ID = {0} AND status  = -1".format(selectedRow+1))
            self.entrymodel.item(index.row()).setWhatsThis("n")
        self.update.add(str(databasefilename))
        SaveCon.commit()
        Globals.ConnectionGracesJapanese.commit()
        

        # color
        if DebugState == False:
            SaveCur.execute("select status from Text where ID={0}".format(selectedRow+1))
            status = SaveCur.fetchall()[0][0]
            if status >= self.role:
                self.entrymodel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(220, 255, 220)))
                if self.author == 'ruta':
                    self.entrymodel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))
                elif self.author == 'Pikachu025':
                    self.entrymodel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(0, 150, 0)))
            else:
                self.entrymodel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
                
        else:
            self.entrymodel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 220, 220)))
            if self.author == 'ruta':
                self.entrymodel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255,225,180)))             
        
    def DebugPrintDatabaseWriteStorage(self):
        for d in self.databaseWriteStorage:
            print("current contents: " + d.databaseName + "/" + str(d.entry) + ": " + d.cleanString)
    
    def InsertOrUpdateEntryToWrite(self, entryStruct):
        #DatabaseEntryStruct(cleanString, databaseName, entry, role, state)
        for i, d in enumerate(self.databaseWriteStorage):
            if d.entry == entryStruct.entry and d.state == entryStruct.state and d.databaseName == entryStruct.databaseName:
                if i != 0:
                #    print("found existing, rotating & removing old")
                    self.databaseWriteStorage.rotate(-i)
                #else:
                #    print("found existing, removing old")
                self.databaseWriteStorage.popleft()
                break
        self.databaseWriteStorage.appendleft(entryStruct) # doesn't exist in list yet, just add new
        #print("added new: " + entryStruct.databaseName + "/" + str(entryStruct.entry) + ": " + entryStruct.cleanString)
        #self.DebugPrintDatabaseWriteStorage()
        return
    
    def UpdateTextGenericFunc(self, role, textBox, footer):
        if textBox.currentEntry < 0:
            return
            
        treeindex = self.tree.currentIndex()
        if self.treemodel.hasChildren(treeindex):
            return
        
        
                        
        #index = self.entry.currentIndex()
        #row = index.row()
        #self.entrymodel.item(index.sibling(index.row()-1, 0).row()).setBackground(QtGui.QBrush(QtGui.QColor(220, 255, 220)))
        #if self.author == 'ruta':
        #    self.entrymodel.item(index.sibling(index.row()-1, 0).row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))
            
        GoodString = Globals.VariableRemove(textBox.toPlainText())

        if role == 5:
            CommandOriginButton = False
            role = self.role
        else:
            CommandOriginButton = True
        
        
        if CommandOriginButton == True:
            # if origin a button: always set to argument
            updateStatusValue = role
        elif self.state == "COM":
            # if origin a Comment box, don't update
            updateStatusValue = self.text[textBox.currentEntry - 1][4]
        else:
            # if origin by typing or automatic:
            if Globals.ModeFlag == 'Manual':
                # in manual mode: leave status alone, do not change, just fetch the existing one
                updateStatusValue = self.text[textBox.currentEntry - 1][4]
            else:
                # in (semi)auto mode: change to current role, except when disabled by option and current role is lower than existing status
                if Globals.UpdateLowerStatusFlag == False:
                    statuscheck = self.text[textBox.currentEntry - 1][4]
                    if statuscheck > role:
                        updateStatusValue = statuscheck
                    else:
                        updateStatusValue = role
                else:
                    updateStatusValue = role
                # endif Globals.UpdateLowerStatusFlag
            # endif Globals.ModeFlag
        # endif CommandOriginButton


        self.text[textBox.currentEntry - 1][4] = updateStatusValue
        textBox.iconToggle(updateStatusValue)
        
        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        
        #DatabaseEntryStruct(cleanString, databaseName, entry, role, state)
        # keep for later write to HDD
        self.InsertOrUpdateEntryToWrite(DatabaseEntryStruct(GoodString, databasefilename, textBox.currentEntry, updateStatusValue, self.state))
        textBox.refreshFooter(GoodString, self.state[0] + ': ')
        
        # write the new string back into the main window, this is neccessary or else the new string isn't there when the displayed entry is changed!
        if self.state == 'ENG':
            self.text[textBox.currentEntry - 1][0] = GoodString
        elif self.state == "COM":
            self.text[textBox.currentEntry - 1][2] = GoodString
            
        return

    def WriteDatabaseStorageToHdd(self):
        if not self.databaseWriteStorage:
            #print("Database storage empty, no need to write.")
            return
    
        lastDatabase = ""
        
        print("Writing database storage in memory to HDD...")
        
        # sort by time of entry creation so order of inserts is preserved (necessary eg. if changing both english and comment on same entry
        sortedStorage = sorted(self.databaseWriteStorage, key=lambda DatabaseEntryStruct: DatabaseEntryStruct.timestamp)
        
        #DatabaseEntryStruct(cleanString, databaseName, entry, role, state)
        for d in sortedStorage:
            if lastDatabase != d.databaseName: # open up new DB connectin if neccesary, otherwise just reuse the old one
                self.update.add(str(d.databaseName))
                SaveCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(d.databaseName))
                SaveCur = SaveCon.cursor()
                
            if d.state == 'ENG':
                SaveCur.execute(u"update Text set english=?, updated=1, status=? where ID=?", (d.cleanString, d.role, d.entry))
            elif d.state == "COM":
                SaveCur.execute(u"update Text set comment=?, updated=1, status=? where ID=?", (d.cleanString, d.role, d.entry))
            SaveCon.commit()
        
        self.databaseWriteStorage.clear()

    def PopulateTextEdit(self):
        if Globals.WriteDatabaseStorageToHddOnEntryChange == True:
            self.WriteDatabaseStorageToHdd()
                
        index = self.entry.currentIndex()
        row = index.row()

        if index == None or row == -1:
            return
        
        if self.state == 'ENG':
            t = 0
        elif self.state == 'JPN':
            t = 1
        elif self.state == 'COM':
            t = 2
        
        commentTexts = []
        for i in range(len(self.textEditingBoxes)):
            commentTexts.append('')

        # boxes here
        rowBoxes = []
        for i in range(len(self.textEditingBoxes)):
            try:
                entrytextdisplay = self.entrysort.data(index.sibling(index.row()+(i-1), index.column()))
                if entrytextdisplay != None:
                    rowBoxes.append( int(entrytextdisplay[6:11])-1 )
                else:
                    rowBoxes.append( -2 )
            except:
                rowBoxes.append( -2 )
        
        textEntries1 = []
        textEntries1raw = []
        textEntries2 = []
        textEntries2raw = []
        for i in range(len(self.textEditingBoxes)):
            if rowBoxes[i] >= 0:
                textEntries1.append( Globals.VariableReplace(self.text[rowBoxes[i]][t]) )
                textEntries1raw.append( self.text[rowBoxes[i]][t] )
                textEntries2.append( Globals.VariableReplace(self.text[rowBoxes[i]][self.twoupEditingTextBoxes[i].role]) )
                textEntries2raw.append( self.text[rowBoxes[i]][self.twoupEditingTextBoxes[i].role] )
                commentTexts[i] = self.text[rowBoxes[i]][5] + '     '
                if self.text[rowBoxes[i]][2] != '':
                    commentTexts[i] = commentTexts[i] + 'Comment Available'
                self.regularEditingTextBoxes[i].iconToggle(self.text[rowBoxes[i]][4])
                self.regularEditingTextBoxes[i].currentEntry = rowBoxes[i] + 1
                self.regularEditingTextBoxes[i].setReadOnly(False)
            else:
                textEntries1.append( '' )
                textEntries1raw.append( '' )
                textEntries2.append( '' )
                textEntries2raw.append( '' )
                self.regularEditingTextBoxes[i].iconToggle(0)
                self.regularEditingTextBoxes[i].currentEntry = -1
                self.regularEditingTextBoxes[i].setReadOnly(True)

        # audio clip check
        if Globals.Audio == True:
            lengthEditingBoxes = len(self.textEditingBoxes)
            for i in range(lengthEditingBoxes):
                if self.regularEditingTextBoxes[i].currentEntry == -1:
                    continue
                AudioSearchText = Globals.VariableReplace(self.text[rowBoxes[i] + Globals.configData.VoiceEntryOffset][t])
                AudioClips = re.findall('<Audio: (.*?)>', AudioSearchText, re.DOTALL)
                AudioClips = AudioClips + re.findall('<Voice: (.*?)>', AudioSearchText, re.DOTALL)
                if AudioClips == []:
                    self.regularEditingTextBoxes[i].clearPlaybackButtons()
                else:
                    self.regularEditingTextBoxes[i].makePlaybackButtons(AudioClips)

        # inform media boxes
        centerPanel = 1
        for name, medium in self.media.iteritems():
            #print self.text[rowBoxes[centerPanel] + medium.medium.offs][t]
            medium.refreshInfo( Globals.VariableReplace(self.text[rowBoxes[centerPanel] + medium.medium.offs][t]) )
                    
        # put text into textboxes, display entry number
        twoupTypeHelper = []
        twoupTypeHelper.append('E')
        twoupTypeHelper.append('J')
        twoupTypeHelper.append('C')
        for i in range(len(self.textEditingBoxes)):
            self.regularEditingTextBoxes[i].setText(textEntries1[i])
            if self.twoupAct.isChecked() == True:
                self.twoupEditingTextBoxes[i].setText(textEntries2[i])
                
            if self.regularEditingTextBoxes[i].currentEntry >= 0:
                self.textEditingBoxes[i].setTitle("Entry {0}: {1}".format(rowBoxes[i]+1, commentTexts[i]))
                self.regularEditingTextBoxes[i].refreshFooter(textEntries1raw[i], self.state[0] + ': ')
                self.twoupEditingTextBoxes[i].refreshFooter(textEntries2raw[i], twoupTypeHelper[self.twoupEditingTextBoxes[i].role] + ': ')
            else:
                self.textEditingBoxes[i].setTitle("-----")
                self.textEditingFooters[i].setText('')
                self.twoupEditingFooters[i].setText('')
            

        # auto-update in Auto mode
        if Globals.ModeFlag == 'Auto':
            for i in range(len(self.textEditingBoxes)):
                self.regularEditingTextBoxes[i].manualEdit.emit(5, self.regularEditingTextBoxes[i], self.textEditingFooters[i])

        
    def SwapEnglish(self):

        if self.state == 'ENG':
            return

        for box in self.regularEditingTextBoxes:
            box.setReadOnly(False)
        
        self.state = 'ENG'
        self.PopulateTextEdit()


    def SwapJapanese(self):

        if self.state == 'JPN':
            return

        for box in self.regularEditingTextBoxes:
            box.setReadOnly(False)
        
        self.state = 'JPN'
        self.PopulateTextEdit()


    def SwapComment(self):

        if self.state == 'COM':
            return

        for box in self.regularEditingTextBoxes:
            box.setReadOnly(False)
        
        self.state = 'COM'
        self.PopulateTextEdit()

    def RecalculateFilesToBeUploaded(self):
        self.WriteDatabaseStorageToHdd()
        
        print 'Searching for databases with unsaved changes...'
        i = 1
        for item in Globals.configData.FileList[0]:
            for item in Globals.configData.FileList[i]:
                RecalcDbConn = sqlite3.connect(Globals.configData.LocalDatabasePath + "/" + item)
                RecalcDbCur = RecalcDbConn.cursor()
                RecalcDbCur.execute("SELECT Count(1) FROM Text WHERE updated = 1")
                exists = RecalcDbCur.fetchall()[0][0]
                if exists > 0:
                    self.update.add(str(item))
                    print 'Found database: ' + item
                RecalcDbConn.close()
            i = i + 1
        self.settings.setValue('update', set(self.update))
        self.settings.sync()
        print 'Done searching for databases with unsaved changes!'
        return
        
    def SavetoServer(self):
        self.WriteDatabaseStorageToHdd()
        
        if len(self.update) == 0:
            print 'Nothing to save!'
            return

        print 'Beginning Save...'
        
        
        autoRestartAfter = False
        
        for ftperrorcount in range(1, 20):
            try:        
                try:
                    self.ftp = FTP(Globals.configData.FTPServer, Globals.configData.FTPUsername, Globals.configData.FTPPassword, "", 15)
                except:
                    if ftperrorcount >= 20:
                        print "Warning:\n\nYour computer is currently offline, and will not be able to recieve updates or save to the server. Your progress will instead be saved for uploading upon re-establishment of a network connection, and any text you enter will be preserved automatically until such time."
                        self.settings.setValue('update', set(self.update))
                        return
                    print 'Error during FTP transfer, retrying...'
                    continue

                progress = QtGui.QProgressDialog("Saving to Server...", "Abort", 0, len(self.update)+1)
                progress.setWindowModality(QtCore.Qt.WindowModal)

                i = 0
                progress.setValue(i)
                progress.setLabelText('Connecting to server...')
                
                self.ftp.cwd('/')
                self.ftp.cwd(Globals.configData.RemoteDatabasePath)

                print "Retrieving any files modified by others..."
                self.RetrieveModifiedFiles(self.splashScreen)
                
                progress.setLabelText('Uploading Files...')
                LogTable = []
                saveUpdate = set()
                
                # stagger upload into multiple 10-file batches
                # the way this is written we cannot keep it, but eh
                singleFileUploadCounter = 0
                
                for filename in self.update:
                    singleFileUploadCounter = singleFileUploadCounter + 1
                    if singleFileUploadCounter > 10:
                        autoRestartAfter = True
                        saveUpdate.add(filename)
                        continue
                    
                    # remove empty comments
                    rcommentconn = sqlite3.connect(Globals.configData.LocalDatabasePath + "/" + filename)
                    rcommentcur = rcommentconn.cursor()
                    rcommentcur.execute(u"UPDATE text SET comment = '', updated = 1 WHERE comment IS NULL")
                    rcommentconn.commit()
                    rcommentconn.close()
                    
                    Globals.CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [filename])
                    exists = Globals.CursorGracesJapanese.fetchall()[0][0]
                    if exists > 0:
                        Globals.CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [filename])
                        desc = Globals.CursorGracesJapanese.fetchall()[0][0]
                        print 'Uploading ' + desc + ' [' + filename + ']...'
                    else:
                        print 'Uploading ' + filename + '...'

                    # Downloading the server version and double checking
                    self.DownloadFile(self.ftp, str(filename), 'temp')

                    try:
                        WipeUpdateCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/temp")
                        WipeUpdateCur = WipeUpdateCon.cursor()
                
                        WipeUpdateCur.execute(u"update Text set updated=0")
                        WipeUpdateCon.commit()
                        
                        # Merging the Server and the local version
                        NewMergeCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(filename))
                        NewMergeCur = NewMergeCon.cursor()
            
                        OldMergeCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/temp")
                        OldMergeCur = OldMergeCon.cursor()
                                
                        NewMergeCur.execute(u'SELECT id, stringid, english, comment, updated, status FROM Text WHERE updated=1')
                        NewTable = NewMergeCur.fetchall()
                    
                        for item in NewTable:
                            if item[4] == 1:
                                OldMergeCur.execute(u"UPDATE Text SET english=?, comment=?, status=? WHERE ID=?", (item[2], item[3], item[5], item[0]))
                        OldMergeCon.commit()
                        
                        # Upload new file
                        for ftpSingleFileUpErrorCount in range(1, 20):
                            try:
                                if ftpSingleFileUpErrorCount >= 20:
                                    print 'Failed on single file 20 files, try again later and confirm the server file is not corrupted.'
                                    print 'File in question: ' + filename
                                    return
                                result = self.UploadFile(self.ftp, 'temp', str(filename))
                                if isinstance(result, str):
                                    continue
                                break
                            except ftplib.all_errors:
                                print 'Error uploading ' + filename + ', retrying...'
                                continue
            
                        # Transposing the local file
                        fnew = open(Globals.configData.LocalDatabasePath + '/temp', 'rb')
                        data = fnew.read()
                        fnew.close()
                        
                        old = open(Globals.configData.LocalDatabasePath + '/{0}'.format(filename), 'wb')
                        old.write(data)
                        old.close()

                    except:
                    
                        print 'Server file corrupted. Fixing...'
                        
                        self.UploadFile(self.ftp, filename, filename)
                    
                        print 'Fixed'

                    i = i + 1
                    progress.setValue(i)

                    LogTable.append(filename)
                    
                    CompletionTable.CalculateCompletionForDatabase(filename)

                # Fix up the changelog and upload
                Globals.LogCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/ChangeLog")
                Globals.LogCur = Globals.LogCon.cursor()

                Globals.LogCur.execute('select Max(ID) as Highest from Log')
                MaxID = Globals.LogCur.fetchall()[0][0]

                fileString = ''.join(["%s," % (k) for k in LogTable])[:-1]
                print 'Uploaded: ', fileString
                
                Globals.LogCur.execute(u"insert into Log values({0}, '{1}', '{2}', {3})".format(MaxID + 1, fileString, self.author, "strftime('%s','now')"))
                Globals.LogCon.commit()

                print 'Uploading: ChangeLog'
                changeLogUploadSuccess = False
                for changeup in range(1, 20):
                    try:
                        result = self.UploadFile(self.ftp, 'ChangeLog', 'ChangeLog', False)
                        if result != True:
                            if changeup >= 20:
                                print "ERROR:\n\nChangelog has not been uploaded, please retry immediately."
                                break
                            else:
                                print 'Changelog upload failed, trying again! ({0}/20)'.format(changeup)
                                continue
                        #self.ftp.rename('NewChangeLog', 'ChangeLog')
                        changeLogUploadSuccess = True
                        break
                    except ftplib.all_errors:
                        if changeup >= 20:
                            print 'ERROR:\n\Changelog has not been uploaded, please retry immediately.'
                            break
                        print 'Error uploading Changelog, retrying...'
                        continue
                if changeLogUploadSuccess == False:
                    return
                
                # Everything is done.
                progress.setValue(len(self.update)+1);

                print 'Done!'
                self.ftp.close()
                
                print 'Retaining the following files for later upload: ', saveUpdate
                self.update.clear()
                self.update = set(saveUpdate)
                self.settings.setValue('update', self.update)
                self.settings.sync()
                
                if autoRestartAfter == True:
                    self.SavetoServer()
                break
            except ftplib.all_errors:
                if ftperrorcount >= 20:
                    print '20 errors is enough, this is not gonna work. There is probably some fucked up file on the FTP server now, please fix manually or contact someone that knows how to.'
                    break
                print 'Error during FTP transfer, retrying...'
                continue

    def RevertFromServer(self):
        self.WriteDatabaseStorageToHdd()
        
        if len(self.update) == 0:
            print 'Nothing to revert!'
            return

        print 'Reverting databases...'
        
        
        for i in range(1, 20):
            try:        
                try:
                    self.ftp = FTP(Globals.configData.FTPServer, Globals.configData.FTPUsername, Globals.configData.FTPPassword, "", 15)
                except:
                    if i == 20:
                        print "FTP connection failed, revert didn't succeed.\nPlease try to revert again at a later date."
                        self.settings.setValue('update', set(self.update))
                        self.settings.sync()
                        return
                    print 'Error during FTP transfer, retrying...'
                    continue
               
                self.ftp.cwd('/')
                self.ftp.cwd(Globals.configData.RemoteDatabasePath)

                print "Re-getting changed files from server..."
                for item in self.update:
                    Globals.CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [item])
                    exists = Globals.CursorGracesJapanese.fetchall()[0][0]
                    if exists > 0:
                        Globals.CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [item])
                        desc = Globals.CursorGracesJapanese.fetchall()[0][0]
                        print 'Downloading ' + desc + ' [' + item + ']...'
                    else:
                        print 'Downloading ' + item + '...'
                    
                    
                    
                    self.DownloadFile(self.ftp, item, item)
                    WipeUpdateCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(item))
                    WipeUpdateCur = WipeUpdateCon.cursor()
            
                    WipeUpdateCur.execute(u"update Text set updated=0")
                    WipeUpdateCon.commit()
                    
                    CompletionTable.CalculateCompletionForDatabase(item)

                self.ftp.close()
                self.update.clear()
                self.settings.setValue('update', self.update)
                self.settings.sync()
                print 'Reverted!'
                break
            except ftplib.all_errors:
                if i == 20:
                    print '20 errors is enough, this is not gonna work. Try again later.'
                    break
                print 'Error during FTP transfer, retrying...'
                continue
    
    
    def SavetoPatch(self):
        self.WriteDatabaseStorageToHdd()
        


        # Make some output directories
        if not os.path.exists('riivolution'):
            os.makedirs('riivolution')

        if not os.path.exists('Graces'):
            os.makedirs('Graces')

        if not os.path.exists('Resources/Wii'):
            os.makedirs('Resources/Wii')

        rootFile = open('Graces/rootR.bin', 'wb')
        map0File = open('Graces/map0R.bin', 'wb')
        map1File = open('Graces/map1R.bin', 'wb')



        # Everyone loves progress bars!
        progress = QtGui.QProgressDialog("Saving databases...", "Abort", 0, 1260)
        progress.setWindowModality(QtCore.Qt.WindowModal)


        Archive = Globals.configDataGracesFolders[1][:] # Chat_MS
        Archive.extend(Globals.configDataGracesFolders[2][:]) # Chat_SB
        Archive.extend(Globals.configDataGracesFolders[-1][:]) # SysString.bin
        Archive = (['TOG_SS_ChatName', 'TOG_SS_StringECommerce']) # Special Cased Sys Subs
        Archive.extend(Globals.configDataGracesFolders[-2][:]) # Movie Subtitles
        Archive.extend(Globals.configDataGracesFolders[-3][:]) # Special Strings

        print 'Creating root (Chat, SysString, Subtitles, Special stuff)'
        self.MakeSCS(Archive, progress, 'Wii', rootFile)

        Images = ["Resources/TitleTexture.tex", 
                  "Resources/main.tex",
                  "Resources/shop.tex",
                  "Resources/skill.tex",
#                  "Resources/snd_test.tex",
                  "Resources/bin000.acf",
                  "Resources/FontTexture2.tex",
                  "Resources/FontBinary2.bin",
                  "Resources/mainRR.sel"
                  ]

        for image in Images:
            tempFile = open(image, 'rb')
            tempData = tempFile.read()
            rootFile.write(tempData)
            tempFile.close()
        rootFile.close()



        Map0RCPK = ['mapfile_basiR.cpk', 'mapfile_briaR.cpk', 'mapfile_bridR.cpk', 'mapfile_caveR.cpk', 'mapfile_fallR.cpk', 'mapfile_ff12R.cpk', 'mapfile_ff13R.cpk', 'mapfile_ff14R.cpk', 'mapfile_ff15R.cpk', 'mapfile_ff16R.cpk', 'mapfile_ff17R.cpk', 'mapfile_ff19R.cpk', 'mapfile_ff20R.cpk', 'mapfile_foreR.cpk', 'mapfile_gentR.cpk', 'mapfile_icebR.cpk', 'mapfile_ironR.cpk', 'mapfile_koneR.cpk', 'mapfile_kotR.cpk', 'mapfile_lasR.cpk', 'mapfile_montR.cpk', 'mapfile_rockR.cpk', 'mapfile_sandR.cpk', 'mapfile_sf08R.cpk', 'mapfile_sf09R.cpk', 'mapfile_sf10R.cpk', 'mapfile_sf11R.cpk', 'mapfile_sf18R.cpk', 'mapfile_sneeR.cpk', 'mapfile_snowR.cpk', 'mapfile_stdaR.cpk', 'mapfile_varoR.cpk', 'mapfile_wf01R.cpk', 'mapfile_wf02R.cpk', 'mapfile_wf03R.cpk', 'mapfile_wf04R.cpk', 'mapfile_wf05R.cpk', 'mapfile_wf06R.cpk', 'mapfile_wf07R.cpk', 'mapfile_wf21R.cpk', 'mapfile_wincR.cpk', 'mapfile_zoneR.cpk']

        i = 4

        print 'Creating Map0'
        for CPK in Map0RCPK:
            Archive = Globals.configDataGracesFolders[i]
            self.MakeSCS(Archive, progress, 'Wii', map0File)
            i += 1
            
        map0File.close()
        

        Map1RCPK = ['mapfile_anmaR.cpk', 'mapfile_beraR.cpk', 'mapfile_debugR.cpk', 'mapfile_fendR.cpk', 'mapfile_kameR.cpk', 'mapfile_koya_r06R.cpk', 'mapfile_lakeR.cpk', 'mapfile_lanR.cpk', 'mapfile_nekoR.cpk', 'mapfile_olleR.cpk', 'mapfile_otheR.cpk', 'mapfile_ozweR.cpk', 'mapfile_riotR.cpk', 'mapfile_sablR.cpk', 'mapfile_shatR.cpk', 'mapfile_shipR.cpk', 'mapfile_strtR.cpk', 'mapfile_supaR.cpk', 'mapfile_systemR.cpk', 'mapfile_winR.cpk']

        i = 46

        print 'Creating Map1'
        for CPK in Map1RCPK:
            Archive = Globals.configDataGracesFolders[i]
            self.MakeSCS(Archive, progress, 'Wii', map1File)
            i += 1

        map1File.close()
        
        progress.setValue(1260)


        #shutil.rmtree('Resources/Wii')



    def MakeSCS(self, allFiles, progress, path, BIN=None):
        self.WriteDatabaseStorageToHdd()
        


        # Create the .scs files
        
        JPCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/GracesJapanese')
        JPCur = JPCon.cursor()

        fileExceptions = ['GracesJapanese', 'NewChangeLog', 'None', 'ChangeLog', 'temp', '.DS_Store', 'endingData', 'Artes', 'Battle', 'Discovery', 'GradeShop-Missions', 'Item', 'MonsterBook', 'Skills', 'System', 'Tactics', 'Titles', 'Tutorial', 'soundTest', 'ArteNames', 'Skits', 'GracesFDump', 'S', 'CheckTags.bat', 'System.Data.SQLite.DLL', 'GraceNote_CheckTags.exe', 'sqlite3.exe', 'taglog.txt', 'CompletionPercentage']

        i = 0
        p = 0


        for filename in allFiles:

            progress.setValue(progress.value() + 1)

            if fileExceptions.count(filename) > 0:
                continue
            print filename

            OutCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/{0}'.format(filename))
            OutCur = OutCon.cursor()

            
            OutCur.execute("select english, StringID from Text")
            i += 1
            
            stringlist = []
            TempList = OutCur.fetchall()
            
            for i in xrange(len(TempList)):

                # Generate Strings Table
                if TempList[i][0] != '':
                    string = re.sub(u"'+", "'", unicode(TempList[i][0]))
                    string = re.sub(u"‾", u"~", unicode(string))
                    string = unicode(string).replace(u" ", u"_")
                    string = unicode(string).replace(u"　", u"_")
                    string = unicode(string).encode('cp932', 'ignore')
                    if string.endswith('\x00') != True:
                        string = string + '\x00'        
                    stringlist.append(string)
                else:
                    JPCur.execute("select string from Japanese where ID={0}".format(TempList[i][1]))
                    p += 1
                    string = JPCur.fetchall()[0][0]
                    string = re.sub(u"‾", u"~", unicode(string))
                    string = unicode(string).replace(u" ", u"_")
                    string = unicode(string).replace(u"　", u"_")
                    string = unicode(string).encode('cp932', 'ignore')
                    if string.endswith('\x00') != True:
                        string = string + '\x00'        
                    stringlist.append(string)
        
        
            # Generate Length Table
            length = (len(stringlist) * 4) + 4
            newlenlist = [struct.pack('>I', len(stringlist))]
            for x in stringlist:
                newlenlist.append(struct.pack('>I', length))
                length += len(x)
                    
                                
            # Generate the concatenated strings
            newlendata = "".join(["%s" % (k) for k in newlenlist])
            stringdata = "".join(["%s" % (k) for k in stringlist])


            # Exceptions
            if filename == 'CharName':
                f = open('Resources/CharNameHeader.bin', 'rb')
                CharNameHeader = f.read()
                f.close()
                
                newlendata = CharNameHeader + newlendata

            if filename == 'CharName-f':
                f = open('Resources/FResources/CharNameHeader.bin', 'rb')
                CharNameHeader = f.read()
                f.close()
                
                newlendata = CharNameHeader + newlendata
                
            if filename == 'TOG_SS_ChatName':
                ChatNameHeader = unhexlify('0000000C000000140000015D544F31305F434E2000000000')
                
                length = (len(stringlist) * 4)
                newlenlist = []
                for x in stringlist:
                    newlenlist.append(struct.pack('>I', length))
                    length += (len(x) - 4)
                    
                newlendata = ChatNameHeader + "".join(["%s" % (k) for k in newlenlist])

            if filename == 'TOG_SS_ChatName-f':
                ChatNameHeader = unhexlify('0000000C00000014000001B1544F31305F434E2000000000')
                
                length = (len(stringlist) * 4)
                newlenlist = []
                for x in stringlist:
                    newlenlist.append(struct.pack('>I', length))
                    length += (len(x) - 4)
                    
                newlendata = ChatNameHeader + "".join(["%s" % (k) for k in newlenlist])

            if filename == 'TOG_SS_StringECommerce':
                ChatNameHeader = unhexlify('0000000C000000140000003A544F47535452462000000000')
                
                length = (len(stringlist) * 4) + 4
                newlenlist = [struct.pack('>I', len(stringlist))]
                i = 0
                for x in stringlist:
                    newlenlist.append(struct.pack('>I', i))
                    newlenlist.append(struct.pack('>I', length))
                    length += len(x)
                    i += 1
                    
                newlendata = "".join(["%s" % (k) for k in newlenlist])
                newlendata = ChatNameHeader + newlendata[4:]

            
            if filename == 'MapName':

                indexList = [0, 0, 1, 2, 3, 4, 5, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 51, 52, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 47, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 86, 87, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 126, 127, 127, 128, 128, 129, 130, 131, 132, 133, 134, 135, 135, 136, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 147, 148, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 47, 48, 159, 160, 161, 161, 1, 162, 1, 163, 1, 164, 1, 165, 1, 166, 1, 167, 1, 168, 1, 169, 1, 170, 1, 171, 1, 172, 1, 173, 174, 175, 1, 176, 1, 177, 1, 178, 1, 179, 1, 180, 1, 181, 1, 182, 1, 183, 1, 184, 1, 185, 1, 186, 1, 186, 1, 186, 3, 186, 7, 187, 7, 188, 189, 190, 137, 191, 137, 192, 9, 193, 189, 194, 11, 195, 189, 196, 139, 197, 139, 198, 13, 199, 15, 200, 15, 201, 189, 202, 17, 203, 19, 204, 21, 205, 23, 206, 189, 207, 25, 208, 27, 209, 141, 210, 141, 211, 29, 212, 143, 213, 143, 214, 31, 215, 189, 216, 33, 217, 145, 218, 145, 219, 35, 220, 37, 221, 39, 222, 41, 223, 43, 224, 45, 225, 47, 226, 49, 227, 49, 228, 53, 229, 53, 230, 53, 231, 53, 232, 53, 233, 53, 234, 53, 235, 53, 236, 53, 237, 53, 238, 53, 239, 53, 240, 53, 241, 53, 242, 53, 243, 53, 244, 53, 245, 53, 246, 53, 247, 53, 248, 55, 249, 55, 250, 251, 252, 55, 253, 55, 254, 55, 255, 55, 256, 55, 257, 55, 258, 55, 259, 55, 260, 251, 261, 55, 262, 55, 263, 55, 264, 55, 265, 55, 266, 55, 267, 55, 268, 55, 269, 55, 270, 57, 271, 57, 272, 273, 274, 57, 275, 57, 276, 57, 277, 57, 278, 57, 279, 57, 280, 59, 281, 59, 282, 61, 283, 61, 284, 61, 285, 61, 286, 63, 287, 63, 288, 63, 289, 63, 290, 63, 291, 63, 292, 63, 293, 63, 294, 63, 295, 63, 296, 63, 297, 63, 298, 63, 299, 65, 300, 65, 301, 65, 302, 67, 303, 67, 304, 67, 305, 67, 306, 69, 307, 308, 309, 69, 310, 69, 311, 69, 312, 69, 313, 69, 314, 69, 315, 69, 316, 69, 317, 308, 318, 71, 319, 71, 320, 71, 321, 71, 322, 71, 323, 71, 324, 73, 325, 73, 326, 73, 327, 73, 328, 73, 329, 73, 330, 73, 331, 73, 332, 75, 333, 75, 334, 335, 336, 78, 337, 78, 338, 80, 339, 80, 340, 82, 341, 84, 342, 88, 343, 344, 345, 346, 347, 90, 348, 90, 349, 92, 350, 94, 351, 94, 352, 96, 353, 96, 354, 98, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 382, 384, 382, 385, 382, 386, 382, 387, 382, 388, 382, 389, 382, 390, 100, 391, 100, 392, 100, 393, 100, 394, 100, 395, 100, 396, 100, 397, 100, 398, 100, 399, 100, 400, 100, 401, 100, 402, 100, 403, 100, 404, 100, 405, 100, 406, 100, 407, 100, 408, 100, 409, 100, 410, 100, 411, 100, 412, 102, 413, 102, 414, 104, 415, 416, 417, 416, 418, 416, 419, 420, 421, 420, 422, 420, 423, 420, 424, 420, 425, 426, 427, 426, 428, 426, 429, 426, 430, 426, 431, 426, 432, 426, 433, 434, 435, 434, 436, 434, 437, 438, 439, 438, 440, 438, 441, 438, 442, 434, 443, 434, 444, 434, 445, 446, 447, 446, 448, 446, 449, 106, 450, 451, 452, 453, 454, 455, 456, 455, 457, 458, 459, 458, 460, 461, 462, 461, 463, 461, 464, 461, 465, 461, 466, 461, 454, 461, 456, 467, 457, 467, 468, 469, 470, 469, 471, 472, 473, 108, 474, 108, 475, 108, 476, 108, 477, 108, 478, 108, 479, 108, 480, 108, 481, 108, 482, 108, 483, 110, 484, 110, 485, 110, 486, 110, 487, 110, 488, 110, 489, 110, 490, 110, 491, 110, 492, 110, 493, 110, 494, 110, 495, 110, 496, 110, 497, 110, 498, 110, 499, 112, 500, 112, 501, 112, 502, 112, 503, 112, 504, 112, 505, 112, 506, 112, 507, 112, 508, 112, 509, 112, 510, 112, 511, 112, 512, 112, 513, 112, 514, 112, 515, 112, 516, 112, 517, 112, 518, 112, 519, 112, 520, 112, 521, 112, 522, 112, 523, 112, 524, 112, 525, 112, 526, 112, 527, 528, 529, 528, 530, 531, 532, 531, 533, 531, 534, 535, 536, 535, 537, 535, 538, 535, 539, 540, 541, 540, 542, 540, 543, 544, 545, 544, 546, 528, 547, 528, 548, 531, 549, 531, 550, 535, 551, 535, 552, 535, 553, 535, 554, 540, 555, 540, 556, 540, 557, 558, 559, 544, 560, 535, 561, 116, 562, 116, 563, 116, 564, 116, 565, 116, 566, 116, 567, 116, 568, 116, 569, 116, 570, 116, 571, 116, 572, 116, 573, 116, 574, 116, 575, 116, 576, 116, 577, 116, 578, 118, 579, 118, 580, 581, 582, 581, 583, 581, 584, 581, 585, 581, 586, 581, 587, 581, 588, 581, 589, 581, 590, 581, 591, 581, 592, 581, 593, 581, 594, 581, 595, 581, 596, 581, 597, 581, 598, 581, 599, 581, 600, 581, 601, 581, 602, 581, 603, 581, 604, 581, 605, 581, 606, 581, 607, 581, 608, 609, 610, 609, 611, 609, 612, 609, 613, 614, 615, 614, 616, 617, 618, 619, 620, 619, 621, 122, 622, 122, 623, 122, 624, 625, 626, 124, 627, 189, 628, 625, 629, 126, 630, 126, 631, 131, 632, 131, 633, 131, 634, 131, 635, 133, 636, 133, 637, 133, 638, 133, 639, 133, 640, 133, 641, 133, 642, 133, 643, 133, 644, 133, 645]
                
                newlendata = struct.pack('>I', len(indexList))
                
                for listItem in indexList:
                    newlendata += struct.pack('>I', struct.unpack('>I', newlenlist[listItem+1])[0] + 0x684)



            if BIN == None:
                # Write it to a file
                binFiles = ['ActInfo', 'CharName', 'MapName', 'Navigation', 'TOG_S01', 'TOG_S02', 'TOG_S03', 'TOG_S04', 'TOG_S05', 'TOG_S06', 'TOG_S07', 'TOG_S08', 'TOG_S09', 'TOG_S10', 'TOG_S11', 'SysString']
                
                datFiles = ['TOG_SS_ChatName', 'TOG_SS_StringECommerce']
                
                if binFiles.count(filename) >0:
                    with open('Resources/{0}/{1}.bin'.format(path,filename), 'wb') as f:
                        writeOut = (newlendata + stringdata) 
                        f.write(writeOut + '\x00'*(0x1000-(len(writeOut)%0x1000)))
                        f.close()
                if datFiles.count(filename) >0:
                    with open('Resources/{0}/{1}.dat'.format(path,filename), 'wb') as f:
                        writeOut = (newlendata + stringdata) 
                        f.write(writeOut + '\x00'*(0x1000-(len(writeOut)%0x1000)))
                        f.close()
                else:
                    with open('Resources/{0}/{1}.scs'.format(path,filename), 'wb') as f:
                        writeOut = (newlendata + stringdata) 
                        f.write(writeOut + '\x00'*(0x1000-(len(writeOut)%0x1000)))
                        f.close()
                        
            else:
                writeOut = (newlendata + stringdata) 
                BIN.write(writeOut + '\x00'*(0x1000-(len(writeOut)%0x1000)))



#    def BabysitGraceful(self, args):
#        exec_args = args[:2]
#        args      = args[2:]
#        args.append('11') #Make sure to manually quit
#        stdout_dump = StringIO.StringIO()
#        if sys.platform == 'win32': exec_args.pop(0) #We don't need the "mono" argument in win32, so remove it
#        proc = subprocess.Popen(exec_args, shell=False, stdin=subprocess.PIPE,stdout=subprocess.PIPE)
#        while args:
#            arg = args.pop(0)
#            print arg
#            subprocess.send_all(proc, arg + '\n')
#            stdout_dump.write(subprocess.recv_some(proc, t=.01, tr=2))
#        stdout_dump.write(proc.recv())
#        return stdout_dump.getvalue()


    def SavetoXML(self):
        self.WriteDatabaseStorageToHdd()
        


        # Make some output directories
        if not os.path.exists('riivolution'):
            os.makedirs('riivolution')

        if not os.path.exists('Graces'):
            os.makedirs('Graces')

        if not os.path.exists('Graces/v0'):
            os.makedirs('Graces/v0')

        if not os.path.exists('Resources/Wii'):
            os.makedirs('Resources/Wii')


        if self.settings.contains('Graceful'):
            Graceful = self.settings.value('Graceful')
            if not os.path.isfile(Graceful):
                Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
                if Graceful == '': return
                Graceful = str(Graceful)
        else:
            Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
            if Graceful == '': return
            Graceful = str(Graceful)
        self.settings.setValue("Graceful", Graceful)

        if self.settings.contains('RootR'):
            RootR = self.settings.value('RootR')
            if not os.path.isfile(RootR):
                RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if RootR == '': return
                RootR = str(RootR)
        else:
            RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if RootR == '': return
            RootR = str(RootR)
        self.settings.setValue("RootR", RootR)

        if self.settings.contains('Map0R'):
            Map0R = self.settings.value('Map0R')
            if not os.path.isfile(Map0R):
                Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if Map0R == '': return
                Map0R = str(Map0R)
        else:
            Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map0R == '': return
            Map0R = str(Map0R)
        self.settings.setValue("Map0R", Map0R)

        if self.settings.contains('Map1R'):
            Map1R = self.settings.value('Map1R')
            if not os.path.isfile(Map1R):
                Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if Map1R == '': return
                Map1R = str(Map1R)
        else:
            Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map1R == '': return
            Map1R = str(Map1R)
        self.settings.setValue("Map1R", Map1R)

        
        #Delety function!
        TestPath = [os.path.dirname(str(RootR)), os.path.dirname(str(Map0R)), os.path.dirname(str(Map1R))]
        
        for Path in TestPath:
            for File in os.listdir(Path):
                if File.rfind('.toc') >= 0:
                    os.remove(Path + "/" + File)
                if File.rfind('.patch') >=0:
                    os.remove(Path + '/' + File)


        # Everyone loves progress bars!
        progress = QtGui.QProgressDialog("Saving databases to SCS...", "Abort", 0, len(os.listdir(Globals.configData.LocalDatabasePath))+1)
        progress.setWindowModality(QtCore.Qt.WindowModal)


        # Create the .scs files
        self.MakeSCS(os.listdir(Globals.configData.LocalDatabasePath), progress, 'Wii')

        progress.setValue(len(os.listdir(Globals.configData.LocalDatabasePath))+1)
 
        

        # Now do Graceful Stuff!
        progress = QtGui.QProgressDialog("Creating Riivolution Patch with Graceful...", "Abort", 0, 120)
        progress.setWindowModality(QtCore.Qt.WindowModal)

        XML = []
        GracesPath = os.path.dirname(os.path.abspath(sys.argv[0])) + os.sep + "Resources" + os.sep + 'Wii' + os.sep
        
        
        
        # RootR Scripts
        args = ["mono", str(Graceful), "4", "2", str(RootR)]

        if os.name != 'posix':
            args = []
            command = [str(Graceful), "4", "2", str(RootR)]

        rootRbin = open('Graces/rootR.bin', 'wb')

    
        # Chat  
        Archive = Globals.configDataGracesFolders[1][:] # Chat_MS
        Archive.extend(Globals.configDataGracesFolders[2][:]) # Chat_SB
        ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()
            

        # SysString
        Archive = (Globals.configDataGracesFolders[-1]) # SysString.bin
        ArchiveLocation = 'sys' + os.sep + 'ja' + os.sep
        args.extend(["{0}{1}.bin".format(GracesPath, Archive[0]), "{0}{1}.bin".format(ArchiveLocation, Archive[0])])
        tempFile = open("{0}{1}.bin".format(GracesPath, Archive[0]))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()


        # TOG stuff
        Archive = (['TOG_SS_ChatName', 'TOG_SS_StringECommerce']) # Special Cased Sys Subs
        ArchiveLocation = 'SysSub' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.dat".format(GracesPath, file), "{0}{1}.dat".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.dat".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()


        # Movies
        Archive = (Globals.configDataGracesFolders[-2]) # Movie Subtitles
        ArchiveLocation = 'movie' + os.sep + 'str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(GracesPath, file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()

        progress.setValue(10)


        # Special Strings
        Archive = (Globals.configDataGracesFolders[-3]) # Special Stuff
        ArchiveLocation = 'str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(str(GracesPath), file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()


        # Images

        Images = [("Resources/TitleTexture.tex", "SysSub/JA/TitleTexture.tex"), 
                  ("Resources/main.tex", "mnu/tex/main.tex"),
                  ("Resources/shop.tex", "mnu/tex/shop.tex"),
                  ("Resources/skill.tex", "mnu/tex/skill.tex"),
#                  ("Resources/snd_test.tex", "mnu/tex/snd_test.tex"),
                  ("Resources/bin000.acf", "btl/acf/bin000.acf"),
                  ("Resources/FontTexture2.tex", "sys/FontTexture2.tex"),
                  ("Resources/FontBinary2.bin", "sys/FontBinary2.bin"),
                  ("Resources/mainRR.sel", "module/mainRR.sel")
                  ]

        for image in Images:
            args.extend([image[0], image[1]])
            tempFile = open(image[0], 'rb')
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()


        # Run the process!
        if os.name == 'posix':
        
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
            data = proc.stdout.read()
            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
            progress.setValue(57)
            rootRbin.close()

        else:
            
            for i in range(0, len(args), 20):
                if len(args) > i+20:
                    finalArgs = command+(args[i:i+20])
                else:
                    finalArgs = command+(args[i:])
                                    
                proc=subprocess.Popen(finalArgs,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        
                data = proc.stdout.read()
                XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
            progress.setValue(57)
            rootRbin.close()
                        


        # Map0R Scripts
        Map0RCPK = ['mapfile_basiR.cpk', 'mapfile_briaR.cpk', 'mapfile_bridR.cpk', 'mapfile_caveR.cpk', 'mapfile_fallR.cpk', 'mapfile_ff12R.cpk', 'mapfile_ff13R.cpk', 'mapfile_ff14R.cpk', 'mapfile_ff15R.cpk', 'mapfile_ff16R.cpk', 'mapfile_ff17R.cpk', 'mapfile_ff19R.cpk', 'mapfile_ff20R.cpk', 'mapfile_foreR.cpk', 'mapfile_gentR.cpk', 'mapfile_icebR.cpk', 'mapfile_ironR.cpk', 'mapfile_koneR.cpk', 'mapfile_kotR.cpk', 'mapfile_lasR.cpk', 'mapfile_montR.cpk', 'mapfile_rockR.cpk', 'mapfile_sandR.cpk', 'mapfile_sf08R.cpk', 'mapfile_sf09R.cpk', 'mapfile_sf10R.cpk', 'mapfile_sf11R.cpk', 'mapfile_sf18R.cpk', 'mapfile_sneeR.cpk', 'mapfile_snowR.cpk', 'mapfile_stdaR.cpk', 'mapfile_varoR.cpk', 'mapfile_wf01R.cpk', 'mapfile_wf02R.cpk', 'mapfile_wf03R.cpk', 'mapfile_wf04R.cpk', 'mapfile_wf05R.cpk', 'mapfile_wf06R.cpk', 'mapfile_wf07R.cpk', 'mapfile_wf21R.cpk', 'mapfile_wincR.cpk', 'mapfile_zoneR.cpk']

        map0Rbin = open('Graces/map0R.bin', 'wb')


        i = 4

        for CPK in Map0RCPK:
            args = ["mono", str(Graceful), "4", "1", str(Map0R), CPK]
            if os.name != 'posix':
                args = [str(Graceful), "4", "1", str(Map0R), CPK]
            
            Archive = Globals.configDataGracesFolders[i]
            i += 1
            ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

            for file in Archive:
                args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

                tempFile = open("{0}{1}.scs".format(GracesPath, file))
                tempData = tempFile.read()
                map0Rbin.write(tempData)
                tempFile.close()


            # Run the process!
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
            data = proc.stdout.read()
            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
            progress.setValue(progress.value() + 1)

        map0Rbin.close()
        

        # Map1R Scripts
        Map1RCPK = ['mapfile_anmaR.cpk', 'mapfile_beraR.cpk', 'mapfile_debugR.cpk', 'mapfile_fendR.cpk', 'mapfile_kameR.cpk', 'mapfile_koya_r06R.cpk', 'mapfile_lakeR.cpk', 'mapfile_lanR.cpk', 'mapfile_nekoR.cpk', 'mapfile_olleR.cpk', 'mapfile_otheR.cpk', 'mapfile_ozweR.cpk', 'mapfile_riotR.cpk', 'mapfile_sablR.cpk', 'mapfile_shatR.cpk', 'mapfile_shipR.cpk', 'mapfile_strtR.cpk', 'mapfile_supaR.cpk', 'mapfile_systemR.cpk', 'mapfile_winR.cpk']


        map1Rbin = open('Graces/map1R.bin', 'wb')

        i = 46

        for CPK in Map1RCPK:
            args = ["mono", str(Graceful), "4", "1", str(Map1R), CPK]
            if os.name != 'posix':
                args = [str(Graceful), "4", "1", str(Map0R), CPK]
            
            Archive = Globals.configDataGracesFolders[i]
            i += 1
            ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

            for file in Archive:
                args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

                tempFile = open("{0}{1}.scs".format(GracesPath, file))
                tempData = tempFile.read()
                map1Rbin.write(tempData)
                tempFile.close()


            # Run the process!
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
            data = proc.stdout.read()
            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
            progress.setValue(progress.value() + 1)

        map1Rbin.close()


        # Let's make an XML! And also move all those .toc files over

        for Path in TestPath:
            for File in os.listdir(Path):
                if File.rfind('.toc') >= 0:
                    try:
                        os.remove("Graces/v0/" + File)
                    except:
                        pass
                    shutil.move(Path + "/" + File, "Graces/v0")
                if File.rfind('.patch') >=0:
                    try:
                        os.remove("Graces/v0/" + File)
                    except:
                        pass
                    shutil.move(Path + "/" + File, "Graces/v0")
                    
        #shutil.rmtree("Resources/Wii")


        XMLset = set(XML)
        XMLFinal = []
        for entry in XMLset:
            XMLFinal.append(entry)
        
        XMLFinal.sort()    
                
        xmlFile = open("riivolution/Graces.xml", "w")
        
        
        
        patchFile = open("Graces/v0/rootR.cpk.patch", "r")
        rootRPatch = patchFile.readline()
        patchFile.close()

        patchFile = open("Graces/v0/map0R.cpk.patch", "r")
        map0RPatch = patchFile.readline()
        patchFile.close()

        patchFile = open("Graces/v0/map1R.cpk.patch", "r")
        map1RPatch = patchFile.readline()
        patchFile.close()

                

        XMLString = [
        
        '<wiidisc version="1">\n',        
        '\t<id game="STG" version="0"/>\n',
        '\t<options>\n',
        '\t\t<section name="Testing">\n',
        
        '\t\t\t<option name="Graces Translation" default="1">\n',
        '\t\t\t\t<choice name="Enabled">\n',
        '\t\t\t\t\t<patch id="graces" />\n',
        '\t\t\t\t\t<patch id="gracesfiles" />\n',
        '\t\t\t\t</choice>\n',
        '\t\t\t</option>\n',

        '\t\t\t<option name="Bugfixes" default="1">\n',
        '\t\t\t\t<choice name="v2 Patch">\n',
        '\t\t\t\t\t<patch id="doll" />\n',
        '\t\t\t\t</choice>\n',
        '\t\t\t\t<choice name="Original">\n',
        '\t\t\t\t\t<patch id="localeZero" />\n',
        '\t\t\t\t</choice>\n',
        '\t\t\t</option>\n',
        
        '\t\t\t<option name="Debug Output">\n',
        '\t\t\t\t<choice name="For Original (v0)">\n',
        '\t\t\t\t\t<patch id="kamek_Ori" />\n',
        '\t\t\t\t</choice>\n',
        '\t\t\t</option>\n',
        
        '\t\t</section>\n',
        '\t</options>\n',
        
        '\t<patch id="doll" root="/Resources">\n',
        '\t\t<file disc="main.dol" external="main.dol" />\n',
		'\t\t<file disc="mainRR.sel" external="mainRR.sel" />\n'
        '\t\t<memory offset="0x803595DC" value="38600000" />\n',
        '\t</patch>\n',

        '\t<patch id="localeZero">\n',
        '\t\t<memory offset="0x803586DC" value="38600000" />\n',
        '\t</patch>\n',

        '\t<patch id="graces" root="/Graces/v0">\n',
        '\t\t<file disc="/rootR.cpk" external="rootR.cpk.patch" offset="{0}" resize="true" />\n'.format(rootRPatch),
        '\t\t<file disc="/map0R.cpk" external="map0R.cpk.patch" offset="{0}" resize="true" />\n'.format(map0RPatch),
        '\t\t<file disc="/map1R.cpk" external="map1R.cpk.patch" offset="{0}" resize="true" />\n'.format(map1RPatch),
        "".join(["\t\t%s\n" % (k) for k in XMLFinal[:63]]), #[:63]
        '\t</patch>\n',

        '\t<patch id="gracesfiles" root="/Graces">\n',
        '\t\t<file resize="false" offset="0x70000000" disc="map0R.cpk" external="map0R.bin" />\n',
	    '\t\t<file resize="false" offset="0x70000000" disc="map1R.cpk" external="map1R.bin" />\n',
	    '\t\t<file resize="false" offset="0x70000000" disc="rootR.cpk" external="rootR.bin" />\n',
        '\t</patch>\n',
        
        '\t<patch id="kamek_Ori">\n',
        '\t\t<memory offset="0x80035C10" value="4bfcbc2c" />\n',
        '\t\t<memory offset="0x80001800" value="9421fff07c0802a693e1000c7c7f1b783c60800090010014386318f04cc63182480343f1800100147fe3fb7883e1000c7c0803a6382100104e8000207c0802a69421ef8093e1107c900110849081101c90a1102090c1102490e110289101102c912110309141103440860024d8211038d8411040d8611048d8811050d8a11058d8c11060d8e11068d9011070380000013be10014980100083800000098010009380110887c641b7838a100089001000c7fe3fb7838011018900100104832e8457fe3fb78483258f9388000017c651b7838c000007fe3fb784832b5418001108483e1107c382110807c0803a64e8000206c6f6c0a00" />\n',
        '\t</patch>\n',
        
        '</wiidisc>'
        
        ]
        
        xmlFile.write("".join(["%s" % (k) for k in XMLString]))
        progress.setValue(progress.value() + 1)

        xmlFile.close()



    def SavetoGracesfDemoXML(self):
        self.WriteDatabaseStorageToHdd()
        


        if os.name != 'posix':
            reply = QtGui.QMessageBox.information(self, "Incompatible OS", "Attention:\n\nThis feature is only compatible with posix style operating systems. Please use the distributed XML along with the 'save to patch' feature.")
            return        

        # Make some output directories
        if not os.path.exists('riivolution'):
            os.makedirs('riivolution')

        if not os.path.exists('Graces'):
            os.makedirs('Graces')

        if not os.path.exists('Graces/fDemo'):
            os.makedirs('Graces/fDemo')

        if not os.path.exists('Resources/fDemo'):
            os.makedirs('Resources/fDemo')


        if self.settings.contains('Graceful'):
            Graceful = self.settings.value('Graceful')
            if not os.path.isfile(Graceful):
                Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
                if Graceful == '': return
                Graceful = str(Graceful)
        else:
            Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
            if Graceful == '': return
            Graceful = str(Graceful)
        self.settings.setValue("Graceful", Graceful)

        if self.settings.contains('RootRToGf'):
            RootR = self.settings.value('RootRToGf')
            if not os.path.isfile(RootR):
                RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if RootR == '': return
                RootR = str(RootR)
        else:
            RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if RootR == '': return
            RootR = str(RootR)
        self.settings.setValue("RootRToGf", RootR)

        if self.settings.contains('Map0RToGf'):
            Map0R = self.settings.value('Map0RToGf')
            if not os.path.isfile(Map0R):
                Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if Map0R == '': return
                Map0R = str(Map0R)
        else:
            Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map0R == '': return
            Map0R = str(Map0R)
        self.settings.setValue("Map0RToGf", Map0R)

        if self.settings.contains('Map1RToGf'):
            Map1R = self.settings.value('Map1RToGf')
            if not os.path.isfile(Map1R):
                Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if Map1R == '': return
                Map1R = str(Map1R)
        else:
            Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map1R == '': return
            Map1R = str(Map1R)
        self.settings.setValue("Map1RToGf", Map1R)

        
        #Delety function!
        TestPath = [os.path.dirname(str(RootR)), os.path.dirname(str(Map0R)), os.path.dirname(str(Map1R))]
        
        for Path in TestPath:
            for File in os.listdir(Path):
                if File.rfind('.toc') >= 0:
                    os.remove(Path + "/" + File)
                    print "Removed: {0}".format(Path + "/" + File)
                if File.rfind('.patch') >=0:
                    os.remove(Path + '/' + File)
                    print "Removed: {0}".format(Path + "/" + File)


        # Everyone loves progress bars!
        progress = QtGui.QProgressDialog("Saving databases to SCS...", "Abort", 0, 16)
        progress.setWindowModality(QtCore.Qt.WindowModal)


        # Create the .scs files
        self.MakeSCS(['ActInfo-f', 'CharName-f', 'CHT_PR001-f', 'CHT_PR002-f', 'CHT_PR003-f', 'CHT_PR005-f', 'CHT_PR007-f', 'e950_020-f', 'MapName-f', 'Navigation-f', 'sofi_d02-f', 'sysm_d01-f', 'SysString-f', 'TOG_SS_ChatName-f', 'TOG_SS_StringECommerce-f'], progress, 'fDemo')

        progress.setValue(16)
 
        

        # Now do Graceful Stuff!
        progress = QtGui.QProgressDialog("Creating Riivolution Patch with Graceful...", "Abort", 0, 120)
        progress.setWindowModality(QtCore.Qt.WindowModal)

        XML = []
        GracesPath = os.path.dirname(os.path.abspath(sys.argv[0])) + os.sep + "Resources" + os.sep + "fDemo" + os.sep
        
        
        # Rename those scs files properly!
        for item in ['CHT_PR001-f', 'CHT_PR002-f', 'CHT_PR003-f', 'CHT_PR005-f', 'CHT_PR007-f', 'e950_020-f', 'sofi_d02-f', 'sysm_d01-f', 'TOG_SS_ChatName-f', 'TOG_SS_StringECommerce-f']:

            shutil.copyfile("{0}{1}.scs".format(GracesPath, item), "{0}{1}.scs".format(GracesPath, item[:-2]))

        for item in ['ActInfo-f', 'CharName-f', 'MapName-f', 'Navigation-f', 'SysString-f']:

            shutil.copyfile("{0}{1}.scs".format(GracesPath, item), "{0}{1}.bin".format(GracesPath, item[:-2]))

        
        
        # RootR Scripts
        args = ["mono", str(Graceful), "4", "2", str(RootR)]

        rootRbin = open('Graces/fDemo/rootR.bin', 'wb')

        off = 0

        # Chat  
        Archive = ['CHT_PR001', 'CHT_PR002', 'CHT_PR003', 'CHT_PR005', 'CHT_PR007'] # Chat_MS
        ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()
            
            
        # SysString        
        ArchiveLocation = 'Sys' + os.sep + 'ja' + os.sep
        args.extend(["{0}{1}.bin".format(GracesPath, 'SysString'), "{0}{1}.bin".format(ArchiveLocation, 'SysString')])
        tempFile = open("{0}{1}.bin".format(GracesPath, 'SysString'))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()


        progress.setValue(10)


        # Special Strings
        Archive = (['ActInfo', 'Navigation', 'CharName']) # Special Stuff ---  'MapName', 
        ArchiveLocation = 'Str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(str(GracesPath), file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()


        # Images

        Images = [("Resources/fDemo/TOG_SS_ChatName.scs", "SysSub/JA/TOG_SS_ChatName.dat"),
                  ("Resources/FResources/TitleTexture.tex", "SysSub/JA/TitleTexture.tex"), 
                  ("Resources/FResources/skill.tex", "mnu/tex/skill.tex"),
                  ("Resources/FResources/main.tex", "mnu/tex/main.tex"),
                  ("Resources/FResources/bin000.acf", "btl/acf/bin000.acf"),
                  ("Resources/FResources/MapName.bin", "Str/ja/MapName.bin"),
                  ("Resources/FResources/FontTexture2.tex", "Sys/FontTexture2.tex"),
                  ("Resources/FResources/FontBinary2.bin", "Sys/FontBinary2.bin"),
                  ("Resources/FResources/TrialHelp.slz", "Sys/Trial/TrialHelp.slz")
                  ]

        for image in Images:
            args.extend([image[0], image[1]])
            tempFile = open(image[0], 'rb')
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()

        # Run the process!
        print args
        proc=subprocess.Popen(args,shell=False,bufsize=-1,stdin=subprocess.PIPE,stdout=subprocess.PIPE)

        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(57)
        rootRbin.close()


        # Map0R Scripts
        Map0RCPK = ['mapfile_elemR.cpk', 'mapfile_sofiR.cpk']

        map0Rbin = open('Graces/fDemo/map0R.bin', 'wb')

        scsList = [['e950_020'], ['sofi_d02']] 


        i = 0

        for CPK in Map0RCPK:
            args = ["mono", str(Graceful), "4", "1", str(Map0R), CPK]
            if os.name != 'posix':
                args = [str(Graceful), "4", "1", str(Map0R), CPK]
            
            Archive = scsList[i]
            i += 1
            ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

            for file in Archive:
                args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

                tempFile = open("{0}{1}.scs".format(GracesPath, file))
                tempData = tempFile.read()
                map0Rbin.write(tempData)
                tempFile.close()


            # Run the process!
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
            data = proc.stdout.read()
            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
            progress.setValue(progress.value() + 1)

        map0Rbin.close()
        

        # Map1R Scripts
        Map1RCPK = 'mapfile_systemR.cpk'

        map1Rbin = open('Graces/fDemo/map1R.bin', 'wb')

        args = ["mono", str(Graceful), "4", "1", str(Map1R), Map1RCPK]
        if os.name != 'posix':
            args = [str(Graceful), "4", "1", str(Map0R), CPK]
        
        file = 'sysm_d01'
        ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

        args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

        tempFile = open("{0}{1}.scs".format(GracesPath, file))
        tempData = tempFile.read()
        map1Rbin.write(tempData)
        tempFile.close()


        # Run the process!
        proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)

        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(progress.value() + 1)

        map1Rbin.close()


        # Let's make an XML! And also move all those .toc files over

        for Path in TestPath:
            for File in os.listdir(Path):
                if File.rfind('.toc') >= 0:
                    try:
                        os.remove("Graces/fDemo/" + File)
                    except:
                        pass
                    shutil.move(Path + "/" + File, "Graces/fDemo")
                if File.rfind('.patch') >=0:
                    try:
                        os.remove("Graces/fDemo/" + File)
                    except:
                        pass
                    shutil.move(Path + "/" + File, "Graces/fDemo")
                    
        shutil.copy("Resources/FResources/PARAM.SFO", "Graces/fDemo/PARAM.SFO")
        shutil.copy("Resources/FResources/PIC1.png", "Graces/fDemo/PIC1.PNG")
        shutil.copy("Resources/FResources/ICON0.png", "Graces/fDemo/ICON0.PNG")
        shutil.copy("Resources/FResources/BootLogo.slz", "Graces/fDemo/BootLogo.slz")

        XMLset = set(XML)
        XMLFinal = []
        for entry in XMLset:
            XMLFinal.append(entry)
        
        XMLFinal.sort()    
                
        
        xmlFile = open("riivolution/GracesfDemo.xml", "w")
        
        
        
        patchFile = open("Graces/fDemo/rootR.cpk.patch", "r")
        rootRPatch = patchFile.readline()
        patchFile.close()

        patchFile = open("Graces/fDemo/map0R.cpk.patch", "r")
        map0RPatch = patchFile.readline()
        patchFile.close()

        patchFile = open("Graces/fDemo/map1R.cpk.patch", "r")
        map1RPatch = patchFile.readline()
        patchFile.close()

        for thing in XMLFinal: print thing                
        XMLString = [
        
        '<ps3disc version="1" gameroot="/dev_hdd0/game/NPJB90302/USRDIR">\n',        
        '\t<options>\n',
        '\t\t<section name="Testing">\n',
        
        '\t\t\t<option name="Graces f Demo Translation" default="1">\n',
        '\t\t\t\t<choice name="Enabled">\n',
        '\t\t\t\t\t<patch id="graces" />\n',
        '\t\t\t\t\t<patch id="gracesfiles" />\n',
        '\t\t\t\t</choice>\n',
        '\t\t\t</option>\n',
        
        '\t\t</section>\n',
        '\t</options>\n',
        
        '\t<patch id="graces" root="Graces/fDemo">\n',
        '\t\t<file disc="Logo/BootLogo.slz" external="BootLogo.slz" resize="true" />\n',
        '\t\t<file disc="/PARAM.SFO" external="PARAM.SFO" resize="true" />\n',
        '\t\t<file disc="/PIC1.PNG" external="PIC1.PNG" resize="true" />\n',
        '\t\t<file disc="/ICON0.PNG" external="ICON0.PNG" resize="true" />\n',
        '\t\t<file disc="rootR.cpk" external="rootR.cpk.patch" offset="{0}" resize="true" />\n'.format(rootRPatch),
        '\t\t<file disc="map0R.cpk" external="map0R.cpk.patch" offset="{0}" resize="true" />\n'.format(map0RPatch),
        '\t\t<file disc="map1R.cpk" external="map1R.cpk.patch" offset="{0}" resize="true" />\n'.format(map1RPatch),
        "".join(["\t\t%s\n" % (k) for k in [XMLFinal[0], XMLFinal[1], XMLFinal[2], XMLFinal[4]]]), #[:0,1,2,4]
        '\t</patch>\n',

        '\t<patch id="gracesfiles" root="Graces/fDemo">\n',
        '\t\t<file resize="false" offset="0x02253A60" disc="map0R.cpk" external="map0R.bin" />\n',
	    '\t\t<file resize="false" offset="0x002211E0" disc="map1R.cpk" external="map1R.bin" />\n',
	    '\t\t<file resize="false" offset="0x07593CA0" disc="rootR.cpk" external="rootR.bin" />\n',
        '\t</patch>\n',
        
        '</ps3disc>'
        
        ]
        
        xmlFile.write("".join(["%s" % (k) for k in XMLString]))

        xmlFile.close()


        if os.name == 'posix':
        
            try:
                args = ['mono', 'PatchDolStrings.exe', 'Resources/elfpatchconfig.xml']
                proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            
                data = proc.stdout.read()
                print data

                reply = QtGui.QMessageBox.information(self, "Complete", "Embedded Strings Patch Complete.")
                
            except:
                reply = QtGui.QMessageBox.information(self, "Error", "There was an error during patching. You must have mono installed to patch, and have the PatchDolStrings.exe and it's two .dlls in the GraceNote folder.")
                return        
        
        
        else:
        
            try:
                args = ['PatchDolStrings.exe', 'Resources\elfpatchconfig.xml']
                proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            
                data = proc.stdout.read()
                print data
                
                reply = QtGui.QMessageBox.information(self, "Complete", "Embedded Strings Patch Complete.")

            except:
                reply = QtGui.QMessageBox.information(self, "Error", "There was an error during patching. I have no idea what went wrong.")
                return        


        progress.setValue(progress.value() + 1)



    def PatchDol(self):
        self.WriteDatabaseStorageToHdd()
        
    
        # Make some output directories
        if not os.path.exists('riivolution'):
            os.makedirs('riivolution')

        GracesPath = os.path.dirname(os.path.abspath(sys.argv[0]))

        if os.name == 'posix':
        
            try:
                args = ['mono', 'PatchDolStrings.exe', 'Resources/dolpatchconfig.xml']
                proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            
                data = proc.stdout.read()
                print data

                reply = QtGui.QMessageBox.information(self, "Complete", "Embedded Strings Patch Complete.")
                
            except:
                reply = QtGui.QMessageBox.information(self, "Error", "There was an error during patching. You must have mono installed to patch, and have the PatchDolStrings.exe and it's two .dlls in the GraceNote folder.")
                return        
        
        
        else:
        
            try:
                args = ['PatchDolStrings.exe', 'Resources\dolpatchconfig.xml']
                proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            
                data = proc.stdout.read()
                print data
                
                reply = QtGui.QMessageBox.information(self, "Complete", "Embedded Strings Patch Complete.")

            except:
                reply = QtGui.QMessageBox.information(self, "Error", "There was an error during patching. I have no idea what went wrong.")
                return        
        
    
    
#
#        # Make some output directories
#        if not os.path.exists('riivolution'):
#            os.makedirs('riivolution')
#
#
#        if self.settings.contains('MemOne'):
#            MemOne = self.settings.value('MemOne')
#            if not os.path.isfile(MemOne):
#                MemOne = QtGui.QFileDialog.getOpenFileName(self, 'Locate the Tales of Graces v2 MemDump', '', 'Wii Mem One dump (*.bin);;All Files(*)')
#                if MemOne == '': return
#                MemOne = str(MemOne)
#        else:
#            MemOne = QtGui.QFileDialog.getOpenFileName(self, 'Locate the Tales of Graces v2 MemDump', '', 'Wii Mem One Dump (*.bin);;All Files(*)')
#            if MemOne == '': return
#            MemOne = str(MemOne)
#        self.settings.setValue("MemOne", MemOne)
#
#
#
#        file = open(MemOne, 'rb')
#        data = file.read()
#        file.close()
#        
#        lowrange = 0x804CE000 # Start of data section in dol in memory
#        highrange = 0x8072E000 # End of data section in dol in memory
#        
#        print "Reading file {0} looking for pointers between {1} and {2}".format(MemOne, hex(lowrange), hex(highrange))
#        
#        PointedAreas = dict([])
#        
#        loops = len(data) / 4
#
#        for integer in xrange(loops):
#        
#            offset = integer*4
#            pointer = struct.unpack_from('>I', data, offset)[0]
#            
#            if lowrange < pointer and pointer < highrange:
#                if pointer in PointedAreas:
#                    PointedAreas[pointer].append(offset)
#                else:
#                    PointedAreas[pointer] = [offset]
#
#        		
#        print 'Found {0} pointers'.format(len(PointedAreas))
#
#
#
#        dolNames = ['Artes', 'ArteNames', 'Battle', 'Discovery', 'GradeShop-Missions', 'Item', 'MonsterBook', 'Skills', 'System', 'Tactics', 'Titles', 'Tutorial']
#
#
#        file = open('riivolution/DolPatches.xml', 'w')
#
#        XMLString = [
#        '<wiidisc version="1">\n',        
#        '\t<id game="STG" />\n',
#        '\t<options>\n',
#        '\t\t<section name="Embedded Strings">\n',
#        '\t\t\t<option name="Graces Translation" default="1">\n',
#        '\t\t\t\t<choice name="Enabled">\n',
#        '\t\t\t\t\t<patch id="dolstrings" />\n',
#        '\t\t\t\t</choice>\n',
#        '\t\t\t</option>\n',
#        '\t\t</section>\n',
#        '\t</options>\n',
#        
#        '\t<patch id="dolstrings">\n',
#        '\t\t<memory offset="0x802F89C4" value="494f763c" />\n',
#        '\t\t<memory offset="0x802F89E4" value="494f761c" />\n',
#        '\t\t<memory offset="0x817F0000" value="3d20817f380900007f8300404dbc00207c0303784e80002000000000" />\n'
#
#        ]
#        
#        file.write("".join(["%s" % (k) for k in XMLString]))
#
#        targetOffset = 0x817F0100
#
#        for pointer, offsetlist in PointedAreas.iteritems():
#                        
#            # Reset the variables for the loop
#            NextChar = True
#            i = 0
#            stringBuffer = ''
#            string = ''
#            
#            # Parse a C-string of unknown length
#            while NextChar == True:
#                char = data[pointer - 0x80000000 + i]
#                
#                if char == '\x00':
#                    NextChar = False
#                    
#                else:
#                    stringBuffer += char
#                
#                i += 1    
#                    
#                    
#            # Convert string buffer to text I can use
#            string = stringBuffer.decode('cp932', 'ignore')
#            
#            # Check to see if such a Japanese string exists
#            Globals.CursorGracesJapanese.execute(u"select ID from Japanese where string=?", (unicode(string),))
#            results = Globals.CursorGracesJapanese.fetchall()
##            
#            
#            
#            # Check to see if the JP string has an English equivalent
#            
#            maxlen = 4 - (len(stringBuffer) % 4) + len(stringBuffer)
#            
#            if results == []:
#                pass
##                print 'No JP string'
#            else:
#                for entry in results:
#                    for DBName in dolNames:
#                        TmpCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/' + DBName)
#                        TmpCur = TmpCon.cursor()    
#                        
#                        TmpCur.execute(u"select english from Text where StringID=?", (unicode(entry[0]),))
#                        
#                        thing = TmpCur.fetchall()
#                        if thing == [] or thing == [(u'',)] or thing == [(u' ',)]:
#                            continue
#                        else:
#                            thinglen = len(thing[0][0].encode('cp932', 'ignore'))
#                            if thinglen > maxlen:
#
##       The commented code here will be used when Aaron has put aside some memory 
##       for these strings. Just set the beginning of the target memory range at 
##       targetOffset above, and off it goes! It will increment and pad the patches 
##       according, and use a memory search to modify any pointers.
#
#                                blank = thinglen % 8
#                                if blank == 0:
#                                    blank = 8
#                                print 'String is longer than {0} by {1}. Being moved to unallocated memory'.format(maxlen, thinglen-maxlen)
#
#                                for offset in offsetlist:
#                                    
#                                    pA = '\t\t<memory offset="{0}" value="{1}" />\n'.format(hex(offset), hex(targetOffset)[2:])
#                                    file.write(pA)
#
#                                pB = '\t\t<memory offset="{0}" value="{1}" />\n'.format(hex(targetOffset), hexlify(re.sub(u"'+", "'", unicode(thing[0][0])).encode('cp932', 'ignore')) + (blank * '00'))
#                                
#                                file.write(pB)
#                                
#                                targetOffset += 4 - (thinglen % 4) + thinglen
#
#                            else:
#                                blank = maxlen - thinglen
#                                pC = '\t\t<memory offset="{0}" value="{1}" />\n'.format(hex(pointer), hexlify(re.sub(u"'+", "'", unicode(thing[0][0])).encode('cp932', 'ignore')) + (blank * '00'))
#            
#                                file.write(pC)
#                                
#        file.write('\t</patch>\n')
#        file.write('</wiidisc>')
#        file.close()
   

    def SavetoBugfixXML(self):
        self.WriteDatabaseStorageToHdd()
        


        # Make some output directories
        if not os.path.exists('riivolution'):
            os.makedirs('riivolution')

        if not os.path.exists('Graces'):
            os.makedirs('Graces')

        if not os.path.exists('Graces/v2'):
            os.makedirs('Graces/v2')

        if not os.path.exists('Resources/Wii'):
            os.makedirs('Resources/Wii')


        if self.settings.contains('Graceful'):
            Graceful = self.settings.value('Graceful')
            if not os.path.isfile(Graceful):
                Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
                if Graceful == '': return
                Graceful = str(Graceful)
        else:
            Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
            if Graceful == '': return
            Graceful = str(Graceful)
        self.settings.setValue("Graceful", Graceful)

        if self.settings.contains('RootRfix'):
            RootR = self.settings.value('RootRfix')
            if not os.path.isfile(RootR):
                RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if RootR == '': return
                RootR = str(RootR)
        else:
            RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if RootR == '': return
            RootR = str(RootR)
        self.settings.setValue("RootRfix", RootR)

        if self.settings.contains('Map0Rfix'):
            Map0R = self.settings.value('Map0Rfix')
            if not os.path.isfile(Map0R):
                Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if Map0R == '': return
                Map0R = str(Map0R)
        else:
            Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map0R == '': return
            Map0R = str(Map0R)
        self.settings.setValue("Map0Rfix", Map0R)

        if self.settings.contains('Map1Rfix'):
            Map1R = self.settings.value('Map1Rfix')
            if not os.path.isfile(Map1R):
                Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
                if Map1R == '': return
                Map1R = str(Map1R)
        else:
            Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map1R == '': return
            Map1R = str(Map1R)
        self.settings.setValue("Map1Rfix", Map1R)

        
        #Delety function!
        TestPath = [os.path.dirname(str(RootR)), os.path.dirname(str(Map0R)), os.path.dirname(str(Map1R))]
        
        for Path in TestPath:
            for File in os.listdir(Path):
                if File.rfind('.toc') >= 0:
                    os.remove(Path + "/" + File)
                if File.rfind('.patch') >=0:
                    os.remove(Path + '/' + File)


        # Everyone loves progress bars!
        progress = QtGui.QProgressDialog("Saving databases to SCS...", "Abort", 0, len(os.listdir(Globals.configData.LocalDatabasePath))+1)
        progress.setWindowModality(QtCore.Qt.WindowModal)


        # Create the .scs files
        self.MakeSCS(os.listdir(Globals.configData.LocalDatabasePath), progress, 'Wii')

        progress.setValue(len(os.listdir(Globals.configData.LocalDatabasePath))+1)
 
        

        # Now do Graceful Stuff!
        progress = QtGui.QProgressDialog("Creating Riivolution Patch with Graceful...", "Abort", 0, 120)
        progress.setWindowModality(QtCore.Qt.WindowModal)

        XML = []
        GracesPath = os.path.dirname(os.path.abspath(sys.argv[0])) + os.sep + "Resources" + os.sep + 'Wii' + os.sep
        
        
        
        # RootR Scripts
        args = ["mono", str(Graceful), "4", "2", str(RootR)]

        if os.name != 'posix':
            args = []
            command = [str(Graceful), "4", "2", str(RootR)]

        rootRbin = open('Graces/rootR.bin', 'wb')

        off = 0

        # Chat  
        Archive = Globals.configDataGracesFolders[1][:] # Chat_MS
        Archive.extend(Globals.configDataGracesFolders[2][:]) # Chat_SB
        ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()
            
            
        # SysString        
        Archive = (Globals.configDataGracesFolders[-1]) # SysString.bin
        ArchiveLocation = 'sys' + os.sep + 'ja' + os.sep
        args.extend(["{0}{1}.bin".format(GracesPath, Archive[0]), "{0}{1}.bin".format(ArchiveLocation, Archive[0])])
        tempFile = open("{0}{1}.bin".format(GracesPath, Archive[0]))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()


        # TOG stuff
        Archive = (['TOG_SS_ChatName', 'TOG_SS_StringECommerce']) # Special Cased Sys Subs
        ArchiveLocation = 'SysSub' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.dat".format(GracesPath, file), "{0}{1}.dat".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.dat".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()
                    
        
        # Movies
        Archive = (Globals.configDataGracesFolders[-2]) # Movie Subtitles
        ArchiveLocation = 'movie' + os.sep + 'str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(GracesPath, file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()

        progress.setValue(10)


        # Special Strings
        Archive = (Globals.configDataGracesFolders[-3]) # Special Stuff
        ArchiveLocation = 'str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(str(GracesPath), file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()


        # Images
        Images = [("Resources/TitleTexture.tex", "SysSub/JA/TitleTexture.tex"), 
                  ("Resources/main.tex", "mnu/tex/main.tex"),
                  ("Resources/shop.tex", "mnu/tex/shop.tex"),
                  ("Resources/skill.tex", "mnu/tex/skill.tex"),
#                  ("Resources/snd_test.tex", "mnu/tex/snd_test.tex"),
                  ("Resources/bin000.acf", "btl/acf/bin000.acf"),
                  ("Resources/FontTexture2.tex", "sys/FontTexture2.tex"),
                  ("Resources/FontBinary2.bin", "sys/FontBinary2.bin"),
                  ("Resources/mainRR.sel", "module/mainRR.sel")
                  ]

        for image in Images:
            args.extend([image[0], image[1]])
            tempFile = open(image[0], 'rb')
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()

        # Run the process!
        if os.name == 'posix':
        
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
            data = proc.stdout.read()
            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
            progress.setValue(57)
            rootRbin.close()

        else:
            for i in range(0, len(args), 20):
                if len(args) > i+20:
                    finalArgs = command + args[i:i+20]
                else:
                    finalArgs = command + args[i:]
                
                
                proc=subprocess.Popen(finalArgs,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)

                while proc.poll() == None:
                    pass
                
                data = proc.stdout.read()

                XML.extend(re.findall(u'<.*?>', data, re.DOTALL))

            progress.setValue(57)
            rootRbin.close()


        # Map0R Scripts
        Map0RCPK = ['mapfile_basiR.cpk', 'mapfile_briaR.cpk', 'mapfile_bridR.cpk', 'mapfile_caveR.cpk', 'mapfile_fallR.cpk', 'mapfile_ff12R.cpk', 'mapfile_ff13R.cpk', 'mapfile_ff14R.cpk', 'mapfile_ff15R.cpk', 'mapfile_ff16R.cpk', 'mapfile_ff17R.cpk', 'mapfile_ff19R.cpk', 'mapfile_ff20R.cpk', 'mapfile_foreR.cpk', 'mapfile_gentR.cpk', 'mapfile_icebR.cpk', 'mapfile_ironR.cpk', 'mapfile_koneR.cpk', 'mapfile_kotR.cpk', 'mapfile_lasR.cpk', 'mapfile_montR.cpk', 'mapfile_rockR.cpk', 'mapfile_sandR.cpk', 'mapfile_sf08R.cpk', 'mapfile_sf09R.cpk', 'mapfile_sf10R.cpk', 'mapfile_sf11R.cpk', 'mapfile_sf18R.cpk', 'mapfile_sneeR.cpk', 'mapfile_snowR.cpk', 'mapfile_stdaR.cpk', 'mapfile_varoR.cpk', 'mapfile_wf01R.cpk', 'mapfile_wf02R.cpk', 'mapfile_wf03R.cpk', 'mapfile_wf04R.cpk', 'mapfile_wf05R.cpk', 'mapfile_wf06R.cpk', 'mapfile_wf07R.cpk', 'mapfile_wf21R.cpk', 'mapfile_wincR.cpk', 'mapfile_zoneR.cpk']

        map0Rbin = open('Graces/map0R.bin', 'wb')


        i = 4

        for CPK in Map0RCPK:
            args = ["mono", str(Graceful), "4", "1", str(Map0R), CPK]
            if os.name != 'posix':
                args = [str(Graceful), "4", "1", str(Map0R), CPK]
            
            Archive = Globals.configDataGracesFolders[i]
            i += 1
            ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

            for file in Archive:
                args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

                tempFile = open("{0}{1}.scs".format(GracesPath, file))
                tempData = tempFile.read()
                map0Rbin.write(tempData)
                tempFile.close()


            # Run the process!
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
            data = proc.stdout.read()
            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
            progress.setValue(progress.value() + 1)

        map0Rbin.close()
        

        # Map1R Scripts
        Map1RCPK = ['mapfile_anmaR.cpk', 'mapfile_beraR.cpk', 'mapfile_debugR.cpk', 'mapfile_fendR.cpk', 'mapfile_kameR.cpk', 'mapfile_koya_r06R.cpk', 'mapfile_lakeR.cpk', 'mapfile_lanR.cpk', 'mapfile_nekoR.cpk', 'mapfile_olleR.cpk', 'mapfile_otheR.cpk', 'mapfile_ozweR.cpk', 'mapfile_riotR.cpk', 'mapfile_sablR.cpk', 'mapfile_shatR.cpk', 'mapfile_shipR.cpk', 'mapfile_strtR.cpk', 'mapfile_supaR.cpk', 'mapfile_systemR.cpk', 'mapfile_winR.cpk']


        map1Rbin = open('Graces/map1R.bin', 'wb')

        i = 46

        for CPK in Map1RCPK:
            args = ["mono", str(Graceful), "4", "1", str(Map1R), CPK]
            if os.name != 'posix':
                args = [str(Graceful), "4", "1", str(Map1R), CPK]
            
            Archive = Globals.configDataGracesFolders[i]
            i += 1
            ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

            for file in Archive:
                args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

                tempFile = open("{0}{1}.scs".format(GracesPath, file))
                tempData = tempFile.read()
                map1Rbin.write(tempData)
                tempFile.close()


            # Run the process!
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
            data = proc.stdout.read()
            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
            progress.setValue(progress.value() + 1)

        map1Rbin.close()


        # Let's make an XML! And also move all those .toc files over

        for Path in TestPath:
            for File in os.listdir(Path):
                if File.rfind('.toc') >= 0:
                    try:
                        os.remove("Graces/v2/" + File)
                    except:
                        pass
                    shutil.move(Path + "/" + File, "Graces/v2")
                if File.rfind('.patch') >=0:
                    try:
                        os.remove("Graces/v2/" + File)
                    except:
                        pass
                    shutil.move(Path + "/" + File, "Graces/v2")
                    
        #shutil.rmtree('Resources/Wii')
        

        XMLset = set(XML)
        XMLFinal = []
        for entry in XMLset:
            XMLFinal.append(entry)
        
        XMLFinal.sort()    
                
        
        xmlFile = open("riivolution/GracesBugfix.xml", "w")
        
        
        
        patchFile = open("Graces/v2/rootR.cpk.patch", "r")
        rootRPatch = patchFile.readline()
        patchFile.close()

        patchFile = open("Graces/v2/map0R.cpk.patch", "r")
        map0RPatch = patchFile.readline()
        patchFile.close()

        patchFile = open("Graces/v2/map1R.cpk.patch", "r")
        map1RPatch = patchFile.readline()
        patchFile.close()

                
        XMLString = [
        
        '<wiidisc version="1">\n',        
        '\t<id game="STG" version="2"/>\n',
        '\t<options>\n',
        '\t\t<section name="Testing">\n',
        
        '\t\t\t<option name="Graces Translation" default="1">\n',
        '\t\t\t\t<choice name="Enabled">\n',
        '\t\t\t\t\t<patch id="graces" />\n',
        '\t\t\t\t\t<patch id="gracesfiles" />\n',
        '\t\t\t\t</choice>\n',
        '\t\t\t</option>\n',

        '\t\t\t<option name="Region Patch" default="1">\n',
        '\t\t\t\t<choice name="Enabled">\n',
        '\t\t\t\t\t<patch id="localeZero" />\n',
        '\t\t\t\t</choice>\n',
        '\t\t\t</option>\n',
        
        '\t\t\t<option name="Debug Output">\n',
        '\t\t\t\t<choice name="For Original (v0)">\n',
        '\t\t\t\t\t<patch id="kamek_Ori" />\n',
        '\t\t\t\t</choice>\n',
        '\t\t\t</option>\n',
        
        '\t\t</section>\n',
        '\t</options>\n',
        
        '\t<patch id="localeZero">\n',
        '\t\t<memory offset="0x803595DC" value="38600000" />\n',
        '\t</patch>\n',

        '\t<patch id="graces" root="/Graces/v2">\n',
        '\t\t<file disc="/rootR.cpk" external="rootR.cpk.patch" offset="{0}" resize="true" />\n'.format(rootRPatch),
        '\t\t<file disc="/map0R.cpk" external="map0R.cpk.patch" offset="{0}" resize="true" />\n'.format(map0RPatch),
        '\t\t<file disc="/map1R.cpk" external="map1R.cpk.patch" offset="{0}" resize="true" />\n'.format(map1RPatch),
        "".join(["\t\t%s\n" % (k) for k in XMLFinal[:63]]), #[:63]
        '\t</patch>\n',

        '\t<patch id="gracesfiles" root="/Graces">\n',
        '\t\t<file resize="false" offset="0x70000000" disc="map0R.cpk" external="map0R.bin" />\n',
	    '\t\t<file resize="false" offset="0x70000000" disc="map1R.cpk" external="map1R.bin" />\n',
	    '\t\t<file resize="false" offset="0x70000000" disc="rootR.cpk" external="rootR.bin" />\n',
        '\t</patch>\n',
        
        '\t<patch id="kamek_New">\n',
        '\t\t<memory offset="0x80035C10" value="4bfcbc2c" />\n',
        '\t\t<memory offset="0x80001800" value="9421fff07c0802a693e1000c7c7f1b783c60800090010014386318f04cc63182480343f1800100147fe3fb7883e1000c7c0803a6382100104e8000207c0802a69421ef8093e1107c900110849081101c90a1102090c1102490e110289101102c912110309141103440860024d8211038d8411040d8611048d8811050d8a11058d8c11060d8e11068d9011070380000013be10014980100083800000098010009380110887c641b7838a100089001000c7fe3fb7838011018900100104832e8457fe3fb78483258f9388000017c651b7838c000007fe3fb784832b5418001108483e1107c382110807c0803a64e8000206c6f6c0a00" />\n',
        '\t</patch>\n',
        
        '</wiidisc>'
        
        ]
        
        xmlFile.write("".join(["%s" % (k) for k in XMLString]))
        progress.setValue(progress.value() + 1)

        xmlFile.close()

def TrueCount():
    i = 1
    aList = Globals.configData.FileList[0]

    for item in aList:
        typeset = set([])
    
        for name in aList[i]:
            tempCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/' + name)
            tempCur = tempCon.cursor()
            
            tempCur.execute("SELECT StringID from Text")
            for thing in tempCur.fetchall():
                Globals.CursorGracesJapanese.execute("SELECT COUNT(ID) from Japanese where debug == 0 and ID == ?", (thing[0],))
                if Globals.CursorGracesJapanese.fetchall()[0][0] > 0:
                    typeset.add(thing[0])
                    
        print '{0}: {1} entries'.format(item, len(typeset))
        i += 1
