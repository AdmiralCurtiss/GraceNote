#!/usr/bin/env python

import sys
sys.path.append('GraceNote')
from Scripts import *
from MainWindow import *
import Globals

if __name__ == '__main__':

    print "Grace Note v10.0 - Coded by Tempus for the Tales of Graces Translation Project\n    - http://www.talesofgraces.com\n    - irc.freenode.net  #Graces"

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('Grace Note')
    
    if Scripts.SetupEnvironment():
        Globals.configData.DelayedLoad()
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
