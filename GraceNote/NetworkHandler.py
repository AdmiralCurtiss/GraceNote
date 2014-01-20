import Globals
from PyQt4 import QtCore, QtGui
import sqlite3
import ftplib
import CompletionTable
import filecmp
import DatabaseHandler
import NetworkTransferWindow
import threading


def ConnectToFtp():
    ftp = ftplib.FTP()
    ftp.connect(Globals.configData.FTPServer, Globals.configData.FTPPort, 15)
    ftp.login(Globals.configData.FTPUsername, Globals.configData.FTPPassword)
    return ftp

# splash is never used
def RetrieveModifiedFiles(scripts, splash):
    scripts.WriteDatabaseStorageToHdd()

    # open up a window to tell the user what we're doing
    networkTransferWindow = NetworkTransferWindow.NetworkTransferWindow()
    
    networkTransferThread = threading.Thread(target=RetrieveModifiedFilesWorker, args=(scripts, splash, networkTransferWindow, True))
    networkTransferThread.start()
    networkTransferWindow.exec_()

def RetrieveModifiedFilesWorker(scripts, splash, networkTransferWindow, sendWindowCloseSignal):
    scripts.WriteDatabaseStorageToHdd()

    Globals.Cache.databaseAccessRLock.acquire()
    # Nab the online changelog
    try:
        splash.text = 'Downloading updated files...'
    except:
        pass
            
    # loop to prevent crashes during FTP stuff
    for i in range( 0, 20 ):    # range( start, stop, step )
        try:
                
            try: # try to connect to the FTP
                ftp = ConnectToFtp()
                ftp.cwd('/')
                ftp.cwd(Globals.configData.RemoteDatabasePath)
            except: # if FTP conn fails 3 times assume it doesn't work at all and just cancel
                if i > 2:
                    networkTransferWindow.addListEntry("Couldn't connect to FTP Server. Databases may not be up-to-date.", "< Error >")
                    try:
                        splash.text = 'Grace Note Loaded'.format(scripts.roletext[scripts.role], Globals.ModeFlag)
                        splash.complete = True
                        splash.offline = True
                    except:
                        pass
                    if sendWindowCloseSignal:
                        networkTransferWindow.allowCloseSignal.emit(False)
                    Globals.Cache.databaseAccessRLock.release()
                    return
                networkTransferWindow.addListEntry("Couldn't connect to FTP Server, retrying...", "< Error >")
                continue
                    
                        
            # get new changelog
            transferWindowChangeLogIdx = networkTransferWindow.addListEntry("Downloading...", "ChangeLog")
            changes = DownloadFile(scripts, ftp, 'ChangeLog', 'NewChangeLog')
                
            if not changes:
                networkTransferWindow.modifyListEntryStatus(transferWindowChangeLogIdx, "Failed, please retry.")
                if sendWindowCloseSignal:
                    networkTransferWindow.allowCloseSignal.emit(False)
                Globals.Cache.databaseAccessRLock.release()
                return
            
            networkTransferWindow.modifyListEntryStatus(transferWindowChangeLogIdx, "Complete!")

            # Get any new entries
            LogSet = DatabaseHandler.GetChangelogData()
            newLogSet = DatabaseHandler.GetNewChangelogData()
            DownloaderSet = LogSet.symmetric_difference(newLogSet)
            Downloader = []
                        
            for item in DownloaderSet:
                itemList = item[1].split(',')
                for subitem in itemList:
                    Downloader.append(subitem)
                
            # remove possible duplicates from list, so it doesn't download the same file multiple times
            Downloader = list(set(Downloader))
            FilesToDownload = []

            # Don't download stuff that still has unsaved changes locally
            for item in Downloader:
                if item in scripts.update:
                    networkTransferWindow.addListEntry("Not downloading, still has unsaved local changes.", item)
                else: 
                    transferWindowIdx = networkTransferWindow.addListEntry("Waiting...", item)
                    FilesToDownload.append((item, transferWindowIdx))
                
            # Download the files that have been changed
            for item, transferWindowIdx in FilesToDownload:
                #desc = Globals.GetDatabaseDescriptionString(item)
                #print 'Downloading ' + desc + ' [' + item + ']...'
                   
                networkTransferWindow.modifyListEntryStatus(transferWindowIdx, "Downloading...")

                DownloadFile(scripts, ftp, item, 'temp')

                # Clean up downloaded file
                WipeUpdateCon = DatabaseHandler.OpenEntryDatabase('temp')
                WipeUpdateCur = WipeUpdateCon.cursor()
                WipeUpdateCur.execute(u"UPDATE Text SET updated=0")
                WipeUpdateCon.commit()

                # Copy it to the right place
                old = open(Globals.configData.LocalDatabasePath + '/{0}'.format(item), 'wb')
                new = open(Globals.configData.LocalDatabasePath + '/temp', 'rb')
                old.write(new.read())
                new.close()
                old.close()
                    
                CompletionTable.CalculateCompletionForDatabase(item)
                Globals.Cache.LoadDatabase(item)

                networkTransferWindow.modifyListEntryStatus(transferWindowIdx, "Complete!")

            ftp.close()

            
            # Copy new change log over old

            old = open(Globals.configData.LocalDatabasePath + '/ChangeLog', 'wb')
            new = open(Globals.configData.LocalDatabasePath + '/NewChangeLog', 'rb')
            old.write(new.read())
            new.close()
            old.close()

            break
                
        except ftplib.all_errors:
            if i == 19:
                networkTransferWindow.addListEntry("Error during FTP transfer. Databases may not be up-to-date.", "< Error >")
                break
            networkTransferWindow.addListEntry("Error during FTP transfer, retrying...", "< Error >")
            continue
                
    try:
        splash.text = 'Grace Note now {0} in {1} Mode'.format(scripts.roletext[scripts.role], Globals.ModeFlag)
        splash.complete = True
    except:
        pass

    Globals.Cache.databaseAccessRLock.release()
    if sendWindowCloseSignal:
        networkTransferWindow.allowCloseSignal.emit(True)
    return

