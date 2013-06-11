from PyQt4 import QtCore, QtGui

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
        textboxAmountComboBox = QtGui.QComboBox()
        for i in xrange(3, 21):
            textboxAmountComboBox.addItem(str(i))
        entryBoxAmountLayout = QtGui.QHBoxLayout()
        entryBoxAmountLayout.addWidget(textboxAmountComboBox)
        entryBoxAmountLayout.addWidget(textboxAmountLabel)
        checkLayout.addLayout(entryBoxAmountLayout)

        voiceLanguageLabel = QtGui.QLabel('Voice Language')
        voiceLanguageComboBox = QtGui.QComboBox()
        voiceLanguageComboBox.addItem('Japanese')
        voiceLanguageComboBox.addItem('English')
        voiceLanguageLayout = QtGui.QHBoxLayout()
        voiceLanguageLayout.addWidget(voiceLanguageComboBox)
        voiceLanguageLayout.addWidget(voiceLanguageLabel)
        checkLayout.addLayout(voiceLanguageLayout)
                
        self.applyButton.released.connect(self.ApplySettingsAndClose)
        self.cancelButton.released.connect(self.RevertSettingsAndClose)
                
        self.setWindowTitle('Options')
        layout = QtGui.QVBoxLayout()
        layout.addLayout(checkLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        #self.setMinimumSize(800, 600)

    def ApplySettingsAndClose(self):
        return

    def RevertSettingsAndClose(self):
        return
