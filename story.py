import copy
import speaker, tools, role
import item, logbook
from questSystem import Quest

class BookCase:

    def __init__(self, books, privateBooks, reserve):
        self.books = books
        self.privateBooks = privateBooks
        self.reserve = reserve
        self.current = ""

    def FromJson(gameMaster, input):
        books = {}
        privateBooks = {}
        reserve = {}

        bookcase = input.pop("bookcase")
        for book in bookcase.values():
            bookInput = tools.ParseJson(book + "Book")
            books[book] = StoryBook.FromJson(gameMaster, bookInput.pop("StoryBook"))
            privateBooks[book] = StoryBook.FromJson(gameMaster, bookInput.pop("PrivateStoryBook"))

        inputReserve = input.pop("reserve")
        for key, itm in inputReserve.items():
            reserve[key] = item.Item.FromJson(itm[0], itm[1])
            
        return BookCase(books, privateBooks, reserve)

    def SetCurrentBook(self, book):
        self.previous = self.current
        self.current = book

        self.book = self.books[book]
        self.privateBook = self.privateBooks[book]


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
            if evt.IsAccessable():
                events[name] = evt

        return events

    def FromJson(gameMaster, input):

        events = {}

        for name, storyEvent in input.items():
            events[name] = StoryEvent.FromJson(gameMaster, storyEvent)

        return StoryBook(events)

class StoryEvent:

    def __init__(self, gameMaster, enunciate, choices, access):
        self.gameMaster = gameMaster
        self.enunciate = enunciate
        self.choices = choices
        self.access = access

    def IsAccessable(self):
        if tools.Empty(self.access):
                return True
        else:
            for key, val in self.access.items():
                if val is not logbook.IsKeyItem(key): # return false if the access is wrong
                    return False

        return True

    def Happens(self, gameMaster):
        # WRITE ENUNCIATE
        speaker.Speak("_____________________\n")
        speaker.ListWrite(self.enunciate)
        speaker.Input()

        tools.EnumerateAndSelect(self.SortChoices(gameMaster))[1].Happens(gameMaster)
        logbook.storyListened += 1

        return

    def SortChoices(self, gameMaster):
        chs = []
        for choice in self.choices:
            if choice.IsAccessable():
                chs.append(choice)

        return chs

    def FromJson(gameMaster, input):

        enunciate = input.pop("enunciate")
        access = input.pop("access", {})

        choices = []

        for choice in input.values():
            choices.append(StoryChoice.FromJson(choice))

        return StoryEvent(gameMaster, enunciate, choices, access)

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

    def IsAccessable(self):
        if tools.Empty(self.access):
                return True
        else:
            for key, val in self.access.items():
                if val is not logbook.IsKeyItem(key): # return false if the access is wrong
                    return False

        return True

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
        reward = self.reward
        gameMaster.ReadBook(reward)
        speaker.WriteInput("You're now at " + reward + ".")
        return

    def PreviousBook(self, gameMaster):
        gameMaster.ReadBook(gameMaster.bookCase.previous)
        speaker.WriteInput("You're now at " + gameMaster.bookCase.previous + ".")
        return

    def NextStory(self, gameMaster):
        reward = self.reward
        gameMaster.ChoseStory(reward)
        
        return

    def SetPublic(self, gameMaster):
        '''Set a private story to public'''
        reward = self.reward
        private, public = gameMaster.privateBook, gameMaster.book

        story = private.get(reward, None)
        if story is not None:
            public[reward] = story

        return

    def SetPrivate(self, gameMaster):
        '''Set a public story to private'''
        reward = self.reward
        private, public = gameMaster.privateBook, gameMaster.book

        story = public.get(reward, None)
        if story is not None:
            private[reward] = story

        return

    def NewMember(self, gameMaster):
        member = gameMaster.NewRandomMember()

        if member is None:
            speaker.WriteInput("You can't enroll a new adventurer...")
        else:
            speaker.WriteInput(member.getName() + " is now part of your team !")

        return

    def GiveItem(self, gameMaster):
        gameMaster.GiveItem(self.reward)

    def GiveKeyItem(self, gameMaster):
        logbook.AddKeyItem(self.reward)

    def GiveQuest(self, gameMaster):
        gameMaster.questSystem.AddQuest(self.reward)

    def TeamHurt(self, gameMaster):
        dmg = self.reward
        speaker.WriteInput("Your team gets hurt with " + str(dmg) + " damages.")
        for adv in gameMaster.advGroup.values():
            adv.Hurt(dmg)

    def MemberHurt(self, gameMaster):
        dmg = self.reward
        victim = tools.RandomItem(gameMaster.advGroup)[1]
        speaker.WriteInput(victim.getName() + " gets hurt with " + str(dmg) + " damages.")
        victim.Hurt(dmg)

    def TeamHeal(self, gameMaster):
        heal = self.reward
        speaker.WriteInput("Your team is healed with " + str(heal) + " HP.")
        for adv in gameMaster.advGroup.values():
            adv.Heal(heal)

    def ForceBattle(self, gameMaster):
        gameMaster.battleContext.battle = True
        return

    def DefineHorde(self, gameMaster):
        gameMaster.battleContext.horde = self.reward

    def HordeStrenght(self, gameMaster):
        strenght = self.reward
        speaker.WriteInput("Your next opponents will have " + str(strenght) + " bonus damages.")
        gameMaster.battleContext.hordeStrenght = strenght

    def ValueCast(toCast):
        return toCast

    def QuestCast(toCast):
        return Quest.FromJson(toCast)

    def FromJson(input):
        func = input.pop("func", None)
        cast = input.pop("cast", "ValueCast")

        if func is None:
            return StoryChoiceEvent(enunciate, None, None)

        rewards = []
        # Call the cast function to cast reward in correct type
        for reward in input.values():
            rewards.append(getattr(StoryReward, cast)(reward))

        return StoryReward(func, rewards)
