#!/usr/bin/env python

from Scripts import *


if __name__ == '__main__':

    print "Grace Note v10.0 - Coded by Tempus for the Tales of Graces Translation Project\n    - http://www.talesofgraces.com\n    - irc.freenode.net  #Graces"

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('Grace Note')
    try:
        if sys.argv[1] == '-ruta':
    
#            print 'Available Styles:'
#            for item in QtGui.QStyleFactory.keys():
#                print item
    
            app.setStyle(QtGui.QStyleFactory.create('Plastique'))
    
            colour = QtGui.QColor(255, 245, 250)
            brush = QtGui.QBrush(colour)
            palette = QtGui.QPalette(colour)
    
            app.setPalette(palette)
            print 'Sakura Dream Mode Activated'
    except:
        pass

    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())