from enum import Enum
import copy
import speaker, tools

class Effect(Enum):
    # 1 turn
    NEUTRE = 0          # nothing
    EFFROI = 1          # can't battle
    # 1-3 turns
    PARA = 10           # can't battle
    CURIEUX = 11        # 25% less chance to break armor
    GEL = 12            # can't attack       
    # 2 - 5 turns
    POISON = 20         # lost 20% of current life each turn
    FEU = 21            # get hurts of 50% of the damages dealed to the ennemy
    FATIGUE = 22        # can't special
    FAIBLE = 23         # lost 20% of attack
    # only on hit
    DRAIN = 30          # get heals of 50% of the damages dealed to the ennemy
    DESTROY = 31        # one-shot
    VOL = 32            # steal 10 coins from the victim
    ENBARTHELEMY = 777

    def GetTurn(effect):
        if effect.value < 10:
            return 1
        elif effect.value < 20:
            return tools.RollDice(1, 3)
        else:
            return tools.RollDice(2, 5)

    def Steal(predator, prey):
        coins = 0
        if(prey.coins < 10):
            coins = prey.coins
        else:
            coins = 10

        prey.coins -= coins
        predator.coins += coins
        return coins

    def Apply(predator, prey, enemies, allies, damage, effect):
        if effect is Effect.NEUTRE:
            return

        recurse = round(damage * 50 / 100)
        weakeness = round(damage * 20 / 100)

        if effect is Effect.DRAIN:
            speaker.Speak("DRAIN\t- " + predator.getName() + " a volé la vie de son ennemie ! Il est soigné de" + str(recurse) + "PV.")
            predator.Heal(recurse)

        if effect is Effect.VOL:
            speaker.Speak("VOL\t- " + predator.getName() + " vole " + prey.getName() + "!")
            coins = Effect.Steal(predator, prey)
            if(coins > 0 and predator.adventurer):
                speaker.Speak("MONEY\t- Vous gagnez " + str(coins) + " pièces !")
            elif(coins > 0 and not predator.adventurer):
                speaker.Speak("MONEY\t- Vous perdez " + str(coins) + " pièces...")

        if predator.effect is Effect.FEU:
            speaker.Speak("BRULURE\t- " + predator.getName() + " s'est blessé lui-même par brûlure ! Il reçoit " + str(recurse) + " de dommages.")
            predator.Hurt(recurse)

        if predator.effect is Effect.FAIBLE:
            speaker.Speak("FAIBLE\t- " + predator.getName() + " est vraiment affaiblie. Ses attaques vont faire " + str(weakeness) + " de dégâts en moins.")
            damage -= weakeness

        if effect is Effect.DESTROY:
            speaker.Speak("DESTROY\t- " + predator.getName() + " a désintégré " + prey.getName() + ". Sa victime n'existe plus.")
            prey.Hurt(prey.life)

        if effect.value < 30:
            prey.GetEffected(effect, predator.getName())

        return

    def Undergo(entity, effect):
        if effect is Effect.NEUTRE:
            return

        elif effect is Effect.EFFROI:
            speaker.Speak("EFFROI\t- " + entity.getName() + " est trop effrayé pour se battre.")
            entity.battling = False
            
        elif effect is Effect.PARA:
            speaker.Speak("PARA\t- " + entity.getName() + " est paralysé, impossible d'agir.")
            entity.battling = False

        elif effect is Effect.CURIEUX:
            speaker.Speak("DISTR.\t- " + entity.getName() + " est distrait, perd en précision.")
            # Lose 25% of armor breaker
            entity.turnArmorBreaker -= round(entity.turnArmorBreaker * 25 / 100)

        elif effect is Effect.POISON:
            # Hit 20% of entity current life
            dmg = round(entity.life * 20 / 100)
            speaker.Speak("POISON\t- " + entity.getName() + " est empoisonné, et perd " + str(dmg) + "PV.")
            entity.Hurt(dmg)

        elif effect is Effect.FEU:
            entity.turnDamage += 6

        elif effect is Effect.GEL:
            speaker.Speak("GEL\t- " + entity.getName() + " est gelé. Ne peut plus attaquer --o--")
            entity.processAttack = False

        elif effect is Effect.FATIGUE:
            speaker.Speak("FATIGUE\t- " + entity.getName() + " est fatigué. N'est pas prêt d'utiliser son spécial.")
            entity.processSpecial = False

class BattleContext:

    battle = False
    horde = []

    def __init__(self):
        return

    def DefineHordeGroup(self, gameMaster):

        adventurerPods = 0
        for adventurer in gameMaster.advEnroll:
            adventurerPods += adventurer.pods

        hordePods = 0
        # create a random enemy group, based on the pods system
        # hordePods in range(advPods - 3, advPods + 3) 
        while(hordePods < adventurerPods):
            monster = tools.CopyEntity(tools.RandomElement(gameMaster.horde))

            newHordePods = hordePods + monster.pods
            # Don't accept enemy which are too strong
            if newHordePods > adventurerPods + 3:
                continue

            hordePods = newHordePods
            self.horde.append(monster)

        return self.horde

    def ToDefault(self):
        self.battle = False
        self.horde.clear()