   
class ImageViewerWindow(QtGui.QDialog):

    def __init__(self, parent, image):
        super(ImageViewerWindow, self).__init__()
        self.parent = parent
        self.medium = image
        self.setWindowModality(False)        
        
        self.setWindowTitle(image.name)
        self.scroll = QtGui.QScrollArea()
        self.layout = QtGui.QVBoxLayout(self.scroll)
        self.setLayout(self.layout)
        
    def refreshInfo(self, text):
        search = '<' + self.medium.var + ': (.*?)>'
        parameters = re.findall(search, text, re.DOTALL)
        self.clearInfo()
        
        for param in parameters:
            splitparams = param.split(' ')
            
            pixmap = QtGui.QPixmap( os.getcwd() + '/' + self.medium.path.format(*splitparams) )
            piclabel = QtGui.QLabel()
            piclabel.setPixmap(pixmap)
            self.layout.addWidget(piclabel)
    
    def clearInfo(self):
        if self.layout is not None:
            old_layout = self.layout
            for i in reversed(range(old_layout.count())):
                old_layout.itemAt(i).widget().setParent(None)
            import sip
            sip.delete(old_layout)
        self.layout = QtGui.QVBoxLayout(self.scroll)
        self.setLayout(self.layout)


