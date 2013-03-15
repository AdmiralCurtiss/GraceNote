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
from PyQt4 import QtCore, QtGui
import sqlite3
import os, sys, re, time, struct, platform
import shutil
import ftplib
#from ftplib import FTP
from binascii import hexlify, unhexlify
import subprocess
import codecs
from Config import *
from collections import deque
import filecmp

from MainWindow import *
from XTextBox import *
from CustomHighlighter import *
from MassReplace import *
from GlobalChangelog import *
from LocalChangelog import *
from Statistics import *
from DuplicateText import *
import CompletionTable
from ImageViewerWindow import *


def SetupEnvironment():
    Globals.commentsAvailableLabel = False

    # load config
    try:
        Globals.configfile = sys.argv[1]
        print 'Loading configuration: ' + Globals.configfile
        Globals.configData = Configuration(Globals.configfile)
    except:
        print 'Failed, fallback to default config.xml'
        Globals.configfile = 'config.xml'
        Globals.configData = Configuration(Globals.configfile)

    # load graces folder config if it's available
    try:
        Globals.configDataGracesFolders = Configuration('config_graces_byfolder.xml').FileList
    except:
        Globals.configDataGracesFolders = [['none'], ['none']]

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
    return

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
        if Globals.EnglishVoiceLanguageFlag:
            self.voiceLangAct.setText('Japanese Voices')
            Globals.EnglishVoiceLanguageFlag = False
            self.settings.setValue('voicelanguage', 'JP')
        else:
            self.voiceLangAct.setText('English Voices')
            Globals.EnglishVoiceLanguageFlag = True
            self.settings.setValue('voicelanguage', 'EN')
        
    def UpdateLowerStatusSwap(self):
        if Globals.UpdateLowerStatusFlag:
            self.updateLowerStatusAct.setText('Not updating lower status')
            Globals.UpdateLowerStatusFlag = False
            self.settings.setValue('updatelowerstatus', 'False')
        else:
            self.updateLowerStatusAct.setText('Updating lower status')
            Globals.UpdateLowerStatusFlag = True
            self.settings.setValue('updatelowerstatus', 'True')
            
    def DisplayFooterSwap(self):
        if Globals.FooterVisibleFlag:
            self.displayFooterAct.setText('Footer disabled')
            Globals.FooterVisibleFlag = False
            self.settings.setValue('footervisible', 'False')
        else:
            self.displayFooterAct.setText('Footer enabled')
            Globals.FooterVisibleFlag = True
            self.settings.setValue('footervisible', 'True')

    def ChangeWriteDatabaseStorageToHddBehavior(self):
        if Globals.WriteDatabaseStorageToHddOnEntryChange:
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
        if bool:
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

        if self.treemodel.hasChildren(index):
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
            if ContainsIDString:
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
    
            if (TempDebug == 1) and (not self.debug.isChecked()):
                pass
            elif (TempDebug == 1) and (self.debug.isChecked()):
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
            
        if containsComments:
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
            if entry[3] == 0 or self.debug.isChecked():
                string = string + 'Entry {0}\n'.format(i)
                if replaceVariables:
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
                    if self.debug.isChecked():
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


    def JumpToEntry(self, databaseName, entry):
        self.WriteDatabaseStorageToHdd()
        
        if databaseName == '':
            databaseName = self.currentlyOpenDatabase
        self.tree.collapseAll()
        for i in xrange(self.treemodel.rowCount()):
            category = self.treemodel.item(i)

            for p in xrange(category.rowCount()):
            
                if category.child(p).statusTip() == databaseName:
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
        if bool:
            self.debug.setIcon(QtGui.QIcon('icons/debugon.png'))
        else:
            self.debug.setIcon(QtGui.QIcon('icons/debugoff.png'))
        
    
    
    def ShowChangelog(self):
        item = self.treemodel.itemFromIndex(self.tree.currentIndex())
        if item == None or item.statusTip() == '':
            return
        self.LogDialog = LocalChangelog(item.statusTip())

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
        
        if not self.massDialogOpened:
            self.massDialog = MassReplace(self)
            self.massDialogOpened = True
        self.massDialog.show()
        self.massDialog.raise_()
        self.massDialog.activateWindow()


    def ShowCompletionTable(self):
        self.WriteDatabaseStorageToHdd()
        
        self.comDialog = CompletionTable.CompletionTable(self)

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
        
        if not self.duplicateTextDialogOpened:
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
        if DebugState:
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
        if not DebugState:
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
        
        
        if CommandOriginButton:
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
                if not Globals.UpdateLowerStatusFlag:
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
        if Globals.WriteDatabaseStorageToHddOnEntryChange:
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
        if Globals.Audio:
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
            if self.twoupAct.isChecked():
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