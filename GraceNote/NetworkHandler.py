
def RetrieveModifiedFiles(self, splash):
    self.WriteDatabaseStorageToHdd()
        
    # Nab the online changelog
    try:
        splash.text = 'Downloading updated files...'
    except:
        pass
    print 'Downloading updated files...'
            
    # loop to prevent crashes during FTP stuff
    for i in range( 0, 20 ):    # range( start, stop, step )
        try:
                
            try:
                ftp = ftplib.FTP(Globals.configData.FTPServer, Globals.configData.FTPUsername, Globals.configData.FTPPassword, "", 15)
            except:
                if i == 20:
                    print '20 errors is enough, this is not gonna work'
                    try:
                        splash.text = 'Grace Note Loaded'.format(self.roletext[self.role], Globals.ModeFlag)
                        splash.complete = True
                        splash.offline = True
                    except:
                        pass
                    return
                print 'Failed connecting to FTP, retrying...'
                continue
                    
            ftp.cwd('/')
            ftp.cwd(Globals.configData.RemoteDatabasePath)
                        
            changes = self.DownloadFile(ftp, 'ChangeLog', 'NewChangeLog')
                
            if not changes:
                "This isn't going to work, is it? Try again later."
                self.cleanupAndQuit() 


            # Get any new entries
            Globals.LogCur.execute('select ID, File from Log ORDER BY ID')
            results = Globals.LogCur.fetchall()
            LogSet = set(results)

            NewLogCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/NewChangeLog")
            NewLogCur = NewLogCon.cursor()
                
            NewLogCur.execute('select ID, File from Log ORDER BY ID')
            newResults = NewLogCur.fetchall()
            newLogSet = set(newResults)
                
            DownloaderSet = LogSet.symmetric_difference(newLogSet)
            Downloader = []
                        
            for item in DownloaderSet:
                itemList = item[1].split(',')
                for subitem in itemList:
                    if subitem in self.update:
                        print '{0} was skipped because you have local save data which needs uploading.'.format(subitem)
                        continue
                    Downloader.append(subitem)
                
            # by pika: remove possible duplicates from list, so it doesn't download the same file multiple times
            Downloader = list(set(Downloader))
                
            #Downloader.sort()
            for item in set(Downloader):
                Globals.CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [item])
                exists = Globals.CursorGracesJapanese.fetchall()[0][0]
                if exists > 0:
                    Globals.CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [item])
                    desc = Globals.CursorGracesJapanese.fetchall()[0][0]
                    print 'Downloading ' + desc + ' [' + item + ']...'
                else:
                    print 'Downloading ' + item + '...'
                    
                    
                    
                self.DownloadFile(ftp, item, item)
                WipeUpdateCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(item))
                WipeUpdateCur = WipeUpdateCon.cursor()
            
                WipeUpdateCur.execute(u"update Text set updated=0")
                WipeUpdateCon.commit()
                    
                CompletionTable.CalculateCompletionForDatabase(item)

                                
            old = open(Globals.configData.LocalDatabasePath + '/ChangeLog', 'wb')
            new = open(Globals.configData.LocalDatabasePath + '/NewChangeLog', 'rb')
            old.write(new.read())
            new.close()
            old.close()

            ftp.close()
                
            break
                
        except ftplib.all_errors:
            if i == 20:
                print '20 errors is enough, this is not gonna work'
                break
            print 'Error during FTP transfer, retrying...'
            continue
                
    try:
        splash.text = 'Grace Note now {0} in {1} Mode'.format(self.roletext[self.role], Globals.ModeFlag)
        splash.complete = True
    except:
        pass
    print 'Downloaded updated files!'


def DownloadFile(self, ftp, source, dest):
    self.WriteDatabaseStorageToHdd()
                
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
        

