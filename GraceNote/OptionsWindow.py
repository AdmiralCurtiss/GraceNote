from PyQt4 import QtCore, QtGui
import Globals

class OptionsWindow(QtGui.QDialog):
    def __init__(self, parent):
        super(OptionsWindow, self).__init__()

        self.parent = parent

        self.setWindowModality(False)
        
        self.updateLowerStatusCheckbox = QtGui.QCheckBox('Update Status if current Role is lower than current Status')
        self.enableFooterCheckbox = QtGui.QCheckBox('Enable Footer')
        self.writeToHddCheckbox = QtGui.QCheckBox('Write entries to HDD every time the displayed entry changes')

        #originalLabel = QtGui.QLabel('Search for:')
        #replaceLabel =  QtGui.QLabel('Search for:')
        self.applyButton = QtGui.QPushButton('Apply')
        self.cancelButton = QtGui.QPushButton('Cancel')

        checkLayout = QtGui.QVBoxLayout()
        checkLayout.addWidget(self.updateLowerStatusCheckbox)
        checkLayout.addWidget(self.enableFooterCheckbox)
        checkLayout.addWidget(self.writeToHddCheckbox)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.applyButton)
        buttonLayout.addWidget(self.cancelButton)

        textboxAmountLabel = QtGui.QLabel('Entry Boxes')
        self.textboxAmountComboBox = QtGui.QComboBox()
        for i in xrange(3, 21):
            self.textboxAmountComboBox.addItem(str(i))
        entryBoxAmountLayout = QtGui.QHBoxLayout()
        entryBoxAmountLayout.addWidget(self.textboxAmountComboBox)
        entryBoxAmountLayout.addWidget(textboxAmountLabel)
        checkLayout.addLayout(entryBoxAmountLayout)

        voiceLanguageLabel = QtGui.QLabel('Voice Language')
        self.voiceLanguageComboBox = QtGui.QComboBox()
        self.voiceLanguageComboBox.addItem('Japanese')
        self.voiceLanguageComboBox.addItem('English')
        voiceLanguageLayout = QtGui.QHBoxLayout()
        voiceLanguageLayout.addWidget(self.voiceLanguageComboBox)
        voiceLanguageLayout.addWidget(voiceLanguageLabel)
        checkLayout.addLayout(voiceLanguageLayout)

        self.LoadSettings()
                
        self.applyButton.released.connect(self.ApplySettingsAndClose)
        self.cancelButton.released.connect(self.RevertSettingsAndClose)
                
        self.setWindowTitle('Options')
        layout = QtGui.QVBoxLayout()
        layout.addLayout(checkLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        #self.setMinimumSize(800, 600)

    def LoadSettings(self):
        try:
            self.writeToHddCheckbox.setChecked(Globals.WriteDatabaseStorageToHddOnEntryChange)
            self.enableFooterCheckbox.setChecked(Globals.FooterVisibleFlag)
            self.updateLowerStatusCheckbox.setChecked(Globals.UpdateLowerStatusFlag)
            
            idx = self.textboxAmountComboBox.findText( str(Globals.AmountEditingWindows) )
            self.textboxAmountComboBox.setCurrentIndex(idx)
            
            if Globals.EnglishVoiceLanguageFlag:
                idx = self.voiceLanguageComboBox.findText('English')
            else:
                idx = self.voiceLanguageComboBox.findText('Japanese')
            self.voiceLanguageComboBox.setCurrentIndex(idx)

        except:
            pass

        return

    def ApplySettingsAndClose(self):
        Globals.WriteDatabaseStorageToHddOnEntryChange = self.writeToHddCheckbox.isChecked()
        Globals.Settings.setValue('writeonentrychange', str(Globals.WriteDatabaseStorageToHddOnEntryChange))

        Globals.FooterVisibleFlag = self.enableFooterCheckbox.isChecked()
        Globals.Settings.setValue('footervisible', str(Globals.FooterVisibleFlag))

        Globals.UpdateLowerStatusFlag = self.updateLowerStatusCheckbox.isChecked()
        Globals.Settings.setValue('updatelowerstatus', str(Globals.UpdateLowerStatusFlag))

        Globals.AmountEditingWindows = int(self.textboxAmountComboBox.currentText())
        Globals.Settings.setValue('editpane_amount', str(Globals.AmountEditingWindows))
        
        lang = self.voiceLanguageComboBox.currentText()
        if lang == 'English':
            Globals.EnglishVoiceLanguageFlag = True
            Globals.Settings.setValue('voicelanguage', 'EN')
        elif lang == 'Japanese':
            Globals.EnglishVoiceLanguageFlag = False
            Globals.Settings.setValue('voicelanguage', 'JP')

        Globals.Settings.sync()

        self.done(0)
        return

    def RevertSettingsAndClose(self):
        self.done(-1)
        return
