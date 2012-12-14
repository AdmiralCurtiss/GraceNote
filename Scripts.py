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
from collections import deque


# load config
try:
    configfile = sys.argv[1]
except:
    configfile = 'config.xml'
print 'Loading configuration: ' + configfile
configData = Configuration(configfile)

# load graces folder config if it's available
try:
    configDataGracesFolders = Configuration('config_graces_byfolder.xml').FileList
except:
    configDataGracesFolders = [[]]


try:
    Audio = True
    sys.path.append('Clips')
    from PyQt4.phonon import Phonon
    if os.path.exists('Clips/hashtable.py'):
        from hashtable import hashtable
        HashTableExists = True
    else:
        HashTableExists = False
except ImportError:
    print "Your Qt installation does not have Phonon support.\nPhonon is required to play audio clips."
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

EnglishVoiceLanguageFlag = False
UpdateLowerStatusFlag = False
ModeFlag = 'Semi-Auto'
AmountEditingWindows = 5
WriteDatabaseStorageToHddOnEntryChange = False
FooterVisibleFlag = False


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

        self.scripts2 = Scripts2(self)
        self.setCentralWidget(self.scripts2)
        
    def closeEvent(self, event):
        self.scripts2.cleanupAndQuit()
        return



class XTextBox(QtGui.QTextEdit):

    #should be: manualEdit = QtCore.pyqtSignal(int, XTextBox, QtGui.QLabel) but I haven't figured out how to give the current class as parameter
    manualEdit = QtCore.pyqtSignal(int, object, QtGui.QLabel)
    currentEntry = -1


    def __init__(self, HUD, parent):
        super(XTextBox, self).__init__()
        
        self.parent = parent
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
        
        
    def setFooter(self, footer):
        self.footer = footer
        
    def refreshFooter(self, text, prepend):
        if FooterVisibleFlag == False:
            return
            
        feedCount = text.count('\f')
        sanitizedText = re.sub('<CLT[ 0-9]+>', '', text.replace("''", "'"))
        splitOnFeeds = sanitizedText.split('\f')
        splitOnLines = sanitizedText.replace('\f', '\n').split('\n')
        longestLineChars = 0
        for s in splitOnLines:
            longestLineChars = max(longestLineChars, len(s))
        highestBoxNewlines = 0
        for s in splitOnFeeds:
            highestBoxNewlines = max(highestBoxNewlines, s.count('\n')+1)
        self.footer.setText(prepend + 'Textboxes: ' + str(feedCount+1) + ' / Highest Box: ' + str(highestBoxNewlines) + ' lines / Longest Line: ' + str(longestLineChars) + ' chars')
    
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
        
        if configData.UseGracesVoiceHash == False:
            if EnglishVoiceLanguageFlag == True:
                return configData.VoicePathEnPrefix + name + configData.VoicePathEnPostfix
            return configData.VoicePathJpPrefix + name + configData.VoicePathJpPostfix
        
        if HashTableExists == False:
            return ''
        
        temphash = 0
        for i in name:
            temphash = ((temphash * 137) + ord(i)) % 0x100000000
        
        if name[:2] == 'VS':
            index = hashtable[int(name[2])-1].index(temphash)
            filename = 'VOSCE0' + name[2] + '_' + str(index+1).zfill(5)
        
        elif name[:2] == 'VA':
            index = hashtable[8].index(temphash)
            filename = 'VOSCE16' + '_' + str(index+1).zfill(5)
        
        if EnglishVoiceLanguageFlag == True:
            return configData.VoicePathEnPrefix + filename + configData.VoicePathEnPostfix
        return configData.VoicePathJpPrefix + filename + configData.VoicePathJpPostfix

    def playAudio(self):
    
        self.player.clear()
        playerQueue = []
    
        for clip in self.audioClips:
            filename = self.lookupAudioHash(clip)
            if os.path.exists(filename):
                playerQueue.append(Phonon.MediaSource(filename))
                
        if playerQueue:
            self.player.enqueue(playerQueue)
            self.player.play()

    def textChangedSignal(self):
        if self.modified == True:
            self.manualEdit.emit(5, self, self.footer)
            
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
            
            # offer a quick jump on [entrynumber] or [databasename] or [databasename/entrynumber]
            plaintext = self.toPlainText()
            selstart = cursor.selectionStart()-1
            selend = cursor.selectionEnd()+1
            textplus = unicode(plaintext[selstart : selend])
            if textplus.startswith('/'):
                while plaintext[selstart] != u'[':
                    selstart = selstart - 1
                textplus = unicode(plaintext[selstart : selend])
            elif textplus.endswith('/'):
                while plaintext[selend] != u']':
                    selend = selend + 1
                selend = selend + 1
                textplus = unicode(plaintext[selstart : selend])
            if textplus.startswith('[') and textplus.endswith(']'):
                popup_menu.insertSeparator(popup_menu.actions()[0])
                action = SpellAction('Jump to ' + textplus, popup_menu)
                action.correct.connect(self.jumpToDatabaseFromBracketString)
                popup_menu.addAction(action)
                
                                
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
    
    def jumpToDatabaseFromBracketString(self, word):
        # word is something like: "Jump to [DRBO1234/56]", "Jump to [1]", "Jump to [VItems]"
        word = unicode(word)
        word = word[word.index('[') + 1 : word.index(']')]
        words = word.split('/', 1)
        if len(words) == 2:
            db = words[0]
            entry = words[1]
        else:
            try:
                entry = int(word)
                db = ''
            except ValueError:
                db = word
                entry = 1
        
        self.parent.JumpToEntry(db, entry)

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
            self.manualEdit.emit(1, self, self.footer)
        else:
            self.translate.setIcon(QtGui.QIcon('icons/tloff.png'))
            self.one = False
            self.manualEdit.emit(0, self, self.footer)

            
    def checkTogglem(self):
        if self.two == False:
            self.tlCheck.setIcon(QtGui.QIcon('icons/oneon.png'))
            self.two = True
            self.manualEdit.emit(2, self, self.footer)
        else:
            self.tlCheck.setIcon(QtGui.QIcon('icons/oneoff.png'))
            self.two = False
            self.manualEdit.emit(1, self, self.footer)


    def rewriteTogglem(self):
        if self.three == False:
            self.rewrite.setIcon(QtGui.QIcon('icons/twoon.png'))
            self.three = True
            self.manualEdit.emit(3, self, self.footer)
        else:
            self.rewrite.setIcon(QtGui.QIcon('icons/twooff.png'))
            self.three = False
            self.manualEdit.emit(2, self, self.footer)


    def grammarTogglem(self):
        if self.four == False:
            self.grammar.setIcon(QtGui.QIcon('icons/threeon.png'))
            self.four = True
            self.manualEdit.emit(4, self, self.footer)
        else:
            self.grammar.setIcon(QtGui.QIcon('icons/threeoff.png'))
            self.four = False
            self.manualEdit.emit(3, self, self.footer)



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

        painter.drawText(350, 185, 'v10.0')
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
            ModeFlag = 'Semi-Auto'
        
        global EnglishVoiceLanguageFlag
        if self.settings.contains('voicelanguage'):
            EnglishVoiceLanguageFlag = self.settings.value('voicelanguage') == 'EN'
        else:
            self.settings.setValue('voicelanguage', 'JP')
            EnglishVoiceLanguageFlag = False
        
        global UpdateLowerStatusFlag
        if self.settings.contains('updatelowerstatus'):
            UpdateLowerStatusFlag = self.settings.value('updatelowerstatus') == 'True'
        else:
            self.settings.setValue('updatelowerstatus', 'False')
            UpdateLowerStatusFlag = False
        
        global WriteDatabaseStorageToHddOnEntryChange
        if self.settings.contains('writeonentrychange'):
            WriteDatabaseStorageToHddOnEntryChange = self.settings.value('writeonentrychange') == 'True'
        else:
            self.settings.setValue('writeonentrychange', 'False')
            WriteDatabaseStorageToHddOnEntryChange = False
        
        global FooterVisibleFlag
        if self.settings.contains('footervisible'):
            FooterVisibleFlag = self.settings.value('footervisible') == 'True'
        else:
            self.settings.setValue('footervisible', 'False')
            FooterVisibleFlag = False
        
        global AmountEditingWindows
        if self.settings.contains('editpane_amount'):
            AmountEditingWindows = int(self.settings.value('editpane_amount'))
        else:
            self.settings.setValue('editpane_amount', '5')
            AmountEditingWindows = 5
        if AmountEditingWindows < 3 or AmountEditingWindows > 25:
            AmountEditingWindows = 5

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
        #self.tree.setFixedWidth(190)
        self.tree.sortByColumn(1, 0)
        self.tree.setHeaderHidden(True)
        
        self.PopulateModel(configData.FileList)

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
        for i in range(AmountEditingWindows):
            # create text boxes, set defaults
            tb1 = XTextBox(None, self)
            tb2 = XTextBox('jp', self)
            tb2.hide()
            tb2.setReadOnly(True)
            MyHighlighter(tb2, 'something')
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
            if FooterVisibleFlag:
                tmplayout.addWidget(footer, 2, 1, 1, 2)
                tmplayout.addWidget(footer2, 3, 1, 1, 2)
            
            # create QGroupBox
            tmpqgrpbox = QtGui.QGroupBox()
            tmpqgrpbox.setLayout(tmplayout)
            tmpqgrpbox.setTitle("-----")
            if FooterVisibleFlag:
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
        
        if EnglishVoiceLanguageFlag:
            self.voiceLangAct = QtGui.QAction('English Voices', None)
        else:
            self.voiceLangAct = QtGui.QAction('Japanese Voices', None)
        self.voiceLangAct.triggered.connect(self.VoiceLanguageSwap)
        self.voiceLangAct.setShortcut(QtGui.QKeySequence('Ctrl-Shift-Alt-E'))
        
        if UpdateLowerStatusFlag:
            self.updateLowerStatusAct = QtGui.QAction('Updating lower status', None)
        else:
            self.updateLowerStatusAct = QtGui.QAction('Not updating lower status', None)
        self.updateLowerStatusAct.triggered.connect(self.UpdateLowerStatusSwap)
        
        if FooterVisibleFlag:
            self.displayFooterAct = QtGui.QAction('Footer enabled', None)
        else:
            self.displayFooterAct = QtGui.QAction('Footer disabled', None)
        self.displayFooterAct.triggered.connect(self.DisplayFooterSwap)
        
        self.changeEditingWindowAmountAct = QtGui.QAction('Change Editing Window Amount', None)
        self.changeEditingWindowAmountAct.triggered.connect(self.ChangeEditingWindowAmountDisplay)
        
        if WriteDatabaseStorageToHddOnEntryChange:
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
        global commentsAvailableLabel
        commentsAvailableLabel = QtGui.QLabel("-")
        
        FileListSubLayout = QtGui.QVBoxLayout()
        FileListSubLayout.addWidget(commentsAvailableLabel)
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

    def cleanupAndQuit(self):
        self.WriteDatabaseStorageToHdd()
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


    def ReloadConfiguration(self):
        self.WriteDatabaseStorageToHdd()
        
        global configfile
        global configData
        
        configData = Configuration(configfile)
        self.PopulateModel(configData.FileList)
        
    def VoiceLanguageSwap(self):
        global EnglishVoiceLanguageFlag
        if EnglishVoiceLanguageFlag == True:
            self.voiceLangAct.setText('Japanese Voices')
            EnglishVoiceLanguageFlag = False
            self.settings.setValue('voicelanguage', 'JP')
        else:
            self.voiceLangAct.setText('English Voices')
            EnglishVoiceLanguageFlag = True
            self.settings.setValue('voicelanguage', 'EN')
        
    def UpdateLowerStatusSwap(self):
        global UpdateLowerStatusFlag
        if UpdateLowerStatusFlag == True:
            self.updateLowerStatusAct.setText('Not updating lower status')
            UpdateLowerStatusFlag = False
            self.settings.setValue('updatelowerstatus', 'False')
        else:
            self.updateLowerStatusAct.setText('Updating lower status')
            UpdateLowerStatusFlag = True
            self.settings.setValue('updatelowerstatus', 'True')
            
    def DisplayFooterSwap(self):
        global FooterVisibleFlag
        if FooterVisibleFlag == True:
            self.displayFooterAct.setText('Footer disabled')
            FooterVisibleFlag = False
            self.settings.setValue('footervisible', 'False')
        else:
            self.displayFooterAct.setText('Footer enabled')
            FooterVisibleFlag = True
            self.settings.setValue('footervisible', 'True')

    def ChangeWriteDatabaseStorageToHddBehavior(self):
        global WriteDatabaseStorageToHddOnEntryChange
        if WriteDatabaseStorageToHddOnEntryChange == True:
            self.writeDatabaseStorageToHddAct.setText('Not writing on Entry change')
            WriteDatabaseStorageToHddOnEntryChange = False
            self.settings.setValue('writeonentrychange', 'False')
        else:
            self.writeDatabaseStorageToHddAct.setText('Writing on Entry change')
            WriteDatabaseStorageToHddOnEntryChange = True
            self.settings.setValue('writeonentrychange', 'True')
            
    def ChangeEditingWindowAmountDisplay(self):
        global AmountEditingWindows
        text, ok = QtGui.QInputDialog.getText(self, "Enter new window amount", "New amount: (restart GN after entering!)", QtGui.QLineEdit.Normal)
        if ok and text != '':
            tmp = int(text)
            if tmp >= 3 and tmp <= 25:
                self.settings.setValue('editpane_amount', text)
                AmountEditingWindows = tmp

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

    def ReverseConsolidateDebug(self):
        self.WriteDatabaseStorageToHdd()
        
        # Applies the debug status in Databases to GracesJapanese
        
        i = 1
        aList = configData.FileList
            
        for item in aList[0]:
            print item
            for filename in aList[i]:

                print "Processing: {0}".format(filename)
            
                UpdateCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(filename))
                UpdateCur = UpdateCon.cursor()
                        
                UpdateCur.execute("SELECT StringID FROM Text WHERE status = -1")
                
                for entry in UpdateCur.fetchall():
                    CursorGracesJapanese.execute("UPDATE Japanese SET debug = 1 WHERE ID=?", (entry[0],))
                UpdateCon.rollback()
                
            i += 1
        ConnectionGracesJapanese.commit()

    def RetrieveModifiedFiles(self, splash):
        self.WriteDatabaseStorageToHdd()
        
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
                    self.cleanupAndQuit() 


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
                            continue
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
        self.WriteDatabaseStorageToHdd()
                
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
        self.WriteDatabaseStorageToHdd()
        
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
        self.WriteDatabaseStorageToHdd()
        
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
        self.WriteDatabaseStorageToHdd()
        
        global commentsAvailableLabel
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
            
            identifyString = ''
            if ContainsIDString == True:
                try:
                    tmp = str(TempList[i][6])
                    identifyString = tmp
                    entryDisplayString = entryDisplayString + ' ' + identifyString
                except:
                    pass
            
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
        
        CalculateAllCompletionPercentagesForDatabase()

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
        SaveCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(databasefilename))
        SaveCur = SaveCon.cursor()
        SaveCur.execute("select StringID from Text where ID={0}".format(selectedRow+1))
        NextID = SaveCur.fetchall()[0][0]
        if DebugState == True:
            CursorGracesJapanese.execute("UPDATE Japanese SET debug = 1 WHERE ID = {0} AND debug != 1".format(NextID))
            SaveCur.execute("UPDATE Text SET status = -1, updated = 1 WHERE ID = {0} AND status != -1".format(selectedRow+1))
            self.entrymodel.item(index.row()).setWhatsThis("d")
        else:
            CursorGracesJapanese.execute("UPDATE Japanese SET debug = 0 WHERE ID = {0} AND debug != 0".format(NextID))
            SaveCur.execute("UPDATE Text SET status =  0, updated = 1 WHERE ID = {0} AND status  = -1".format(selectedRow+1))
            self.entrymodel.item(index.row()).setWhatsThis("n")
        self.update.add(str(databasefilename))
        SaveCon.commit()
        ConnectionGracesJapanese.commit()
        

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
            
        GoodString = VariableRemove(textBox.toPlainText())

        if role == 5:
            CommandOriginButton = False
            role = self.role
        else:
            CommandOriginButton = True
        
        
        global ModeFlag
        if CommandOriginButton == True:
            # if origin a button: always set to argument
            updateStatusValue = role
        elif self.state == "COM":
            # if origin a Comment box, don't update
            updateStatusValue = self.text[textBox.currentEntry - 1][4]
        else:
            # if origin by typing or automatic:
            if ModeFlag == 'Manual':
                # in manual mode: leave status alone, do not change, just fetch the existing one
                updateStatusValue = self.text[textBox.currentEntry - 1][4]
            else:
                # in (semi)auto mode: change to current role, except when disabled by option and current role is lower than existing status
                global UpdateLowerStatusFlag
                if UpdateLowerStatusFlag == False:
                    statuscheck = self.text[textBox.currentEntry - 1][4]
                    if statuscheck > role:
                        updateStatusValue = statuscheck
                    else:
                        updateStatusValue = role
                else:
                    updateStatusValue = role
                # endif UpdateLowerStatusFlag
            # endif ModeFlag
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
                SaveCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(d.databaseName))
                SaveCur = SaveCon.cursor()
                
            if d.state == 'ENG':
                SaveCur.execute(u"update Text set english=?, updated=1, status=? where ID=?", (d.cleanString, d.role, d.entry))
            elif d.state == "COM":
                SaveCur.execute(u"update Text set comment=?, updated=1, status=? where ID=?", (d.cleanString, d.role, d.entry))
            SaveCon.commit()
        
        self.databaseWriteStorage.clear()

    def PopulateTextEdit(self):
        global WriteDatabaseStorageToHddOnEntryChange
        if WriteDatabaseStorageToHddOnEntryChange == True:
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
                rowBoxes.append( int(entrytextdisplay[6:11])-1 )
            except:
                rowBoxes.append( -2 )
        
        textEntries1 = []
        textEntries1raw = []
        textEntries2 = []
        textEntries2raw = []
        for i in range(len(self.textEditingBoxes)):
            if rowBoxes[i] >= 0:
                textEntries1.append( VariableReplace(self.text[rowBoxes[i]][t]) )
                textEntries1raw.append( self.text[rowBoxes[i]][t] )
                textEntries2.append( VariableReplace(self.text[rowBoxes[i]][self.twoupEditingTextBoxes[i].role]) )
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
        if Audio == True:
            lengthEditingBoxes = len(self.textEditingBoxes)
            for i in range(lengthEditingBoxes):
                if self.regularEditingTextBoxes[i].currentEntry == -1:
                    continue
                AudioSearchText = VariableReplace(self.text[rowBoxes[i] + configData.VoiceEntryOffset][t])
                AudioClips = re.findall('<Audio: (.*?)>', AudioSearchText, re.DOTALL)
                AudioClips = AudioClips + re.findall('<Voice: (.*?)>', AudioSearchText, re.DOTALL)
                if AudioClips == []:
                    self.regularEditingTextBoxes[i].clearPlaybackButtons()
                else:
                    self.regularEditingTextBoxes[i].makePlaybackButtons(AudioClips)

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
        global ModeFlag
        if ModeFlag == 'Auto':
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

                    
       
    def SavetoServer(self):
        self.WriteDatabaseStorageToHdd()
        
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

    def RevertFromServer(self):
        self.WriteDatabaseStorageToHdd()
        
        if len(self.update) == 0:
            print 'Nothing to revert!'
            return

        print 'Reverting databases...'
        
        
        for i in range(1, 20):
            try:        
                try:
                    self.ftp = FTP(configData.FTPServer, configData.FTPUsername, configData.FTPPassword, "", 15)
                except:
                    if i == 20:
                        print "FTP connection failed, revert didn't succeed.\nPlease try to revert again at a later date."
                        self.settings.setValue('update', set(self.update))
                        return
                    print 'Error during FTP transfer, retrying...'
                    continue
               
                self.ftp.cwd('/')
                self.ftp.cwd(configData.RemoteDatabasePath)

                print "Re-getting changed files from server..."
                for item in self.update:
                    CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [item])
                    exists = CursorGracesJapanese.fetchall()[0][0]
                    if exists > 0:
                        CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [item])
                        desc = CursorGracesJapanese.fetchall()[0][0]
                        print 'Downloading ' + desc + ' [' + item + ']...'
                    else:
                        print 'Downloading ' + item + '...'
                    
                    
                    
                    self.DownloadFile(self.ftp, item, item)
                    WipeUpdateCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(item))
                    WipeUpdateCur = WipeUpdateCon.cursor()
            
                    WipeUpdateCur.execute(u"update Text set updated=0")
                    WipeUpdateCon.commit()
                    
                    CalculateCompletionForDatabase(item)

                self.ftp.close()
                self.update.clear()
                self.settings.setValue('update', self.update)
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


        Archive = configDataGracesFolders[1][:] # Chat_MS
        Archive.extend(configDataGracesFolders[2][:]) # Chat_SB
        Archive.extend(configDataGracesFolders[-1][:]) # SysString.bin
        Archive = (['TOG_SS_ChatName', 'TOG_SS_StringECommerce']) # Special Cased Sys Subs
        Archive.extend(configDataGracesFolders[-2][:]) # Movie Subtitles
        Archive.extend(configDataGracesFolders[-3][:]) # Special Strings

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
            Archive = configDataGracesFolders[i]
            self.MakeSCS(Archive, progress, 'Wii', map0File)
            i += 1
            
        map0File.close()
        

        Map1RCPK = ['mapfile_anmaR.cpk', 'mapfile_beraR.cpk', 'mapfile_debugR.cpk', 'mapfile_fendR.cpk', 'mapfile_kameR.cpk', 'mapfile_koya_r06R.cpk', 'mapfile_lakeR.cpk', 'mapfile_lanR.cpk', 'mapfile_nekoR.cpk', 'mapfile_olleR.cpk', 'mapfile_otheR.cpk', 'mapfile_ozweR.cpk', 'mapfile_riotR.cpk', 'mapfile_sablR.cpk', 'mapfile_shatR.cpk', 'mapfile_shipR.cpk', 'mapfile_strtR.cpk', 'mapfile_supaR.cpk', 'mapfile_systemR.cpk', 'mapfile_winR.cpk']

        i = 46

        print 'Creating Map1'
        for CPK in Map1RCPK:
            Archive = configDataGracesFolders[i]
            self.MakeSCS(Archive, progress, 'Wii', map1File)
            i += 1

        map1File.close()
        
        progress.setValue(1260)


        #shutil.rmtree('Resources/Wii')



    def MakeSCS(self, allFiles, progress, path, BIN=None):
        self.WriteDatabaseStorageToHdd()
        


        # Create the .scs files
        
        JPCon = sqlite3.connect(configData.LocalDatabasePath + '/GracesJapanese')
        JPCur = JPCon.cursor()

        fileExceptions = ['GracesJapanese', 'NewChangeLog', 'None', 'ChangeLog', 'temp', '.DS_Store', 'endingData', 'Artes', 'Battle', 'Discovery', 'GradeShop-Missions', 'Item', 'MonsterBook', 'Skills', 'System', 'Tactics', 'Titles', 'Tutorial', 'soundTest', 'ArteNames', 'Skits', 'GracesFDump', 'S', 'CheckTags.bat', 'System.Data.SQLite.DLL', 'GraceNote_CheckTags.exe', 'sqlite3.exe', 'taglog.txt', 'CompletionPercentage']

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
        Archive = configDataGracesFolders[1][:] # Chat_MS
        Archive.extend(configDataGracesFolders[2][:]) # Chat_SB
        ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()
            

        # SysString
        Archive = (configDataGracesFolders[-1]) # SysString.bin
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
        Archive = (configDataGracesFolders[-2]) # Movie Subtitles
        ArchiveLocation = 'movie' + os.sep + 'str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(GracesPath, file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()

        progress.setValue(10)


        # Special Strings
        Archive = (configDataGracesFolders[-3]) # Special Stuff
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
            
            Archive = configDataGracesFolders[i]
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
            
            Archive = configDataGracesFolders[i]
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
        Archive = configDataGracesFolders[1][:] # Chat_MS
        Archive.extend(configDataGracesFolders[2][:]) # Chat_SB
        ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()
            
            
        # SysString        
        Archive = (configDataGracesFolders[-1]) # SysString.bin
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
        Archive = (configDataGracesFolders[-2]) # Movie Subtitles
        ArchiveLocation = 'movie' + os.sep + 'str' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.bin".format(GracesPath, file), "{0}{1}.bin".format(ArchiveLocation, file)])
            tempFile = open("{0}{1}.bin".format(GracesPath, file))
            tempData = tempFile.read()
            rootRbin.write(tempData)
            tempFile.close()

        progress.setValue(10)


        # Special Strings
        Archive = (configDataGracesFolders[-3]) # Special Stuff
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
            
            Archive = configDataGracesFolders[i]
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
            
            Archive = configDataGracesFolders[i]
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

        
        self.setWindowTitle('Changelog: {0}'.format(file))
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

        self.setWindowTitle('Global Changelog')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Recent Changes:'))
        layout.addWidget(self.treewidget)
        self.setLayout(layout)

    def JumpToFile(self, item, column):
        file = item.data(2, 0)
        self.parent.JumpToEntry(file, 1)