def UploadFile(self, ftp, source, dest, confirmUpload=False):
    self.WriteDatabaseStorageToHdd()
        
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
                self.DownloadFile(ftp, dest, 'uploadConfirmTemp')
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


        
def SavetoServer(self):
    self.WriteDatabaseStorageToHdd()
        
    if len(self.update) == 0:
        print 'Nothing to save!'
        return

    print 'Beginning Save...'
        
        
    autoRestartAfter = False
        
    for ftperrorcount in range(1, 20):
        try:        
            try:
                self.ftp = ftplib.FTP(Globals.configData.FTPServer, Globals.configData.FTPUsername, Globals.configData.FTPPassword, "", 15)
            except:
                if ftperrorcount >= 20:
                    print "Warning:\n\nYour computer is currently offline, and will not be able to recieve updates or save to the server. Your progress will instead be saved for uploading upon re-establishment of a network connection, and any text you enter will be preserved automatically until such time."
                    self.settings.setValue('update', set(self.update))
                    return
                print 'Error during FTP transfer, retrying...'
                continue

            progress = QtGui.QProgressDialog("Saving to Server...", "Abort", 0, len(self.update)+1)
            progress.setWindowModality(QtCore.Qt.WindowModal)

            i = 0
            progress.setValue(i)
            progress.setLabelText('Connecting to server...')
                
            self.ftp.cwd('/')
            self.ftp.cwd(Globals.configData.RemoteDatabasePath)

            print "Retrieving any files modified by others..."
            self.RetrieveModifiedFiles(self.splashScreen)
                
            progress.setLabelText('Uploading Files...')
            LogTable = []
            saveUpdate = set()
                
            # stagger upload into multiple 10-file batches
            # the way this is written we cannot keep it, but eh
            singleFileUploadCounter = 0
                
            for filename in self.update:
                singleFileUploadCounter = singleFileUploadCounter + 1
                if singleFileUploadCounter > 10:
                    autoRestartAfter = True
                    saveUpdate.add(filename)
                    continue
                    
                # remove empty comments
                rcommentconn = sqlite3.connect(Globals.configData.LocalDatabasePath + "/" + filename)
                rcommentcur = rcommentconn.cursor()
                rcommentcur.execute(u"UPDATE text SET comment = '', updated = 1 WHERE comment IS NULL")
                rcommentconn.commit()
                rcommentconn.close()
                    
                Globals.CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [filename])
                exists = Globals.CursorGracesJapanese.fetchall()[0][0]
                if exists > 0:
                    Globals.CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [filename])
                    desc = Globals.CursorGracesJapanese.fetchall()[0][0]
                    print 'Uploading ' + desc + ' [' + filename + ']...'
                else:
                    print 'Uploading ' + filename + '...'

                # Downloading the server version and double checking
                self.DownloadFile(self.ftp, str(filename), 'temp')

                try:
                    WipeUpdateCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/temp")
                    WipeUpdateCur = WipeUpdateCon.cursor()
                
                    WipeUpdateCur.execute(u"update Text set updated=0")
                    WipeUpdateCon.commit()
                        
                    # Merging the Server and the local version
                    NewMergeCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(filename))
                    NewMergeCur = NewMergeCon.cursor()
            
                    OldMergeCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/temp")
                    OldMergeCur = OldMergeCon.cursor()
                                
                    NewMergeCur.execute(u'SELECT id, stringid, english, comment, updated, status FROM Text WHERE updated=1')
                    NewTable = NewMergeCur.fetchall()
                    
                    for item in NewTable:
                        if item[4] == 1:
                            OldMergeCur.execute(u"UPDATE Text SET english=?, comment=?, status=? WHERE ID=?", (item[2], item[3], item[5], item[0]))
                    OldMergeCon.commit()
                        
                    # Upload new file
                    for ftpSingleFileUpErrorCount in range(1, 20):
                        try:
                            if ftpSingleFileUpErrorCount >= 20:
                                print 'Failed on single file 20 files, try again later and confirm the server file is not corrupted.'
                                print 'File in question: ' + filename
                                return
                            result = self.UploadFile(self.ftp, 'temp', str(filename))
                            if isinstance(result, str):
                                continue
                            break
                        except ftplib.all_errors:
                            print 'Error uploading ' + filename + ', retrying...'
                            continue
            
                    # Transposing the local file
                    fnew = open(Globals.configData.LocalDatabasePath + '/temp', 'rb')
                    data = fnew.read()
                    fnew.close()
                        
                    old = open(Globals.configData.LocalDatabasePath + '/{0}'.format(filename), 'wb')
                    old.write(data)
                    old.close()

                except:
                    
                    print 'Server file corrupted. Fixing...'
                        
                    self.UploadFile(self.ftp, filename, filename)
                    
                    print 'Fixed'

                i = i + 1
                progress.setValue(i)

                LogTable.append(filename)
                    
                CompletionTable.CalculateCompletionForDatabase(filename)

            # Fix up the changelog and upload
            Globals.LogCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/ChangeLog")
            Globals.LogCur = Globals.LogCon.cursor()

            Globals.LogCur.execute('select Max(ID) as Highest from Log')
            MaxID = Globals.LogCur.fetchall()[0][0]

            fileString = ''.join(["%s," % (k) for k in LogTable])[:-1]
            print 'Uploaded: ', fileString
                
            Globals.LogCur.execute(u"insert into Log values({0}, '{1}', '{2}', {3})".format(MaxID + 1, fileString, self.author, "strftime('%s','now')"))
            Globals.LogCon.commit()

            print 'Uploading: ChangeLog'
            changeLogUploadSuccess = False
            for changeup in range(1, 20):
                try:
                    result = self.UploadFile(self.ftp, 'ChangeLog', 'ChangeLog', False)
                    if isinstance(result, str) or not result:
                        if changeup >= 20:
                            print "ERROR:\n\nChangelog has not been uploaded, please retry immediately."
                            break
                        else:
                            print 'Changelog upload failed, trying again! ({0}/20)'.format(changeup)
                            continue
                    #self.ftp.rename('NewChangeLog', 'ChangeLog')
                    changeLogUploadSuccess = True
                    break
                except ftplib.all_errors:
                    if changeup >= 20:
                        print 'ERROR:\n\Changelog has not been uploaded, please retry immediately.'
                        break
                    print 'Error uploading Changelog, retrying...'
                    continue
            if not changeLogUploadSuccess:
                return
                
            # Everything is done.
            progress.setValue(len(self.update)+1);

            print 'Done!'
            self.ftp.close()
                
            print 'Retaining the following files for later upload: ', saveUpdate
            self.update.clear()
            self.update = set(saveUpdate)
            self.settings.setValue('update', self.update)
            self.settings.sync()
                
            if autoRestartAfter:
                self.SavetoServer()
            break
        except ftplib.all_errors:
            if ftperrorcount >= 20:
                print '20 errors is enough, this is not gonna work. There is probably some fucked up file on the FTP server now, please fix manually or contact someone that knows how to.'
                break
            print 'Error during FTP transfer, retrying...'
            continue

