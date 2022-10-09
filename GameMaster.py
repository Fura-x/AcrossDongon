import copy, keyboard
import role, item, story
import logbook, questSystem
import speaker, tools
import questSystem

from battleSystem import BattleContext

class GameMaster():
    """The Master of the game"""

    godGift = True
    advGroup = {}
    hordeGroup = {}
    advEnroll = []

    def __init__(self):

        speaker.InitTimer()
        speaker.Write()

        # PARSE LIBRARY.JSON
        self.bookCase = story.BookCase.FromJson(self, tools.ParseJson("library"))
        self.bookCase.EntitiesFromJson(self, tools.ParseJson("library"))
        # CHOSE QUEST
        speaker.Write("Pour commencer,")
        speaker.Write("Choisissez une mission pour obtenir le soutien des dieux:")
        self.questSystem = questSystem.QuestSytem()
        self.questSystem.AddQuest(tools.EnumerateAndSelect(self.bookCase.quests)[1])
        # CHOSE WORLD AND ADVENTURER
        self.ReadSelectedBook()
        # CHOSE ADVENTURER
        speaker.Write("\nChoisissez votre second aventurier :")
        self.ChoseNewAdventurer()


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

        inputEntities = []
        inputEntities = bookInput.pop("entities")

        # ENTITY STORAGE
        self.horde = []
        self.adventurers = []

        for key, value in self.bookCase.entities.items():
            if key in inputEntities:
                if (value.adventurer is True):
                    self.adventurers.append(value)
                else:
                    self.horde.append(value)

        self.entities = self.horde + self.adventurers

    def ReadRandomBook(self):
        book = tools.RandomElement(list(self.bookCase.books.keys()))
        self.ReadBook(book)

    def ReadSelectedBook(self):
        speaker.Write("Choisissez un lieu où aller:")
        book = tools.EnumerateAndSelect(list(self.bookCase.books.keys()))[1]
        self.ReadBook(book)
        speaker.Write("Vous rencontrez des nouveaux personnages! Lequel voulez-vous enroller?")
        self.ChoseNewAdventurer()

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
                self.PopMember(adv.getName())

            enemy = self.hordeGroup.pop(key, None)
            if enemy is not None:
                logbook.enemyKilled += 1

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

            logbook.battleWon += 1 # battleWon = -1 at beginning

            # CHANGE WORLD
            worldRatio = 3
            if logbook.battleWon != 0 and logbook.battleWon % worldRatio == 0:
                self.ReadSelectedBook()

            # QUEST
            self.questSystem.Check(self)
            speaker.WriteInput(str(self.questSystem))

            # STORY
            st = self.bookCase.book.GetRandomStory()
            self.StoryHappens(st)

            # BATTLE
            
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

        # Improve adventurer strength each round
        for adv in self.advGroup.values():
            adv.baseArmorBreaker = 20 + logbook.battleWon * 2

        # Send a signal for battle beginning
        for entity in self.combattants.values():
            entity.OnBattleBegins()

        self.enemyJoin = []

        return

    def Battle(self):

        self.SetBattleContext()

        #Introduction sentences
        speaker.Write("Une horde d'ennemis apparaît !")
        speaker.Input()
        speaker.Write(str(self))
        speaker.WriteInput("\n ... Tapez ENTREE pour commencer la confrontation.")
        speaker.Speak()

        # Battle loop
        self.prevTurn = 0


        while(self.Fighting()):

            speaker.Speak()

            # PAUSE THE GAME
            if keyboard.is_pressed('p'):
                speaker.Input()
                    
            # PICK AN ENTITY
            key = list(self.combattants.keys())[0]
            self.currentEntity = list(self.combattants.values())[0]
            # Check entity's life
            if self.AssertEntityDead(key, self.currentEntity):
                break
            # Check new turn condition
            elif (self.currentEntity.turn is not self.prevTurn):
                self.Pause(self.prevTurn)
                self.prevTurn += 1

            # ENTITY TURN
            self.currentEntity.Play()

            self.EndTurn(key)

            # ADD NEW ENEMY TO THE BATTLE
            if not tools.Empty(self.enemyJoin):
                for enemyJoin in self.enemyJoin:
                    self.EnemyJoin(enemyJoin)
                self.enemyJoin.clear()

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

    def EnemyJoin(self, name):

        # Find the enemy
        newEnemy = None
        for enemy in self.horde:
            if enemy.getName() is name:
                newEnemy = tools.CopyEntity(enemy)

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

    def AddNewMember(self, adventurer):
        self.advEnroll.append(tools.CopyEntity(adventurer))
        logbook.AddKeyItem(adventurer.getName())

    def NewRandomMember(self):
        '''Get a random member which is not enrolled'''
        name = []
        for adventurer in self.advEnroll:
            name.append(adventurer.getName())

        tools.RandomizeList(self.adventurers)
        for adventurer in self.adventurers:
            if adventurer.getName() in name:
                continue
            self.AddNewMember(adventurer)
            return adventurer

        return None

    def NewMember(self, memberName):
        '''Try to enroll a new member with a given name'''
        name = []
        for adventurer in self.advEnroll:
            name.append(adventurer.getName())

        for adventurer in self.bookCase.entities.values():
            if adventurer.getName() in name:
                continue
            if adventurer.getName() == memberName:

                self.AddNewMember(adventurer)
                return adventurer

    def PopMember(self, advName):
        tools.Pop(self.advEnroll, advName, lambda name, a: name == a.getName())
        logbook.PopKeyItem(advName)

    def GiveItemRandom(self, item, groupIndex = 0):
        '''groupIndex : 0 -adventurers 1- horde 2- all'''
        if groupIndex == 0:
            tools.RandomItem(self.advGroup)[1].GiveItem(item)
        elif groupIndex == 1:
            tools.RandomItem(self.hordeGroup)[1].GiveItem(item)
        else:
            tools.RandomItem(self.combattants)[1].GiveItem(item)

    def ChoseNewAdventurer(self):
        availableAdventurers = []
        for adv in self.adventurers:
            if adv.getName() not in logbook.keyItems:
                availableAdventurers.append(adv)

        if tools.Empty(availableAdventurers):
            return

        adventurer = tools.EnumerateAndSelect(availableAdventurers)[1]
        self.AddNewMember(adventurer)
        speaker.Write("Vous avez enrollé " + adventurer.getName() + " !")



    def GetAdventurer(self, name):
        # Find an adventurer by its name
        for adv in self.advGroup.values():
            if name.lower() == adv.getName().lower():
                return adv
                
        return None

    def SelectAdventurer(self, recall = False):
        '''Ask player to chose an adventurer'''
        return tools.EnumerateAndSelect(self.advEnroll)[1]

    def GetItem(self, itemName):
        return tools.CopyItem(self.bookCase.reserve[itemName])

    def GetRandomItem(self, object = None):
        if (object is None):
            return tools.CopyItem(tools.RandomElement(list(self.bookCase.reserve.values())))

        else:
            item = tools.CopyItem(tools.RandomElement(list(self.bookCase.reserve.values())))
            while item.object is not object:
                item = tools.CopyItem(tools.RandomElement(list(self.bookCase.reserve.values())))

            return item

    def GiveItem(self, itemName):
        '''give the item to the adventurer whom player will chose'''
        item = self.GetItem(itemName)

        speaker.Write(" =-= Item : " + str(item) + " =-=")

        adv = self.SelectAdventurer()
        adv.GiveItem(item)
        speaker.WriteInput(item.object + " donné à " + adv.getName() + " ! Tapez ENTREE pour continuer\n")

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




    



