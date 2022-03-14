from enum import Enum
import speaker, tools
from battleSystem import Effect

class PotionType(Enum):
	NONE = 0
	HEAL = 1		# Give HP to the owner
	STRENGHT = 2	# Increase owner's damages
	ARMOR = 3		# Increase owner's defense
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
		if self.type is PotionType.HEAL: # HEAL
			return entity.life <= entity.maxLife*0.4

		elif self.type is PotionType.STRENGHT: # STRENGHT
			return tools.RollDice(1, 5) == 1

		elif self.type is PotionType.ARMOR: # ARMOR
			return entity.life <= entity.maxLife*0.5

		elif self.type is PotionType.SPRAY: # SPRAY
			return entity.effect is not Effect.NEUTRAL and entity.life <= entity.maxLife*0.5

	def Use(self, entity):
		if self.type is PotionType.HEAL: # HEAL
			if not self.used:
			   speaker.Speak("POTION\t- " + entity.getName() + " heals with a potion ! " + str(self.value) + "HP healed for " + str(self.lifeTime) + " turns.")
			else:
				speaker.Speak("POTION\t- " + entity.getName() + " heals " + str(self.value) + "HP from used potion.")
			entity.Hurt(-self.value)

		elif self.type is PotionType.STRENGHT: # STRENGHT
			if not self.used: 
				speaker.Speak("POTION\t- " + entity.getName() + " uses a strenght potion ! " + str(self.value) + "DMG increased for " + str(self.lifeTime) + " turns.")
			entity.specialDamage += self.value

		elif self.type is PotionType.ARMOR: # ARMOR
			if not self.used: 
				speaker.Speak("POTION\t- " + entity.getName() + " needs protection ! " + str(self.value) + "ARMOR added for " + str(self.lifeTime) + " turns.")
			entity.armor += self.value

		elif self.type is PotionType.SPRAY: # SPRAY
			if entity.effect is not Effect.NEUTRAL:
				speaker.Speak("POTION\t- " + entity.getName() + " use a spray to heal from effect ! " + entity.effect.name + " canceled.")
				entity.effect = Effect.NEUTRAL
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
		effect = Effect.NEUTRAL
		if tools.RollDice(1, self.effect[0]) == 1:
			effect = self.effect[1]

		return dmg, effect

	def FromJson(input):
		proba, effect = input.pop("effect", (1, "NEUTRAL"))
		effect = Effect[effect]
		return Weapon(input["name"], input["damage"], (proba, effect))

class Inventory:

	def __init__(self):
		self.Potions = []
		self.Weapons = []

	def __str__(self):
		p = "    Inventory:"

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
			speaker.Speak("Too many " + item.object + "s in their inventory !")
			self.RemoveItem()
		
		items.append(item)
		return

	def RemoveItem(self, item):
		# Remove an item from inventory, player will chose
		items = self.GetItems(item.object)

		speaker.Speak()
		speaker.Speak("Chose a " + item.object + " to remove from inventory : ")

		index, popItem = tools.EnumerateAndSelect(items)
		items.pop(index)

		speaker.Input("You removed " + str(popItem) + ".")

	def PopItem(self, index, object):
		# Remove a specific item from inventory
		items = self.GetItems(object)

		if index >= len(items) :
			return None
		return items(index)

	def PopRandom(self):
		# Remove an random item from inventory
		lists = []
		if len(self.Weapons) > 0:
			lists.append(self.Weapons)
		if len(self.Potions) > 0:
			lists.append(self.Potions)

		items = tools.RandomElement(lists)
		return items.pop(tools.randomElement(items))

	def GetItems(self, object):
		return getattr(self, object + "s")

	def Empty(self):
		return (len(self.Potions) == 0) and (len(self.Weapons) == 0)

	def clear(self):
		self.Potions.clear()
		self.Weapons.clear()