def DownloadFile(scripts, ftp, source, dest):
    scripts.WriteDatabaseStorageToHdd()

    save = open(Globals.configData.LocalDatabasePath + '/{0}'.format(dest), 'wb')
    ftp.retrbinary('RETR {0}'.format(source), save.write)
    save.close()

    size = ftp.size('{0}'.format(source))

    check = open(Globals.configData.LocalDatabasePath + '/{0}'.format(dest), 'rb')
    localsize = len(check.read())
    check.close()
        
    if size != localsize:
        success = False
        for i in range(3):
            print 'Problem Downloading {0}. Retry #{1}'.format(source, i+1)
                
            e = open(Globals.configData.LocalDatabasePath + '/{0}'.format(dest), 'wb')
            ftp.retrbinary('RETR {0}'.format(source), e.write)
            e.close()
        
            e = open(Globals.configData.LocalDatabasePath + '/{0}'.format(dest), 'rb')
            localsize = len(e.read())
            e.close()

            if size == localsize:
                success = True
                break
        if not success:
            "Looks like {0} won't download. Moving on, I suppose.".format(source)
            return False
                
        
    return True
        

def UploadFile(scripts, ftp, source, dest, confirmUpload=False):
    scripts.WriteDatabaseStorageToHdd()
        
    source = str(source)
    dest = str(dest)
    
    check = open(Globals.configData.LocalDatabasePath + '/{0}'.format(source), 'rb')
    localsize = len(check.read())
    check.close()
        
    success = False
    for i in range(6):
        fnew = open(Globals.configData.LocalDatabasePath + '/{0}'.format(source), 'rb')
        UploadString = str('STOR ' + dest)
        ftp.storbinary(UploadString, fnew)
        fnew.close()
        size = ftp.size(dest)
        if size == localsize:
            if confirmUpload:
                DownloadFile(scripts, ftp, dest, 'uploadConfirmTemp')
                success = filecmp.cmp(Globals.configData.LocalDatabasePath + '/{0}'.format(source), Globals.configData.LocalDatabasePath + '/uploadConfirmTemp')
            else:
                success = True
                break
        else:
            print 'Failed uploading {0}, retrying...'.format(dest)
    if not success:
        "Looks like {0} won't upload. Better talk to Tempus about it.".format(dest)
        return dest
            
        
    return True


def SavetoServer(scripts):
    scripts.WriteDatabaseStorageToHdd()

    if len(scripts.update) == 0:
        Globals.MainWindow.displayStatusMessage('Nothing to save!')
        return False

    # TODO: properly propagate return value
    networkTransferWindow = NetworkTransferWindow.NetworkTransferWindow()
    networkTransferThread = threading.Thread(target=SavetoServerWorker, args=(scripts, networkTransferWindow, True))
    networkTransferThread.start()
    networkTransferWindow.exec_()
                
