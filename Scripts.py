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
#   - Split Graces and Vesperia
#   - Add Graces f
#
################################################


commentsAvailableLabel = False


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


# load config
configData = Configuration('config.xml')



if os.path.exists('Clips'):
    try:
        sys.path.append('Clips')
        from PyQt4.phonon import Phonon
    except ImportError:
        print "Your Qt installation does not have Phonon support.\nPhonon is required to play audio clips."
    if os.path.exists('Clips/hashtable.py'):
        from hashtable import hashtable
        HashTableExists = True
    else:
        HashTableExists = False
    Audio = True


else:
    print "No folder named 'Clips' found. Audio playback disabled."
    Audio = False


if not os.path.exists(configData.LocalDatabasePath + '/CompletionPercentage'):
    CreateConnection = sqlite3.connect(configData.LocalDatabasePath + '/CompletionPercentage')
    CreateCursor = CreateConnection.cursor()
    CreateCursor.execute("CREATE TABLE Percentages (Database TEXT PRIMARY KEY, entries INT, translation INT, editing1 INT, editing2 INT, editing3 INT, comments INT)")
    CreateConnection.commit()
    

try:
    import enchant
    enchanted = True
except:
    enchanted = False
    print 'No pyenchant found. Spell checking will not be available.'


os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

ConnectionGracesJapanese = sqlite3.connect(configData.LocalDatabasePath + '/GracesJapanese')
CursorGracesJapanese = ConnectionGracesJapanese.cursor()

LogCon = sqlite3.connect(configData.LocalDatabasePath + '/ChangeLog')
LogCur = LogCon.cursor()

VesperiaFlag = True
EnglishVoiceLanguageFlag = False
UpdateLowerStatusFlag = False
ModeFlag = 'Semi-Auto'


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.Toolbar = QtGui.QToolBar()
        
        self.editMenu = QtGui.QMenu("&Edit", self)
                
        self.editMenu.addAction("Undo")
        self.editMenu.addAction("Redo")        
        self.editMenu.addSeparator()
        self.editMenu.addAction("Cut")
        self.editMenu.addAction("Copy")
        self.editMenu.addAction("Paste")
        self.editMenu.addAction("Select All")
                        
        self.menuBar().addMenu(self.editMenu)

        self.addToolBar(self.Toolbar)
        self.setUnifiedTitleAndToolBarOnMac(True)

        self.setCentralWidget(Scripts2(self))
        


class XTextBox(QtGui.QTextEdit):

    manualEdit = QtCore.pyqtSignal(int)


    def __init__(self, HUD=None):
        super(XTextBox, self).__init__()

        self.Jpcon = sqlite3.connect('Resources/JPDictionary')
        self.Jpcur = self.Jpcon.cursor()
        self.modified = False
        
        self.one = False
        self.two = False
        self.three = False
        self.four = False

        self.buttons = []

        if Audio == True:
            self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory)
            self.player = Phonon.MediaObject()
            Phonon.createPath(self.player, self.audioOutput)

        if HUD == None:
            self.translate = QtGui.QToolButton()
            self.translate.setAutoRaise(True)
            self.translate.setIcon(QtGui.QIcon('icons/tloff.png'))
    
            self.tlCheck = QtGui.QToolButton()
            self.tlCheck.setAutoRaise(True)
            self.tlCheck.setIcon(QtGui.QIcon('icons/oneoff.png'))
    
            self.rewrite = QtGui.QToolButton()
            self.rewrite.setAutoRaise(True)
            self.rewrite.setIcon(QtGui.QIcon('icons/twooff.png'))
    
            self.grammar = QtGui.QToolButton()
            self.grammar.setAutoRaise(True)
            self.grammar.setIcon(QtGui.QIcon('icons/threeoff.png'))

            topLayout = QtGui.QHBoxLayout()

            layout = HUDLayout()
            layout.addWidget(self.grammar)
            layout.addWidget(self.rewrite)
            layout.addWidget(self.tlCheck)
            layout.addWidget(self.translate)
            
            topLayout.setMargin(0)
            topLayout.addLayout(layout)
            self.setLayout(topLayout)

            self.translate.released.connect(self.transTogglem)
            self.tlCheck.released.connect(self.checkTogglem)
            self.rewrite.released.connect(self.rewriteTogglem)
            self.grammar.released.connect(self.grammarTogglem)


        elif HUD == 'jp':
            self.jpflag = QtGui.QToolButton()
            self.jpflag.setCheckable(False)
            self.jpflag.setAutoRaise(True)
            self.jpflag.setIcon(QtGui.QIcon('icons/japanflag.png'))
            
            layout = HUDLayout()
            layout.addWidget(self.jpflag)
            self.setLayout(layout)

            self.jpflag.released.connect(self.flagToggle)
            self.role = 1
            
            
        if enchanted == True:
            self.dict = enchant.Dict("en_GB")
            if os.path.isfile('Resources/proper_nouns.txt'):
                customWordFile = file('Resources/proper_nouns.txt', 'rb')
                for word in customWordFile.xreadlines():
                    self.dict.add_to_session(word.strip())
                customWordFile.close()
            self.dict.add_to_session
            self.highlighter = MyHighlighter(self.document(), 'something')
            self.highlighter.setDict(self.dict)
        
        self.textChanged.connect(self.textChangedSignal)
        self.undoAvailable.connect(self.modifyTrue)
        
        
    def makePlaybackButtons(self, clipList):
    
        topLayout = self.layout()
        thing = topLayout.itemAt(0)

        topLayout.removeItem(thing)


        layout = HUDLayout()
        layout.addWidget(self.grammar)
        layout.addWidget(self.rewrite)
        layout.addWidget(self.tlCheck)
        layout.addWidget(self.translate)

        self.audioClips = clipList

        self.button = QtGui.QToolButton()
        self.button.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
        self.button.setAutoRaise(True)
        self.button.released.connect(self.playAudio)

        layout.addWidget(self.button)
        topLayout.addLayout(layout)        
       
                
    def clearPlaybackButtons(self):
    
        self.audioClips = []
        
        topLayout = self.layout()
        thing = topLayout.itemAt(0)
        topLayout.removeItem(thing)
    
        self.button = None

        layout = HUDLayout()
        layout.addWidget(self.grammar)
        layout.addWidget(self.rewrite)
        layout.addWidget(self.tlCheck)
        layout.addWidget(self.translate)
        topLayout.addLayout(layout)        

                        
    def lookupAudioHash(self, name):
        
        if VesperiaFlag == True:
            if EnglishVoiceLanguageFlag == True:
                #print 'Clips/US_' + name + '.mp3'
                return 'Clips/US_' + name + '.mp3'
            #print 'Clips/' + name + '.mp3'
            return 'Clips/' + name + '.mp3'
        
        if HashTableExists == False:
            return ''
        
        temphash = 0
        for i in name:
            temphash = ((temphash * 137) + ord(i)) % 0x100000000
        
        if name[:2] == 'VS':
            index = hashtable[int(name[2])-1].index(temphash)
            filename = 'VOSCE0' + name[2] + '_' + str(index+1).zfill(5) + '.mp3'
        
        elif name[:2] == 'VA':
            index = hashtable[8].index(temphash)
            filename = 'VOSCE16' + '_' + str(index+1).zfill(5) + '.mp3'
        
        return 'Clips/' + filename
        

    def playAudio(self):
    
        self.player.clear()
        playerQueue = []
    
        for clip in self.audioClips:
            filename = self.lookupAudioHash(clip)
            playerQueue.append(Phonon.MediaSource(filename))
                
        self.player.enqueue(playerQueue)
        self.player.play()

    def textChangedSignal(self):
        if self.modified == True:
            self.manualEdit.emit(5)
            
    def modifyTrue(self, set):
        self.modified = set

    def setText(self, string):
        self.modified = False
        QtGui.QTextEdit.setText(self, string)
        

    def mousePressEvent(self, event):
        if enchanted == True:
            if event.button() == QtCore.Qt.RightButton:
                event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress, event.pos(),
                    QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
        QtGui.QTextEdit.mousePressEvent(self, event)


    def contextMenuEvent(self, event):
        popup_menu = self.createStandardContextMenu()
    
        # Select the word under the cursor.
        cursor = self.textCursor()
        if cursor.selectedText() == '':
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        self.setTextCursor(cursor)
    
        # Check if the selected word is misspelled or JP and offer spelling
        # suggestions if it is.
        if self.textCursor().hasSelection():
            text = unicode(self.textCursor().selectedText())
            
            # JP Lookup
            if ord(text[0]) > 0x79:
                select = unicode(cursor.selectedText()) + u'%'

                # All matches
                self.Jpcur.execute(u'select * from Dictionary where Kanji LIKE ? OR Kana LIKE ?', (select, select))
                results = self.Jpcur.fetchall()

                if results != []:
                    
                    font = self.font()
                    font.setPixelSize(9)
                    
                    resultsMenu = []
                    i = 0
                    for result in results[:16]:
                        if result[1] != None:
                            yum = u' [' + unicode(result[1]) + u']'
                        else:
                            yum = ''
                        
                        menu = QtGui.QMenu(u'{0}{1}'.format(result[0], yum))
                        menu.setFont(font)
                        
                        actionList = self.DefSplit(unicode(result[2]))
                        for item in actionList:
                            menu.addAction(item)
                        resultsMenu.append(menu)
                    
                    theCookieMenu = QtGui.QMenu('{0} Partial Matches'.format(len(resultsMenu)))
                    popup_menu.insertSeparator(popup_menu.actions()[0])
                    popup_menu.insertMenu(popup_menu.actions()[0], theCookieMenu)
                    
                    for menu in resultsMenu:
                        theCookieMenu.addMenu(menu)
                        i += 1


                # Perfect Match
                self.Jpcur.execute(u'select * from Dictionary where Kanji=? OR Kana=?', (unicode(cursor.selectedText()), unicode(cursor.selectedText())))
                trueResults = self.Jpcur.fetchall()

                if trueResults != []:
                    if trueResults[0][1] != None:
                        yum = u' [' + unicode(trueResults[0][1]) + u']'
                    else:
                        yum = ''
                
                    amenu = QtGui.QMenu(u'{0}{1}'.format(trueResults[0][0], yum))
                    
                    actionList = self.DefSplit(unicode(trueResults[0][2]))
                    for item in actionList:
                        amenu.addAction(item)

                    popup_menu.insertSeparator(popup_menu.actions()[0])
                    popup_menu.insertMenu(popup_menu.actions()[0], amenu)

                if results == [] and trueResults == []:
                    menu = QtGui.QMenu('No JP-Eng Matches Found')
                    popup_menu.insertSeparator(popup_menu.actions()[0])
                    popup_menu.insertMenu(popup_menu.actions()[0], menu)

            # Enchant
            if enchanted == True:
                if not self.dict.check(text):
                    spell_menu = QtGui.QMenu('Spelling Suggestions')
                    for word in self.dict.suggest(text):
                        action = SpellAction(word, spell_menu)
                        action.correct.connect(self.correctWord)
                        spell_menu.addAction(action)
                    # Only add the spelling suggests to the menu if there are
                    # suggestions.
                    if len(spell_menu.actions()) != 0:
                        popup_menu.insertSeparator(popup_menu.actions()[0])
                        popup_menu.insertMenu(popup_menu.actions()[0], spell_menu)
                                
            popup_menu.exec_(event.globalPos())


    def DefSplit(self, string):
        
        cookielist = []
        pat = re.compile('([(].*?[)]) *(.*)')
        match = re.match(pat, string)

        
        cookieString = match.group(1)[1:-1] + ':'

        thinglist = [
        ['n', 'Noun'],
        ['aux', 'Auxiliary'],
        ['id', 'Idiom'],
        ['int', 'Interjection'],
        ['iv', 'Irregular Verb'],
        ['vi', 'Intransitive Verb'],
        ['adv', 'Adverb'],
        ['conj', 'Conjunction'],
        ['ctr', 'Counter'],
        ['exp', 'Expression'],
        ['pref', 'Prefix'],
        ['suf', 'Suffix'],
        ['adj-i', 'Adjective'],
        ['num', 'Numeric'],
        ['pn', 'Pronoun'],
        ['prt', 'Particle'],
        ['Noun-', 'n-'],
        ['n-pref', 'Noun Prefix'],
        ['n-suf', 'Noun Suffix'],
        ['n-t', 'Noun (Temporal)'],
        ['v5aru', 'Verb ~aru'],
        ['v5b', 'Verb ~bu'],
        ['v5g', 'Verb ~gu'],
        ['v5k-s', 'Verb ~iku/yuku'],
        ['v5k', 'Verb ~ku'],
        ['v5m', 'Verb ~mu'],
        ['v5n', 'Verb ~nu'],
        ['v5r-i', 'Verb ~ru (irregular)'],
        ['v5r', 'Verb ~ru'],
        ['v5s', 'Verb ~su'],
        ['v5t', 'Verb ~tsu'],
        ['v5u-s', 'Verb ~u (special)'],
        ['v5uru', 'Verb ~uru'],
        ['v5u', 'Verb ~u'],
        ['v5z', 'Verb ~zu'],
        ['vz', 'Ichidan verb ~zuru)'],
        ['vk', 'Kuru Verb'],
        ['vn', 'Irregular ~nu Verb'],
        ['vs-i', 'Suru Verb (irregular)'],
        ['vs-s', 'Suru Verb (special)'],
        ['vs', 'Noun with ~suru'],
        ['vt', 'Transitive Verb']]
        ['v1', 'Ichidan verb'],
        ['v5', 'Verb'],


        for thing in thinglist:
            cookieString = cookieString.replace(thing[0], thing[1])


        cookielist.append(cookieString)

        NewString = match.group(2)
        
        i = 1
        loop = True
        while loop == True:
            if NewString.count('({0})'.format(i)) == 1:
                if NewString.count('({0})'.format(i+1)) == 1:
                    cookielist.append(NewString[NewString.find('({0})'.format(i))+4:NewString.find('({0})'.format(i+1))])
                    i += 1
                else:
                    cookielist.append(NewString[NewString.find('({0})'.format(i))+4:])
                    loop = False
                    break
            else:
                cookielist.append(NewString)
                loop = False
                break
            
        return cookielist
    
    def correctWord(self, word):
        '''
        Replaces the selected text with word.
        '''
        cursor = self.textCursor()
        cursor.beginEditBlock()
 
        cursor.removeSelectedText()
        cursor.insertText(word)
 
        cursor.endEditBlock()


    def transTogglem(self):
        if self.one == False:
            self.translate.setIcon(QtGui.QIcon('icons/tlon.png'))
            self.one = True
            self.manualEdit.emit(1)
        else:
            self.translate.setIcon(QtGui.QIcon('icons/tloff.png'))
            self.one = False
            self.manualEdit.emit(0)

            
    def checkTogglem(self):
        if self.two == False:
            self.tlCheck.setIcon(QtGui.QIcon('icons/oneon.png'))
            self.two = True
            self.manualEdit.emit(2)
        else:
            self.tlCheck.setIcon(QtGui.QIcon('icons/oneoff.png'))
            self.two = False
            self.manualEdit.emit(1)


    def rewriteTogglem(self):
        if self.three == False:
            self.rewrite.setIcon(QtGui.QIcon('icons/twoon.png'))
            self.three = True
            self.manualEdit.emit(3)
        else:
            self.rewrite.setIcon(QtGui.QIcon('icons/twooff.png'))
            self.three = False
            self.manualEdit.emit(2)


    def grammarTogglem(self):
        if self.four == False:
            self.grammar.setIcon(QtGui.QIcon('icons/threeon.png'))
            self.four = True
            self.manualEdit.emit(4)
        else:
            self.grammar.setIcon(QtGui.QIcon('icons/threeoff.png'))
            self.four = False
            self.manualEdit.emit(3)



    def iconToggle(self, icon):
        self.translate.setIcon(QtGui.QIcon('icons/tloff.png'))
        self.tlCheck.setIcon(QtGui.QIcon('icons/oneoff.png'))
        self.rewrite.setIcon(QtGui.QIcon('icons/twooff.png'))
        self.grammar.setIcon(QtGui.QIcon('icons/threeoff.png'))

        self.one = False
        self.two = False
        self.three = False
        self.four = False
    
        if icon >= 1:
            self.translate.setIcon(QtGui.QIcon('icons/tlon.png'))
            self.one = True
            
            if icon >= 2:
                self.tlCheck.setIcon(QtGui.QIcon('icons/oneon.png'))
                self.two = True
                
                if icon >= 3:
                    self.rewrite.setIcon(QtGui.QIcon('icons/twoon.png'))
                    self.three = True
                    
                    if icon == 4:
                        self.grammar.setIcon(QtGui.QIcon('icons/threeon.png'))
                        self.four = True


    def flagToggle(self):
        if self.role == 2:
            self.jpflag.setIcon(QtGui.QIcon('icons/cdnflag.png'))
            self.role = 0
        elif self.role == 1:
            self.jpflag.setIcon(QtGui.QIcon('icons/comment.png'))
            self.role = 2
        else:
            self.jpflag.setIcon(QtGui.QIcon('icons/japanflag.png'))
            self.role = 1

        

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



class HUDLayout(QtGui.QLayout):
    MinimumSize, SizeHint = range(2)

    def __init__(self, parent=None, margin=0, spacing=-1):
        super(HUDLayout, self).__init__(parent)

        self.setMargin(margin)
        self.setSpacing(spacing)
        self.list = []

    def addItem(self, item):
        self.add(item)

    def addWidget(self, widget):
        widget.setGeometry(QtCore.QRect(0,0,26,26))
        widget.setMinimumSize(QtCore.QSize(26,26))
        self.add(QtGui.QWidgetItem(widget))

    def expandingDirections(self):
        return QtCore.Qt.Horizontal | QtCore.Qt.Vertical

    def hasHeightForWidth(self):
        return False

    def count(self):
        return len(self.list)

    def itemAt(self, index):
        if index < len(self.list):
            return self.list[index]

        return None

    def minimumSize(self):
        return self.calculateSize(HUDLayout.MinimumSize)

    def setGeometry(self, rect):
        Width = 0
        Height = 0

        super(HUDLayout, self).setGeometry(rect)

        for item in self.list:            
            Height = item.geometry().height() + self.spacing()
            Width += item.geometry().width() + self.spacing()

            newRect = QtCore.QRect(
                    rect.x() + rect.width() - Width + self.spacing(),
                    rect.y() + rect.height() - Height + self.spacing(),
                    item.geometry().width(), 
                    item.geometry().height())

            item.setGeometry(newRect)

    def sizeHint(self):
        return self.calculateSize(HUDLayout.SizeHint)

    def takeAt(self, index):
        if index >= 0 and index < len(self.list):
            layoutStruct = self.list.pop(index)
            return layoutStruct

        return None

    def add(self, item):
        self.list.append(item)

    def calculateSize(self, sizeType):
        totalSize = QtCore.QSize()

        for item in self.list:
            itemSize = QtCore.QSize()

            if sizeType == HUDLayout.MinimumSize:
                itemSize = item.minimumSize()
            else: # sizeType == BorderLayout.SizeHint
                itemSize = item.sizeHint()

            totalSize.setWidth(totalSize.width() + itemSize.width())

        return totalSize



