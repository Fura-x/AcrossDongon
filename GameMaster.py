import copy
import role, item, story
import logbook, questSystem
import speaker, tools

from battleSystem import BattleContext

class GameMaster():
    """The Master of the game"""

    godGift = True
    advGroup = {}
    hordeGroup = {}
    money = 0

    def __init__(self):

        speaker.InitTimer()
        speaker.Write()

        self.bookCase = story.BookCase.FromJson(self, tools.ParseJson("library"))
        self.ReadSelectedBook()

        self.advEnroll = tools.CopyEntities(self.adventurers[:1])
        self.advGroup = tools.RandomDict(self.advEnroll, 20)

        self.battleContext = BattleContext()
        self.questSystem = questSystem.QuestSytem()

        speaker.Write(str(self))

        return

    def __str__(self):
        return "\nInformations:\n" + "Aventuriers:\n" + self.AdventurersToString() + "Horde:\n" + self.HordeToString()

    def AdventurersToString(self):
        adventurers = ""

        for adv in self.advGroup.values():
            adventurers += "  " + str(adv) + "\n\n"

        return adventurers

    def HordeToString(self):
        horde = ""

        for monster in self.hordeGroup.values():
            horde += "  " + str(monster) + "\n\n"

        return horde

    def ReadBook(self, book):

        speaker.WriteInput("=-= Nouveau lieu: Vous êtes à " + book + " =-=")

        self.bookCase.SetCurrentBook(book)

        bookInput = tools.ParseJson(book + "Book")
        bookInput.pop("StoryBook")

        # ENTITY STORAGE
        self.horde = []
        self.adventurers = []

        for key, value in bookInput.items():
            entity = role.Role.FromJson(self, key, value)
            if (entity.adventurer is True):
                self.adventurers.append(entity)
            else:
                self.horde.append(entity)

        self.entities = self.horde + self.adventurers

    def ReadRandomBook(self):
        book = tools.RandomElement(list(self.bookCase.books.keys()))
        self.ReadBook(book)

    def ReadSelectedBook(self):
        speaker.Write("Choisissez un lieu où aller:")
        book = tools.EnumerateAndSelect(list(self.bookCase.books.keys()))[1]
        self.ReadBook(book)

    def AdventurersAlive(self):
        return len(self.advGroup) > 0

    def HordeAlive(self):
        return len(self.hordeGroup) > 0

    def Fighting(self):
        return self.AdventurersAlive() and self.HordeAlive()

    def AssertEntityDead(self, key, entity):
        ## Check if entity is alive
        if not entity.Alive():
            ## Remove entity from the game
            self.combattants.pop(key)

            adv = self.advGroup.pop(key, None)
            if adv is not None:
                tools.Pop(self.advEnroll, adv.getName(), lambda name, a: name == a.getName())

            self.hordeGroup.pop(key, None)

            return True

    def Pause(self, turn):
        speaker.Speak("\n=== tour n°" + str(turn) + " terminé. \n  - 'info' \n  - 'help' pour provoquer la chance\n  - ENTREE pour continuer\n ")
        self.PauseInput()

    def PauseInput(self, help=True):
        entry = speaker.Input()

        if (entry == 'info'): # Battle info (entity stats)
            speaker.Write(str(self))
            if help:
                speaker.Speak("Tapez 'help' ou ENTREE:")
            else:
                speaker.Speak("Tapez ENTREE:")
            self.PauseInput(help)

        elif (help and entry == 'help'): # Get a chance to have a special rewards, cost is patience
            speaker.Write("Vous avez demandé de l'aide...")
            speaker.time.sleep(3)
            if self.GodGift():
                speaker.Write("Un dieu vous a entendu, et vous a récompensé.")
            else:
                speaker.Write("Désolé mais, vous avez attendu pour rien.")
            speaker.Speak("Tapez 'info' ou ENTREE:")
            self.PauseInput(False)

        print()

    def EndTurn(self, key):
        # move entity to the end of the list
        if key in self.combattants.keys():
            self.combattants.move_to_end(key)

    def GameLoop(self):
        journey, final = True, False
        while journey and self.AdventurersAlive() :

            # QUEST
            self.questSystem.Check(self)

            # STORY
            st = self.bookCase.book.GetRandomStory()
            self.StoryHappens(st)

            # BATTLE

            logbook.battleWon += 1 # battleWon = -1 at beginning
            
            self.Battle() # battle event
            self.EndBattle() # a party won

            # CHECK ADVENTURER STATES
            if (not self.AdventurersAlive()):
                break

            # REWARD
            speaker.WriteInput("Vous avez remporté le combat ! Par chance, vous obtenez une récompense.")
            self.GetRandomReward()

            # CHECK FOR BATTLE COUNT
            if logbook.battleWon == 13:
                self.BossBattle()
                final = True
                break




        # END
        speaker.Write(".")
        speaker.Write(".")
        speaker.Write(".")
        speaker.Write("Votre aventure se termine ici, vous avez remporté " + str(logbook.battleWon) + " batailles !\n")

    def StoryHappens(self, storyTuple):
        speaker.Speak()
        speaker.Write(storyTuple[0])
        storyTuple[1].Happens(self)


    def SetBattleContext(self):

        hordeGroup = self.battleContext.DefineHordeGroup(self)

        # Define the order of the entities in battle
        self.advGroup = tools.RandomDict(self.advEnroll, 20)
        self.hordeGroup = tools.RandomDict(hordeGroup, 20, 0.1)
        merge = tools.MergeDict(self.advGroup, self.hordeGroup)
        
        self.combattants = tools.Reorder(merge)

        # Improve adventurer strenght each round
        for adv in self.advGroup.values():
            adv.baseArmorBreaker = 20 + logbook.battleWon

        # Send a signal for battle beginning
        for entity in self.combattants.values():
            entity.OnBattleBegins()

        self.enemyJoin = None

        return

    def Battle(self):

        self.SetBattleContext()

        #Introduction sentences
        speaker.Write("Une horde d'ennemis apparaît !")
        speaker.Input()
        speaker.Write(str(self))
        speaker.WriteInput("\n ... Tapez ENTREE pour commencer la confrontation.")
        speaker.Speak("\n")

        # Battle loop
        self.prevTurn = 0

        while(self.Fighting()):
            key = list(self.combattants.keys())[0]
            entity = list(self.combattants.values())[0]
            # Check entity life
            if self.AssertEntityDead(key, entity):
                break
            # Check new turn condition
            elif (entity.turn is not self.prevTurn):
                self.Pause(self.prevTurn)
                self.prevTurn += 1

            # ENTITY TURN
            entity.Play()

            self.EndTurn(key)

            if self.enemyJoin is not None:
                self.EnemyJoin()

        # WINNER
        if self.AdventurersAlive():
            speaker.Speak("\n===== VOUS AVEZ GAGNE ! =====")
        else:
            speaker.Speak("\n===== LA HORDE L'EMPORTE ! VOUS ETES VAINCUE... =====")

        self.battleContext.horde.clear() # Clear battleContext horde group
        speaker.Input("")

        return

    def EndBattle(self):
        self.battleContext.ToDefault()
        return

    def BossBattle(self):

        return

    def EnemyJoin(self):

        # Find the enemy
        newEnemy = None
        for enemy in self.horde:
            if enemy.getName() is self.enemyJoin:
                newEnemy = tools.CopyEntity(enemy)

        self.enemyJoin = None

        if newEnemy is None:
            return

        speaker.Speak("\nJOIN\t- " + newEnemy.getName() + " rejoint le combat ! --- Le tour recommence. \n")

        # Add to the current horde group
        hordeGroup = list(self.hordeGroup.values())
        hordeGroup.append(newEnemy)

        # Reorder entities in battle
        self.advGroup = tools.RandomDict(self.advEnroll, 20)
        self.hordeGroup = tools.RandomDict(hordeGroup, 20, 0.1)
        merge = tools.MergeDict(self.advGroup, self.hordeGroup)
        
        self.combattants = tools.Reorder(merge)

        # Send a signal for battle re-beginning
        for entity in self.combattants.values():
            entity.OnBattleBegins()
            entity.turn = self.prevTurn

        return

    def NewRandomMember(self):
        '''Get a random member which is not enrolled'''
        name = []
        for adventurer in self.advEnroll:
            name.append(adventurer.getName())

        tools.RandomizeList(self.adventurers)
        for adventurer in self.adventurers:
            if adventurer.getName() in name:
                continue
            self.advEnroll.append(tools.CopyEntity(adventurer))
            return adventurer

        return None

    def NewMember(self, memberName):
        '''Try to enroll a new member with a given name'''
        name = []
        for adventurer in self.advEnroll:
            name.append(adventurer.getName())

        for adventurer in self.adventurers:
            if adventurer.getName() in name:
                continue
            if adventurer.getName() is memberName:
                self.advEnroll.append(tools.CopyEntity(adventurer))
                return adventurer

    def GiveItemRandom(self, item, groupIndex = 0):
        '''groupIndex : 0 -adventurers 1- horde 2- all'''
        if groupIndex == 0:
            tools.RandomItem(self.advGroup)[1].GiveItem(item)
        elif groupIndex == 1:
            tools.RandomItem(self.hordeGroup)[1].GiveItem(item)
        else:
            tools.RandomItem(self.combattants)[1].GiveItem(item)

    def GetAdventurer(self, name):
        # Find an adventurer by its name
        for adv in self.advGroup.values():
            if name.lower() == adv.getName().lower():
                return adv
                
        return None

    def SelectAdventurer(self, recall = False):
        '''Ask player to chose an adventurer'''
        if not recall:
            entry = speaker.WriteInput("Choisissez un aventurier pour donner l'item, tapez 'info' pour voir l'équipe : ")
        else:
            entry = speaker.WriteInput("Tapez le nom de l'aventurier: ")

        if entry == "info":
            speaker.Speak(self.AdventurersToString())
            return self.SelectAdventurer(True)

        while(entry ==  "" or self.GetAdventurer(entry) is None):
            return self.SelectAdventurer(True)

        return self.GetAdventurer(entry)

    def GetItem(self, itemName):
        return self.bookCase.reserve[itemName]

    def GiveItem(self, itemName):
        '''give the item to the adventurer whom player will chose'''
        item = self.GetItem(itemName)

        speaker.Write(" =-= Item : " + str(item) + " =-=")

        adv = self.SelectAdventurer()
        adv.GiveItem(item)
        speaker.WriteInput(item.object + " donné à " + adv.getName() + " ! Tapez ENTREE pour continuer\n")

        return

    def GiveMoney(self, coins):
        '''Give money to the adventurer player will chose'''
        speaker.Write(" =-= " + str(coins) + " pièces récupérées =-=")

        adv = self.SelectAdventurer()
        adv.coins += coins
        speaker.WriteInput("L'argent est donné à " + adv.getName() + " ! Tapez ENTREE pour continuer\n")

        return

    def GetRandomReward(self):
        '''Apply random reward from bookCase's chest'''
        tools.RandomElement(self.bookCase.chest).Happens(self)

    def GodGift(self):
        '''Give a lucky reward '''
        if self.godGift or tools.RollDice(1, 8) == 1:

            self.GetRandomReward()
            self.godGift = False

            return True
        return False




    



