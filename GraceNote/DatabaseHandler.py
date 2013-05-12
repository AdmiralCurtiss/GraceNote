import Globals
import sqlite3


def OpenEntryDatabase(filename):
    connection = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(filename))
    
    # check for correct tables, columns, ... and fix if neccesary    
    cursor = connection.cursor()
    
    # SELECT cid, name, type, notnull, dflt_value, pk FROM [somewhere] WHERE [tablename] = Text;
    existingColumns = {}
    cursor.execute("PRAGMA table_info(Text)")
    for row in cursor.fetchall():
        existingColumns[row[1]] = True
    
    if not 'IdentifyString' in existingColumns:
        cursor.execute("ALTER TABLE Text ADD COLUMN IdentifyString text")
        connection.commit()
    if not 'IdentifyPointerRef' in existingColumns:
        cursor.execute("ALTER TABLE Text ADD COLUMN IdentifyPointerRef int")
        connection.commit()
    if not 'UpdatedBy' in existingColumns:
        cursor.execute("ALTER TABLE Text ADD COLUMN UpdatedBy text")
        connection.commit()
    if not 'UpdatedTimestamp' in existingColumns:
        cursor.execute("ALTER TABLE Text ADD COLUMN UpdatedTimestamp int")
        connection.commit()

    cursor.execute("SELECT Count(1) FROM sqlite_master WHERE type='table' AND name='History'")
    exists = cursor.fetchall()[0][0]
    if not exists:
        cursor.execute("CREATE TABLE History(ID int, english text, comment text, status tinyint, UpdatedBy text, UpdatedTimestamp int)")
        cursor.execute("CREATE INDEX History_ID_Index ON History(ID)")
        connection.commit()

    return connection

def CopyEntryToHistory(cursor, ID):
    cursor.execute("INSERT INTO History(ID, english, comment, status, UpdatedBy, UpdatedTimestamp) SELECT ID, english, comment, status, UpdatedBy, UpdatedTimestamp FROM Text WHERE ID = {0}".format(ID))
    return

def GetChangelogData(cursor = None):
    if not cursor:
        cursor = Globals.LogCur
    cursor.execute('SELECT ID, File FROM Log ORDER BY ID')
    results = Globals.LogCur.fetchall()
    LogSet = set(results)
    return LogSet

def GetNewChangelogData():
    NewLogCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/NewChangeLog")
    NewLogCur = NewLogCon.cursor()
    return GetChangelogData(NewLogCur)            

def MergeDatabaseWithServerVersionBeforeUpload(LocalMergeCur, RemoteMergeCur):
    # Merging the Server and the local version
    # First clean up remote version
    RemoteMergeCur.execute(u"update Text set updated=0")
                                
    # Then take new stuff from local
    LocalMergeCur.execute(u'SELECT id, stringid, english, comment, updated, status FROM Text WHERE updated=1')
    NewTable = LocalMergeCur.fetchall()
                    
    # And insert it into the remote
    for item in NewTable:
        DatabaseHandler.CopyEntryToHistory(RemoteMergeCur, item[0])
        RemoteMergeCur.execute(u"UPDATE Text SET english=?, comment=?, status=? WHERE ID=?", (item[2], item[3], item[5], item[0]))
    RemoteMergeCon.commit()
    return

