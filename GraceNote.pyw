#!/usr/bin/env python

print 'GraceNote.pyw executing...'

import sys

class Tee(object):
    def __init__(self, name, mode, redir):
        self.file = open(name, mode)
        self.stdout = redir
        redir = self
    def __del__(self):
        redir = self.stdout
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.file.flush()
        self.stdout.write(data)


if __name__ == '__main__':
    print 'GraceNote.pyw is main, starting GraceNote...'
    sys.path.append('GraceNote')
    sys.stdout = Tee('stdout.log', 'w', sys.stdout)
    sys.stderr = Tee('stderr.log', 'w', sys.stderr)
    from Scripts import *
    from MainWindow import *
    import Globals

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
else:
    print 'GraceNote.pyw is not main (' + str(__name__) + '), exiting...'