class SplashScreen(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(SplashScreen, self).__init__(parent)
        
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowModality(True)        
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        self.setFixedSize(450, 350)

        self.text = 'Downloading new files...'

        self.complete = False
        self.offline = False
        
        font = self.font()
        font.setPixelSize(10)
        self.setFont(font)


    def paintEvent(self, event):
        QtGui.QWidget.paintEvent(self, event)
        
        painter = QtGui.QPainter(self)

        painter.drawPixmap(0, 0, QtGui.QPixmap('icons/Splash.png'))

        painter.drawText(350, 185, 'v9.6')
        painter.drawText(92, 185, self.text)
        
        
        
        if enchanted == False and self.offline == True:
            painter.setPen(QtGui.QColor(255, 0, 0, 255))
            painter.drawText(100, 198, 'Spell Checker not available')
            painter.drawText(112, 210, 'Offline Mode')
            painter.setPen(QtGui.QColor(0, 0, 0, 255))
        
        elif enchanted == False:
            painter.setPen(QtGui.QColor(255, 0, 0, 255))
            painter.drawText(100, 198, 'Spell Checker not available')
            painter.setPen(QtGui.QColor(0, 0, 0, 255))
            
        elif self.offline == True:
            painter.setPen(QtGui.QColor(255, 0, 0, 255))
            painter.drawText(100, 198, 'Offline Mode')
            painter.setPen(QtGui.QColor(0, 0, 0, 255))
               
                   
    def mousePressEvent(self, event):
        if self.complete == True:
            self.close()
            self.destroy(True)


    def destroyScreen(self):
        self.close()
        self.destroy(True)


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
        VesperiaFlag = True
        EnglishVoiceLanguageFlag = False

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
            print 'Files retained from last session: ', ''.join(["%s, " % (k) for k in self.update])[:-2]
        
        else:
            print 'Files retained from last session: ', ''.join(["%s, " % (k) for k in self.update])[:-2]

        if self.settings.contains('role'):
            self.role = int(self.settings.value('role'))
        else:
            self.role = 1

        global ModeFlag
        if self.settings.contains('mode'):
            ModeFlag = self.settings.value('mode')
        else:
            self.settings.setValue('mode', 'Semi-Auto')

        self.roletext = ['', 'Translating', 'Reviewing Translations', 'Reviewing Context', 'Editing']

        self.parent.setWindowTitle("Grace Note - {0} in {1} mode".format(self.roletext[self.role] , ModeFlag))
        #>>> CursorGracesJapanese.execute('create table Log(ID int primary key, File text, Name text, Timestamp int)')


        # Grab the changes
        self.RetrieveModifiedFiles(self.splashScreen)

        self.splashScreen.destroyScreen()
        
        
        # List View of Files
        self.tree = QtGui.QTreeView()
        self.treemodel = QtGui.QStandardItemModel()

        self.tree.setAnimated(True)
        self.tree.setIndentation(10)
        self.tree.setSortingEnabled(False)
        self.tree.setFixedWidth(190)
        self.tree.sortByColumn(1, 0)
        self.tree.setHeaderHidden(True)
        
        self.PopulateModel(configData.FileList)

#        self.treemodel = QtGui.QSortFilterProxyModel()
#        self.treemodel.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)


#        self.treemodel.setSourceModel(self.treemodel)
        self.tree.setModel(self.treemodel)

        self.sortSwapGroup = QtGui.QGroupBox()
        self.sortSwapGroup.setTitle('Sort by:')
        
        self.sortByType = QtGui.QRadioButton('Type')
        self.sortByType.setChecked(True)
        self.sortByLocation = QtGui.QRadioButton('Location')
        
        boxLayout = QtGui.QHBoxLayout()
        boxLayout.addWidget(self.sortByType)
        boxLayout.addWidget(self.sortByLocation)
        self.sortSwapGroup.setLayout(boxLayout)
        


        # List View of Entries
        self.entry = QtGui.QListView()
        self.entrymodel = QtGui.QStandardItemModel()

        self.entry.setFixedWidth(180)
 
        self.entrysort = QtGui.QSortFilterProxyModel()
        self.entrysort.setSourceModel(self.entrymodel)
        self.entry.setModel(self.entrysort)


        # Text Edits
        self.editpast = XTextBox()
        self.editpresent = XTextBox()
        self.editfuture = XTextBox()
        
        self.Beditpast = XTextBox('jp')
        self.Beditpresent = XTextBox('jp')
        self.Beditfuture = XTextBox('jp')

        self.Beditpast.hide()
        self.Beditpresent.hide()
        self.Beditfuture.hide()

        self.Beditpast.setReadOnly(True)
        self.Beditpresent.setReadOnly(True)
        self.Beditfuture.setReadOnly(True)
        
        MyHighlighter(self.Beditpast, 'something')
        MyHighlighter(self.Beditpresent, 'something')
        MyHighlighter(self.Beditfuture, 'something')

        if self.settings.contains('font'):
            size = int(self.settings.value('font'))

            self.editpast.setFontPointSize(size)
            self.editpresent.setFontPointSize(size)
            self.editfuture.setFontPointSize(size)
            
            self.Beditpast.setFontPointSize(size)
            self.Beditpresent.setFontPointSize(size)
            self.Beditfuture.setFontPointSize(size)


        
        LayoutPast = QtGui.QHBoxLayout()
        LayoutPresent = QtGui.QHBoxLayout()
        LayoutFuture = QtGui.QHBoxLayout()

        LayoutPast.addWidget(self.editpast)
        LayoutPresent.addWidget(self.editpresent)
        LayoutFuture.addWidget(self.editfuture)

        LayoutPast.addWidget(self.Beditpast)
        LayoutPresent.addWidget(self.Beditpresent)
        LayoutFuture.addWidget(self.Beditfuture)

        self.PastBox = QtGui.QGroupBox()
        self.PresentBox = QtGui.QGroupBox()
        self.FutureBox = QtGui.QGroupBox()

        self.PastBox.setLayout(LayoutPast)
        self.PresentBox.setLayout(LayoutPresent)
        self.FutureBox.setLayout(LayoutFuture)

        self.PastBox.setTitle("Entry -:")
        self.PresentBox.setTitle("Entry -:")
        self.FutureBox.setTitle("Entry -:")


                
        # Filter Input
        self.filter = QtGui.QLineEdit()
        self.filter.setFixedWidth(200)
        
        self.debug = QtGui.QAction(QtGui.QIcon('icons/debugoff.png'), 'Display Debug', None)
        self.debug.setCheckable(True)
        self.debug.setChecked(0)
        
        # Connections
        self.tree.selectionModel().selectionChanged.connect(self.PopulateEntryList)
        self.entry.selectionModel().selectionChanged.connect(self.PopulateTextEdit)
        self.entry.clicked.connect(self.UpdateDebug)
        #self.entry.pressed.connect(self.UpdateDebug)
        self.editpast.manualEdit.connect(self.UpdatePast)
        self.editpresent.manualEdit.connect(self.UpdatePresent)
        self.editfuture.manualEdit.connect(self.UpdateFuture)
        self.debug.toggled.connect(self.DebugFilter)
        self.filter.returnPressed.connect(self.LiveSearch)
        self.sortByType.toggled.connect(self.SortToggle)
        self.sortByLocation.toggled.connect(self.SortToggle)


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

        self.updateAct = QtGui.QAction(QtGui.QIcon('icons/upload.png'), 'Update', None)
        self.updateAct.triggered.connect(self.RetrieveModifiedFiles)
        self.updateAct.setShortcut(QtGui.QKeySequence('Ctrl+U'))

        self.refreshCompleteAct = QtGui.QAction(QtGui.QIcon('icons/upload.png'), 'Refresh Completion Database', None)
        self.refreshCompleteAct.triggered.connect(self.RefreshCompletion)
        self.refreshCompleteAct.setShortcut(QtGui.QKeySequence('Ctrl+W'))

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
        self.quitAct.triggered.connect(self.quit)
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

        self.vesperiaAct = QtGui.QAction('Deactivate', None)
        self.vesperiaAct.triggered.connect(self.VesperiaSwap)
        self.vesperiaAct.setShortcut(QtGui.QKeySequence('Ctrl-Shift-Alt-V'))
        self.voiceLangAct = QtGui.QAction('Japanese Voices', None)
        self.voiceLangAct.triggered.connect(self.VoiceLanguageSwap)
        self.voiceLangAct.setShortcut(QtGui.QKeySequence('Ctrl-Shift-Alt-E'))
        
        
        self.updateLowerStatusAct = QtGui.QAction('Not updating lower status', None)
        self.updateLowerStatusAct.triggered.connect(self.UpdateLowerStatusSwap)
        
        
        self.autoAct = QtGui.QAction('Auto', None)
        self.semiAct = QtGui.QAction('Semi-Auto', None)
        self.manuAct = QtGui.QAction('Manual', None)
        

        self.scrollUpAct = QtGui.QAction('Scroll Up', None)
        self.scrollUpAct.triggered.connect(self.scrollUp)
        self.scrollUpAct.setShortcut(QtGui.QKeySequence('Alt+Up'))

        self.scrollDownAct = QtGui.QAction('Scroll Down', None)
        self.scrollDownAct.triggered.connect(self.scrollDown)
        self.scrollDownAct.setShortcut(QtGui.QKeySequence('Alt+Down'))


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
        self.Toolbar.addWidget(QtGui.QLabel('Search'))
        self.Toolbar.addWidget(self.filter)
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
        fileMenu.addSeparator()
        fileMenu.addAction(self.patchAct)
        fileMenu.addAction(self.patchdolAct)
        fileMenu.addAction(self.patchzeroAct)
        fileMenu.addAction(self.patchtwoAct)
        fileMenu.addAction(self.patchfDemoAct)
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
        

        vesperiaMenu = QtGui.QMenu("Vesperia", self)
        vesperiaMenu.addAction(self.vesperiaAct)
        vesperiaMenu.addAction(self.voiceLangAct)
        vesperiaMenu.addAction(self.updateLowerStatusAct)

        parent.menuBar().addMenu(fileMenu)
        parent.menuBar().addMenu(parent.editMenu)
        parent.menuBar().addMenu(viewMenu)
        parent.menuBar().addMenu(roleMenu)
        parent.menuBar().addMenu(modeMenu)
        parent.menuBar().addMenu(toolsMenu)
        parent.menuBar().addMenu(vesperiaMenu)


        # Layout
        layout = QtGui.QGridLayout()

        subLayout = QtGui.QVBoxLayout()
        
        #subLayout.addWidget(self.sortSwapGroup)
        global commentsAvailableLabel
        commentsAvailableLabel = QtGui.QLabel("-")
        subLayout.addWidget(commentsAvailableLabel)
        subLayout.addWidget(self.tree)
        
        layout.addLayout(subLayout, 0, 0, 3, 1)
        layout.addWidget(self.PastBox, 0, 1, 1, 2)
        layout.addWidget(self.PresentBox, 1, 1, 1, 2)
        layout.addWidget(self.FutureBox, 2, 1, 1, 2)
        layout.addWidget(self.entry, 0, 3, 3, 1)
        layout.setColumnStretch(1,1)
        self.setLayout(layout)


    def quit(self):
        self.settings.setValue('update', set(self.update))
        print 'These files retained for next session: ', ''.join(["%s, " % (k) for k in self.update])[:-2]
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

        self.editpast.setFontPointSize(size)
        self.editpresent.setFontPointSize(size)
        self.editfuture.setFontPointSize(size)
        
        self.Beditpast.setFontPointSize(size)
        self.Beditpresent.setFontPointSize(size)
        self.Beditfuture.setFontPointSize(size)

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

        global ModeFlag
        try:
            self.settings.setValue('role', int(self.role))
        except:
            self.settings.setValue('role', 1)
        self.parent.setWindowTitle("Grace Note - {0} in {1} mode".format(self.roletext[self.role] , ModeFlag))
        self.PopulateEntryList()


    def setMode(self, action):
        if action == self.autoAct:
            mode = 'Auto'
        if action == self.semiAct:
            mode = 'Semi-Auto'
        if action == self.manuAct:
            mode = 'Manual'
            
        self.settings.setValue('mode', mode)
        global ModeFlag
        ModeFlag = mode

        self.parent.setWindowTitle("Grace Note - {0} in {1} mode".format(self.roletext[self.role] , ModeFlag))


    def VesperiaSwap(self):
        
        global VesperiaFlag

        
        if self.vesperiaAct.text() == 'Activate':
            self.vesperiaAct.setText('Deactivate')
            self.PopulateModel(configData.FileList)
                    
            VesperiaFlag = True

        elif self.vesperiaAct.text() == 'Deactivate':
            self.vesperiaAct.setText('Activate')
            self.PopulateModel(configData.FileList)
                    
            VesperiaFlag = False

        else:
            self.vesperiaAct.setText('Activate')
            self.PopulateModel(configData.FileList)
                    
            VesperiaFlag = False

    def VoiceLanguageSwap(self):
        
        global EnglishVoiceLanguageFlag

        
        if EnglishVoiceLanguageFlag == True:
            self.voiceLangAct.setText('Japanese Voices')
            EnglishVoiceLanguageFlag = False

        else:
            self.voiceLangAct.setText('English Voices')
            EnglishVoiceLanguageFlag = True
        
    def UpdateLowerStatusSwap(self):
        global UpdateLowerStatusFlag
        if UpdateLowerStatusFlag == True:
            self.updateLowerStatusAct.setText('Not updating lower status')
            UpdateLowerStatusFlag = False
        else:
            self.updateLowerStatusAct.setText('Updating lower status')
            UpdateLowerStatusFlag = True

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

            self.Beditpast.show()
            self.Beditpresent.show()
            self.Beditfuture.show()
            
            self.PopulateTextEdit()

        else:
            self.twoupAct.setIcon(QtGui.QIcon('icons/twoup.png'))
            self.twoupAct.setText('Two up')

            self.Beditpast.hide()
            self.Beditpresent.hide()
            self.Beditfuture.hide()

        
    def SortToggle(self):
        global VesperiaFlag
        if VesperiaFlag == True:
            return
        if self.sortByType.isChecked():
            self.PopulateModel(configData.FileList)
        elif self.sortByLocation.isChecked():
            self.PopulateModel(configData.FileList)
        else:
            print 'Unknown Sort Type'


    def ConsolidateDebug(self):
    
        i = 1
        aList = configData.FileList
            
        for item in aList[0]:
            print item
            for filename in aList[i]:

                print "Processing: {0}".format(filename)
            
                UpdateCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(filename))
                UpdateCur = UpdateCon.cursor()
                        
                UpdateCur.execute("select ID, StringID, status from Text")
                
                for entry in UpdateCur.fetchall():                        
                    CursorGracesJapanese.execute("select debug from Japanese where ID=?", (entry[1],))
            
                    try:
                        if CursorGracesJapanese.fetchall()[0][0] == 1:
                            UpdateCur.execute("update Text set status=-1 where ID=? AND status != -1", (entry[0],))
                        else:
                            if entry[2] == -1:
                                UpdateCur.execute("update Text set status = 0 where ID=? AND status != 0", (entry[0],))
                    except:
                        pass
                        
                UpdateCon.commit()
                
            i += 1

    def RetrieveModifiedFiles(self, splash):
        # Nab the online changelog
        try:
            splash.text = 'Downloading updated files...'
        except:
            print 'Downloading updated files...'
            
        # loop to prevent crashes during FTP stuff
        for i in range( 0, 20 ):    # range( start, stop, step )
            try:
                
                try:
                    ftp = FTP(configData.FTPServer, configData.FTPUsername, configData.FTPPassword, "", 15)
                except:
                    if i == 20:
                        print '20 errors is enough, this is not gonna work'
                        try:
                            splash.text = 'Grace Note Loaded'.format(self.roletext[self.role], ModeFlag)
                            splash.complete = True
                            splash.offline = True
                        except:
                            pass
                        return
                    print 'Failed connecting to FTP, retrying...'
                    continue
                    
                ftp.cwd('/')
                ftp.cwd(configData.RemoteDatabasePath)
                        
                changes = self.DownloadFile(ftp, 'ChangeLog', 'NewChangeLog')
                
                if changes == False:
                    "This isn't going to work, is it? Try again later."
                    self.quit() 


                # Get any new entries
                LogCur.execute('select ID, File from Log ORDER BY ID')
                results = LogCur.fetchall()
                LogSet = set(results)

                NewLogCon = sqlite3.connect(configData.LocalDatabasePath + "/NewChangeLog")
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
                        Downloader.append(subitem)
                
                # by pika: remove possible duplicates from list, so it doesn't download the same file multiple times
                Downloader = list(set(Downloader))
                
                #Downloader.sort()
                for item in set(Downloader):
                    CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [item])
                    exists = CursorGracesJapanese.fetchall()[0][0]
                    if exists > 0:
                        CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [item])
                        desc = CursorGracesJapanese.fetchall()[0][0]
                        print 'Downloading ' + desc + ' [' + item + ']...'
                    else:
                        print 'Downloading ' + item + '...'
                    
                    
                    
                    self.DownloadFile(ftp, item, item)
                    WipeUpdateCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(item))
                    WipeUpdateCur = WipeUpdateCon.cursor()
            
                    WipeUpdateCur.execute(u"update Text set updated=0")
                    WipeUpdateCon.commit()
                    
                    CalculateCompletionForDatabase(item)

                                
                old = open(configData.LocalDatabasePath + '/ChangeLog', 'wb')
                new = open(configData.LocalDatabasePath + '/NewChangeLog', 'rb')
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
            splash.text = 'Grace Note now {0} in {1} Mode'.format(self.roletext[self.role], ModeFlag)
            splash.complete = True
        except:
            print 'Downloaded updated files!'


    def DownloadFile(self, ftp, source, dest):
        
        save = open(configData.LocalDatabasePath + '/{0}'.format(dest), 'wb')
        ftp.retrbinary('RETR {0}'.format(source), save.write)
        save.close()

        size = ftp.size('{0}'.format(source))

        check = open(configData.LocalDatabasePath + '/{0}'.format(dest), 'rb')
        localsize = len(check.read())
        check.close()
        
        if size != localsize:
            success = False
            for i in range(3):
                print 'Problem Downloading {0}. Retry #{1}'.format(source, i+1)
                
                e = open(configData.LocalDatabasePath + '/{0}'.format(dest), 'wb')
                ftp.retrbinary('RETR {0}'.format(source), e.write)
                e.close()
        
                e = open(configData.LocalDatabasePath + '/{0}'.format(dest), 'rb')
                localsize = len(e.read())
                e.close()

                if size == localsize:
                    success = True
                    break
            if success == False:
                "Looks like {0} won't download. Moving on, I suppose.".format(source)
                return False
                
        
        return True
        

    def UploadFile(self, ftp, source, dest):
    
        source = str(source)
        dest = str(dest)
    
        fnew = open(configData.LocalDatabasePath + '/{0}'.format(source), 'rb')
        UploadString = str('STOR ' + dest)
        ftp.storbinary(UploadString, fnew)
        fnew.close()

        size = ftp.size(dest)

        check = open(configData.LocalDatabasePath + '/{0}'.format(source), 'rb')
        localsize = len(check.read())
        check.close()

        if size != localsize:
            success = False
            for p in range(5):
                print 'Problem Uploading {0}. Retry #{1}'.format(dest, p+1)
                
                fnew = open(configData.LocalDatabasePath + '/{0}'.format(source), 'rb')
                UploadString = str('STOR ' + dest)
                ftp.storbinary(UploadString, fnew)
                size = ftp.size(dest)
                fnew.close()
        
                if size == localsize:
                    success = True
                    break
                    
            if success == False:
                "Looks like {0} won't upload. Better talk to Tempus about it.".format(dest)
                return dest
            
        
        return True

    def PopulateModel(self, FileList):
        self.treemodel.clear()
        
        PercentageConnection = sqlite3.connect(configData.LocalDatabasePath + "/CompletionPercentage")
        PercentageCursor = PercentageConnection.cursor()
        
        i = 1
        for item in FileList[0]:
            cat = QtGui.QStandardItem(item)
            self.treemodel.appendRow(cat)
            for item in FileList[i]:
                newrow = QtGui.QStandardItem()
                newrow.setStatusTip(item)

                CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [item])
                exists = CursorGracesJapanese.fetchall()[0][0]
                if exists > 0:
                    CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [item])
                    desc = CursorGracesJapanese.fetchall()[0][0]
                    newrow.setText(desc)
                else:
                    newrow.setText(item)
                
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
        global commentsAvailableLabel
        containsComments = False
    
        self.editpast.iconToggle(0)
        self.editpresent.iconToggle(0)
        self.editfuture.iconToggle(0)

        self.entrymodel.clear()
        
        self.text = []

        self.editpast.setText('')
        self.editpresent.setText('')
        self.editfuture.setText('')

        index = self.tree.currentIndex()
        parent = self.treemodel.data(self.tree.currentIndex().parent())

        if self.treemodel.hasChildren(index) == True:
            return

        databasefilename = self.treemodel.itemFromIndex(index).statusTip()
        SaveCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(databasefilename))
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
            CursorGracesJapanese.execute("select * from Japanese where ID={0}".format(TempList[i][1]))
            TempString = CursorGracesJapanese.fetchall() 
            TempJPN = TempString[0][1]
            TempDebug = TempString[0][2]

            TempENG = TempList[i][2]
            TempCOM = TempList[i][3]
            TempStatus = TempList[i][5]

            if TempENG == '':
                TempENG = TempJPN

            entryDisplayString = 'Entry ' + str(i+1).zfill(5) + ' [' + str(TempStatus) + ']'
            
            if ContainsIDString == True:
                try:
                    entryDisplayString = entryDisplayString + ' ' + TempList[i][6]
                except:
                    pass
            
            if TempCOM != '':
                entryDisplayString = entryDisplayString + ' [Comment]'
                containsComments = True
            
            additem = QtGui.QStandardItem(entryDisplayString)
            additem.setCheckable(True)
            
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
                self.entrymodel.appendRow(additem)
            else:            
                self.entrymodel.appendRow(additem)
            
            if TempStatus != -1 and TempDebug == 1:
                SaveCur.execute("update Text set status=-1 where ID=?", (TempString[0][0],))
                SaveCon.commit()
                
            self.text.append([TempENG, TempJPN, TempCOM, TempDebug, TempStatus])
            
        if containsComments == True:
            commentsAvailableLabel.setText(databasefilename + " | Comments exist!")
        else:
            commentsAvailableLabel.setText(databasefilename)
            
        
    def GetFullText(self, replaceVariables):
        string = ''
        i = 1
        for entry in self.text:
            if entry[3] == 0:
                string = string + 'Entry {0}\n'.format(i)
                if replaceVariables == True:
                    string = string + VariableReplace(entry[0])
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

    def LiveSearch(self):

        matchString = self.filter.text()

        # Check to make sure people aren't idiots
        if matchString.count(unicode('<', 'UTF-8')) != matchString.count(unicode('>', 'UTF-8')):
            
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYou can not search for part of a variable. Please be sure to include the entire variable tag.")
            return


        matchString = VariableRemove(matchString)
        
        if len(matchString) == 0:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search can not be empty. Please enter text in the search bar.")
            return


        popup_menu = QtGui.QMenu()


        # For an Exact match to the string at any point                        
        try:
            CursorGracesJapanese.execute(u"select ID from Japanese where debug=0 AND string LIKE ?", ('%' + unicode(matchString) + '%', ))
            JPmatches = set(CursorGracesJapanese.fetchall())
        except:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search returned too many results, try something with more letters or use the mass replace.")
            return

        MatchedEntries = []

        aList = configData.FileList

        for i in range(1, len(aList)):
            for File in aList[i]:
                FilterCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(File))
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
                        CursorGracesJapanese.execute('select string from Japanese where ID={0}'.format(item[2]))
                        String = CursorGracesJapanese.fetchall()[0][0]
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
            newString = VariableReplace(item[2])
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
        self.gLogDialog = GlobalChangelog(self)

        self.gLogDialog.show()
        self.gLogDialog.raise_()
        self.gLogDialog.activateWindow()


    def ShowStats(self):
        self.statDialog = Statistics()

        self.statDialog.show()
        self.statDialog.raise_()
        self.statDialog.activateWindow()


    def ShowMassReplace(self):
        self.massDialog = MassReplace(self)

        self.massDialog.show()
        self.massDialog.raise_()
        self.massDialog.activateWindow()


    def ShowCompletionTable(self):
        self.comDialog = CompletionTable(self)

        self.comDialog.show()
        self.comDialog.raise_()
        self.comDialog.activateWindow()

    def RefreshCompletion(self):
        CalculateAllCompletionPercentagesForDatabase()

    def PlayCentralAudio(self):
        self.editpresent.playAudio()
        
    def ShowDuplicateText(self):
        self.dupeDialog = DuplicateText()

        self.dupeDialog.show()
        self.dupeDialog.raise_()
        self.dupeDialog.activateWindow()
        


    def UpdateDebug(self):
        index = self.entry.currentIndex()
        rowPresent = int(self.entrysort.data(index)[6:11])-1
        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        SaveCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(databasefilename))
        SaveCur = SaveCon.cursor()

        if self.entrymodel.item(index.row()).checkState() == 0:
            SaveCur.execute("select StringID from Text where ID={0}".format(rowPresent+1))
            NextID = SaveCur.fetchall()[0][0]
            CursorGracesJapanese.execute("update Japanese set debug=0 where ID={0}".format(NextID))
            SaveCur.execute("update Text set status=0 where ID={0} AND status=-1".format(rowPresent+1))
            SaveCon.commit()
            ConnectionGracesJapanese.commit()
            
            SaveCur.execute("select status from Text where ID={0}".format(rowPresent+1))
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
            SaveCur.execute("select StringID from Text where ID={0}".format(rowPresent+1))
            NextID = SaveCur.fetchall()[0][0]
            CursorGracesJapanese.execute("update Japanese set debug=1 where ID={0}".format(NextID))
            SaveCur.execute("update Text set status=-1 where ID={0}".format(rowPresent+1))
            SaveCon.commit()
            ConnectionGracesJapanese.commit()
            
            self.entrymodel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 220, 220)))
            if self.author == 'ruta':
                self.entrymodel.item(index.row()).setBackground(QtGui.QBrush(QtGui.QColor(255,225,180)))             
        

    def UpdatePast(self, role):
        treeindex = self.tree.currentIndex()
        if self.treemodel.hasChildren(treeindex):
            return
        
        index = self.entry.currentIndex()
        row = index.row()

        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        SaveCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(databasefilename))
        SaveCur = SaveCon.cursor()
        
        if row == 0 or row == None:
            return

        self.update.add(str(databasefilename))
                        
        rowPast = int(self.entrysort.data(index.sibling(index.row()-1, index.column()))[6:11])-1
        
        self.entrymodel.item(index.sibling(index.row()-1, 0).row()).setBackground(QtGui.QBrush(QtGui.QColor(220, 255, 220)))
        if self.author == 'ruta':
            self.entrymodel.item(index.sibling(index.row()-1, 0).row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))
            
        GoodString = VariableRemove(self.editpast.toPlainText())

        if role == 5:
            role = self.role
            
        global UpdateLowerStatusFlag
        if UpdateLowerStatusFlag == False:
            SaveCur.execute("SELECT status FROM Text WHERE ID={0}".format(rowPast+1))
            statuscheck = SaveCur.fetchall()[0][0]
            if statuscheck > role:
                updateStatusValue = statuscheck
            else:
                updateStatusValue = role
        else:
            updateStatusValue = role
        
        global ModeFlag
        if ModeFlag != 'Manual':
            self.text[rowPast][4] = updateStatusValue
            self.editpast.iconToggle(updateStatusValue)
                
        if self.state == 'ENG':
            if ModeFlag == 'Manual':
                SaveCur.execute(u"update Text set english=?, updated=1 where ID=?", (GoodString, rowPast+1))
            else:
                SaveCur.execute(u"update Text set english=?, updated=1, status=? where ID=?", (GoodString, updateStatusValue, rowPast+1))
            SaveCon.commit()
            self.text[rowPast][0] = GoodString

        elif self.state == "COM":
            if ModeFlag == 'Manual':
                SaveCur.execute(u"update Text set comment=?, updated=1 where ID=?", (GoodString, rowPast+1))
            else:
                SaveCur.execute(u"update Text set comment=?, updated=1, status=? where ID=?", (GoodString, updateStatusValue, rowPast+1))
            SaveCon.commit()
            self.text[rowPast][2] = GoodString

        
    def UpdatePresent(self, role):
        treeindex = self.tree.currentIndex()
        if self.treemodel.hasChildren(treeindex):
            return

        index = self.entry.currentIndex()
        row = index.row()

        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        SaveCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(databasefilename))
        SaveCur = SaveCon.cursor()

        self.update.add(str(databasefilename))
                        
        rowPresent = int(self.entrysort.data(index)[6:11])-1

        self.entrymodel.item(index.row(), 0).setBackground(QtGui.QBrush(QtGui.QColor(220, 255, 220)))
        if self.author == 'ruta':
            self.entrymodel.item(index.row(), 0).setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))

        GoodString = VariableRemove(self.editpresent.toPlainText())

        if role == 5:
            role = self.role
        
        global UpdateLowerStatusFlag
        if UpdateLowerStatusFlag == False:
            SaveCur.execute("SELECT status FROM Text WHERE ID={0}".format(rowPresent+1))
            statuscheck = SaveCur.fetchall()[0][0]
          #  print '{0} statuscheck'.format(statuscheck)
         #   print '{0} role'.format(role)
            if statuscheck > role:
                updateStatusValue = statuscheck
            else:
                updateStatusValue = role
        else:
            updateStatusValue = role
        
        #print '{0} updateStatusValue'.format(updateStatusValue)
        
        global ModeFlag
        if ModeFlag != 'Manual':
            self.text[rowPresent][4] = updateStatusValue
            self.editpresent.iconToggle(updateStatusValue)

        if self.state == 'ENG':
            if ModeFlag == 'Manual':
                SaveCur.execute(u"update Text set english=?, updated=1 where ID=?", (GoodString, rowPresent+1))
            else:
                SaveCur.execute(u"update Text set english=?, updated=1, status=? where ID=?", (GoodString, updateStatusValue, rowPresent+1))
            SaveCon.commit()
            self.text[rowPresent][0] = GoodString

        elif self.state == "COM":
            if ModeFlag == 'Manual':
                SaveCur.execute(u"update Text set comment=?, updated=1 where ID=?", (GoodString, rowPresent+1))
            else:
                SaveCur.execute(u"update Text set comment=?, updated=1, status=? where ID=?", (GoodString, updateStatusValue, rowPresent+1))
            SaveCon.commit()
            self.text[rowPresent][2] = GoodString

        
    def UpdateFuture(self, role):
        treeindex = self.tree.currentIndex()
        if self.treemodel.hasChildren(treeindex):
            return

        index = self.entry.currentIndex()
        row = index.row()

        databasefilename = self.treemodel.itemFromIndex(self.tree.currentIndex()).statusTip()
        SaveCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(databasefilename))
        SaveCur = SaveCon.cursor()
        
        if row == self.entrymodel.rowCount()-1:
            return
            
        self.update.add(str(databasefilename))
                        
        rowFuture = int(self.entrysort.data(index.sibling(index.row()+1, index.column()))[6:11])-1
        
        self.entrymodel.item(index.sibling(index.row()+1, 0).row()).setBackground(QtGui.QBrush(QtGui.QColor(220, 255, 220)))
        if self.author == 'ruta':
            self.entrymodel.item(index.sibling(index.row()+1, 0).row()).setBackground(QtGui.QBrush(QtGui.QColor(255, 235, 245)))

        GoodString = VariableRemove(self.editfuture.toPlainText())

        if role == 5:
            role = self.role

        global UpdateLowerStatusFlag
        if UpdateLowerStatusFlag == False:
            SaveCur.execute("SELECT status FROM Text WHERE ID={0}".format(rowFuture+1))
            statuscheck = SaveCur.fetchall()[0][0]
            if statuscheck > role:
                updateStatusValue = statuscheck
            else:
                updateStatusValue = role
        else:
            updateStatusValue = role
        
        global ModeFlag
        if ModeFlag != 'Manual':
            self.text[rowFuture][4] = updateStatusValue
            self.editfuture.iconToggle(updateStatusValue)

        if self.state == 'ENG':
            if ModeFlag == 'Manual':
                SaveCur.execute(u"update Text set english=?, updated=1 where ID=?", (GoodString, rowFuture+1))
            else:
                SaveCur.execute(u"update Text set english=?, updated=1, status=? where ID=?", (GoodString, updateStatusValue, rowFuture+1))
            SaveCon.commit()
            self.text[rowFuture][0] = GoodString

        elif self.state == "COM":
            if ModeFlag == 'Manual':
                SaveCur.execute(u"update Text set comment=?, updated=1 where ID=?", (GoodString, rowFuture+1))
            else:
                SaveCur.execute(u"update Text set comment=?, updated=1, status=? where ID=?", (GoodString, updateStatusValue, rowFuture+1))
            SaveCon.commit()
            self.text[rowFuture][2] = GoodString
        

    def PopulateTextEdit(self):
        
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
        
        commentPast = ''
        commentPresent = ''
        commentFuture = ''

        # Past Boxes
        if not row == 0:
            rowPast = int(self.entrysort.data(index.sibling(index.row()-1, index.column()))[6:11])-1
            TextPast = VariableReplace(self.text[rowPast][t])
            BTextPast = VariableReplace(self.text[rowPast][self.Beditpast.role])
            if self.text[rowPast][2] != '':
                commentPast = 'Comment Available'
            
            self.editpast.iconToggle(self.text[rowPast][4])
            AudioClips = re.findall('<Audio: (.*?)>', TextPast, re.DOTALL)
            if Audio == True:
                self.editpast.makePlaybackButtons(AudioClips)
            if AudioClips == []:
                self.editpast.clearPlaybackButtons()

        else:
            self.editpast.iconToggle(0)


        # Present Boxes
        rowPresent = int(self.entrysort.data(index)[6:11])-1
        TextPresent = VariableReplace(self.text[rowPresent][t])
        BTextPresent = VariableReplace(self.text[rowPresent][self.Beditpresent.role])

        if self.text[rowPresent][2] != '':
            commentPresent = 'Comment Available'
            
        self.editpresent.iconToggle(self.text[rowPresent][4])

        AudioClips = re.findall('<Audio: (.*?)>', TextPresent, re.DOTALL)
        if Audio == True:
            self.editpresent.makePlaybackButtons(AudioClips)
        if AudioClips == []:
            self.editpresent.clearPlaybackButtons()


        # Future Boxes
        if not row == self.entrymodel.rowCount()-1:
            rowFuture = int(self.entrysort.data(index.sibling(index.row()+1, index.column()))[6:11])-1
            TextFuture = VariableReplace(self.text[rowFuture][t])
            BTextFuture = VariableReplace(self.text[rowFuture][self.Beditfuture.role])

            if self.text[rowFuture][2] != '':
                commentFuture = 'Comment Available'

            self.editfuture.iconToggle(self.text[rowFuture][4])

            AudioClips = re.findall('<Audio: (.*?)>', TextFuture, re.DOTALL)
            if Audio == True:
                self.editfuture.makePlaybackButtons(AudioClips)
            if AudioClips == []:
                self.editfuture.clearPlaybackButtons()
        else:
            self.editfuture.iconToggle(0)




        # The good stuff
        if self.entrymodel.rowCount() == 0:
            return

        elif self.entrymodel.rowCount() == 1:
            self.editpast.setText('')
            self.editpresent.setText(TextPresent)
            self.editfuture.setText('')

            if self.twoupAct.isChecked() == True:
                self.Beditpast.setText('')
                self.Beditpresent.setText(BTextPresent)
                self.Beditfuture.setText('')

            self.PastBox.setTitle("Entry -:      {0}".format(commentPast))
            self.PresentBox.setTitle("Entry {0}:      {1}".format(rowPresent+1, commentPresent))
            self.FutureBox.setTitle("Entry -:      {0}".format(commentFuture))

        elif row == 0:
            self.editpast.setText('')
            self.editpresent.setText(TextPresent)
            self.editfuture.setText(TextFuture)
    
            if self.twoupAct.isChecked() == True:
                self.Beditpast.setText('')
                self.Beditpresent.setText(BTextPresent)
                self.Beditfuture.setText(BTextFuture)

            self.PastBox.setTitle("Entry -:      {0}".format(commentPast))
            self.PresentBox.setTitle("Entry {1}:      {0}".format(commentPresent, rowPresent+1))
            self.FutureBox.setTitle("Entry {1}:      {0}".format(commentFuture, rowFuture+1))

        elif row == self.entrymodel.rowCount()-1:
            self.editpast.setText(TextPast)
            self.editpresent.setText(TextPresent)
            self.editfuture.setText('')

            if self.twoupAct.isChecked() == True:
                self.Beditpast.setText(BTextPast)
                self.Beditpresent.setText(BTextPresent)
                self.Beditfuture.setText('')

            self.PastBox.setTitle("Entry {0}:      {1}".format(rowPast+1, commentPast))
            self.PresentBox.setTitle("Entry {0}:      {1}".format(rowPresent+1, commentPresent))
            self.FutureBox.setTitle("Entry -:      {0}".format(commentFuture))

        elif row == -1 or row == None:
            self.editpast.setText('')
            self.editpresent.setText('')
            self.editfuture.setText('')

            if self.twoupAct.isChecked() == True:
                self.Beditpast.setText('')
                self.Beditpresent.setText('')
                self.Beditfuture.setText('')

            self.PastBox.setTitle("Entry -:")
            self.PresentBox.setTitle("Entry -:")
            self.FutureBox.setTitle("Entry -:")

        else:
            self.editpast.setText(TextPast)
            self.editpresent.setText(TextPresent)
            self.editfuture.setText(TextFuture)

            if self.twoupAct.isChecked() == True:
                self.Beditpast.setText(BTextPast)
                self.Beditpresent.setText(BTextPresent)
                self.Beditfuture.setText(BTextFuture)

            self.PastBox.setTitle("Entry {0}:      {1}".format(rowPast+1, commentPast))
            self.PresentBox.setTitle("Entry {0}:      {1}".format(rowPresent+1, commentPresent))
            self.FutureBox.setTitle("Entry {0}:      {1}".format(rowFuture+1, commentFuture))

        
        global ModeFlag
        if ModeFlag == 'Auto':
            self.editpast.manualEdit.emit(self.role)
            self.editpresent.manualEdit.emit(self.role)
            self.editfuture.manualEdit.emit(self.role)

        
    def SwapEnglish(self):

        if self.state == 'ENG':
            return

        self.editpast.setReadOnly(False)
        self.editpresent.setReadOnly(False)
        self.editfuture.setReadOnly(False)
        
        self.state = 'ENG'
        self.PopulateTextEdit()


    def SwapJapanese(self):

        if self.state == 'JPN':
            return

        self.editpast.setReadOnly(True)
        self.editpresent.setReadOnly(True)
        self.editfuture.setReadOnly(True)
        
        self.state = 'JPN'
        self.PopulateTextEdit()


    def SwapComment(self):

        if self.state == 'COM':
            return

        self.editpast.setReadOnly(False)
        self.editpresent.setReadOnly(False)
        self.editfuture.setReadOnly(False)
        
        self.state = 'COM'
        self.PopulateTextEdit()

                    
       
    def SavetoServer(self):
        if len(self.update) == 0:
            print 'Nothing to save!'
            return

        print 'Beginning Save...'
        
        
        for i in range(1, 20):
            try:        
                try:
                    self.ftp = FTP(configData.FTPServer, configData.FTPUsername, configData.FTPPassword, "", 15)
                except:
                    if i == 20:
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
                self.ftp.cwd(configData.RemoteDatabasePath)

                print "Retrieving any files modified by others..."
                self.RetrieveModifiedFiles(self.splashScreen)
                
                progress.setLabelText('Uploading Files...')
                LogTable = []
                saveUpdate = set()
         
                for filename in self.update:
                    
                    # remove empty comments
                    rcommentconn = sqlite3.connect(configData.LocalDatabasePath + "/" + filename)
                    rcommentcur = rcommentconn.cursor()
                    rcommentcur.execute(u"UPDATE text SET comment = '', updated = 1 WHERE comment IS NULL")
                    rcommentconn.commit()
                    rcommentconn.close()
                    
                    CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [filename])
                    exists = CursorGracesJapanese.fetchall()[0][0]
                    if exists > 0:
                        CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [filename])
                        desc = CursorGracesJapanese.fetchall()[0][0]
                        print 'Uploading ' + desc + ' [' + filename + ']...'
                    else:
                        print 'Uploading ' + filename + '...'

                    # Downloading the server version and double checking
                    self.DownloadFile(self.ftp, str(filename), 'temp')

                    try:
                        WipeUpdateCon = sqlite3.connect(configData.LocalDatabasePath + "/temp")
                        WipeUpdateCur = WipeUpdateCon.cursor()
                
                        WipeUpdateCur.execute(u"update Text set updated=0")
                        WipeUpdateCon.commit()
                        
                        # Merging the Server and the local version
                        NewMergeCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(filename))
                        NewMergeCur = NewMergeCon.cursor()
            
                        OldMergeCon = sqlite3.connect(configData.LocalDatabasePath + "/temp")
                        OldMergeCur = OldMergeCon.cursor()
                                
                        NewMergeCur.execute(u'select * from Text where updated=1')
                        NewTable = NewMergeCur.fetchall()
                    
                        for item in NewTable:
                            if item[4] == 1:
                                OldMergeCur.execute(u"update Text set english=?, comment=?, status=? where ID=?", (item[2], item[3], item[5], item[0]))
                        OldMergeCon.commit()
                        
                        # Uploading new files
                        result = self.UploadFile(self.ftp, 'temp', str(filename))
                        if isinstance(result, str):
                            saveUpdate.add(str(dest))
            
                        # Transposing the local file
                        fnew = open(configData.LocalDatabasePath + '/temp', 'rb')
                        data = fnew.read()
                        fnew.close()
                        
                        old = open(configData.LocalDatabasePath + '/{0}'.format(filename), 'wb')
                        old.write(data)
                        old.close()

                    except:
                    
                        print 'Server file corrupted. Fixing...'
                        
                        self.UploadFile(self.ftp, filename, filename)
                    
                        print 'Fixed'

                    i = i + 1
                    progress.setValue(i)

                    LogTable.append(filename)
                    
                    CalculateCompletionForDatabase(filename)

                # Fix up the changelog and upload
                LogCon = sqlite3.connect(configData.LocalDatabasePath + "/ChangeLog")
                LogCur = LogCon.cursor()

                LogCur.execute('select Max(ID) as Highest from Log')
                MaxID = LogCur.fetchall()[0][0]

                fileString = ''.join(["%s," % (k) for k in LogTable])[:-1]
                print 'Uploaded: ', fileString
                
                LogCur.execute(u"insert into Log values({0}, '{1}', '{2}', {3})".format(MaxID + 1, fileString, self.author, "strftime('%s','now')"))
                LogCon.commit()

                print 'Uploading: ChangeLog'
                result = self.UploadFile(self.ftp, 'ChangeLog', 'ChangeLog')
                if result == False:
                    if i == 20:
                        print "Warning:\n\nYour internet sucks, and you are ruining it for everyone. Re-upload your changelog via an FTP client immediately, or contact Tempus to whap you on the head."
                    else:
                        continue

                # Everything is done.
                progress.setValue(len(self.update)+1);

                print 'Done!'
                self.ftp.close()
                print 'Clearing updates for this session.'
                self.update.clear()
                print 'Retaining the following files for later upload: ', saveUpdate
                self.update = set(saveUpdate)
                self.settings.setValue('update', self.update)
                break
            except ftplib.all_errors:
                if i == 20:
                    print '20 errors is enough, this is not gonna work. There is probably some fucked up file on the FTP server now, please fix manually or contact someone that knows how to.'
                    break
                print 'Error during FTP transfer, retrying...'
                continue

    def SavetoPatch(self):


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


        Archive = ByFolder[1][:] # Chat_MS
        Archive.extend(ByFolder[2][:]) # Chat_SB
        Archive.extend(ByFolder[-1][:]) # SysString.bin
        Archive = (['TOG_SS_ChatName', 'TOG_SS_StringECommerce']) # Special Cased Sys Subs
        Archive.extend(ByFolder[-2][:]) # Movie Subtitles
        Archive.extend(ByFolder[-3][:]) # Special Strings

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

        for CPK in Map0RCPK:
            Archive = ByFolder[i]
            self.MakeSCS(Archive, progress, 'Wii', map0File)
            i += 1
            
        map0File.close()
        

        Map1RCPK = ['mapfile_anmaR.cpk', 'mapfile_beraR.cpk', 'mapfile_debugR.cpk', 'mapfile_fendR.cpk', 'mapfile_kameR.cpk', 'mapfile_koya_r06R.cpk', 'mapfile_lakeR.cpk', 'mapfile_lanR.cpk', 'mapfile_nekoR.cpk', 'mapfile_olleR.cpk', 'mapfile_otheR.cpk', 'mapfile_ozweR.cpk', 'mapfile_riotR.cpk', 'mapfile_sablR.cpk', 'mapfile_shatR.cpk', 'mapfile_shipR.cpk', 'mapfile_strtR.cpk', 'mapfile_supaR.cpk', 'mapfile_systemR.cpk', 'mapfile_winR.cpk']

        i = 46

        for CPK in Map1RCPK:
            Archive = ByFolder[i]
            self.MakeSCS(Archive, progress, 'Wii', map1File)
            i += 1

        map1File.close()
        
        progress.setValue(1260)


        shutil.rmtree('Resources/Wii')



    def MakeSCS(self, allFiles, progress, path, BIN=None):


        # Create the .scs files
        
        JPCon = sqlite3.connect(configData.LocalDatabasePath + '/GracesJapanese')
        JPCur = JPCon.cursor()

        fileExceptions = ['GracesJapanese', 'NewChangeLog', 'None', 'ChangeLog', 'temp', '.DS_Store', 'endingData', 'Artes', 'Battle', 'Discovery', 'GradeShop-Missions', 'Item', 'MonsterBook', 'Skills', 'System', 'Tactics', 'Titles', 'Tutorial', 'soundTest', 'ArteNames', 'Skits', 'GracesFDump', 'S']

        i = 0
        p = 0


        for filename in allFiles:

            progress.setValue(progress.value() + 1)

            if fileExceptions.count(filename) > 0:
                continue
            print filename

            OutCon = sqlite3.connect(configData.LocalDatabasePath + '/{0}'.format(filename))
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
        progress = QtGui.QProgressDialog("Saving databases to SCS...", "Abort", 0, len(os.listdir(configData.LocalDatabasePath))+1)
        progress.setWindowModality(QtCore.Qt.WindowModal)


        # Create the .scs files
        self.MakeSCS(os.listdir(configData.LocalDatabasePath), progress, 'Wii')

        progress.setValue(len(os.listdir(configData.LocalDatabasePath))+1)
 
        

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
        Archive = ByFolder[1][:] # Chat_MS
        Archive.extend(ByFolder[2][:]) # Chat_SB
        ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()
            

        # SysString
        Archive = (ByFolder[-1]) # SysString.bin
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
        Archive = (ByFolder[-2]) # Movie Subtitles
        ArchiveLocation = 'movie' + os.sep + 'str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(GracesPath, file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()

        progress.setValue(10)


        # Special Strings
        Archive = (ByFolder[-3]) # Special Stuff
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
            
            Archive = ByFolder[i]
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
            
            Archive = ByFolder[i]
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
                    
        shutil.rmtree("Resources/Wii")


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



    def SavetoBugfixXML(self):


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
        progress = QtGui.QProgressDialog("Saving databases to SCS...", "Abort", 0, len(os.listdir(configData.LocalDatabasePath))+1)
        progress.setWindowModality(QtCore.Qt.WindowModal)


        # Create the .scs files
        self.MakeSCS(os.listdir(configData.LocalDatabasePath), progress, 'Wii')

        progress.setValue(len(os.listdir(configData.LocalDatabasePath))+1)
 
        

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
        Archive = ByFolder[1][:] # Chat_MS
        Archive.extend(ByFolder[2][:]) # Chat_SB
        ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()
            
            
        # SysString        
        Archive = (ByFolder[-1]) # SysString.bin
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
        Archive = (ByFolder[-2]) # Movie Subtitles
        ArchiveLocation = 'movie' + os.sep + 'str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(GracesPath, file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()

        progress.setValue(10)


        # Special Strings
        Archive = (ByFolder[-3]) # Special Stuff
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
            
            Archive = ByFolder[i]
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
            
            Archive = ByFolder[i]
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
                    
        shutil.rmtree('Resources/Wii')
        

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


    def SavetoGracesfDemoXML(self):


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
#            CursorGracesJapanese.execute(u"select ID from Japanese where string=?", (unicode(string),))
#            results = CursorGracesJapanese.fetchall()
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
#                        TmpCon = sqlite3.connect(configData.LocalDatabasePath + '/' + DBName)
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
   