class DuplicateText(QtGui.QDialog):

    def __init__(self, parent):
        super(DuplicateText, self).__init__()

        self.setWindowModality(False)        
        
        self.parent = parent

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
        x = 0
        y = 0
        for cat in configData.FileList[0]:
            self.categories.append(QtGui.QCheckBox(cat))
            layout.addWidget(self.categories[i], y, x)
            i += 1
            x += 1
            if x > 5:
                x = 0
                y += 1
        
        self.exceptions = QtGui.QRadioButton('Inconsistent Translations only')
        self.dupes = QtGui.QRadioButton('All Duplicates')
        self.exceptions.setChecked(True)
        
        self.go = QtGui.QPushButton('Search')

        self.progressbar = QtGui.QProgressBar()
        self.progressbar.setRange(0, 100000)
        
        self.progressLabel = QtGui.QLabel('Pending')
        
        layoutSystemButtons = QtGui.QGridLayout()
        layoutSystemButtons.addWidget(self.exceptions, 0, 0)
        layoutSystemButtons.addWidget(self.dupes, 0, 1)
        #layoutSystemButtons.addWidget(self.progressbar, 3, 1)
        #layoutSystemButtons.addWidget(self.progressLabel, 4, 1)
        layoutSystemButtons.addWidget(self.go, 0, 2)
        layoutSystemButtons.setColumnMinimumWidth(0, 200)
        
        self.treewidget.itemDoubleClicked.connect(self.InitiateMassReplaceSearch)

        self.setWindowTitle('Duplicate Text Retriever')
        subLayout = QtGui.QVBoxLayout()
        subLayout.addLayout(layoutSystemButtons)
        subLayout.addLayout(layout)
        subLayout.addWidget(self.treewidget)
        self.setLayout(subLayout)

        self.go.released.connect(self.SearchCategories)
        