def SavetoServerWorker(scripts, networkTransferWindow, sendWindowCloseSignal):
    Globals.Cache.databaseAccessRLock.acquire()

    scripts.WriteDatabaseStorageToHdd()
        
    if len(scripts.update) == 0:
        networkTransferWindow.addListEntry("Nothing to save!", "-")
        if sendWindowCloseSignal:
            networkTransferWindow.allowCloseSignal.emit(False)
        Globals.Cache.databaseAccessRLock.release()
        return False

    # Beginning Save...
    autoRestartAfter = False
    for ftperrorcount in range(1, 20):
        try:        
            try:
                scripts.ftp = ConnectToFtp()
            except:
                if ftperrorcount >= 20:
                    networkTransferWindow.addListEntry("Couldn't connect to FTP Server, stopping upload. Please try again later.", "< Error >")
                    Globals.Settings.setValue('update', set(scripts.update))
                    if sendWindowCloseSignal:
                        networkTransferWindow.allowCloseSignal.emit(False)
                    Globals.Cache.databaseAccessRLock.release()
                    return False
                networkTransferWindow.addListEntry("Couldn't connect to FTP Server, retrying...", "< Error >")
                continue

            scripts.ftp.cwd('/')
            scripts.ftp.cwd(Globals.configData.RemoteDatabasePath)

            # Retrieving any files modified by others...
            RetrieveModifiedFilesWorker(scripts, scripts.splashScreen, networkTransferWindow, False)
                
            # Uploading Files...
            LogTable = []
            saveUpdate = set()
                
            # stagger upload into multiple 10-file batches
            # the way this is written we cannot keep it, but eh
            singleFileUploadCounter = 0
                
            for filename in scripts.update:
                singleFileUploadCounter = singleFileUploadCounter + 1
                if singleFileUploadCounter > 10:
                    autoRestartAfter = True
                    saveUpdate.add(filename)
                    continue
                
                # 'Uploading ' + Globals.GetDatabaseDescriptionString(filename) + ' [' + filename + ']...'

                transferWindowIdx = networkTransferWindow.addListEntry("Downloading...", filename)

                # Downloading the server version and double checking
                DownloadFile(scripts, scripts.ftp, str(filename), 'temp')

                try:
                    networkTransferWindow.modifyListEntryStatus(transferWindowIdx, "Merging...")
                    RemoteMergeCon = DatabaseHandler.OpenEntryDatabase('temp')
                    DatabaseHandler.MergeDatabaseWithServerVersionBeforeUpload(
                        DatabaseHandler.OpenEntryDatabase(filename).cursor(),
                        RemoteMergeCon.cursor()
                    )
                    RemoteMergeCon.commit()
                        
                    networkTransferWindow.modifyListEntryStatus(transferWindowIdx, "Uploading...")
                    for ftpSingleFileUpErrorCount in range(1, 20):
                        try:
                            if ftpSingleFileUpErrorCount >= 20:
                                networkTransferWindow.modifyListEntryStatus(transferWindowIdx, "!! Error !! Server file may be corrupted, please manually check and fix or inform someone who can.")
                                if sendWindowCloseSignal:
                                    networkTransferWindow.allowCloseSignal.emit(False)
                                Globals.Cache.databaseAccessRLock.release()
                                return False
                            result = UploadFile(scripts, scripts.ftp, 'temp', str(filename))
                            if isinstance(result, str):
                                continue
                            break
                        except ftplib.all_errors:
                            networkTransferWindow.modifyListEntryStatus(transferWindowIdx, "Error, retrying... (" + str(ftpSingleFileUpErrorCount) + ")")
                            continue
            
                    # And copy the new remote over the old local
                    Globals.CopyFile(Globals.configData.LocalDatabasePath + '/temp', Globals.configData.LocalDatabasePath + '/{0}'.format(filename))

                except:
                    networkTransferWindow.modifyListEntryStatus(transferWindowIdx, "Server file corrupted, replacing with local file...")
                    UploadFile(scripts, scripts.ftp, filename, filename)

                LogTable.append(filename)
                
                networkTransferWindow.modifyListEntryStatus(transferWindowIdx, "Complete!")

                CompletionTable.CalculateCompletionForDatabase(filename)
                Globals.Cache.LoadDatabase(filename)

            # Fix up the changelog and upload
            transferWindowChangeLogIdx = networkTransferWindow.addListEntry("Modifying...", "ChangeLog")

            ChangeLogConnection, ChangeLogCursor = Globals.GetNewChangeLogConnectionAndCursor()
            ChangeLogCursor.execute('SELECT Max(ID) as Highest FROM Log')
            MaxID = ChangeLogCursor.fetchall()[0][0]

            fileString = ''.join(["%s," % (k) for k in LogTable])[:-1]
            # 'Uploaded: ', fileString
                
            ChangeLogCursor.execute(u"insert into Log values({0}, '{1}', '{2}', {3})".format(MaxID + 1, fileString, Globals.Author, "strftime('%s','now')"))
            ChangeLogConnection.commit()
            ChangeLogConnection.close()

            networkTransferWindow.modifyListEntryStatus(transferWindowChangeLogIdx, "Uploading...")
            changeLogUploadSuccess = False
            for changeup in range(1, 20):
                try:
                    result = UploadFile(scripts, scripts.ftp, 'ChangeLog', 'ChangeLog', False)
                    if isinstance(result, str) or not result:
                        if changeup >= 20:
                            break
                        else:
                            networkTransferWindow.modifyListEntryStatus(transferWindowChangeLogIdx, "Error, retrying... (" + str(changeup) + ")")
                            continue
                    networkTransferWindow.modifyListEntryStatus(transferWindowChangeLogIdx, "Complete!")
                    changeLogUploadSuccess = True
                    break
                except ftplib.all_errors:
                    if changeup >= 20:
                        break
                    networkTransferWindow.modifyListEntryStatus(transferWindowChangeLogIdx, "Error, retrying... (" + str(changeup) + ")")
                    continue
            if not changeLogUploadSuccess:
                networkTransferWindow.modifyListEntryStatus(transferWindowChangeLogIdx, "!! Error !! Server ChangeLog may be corrupted, please fix immediately.")
                if sendWindowCloseSignal:
                    networkTransferWindow.allowCloseSignal.emit(False)
                Globals.Cache.databaseAccessRLock.release()
                return False
                
            # Everything is done.
            scripts.ftp.close()
               
            if len(saveUpdate) > 0:
                Globals.MainWindow.displayStatusMessage( 'Retaining the following files for later upload: ' + str(saveUpdate) )
            scripts.update.clear()
            scripts.update = set(saveUpdate)
            Globals.Settings.setValue('update', scripts.update)
            Globals.Settings.sync()

            if autoRestartAfter:
                retval = SavetoServerWorker(scripts, networkTransferWindow, sendWindowCloseSignal)
                Globals.Cache.databaseAccessRLock.release()
                return retval

            if len(scripts.update) > 0:
                Globals.HaveUnsavedChanges = True
            else:
                Globals.HaveUnsavedChanges = False

            scripts.SetWindowTitle()

            if sendWindowCloseSignal:
                networkTransferWindow.allowCloseSignal.emit(True)
            Globals.Cache.databaseAccessRLock.release()
            return True
            
        except ftplib.all_errors:
            if ftperrorcount >= 20:
                networkTransferWindow.addListEntry("Error during FTP transfer. File(s) that were in progress may be corrupted, please confirm and fix.", "< Error >")
                break
            networkTransferWindow.addListEntry("Error during FTP transfer, retrying...", "< Error >")
            continue

    if sendWindowCloseSignal:
        networkTransferWindow.allowCloseSignal.emit(False)
    Globals.Cache.databaseAccessRLock.release()
    return False