class LocalChangelog(QtGui.QDialog):

    def __init__(self, file):
    
        super(LocalChangelog, self).__init__()

        self.setWindowModality(False)        
        self.listwidget = QtGui.QListWidget()
        
        LogCur.execute("select * from Log where File='{0}'".format(file))
        templist = LogCur.fetchall()
        for entry in templist:
            self.listwidget.addItem('{0} on {1}'.format(entry[2], time.strftime('%a, %B %d at %H:%M %p', time.localtime(entry[3]))))

        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('File Modified By:'))
        layout.addWidget(self.listwidget)
        self.setLayout(layout)


class GlobalChangelog(QtGui.QDialog):

    def __init__(self, parent):
        super(GlobalChangelog, self).__init__()

        self.parent = parent
        
        self.setWindowModality(False)        
        self.treewidget = QtGui.QTreeWidget()
        
        self.treewidget.setColumnCount(3)
        self.treewidget.setHeaderLabels(['Date', 'Name', 'File'])
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 200)
        self.treewidget.setColumnWidth(1, 100)
        self.treewidget.setColumnWidth(2, 80)
        
        self.treewidget.setMinimumSize(450, 600)
        
        LogCur.execute("SELECT * FROM Log ORDER BY Timestamp DESC")
        templist = LogCur.fetchall()
        #templist.pop(0)
        for entry in templist:
            for filename in entry[1].split(','):
                self.treewidget.addTopLevelItem(QtGui.QTreeWidgetItem(['{0}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry[3]))), '{0}'.format(entry[2]), '{0}'.format(filename)]))
        
        self.treewidget.itemDoubleClicked.connect(self.JumpToFile)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Recent Changes:'))
        layout.addWidget(self.treewidget)
        self.setLayout(layout)

    def JumpToFile(self, item, column):
        file = item.data(2, 0)
        self.parent.JumpToEntry(file, 1)


class DuplicateText(QtGui.QDialog):

    def __init__(self):
        super(DuplicateText, self).__init__()

        self.setWindowModality(False)        

        self.treewidget = QtGui.QTreeWidget()
        
        self.treewidget.setColumnCount(2)
        self.treewidget.setHeaderLabels(['Amount', 'Text'])
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 80)
        self.treewidget.setColumnWidth(1, 540)
        
        self.treewidget.setMinimumSize(620, 500)

        
        self.box = QtGui.QGroupBox()
        self.box.setTitle('Search:')
        
        layout = QtGui.QGridLayout()
        
        self.categories = []
        
        i = 0
        for cat in configData.FileList[0]:
            self.categories.append(QtGui.QCheckBox(cat))
            layout.addWidget(self.categories[i], i, 0)
            i += 1
        
        self.exceptions = QtGui.QRadioButton('Inconsistent Translations only')
        self.dupes = QtGui.QRadioButton('All Duplicates')
        
        self.go = QtGui.QPushButton('Search')

        self.progressbar = QtGui.QProgressBar()
        self.progressbar.setRange(0, 100000)
        
        self.progressLabel = QtGui.QLabel('Pending')
        
        layout.addWidget(self.exceptions, 1, 1)
        layout.addWidget(self.dupes, 0, 1)
        layout.addWidget(self.progressbar, 3, 1)
        layout.addWidget(self.progressLabel, 4, 1)
        layout.addWidget(self.go, i-1, 1)
        layout.setColumnMinimumWidth(0, 200)

        self.setWindowTitle('Duplicate Text Retriever')
        subLayout = QtGui.QVBoxLayout()
        subLayout.addLayout(layout)
        subLayout.addWidget(self.treewidget)
        self.setLayout(subLayout)

        self.go.released.connect(self.SearchCategories)



#     Two options
#        One: Search for any cloned text with more than one unique translation, and display them
#        Two: Search for any cloned text at all, and display them



    def SearchCategories(self):

        self.treewidget.clear()

        Table =[]

        for i in xrange(50000):
            Table.append([0, set([])])

        CursorGracesJapanese.execute('select ID from Japanese where debug=1')
        blacklist = CursorGracesJapanese.fetchall()
        aList = configData.FileList

        i = 1
        for category in self.categories:
            if category.isChecked() == True:
                
                for filename in aList[i]:

                    conC = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(filename))
                    curC = conC.cursor()
                    
                    curC.execute("select StringID, English from Text")
                    
                    results = curC.fetchall()
                    
                    for item in results:
                        if blacklist.count((item[0],)) == 0:
                            Table[item[0]][0] += 1
                            Table[item[0]][1].add(item[1])
#                    self.progressbar.setValue(self.progressbar.value() + (6250/len(configData.FileList[i])))
#                    self.progressLabel.setText("Processing {0}".format(category))
#                    self.progressLabel.update()
#            self.progressbar.setValue(i * 6250)
            i += 1
        
        i = 0
        if self.exceptions.isChecked() == True:
            for item in Table:
                if ((item[0] > 1) and (len(item[1]) > 2)) or ((item[0] > 1) and (item[1] == set(['']))):
                    
                    CursorGracesJapanese.execute('select String from Japanese where ID=?', (i, ))
                    JP = CursorGracesJapanese.fetchall()[0][0]
                
                    textexception = QtGui.QTreeWidgetItem(self.treewidget, [str(item[0]).zfill(2), JP])
                    textexception.setBackgroundColor(0, QtGui.QColor(212,236,255,255))
                    textexception.setBackgroundColor(1, QtGui.QColor(212,236,255,255))
                    for exception in item[1]:
                        newline = QtGui.QTreeWidgetItem(textexception, ['', exception])
#                self.progressLabel.setText("Processing {0}/50000".format(i))
                i += 1
#                self.progressbar.setValue(self.progressbar.value() + 1)


        else:
            for item in Table:
                if item[0] > 1:
                    CursorGracesJapanese.execute('select String from Japanese where ID=?', (i, ))
                    JP = CursorGracesJapanese.fetchall()[0][0]
                
                    textexception = QtGui.QTreeWidgetItem(self.treewidget, [str(item[0]).zfill(2), JP])
                    textexception.setBackgroundColor(0, QtGui.QColor(212,236,255,255))
                    textexception.setBackgroundColor(1, QtGui.QColor(212,236,255,255))
                    for exception in item[1]:
                        newline = QtGui.QTreeWidgetItem(textexception, ['', exception])
#                self.progressLabel.setText("Processing {0}/50000".format(i))
                i += 1
#                self.progressbar.setValue(self.progressbar.value() + 1)
#        self.progressLabel.setText('Done!')
        i = 0

#        self.progressbar.reset


def CalculateAllCompletionPercentagesForDatabase():
    aList = configData.FileList
    
    
    for i in range(len(aList)-1):
        for item in aList[i+1]:
            CalculateCompletionForDatabase(item)

def CalculateCompletionForDatabase(database):
    print 'Calculating percentages for ' + database + '...'
    
    tempCon = sqlite3.connect(configData.LocalDatabasePath + '/' + database)
    tempCur = tempCon.cursor()
    
    tempCur.execute("SELECT Count(1) from Text where status>=0")
    totalDB = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) from Text where status>=1")
    translated = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) from Text where status>=2")
    tlCheck = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) from Text where status>=3")
    rewrite = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) from Text where status>=4")
    grammar = tempCur.fetchall()[0][0]

    tempCur.execute("SELECT Count(1) FROM Text WHERE comment != ''")
    commentAmount = tempCur.fetchall()[0][0]
    
    tempCon = sqlite3.connect(configData.LocalDatabasePath + '/CompletionPercentage')
    tempCur = tempCon.cursor()
    
    tempCur.execute("SELECT Count(1) FROM Percentages WHERE Database = ?", [database])
    exists = tempCur.fetchall()[0][0]
    
    if exists > 0:
        tempCur.execute("UPDATE Percentages SET entries = ?, translation = ?, editing1 = ?, editing2 = ?, editing3 = ?, comments = ? WHERE Database = ?", [totalDB, translated, tlCheck, rewrite, grammar, commentAmount, database])
    else:
        tempCur.execute("INSERT INTO Percentages (entries, translation, editing1, editing2, editing3, comments, Database) VALUES (?, ?, ?, ?, ?, ?, ?)", [totalDB, translated, tlCheck, rewrite, grammar, commentAmount, database])
    tempCon.commit()


class CompletionTable(QtGui.QDialog):

    def __init__(self, parent):
        super(CompletionTable, self).__init__()


        self.parent = parent
        self.setWindowModality(False)        

        self.treewidget = QtGui.QTreeWidget()
        
        self.treewidget.setColumnCount(6)
        self.treewidget.setHeaderLabels(['Name', 'Translation', 'Editing 1', 'Editing 2', 'Editing 3', 'Comments'])
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 200)
        
        self.treewidget.setMinimumSize(620, 500)

        subLayout = QtGui.QVBoxLayout()
        subLayout.addWidget(self.treewidget)
        self.setLayout(subLayout)

        self.treewidget.itemDoubleClicked.connect(self.JumpToFile)

        progress = QtGui.QProgressDialog("Calculating percentages...", "Abort", 0, len(os.listdir(configData.LocalDatabasePath))+1)
        progress.setWindowModality(QtCore.Qt.WindowModal)

        bigTotal = 0
        bigTrans = 0

        i = 1
        aList = configData.FileList
            
            
        tempCon = sqlite3.connect(configData.LocalDatabasePath + '/CompletionPercentage')
        tempCur = tempCon.cursor()
            
        for item in aList[0]:
                        
            cat = QtGui.QTreeWidgetItem(self.treewidget, [item, '-', '-', '-', '-', '-'])
            
            catTotalDB = 0
            catTrans = 0
            catTlCheck = 0
            catRewrite = 0
            catGrammar = 0
            catTotalComments = 0
            
            for item in aList[i]:                
                try:
                    tempCur.execute("SELECT entries, translation, editing1, editing2, editing3, comments FROM Percentages WHERE Database = ?", [item])
                    rows = tempCur.fetchall()
                    totalDB = rows[0][0]
                    translated = rows[0][1]
                    tlCheck = rows[0][2]
                    rewrite = rows[0][3]
                    grammar = rows[0][4]
                    commentamount = rows[0][5]
                except:
                    CalculateCompletionForDatabase(item)
                    tempCur.execute("SELECT entries, translation, editing1, editing2, editing3, comments FROM Percentages WHERE Database = ?", [item])
                    rows = tempCur.fetchall()
                    totalDB = rows[0][0]
                    translated = rows[0][1]
                    tlCheck = rows[0][2]
                    rewrite = rows[0][3]
                    grammar = rows[0][4]
                    commentamount = rows[0][5]
                    
                catTotalDB += totalDB
                catTotalComments += commentamount
                catTrans += translated
                catTlCheck += tlCheck
                catRewrite += rewrite
                catGrammar += grammar

                if totalDB != 0:
                    translationPercent = '{0:06.2f}%'.format(float(translated)/float(totalDB)*100)
                    tlCheckPercent = '{0:06.2f}%'.format(float(tlCheck)/float(totalDB)*100)
                    rewritePercent = '{0:06.2f}%'.format(float(rewrite)/float(totalDB)*100)
                    grammarPercent = '{0:06.2f}%'.format(float(grammar)/float(totalDB)*100)
                else:
                    translationPercent = 'N/A'
                    tlCheckPercent = 'N/A'
                    rewritePercent = 'N/A'
                    grammarPercent = 'N/A'
                    
                newrow = QtGui.QTreeWidgetItem(cat, [item, translationPercent, tlCheckPercent, rewritePercent, grammarPercent, '{0}'.format(commentamount)])
                    
                progress.setValue(progress.value() + 1)
    
            cat.setData(1, 0, '{0:06.2f}%'.format(float(catTrans)/float(catTotalDB)*100))
            cat.setData(2, 0, '{0:06.2f}%'.format(float(catTlCheck)/float(catTotalDB)*100))
            cat.setData(3, 0, '{0:06.2f}%'.format(float(catRewrite)/float(catTotalDB)*100)) 
            cat.setData(4, 0, '{0:06.2f}%'.format(float(catGrammar)/float(catTotalDB)*100))
            cat.setData(5, 0, '{0}'.format(catTotalComments))
            
            bigTotal += catTotalDB
            bigTrans += catTrans           
                
            i = i + 1

        self.treewidget.sortItems(0, 1)
        progress.setValue(len(os.listdir(configData.LocalDatabasePath))+1)
        
        
        self.setWindowTitle('Current Phase: Translation, at {0:.2f}% completion'.format(float(bigTrans)/float(bigTotal)*100))

    def JumpToFile(self, item, column):
        if item.childCount() > 0:
            return

        file = item.data(0, 0)
        self.parent.JumpToEntry(file, 1)


def TrueCount():
    
    i = 1
    aList = configData.FileList[0]

    for item in aList:
        typeset = set([])
    
        for name in aList[i]:
            tempCon = sqlite3.connect(configData.LocalDatabasePath + '/' + name)
            tempCur = tempCon.cursor()
            
            tempCur.execute("SELECT StringID from Text")
            for thing in tempCur.fetchall():
                CursorGracesJapanese.execute("SELECT COUNT(ID) from Japanese where debug == 0 and ID == ?", (thing[0],))
                if CursorGracesJapanese.fetchall()[0][0] > 0:
                    typeset.add(thing[0])
                    
        print '{0}: {1} entries'.format(item, len(typeset))
        i += 1