#     Two options
#        One: Search for any cloned text with more than one unique translation, and display them
#        Two: Search for any cloned text at all, and display them
    def SearchCategories(self):

        self.treewidget.clear()

        print 'Initializing container...'
        Table = []
        BlackList = []
        CursorGracesJapanese.execute('SELECT MAX(ID) FROM Japanese')
        maxid = int(CursorGracesJapanese.fetchall()[0][0])
        for i in xrange( maxid + 1 ):
            Table.append([0, set([])])
            BlackList.append(0)

        print 'Fetching debug information...'
        CursorGracesJapanese.execute('select ID from Japanese where debug=1')
        BlackListDB = CursorGracesJapanese.fetchall()
        for id in BlackListDB:
            BlackList[int(id[0])] = 1
        aList = configData.FileList

        i = 1
        print 'Processing databases...'
        for category in self.categories:
            if category.isChecked() == True:
                for filename in aList[i]:
                    #print 'Processing ' + filename + '...'

                    conC = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(filename))
                    curC = conC.cursor()
                    
                    curC.execute("select StringID, English from Text")
                    
                    results = curC.fetchall()
                    
                    for item in results:
                        if BlackList[int(item[0])] == 0:
                            Table[item[0]][0] += 1
                            Table[item[0]][1].add(item[1])
