from enum import Enum
from GameMaster import GameMaster
import item
import tools, time, speaker

from battleSystem import Effect


class Target(Enum):
    NONE = 0
    NEXT = 1
    RANDOM = 2
    ALL = 3

class Role:
    # GAMEMASTER INFO
    turn = 0

    # ENTITY STAT
    turnDamage , baseDamage = 0, 0
    turnCritChance, baseCritChance = 0, 0

    turnArmor, baseArmor = 0, 0
    turnArmorBreaker, baseArmorBreaker = 0, 20

    life, maxLife = 0, 0

    specialDice = 0

    coins = 10
    pods = 0

    # ACTION BOOLEAN
    specialAttack, battling = False, True
    processSpecial, processAttack = True, True

    # EFFECT
    effectTurn = 0
    effect = Effect.NEUTRE


    def __init__(self, gameMaster, armor, inventory, life, special, adventurer, pods, name):
        self.gameMaster = gameMaster
        self.turnArmor = self.baseArmor = armor[0]
        self.turnArmorBreaker = self.baseArmorBreaker = armor[1]
        self.life = self.maxLife = life
        self.special = special
        self.adventurer = adventurer
        self.pods = pods
        self.name = name
        self.inventory = inventory

    def __str__(self):
        if self.Alive():
            effect = ": " + self.effect.name + "\n"

            bonusDamage = self.turnDamage + self.baseDamage
            if bonusDamage > 0: strenght = "\t Force+: " + str(bonusDamage)
            else: strenght = ""

            armor = "\t Armure: " + str(self.turnArmor) + "/" + str(self.baseArmor)

            if self.inventory.Empty(): inventory = ""
            else: inventory = "\n" + str(self.inventory)

            return self.getName() + effect + "    PV: " + str(self.life) + "/" + str(self.maxLife) + armor + strenght + inventory

        return self.getName() + ": mort"

    def OnBattleBegins(self):

        self.turn = 0

        if self.adventurer:
            self.enemies = self.gameMaster.hordeGroup
            self.allies = self.gameMaster.advGroup
        else:
            self.enemies = self.gameMaster.advGroup
            self.allies = self.gameMaster.hordeGroup

    def getName(self):
        return self.name

    def Play(self):

        self.turnArmor = self.baseArmor

        # POTION
        self.UsePotion()

        # EFFECT 
        Effect.Undergo(self, self.effect)

        if not self.battling or self.life <= 0:
            self.turn += 1
            self.EndTurn()
            return

        # SPECIAL
        if self.processSpecial:

            if not self.specialAttack:
                self.Special()

            if (not self.gameMaster.Fighting()): # Special could end the fight
                return

        # TARGET
        targetKey, target = tools.RandomItem(self.enemies)

        # ATTACK
        if self.processAttack:

            hit = self.Attack(target)
            # SPECIAL bis
            if hit[0] and self.specialAttack:
                self.SpecialAttack(hit[1])

        # TURN END
        self.gameMaster.AssertEntityDead(targetKey, target)

        self.turn += 1
        self.EndTurn()

        return

    def ArmorBreak(self, target):
        armorBreaker = self.turnArmorBreaker
        breakResult = tools.RollDice(1, armorBreaker)
        crit = self.turnCritChance + self.baseCritChance
        if (breakResult > target.turnArmor):
            return True, (breakResult >= self.turnArmorBreaker - crit)

        return False, False

    def SelectWeapon(self):
        return tools.RandomElement(self.inventory.Weapons)

    def Special(self):
        return

    def Attack(self, target):
        # Try break ennemy armor
        armorBreak, critical = self.ArmorBreak(target)
        if armorBreak:
            # Compute damage
            weapon = self.SelectWeapon()
            damage, effect = weapon.Use(self.specialDice)
            damage += self.baseDamage + self.turnDamage

            if critical:
                damage *= 2
                speaker.Speak("CRIT.\t- " + self.getName() + " fait une attaque critique contre " + target.getName() + " avec son arme " + weapon.name + ". " + str(damage) + " dégâts causés.")
            else:
                speaker.Speak("ATTAQUE\t- " + self.getName() + " attaque " + target.getName() + " avec son arme " + weapon.name + ". " + str(damage) + " dégâts causés.")

            # EFFECT
            Effect.Apply(self, target, self.enemies, self.allies, damage, effect)
            # Assert damage is not negative
            damage = max(damage, 0)
            # HURT
            target.Hurt(damage)

            return True, target
        else:
            speaker.Speak("ECHEC\t- L'attaque de " + self.getName() + " échoue sur " + target.getName())
            return False, None

    def SpecialAttack(self, target):
        return

    def Hurt(self, damage):
        self.life -= damage
        self.life = max(self.life, 0)

        if (not self.Alive()):
            speaker.Speak("MORT\t- " + self.getName() + " est mort...")
            self.Dying()

    def Heal(self, heal):
        self.life += heal
        self.life = min(self.life, self.maxLife)

    def GetEffected(self, effect, origin = None):
        if effect is not Effect.NEUTRE and self.effect is Effect.NEUTRE:
            if origin is not None: 
                speaker.Speak("EFFET\t- " + self.getName() + " est affecté par l'effet " + effect.name + " de " + origin + "!")
            self.effect = effect
            self.effectTurn = Effect.GetTurn(effect)

    def EndTurn(self):
        self.battling = self.processAttack = self.processSpecial = True
        self.specialDice = 0
        self.turnDamage = self.baseDamage
        self.turnArmorBreaker = self.baseArmorBreaker

        self.effectTurn -= 1
        if self.effectTurn <= 0:
            self.effect = Effect.NEUTRE

    def Alive(self):
        return self.life > 0

    def Dying(self):
        return

    def GiveItem(self, item):
        self.inventory.AddItem(item)

    def UsePotion(self):
        
        use, index = -1, 0
        for potion in self.inventory.Potions:
            if potion.used:
                u_potion = potion
                use = index
                break
            elif potion.UseCondition(self):
                u_potion = potion
                use = index

            index += 1

        if use > -1:
            u_potion.Use(self)
            if u_potion.lifeTime <= 0:
                self.inventory.Potions.pop(use)

    def Reset(self):
        self.inventory = item.Inventory()

    def ToJson(self):
        # Copy class dict and remove name because don't need
        data = self.__dict__.copy()
        data.pop("name")
        return data

    def FromJson(gameMaster, name, input):
        # Find the type with name, default is Role
        module = __import__("role")
        _class_ = getattr(module, name, Role)
        armor, life, special = (input.pop("armor"), input.pop("armorBreaker", 20)), input.pop("life"), input.pop("special")
        adventurer = input.pop("adventurer", True)
        pods = input.pop("pods", 3)

        inventory = item.Inventory()

        for itm in input.values():
            inventory.AddItem(gameMaster.GetItem(itm))

        return _class_(gameMaster, armor, inventory, life, special, adventurer, pods, name)


