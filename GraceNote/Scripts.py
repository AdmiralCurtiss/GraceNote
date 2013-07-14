# -*- coding: utf-8 -*-

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
import os, sys, re, time, platform
from binascii import hexlify, unhexlify
import subprocess
import codecs
from Config import *
from collections import deque

from MainWindow import *
from XTextBox import *
from CustomHighlighter import *
from MassReplace import *
from GlobalChangelog import *
from LocalChangelog import *
from Statistics import *
from DuplicateText import *
import CompletionTable
import ImageViewerWindow
import FontDisplayWindow
import GracesCreation
import NetworkHandler
import DatabaseHandler
import HistoryWindow
import DatabaseCache
import OptionsWindow

def SetupEnvironment():
    Globals.commentsAvailableLabel = False

    try:
        from PyQt4.phonon import Phonon
        Globals.Audio = True
    except ImportError:
        print "Your Qt installation does not have Phonon support.\nPhonon is required to play audio clips."
        Globals.Audio = False

    # load config
    try:
        if len(sys.argv) > 1:
            Globals.configfile = sys.argv[1]
        else:
            Globals.configfile = 'config.xml'
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

    Globals.Cache = DatabaseCache.DatabaseCache()

    return

class SearchAction(QtGui.QAction):
 
    jumpTo = QtCore.pyqtSignal(unicode, int)
 
    def __init__(self, *args):
        QtGui.QAction.__init__(self, *args)
 
        self.triggered.connect(lambda x: self.jumpTo.emit(self.data()[0], self.data()[1]))

class Scripts2(QtGui.QWidget):

    def __init__(self, parent=None):
        super(Scripts2, self).__init__(parent)
        
        self.parent = parent

        self.splashScreen = SplashScreen()

        self.splashScreen.show()
        self.splashScreen.raise_()
        self.splashScreen.activateWindow()

        self.LogDialog = None
        self.gLogDialog = None
        self.statDialog = None
        self.massDialog = None
        self.comDialog = None
        self.dupeDialog = None
        self.optionsWindow = None


        # Current Variables
        self.state = 'ENG'
        self.text = []

        # True Entries Translated Count
#        TrueCount()
             
        # Settings
        Globals.Settings = QtCore.QSettings("GraceNote", Globals.configData.ID)
        if not Globals.Settings.contains('author'):
            text, ok = QtGui.QInputDialog.getText(self, "Enter your Name", "Author name:", QtGui.QLineEdit.Normal)
            if ok and text != '':
                Globals.Settings.setValue('author', text)

        Globals.Author = Globals.Settings.value('author')
        self.update = Globals.Settings.value('update')
        self.databaseWriteStorage = deque()
        self.currentTreeIndex = None
        self.currentOpenedEntryIndexes = None
       
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

        if Globals.Settings.contains('role'):
            self.role = int(Globals.Settings.value('role'))
        else:
            self.role = 1

        if Globals.Settings.contains('autoThreshold'):
            self.autoThreshold = int(Globals.Settings.value('autoThreshold'))
        else:
            self.autoThreshold = 0

        if Globals.Settings.contains('mode'):
            Globals.ModeFlag = Globals.Settings.value('mode')
        else:
            Globals.Settings.setValue('mode', 'Semi-Auto')
            Globals.ModeFlag = 'Semi-Auto'
        
        if Globals.Settings.contains('voicelanguage'):
            Globals.EnglishVoiceLanguageFlag = Globals.Settings.value('voicelanguage') == 'EN'
        else:
            Globals.Settings.setValue('voicelanguage', 'JP')
            Globals.EnglishVoiceLanguageFlag = False
        
        if Globals.Settings.contains('updatelowerstatus'):
            Globals.UpdateLowerStatusFlag = Globals.Settings.value('updatelowerstatus') == 'True'
        else:
            Globals.Settings.setValue('updatelowerstatus', 'False')
            Globals.UpdateLowerStatusFlag = False
        
        if Globals.Settings.contains('writeonentrychange'):
            Globals.WriteDatabaseStorageToHddOnEntryChange = Globals.Settings.value('writeonentrychange') == 'True'
        else:
            Globals.Settings.setValue('writeonentrychange', 'False')
            Globals.WriteDatabaseStorageToHddOnEntryChange = False
        
        if Globals.Settings.contains('footervisible'):
            Globals.FooterVisibleFlag = Globals.Settings.value('footervisible') == 'True'
        else:
            Globals.Settings.setValue('footervisible', 'False')
            Globals.FooterVisibleFlag = False
        
        if Globals.Settings.contains('editpane_amount'):
            Globals.AmountEditingWindows = int(Globals.Settings.value('editpane_amount'))
        else:
            Globals.Settings.setValue('editpane_amount', '5')
            Globals.AmountEditingWindows = 5
        if Globals.AmountEditingWindows < 3 or Globals.AmountEditingWindows > 25:
            Globals.AmountEditingWindows = 5

        if Globals.Settings.contains('TwoUpMode'):
            Globals.TwoUpMode = int(Globals.Settings.value('TwoUpMode'))
        else:
            Globals.TwoUpMode = 1

        self.rolenames = ['None', 'Translation', 'Translation Review', 'Contextual Review', 'Editing']
        self.roletext = ['Doing Nothing', 'Translating', 'Reviewing Translations', 'Reviewing Context', 'Editing']

        self.SetWindowTitle()
        #>>> Globals.CursorGracesJapanese.execute('create table Log(ID int primary key, File text, Name text, Timestamp int)')


        self.timeoutTimer = QtCore.QTimer()
        self.timeoutTimer.timeout.connect(self.WriteDatabaseStorageToHdd)


        # Grab the changes
        NetworkHandler.RetrieveModifiedFiles(self, self.splashScreen)

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
        self.tree.setContentsMargins(0, 0, 0, 0)
        
        self.PopulateModel(Globals.configData.FileList)

#        self.treemodel = QtGui.QSortFilterProxyModel()
#        self.treemodel.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)


