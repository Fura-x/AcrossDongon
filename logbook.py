import speaker

battleWon = -1
storyListened = 0

global keyItems
keyItems = {}

def AddKeyItem(key):
    if key not in keyItems.keys():
        speaker.WriteInput("Add [ " + key + " ] to your key items!")
    keyItems[key] = key

def PopKeyItem(key):
    pop = keyItems.pop(key, None)
    if pop is not None:
        speaker.Speak("Remove [ " + key + " ] from your key items.")

def IsKeyItem(key):
    return key in keyItems.keys()
