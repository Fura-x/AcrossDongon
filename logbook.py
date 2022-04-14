import speaker

battleWon = -1
storyListened = 0

global keyItems
keyItems = {}

def AddKeyItem(key):
    if key not in keyItems.keys():
        speaker.WriteInput("Item clé [ " + key + " ] obtenu!")
    keyItems[key] = key

def PopKeyItem(key):
    pop = keyItems.pop(key, None)
    if pop is not None:
        speaker.Speak("Item clé [ " + key + " ] retiré.")

def IsKeyItem(key):
    return key in keyItems.keys()
