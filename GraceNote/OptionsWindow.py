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

        self.applyButton = QtGui.QPushButton('Apply')
        self.cancelButton = QtGui.QPushButton('Cancel')

        checkLayout = QtGui.QVBoxLayout()
        
        userNameLabel = QtGui.QLabel('Username')
        self.userNameTextField = QtGui.QLineEdit(Globals.Author)
        userNameLayout = QtGui.QHBoxLayout()
        userNameLayout.addWidget(userNameLabel)
        userNameLayout.addWidget(self.userNameTextField)
        checkLayout.addLayout(userNameLayout)
        
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

        self.colorButtonLowerStatus = QtGui.QPushButton('Color')
        self.colorButtonLowerStatus.released.connect(self.LaunchColorPickerLowerStatus)
        colorLabelLowerStatus = QtGui.QLabel('Color for lower status')
        colorButtonLowerStatusLayout = QtGui.QHBoxLayout()
        colorButtonLowerStatusLayout.addWidget(self.colorButtonLowerStatus)
        colorButtonLowerStatusLayout.addWidget(colorLabelLowerStatus)
        checkLayout.addLayout(colorButtonLowerStatusLayout)

        self.colorButtonCurrentStatus = QtGui.QPushButton('Color')
        self.colorButtonCurrentStatus.released.connect(self.LaunchColorPickerCurrentStatus)
        colorLabelCurrentStatus = QtGui.QLabel('Color for current status')
        colorButtonCurrentStatusLayout = QtGui.QHBoxLayout()
        colorButtonCurrentStatusLayout.addWidget(self.colorButtonCurrentStatus)
        colorButtonCurrentStatusLayout.addWidget(colorLabelCurrentStatus)
        checkLayout.addLayout(colorButtonCurrentStatusLayout)

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
            self.userNameTextField.setText(Globals.Author)

            self.writeToHddCheckbox.setChecked(Globals.WriteDatabaseStorageToHddOnEntryChange)
            self.enableFooterCheckbox.setChecked(Globals.FooterVisibleFlag)
            self.updateLowerStatusCheckbox.setChecked(Globals.UpdateLowerStatusFlag)
            
            idx = self.textboxAmountComboBox.findText( str(Globals.AmountEditingWindows) )
            self.textboxAmountComboBox.setCurrentIndex(idx)
            
            self.ColorLowerStatus = Globals.ColorLowerStatus
            self.colorButtonLowerStatus.setText( str(self.ColorLowerStatus.red()) +  ' / ' + str(self.ColorLowerStatus.green()) + ' / ' + str(self.ColorLowerStatus.blue()) )
            self.ColorCurrentStatus = Globals.ColorCurrentStatus
            self.colorButtonCurrentStatus.setText( str(self.ColorCurrentStatus.red()) +  ' / ' + str(self.ColorCurrentStatus.green()) + ' / ' + str(self.ColorCurrentStatus.blue()) )

        except:
            pass

        return

    def LaunchColorPickerLowerStatus(self):
        col = QtGui.QColorDialog.getColor(self.ColorLowerStatus)
        if col.isValid():
            self.ColorLowerStatus = col
            self.colorButtonLowerStatus.setText( str(self.ColorLowerStatus.red()) +  ' / ' + str(self.ColorLowerStatus.green()) + ' / ' + str(self.ColorLowerStatus.blue()) )
        return
    def LaunchColorPickerCurrentStatus(self):
        col = QtGui.QColorDialog.getColor(self.ColorCurrentStatus)
        if col.isValid():
            self.ColorCurrentStatus = col
            self.colorButtonCurrentStatus.setText( str(self.ColorCurrentStatus.red()) +  ' / ' + str(self.ColorCurrentStatus.green()) + ' / ' + str(self.ColorCurrentStatus.blue()) )
        return

    def ApplySettingsAndClose(self):
        Globals.Author = unicode(self.userNameTextField.text())

        Globals.WriteDatabaseStorageToHddOnEntryChange = self.writeToHddCheckbox.isChecked()
        Globals.Settings.setValue('writeonentrychange', str(Globals.WriteDatabaseStorageToHddOnEntryChange))

        Globals.FooterVisibleFlag = self.enableFooterCheckbox.isChecked()
        Globals.Settings.setValue('footervisible', str(Globals.FooterVisibleFlag))

        Globals.UpdateLowerStatusFlag = self.updateLowerStatusCheckbox.isChecked()
        Globals.Settings.setValue('updatelowerstatus', str(Globals.UpdateLowerStatusFlag))

        Globals.AmountEditingWindows = int(self.textboxAmountComboBox.currentText())
        Globals.Settings.setValue('editpane_amount', str(Globals.AmountEditingWindows))
        
        Globals.ColorLowerStatus = self.ColorLowerStatus
        Globals.Settings.setValue('ColorLowerStatus', str( self.ColorLowerStatus.rgba() ) )
        Globals.ColorCurrentStatus = self.ColorCurrentStatus
        Globals.Settings.setValue('ColorCurrentStatus', str( self.ColorCurrentStatus.rgba() ) )

        Globals.Settings.sync()

        self.done(0)
        return

    def RevertSettingsAndClose(self):
        self.done(-1)
        return
