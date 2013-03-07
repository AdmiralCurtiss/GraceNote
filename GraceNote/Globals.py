# -*- coding: utf-8 -*-

commentsAvailableLabel = False
Audio = False
configfile = ''
configData = None
enchanted = False
HashTableExists = False

ConnectionGracesJapanese = None
CursorGracesJapanese = None
LogCon = None
LogCur = None

EnglishVoiceLanguageFlag = False
UpdateLowerStatusFlag = False
ModeFlag = 'Semi-Auto'
AmountEditingWindows = 5
WriteDatabaseStorageToHddOnEntryChange = False
FooterVisibleFlag = False


import re

def VariableSwap(raw):        
    matchobj = raw.group()
    code = matchobj[:1]
        
    if code == u'<':
        if matchobj == ('<con>' or '<default>' or '<inn>' or '<macro>' or '<mini>' or '<se>' or '<shop>' or '<(_ _)>'):
            return matchobj
            
        colon = matchobj.find(':')
        if colon == -1:
            return matchobj
        newcode = matchobj[1:colon]

        if newcode == u'Metric':
            return u'\x01({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Unk2':
            return u'\x02({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Sys Col':
            return u'\x03({0})'.format(Sub(matchobj[colon+2:-1], 0x3))
        if newcode == u'Name':
            return u'\x04({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Unk6':
            return u'\x06({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Colour':
            return u'\x07({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Icon':
            return u'\x08({0})'.format(Sub(matchobj[colon+2:-1], 0x8))
        if newcode == u'Audio':
            return u'\x09({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Local':
            return u'\x0B({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Furi':
            return u'\x0D({0})'.format(matchobj[colon+2:-1])
        if newcode == u'Button':
            return u'\x0F({0})'.format(Sub(matchobj[colon+2:-1], 0xF))
        if newcode == u'Tab':
            return u'\x10({0})'.format(Sub(matchobj[colon+2:-1], 0x10))
        if newcode == u'Unk':
            return u'\x11({0})'.format(matchobj[colon+2:-1])
        else:
            return matchobj
            

    elif code == u'\x01':
        tag = 'Metric: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x02':
        tag = 'Unk2: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)
            
    elif code == u'\x03':
        tag = 'Sys Col: '        
        value = Sub(matchobj[2:-1], 0x3)
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x04':
        tag = 'Name: '
        value = matchobj[2:-1]

        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x06':
        tag = 'Unk6: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x07':
        tag = 'Colour: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x08':
        tag = 'Icon: '        
        value = Sub(matchobj[2:-1], 0x8)
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x09':
        tag = 'Audio: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x0b':
        tag = 'Local: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x0d':
        tag = 'Furi: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x0f':
        tag = 'Button: '        
        value = Sub(matchobj[2:-1], 0xF)
        
        return u'<{0}{1}>'.format(tag, value)

    elif code == u'\x10':
        tag = 'Tab: '        
        value = Sub(matchobj[2:-1], 0x10)
        
        return u'<{0}{1}>'.format(tag, value)
        
    elif code == u'\x11':
        tag = 'Unk: '        
        value = matchobj[2:-1]
        
        return u'<{0}{1}>'.format(tag, value)
        
    else:
        return matchobj
        
    return matchobj
    
def Sub(string, subsection):
    for item in SubstitutionTable[subsection]:
        if string == item[0]:
            return item[1]
        if string == item[1]:
            return item[0]
    

def VariableReplace(string):
    string = re.sub(u"'+", "'", unicode(string))
    string = re.sub('(.|\r)\(.*?\)', VariableSwap, unicode(string), re.DOTALL)
    string = re.sub(u"\x0A", u"↵\x0A", unicode(string))
    string = re.sub(u"\x0C", u"<Feed>\x0A", unicode(string))
    return string
    
    
def VariableRemove(string):
    string = re.sub(u"'+", "''", unicode(string))
    string = re.sub(u"<Feed>\x0A", u"\x0C", unicode(string))
    string = re.sub(u"<Feed>", u"\x0C", unicode(string))
    string = re.sub(u"↵\x0A", u"\x0A", unicode(string))
    string = re.sub(u"↵", u"\x0A", unicode(string))
    string = re.sub(u'<.*?>', VariableSwap, unicode(string), re.DOTALL)
    return string
        









