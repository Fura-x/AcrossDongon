import speaker
import story, logbook

class QuestSytem:

    quests = []

    def __init__(self):
        return

    def AddQuest(self, quest):
        speaker.WriteInput("NEW QUEST : " + quest.enunciate)
        quest.Reset()
        self.quests.append(quest)
        return

    def Check(self, gameMaster):

        index, indexes = 0, []
        for quest in self.quests:
            if quest.Check(gameMaster):
                indexes.append(index)
            index += 1

        for id in indexes:
            self.quests.pop(id)

class Quest:

    def __init__(self, enunciate, condition, value, event):
        self.enunciate = enunciate
        self.condition = condition
        self.value = value
        self.event = event

    def Reset(self):
        getattr(self, self.condition)(True)

    def Check(self, gameMaster):
        if getattr(self, self.condition)():
            self.event.Happens(gameMaster)
            return True
        return False
                               
    def BattleHorde(self, init = False):
        if init:
            self.goal = logbook.battleWon + self.value
        return logbook.battleWon >= self.goal

    def KeyItem(self, init = False):
        return logbook.IsKeyItem(value)

    def FromJson(input):
        return Quest(input["enunciate"], input["condition"], input["value"], story.StoryChoiceEvent.FromJson(input["event"]))
