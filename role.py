from enum import Enum
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

    # ACTION BOOLEAN
    specialAttack, battling = False, True
    processSpecial, processAttack = True, True

    # EFFECT
    effectTurn = 0
    effect = Effect.NEUTRAL


    def __init__(self, gameMaster, armor, inventory, life, special, adventurer, common, name):
        self.gameMaster = gameMaster
        self.turnArmor = self.baseArmor = armor[0]
        self.turnArmorBreaker = self.baseArmorBreaker = armor[1]
        self.life = self.maxLife = life
        self.special = special
        self.adventurer = adventurer
        self.common = common
        self.name = name
        self.inventory = inventory

    def __str__(self):
        if self.Alive():
            effect = ": " + self.effect.name + "\n"

            bonusDamage = self.turnDamage + self.baseDamage
            if bonusDamage > 0: strenght = "\t Strenght+: " + str(bonusDamage)
            else: strenght = ""

            armor = "\t Armor: " + str(self.turnArmor) + "/" + str(self.baseArmor)

            if self.inventory.Empty(): inventory = ""
            else: inventory = "\n" + str(self.inventory)

            return self.getName() + effect + "    Life: " + str(self.life) + "/" + str(self.maxLife) + armor + strenght + inventory

        return self.getName() + ": Dead"

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
                speaker.Speak("CRIT.\t- " + self.getName() + " critical strikes " + target.getName() + " with their " + weapon.name + ". " + str(damage) + " damages dealed.")
            else:
                speaker.Speak("ATTACK\t- " + self.getName() + " attacks " + target.getName() + " with their " + weapon.name + ". " + str(damage) + " damages dealed.")

            # EFFECT
            Effect.Apply(self, target, self.enemies, self.allies, damage, effect)
            # Assert damage is not negative
            damage = max(damage, 0)
            # HURT
            target.Hurt(damage)

            return True, target
        else:
            speaker.Speak("FAIL\t- " + self.getName() + "'s attack fail on " + target.getName())
            return False, None

    def SpecialAttack(self, target):
        return

    def Hurt(self, damage):
        self.life -= damage
        self.life = max(self.life, 0)

        if (not self.Alive()):
            speaker.Speak("DEATH\t- " + self.getName() + " is dead...")
            self.Dying()

    def Heal(self, heal):
        self.life += heal
        self.life = min(self.life, self.maxLife)

    def GetEffected(self, effect, origin = None):
        if effect is not Effect.NEUTRAL and self.effect is Effect.NEUTRAL:
            if origin is not None: 
                speaker.Speak("EFFECT\t- " + self.getName() + " is effected by " + effect.name + " from " + origin + " !")
            self.effect = effect
            self.effectTurn = Effect.GetTurn(effect)

    def EndTurn(self):
        self.battling = self.processAttack = self.processSpecial = True
        self.specialDice = 0
        self.turnDamage = self.baseDamage
        self.turnArmorBreaker = self.baseArmorBreaker

        self.effectTurn -= 1
        if self.effectTurn <= 0:
            self.effect = Effect.NEUTRAL

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
        adventurer, common = input.pop("adventurer", True), input.pop("common", True)

        inventory = item.Inventory()

        for itm in input.values():
            inventory.AddItem(gameMaster.GetItem(itm))

        return _class_(gameMaster, armor, inventory, life, special, adventurer, common, name)


class Mage(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name = ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "Mage")

    def Special(self):
        # Fireball
        if (tools.RollDice(1, 20) >= 18):
            damage = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Mage cast a fire balls spell, the atmoshpere becomes hot ! Enemies will recieve " + str(damage) + " damages !")
            tools.GlobalAttack(self.enemies, damage)

        return Target.NONE, 0

class Rogue(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "Rogue")

    def Special(self):
        #Sneak attack
        if (tools.RollDice(1, 20) >= 16):
            speaker.Speak("SPECIAL\t- Rogue prepare a sneak attack, it will be painful for his target !")
            self.specialDamage = tools.RollDice(self.special[0], self.special[1])

class Warrior(Role):
    processedHeal = False

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "Warrior")

    def __str__(self):
        return super().__str__() + "\n    Healed: " + str(self.processedHeal)

    def OnBattleBegins(self):
        super().OnBattleBegins()
        processedHeal = False
        
    def Dying(self):
        #Second Win
        if (not self.processedHeal):
            speaker.Speak("SPECIAL\t- Warrior doesn't want to give up, he drinks a good coffee and heals 10 HP !")
            self.Heal(self.special[1])
            self.processedHeal = True
        

    def Special(self):
        return

class Hunter(Role):

    ignoreDef = False

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name= ""):
        self.baseArmor = armor
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "Hunter")

    def __str__(self):
        return super().__str__() + "\n    Camouflage: " + str(self.ignoreDef)

    def Special(self):
        # Camouflage
        if (tools.RollDice(1, 20) >= 13):
            armor = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Hunter hides in the battle field ! Enemy can't dodge next attack, and he earns " + str(armor) + " armor !")
            self.ignoreDef = True
            self.turnArmor += armor

    def ArmorBreak(self, target):
        armorBreak = tools.RollDice(1, 20)
        if (self.ignoreDef or armorBreak > target.armor):
            return True, armorBreak == 20

        return False, False

class Orc(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "Orc")

class Grick(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name= ""):
        self.specialAttack = True
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "Grick")

    def SpecialAttack(self, target):
        damage = tools.RollDice(self.special[0], self.special[1])
        speaker.Speak("SPECIAL\t- Grick attacks again with " + str(damage) + " damages.")
        target.Hurt(damage)

class Banshee(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "Banshee")

    def Special(self):
        if (tools.RollDice(1, 20) >= 15):
            target = tools.RandomItem(self.enemies)[1]
            speaker.Speak("SPECIAL\t- Banshee scares " + target.getName())
            target.GetEffected(Effect.SCARY)

class Bandit(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "Bandit")

    def Special(self):
        '''Steal an enemies item'''
        if tools.RollDice(1, 20) >= 16:
            enemy = tools.RandomItem(self.enemies)[1]
            if not enemy.inventory.Empty():
                self.inventory.AddItem(enemy.inventory.PopRandom())

class RareNiffleur(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, common, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, common, "RareNiffleur")

    def Special(self):
        if tools.RollDice(1, 20) >= 12:
            bonusArmor = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- RareNiffleur reinforce its golden aura, and won " + str(bonusArmor) + " bonus armor !")
            self.turnArmor += bonusArmor
                    

