#!/usr/bin/env python

import sys
sys.path.append('GraceNote')
sys.stdout = open('stdout.log', 'w')
sys.stderr = open('stderr.log', 'w')
from Scripts import *
from MainWindow import *
import Globals

if __name__ == '__main__':
    print 'Grace Note - Original by Tempus for the Tales of Graces Translation Project'
    print '           - http://www.talesofgraces.com'
    print '           - irc.freenode.net  #Graces'
    print 'Modified and expanded for other games by Admiral H. Curtiss'

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('Grace Note')
    
    if Scripts.SetupEnvironment():
        Globals.configData.DelayedLoad()
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
