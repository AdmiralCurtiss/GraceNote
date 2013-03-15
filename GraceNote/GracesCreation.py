import Globals
from PyQt4 import QtCore, QtGui
import sqlite3
import os, sys, re, time, struct, platform
import shutil
import ftplib
from binascii import hexlify, unhexlify
import subprocess
import codecs
from Config import *
from collections import deque
import filecmp


def SavetoPatch(self):
    self.WriteDatabaseStorageToHdd()
        


    # Make some output directories
    if not os.path.exists('riivolution'):
        os.makedirs('riivolution')

    if not os.path.exists('Graces'):
        os.makedirs('Graces')

    if not os.path.exists('Resources/Wii'):
        os.makedirs('Resources/Wii')

    rootFile = open('Graces/rootR.bin', 'wb')
    map0File = open('Graces/map0R.bin', 'wb')
    map1File = open('Graces/map1R.bin', 'wb')



    # Everyone loves progress bars!
    progress = QtGui.QProgressDialog("Saving databases...", "Abort", 0, 1260)
    progress.setWindowModality(QtCore.Qt.WindowModal)


    Archive = Globals.configDataGracesFolders[1][:] # Chat_MS
    Archive.extend(Globals.configDataGracesFolders[2][:]) # Chat_SB
    Archive.extend(Globals.configDataGracesFolders[-1][:]) # SysString.bin
    Archive = (['TOG_SS_ChatName', 'TOG_SS_StringECommerce']) # Special Cased Sys Subs
    Archive.extend(Globals.configDataGracesFolders[-2][:]) # Movie Subtitles
    Archive.extend(Globals.configDataGracesFolders[-3][:]) # Special Strings

    print 'Creating root (Chat, SysString, Subtitles, Special stuff)'
    self.MakeSCS(Archive, progress, 'Wii', rootFile)

    Images = ["Resources/TitleTexture.tex", 
                "Resources/main.tex",
                "Resources/shop.tex",
                "Resources/skill.tex",
#                  "Resources/snd_test.tex",
                "Resources/bin000.acf",
                "Resources/FontTexture2.tex",
                "Resources/FontBinary2.bin",
                "Resources/mainRR.sel"
                ]

    for image in Images:
        tempFile = open(image, 'rb')
        tempData = tempFile.read()
        rootFile.write(tempData)
        tempFile.close()
    rootFile.close()



    Map0RCPK = ['mapfile_basiR.cpk', 'mapfile_briaR.cpk', 'mapfile_bridR.cpk', 'mapfile_caveR.cpk', 'mapfile_fallR.cpk', 'mapfile_ff12R.cpk', 'mapfile_ff13R.cpk', 'mapfile_ff14R.cpk', 'mapfile_ff15R.cpk', 'mapfile_ff16R.cpk', 'mapfile_ff17R.cpk', 'mapfile_ff19R.cpk', 'mapfile_ff20R.cpk', 'mapfile_foreR.cpk', 'mapfile_gentR.cpk', 'mapfile_icebR.cpk', 'mapfile_ironR.cpk', 'mapfile_koneR.cpk', 'mapfile_kotR.cpk', 'mapfile_lasR.cpk', 'mapfile_montR.cpk', 'mapfile_rockR.cpk', 'mapfile_sandR.cpk', 'mapfile_sf08R.cpk', 'mapfile_sf09R.cpk', 'mapfile_sf10R.cpk', 'mapfile_sf11R.cpk', 'mapfile_sf18R.cpk', 'mapfile_sneeR.cpk', 'mapfile_snowR.cpk', 'mapfile_stdaR.cpk', 'mapfile_varoR.cpk', 'mapfile_wf01R.cpk', 'mapfile_wf02R.cpk', 'mapfile_wf03R.cpk', 'mapfile_wf04R.cpk', 'mapfile_wf05R.cpk', 'mapfile_wf06R.cpk', 'mapfile_wf07R.cpk', 'mapfile_wf21R.cpk', 'mapfile_wincR.cpk', 'mapfile_zoneR.cpk']

    i = 4

    print 'Creating Map0'
    for CPK in Map0RCPK:
        Archive = Globals.configDataGracesFolders[i]
        self.MakeSCS(Archive, progress, 'Wii', map0File)
        i += 1
            
    map0File.close()
        

    Map1RCPK = ['mapfile_anmaR.cpk', 'mapfile_beraR.cpk', 'mapfile_debugR.cpk', 'mapfile_fendR.cpk', 'mapfile_kameR.cpk', 'mapfile_koya_r06R.cpk', 'mapfile_lakeR.cpk', 'mapfile_lanR.cpk', 'mapfile_nekoR.cpk', 'mapfile_olleR.cpk', 'mapfile_otheR.cpk', 'mapfile_ozweR.cpk', 'mapfile_riotR.cpk', 'mapfile_sablR.cpk', 'mapfile_shatR.cpk', 'mapfile_shipR.cpk', 'mapfile_strtR.cpk', 'mapfile_supaR.cpk', 'mapfile_systemR.cpk', 'mapfile_winR.cpk']

    i = 46

    print 'Creating Map1'
    for CPK in Map1RCPK:
        Archive = Globals.configDataGracesFolders[i]
        self.MakeSCS(Archive, progress, 'Wii', map1File)
        i += 1

    map1File.close()
        
    progress.setValue(1260)


    #shutil.rmtree('Resources/Wii')



