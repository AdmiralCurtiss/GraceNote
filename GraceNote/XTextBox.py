from PyQt4 import QtCore, QtGui
import Globals
import sqlite3
from HUDLayout import *
import re

try:
    from PyQt4.phonon import Phonon
    Globals.Audio = True
except ImportError:
    print "Your Qt installation does not have Phonon support.\nPhonon is required to play audio clips."
    Globals.Audio = False

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

        if Globals.Audio == True:
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
            
            
        if Globals.enchanted == True:
            self.dict = enchant.Dict("en_GB")
            if os.path.isfile('Resources/proper_nouns.txt'):
                customWordFile = file('Resources/proper_nouns.txt', 'rb')
                for word in customWordFile.xreadlines():
                    self.dict.add_to_session(word.strip())
                customWordFile.close()
            self.dict.add_to_session
            self.highlighter = CustomHighlighter(self.document(), 'something')
            self.highlighter.setDict(self.dict)
        
        self.textChanged.connect(self.textChangedSignal)
        self.undoAvailable.connect(self.modifyTrue)
        
        
    def setFooter(self, footer):
        self.footer = footer
        
    def refreshFooter(self, text, prepend):
        if Globals.FooterVisibleFlag == False:
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
            if Globals.EnglishVoiceLanguageFlag == True:
                return configData.VoicePathEnPrefix + name + configData.VoicePathEnPostfix
            return configData.VoicePathJpPrefix + name + configData.VoicePathJpPostfix
        
        if Globals.HashTableExists == False:
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
        
        if Globals.EnglishVoiceLanguageFlag == True:
            return configData.VoicePathEnPrefix + filename + configData.VoicePathEnPostfix
        return configData.VoicePathJpPrefix + filename + configData.VoicePathJpPostfix

    def playAudio(self):
    
        self.player.clear()
        playerQueue = []
    
        for clip in self.audioClips:
            filename = self.lookupAudioHash(clip)
            if os.path.exists(filename):
                #print 'playing audio: "' + filename + '"'
                playerQueue.append(Phonon.MediaSource(filename))
            else:
                print 'couldn\'t find audio: "' + filename + '"'
                
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
        if Globals.enchanted == True:
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
            if Globals.enchanted == True:
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

