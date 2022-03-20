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
        self.inventory.selectEnable = self.adventurer

    def __str__(self):
        if self.Alive():
            effect = ": " + self.effect.name + "\n"

            bonusDamage = self.turnDamage + self.baseDamage
            if bonusDamage > 0: strength = "\t Force+: " + str(bonusDamage)
            else: strength = ""

            armor = "\t Armure: " + str(self.turnArmor) + "/" + str(self.baseArmor)

            if self.inventory.Empty(): inventory = ""
            else: inventory = "\n" + str(self.inventory)

            return self.getName() + effect + "    PV: " + str(self.life) + "/" + str(self.maxLife) + armor + strength + inventory

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

            if weapon is None:
                speaker.Speak("ECHEC\t- L'attaque de " + self.getName() + " échoue sur " + target.getName())
                return False, None

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
        if damage is None:
            damage = 0

        if damage > self.life:
            damage = self.life

        self.life -= damage

        if (not self.Alive()):
            speaker.Speak("MORT\t- " + self.getName() + " est mort...")
            self.Dying()

        return damage

    def Heal(self, heal):
        if heal is None:
            heal = 0

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
            speaker.Speak("SPECIAL\t- Le voleur prépare une attaque surprise, ça va être douloureux pour la cible !")
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
            speaker.Speak("SPECIAL\t- Le guerrier est sur le point de mourir, il puise de la force dans son mental et récupère 10PV!")
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
        if (self.ignoreDef or armorBreak > target.turnArmor):
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

class HommePoisson(Role):

    charge = 0

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Homme poisson")

    def OnBattleBegins(self):
        self.charge = 0
        return super().OnBattleBegins()

    def Special(self):
        if(tools.RollDice(1,20) >= 6):
            speaker.Speak("SPECIAL\t- L'homme poisson absorbe l'humidité de l'air.")
            self.charge += 1
            if self.charge == 3:
                speaker.Speak("SPECIAL\t- Il a absorbé suffisamment d'humidité, il fait déferler un énorme torrent sur les ennemies!")
                speaker.Speak("ATTAQUE\t- Tous les ennemis subissent 30 de dégâts.")
                tools.GlobalAttack(self.enemies, 30)
                self.charge = 0