def MakeSCS(self, allFiles, progress, path, BIN=None):
    self.WriteDatabaseStorageToHdd()
        


    # Create the .scs files
        
    JPCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/GracesJapanese')
    JPCur = JPCon.cursor()

    fileExceptions = ['GracesJapanese', 'NewChangeLog', 'None', 'ChangeLog', 'temp', '.DS_Store', 'endingData', 'Artes', 'Battle', 'Discovery', 'GradeShop-Missions', 'Item', 'MonsterBook', 'Skills', 'System', 'Tactics', 'Titles', 'Tutorial', 'soundTest', 'ArteNames', 'Skits', 'GracesFDump', 'S', 'CheckTags.bat', 'System.Data.SQLite.DLL', 'GraceNote_CheckTags.exe', 'sqlite3.exe', 'taglog.txt', 'CompletionPercentage']

    i = 0
    p = 0


    for filename in allFiles:

        progress.setValue(progress.value() + 1)

        if fileExceptions.count(filename) > 0:
            continue
        print filename

        OutCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/{0}'.format(filename))
        OutCur = OutCon.cursor()

            
        OutCur.execute("select english, StringID from Text")
        i += 1
            
        stringlist = []
        TempList = OutCur.fetchall()
            
        for i in xrange(len(TempList)):

            # Generate Strings Table
            if TempList[i][0] != '':
                string = re.sub(u"'+", "'", unicode(TempList[i][0]))
                string = re.sub(u"‾", u"~", unicode(string))
                string = unicode(string).replace(u" ", u"_")
                string = unicode(string).replace(u"　", u"_")
                string = unicode(string).encode('cp932', 'ignore')
                if not string.endswith('\x00'):
                    string = string + '\x00'
                stringlist.append(string)
            else:
                JPCur.execute("select string from Japanese where ID={0}".format(TempList[i][1]))
                p += 1
                string = JPCur.fetchall()[0][0]
                string = re.sub(u"‾", u"~", unicode(string))
                string = unicode(string).replace(u" ", u"_")
                string = unicode(string).replace(u"　", u"_")
                string = unicode(string).encode('cp932', 'ignore')
                if not string.endswith('\x00'):
                    string = string + '\x00'
                stringlist.append(string)
        
        
        # Generate Length Table
        length = (len(stringlist) * 4) + 4
        newlenlist = [struct.pack('>I', len(stringlist))]
        for x in stringlist:
            newlenlist.append(struct.pack('>I', length))
            length += len(x)
                    
                                
        # Generate the concatenated strings
        newlendata = "".join(["%s" % (k) for k in newlenlist])
        stringdata = "".join(["%s" % (k) for k in stringlist])


        # Exceptions
        if filename == 'CharName':
            f = open('Resources/CharNameHeader.bin', 'rb')
            CharNameHeader = f.read()
            f.close()
                
            newlendata = CharNameHeader + newlendata

        if filename == 'CharName-f':
            f = open('Resources/FResources/CharNameHeader.bin', 'rb')
            CharNameHeader = f.read()
            f.close()
                
            newlendata = CharNameHeader + newlendata
                
        if filename == 'TOG_SS_ChatName':
            ChatNameHeader = unhexlify('0000000C000000140000015D544F31305F434E2000000000')
                
            length = (len(stringlist) * 4)
            newlenlist = []
            for x in stringlist:
                newlenlist.append(struct.pack('>I', length))
                length += (len(x) - 4)
                    
            newlendata = ChatNameHeader + "".join(["%s" % (k) for k in newlenlist])

        if filename == 'TOG_SS_ChatName-f':
            ChatNameHeader = unhexlify('0000000C00000014000001B1544F31305F434E2000000000')
                
            length = (len(stringlist) * 4)
            newlenlist = []
            for x in stringlist:
                newlenlist.append(struct.pack('>I', length))
                length += (len(x) - 4)
                    
            newlendata = ChatNameHeader + "".join(["%s" % (k) for k in newlenlist])

        if filename == 'TOG_SS_StringECommerce':
            ChatNameHeader = unhexlify('0000000C000000140000003A544F47535452462000000000')
                
            length = (len(stringlist) * 4) + 4
            newlenlist = [struct.pack('>I', len(stringlist))]
            i = 0
            for x in stringlist:
                newlenlist.append(struct.pack('>I', i))
                newlenlist.append(struct.pack('>I', length))
                length += len(x)
                i += 1
                    
            newlendata = "".join(["%s" % (k) for k in newlenlist])
            newlendata = ChatNameHeader + newlendata[4:]

            
        if filename == 'MapName':

            indexList = [0, 0, 1, 2, 3, 4, 5, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 51, 52, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 47, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 86, 87, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 126, 127, 127, 128, 128, 129, 130, 131, 132, 133, 134, 135, 135, 136, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 147, 148, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 47, 48, 159, 160, 161, 161, 1, 162, 1, 163, 1, 164, 1, 165, 1, 166, 1, 167, 1, 168, 1, 169, 1, 170, 1, 171, 1, 172, 1, 173, 174, 175, 1, 176, 1, 177, 1, 178, 1, 179, 1, 180, 1, 181, 1, 182, 1, 183, 1, 184, 1, 185, 1, 186, 1, 186, 1, 186, 3, 186, 7, 187, 7, 188, 189, 190, 137, 191, 137, 192, 9, 193, 189, 194, 11, 195, 189, 196, 139, 197, 139, 198, 13, 199, 15, 200, 15, 201, 189, 202, 17, 203, 19, 204, 21, 205, 23, 206, 189, 207, 25, 208, 27, 209, 141, 210, 141, 211, 29, 212, 143, 213, 143, 214, 31, 215, 189, 216, 33, 217, 145, 218, 145, 219, 35, 220, 37, 221, 39, 222, 41, 223, 43, 224, 45, 225, 47, 226, 49, 227, 49, 228, 53, 229, 53, 230, 53, 231, 53, 232, 53, 233, 53, 234, 53, 235, 53, 236, 53, 237, 53, 238, 53, 239, 53, 240, 53, 241, 53, 242, 53, 243, 53, 244, 53, 245, 53, 246, 53, 247, 53, 248, 55, 249, 55, 250, 251, 252, 55, 253, 55, 254, 55, 255, 55, 256, 55, 257, 55, 258, 55, 259, 55, 260, 251, 261, 55, 262, 55, 263, 55, 264, 55, 265, 55, 266, 55, 267, 55, 268, 55, 269, 55, 270, 57, 271, 57, 272, 273, 274, 57, 275, 57, 276, 57, 277, 57, 278, 57, 279, 57, 280, 59, 281, 59, 282, 61, 283, 61, 284, 61, 285, 61, 286, 63, 287, 63, 288, 63, 289, 63, 290, 63, 291, 63, 292, 63, 293, 63, 294, 63, 295, 63, 296, 63, 297, 63, 298, 63, 299, 65, 300, 65, 301, 65, 302, 67, 303, 67, 304, 67, 305, 67, 306, 69, 307, 308, 309, 69, 310, 69, 311, 69, 312, 69, 313, 69, 314, 69, 315, 69, 316, 69, 317, 308, 318, 71, 319, 71, 320, 71, 321, 71, 322, 71, 323, 71, 324, 73, 325, 73, 326, 73, 327, 73, 328, 73, 329, 73, 330, 73, 331, 73, 332, 75, 333, 75, 334, 335, 336, 78, 337, 78, 338, 80, 339, 80, 340, 82, 341, 84, 342, 88, 343, 344, 345, 346, 347, 90, 348, 90, 349, 92, 350, 94, 351, 94, 352, 96, 353, 96, 354, 98, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 382, 384, 382, 385, 382, 386, 382, 387, 382, 388, 382, 389, 382, 390, 100, 391, 100, 392, 100, 393, 100, 394, 100, 395, 100, 396, 100, 397, 100, 398, 100, 399, 100, 400, 100, 401, 100, 402, 100, 403, 100, 404, 100, 405, 100, 406, 100, 407, 100, 408, 100, 409, 100, 410, 100, 411, 100, 412, 102, 413, 102, 414, 104, 415, 416, 417, 416, 418, 416, 419, 420, 421, 420, 422, 420, 423, 420, 424, 420, 425, 426, 427, 426, 428, 426, 429, 426, 430, 426, 431, 426, 432, 426, 433, 434, 435, 434, 436, 434, 437, 438, 439, 438, 440, 438, 441, 438, 442, 434, 443, 434, 444, 434, 445, 446, 447, 446, 448, 446, 449, 106, 450, 451, 452, 453, 454, 455, 456, 455, 457, 458, 459, 458, 460, 461, 462, 461, 463, 461, 464, 461, 465, 461, 466, 461, 454, 461, 456, 467, 457, 467, 468, 469, 470, 469, 471, 472, 473, 108, 474, 108, 475, 108, 476, 108, 477, 108, 478, 108, 479, 108, 480, 108, 481, 108, 482, 108, 483, 110, 484, 110, 485, 110, 486, 110, 487, 110, 488, 110, 489, 110, 490, 110, 491, 110, 492, 110, 493, 110, 494, 110, 495, 110, 496, 110, 497, 110, 498, 110, 499, 112, 500, 112, 501, 112, 502, 112, 503, 112, 504, 112, 505, 112, 506, 112, 507, 112, 508, 112, 509, 112, 510, 112, 511, 112, 512, 112, 513, 112, 514, 112, 515, 112, 516, 112, 517, 112, 518, 112, 519, 112, 520, 112, 521, 112, 522, 112, 523, 112, 524, 112, 525, 112, 526, 112, 527, 528, 529, 528, 530, 531, 532, 531, 533, 531, 534, 535, 536, 535, 537, 535, 538, 535, 539, 540, 541, 540, 542, 540, 543, 544, 545, 544, 546, 528, 547, 528, 548, 531, 549, 531, 550, 535, 551, 535, 552, 535, 553, 535, 554, 540, 555, 540, 556, 540, 557, 558, 559, 544, 560, 535, 561, 116, 562, 116, 563, 116, 564, 116, 565, 116, 566, 116, 567, 116, 568, 116, 569, 116, 570, 116, 571, 116, 572, 116, 573, 116, 574, 116, 575, 116, 576, 116, 577, 116, 578, 118, 579, 118, 580, 581, 582, 581, 583, 581, 584, 581, 585, 581, 586, 581, 587, 581, 588, 581, 589, 581, 590, 581, 591, 581, 592, 581, 593, 581, 594, 581, 595, 581, 596, 581, 597, 581, 598, 581, 599, 581, 600, 581, 601, 581, 602, 581, 603, 581, 604, 581, 605, 581, 606, 581, 607, 581, 608, 609, 610, 609, 611, 609, 612, 609, 613, 614, 615, 614, 616, 617, 618, 619, 620, 619, 621, 122, 622, 122, 623, 122, 624, 625, 626, 124, 627, 189, 628, 625, 629, 126, 630, 126, 631, 131, 632, 131, 633, 131, 634, 131, 635, 133, 636, 133, 637, 133, 638, 133, 639, 133, 640, 133, 641, 133, 642, 133, 643, 133, 644, 133, 645]
                
            newlendata = struct.pack('>I', len(indexList))
                
            for listItem in indexList:
                newlendata += struct.pack('>I', struct.unpack('>I', newlenlist[listItem+1])[0] + 0x684)



        if BIN == None:
            # Write it to a file
            binFiles = ['ActInfo', 'CharName', 'MapName', 'Navigation', 'TOG_S01', 'TOG_S02', 'TOG_S03', 'TOG_S04', 'TOG_S05', 'TOG_S06', 'TOG_S07', 'TOG_S08', 'TOG_S09', 'TOG_S10', 'TOG_S11', 'SysString']
                
            datFiles = ['TOG_SS_ChatName', 'TOG_SS_StringECommerce']
                
            if binFiles.count(filename) >0:
                with open('Resources/{0}/{1}.bin'.format(path,filename), 'wb') as f:
                    writeOut = (newlendata + stringdata) 
                    f.write(writeOut + '\x00'*(0x1000-(len(writeOut)%0x1000)))
                    f.close()
            if datFiles.count(filename) >0:
                with open('Resources/{0}/{1}.dat'.format(path,filename), 'wb') as f:
                    writeOut = (newlendata + stringdata) 
                    f.write(writeOut + '\x00'*(0x1000-(len(writeOut)%0x1000)))
                    f.close()
            else:
                with open('Resources/{0}/{1}.scs'.format(path,filename), 'wb') as f:
                    writeOut = (newlendata + stringdata) 
                    f.write(writeOut + '\x00'*(0x1000-(len(writeOut)%0x1000)))
                    f.close()
                        
        else:
            writeOut = (newlendata + stringdata) 
            BIN.write(writeOut + '\x00'*(0x1000-(len(writeOut)%0x1000)))