def RevertFromServer(scripts):
    Globals.Cache.databaseAccessRLock.acquire()
    scripts.WriteDatabaseStorageToHdd()
        
    if len(scripts.update) == 0:
        Globals.MainWindow.displayStatusMessage( 'Nothing to revert!' )
        Globals.Cache.databaseAccessRLock.release()
        return

    print 'Reverting databases...'
        
        
    for i in range(1, 20):
        try:        
            try:
                scripts.ftp = ConnectToFtp()
            except:
                if i == 20:
                    print "FTP connection failed, revert didn't succeed.\nPlease try to revert again at a later date."
                    Globals.Settings.setValue('update', set(scripts.update))
                    Globals.Settings.sync()
                    Globals.Cache.databaseAccessRLock.release()
                    return
                print 'Error during FTP transfer, retrying...'
                continue
               
            scripts.ftp.cwd('/')
            scripts.ftp.cwd(Globals.configData.RemoteDatabasePath)

            print "Re-getting changed files from server..."
            for item in scripts.update:
                desc = Globals.GetDatabaseDescriptionString(item)
                print 'Downloading ' + desc + ' [' + item + ']...'
                    
                DownloadFile(scripts, scripts.ftp, item, item)
                WipeUpdateCon = DatabaseHandler.OpenEntryDatabase(item)
                WipeUpdateCur = WipeUpdateCon.cursor()
            
                WipeUpdateCur.execute(u"update Text set updated=0")
                WipeUpdateCon.commit()
                    
                CompletionTable.CalculateCompletionForDatabase(item)
                Globals.Cache.LoadDatabase(item)

            scripts.ftp.close()
            scripts.update.clear()
            Globals.Settings.setValue('update', scripts.update)
            Globals.Settings.sync()
            Globals.HaveUnsavedChanges = False
            scripts.SetWindowTitle()
            print 'Reverted!'
            break
        except ftplib.all_errors:
            if i == 20:
                print '20 errors is enough, this is not gonna work. Try again later.'
                break
            print 'Error during FTP transfer, retrying...'
            continue
    Globals.Cache.databaseAccessRLock.release()
    return
    
