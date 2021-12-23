from enum import Enum
import copy
import speaker, tools

class Effect(Enum):
    # 1 turn
    NEUTRAL = 0         # nothing
    SCARY = 1           # can't battle
    # 1-3 turns
    PARA = 10           # can't battle
    DISTRACT = 11       # 25% less chance to break armor
    FREEZE = 12         # can't attack       
    # 2 - 5 turns
    POISON = 20         # lost 20% of current life each turn
    FIRE = 21           # get hurts of 50% of the damages dealed to the ennemy
    TIRED = 22          # can't special
    WEAKEN = 23         # lost 20% of attack
    # only on hit
    DRAIN = 30          # get heals of 50% of the damages dealed to the ennemy
    DESTROY = 31        # one-shot
    ENBARTHELEMY = 777

    def GetTurn(effect):
        if effect.value < 10:
            return 1
        elif effect.value < 20:
            return tools.RollDice(1, 3)
        else:
            return tools.RollDice(2, 5)

    def Apply(predator, prey, enemies, allies, damage, effect):
        if effect is Effect.NEUTRAL:
            return

        recurse = round(damage * 50 / 100)
        weakeness = round(damage * 20 / 100)

        if effect is Effect.DRAIN:
            speaker.Speak("DRAIN\t- " + predator.getName() + "drains enemy HP ! " + str(recurse) + " healing recieved.")
            predator.Heal(recurse)

        if predator.effect is Effect.FIRE:
            speaker.Speak("FIRE\t- " + predator.getName() + " hit themself with fire ! " + str(recurse) + " damages recieved.")
            predator.Hurt(recurse)

        if predator.effect is Effect.WEAKEN:
            speaker.Speak("WEAKEN\t- " + predator.getName() + " is really weakened. Their attacks deal " + str(weakeness) + " less damages.")
            damage -= weakeness

        if effect is Effect.DESTROY:
            speaker.Speak("DESTROY\t- " + predator.getName() + " just destroyed " + prey.getName() + ". Their victim no longer exists.")
            prey.Hurt(prey.life)

        if effect.value < 30:
            prey.GetEffected(effect, predator.getName())

        return

    def Undergo(entity, effect):
        if effect is Effect.NEUTRAL:
            return

        elif effect is Effect.SCARY:
            speaker.Speak("SCARY\t- " + entity.getName() + " is too afraid to fight")
            entity.battling = False
            
        elif effect is Effect.PARA:
            speaker.Speak("PARA\t- " + entity.getName() + " is paralysed, impossible to fight")
            entity.battling = False

        elif effect is Effect.DISTRACT:
            speaker.Speak("DISTR.\t- " + entity.getName() + " is distracted, they lost precision...")
            # Lose 25% of armor breaker
            entity.armorBreaker -= round(entity.armorBreaker * 25 / 100)

        elif effect is Effect.POISON:
            # Hit 20% of entity current life
            dmg = round(entity.life * 20 / 100)
            speaker.Speak("POISON\t- " + entity.getName() + " is poisoned. They lost " + str(dmg) + "HP o.O")
            entity.Hurt(dmg)

        elif effect is Effect.FIRE:
            entity.specialDamage += 6

        elif effect is Effect.FREEZE:
            speaker.Speak("FREEZE\- " + entity.getName() + " is froze. They can't attack --o--")
            entity.processAttack = False

        elif effect is Effect.TIRED:
            speaker.Speak("TIRED\- " + entity.getName() + " is tired. They doesn't feel enough good to use their special.")
            entity.processSpecial = False

class BattleContext:

    hordeStrenght = 0
    horde = []
    battle = False

    def __init__(self):
        return

    def DefineHordeGroup(self, gameMaster):

        if tools.Empty(self.horde):
            # create an enemy group if not defined previously
            for i in range(0, tools.RollDice(1, len(gameMaster.advEnroll)) + 1):
                monster = tools.CopyEntity(tools.random.choice(gameMaster.horde))
                self.horde.append(monster)
        else:
            # Horde defined from story event reward, so we have only strings
            trueHorde = []
            for str in self.horde:
                entity = tools.CopyEntity(tools.Find(gameMaster.entities, str, lambda val, role: val == role.getName())[1])
                trueHorde.append(entity)
            self.horde = trueHorde

        return self.horde

    def ApplyContext(self, advGroup, hordeGroup, entities):

        for monster in hordeGroup.values():
            monster.baseDamage = self.hordeStrenght

        return

    def ToDefault(self):
        self.hordeStrenght = 0
        self.battle = False
