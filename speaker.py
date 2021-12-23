import time, msvcrt, keyboard


writeTimer = writeTimerReset = 0.03
speakTimer = speakTimerReset = 0.5
pressed = False
enterSymbol = "> "

def SpeakSleep(splitTimer, rng):
    for i in range(0, rng):
        time.sleep(splitTimer)
        if IsPressed(): 
            splitTimer = 0
            Skip()

def Speak(str = "", toBlock = True):
    # listen every *splitTimer* seconds if key pressed
    splitTimer = speakTimer / 10.0

    SpeakSleep(splitTimer, 10)

    print(str)
    
    if (str.endswith("...")):
        SpeakSleep(splitTimer, 20)
            

def Input(str = ""):

    if str == "": 
        str = enterSymbol

    # Recieve all the none-wanted input from the last input
    while msvcrt.kbhit():
        msvcrt.getch()

    i = input(str)
    # Reset timer and active pressed variable
    Reset()
    return i

def ListSpeak(list):
    for str in list:
        Speak(str, False)

def SplitSpeak(str, sep):
    split = str.split(sep)
    ListSpeak(split)

def Write(str = "", toBlock = True):
    if str == "":
        Speak(str)
        time.sleep(100 * writeTimer)
    else:
        for char in str:
            print(char, end='')
            if char == '.':
                time.sleep(20 * writeTimer)
            else:
                time.sleep(writeTimer)
            # Assert if player wants to skip each frame
            if IsPressed(): 
                Skip()

        print("")

def ListWrite(list):
    for str in list:
        Write(str, False)

def WriteInput(str = ""):
    Write(str)
    return Input()

def InitTimer():
    global writeTimer, writeTimerReset, speakTimer, speakTimerReset, enterSymbol

    str1 = Input("Story messager speed (" + str(writeTimer) + " by default): ")
    str2 = Input("Battle messager speed (" + str(speakTimer) + " by default): ")
    str3 = Input("Symbol written when you have to press ENTER ( " + enterSymbol + " by default): ")
    if (str1 != ""):
        writeTimer = writeTimerReset = float(str1)
    if (str2 != ""):
        speakTimer = speakTimerReset = float(str2)
    if (str3 != ""):
        enterSymbol = str3

def Skip():
    global writeTimer, speakTimer, skip

    skip = True
    writeTimer = speakTimer = 0

def Reset():
    global writeTimer, writeTimerReset, speakTimer, speakTimerReset, pressed
    
    writeTimer = writeTimerReset
    speakTimer = speakTimerReset
    pressed = True

def IsPressed():
    '''Register ENTER pressed info and return true only the first time'''
    global pressed
    if keyboard.is_pressed('enter') and not pressed:# PRESS
        pressed = True
        return True
    elif keyboard.is_pressed('enter') and pressed:  # DOWN
        pressed = True
        return False
    else:                                           # RELEASE
        pressed = False
        return False




