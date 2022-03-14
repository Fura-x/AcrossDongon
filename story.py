import copy
import speaker, tools, role
import item, logbook
from questSystem import Quest

class BookCase:

    def __init__(self, books, reserve):
        self.books = books
        self.reserve = reserve
        self.current = ""

    def FromJson(gameMaster, input):
        books = {}
        reserve = {}

        bookcase = input.pop("bookcase")
        for book in bookcase.values():
            bookInput = tools.ParseJson(book + "Book")
            books[book] = StoryBook.FromJson(gameMaster, bookInput.pop("StoryBook"))

        inputReserve = input.pop("reserve")
        for key, itm in inputReserve.items():
            reserve[key] = item.Item.FromJson(itm[0], itm[1])
            
        return BookCase(books, privateBooks, reserve)

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
        speaker.WriteInput("You're now at " + reward + ".")
        return

    def NewMember(self, gameMaster):
        # Return random member not enrolled
        member = gameMaster.NewRandomMember()

        if member is None:
            speaker.WriteInput("You can't enroll a new adventurer...")
        else:
            speaker.WriteInput(member.getName() + " is now part of your team !")

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
        speaker.WriteInput("Your team gets hurt with " + str(dmg) + " damages.")
        for adv in gameMaster.advGroup.values():
            adv.Hurt(dmg)

    def MemberHurt(self, gameMaster):
        # A random member get hurts
        dmg = self.reward
        victim = tools.RandomItem(gameMaster.advGroup)[1]
        speaker.WriteInput(victim.getName() + " gets hurt with " + str(dmg) + " damages.")
        victim.Hurt(dmg)

    def TeamHeal(self, gameMaster):
        # All members are healed
        heal = self.reward
        speaker.WriteInput("Your team is healed with " + str(heal) + " HP!")
        for adv in gameMaster.advGroup.values():
            adv.Heal(heal)

    def MemberHeal(self, gameMaster):
        # A random member is healed
        heal = self.reward
        victim = tools.RandomItem(gameMaster.advGroup)[1]
        speaker.WriteInput(victime.getName() + " is healed with " + str(heal) + " HP!")
        victim.Heal(heal)

    def ValueCast(toCast):
        # Used for string (Items, Key Items) and units (Heal, Damage)
        return toCast

    def QuestCast(toCast):
        # Used for generate quest from json
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