#    def BabysitGraceful(self, args):
#        exec_args = args[:2]
#        args      = args[2:]
#        args.append('11') #Make sure to manually quit
#        stdout_dump = StringIO.StringIO()
#        if sys.platform == 'win32': exec_args.pop(0) #We don't need the "mono" argument in win32, so remove it
#        proc = subprocess.Popen(exec_args, shell=False, stdin=subprocess.PIPE,stdout=subprocess.PIPE)
#        while args:
#            arg = args.pop(0)
#            print arg
#            subprocess.send_all(proc, arg + '\n')
#            stdout_dump.write(subprocess.recv_some(proc, t=.01, tr=2))
#        stdout_dump.write(proc.recv())
#        return stdout_dump.getvalue()


def SavetoXML(self):
    self.WriteDatabaseStorageToHdd()
        


    # Make some output directories
    if not os.path.exists('riivolution'):
        os.makedirs('riivolution')

    if not os.path.exists('Graces'):
        os.makedirs('Graces')

    if not os.path.exists('Graces/v0'):
        os.makedirs('Graces/v0')

    if not os.path.exists('Resources/Wii'):
        os.makedirs('Resources/Wii')


    if self.settings.contains('Graceful'):
        Graceful = self.settings.value('Graceful')
        if not os.path.isfile(Graceful):
            Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
            if Graceful == '': return
            Graceful = str(Graceful)
    else:
        Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
        if Graceful == '': return
        Graceful = str(Graceful)
    self.settings.setValue("Graceful", Graceful)

    if self.settings.contains('RootR'):
        RootR = self.settings.value('RootR')
        if not os.path.isfile(RootR):
            RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if RootR == '': return
            RootR = str(RootR)
    else:
        RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if RootR == '': return
        RootR = str(RootR)
    self.settings.setValue("RootR", RootR)

    if self.settings.contains('Map0R'):
        Map0R = self.settings.value('Map0R')
        if not os.path.isfile(Map0R):
            Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map0R == '': return
            Map0R = str(Map0R)
    else:
        Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if Map0R == '': return
        Map0R = str(Map0R)
    self.settings.setValue("Map0R", Map0R)

    if self.settings.contains('Map1R'):
        Map1R = self.settings.value('Map1R')
        if not os.path.isfile(Map1R):
            Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map1R == '': return
            Map1R = str(Map1R)
    else:
        Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if Map1R == '': return
        Map1R = str(Map1R)
    self.settings.setValue("Map1R", Map1R)

        
    #Delety function!
    TestPath = [os.path.dirname(str(RootR)), os.path.dirname(str(Map0R)), os.path.dirname(str(Map1R))]
        
    for Path in TestPath:
        for File in os.listdir(Path):
            if File.rfind('.toc') >= 0:
                os.remove(Path + "/" + File)
            if File.rfind('.patch') >=0:
                os.remove(Path + '/' + File)


    # Everyone loves progress bars!
    progress = QtGui.QProgressDialog("Saving databases to SCS...", "Abort", 0, len(os.listdir(Globals.configData.LocalDatabasePath))+1)
    progress.setWindowModality(QtCore.Qt.WindowModal)


    # Create the .scs files
    self.MakeSCS(os.listdir(Globals.configData.LocalDatabasePath), progress, 'Wii')

    progress.setValue(len(os.listdir(Globals.configData.LocalDatabasePath))+1)
 
        

    # Now do Graceful Stuff!
    progress = QtGui.QProgressDialog("Creating Riivolution Patch with Graceful...", "Abort", 0, 120)
    progress.setWindowModality(QtCore.Qt.WindowModal)

    XML = []
    GracesPath = os.path.dirname(os.path.abspath(sys.argv[0])) + os.sep + "Resources" + os.sep + 'Wii' + os.sep
        
        
        
    # RootR Scripts
    args = ["mono", str(Graceful), "4", "2", str(RootR)]

    if os.name != 'posix':
        args = []
        command = [str(Graceful), "4", "2", str(RootR)]

    rootRbin = open('Graces/rootR.bin', 'wb')

    
    # Chat  
    Archive = Globals.configDataGracesFolders[1][:] # Chat_MS
    Archive.extend(Globals.configDataGracesFolders[2][:]) # Chat_SB
    ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.scs".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()
            

    # SysString
    Archive = (Globals.configDataGracesFolders[-1]) # SysString.bin
    ArchiveLocation = 'sys' + os.sep + 'ja' + os.sep
    args.extend(["{0}{1}.bin".format(GracesPath, Archive[0]), "{0}{1}.bin".format(ArchiveLocation, Archive[0])])
    tempFile = open("{0}{1}.bin".format(GracesPath, Archive[0]))
    tempData = tempFile.read()
    rootRbin.write(tempData)
    tempFile.close()


    # TOG stuff
    Archive = (['TOG_SS_ChatName', 'TOG_SS_StringECommerce']) # Special Cased Sys Subs
    ArchiveLocation = 'SysSub' + os.sep + 'JA' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.dat".format(GracesPath, file), "{0}{1}.dat".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.dat".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()


    # Movies
    Archive = (Globals.configDataGracesFolders[-2]) # Movie Subtitles
    ArchiveLocation = 'movie' + os.sep + 'str' + os.sep + 'ja' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.bin".format(GracesPath, file), "{0}{1}.bin".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.bin".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()

    progress.setValue(10)


    # Special Strings
    Archive = (Globals.configDataGracesFolders[-3]) # Special Stuff
    ArchiveLocation = 'str' + os.sep + 'ja' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.bin".format(str(GracesPath), file), "{0}{1}.bin".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.bin".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()


    # Images

    Images = [("Resources/TitleTexture.tex", "SysSub/JA/TitleTexture.tex"), 
                ("Resources/main.tex", "mnu/tex/main.tex"),
                ("Resources/shop.tex", "mnu/tex/shop.tex"),
                ("Resources/skill.tex", "mnu/tex/skill.tex"),
#                  ("Resources/snd_test.tex", "mnu/tex/snd_test.tex"),
                ("Resources/bin000.acf", "btl/acf/bin000.acf"),
                ("Resources/FontTexture2.tex", "sys/FontTexture2.tex"),
                ("Resources/FontBinary2.bin", "sys/FontBinary2.bin"),
                ("Resources/mainRR.sel", "module/mainRR.sel")
                ]

    for image in Images:
        args.extend([image[0], image[1]])
        tempFile = open(image[0], 'rb')
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()


    # Run the process!
    if os.name == 'posix':
        
        proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(57)
        rootRbin.close()

    else:
            
        for i in range(0, len(args), 20):
            if len(args) > i+20:
                finalArgs = command+(args[i:i+20])
            else:
                finalArgs = command+(args[i:])
                                    
            proc=subprocess.Popen(finalArgs,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        
            data = proc.stdout.read()
            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(57)
        rootRbin.close()
                        


    # Map0R Scripts
    Map0RCPK = ['mapfile_basiR.cpk', 'mapfile_briaR.cpk', 'mapfile_bridR.cpk', 'mapfile_caveR.cpk', 'mapfile_fallR.cpk', 'mapfile_ff12R.cpk', 'mapfile_ff13R.cpk', 'mapfile_ff14R.cpk', 'mapfile_ff15R.cpk', 'mapfile_ff16R.cpk', 'mapfile_ff17R.cpk', 'mapfile_ff19R.cpk', 'mapfile_ff20R.cpk', 'mapfile_foreR.cpk', 'mapfile_gentR.cpk', 'mapfile_icebR.cpk', 'mapfile_ironR.cpk', 'mapfile_koneR.cpk', 'mapfile_kotR.cpk', 'mapfile_lasR.cpk', 'mapfile_montR.cpk', 'mapfile_rockR.cpk', 'mapfile_sandR.cpk', 'mapfile_sf08R.cpk', 'mapfile_sf09R.cpk', 'mapfile_sf10R.cpk', 'mapfile_sf11R.cpk', 'mapfile_sf18R.cpk', 'mapfile_sneeR.cpk', 'mapfile_snowR.cpk', 'mapfile_stdaR.cpk', 'mapfile_varoR.cpk', 'mapfile_wf01R.cpk', 'mapfile_wf02R.cpk', 'mapfile_wf03R.cpk', 'mapfile_wf04R.cpk', 'mapfile_wf05R.cpk', 'mapfile_wf06R.cpk', 'mapfile_wf07R.cpk', 'mapfile_wf21R.cpk', 'mapfile_wincR.cpk', 'mapfile_zoneR.cpk']

    map0Rbin = open('Graces/map0R.bin', 'wb')


    i = 4

    for CPK in Map0RCPK:
        args = ["mono", str(Graceful), "4", "1", str(Map0R), CPK]
        if os.name != 'posix':
            args = [str(Graceful), "4", "1", str(Map0R), CPK]
            
        Archive = Globals.configDataGracesFolders[i]
        i += 1
        ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            map0Rbin.write(tempData)
            tempFile.close()


        # Run the process!
        proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(progress.value() + 1)

    map0Rbin.close()
        

    # Map1R Scripts
    Map1RCPK = ['mapfile_anmaR.cpk', 'mapfile_beraR.cpk', 'mapfile_debugR.cpk', 'mapfile_fendR.cpk', 'mapfile_kameR.cpk', 'mapfile_koya_r06R.cpk', 'mapfile_lakeR.cpk', 'mapfile_lanR.cpk', 'mapfile_nekoR.cpk', 'mapfile_olleR.cpk', 'mapfile_otheR.cpk', 'mapfile_ozweR.cpk', 'mapfile_riotR.cpk', 'mapfile_sablR.cpk', 'mapfile_shatR.cpk', 'mapfile_shipR.cpk', 'mapfile_strtR.cpk', 'mapfile_supaR.cpk', 'mapfile_systemR.cpk', 'mapfile_winR.cpk']


    map1Rbin = open('Graces/map1R.bin', 'wb')

    i = 46

    for CPK in Map1RCPK:
        args = ["mono", str(Graceful), "4", "1", str(Map1R), CPK]
        if os.name != 'posix':
            args = [str(Graceful), "4", "1", str(Map0R), CPK]
            
        Archive = Globals.configDataGracesFolders[i]
        i += 1
        ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            map1Rbin.write(tempData)
            tempFile.close()


        # Run the process!
        proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(progress.value() + 1)

    map1Rbin.close()


    # Let's make an XML! And also move all those .toc files over

    for Path in TestPath:
        for File in os.listdir(Path):
            if File.rfind('.toc') >= 0:
                try:
                    os.remove("Graces/v0/" + File)
                except:
                    pass
                shutil.move(Path + "/" + File, "Graces/v0")
            if File.rfind('.patch') >=0:
                try:
                    os.remove("Graces/v0/" + File)
                except:
                    pass
                shutil.move(Path + "/" + File, "Graces/v0")
                    
    #shutil.rmtree("Resources/Wii")


    XMLset = set(XML)
    XMLFinal = []
    for entry in XMLset:
        XMLFinal.append(entry)
        
    XMLFinal.sort()    
                
    xmlFile = open("riivolution/Graces.xml", "w")
        
        
        
    patchFile = open("Graces/v0/rootR.cpk.patch", "r")
    rootRPatch = patchFile.readline()
    patchFile.close()

    patchFile = open("Graces/v0/map0R.cpk.patch", "r")
    map0RPatch = patchFile.readline()
    patchFile.close()

    patchFile = open("Graces/v0/map1R.cpk.patch", "r")
    map1RPatch = patchFile.readline()
    patchFile.close()

                

    XMLString = [
        
    '<wiidisc version="1">\n',        
    '\t<id game="STG" version="0"/>\n',
    '\t<options>\n',
    '\t\t<section name="Testing">\n',
        
    '\t\t\t<option name="Graces Translation" default="1">\n',
    '\t\t\t\t<choice name="Enabled">\n',
    '\t\t\t\t\t<patch id="graces" />\n',
    '\t\t\t\t\t<patch id="gracesfiles" />\n',
    '\t\t\t\t</choice>\n',
    '\t\t\t</option>\n',

    '\t\t\t<option name="Bugfixes" default="1">\n',
    '\t\t\t\t<choice name="v2 Patch">\n',
    '\t\t\t\t\t<patch id="doll" />\n',
    '\t\t\t\t</choice>\n',
    '\t\t\t\t<choice name="Original">\n',
    '\t\t\t\t\t<patch id="localeZero" />\n',
    '\t\t\t\t</choice>\n',
    '\t\t\t</option>\n',
        
    '\t\t\t<option name="Debug Output">\n',
    '\t\t\t\t<choice name="For Original (v0)">\n',
    '\t\t\t\t\t<patch id="kamek_Ori" />\n',
    '\t\t\t\t</choice>\n',
    '\t\t\t</option>\n',
        
    '\t\t</section>\n',
    '\t</options>\n',
        
    '\t<patch id="doll" root="/Resources">\n',
    '\t\t<file disc="main.dol" external="main.dol" />\n',
	'\t\t<file disc="mainRR.sel" external="mainRR.sel" />\n'
    '\t\t<memory offset="0x803595DC" value="38600000" />\n',
    '\t</patch>\n',

    '\t<patch id="localeZero">\n',
    '\t\t<memory offset="0x803586DC" value="38600000" />\n',
    '\t</patch>\n',

    '\t<patch id="graces" root="/Graces/v0">\n',
    '\t\t<file disc="/rootR.cpk" external="rootR.cpk.patch" offset="{0}" resize="true" />\n'.format(rootRPatch),
    '\t\t<file disc="/map0R.cpk" external="map0R.cpk.patch" offset="{0}" resize="true" />\n'.format(map0RPatch),
    '\t\t<file disc="/map1R.cpk" external="map1R.cpk.patch" offset="{0}" resize="true" />\n'.format(map1RPatch),
    "".join(["\t\t%s\n" % (k) for k in XMLFinal[:63]]), #[:63]
    '\t</patch>\n',

    '\t<patch id="gracesfiles" root="/Graces">\n',
    '\t\t<file resize="false" offset="0x70000000" disc="map0R.cpk" external="map0R.bin" />\n',
	'\t\t<file resize="false" offset="0x70000000" disc="map1R.cpk" external="map1R.bin" />\n',
	'\t\t<file resize="false" offset="0x70000000" disc="rootR.cpk" external="rootR.bin" />\n',
    '\t</patch>\n',
        
    '\t<patch id="kamek_Ori">\n',
    '\t\t<memory offset="0x80035C10" value="4bfcbc2c" />\n',
    '\t\t<memory offset="0x80001800" value="9421fff07c0802a693e1000c7c7f1b783c60800090010014386318f04cc63182480343f1800100147fe3fb7883e1000c7c0803a6382100104e8000207c0802a69421ef8093e1107c900110849081101c90a1102090c1102490e110289101102c912110309141103440860024d8211038d8411040d8611048d8811050d8a11058d8c11060d8e11068d9011070380000013be10014980100083800000098010009380110887c641b7838a100089001000c7fe3fb7838011018900100104832e8457fe3fb78483258f9388000017c651b7838c000007fe3fb784832b5418001108483e1107c382110807c0803a64e8000206c6f6c0a00" />\n',
    '\t</patch>\n',
        
    '</wiidisc>'
        
    ]
        
    xmlFile.write("".join(["%s" % (k) for k in XMLString]))
    progress.setValue(progress.value() + 1)

    xmlFile.close()



def SavetoGracesfDemoXML(self):
    self.WriteDatabaseStorageToHdd()
        


    if os.name != 'posix':
        reply = QtGui.QMessageBox.information(self, "Incompatible OS", "Attention:\n\nThis feature is only compatible with posix style operating systems. Please use the distributed XML along with the 'save to patch' feature.")
        return        

    # Make some output directories
    if not os.path.exists('riivolution'):
        os.makedirs('riivolution')

    if not os.path.exists('Graces'):
        os.makedirs('Graces')

    if not os.path.exists('Graces/fDemo'):
        os.makedirs('Graces/fDemo')

    if not os.path.exists('Resources/fDemo'):
        os.makedirs('Resources/fDemo')


    if self.settings.contains('Graceful'):
        Graceful = self.settings.value('Graceful')
        if not os.path.isfile(Graceful):
            Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
            if Graceful == '': return
            Graceful = str(Graceful)
    else:
        Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
        if Graceful == '': return
        Graceful = str(Graceful)
    self.settings.setValue("Graceful", Graceful)

    if self.settings.contains('RootRToGf'):
        RootR = self.settings.value('RootRToGf')
        if not os.path.isfile(RootR):
            RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if RootR == '': return
            RootR = str(RootR)
    else:
        RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if RootR == '': return
        RootR = str(RootR)
    self.settings.setValue("RootRToGf", RootR)

    if self.settings.contains('Map0RToGf'):
        Map0R = self.settings.value('Map0RToGf')
        if not os.path.isfile(Map0R):
            Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map0R == '': return
            Map0R = str(Map0R)
    else:
        Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if Map0R == '': return
        Map0R = str(Map0R)
    self.settings.setValue("Map0RToGf", Map0R)

    if self.settings.contains('Map1RToGf'):
        Map1R = self.settings.value('Map1RToGf')
        if not os.path.isfile(Map1R):
            Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map1R == '': return
            Map1R = str(Map1R)
    else:
        Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate Tales of Graces f map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if Map1R == '': return
        Map1R = str(Map1R)
    self.settings.setValue("Map1RToGf", Map1R)

        
    #Delety function!
    TestPath = [os.path.dirname(str(RootR)), os.path.dirname(str(Map0R)), os.path.dirname(str(Map1R))]
        
    for Path in TestPath:
        for File in os.listdir(Path):
            if File.rfind('.toc') >= 0:
                os.remove(Path + "/" + File)
                print "Removed: {0}".format(Path + "/" + File)
            if File.rfind('.patch') >=0:
                os.remove(Path + '/' + File)
                print "Removed: {0}".format(Path + "/" + File)


    # Everyone loves progress bars!
    progress = QtGui.QProgressDialog("Saving databases to SCS...", "Abort", 0, 16)
    progress.setWindowModality(QtCore.Qt.WindowModal)


    # Create the .scs files
    self.MakeSCS(['ActInfo-f', 'CharName-f', 'CHT_PR001-f', 'CHT_PR002-f', 'CHT_PR003-f', 'CHT_PR005-f', 'CHT_PR007-f', 'e950_020-f', 'MapName-f', 'Navigation-f', 'sofi_d02-f', 'sysm_d01-f', 'SysString-f', 'TOG_SS_ChatName-f', 'TOG_SS_StringECommerce-f'], progress, 'fDemo')

    progress.setValue(16)
 
        

    # Now do Graceful Stuff!
    progress = QtGui.QProgressDialog("Creating Riivolution Patch with Graceful...", "Abort", 0, 120)
    progress.setWindowModality(QtCore.Qt.WindowModal)

    XML = []
    GracesPath = os.path.dirname(os.path.abspath(sys.argv[0])) + os.sep + "Resources" + os.sep + "fDemo" + os.sep
        
        
    # Rename those scs files properly!
    for item in ['CHT_PR001-f', 'CHT_PR002-f', 'CHT_PR003-f', 'CHT_PR005-f', 'CHT_PR007-f', 'e950_020-f', 'sofi_d02-f', 'sysm_d01-f', 'TOG_SS_ChatName-f', 'TOG_SS_StringECommerce-f']:

        shutil.copyfile("{0}{1}.scs".format(GracesPath, item), "{0}{1}.scs".format(GracesPath, item[:-2]))

    for item in ['ActInfo-f', 'CharName-f', 'MapName-f', 'Navigation-f', 'SysString-f']:

        shutil.copyfile("{0}{1}.scs".format(GracesPath, item), "{0}{1}.bin".format(GracesPath, item[:-2]))

        
        
    # RootR Scripts
    args = ["mono", str(Graceful), "4", "2", str(RootR)]

    rootRbin = open('Graces/fDemo/rootR.bin', 'wb')

    off = 0

    # Chat  
    Archive = ['CHT_PR001', 'CHT_PR002', 'CHT_PR003', 'CHT_PR005', 'CHT_PR007'] # Chat_MS
    ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.scs".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()
            
            
    # SysString        
    ArchiveLocation = 'Sys' + os.sep + 'ja' + os.sep
    args.extend(["{0}{1}.bin".format(GracesPath, 'SysString'), "{0}{1}.bin".format(ArchiveLocation, 'SysString')])
    tempFile = open("{0}{1}.bin".format(GracesPath, 'SysString'))
    tempData = tempFile.read()
    rootRbin.write(tempData)
    tempFile.close()


    progress.setValue(10)


    # Special Strings
    Archive = (['ActInfo', 'Navigation', 'CharName']) # Special Stuff ---  'MapName', 
    ArchiveLocation = 'Str' + os.sep + 'ja' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.bin".format(str(GracesPath), file), "{0}{1}.bin".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.bin".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()


    # Images

    Images = [("Resources/fDemo/TOG_SS_ChatName.scs", "SysSub/JA/TOG_SS_ChatName.dat"),
                ("Resources/FResources/TitleTexture.tex", "SysSub/JA/TitleTexture.tex"), 
                ("Resources/FResources/skill.tex", "mnu/tex/skill.tex"),
                ("Resources/FResources/main.tex", "mnu/tex/main.tex"),
                ("Resources/FResources/bin000.acf", "btl/acf/bin000.acf"),
                ("Resources/FResources/MapName.bin", "Str/ja/MapName.bin"),
                ("Resources/FResources/FontTexture2.tex", "Sys/FontTexture2.tex"),
                ("Resources/FResources/FontBinary2.bin", "Sys/FontBinary2.bin"),
                ("Resources/FResources/TrialHelp.slz", "Sys/Trial/TrialHelp.slz")
                ]

    for image in Images:
        args.extend([image[0], image[1]])
        tempFile = open(image[0], 'rb')
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()

    # Run the process!
    print args
    proc=subprocess.Popen(args,shell=False,bufsize=-1,stdin=subprocess.PIPE,stdout=subprocess.PIPE)

    data = proc.stdout.read()
    XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
    progress.setValue(57)
    rootRbin.close()


    # Map0R Scripts
    Map0RCPK = ['mapfile_elemR.cpk', 'mapfile_sofiR.cpk']

    map0Rbin = open('Graces/fDemo/map0R.bin', 'wb')

    scsList = [['e950_020'], ['sofi_d02']] 


    i = 0

    for CPK in Map0RCPK:
        args = ["mono", str(Graceful), "4", "1", str(Map0R), CPK]
        if os.name != 'posix':
            args = [str(Graceful), "4", "1", str(Map0R), CPK]
            
        Archive = scsList[i]
        i += 1
        ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            map0Rbin.write(tempData)
            tempFile.close()


        # Run the process!
        proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(progress.value() + 1)

    map0Rbin.close()
        

    # Map1R Scripts
    Map1RCPK = 'mapfile_systemR.cpk'

    map1Rbin = open('Graces/fDemo/map1R.bin', 'wb')

    args = ["mono", str(Graceful), "4", "1", str(Map1R), Map1RCPK]
    if os.name != 'posix':
        args = [str(Graceful), "4", "1", str(Map0R), CPK]
        
    file = 'sysm_d01'
    ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

    args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

    tempFile = open("{0}{1}.scs".format(GracesPath, file))
    tempData = tempFile.read()
    map1Rbin.write(tempData)
    tempFile.close()


    # Run the process!
    proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)

    data = proc.stdout.read()
    XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
    progress.setValue(progress.value() + 1)

    map1Rbin.close()


    # Let's make an XML! And also move all those .toc files over

    for Path in TestPath:
        for File in os.listdir(Path):
            if File.rfind('.toc') >= 0:
                try:
                    os.remove("Graces/fDemo/" + File)
                except:
                    pass
                shutil.move(Path + "/" + File, "Graces/fDemo")
            if File.rfind('.patch') >=0:
                try:
                    os.remove("Graces/fDemo/" + File)
                except:
                    pass
                shutil.move(Path + "/" + File, "Graces/fDemo")
                    
    shutil.copy("Resources/FResources/PARAM.SFO", "Graces/fDemo/PARAM.SFO")
    shutil.copy("Resources/FResources/PIC1.png", "Graces/fDemo/PIC1.PNG")
    shutil.copy("Resources/FResources/ICON0.png", "Graces/fDemo/ICON0.PNG")
    shutil.copy("Resources/FResources/BootLogo.slz", "Graces/fDemo/BootLogo.slz")

    XMLset = set(XML)
    XMLFinal = []
    for entry in XMLset:
        XMLFinal.append(entry)
        
    XMLFinal.sort()    
                
        
    xmlFile = open("riivolution/GracesfDemo.xml", "w")
        
        
        
    patchFile = open("Graces/fDemo/rootR.cpk.patch", "r")
    rootRPatch = patchFile.readline()
    patchFile.close()

    patchFile = open("Graces/fDemo/map0R.cpk.patch", "r")
    map0RPatch = patchFile.readline()
    patchFile.close()

    patchFile = open("Graces/fDemo/map1R.cpk.patch", "r")
    map1RPatch = patchFile.readline()
    patchFile.close()

    for thing in XMLFinal: print thing                
    XMLString = [
        
    '<ps3disc version="1" gameroot="/dev_hdd0/game/NPJB90302/USRDIR">\n',        
    '\t<options>\n',
    '\t\t<section name="Testing">\n',
        
    '\t\t\t<option name="Graces f Demo Translation" default="1">\n',
    '\t\t\t\t<choice name="Enabled">\n',
    '\t\t\t\t\t<patch id="graces" />\n',
    '\t\t\t\t\t<patch id="gracesfiles" />\n',
    '\t\t\t\t</choice>\n',
    '\t\t\t</option>\n',
        
    '\t\t</section>\n',
    '\t</options>\n',
        
    '\t<patch id="graces" root="Graces/fDemo">\n',
    '\t\t<file disc="Logo/BootLogo.slz" external="BootLogo.slz" resize="true" />\n',
    '\t\t<file disc="/PARAM.SFO" external="PARAM.SFO" resize="true" />\n',
    '\t\t<file disc="/PIC1.PNG" external="PIC1.PNG" resize="true" />\n',
    '\t\t<file disc="/ICON0.PNG" external="ICON0.PNG" resize="true" />\n',
    '\t\t<file disc="rootR.cpk" external="rootR.cpk.patch" offset="{0}" resize="true" />\n'.format(rootRPatch),
    '\t\t<file disc="map0R.cpk" external="map0R.cpk.patch" offset="{0}" resize="true" />\n'.format(map0RPatch),
    '\t\t<file disc="map1R.cpk" external="map1R.cpk.patch" offset="{0}" resize="true" />\n'.format(map1RPatch),
    "".join(["\t\t%s\n" % (k) for k in [XMLFinal[0], XMLFinal[1], XMLFinal[2], XMLFinal[4]]]), #[:0,1,2,4]
    '\t</patch>\n',

    '\t<patch id="gracesfiles" root="Graces/fDemo">\n',
    '\t\t<file resize="false" offset="0x02253A60" disc="map0R.cpk" external="map0R.bin" />\n',
	'\t\t<file resize="false" offset="0x002211E0" disc="map1R.cpk" external="map1R.bin" />\n',
	'\t\t<file resize="false" offset="0x07593CA0" disc="rootR.cpk" external="rootR.bin" />\n',
    '\t</patch>\n',
        
    '</ps3disc>'
        
    ]
        
    xmlFile.write("".join(["%s" % (k) for k in XMLString]))

    xmlFile.close()


    if os.name == 'posix':
        
        try:
            args = ['mono', 'PatchDolStrings.exe', 'Resources/elfpatchconfig.xml']
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            
            data = proc.stdout.read()
            print data

            reply = QtGui.QMessageBox.information(self, "Complete", "Embedded Strings Patch Complete.")
                
        except:
            reply = QtGui.QMessageBox.information(self, "Error", "There was an error during patching. You must have mono installed to patch, and have the PatchDolStrings.exe and it's two .dlls in the GraceNote folder.")
            return        
        
        
    else:
        
        try:
            args = ['PatchDolStrings.exe', 'Resources\elfpatchconfig.xml']
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            
            data = proc.stdout.read()
            print data
                
            reply = QtGui.QMessageBox.information(self, "Complete", "Embedded Strings Patch Complete.")

        except:
            reply = QtGui.QMessageBox.information(self, "Error", "There was an error during patching. I have no idea what went wrong.")
            return        


    progress.setValue(progress.value() + 1)


