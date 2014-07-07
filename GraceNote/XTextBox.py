# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import Globals
import sqlite3
from HUDLayout import *
import re
import os
from CustomHighlighter import *
try:
    from PyQt4.phonon import Phonon
except ImportError:
    pass

class XTextBox(QtGui.QTextEdit):

    #should be: manualEdit = QtCore.pyqtSignal(int, XTextBox, QtGui.QLabel) but I haven't figured out how to give the current class as parameter
    manualEdit = QtCore.pyqtSignal(int, object, QtGui.QLabel)
    currentEntry = -1


    def __init__(self, parent, contentType = 'ENG', readOnly = False, buttonLess = False):
        super(XTextBox, self).__init__()
        
        self.parent = parent
        self.Jpcon = sqlite3.connect('Resources/JPDictionary')
        self.Jpcur = self.Jpcon.cursor()
        self.modified = False
        self.setAcceptRichText( False )
        
        self.currentlySetStatus = 0
        self.contentType = contentType

        self.buttons = []

        self.readOnly = readOnly
        self.buttonLess = buttonLess

        if Globals.Audio:
            self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory)
            self.player = Phonon.MediaObject()
            Phonon.createPath(self.player, self.audioOutput)

        if contentType == 'ENG':
            self.StatusButtons = {}
            for i in range( 1, Globals.configData.TranslationStagesCount + 1 ):
                button = QtGui.QToolButton()
                button.setAutoRaise(True)
                button.setIcon(QtGui.QIcon('icons/status/{0}.png'.format(i)))
                if self.buttonLess:
                    button.hide()
                self.StatusButtons[i] = button
    
            self.AudioButtonJpn = QtGui.QToolButton()
            self.AudioButtonJpn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
            self.AudioButtonJpn.setAutoRaise(True)
            self.AudioButtonJpn.released.connect(self.playAudioJpn)
            self.AudioButtonJpn.hide()
            self.AudioButtonEng = QtGui.QToolButton()
            self.AudioButtonEng.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
            self.AudioButtonEng.setAutoRaise(True)
            self.AudioButtonEng.released.connect(self.playAudioEng)
            self.AudioButtonEng.hide()

            topLayout = QtGui.QHBoxLayout()

            layout = HUDLayout()
            for i in range( Globals.configData.TranslationStagesCount, 0, -1 ):
                layout.addWidget(self.StatusButtons[i])
            layout.addWidget(self.AudioButtonEng)
            layout.addWidget(self.AudioButtonJpn)
            
            topLayout.setMargin(0)
            topLayout.addLayout(layout)
            self.setLayout(topLayout)

            if not self.readOnly:
                for i in range( 1, Globals.configData.TranslationStagesCount + 1 ):
                    self.StatusButtons[i].released.connect(self.ToggleStatusButtonClosure(i))

        elif contentType == 'JPN' or contentType == 'COM':
            self.jpflag = QtGui.QToolButton()
            self.jpflag.setCheckable(False)
            self.jpflag.setAutoRaise(True)
            self.jpflag.setIcon(QtGui.QIcon('icons/japanflag.png'))
            
            layout = HUDLayout()
            layout.addWidget(self.jpflag)
            self.setLayout(layout)

            self.role = 1

            if contentType == 'COM':
                self.flagToggle()
            
            
        self.highlighter = CustomHighlighter(self)

        if Globals.enchanted:
            import enchant
            self.dict = enchant.Dict("en_US")
            for word in Globals.configData.Dictionary:
                self.dict.add_to_session(word.strip())
            self.highlighter.setDict(self.dict)
        
        self.textChanged.connect(self.textChangedSignal)
        self.undoAvailable.connect(self.modifyTrue)
        
        
    def setFooter(self, footer):
        self.footer = footer
        
    def refreshFooter(self, text, prepend):
        if not Globals.FooterVisibleFlag:
            return
            
        feedCount = text.count('\f')
        sanitizedText = Globals.configData.ReplaceInGameString(text)
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
        if not self.buttonLess:
            self.audioClips = clipList
            self.AudioButtonJpn.show()
            # only display the second button if there are actually two different voice clips
            if not ( Globals.configData.VoicePathEnPrefix == Globals.configData.VoicePathJpPrefix and Globals.configData.VoicePathEnPostfix == Globals.configData.VoicePathJpPostfix ):
                self.AudioButtonEng.show()
                
    def clearPlaybackButtons(self):
        self.audioClips = []
        self.AudioButtonJpn.hide()
        self.AudioButtonEng.hide()

                        
    def lookupAudioHash(self, name, forceAlternateLanguage):
        
        if not Globals.configData.UseGracesVoiceHash:
            if Globals.EnglishVoiceLanguageFlag or forceAlternateLanguage:
                return Globals.configData.VoicePathEnPrefix + name + Globals.configData.VoicePathEnPostfix
            return Globals.configData.VoicePathJpPrefix + name + Globals.configData.VoicePathJpPostfix
        
        if not Globals.HashTableExists:
            return ''
        
        import hashtable

        temphash = 0
        for i in name:
            temphash = ((temphash * 137) + ord(i)) % 0x100000000
        
        if name[:2] == 'VS':
            index = hashtable.hashtable[int(name[2])-1].index(temphash)
            filename = 'VOSCE0' + name[2] + '_' + str(index+1).zfill(5)
        
        elif name[:2] == 'VA':
            index = hashtable.hashtable[8].index(temphash)
            filename = 'VOSCE16' + '_' + str(index+1).zfill(5)
        
        if Globals.EnglishVoiceLanguageFlag or forceAlternateLanguage:
            return Globals.configData.VoicePathEnPrefix + filename + Globals.configData.VoicePathEnPostfix
        return Globals.configData.VoicePathJpPrefix + filename + Globals.configData.VoicePathJpPostfix

    def playAudioJpn(self):
        self.playAudio(self.audioClips, False)
    def playAudioEng(self):
        self.playAudio(self.audioClips, True)

    def playAudio(self, clips, forceAlternateLanguage):
    
        self.player.clear()
        playerQueue = []
    
        for clip in clips:
            filename = self.lookupAudioHash(clip, forceAlternateLanguage)
            if os.path.exists(filename):
                #print 'playing audio: "' + filename + '"'
                playerQueue.append(Phonon.MediaSource(filename))
            else:
                Globals.MainWindow.displayStatusMessage( 'couldn\'t find audio: "' + filename + '"' )
                
        if playerQueue:
            self.player.enqueue(playerQueue)
            self.player.play()

    def textChangedSignal(self):
        if self.modified:
            self.manualEdit.emit(-1, self, self.footer)
            
    def modifyTrue(self, set):
        self.modified = set

    def setText(self, string):
        self.modified = False
        QtGui.QTextEdit.setText(self, string)
        

    def mousePressEvent(self, event):
        if Globals.enchanted:
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
    
        popup_menu.addSeparator()
        searchEntryAction = QtGui.QAction( 'Search for Entry', None )
        searchEntryAction.triggered.connect( self.SearchEntry )
        popup_menu.addAction( searchEntryAction )

        if self.textCursor().hasSelection():
            text = unicode(self.textCursor().selectedText())
            searchSelectionAction = TextAction( u'Search for "' + unicode(text) + u'"', popup_menu )
            searchSelectionAction.data = text
            searchSelectionAction.textActionTriggered.connect( self.SearchSelection )
            popup_menu.addAction( searchSelectionAction )
        popup_menu.addSeparator()
        
        if self.textCursor().hasSelection():
            # Check if the selected word is misspelled or JP and offer spelling
            # suggestions if it is.
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
            if Globals.enchanted:
                if not self.dict.check(text):
                    spell_menu = QtGui.QMenu('Spelling Suggestions')
                    for word in self.dict.suggest(text):
                        action = TextAction(word, spell_menu)
                        action.data = word
                        action.textActionTriggered.connect(self.correctWord)
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
                popup_menu.addSeparator()
                action = TextAction(u'Jump to ' + unicode(textplus), popup_menu)
                action.data = textplus
                action.textActionTriggered.connect(self.jumpToDatabaseFromBracketString)
                popup_menu.addAction(action)
                


        popup_menu.exec_( event.globalPos() )

    def SearchSelection(self, text):
        self.parent.ShowMassReplace()
        self.parent.massDialog.original.setText( text )
        self.parent.massDialog.matchEngCheckbox.setChecked( True if self.contentType == 'ENG' else False )
        self.parent.massDialog.matchJpnCheckbox.setChecked( True if self.contentType == 'JPN' else False )
        self.parent.massDialog.matchEntryCheckbox.setChecked( False )
        self.parent.massDialog.matchCase.setChecked( False )
        self.parent.massDialog.searchDebug.setChecked( False )
        self.parent.massDialog.fileFilter.setText( '' )
        self.parent.massDialog.exceptions.setText( '' )
        self.parent.massDialog.Search()

    def SearchEntry(self):
        self.parent.ShowMassReplace()
        self.parent.massDialog.original.setText( self.toPlainText() )
        self.parent.massDialog.matchEngCheckbox.setChecked( True if self.contentType == 'ENG' else False )
        self.parent.massDialog.matchJpnCheckbox.setChecked( True if self.contentType == 'JPN' else False )
        self.parent.massDialog.matchEntryCheckbox.setChecked( True )
        self.parent.massDialog.matchCase.setChecked( True )
        self.parent.massDialog.searchDebug.setChecked( False )
        self.parent.massDialog.fileFilter.setText( '' )
        self.parent.massDialog.exceptions.setText( '' )
        self.parent.massDialog.Search()

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
        ['vt', 'Transitive Verb'],
        ['v1', 'Ichidan verb'],
        ['v5', 'Verb']]


        for thing in thinglist:
            cookieString = cookieString.replace(thing[0], thing[1])


        cookielist.append(cookieString)

        NewString = match.group(2)
        
        i = 1
        loop = True
        while loop:
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
        # word is something like: "[DRBO1234/56]", "[1]", "[VItems]"
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
        if not self.readOnly:
            cursor = self.textCursor()
            cursor.beginEditBlock()
 
            cursor.removeSelectedText()
            cursor.insertText(word)
 
            cursor.endEditBlock()



    def ToggleStatusButtonClosure(self, status):
        def callFunc():
            if not self.readOnly:
                if self.currentlySetStatus != status:
                    self.StatusButtons[status].setIcon(QtGui.QIcon('icons/status/{0}g.png'.format(status)))
                    self.currentlySetStatus = status
                    self.manualEdit.emit(status, self, self.footer)
                else:
                    self.StatusButtons[status].setIcon(QtGui.QIcon('icons/status/{0}.png'.format(status)))
                    self.currentlySetStatus = status - 1
                    self.manualEdit.emit(status - 1, self, self.footer)
        return callFunc

    def iconToggle(self, icon):
        if icon > Globals.configData.TranslationStagesCount:
            icon = Globals.configData.TranslationStagesCount
        for i in range( 1, Globals.configData.TranslationStagesCount + 1 ):
            self.StatusButtons[i].setIcon(QtGui.QIcon('icons/status/{0}.png'.format(i)))
        for i in range( 1, icon + 1 ):
            self.StatusButtons[i].setIcon(QtGui.QIcon('icons/status/{0}g.png'.format(i)))
        self.currentlySetStatus = icon

    def flagToggle(self):
        if self.readOnly:
            return

        if self.role == 2:
            self.jpflag.setIcon(QtGui.QIcon('icons/cdnflag.png'))
            self.role = 0
        elif self.role == 1:
            self.jpflag.setIcon(QtGui.QIcon('icons/comment.png'))
            self.role = 2
        else:
            self.jpflag.setIcon(QtGui.QIcon('icons/japanflag.png'))
            self.role = 1

class TextAction(QtGui.QAction):
    textActionTriggered = QtCore.pyqtSignal(unicode)
 
    def __init__(self, *args):
        QtGui.QAction.__init__(self, *args)
 
        self.triggered.connect(lambda x: self.textActionTriggered.emit(
            unicode( self.data )))

