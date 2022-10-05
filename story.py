import copy
import speaker, tools, role
import item, logbook
from questSystem import Quest, QuestSytem

class BookCase:

    def __init__(self, books, reserve, chest, quests, echest):
        self.books = books
        self.reserve = reserve
        self.entities = {}
        self.chest = chest
        self.enemyChest = echest
        self.quests = quests
        self.current = ""

    def FromJson(gameMaster, input):
        books = {}
        reserve = {}
        chest = []
        quests = []

        bookcase = input.pop("bookcase")
        for book in bookcase.values():
            bookInput = tools.ParseJson(book + "Book")
            books[book] = StoryBook.FromJson(gameMaster, bookInput.pop("StoryBook"))

        inputReserve = input.pop("reserve")
        for key, itm in inputReserve.items():
            reserve[key] = item.Item.FromJson(itm[0], itm[1])

        inputChest = input.pop("chest")
        for key, itm in inputChest.items():
            chest.append(StoryReward.FromJson(itm))

        inputQuests = input.pop("quests")
        for key, itm in inputQuests.items():
            quests.append(Quest.FromJson(itm))

        return BookCase(books, reserve, chest, quests, input.pop("echest"))

    def EntitiesFromJson(self, gameMaster, input):
            # Seconde fonction qui assure que les items sont déjà créés
        inputEntities = input.pop("entities")
        for key, itm in inputEntities.items():
            self.entities[key] = role.Role.FromJson(gameMaster, key, itm)

    def SetCurrentBook(self, book):
        self.current = book

        self.book = self.books[book]


class StoryBook:

    def __init__(self, events):
        self.events = events

    def GetRandomStory(self):
        events = self.SortEvents()
        return tools.RandomItem(events)

    def GetStory(self, name):
        return self.events.get(name, None)

    def SortEvents(self):
        events = {}
        for name, evt in self.events.items():
            if tools.IsAccessable(evt.access):
                events[name] = evt

        return events

    def FromJson(gameMaster, input):

        events = {}

        for name, storyEvent in input.items():
            events[name] = StoryEvent.FromJson(gameMaster, storyEvent)

        return StoryBook(events)

class StoryEvent:

    def __init__(self, gameMaster, enunciate, backEnunciate, choices, access):
        self.gameMaster = gameMaster
        self.enunciate = enunciate
        self.choices = choices
        self.access = access
        # When story happened twice
        self.backEnunciate = backEnunciate
        self.happened = False

    def Happens(self, gameMaster):
        # WRITE ENUNCIATE
        speaker.Speak("_____________________\n")
        if self.happened:
            speaker.ListWrite(self.backEnunciate)
        else:
            speaker.ListWrite(self.enunciate)

        speaker.Input()

        tools.EnumerateAndSelect(self.SortChoices(gameMaster))[1].Happens(gameMaster)
        logbook.storyListened += 1

        self.happened = True

        return

    def SortChoices(self, gameMaster):
        chs = []
        for choice in self.choices:
            if tools.IsAccessable(choice.access):
                chs.append(choice)

        return chs

    def FromJson(gameMaster, input):

        enunciate = input.pop("enunciate")
        backEnunciate = input.pop("back", enunciate)
        access = input.pop("access", {})

        choices = []

        for choice in input.values():
            choices.append(StoryChoice.FromJson(choice))

        return StoryEvent(gameMaster, enunciate, backEnunciate, choices, access)

class StoryChoice:

    def __init__(self, enunciate, events, access):
        self.enunciate = enunciate
        self.events = events
        self.access = access

    def __str__(self):
        key = ""
        for k, val in self.access.items():
            if val:
                key += "[" + k + "] "

        return  key + self.enunciate

    def Happens(self, gameMaster):
        tools.RandomElement(self.events).Happens(gameMaster)

    def FromJson(input):

        enunciate = input.pop("enunciate")
        access = input.pop("access", {})

        events = []
        for event in input.values():
            # Get the probability factor from this event
            proba = event.pop("prob", 1)

            choiceEvent = StoryChoiceEvent.FromJson(event)
            for i in range(0, proba):
                events.append(choiceEvent)

        return StoryChoice(enunciate, events, access)