class Vampire(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Vampire")

    def Special(self):
        if(tools.RollDice(1,20) >= 16):
            damage = tools.RollDice(self.special[0], self.special[1])
            victim = tools.RandomItem(self.enemies)[1]
            speaker.Speak("SPECIAL\t- Le vampire est assoifé de sang ! Il se jette sur " + victim.getName() + " !")
            damage = victim.Hurt(damage)
            speaker.Speak("DRAIN\t- Le vampire a aspiré " + str(damage) + "PV.")
            self.Heal(damage)
            
class Nomade(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Nomade")

    def Special(self):
        for ally in self.allies.values():
            if tools.Empty(ally.inventory.Potions):
                potion = self.gameMaster.GetRandomItem("Potion")
                if ally.getName() != "Nomade":
                    speaker.Speak("SPECIAL\t- Le nomade remarque que " + ally.getName() + " n'a pas de potions. Il lui donne " + str(potion) + " pour le protéger !")
                else:
                    speaker.Speak("SPECIAL\t- Le nomade n'a plus de potions. Il sort " + str(potion) + " de son sac pour se protéger !")
                ally.GiveItem(potion)



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
                item = enemy.inventory.PopRandom()

                if item is not None:
                    speaker.Speak("SPECIAL\t- Le bandit dérobe l'item " + str(item) + " à " + enemy.getName() + ".")
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

class Pyrahna(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        self.specialAttack = True
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Pyrahna")
    
    def SpecialAttack(self, target):
        if(tools.RollDice(1,20) >= 5):
            count = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Le pyrahna s'est accroché à " + target.getName() + ". Il le mâchouille encore " + str(count) + " fois.")
            weapon = self.SelectWeapon()
            for i in range(count):
                damage = weapon.Use()[0]
                speaker.Speak("ATTAQUE\t- Le pyrahna fait subir " + str(damage) + " dégâts à " + target.getName())
                target.Hurt(weapon.Use()[0])

class Gobelin(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Gobelin")

    def Special(self):
        if(tools.RollDice(1,20) >= 15):
            itm = self.gameMaster.GetRandomItem()
            speaker.Speak("SPECIAL\t- Le gobelin a fouiné le champs de bataille et a trouvé un objet : " + str(itm))
            self.inventory.AddItem(itm)

class Scorpion(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        self.specialAttack = True
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Scorpion")

    def SpecialAttack(self, target):
        if(tools.RollDice(1,20) >= 12) and target.effect is Effect.POISON:
            speaker.Speak("SPECIAL\t- Le scorpion est excité par le poison qui se propage en vous. Il attaque encore !")
            damage = tools.RollDice(self.special[0], self.special[1]) * 2
            speaker.Speak("CRIT.\t- Scorpion attaque " + target.getName() + " avec son Dard envenimé. " + str(damage) + " dégâts causés.")
            target.Hurt(damage)

class Mordu(Role):

    hurtCount = 0

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Mordu")

    def Hurt(self, damage):

        self.hurtCount += 1
        revive = tools.RollDice(1, 20) > (20 - self.hurtCount)

        if not revive and self.effect is Effect.NEUTRE:
            speaker.Speak("ECHEC\t- Le mordu semble immortel.")
            return 0

        speaker.Speak("ATTAQUE\t- Le mordu n'était plus en état de revivre. Votre attaque lui est fatal !")
        super().Hurt(damage)

    def Special(self):
        if(tools.RollDice(1,20) >= 15):
            speaker.Speak("SPECIAL\t- Le mordu change de bras pour se battre.")

class Niffleur(Role):

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Niffleur")

    def Special(self):
        if tools.RollDice(1, 20) >= 12:
            bonusArmor = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Niffleur améliore son aura royale, et gagne " + str(bonusArmor) + " d'armure!")
            self.turnArmor += bonusArmor

class Scientist(Role):

    invoked = False

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Dr.Octavia Puzz")


    def Play(self):
        if not self.invoked:
            speaker.Speak("SPECIAL\t- La scientifique Ocatavia Puzz jette trois fioles sur le terrain. Des grosses boules bleus en sortent !")
            self.gameMaster.enemyJoin.append("Blob")
            self.gameMaster.enemyJoin.append("Blob")
            self.gameMaster.enemyJoin.append("Blob")
            self.invoked = True

        
        return super().Play()

    def Special(self):
        if tools.RollDice(1,20) >= 18:
            speaker.Speak("SPECIAL\t- Doctresse Octavia Puzz manipule la matière devant vos yeux, et crée une nouvelle entité !")
            self.gameMaster.enemyJoin.append("Blob")


class Blob(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Blob")

    def Dying(self):
        speaker.Speak("SPECIAL\t- Le blob est sur le point de disparaître, mais au lieu de ça il explose et se divise en deux !")
        self.gameMaster.enemyJoin.append("Mini blob")
        self.gameMaster.enemyJoin.append("Mini blob")
        
class MiniBlob(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Mini blob")
                    
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
            self.gameMaster.enemyJoin.append("Croyant")

class Moldrick(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Moldrick")

    def Special(self):
        if(tools.RollDice(1,20) >= 17):
            damage = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- Le capitaine Moldrick sort toute artillerie, et mitraille votre équipe ! " + str(damage) + " dégâts infligés.")
            tools.GlobalAttack(self.enemies, damage)

            if(tools.RollDice(1, 20) >= 10):
                itm = self.gameMaster.GetRandomItem()
                speaker.Speak("SPECIAL\t- L'attaque du capitaine a secoué le terrain, il remarque alors un objet qu'il dérobe : " + str(itm))
                self.inventory.AddItem(itm)

class Nessie(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Nessie")

class Illusos(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Illusos")

    def Hurt(self, damage):

        enemy = self.gameMaster.currentEntity
        if self is not enemy and tools.RollDice(1, 20) >= 12:
            repost = tools.RollDice(self.special[0], self.special[1])
            speaker.Speak("SPECIAL\t- L'Illusos vous a trompé avec une illusion !")
            speaker.Speak("ATTAQUE\t- Il contre-attaque et inflige " + str(repost) + " dégâts à " + enemy.getName() + ".")
            enemy.Hurt(repost)
            return 0

        super().Hurt(damage)

class HommeDesSables(Role):

    invoked = False

    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Homme des sables")

    def Special(self):
        if not self.invoked and tools.RollDice(1,20) >= 19:
            speaker.Speak("SPECIAL\t- L'homme des sables pousse un cri puissant, et frappe le sol à plusieurs reprises...")
            speaker.Speak("???\t- Le sol tremble, le sable s'envole. Un gigantesque ver sort du sol derrière l'homme des sables !")
            self.gameMaster.enemyJoin.append("Ver des sables")
            self.invoked = True

class VerDesSables(Role):
    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "Ver des sables")


####class NewHero(Role):
####    def __init__(self, gameMaster, armor, weapon, life, special, adventurer, pods, name= ""):
####        super().__init__(gameMaster, armor, weapon, life, special, adventurer, pods, "NewHero")
####
####    def Special(self):
####        if tools.RollDice(1,20) >= 15:
####            speaker.Speak("SPECIAL\t-")