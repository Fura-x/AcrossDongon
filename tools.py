import random, collections, operator, json, copy
import speaker, logbook

## Dungeon and Dragon
def RollDice(number, value):
    result = 0
    for i in range(number):
        result += random.randint(1, value)
    return result
    
def GlobalAttack(group, damage):

    keys = [] # stock dead entities' key to delete them
    for key, entity in group.items():
        entity.Hurt(damage)

    return

def CopyItem(toCopy):
    copi = copy.copy(toCopy)
    return copi

def CopyEntity(toCopy):
    inventory = copy.deepcopy(toCopy.inventory)
    copi = copy.copy(toCopy)
    copi.inventory = inventory
    return copi

def CopyEntities(listToCopy):
    copyList = []
    for en in listToCopy:
        copyList.append(CopyEntity(en))
    return copyList

def IsAccessable(access):
        if Empty(access):
                return True
        else:
            for key, val in access.items():
                if val is not logbook.IsKeyItem(key): # return false if the access is wrong
                    return False

        return True

## Dictionary && List

def Empty(array):
    return len(array) == 0

def Find(_list, value, comp = lambda val,elem : val == elem):
    index = 0
    for element in _list:
        if comp(value, element):
            return index, element
        index += 1

    return -1, None

def Pop(_list, value, comp = lambda val,elem : val == elem):
    index = 0
    for element in _list:
        if comp(value, element):
            return  _list.pop(index)
        index += 1

    return None

def RandomItem(group):
    if not Empty(group):
        return random.choice(list(group.items()))

def RandomElement(l):
    if not Empty(l):
        return random.choice(l)

def PopRandomItem(l):
    if not Empty(l):
        random.shuffle(l)
        return l.pop(0)

def RandomizeList(list):
    if not Empty(list):
        random.shuffle(list)

def RandomDict(list, value, key_separator = 0.0):
    # create a dictionnary from a list with random index
    dic = {}
    for e in list:
        key = RollDice(1, value) + key_separator
        while key in dic: #need a different value
            key = RollDice(1, value)  + key_separator 

        dic[key] = e

    return dic

def MergeDict(a, b):
    return {**a, **b}

def Reorder(dic, _reverse=True):
    # order dict with key
    return collections.OrderedDict(sorted(dic.items(), key = operator.itemgetter(0), reverse=_reverse))

## Keyboard
    

## Other utility

def CheckStringIndex(strIndex, array):
    return strIndex.isdigit() and int(strIndex) < len(array)

def ParseJson(jsonName):
    input = {}
    with open(jsonName + ".json") as infile:
            input = json.load(infile)
    return input

def EnumerateAndSelect(list):
    # ENUMERATE
    index = 0
    for element in list:
        speaker.Write(str(index) + " - " + str(element))
        index += 1
    
        
    if index == 1:
        speaker.WriteInput("Cette fois-ci, vous n'avez pas le choix.")
        return 0, list[0]
    
    
    # SELECT
    element = speaker.WriteInput("Votre choix : ")
    while element ==  "" or not CheckStringIndex(element, list):
        element = speaker.WriteInput("Tapez un numéro : ")
                
    return int(element), list[int(element)]


####if (index is 1):
####    speaker.Write("Cette fois-ci, vous n'avez pas le choix.")
####    return 0, list[0]