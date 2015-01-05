# -*- coding: utf-8 -*-

# This is only needed for Python v2 but is harmless for Python v3.
import sip
sip.setapi('QVariant', 2)

import Globals
from PyQt4 import Qt, QtCore, QtGui
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
try:
    from MassSpellcheck import *
except ImportError:
    pass
from GlobalChangelog import *
from LocalChangelog import *
from Statistics import *
from DuplicateText import *
import CompletionTable
import ImageViewerWindow
import FontDisplayWindow
import NetworkHandler
import DatabaseHandler
import HistoryWindow
import DatabaseCache
import OptionsWindow
import ProjectSelectWindow

def SetupEnvironment():
    Globals.commentsAvailableLabel = False

    try:
        from PyQt4.phonon import Phonon
        Globals.Audio = True
    except ImportError:
        print "Your Qt installation does not have Phonon support.\nPhonon is required to play audio clips."
        Globals.Audio = False

    Globals.SplashScreen = SplashScreen()
    Globals.SplashScreen.show()
    Globals.SplashScreen.raise_()
    Globals.SplashScreen.activateWindow()

    # load config
    try:
        projectSelectWindow = ProjectSelectWindow.ProjectSelectWindow()
        if not projectSelectWindow.configFileSelected: # if a file was auto-selected, don't open window
            projectSelectWindow.exec_()
        if projectSelectWindow.configFileSelected:
            Globals.configfile = projectSelectWindow.configfile
            Globals.configData = Configuration(Globals.configfile)
        else:
            return False
    except:
        print 'Failed, fallback to default config.xml'
        Globals.configfile = 'Projects/config.xml'
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

    try:
        import enchant
        Globals.enchanted = True
    except ImportError:
        Globals.enchanted = False
        print 'No pyenchant found. Spell checking will not be available.'


    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    Globals.ConnectionGracesJapanese = sqlite3.connect( Globals.configData.LocalDatabasePath + '/' + Globals.configData.OriginalDatabases[0] )
    Globals.CursorGracesJapanese = Globals.ConnectionGracesJapanese.cursor()
    Globals.ConnectionsOriginalDatabases = []
    for db in Globals.configData.OriginalDatabases:
        conn = sqlite3.connect( Globals.configData.LocalDatabasePath + '/' + db )
        Globals.ConnectionsOriginalDatabases.append( conn )

    Globals.EnglishVoiceLanguageFlag = False
    Globals.UpdateLowerStatusFlag = False
    Globals.ModeFlag = 'Semi-Auto'
    Globals.AmountEditingWindows = 5
    Globals.WriteDatabaseStorageToHddOnEntryChange = False
    Globals.FooterVisibleFlag = False

    Globals.Cache = DatabaseCache.DatabaseCache()

    return True

class SearchAction(QtGui.QAction):
 
    jumpTo = QtCore.pyqtSignal(unicode, int)
 
    def __init__(self, *args):
        QtGui.QAction.__init__(self, *args)
 
        self.triggered.connect(lambda x: self.jumpTo.emit(self.data()[0], self.data()[1]))