class Mage(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name = ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Mage")

    def Special(self):
        # Fireball
        if (tools.RollDice(1, 20) >= 18):
            damage = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Le mage lance un sort de feu, ça devient chaud ! Tous les ennemies subissent " + str(damage) + " dommages !")
            tools.GlobalAttack(self.enemies, damage)

        return Target.NONE, 0

class Voleur(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Voleur")

    def Special(self):
        #Sneak attack
        if (tools.RollDice(1, 20) >= 16):
            speaker.Speak("SPECIAL\t- Rogue prépare une attaque surprise, ça va être douloureux pour la cible !")
            self.specialDamage = tools.RollDice(self.special[0], self.special[1])

class Guerrier(Role):
    processedHeal = False

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Guerrier")

    def __str__(self):
        return super().__str__() + "\n    Soin utilisé: " + str(self.processedHeal)

    def OnBattleBegins(self):
        super().OnBattleBegins()
        processedHeal = False
        
    def Dying(self):
        #Second Win
        if (not self.processedHeal):
            speaker.Speak("SPECIAL\t- Warrior ne se sent pas bien, il puisse de la force dans son mental et récupère 10PV!")
            self.Heal(self.special[1])
            self.processedHeal = True
        

    def Special(self):
        return

class Chasseur(Role):

    ignoreDef = False

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        self.baseArmor = armor
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Chasseur")

    def __str__(self):
        return super().__str__() + "\n    Camouflage: " + str(self.ignoreDef)

    def Special(self):
        # Camouflage
        if (tools.RollDice(1, 20) >= 13):
            armor = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Hunter se cache dans le champ de bataille ! Les ennemies ne peuvent l'éviter, et il gagne " + str(armor) + " d'armure!")
            self.ignoreDef = True
            self.turnArmor += armor

    def ArmorBreak(self, target):
        armorBreak = tools.RollDice(1, 20)
        if (self.ignoreDef or armorBreak > target.armor):
            return True, armorBreak == 20

        return False, False

class Mercenaire(Role):
     def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Mercenaire")
 
     def Special(self):
         # Second hit
         if (tools.RollDice(1, 20) >= 15):
            targetKey, target = tools.RandomItem(self.enemies)
            speaker.Speak("SPECIAL\t- Le Mercenaire ne fait pas son travail à moitié ! Il prépare une double attaque !")
            if self.processAttack:
                self.Attack(target)

class Marchant(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Marchant")

    def Special(self):
        if(tools.RollDice(1, 20) >= 10):
            money = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Le marchand gère un petit commerce. Vous gagné " + str(money) + " pièces ! Mais comment fait-il ?")
            self.coins += money
 
class SansAbri(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "SansAbri")

    def Special(self):
        if(tools.RollDice(1,20) >= 5):
            heal = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Le sans-abri est très débrouillard, il se remet d'aplomb avec ce qui l'entoure ! Il regagne " + str(heal) + "PV!")
            self.Heal(heal)

class Lithologue(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Lithologue")

    def Special(self):
        if(tools.RollDice(1,20) >= 15):
            victim = tools.RandomElement(list(self.enemies.values()))
            speaker.Speak("SPECIAL\t- Le lithologue concentre l'énergie des pierres, et la redirige vers " + victim.getName() + ".")
            victim.GetEffected(Effect.PARA, self.getName())



class Orc(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Orc")

class Grick(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        self.specialAttack = True
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Grick")

    def SpecialAttack(self, target):
        damage = tools.RollDice(self.special[0], self.special[1])
        speaker.Speak("SPECIAL\t- Grick attaque encore en causant " + str(damage) + " de dégâts supplémentaires.")
        target.Hurt(damage)

class Banshee(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Banshee")

    def Special(self):
        if (tools.RollDice(1, 20) >= 15):
            target = tools.RandomItem(self.enemies)[1]
            speaker.Speak("SPECIAL\t- Banshee terrifie " + target.getName())
            target.GetEffected(Effect.EFFROI)

class Bandit(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Bandit")

    def Special(self):
        '''Steal an enemies item'''
        if tools.RollDice(1, 20) >= 20:
            enemy = tools.RandomItem(self.enemies)[1]
            if not enemy.inventory.Empty():
                self.inventory.AddItem(enemy.inventory.PopRandom())

class Croyant(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Croyant")

    def Special(self):
        if(tools.RollDice(1,20) >= 10):
            speaker.Speak("SPECIAL\t- Le croyant commence à réciter une incantation. Cependant il ne se produit rien.")

class Mechancenaire(Role):
     def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Mechancenaire")
 
     def Special(self):
         # Second hit
         if (tools.RollDice(1, 20) >= 15):
            targetKey, target = tools.RandomItem(self.enemies)
            speaker.Speak("SPECIAL\t- Le méchant mercenaire a la rogne ! Il prépare une double attaque !")
            if self.processAttack:
                self.Attack(target)

class Niffleur(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Niffleur")

    def Special(self):
        if tools.RollDice(1, 20) >= 12:
            bonusArmor = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Niffleur améliore son aura royale, et gagne " + str(bonusArmor) + " d'armure!")
            self.turnArmor += bonusArmor
                    
class Treiish(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Treiish")
    
    def Play(self):

        self.turnArmor = self.baseArmor

        # POTION
        self.UsePotion()

        # EFFECT 
        Effect.Undergo(self, self.effect)

        if self.life <= 0:
            self.turn += 1
            self.EndTurn()
            return

        # SPECIAL
        if self.processSpecial:

            if not self.specialAttack:
                self.Special()

            if (not self.gameMaster.Fighting()): # Special could end the fight
                return

        # ASSERT BATTLE STATE
        if not self.battling:
            self.turn += 1
            self.EndTurn()
            return

        # TARGET
        targetKey, target = tools.RandomItem(self.enemies)

        # ATTACK
        if self.processAttack:

            hit = self.Attack(target)
            # SPECIAL bis
            if hit[0] and self.specialAttack:
                self.SpecialAttack(hit[1])

        # TURN END
        self.gameMaster.AssertEntityDead(targetKey, target)

        self.turn += 1
        self.EndTurn()

        return

    def Special(self):
        if tools.RollDice(1, 20) >= 12:
            if self.effect is not Effect.NEUTRE:
                speaker.Speak("SPECIAL\t- La sorcière Treiish est insensible aux malédictions. L'effet " + self.effect.name + " est supprimé.")
                self.effect = Effect.NEUTRE
                self.battling = self.processAttack = self.processSpecial = True


class Libraire(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Libraire")

    def Special(self):
        if(tools.RollDice(1,20) >= 17):
            speaker.Speak("SPECIAL\t- Le libraire appelle à l'aide. Un être malvaillant le rejoint.")
            self.gameMaster.enemyJoin = "Croyant"





####class NewHero(Role):
####    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
####        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "NewHero")
####
####    def Special(self):
####        if(tools.RollDice(1,20) > 15):
####            speaker.Speak("SPECIAL\t-")