import speaker

battleWon = -1
storyListened = 0

global keyItems
keyItems = {}

def AddKeyItem(key):
    if key not in keyItems.keys():
        speaker.WriteInput("Add [ " + key + " ] to your key items !")
    keyItems[key] = key

def IsKeyItem(key):
    return key in keyItems.keys()