class Scripts2(QtGui.QWidget):

    def __init__(self, parent=None):
        super(Scripts2, self).__init__(parent)
        self.parent = parent
        self.parent.setWindowIcon(QtGui.QIcon('icons/GraceNote_48px.png'))
        self.LogDialog = None
        self.gLogDialog = None
        self.statDialog = None
        self.massDialog = None
        self.massSpellcheckDialog = None
        self.comDialog = None
        self.dupeDialog = None
        self.optionsWindow = None
        self.text = {}
        self.databaseWriteStorage = deque()
        self.currentTreeIndex = None
        self.currentOpenedEntryIndexes = None

        # --- Load User Settings ---
        Globals.Settings = QtCore.QSettings("GraceNote", Globals.configData.ID)
        if not Globals.Settings.contains('author'):
            text, ok = QtGui.QInputDialog.getText(self, "Enter your Name", "Author name:", QtGui.QLineEdit.Normal)
            if ok and text != '':
                Globals.Settings.setValue('author', text)

        Globals.Author = Globals.Settings.value('author')
        self.update = Globals.Settings.value('update')
       
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
        Globals.MainWindow.displayStatusMessage( str(len(self.update)) + ' files retained from last session: ' + ''.join(["%s, " % (k) for k in self.update])[:-2] )
        if len(self.update) > 0:
            Globals.HaveUnsavedChanges = True

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
            Globals.EnglishVoiceLanguageFlag = False
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

        if Globals.Settings.contains('TextboxVisibleFlagEnglish'):
            self.TextboxVisibleFlagEnglish = Globals.Settings.value('TextboxVisibleFlagEnglish') == 'True'
        else:
            self.TextboxVisibleFlagEnglish = True
        if Globals.Settings.contains('TextboxVisibleFlagJapanese'):
            self.TextboxVisibleFlagJapanese = Globals.Settings.value('TextboxVisibleFlagJapanese') == 'True'
        else:
            self.TextboxVisibleFlagJapanese = True
        if Globals.Settings.contains('TextboxVisibleFlagComment'):
            self.TextboxVisibleFlagComment = Globals.Settings.value('TextboxVisibleFlagComment') == 'True'
        else:
            self.TextboxVisibleFlagComment = True

        if Globals.Settings.contains('ColorCurrentStatus'):
            Globals.ColorCurrentStatus = QtGui.QColor( int(Globals.Settings.value('ColorCurrentStatus')) )
        else:
            Globals.ColorCurrentStatus = QtGui.QColor(160, 255, 160)

        if Globals.Settings.contains('ColorLowerStatus'):
            Globals.ColorLowerStatus = QtGui.QColor( int(Globals.Settings.value('ColorLowerStatus')) )
        else:
            Globals.ColorLowerStatus = QtGui.QColor(255, 160, 160)

        if Globals.Settings.contains('Scripts2.entryTreeViewHeaderWidths'):
            widths = str(Globals.Settings.value('Scripts2.entryTreeViewHeaderWidths')).split(',')
            self.entryTreeViewHeaderWidths = [int(w) for w in widths]
        else:
            self.entryTreeViewHeaderWidths = None

        if Globals.Settings.contains('Scripts2.entryTreeViewHeaderState'):
            self.entryTreeViewHeaderState = Globals.Settings.value('Scripts2.entryTreeViewHeaderState')
        else:
            self.entryTreeViewHeaderState = None

        self.SetWindowTitle()
        #>>> Globals.CursorGracesJapanese.execute('create table Log(ID int primary key, File text, Name text, Timestamp int)')


        self.timeoutTimer = QtCore.QTimer()
        self.timeoutTimer.timeout.connect(self.WriteDatabaseStorageToHdd)

        
        # --- List View of Files/Databases ---
        self.databaseTreeView = QtGui.QTreeView()
        self.databaseTreeModel = QtGui.QStandardItemModel()
        self.databaseTreeView.setAnimated(True)
        self.databaseTreeView.setIndentation(10)
        self.databaseTreeView.setSortingEnabled(False)
        self.databaseTreeView.sortByColumn(1, 0)
        self.databaseTreeView.setHeaderHidden(True)
        self.databaseTreeView.setContentsMargins(0, 0, 0, 0)
        self.PopulateDatabaseView(Globals.configData.FileTree)
        self.databaseTreeView.setModel(self.databaseTreeModel)


        # --- List View of Entries ---
        self.entryTreeView = QtGui.QTreeView()
        self.entryStandardItemModel = QtGui.QStandardItemModel()
        self.entrySortFilterProxyModel = QtGui.QSortFilterProxyModel()
        self.entrySortFilterProxyModel.setSourceModel(self.entryStandardItemModel)
        self.entryTreeView.setModel(self.entrySortFilterProxyModel)
        self.entryTreeView.setRootIsDecorated(False)

        self.entryTreeViewHeaderLabels = ['ID', 'Status', 'Comment?', 'IdentifyString', 'Text', 'Comment', 'Last updated by', 'Last updated at', 'Debug?']
        self.entryTreeViewHeadersVisible = []
        self.entryTreeViewHasBeenFilledOnce = False
        self.entryTreeViewHeaderWidthsDefaults = [30, 10, 10, 50, 200, 100, 90, 110, 20]

        # figure out which entry columns are visible
        visibleCount = 0
        try:
            tmpVisibleList = Globals.Settings.value('entryTreeViewHeadersVisible')
            for i in xrange( len(self.entryTreeViewHeaderLabels) ):
                visible = tmpVisibleList[i] == 't'
                self.entryTreeViewHeadersVisible.append( visible )
                if visible:
                    visibleCount += 1
        except:
            visibleCount = 0
        if visibleCount == 0:
            self.entryTreeViewHeadersVisible = []
            for i in xrange( len(self.entryTreeViewHeaderLabels) ):
                self.entryTreeViewHeadersVisible.append( True )


        self.termInEntryIcon = QtGui.QPixmap( 'icons/pictogram-din-m000-general.png' )
        self.termInEntryIcon = self.termInEntryIcon.scaled(13, 13, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.warningInEntryIcon = QtGui.QPixmap( 'icons/pictogram-din-w000-general.png' )
        self.warningInEntryIcon = self.warningInEntryIcon.scaled(13, 13, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        # --- Textboxes in the middle ---
        # should probably make this more readable and cleaner at some point...
        self.xTextBoxesENG = []
        self.xTextBoxesJPN = []
        self.xTextBoxesOrigLangs = []
        self.xTextBoxesCOM = []
        self.textEditingBoxes = []
        self.textEditingTitles = []
        self.textEditingTermIcons = []
        self.textEditingWarningIcons = []
        self.textEditingFootersENG = []
        self.textEditingFootersJPN = []
        for i in range(Globals.AmountEditingWindows):
            # create text boxes, set defaults
            tb1 = XTextBox(self, 'ENG')
            tb2 = XTextBox(self, 'JPN')
            tb2.setReadOnly(True)
            tb3 = XTextBox(self, 'COM')
            tb3.setReadOnly(False)

            if Globals.Settings.contains('font'):
                size = int(Globals.Settings.value('font'))
                font = QtGui.QFont()
                font.setPointSize( size )
           
                tb1.setFontPointSize(size)
                tb1.document().setDefaultFont( font )
                tb2.setFontPointSize(size)
                tb2.document().setDefaultFont( font )
                tb3.setFontPointSize(size)
                tb3.document().setDefaultFont( font )

            tbOrig = []
            for i in range(1, len(Globals.configData.OriginalDatabases)):
                tmp = XTextBox(self, 'JPN')
                tmp.setReadOnly(True)
                if Globals.Settings.contains('font'):
                    tmp.setFontPointSize(size)
                    tmp.document().setDefaultFont( font )
                tmp.setFooter(QtGui.QLabel())
                tbOrig.append(tmp)

            self.xTextBoxesENG.append(tb1)
            self.xTextBoxesJPN.append(tb2)
            self.xTextBoxesCOM.append(tb3)
            self.xTextBoxesOrigLangs.append( tbOrig )
            
            footer = QtGui.QLabel('')
            footer.setContentsMargins(0, 0, 0, 0)
            self.textEditingFootersENG.append(footer)
            tb1.setFooter(footer)
            footer2 = QtGui.QLabel('')
            footer2.setContentsMargins(0, 0, 0, 0)
            self.textEditingFootersJPN.append(footer2)
            tb2.setFooter(footer2)
            tb3.setFooter(QtGui.QLabel()) # questionable, but fixes a bug that would require a (minor, I guess) change of the signal/slot/UpdateTextGenericFunc stuff
            
            # Create layout for text boxes
            tmplayout = QtGui.QGridLayout()
            title = QtGui.QLabel('')
            termicon = QtGui.QLabel('')
            warningIcon = QtGui.QLabel('')

            htitlelayout = QtGui.QHBoxLayout()
            htitlelayout.addWidget(warningIcon)
            htitlelayout.addWidget(termicon)
            htitlelayout.addWidget(title)
            htitlelayout.setContentsMargins(0, 0, 0, 0)
            titlelayoutwgt = QtGui.QWidget()
            titlelayoutwgt.setLayout(htitlelayout)

            totalWidth = len(Globals.configData.OriginalDatabases) + 2
            tmplayout.addWidget(titlelayoutwgt, 1, 1, 1, totalWidth)
            tmplayout.addWidget(tb1, 2, 1, 1, 1)
            tmplayout.addWidget(tb2, 2, 2, 1, 1)
            counter = 3
            for tb in tbOrig:
                tmplayout.addWidget(tb, 2, counter, 1, 1)
                counter += 1
            tmplayout.addWidget(tb3, 2, counter, 1, 1)
            if Globals.FooterVisibleFlag:
                tmplayout.addWidget(footer , 3, 1, 1, totalWidth)
                tmplayout.addWidget(footer2, 4, 1, 1, totalWidth)
            tmplayout.setContentsMargins(0, 0, 0, 0)

            tmpqgrpbox = QtGui.QWidget()
            tmpqgrpbox.setLayout(tmplayout)
            tmpqgrpbox.setContentsMargins( 0, 0, 0, 0 )
            tmpqgrpbox.setMinimumSize( 0, 0 )

            termicon.setPixmap(self.termInEntryIcon)
            termicon.hide()
            termicon.setFixedSize(13, 13)
            warningIcon.setPixmap(self.warningInEntryIcon)
            warningIcon.hide()
            warningIcon.setFixedSize(13, 13)
            
            self.textEditingBoxes.append(tmpqgrpbox)
            self.textEditingTitles.append(title)
            self.textEditingTermIcons.append(termicon)
            self.textEditingWarningIcons.append(warningIcon)
            
        # ------------------------------------------------------ #

        self.liveSearchTextbox = QtGui.QLineEdit()
        self.liveSearchTextbox.setFixedWidth(200)
        self.jumpToTextbox = QtGui.QLineEdit()
        self.jumpToTextbox.setFixedWidth(120)
        
        self.debugOnOffButton = QtGui.QAction(QtGui.QIcon('icons/debugoff.png'), 'Display Debug', None)
        self.debugOnOffButton.setCheckable(True)
        self.debugOnOffButton.setChecked(0)

        self.alwaysOnTopButton = QtGui.QAction('Always on Top', None)
        self.alwaysOnTopButton.setCheckable(True)
        self.alwaysOnTopButton.setChecked(0)
        
        self.databaseTreeView.selectionModel().selectionChanged.connect(self.PopulateEntryList)
        self.entryTreeView.selectionModel().selectionChanged.connect(self.PopulateTextEdit)
        self.entryStandardItemModel.itemChanged.connect(self.UpdateDebug)
        self.entryTreeView.setSortingEnabled(True)
        self.entryTreeView.header().setClickable(True)
        self.entryTreeView.header().setSortIndicatorShown(True)
        self.entryTreeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.entryTreeView.header().customContextMenuRequested.connect(self.SpawnEntryListColumnHideMenu)
        for editbox in self.xTextBoxesENG:
            editbox.manualEdit.connect(self.UpdateTextGenericFunc)
        for editbox in self.xTextBoxesCOM:
            editbox.manualEdit.connect(self.UpdateTextGenericFunc)
        self.debugOnOffButton.toggled.connect(self.DebugFilter)
        self.alwaysOnTopButton.toggled.connect(self.AlwaysOnTopToggle)
        self.liveSearchTextbox.returnPressed.connect(self.LiveSearch)
        self.jumpToTextbox.returnPressed.connect(self.JumpToDatabase)

        # --- Toolbar & Menu Options ---
        FlexibleSpace = QtGui.QLabel('')
        FlexibleSpace.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        
        self.switchEngOnOffAction = QtGui.QAction(QtGui.QIcon('icons/globe.png'), 'English', None)
        self.switchEngOnOffAction.triggered.connect(self.SwitchVisibleEng)
        self.switchEngOnOffAction.setShortcut(QtGui.QKeySequence('Ctrl+1'))
        self.switchJpnOnOffAction = QtGui.QAction(QtGui.QIcon('icons/japan.png'), 'Japanese', None)
        self.switchJpnOnOffAction.triggered.connect(self.SwitchVisibleJpn)
        self.switchJpnOnOffAction.setShortcut(QtGui.QKeySequence('Ctrl+2'))
        self.switchComOnOffAction = QtGui.QAction(QtGui.QIcon('icons/comment.png'), 'Comments', None)
        self.switchComOnOffAction.triggered.connect(self.SwitchVisibleCom)
        self.switchComOnOffAction.setShortcut(QtGui.QKeySequence('Ctrl+3'))

        self.playCentralAudioAction = QtGui.QAction('Play Audio (2nd Textbox)', None)
        self.playCentralAudioAction.triggered.connect(self.PlayCentralAudio)
        self.playCentralAudioAction.setShortcut(QtGui.QKeySequence('Ctrl+-'))
        self.formatCentralTextMode1Action = QtGui.QAction('[BETA] Format Text (Max JP Width, any linecount)', None)
        self.formatCentralTextMode1Action.triggered.connect(self.FormatCentralTextMatchJapaneseWidth)
        self.formatCentralTextMode2Action = QtGui.QAction('[BETA] Format Text (Any width, max JP linecount)', None)
        self.formatCentralTextMode2Action.triggered.connect(self.FormatCentralTextAllowExceedWidth)
        self.formatCentralTextMode3Action = QtGui.QAction('[BETA] Format Text (Match JP Linecount in Block)', None)
        self.formatCentralTextMode3Action.triggered.connect(self.FormatCentralTextMatchJapaneseLinecountAsBlock)
        

        self.setCentralAsActs = []
        for i in range( Globals.configData.TranslationStagesCount + 1 ):
            action = QtGui.QAction( 'Set Status to {0} (Center Panel)'.format(i), None )
            action.triggered.connect( self.SetCentralAsClosure(i) )
            action.setShortcut( QtGui.QKeySequence( 'Alt+' + str(i) ) )
            self.setCentralAsActs.append( action )

        self.openStatisticsAction = QtGui.QAction(QtGui.QIcon('icons/report.png'), 'Reports', None)
        self.openStatisticsAction.triggered.connect(self.ShowStats)
        self.openStatisticsAction.setShortcut(QtGui.QKeySequence('Ctrl+R'))

        self.openMassReplaceAction = QtGui.QAction(QtGui.QIcon('icons/massreplace.png'), 'Mass &Replace', None)
        self.openMassReplaceAction.triggered.connect(self.ShowMassReplace)
        self.openMassReplaceAction.setShortcut(QtGui.QKeySequence('Ctrl+M'))
        
        self.openMassSpellcheckAction = QtGui.QAction(QtGui.QIcon('icons/massreplace.png'), 'Mass Spellcheck', None)
        self.openMassSpellcheckAction.triggered.connect(self.ShowMassSpellcheck)

        self.openCompletionAction = QtGui.QAction(QtGui.QIcon('icons/completion.png'), 'Completion', None)
        self.openCompletionAction.triggered.connect(self.ShowCompletionTable)
        self.openCompletionAction.setShortcut(QtGui.QKeySequence('Ctrl+%'))

        self.runPropagateDebugG2DAction = QtGui.QAction('Propagate Debug (GracesJapanese -> Databases)', None)
        self.runPropagateDebugG2DAction.triggered.connect(self.PropagateDebugGJ2Databases)
        self.runPropagateDebugD2GAction = QtGui.QAction('Propagate Debug (Databases -> GracesJapanese)', None)
        self.runPropagateDebugD2GAction.triggered.connect(self.PropagateDebugDatabases2GJ)

        self.runFullTextCopyAction = QtGui.QAction('Full-Text Copy', None)
        self.runFullTextCopyAction.triggered.connect(self.FullTextCopy)
        self.runFullTextCopyAction.setShortcut(QtGui.QKeySequence('Ctrl+T'))

        self.runSaveToServerAction = QtGui.QAction(QtGui.QIcon('icons/upload.png'), 'Save', None)
        self.runSaveToServerAction.triggered.connect(self.CallSavetoServer)
        self.runSaveToServerAction.setShortcut(QtGui.QKeySequence('Ctrl+S'))

        self.runRevertFromServerAction = QtGui.QAction(QtGui.QIcon('icons/save.png'), 'Revert', None)
        self.runRevertFromServerAction.triggered.connect(self.CallRevertFromServer)
        
        self.runRetrieveModifiedFilesAction = QtGui.QAction(QtGui.QIcon('icons/save.png'), 'Update', None)
        self.runRetrieveModifiedFilesAction.triggered.connect(self.CallRetrieveModifiedFiles)
        self.runRetrieveModifiedFilesAction.setShortcut(QtGui.QKeySequence('Ctrl+U'))

        self.runRefreshCompletionDatabaseAction = QtGui.QAction('Refresh Completion Database', None)
        self.runRefreshCompletionDatabaseAction.triggered.connect(self.RefreshCompletionDatabase)

        self.runFindUsedSymbolsAction = QtGui.QAction('Find Used Symbols', None)
        self.runFindUsedSymbolsAction.triggered.connect(self.FindAllUsedSymbols)
        
        self.runFindUnsavedDatabasesAction = QtGui.QAction(QtGui.QIcon('icons/refresh.png'), 'Find Unsaved Databases', None)
        self.runFindUnsavedDatabasesAction.triggered.connect(self.FindUnsavedDatabases)

        self.openGlobalChangelogAction = QtGui.QAction(QtGui.QIcon('icons/global.png'), 'Global Changelog', None)
        self.openGlobalChangelogAction.triggered.connect(self.ShowGlobalChangelog)
        self.openGlobalChangelogAction.setShortcut(QtGui.QKeySequence('Ctrl+G'))

        self.openLocalChangelogAction = QtGui.QAction(QtGui.QIcon('icons/changelog.png'), 'Changelog', None)
        self.openLocalChangelogAction.triggered.connect(self.ShowChangelog)
        self.openLocalChangelogAction.setShortcut(QtGui.QKeySequence('Ctrl+L'))

        self.openDuplicateTextAction = QtGui.QAction(QtGui.QIcon('icons/ruta.png'), 'Duplicate Text', None)
        self.openDuplicateTextAction.triggered.connect(self.ShowDuplicateText)
        self.openDuplicateTextAction.setShortcut(QtGui.QKeySequence('Ctrl+D'))

        self.runQuitAction = QtGui.QAction('Quit', None)
        self.runQuitAction.triggered.connect(self.CleanUpAndQuit)
        self.runQuitAction.setShortcut(QtGui.QKeySequence('Ctrl+W'))


        self.toolbarIconSizes = [12, 16, 18, 24, 36, 48, 64]
        self.changeToolbarIconSizeActions = []
        for size in self.toolbarIconSizes:
            self.changeToolbarIconSizeActions.append(QtGui.QAction('{0} x {0}'.format(size), None))

        self.changeToolbarToOnlyTextAction = QtGui.QAction('Only Text', None)
        self.changeToolbarToOnlyIconAction = QtGui.QAction('Only Icon', None)
        self.changeToolbarToBelowIconAction = QtGui.QAction('Beneath Icon', None)
        self.changeToolbarToLeftOfIconAction = QtGui.QAction('Beside Icon', None)

        self.setTranslationRoleActions = []
        for i in range( 1, Globals.configData.TranslationStagesCount + 1 ):
            action = QtGui.QAction(QtGui.QIcon('icons/status/{0}g.png'.format(i)), Globals.configData.TranslationStagesNames[i], None)
            action.setToolTip( Globals.configData.TranslationStagesDescs[i] )
            self.setTranslationRoleActions.append( action )

        self.setAutoThresholdActions = []
        action = QtGui.QAction(QtGui.QIcon('icons/status/1.png'), Globals.configData.TranslationStagesNames[0], None)
        self.setAutoThresholdActions.append( action )
        for i in range( 1, Globals.configData.TranslationStagesCount ):
            action = QtGui.QAction(QtGui.QIcon('icons/status/{0}g.png'.format(i)), Globals.configData.TranslationStagesNames[i], None)
            self.setAutoThresholdActions.append( action )

        self.openOptionsWindowAction = QtGui.QAction('Preferences...', None)
        self.openOptionsWindowAction.triggered.connect(self.OpenOptionsWindow)

        self.setTranslationModeAutoAction = QtGui.QAction('Auto', None)
        self.setTranslationModeSemiautoAction = QtGui.QAction('Semi-Auto', None)
        self.setTranslationModeManualAction = QtGui.QAction('Manual', None)
        

        self.runScrollUpAction = QtGui.QAction('Scroll Up', None)
        self.runScrollUpAction.triggered.connect(self.ScrollUp)
        self.runScrollUpAction.setShortcut(QtGui.QKeySequence('Ctrl+Up'))
        self.runScrollUpAction2 = QtGui.QAction('Scroll Up', None)
        self.runScrollUpAction2.triggered.connect(self.ScrollUp)
        self.runScrollUpAction2.setShortcut(QtGui.QKeySequence('Alt+Up'))
        self.runScrollUpAction3 = QtGui.QAction('Scroll Up', None)
        self.runScrollUpAction3.triggered.connect(self.ScrollUp)
        self.runScrollUpAction3.setShortcut(QtGui.QKeySequence('PgUp'))

        self.runScrollDownAction = QtGui.QAction('Scroll Down', None)
        self.runScrollDownAction.triggered.connect(self.ScrollDown)
        self.runScrollDownAction.setShortcut(QtGui.QKeySequence('Ctrl+Down'))
        self.runScrollDownAction2 = QtGui.QAction('Scroll Down', None)
        self.runScrollDownAction2.triggered.connect(self.ScrollDown)
        self.runScrollDownAction2.setShortcut(QtGui.QKeySequence('Alt+Down'))
        self.runScrollDownAction3 = QtGui.QAction('Scroll Down', None)
        self.runScrollDownAction3.triggered.connect(self.ScrollDown)
        self.runScrollDownAction3.setShortcut(QtGui.QKeySequence('PgDown'))
        
        self.openMediaWindowsAction = QtGui.QAction('Reopen Media Windows', None)
        self.openMediaWindowsAction.triggered.connect(self.OpenMediumWindows)

        self.openFontWindownAction = QtGui.QAction('Reopen Font Window', None)
        self.openFontWindownAction.triggered.connect(self.OpenFontWindow)

        self.openHistoryWindowAction = QtGui.QAction('Reopen History Window', None)
        self.openHistoryWindowAction.triggered.connect(self.OpenHistoryWindow)


        # === Toolbar ===
        self.Toolbar = parent.Toolbar
        self.Toolbar.clear()
        
        self.Toolbar.addAction(self.switchEngOnOffAction)
        self.Toolbar.addAction(self.switchJpnOnOffAction)
        self.Toolbar.addAction(self.switchComOnOffAction)
        self.Toolbar.addAction(self.openLocalChangelogAction)
        self.Toolbar.addAction(self.openGlobalChangelogAction)
        self.Toolbar.addAction(self.openStatisticsAction)
        self.Toolbar.addAction(self.openCompletionAction)
        self.Toolbar.addAction(self.openMassReplaceAction)
        if Globals.enchanted:
            self.Toolbar.addAction(self.openMassSpellcheckAction)
        self.Toolbar.addAction(self.openDuplicateTextAction)
        self.Toolbar.addWidget(FlexibleSpace)

        formatButtonToolbar = QtGui.QToolBar()
        formatButtonToolbar.setOrientation( Qt.Qt.Vertical )
        formatButtonToolbar.addAction(self.formatCentralTextMode1Action)
        formatButtonToolbar.addAction(self.formatCentralTextMode2Action)
        formatButtonToolbar.addAction(self.formatCentralTextMode3Action)
        self.Toolbar.addWidget( formatButtonToolbar )
        self.Toolbar.addSeparator()
        
        jumpToAndQuickSearchLayout = QtGui.QGridLayout()
        jumpToAndQuickSearchLayout.addWidget( QtGui.QLabel('Jump To'), 0, 0 )
        jumpToAndQuickSearchLayout.addWidget( self.jumpToTextbox, 0, 1 )
        jumpToAndQuickSearchLayout.addWidget( QtGui.QLabel('Quick Search'), 1, 0 )
        jumpToAndQuickSearchLayout.addWidget( self.liveSearchTextbox, 1, 1 )
        jumpToAndQuickSearchGroupBox = QtGui.QGroupBox()
        jumpToAndQuickSearchGroupBox.setLayout( jumpToAndQuickSearchLayout )
        self.Toolbar.addWidget( jumpToAndQuickSearchGroupBox )

        self.Toolbar.addAction(self.debugOnOffButton)
        self.Toolbar.addAction(self.alwaysOnTopButton)
        
        if Globals.Settings.contains('toolicon'):
            self.Toolbar.setIconSize(QtCore.QSize(Globals.Settings.value('toolicon'), Globals.Settings.value('toolicon')))
        if Globals.Settings.contains('toolstyle'):
            self.Toolbar.setToolButtonStyle(Globals.Settings.value('toolstyle'))
        else:
            self.Toolbar.setToolButtonStyle(3)

        # === File Menu ===
        fileMenu = QtGui.QMenu("&File", self)
        fileMenu.addAction(self.runSaveToServerAction)
        fileMenu.addAction(self.runRetrieveModifiedFilesAction)
        fileMenu.addAction(self.runFindUnsavedDatabasesAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.runRevertFromServerAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.runQuitAction)

        # === Edit Menu ===
        editMenu = QtGui.QMenu("&Edit", self)
        editMenu.addAction(self.runFullTextCopyAction)
        editMenu.addSeparator()
        for action in self.setCentralAsActs:
            editMenu.addAction( action )

        # === View Menu ===
        viewMenu = QtGui.QMenu("View", self)
        viewMenu.addAction(self.switchEngOnOffAction)
        viewMenu.addAction(self.switchJpnOnOffAction)
        viewMenu.addAction(self.switchComOnOffAction)
        viewMenu.addSeparator()
        viewMenu.addAction(self.playCentralAudioAction)
        viewMenu.addSeparator()
        viewMenu.addAction(self.runScrollUpAction)
        viewMenu.addAction(self.runScrollDownAction)
        viewMenu.addAction(self.runScrollUpAction2)
        viewMenu.addAction(self.runScrollDownAction2)
        viewMenu.addAction(self.runScrollUpAction3)
        viewMenu.addAction(self.runScrollDownAction3)
        viewMenu.addSeparator()
        viewMenu.addAction(self.openFontWindownAction)
        viewMenu.addAction(self.openMediaWindowsAction)
        viewMenu.addAction(self.openHistoryWindowAction)
        viewMenu.addSeparator()

        textMenu = QtGui.QMenu("Toolbar Style", self)
        textMenu.triggered.connect(self.SetToolbarStyle)
        textMenu.addAction(self.changeToolbarToOnlyIconAction)
        textMenu.addAction(self.changeToolbarToOnlyTextAction)
        textMenu.addAction(self.changeToolbarToBelowIconAction)
        textMenu.addAction(self.changeToolbarToLeftOfIconAction)
        viewMenu.addMenu(textMenu)

        iconSizeMenu = QtGui.QMenu("Toolbar Icon Size", self)
        iconSizeMenu.triggered.connect(self.SetToolbarIconSize)
        for action in self.changeToolbarIconSizeActions:
            iconSizeMenu.addAction(action)
        viewMenu.addMenu(iconSizeMenu)

        fontSizeMenu = QtGui.QMenu("Font Size", self)
        fontSizeMenu.triggered.connect(self.ChangeFontSize)
        fontSizeMenu.addAction('8')
        fontSizeMenu.addAction('9')
        fontSizeMenu.addAction('10')
        fontSizeMenu.addAction('12')
        fontSizeMenu.addAction('14')
        fontSizeMenu.addAction('18')
        fontSizeMenu.addAction('24')
        fontSizeMenu.addAction('36')
        viewMenu.addMenu(fontSizeMenu)

        # === Role Menu ===
        roleMenu = QtGui.QMenu('Role', self)
        roleMenu.triggered.connect(self.SetTranslationRole)

        self.disabledMenuOptionSetRole = QtGui.QAction('Role', None)
        self.disabledMenuOptionSetRole.setEnabled(False)
        roleMenu.addAction(self.disabledMenuOptionSetRole)
        for action in self.setTranslationRoleActions:
            roleMenu.addAction( action )
        roleMenu.addSeparator()

        self.disabledMenuOptionSetMode = QtGui.QAction('Mode', None)
        self.disabledMenuOptionSetMode.setEnabled(False)
        roleMenu.addAction(self.disabledMenuOptionSetMode)
        roleMenu.addAction(self.setTranslationModeAutoAction)
        roleMenu.addAction(self.setTranslationModeSemiautoAction)
        roleMenu.addAction(self.setTranslationModeManualAction)
        roleMenu.addSeparator()

        self.disabledMenuOptionSetThreshold = QtGui.QAction('Auto Mode Threshold', None)
        self.disabledMenuOptionSetThreshold.setEnabled(False)
        roleMenu.addAction(self.disabledMenuOptionSetThreshold)
        for action in self.setAutoThresholdActions:
            roleMenu.addAction( action )

        # === Tools Menu ===
        toolsMenu = QtGui.QMenu("Tools", self)
        toolsMenu.addAction(self.openLocalChangelogAction)
        toolsMenu.addAction(self.openGlobalChangelogAction)
        toolsMenu.addAction(self.openStatisticsAction)
        toolsMenu.addAction(self.openCompletionAction)
        toolsMenu.addSeparator()
        toolsMenu.addAction(self.openMassReplaceAction)
        if Globals.enchanted:
            toolsMenu.addAction(self.openMassSpellcheckAction)
        toolsMenu.addAction(self.openDuplicateTextAction)
        toolsMenu.addSeparator()
        toolsMenu.addAction(self.formatCentralTextMode1Action)
        toolsMenu.addAction(self.formatCentralTextMode2Action)
        toolsMenu.addAction(self.formatCentralTextMode3Action)
        toolsMenu.addSeparator()
        toolsMenu.addAction(self.runPropagateDebugG2DAction)
        toolsMenu.addAction(self.runPropagateDebugD2GAction)
        toolsMenu.addAction(self.runRefreshCompletionDatabaseAction)
        toolsMenu.addAction(self.runFindUsedSymbolsAction)

        # === Options Menu ===
        optionsMenu = QtGui.QMenu("Options", self)
        optionsMenu.addAction(self.openOptionsWindowAction)

        # === Menu Bar ===
        parent.menuBar().clear()
        parent.menuBar().addMenu(fileMenu)
        parent.menuBar().addMenu(editMenu)
        parent.menuBar().addMenu(viewMenu)
        parent.menuBar().addMenu(roleMenu)
        parent.menuBar().addMenu(toolsMenu)
        parent.menuBar().addMenu(optionsMenu)


        # --- Layout ---
        Globals.commentsAvailableLabel = QtGui.QLabel("-")
        
        FileListSubLayout = QtGui.QVBoxLayout()
        FileListSubLayout.addWidget(Globals.commentsAvailableLabel)
        FileListSubLayout.addWidget(self.databaseTreeView)
        
        EditingWindowSubLayoutSplitter = QtGui.QSplitter()
        EditingWindowSubLayoutSplitter.setOrientation(QtCore.Qt.Vertical)
        EditingWindowSubLayoutSplitter.setChildrenCollapsible( False )
        EditingWindowSubLayoutSplitter.setMidLineWidth( 0 )
        EditingWindowSubLayoutSplitter.setMinimumSize( 0, 0 )
        for i in range(len(self.textEditingBoxes)):
            EditingWindowSubLayoutSplitter.addWidget(self.textEditingBoxes[i])
        
        self.mainAreaSplitLayout = QtGui.QSplitter()
        FileListSubLayoutWidget = QtGui.QWidget()
        FileListSubLayoutWidget.setLayout(FileListSubLayout)
        self.mainAreaSplitLayout.addWidget(FileListSubLayoutWidget)
        self.mainAreaSplitLayout.addWidget(EditingWindowSubLayoutSplitter)
        self.mainAreaSplitLayout.addWidget(self.entryTreeView)
        
        self.mainAreaSplitLayout.setSizes( [200, 400, 200] )

        geom = Globals.Settings.value('Geometry/Scripts2.mainAreaSplitLayout')
        if geom is not None:
            self.mainAreaSplitLayout.restoreGeometry(geom)
        state = Globals.Settings.value('States/Scripts2.mainAreaSplitLayout')
        if state is not None:
            self.mainAreaSplitLayout.restoreState(state)
        
        layoutWidgetAdapter = QtGui.QVBoxLayout()
        layoutWidgetAdapter.addWidget(self.mainAreaSplitLayout)
        self.setLayout(layoutWidgetAdapter)

        self.massDialogOpened = False
        self.massSpellcheckDialogOpened = False
        self.globalChangelogOpened = False
        self.statsDialogOpened = False
        self.duplicateTextDialogOpened = False
        
        geom = Globals.Settings.value('Geometry/Scripts2')
        if geom is not None:
            self.restoreGeometry(geom)

        if not self.TextboxVisibleFlagEnglish:
            for box in self.xTextBoxesENG:
                box.hide()
        if not self.TextboxVisibleFlagJapanese:
            for box in self.xTextBoxesJPN:
                box.hide()
        if not self.TextboxVisibleFlagComment:
            for box in self.xTextBoxesCOM:
                box.hide()

        self.OpenMediumWindows()
        self.OpenFontWindow()
        self.OpenHistoryWindow()

        NetworkHandler.RetrieveModifiedFiles(self, None)
        Globals.Cache.StartBackgroundDatabaseLoadingThread()

        Globals.SplashScreen.destroyScreen()

    def OpenMediumWindows(self):
        self.media = {}
        self.OpenImageWindows()
            
    def OpenImageWindows(self):
        for img in Globals.configData.Images:
            self.OpenImageWindow(img)
    
    def OpenImageWindow(self, img):
        self.media[img.name] = ImageViewerWindow.ImageViewerWindow(self, img)
        self.media[img.name].show()
        self.media[img.name].raise_()
        self.media[img.name].activateWindow()

    def OpenFontWindow(self):
        self.fontWindow = FontDisplayWindow.FontDisplayWindow(self)
        self.fontWindow.show()
        self.fontWindow.raise_()
        self.fontWindow.activateWindow()

    def OpenHistoryWindow(self):
        self.historyWindow = HistoryWindow.HistoryWindow(self)
        self.historyWindow.show()
        self.historyWindow.raise_()
        self.historyWindow.activateWindow()

    def CleanUpAndQuit(self):
        self.WriteDatabaseStorageToHdd()

        # display warning to user if there are unsaved changes
        if Globals.HaveUnsavedChanges:
            msg = QtGui.QMessageBox()
            msg.setText("Local changes have not been saved to the server!")
            msg.setInformativeText("It is recommended to upload changes before closing. If changes are not saved, they will be available for later upload the next time this project is opened.")
            msg.setStandardButtons( QtGui.QMessageBox.Save | QtGui.QMessageBox.Close | QtGui.QMessageBox.Cancel )
            ret = msg.exec_()
            
            if ret == QtGui.QMessageBox.Save:
                # try saving, keep program open if save fails
                if not self.CallSavetoServer():
                    return False
            elif ret == QtGui.QMessageBox.Close:
                pass
            elif ret == QtGui.QMessageBox.Cancel:
                return False


        Globals.GraceNoteIsTerminating = True

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

        headersVisibleString = ''
        for i in xrange( len(self.entryTreeViewHeadersVisible) ):
            if self.entryTreeViewHeadersVisible[i]:
                headersVisibleString += 't'
            else:
                headersVisibleString += 'f'
        Globals.Settings.setValue('entryTreeViewHeadersVisible', headersVisibleString)

        Globals.Settings.setValue('update', set(self.update))
        Globals.MainWindow.displayStatusMessage( str(len(self.update)) + ' files retained for next session: ' + ''.join(["%s, " % (k) for k in self.update])[:-2] )

        Globals.Settings.setValue('Geometry/Scripts2', self.saveGeometry())
        Globals.Settings.setValue('Geometry/Scripts2.mainAreaSplitLayout', self.mainAreaSplitLayout.saveGeometry())
        Globals.Settings.setValue('States/Scripts2.mainAreaSplitLayout', self.mainAreaSplitLayout.saveState())

        if self.entryTreeViewHasBeenFilledOnce:
            self.StoreWidthsOfEntryList()
        if self.entryTreeViewHeaderWidths is not None:
            widths = ','.join([str(w) for w in self.entryTreeViewHeaderWidths])
            Globals.Settings.setValue('Scripts2.entryTreeViewHeaderWidths', widths)
        if self.entryTreeViewHeaderState is not None:
            Globals.Settings.setValue('Scripts2.entryTreeViewHeaderState', self.entryTreeViewHeaderState)

        Globals.Settings.sync()
        self.close()
        quit()

        return True
        

    def ScrollUp(self, action):
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
            pass


    def ScrollDown(self, action):
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
            pass



    def ChangeFontSize(self, action):
        size = int(action.iconText())

        font = QtGui.QFont()
        font.setPointSize( size )
        for box in self.xTextBoxesENG:
            box.setFontPointSize(size)
            box.document().setDefaultFont( font )
        for box in self.xTextBoxesJPN:
            box.setFontPointSize(size)
            box.document().setDefaultFont( font )
        for box in self.xTextBoxesCOM:
            box.setFontPointSize(size)
            box.document().setDefaultFont( font )

        self.PopulateTextEdit()
        Globals.Settings.setValue('font', size)


    def SetTranslationRole(self, action):
        if action == self.setTranslationModeAutoAction:
            Globals.ModeFlag = 'Auto'
        if action == self.setTranslationModeSemiautoAction:
            Globals.ModeFlag = 'Semi-Auto'
        if action == self.setTranslationModeManualAction:
            Globals.ModeFlag = 'Manual'
        Globals.Settings.setValue('mode', Globals.ModeFlag)

        for i, act in enumerate( self.setTranslationRoleActions ):
            if action == act:
                self.role = i + 1
                break

        for i, act in enumerate( self.setAutoThresholdActions ):
            if action == act:
                self.autoThreshold = i
                break

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
        t = "GraceNote"
        if Globals.ModeFlag == 'Auto':
            t = t + " - {0} in {1} mode (Threshold: {2})".format(Globals.configData.TranslationStagesVerbs[self.role], Globals.ModeFlag, Globals.configData.TranslationStagesNames[self.autoThreshold])
        else:
            t = t + " - {0} in {1} mode".format(Globals.configData.TranslationStagesVerbs[self.role], Globals.ModeFlag)
        t = t + " - "
        if Globals.HaveUnsavedChanges:
            t = t + "*"
        t = t + Globals.configfile
        self.parent.setWindowTitle(t)


    def SetToolbarIconSize(self, action):
        i = 0
        for size in self.toolbarIconSizes:
            if action == self.changeToolbarIconSizeActions[i]:
                self.Toolbar.setIconSize(QtCore.QSize(size, size))
                Globals.Settings.setValue('toolicon', size)
                if self.Toolbar.toolButtonStyle() == 1:
                    self.Toolbar.setToolButtonStyle(3)
            i += 1
            
            
    def SetToolbarStyle(self, action):

        if action == self.changeToolbarToOnlyTextAction:
            self.Toolbar.setToolButtonStyle(1)
            Globals.Settings.setValue('toolstyle', 1)

        if action == self.changeToolbarToOnlyIconAction:
            self.Toolbar.setToolButtonStyle(0)
            Globals.Settings.setValue('toolstyle', 0)
        
        if action == self.changeToolbarToBelowIconAction:
            self.Toolbar.setToolButtonStyle(3)
            Globals.Settings.setValue('toolstyle', 3)
        
        if action == self.changeToolbarToLeftOfIconAction:
            self.Toolbar.setToolButtonStyle(2)
            Globals.Settings.setValue('toolstyle', 2)
        
    def PropagateDebugGJ2Databases(self):
        self.WriteDatabaseStorageToHdd()
        
        # Applies the debug status in GracesJapanese to all databases
        Globals.MainWindow.displayStatusMessage( 'Consolidate Debug: GracesJapanese -> Individual Databases' )
        
        Globals.Cache.databaseAccessRLock.acquire()

        for filename in Globals.configData.FileList:
            Globals.MainWindow.displayStatusMessage( "Consolidate Debug: Processing: {0}".format(filename) )
            
            UpdateCon = DatabaseHandler.OpenEntryDatabase(filename)
            UpdateCur = UpdateCon.cursor()
            UpdateCur.execute("SELECT ID, StringID, status FROM Text")
                
            for entry in UpdateCur.fetchall():                        
                Globals.CursorGracesJapanese.execute("SELECT debug FROM Japanese where ID=?", (entry[1],))
            
                try:
                    if Globals.CursorGracesJapanese.fetchall()[0][0] == 1:
                        UpdateCur.execute("UPDATE Text SET status=-1 WHERE ID=? AND status != -1", (entry[0],))
                    else:
                        if entry[2] == -1:
                            UpdateCur.execute("UPDATE Text SET status = 0 WHERE ID=? AND status != 0", (entry[0],))
                except:
                    pass
                        
            UpdateCon.commit()

        Globals.MainWindow.displayStatusMessage( 'Consolidate Debug Finished!' )
        Globals.Cache.databaseAccessRLock.release()

    def PropagateDebugDatabases2GJ(self):
        self.WriteDatabaseStorageToHdd()
        
        # Applies the debug status in Databases to GracesJapanese
        Globals.MainWindow.displayStatusMessage( 'Consolidate Debug: Individual Databases -> GracesJapanese' )
        
        Globals.Cache.databaseAccessRLock.acquire()

        for filename in Globals.configData.FileList:

            Globals.MainWindow.displayStatusMessage( "Consolidate Debug: Processing: {0}".format(filename) )
            
            UpdateCon = DatabaseHandler.OpenEntryDatabase(filename)
            UpdateCur = UpdateCon.cursor()
                        
            UpdateCur.execute("SELECT StringID FROM Text WHERE status = -1")
                
            for entry in UpdateCur.fetchall():
                Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 1 WHERE ID=?", (entry[0],))
            UpdateCon.rollback()
                
        Globals.ConnectionGracesJapanese.commit()
        Globals.MainWindow.displayStatusMessage( 'Consolidate Debug Finished!' )
        Globals.Cache.databaseAccessRLock.release()

    # fills in the database list to the left
    def PopulateDatabaseView(self, fileTree):
        self.WriteDatabaseStorageToHdd()
        
        self.databaseTreeModel.clear()
        
        PercentageConnection, PercentageCursor = DatabaseHandler.GetCompletionPercentageConnectionAndCursor()
        
        def AddCategory( category, parent ):
            categoryItem = QtGui.QStandardItem( category.Name )
            categoryItem.setEditable( False )
            parent.appendRow( categoryItem )
            categoryPhase = Globals.configData.TranslationStagesCountMaximum
            
            for db in category.Data:
                if db.IsCategory:
                    newCatPhase = AddCategory( db, categoryItem )
                    categoryPhase = min( newCatPhase, categoryPhase )
                else:
                    dbItem = QtGui.QStandardItem()
                    dbItem.DatabaseTreeNode = db
                    dbItem.setStatusTip( db.Name )
                    dbItem.setEditable( False )
                    dbPhase = self.FormatDatabaseListItem( dbItem, PercentageCursor = PercentageCursor )
                    categoryPhase = min( dbPhase, categoryPhase )
                    categoryItem.appendRow( dbItem )

            categoryItem.setText( '[' + str(categoryPhase) + '] ' + category.Name )
            if categoryPhase >= self.role:
                categoryItem.setBackground( QtGui.QBrush( Globals.ColorCurrentStatus ) )

            return categoryPhase
        
        for category in fileTree.Data:
            AddCategory( category, self.databaseTreeModel )

    def FormatDatabaseListItem(self, treeItem, PercentageCursor = None):
        databaseName = treeItem.DatabaseTreeNode.Name
        databaseDescription = treeItem.DatabaseTreeNode.Desc
        completionDbName = CompletionTable.GetCompletionTableDatabaseNameOfTreeNode( treeItem.DatabaseTreeNode )

        if PercentageCursor is None:
            PercentageConnection, PercentageCursor = DatabaseHandler.GetCompletionPercentageConnectionAndCursor()

        if databaseDescription is None:
            databaseDescription = Globals.GetDatabaseDescriptionString(databaseName)
        treeItem.setText(databaseDescription)

        PercentageCursor.execute("SELECT Count(1) FROM StatusData WHERE Database = ?", [completionDbName])
        exists = PercentageCursor.fetchall()[0][0]
        dbPhase = 0
        if exists > 0:
            PercentageCursor.execute("SELECT type, amount FROM StatusData WHERE Database = ?", [completionDbName])
            rows = PercentageCursor.fetchall()

            # type == 0 -> non-debug linecount, type == -2 -> comment count, otherwise type == status
            data = {}
            for row in rows:
                type = row[0]
                data[type] = row[1]

            linecountTotal = data[0]
            linecountCurrentStage = data[self.role]
            commentAmount = data[-2]
                    
            if linecountCurrentStage >= linecountTotal:
                treeItem.setBackground(QtGui.QBrush( Globals.ColorCurrentStatus ));
            else:
                treeItem.setBackground(QtGui.QBrush( Globals.ColorLowerStatus ));

            # figure out the minimum status of all entries in the DB
            for i in range(1, Globals.configData.TranslationStagesCount + 1):
                try:
                    if linecountTotal == data[i]:
                        dbPhase += 1
                except KeyError:
                    pass

            if commentAmount > 0:
                treeItem.setText('[' + str(dbPhase) + 'c] ' + treeItem.text())
            else:
                treeItem.setText('[' + str(dbPhase) + '  ] ' + treeItem.text())
        
        return dbPhase

    def FormatEntryListItemColor(self, item, status):
        if status == -1:
            item.setBackground(QtGui.QBrush(QtGui.QColor(255, 220, 220)))
        elif status >= self.role:
            item.setBackground(QtGui.QBrush( Globals.ColorCurrentStatus ))
        else:
            item.setBackground(QtGui.QBrush( Globals.ColorLowerStatus ))

    def StoreWidthsOfEntryList(self):
        widths = [self.entryTreeView.columnWidth(index) for index in range(len(self.entryTreeViewHeaderWidths))]
        self.entryTreeViewHeaderWidths = widths
        self.entryTreeViewHeaderState = self.entryTreeView.header().saveState()

    # fills in the entry list to the right        
    def PopulateEntryList(self):
        self.WriteDatabaseStorageToHdd()
        
        containsComments = False
    
        if self.fontWindow:
            self.fontWindow.clearInfo()

        for editbox in self.xTextBoxesENG:
            editbox.iconToggle(0)

        if self.entryTreeViewHeaderWidths is None:
            self.entryTreeViewHeaderWidths = self.entryTreeViewHeaderWidthsDefaults[:] # copy list
        
        if self.entryTreeViewHasBeenFilledOnce:
            self.StoreWidthsOfEntryList()
        self.entryTreeViewHasBeenFilledOnce = True

        self.entryStandardItemModel.clear()
        self.entryStandardItemModel.setColumnCount(9)
        self.entryStandardItemModel.setHorizontalHeaderLabels(self.entryTreeViewHeaderLabels)
        if self.entryTreeViewHeaderState is not None:
            self.entryTreeView.header().restoreState(self.entryTreeViewHeaderState)
        self.entryTreeView.header().setStretchLastSection(True)
        for i in xrange( len(self.entryTreeViewHeaderWidths) ):
            self.entryTreeView.setColumnWidth( i, self.entryTreeViewHeaderWidths[i] )
        for i in xrange( len(self.entryTreeViewHeaderLabels) ):
            self.entryTreeView.setColumnHidden( i, self.entryTreeViewHeadersVisible[i] == False )

        self.currentOpenedEntryIndexes = None
        
        self.text = {}

        for editbox in self.xTextBoxesENG:
            editbox.setText('')
        for txtttle in self.textEditingTitles:
            txtttle.setText('')
        for footer in self.textEditingFootersENG:
            footer.setText('')
        for footer in self.textEditingFootersJPN:
            footer.setText('')

        # refresh the string & color in the list to the left of the entry we just changed from
        if self.currentTreeIndex is not None:
            treeItem = self.databaseTreeModel.itemFromIndex(self.currentTreeIndex)
            self.FormatDatabaseListItem( treeItem )

        index = self.databaseTreeView.currentIndex()
        if index is None:
            return

        itemFromIndex = self.databaseTreeModel.itemFromIndex(index)
        if itemFromIndex is None:
            return

        databasefilename = itemFromIndex.statusTip()
        parent = self.databaseTreeModel.data(index.parent())
        if self.databaseTreeModel.hasChildren(index):
            self.currentTreeIndex = None
            return


        Globals.Cache.databaseAccessRLock.acquire()

        self.currentTreeIndex = index
        self.currentlyOpenDatabase = str(databasefilename)
        SaveCon = DatabaseHandler.OpenEntryDatabase(databasefilename)
        SaveCur = SaveCon.cursor()
        
        SaveCur.execute('SELECT ID, StringID, english, comment, updated, status, IdentifyString, UpdatedBy, UpdatedTimestamp FROM Text ORDER BY ID ASC')
        TempList = SaveCur.fetchall()

        SaveCur.execute('SELECT ID, english, comment, status, UpdatedBy, UpdatedTimestamp FROM History ORDER BY ID ASC, UpdatedTimestamp DESC')
        HistoryList = SaveCur.fetchall()
        SaveCur.execute('SELECT MAX(ID) FROM Text')
        MaxId = SaveCur.fetchall()[0][0]
        if MaxId is None:
            MaxId = 0
        self.historyWindow.setHistoryList(HistoryList, MaxId, TempList)

        def inSubsection(i, subsections):
            for sec in subsections:
                if i >= sec.Start and i <= sec.End:
                    return True
            return False

        subsections = itemFromIndex.DatabaseTreeNode.Subsections
        debugButtonChecked = self.debugOnOffButton.isChecked()
        for i in xrange(len(TempList)):
            if subsections and not inSubsection(i + 1, subsections):
                continue

            Globals.CursorGracesJapanese.execute("SELECT string, debug FROM Japanese WHERE ID={0}".format(TempList[i][1]))
            TempString = Globals.CursorGracesJapanese.fetchall() 
            TempJPN = TempString[0][0]
            TempDebug = TempString[0][1]

            alternateOriginalLanguageStrings = []
            for j in range( 1, len( Globals.ConnectionsOriginalDatabases ) ):
                conn = Globals.ConnectionsOriginalDatabases[j]
                cur = conn.cursor()
                cur.execute( "SELECT string FROM Japanese WHERE ID={0}".format( TempList[i][1] ) )
                data = cur.fetchone()
                if data:
                    alternateOriginalLanguageStrings.append( data[0] )

            TempENG = TempList[i][2]
            TempCOM = TempList[i][3]
            TempStatus = TempList[i][5]
            TempIdentifyString = str(TempList[i][6])
            TempUpdatedBy = TempList[i][7]
            TempUpdatedTimestamp = TempList[i][8]
            TempID = TempList[i][0]

            if TempENG == '' or TempENG == None:
                TempENG = TempJPN
            if TempUpdatedBy is None:
                TempUpdatedBy = '[None]'
            if TempUpdatedTimestamp is not None:
                TempUpdatedTimestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(TempUpdatedTimestamp))
            else:
                TempUpdatedTimestamp = '0000-00-00 00:00:00'
            
            if TempCOM == None:
                TempCOM = ''

            commentString = ''
            if TempCOM != '':
                containsComments = True
                commentString = 'C'

            # change database entry status if it mismatches the GracesJapanese Debug status
            if TempStatus != -1 and TempDebug == 1: # GracesJapanese says Debug, change DB to match
                Globals.MainWindow.displayStatusMessage("Setting status of " + databasefilename + ", Entry " + str(TempID) + " to Debug (StringID: " + str(TempList[i][1]) + ")")
                SaveCur.execute("UPDATE Text SET status=-1, updated=1 WHERE ID=?", (TempID,))
                SaveCon.commit()
                TempStatus = -1
            elif TempStatus == -1 and TempDebug == 0: # Graces Japanese says not Debug, change DB to match
                Globals.MainWindow.displayStatusMessage("Setting status of " + databasefilename + ", Entry " + str(TempID) + " to Not Debug (StringID: " + str(TempList[i][1]) + ")")
                SaveCur.execute("UPDATE Text SET status=0, updated=1 WHERE ID=?", (TempID,))
                SaveCon.commit()
                TempStatus = 0

            entryDisplayString = Globals.VariableReplace( TempENG.replace('\f', ' ').replace('\n', ' ') )
            commentDisplayString = Globals.VariableReplace( TempCOM.replace('\f', ' ').replace('\n', ' ') )
                        
            additemEntryEnglishID = QtGui.QStandardItem(str(TempID))
            additemEntryEnglishID.setStatusTip(TempIdentifyString)
            additemEntryEnglishID.GraceNoteEntryId = i+1
            additemEntryEnglishID.setEditable(False)
            additemEntryStatus = QtGui.QStandardItem(str(TempStatus))
            additemEntryStatus.setEditable(False)
            additemEntryText = QtGui.QStandardItem(entryDisplayString)
            additemEntryText.setEditable(False)
            additemEntryIdentifyString = QtGui.QStandardItem(TempIdentifyString)
            additemEntryIdentifyString.setEditable(False)
            additemEntryCommentExists = QtGui.QStandardItem(commentString)
            additemEntryCommentExists.setEditable(False)
            additemEntryTimestamp = QtGui.QStandardItem(str(TempUpdatedTimestamp))
            additemEntryTimestamp.setEditable(False)
            additemEntryUpdatedBy = QtGui.QStandardItem(str(TempUpdatedBy))
            additemEntryUpdatedBy.setEditable(False)
            additemEntryIsDebug = QtGui.QStandardItem('')
            additemEntryIsDebug.setCheckable(True)
            additemEntryIsDebug.setEditable(False)
            additemEntryCommentText = QtGui.QStandardItem(commentDisplayString)
            additemEntryCommentText.setEditable(False)
    
            self.FormatEntryListItemColor(additemEntryStatus, TempStatus)        
            self.FormatEntryListItemColor(additemEntryText, TempStatus)        
            self.FormatEntryListItemColor(additemEntryIdentifyString, TempStatus)        
            self.FormatEntryListItemColor(additemEntryCommentExists, TempStatus)        
            self.FormatEntryListItemColor(additemEntryTimestamp, TempStatus)        
            self.FormatEntryListItemColor(additemEntryUpdatedBy, TempStatus)        
            self.FormatEntryListItemColor(additemEntryIsDebug, TempStatus)        
            self.FormatEntryListItemColor(additemEntryEnglishID, TempStatus)        
            self.FormatEntryListItemColor(additemEntryCommentText, TempStatus)        
    
            if TempDebug == 1 and debugButtonChecked:
                additemEntryIsDebug.setCheckState(QtCore.Qt.Checked)
                additemEntryIsDebug.DebugStatus = True
                self.entryStandardItemModel.appendRow([additemEntryEnglishID, additemEntryStatus, additemEntryCommentExists, additemEntryIdentifyString, additemEntryText, additemEntryCommentText, additemEntryUpdatedBy, additemEntryTimestamp, additemEntryIsDebug])
            elif TempDebug == 1 and not debugButtonChecked:
                pass
            else:
                additemEntryIsDebug.DebugStatus = False
                self.entryStandardItemModel.appendRow([additemEntryEnglishID, additemEntryStatus, additemEntryCommentExists, additemEntryIdentifyString, additemEntryText, additemEntryCommentText, additemEntryUpdatedBy, additemEntryTimestamp, additemEntryIsDebug])
                
            self.text[i] = {
                'eng': TempENG,
                'jpn': TempJPN,
                'com': TempCOM,
                'debug': TempDebug,
                'status': TempStatus,
                'ident': TempIdentifyString,
                'alts': alternateOriginalLanguageStrings,
            }
            
        Globals.commentsAvailableLabel.setText(databasefilename)
            
        if self.entrySortFilterProxyModel.rowCount() != 1:
            index = self.entrySortFilterProxyModel.index(1, 0)
        else:
            index = self.entrySortFilterProxyModel.index(0, 0)
        self.entryTreeView.setCurrentIndex(index)
        self.entryTreeView.selectionModel().select(index, QtGui.QItemSelectionModel.SelectionFlags(3))

        Globals.Cache.databaseAccessRLock.release()

    def FormatCurrentlyOpenedEntryIndexes(self):
        if self.currentOpenedEntryIndexes is not None:
            for i, idx in enumerate(self.currentOpenedEntryIndexes):
                if idx is not None:
                    self.ReformatEntryInEntryList(idx.row(), i)
        return

    def ReformatEntryInEntryList(self, entryListRow, entryBoxNumber):
        textBox = self.xTextBoxesENG[entryBoxNumber]
        textEntry = self.text[textBox.currentEntry - 1]
        for i in range( len( self.entryTreeViewHeaderLabels ) ):
            item = self.entryStandardItemModel.item( entryListRow, i )
            self.FormatEntryListItemColor( item, textEntry['status'] )

        itemStatus = self.entryStandardItemModel.item( entryListRow, 1 )
        itemCommentExists = self.entryStandardItemModel.item( entryListRow, 2 )
        itemText = self.entryStandardItemModel.item( entryListRow, 4 )
        itemCommentText = self.entryStandardItemModel.item( entryListRow, 5 )
        itemUpdatedBy = self.entryStandardItemModel.item( entryListRow, 6 )
        itemTimestamp = self.entryStandardItemModel.item( entryListRow, 7 )

        entryDisplayString = Globals.VariableReplace( textEntry['eng'].replace('\f', ' ').replace('\n', ' ') )
        commentDisplayString = Globals.VariableReplace( textEntry['com'].replace('\f', ' ').replace('\n', ' ') )

        itemStatus.setText( str(textEntry['status']) )
        itemCommentExists.setText( '' if commentDisplayString == '' else 'C' )
        itemText.setText( entryDisplayString )
        itemCommentText.setText( commentDisplayString )
        #itemUpdatedBy.setText()
        #itemTimestamp.setText()

        return

    # fills in the textboxes in the middle
    def PopulateTextEdit(self):
        if Globals.WriteDatabaseStorageToHddOnEntryChange:
            self.WriteDatabaseStorageToHdd()
                
        index = self.entryTreeView.currentIndex()
        row = index.row()

        if index == None or row == -1:
            return
        
        commentTexts = []
        for i in range(len(self.textEditingBoxes)):
            commentTexts.append('')

        self.FormatCurrentlyOpenedEntryIndexes()

        # boxes here
        rowBoxes = []
        self.currentOpenedEntryIndexes = []
        for i in range(len(self.textEditingBoxes)):
            try:
                idx = self.entrySortFilterProxyModel.index(index.row()+(i-1), index.column())
                a = self.entryStandardItemModel.index(index.row()+(i-1), index.column())
                b = self.entrySortFilterProxyModel.index(a.row(), 0)
                d = self.entrySortFilterProxyModel.mapToSource(b)
                c = self.entryStandardItemModel.itemFromIndex(d)
                entryitem = c
                entrytextdisplay = self.entrySortFilterProxyModel.data(idx)

                if entrytextdisplay != None:
                    rowBoxes.append( entryitem.GraceNoteEntryId - 1 )
                    self.currentOpenedEntryIndexes.append( d )
                else:
                    rowBoxes.append( -2 )
                    self.currentOpenedEntryIndexes.append( None )
            except:
                rowBoxes.append( -2 )
                self.currentOpenedEntryIndexes.append( None )
        
        textEntriesEng = []
        for i in range(len(self.textEditingBoxes)):
            if rowBoxes[i] >= 0:
                textEntry = self.text[rowBoxes[i]]
                textEntriesEng.append( Globals.VariableReplace(textEntry['eng']) )
                self.xTextBoxesJPN[i].setText( Globals.VariableReplace(textEntry['jpn']) )
                self.xTextBoxesCOM[i].setText( Globals.VariableReplace(textEntry['com']) )
                self.xTextBoxesENG[i].refreshFooter(textEntry['eng'], 'E: ')
                self.xTextBoxesJPN[i].refreshFooter(textEntry['jpn'], 'J: ')
                commentTexts[i] = textEntry['ident'] + '     '
                self.xTextBoxesENG[i].iconToggle(textEntry['status'])
                self.xTextBoxesENG[i].currentEntry = rowBoxes[i] + 1
                self.xTextBoxesJPN[i].currentEntry = rowBoxes[i] + 1
                self.xTextBoxesCOM[i].currentEntry = rowBoxes[i] + 1
                self.xTextBoxesENG[i].setReadOnly(False)
                self.xTextBoxesJPN[i].setReadOnly(True)
                self.xTextBoxesCOM[i].setReadOnly(False)
                for j, tb in enumerate( self.xTextBoxesOrigLangs[i] ):
                    try:
                        tb.setText( Globals.VariableReplace( textEntry['alts'][j] ) )
                    except IndexError:
                        tb.setText( '' )
                        pass
                    tb.currentEntry = rowBoxes[i] + 1
                    tb.setReadOnly(True)
            else:
                textEntriesEng.append( '' )
                self.xTextBoxesJPN[i].setText( '' )
                self.xTextBoxesCOM[i].setText( '' )
                self.xTextBoxesENG[i].clearFooter()
                self.xTextBoxesJPN[i].clearFooter()
                self.xTextBoxesENG[i].iconToggle(0)
                self.xTextBoxesENG[i].currentEntry = -1
                self.xTextBoxesJPN[i].currentEntry = -1
                self.xTextBoxesCOM[i].currentEntry = -1
                self.xTextBoxesENG[i].setReadOnly(True)
                self.xTextBoxesJPN[i].setReadOnly(True)
                self.xTextBoxesCOM[i].setReadOnly(True)
                for tb in self.xTextBoxesOrigLangs[i]:
                    tb.setText( '' )
                    tb.currentEntry = -1
                    tb.setReadOnly(True)

        # audio clip check
        if Globals.Audio:
            lengthEditingBoxes = len(self.textEditingBoxes)
            for i in range(lengthEditingBoxes):
                if self.xTextBoxesENG[i].currentEntry == -1:
                    continue
                audioTextBox = self.text.get(rowBoxes[i] + Globals.configData.VoiceEntryOffset)
                if not audioTextBox:
                    continue
                AudioSearchText = Globals.VariableReplace(audioTextBox['eng'])
                AudioClips = re.findall('<Audio: (.*?)>', AudioSearchText, re.DOTALL)
                AudioClips = AudioClips + re.findall('<Voice: (.*?)>', AudioSearchText, re.DOTALL)
                if AudioClips == []:
                    self.xTextBoxesENG[i].clearPlaybackButtons()
                else:
                    self.xTextBoxesENG[i].makePlaybackButtons(AudioClips)

        # check for terms
        lengthEditingBoxes = len(self.textEditingBoxes)
        self.termTooltips = []
        for i in range(lengthEditingBoxes):
            if rowBoxes[i] >= 0:
                japanese = self.text[rowBoxes[i]]['jpn']
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
            textEntry = self.text.get(rowBoxes[centerPanel] + medium.medium.offs)
            if textEntry:
                medium.refreshInfo( Globals.VariableReplace(textEntry['eng']) )

        # inform font box
        databasefilename = self.databaseTreeModel.itemFromIndex(self.databaseTreeView.currentIndex()).statusTip()
        self.fontWindow.drawText( self.text[rowBoxes[centerPanel]]['eng'], self.text[rowBoxes[centerPanel]]['jpn'], Globals.GetDatabaseDescriptionString(str(databasefilename)) )

        # inform history window
        self.historyWindow.displayHistoryOfEntry(self.xTextBoxesENG[centerPanel].currentEntry)
                    
        # put text into textboxes, display entry number
        for i in range(len(self.textEditingBoxes)):
            self.xTextBoxesENG[i].setText(textEntriesEng[i])
                
            if self.xTextBoxesENG[i].currentEntry >= 0:
                self.textEditingTitles[i].setText('Entry {0}: {1}'.format(rowBoxes[i]+1, commentTexts[i]))
                if self.termTooltips[i] != '':
                    self.textEditingTermIcons[i].setToolTip( 'Terminology in this Entry:\n' + self.termTooltips[i] )
                    self.textEditingTermIcons[i].show()
                else:
                    self.textEditingTermIcons[i].setToolTip('')
                    self.textEditingTermIcons[i].hide()

                if textEntriesEng[i].count('<') != textEntriesEng[i].count('>'):
                    self.textEditingWarningIcons[i].setToolTip('WARNING: It looks like there\'s a broken variable or control code in this entry.')
                    self.textEditingWarningIcons[i].show()
                else:
                    self.textEditingWarningIcons[i].setToolTip('')
                    self.textEditingWarningIcons[i].hide()
            else:
                self.textEditingTitles[i].setText('')
                self.textEditingFootersENG[i].setText('')
                self.textEditingFootersJPN[i].setText('')
                self.textEditingTermIcons[i].setToolTip('')
                self.textEditingTermIcons[i].hide()
                self.textEditingWarningIcons[i].setToolTip('')
                self.textEditingWarningIcons[i].hide()
            

        # auto-update in Auto mode
        if Globals.ModeFlag == 'Auto':
            for i in range(len(self.textEditingBoxes)):
                self.xTextBoxesENG[i].manualEdit.emit(-2, self.xTextBoxesENG[i], self.textEditingFootersENG[i])


        
    def GetFullText(self, replaceVariables, dumpEnglish=True, dumpJapanese=False, dumpComments=False, seperator='\n', entrySeperator='\n\n\n'):
        string = ''
        i = 1
        textToDump = []
        if dumpJapanese:
            textToDump.append('jpn')
        if dumpEnglish:
            textToDump.append('eng')
        if dumpComments:
            textToDump.append('com')

        for entry in self.text.itervalues():
            if entry['debug'] == 0 or self.debugOnOffButton.isChecked():
                string = string + '{0}'.format(i) # entry id
                string = string + seperator + entry['ident']
                string = string + seperator + str(entry['status'])
                string = string + seperator

                currentEntryString = ''
                for type in textToDump:
                    txt = (entry[type] if not replaceVariables else Globals.VariableReplace(entry[type])).replace('\n','').replace('\r', '')
                    currentEntryString = currentEntryString + txt + seperator

                string = string + currentEntryString + entrySeperator
            
            i += 1
        return string

    def FullTextCopy(self):
        string = self.GetFullText(True, self.TextboxVisibleFlagEnglish, self.TextboxVisibleFlagJapanese, self.TextboxVisibleFlagComment)
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(string)
        return

    def JumpToDatabase(self):
        jumpto = self.jumpToTextbox.text()
        self.JumpToEntry(jumpto, 0)
    
    def LiveSearch(self):
        self.WriteDatabaseStorageToHdd()
        
        matchString = self.liveSearchTextbox.text()

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


        
        for File in Globals.configData.FileList:
            data = Globals.Cache.GetDatabase(File)
            if self.debugOnOffButton.isChecked():
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
        
        popup_menu.exec_(self.liveSearchTextbox.mapToGlobal(QtCore.QPoint(0,self.liveSearchTextbox.height())))


    def JumpToEntry(self, databaseName, entry):
        self.WriteDatabaseStorageToHdd()
        entry = int(entry)
        if databaseName == '':
            return

        def SearchCategory( category ):
            for p in xrange(category.rowCount()):
                child = category.child(p)
                try:
                    dbNode = child.DatabaseTreeNode
                    if dbNode.Name == databaseName:
                        # if the database is a subsectioned one, also make sure the requested entry is in this subsection
                        if not dbNode.ContainsEntry(entry):
                            continue

                        # found correct database, expand
                        treeExpand = self.databaseTreeModel.indexFromItem(category)
                        self.databaseTreeView.expand(treeExpand)

                        # and select
                        treeIndex = self.databaseTreeModel.indexFromItem(category.child(p))
                        self.databaseTreeView.setCurrentIndex(treeIndex)
                        self.databaseTreeView.selectionModel().select(treeIndex, QtGui.QItemSelectionModel.SelectionFlags(3))

                        # select requested entry
                        try:
                            for i in xrange(self.entryStandardItemModel.rowCount()):
                                item = self.entryStandardItemModel.item(i, 0)
                                if item.GraceNoteEntryId == entry:
                                    entryIndex = self.entryStandardItemModel.indexFromItem(item)
                                    sortIndex = self.entrySortFilterProxyModel.mapFromSource(entryIndex)
                                    self.entryTreeView.setCurrentIndex(sortIndex)
                                    self.entryTreeView.selectionModel().select(sortIndex, QtGui.QItemSelectionModel.SelectionFlags(3))
                                    break
                        except:
                            pass

                        return True

                except AttributeError:
                    # I don't think this is the best way to handle that honestly
                    # but if this happens this is a category node
                    if SearchCategory( child ):
                        return True

            return False

        for i in xrange(self.databaseTreeModel.rowCount()):
            category = self.databaseTreeModel.item(i)
            if SearchCategory( category ):
                return


    def DebugFilter(self, bool):
        self.PopulateEntryList()
        if bool:
            self.debugOnOffButton.setIcon(QtGui.QIcon('icons/debugon.png'))
        else:
            self.debugOnOffButton.setIcon(QtGui.QIcon('icons/debugoff.png'))
        
    def AlwaysOnTopToggle(self, enabled):
        if enabled:
            self.parent.setWindowFlags(self.parent.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.parent.setWindowFlags(self.parent.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        self.parent.show()
    
    def ShowChangelog(self):
        item = self.databaseTreeModel.itemFromIndex(self.databaseTreeView.currentIndex())
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

    def ShowMassSpellcheck(self):
        self.WriteDatabaseStorageToHdd()
        
        if not self.massSpellcheckDialogOpened:
            self.massSpellcheckDialog = MassSpellcheck(self)
            self.massSpellcheckDialogOpened = True
        self.massSpellcheckDialog.show()
        self.massSpellcheckDialog.raise_()
        self.massSpellcheckDialog.activateWindow()

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

    def RefreshCompletionDatabase(self):
        self.WriteDatabaseStorageToHdd()
        
        CompletionTable.CalculateAllCompletionPercentagesForDatabase()

    def PlayCentralAudio(self):
        self.xTextBoxesENG[1].playAudio()

    def FormatCentralTextMatchJapaneseWidth(self):
        self.FormatCentralText(FontDisplayWindow.FontFormattingModes.MaximumWidth_AnyLinecount)
    def FormatCentralTextAllowExceedWidth(self):
        self.FormatCentralText(FontDisplayWindow.FontFormattingModes.AllowExceedWidth_MaximumLinecount)
    def FormatCentralTextMatchJapaneseLinecountAsBlock(self):
        self.FormatCentralText(FontDisplayWindow.FontFormattingModes.AutoWidth_ExactLinecount)

    def FormatCentralText(self, mode):
        font = Globals.configData.Fonts['default']
        unformattedText = Globals.VariableRemove(self.xTextBoxesENG[1].toPlainText())
        jpnText = Globals.VariableRemove(self.xTextBoxesJPN[1].toPlainText())

        engTextSplit = unformattedText.split('\f')
        jpnTextSplit = jpnText.split('\f')

        if len(engTextSplit) != len(jpnTextSplit):
            self.parent.displayStatusMessage('<Feed> count inconsistent between English and Japanese, can\'t format.')
            return

        formattedTextSplit = []
        for i in range(len(engTextSplit)):
            width = FontDisplayWindow.renderText(Globals.configData.ReplaceInGameString(jpnTextSplit[i]), None, 1, font)[0]
            linecount = jpnTextSplit[i].count('\n') + 1

            formattedText = FontDisplayWindow.formatText(engTextSplit[i], font, width, linecount, mode)
            formattedTextSplit.append( formattedText )

        self.xTextBoxesENG[1].setText( Globals.VariableReplace( '\f'.join(formattedTextSplit) ) )
        self.xTextBoxesENG[1].manualEdit.emit( -1, self.xTextBoxesENG[1], self.textEditingFootersENG[1] )

    def SetCentralAsClosure(self, status):
        def callFunc():
            self.SetCentralAs(status)
        return callFunc
    def SetCentralAs(self, status):
        self.xTextBoxesENG[1].manualEdit.emit(status, self.xTextBoxesENG[1], self.textEditingFootersENG[1])
        
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
                self.entryTreeView.setColumnWidth(i, self.entryTreeViewHeaderWidthsDefaults[i])
                # make sure people don't disable all sections
                if self.entryTreeView.header().hiddenSectionCount() == self.entryTreeView.header().count():
                    self.entryTreeView.setColumnHidden(i, False)

        for i in xrange( len(menuOptions) ):
            self.entryTreeViewHeadersVisible[i] = self.entryTreeView.header().isSectionHidden(i) == False

        return

    def UpdateDebug(self, additemEntryIsDebug):
        try:
            if additemEntryIsDebug.checkState() == 0:
                if additemEntryIsDebug.DebugStatus == False:
                    return # no change, was already not debug
                DebugState = False
            else:
                if additemEntryIsDebug.DebugStatus == True:
                    return # no change, was already debug
                DebugState = True
        except: # item is not the debug checkbox item, might be a better way to do this (.whatsThis()?) but this should work
            return
        
        index = self.entryStandardItemModel.indexFromItem(additemEntryIsDebug)

        self.WriteDatabaseStorageToHdd()
        
        Globals.Cache.databaseAccessRLock.acquire()

        selectedEntryId = self.entryStandardItemModel.item(index.row(), 0).GraceNoteEntryId - 1
        databasefilename = self.databaseTreeModel.itemFromIndex(self.databaseTreeView.currentIndex()).statusTip()
        SaveCon = DatabaseHandler.OpenEntryDatabase(databasefilename)
        SaveCur = SaveCon.cursor()
        SaveCur.execute("SELECT StringID FROM Text WHERE ID={0}".format(selectedEntryId+1))
        NextID = SaveCur.fetchall()[0][0]
        if DebugState:
            Globals.MainWindow.displayStatusMessage('Setting Entry ' + str(selectedEntryId+1) + ' to Debug')
            Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 1 WHERE ID = {0} AND debug != 1".format(NextID))
            SaveCur.execute("UPDATE Text SET status = -1, updated = 1 WHERE ID = {0} AND status != -1".format(selectedEntryId+1))
            additemEntryIsDebug.DebugStatus = True
        else:
            Globals.MainWindow.displayStatusMessage('Setting Entry ' + str(selectedEntryId+1) + ' to Not Debug')
            Globals.CursorGracesJapanese.execute("UPDATE Japanese SET debug = 0 WHERE ID = {0} AND debug != 0".format(NextID))
            SaveCur.execute("UPDATE Text SET status =  0, updated = 1 WHERE ID = {0} AND status  = -1".format(selectedEntryId+1))
            additemEntryIsDebug.DebugStatus = False
        self.AddDatabaseToUpdateSet(str(databasefilename))
        SaveCon.commit()
        Globals.ConnectionGracesJapanese.commit()
        
        # color
        SaveCur.execute("SELECT status FROM Text WHERE ID={0}".format(selectedEntryId+1))
        status = SaveCur.fetchall()[0][0]
        for i in xrange( len(self.entryTreeViewHeaderLabels) ):
            self.FormatEntryListItemColor( self.entryStandardItemModel.item(index.row(), i), status )

        Globals.Cache.databaseAccessRLock.release()

    def DebugPrintDatabaseWriteStorage(self):
        for d in self.databaseWriteStorage:
            print("current contents: " + d.databaseName + "/" + str(d.entry) + ": " + d.cleanString)
    
    def AddDatabaseToUpdateSet(self, databasename):
        if not Globals.HaveUnsavedChanges:
            Globals.HaveUnsavedChanges = True
            self.SetWindowTitle()
        self.update.add(databasename)
        return

    def ClearUpdateSet(self):
        self.update.clear()
        return
    
    def InsertOrUpdateEntryToWrite(self, entryStruct):
        if not Globals.HaveUnsavedChanges:
            Globals.HaveUnsavedChanges = True
            self.SetWindowTitle()

        #UpdatedDatabaseEntry(cleanString, commentString, databaseName, entry, role, state)
        for i, d in enumerate(self.databaseWriteStorage):
            if d.entry == entryStruct.entry and d.databaseName == entryStruct.databaseName:
                if i != 0:
                #    print("found existing, rotating & removing old")
                    self.databaseWriteStorage.rotate(-i)
                #else:
                #    print("found existing, removing old")
                oldEntry = self.databaseWriteStorage.popleft()

                # copy over the just popped entry's english or comment, whatever is not being updated
                # so we're not losing important content from the popped entry
                if entryStruct.cleanString is None:
                    entryStruct.cleanString = oldEntry.cleanString
                if entryStruct.commentString is None:
                    entryStruct.commentString = oldEntry.commentString
                break
        self.databaseWriteStorage.appendleft(entryStruct) # doesn't exist in list yet, just add new
        #print("added new: " + entryStruct.databaseName + "/" + str(entryStruct.entry) + ": " + entryStruct.cleanString)
        #self.DebugPrintDatabaseWriteStorage()
        return
    
    def UpdateTextGenericFunc(self, role, textBox, footer):
        if textBox.currentEntry < 0:
            return
            
        treeindex = self.databaseTreeView.currentIndex()
        if self.databaseTreeModel.hasChildren(treeindex):
            return
        
        CommandOriginAutoMode = ( role == -2 )
        currentDatabaseStatus = self.text[textBox.currentEntry - 1]['status']

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
        
        updateStatusValue = self.FigureOutNewStatusValue(role, currentDatabaseStatus, textBox.contentType, CommandOriginButton, CommandOriginAutoMode)

        self.text[textBox.currentEntry - 1]['status'] = updateStatusValue
        if textBox.contentType == 'ENG':
            textBox.iconToggle(updateStatusValue)
        
        databasefilename = self.databaseTreeModel.itemFromIndex(self.databaseTreeView.currentIndex()).statusTip()
        
        #UpdatedDatabaseEntry(cleanString, databaseName, entry, role, state)
        # keep for later write to HDD
        if textBox.contentType == 'ENG':
            self.InsertOrUpdateEntryToWrite(DatabaseCache.UpdatedDatabaseEntry(GoodString, None, databasefilename, textBox.currentEntry, updateStatusValue))
        elif textBox.contentType == "COM":
            self.InsertOrUpdateEntryToWrite(DatabaseCache.UpdatedDatabaseEntry(None, GoodString, databasefilename, textBox.currentEntry, updateStatusValue))
        else:
            Globals.MainWindow.displayStatusMessage("ERROR: Couldn't update entry, ContentState is neither English nor Comment!")
            return
        textBox.refreshFooter(GoodString, textBox.contentType + ': ')

        self.ReStartTimeoutTimer()
        
        # write the new string back into the main window, this is neccessary or else the new string isn't there when the displayed entry is changed!
        if textBox.contentType == 'ENG':
            self.text[textBox.currentEntry - 1]['eng'] = GoodString
        elif textBox.contentType == "COM":
            self.text[textBox.currentEntry - 1]['com'] = GoodString
        
        # should probably make this optional
        if not CommandOriginAutoMode and textBox.contentType == 'ENG':
            self.fontWindow.drawText( GoodString, self.text[textBox.currentEntry - 1]['jpn'], Globals.GetDatabaseDescriptionString(str(databasefilename)) )

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
    
        Globals.Cache.databaseAccessRLock.acquire()

        lastDatabase = ""
        
        Globals.MainWindow.displayStatusMessage("Writing database storage in memory to HDD...")
        
        # sort by time of entry creation so order of inserts is preserved (necessary eg. if changing both english and comment on same entry
        sortedStorage = sorted(self.databaseWriteStorage, key=lambda UpdatedDatabaseEntry: UpdatedDatabaseEntry.timestamp)
        
        databasesWrittenTo = set()

        #UpdatedDatabaseEntry(cleanString, commentString, databaseName, entry, role, state)
        SaveCon = None
        for d in sortedStorage:
            if lastDatabase != d.databaseName: # open up new DB connection if neccesary, otherwise just reuse the old one
                if SaveCon is not None:
                    SaveCon.commit()
                self.AddDatabaseToUpdateSet(str(d.databaseName))
                SaveCon = DatabaseHandler.OpenEntryDatabase(d.databaseName)
                SaveCur = SaveCon.cursor()
                lastDatabase = d.databaseName
                databasesWrittenTo.add(d.databaseName)
            
            DatabaseHandler.CopyEntryToHistory(SaveCur, d.entry)
            
            # only update those columns that actually contain new/changed text
            sqlStatement = u"UPDATE Text SET "
            values = ()
            if d.cleanString is not None:
                sqlStatement = sqlStatement + "english=?, "
                values = values + (d.cleanString,)
            if d.commentString is not None:
                sqlStatement = sqlStatement + "comment=?, "
                values = values + (d.commentString,)
            sqlStatement = sqlStatement + "updated=1, status=?, UpdatedBy=?, UpdatedTimestamp=strftime('%s',?) WHERE ID=?"
            values = values + (d.role, str(Globals.Author), d.timestring, d.entry)
            SaveCur.execute(sqlStatement, values)

        if SaveCon is not None:
            SaveCon.commit()
        
        for db in databasesWrittenTo:
            CompletionTable.CalculateCompletionForDatabase(str(db))
            Globals.Cache.LoadDatabase(str(db))

        self.databaseWriteStorage.clear()

        Globals.Cache.databaseAccessRLock.release()
        
    def SwitchVisibleEng(self):
        self.TextboxVisibleFlagEnglish = not self.TextboxVisibleFlagEnglish
        if self.TextboxVisibleFlagEnglish:
            for box in self.xTextBoxesENG:
                box.show()
        else:
            for box in self.xTextBoxesENG:
                box.hide()
        Globals.Settings.setValue('TextboxVisibleFlagEnglish', 'True' if self.TextboxVisibleFlagEnglish else 'False')
        Globals.Settings.sync()
        return

    def SwitchVisibleJpn(self):
        self.TextboxVisibleFlagJapanese = not self.TextboxVisibleFlagJapanese
        if self.TextboxVisibleFlagJapanese:
            for box in self.xTextBoxesJPN:
                box.show()
        else:
            for box in self.xTextBoxesJPN:
                box.hide()
        Globals.Settings.setValue('TextboxVisibleFlagJapanese', 'True' if self.TextboxVisibleFlagJapanese else 'False')
        Globals.Settings.sync()
        return

    def SwitchVisibleCom(self):
        self.TextboxVisibleFlagComment = not self.TextboxVisibleFlagComment
        if self.TextboxVisibleFlagComment:
            for box in self.xTextBoxesCOM:
                box.show()
        else:
            for box in self.xTextBoxesCOM:
                box.hide()
        Globals.Settings.setValue('TextboxVisibleFlagComment', 'True' if self.TextboxVisibleFlagComment else 'False')
        Globals.Settings.sync()
        return

    def FindUnsavedDatabases(self):
        self.WriteDatabaseStorageToHdd()
        
        Globals.Cache.databaseAccessRLock.acquire()
        self.ClearUpdateSet()
        Globals.MainWindow.displayStatusMessage( 'Searching for databases with unsaved changes...' )

        for item in Globals.configData.FileList:
            RecalcDbConn = DatabaseHandler.OpenEntryDatabase(item)
            RecalcDbCur = RecalcDbConn.cursor()
            RecalcDbCur.execute("SELECT Count(1) FROM Text WHERE updated = 1")
            exists = RecalcDbCur.fetchall()[0][0]
            if exists > 0:
                self.AddDatabaseToUpdateSet(str(item))
                Globals.MainWindow.displayStatusMessage( 'Found database with unsaved changes: ' + item )
            RecalcDbConn.close()

        Globals.Settings.setValue('update', set(self.update))
        Globals.Settings.sync()
        Globals.MainWindow.displayStatusMessage( 'Done searching for databases with unsaved changes!' )
        Globals.Cache.databaseAccessRLock.release()
        return
    
    def FindAllUsedSymbols(self):
        charSet = set()
        for File in Globals.configData.FileList:
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
        return NetworkHandler.SavetoServer(self)
    
    def CallRevertFromServer(self):
        self.WriteDatabaseStorageToHdd()

        if len(self.update) == 0:
            Globals.MainWindow.displayStatusMessage( 'Nothing to revert!' )
            return

        reply = QtGui.QMessageBox.warning(self, "Warning!", "This will discard all changes since the last save to the server.\nAre you really sure you want to revert?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            NetworkHandler.RevertFromServer(self)
        return

    def CallRetrieveModifiedFiles(self):
        NetworkHandler.RetrieveModifiedFiles(self, None)
        return