class Statistics(QtGui.QDialog):

    def __init__(self):
        super(Statistics, self).__init__()

        self.setWindowModality(False)        
        layout = QtGui.QVBoxLayout()
        
        
        self.setMinimumSize(400, 600)
        self.setMaximumWidth(400)
        
        LogCur.execute("select * from Log")
        LogList = LogCur.fetchall()
        
        # Today Stats
        TodayGroup = QtGui.QGroupBox()
        layout.addWidget(TodayGroup)
        
        TodayGroup.setTitle('Today:')   
        TodayLay = QtGui.QVBoxLayout()
        TodayGroup.setLayout(TodayLay)
        TodayList = set()
        TodaySet = set()
        today = time.strftime('%m/%d', time.localtime(time.time()))
        for entry in LogList:
            if time.strftime('%m/%d', time.localtime(entry[3])) == today:
                TodaySet.add(entry[2])
                for x in entry[1].split(','):
                    TodayList.add((x, entry[2]))

        if TodaySet == set([]):
            TodayLay.addWidget(QtGui.QLabel("Nobody's done anything today =("))
        else:
            for name in TodaySet:
                string = ''
                i = 0
                for entry in TodayList:
                    if entry[1] == name:
                        string = string + entry[0] + ', '
                        i+=1 
                label = QtGui.QLabel('{0}: {1} files translated'.format(name, i))
                TodayLay.addWidget(label)
                label = QtGui.QLabel(string[:-2] + '\n')
                label.setWordWrap(True)
                font = label.font()
                font.setPointSize(10)
                font.setItalic(True)
                label.setFont(font)
                TodayLay.addWidget(label)


        # Yesterday Stats
        YesterdayGroup = QtGui.QGroupBox()
        layout.addWidget(YesterdayGroup)
        
        YesterdayGroup.setTitle('Yesterday:')   
        YesterdayLay = QtGui.QVBoxLayout()
        YesterdayGroup.setLayout(YesterdayLay)
        YesterdayList = set()
        YesterdaySet = set()
        
        yesterday = '{0}/{1}'.format(time.strftime('%m', time.localtime(time.time())), str(int(time.strftime('%d', time.localtime(time.time())))-1).zfill(2))
                
        for entry in LogList:
            if time.strftime('%m/%d', time.localtime(entry[3])) == yesterday:
                YesterdaySet.add(entry[2])
                for x in entry[1].split(','):
                    YesterdayList.add((x, entry[2]))

        if YesterdaySet == ():
            YesterdayLay.addWidget(QtGui.QLabel("Nobody did anything yesterday =("))
        else:
            for name in YesterdaySet:
                string = ''
                i = 0
                for entry in YesterdayList:
                    if entry[1] == name:
                        string = string + entry[0] + ', '
                        i+=1 
                label = QtGui.QLabel('{0}: {1} files translated'.format(name, i))
                YesterdayLay.addWidget(label)
                label = QtGui.QLabel(string[:-2] + '\n')
                label.setWordWrap(True)
                font = label.font()
                font.setPointSize(10)
                font.setItalic(True)
                label.setFont(font)
                YesterdayLay.addWidget(label)

        
        #Lifetime Stats
        LifetimeGroup = QtGui.QGroupBox()
        layout.addWidget(LifetimeGroup)
        
        LifetimeGroup.setTitle('Lifetime:')   
        LifetimeLay = QtGui.QVBoxLayout()
        LifetimeGroup.setLayout(LifetimeLay)
        
        LifetimeList = []
        LifetimeSet = set()
        for entry in LogList:
            LifetimeSet.add(entry[2])
            for x in entry[1].split(','):
                LifetimeList.append((x, entry[2]))

        PrintList = []   
        for name in LifetimeSet:
            string = ''
            countset = set()
            for entry in LifetimeList:
                if entry[1] == name:
                    countset.add(entry[0]) 
            PrintList.append([len(countset), name])
        
            
        PrintList.sort()
        PrintList.reverse()
        
        for entry in PrintList:         
            label = QtGui.QLabel('{0:<20}\t{1} files translated'.format(entry[1] + ':', entry[0]))
            LifetimeLay.addWidget(label)

        
        self.setLayout(layout)



class MassReplace(QtGui.QDialog):

    def __init__(self, parent):
        super(MassReplace, self).__init__()

        self.role = parent.role
        self.parent = parent

        self.setWindowModality(False)        
        self.treewidget = QtGui.QTreeWidget()
        
        self.treewidget.setColumnCount(5)
        self.treewidget.setHeaderLabels(['File', 'Entry', 'Replace', 'E String', 'J String'])
        self.treewidget.setSortingEnabled(True)
        
        self.treewidget.setColumnWidth(0, 120)
        self.treewidget.setColumnWidth(1, 30)
        self.treewidget.setColumnWidth(2, 20)
        self.treewidget.setColumnWidth(3, 300)
        self.treewidget.setColumnWidth(4, 300)
        
        self.treewidget.setMinimumSize(780, 400)
        self.treewidget.sortItems(0, QtCore.Qt.AscendingOrder)
        
        font = QtGui.QLabel().font()
        font.setPointSize(10)
 
        self.original = QtGui.QLineEdit()
        self.replacement = QtGui.QLineEdit()
        self.fileFilter = QtGui.QLineEdit()
        self.matchExact = QtGui.QRadioButton('Any Match')
        self.matchEnglish = QtGui.QRadioButton('Any: English Only')
        self.matchEntry = QtGui.QRadioButton('Complete Entry')
        self.matchEntry.setChecked(True)
        self.fileFilter.setToolTip('Wildcards implicit. eg CHT will match all skits')
        
        self.matchEnglish.setFont(font)
        self.matchExact.setFont(font)
        self.matchEntry.setFont(font)
                
        originalLabel = QtGui.QLabel('Original:')
        originalLabel.setFont(font)
        replaceLabel = QtGui.QLabel('Replacement:')
        replaceLabel.setFont(font)
        
        filterLabel = QtGui.QLabel('Filter by File:')
        filterLabel.setToolTip('Wildcards implicit. eg CHT will match all skits')
        filterLabel.setFont(font)
        
        self.search = QtGui.QPushButton('Search')
        self.replace = QtGui.QPushButton('Replace')

        self.checkAll = QtGui.QToolButton()
        self.checkAll.setText('Check All')
        self.checkNone = QtGui.QToolButton()
        self.checkNone.setText('Check None')
        
        checkLayout = QtGui.QHBoxLayout()
        checkLayout.addWidget(self.checkAll)
        checkLayout.addWidget(self.checkNone)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addLayout(checkLayout)
        buttonLayout.addWidget(self.search)
        buttonLayout.addWidget(self.replace)
                
        inputLayout = QtGui.QGridLayout()
        inputLayout.addWidget(originalLabel, 0, 0)
        inputLayout.addWidget(replaceLabel, 2, 0)
        inputLayout.addWidget(self.original, 1, 0, 1, 2)
        inputLayout.addWidget(self.replacement, 3, 0, 1, 2)
        inputLayout.addWidget(filterLabel, 0, 2, 1, 1)
        inputLayout.addWidget(self.matchEntry, 2, 2, 1, 1)
        inputLayout.addWidget(self.matchExact, 3, 2, 1, 1)
        inputLayout.addWidget(self.matchEnglish, 4, 2, 1, 1)
        inputLayout.addWidget(self.fileFilter, 1, 2, 1, 1)
        
        inputLayout.setColumnStretch(1, 1)
        
        self.search.released.connect(self.Search)
        self.replace.released.connect(self.Replace)
        self.checkAll.released.connect(self.checkingAll)
        self.checkNone.released.connect(self.checkingNone)
        
        self.treewidget.itemDoubleClicked.connect(self.JumpToFile)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Replace:'))
        layout.addLayout(inputLayout)
        layout.addWidget(self.treewidget)
        layout.addLayout(buttonLayout, QtCore.Qt.AlignRight)
        self.setLayout(layout)



    def checkingAll(self):
    
        Iterator = QtGui.QTreeWidgetItemIterator(self.treewidget)
        while Iterator.value():

            Iterator.value().setCheckState(2, 2)
            Iterator += 1 
        
    def checkingNone(self):
    
        Iterator = QtGui.QTreeWidgetItemIterator(self.treewidget)
        while Iterator.value():

            Iterator.value().setCheckState(2, 0)
            Iterator += 1 

    def Search(self):
        # Place all matching strings to the search into the tree widget
        
        self.treewidget.clear()


        matchString = unicode(self.original.text())

        if matchString.count(unicode('<', 'UTF-8')) != matchString.count(unicode('>', 'UTF-8')):
            
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nPart of a variable: Be sure you know what you're doing.")
            #return


        matchString = VariableRemove(matchString)

        if len(matchString) == 1:
            if ord(matchString) <= 0x20:
                reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search can not be only a space, a form feed, a newline, or a tab.")
                return
        elif len(matchString) == 0:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search can not be empty. Please enter text in the search bar.")
            return


        # For an Exact match to the string at any point
        if self.matchExact.isChecked():
                        
            CursorGracesJapanese.execute(u"select ID from Japanese where string LIKE ?", ('%' + unicode(matchString) + '%', ))
            JPmatches = set(CursorGracesJapanese.fetchall())
            MatchedEntries = []

            aList = configData.FileList
    
            for i in range(1, len(aList)):
                for File in aList[i]:
                    if File.find(self.fileFilter.text()) >= 0:
                        FilterCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(File))
                        FilterCur = FilterCon.cursor()
                        
                        ORIDString = ''
                        for match in JPmatches:
                            ORIDString = ORIDString + " OR StringID='" + str(match[0]) + "'"
                            
                        FilterCur.execute(u"select ID, English, StringID from Text where english LIKE ? {0}".format(ORIDString), ('%' + unicode(matchString) + '%', ))
                        TempList = FilterCur.fetchall()
                                                
                        for item in TempList:
                            ENString = item[1]
                            CursorGracesJapanese.execute('select string from Japanese where ID={0}'.format(item[2]))
                            JPString = CursorGracesJapanese.fetchall()[0][0]
                            MatchedEntries.append([File, item[0], ENString, JPString])
            
            if len(MatchedEntries) == 0:
                return

            for item in MatchedEntries:
                treeItem = QtGui.QTreeWidgetItem([item[0], str(item[1]), "", VariableReplace(item[2]), VariableReplace(item[3])])
                treeItem.setCheckState(2, QtCore.Qt.Checked)
                self.treewidget.addTopLevelItem(treeItem)

        # if searching in English strings only
        if self.matchEnglish.isChecked():
            
            MatchedEntries = []
            
            aList = configData.FileList
    
            for i in range(1, len(aList)):
                for File in aList[i]:
                    if File.find(self.fileFilter.text()) >= 0:
                        FilterCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(File))
                        FilterCur = FilterCon.cursor()
                        
                        FilterCur.execute(u"select ID, English, StringID from Text where english LIKE ?", ('%' + unicode(matchString) + '%', ))
                        TempList = FilterCur.fetchall()
                                                
                        for item in TempList:
                            ENString = item[1]
                            CursorGracesJapanese.execute('select string from Japanese where ID={0}'.format(item[2]))
                            JPString = CursorGracesJapanese.fetchall()[0][0]
                            MatchedEntries.append([File, item[0], ENString, JPString])
            
            if len(MatchedEntries) == 0:
                return

            for item in MatchedEntries:
                treeItem = QtGui.QTreeWidgetItem([item[0], str(item[1]), "", VariableReplace(item[2]), VariableReplace(item[3])])
                treeItem.setCheckState(2, QtCore.Qt.Checked)
                self.treewidget.addTopLevelItem(treeItem)
    
        # For an exact match to the entry
        elif self.matchEntry.isChecked():


            CursorGracesJapanese.execute(u"select ID from Japanese where string=?", (unicode(matchString),))
            JPmatches = set(CursorGracesJapanese.fetchall())
            MatchedEntries = []
    
            aList = configData.FileList

            for i in range(1, len(aList)):
                for File in aList[i]:
                    if File.find(self.fileFilter.text()) >= 0:
                        FilterCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(File))
                        FilterCur = FilterCon.cursor()
                        
                        ORIDString = ''
                        
                        if JPmatches != set([]):
                            for match in JPmatches:
                                ORIDString = ORIDString + " OR StringID='" + str(match[0]) + "'"
                        
                        FilterCur.execute(u"select ID, English, StringID from Text where english=? {0}".format(ORIDString), (unicode(matchString),))
                        TempList = FilterCur.fetchall()
                                                
                        for item in TempList:
                            ENString = item[1]
                            CursorGracesJapanese.execute('select string from Japanese where ID={0}'.format(item[2]))
                            JPString = CursorGracesJapanese.fetchall()[0][0]
                            MatchedEntries.append([File, item[0], ENString, JPString])
            
            if len(MatchedEntries) == 0:
                return

            for item in MatchedEntries:
                treeItem = QtGui.QTreeWidgetItem([item[0], str(item[1]), "", VariableReplace(item[2]), VariableReplace(item[3])])
                treeItem.setCheckState(2, QtCore.Qt.Checked)
                self.treewidget.addTopLevelItem(treeItem)
        
        
    def Replace(self):

        Iterator = QtGui.QTreeWidgetItemIterator(self.treewidget)

        if len(self.replacement.text()) == 0:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour replacement can not be empty. Please enter text in the search bar.")
            return
                
        while Iterator.value():
        
            if Iterator.value().checkState(2) == 2:
                        
                IterCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(Iterator.value().data(0, 0)))
                IterCur = IterCon.cursor()
                
                string = unicode(Iterator.value().data(3, 0))
                if self.matchEntry.isChecked():
                    string = unicode(self.replacement.text())
                else:
                    string = string.replace(unicode(self.original.text()), unicode(self.replacement.text()))
                string = VariableRemove(string)
                                
                IterCur.execute(u"update Text set english=?, updated=1, status=? where ID=?", (unicode(string), self.role, int(Iterator.value().data(1, 0))))
                self.parent.update.add(unicode(Iterator.value().data(0, 0)))
            
                IterCon.commit()

            Iterator += 1 
        
        self.treewidget.clear()
    
    def JumpToFile(self, item, column):
        if item.childCount() > 0:
            return

        file = item.data(0, 0)
        entryno = item.data(1, 0)
        self.parent.JumpToEntry(file, entryno)

class MyHighlighter( QtGui.QSyntaxHighlighter ):

    WORDS = u'(?iu)[\w\']+'
    
    def __init__( self, parent, theme ):
        self.dict = None
        QtGui.QSyntaxHighlighter.__init__( self, parent )
        self.parent = parent
        self.stateDic={'normalState':-1,'inPrefix':0,'inPostfix':1,'inName':2}
        self.m_formats= {'othtag':0,'postfix':1,'prefix':2,'name':3}
        #init formats
        darkBlue = QtGui.QColor()
        darkBlue.setNamedColor("darkBlue")
        darkRed = QtGui.QColor()
        darkRed.setNamedColor("darkRed")
        darkGreen = QtGui.QColor()
        darkGreen.setNamedColor("darkGreen")
        entityFmt = QtGui.QTextCharFormat()
        entityFmt.setForeground( darkBlue )
        entityFmt.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor('othtag',entityFmt)
        tagFmt = QtGui.QTextCharFormat()
        tagFmt.setForeground( darkGreen )
        tagFmt.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor('postfix',tagFmt)
        commentFmt = QtGui.QTextCharFormat()
        commentFmt.setForeground( darkRed )
        commentFmt.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor('prefix',commentFmt)
        nameFmt = QtGui.QTextCharFormat()
        nameFmt.setForeground( darkRed )
        nameFmt.setFontWeight( QtGui.QFont.Bold )
        self.setFormatFor('name',entityFmt)


    def highlightBlock( self, text ):
        state = self.previousBlockState()
        len = text.length()
        start = 0
        pos = 0
        while pos<len:
            if  state==self.stateDic['normalState']:
                while pos < len :
                    if  text.mid(pos, 1) == u'<' :
                        if text.mid(pos, 2) == u'<C' :
                            state = self.stateDic['inPrefix']
                        else :
                            state = self.stateDic['inPostfix']
                        break
                    else :
                        pos=pos+1
                continue
            if  state==self.stateDic['inPrefix'] :
                start = pos
                while pos < len :
                    if  text.mid(pos, 1) == u'>' :
                        pos=pos+1
                        state = self.stateDic['inName']
                        break
                    else :
                        pos=pos+1
                self.setFormat(start, pos - start, self.m_formats['prefix'])
                continue
            if  state==self.stateDic['inPostfix'] :
                start = pos
                while pos < len :
                    if  text.mid(pos, 1) == u'>':
                        pos=pos+1
                        state = self.stateDic['normalState']
                        break
                    else :
                        pos=pos+1
                self.setFormat(start, pos - start, self.m_formats['postfix'])
                continue
            if  state==self.stateDic['inName'] :
                start = pos
                while pos < len :
                    if  text.mid(pos, 1) == u'<':
                        if text.mid(pos, 2) == u'<C' :
                            state = self.stateDic['inPrefix']
                        else :
                            state = self.stateDic['inPostfix']
                        break
                    else :
                        pos=pos+1
                self.setFormat(start, pos - start, self.m_formats['name'])
                continue
        self.setCurrentBlockState(state)

        if enchanted == True:
            if not self.dict:
                return
     
            text = unicode(text)
     
            format = QtGui.QTextCharFormat()
            format.setUnderlineColor(QtCore.Qt.red)
            format.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
          
            for word_object in re.finditer(self.WORDS, text):
                if ord(word_object.group()[0]) > 0x79:
                    continue
                if not self.dict.check(word_object.group()):
                    self.setFormat(word_object.start(),
                        word_object.end() - word_object.start(), format)

                
                
    def setFormatFor( self,cons,qformat):
        self.m_formats[cons]=qformat
        self.rehighlight()


    def getFormatFor( self, cons):
        return self.m_formats[cons]


    def setDict(self, dict):
        self.dict = dict




def VariableSwap(raw):        
    matchobj = raw.group()
    code = matchobj[:1]
        
    if code == u'<':
        if matchobj == ('<con>' or '<default>' or '<inn>' or '<macro>' or '<mini>' or '<se>' or '<shop>' or '<(_ _)>'):
            return matchobj
            
        colon = matchobj.find(':')
        if colon == -1:
            return matchobj
        newcode = matchobj[1:colon]

        if newcode == u'Metric':
            return u'\x01({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Unk2':
            return u'\x02({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Sys Col':
            return u'\x03({0})'.format(Sub(matchobj[colon+2:-1], 0x3))
        if newcode == u'Name':
            return u'\x04({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Unk6':
            return u'\x06({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Colour':
            return u'\x07({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Icon':
            return u'\x08({0})'.format(Sub(matchobj[colon+2:-1], 0x8))
        if newcode == u'Audio':
            return u'\x09({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Local':
            return u'\x0B({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Furi':
            return u'\x0D({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Button':
            return u'\x0F({0})'.format(Sub(matchobj[colon+2:-1], 0xF))
        if newcode == u'Tab':
            return u'\x10({0})'.format(Sub(matchobj[colon+2:-1], 0x10))
        if newcode == u'Unk':
            return u'\x11({0})'.format(matchobj[colon+2:-1])
        else:
            return matchobj
            

    elif code == u'\x01':
        tag = 'Metric: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x02':
        tag = 'Unk2: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)
            
    elif code == u'\x03':
        tag = 'Sys Col: '        
        value = Sub(matchobj[2:-1], 0x3)
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x04':
        tag = 'Name: '
        value = matchobj[2:-1]

        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x06':
        tag = 'Unk6: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x07':
        tag = 'Colour: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x08':
        tag = 'Icon: '        
        value = Sub(matchobj[2:-1], 0x8)
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x09':
        tag = 'Audio: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x0b':
        tag = 'Local: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x0d':
        tag = 'Furi: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x0f':
        tag = 'Button: '        
        value = Sub(matchobj[2:-1], 0xF)
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x10':
        tag = 'Tab: '        
        value = Sub(matchobj[2:-1], 0x10)
        
        return u'<{0}{1}>'.format(tag, value)
        
    elif code == u'\x11':
        tag = 'Unk: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)
        
    else:
        return matchobj
        
    return matchobj
    
def Sub(string, subsection):
    for item in SubstitutionTable[subsection]:
        if string == item[0]:
            return item[1]
        if string == item[1]:
            return item[0]
    

def VariableReplace(string):
    string = re.sub(u"'+", "'", unicode(string))
    string = re.sub('(.|\r)\(.*?\)', VariableSwap, unicode(string), re.DOTALL)
    string = re.sub(u"\x0C", u"<Feed>", unicode(string))
    string = re.sub(u"\x0A", u"↵\x0A", unicode(string))
    return string
    
    
def VariableRemove(string):
    string = re.sub(u"'+", "''", unicode(string))
    string = re.sub(u"<Feed>", u"\x0C", unicode(string))
    string = re.sub(u"↵\x0A", u"\x0A", unicode(string))
    string = re.sub(u'<.*?>', VariableSwap, unicode(string), re.DOTALL)
    return string
        


SubstitutionTable = [

[ # 0x0
],

[ # 0x1
],

[ # 0x2
],

[ # 0x3
    ['0', 'Default'],
    ['1', 'Blue'],
    ['2', 'Red'],
    ['3', 'Purple'],
    ['4', 'Green'],
    ['5', 'Cyan'],
    ['6', 'Mustard'],
    ['7', 'White'],
    ['8', 'Chestnut'],
    ['9', 'Wii Blue']
],

[ # 0x4
],

[ # 0x5
],

[ # 0x6
],

[ # 0x7
],

[ # 0x8
    ['$Z1', 'Crossed Swords'],
    ['$_1', 'Crescent Moon'],
    ['$s4', 'Up Arrow'],
    ['$t4', 'Down Arrow'],
    ['$u4', 'Left Arrow'],
    ['$v4', 'Right Arrow'],
    ['$‾1', 'Bottle']
],

[ # 0x9
],

[ # 0xA
],

[ # 0xB
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', '']
],

[ # 0xC
],

[ # 0xD
],

[ # 0xE
],

[ # 0xF
    ['0,$1g1', 'A'],
    ['0,$2g1', 'B'],
    ['0,$3g1', 'Analog'],
    ['0,$4g1', 'Vert Analog'],
    ['0,$5g1', 'Horiz Analog'],
    ['0,$6g1', '2 and Horiz Analog'],
    ['0,$7g1', 'Z'],
    ['0,$8g1', '2'],
    ['0,$9g1', '1 and Horiz Analog'],
    ['0,$ag1', 'C'],
    ['0,$bg1', 'A (2)'],
    ['0,$cg1', 'Left DPad'],
    ['0,$dg1', 'Right DPad'],
    ['0,$eg1', 'Plus'],
    ['0,$fg1', '1'],
    ['0,$gg1', '1 (2)'],
    ['0,$hg1', 'Z (2)'],
    ['0,$ig1', 'Fast A'],
    ['0,$jg1', 'Minus'],
    ['0,$kg1', 'Horiz Analog (2)'],
    ['0,$lg1', 'None'],
    ['0,$mg1', 'Z + 1 + DPad Horiz + Analog Down + A'],
    ['0,$ug1', 'Minus + Plus + DPad Up + Analog Left-Right-Down'],
    ['0,$xg1', 'Minus + Plus + DPad Vert + Analog Up'],
    ['0,1024', 'Unknown1'],
    ['0,1025', 'Unknown2'],
    ['0,1026', 'Unknown3'],
    ['0,1027', 'Unknown4'],
    ['0,1028', 'Unknown5'],
    ['0,1029', 'Unknown6'],
    ['0,1030', 'Unknown7'],
    ['0,1031', 'Unknown8'],
    ['0,1032', 'Unknown9'],
    ['0,1033', 'UnknownA'],
    ['0,1034', 'UnknownB'],
    ['0,1035', 'UnknownC'],
    ['0,1036', 'UnknownD'],
    ['0,1037', 'UnknownE'],
    ['0,1038', 'UnknownF'],
    ['0,1039', 'L1'],
    ['0,1040', 'R1'],
    ['0,1040', 'UnknownI'],
    ['0,1041', 'UnknownJ'],
    ['0,1042', 'UnknownK'],
    ['0,1043', 'UnknownL'],
    ['0,1044', 'Right Analog Stick'],
    ['0,1045', 'UnknownN'],
    ['0,2048', 'X'],
    ['0,2049', 'UnknownP'],
    ['0,2050', 'UnknownQ'],
    ['0,2051', 'UnknownR'],
    ['0,2052', 'UnknownS'],
    ['0,2053', 'UnknownT'],
    ['0,2054', 'UnknownU'],
    ['0,2055', 'UnknownV'],
    ['0,2056', 'UnknownW'],
    ['0,2057', 'UnknownX'],
    ['0,2058', 'UnknownY'],
    ['0,2059', 'Left Analog Stick'],
    ['0,2060', 'L1-B'],
    ['0,2061', 'UnknownAB'],
    ['0,2062', 'UnknownAC'],
    ['0,2063', 'UnknownAD'],
    ['0,2064', 'UnknownAE'],
    ['0,2065', 'UnknownAF'],
    ['0,2066', 'R2'],
    ['0,2067', 'UnknownAH'],
    ['0,2068', 'UnknownAI'],
    ['0,2069', 'UnknownAJ'],
    ['0,2070', 'UnknownAK'],
    ['0,2071', 'UnknownAL'],
    ['0,2072', 'UnknownAM'],
    ['0,2073', 'UnknownAN']
],

[ # 0x10
    ['$q', '1'],
    ['$a1', '2'],
    ['$U1', '3'],
    ['$‾1', '3.25'],
    ['$w2', '3.75'],
    ['$K2', '4'],
    ['$A3', '5']
],

[ # 0x11
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', '']
]

]









