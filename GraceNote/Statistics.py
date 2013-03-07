
class Statistics(QtGui.QDialog):

    def __init__(self):
        super(Statistics, self).__init__()

        self.setWindowModality(False)        
        layout = QtGui.QVBoxLayout()
        
        
        self.setMinimumSize(400, 600)
        self.setMaximumWidth(400)
        
        Globals.LogCur.execute("SELECT * FROM Log")
        LogList = Globals.LogCur.fetchall()
        
        # Today Stats
        TodayGroup = QtGui.QGroupBox()
        layout.addWidget(TodayGroup)
        
        TodayGroup.setTitle('Today:')   
        TodayLay = QtGui.QVBoxLayout()
        TodayGroup.setLayout(TodayLay)
        TodayList = set()
        TodaySet = set()
        today = time.strftime('%m/%d', time.localtime(time.time()))
        for entry in LogList:
            if time.strftime('%m/%d', time.localtime(entry[3])) == today:
                TodaySet.add(entry[2])
                for x in entry[1].split(','):
                    TodayList.add((x, entry[2]))

        if TodaySet == set([]):
            TodayLay.addWidget(QtGui.QLabel("Nobody's done anything today =("))
        else:
            for name in TodaySet:
                string = ''
                i = 0
                for entry in TodayList:
                    if entry[1] == name:
                        string = string + entry[0] + ', '
                        i+=1 
                label = QtGui.QLabel('{0}: {1} files translated'.format(name, i))
                TodayLay.addWidget(label)
                label = QtGui.QLabel(string[:-2] + '\n')
                label.setWordWrap(True)
                font = label.font()
                font.setPointSize(10)
                font.setItalic(True)
                label.setFont(font)
                TodayLay.addWidget(label)


        # Yesterday Stats
        YesterdayGroup = QtGui.QGroupBox()
        layout.addWidget(YesterdayGroup)
        
        YesterdayGroup.setTitle('Yesterday:')   
        YesterdayLay = QtGui.QVBoxLayout()
        YesterdayGroup.setLayout(YesterdayLay)
        YesterdayList = set()
        YesterdaySet = set()
        
        yesterday = '{0}/{1}'.format(time.strftime('%m', time.localtime(time.time())), str(int(time.strftime('%d', time.localtime(time.time())))-1).zfill(2))
                
        for entry in LogList:
            if time.strftime('%m/%d', time.localtime(entry[3])) == yesterday:
                YesterdaySet.add(entry[2])
                for x in entry[1].split(','):
                    YesterdayList.add((x, entry[2]))

        if YesterdaySet == ():
            YesterdayLay.addWidget(QtGui.QLabel("Nobody did anything yesterday =("))
        else:
            for name in YesterdaySet:
                string = ''
                i = 0
                for entry in YesterdayList:
                    if entry[1] == name:
                        string = string + entry[0] + ', '
                        i+=1 
                label = QtGui.QLabel('{0}: {1} files translated'.format(name, i))
                YesterdayLay.addWidget(label)
                label = QtGui.QLabel(string[:-2] + '\n')
                label.setWordWrap(True)
                font = label.font()
                font.setPointSize(10)
                font.setItalic(True)
                label.setFont(font)
                YesterdayLay.addWidget(label)

        
        #Lifetime Stats
        LifetimeGroup = QtGui.QGroupBox()
        layout.addWidget(LifetimeGroup)
        
        LifetimeGroup.setTitle('Lifetime:')   
        LifetimeLay = QtGui.QVBoxLayout()
        LifetimeGroup.setLayout(LifetimeLay)
        
        LifetimeList = []
        LifetimeSet = set()
        for entry in LogList:
            LifetimeSet.add(entry[2])
            for x in entry[1].split(','):
                LifetimeList.append((x, entry[2]))

        PrintList = []   
        for name in LifetimeSet:
            string = ''
            countset = set()
            for entry in LifetimeList:
                if entry[1] == name:
                    countset.add(entry[0]) 
            PrintList.append([len(countset), name])
        
            
        PrintList.sort()
        PrintList.reverse()
        
        for entry in PrintList:         
            label = QtGui.QLabel('{0:<20}\t{1} files translated'.format(entry[1] + ':', entry[0]))
            LifetimeLay.addWidget(label)

        
        self.setLayout(layout)