class StoryChoiceEvent:

    def __init__(self, enunciate, storyRewards):
        self.enunciate = enunciate
        self.storyRewards = storyRewards

    def Happens(self, gameMaster):
        speaker.ListWrite(self.enunciate)
        speaker.Input()

        for sr in self.storyRewards:
            sr.Happens(gameMaster)

    def FromJson(input):
        enunciate = input.pop("enunciate")
        
        storyRewards = []
        for sr in input.values():
            storyRewards.append(StoryReward.FromJson(sr))

        return StoryChoiceEvent(enunciate, storyRewards)

class StoryReward:

    def __init__(self, func, rewards):
        self.func = func
        self.rewards = rewards

    def Happens(self, gameMaster):
        self.reward = tools.RandomElement(self.rewards)
        getattr(StoryReward, self.func)(self, gameMaster)
        
    def NextBook(self, gameMaster):
        # Change the current story book
        reward = self.reward
        gameMaster.ReadBook(reward)
        speaker.WriteInput("Vous êtes désormais à " + reward + ".")
        return

    def NewRandomMember(self, gameMaster):
        # Return random member not enrolled
        member = gameMaster.NewRandomMember()

        if member is None:
            speaker.WriteInput("Vous ne pouvez pas avoir de nouveaux membres...")
        else:
            speaker.WriteInput(member.getName() + " fait maintenant parti de votre équipe!")

        return

    def NewMember(self, gameMaster):
        # Return member not enrolled according to reward name
        member = gameMaster.NewMember(self.reward)

        if member is None:
            speaker.WriteInput("Vous ne pouvez pas avoir de nouveaux membres...")
        else:
            speaker.WriteInput(member.getName() + " fait maintenant parti de votre équipe!")

        return

    def GiveItem(self, gameMaster):
        # Return weapon or potion
        gameMaster.GiveItem(self.reward)

    def GiveKeyItem(self, gameMaster):
        # Unlock new Key Item
        logbook.AddKeyItem(self.reward)

    def GiveQuest(self, gameMaster):
        # Add a new quest to the journey !
        gameMaster.questSystem.AddQuest(self.reward)

    def Text(self, gameMaster):
        # Just write a text for story
        speaker.ListWrite(self.reward)
        speaker.Input()

    def TeamHurt(self, gameMaster):
        # All members get hurt
        dmg = self.reward
        speaker.WriteInput("Votre équipe subit " + str(dmg) + " de dégâts.")
        for adv in gameMaster.advGroup.values():
            adv.Hurt(dmg)

    def MemberHurt(self, gameMaster):
        # A random member get hurts
        dmg = self.reward
        victim = tools.RandomItem(gameMaster.advGroup)[1]
        speaker.WriteInput(victim.getName() + " subit " + str(dmg) + " de dégâts.")
        victim.Hurt(dmg)

    def TeamHeal(self, gameMaster):
        # All members are healed
        heal = self.reward
        speaker.WriteInput("Votre équipe est soignée de " + str(heal) + "PV!")
        for adv in gameMaster.advGroup.values():
            adv.Heal(heal)

    def MemberHeal(self, gameMaster):
        # A random member is healed
        heal = self.reward
        victim = tools.RandomItem(gameMaster.advGroup)[1]
        speaker.WriteInput(victim.getName() + " est soigné(e) de " + str(heal) + "PV!")
        victim.Heal(heal)

    def LosePotion(self, gameMaster):
        # Lose a random potion from random adventurer
        victim = tools.RandomItem(gameMaster.advGroup)[1]
        potion = victim.inventory.PopRandomSpec("Potion")
        if potion is None:
            speaker.Write("On a rien pu vous voler...")
        else:
            speaker.Write(victim.getName() + " s'est fait prendre " + str(potion))

    def Final(self, gameMaster):
        #Activate final challenge
        gameMaster.BossBattle()
        return

    def ValueCast(toCast):
        # Used for string (Items, Key Items) and units (Heal, Damage)
        return toCast

    def QuestCast(toCast):
        # Used for generate quest from json
        return Quest.FromJson(toCast)

    def FromJson(input):
        func = input.pop("func", None)
        cast = input.pop("cast", "ValueCast")

        rewards = []
        # Call the cast function to cast reward in correct type
        for reward in input.values():
            rewards.append(getattr(StoryReward, cast)(reward))

        return StoryReward(func, rewards)