ByFolder = [

['Chat_MS', 'Chat_SB', 'Debug', 'M0Basi', 'M0Bria', 'M0Brid', 'M0Cave', 'M0Fall', 'M0ff12', 'M0ff13', 'M0ff14', 'M0ff15', 'M0ff16', 'M0ff17', 'M0ff19', 'M0ff20', 'M0Fore', 'M0gent', 'M0iceb', 'M0Iron', 'M0Kone', 'M0Kot', 'M0Las', 'M0Mont', 'M0Rock', 'M0Sand', 'M0sf08', 'M0sf09', 'M0sf10', 'M0sf11', 'M0sf18', 'M0Snee', 'M0Snow', 'M0Stda', 'M0Varo', 'M0wf01', 'M0wf02', 'M0wf03', 'M0wf04', 'M0wf05', 'M0wf06', 'M0wf07', 'M0wf21', 'M0Winc', 'M0Zone', 'M1Anma', 'M1Bera', 'M1Debug', 'M1Fend', 'M1Kame', 'M1Koya', 'M1Lake', 'M1Lan', 'M1Neko', 'M1Olle', 'M1Other', 'M1Ozwe', 'M1Riot', 'M1Sabl', 'M1Shat', 'M1Ship', 'M1Strt', 'M1Supa', 'M1System', 'M1Win', 'RootStrings', 'Subtitles', 'DR', 'System'], 

['CHT_MS001', 'CHT_MS002', 'CHT_MS003', 'CHT_MS004', 'CHT_MS005', 'CHT_MS006', 'CHT_MS007', 'CHT_MS008', 'CHT_MS009', 'CHT_MS010', 'CHT_MS011', 'CHT_MS012', 'CHT_MS013', 'CHT_MS014', 'CHT_MS015', 'CHT_MS016', 'CHT_MS017', 'CHT_MS018', 'CHT_MS019', 'CHT_MS020', 'CHT_MS021', 'CHT_MS022', 'CHT_MS023', 'CHT_MS024', 'CHT_MS025', 'CHT_MS026', 'CHT_MS027', 'CHT_MS028', 'CHT_MS029', 'CHT_MS030', 'CHT_MS031', 'CHT_MS032', 'CHT_MS033', 'CHT_MS034', 'CHT_MS035', 'CHT_MS036', 'CHT_MS037', 'CHT_MS038', 'CHT_MS039', 'CHT_MS040', 'CHT_MS041', 'CHT_MS042', 'CHT_MS043', 'CHT_MS044', 'CHT_MS045', 'CHT_MS046', 'CHT_MS047', 'CHT_MS048', 'CHT_MS049', 'CHT_MS050', 'CHT_MS051', 'CHT_MS052', 'CHT_MS053', 'CHT_MS054', 'CHT_MS055', 'CHT_MS056', 'CHT_MS057', 'CHT_MS058', 'CHT_MS059', 'CHT_MS060', 'CHT_MS061', 'CHT_MS062', 'CHT_MS063', 'CHT_MS064', 'CHT_MS065', 'CHT_MS066', 'CHT_MS067', 'CHT_MS068', 'CHT_MS069', 'CHT_MS070', 'CHT_MS071', 'CHT_MS072', 'CHT_MS073', 'CHT_MS074', 'CHT_MS075', 'CHT_MS076', 'CHT_MS077', 'CHT_MS078', 'CHT_MS079', 'CHT_MS080', 'CHT_MS081', 'CHT_MS082', 'CHT_MS083', 'CHT_MS084', 'CHT_MS085', 'CHT_MS086', 'CHT_MS087', 'CHT_MS088', 'CHT_MS089', 'CHT_MS090', 'CHT_MS091', 'CHT_MS092', 'CHT_MS093', 'CHT_MS094', 'CHT_MS095', 'CHT_MS096', 'CHT_MS097', 'CHT_MS098', 'CHT_MS099', 'CHT_MS100', 'CHT_MS101', 'CHT_MS102', 'CHT_MS103', 'CHT_MS104', 'CHT_MS105', 'CHT_MS106', 'CHT_MS107', 'CHT_MS108', 'CHT_MS109', 'CHT_MS110', 'CHT_MS111', 'CHT_MS112', 'CHT_MS113', 'CHT_MS114', 'CHT_MS115', 'CHT_MS116', 'CHT_MS117', 'CHT_MS118', 'CHT_MS119', 'CHT_MS120', 'CHT_MS121', 'CHT_MS122', 'CHT_MS123', 'CHT_MS124', 'CHT_MS125', 'CHT_MS126', 'CHT_MS127', 'CHT_MS128', 'CHT_MS129', 'CHT_MS130', 'CHT_MS131', 'CHT_MS132', 'CHT_MS133', 'CHT_MS134', 'CHT_MS135', 'CHT_MS136', 'CHT_MS137', 'CHT_MS138', 'CHT_MS139', 'CHT_MS140', 'CHT_MS141', 'CHT_MS142', 'CHT_MS143', 'CHT_MS144', 'CHT_MS145', 'CHT_MS146', 'CHT_MS147', 'CHT_MS148', 'CHT_MS149', 'CHT_MS150', 'CHT_MS151', 'CHT_MS152', 'CHT_MS153', 'CHT_MS154', 'CHT_MS155', 'CHT_MS156', 'CHT_MS157', 'CHT_MS158', 'CHT_MS159', 'CHT_MS160', 'CHT_MS161', 'CHT_MS162', 'CHT_MS163', 'CHT_MS164', 'CHT_MS165', 'CHT_MS166', 'CHT_MS167', 'CHT_MS168', 'CHT_MS169', 'CHT_MS170', 'CHT_MS171', 'CHT_MS172', 'CHT_MS173', 'CHT_MS174', 'CHT_MS175', 'CHT_MS176', 'CHT_MS177', 'CHT_MS178', 'CHT_MS179', 'CHT_MS180', 'CHT_MS181', 'CHT_MS182', 'CHT_MS183', 'CHT_MS184', 'CHT_MS185', 'CHT_MS186', 'CHT_MS187', 'CHT_MS188', 'CHT_MS189', 'CHT_MS190', 'CHT_MS191', 'CHT_MS192', 'CHT_MS193', 'CHT_MS194', 'CHT_MS195', 'CHT_MS196', 'CHT_MS197', 'CHT_MS198', 'CHT_MS199', 'CHT_MS200', 'CHT_MS201', 'CHT_MS202', 'CHT_MS203', 'CHT_MS204', 'CHT_MS205', 'CHT_MS206', 'CHT_MS207', 'CHT_MS208', 'CHT_MS209', 'CHT_MS210', 'CHT_MS211', 'CHT_MS212', 'CHT_MS213', 'CHT_MS214', 'CHT_MS215', 'CHT_MS216', 'CHT_MS217', 'CHT_MS218', 'CHT_MS219', 'CHT_MS220', 'CHT_MS221', 'CHT_MS222', 'CHT_MS223', 'CHT_MS224', 'CHT_MS225', 'CHT_MS226', 'CHT_MS227', 'CHT_MS228', 'CHT_MS229', 'CHT_MS230', 'CHT_MS231', 'CHT_MS232', 'CHT_MS233', 'CHT_MS234', 'CHT_MS235', 'CHT_MS236', 'CHT_MS237', 'CHT_MS238', 'CHT_MS239', 'CHT_MS240', 'CHT_MS241', 'CHT_MS242'], 

['CHT_SB001', 'CHT_SB002', 'CHT_SB003', 'CHT_SB004', 'CHT_SB005', 'CHT_SB006', 'CHT_SB007', 'CHT_SB008', 'CHT_SB009', 'CHT_SB010', 'CHT_SB011', 'CHT_SB012', 'CHT_SB013', 'CHT_SB014', 'CHT_SB015', 'CHT_SB016', 'CHT_SB017', 'CHT_SB018', 'CHT_SB019', 'CHT_SB020', 'CHT_SB021', 'CHT_SB022', 'CHT_SB023', 'CHT_SB024', 'CHT_SB025', 'CHT_SB026', 'CHT_SB027', 'CHT_SB028', 'CHT_SB029', 'CHT_SB030', 'CHT_SB031', 'CHT_SB032', 'CHT_SB033', 'CHT_SB034', 'CHT_SB035', 'CHT_SB036', 'CHT_SB037', 'CHT_SB038', 'CHT_SB039', 'CHT_SB040', 'CHT_SB041', 'CHT_SB042', 'CHT_SB043', 'CHT_SB044', 'CHT_SB045', 'CHT_SB046', 'CHT_SB047', 'CHT_SB048', 'CHT_SB049', 'CHT_SB050', 'CHT_SB051', 'CHT_SB052', 'CHT_SB053', 'CHT_SB054', 'CHT_SB055', 'CHT_SB056', 'CHT_SB057', 'CHT_SB058', 'CHT_SB059', 'CHT_SB060', 'CHT_SB061', 'CHT_SB062', 'CHT_SB063', 'CHT_SB064', 'CHT_SB065', 'CHT_SB066', 'CHT_SB067', 'CHT_SB068', 'CHT_SB069', 'CHT_SB070', 'CHT_SB071', 'CHT_SB072'], 

['debug_00', 'debug_01', 'debug_02', 'sample'], 

['basi_d01', 'basi_d02', 'basi_d03', 'basi_d04', 'basi_d05', 'basi_d06', 'basi_d07', 'basi_d08', 'basi_d09', 'basi_d10', 'basi_d11', 'basi_d12', 'basi_d13', 'basi_d14', 'basi_d15', 'basi_d16', 'basi_d17', 'e731_090', 'e731_100', 'e731_101', 's231_001'], 

['bria_d01', 'bria_d02', 'e312_050', 'e312_060', 'e312_061', 'e312_070', 'e314_010', 's211_002'], 

['brid_d01', 'brid_d05', 'brid_d06', 'brid_d07', 'brid_d08', 'brid_d09', 'brid_d10', 'brid_d11', 'brid_d12', 'brid_d13', 'brid_d14', 'brid_d15', 'brid_d16', 'brid_d17', 'e314_020', 'e314_030', 'e314_030a', 'e314_040', 'e314_040a', 'e314_050', 'e314_060', 'e314_060a', 'e314_070', 'e314_071', 'e314_080', 'e314_090', 'e314_100', 'e314_110', 'e314_120', 's404_001', 's404_003'], 

['cave_d01', 'cave_d02', 'e210_020', 'e210_030', 'e210_040', 'e210_041', 'e628_070', 'e628_080', 'e629_120', 'e629_130', 'e629_140', 'e629_150', 'e629_160', 'e629_161', 'e629_170'], 

['e835_090', 'fall_d04', 'fall_e01', 's220_001'], 

['e523_010', 'e523_020', 'e628_055', 'fend_f12', 'port_i04', 'port_t04'], 

['fend_f13', 'koya_r08', 's230_001', 's230_002'], 

['e523_070', 'fend_f14', 'port_i05', 'port_t05', 's234_001'], 

['e523_120', 'e523_130', 'e523_131', 'fend_f15', 's233_001'], 

['fend_f16'], 

['e526_030', 'e629_080', 'e629_090', 'e629_110', 'e629_111', 'fend_f17'], 

['e730_020', 'e731_010', 'e731_080', 'fodr_f19'], 

['e731_110', 'fodr_f20', 's243_001'], 

['e206_010', 'e206_011', 'e206_011t', 'e206_020', 'e206_031', 'e206_032', 'e206_033', 'fore_d01', 's107_001', 's207_001'], 

['gent_d01', 'gent_d02', 's249_001', 's413_001', 's413_002', 's413_003'], 

['e525_080', 'e525_090', 'e525_091', 'e525_092', 'e525_093', 'e836_020', 'iceb_d01', 'iceb_d02', 'iceb_d03', 'iceb_d04', 'iceb_d05', 'iceb_d08', 'iceb_d09', 'iceb_d10', 'iceb_e01', 'iceb_e02', 's240_001'], 

['e525_030', 'e525_040', 'e525_041', 'e525_050', 'e525_060', 'e525_070', 'iron_d01', 'iron_d02', 'iron_d03', 'iron_d04', 'iron_d05', 'iron_d06', 'iron_d07', 'iron_d08', 'iron_d09', 'iron_d10', 'iron_d11', 'iron_d12', 'iron_d13', 'iron_d14', 'iron_d15', 'iron_d16', 'iron_d17', 'iron_d18', 'iron_d19', 's128_001', 's236_001'], 

['e731_030', 'e731_040', 'e731_050', 'e731_060', 'e731_061', 'e731_062', 'e731_063', 'e731_064', 'e731_065', 'e731_066', 'e731_070', 'e835_030', 'e835_050', 'kone_d02', 'kone_d03', 'kone_d04', 'kone_d05', 'kone_d06', 'kone_d07', 'kone_d08', 'kone_d09', 'kone_d10', 'kone_d11', 'kone_d12', 'kone_d13', 'kone_d14', 'kone_d15', 'kone_d16', 'kone_d17', 'kone_d18', 'kone_d19', 'kone_d20', 'kone_d21', 'kone_d22', 'kone_d23', 'kone_d24', 'kone_d25', 'kone_d26', 'kone_d29', 'kone_d30', 'kone_e01', 's242_001', 's244_002', 's416_003', 's416_004'], 

['e526_060', 'e526_070', 'e526_071', 'e526_072', 'e731_020', 'e833_010', 'e833_020', 'e833_030', 'e833_031', 'e833_032', 'e833_033', 'kot1_d01', 'kot1_d02', 'kot2_d01', 'kot2_d02', 'kot2_d03', 'kot2_d04', 'kot2_d05', 'kot2_d06', 'kot2_d07', 'kot2_d08', 'kot2_d09', 'kot2_d10', 'kot2_d11', 'kot2_d12', 'kot2_d13', 'kot2_d14', 'kot2_d15', 'kot2_d16', 'kot2_d17', 'kot2_d18', 'kot2_d19', 'kot2_d20', 'kot2_d21', 'kot2_d22', 'kot2_d23', 'kot2_d24', 'kot2_d25', 'kot2_d26', 'kot2_d27', 's244_001'], 

['e835_010', 'e835_020', 'e835_040', 'e835_140', 'e835_141', 'e835_142', 'e835_150', 'e835_160', 'e835_170', 'e835_180', 'las1_d01', 'las2_d01', 'las2_d02', 'las2_d03', 'las3_d01', 'las3_d02', 'las4_d01', 'las4_d02', 'las4_e01'], 

['e101_010', 'e101_020', 'e101_021', 'e101_022', 'e103_040', 'e103_041', 'e103_050', 'e103_060', 'e103_061', 'e103_070', 'e208_030', 'e208_031', 'e208_040', 'e418_030', 'e834_070', 'mont_d01', 'mont_d02', 'mont_d03', 's202_001'], 

['e419_040', 'e419_050', 'e419_060', 'e419_061', 'e419_070', 'e419_080', 'e419_081', 'e419_090', 'rock_d01', 'rock_d02', 'rock_d03', 'rock_e01'], 

['sand_d01', 'sand_d02', 'sand_d03', 'sand_d04', 'sand_d05', 'sand_d06', 'sand_d07', 'sand_d08', 'sand_d09', 'sand_d10', 'sand_d11', 'sand_d12', 'sand_d13', 'sand_d14', 'sand_d15', 'sand_d16'], 

['s213_001', 'stra_f08'], 

['koya_r05', 's222_002', 'stra_f09'], 

['s221_002', 's221_005', 'stra_f10'], 

['e522_010', 'port_i03', 'port_t03', 's219_002', 'stra_f11'], 

['e421_020', 's216_001', 'stra_f18'], 

['e524_040', 'e524_050', 'e524_051', 'e524_060', 's134_001', 's239_001', 's239_002', 'snee_d01', 'snee_d02', 'snee_d03', 'snee_d04', 'snee_d05', 'snee_d06', 'snee_d07', 'snee_d08', 'snee_d09', 'snee_d10', 'snee_d11', 'snee_d12', 'snee_d13', 'snee_d14', 'snee_d15', 'snee_d16', 'snee_d17', 'snee_d18', 'snee_d19', 'snee_d20', 'snee_d21', 'snee_d22', 'snee_d23', 'snee_d24', 'snee_d25', 'snee_d26', 'snee_d27', 'snee_d28', 'snee_d29'], 

['e629_100', 'snow_d01', 'snow_d02', 'snow_d03', 'snow_d04', 'snow_d05', 'snow_d06', 'snow_d07', 'snow_d08', 'snow_d09', 'snow_d10', 'snow_d11', 'snow_d12', 'snow_d13', 'snow_d14', 'snow_d15', 'snow_d16', 'snow_d17', 'snow_d18', 'snow_d19', 'snow_d20', 'snow_d21', 'snow_d22', 'snow_d23', 'snow_d24', 'snow_d25', 'snow_d26', 'snow_d27', 'snow_d28'], 

['e420_080', 'e420_090', 'e420_091', 'stda_d01', 'stda_d02'], 

['e315_020', 'e315_030', 'e315_040', 'e315_041', 'e315_050', 'e316_010', 'e316_020', 'e316_030', 'e418_150', 's211_003', 's214_002', 's214_003', 's414_003', 'varo_d01', 'varo_d02', 'varo_d03', 'varo_d04', 'varo_d05', 'varo_d06', 'varo_d07', 'varo_d08', 'varo_d09', 'varo_d10', 'varo_d11', 'varo_d12', 'varo_d13', 'varo_d14', 'varo_d15', 'varo_d16', 'varo_d17', 'varo_d18', 'varo_d19', 'varo_d20', 'varo_d21', 'varo_d22', 'varo_d23', 'varo_d24', 'varo_d25', 'varo_d26', 'varo_d27', 'varo_d28', 'varo_d29', 'varo_d30'], 

['e103_010', 'e103_011', 'e103_110', 'e207_060', 'e207_061', 'e210_090', 'e210_120', 'e210_130', 'e210_140', 'e210_150', 'e316_060', 'e835_110', 'koya_r01', 'port_i01', 'port_t01', 's103_001b', 's206_001', 'wind_e01', 'wind_f01'], 

['e104_060', 'e206_040', 'koya_r02', 's108_001', 'wind_f02'], 

['e102_030', 'e418_090', 'e418_100', 'e418_101', 'e418_120', 'e418_130', 'koya_r04', 'port_i02', 'port_t02', 's103_001c', 'wind_f03'], 

['e208_020', 'e208_021', 'e210_010', 'e210_050', 'e418_020', 'wind_f04'], 

['e312_010', 'e312_020', 'e312_021', 'e312_030', 'e312_040', 'e315_010', 'e836_010', 'koya_r03', 'wind_e05', 'wind_f05'], 

['e312_080', 'e312_090', 'wind_f06'], 

['s210_001', 'wind_f07'], 

['e628_060', 'wind_f21'], 

['e105_020', 'e105_021', 'e105_022', 'e211_030', 'e211_031', 'e835_120', 'winc_d01', 'winc_d02'], 

['s426_003', 's426_004', 's426_005', 's426_006', 's426_007', 's426_008', 's426_009', 's426_010', 's426_011', 's426_012', 's426_013', 'zone_d01', 'zone_d01_01', 'zone_d01_02', 'zone_d01_03', 'zone_d01_04', 'zone_d01_05', 'zone_d01_06', 'zone_d01_07', 'zone_d01_08', 'zone_d01_09', 'zone_d01_10', 'zone_d02', 'zone_d03'], 

['anma_e01', 'anma_i01', 'anma_i02', 'anma_i03', 'anma_i04', 'anma_t01', 'e524_010', 'e524_020', 'e524_030', 'e526_010', 'e526_020', 's238_001', 's238_002', 's411_009', 's414_004'], 

['bera_i01', 'bera_i02', 'bera_i03', 'bera_t01', 'e523_030', 'e523_040', 'e523_050', 'e523_060', 'e523_061', 'e523_062', 's122_001', 's229_002', 's408_001', 's408_002', 's408_002b', 's408_003', 's408_004', 's411_007'], 

['test_ikeda'], 

['e523_090', 'e523_100', 'e523_110', 'e525_010', 'e525_020', 'e526_040', 'e627_010', 'e627_020', 'e627_030', 'fend_e01', 'fend_i01', 'fend_i02', 'fend_i03', 'fend_i04', 'fend_i05', 'fend_i06', 'fend_i07', 'fend_t01', 'fend_t02', 'port_i06', 's125_001', 's126_001', 's127_001', 's127_002', 's128_002', 's129_001', 's234_002', 's409_001', 's409_002', 's409_003', 's409_004', 's411_008', 's430_001'], 

['kame_d01', 's212_001', 's414_002'], 

['koya_r06', 's424_004'], 

['e313_010', 'e313_020', 'e313_030', 'e313_040', 'e313_050', 'lake_e01', 'lake_e02', 'lake_i01', 'lake_i02', 'lake_i03', 'lake_i04', 'lake_t01', 'lake_t02', 'lake_t03', 's211_001', 's411_001'], 

['e102_010', 'e102_020', 'e102_040', 'e102_050', 'e102_060', 'e103_020', 'e103_020s', 'e103_030', 'e103_080', 'e103_090', 'e103_100', 'e105_030', 'e105_040', 'e208_010', 'e209_010', 'e209_020', 'e209_030', 'e209_040', 'e209_050', 'e210_060', 'e210_061', 'e210_070', 'e210_080', 'e210_081', 'e210_100', 'e317_010', 'e317_020', 'e317_021', 'e317_022', 'e418_010', 'e418_040', 'e418_050', 'e418_060', 'e418_061', 'e418_062', 'e418_070', 'e418_080', 'e418_110', 'e629_010', 'e629_020', 'e629_030', 'e629_040', 'e629_050', 'e629_060', 'e629_070', 'e834_010', 'e834_020', 'e834_030', 'e834_040', 'e834_050', 'e834_051', 'e834_060', 'e834_080', 'e834_090', 'e834_100', 'e834_110', 'e834_120', 'e834_130', 'e834_140', 'e834_150', 'e836_040', 'e836_041', 'lan1_i01', 'lan1_i02', 'lan1_i03', 'lan1_i04', 'lan1_i05', 'lan1_i07', 'lan1_t01', 'lan2_e01', 'lan2_e02', 'lan2_i01', 'lan2_i02', 'lan2_i03', 'lan2_i04', 'lan2_i05', 'lan2_i06', 'lan2_i07', 'lan2_t01', 'lan2_t01_01', 'lan3_e01', 'lan3_t01', 'lan4_t01', 's101_001', 's102_001', 's103_001', 's105_001', 's105_002', 's112_002', 's119_001', 's132_001', 's201_001', 's201_002', 's203_001', 's203_003', 's204_001', 's208_001', 's214_001', 's402_001', 's402_002', 's402_003', 's402_004', 's409_005', 's411_010', 's411_011', 's426_002'], 

['neko_e01', 'neko_i01', 'neko_t01', 's245_001', 's246_001', 's247_001', 's248_001'], 

['e419_010', 'e628_010', 'e628_050', 'olle_i01', 'olle_t01', 's218_001', 's218_002', 's401_002', 's401_003', 's411_003'], 

['e730_030', 'e730_040', 'e730_041', 'e730_042', 'e732_010', 'e732_011', 'e835_070', 'othe_e01', 'othe_i01', 'othe_i02', 'othe_i03', 'othe_i04', 'othe_t01', 'othe_t02', 'othe_t03', 's134_002', 's241_001', 's241_002', 's241_003', 's241_004', 's416_001', 's416_002'], 

['ozwe_d01', 'ozwe_d02', 's224_001'], 

['e522_030', 'e522_040', 'e522_041', 'e522_050', 'riot_i01', 'riot_i02', 'riot_t01', 's225_001', 's407_001', 's407_002', 's411_006'], 

['e419_020', 'e419_030', 'e628_020', 'e628_030', 'e628_040', 's217_001', 's405_001', 's405_003', 's411_004', 'sabl_i01', 'sabl_i02', 'sabl_i03', 'sabl_t01'], 

['e730_010', 'e833_040', 'shat_i01', 'shat_i02', 'shat_i03', 'shat_i04'], 

['e103_120', 'e105_050', 'e207_050', 'e210_160', 'e316_050', 'e418_140', 'e522_020', 'e522_060', 'e523_080', 'e526_050', 'e627_040', 's215_002', 's235_002', 'ship_e01', 'ship_e02', 'ship_e03', 'ship_e04', 'ship_e05', 'ship_e06', 'ship_e07', 'ship_e08', 'ship_e09', 'ship_e10'], 

['e420_010', 'e420_020', 'e420_030', 'e420_040', 'e420_050', 'e420_060', 'e420_070', 'e421_010', 'e836_030', 's120_001', 's121_001', 's136_002', 's221_001', 's221_003', 's221_004', 's221_006', 's222_001', 's222_003', 's223_001', 's411_005', 'strt_e01', 'strt_i01', 'strt_i02', 'strt_i03', 'strt_i04', 'strt_i05', 'strt_i06', 'strt_t01', 'strt_t01_01', 'strt_t01_02', 'strt_t01_03', 'strt_t02', 'strt_t03'], 

['s419_002', 's419_003', 's420_001', 'supa_r01', 'supa_r02'], 

['mg01_e01', 'mg02_e01', 'sysm_d01'], 

['e104_010', 'e104_020', 'e104_030', 'e104_040', 'e104_050', 'e104_070', 'e104_080', 'e104_090', 'e105_010', 'e105_051', 'e207_010', 'e207_020', 'e207_030', 'e207_040', 'e211_010', 'e211_020', 's112_001', 's203_002', 's205_001', 's205_002', 's219_001', 's401_001', 's411_002', 's414_001', 's431_001', 'win1_i03', 'win1_i04', 'win1_i06', 'win1_i07', 'win1_i08', 'win1_i09', 'win1_t01', 'win1_t02', 'win1_t03', 'win2_i01', 'win2_i02', 'win2_i03', 'win2_i04', 'win2_i05', 'win2_i06', 'win2_i07', 'win2_i08', 'win2_i09', 'win2_t01', 'win2_t02', 'win2_t03'], 

['ActInfo', 'Navigation', 'CharName', 'MapName'], 

['TOG_S01', 'TOG_S02', 'TOG_S03', 'TOG_S04', 'TOG_S05', 'TOG_S06', 'TOG_S07', 'TOG_S08', 'TOG_S09', 'TOG_S10', 'TOG_S11'], 

['DR00002344','DR00002345','DR00002346','DR00002347','DR00002348','DR00002349','DR00002350','DR00002372','DR00002374','DR00002375','DR00002377','DR00002378','DR00002380','DR00002382','DR00002384','DR00002386','DR00002387','DR00002388','DR00002389','DR00002390','DR00002391','DR00002392','DR00002394','DR00002395','DR00002396','DR00002397','DR00002398','DR00002400','DR00002401','DR00002402','DR00002403','DR00002404','DR00002405','DR00002406','DR00002407','DR00002408','DR00002409','DR00002410','DR00002411','DR00002412','DR00002413','DR00002414','DR00002415','DR00002416','DR00002418','DR00002419','DR00002420','DR00002421','DR00002422','DR00002423','DR00002424','DR00002425','DR00002426','DR00002427','DR00002428','DR00002429','DR00002430','DR00002431','DR00002432','DR00002433','DR00002434','DR00002436','DR00002437','DR00002439','DR00002441','DR00002442','DR00002443','DR00002445','DR00002447','DR00002448','DR00002449','DR00002450','DR00002452','DR00002454','DR00002456','DR00002458','DR00002459','DR00002461','DR00002462','DR00002464','DR00002465','DR00002467','DR00002468','DR00002470','DR00002472','DR00002473','DR00002474','DR00002475','DR00002476','DR00002477','DR00002478','DR00002479','DR00002480','DR00002481','DR00002482','DR00002484','DR00002485','DR00002486','DR00002488','DR00002491','DR00002493','DR00002495','DR00002496','DR00002497','DR00002499','DR00002501','DR00002503','DR00002504','DR00002505','DR00002507','DR00002509','DR00002510','DR00002511','DR00002513','DR00002514','DR00002515','DR00002516','DR00002517','DR00002518','DR00002519','DR00002520','DR00002521','DR00002522','DR00002523','DR00002524','DR00002525','DR00002526','DR00002527','DR00002528','DR00002529','DR00002530','DR00002531','DR00002532','DR00002533','DR00002534','DR00002535','DR00002536','DR00002537','DR00002538','DR00002539','DR00002540','DR00002541','DR00002542','DR00002543','DR00002544','DR00002545','DR00002546','DR00002547','DR00002548','DR00002549','DR00002550','DR00002551','DR00002552','DR00002553','DR00002554','DR00002555','DR00002556','DR00002557','DR00002560','DR00002561','DR00002562','DR00002563','DR00002564','DR00002565','DR00002566','DR00002567','DR00002569','DR00002570','DR00002571','DR00002572','DR00002573','DR00002574','DR00002575','DR00002577','DR00002579','DR00002580','DR00002581','DR00002582','DR00002583','DR00002584','DR00002585','DR00002586','DR00002587','DR00002589','DR00002590','DR00002592','DR00002594','DR00002596','DR00002597','DR00002598','DR00002599','DR00002600','DR00002601','DR00002602','DR00002603','DR00002604','DR00002605','DR00002607','DR00002609','DR00002610','DR00002612','DR00002613','DR00002614','DR00002615','DR00002616','DR00002617','DR00002618','DR00002619','DR00002620','DR00002622','DR00002624','DR00002625','DR00002626','DR00002627','DR00002628','DR00002630','DR00002631','DR00002632','DR00002634','DR00002636','DR00002637','DR00002639','DR00002640','DR00002642','DR00002643','DR00002645','DR00002647','DR00002648','DR00002650','DR00002652','DR00002653','DR00002654','DR00002655','DR00002656','DR00002657','DR00002659','DR00002661','DR00002662','DR00002664','DR00002665','DR00002666','DR00002667','DR00002668','DR00002669','DR00002671','DR00002673','DR00002675','DR00002676','DR00002678','DR00002680','DR00002681','DR00002682','DR00002684','DR00002685','DR00002686','DR00002687','DR00002688','DR00002689','DR00002690','DR00002691','DR00002692','DR00002693','DR00002694','DR00002695','DR00002696','DR00002697','DR00002698','DR00002699','DR00002700','DR00002701','DR00002702','DR00002703','DR00002704','DR00002705','DR00002706','DR00002707','DR00002708','DR00002709','DR00002710','DR00002711','DR00002712','DR00002714','DR00002715','DR00002716','DR00002718','DR00002719','DR00002720','DR00002721','DR00002722','DR00002723','DR00002724','DR00002725','DR00002726','DR00002727','DR00002728','DR00002729','DR00002730','DR00002731','DR00002732','DR00002733','DR00002734','DR00002735','DR00002736','DR00002737','DR00002738','DR00002739','DR00002740','DR00002741','DR00002742','DR00002743','DR00002744','DR00002745','DR00002746','DR00002747','DR00002748','DR00002749','DR00002750','DR00002751','DR00002753','DR00002754','DR00002755','DR00002756','DR00002757','DR00002758','DR00002759','DR00002760','DR00002761','DR00002762','DR00002763','DR00002766','DR00002767','DR00002768','DR00002769','DR00002770','DR00002771','DR00002772','DR00002774','DR00002775','DR00002776','DR00002778','DR00002779','DR00002780','DR00002781','DR00002782','DR00002783','DR00002784','DR00002785','DR00002787','DR00002788','DR00002789','DR00002790','DR00002791','DR00002793','DR00002794','DR00002798','DR00002799','DR00002800','DR00002801','DR00002802','DR00002803','DR00002805','DR00002806','DR00002807','DR00002809','DR00002811','DR00002813','DR00002814','DR00002815','DR00002816','DR00002817','DR00002818','DR00002819','DR00002820','DR00002821','DR00002822','DR00002823','DR00002824','DR00002825','DR00002826','DR00002827','DR00002828','DR00002830','DR00002831','DR00002832','DR00002834','DR00002835','DR00002836','DR00002838','DR00002840','DR00002841','DR00002843','DR00002845','DR00002846','DR00002847','DR00002848','DR00002849','DR00002850','DR00002852','DR00002853','DR00002855','DR00002857','DR00002858','DR00002860','DR00002861','DR00002863','DR00002864','DR00002865','DR00002866','DR00002867','DR00002868','DR00002870','DR00002871','DR00002872','DR00002873','DR00002874','DR00002875','DR00002877','DR00002878','DR00002880','DR00002882','DR00002883','DR00002884','DR00002885','DR00002886','DR00002887','DR00002889','DR00002890','DR00002891','DR00002892','DR00002893','DR00002894','DR00002896','DR00002897','DR00002899','DR00002900','DR00002902','DR00002903','DR00002904','DR00002906','DR00002907','DR00002908','DR00002909','DR00002910','DR00002911','DR00002912','DR00002913','DR00002915','DR00002917','DR00002919','DR00002921','DR00002922','DR00002924','DR00002925','DR00002926','DR00002928','DR00002930','DR00002932','DR00002933','DR00002935','DR00002936','DR00002937','DR00002939','DR00002941','DR00002942','DR00002943','DR00002945','DR00002946','DR00002947','DR00002948','DR00002949','DR00002950','DR00002951','DR00002953','DR00002954','DR00002956','DR00002957','DR00002958','DR00002959','DR00002960','DR00002961','DR00002962','DR00002963','DR00002964','DR00002965','DR00002966','DR00002967','DR00002968','DR00002969','DR00002970','DR00002971','DR00002972','DR00002973','DR00002974','DR00002975','DR00002976','DR00002977','DR00002978','DR00002979','DR00002980','DR00002981','DR00002982','DR00002983','DR00002984','DR00002985','DR00002986','DR00002987','DR00002988','DR00002989','DR00002990','DR00002991','DR00002992','DR00002993','DR00002995','DR00002997','DR00002999','DR00003001','DR00003002','DR00003003','DR00003005','DR00003006','DR00003007','DR00003009','DR00003010','DR00003011','DR00003012','DR00003014','DR00003015','DR00003016','DR00003017','DR00003018','DR00003019','DR00003020','DR00003021','DR00003022','DR00003023','DR00003024','DR00003025','DR00003026','DR00003027','DR00003028','DR00003029','DR00003030','DR00003031','DR00003032','DR00003033','DR00003034','DR00003035','DR00003036','DR00003037','DR00003038','DR00003039','DR00003040','DR00003041','DR00003042','DR00003043','DR00003044','DR00003045','DR00003046','DR00003047','DR00003048','DR00003049','DR00003050','DR00003051','DR00003052','DR00003053','DR00003055','DR00003056','DR00003058','DR00003059','DR00003061','DR00003062','DR00003063','DR00003064','DR00003066','DR00003067','DR00003068','DR00003069','DR00003070','DR00003071','DR00003072','DR00003075','DR00003076','DR00003077','DR00003078','DR00003079','DR00003080','DR00003081','DR00003082','DR00003083','DR00003084','DR00003086','DR00003087','DR00003088','DR00003089','DR00003090','DR00003091','DR00003092','DR00003093','DR00003094','DR00003096','DR00003097','DR00003098','DR00003099','DR00003100','DR00003101','DR00003102','DR00003103','DR00003104','DR00003105','DR00003106','DR00003107','DR00003108','DR00003109','DR00003110','DR00003111','DR00003112','DR00003113','DR00003114','DR00003115','DR00003116','DR00003117','DR00003118','DR00003119','DR00003121','DR00003122','DR00003123','DR00003125','DR00003127','DR00003129','DR00003130','DR00003131','DR00003132','DR00003133','DR00003134','DR00003136','DR00003138','DR00003139','DR00003141','DR00003142','DR00003144','DR00003145','DR00003147','DR00003149','DR00003150','DR00003151','DR00003152','DR00003153','DR00003155','DR00003156','DR00003157','DR00003159','DR00003161','DR00003163','DR00003164','DR00003165','DR00003166','DR00003168','DR00003169','DR00003170','DR00003171','DR00003172','DR00003174','DR00003175','DR00003177','DR00003179','DR00003180','DR00003181','DR00003182','DR00003183','DR00003186','DR00003187','DR00003188','DR00003189','DR00003192','DR00003193','DR00003195','DR00003196','DR00003197','DR00003198','DR00003199','DR00003200','DR00003201','DR00003202','DR00003203','DR00003204','DR00003206','DR00003207','DR00003208','DR00003209','DR00003210','DR00003211','DR00003213','DR00003214','DR00003215','DR00003216','DR00003217','DR00003218','DR00003219','DR00003220','DR00003221','DR00003222','DR00003223','DR00003224','DR00003225','DR00003226','DR00003227','DR00003229','DR00003230','DR00003231','DR00003232','DR00003233','DR00003234','DR00003235','DR00003236','DR00003237','DR00003239','DR00003240','DR00003242','DR00003243','DR00003244','DR00003245','DR00003246','DR00003247','DR00003248','DR00003249','DR00003250','DR00003251','DR00003252','DR00003253','DR00003254','DR00003255','DR00003256','DR00003257','DR00003258','DR00003259','DR00003260','DR00003261','DR00003262','DR00003263','DR00003264','DR00003265','DR00003266','DR00003267','DR00003268','DR00003269','DR00003270','DR00003271','DR00003272','DR00003273','DR00003274','DR00003275','DR00003276','DR00003277','DR00003278','DR00003279','DR00003280','DR00003281','DR00003282','DR00003283','DR00003284','DR00003285','DR00003286','DR00003287','DR00003288','DR00003289','DR00003290','DR00003291','DR00003292','DR00003293','DR00003294','DR00003295','DR00003296','DR00003298','DR00003299','DR00003300','DR00003301','DR00003302','DR00003303','DR00003304','DR00003305','DR00003306','DR00003307','DR00003308','DR00003309','DR00003310','DR00003311','DR00003312','DR00003313','DR00003314','DR00003315','DR00003316','DR00003317','DR00003319','DR00003320','DR00003321','DR00003322','DR00003323','DR00003324','DR00003325','DR00003326','DR00003327','DR00003328','DR00003329','DR00003330','DR00003331','DR00003332','DR00003333','DR00003334','DR00003336','DR00003337','DR00003338','DR00003339','DR00003340','DR00003341','DR00003342','DR00003343','DR00003344','DR00003346','DR00003347','DR00003348','DR00003349','DR00003350','DR00003351','DR00003352','DR00003353','DR00003354','DR00003355','DR00003357','DR00003359','DR00003360','DR00003362','DR00003363','DR00003364','DR00003365','DR00003366','DR00003367','DR00003368','DR00003369','DR00003370','DR00003372','DR00003374','DR00003376','DR00003378','DR00003380','DR00003381','DR00003383','DR00003385','DR00003386','DR00003388','DR00003390','DR00003391','DR00003393','DR00003394','DR00003396','DR00003398','DR00003399','DR00003401','DR00003403','DR00003404','DR00003406','DR00003407','DR00003408','DR00003409','DR00003411','DR00003413','DR00003415','DR00003416','DR00003418','DR00003419','DR00003420','DR00003421','DR00003422','DR00003423','DR00003425','DR00003426','DR00003428','DR00003430','DR00003431','DR00003432','DR00003434','DR00003435','DR00003436','DR00003437','DR00003438','DR00003439','DR00003440','DR00003441','DR00003442','DR00003443','DR00003445','DR00003446','DR00003447','DR00003448','DR00003449','DR00003450','DR00003451','DR00003452','DR00003453','DR00003454','DR00003455','DR00003456','DR00003458','DR00003459','DR00003461','DR00003463','DR00003465','DR00003466','DR00003467','DR00003469','DR00003470','DR00003471','DR00003472','DR00003473','DR00003474','DR00003475','DR00003476','DR00003477','DR00003479','DR00003480','DR00003481','DR00003482','DR00003484','DR00003485','DR00003486','DR00003487','DR00003488','DR00003489','DR00003490','DR00003491','DR00003492','DR00003493','DR00003494','DR00003495','DR00003496','DR00003497','DR00003498','DR00003499','DR00003500','DR00003501','DR00003502','DR00003503','DR00003504','DR00003505','DR00003506','DR00003507','DR00003508','DR00003509','DR00003510','DR00003511','DR00003512','DR00003514','DR00003515','DR00003517','DR00003518','DR00003519','DR00003520','DR00003521','DR00003523','DR00003524','DR00003525','DR00003526','DR00003527','DR00003528','DR00003529','DR00003530','DR00003531','DR00003532','DR00003533','DR00003534','DR00003535','DR00003536','DR00003537','DR00003538','DR00003539','DR00003540','DR00003541','DR00003542','DR00003544','DR00003545','DR00003546','DR00003547','DR00003548','DR00003549','DR00003550','DR00003551','DR00003552','DR00003553','DR00003554','DR00003555','DR00003556','DR00003557','DR00003558','DR00003559','DR00003560','DR00003562','DR00003563','DR00003564','DR00003565','DR00003566','DR00003567','DR00003568','DR00003569','DR00003570','DR00003571','DR00003572','DR00003573','DR00003574','DR00003575','DR00003576','DR00003577','DR00003578','DR00003579','DR00003580','DR00003581','DR00003582','DR00003583','DR00003587','DR00003590','DR00003591','DR00003592','DR00003593','DR00003595','DR00003597','DR00003598','DR00003599','DR00003601','DR00003603','DR00003604','DR00003606','DR00003607','DR00003608','DR00003609','DR00003611','DR00003612','DR00003613','DR00003614','DR00003615','DR00003616','DR00003617','DR00003618','DR00003619','DR00003620','DR00003621','DR00003622','DR00003623','DR00003625','DR00003627','DR00003629','DR00003630','DR00003631','DR00003632','DR00003634','DR00003636','DR00003638','DR00003639','DR00003640','DR00003642','DR00003643','DR00003644','DR00003645','DR00003646','DR00003647','DR00003648','DR00003649','DR00003650','DR00003651','DR00003652','DR00003653','DR00003654','DR00003655','DR00003656','DR00003657','DR00003658','DR00003659','DR00003660','DR00003662','DR00003663','DR00003664','DR00003665','DR00003666','DR00003667','DR00003668','DR00003669','DR00003670','DR00003671','DR00003672','DR00003674','DR00003675','DR00003676','DR00003677','DR00003678','DR00003679','DR00003680','DR00003681','DR00003682','DR00003683','DR00003684','DR00003685','DR00003686','DR00003687','DR00003688','DR00003689','DR00003690','DR00003691','DR00003692','DR00003693','DR00003694','DR00003695','DR00003697','DR00003698','DR00003699','DR00003700','DR00003701','DR00003702','DR00003704','DR00003705','DR00003707','DR00003708','DR00003709','DR00003710','DR00003711','DR00003712','DR00003713','DR00003714','DR00003715','DR00003716','DR00003717','DR00003718','DR00003719','DR00003720','DR00003721','DR00003722','DR00003723','DR00003724','DR00003725','DR00003726','DR00003727','DR00003728','DR00003729','DR00003730','DR00003731','DR00003732','DR00003733','DR00003734','DR00003735','DR00003736','DR00003737','DR00003738','DR00003739','DR00003740','DR00003741','DR00003742','DR00003743','DR00003744','DR00003745','DR00003746','DR00003747','DR00003748','DR00003749','DR00003750','DR00003751','DR00003752','DR00003753','DR00003754','DR00003755','DR00003756','DR00003757','DR00003758','DR00003759','DR00003760','DR00003761','DR00003762','DR00003763','DR00003764','DR00003765','DR00003766','DR00003767','DR00003768','DR00003769','DR00003770','DR00003771','DR00003772','DR00003773','DR00003774','DR00003775','DR00003776','DR00003777','DR00003778','DR00003779','DR00003780','DR00003781','DR00003782','DR00003783','DR00003784','DR00003785','DR00003786','DR00003787','DR00003788','DR00003789','DR00003790','DR00003791','DR00003792','DR00003793','DR00003794','DR00003795','DR00003796','DR00003797','DR00003798','DR00003799','DR00003800','DR00003801','DR00003802','DR00003803','DR00003804','DR00003805','DR00003806','DR00003807','DR00003808','DR00003809','DR00003810','DR00003811','DR00003812','DR00003813','DR00003814','DR00003815','DR00003816','DR00003817','DR00003818','DR00003819','DR00003820','DR00003821','DR00003822','DR00003823','DR00003824','DR00003825','DR00003826','DR00003827','DR00003828','DR00003829','DR00003830','DR00003831','DR00003832','DR00003833','DR00003834','DR00003835','DR00003836','DR00003837','DR00003838','DR00003839','DR00003840','DR00003841','DR00003842','DR00003843','DR00003844','DR00003845','DR00003846','DR00003847','DR00003848','DR00003849','DR00003850','DR00003851','DR00003852','DR00003853','DR00003854','DR00003855','DR00003856','DR00003857','DR00003858','DR00003859','DR00003860','DR00003861','DR00003862','DR00003863','DR00003864','DR00003865','DR00003866','DR00003867','DR00003868','DR00003869','DR00003870','DR00003871','DR00003872','DR00003873','DR00003874','DR00003875','DR00003876','DR00003877','DR00003878','DR00003879','DR00003880','DR00003881','DR00003882','DR00003883','DR00003884','DR00003885','DR00003886','DR00003887','DR00003888','DR00003889','DR00003890','DR00003891','DR00003892','DR00003893','DR00003894','DR00003895','DR00003896','DR00003897','DR00003898','DR00003899','DR00003900','DR00003901','DR00003902','DR00003903','DR00003904','DR00003905','DR00003906','DR00003907','DR00003908','DR00003909','DR00003910','DR00003911','DR00003912','DR00003913','DR00003914','DR00003915','DR00003916','DR00003917','DR00003918','DR00003919','DR00003920','DR00003921','DR00003922','DR00003923','DRMenu00002311','DRMenu00002312','DRMenu00002313','DRMenu00002314','DRMenu00002315','DRMenu00002316','DRMenu00002317','DRMenu00002318','DRMenu00002319','DRMenu00002320','DRMenu00002321','DRMenu00002322','DRMenu00002323','DRMenu00002324','DRMenu00002325','DRMenu00002326','DRMenu00002327','DRMenu00002328','DRMenu00002329','DRMenu00002330','DRMenu00002331','DRMenu00002332','DRMenu00002333','DRMenu00002334','DRMenu00002335','DRMenu00002336','DRMenu00002337','DRMenu00002338','DRMenu00002339','DRMenu00002340','DRMenu00002341','DRMenu00002342','DRMenu00003925','DRMenu00003926','DRMenu00003927','DRMenu00003928','DRMenu00003929','DRMenu00003930','DRMenu00003931','DRMenu00003932','DRMenu00003933','DRMenu00003934','DRMenu00003935','DRMenu00003936','DRMenu00003937','DRMenu00003938','DRMenu00003939','DRMenu00003940','DRMenu00003941','DRMenu00003942','DRMenu00003943','DRMenu00003944','DRMenu00003945','DRMenu00003946','DRMenu00003947','DRMenu00003948','DRMenu00003949','DRMenu00003950','DRMenu00003951','DRMenu00003952','DRMenu00003953','DRMenu00003954','DRMenu00003955','DRMenu00003956','DRMenu00003966'],

['SysString'],

]