def RevertFromServer(self):
    self.WriteDatabaseStorageToHdd()
        
    if len(self.update) == 0:
        print 'Nothing to revert!'
        return

    print 'Reverting databases...'
        
        
    for i in range(1, 20):
        try:        
            try:
                self.ftp = ftplib.FTP(Globals.configData.FTPServer, Globals.configData.FTPUsername, Globals.configData.FTPPassword, "", 15)
            except:
                if i == 20:
                    print "FTP connection failed, revert didn't succeed.\nPlease try to revert again at a later date."
                    self.settings.setValue('update', set(self.update))
                    self.settings.sync()
                    return
                print 'Error during FTP transfer, retrying...'
                continue
               
            self.ftp.cwd('/')
            self.ftp.cwd(Globals.configData.RemoteDatabasePath)

            print "Re-getting changed files from server..."
            for item in self.update:
                Globals.CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [item])
                exists = Globals.CursorGracesJapanese.fetchall()[0][0]
                if exists > 0:
                    Globals.CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [item])
                    desc = Globals.CursorGracesJapanese.fetchall()[0][0]
                    print 'Downloading ' + desc + ' [' + item + ']...'
                else:
                    print 'Downloading ' + item + '...'
                    
                    
                    
                self.DownloadFile(self.ftp, item, item)
                WipeUpdateCon = sqlite3.connect(Globals.configData.LocalDatabasePath + "/{0}".format(item))
                WipeUpdateCur = WipeUpdateCon.cursor()
            
                WipeUpdateCur.execute(u"update Text set updated=0")
                WipeUpdateCon.commit()
                    
                CompletionTable.CalculateCompletionForDatabase(item)

            self.ftp.close()
            self.update.clear()
            self.settings.setValue('update', self.update)
            self.settings.sync()
            print 'Reverted!'
            break
        except ftplib.all_errors:
            if i == 20:
                print '20 errors is enough, this is not gonna work. Try again later.'
                break
            print 'Error during FTP transfer, retrying...'
            continue
    