def PatchDol(self):
    self.WriteDatabaseStorageToHdd()
        
    
    # Make some output directories
    if not os.path.exists('riivolution'):
        os.makedirs('riivolution')

    GracesPath = os.path.dirname(os.path.abspath(sys.argv[0]))

    if os.name == 'posix':
        
        try:
            args = ['mono', 'PatchDolStrings.exe', 'Resources/dolpatchconfig.xml']
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            
            data = proc.stdout.read()
            print data

            reply = QtGui.QMessageBox.information(self, "Complete", "Embedded Strings Patch Complete.")
                
        except:
            reply = QtGui.QMessageBox.information(self, "Error", "There was an error during patching. You must have mono installed to patch, and have the PatchDolStrings.exe and it's two .dlls in the GraceNote folder.")
            return        
        
        
    else:
        
        try:
            args = ['PatchDolStrings.exe', 'Resources\dolpatchconfig.xml']
            proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            
            data = proc.stdout.read()
            print data
                
            reply = QtGui.QMessageBox.information(self, "Complete", "Embedded Strings Patch Complete.")

        except:
            reply = QtGui.QMessageBox.information(self, "Error", "There was an error during patching. I have no idea what went wrong.")
            return        
        
    
    
#
#        # Make some output directories
#        if not os.path.exists('riivolution'):
#            os.makedirs('riivolution')
#
#
#        if self.settings.contains('MemOne'):
#            MemOne = self.settings.value('MemOne')
#            if not os.path.isfile(MemOne):
#                MemOne = QtGui.QFileDialog.getOpenFileName(self, 'Locate the Tales of Graces v2 MemDump', '', 'Wii Mem One dump (*.bin);;All Files(*)')
#                if MemOne == '': return
#                MemOne = str(MemOne)
#        else:
#            MemOne = QtGui.QFileDialog.getOpenFileName(self, 'Locate the Tales of Graces v2 MemDump', '', 'Wii Mem One Dump (*.bin);;All Files(*)')
#            if MemOne == '': return
#            MemOne = str(MemOne)
#        self.settings.setValue("MemOne", MemOne)
#
#
#
#        file = open(MemOne, 'rb')
#        data = file.read()
#        file.close()
#        
#        lowrange = 0x804CE000 # Start of data section in dol in memory
#        highrange = 0x8072E000 # End of data section in dol in memory
#        
#        print "Reading file {0} looking for pointers between {1} and {2}".format(MemOne, hex(lowrange), hex(highrange))
#        
#        PointedAreas = dict([])
#        
#        loops = len(data) / 4
#
#        for integer in xrange(loops):
#        
#            offset = integer*4
#            pointer = struct.unpack_from('>I', data, offset)[0]
#            
#            if lowrange < pointer and pointer < highrange:
#                if pointer in PointedAreas:
#                    PointedAreas[pointer].append(offset)
#                else:
#                    PointedAreas[pointer] = [offset]
#
#        		
#        print 'Found {0} pointers'.format(len(PointedAreas))
#
#
#
#        dolNames = ['Artes', 'ArteNames', 'Battle', 'Discovery', 'GradeShop-Missions', 'Item', 'MonsterBook', 'Skills', 'System', 'Tactics', 'Titles', 'Tutorial']
#
#
#        file = open('riivolution/DolPatches.xml', 'w')
#
#        XMLString = [
#        '<wiidisc version="1">\n',        
#        '\t<id game="STG" />\n',
#        '\t<options>\n',
#        '\t\t<section name="Embedded Strings">\n',
#        '\t\t\t<option name="Graces Translation" default="1">\n',
#        '\t\t\t\t<choice name="Enabled">\n',
#        '\t\t\t\t\t<patch id="dolstrings" />\n',
#        '\t\t\t\t</choice>\n',
#        '\t\t\t</option>\n',
#        '\t\t</section>\n',
#        '\t</options>\n',
#        
#        '\t<patch id="dolstrings">\n',
#        '\t\t<memory offset="0x802F89C4" value="494f763c" />\n',
#        '\t\t<memory offset="0x802F89E4" value="494f761c" />\n',
#        '\t\t<memory offset="0x817F0000" value="3d20817f380900007f8300404dbc00207c0303784e80002000000000" />\n'
#
#        ]
#        
#        file.write("".join(["%s" % (k) for k in XMLString]))
#
#        targetOffset = 0x817F0100
#
#        for pointer, offsetlist in PointedAreas.iteritems():
#                        
#            # Reset the variables for the loop
#            NextChar = True
#            i = 0
#            stringBuffer = ''
#            string = ''
#            
#            # Parse a C-string of unknown length
#            while NextChar == True:
#                char = data[pointer - 0x80000000 + i]
#                
#                if char == '\x00':
#                    NextChar = False
#                    
#                else:
#                    stringBuffer += char
#                
#                i += 1    
#                    
#                    
#            # Convert string buffer to text I can use
#            string = stringBuffer.decode('cp932', 'ignore')
#            
#            # Check to see if such a Japanese string exists
#            Globals.CursorGracesJapanese.execute(u"select ID from Japanese where string=?", (unicode(string),))
#            results = Globals.CursorGracesJapanese.fetchall()
##            
#            
#            
#            # Check to see if the JP string has an English equivalent
#            
#            maxlen = 4 - (len(stringBuffer) % 4) + len(stringBuffer)
#            
#            if results == []:
#                pass
##                print 'No JP string'
#            else:
#                for entry in results:
#                    for DBName in dolNames:
#                        TmpCon = sqlite3.connect(Globals.configData.LocalDatabasePath + '/' + DBName)
#                        TmpCur = TmpCon.cursor()    
#                        
#                        TmpCur.execute(u"select english from Text where StringID=?", (unicode(entry[0]),))
#                        
#                        thing = TmpCur.fetchall()
#                        if thing == [] or thing == [(u'',)] or thing == [(u' ',)]:
#                            continue
#                        else:
#                            thinglen = len(thing[0][0].encode('cp932', 'ignore'))
#                            if thinglen > maxlen:
#
##       The commented code here will be used when Aaron has put aside some memory 
##       for these strings. Just set the beginning of the target memory range at 
##       targetOffset above, and off it goes! It will increment and pad the patches 
##       according, and use a memory search to modify any pointers.
#
#                                blank = thinglen % 8
#                                if blank == 0:
#                                    blank = 8
#                                print 'String is longer than {0} by {1}. Being moved to unallocated memory'.format(maxlen, thinglen-maxlen)
#
#                                for offset in offsetlist:
#                                    
#                                    pA = '\t\t<memory offset="{0}" value="{1}" />\n'.format(hex(offset), hex(targetOffset)[2:])
#                                    file.write(pA)
#
#                                pB = '\t\t<memory offset="{0}" value="{1}" />\n'.format(hex(targetOffset), hexlify(re.sub(u"'+", "'", unicode(thing[0][0])).encode('cp932', 'ignore')) + (blank * '00'))
#                                
#                                file.write(pB)
#                                
#                                targetOffset += 4 - (thinglen % 4) + thinglen
#
#                            else:
#                                blank = maxlen - thinglen
#                                pC = '\t\t<memory offset="{0}" value="{1}" />\n'.format(hex(pointer), hexlify(re.sub(u"'+", "'", unicode(thing[0][0])).encode('cp932', 'ignore')) + (blank * '00'))
#            
#                                file.write(pC)
#                                
#        file.write('\t</patch>\n')
#        file.write('</wiidisc>')
#        file.close()
   