ByType = [

['Skits', 'Story Events', 'Sub Events', 'Movies', 'NPC locations', 'Menu', 'System Strings', 'Debug',
#'DR',
'Graces-f', 'Xillia'],

['CHT_MS001', 'CHT_MS002', 'CHT_MS003', 'CHT_MS004', 'CHT_MS005', 'CHT_MS006', 'CHT_MS007', 'CHT_MS008', 'CHT_MS009', 'CHT_MS010', 'CHT_MS011', 'CHT_MS012', 'CHT_MS013', 'CHT_MS014', 'CHT_MS015', 'CHT_MS016', 'CHT_MS017', 'CHT_MS018', 'CHT_MS019', 'CHT_MS020', 'CHT_MS021', 'CHT_MS022', 'CHT_MS023', 'CHT_MS024', 'CHT_MS025', 'CHT_MS026', 'CHT_MS027', 'CHT_MS028', 'CHT_MS029', 'CHT_MS030', 'CHT_MS031', 'CHT_MS032', 'CHT_MS033', 'CHT_MS034', 'CHT_MS035', 'CHT_MS036', 'CHT_MS037', 'CHT_MS038', 'CHT_MS039', 'CHT_MS040', 'CHT_MS041', 'CHT_MS042', 'CHT_MS043', 'CHT_MS044', 'CHT_MS045', 'CHT_MS046', 'CHT_MS047', 'CHT_MS048', 'CHT_MS049', 'CHT_MS050', 'CHT_MS051', 'CHT_MS052', 'CHT_MS053', 'CHT_MS054', 'CHT_MS055', 'CHT_MS056', 'CHT_MS057', 'CHT_MS058', 'CHT_MS059', 'CHT_MS060', 'CHT_MS061', 'CHT_MS062', 'CHT_MS063', 'CHT_MS064', 'CHT_MS065', 'CHT_MS066', 'CHT_MS067', 'CHT_MS068', 'CHT_MS069', 'CHT_MS070', 'CHT_MS071', 'CHT_MS072', 'CHT_MS073', 'CHT_MS074', 'CHT_MS075', 'CHT_MS076', 'CHT_MS077', 'CHT_MS078', 'CHT_MS079', 'CHT_MS080', 'CHT_MS081', 'CHT_MS082', 'CHT_MS083', 'CHT_MS084', 'CHT_MS085', 'CHT_MS086', 'CHT_MS087', 'CHT_MS088', 'CHT_MS089', 'CHT_MS090', 'CHT_MS091', 'CHT_MS092', 'CHT_MS093', 'CHT_MS094', 'CHT_MS095', 'CHT_MS096', 'CHT_MS097', 'CHT_MS098', 'CHT_MS099', 'CHT_MS100', 'CHT_MS101', 'CHT_MS102', 'CHT_MS103', 'CHT_MS104', 'CHT_MS105', 'CHT_MS106', 'CHT_MS107', 'CHT_MS108', 'CHT_MS109', 'CHT_MS110', 'CHT_MS111', 'CHT_MS112', 'CHT_MS113', 'CHT_MS114', 'CHT_MS115', 'CHT_MS116', 'CHT_MS117', 'CHT_MS118', 'CHT_MS119', 'CHT_MS120', 'CHT_MS121', 'CHT_MS122', 'CHT_MS123', 'CHT_MS124', 'CHT_MS125', 'CHT_MS126', 'CHT_MS127', 'CHT_MS128', 'CHT_MS129', 'CHT_MS130', 'CHT_MS131', 'CHT_MS132', 'CHT_MS133', 'CHT_MS134', 'CHT_MS135', 'CHT_MS136', 'CHT_MS137', 'CHT_MS138', 'CHT_MS139', 'CHT_MS140', 'CHT_MS141', 'CHT_MS142', 'CHT_MS143', 'CHT_MS144', 'CHT_MS145', 'CHT_MS146', 'CHT_MS147', 'CHT_MS148', 'CHT_MS149', 'CHT_MS150', 'CHT_MS151', 'CHT_MS152', 'CHT_MS153', 'CHT_MS154', 'CHT_MS155', 'CHT_MS156', 'CHT_MS157', 'CHT_MS158', 'CHT_MS159', 'CHT_MS160', 'CHT_MS161', 'CHT_MS162', 'CHT_MS163', 'CHT_MS164', 'CHT_MS165', 'CHT_MS166', 'CHT_MS167', 'CHT_MS168', 'CHT_MS169', 'CHT_MS170', 'CHT_MS171', 'CHT_MS172', 'CHT_MS173', 'CHT_MS174', 'CHT_MS175', 'CHT_MS176', 'CHT_MS177', 'CHT_MS178', 'CHT_MS179', 'CHT_MS180', 'CHT_MS181', 'CHT_MS182', 'CHT_MS183', 'CHT_MS184', 'CHT_MS185', 'CHT_MS186', 'CHT_MS187', 'CHT_MS188', 'CHT_MS189', 'CHT_MS190', 'CHT_MS191', 'CHT_MS192', 'CHT_MS193', 'CHT_MS194', 'CHT_MS195', 'CHT_MS196', 'CHT_MS197', 'CHT_MS198', 'CHT_MS199', 'CHT_MS200', 'CHT_MS201', 'CHT_MS202', 'CHT_MS203', 'CHT_MS204', 'CHT_MS205', 'CHT_MS206', 'CHT_MS207', 'CHT_MS208', 'CHT_MS209', 'CHT_MS210', 'CHT_MS211', 'CHT_MS212', 'CHT_MS213', 'CHT_MS214', 'CHT_MS215', 'CHT_MS216', 'CHT_MS217', 'CHT_MS218', 'CHT_MS219', 'CHT_MS220', 'CHT_MS221', 'CHT_MS222', 'CHT_MS223', 'CHT_MS224', 'CHT_MS225', 'CHT_MS226', 'CHT_MS227', 'CHT_MS228', 'CHT_MS229', 'CHT_MS230', 'CHT_MS231', 'CHT_MS232', 'CHT_MS233', 'CHT_MS234', 'CHT_MS235', 'CHT_MS236', 'CHT_MS237', 'CHT_MS238', 'CHT_MS239', 'CHT_MS240', 'CHT_MS241', 'CHT_MS242','CHT_SB001', 'CHT_SB002', 'CHT_SB003', 'CHT_SB004', 'CHT_SB005', 'CHT_SB006', 'CHT_SB007', 'CHT_SB008', 'CHT_SB009', 'CHT_SB010', 'CHT_SB011', 'CHT_SB012', 'CHT_SB013', 'CHT_SB014', 'CHT_SB015', 'CHT_SB016', 'CHT_SB017', 'CHT_SB018', 'CHT_SB019', 'CHT_SB020', 'CHT_SB021', 'CHT_SB022', 'CHT_SB023', 'CHT_SB024', 'CHT_SB025', 'CHT_SB026', 'CHT_SB027', 'CHT_SB028', 'CHT_SB029', 'CHT_SB030', 'CHT_SB031', 'CHT_SB032', 'CHT_SB033', 'CHT_SB034', 'CHT_SB035', 'CHT_SB036', 'CHT_SB037', 'CHT_SB038', 'CHT_SB039', 'CHT_SB040', 'CHT_SB041', 'CHT_SB042', 'CHT_SB043', 'CHT_SB044', 'CHT_SB045', 'CHT_SB046', 'CHT_SB047', 'CHT_SB048', 'CHT_SB049', 'CHT_SB050', 'CHT_SB051', 'CHT_SB052', 'CHT_SB053', 'CHT_SB054', 'CHT_SB055', 'CHT_SB056', 'CHT_SB057', 'CHT_SB058', 'CHT_SB059', 'CHT_SB060', 'CHT_SB061', 'CHT_SB062', 'CHT_SB063', 'CHT_SB064', 'CHT_SB065', 'CHT_SB066', 'CHT_SB067', 'CHT_SB068', 'CHT_SB069', 'CHT_SB070', 'CHT_SB071', 'CHT_SB072'], 

['e101_010', 'e101_020', 'e101_021', 'e101_022', 'e102_010', 'e102_020', 'e102_030', 'e102_040', 'e102_050', 'e102_060', 'e103_010', 'e103_011', 'e103_020', 'e103_020s', 'e103_030', 'e103_040', 'e103_041', 'e103_050', 'e103_060', 'e103_061', 'e103_070', 'e103_080', 'e103_090', 'e103_100', 'e103_110', 'e103_120', 'e104_010', 'e104_020', 'e104_030', 'e104_040', 'e104_050', 'e104_060', 'e104_070', 'e104_080', 'e104_090', 'e105_010', 'e105_020', 'e105_021', 'e105_022', 'e105_030', 'e105_040', 'e105_050', 'e105_051', 'e206_010', 'e206_011', 'e206_011t', 'e206_020', 'e206_031', 'e206_032', 'e206_033', 'e206_040', 'e207_010', 'e207_020', 'e207_030', 'e207_040', 'e207_050', 'e207_060', 'e207_061', 'e208_010', 'e208_020', 'e208_021', 'e208_030', 'e208_031', 'e208_040', 'e209_010', 'e209_020', 'e209_030', 'e209_040', 'e209_050', 'e210_010', 'e210_020', 'e210_030', 'e210_040', 'e210_041', 'e210_050', 'e210_060', 'e210_061', 'e210_070', 'e210_080', 'e210_081', 'e210_090', 'e210_100', 'e210_120', 'e210_130', 'e210_140', 'e210_150', 'e210_160', 'e211_010', 'e211_020', 'e211_030', 'e211_031', 'e312_010', 'e312_020', 'e312_021', 'e312_030', 'e312_040', 'e312_050', 'e312_060', 'e312_061', 'e312_070', 'e312_080', 'e312_090', 'e313_010', 'e313_020', 'e313_030', 'e313_040', 'e313_050', 'e314_010', 'e314_020', 'e314_030', 'e314_030a', 'e314_040', 'e314_040a', 'e314_050', 'e314_060', 'e314_060a', 'e314_070', 'e314_071', 'e314_080', 'e314_090', 'e314_100', 'e314_110', 'e314_120', 'e315_010', 'e315_020', 'e315_030', 'e315_040', 'e315_041', 'e315_050', 'e316_010', 'e316_020', 'e316_030', 'e316_050', 'e316_060', 'e317_010', 'e317_020', 'e317_021', 'e317_022', 'e418_010', 'e418_020', 'e418_030', 'e418_040', 'e418_050', 'e418_060', 'e418_061', 'e418_062', 'e418_070', 'e418_080', 'e418_090', 'e418_100', 'e418_101', 'e418_110', 'e418_120', 'e418_130', 'e418_140', 'e418_150', 'e419_010', 'e419_020', 'e419_030', 'e419_040', 'e419_050', 'e419_060', 'e419_061', 'e419_070', 'e419_080', 'e419_081', 'e419_090', 'e420_010', 'e420_020', 'e420_030', 'e420_040', 'e420_050', 'e420_060', 'e420_070', 'e420_080', 'e420_090', 'e420_091', 'e421_010', 'e421_020', 'e522_010', 'e522_020', 'e522_030', 'e522_040', 'e522_041', 'e522_050', 'e522_060', 'e523_010', 'e523_020', 'e523_030', 'e523_040', 'e523_050', 'e523_060', 'e523_061', 'e523_062', 'e523_070', 'e523_080', 'e523_090', 'e523_100', 'e523_110', 'e523_120', 'e523_130', 'e523_131', 'e524_010', 'e524_020', 'e524_030', 'e524_040', 'e524_050', 'e524_051', 'e524_060', 'e525_010', 'e525_020', 'e525_030', 'e525_040', 'e525_041', 'e525_050', 'e525_060', 'e525_070', 'e525_080', 'e525_090', 'e525_091', 'e525_092', 'e525_093', 'e526_010', 'e526_020', 'e526_030', 'e526_040', 'e526_050', 'e526_060', 'e526_070', 'e526_071', 'e526_072', 'e627_010', 'e627_020', 'e627_030', 'e627_040', 'e628_010', 'e628_020', 'e628_030', 'e628_040', 'e628_050', 'e628_055', 'e628_060', 'e628_070', 'e628_080', 'e629_010', 'e629_020', 'e629_030', 'e629_040', 'e629_050', 'e629_060', 'e629_070', 'e629_080', 'e629_090', 'e629_100', 'e629_110', 'e629_111', 'e629_120', 'e629_130', 'e629_140', 'e629_150', 'e629_160', 'e629_161', 'e629_170', 'e730_010', 'e730_020', 'e730_030', 'e730_040', 'e730_041', 'e730_042', 'e731_010', 'e731_020', 'e731_030', 'e731_040', 'e731_050', 'e731_060', 'e731_061', 'e731_062', 'e731_063', 'e731_064', 'e731_065', 'e731_066', 'e731_070', 'e731_080', 'e731_090', 'e731_100', 'e731_101', 'e731_110', 'e732_010', 'e732_011', 'e833_010', 'e833_020', 'e833_030', 'e833_031', 'e833_032', 'e833_033', 'e833_040', 'e834_010', 'e834_020', 'e834_030', 'e834_040', 'e834_050', 'e834_051', 'e834_060', 'e834_070', 'e834_080', 'e834_090', 'e834_100', 'e834_110', 'e834_120', 'e834_130', 'e834_140', 'e834_150', 'e835_010', 'e835_020', 'e835_030', 'e835_040', 'e835_050', 'e835_070', 'e835_090', 'e835_110', 'e835_120', 'e835_140', 'e835_141', 'e835_142', 'e835_150', 'e835_160', 'e835_170', 'e835_180', 'e836_010', 'e836_020', 'e836_030', 'e836_040', 'e836_041'],

['s101_001', 's102_001', 's103_001', 's103_001b', 's103_001c', 's105_001', 's105_002', 's107_001', 's108_001', 's112_001', 's112_002', 's119_001', 's120_001', 's121_001', 's122_001', 's125_001', 's126_001', 's127_001', 's127_002', 's128_001', 's128_002', 's129_001', 's132_001', 's134_001', 's134_002', 's136_002', 's201_001', 's201_002', 's202_001', 's203_001', 's203_002', 's203_003', 's204_001', 's205_001', 's205_002', 's206_001', 's207_001', 's208_001', 's210_001', 's211_001', 's211_002', 's211_003', 's212_001', 's213_001', 's214_001', 's214_002', 's214_003', 's215_002', 's216_001', 's217_001', 's218_001', 's218_002', 's219_001', 's219_002', 's220_001', 's221_001', 's221_002', 's221_003', 's221_004', 's221_005', 's221_006', 's222_001', 's222_002', 's222_003', 's223_001', 's224_001', 's225_001', 's229_002', 's230_001', 's230_002', 's231_001', 's233_001', 's234_001', 's234_002', 's235_002', 's236_001', 's238_001', 's238_002', 's239_001', 's239_002', 's240_001', 's241_001', 's241_002', 's241_003', 's241_004', 's242_001', 's243_001', 's244_001', 's244_002', 's245_001', 's246_001', 's247_001', 's248_001', 's249_001', 's401_001', 's401_002', 's401_003', 's402_001', 's402_002', 's402_003', 's402_004', 's404_001', 's404_003', 's405_001', 's405_003', 's407_001', 's407_002', 's408_001', 's408_002', 's408_002b', 's408_003', 's408_004', 's409_001', 's409_002', 's409_003', 's409_004', 's409_005', 's411_001', 's411_002', 's411_003', 's411_004', 's411_005', 's411_006', 's411_007', 's411_008', 's411_009', 's411_010', 's411_011', 's413_001', 's413_002', 's413_003', 's414_001', 's414_002', 's414_003', 's414_004', 's416_001', 's416_002', 's416_003', 's416_004', 's419_002', 's419_003', 's420_001', 's424_004', 's426_002', 's426_003', 's426_004', 's426_005', 's426_006', 's426_007', 's426_008', 's426_009', 's426_010', 's426_011', 's426_012', 's426_013', 's430_001', 's431_001'],

['TOG_S01', 'TOG_S02', 'TOG_S03', 'TOG_S04', 'TOG_S05', 'TOG_S06', 'TOG_S07', 'TOG_S08', 'TOG_S09', 'TOG_S10', 'TOG_S11'],

['anma_e01', 'anma_i01', 'anma_i02', 'anma_i03', 'anma_i04', 'anma_t01', 'basi_d01', 'basi_d02', 'basi_d03', 'basi_d04', 'basi_d05', 'basi_d06', 'basi_d07', 'basi_d08', 'basi_d09', 'basi_d10', 'basi_d11', 'basi_d12', 'basi_d13', 'basi_d14', 'basi_d15', 'basi_d16', 'basi_d17', 'bera_i01', 'bera_i02', 'bera_i03', 'bera_t01', 'bria_d01', 'bria_d02', 'brid_d01', 'brid_d05', 'brid_d06', 'brid_d07', 'brid_d08', 'brid_d09', 'brid_d10', 'brid_d11', 'brid_d12', 'brid_d13', 'brid_d14', 'brid_d15', 'brid_d16', 'brid_d17', 'cave_d01', 'cave_d02', 'fall_d04', 'fall_e01', 'fend_e01', 'fend_f12', 'fend_f13', 'fend_f14', 'fend_f15', 'fend_f16', 'fend_f17', 'fend_i01', 'fend_i02', 'fend_i03', 'fend_i04', 'fend_i05', 'fend_i06', 'fend_i07', 'fend_t01', 'fend_t02', 'fodr_f19', 'fodr_f20', 'fore_d01', 'gent_d01', 'gent_d02', 'iceb_d01', 'iceb_d02', 'iceb_d03', 'iceb_d04', 'iceb_d05', 'iceb_d08', 'iceb_d09', 'iceb_d10', 'iceb_e01', 'iceb_e02', 'iron_d01', 'iron_d02', 'iron_d03', 'iron_d04', 'iron_d05', 'iron_d06', 'iron_d07', 'iron_d08', 'iron_d09', 'iron_d10', 'iron_d11', 'iron_d12', 'iron_d13', 'iron_d14', 'iron_d15', 'iron_d16', 'iron_d17', 'iron_d18', 'iron_d19', 'kame_d01', 'kone_d02', 'kone_d03', 'kone_d04', 'kone_d05', 'kone_d06', 'kone_d07', 'kone_d08', 'kone_d09', 'kone_d10', 'kone_d11', 'kone_d12', 'kone_d13', 'kone_d14', 'kone_d15', 'kone_d16', 'kone_d17', 'kone_d18', 'kone_d19', 'kone_d20', 'kone_d21', 'kone_d22', 'kone_d23', 'kone_d24', 'kone_d25', 'kone_d26', 'kone_d29', 'kone_d30', 'kone_e01', 'kot1_d01', 'kot1_d02', 'kot2_d01', 'kot2_d02', 'kot2_d03', 'kot2_d04', 'kot2_d05', 'kot2_d06', 'kot2_d07', 'kot2_d08', 'kot2_d09', 'kot2_d10', 'kot2_d11', 'kot2_d12', 'kot2_d13', 'kot2_d14', 'kot2_d15', 'kot2_d16', 'kot2_d17', 'kot2_d18', 'kot2_d19', 'kot2_d20', 'kot2_d21', 'kot2_d22', 'kot2_d23', 'kot2_d24', 'kot2_d25', 'kot2_d26', 'kot2_d27', 'koya_r01', 'koya_r02', 'koya_r03', 'koya_r04', 'koya_r05', 'koya_r06', 'koya_r08', 'lake_e01', 'lake_e02', 'lake_i01', 'lake_i02', 'lake_i03', 'lake_i04', 'lake_t01', 'lake_t02', 'lake_t03', 'lan1_i01', 'lan1_i02', 'lan1_i03', 'lan1_i04', 'lan1_i05', 'lan1_i07', 'lan1_t01', 'lan2_e01', 'lan2_e02', 'lan2_i01', 'lan2_i02', 'lan2_i03', 'lan2_i04', 'lan2_i05', 'lan2_i06', 'lan2_i07', 'lan2_t01', 'lan2_t01_01', 'lan3_e01', 'lan3_t01', 'lan4_t01', 'las1_d01', 'las2_d01', 'las2_d02', 'las2_d03', 'las3_d01', 'las3_d02', 'las4_d01', 'las4_d02', 'las4_e01', 'mg01_e01', 'mg02_e01', 'mont_d01', 'mont_d02', 'mont_d03', 'neko_e01', 'neko_i01', 'neko_t01', 'olle_i01', 'olle_t01', 'othe_e01', 'othe_i01', 'othe_i02', 'othe_i03', 'othe_i04', 'othe_t01', 'othe_t02', 'othe_t03', 'ozwe_d01', 'ozwe_d02', 'port_i01', 'port_i02', 'port_i03', 'port_i04', 'port_i05', 'port_i06', 'port_t01', 'port_t02', 'port_t03', 'port_t04', 'port_t05', 'riot_i01', 'riot_i02', 'riot_t01', 'rock_d01', 'rock_d02', 'rock_d03', 'rock_e01', 'sabl_i01', 'sabl_i02', 'sabl_i03', 'sabl_t01', 'sand_d01', 'sand_d02', 'sand_d03', 'sand_d04', 'sand_d05', 'sand_d06', 'sand_d07', 'sand_d08', 'sand_d09', 'sand_d10', 'sand_d11', 'sand_d12', 'sand_d13', 'sand_d14', 'sand_d15', 'sand_d16', 'shat_i01', 'shat_i02', 'shat_i03', 'shat_i04', 'ship_e01', 'ship_e02', 'ship_e03', 'ship_e04', 'ship_e05', 'ship_e06', 'ship_e07', 'ship_e08', 'ship_e09', 'ship_e10', 'snee_d01', 'snee_d02', 'snee_d03', 'snee_d04', 'snee_d05', 'snee_d06', 'snee_d07', 'snee_d08', 'snee_d09', 'snee_d10', 'snee_d11', 'snee_d12', 'snee_d13', 'snee_d14', 'snee_d15', 'snee_d16', 'snee_d17', 'snee_d18', 'snee_d19', 'snee_d20', 'snee_d21', 'snee_d22', 'snee_d23', 'snee_d24', 'snee_d25', 'snee_d26', 'snee_d27', 'snee_d28', 'snee_d29', 'snow_d01', 'snow_d02', 'snow_d03', 'snow_d04', 'snow_d05', 'snow_d06', 'snow_d07', 'snow_d08', 'snow_d09', 'snow_d10', 'snow_d11', 'snow_d12', 'snow_d13', 'snow_d14', 'snow_d15', 'snow_d16', 'snow_d17', 'snow_d18', 'snow_d19', 'snow_d20', 'snow_d21', 'snow_d22', 'snow_d23', 'snow_d24', 'snow_d25', 'snow_d26', 'snow_d27', 'snow_d28', 'stda_d01', 'stda_d02', 'stra_f08', 'stra_f09', 'stra_f10', 'stra_f11', 'stra_f18', 'strt_e01', 'strt_i01', 'strt_i02', 'strt_i03', 'strt_i04', 'strt_i05', 'strt_i06', 'strt_t01', 'strt_t01_01', 'strt_t01_02', 'strt_t01_03', 'strt_t02', 'strt_t03', 'supa_r01', 'supa_r02', 'sysm_d01', 'varo_d01', 'varo_d02', 'varo_d03', 'varo_d04', 'varo_d05', 'varo_d06', 'varo_d07', 'varo_d08', 'varo_d09', 'varo_d10', 'varo_d11', 'varo_d12', 'varo_d13', 'varo_d14', 'varo_d15', 'varo_d16', 'varo_d17', 'varo_d18', 'varo_d19', 'varo_d20', 'varo_d21', 'varo_d22', 'varo_d23', 'varo_d24', 'varo_d25', 'varo_d26', 'varo_d27', 'varo_d28', 'varo_d29', 'varo_d30', 'win1_i03', 'win1_i04', 'win1_i06', 'win1_i07', 'win1_i08', 'win1_i09', 'win1_t01', 'win1_t02', 'win1_t03', 'win2_i01', 'win2_i02', 'win2_i03', 'win2_i04', 'win2_i05', 'win2_i06', 'win2_i07', 'win2_i08', 'win2_i09', 'win2_t01', 'win2_t02', 'win2_t03', 'winc_d01', 'winc_d02', 'wind_e01', 'wind_e05', 'wind_f01', 'wind_f02', 'wind_f03', 'wind_f04', 'wind_f05', 'wind_f06', 'wind_f07', 'wind_f21', 'zone_d01', 'zone_d01_01', 'zone_d01_02', 'zone_d01_03', 'zone_d01_04', 'zone_d01_05', 'zone_d01_06', 'zone_d01_07', 'zone_d01_08', 'zone_d01_09', 'zone_d01_10', 'zone_d02', 'zone_d03'],

['Artes', 'ArteNames', 'Battle', 'Discovery', 'GradeShop-Missions', 'Item', 'MonsterBook', 'Skills', 'System', 'soundTest', 'Tactics', 'Titles', 'Tutorial', 'TOG_SS_ChatName', 'TOG_SS_StringECommerce'],

['ActInfo', 'CharName', 'Navigation', 'SysString', 'endingData', 'MapName'],

['debug_00', 'debug_01', 'debug_02', 'sample', 'test_ikeda'],

#['DR00002344','DR00002345','DR00002346','DR00002347','DR00002348','DR00002349','DR00002350','DR00002372','DR00002374','DR00002375','DR00002377','DR00002378','DR00002380','DR00002382','DR00002384','DR00002386','DR00002387','DR00002388','DR00002389','DR00002390','DR00002391','DR00002392','DR00002394','DR00002395','DR00002396','DR00002397','DR00002398','DR00002400','DR00002401','DR00002402','DR00002403','DR00002404','DR00002405','DR00002406','DR00002407','DR00002408','DR00002409','DR00002410','DR00002411','DR00002412','DR00002413','DR00002414','DR00002415','DR00002416','DR00002418','DR00002419','DR00002420','DR00002421','DR00002422','DR00002423','DR00002424','DR00002425','DR00002426','DR00002427','DR00002428','DR00002429','DR00002430','DR00002431','DR00002432','DR00002433','DR00002434','DR00002436','DR00002437','DR00002439','DR00002441','DR00002442','DR00002443','DR00002445','DR00002447','DR00002448','DR00002449','DR00002450','DR00002452','DR00002454','DR00002456','DR00002458','DR00002459','DR00002461','DR00002462','DR00002464','DR00002465','DR00002467','DR00002468','DR00002470','DR00002472','DR00002473','DR00002474','DR00002475','DR00002476','DR00002477','DR00002478','DR00002479','DR00002480','DR00002481','DR00002482','DR00002484','DR00002485','DR00002486','DR00002488','DR00002491','DR00002493','DR00002495','DR00002496','DR00002497','DR00002499','DR00002501','DR00002503','DR00002504','DR00002505','DR00002507','DR00002509','DR00002510','DR00002511','DR00002513','DR00002514','DR00002515','DR00002516','DR00002517','DR00002518','DR00002519','DR00002520','DR00002521','DR00002522','DR00002523','DR00002524','DR00002525','DR00002526','DR00002527','DR00002528','DR00002529','DR00002530','DR00002531','DR00002532','DR00002533','DR00002534','DR00002535','DR00002536','DR00002537','DR00002538','DR00002539','DR00002540','DR00002541','DR00002542','DR00002543','DR00002544','DR00002545','DR00002546','DR00002547','DR00002548','DR00002549','DR00002550','DR00002551','DR00002552','DR00002553','DR00002554','DR00002555','DR00002556','DR00002557','DR00002560','DR00002561','DR00002562','DR00002563','DR00002564','DR00002565','DR00002566','DR00002567','DR00002569','DR00002570','DR00002571','DR00002572','DR00002573','DR00002574','DR00002575','DR00002577','DR00002579','DR00002580','DR00002581','DR00002582','DR00002583','DR00002584','DR00002585','DR00002586','DR00002587','DR00002589','DR00002590','DR00002592','DR00002594','DR00002596','DR00002597','DR00002598','DR00002599','DR00002600','DR00002601','DR00002602','DR00002603','DR00002604','DR00002605','DR00002607','DR00002609','DR00002610','DR00002612','DR00002613','DR00002614','DR00002615','DR00002616','DR00002617','DR00002618','DR00002619','DR00002620','DR00002622','DR00002624','DR00002625','DR00002626','DR00002627','DR00002628','DR00002630','DR00002631','DR00002632','DR00002634','DR00002636','DR00002637','DR00002639','DR00002640','DR00002642','DR00002643','DR00002645','DR00002647','DR00002648','DR00002650','DR00002652','DR00002653','DR00002654','DR00002655','DR00002656','DR00002657','DR00002659','DR00002661','DR00002662','DR00002664','DR00002665','DR00002666','DR00002667','DR00002668','DR00002669','DR00002671','DR00002673','DR00002675','DR00002676','DR00002678','DR00002680','DR00002681','DR00002682','DR00002684','DR00002685','DR00002686','DR00002687','DR00002688','DR00002689','DR00002690','DR00002691','DR00002692','DR00002693','DR00002694','DR00002695','DR00002696','DR00002697','DR00002698','DR00002699','DR00002700','DR00002701','DR00002702','DR00002703','DR00002704','DR00002705','DR00002706','DR00002707','DR00002708','DR00002709','DR00002710','DR00002711','DR00002712','DR00002714','DR00002715','DR00002716','DR00002718','DR00002719','DR00002720','DR00002721','DR00002722','DR00002723','DR00002724','DR00002725','DR00002726','DR00002727','DR00002728','DR00002729','DR00002730','DR00002731','DR00002732','DR00002733','DR00002734','DR00002735','DR00002736','DR00002737','DR00002738','DR00002739','DR00002740','DR00002741','DR00002742','DR00002743','DR00002744','DR00002745','DR00002746','DR00002747','DR00002748','DR00002749','DR00002750','DR00002751','DR00002753','DR00002754','DR00002755','DR00002756','DR00002757','DR00002758','DR00002759','DR00002760','DR00002761','DR00002762','DR00002763','DR00002766','DR00002767','DR00002768','DR00002769','DR00002770','DR00002771','DR00002772','DR00002774','DR00002775','DR00002776','DR00002778','DR00002779','DR00002780','DR00002781','DR00002782','DR00002783','DR00002784','DR00002785','DR00002787','DR00002788','DR00002789','DR00002790','DR00002791','DR00002793','DR00002794','DR00002798','DR00002799','DR00002800','DR00002801','DR00002802','DR00002803','DR00002805','DR00002806','DR00002807','DR00002809','DR00002811','DR00002813','DR00002814','DR00002815','DR00002816','DR00002817','DR00002818','DR00002819','DR00002820','DR00002821','DR00002822','DR00002823','DR00002824','DR00002825','DR00002826','DR00002827','DR00002828','DR00002830','DR00002831','DR00002832','DR00002834','DR00002835','DR00002836','DR00002838','DR00002840','DR00002841','DR00002843','DR00002845','DR00002846','DR00002847','DR00002848','DR00002849','DR00002850','DR00002852','DR00002853','DR00002855','DR00002857','DR00002858','DR00002860','DR00002861','DR00002863','DR00002864','DR00002865','DR00002866','DR00002867','DR00002868','DR00002870','DR00002871','DR00002872','DR00002873','DR00002874','DR00002875','DR00002877','DR00002878','DR00002880','DR00002882','DR00002883','DR00002884','DR00002885','DR00002886','DR00002887','DR00002889','DR00002890','DR00002891','DR00002892','DR00002893','DR00002894','DR00002896','DR00002897','DR00002899','DR00002900','DR00002902','DR00002903','DR00002904','DR00002906','DR00002907','DR00002908','DR00002909','DR00002910','DR00002911','DR00002912','DR00002913','DR00002915','DR00002917','DR00002919','DR00002921','DR00002922','DR00002924','DR00002925','DR00002926','DR00002928','DR00002930','DR00002932','DR00002933','DR00002935','DR00002936','DR00002937','DR00002939','DR00002941','DR00002942','DR00002943','DR00002945','DR00002946','DR00002947','DR00002948','DR00002949','DR00002950','DR00002951','DR00002953','DR00002954','DR00002956','DR00002957','DR00002958','DR00002959','DR00002960','DR00002961','DR00002962','DR00002963','DR00002964','DR00002965','DR00002966','DR00002967','DR00002968','DR00002969','DR00002970','DR00002971','DR00002972','DR00002973','DR00002974','DR00002975','DR00002976','DR00002977','DR00002978','DR00002979','DR00002980','DR00002981','DR00002982','DR00002983','DR00002984','DR00002985','DR00002986','DR00002987','DR00002988','DR00002989','DR00002990','DR00002991','DR00002992','DR00002993','DR00002995','DR00002997','DR00002999','DR00003001','DR00003002','DR00003003','DR00003005','DR00003006','DR00003007','DR00003009','DR00003010','DR00003011','DR00003012','DR00003014','DR00003015','DR00003016','DR00003017','DR00003018','DR00003019','DR00003020','DR00003021','DR00003022','DR00003023','DR00003024','DR00003025','DR00003026','DR00003027','DR00003028','DR00003029','DR00003030','DR00003031','DR00003032','DR00003033','DR00003034','DR00003035','DR00003036','DR00003037','DR00003038','DR00003039','DR00003040','DR00003041','DR00003042','DR00003043','DR00003044','DR00003045','DR00003046','DR00003047','DR00003048','DR00003049','DR00003050','DR00003051','DR00003052','DR00003053','DR00003055','DR00003056','DR00003058','DR00003059','DR00003061','DR00003062','DR00003063','DR00003064','DR00003066','DR00003067','DR00003068','DR00003069','DR00003070','DR00003071','DR00003072','DR00003075','DR00003076','DR00003077','DR00003078','DR00003079','DR00003080','DR00003081','DR00003082','DR00003083','DR00003084','DR00003086','DR00003087','DR00003088','DR00003089','DR00003090','DR00003091','DR00003092','DR00003093','DR00003094','DR00003096','DR00003097','DR00003098','DR00003099','DR00003100','DR00003101','DR00003102','DR00003103','DR00003104','DR00003105','DR00003106','DR00003107','DR00003108','DR00003109','DR00003110','DR00003111','DR00003112','DR00003113','DR00003114','DR00003115','DR00003116','DR00003117','DR00003118','DR00003119','DR00003121','DR00003122','DR00003123','DR00003125','DR00003127','DR00003129','DR00003130','DR00003131','DR00003132','DR00003133','DR00003134','DR00003136','DR00003138','DR00003139','DR00003141','DR00003142','DR00003144','DR00003145','DR00003147','DR00003149','DR00003150','DR00003151','DR00003152','DR00003153','DR00003155','DR00003156','DR00003157','DR00003159','DR00003161','DR00003163','DR00003164','DR00003165','DR00003166','DR00003168','DR00003169','DR00003170','DR00003171','DR00003172','DR00003174','DR00003175','DR00003177','DR00003179','DR00003180','DR00003181','DR00003182','DR00003183','DR00003186','DR00003187','DR00003188','DR00003189','DR00003192','DR00003193','DR00003195','DR00003196','DR00003197','DR00003198','DR00003199','DR00003200','DR00003201','DR00003202','DR00003203','DR00003204','DR00003206','DR00003207','DR00003208','DR00003209','DR00003210','DR00003211','DR00003213','DR00003214','DR00003215','DR00003216','DR00003217','DR00003218','DR00003219','DR00003220','DR00003221','DR00003222','DR00003223','DR00003224','DR00003225','DR00003226','DR00003227','DR00003229','DR00003230','DR00003231','DR00003232','DR00003233','DR00003234','DR00003235','DR00003236','DR00003237','DR00003239','DR00003240','DR00003242','DR00003243','DR00003244','DR00003245','DR00003246','DR00003247','DR00003248','DR00003249','DR00003250','DR00003251','DR00003252','DR00003253','DR00003254','DR00003255','DR00003256','DR00003257','DR00003258','DR00003259','DR00003260','DR00003261','DR00003262','DR00003263','DR00003264','DR00003265','DR00003266','DR00003267','DR00003268','DR00003269','DR00003270','DR00003271','DR00003272','DR00003273','DR00003274','DR00003275','DR00003276','DR00003277','DR00003278','DR00003279','DR00003280','DR00003281','DR00003282','DR00003283','DR00003284','DR00003285','DR00003286','DR00003287','DR00003288','DR00003289','DR00003290','DR00003291','DR00003292','DR00003293','DR00003294','DR00003295','DR00003296','DR00003298','DR00003299','DR00003300','DR00003301','DR00003302','DR00003303','DR00003304','DR00003305','DR00003306','DR00003307','DR00003308','DR00003309','DR00003310','DR00003311','DR00003312','DR00003313','DR00003314','DR00003315','DR00003316','DR00003317','DR00003319','DR00003320','DR00003321','DR00003322','DR00003323','DR00003324','DR00003325','DR00003326','DR00003327','DR00003328','DR00003329','DR00003330','DR00003331','DR00003332','DR00003333','DR00003334','DR00003336','DR00003337','DR00003338','DR00003339','DR00003340','DR00003341','DR00003342','DR00003343','DR00003344','DR00003346','DR00003347','DR00003348','DR00003349','DR00003350','DR00003351','DR00003352','DR00003353','DR00003354','DR00003355','DR00003357','DR00003359','DR00003360','DR00003362','DR00003363','DR00003364','DR00003365','DR00003366','DR00003367','DR00003368','DR00003369','DR00003370','DR00003372','DR00003374','DR00003376','DR00003378','DR00003380','DR00003381','DR00003383','DR00003385','DR00003386','DR00003388','DR00003390','DR00003391','DR00003393','DR00003394','DR00003396','DR00003398','DR00003399','DR00003401','DR00003403','DR00003404','DR00003406','DR00003407','DR00003408','DR00003409','DR00003411','DR00003413','DR00003415','DR00003416','DR00003418','DR00003419','DR00003420','DR00003421','DR00003422','DR00003423','DR00003425','DR00003426','DR00003428','DR00003430','DR00003431','DR00003432','DR00003434','DR00003435','DR00003436','DR00003437','DR00003438','DR00003439','DR00003440','DR00003441','DR00003442','DR00003443','DR00003445','DR00003446','DR00003447','DR00003448','DR00003449','DR00003450','DR00003451','DR00003452','DR00003453','DR00003454','DR00003455','DR00003456','DR00003458','DR00003459','DR00003461','DR00003463','DR00003465','DR00003466','DR00003467','DR00003469','DR00003470','DR00003471','DR00003472','DR00003473','DR00003474','DR00003475','DR00003476','DR00003477','DR00003479','DR00003480','DR00003481','DR00003482','DR00003484','DR00003485','DR00003486','DR00003487','DR00003488','DR00003489','DR00003490','DR00003491','DR00003492','DR00003493','DR00003494','DR00003495','DR00003496','DR00003497','DR00003498','DR00003499','DR00003500','DR00003501','DR00003502','DR00003503','DR00003504','DR00003505','DR00003506','DR00003507','DR00003508','DR00003509','DR00003510','DR00003511','DR00003512','DR00003514','DR00003515','DR00003517','DR00003518','DR00003519','DR00003520','DR00003521','DR00003523','DR00003524','DR00003525','DR00003526','DR00003527','DR00003528','DR00003529','DR00003530','DR00003531','DR00003532','DR00003533','DR00003534','DR00003535','DR00003536','DR00003537','DR00003538','DR00003539','DR00003540','DR00003541','DR00003542','DR00003544','DR00003545','DR00003546','DR00003547','DR00003548','DR00003549','DR00003550','DR00003551','DR00003552','DR00003553','DR00003554','DR00003555','DR00003556','DR00003557','DR00003558','DR00003559','DR00003560','DR00003562','DR00003563','DR00003564','DR00003565','DR00003566','DR00003567','DR00003568','DR00003569','DR00003570','DR00003571','DR00003572','DR00003573','DR00003574','DR00003575','DR00003576','DR00003577','DR00003578','DR00003579','DR00003580','DR00003581','DR00003582','DR00003583','DR00003587','DR00003590','DR00003591','DR00003592','DR00003593','DR00003595','DR00003597','DR00003598','DR00003599','DR00003601','DR00003603','DR00003604','DR00003606','DR00003607','DR00003608','DR00003609','DR00003611','DR00003612','DR00003613','DR00003614','DR00003615','DR00003616','DR00003617','DR00003618','DR00003619','DR00003620','DR00003621','DR00003622','DR00003623','DR00003625','DR00003627','DR00003629','DR00003630','DR00003631','DR00003632','DR00003634','DR00003636','DR00003638','DR00003639','DR00003640','DR00003642','DR00003643','DR00003644','DR00003645','DR00003646','DR00003647','DR00003648','DR00003649','DR00003650','DR00003651','DR00003652','DR00003653','DR00003654','DR00003655','DR00003656','DR00003657','DR00003658','DR00003659','DR00003660','DR00003662','DR00003663','DR00003664','DR00003665','DR00003666','DR00003667','DR00003668','DR00003669','DR00003670','DR00003671','DR00003672','DR00003674','DR00003675','DR00003676','DR00003677','DR00003678','DR00003679','DR00003680','DR00003681','DR00003682','DR00003683','DR00003684','DR00003685','DR00003686','DR00003687','DR00003688','DR00003689','DR00003690','DR00003691','DR00003692','DR00003693','DR00003694','DR00003695','DR00003697','DR00003698','DR00003699','DR00003700','DR00003701','DR00003702','DR00003704','DR00003705','DR00003707','DR00003708','DR00003709','DR00003710','DR00003711','DR00003712','DR00003713','DR00003714','DR00003715','DR00003716','DR00003717','DR00003718','DR00003719','DR00003720','DR00003721','DR00003722','DR00003723','DR00003724','DR00003725','DR00003726','DR00003727','DR00003728','DR00003729','DR00003730','DR00003731','DR00003732','DR00003733','DR00003734','DR00003735','DR00003736','DR00003737','DR00003738','DR00003739','DR00003740','DR00003741','DR00003742','DR00003743','DR00003744','DR00003745','DR00003746','DR00003747','DR00003748','DR00003749','DR00003750','DR00003751','DR00003752','DR00003753','DR00003754','DR00003755','DR00003756','DR00003757','DR00003758','DR00003759','DR00003760','DR00003761','DR00003762','DR00003763','DR00003764','DR00003765','DR00003766','DR00003767','DR00003768','DR00003769','DR00003770','DR00003771','DR00003772','DR00003773','DR00003774','DR00003775','DR00003776','DR00003777','DR00003778','DR00003779','DR00003780','DR00003781','DR00003782','DR00003783','DR00003784','DR00003785','DR00003786','DR00003787','DR00003788','DR00003789','DR00003790','DR00003791','DR00003792','DR00003793','DR00003794','DR00003795','DR00003796','DR00003797','DR00003798','DR00003799','DR00003800','DR00003801','DR00003802','DR00003803','DR00003804','DR00003805','DR00003806','DR00003807','DR00003808','DR00003809','DR00003810','DR00003811','DR00003812','DR00003813','DR00003814','DR00003815','DR00003816','DR00003817','DR00003818','DR00003819','DR00003820','DR00003821','DR00003822','DR00003823','DR00003824','DR00003825','DR00003826','DR00003827','DR00003828','DR00003829','DR00003830','DR00003831','DR00003832','DR00003833','DR00003834','DR00003835','DR00003836','DR00003837','DR00003838','DR00003839','DR00003840','DR00003841','DR00003842','DR00003843','DR00003844','DR00003845','DR00003846','DR00003847','DR00003848','DR00003849','DR00003850','DR00003851','DR00003852','DR00003853','DR00003854','DR00003855','DR00003856','DR00003857','DR00003858','DR00003859','DR00003860','DR00003861','DR00003862','DR00003863','DR00003864','DR00003865','DR00003866','DR00003867','DR00003868','DR00003869','DR00003870','DR00003871','DR00003872','DR00003873','DR00003874','DR00003875','DR00003876','DR00003877','DR00003878','DR00003879','DR00003880','DR00003881','DR00003882','DR00003883','DR00003884','DR00003885','DR00003886','DR00003887','DR00003888','DR00003889','DR00003890','DR00003891','DR00003892','DR00003893','DR00003894','DR00003895','DR00003896','DR00003897','DR00003898','DR00003899','DR00003900','DR00003901','DR00003902','DR00003903','DR00003904','DR00003905','DR00003906','DR00003907','DR00003908','DR00003909','DR00003910','DR00003911','DR00003912','DR00003913','DR00003914','DR00003915','DR00003916','DR00003917','DR00003918','DR00003919','DR00003920','DR00003921','DR00003922','DR00003923','DRMenu00002311','DRMenu00002312','DRMenu00002313','DRMenu00002314','DRMenu00002315','DRMenu00002316','DRMenu00002317','DRMenu00002318','DRMenu00002319','DRMenu00002320','DRMenu00002321','DRMenu00002322','DRMenu00002323','DRMenu00002324','DRMenu00002325','DRMenu00002326','DRMenu00002327','DRMenu00002328','DRMenu00002329','DRMenu00002330','DRMenu00002331','DRMenu00002332','DRMenu00002333','DRMenu00002334','DRMenu00002335','DRMenu00002336','DRMenu00002337','DRMenu00002338','DRMenu00002339','DRMenu00002340','DRMenu00002341','DRMenu00002342','DRMenu00003925','DRMenu00003926','DRMenu00003927','DRMenu00003928','DRMenu00003929','DRMenu00003930','DRMenu00003931','DRMenu00003932','DRMenu00003933','DRMenu00003934','DRMenu00003935','DRMenu00003936','DRMenu00003937','DRMenu00003938','DRMenu00003939','DRMenu00003940','DRMenu00003941','DRMenu00003942','DRMenu00003943','DRMenu00003944','DRMenu00003945','DRMenu00003946','DRMenu00003947','DRMenu00003948','DRMenu00003949','DRMenu00003950','DRMenu00003951','DRMenu00003952','DRMenu00003953','DRMenu00003954','DRMenu00003955','DRMenu00003956','DRMenu00003966'],

['ActInfo-f', 'CharName-f', 'CHT_PR001-f', 'CHT_PR002-f', 'CHT_PR003-f', 'CHT_PR005-f', 'CHT_PR007-f', 'e950_020-f', 'MapName-f', 'Navigation-f', 'sofi_d02-f', 'sysm_d01-f', 'SysString-f', 'TOG_SS_ChatName-f', 'TOG_SS_StringECommerce-f', 'GracesFDump'],

['X00142280', 'X00142288', 'X00142296', 'X00142304', 'X00142312', 'X00142320', 'X00142328', 'X00142336', 'X00142344', 'X00142352', 'X00142360', 'X00142368', 'X00142376', 'X00142384', 'X00142392', 'X00142400', 'X00142408', 'X00142416', 'X00142424', 'X00142432', 'X00142440', 'X00142448', 'X00142456', 'X00142464', 'X00142472', 'X00142480', 'X00142488', 'X00142496', 'X00142504', 'X00142512', 'X00142520', 'X00142528', 'X00142536', 'X00142544', 'X00142552', 'X00142560', 'X00142568', 'X00142576', 'X00142584', 'X00142592', 'X00142600', 'X00142608', 'X00142616', 'X00142624', 'X00142632', 'X00142640', 'X00142648', 'X00142656', 'X00142664', 'X00142672', 'X00142680', 'X00142688', 'X00142696', 'X00142704', 'X00142712', 'X00142720', 'X00142728', 'X00142736', 'X00142744', 'X00142752', 'X00142760', 'X00142768', 'X00142776', 'X00142784', 'X00142792', 'X00142800', 'X00142808', 'X00142816', 'X00142824', 'X00142832', 'X00142840', 'X00142848', 'X00142856', 'X00142864', 'X00142872', 'X00142880', 'X00142888', 'X00142896', 'X00142904', 'X00142912', 'X00142920', 'X00142928', 'X00142936', 'X00142944', 'X00142952', 'X00142960', 'X00142968', 'X00142976', 'X00142984', 'X00142992', 'X00143000', 'X00143008', 'X00143016', 'X00143024', 'X00143032', 'X00143040', 'X00143048', 'X00143056', 'X00143064', 'X00143072', 'X00143080', 'X00143088', 'X00143096', 'X00143104', 'X00143112', 'X00143120', 'X00143128', 'X00143136', 'X00143144', 'X00143152', 'X00143160', 'X00143168', 'X00143176', 'X00143184', 'X00143192', 'X00143200', 'X00143208', 'X00143216', 'X00143224', 'X00143232', 'X00143240', 'X00143248', 'X00143256', 'X00143264', 'X00143272', 'X00143280', 'X00143288', 'X00143296', 'X00143304', 'X00143312', 'X00143320', 'X00143328', 'X00143336', 'X00143344', 'X00143352', 'X00143360', 'X00143368', 'X00143376', 'X00143384', 'X00143392', 'X00143400', 'X00143408', 'X00143416', 'X00143424', 'X00143432', 'X00143440', 'X00143448', 'X00143456', 'X00143464', 'X00143472', 'X00143480', 'X00143488', 'X00143496', 'X00143504', 'X00143512', 'X00143520', 'X00143528', 'X00143536', 'X00143544', 'X00143552', 'X00143560', 'X00143568', 'X00143576', 'X00143584', 'X00143592', 'X00143600', 'X00143608', 'X00143616', 'X00143624', 'X00143632', 'X00143640', 'X00143648', 'X00143656', 'X00143664', 'X00143672', 'X00143680', 'X00143688', 'X00143696', 'X00143704', 'X00143712', 'X00143720', 'X00143728', 'X00143736', 'X00143744', 'X00143752', 'X00143760', 'X00143768', 'X00143776', 'X00143784', 'X00143792', 'X00143800', 'X00143808', 'X00143816', 'X00143824', 'X00143832', 'X00143840', 'X00143848', 'X00143856', 'X00143864', 'X00143872', 'X00143880', 'X00143888', 'X00143896', 'X00143904', 'X00143912', 'X00143920', 'X00143928', 'X00143936', 'X00143944', 'X00143952', 'X00143960', 'X00143968', 'X00143976', 'X00143984', 'X00143992', 'X00144000', 'X00144008', 'X00144016', 'X00144024', 'X00144032', 'X00144040', 'X00144048', 'X00144056', 'X00144064', 'X00144072', 'X00144080', 'X00144088', 'X00144096', 'X00144104', 'X00144112', 'X00144120', 'X00144128', 'X00144136', 'X00144144', 'X00144152', 'X00144160', 'X00144168', 'X00144176', 'X00144184', 'X00144192', 'X00144200', 'X00144208', 'X00144216', 'X00144224', 'X00144232', 'X00144240', 'X00144248', 'X00144256', 'X00144264', 'X00144272', 'X00144280', 'X00144288', 'X00144296', 'X00144304', 'X00144312', 'X00144320', 'X00144328', 'X00144336', 'X00144344', 'X00144352', 'X00144360', 'X00144368', 'X00144376', 'X00144384', 'X00144392', 'X00144400', 'X00144408', 'X00144416', 'X00144424', 'X00144432', 'X00144440', 'X00144448', 'X00144456', 'X00144464', 'X00144472', 'X00144480', 'X00144488', 'X00144496', 'X00144504', 'X00144512', 'X00144520', 'X00144528', 'X00144536', 'X00144544', 'X00144552', 'X00144560', 'X00144568', 'X00144576', 'X00144584', 'X00144592', 'X00144600', 'X00144608', 'X00144616', 'X00144624', 'X00144632', 'X00144640', 'X00144648', 'X00144656', 'X00144664', 'X00144672', 'X00144680', 'X00144688', 'X00144696', 'X00144704', 'X00144712', 'X00144720', 'X00144728', 'X00144736', 'X00144744', 'X00144752', 'X00144760', 'X00144768', 'X00144776', 'X00144784', 'X00144792', 'X00144800', 'X00144808', 'X00144816', 'X00144824', 'X00144832', 'X00144840', 'X00144848', 'X00144856', 'X00144864', 'X00144872', 'X00144880', 'X00144888', 'X00144896', 'X00144904', 'X00144912', 'X00144920', 'X00144928', 'X00144936', 'X00144944', 'X00144952', 'X00144960', 'X00144968', 'X00144976', 'X00144984', 'X00144992', 'X00145000', 'X00145008', 'X00145016', 'X00145024', 'X00145032', 'X00145040', 'X00145048', 'X00145056', 'X00145064', 'X00145072', 'X00145080', 'X00145088', 'X00145096', 'X00145104', 'X00145112', 'X00145120', 'X00145128', 'X00145136', 'X00145144', 'X00145152', 'X00145160', 'X00145168', 'X00145176', 'X00145184', 'X00145192', 'X00145200', 'X00145208', 'X00145216', 'X00145224', 'X00145232', 'X00145240', 'X00145248', 'X00145256', 'X00145264', 'X00145272', 'X00145280', 'X00145288', 'X00145296', 'X00145304', 'X00145312', 'X00145320', 'X00145328', 'X00145336', 'X00145344', 'X00145352', 'X00145360', 'X00145368', 'X00145376', 'X00145384', 'X00145392', 'X00145400', 'X00145408', 'X00145416', 'X00145424', 'X00145432', 'X00145440', 'X00145448', 'X00145456', 'X00145464', 'X00145472', 'X00145480', 'X00145488', 'X00145496', 'X00145504', 'X00145512', 'X00145520', 'X00145528', 'X00145536', 'X00145544', 'X00145552', 'X00145560', 'X00145568', 'X00145576', 'X00145584', 'X00145592', 'X00145600', 'X00145608', 'X00145616', 'X00145624', 'X00145632', 'X00145640', 'X00145648', 'X00145656', 'X00145664', 'X00145672', 'X00145680', 'X00145688', 'X00145696', 'X00145704', 'X00145712', 'X00145720', 'X00145728', 'X00145736', 'X00145744', 'X00145752', 'X00145760', 'X00145768', 'X00145776', 'X00145784', 'X00145792', 'X00145800', 'X00145808', 'X00145816', 'X00145824', 'X00145832', 'X00145840', 'X00145848', 'X00145856', 'X00145864', 'X00145872', 'X00145880', 'X00145888', 'X00145896', 'X00145904', 'X00145912', 'X00145920', 'X00145928', 'X00145936', 'X00145944', 'X00145952', 'X00145960', 'X00145968', 'X00145976', 'X00145984', 'X00145992', 'X00146000', 'X00146008', 'X00146016', 'X00146024', 'X00146032', 'X00146040', 'X00146048', 'X00146056', 'X00146064', 'X00146072', 'X00146080', 'X00146088', 'X00146096', 'X00146104', 'X00146112', 'X00146120', 'X00146128', 'X00146136', 'X00146144', 'X00146152', 'X00146160', 'X00146168', 'X00146176', 'X00146184', 'X00146192', 'X00146200', 'X00146208', 'X00146216', 'X00146224', 'X00146232', 'X00146240', 'X00146248', 'X00146256', 'X00146264', 'X00146272', 'X00146280', 'X00146288', 'X00146296', 'X00146304', 'X00146312', 'X00146320', 'X00146328', 'X00146336', 'X00146344', 'X00146352', 'X00146360', 'X00146368', 'X00146376', 'X00146384', 'X00146392', 'X00146400', 'X00146408', 'X00146416', 'X00146424', 'X00146432', 'X00146440', 'X00146448', 'X00146456', 'X00146464', 'X00146472', 'X00146480', 'X00146488', 'X00146496', 'X00146504', 'X00146512', 'X00146520', 'X00146528', 'X00146536', 'X00146544', 'X00146552', 'X00146560', 'X00146568', 'X00146576', 'X00146584', 'X00146592', 'X00146600', 'X00146608', 'X00146616', 'X00146624', 'X00146632', 'X00146640', 'X00146648', 'X00146656', 'X00146664', 'X00146672', 'X00146680', 'X00146688', 'X00146696', 'X00146704', 'X00146712', 'X00146720', 'X00146728', 'X00146736', 'X00146744', 'X00146752', 'X00146760', 'X00146768', 'X00146776', 'X00146784', 'X00146792', 'X00146800', 'X00146808', 'X00146816', 'X00146824', 'X00146832', 'X00146840', 'X00146848', 'X00146856', 'X00146864', 'X00146872', 'X00146880', 'X00146888', 'X00146896', 'X00146904', 'X00146912', 'X00146920', 'X00146928', 'X00146936', 'X00146944', 'X00146952', 'X00146960', 'X00146968', 'X00146976', 'X00146984', 'X00146992', 'X00147000', 'X00147008', 'X00147016', 'X00147024', 'X00147032', 'X00147040', 'X00147048', 'X00147056', 'X00147064', 'X00147072', 'X00147080', 'X00147088', 'X00147096', 'X00147104', 'X00147112', 'X00147120', 'X00147128', 'X00147136', 'X00147144', 'X00147152', 'X00147160', 'X00147168', 'X00147176', 'X00147184', 'X00147192', 'X00147200', 'X00147208', 'X00147216', 'X00147224', 'X00147232', 'X00147240', 'X00147248', 'X00147256', 'X00147264', 'X00147272', 'X00147280', 'X00147288', 'X00147296', 'X00147304', 'X00147312', 'X00147320', 'X00147328', 'X00147336', 'X00147344', 'X00147352', 'X00147360', 'X00147368', 'X00147376', 'X00147384', 'X00147392', 'X00147400', 'X00147408', 'X00147416', 'X00147424', 'X00147432', 'X00147440', 'X00147448', 'X00147456', 'X00147464', 'X00147472', 'X00147480', 'X00147488', 'X00147496', 'X00147504', 'X00147512', 'X00147520', 'X00147528', 'X00147536', 'X00147544', 'X00147552', 'X00147560', 'X00147568', 'X00147576', 'X00147584', 'X00147592', 'X00147600', 'X00147608', 'X00147616', 'X00147624', 'X00147632', 'X00147640', 'X00147648', 'X00147656', 'X00147664', 'X00147672', 'X00147680', 'X00147688', 'X00147696', 'X00147704', 'X00147712', 'X00147720', 'X00147728', 'X00147736', 'X00147744', 'X00147752', 'X00147760', 'X00147768', 'X00147776', 'X00147784', 'X00147792', 'X00147800', 'X00147808', 'X00147816', 'X00147824', 'X00147832', 'X00147840', 'X00147848', 'X00147856', 'X00147864', 'X00147872', 'X00147880', 'X00147888', 'X00147896', 'X00147904', 'X00147912', 'X00147920', 'X00147928', 'X00147936', 'X00147944', 'X00147952', 'X00147960', 'X00147968', 'X00147976', 'X00147984', 'X00147992', 'X00148000', 'X00148008', 'X00148016', 'X00148024', 'X00148032', 'X00148040', 'X00148048', 'X00148056', 'X00148064', 'X00148072', 'X00148080', 'X00148088', 'X00148096', 'X00148104', 'X00148112', 'X00148120', 'X00148128', 'X00148136', 'X00148144', 'X00148152', 'X00148160', 'X00148168', 'X00148176', 'X00148184', 'X00148192', 'X00148200', 'X00148208', 'X00148216', 'X00148224', 'X00148232', 'X00148240', 'X00148248', 'X00148256', 'X00148264', 'X00148272', 'X00148280', 'X00148288', 'X00148296', 'X00148304', 'X00148312', 'X00148320', 'X00148328', 'X00148336', 'X00148344', 'X00148352', 'X00148360', 'X00148368', 'X00148376', 'X00148384', 'X00148392', 'X00148400', 'X00148408', 'X00148416', 'X00148424', 'X00148432', 'X00148440', 'X00148448', 'X00148456', 'X00148464', 'X00148472', 'X00148480', 'X00148488', 'X00148496', 'X00148504', 'X00148512', 'X00148520', 'X00148528', 'X00148536', 'X00148544', 'X00148552', 'X00148560', 'X00148568', 'X00148576', 'X00148584', 'X00148592', 'X00148600', 'X00148608', 'X00148616', 'X00148624', 'X00148632', 'X00148640', 'X00148648', 'X00148656', 'X00148664', 'X00148672', 'X00148680', 'X00148688', 'X00148696', 'X00148704', 'X00148712', 'X00148720', 'X00148728', 'X00148736', 'X00148744', 'X00148752', 'X00148760', 'X00148768', 'X00148776', 'X00148784', 'X00148792', 'X00148800', 'X00148808', 'X00148816', 'X00148824', 'X00148832', 'X00148840', 'X00148848', 'X00148856', 'X00148864', 'X00148872', 'X00148880', 'X00148888', 'X00148896', 'X00148904', 'X00148912', 'X00148920', 'X00148928', 'X00148936', 'X00148944', 'X00148952', 'X00148960', 'X00148968', 'X00148976', 'X00148984', 'X00148992', 'X00149000', 'X00149008', 'X00149016', 'X00149024', 'X00149032', 'X00149040', 'X00149048', 'X00149056', 'X00149064', 'X00149072', 'X00149080', 'X00149088', 'X00149096', 'X00149104', 'X00149112', 'X00149120', 'X00149128', 'X00149136', 'X00149144', 'X00149152', 'X00149160', 'X00149168', 'X00149176', 'X00149184', 'X00149192', 'X00149200', 'X00149208', 'X00149216', 'X00149224', 'X00149232', 'X00149240', 'X00149248', 'X00149256', 'X00149264', 'X00149272', 'X00149280', 'X00149288', 'X00149296', 'X00149304', 'X00149312', 'X00149320', 'X00149328', 'X00149336', 'X00149344', 'X00149352', 'X00149360', 'X00149368', 'X00149376', 'X00149384', 'X00149392', 'X00149400', 'X00149408', 'X00149416', 'X00149424', 'X00149432', 'X00149440', 'X00149448', 'X00149456', 'X00149464', 'X00149472', 'X00149480', 'X00149488', 'X00149496', 'X00149504', 'X00149512', 'X00149520', 'X00149528', 'X00149536', 'X00149544', 'X00149552', 'X00149560', 'X00149568', 'X00149576', 'X00149584', 'X00149592', 'X00149600']

]