SubstitutionTable = [

[ # 0x0
],

[ # 0x1
],

[ # 0x2
],

[ # 0x3
    ['0', 'Default'],
    ['1', 'Blue'],
    ['2', 'Red'],
    ['3', 'Purple'],
    ['4', 'Green'],
    ['5', 'Cyan'],
    ['6', 'Mustard'],
    ['7', 'White'],
    ['8', 'Chestnut'],
    ['9', 'Wii Blue']
],

[ # 0x4
],

[ # 0x5
],

[ # 0x6
],

[ # 0x7
],

[ # 0x8
    ['$Z1', 'Crossed Swords'],
    ['$_1', 'Crescent Moon'],
    ['$s4', 'Up Arrow'],
    ['$t4', 'Down Arrow'],
    ['$u4', 'Left Arrow'],
    ['$v4', 'Right Arrow'],
    ['$‾1', 'Bottle']
],

[ # 0x9
],

[ # 0xA
],

[ # 0xB
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', '']
],

[ # 0xC
],

[ # 0xD
],

[ # 0xE
],

[ # 0xF
    ['0,$1g1', 'A'],
    ['0,$2g1', 'B'],
    ['0,$3g1', 'Analog'],
    ['0,$4g1', 'Vert Analog'],
    ['0,$5g1', 'Horiz Analog'],
    ['0,$6g1', '2 and Horiz Analog'],
    ['0,$7g1', 'Z'],
    ['0,$8g1', '2'],
    ['0,$9g1', '1 and Horiz Analog'],
    ['0,$ag1', 'C'],
    ['0,$bg1', 'A (2)'],
    ['0,$cg1', 'Left DPad'],
    ['0,$dg1', 'Right DPad'],
    ['0,$eg1', 'Plus'],
    ['0,$fg1', '1'],
    ['0,$gg1', '1 (2)'],
    ['0,$hg1', 'Z (2)'],
    ['0,$ig1', 'Fast A'],
    ['0,$jg1', 'Minus'],
    ['0,$kg1', 'Horiz Analog (2)'],
    ['0,$lg1', 'None'],
    ['0,$mg1', 'Z + 1 + DPad Horiz + Analog Down + A'],
    ['0,$ug1', 'Minus + Plus + DPad Up + Analog Left-Right-Down'],
    ['0,$xg1', 'Minus + Plus + DPad Vert + Analog Up'],
    ['0,1024', 'Unknown1'],
    ['0,1025', 'Unknown2'],
    ['0,1026', 'Unknown3'],
    ['0,1027', 'Unknown4'],
    ['0,1028', 'Unknown5'],
    ['0,1029', 'Unknown6'],
    ['0,1030', 'Unknown7'],
    ['0,1031', 'Unknown8'],
    ['0,1032', 'Unknown9'],
    ['0,1033', 'UnknownA'],
    ['0,1034', 'UnknownB'],
    ['0,1035', 'UnknownC'],
    ['0,1036', 'UnknownD'],
    ['0,1037', 'UnknownE'],
    ['0,1038', 'UnknownF'],
    ['0,1039', 'L1'],
    ['0,1040', 'R1'],
    ['0,1040', 'UnknownI'],
    ['0,1041', 'UnknownJ'],
    ['0,1042', 'UnknownK'],
    ['0,1043', 'UnknownL'],
    ['0,1044', 'Right Analog Stick'],
    ['0,1045', 'UnknownN'],
    ['0,2048', 'X'],
    ['0,2049', 'UnknownP'],
    ['0,2050', 'UnknownQ'],
    ['0,2051', 'UnknownR'],
    ['0,2052', 'UnknownS'],
    ['0,2053', 'UnknownT'],
    ['0,2054', 'UnknownU'],
    ['0,2055', 'UnknownV'],
    ['0,2056', 'UnknownW'],
    ['0,2057', 'UnknownX'],
    ['0,2058', 'UnknownY'],
    ['0,2059', 'Left Analog Stick'],
    ['0,2060', 'L1-B'],
    ['0,2061', 'UnknownAB'],
    ['0,2062', 'UnknownAC'],
    ['0,2063', 'UnknownAD'],
    ['0,2064', 'UnknownAE'],
    ['0,2065', 'UnknownAF'],
    ['0,2066', 'R2'],
    ['0,2067', 'UnknownAH'],
    ['0,2068', 'UnknownAI'],
    ['0,2069', 'UnknownAJ'],
    ['0,2070', 'UnknownAK'],
    ['0,2071', 'UnknownAL'],
    ['0,2072', 'UnknownAM'],
    ['0,2073', 'UnknownAN']
],

[ # 0x10
    ['$q', '1'],
    ['$a1', '2'],
    ['$U1', '3'],
    ['$‾1', '3.25'],
    ['$w2', '3.75'],
    ['$K2', '4'],
    ['$A3', '5']
],

[ # 0x11
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', ''],
    ['', '']
]

]




def GetDatabaseDescriptionString(filename):
    CursorGracesJapanese.execute("SELECT count(1) FROM descriptions WHERE filename = ?", [filename])
    exists = CursorGracesJapanese.fetchall()[0][0]
    if exists > 0:
        CursorGracesJapanese.execute("SELECT shortdesc FROM descriptions WHERE filename = ?", [filename])
        desc = CursorGracesJapanese.fetchall()[0][0]
        return desc
    else:
        return filename

