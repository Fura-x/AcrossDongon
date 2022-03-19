from enum import Enum
import speaker, tools
from battleSystem import Effect

class PotionType(Enum):
	NONE = 0
	SOIN = 1		# Give HP to the owner
	FORCE = 2	# Increase owner's damages
	ARMURE = 3		# Increase owner's defense
	SPRAY = 4		# Purify owner's effect, set it to NEUTRAL

class Item:

	def __init__(self, object):
		self.object = object
		return

	def FromJson(name, input):
		# Find class from object
		module = __import__("item")
		__class__ = getattr(module, name)
		return __class__.FromJson(input)

class Potion(Item):
	
	used = False

	def __init__(self, type = PotionType.NONE, value = 0, lifeTime = 1):
		super().__init__("Potion")
		self.type = type
		self.value = value
		self.lifeTime = lifeTime

	def __str__(self):
		if self.used: cursor = "=>"
		else: cursor = ""
		return cursor + self.type.name + "[" + str(self.value) + "|" + str(self.lifeTime) + "]"

	def UseCondition(self, entity):
		if self.type is PotionType.SOIN: # HEAL
			return entity.life <= entity.maxLife*0.4

		elif self.type is PotionType.FORCE: # STRENGHT
			return tools.RollDice(1, 5) == 1

		elif self.type is PotionType.ARMURE: # ARMOR
			return entity.life <= entity.maxLife*0.5

		elif self.type is PotionType.SPRAY: # SPRAY
			return entity.effect is not Effect.NEUTRE and entity.life <= entity.maxLife*0.5

	def Use(self, entity):
		if self.type is PotionType.SOIN: # HEAL
			if not self.used:
			   speaker.Speak("POTION\t- " + entity.getName() + " se soigne avec une potion ! " + str(self.value) + "PV soigné pendant " + str(self.lifeTime) + " tours.")
			else:
				speaker.Speak("POTION\t- " + entity.getName() + " se soigne " + str(self.value) + "PV grâce à sa potion.")
			entity.Hurt(-self.value)

		elif self.type is PotionType.FORCE: # STRENGHT
			if not self.used: 
				speaker.Speak("POTION\t- " + entity.getName() + " utilise une potion de force ! Les dégâts sont augmentés de " + str(self.value) + " pendant " + str(self.lifeTime) + " tours.")
			entity.turnDamage += self.value

		elif self.type is PotionType.ARMURE: # ARMOR
			if not self.used: 
				speaker.Speak("POTION\t- " + entity.getName() + " a besoin de protection ! " + str(self.value) + " d'arumre ajouté pour " + str(self.lifeTime) + " tours.")
			entity.turnArmor += self.value

		elif self.type is PotionType.SPRAY: # SPRAY
			if entity.effect is not Effect.NEUTRE:
				speaker.Speak("POTION\t- " + entity.getName() + " utilise un spray pour se purifier ! " + entity.effect.name + " oublié.")
				entity.effect = Effect.NEUTRE
				entity.effectTurn = 0

		self.used = True
		self.lifeTime -= 1

	def FromJson(input):
		return Potion(PotionType[input["type"]], input["value"], input["lifeTime"])

class Weapon(Item):

	def __init__(self, name, damage, effect):
		super().__init__("Weapon")
		self.name = name
		self.damage = damage
		self.effect = effect

	def __str__(self):
		return self.name + "[" + str(self.damage[0]) + "|" + str(self.damage[1]) + "|" + self.effect[1].name + "]"
		
	def Use(self, specialDice=0):
		# Get random damages value
		dmg = tools.RollDice(self.damage[0] + specialDice, self.damage[1])

		# Get a chance to apply special effect
		effect = Effect.NEUTRE
		if tools.RollDice(1, self.effect[0]) == 1:
			effect = self.effect[1]

		return dmg, effect

	def FromJson(input):
		proba, effect = input.pop("effect", (1, "NEUTRE"))
		effect = Effect[effect]
		return Weapon(input["name"], input["damage"], (proba, effect))

class Inventory:

	selectEnable = True

	def __init__(self):
		self.Potions = []
		self.Weapons = []

	def __str__(self):
		p = "    Inventaire:"

		if not tools.Empty(self.Weapons): p += "\n"

		for weapon in self.Weapons:
			p += "\t" + str(weapon)

		if not tools.Empty(self.Potions): p += "\n"

		for potion in self.Potions:
			p += "\t" + str(potion)

		return p

	def AddItem(self, item):
		# find list from item type
		items = self.GetItems(item.object)

		# 3 item max per object type
		if len(items) >= 3:
			if self.selectEnable:
			    speaker.Speak("Trop de " + item.object + "s dans votre inventaire!")
			    self.SelectAndRemoveItem(item.object)
			else:
				self.PopRandomSpec(item.object)
		
		items.append(item)
		return

	def SelectAndRemoveItem(self, object):
		# Remove an item from inventory, player will chose
		items = self.GetItems(object)

		speaker.Speak()
		speaker.Speak("Choisissez une " + object + " a retirer de votre inventaire : ")

		index, popItem = tools.EnumerateAndSelect(items)
		items.pop(index)

		speaker.Input("Vous avez retiré " + str(popItem) + ".")

	def PopItem(self, index, object):
		# Remove a specific item from inventory
		items = self.GetItems(object)

		if index >= len(items) :
			return None
		return items.pop(index)

	def PopRandom(self):
		# Remove a random item from inventory
		lists = []
		if not tools.Empty(self.Weapons):
			lists.append(self.Weapons)
		if not tools.Empty(self.Potion):
			lists.append(self.Potions)

		if tools.Empty(lists):
			return None

		items = tools.RandomElement(lists)
		return tools.PopRandomItem(items)

	def PopRandomSpec(self, object):
		# Remove a random item according to its type
		items = self.GetItems(object)

		if len(items) > 0:
			return tools.PopRandomItem(items)

	def GetItems(self, object):
		return getattr(self, object + "s")

	def Empty(self):
		return (len(self.Potions) == 0) and (len(self.Weapons) == 0)

	def clear(self):
		self.Potions.clear()
		self.Weapons.clear()