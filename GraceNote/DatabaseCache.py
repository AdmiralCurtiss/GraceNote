# Caches access to the databasese
import DatabaseHandler
import time
import threading
import Globals

# Setup is:
# Dictionary "Databases" ->
#  Key = Database Filename
#  Value = Array of EntryStructs, index == ID-1

class EntryStruct():
    def __init__(self, english, comment, stringId, status, IdentifyString):
        self.english = english
        self.comment = comment
        self.stringId = stringId
        self.status = status
        self.IdentifyString = IdentifyString
        #self.UpdatedBy
        #self.UpdatedTimestamp

class UpdatedDatabaseEntry():
    def __init__(self, cleanString, databaseName, entry, role, state):
        #string cleanString; // this is the actual entry text
        self.cleanString = cleanString
        #string database;
        self.databaseName = databaseName
        #int entry;
        self.entry = entry
        #int role;
        self.role = role
        #string state; // "ENG" or "COM", defines which column in the database to update
        self.state = state
        self.timestamp = time.clock()

class DatabaseCache(object):
    def __init__(self):
        self.Databases = {}
        self.loadDatabaseThread = threading.Thread(target=self.GetAllDatabasesViaThread)
        self.databaseAccessRLock = threading.RLock()

    def StartBackgroundDatabaseLoadingThread(self):
        self.loadDatabaseThread.start()

    def GetAllDatabasesViaThread(self):
        aList = Globals.configData.FileList
        for j in range(1, len(aList)):
            for File in aList[j]:
                if Globals.GraceNoteIsTerminating:
                    return
                self.GetDatabase(File)
        return

    def GetDatabase(self, name):
        name = str(name)
        if not self.Databases.has_key(name):
            self.LoadDatabase(name)
        return self.Databases[name]

    def LoadDatabase(self, name):
        self.databaseAccessRLock.acquire()
        print 'Loading Database ' + name

        Connection = DatabaseHandler.OpenEntryDatabase(name)
        Cursor = Connection.cursor()
        Cursor.execute("SELECT ID, StringID, english, comment, status, IdentifyString FROM Text")
        table = Cursor.fetchall()

        db = [None] * len(table)
        for entry in table:
            db[ int(entry[0]) - 1 ] = EntryStruct(unicode(entry[2]), unicode(entry[3]), int(entry[1]), int(entry[4]), unicode(entry[5]))

        self.Databases[name] = db

        self.databaseAccessRLock.release()
        return
