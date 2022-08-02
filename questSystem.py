import speaker
import story, logbook

class QuestSytem:

    quests = []

    def __init__(self):
        return

    def __str__(self):
        string = "MISSIONS:\n"
        for quest in self.quests:
            string += "\t" + quest.enunciate + " -> " + str(quest.currentValue) + "/" + str(quest.goal) + "\n"
        return string

    def AddQuest(self, quest):
        speaker.WriteInput("NOUVELLE MISSION: " + quest.enunciate)
        quest.Reset()
        self.quests.append(quest)
        return

    def Check(self, gameMaster):
        # Check if quests have been completed
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
        self.currentValue = 0
        self.event = event

    def __str__(self):
        return self.enunciate

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
        self.currentValue = logbook.battleWon
        return self.currentValue >= self.goal

    def KeyItem(self, init = False):
        return logbook.IsKeyItem(value)

    def EnemyKill(self, init = False):
        if init:
            self.goal = logbook.enemyKilled + self.value
        self.currentValue = logbook.enemyKilled 
        return self.currentValue >= self.goal

    def PotionConsuming(self, init = False):
        if init:
            self.goal = logbook.potionConsumed + self.value
        self.currentValue = logbook.potionConsumed 
        return self.currentValue >= self.goal

    def WorldDiscover(self, init = False):
        if init:
            self.goal = logbook.worldDiscovered + self.value
        self.currentValue = logbook.worldDiscovered
        return self.currentValue >= self.goal

    def WorldCross(self, init = False):
        if init:
            self.goal = logbook.worldCrossed + self.value
        self.currentValue = logbook.worldCrossed 
        return self.currentValue >= self.goal

    def EarnCoin(self, init = False):
        if init:
            self.goal = logbook.coins + self.value
        self.currentValue = logbook.coins 
        return self.currentValue >= self.goal

    def FromJson(input):
        return Quest(input["enunciate"], input["condition"], input["value"], story.StoryChoiceEvent.FromJson(input["event"]))
