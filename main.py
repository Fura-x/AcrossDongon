import time
import role, GameMaster


def main():
    
    #text = str()
    #for i in range(10):
    #    print("Loading" + "." * i, end="\r", flush=True)
    #    time.sleep(0.1)
    #print(" " * len(text), end="\r")


    gameMaster = GameMaster.GameMaster()
    gameMaster.GameLoop()

    #for r in roles:
    #    data[r.getName()] = r.ToJson()
    #
    #with open("dbb.json", 'w') as outfile:
    #    json.dump(data, outfile, indent=4, separators=(',',':'), sort_keys=True)

main()