def SavetoBugfixXML(self):
    self.WriteDatabaseStorageToHdd()
        


    # Make some output directories
    if not os.path.exists('riivolution'):
        os.makedirs('riivolution')

    if not os.path.exists('Graces'):
        os.makedirs('Graces')

    if not os.path.exists('Graces/v2'):
        os.makedirs('Graces/v2')

    if not os.path.exists('Resources/Wii'):
        os.makedirs('Resources/Wii')


    if self.settings.contains('Graceful'):
        Graceful = self.settings.value('Graceful')
        if not os.path.isfile(Graceful):
            Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
            if Graceful == '': return
            Graceful = str(Graceful)
    else:
        Graceful = QtGui.QFileDialog.getOpenFileName(self, 'Locate Graceful', '', 'All Files(*)')
        if Graceful == '': return
        Graceful = str(Graceful)
    self.settings.setValue("Graceful", Graceful)

    if self.settings.contains('RootRfix'):
        RootR = self.settings.value('RootRfix')
        if not os.path.isfile(RootR):
            RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if RootR == '': return
            RootR = str(RootR)
    else:
        RootR = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix rootR.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if RootR == '': return
        RootR = str(RootR)
    self.settings.setValue("RootRfix", RootR)

    if self.settings.contains('Map0Rfix'):
        Map0R = self.settings.value('Map0Rfix')
        if not os.path.isfile(Map0R):
            Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map0R == '': return
            Map0R = str(Map0R)
    else:
        Map0R = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix map0R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if Map0R == '': return
        Map0R = str(Map0R)
    self.settings.setValue("Map0Rfix", Map0R)

    if self.settings.contains('Map1Rfix'):
        Map1R = self.settings.value('Map1Rfix')
        if not os.path.isfile(Map1R):
            Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
            if Map1R == '': return
            Map1R = str(Map1R)
    else:
        Map1R = QtGui.QFileDialog.getOpenFileName(self, 'Locate bugfix map1R.cpk', '', 'CRIWARE Packed Archive (*.cpk);;All Files(*)')
        if Map1R == '': return
        Map1R = str(Map1R)
    self.settings.setValue("Map1Rfix", Map1R)

        
    #Delety function!
    TestPath = [os.path.dirname(str(RootR)), os.path.dirname(str(Map0R)), os.path.dirname(str(Map1R))]
        
    for Path in TestPath:
        for File in os.listdir(Path):
            if File.rfind('.toc') >= 0:
                os.remove(Path + "/" + File)
            if File.rfind('.patch') >=0:
                os.remove(Path + '/' + File)


    # Everyone loves progress bars!
    progress = QtGui.QProgressDialog("Saving databases to SCS...", "Abort", 0, len(os.listdir(Globals.configData.LocalDatabasePath))+1)
    progress.setWindowModality(QtCore.Qt.WindowModal)


    # Create the .scs files
    self.MakeSCS(os.listdir(Globals.configData.LocalDatabasePath), progress, 'Wii')

    progress.setValue(len(os.listdir(Globals.configData.LocalDatabasePath))+1)
 
        

    # Now do Graceful Stuff!
    progress = QtGui.QProgressDialog("Creating Riivolution Patch with Graceful...", "Abort", 0, 120)
    progress.setWindowModality(QtCore.Qt.WindowModal)

    XML = []
    GracesPath = os.path.dirname(os.path.abspath(sys.argv[0])) + os.sep + "Resources" + os.sep + 'Wii' + os.sep
        
        
        
    # RootR Scripts
    args = ["mono", str(Graceful), "4", "2", str(RootR)]

    if os.name != 'posix':
        args = []
        command = [str(Graceful), "4", "2", str(RootR)]

    rootRbin = open('Graces/rootR.bin', 'wb')

    off = 0

    # Chat  
    Archive = Globals.configDataGracesFolders[1][:] # Chat_MS
    Archive.extend(Globals.configDataGracesFolders[2][:]) # Chat_SB
    ArchiveLocation = 'chat' + os.sep + 'scs' + os.sep + 'JA' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.scs".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()
            
            
    # SysString        
    Archive = (Globals.configDataGracesFolders[-1]) # SysString.bin
    ArchiveLocation = 'sys' + os.sep + 'ja' + os.sep
    args.extend(["{0}{1}.bin".format(GracesPath, Archive[0]), "{0}{1}.bin".format(ArchiveLocation, Archive[0])])
    tempFile = open("{0}{1}.bin".format(GracesPath, Archive[0]))
    tempData = tempFile.read()
    rootRbin.write(tempData)
    tempFile.close()


    # TOG stuff
    Archive = (['TOG_SS_ChatName', 'TOG_SS_StringECommerce']) # Special Cased Sys Subs
    ArchiveLocation = 'SysSub' + os.sep + 'JA' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.dat".format(GracesPath, file), "{0}{1}.dat".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.dat".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()
                    
        
    # Movies
    Archive = (Globals.configDataGracesFolders[-2]) # Movie Subtitles
    ArchiveLocation = 'movie' + os.sep + 'str' + os.sep + 'ja' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.bin".format(GracesPath, file), "{0}{1}.bin".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.bin".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()

    progress.setValue(10)


    # Special Strings
    Archive = (Globals.configDataGracesFolders[-3]) # Special Stuff
    ArchiveLocation = 'str' + os.sep + 'ja' + os.sep

    for file in Archive:
        args.extend(["{0}{1}.bin".format(str(GracesPath), file), "{0}{1}.bin".format(ArchiveLocation, file)])
        tempFile = open("{0}{1}.bin".format(GracesPath, file))
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()


    # Images
    Images = [("Resources/TitleTexture.tex", "SysSub/JA/TitleTexture.tex"), 
                ("Resources/main.tex", "mnu/tex/main.tex"),
                ("Resources/shop.tex", "mnu/tex/shop.tex"),
                ("Resources/skill.tex", "mnu/tex/skill.tex"),
#                  ("Resources/snd_test.tex", "mnu/tex/snd_test.tex"),
                ("Resources/bin000.acf", "btl/acf/bin000.acf"),
                ("Resources/FontTexture2.tex", "sys/FontTexture2.tex"),
                ("Resources/FontBinary2.bin", "sys/FontBinary2.bin"),
                ("Resources/mainRR.sel", "module/mainRR.sel")
                ]

    for image in Images:
        args.extend([image[0], image[1]])
        tempFile = open(image[0], 'rb')
        tempData = tempFile.read()
        rootRbin.write(tempData)
        tempFile.close()

    # Run the process!
    if os.name == 'posix':
        
        proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(57)
        rootRbin.close()

    else:
        for i in range(0, len(args), 20):
            if len(args) > i+20:
                finalArgs = command + args[i:i+20]
            else:
                finalArgs = command + args[i:]
                
                
            proc=subprocess.Popen(finalArgs,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)

            while proc.poll() == None:
                pass
                
            data = proc.stdout.read()

            XML.extend(re.findall(u'<.*?>', data, re.DOTALL))

        progress.setValue(57)
        rootRbin.close()


    # Map0R Scripts
    Map0RCPK = ['mapfile_basiR.cpk', 'mapfile_briaR.cpk', 'mapfile_bridR.cpk', 'mapfile_caveR.cpk', 'mapfile_fallR.cpk', 'mapfile_ff12R.cpk', 'mapfile_ff13R.cpk', 'mapfile_ff14R.cpk', 'mapfile_ff15R.cpk', 'mapfile_ff16R.cpk', 'mapfile_ff17R.cpk', 'mapfile_ff19R.cpk', 'mapfile_ff20R.cpk', 'mapfile_foreR.cpk', 'mapfile_gentR.cpk', 'mapfile_icebR.cpk', 'mapfile_ironR.cpk', 'mapfile_koneR.cpk', 'mapfile_kotR.cpk', 'mapfile_lasR.cpk', 'mapfile_montR.cpk', 'mapfile_rockR.cpk', 'mapfile_sandR.cpk', 'mapfile_sf08R.cpk', 'mapfile_sf09R.cpk', 'mapfile_sf10R.cpk', 'mapfile_sf11R.cpk', 'mapfile_sf18R.cpk', 'mapfile_sneeR.cpk', 'mapfile_snowR.cpk', 'mapfile_stdaR.cpk', 'mapfile_varoR.cpk', 'mapfile_wf01R.cpk', 'mapfile_wf02R.cpk', 'mapfile_wf03R.cpk', 'mapfile_wf04R.cpk', 'mapfile_wf05R.cpk', 'mapfile_wf06R.cpk', 'mapfile_wf07R.cpk', 'mapfile_wf21R.cpk', 'mapfile_wincR.cpk', 'mapfile_zoneR.cpk']

    map0Rbin = open('Graces/map0R.bin', 'wb')


    i = 4

    for CPK in Map0RCPK:
        args = ["mono", str(Graceful), "4", "1", str(Map0R), CPK]
        if os.name != 'posix':
            args = [str(Graceful), "4", "1", str(Map0R), CPK]
            
        Archive = Globals.configDataGracesFolders[i]
        i += 1
        ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            map0Rbin.write(tempData)
            tempFile.close()


        # Run the process!
        proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(progress.value() + 1)

    map0Rbin.close()
        

    # Map1R Scripts
    Map1RCPK = ['mapfile_anmaR.cpk', 'mapfile_beraR.cpk', 'mapfile_debugR.cpk', 'mapfile_fendR.cpk', 'mapfile_kameR.cpk', 'mapfile_koya_r06R.cpk', 'mapfile_lakeR.cpk', 'mapfile_lanR.cpk', 'mapfile_nekoR.cpk', 'mapfile_olleR.cpk', 'mapfile_otheR.cpk', 'mapfile_ozweR.cpk', 'mapfile_riotR.cpk', 'mapfile_sablR.cpk', 'mapfile_shatR.cpk', 'mapfile_shipR.cpk', 'mapfile_strtR.cpk', 'mapfile_supaR.cpk', 'mapfile_systemR.cpk', 'mapfile_winR.cpk']


    map1Rbin = open('Graces/map1R.bin', 'wb')

    i = 46

    for CPK in Map1RCPK:
        args = ["mono", str(Graceful), "4", "1", str(Map1R), CPK]
        if os.name != 'posix':
            args = [str(Graceful), "4", "1", str(Map1R), CPK]
            
        Archive = Globals.configDataGracesFolders[i]
        i += 1
        ArchiveLocation = 'map' + os.sep + 'sce' + os.sep + 'R' + os.sep + 'ja' + os.sep

        for file in Archive:
            args.extend(["{0}{1}.scs".format(GracesPath, file), "{0}{1}.scs".format(ArchiveLocation, file)])

            tempFile = open("{0}{1}.scs".format(GracesPath, file))
            tempData = tempFile.read()
            map1Rbin.write(tempData)
            tempFile.close()


        # Run the process!
        proc=subprocess.Popen(args,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    
        data = proc.stdout.read()
        XML.extend(re.findall(u'<.*?>', data, re.DOTALL))
        progress.setValue(progress.value() + 1)

    map1Rbin.close()


    # Let's make an XML! And also move all those .toc files over

    for Path in TestPath:
        for File in os.listdir(Path):
            if File.rfind('.toc') >= 0:
                try:
                    os.remove("Graces/v2/" + File)
                except:
                    pass
                shutil.move(Path + "/" + File, "Graces/v2")
            if File.rfind('.patch') >=0:
                try:
                    os.remove("Graces/v2/" + File)
                except:
                    pass
                shutil.move(Path + "/" + File, "Graces/v2")
                    
    #shutil.rmtree('Resources/Wii')
        

    XMLset = set(XML)
    XMLFinal = []
    for entry in XMLset:
        XMLFinal.append(entry)
        
    XMLFinal.sort()    
                
        
    xmlFile = open("riivolution/GracesBugfix.xml", "w")
        
        
        
    patchFile = open("Graces/v2/rootR.cpk.patch", "r")
    rootRPatch = patchFile.readline()
    patchFile.close()

    patchFile = open("Graces/v2/map0R.cpk.patch", "r")
    map0RPatch = patchFile.readline()
    patchFile.close()

    patchFile = open("Graces/v2/map1R.cpk.patch", "r")
    map1RPatch = patchFile.readline()
    patchFile.close()

                
    XMLString = [
        
    '<wiidisc version="1">\n',        
    '\t<id game="STG" version="2"/>\n',
    '\t<options>\n',
    '\t\t<section name="Testing">\n',
        
    '\t\t\t<option name="Graces Translation" default="1">\n',
    '\t\t\t\t<choice name="Enabled">\n',
    '\t\t\t\t\t<patch id="graces" />\n',
    '\t\t\t\t\t<patch id="gracesfiles" />\n',
    '\t\t\t\t</choice>\n',
    '\t\t\t</option>\n',

    '\t\t\t<option name="Region Patch" default="1">\n',
    '\t\t\t\t<choice name="Enabled">\n',
    '\t\t\t\t\t<patch id="localeZero" />\n',
    '\t\t\t\t</choice>\n',
    '\t\t\t</option>\n',
        
    '\t\t\t<option name="Debug Output">\n',
    '\t\t\t\t<choice name="For Original (v0)">\n',
    '\t\t\t\t\t<patch id="kamek_Ori" />\n',
    '\t\t\t\t</choice>\n',
    '\t\t\t</option>\n',
        
    '\t\t</section>\n',
    '\t</options>\n',
        
    '\t<patch id="localeZero">\n',
    '\t\t<memory offset="0x803595DC" value="38600000" />\n',
    '\t</patch>\n',

    '\t<patch id="graces" root="/Graces/v2">\n',
    '\t\t<file disc="/rootR.cpk" external="rootR.cpk.patch" offset="{0}" resize="true" />\n'.format(rootRPatch),
    '\t\t<file disc="/map0R.cpk" external="map0R.cpk.patch" offset="{0}" resize="true" />\n'.format(map0RPatch),
    '\t\t<file disc="/map1R.cpk" external="map1R.cpk.patch" offset="{0}" resize="true" />\n'.format(map1RPatch),
    "".join(["\t\t%s\n" % (k) for k in XMLFinal[:63]]), #[:63]
    '\t</patch>\n',

    '\t<patch id="gracesfiles" root="/Graces">\n',
    '\t\t<file resize="false" offset="0x70000000" disc="map0R.cpk" external="map0R.bin" />\n',
	'\t\t<file resize="false" offset="0x70000000" disc="map1R.cpk" external="map1R.bin" />\n',
	'\t\t<file resize="false" offset="0x70000000" disc="rootR.cpk" external="rootR.bin" />\n',
    '\t</patch>\n',
        
    '\t<patch id="kamek_New">\n',
    '\t\t<memory offset="0x80035C10" value="4bfcbc2c" />\n',
    '\t\t<memory offset="0x80001800" value="9421fff07c0802a693e1000c7c7f1b783c60800090010014386318f04cc63182480343f1800100147fe3fb7883e1000c7c0803a6382100104e8000207c0802a69421ef8093e1107c900110849081101c90a1102090c1102490e110289101102c912110309141103440860024d8211038d8411040d8611048d8811050d8a11058d8c11060d8e11068d9011070380000013be10014980100083800000098010009380110887c641b7838a100089001000c7fe3fb7838011018900100104832e8457fe3fb78483258f9388000017c651b7838c000007fe3fb784832b5418001108483e1107c382110807c0803a64e8000206c6f6c0a00" />\n',
    '\t</patch>\n',
        
    '</wiidisc>'
        
    ]
        
    xmlFile.write("".join(["%s" % (k) for k in XMLString]))
    progress.setValue(progress.value() + 1)

    xmlFile.close()