#                    self.progressbar.setValue(self.progressbar.value() + (6250/len(configData.FileList[i])))
#                    self.progressLabel.setText("Processing {0}".format(category))
#                    self.progressLabel.update()
#            self.progressbar.setValue(i * 6250)
            i += 1
        
        print 'Displaying entries...'
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

    def InitiateMassReplaceSearch(self, item, column):
        searchstring = item.data(1, 0)
        self.parent.ShowMassReplace()
        self.parent.massDialog.original.setText(searchstring)
        self.parent.massDialog.matchEntry.setChecked(True)
        self.parent.massDialog.Search()

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
        self.treewidget.setColumnWidth(1, 150)
        self.treewidget.setColumnWidth(2, 150)
        self.treewidget.setColumnWidth(3, 150)
        self.treewidget.setColumnWidth(4, 150)
        
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
                    translationPercent = '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(translated)/float(totalDB)*100, translated, totalDB)
                    tlCheckPercent = '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(tlCheck)/float(totalDB)*100, tlCheck, totalDB)
                    rewritePercent = '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(rewrite)/float(totalDB)*100, rewrite, totalDB)
                    grammarPercent = '{0:06.2f}% ({1:04d}/{2:04d})'.format(float(grammar)/float(totalDB)*100, grammar, totalDB)
                else:
                    translationPercent = 'N/A'
                    tlCheckPercent = 'N/A'
                    rewritePercent = 'N/A'
                    grammarPercent = 'N/A'
                    
                newrow = QtGui.QTreeWidgetItem(cat, [item, translationPercent, tlCheckPercent, rewritePercent, grammarPercent, '{0}'.format(commentamount)])
                    
                progress.setValue(progress.value() + 1)
    
            cat.setData(1, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(catTrans)/float(catTotalDB)*100, catTrans, catTotalDB))
            cat.setData(2, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(catTlCheck)/float(catTotalDB)*100, catTlCheck, catTotalDB))
            cat.setData(3, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(catRewrite)/float(catTotalDB)*100, catRewrite, catTotalDB)) 
            cat.setData(4, 0, '{0:06.2f}% ({1:06d}/{2:06d})'.format(float(catGrammar)/float(catTotalDB)*100, catGrammar, catTotalDB))
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

        self.parent = parent

        self.setWindowModality(False)
        
        self.searches = []
        self.tabwidget = QtGui.QTabWidget()
        
        
        font = QtGui.QLabel().font()
        font.setPointSize(10)
 
        self.original = QtGui.QLineEdit()
        self.replacement = QtGui.QLineEdit()
        self.exceptions = QtGui.QLineEdit()
        self.fileFilter = QtGui.QLineEdit()
        self.matchExact = QtGui.QRadioButton('Any Match')
        self.matchEnglish = QtGui.QRadioButton('Any: English Only')
        self.matchEntry = QtGui.QRadioButton('Complete Entry')
        self.matchComments = QtGui.QRadioButton('Comments')
        self.matchEnglish.setChecked(True)
        self.fileFilter.setToolTip('Wildcards implicit. eg CHT will match all skits')
        self.matchCase = QtGui.QCheckBox('Match case')
        self.searchDebug = QtGui.QCheckBox('Search Debug')
        
        self.matchEnglish.setFont(font)
        self.matchExact.setFont(font)
        self.matchEntry.setFont(font)
        self.matchComments.setFont(font)
                
        originalLabel = QtGui.QLabel('Search for:')
        originalLabel.setFont(font)
        exceptionLabel = QtGui.QLabel('Excluding:')
        exceptionLabel.setFont(font)
        replaceLabel = QtGui.QLabel('Replace with:')
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
        self.removeTabButton = QtGui.QToolButton()
        self.removeTabButton.setText('Remove Tab')
        
        checkLayout = QtGui.QHBoxLayout()
        checkLayout.addWidget(self.checkAll)
        checkLayout.addWidget(self.checkNone)
        checkLayout.addWidget(self.removeTabButton)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addLayout(checkLayout)
        buttonLayout.addWidget(self.search)
        buttonLayout.addWidget(self.replace)
                
        inputLayout = QtGui.QGridLayout()
        inputLayout.addWidget(originalLabel    , 1, 0, 1, 1)
        inputLayout.addWidget(exceptionLabel   , 2, 0, 1, 1)
        inputLayout.addWidget(replaceLabel     , 3, 0, 1, 1)
        inputLayout.addWidget(self.original    , 1, 1, 1, 1)
        inputLayout.addWidget(self.exceptions  , 2, 1, 1, 1)
        inputLayout.addWidget(self.replacement , 3, 1, 1, 1)
        inputLayout.addWidget(self.matchCase   , 4, 0, 1, 1)
        inputLayout.addWidget(self.searchDebug , 4, 1, 1, 1)
        inputLayout.addWidget(filterLabel      , 0, 2, 1, 1)
        inputLayout.addWidget(self.fileFilter  , 1, 2, 1, 1)
        inputLayout.addWidget(self.matchEntry  , 2, 2, 1, 1)
        inputLayout.addWidget(self.matchExact  , 3, 2, 1, 1)
        inputLayout.addWidget(self.matchEnglish, 4, 2, 1, 1)
        #inputLayout.addWidget(self.matchComments,5, 2, 1, 1)
        
        inputLayout.setColumnStretch(1, 1)
        
        self.search.released.connect(self.Search)
        self.replace.released.connect(self.Replace)
        self.checkAll.released.connect(self.checkingAll)
        self.checkNone.released.connect(self.checkingNone)
        self.removeTabButton.released.connect(self.closeCurrentTab)
                
        self.setWindowTitle('Mass Replace')
        layout = QtGui.QVBoxLayout()
        #layout.addWidget(QtGui.QLabel('Replace:'))
        layout.addLayout(inputLayout)
        layout.addWidget(self.tabwidget)
        layout.addLayout(buttonLayout, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(800, 600)

    def generateSearchTab(self):
        treewidget = QtGui.QTreeWidget()
        
        treewidget.setColumnCount(6)
        treewidget.setHeaderLabels(['File', 'Entry', 'Info', 'Replace', 'E String', 'J String', 'Replacement Type', 'Status'])
        treewidget.setSortingEnabled(True)
        
        treewidget.setColumnWidth(0, 120)
        treewidget.setColumnWidth(1, 30)
        treewidget.setColumnWidth(2, 50)
        treewidget.setColumnWidth(3, 20)
        treewidget.setColumnWidth(4, 275)
        treewidget.setColumnWidth(5, 275)
        treewidget.setColumnWidth(6, 30)
        
        #treewidget.setMinimumSize(780, 400)
        treewidget.sortItems(0, QtCore.Qt.AscendingOrder)
        
        treewidget.itemDoubleClicked.connect(self.JumpToFile)
        
        return treewidget

    def checkingAll(self):
    
        Iterator = QtGui.QTreeWidgetItemIterator(self.tabwidget.currentWidget())
        while Iterator.value():

            Iterator.value().setCheckState(3, 2)
            Iterator += 1 
        
    def checkingNone(self):
    
        Iterator = QtGui.QTreeWidgetItemIterator(self.tabwidget.currentWidget())
        while Iterator.value():

            Iterator.value().setCheckState(3, 0)
            Iterator += 1 

    def closeCurrentTab(self):
        self.tabwidget.removeTab( self.tabwidget.currentIndex() )
            
    def Search(self):
        # Place all matching strings to the search into the tree widget
        
        newSearchTab = self.generateSearchTab()


        matchString = unicode(self.original.text())
        exceptString = unicode(self.exceptions.text())

        if matchString.count(unicode('<', 'UTF-8')) != matchString.count(unicode('>', 'UTF-8')):
            
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nPart of a variable: Be sure you know what you're doing.")
            #return

        tabNameString = matchString
        matchString = VariableRemove(matchString)

        if len(matchString) == 1:
            if ord(matchString) <= 0x20:
                reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search can not be only a space, a form feed, a newline, or a tab.")
                return
        elif len(matchString) == 0:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour search can not be empty. Please enter text in the search bar.")
            return

        MatchedEntries = []
        aList = configData.FileList
        
        # turn on case sensitive checking
        if self.matchCase.isChecked():
            CursorGracesJapanese.execute(u"PRAGMA case_sensitive_like = ON")

        # any match within a string
        if self.matchExact.isChecked():
            CursorGracesJapanese.execute(u"select ID from Japanese where string LIKE ?", ('%' + unicode(matchString) + '%', ))
            JPmatches = set(CursorGracesJapanese.fetchall())
            SqlExpressionMatchString = '%' + unicode(matchString) + '%'
            TextSearchColumn = 'English'
            ReplacementType = 'Substr'
        # any match in English strings only
        elif self.matchEnglish.isChecked():
            JPmatches = set()
            SqlExpressionMatchString = '%' + unicode(matchString) + '%'
            TextSearchColumn = 'English'
            ReplacementType = 'Substr'
        # match the entire entry
        elif self.matchEntry.isChecked():
            CursorGracesJapanese.execute(u"select ID from Japanese where string LIKE ?", (unicode(matchString),))
            JPmatches = set(CursorGracesJapanese.fetchall())
            SqlExpressionMatchString = unicode(matchString)
            TextSearchColumn = 'English'
            ReplacementType = 'Entry'
        elif self.matchComments.isChecked():
            JPmatches = set()
            SqlExpressionMatchString = '%' + unicode(matchString) + '%'
            TextSearchColumn = 'Comment'
            ReplacementType = 'CommentSubstr'
            
        ORIDStringList = []
        tmp = ''
        i = 0
        while JPmatches:
            i = i + 1
            if i >= 500: # split up query into multiple queries when it gets too large
                ORIDStringList = ORIDStringList + [tmp]
                tmp = ''
                i = 0
            tmp = tmp + " OR StringID=" + str(JPmatches.pop()[0])
        ORIDStringList = ORIDStringList + [tmp]
        
        AdditionalConstraintsString = ""
        if not self.searchDebug.isChecked():
            AdditionalConstraintsString = "AND status >= 0"
            
            
        for i in range(1, len(aList)):
            for File in aList[i]:
                if File.find(self.fileFilter.text()) >= 0:
                    FilterCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(File))
                    FilterCur = FilterCon.cursor()
                    
                    if self.matchCase.isChecked():
                        FilterCur.execute(u"PRAGMA case_sensitive_like = ON")
                        
                    TempList = []
                    try: # fetch the english entires
                        FilterCur.execute(u"SELECT ID, English, StringID, IdentifyString, status FROM Text WHERE {1} LIKE ? {0}".format(AdditionalConstraintsString, TextSearchColumn), (SqlExpressionMatchString, ))
                    except:
                        FilterCur.execute(u"SELECT ID, English, StringID, '' AS IdentifyString, status FROM Text WHERE {1} LIKE ? {0}".format(AdditionalConstraintsString, TextSearchColumn), (SqlExpressionMatchString, ))
                    TempList = TempList + FilterCur.fetchall()
                    
                    for ORIDString in ORIDStringList: # fetch the japanese entries
                        try:
                            FilterCur.execute(u"SELECT ID, English, StringID, IdentifyString, status FROM Text WHERE ( 1=2 {0} ) {1}".format(ORIDString, AdditionalConstraintsString))
                        except:
                            FilterCur.execute(u"SELECT ID, English, StringID, '' AS IdentifyString, status FROM Text WHERE ( 1=2 {0} ) {1}".format(ORIDString, AdditionalConstraintsString))
                        # This may fetch entries that were already fetched above in the english ones, make sure it's not already added
                        JapaneseFetches = FilterCur.fetchall()
                        for JapaneseFetch in JapaneseFetches:
                            notYetAdded = True
                            for EnglishFetch in TempList:
                                if JapaneseFetch[0] == EnglishFetch[0]:
                                    notYetAdded = False
                                    break
                            if notYetAdded:
                                TempList = TempList + [JapaneseFetch]
                    
                    for item in TempList:
                        ENString = item[1]
                        CursorGracesJapanese.execute('SELECT string FROM Japanese WHERE ID={0}'.format(item[2]))
                        JPString = CursorGracesJapanese.fetchall()[0][0]
                        MatchedEntries.append([File, item[0], ENString, JPString, item[3], item[4]])

                    if self.matchCase.isChecked():
                        FilterCur.execute(u"PRAGMA case_sensitive_like = OFF")
                        
        if len(MatchedEntries) == 0:
            return

        if len(exceptString) >= 1:
            checkForExceptions = True
        else:
            checkForExceptions = False
            
        for item in MatchedEntries:
            try:
                englishString = VariableReplace(item[2])
                japaneseString = VariableReplace(item[3])
                
                if checkForExceptions:
                    if exceptString in englishString:
                        continue
                    
                treeItem = QtGui.QTreeWidgetItem([item[0], str(item[1]), str(item[4]), "", englishString, japaneseString, ReplacementType, str(int(item[5]))])
                treeItem.setCheckState(3, QtCore.Qt.Checked)
                newSearchTab.addTopLevelItem(treeItem)
            except:
                print("Mass Replace: Failed adding file [" + item[0] + "], entry [" + str(item[1]) + "]")
        
        # turn case sensitiveness back off
        if self.matchCase.isChecked():
            CursorGracesJapanese.execute(u"PRAGMA case_sensitive_like = OFF")
            
        self.tabwidget.addTab(newSearchTab, tabNameString)
        self.tabwidget.setCurrentIndex(self.tabwidget.count()-1)
        
    def Replace(self):

        Iterator = QtGui.QTreeWidgetItemIterator(self.tabwidget.currentWidget())

        if len(self.replacement.text()) == 0:
            reply = QtGui.QMessageBox.information(self, "Incorrect Search Usage", "Warning:\n\nYour replacement can not be empty. Please enter text in the search bar.")
            return
                
        while Iterator.value():
        
            if Iterator.value().checkState(3) == 2:
                
                databaseName = Iterator.value().data(0, 0)
                entryID = int(Iterator.value().data(1, 0))
                
                IterCon = sqlite3.connect(configData.LocalDatabasePath + "/{0}".format(databaseName))
                IterCur = IterCon.cursor()
                
                #if self.matchCase.isChecked():
                #    IterCur.execute(u"PRAGMA case_sensitive_like = ON")
                
                
                
                IterCur.execute("SELECT status FROM Text WHERE ID=?", (entryID,))
                currentStatus = IterCur.fetchall()[0][0]

                global ModeFlag
                # if origin by typing or automatic:
                if ModeFlag == 'Manual':
                    # in manual mode: leave status alone, do not change, just fetch the existing one
                    updateStatusValue = currentStatus
                else:
                    # in (semi)auto mode: change to current role, except when disabled by option and current role is lower than existing status
                    global UpdateLowerStatusFlag
                    if UpdateLowerStatusFlag == False:
                        statuscheck = currentStatus
                        if statuscheck > self.parent.role:
                            updateStatusValue = statuscheck
                        else:
                            updateStatusValue = self.parent.role
                    else:
                        updateStatusValue = self.parent.role
                    # endif UpdateLowerStatusFlag
                # endif ModeFlag
                
                
                
                ReplacementType = Iterator.value().data(6, 0)
                if ReplacementType == 'Substr':
                    string = unicode(Iterator.value().data(4, 0))
                    
                    orig = unicode(self.tabwidget.tabText(self.tabwidget.currentIndex()))
                    repl = unicode(self.replacement.text())
                    if self.matchCase.isChecked():
                        string = string.replace(orig, repl)
                    else:
                        string = re.sub('(?i)' + re.escape(orig), repl, string)
                        
                    string = VariableRemove(string)
                elif ReplacementType == 'Entry':
                    string = unicode(self.replacement.text())
                    string = VariableRemove(string)
                                
                IterCur.execute(u"update Text set english=?, updated=1, status=? where ID=?", (unicode(string), updateStatusValue, entryID))
                self.parent.update.add(unicode(databaseName))
            
                #if self.matchCase.isChecked():
                #    IterCur.execute(u"PRAGMA case_sensitive_like = OFF")
                    
                IterCon.commit()

            Iterator += 1 
            
        self.tabwidget.removeTab( self.tabwidget.currentIndex() )
        
    def JumpToFile(self, item, column):
        if item.childCount() > 0:
            return

        file = item.data(0, 0)
        entryno = item.data(1, 0)
        self.parent.JumpToEntry(file, entryno)
        self.parent.show()
        self.parent.raise_()
        self.parent.activateWindow()

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
    string = re.sub(u"\x0A", u"↵\x0A", unicode(string))
    string = re.sub(u"\x0C", u"<Feed>\x0A", unicode(string))
    return string
    
    
def VariableRemove(string):
    string = re.sub(u"'+", "''", unicode(string))
    string = re.sub(u"<Feed>\x0A", u"\x0C", unicode(string))
    string = re.sub(u"<Feed>", u"\x0C", unicode(string))
    string = re.sub(u"↵\x0A", u"\x0A", unicode(string))
    string = re.sub(u"↵", u"\x0A", unicode(string))
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