#        self.treemodel.setSourceModel(self.treemodel)
        self.tree.setModel(self.treemodel)


        # List View of Entries
        self.entryTreeView = QtGui.QTreeView()
        self.entryStandardItemModel = QtGui.QStandardItemModel()
        self.entrySortFilterProxyModel = QtGui.QSortFilterProxyModel()
        self.entrySortFilterProxyModel.setSourceModel(self.entryStandardItemModel)
        self.entryTreeView.setModel(self.entrySortFilterProxyModel)
        self.entryTreeView.setRootIsDecorated(False)

        self.termInEntryIcon = QtGui.QPixmap( 'icons/pictogram-din-m000-general.png' )
        self.termInEntryIcon = self.termInEntryIcon.scaled(13, 13, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation);

        # Text Edits
        self.regularEditingTextBoxes = []
        self.twoupEditingTextBoxes = []
        self.threeupEditingTextBoxes = []
        self.textEditingBoxes = []
        self.textEditingTitles = []
        self.textEditingTermIcons = []
        self.textEditingFooters = []
        self.twoupEditingFooters = []
        for i in range(Globals.AmountEditingWindows):
            # create text boxes, set defaults
            tb1 = XTextBox(None, self)
            tb2 = XTextBox('jp', self)
            tb2.hide()
            tb2.setReadOnly(True)
            tb3 = XTextBox('jp', self)
            tb3.hide()
            tb3.setReadOnly(True)
            tb3.flagToggle()
            if Globals.Settings.contains('font'):
                size = int(Globals.Settings.value('font'))
                tb1.setFontPointSize(size)
                tb2.setFontPointSize(size)
                tb3.setFontPointSize(size)
            self.regularEditingTextBoxes.append(tb1)
            self.twoupEditingTextBoxes.append(tb2)
            self.threeupEditingTextBoxes.append(tb3)
            
            footer = QtGui.QLabel('')
            footer.setContentsMargins(0, 0, 0, 0)
            self.textEditingFooters.append(footer)
            tb1.setFooter(footer)
            footer2 = QtGui.QLabel('')
            footer2.setContentsMargins(0, 0, 0, 0)
            self.twoupEditingFooters.append(footer2)
            tb2.setFooter(footer2)
            
            # create layout
            tmplayout = QtGui.QGridLayout()
            title = QtGui.QLabel('')
            termicon = QtGui.QLabel('')

            htitlelayout = QtGui.QHBoxLayout()
            htitlelayout.addWidget(termicon)
            htitlelayout.addWidget(title)
            htitlelayout.setContentsMargins(0, 0, 0, 0)
            titlelayoutwgt = QtGui.QWidget()
            titlelayoutwgt.setLayout(htitlelayout)

            tmplayout.addWidget(titlelayoutwgt, 1, 1, 1, 3)
            tmplayout.addWidget(tb1, 2, 1, 1, 1)
            tmplayout.addWidget(tb2, 2, 2, 1, 1)
            tmplayout.addWidget(tb3, 2, 3, 1, 1)
            if Globals.FooterVisibleFlag:
                tmplayout.addWidget(footer , 3, 1, 1, 3)
                tmplayout.addWidget(footer2, 4, 1, 1, 3)
            tmplayout.setContentsMargins(0, 0, 0, 0)

            tmpqgrpbox = QtGui.QWidget()
            tmpqgrpbox.setLayout(tmplayout)

            termicon.setPixmap(self.termInEntryIcon)
            termicon.hide()
            termicon.setFixedSize(13, 13)
            
            self.textEditingBoxes.append(tmpqgrpbox)
            self.textEditingTitles.append(title)
            self.textEditingTermIcons.append(termicon)
            
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
        self.entryTreeView.selectionModel().selectionChanged.connect(self.PopulateTextEdit)
        self.entryTreeView.clicked.connect(self.UpdateDebug)
        self.entryTreeView.header().setClickable(True)
        self.entryTreeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.entryTreeView.header().customContextMenuRequested.connect(self.SpawnEntryListColumnHideMenu)
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

        self.conDebugAct = QtGui.QAction('Propagate Debug (GracesJapanese -> Databases)', None)
        self.conDebugAct.triggered.connect(self.ConsolidateDebug)
        self.reverseConDebugAct = QtGui.QAction('Propagate Debug (Databases -> GracesJapanese)', None)
        self.reverseConDebugAct.triggered.connect(self.ReverseConsolidateDebug)

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
        self.saveAct.triggered.connect(self.CallSavetoServer)
        self.saveAct.setShortcut(QtGui.QKeySequence('Ctrl+S'))

        self.revertAct = QtGui.QAction(QtGui.QIcon('icons/save.png'), 'Revert', None)
        self.revertAct.triggered.connect(self.CallRevertFromServer)
        
        self.updateAct = QtGui.QAction(QtGui.QIcon('icons/save.png'), 'Update', None)
        self.updateAct.triggered.connect(self.CallRetrieveModifiedFiles)
        self.updateAct.setShortcut(QtGui.QKeySequence('Ctrl+U'))

        self.refreshCompleteAct = QtGui.QAction('Refresh Completion Database', None)
        self.refreshCompleteAct.triggered.connect(self.RefreshCompletion)

        self.findUsedSymbolsAct = QtGui.QAction('Find Used Symbols', None)
        self.findUsedSymbolsAct.triggered.connect(self.FindAllUsedSymbols)
        
        self.recalcFilesToBeUploadedAct = QtGui.QAction(QtGui.QIcon('icons/refresh.png'), 'Find Unsaved Databases', None)
        self.recalcFilesToBeUploadedAct.triggered.connect(self.RecalculateFilesToBeUploaded)

        self.patchAct = QtGui.QAction(QtGui.QIcon('icons/patch.png'), 'Patch Live', None)
        self.patchAct.triggered.connect(self.CallSavetoPatch)
        self.patchAct.setShortcut(QtGui.QKeySequence('Ctrl+P'))

        self.patchdolAct = QtGui.QAction(QtGui.QIcon('icons/patchdol.png'), 'Patch Embedded Strings', None)
        self.patchdolAct.triggered.connect(self.CallPatchDol)
        self.patchdolAct.setShortcut(QtGui.QKeySequence('Ctrl+Alt+P'))

        self.patchzeroAct = QtGui.QAction(QtGui.QIcon('icons/patchv0.png'), 'Patch XML', None)
        self.patchzeroAct.triggered.connect(self.CallSavetoXML)
        self.patchzeroAct.setShortcut(QtGui.QKeySequence('Ctrl+Shift+P'))

        self.patchtwoAct = QtGui.QAction(QtGui.QIcon('icons/patchv2.png'), 'Patch Bugfix XML', None)
        self.patchtwoAct.triggered.connect(self.CallSavetoBugfixXML)
        self.patchtwoAct.setShortcut(QtGui.QKeySequence('Ctrl+Shift+Alt+P'))

        self.patchfDemoAct = QtGui.QAction(QtGui.QIcon('icons/patchv0.png'), 'Patch Graces f Demo XML', None)
        self.patchfDemoAct.triggered.connect(self.CallSavetoGracesfDemoXML)
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
        self.twoupAct.triggered.connect(self.toggleTwoUpMode)
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

        self.DisabledMenuOptionSetRole = QtGui.QAction('Role', None)
        self.DisabledMenuOptionSetRole.setEnabled(False)
        self.DisabledMenuOptionSetThreshold = QtGui.QAction('Auto Mode Threshold', None)
        self.DisabledMenuOptionSetThreshold.setEnabled(False)

        self.autoThreshold0Act = QtGui.QAction(QtGui.QIcon('icons/tloff.png'), 'None', None)
        self.autoThreshold1Act = QtGui.QAction(QtGui.QIcon('icons/tlon.png'), 'Translation', None)
        self.autoThreshold2Act = QtGui.QAction(QtGui.QIcon('icons/oneon.png'), 'Translation Review', None)
        self.autoThreshold3Act = QtGui.QAction(QtGui.QIcon('icons/twoon.png'), 'Contextual Review', None)


        self.openOptionsWindowAct = QtGui.QAction('Preferences...', None)
        self.openOptionsWindowAct.triggered.connect(self.OpenOptionsWindow)

        self.reloadConfigAct = QtGui.QAction('Reload Config', None)
        self.reloadConfigAct.triggered.connect(self.ReloadConfiguration)
        self.reloadConfigAct.setShortcut(QtGui.QKeySequence('Ctrl-Shift-Alt-R'))
        
        
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

        self.reopenFontWinAct = QtGui.QAction('Reopen Font Window', None)
        self.reopenFontWinAct.triggered.connect(self.openFontWindow)

        self.reopenHistoryWinAct = QtGui.QAction('Reopen History Window', None)
        self.reopenHistoryWinAct.triggered.connect(self.openHistoryWindow)

        roleMenu = QtGui.QMenu('Role', self)

        roleMenu.addAction(self.DisabledMenuOptionSetRole)
        roleMenu.addAction(self.tmode)
        roleMenu.addAction(self.tlcheckmode)
        roleMenu.addAction(self.rewritemode)
        roleMenu.addAction(self.grammarmode)
        roleMenu.addSeparator()
        roleMenu.addAction(self.DisabledMenuOptionSetThreshold)
        roleMenu.addAction(self.autoThreshold0Act)
        roleMenu.addAction(self.autoThreshold1Act)
        roleMenu.addAction(self.autoThreshold2Act)
        roleMenu.addAction(self.autoThreshold3Act)

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
        
        
        if Globals.Settings.contains('toolicon'):
            self.Toolbar.setIconSize(QtCore.QSize(Globals.Settings.value('toolicon'), Globals.Settings.value('toolicon')))
        if Globals.Settings.contains('toolstyle'):
            self.Toolbar.setToolButtonStyle(Globals.Settings.value('toolstyle'))
        
        parent.menuBar().clear()
        
        parent.editMenu.addSeparator()
        parent.editMenu.addAction(self.fullcopyAct)
        parent.editMenu.addAction(self.saveAsPngAndOpenAct)
        parent.editMenu.addAction(self.saveAsPngAct)
        parent.editMenu.addAction(self.saveAsMultiplePngAct)
        
        fileMenu = QtGui.QMenu("File", self)
        
        fileMenu.addAction(self.saveAct)
        fileMenu.addAction(self.updateAct)
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
        viewMenu.addAction(self.reopenFontWinAct)
        viewMenu.addAction(self.reopenMediaWinAct)
        viewMenu.addAction(self.reopenHistoryWinAct)
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
        toolsMenu.addSeparator()
        toolsMenu.addAction(self.conDebugAct)
        toolsMenu.addAction(self.reverseConDebugAct)
        toolsMenu.addAction(self.refreshCompleteAct)
        toolsMenu.addAction(self.findUsedSymbolsAct)
        
        
        modeMenu = QtGui.QMenu("Mode", self)
        
        modeMenu.addAction(self.autoAct)
        modeMenu.addAction(self.semiAct)
        modeMenu.addAction(self.manuAct)
        modeMenu.triggered.connect(self.setMode)
        

        optionsMenu = QtGui.QMenu("Options", self)
        #optionsMenu.addAction(self.reloadConfigAct)
        #optionsMenu.addSeparator()
        optionsMenu.addAction(self.openOptionsWindowAct)

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
        layout.addWidget(self.entryTreeView)
        #layout.setColumnStretch(1,1)
        
        layout.setSizes( [200, 400, 200] )
        
        layoutWidgetAdapter = QtGui.QVBoxLayout()
        layoutWidgetAdapter.addWidget(layout)
        self.setLayout(layoutWidgetAdapter)

        self.massDialogOpened = False
        self.globalChangelogOpened = False
        self.statsDialogOpened = False
        self.duplicateTextDialogOpened = False
        
        geom = Globals.Settings.value('Geometry/Scripts2')
        if geom is not None:
            self.restoreGeometry(geom)
        self.SetTwoUpMode(Globals.TwoUpMode)

        self.openMediumWindows()
        self.openFontWindow()
        self.openHistoryWindow()
        
    def openMediumWindows(self):
        self.media = {}
        self.openImageWindows()
            
    def openImageWindows(self):
        for img in Globals.configData.Images:
            self.openImageWindow(img)
    
    def openImageWindow(self, img):
        self.media[img.name] = ImageViewerWindow.ImageViewerWindow(self, img)
        self.media[img.name].show()
        self.media[img.name].raise_()
        self.media[img.name].activateWindow()

    def openFontWindow(self):
        self.fontWindow = FontDisplayWindow.FontDisplayWindow(self)
        self.fontWindow.show()
        self.fontWindow.raise_()
        self.fontWindow.activateWindow()

    def openHistoryWindow(self):
        self.historyWindow = HistoryWindow.HistoryWindow(self)
        self.historyWindow.show()
        self.historyWindow.raise_()
        self.historyWindow.activateWindow()

    def cleanupAndQuit(self):
        self.WriteDatabaseStorageToHdd()

        for key, win in self.media.iteritems():
            win.close()
        self.fontWindow.close()
        self.historyWindow.close()
        if self.LogDialog:
            self.LogDialog.close()
        if self.gLogDialog:
            self.gLogDialog.close()
        if self.statDialog:
            self.statDialog.close()
        if self.massDialog:
            self.massDialog.close()
        if self.optionsWindow:
            self.optionsWindow.close()
        if self.comDialog:
            self.comDialog.close()
        if self.dupeDialog:
            self.dupeDialog.close()

        Globals.Settings.setValue('update', set(self.update))
        print str(len(self.update)) + ' files retained for next session: ', ''.join(["%s, " % (k) for k in self.update])[:-2]

        Globals.Settings.setValue('Geometry/Scripts2', self.saveGeometry())

        Globals.Settings.sync()
        self.close()
        quit()
        

    def scrollUp(self, action):
        try:
            index = self.entryTreeView.currentIndex()
            row = index.row()
    
            sortIndex = index.sibling(row-1, 0)

            if index == None or row == -1 or row == 0:
                sortIndex = self.entrySortFilterProxyModel.index(self.entrySortFilterProxyModel.rowCount()-1,0)                
    
            self.entryTreeView.setCurrentIndex(sortIndex)
            self.entryTreeView.selectionModel().select(sortIndex, QtGui.QItemSelectionModel.SelectionFlags(3))
    
            return
        except:
            print 'scroll up failed'


    def scrollDown(self, action):
        try:
            index = self.entryTreeView.currentIndex()
            row = index.row()
    
            if index == None or row == -1 or row == 0:
                index = self.entrySortFilterProxyModel.index(0,0)
                
            sortIndex = index.sibling(row+1, 0)
    
            self.entryTreeView.setCurrentIndex(sortIndex)
            self.entryTreeView.selectionModel().select(sortIndex, QtGui.QItemSelectionModel.SelectionFlags(3))
    
            return
        except:
            print 'scroll down failed'



    def fontChange(self, action):
        size = int(action.iconText())

        for box in self.regularEditingTextBoxes:
            box.setFontPointSize(size)
        for box in self.twoupEditingTextBoxes:
            box.setFontPointSize(size)
        for box in self.threeupEditingTextBoxes:
            box.setFontPointSize(size)

        self.PopulateTextEdit()
        Globals.Settings.setValue('font', size)


    def setRole(self, action):
        if action == self.tmode:
            self.role = 1
        if action == self.tlcheckmode:
            self.role = 2
        if action == self.rewritemode:
            self.role = 3
        if action == self.grammarmode:
            self.role = 4

        if action == self.autoThreshold0Act:
            self.autoThreshold = 0
        if action == self.autoThreshold1Act:
            self.autoThreshold = 1
        if action == self.autoThreshold2Act:
            self.autoThreshold = 2
        if action == self.autoThreshold3Act:
            self.autoThreshold = 3

        try:
            Globals.Settings.setValue('role', int(self.role))
        except:
            Globals.Settings.setValue('role', 1)

        try:
            Globals.Settings.setValue('autoThreshold', int(self.autoThreshold))
        except:
            Globals.Settings.setValue('autoThreshold', 0)
        
        self.SetWindowTitle()
        self.PopulateEntryList()

    def SetWindowTitle(self):
        if Globals.ModeFlag == 'Auto':
            t = "Grace Note - {0} in {1} mode (Threshold: {2})".format(self.roletext[self.role], Globals.ModeFlag, self.rolenames[self.autoThreshold])
        else:
            t = "Grace Note - {0} in {1} mode".format(self.roletext[self.role], Globals.ModeFlag)
        self.parent.setWindowTitle(t)

    def setMode(self, action):
        if action == self.autoAct:
            mode = 'Auto'
        if action == self.semiAct:
            mode = 'Semi-Auto'
        if action == self.manuAct:
            mode = 'Manual'
            
        Globals.Settings.setValue('mode', mode)
        Globals.ModeFlag = mode

        self.SetWindowTitle()


    def ReloadConfiguration(self):
        self.WriteDatabaseStorageToHdd()
        
        Globals.configData = Configuration(Globals.configfile)
        Globals.configData.DelayedLoad()
        self.PopulateModel(Globals.configData.FileList)
        
       
    def setToolbariconsize(self, action):
        i = 0
        for size in self.iconSizes:
            if action == self.iconSizeActs[i]:
                self.Toolbar.setIconSize(QtCore.QSize(size, size))
                Globals.Settings.setValue('toolicon', size)
                if self.Toolbar.toolButtonStyle() == 1:
                    self.Toolbar.setToolButtonStyle(3)
            i += 1
            
            
    def setToolbartext(self, action):

        if action == self.noIconAct:
            self.Toolbar.setToolButtonStyle(1)
            Globals.Settings.setValue('toolstyle', 1)

        if action == self.noTextAct:
            self.Toolbar.setToolButtonStyle(0)
            Globals.Settings.setValue('toolstyle', 0)
        
        if action == self.textDownAct:
            self.Toolbar.setToolButtonStyle(3)
            Globals.Settings.setValue('toolstyle', 3)
        
        if action == self.textLeftAct:
            self.Toolbar.setToolButtonStyle(2)
            Globals.Settings.setValue('toolstyle', 2)
        
    def toggleTwoUpMode(self):
        mode = Globals.TwoUpMode + 1
        if mode > 3:
            mode = 1
        self.SetTwoUpMode(mode)

    def SetTwoUpMode(self, mode):
        Globals.TwoUpMode = mode

        if mode == 1:
            self.twoupAct.setIcon(QtGui.QIcon('icons/twoup.png'))
            self.twoupAct.setText('Two up')
            for box in self.twoupEditingTextBoxes:
                box.hide()
            for box in self.threeupEditingTextBoxes:
                box.hide()
        
        elif mode == 2:
            self.twoupAct.setIcon(QtGui.QIcon('icons/threeup.png'))
            self.twoupAct.setText('Three up')
            for box in self.twoupEditingTextBoxes:
                box.show()
            for box in self.threeupEditingTextBoxes:
                box.hide()
            self.PopulateTextEdit()

        elif mode == 3:
            self.twoupAct.setIcon(QtGui.QIcon('icons/oneup.png'))
            self.twoupAct.setText('One up')
            for box in self.twoupEditingTextBoxes:
                box.show()
            for box in self.threeupEditingTextBoxes:
                box.show()
            self.PopulateTextEdit()

        Globals.Settings.setValue('TwoUpMode', str(mode))

        return

    def ConsolidateDebug(self):
        self.WriteDatabaseStorageToHdd()
        
        # Applies the debug status in GracesJapanese to all databases
            
        i = 1
        aList = Globals.configData.FileList
            
        for item in aList[0]:
            print item
            for filename in aList[i]:

                print "Processing: {0}".format(filename)
            
                UpdateCon = DatabaseHandler.OpenEntryDatabase(filename)
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
            
                UpdateCon = DatabaseHandler.OpenEntryDatabase(filename)
                UpdateCur = UpdateCon.cursor()
                        
                UpdateCur.execute("SELECT StringID FROM Text WHERE status = -1")
                
                for entry in UpdateCur.fetchall():
                    Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 1 WHERE ID=?", (entry[0],))
                UpdateCon.rollback()
                
            i += 1
        Globals.ConnectionGracesJapanese.commit()

    # fills in the database list to the left
    def PopulateModel(self, FileList):
        self.WriteDatabaseStorageToHdd()
        
        self.treemodel.clear()
        
        PercentageConnection = sqlite3.connect(Globals.configData.LocalDatabasePath + "/CompletionPercentage")
        PercentageCursor = PercentageConnection.cursor()
        
        i = 1
        for item in FileList[0]:
            cat = QtGui.QStandardItem(item)
            cat.setEditable(False)
            self.treemodel.appendRow(cat)
            for item in FileList[i]:
                newrow = QtGui.QStandardItem()
                newrow.setStatusTip(item)
                newrow.setEditable(False)
                
                # color based on completion / comments exist
                self.FormatDatabaseListItem(item, newrow, PercentageCursor)

                cat.appendRow(newrow)
            i = i + 1

    def FormatDatabaseListItem(self, databaseName, treeItem, PercentageCursor = None):
        if PercentageCursor is None:
            PercentageConnection = sqlite3.connect(Globals.configData.LocalDatabasePath + "/CompletionPercentage")
            PercentageCursor = PercentageConnection.cursor()

        treeItem.setText(Globals.GetDatabaseDescriptionString(databaseName))
        PercentageCursor.execute("SELECT Count(1) FROM Percentages WHERE Database = ?", [databaseName])
        exists = PercentageCursor.fetchall()[0][0]
        if exists > 0:
            PercentageCursor.execute("SELECT entries, translation, editing1, editing2, editing3, comments FROM Percentages WHERE Database = ?", [databaseName])
            rows = PercentageCursor.fetchall()
            totalDB = rows[0][0]
            translated = rows[0][self.role]
            phase1 = rows[0][1]
            phase2 = rows[0][2]
            phase3 = rows[0][3]
            phase4 = rows[0][4]
            commentAmount = rows[0][5]
                    
            if translated >= totalDB:
                treeItem.setBackground(QtGui.QBrush(QtGui.QColor(160, 255, 160)));
            else:
                treeItem.setBackground(QtGui.QBrush(QtGui.QColor(255, 160, 160)));
                    
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
                treeItem.setText('[' + str(dbPhase) + 'C] ' + treeItem.text())
            else:
                treeItem.setText('[' + str(dbPhase) + '] ' + treeItem.text())
        # color/comments end
                
        return

    def FormatEntryListItemColor(self, item, status):
        if status >= self.role:
            item.setBackground(QtGui.QBrush(QtGui.QColor(160, 255, 160)))
            if Globals.Author == 'ruta':
                item.setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))

        if status == -1:
            item.setBackground(QtGui.QBrush(QtGui.QColor(255, 220, 220)))
            if Globals.Author == 'ruta':
                item.setBackground(QtGui.QBrush(QtGui.QColor(255, 225, 180)))             


    # fills in the entry list to the right        
    def PopulateEntryList(self):
        self.WriteDatabaseStorageToHdd()
        
        containsComments = False
    
        for editbox in self.regularEditingTextBoxes:
            editbox.iconToggle(0)

        self.entryStandardItemModel.clear()
        self.entryStandardItemModel.setColumnCount(6)
        self.entryTreeViewHeaderLabels = ['Status', 'Comment?', 'IdentifyString', 'Text', 'Last updated by', 'Last updated at', 'Debug?']
        self.entryStandardItemModel.setHorizontalHeaderLabels(self.entryTreeViewHeaderLabels)
        self.entryTreeView.header().setStretchLastSection(False) 
        self.entryTreeView.header().setResizeMode(3, QtGui.QHeaderView.Stretch)
        self.entryTreeView.setColumnWidth(0, 10) # status
        self.entryTreeView.setColumnWidth(1, 10) # comment
        self.entryTreeView.setColumnWidth(2, 50) # identifystring
        #self.entryTreeView.setColumnWidth(3, 200) # text
        self.entryTreeView.setColumnWidth(4, 90) # last updated by
        self.entryTreeView.setColumnWidth(5, 110) # last updated at
        self.entryTreeView.setColumnWidth(6, 20) # debug checkbox

        self.currentOpenedEntryIndexes = None
        
        self.text = []

        for editbox in self.regularEditingTextBoxes:
            editbox.setText('')
        for txtttle in self.textEditingTitles:
            txtttle.setText('')
        for footer in self.textEditingFooters:
            footer.setText('')
        for footer in self.twoupEditingFooters:
            footer.setText('')

        # refresh the string & color in the list to the left of the entry we just changed from
        if self.currentTreeIndex is not None:
            treeItem = self.treemodel.itemFromIndex(self.currentTreeIndex)
            self.FormatDatabaseListItem(self.currentlyOpenDatabase, treeItem)

        index = self.tree.currentIndex()
        if index is None:
            return

        itemFromIndex = self.treemodel.itemFromIndex(index)
        if itemFromIndex is None:
            return

        databasefilename = itemFromIndex.statusTip()
        parent = self.treemodel.data(index.parent())
        if self.treemodel.hasChildren(index):
            self.currentTreeIndex = None
            return

        self.currentTreeIndex = index
        self.currentlyOpenDatabase = str(databasefilename)
        SaveCon = DatabaseHandler.OpenEntryDatabase(databasefilename)
        SaveCur = SaveCon.cursor()
        
        SaveCur.execute('SELECT ID, StringID, english, comment, updated, status, IdentifyString, UpdatedBy, UpdatedTimestamp FROM Text')
        TempList = SaveCur.fetchall()

        SaveCur.execute('SELECT ID, english, comment, status, UpdatedBy, UpdatedTimestamp FROM History ORDER BY ID ASC, UpdatedTimestamp DESC')
        HistoryList = SaveCur.fetchall()
        SaveCur.execute('SELECT MAX(ID) FROM Text')
        MaxId = SaveCur.fetchall()[0][0]
        self.historyWindow.setHistoryList(HistoryList, MaxId)

        for i in xrange(len(TempList)):
            Globals.CursorGracesJapanese.execute("SELECT * FROM Japanese WHERE ID={0}".format(TempList[i][1]))
            TempString = Globals.CursorGracesJapanese.fetchall() 
            TempJPN = TempString[0][1]
            TempDebug = TempString[0][2]

            TempENG = TempList[i][2]
            TempCOM = TempList[i][3]
            TempStatus = TempList[i][5]
            TempIdentifyString = str(TempList[i][6])
            TempUpdatedBy = TempList[i][7]
            TempUpdatedTimestamp = TempList[i][8]

            if TempENG == '':
                TempENG = TempJPN
            if TempUpdatedTimestamp is not None:
                TempUpdatedTimestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(TempUpdatedTimestamp))
            else:
                TempUpdatedTimestamp = 'Unknown'
            
            if TempCOM == None:
                TempCOM = 'None'

            commentString = ''
            if TempCOM != '':
                containsComments = True
                commentString = 'C'

            entryDisplayString = Globals.VariableReplace( TempENG.replace('\f', ' ').replace('\n', ' ') )
                        
            additemEntryStatus = QtGui.QStandardItem(str(TempStatus))
            additemEntryStatus.setStatusTip(TempIdentifyString)
            additemEntryStatus.GraceNoteEntryId = i+1
            additemEntryStatus.setEditable(False)
            additemEntryText = QtGui.QStandardItem(entryDisplayString)
            additemEntryText.setEditable(False)
            additemEntryIdentifyString = QtGui.QStandardItem(TempIdentifyString)
            additemEntryIdentifyString.setEditable(False)
            additemEntryComment = QtGui.QStandardItem(commentString)
            additemEntryComment.setEditable(False)
            additemEntryTimestamp = QtGui.QStandardItem(str(TempUpdatedTimestamp))
            additemEntryTimestamp.setEditable(False)
            additemEntryUpdatedBy = QtGui.QStandardItem(str(TempUpdatedBy))
            additemEntryUpdatedBy.setEditable(False)
            additemEntryIsDebug = QtGui.QStandardItem('')
            additemEntryIsDebug.setCheckable(True)
    
            self.FormatEntryListItemColor(additemEntryText, TempStatus)        
    
            if (TempDebug == 1) and (not self.debug.isChecked()):
                pass
            elif (TempDebug == 1) and (self.debug.isChecked()):
                additemEntryIsDebug.setCheckState(QtCore.Qt.Checked)
                additemEntryStatus.setWhatsThis("d") #debug
                self.entryStandardItemModel.appendRow([additemEntryStatus, additemEntryComment, additemEntryIdentifyString, additemEntryText, additemEntryUpdatedBy, additemEntryTimestamp, additemEntryIsDebug])
            else:
                additemEntryStatus.setWhatsThis("n") #not debug
                self.entryStandardItemModel.appendRow([additemEntryStatus, additemEntryComment, additemEntryIdentifyString, additemEntryText, additemEntryUpdatedBy, additemEntryTimestamp, additemEntryIsDebug])
            
            if TempStatus != -1 and TempDebug == 1:
                SaveCur.execute("update Text set status=-1 where ID=?", (TempString[0][0],))
                SaveCon.commit()
                
            self.text.append([TempENG, TempJPN, TempCOM, TempDebug, TempStatus, TempIdentifyString])
            
        if containsComments:
            Globals.commentsAvailableLabel.setText(databasefilename + " | Comments exist!")
        else:
            Globals.commentsAvailableLabel.setText(databasefilename)
            
        if self.entrySortFilterProxyModel.rowCount() != 1:
            index = self.entrySortFilterProxyModel.index(1, 0)
        else:
            index = self.entrySortFilterProxyModel.index(0, 0)
        self.entryTreeView.setCurrentIndex(index)
        self.entryTreeView.selectionModel().select(index, QtGui.QItemSelectionModel.SelectionFlags(3))


    def FormatCurrentlyOpenedEntryIndexes(self):
        ## DOESNT WORK YET since I can't figure out how to get the QStandardItem() from the self.entrymodel again
        return
        #if self.currentOpenedEntryIndexes is not None:
        #    for i in self.currentOpenedEntryIndexes:
        #        idx = self.entrymodel.itemFromIndex(i)
        #        print '???'

    # fills in the textboxes in the middle
    def PopulateTextEdit(self):
        if Globals.WriteDatabaseStorageToHddOnEntryChange:
            self.WriteDatabaseStorageToHdd()
                
        index = self.entryTreeView.currentIndex()
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

        self.FormatCurrentlyOpenedEntryIndexes()

        # boxes here
        rowBoxes = []
        self.currentOpenedEntryIndexes = []
        for i in range(len(self.textEditingBoxes)):
            try:
                idx = index.sibling(index.row()+(i-1), index.column())
                entryitem = self.entryStandardItemModel.item(idx.row())
                entrytextdisplay = self.entrySortFilterProxyModel.data(idx)

                if entrytextdisplay != None:
                    rowBoxes.append( entryitem.GraceNoteEntryId - 1 )
                    self.currentOpenedEntryIndexes.append( idx )
                else:
                    rowBoxes.append( -2 )
            except:
                rowBoxes.append( -2 )
        
        textEntries1 = []
        textEntries1raw = []
        textEntries2 = []
        textEntries2raw = []
        textEntries3 = []
        textEntries3raw = []
        for i in range(len(self.textEditingBoxes)):
            if rowBoxes[i] >= 0:
                textEntries1.append( Globals.VariableReplace(self.text[rowBoxes[i]][t]) )
                textEntries1raw.append( self.text[rowBoxes[i]][t] )
                textEntries2.append( Globals.VariableReplace(self.text[rowBoxes[i]][self.twoupEditingTextBoxes[i].role]) )
                textEntries2raw.append( self.text[rowBoxes[i]][self.twoupEditingTextBoxes[i].role] )
                textEntries3.append( Globals.VariableReplace(self.text[rowBoxes[i]][self.threeupEditingTextBoxes[i].role]) )
                textEntries3raw.append( self.text[rowBoxes[i]][self.threeupEditingTextBoxes[i].role] )
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
                textEntries3.append( '' )
                textEntries3raw.append( '' )
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

        # check for terms
        lengthEditingBoxes = len(self.textEditingBoxes)
        self.termTooltips = []
        for i in range(lengthEditingBoxes):
            if rowBoxes[i] >= 0:
                japanese = self.text[rowBoxes[i]][1]
                tooltip = ''
                for term in Globals.configData.Terms:
                    if japanese.find(term.JP) > -1:
                        tooltip = tooltip + '[' + term.JP + '] translates to [' + term.EN + ']\n'
                self.termTooltips.append(tooltip.strip())
            else:
                self.termTooltips.append('')

        # inform media boxes
        centerPanel = 1
        for name, medium in self.media.iteritems():
            #print self.text[rowBoxes[centerPanel] + medium.medium.offs][t]
            medium.refreshInfo( Globals.VariableReplace(self.text[rowBoxes[centerPanel] + medium.medium.offs][t]) )

        # inform font box
        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        self.fontWindow.drawText( self.text[rowBoxes[centerPanel]][t], Globals.GetDatabaseDescriptionString(str(databasefilename)) )

        # inform history window
        self.historyWindow.displayHistoryOfEntry(self.regularEditingTextBoxes[centerPanel].currentEntry)
                    
        # put text into textboxes, display entry number
        twoupTypeHelper = []
        twoupTypeHelper.append('E')
        twoupTypeHelper.append('J')
        twoupTypeHelper.append('C')
        for i in range(len(self.textEditingBoxes)):
            self.regularEditingTextBoxes[i].setText(textEntries1[i])
            if Globals.TwoUpMode >= 2:
                self.twoupEditingTextBoxes[i].setText(textEntries2[i])
            if Globals.TwoUpMode >= 3:
                self.threeupEditingTextBoxes[i].setText(textEntries3[i])
                
            if self.regularEditingTextBoxes[i].currentEntry >= 0:
                self.textEditingTitles[i].setText('Entry {0}: {1}'.format(rowBoxes[i]+1, commentTexts[i]))
                self.regularEditingTextBoxes[i].refreshFooter(textEntries1raw[i], self.state[0] + ': ')
                self.twoupEditingTextBoxes[i].refreshFooter(textEntries2raw[i], twoupTypeHelper[self.twoupEditingTextBoxes[i].role] + ': ')
                if self.termTooltips[i] != '':
                    self.textEditingTermIcons[i].setToolTip( 'Terminology in this Entry:\n' + self.termTooltips[i] )
                    self.textEditingTermIcons[i].show()
                else:
                    self.textEditingTermIcons[i].setToolTip('')
                    self.textEditingTermIcons[i].hide()
            else:
                self.textEditingTitles[i].setText('')
                self.textEditingFooters[i].setText('')
                self.twoupEditingFooters[i].setText('')
                self.textEditingTermIcons[i].setToolTip('')
                self.textEditingTermIcons[i].hide()
            

        # auto-update in Auto mode
        if Globals.ModeFlag == 'Auto':
            for i in range(len(self.textEditingBoxes)):
                self.regularEditingTextBoxes[i].manualEdit.emit(-2, self.regularEditingTextBoxes[i], self.textEditingFooters[i])

        
    def GetFullText(self, replaceVariables):
        string = ''
        i = 1
        if self.state == 'ENG':
            idx = 0
        elif self.state == 'JPN':
            idx = 1
        elif self.state == 'COM':
            idx = 2
        else:
            return 'NO VALID STATE'
            
        for entry in self.text:
            if entry[3] == 0 or self.debug.isChecked():
                string = string + 'Entry {0}'.format(i)
                if entry[5]:
                    string = string + ': ' + entry[5]
                string = string + '\n'
                if replaceVariables:
                    string = string + Globals.VariableReplace(entry[idx])
                else:
                    string = string + entry[idx]
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
            Globals.CursorGracesJapanese.execute(u"SELECT ID FROM Japanese WHERE debug=0 AND string LIKE ?", ('%' + unicode(matchString) + '%', ))
            JPmatches = set()
            for match in Globals.CursorGracesJapanese.fetchall():
                JPmatches.add(int(match[0]))
        except:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search returned too many results, try something with more letters or use the mass replace.")
            return

        MatchedEntries = []


        
        aList = Globals.configData.FileList
        for j in range(1, len(aList)):
            for File in aList[j]:
                data = Globals.Cache.GetDatabase(File)
                if self.debug.isChecked():
                    for i in xrange(len(data)):
                        if data[i].stringId in JPmatches or data[i].english.find(matchString) > -1:
                            MatchedEntries.append((File, i+1, data[i].english))
                else:
                    for i in xrange(len(data)):
                        if data[i].status >= 0:
                            if data[i].stringId in JPmatches or data[i].english.find(matchString) > -1:
                                MatchedEntries.append((File, i+1, data[i].english))

        #No matches found case
        if len(MatchedEntries) == 0:
            popup_menu.addAction('No Matches Found')

        TotalResultCount = len(MatchedEntries)
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
        
        if TotalResultCount > ResultLen:
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
            
                if str(category.child(p).statusTip()) == databaseName:
                    treeExpand = self.treemodel.indexFromItem(category)
                    self.tree.expand(treeExpand)
                    treeIndex = self.treemodel.indexFromItem(category.child(p))
                            
                    self.tree.setCurrentIndex(treeIndex)
                    self.tree.selectionModel().select(treeIndex, QtGui.QItemSelectionModel.SelectionFlags(3))

                    try:
                        entryItem = self.entryStandardItemModel.findItems(str(entry).zfill(5), QtCore.Qt.MatchContains)[0]
                        entryIndex = self.entryStandardItemModel.indexFromItem(entryItem)
                        sortIndex = self.entrySortFilterProxyModel.mapFromSource(entryIndex)

                        self.entryTreeView.setCurrentIndex(sortIndex)
                        self.entryTreeView.selectionModel().select(sortIndex, QtGui.QItemSelectionModel.SelectionFlags(3))
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


    def OpenOptionsWindow(self):
        self.WriteDatabaseStorageToHdd()
        self.optionsWindow = OptionsWindow.OptionsWindow(self)
        self.optionsWindow.exec_()


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
        

    def SpawnEntryListColumnHideMenu(self, pos):
        gPos = self.entryTreeView.mapToGlobal(pos)

        menu = QtGui.QMenu(self.entryTreeView)
        menuOptions = []
        for i in xrange( self.entryTreeView.header().count() ):
            qa = QtGui.QAction( self.entryTreeViewHeaderLabels[i], None )
            qa.setCheckable(True)
            qa.setChecked( self.entryTreeView.header().isSectionHidden(i) == False )
            menuOptions.append( qa )
        menu.addActions(menuOptions)

        selected = menu.exec_(gPos)
        for i in xrange( len(menuOptions) ):
            if menuOptions[i] == selected:
                self.entryTreeView.setColumnHidden(i, self.entryTreeView.header().isSectionHidden(i) == False)
                # make sure people don't disable all sections
                if self.entryTreeView.header().hiddenSectionCount() == self.entryTreeView.header().count():
                    self.entryTreeView.setColumnHidden(i, False)

        return

    def UpdateDebug(self):
        index = self.entryTreeView.currentIndex()
        if self.entryStandardItemModel.item(index.row(), 6).checkState() == 0:
            if self.entryStandardItemModel.item(index.row()).whatsThis() == "n":
                return # no change, was already not debug
            DebugState = False
        else:
            if self.entryStandardItemModel.item(index.row()).whatsThis() == "d":
                return # no change, was already debug
            DebugState = True
        
        #print("updateDebug")
        self.WriteDatabaseStorageToHdd()
        
        selectedEntryId = self.entryStandardItemModel.item(index.row(), 0).GraceNoteEntryId - 1
        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        SaveCon = DatabaseHandler.OpenEntryDatabase(databasefilename)
        SaveCur = SaveCon.cursor()
        SaveCur.execute("select StringID from Text where ID={0}".format(selectedEntryId+1))
        NextID = SaveCur.fetchall()[0][0]
        if DebugState:
            Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 1 WHERE ID = {0} AND debug != 1".format(NextID))
            SaveCur.execute("UPDATE Text SET status = -1, updated = 1 WHERE ID = {0} AND status != -1".format(selectedEntryId+1))
            self.entryStandardItemModel.item(index.row()).setWhatsThis("d")
        else:
            Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 0 WHERE ID = {0} AND debug != 0".format(NextID))
            SaveCur.execute("UPDATE Text SET status =  0, updated = 1 WHERE ID = {0} AND status  = -1".format(selectedEntryId+1))
            self.entryStandardItemModel.item(index.row()).setWhatsThis("n")
        self.update.add(str(databasefilename))
        SaveCon.commit()
        Globals.ConnectionGracesJapanese.commit()
        

        # color
        if not DebugState:
            SaveCur.execute("select status from Text where ID={0}".format(selectedEntryId+1))
            status = SaveCur.fetchall()[0][0]
            if status >= self.role:
                self.entryStandardItemModel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(220, 255, 220)))
                if Globals.Author == 'ruta':
                    self.entryStandardItemModel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))
                elif Globals.Author == 'Pikachu025':
                    self.entryStandardItemModel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(0, 150, 0)))
            else:
                self.entryStandardItemModel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
                
        else:
            self.entryStandardItemModel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 220, 220)))
            if Globals.Author == 'ruta':
                self.entryStandardItemModel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255,225,180)))             
        
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
        
        CommandOriginAutoMode = ( role == -2 )
        currentDatabaseStatus = self.text[textBox.currentEntry - 1][4]

        # if this was triggered by the Auto mode feature but the status wouldn't actually change by this operation
        if CommandOriginAutoMode and currentDatabaseStatus == self.role:
            # just exit out and don't write to memory or HDD
            return
        
                        
        #index = self.entry.currentIndex()
        #row = index.row()
        #self.entrymodel.item(index.sibling(index.row()-1, 0).row()).setBackground(QtGui.QBrush(QtGui.QColor(220, 255, 220)))
        #if self.author == 'ruta':
        #    self.entrymodel.item(index.sibling(index.row()-1, 0).row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))
            
        GoodString = Globals.VariableRemove(textBox.toPlainText())

        if role < 0:
            CommandOriginButton = False
            role = self.role
        else:
            CommandOriginButton = True
        
        updateStatusValue = self.FigureOutNewStatusValue(role, currentDatabaseStatus, self.state, CommandOriginButton, CommandOriginAutoMode)

        self.text[textBox.currentEntry - 1][4] = updateStatusValue
        textBox.iconToggle(updateStatusValue)
        
        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        
        #UpdatedDatabaseEntry(cleanString, databaseName, entry, role, state)
        # keep for later write to HDD
        self.InsertOrUpdateEntryToWrite(DatabaseCache.UpdatedDatabaseEntry(GoodString, databasefilename, textBox.currentEntry, updateStatusValue, self.state))
        textBox.refreshFooter(GoodString, self.state[0] + ': ')

        self.ReStartTimeoutTimer()
        
        # write the new string back into the main window, this is neccessary or else the new string isn't there when the displayed entry is changed!
        if self.state == 'ENG':
            self.text[textBox.currentEntry - 1][0] = GoodString
        elif self.state == "COM":
            self.text[textBox.currentEntry - 1][2] = GoodString
        
        # should probably make this optional
        if not CommandOriginAutoMode:
            self.fontWindow.drawText( GoodString, Globals.GetDatabaseDescriptionString(str(databasefilename)) )

        return

    def FigureOutNewStatusValue(self, role, currentDatabaseStatus, state, CommandOriginButton, CommandOriginAutoMode):
        if CommandOriginButton:
            # if origin a button: always set to argument
            return role
        elif state == "COM":
            # if origin a Comment box, don't update
            return currentDatabaseStatus
        else:
            # if origin by typing or automatic:
            if Globals.ModeFlag == 'Manual':
                # in manual mode: leave status alone, do not change, just fetch the existing one
                return currentDatabaseStatus
            else:
                # in Auto mode, check for Threshold
                if CommandOriginAutoMode and currentDatabaseStatus < self.autoThreshold:
                    return currentDatabaseStatus
                else:
                    # in (semi)auto mode: change to current role, except when disabled by option and current role is lower than existing status
                    if (not Globals.UpdateLowerStatusFlag) and currentDatabaseStatus > role:
                        return currentDatabaseStatus
                    else:
                        return role
                # endif Globals.UpdateLowerStatusFlag
            # endif Globals.ModeFlag
        # endif CommandOriginButton

    def WriteDatabaseStorageToHdd(self):
        self.timeoutTimer.stop()

        if not self.databaseWriteStorage:
            #print("Database storage empty, no need to write.")
            return
    
        lastDatabase = ""
        
        print("Writing database storage in memory to HDD...")
        
        # sort by time of entry creation so order of inserts is preserved (necessary eg. if changing both english and comment on same entry
        sortedStorage = sorted(self.databaseWriteStorage, key=lambda DatabaseEntryStruct: DatabaseEntryStruct.timestamp)
        
        databasesWrittenTo = set()

        #DatabaseEntryStruct(cleanString, databaseName, entry, role, state)
        SaveCon = None
        for d in sortedStorage:
            if lastDatabase != d.databaseName: # open up new DB connection if neccesary, otherwise just reuse the old one
                if SaveCon is not None:
                    SaveCon.commit()
                self.update.add(str(d.databaseName))
                SaveCon = DatabaseHandler.OpenEntryDatabase(d.databaseName)
                SaveCur = SaveCon.cursor()
                lastDatabase = d.databaseName
                databasesWrittenTo.add(d.databaseName)
            
            DatabaseHandler.CopyEntryToHistory(SaveCur, d.entry)
            if d.state == 'ENG':
                SaveCur.execute(u"UPDATE Text SET english=?, updated=1, status=?, UpdatedBy=?, UpdatedTimestamp=strftime('%s','now') WHERE ID=?", (d.cleanString, d.role, str(Globals.Author), d.entry))
            elif d.state == "COM":
                SaveCur.execute(u"UPDATE Text SET comment=?, updated=1, status=?, UpdatedBy=?, UpdatedTimestamp=strftime('%s','now') WHERE ID=?", (d.cleanString, d.role, str(Globals.Author), d.entry))
        if SaveCon is not None:
            SaveCon.commit()
        
        for db in databasesWrittenTo:
            CompletionTable.CalculateCompletionForDatabase(str(db))
            Globals.Cache.LoadDatabase(str(db))

        self.databaseWriteStorage.clear()

        
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
        
        self.update.clear()
        print 'Searching for databases with unsaved changes...'
        i = 1
        for item in Globals.configData.FileList[0]:
            for item in Globals.configData.FileList[i]:
                RecalcDbConn = DatabaseHandler.OpenEntryDatabase(item)
                RecalcDbCur = RecalcDbConn.cursor()
                RecalcDbCur.execute("SELECT Count(1) FROM Text WHERE updated = 1")
                exists = RecalcDbCur.fetchall()[0][0]
                if exists > 0:
                    self.update.add(str(item))
                    print 'Found database: ' + item
                RecalcDbConn.close()
            i = i + 1
        Globals.Settings.setValue('update', set(self.update))
        Globals.Settings.sync()
        print 'Done searching for databases with unsaved changes!'
        return
    
    def FindAllUsedSymbols(self):
        charSet = set()
        aList = Globals.configData.FileList
        for i in range(1, len(aList)):
            for File in aList[i]:
                db = Globals.Cache.GetDatabase(str(File))
                for item in db:
                    for char in item.english:
                        charSet.add(char)
        
        file = open('used_symbols.txt', 'w')
        charList = sorted(charSet)
        for char in charList:
            file.write( char.encode('utf8') )
        file.close()
        return

    # starts or restarts the timer that writes entries to HDD after a few minutes of inactivity
    def ReStartTimeoutTimer(self):
        self.timeoutTimer.stop()
        self.timeoutTimer.start( 120000 ) # 2 minutes

    def CallSavetoServer(self):
        NetworkHandler.SavetoServer(self)
        return
    
    def CallRevertFromServer(self):
        NetworkHandler.RevertFromServer(self)
        return

    def CallRetrieveModifiedFiles(self):
        NetworkHandler.RetrieveModifiedFiles(self, None)
        return

    def CallSavetoPatch(self):
        GracesCreation.SavetoPatch(self)
        return

    def CallPatchDol(self):
        GracesCreation.PatchDol(self)
        return

    def CallSavetoXML(self):
        GracesCreation.SavetoXML(self)
        return

    def CallSavetoBugfixXML(self):
        GracesCreation.SavetoBugfixXML(self)
        return

    def CallSavetoGracesfDemoXML(self):
        GracesCreation.SavetoGracesfDemoXML(self)
        return


def TrueCount():
    i = 1
    aList = Globals.configData.FileList[0]

    for item in aList:
        typeset = set([])
    
        for name in aList[i]:
            tempCon = DatabaseHandler.OpenEntryDatabase(name)
            tempCur = tempCon.cursor()
            
            tempCur.execute("SELECT StringID from Text")
            for thing in tempCur.fetchall():
                Globals.CursorGracesJapanese.execute("SELECT COUNT(ID) from Japanese where debug == 0 and ID == ?", (thing[0],))
                if Globals.CursorGracesJapanese.fetchall()[0][0] > 0:
                    typeset.add(thing[0])
                    
        print '{0}: {1} entries'.format(item, len(typeset))
        i += 1
