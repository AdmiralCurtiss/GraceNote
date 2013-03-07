from PyQt4 import QtCore, QtGui

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

