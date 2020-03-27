from util import log
import random

class Building:

	def __init__(self, name, price):
		self.name = name
		self.owner = None
		self.base_price = price
		self.cur_price = 0
		# level 0 means pure land, level 1 means house, level 2 means hotel
		self.level = 0

	def set_owner(self, player):
		self.cur_price += self.base_price
		self.owner = player

	def improve(self):
		if self.level <= 1:
			self.cur_price += self.base_price
			self.level += 1

	def sell(self, other=None):
		self.owner = other


class Player:

	def __init__(self, num, buying_strategy, upgrading_strategy, trading_strategy):
		self.num = num  # player id
		self.position = 0
		self.consecutiveDoubles = 0
		self.consecutive_not_Doubles = 0
		self.at_jail = False
		self.cash = 200
		self.income = 100
		self.building = []
		self.land = 0
		self.house = 0
		self.hotel = 0
		self.bankrupt_status = False
		self.b_strategy = buying_strategy
		self.u_strategy = upgrading_strategy
		self.t_strategy = trading_strategy

	def find_min_house_to_sell(self, c):
		target = None
		price = float("inf")
		if self.t_strategy == 0:
			decision = random.randint(0, 1)  # either buy or not buy
		elif self.t_strategy == 1:
			decision = 0.5
		elif self.t_strategy == 2:
			constant = 500
		for building in self.building:
			print(building.base_price * 0.9 + self.cash, c, building.base_price)
			if (self.t_strategy !=2 and building.base_price * decision + self.cash >= c and building.base_price < price) or\
					(self.t_strategy == 2 and self.cash >= constant and building.base_price < price):
				price = building.base_price
				target = building
		return target

	def go_to_jail(self):
		self.at_jail = True
		self.position = Board.TILES_JAIL[0]

	def go_out_of_jail(self):
		self.at_jail = False
		self.position = Board.TILES_NONE[1]

	def buy_building(self, building):
		assert isinstance(building, Building)

		if building.owner is None:  # the player can buy the building
			# based on the player's strategy, decide how much cash could be used to buy buildings
			if self.b_strategy == 0:
				decision = random.randint(0, 1) # either buy or not buy
			elif self.b_strategy == 1:
				decision = 0.5
			elif self.b_strategy == 2:
				constant = 500
			if (self.b_strategy != 2 and self.cash * decision >= building.base_price) or\
					(self.b_strategy == 2 and self.cash >= constant and self.cash >= building.base_price):
				self.cash -= building.base_price
				self.building.append(building)
				building.set_owner(self)
				self.land += 1
				log.write("player {0} buys a land on {1}, costs {2}, currently has {3} cash.\n".format(self.num, building.name, building.base_price, self.cash))
			else:
				return False
		else:
			if self.u_strategy == 0:
				decision = random.randint(0, 1) # either buy or not buy
			elif self.u_strategy == 1:
				decision = 0.5
			elif self.u_strategy == 2:
				constant = 500
			if building.owner.num == self.num:  # the player is the owner of the building
				if self.u_strategy == 0:
					decision = random.randint(0, 1)  # either build or not build
				elif self.u_strategy == 1:
					decision = 0.5
				elif self.u_strategy == 2:
					constant = 500   # pre-set
				if (self.u_strategy != 2 and self.cash * decision >= building.base_price) or \
						(self.u_strategy == 2 and self.cash >= constant and self.cash >= building.base_price):
					if building.level == 0:
						self.cash -= building.base_price
						self.land -= 1
						self.house += 1
						building.improve()
						log.write('player {0} upgrades the land on {1} to a house, costs {2}, currently has {3} cash.\n'.format(self.num, building.name, building.base_price, self.cash))
					elif building.level == 1:
						self.cash -= building.base_price
						self.house -= 1
						self.hotel += 1
						building.improve()
						log.write(
							'player {0} upgrades the house on {1} to a hotel, costs {2}, currently has {3} cash.\n'.format(
								self.num, building.name, building.base_price, self.cash))

				else:
					return False
			else:
				raise PermissionError("You have no right to upgrade the property.\n")

		return True

	def fine_money(self, fined, other=None):
		if self.cash < fined:
			building_to_sell = self.find_min_house_to_sell(fined)
			# print(self.building)
			if building_to_sell is not None:
				building_to_sell.sell()
				self.building.remove(building_to_sell)
				sell_price = int(building_to_sell.cur_price * 0.9)
				self.cash += sell_price
				log.write("player {0} sells the property on {1} to the bank for {2} cash, currently has {3}.\n".format(self.num, building_to_sell.name, sell_price, self.cash))

		self.cash -= fined
		if other is not None:
			other.cash += fined
			log.write(
				"player {0} lands on player {1}'s property, player {0} gives {2} to player {1}, now player {0} has {3}, player {1} has {4}.\n".format(self.num, other.num, fined, self.cash, other.cash))
		else:
			log.write("player {0} is fined {1} by the country, currently has {2}.\n".format(self.num, fined, self.cash))

	def move(self, board, dice1, dice2):
		# Determine whether to go to jail due to double throws
		if not self.at_jail:
			if dice1 == dice2:
				# Add one to the number of consecutive doubles
				self.consecutiveDoubles += 1

				# Signal to go to jail if 3 doubles in a row
				if self.consecutiveDoubles >= 3:
					self.go_to_jail()
					# Reset consecutive throws
					self.consecutiveDoubles = 0
					log.write("player {0} goes to jail because of 3 consecutive doubles.\n".format(self.num))
					return
			else:
				# Reset consecutive doubles every time different numbers are roled
				self.consecutiveDoubles = 0

			# Calculate new position, overflow if necessary
			newPosition, pass_go = self.getNewPosition(dice1 + dice2, board)

			# gain money when pass Go
			if pass_go:
				self.cash += self.income
				log.write("player {0} gains {1} because of passing Go, currently has {2} cash.\n".format(self.num, self.income, self.cash))
			# Add one to position, if went past jail ？？？
			# if (newPosition >= Board.TILES_JAIL[0] and newPosition < 35) and (
			# 		self.position < Board.TILES_JAIL[0] or self.position > 35):
			# 	newPosition += 1
			#
			if newPosition >= board.TILES_JAIL[0] > self.position:
				newPosition += 1
			# Apply new position
			self.position = newPosition
			log.write("player {0} move to {1}.\n".format(self.num, board.TILE_NAME[self.position]))
		else:
			log.write("player {0} is in jail.\n".format(self.num))
			if dice1 == dice2:
				self.go_out_of_jail()
				log.write("player {0} goes out of jail because of a double.\n".format(self.num))
				return
			else:
				self.consecutive_not_Doubles += 1

			if self.consecutive_not_Doubles >= 3:
				self.fine_money(50)
				self.go_out_of_jail()
				self.consecutive_not_Doubles = 0
				log.write("player {0} goes out of jail because of paying 50.\n".format(self.num))

	def getNewPosition(self, offset, board):
		tmp = self.position + offset
		return tmp % board.getSize(), tmp != (tmp % board.getSize())

	def doChanceCard(self, card, board):
		# Check the type of the chance card
		# card for moving
		log.write("player {0} get a chance card {1}.\n".format(self.num, card))
		if card.kind == "advance":
			# Move to next utilities if necessary
			if card.value == "utility":
				# Keep track if suitable utilities is found
				log.write("player {0} goes to the nearest utility.\n")
				moved = False
				# Go through possible utilities
				for pos in board.TILES_UTILITIES:
					# If player is before current utility, go to that one
					if self.position < pos:
						self.position = pos
						moved = True
						break

				# If not yet moved, go to first utilities in array
				if not moved:
					self.position = board.TILES_UTILITIES[0]

			# Move to next railroad if necessary
			elif card.value == "railroad":
				# Keep track if suitable railroad is found
				log.write("player {0} goes to the nearest railroad.\n")
				moved = False
				# Go through possible railroad
				for pos in board.TILES_TRANSPORT:
					# If player is before current railroad, go to that one
					if self.position < pos:
						self.position = pos
						moved = True
						break

				# If not yet moved, go to first railroad in array
				if not moved:
					self.position = board.TILES_TRANSPORT[0]

			# If negative, thus should move back, do that
			elif card.value <= 0:
				self.position, _ = self.getNewPosition(card.value, board)
				log.write("player {0} moves to {1}.\n".format(self.num, board.TILE_NAME[self.position]))
			# Move player to given position otherwise
			else:
				self.position = card.value
				if self.position == board.TILES_JAIL[0]:
					self.at_jail = True
				log.write("player {0} moves to {1}.\n".format(self.num, board.TILE_NAME[self.position]))
		# card for get money
		elif card.kind == "cash":
			self.cash += card.value
			log.write("player {0} gets {1} cash, currently has {2} cash.\n".format(self.num, card.value, self.cash))

		# card for tax
		elif card.kind == "tax":
			fined = card.value[0] * self.house + card.value[1] * self.hotel
			self.fine_money(fined)
			log.write("player {0} pay {1} tax, currently has {2} cash.\n".format(self.num, fined, self.cash))

	def doCommunityCard(self, card, board):
		# Go to given position if card is of the advance kind
		# Check the type of the chance card
		# card for moving
		log.write("player {0} get a community card {1}.\n".format(self.num, card))
		if card.kind == "advance":
			self.position = card.value
			if self.position == board.TILES_JAIL[0]:
				self.at_jail = True
			log.write("player {0} moves to {1}.\n".format(self.num, board.TILE_NAME[self.position]))
		# card for get money
		elif card.kind == "cash":
			self.cash += card.value
			log.write("player {0} gets {1} cash, currently has {2} cash.\n".format(self.num, card.value, self.cash))

		# card for tax
		elif card.kind == "tax":
			fined = card.value[0] * self.house + card.value[1] * self.hotel
			self.fine_money(fined)
			log.write("player {0} pay {1} tax, currently has {2} cash.\n".format(self.num, fined, self.cash))

	def total_property(self):
		land_value = 0
		for i in self.building:
			land_value += i.cur_price
		return land_value + self.cash

	def is_bankrupt(self):
		return self.cash < 0 or self.bankrupt_status

	def bankrupt(self):
		for building in self.building:
			building.sell()
		self.building = []
		self.bankrupt_status = True


class Board:

	TILE_NAME = [
		"Go",
		"Mediterranean Avenue",
		"Community Chest",
		"Baltic Avenue",
		"Income Tax",
		"Reading Railroad",
		"Oriental Avenue",
		"Chance",
		"Vermont Avenue",
		"Connecticut Avenue",
		"Just Visiting",
		"In Jail",
		"St. Charles Place",
		"Electric Company",
		"States Avenue",
		"Verginia Avenue",
		"Pennsylvania Railroad",
		"St. James Place",
		"Community Chest",
		"Tennessee Avenue",
		"New York Avenue",
		"Free Parking",
		"Kentucky Avenue",
		"Chance",
		"Indiana Avenue",
		"Illinois Avenue",
		"B & O Railroad",
		"Atlantic Avenue",
		"Ventinor Avenue",
		"Waterworks",
		"Marvin Gardens",
		"Go To Jail",
		"Pacific Avenue",
		"North Carolina Avenue",
		"Community Chest",
		"Pennsylvania Avenue",
		"Short Line",
		"Chance",
		"Park Place",
		"Luxury Tax",
		"Boardwalk"
	]

	TILE_BUILDING = [
		None,
		Building("Mediterranean Avenue", 60),
		None,
		Building("Baltic Avenue", 60),
		None,
		Building("Reading Railroad", 200),
		Building("Oriental Avenue", 100),
		None,
		Building("Vermont Avenue", 100),
		Building("Connecticut Avenue", 100),
		None,
		None,
		Building("St. Charles Place", 140),
		Building("Electric Company", 150),
		Building("States Avenue", 140),
		Building("Verginia Avenue", 160),
		Building("Pennsylvania Railroad", 200),
		Building("St. James Place", 180),
		None,
		Building("Tennessee Avenue", 180),
		Building("New York Avenue", 180),
		None,
		Building("Kentucky Avenue", 220),
		None,
		Building("Indiana Avenue", 220),
		Building("Illinois Avenue", 240),
		Building("B & O Railroad", 200),
		Building("Atlantic Avenue", 260),
		Building("Ventinor Avenue", 260),
		Building("Waterworks", 150),
		Building("Marvin Gardens", 280),
		None,
		Building("Pacific Avenue", 300),
		Building("North Carolina Avenue", 300),
		None,
		Building("Pennsylvania Avenue", 320),
		Building("Short Line", 200),
		None,
		Building("Park Place", 350),
		Building("Luxury Tax", 100),
		Building("Boardwalk", 400)
	]

	TILES_REAL_ESTATE = [1, 3, 6, 8, 9, 12, 14, 15, 17, 19, 20, 22, 24, 25, 27, 28, 30, 32, 33, 35, 38, 40]
	TILES_CHANCE = [7, 23, 37]
	TILES_COMMUNITY = [2, 18, 34]
	TILES_UTILITIES = [13, 29]
	TILES_TRANSPORT = [5, 16, 26, 36]
	TILES_TAX = [4, 39]
	TILES_NONE = [10, 21]
	TILES_JAIL = [11]
	TILES_GO_TO_JAIL = [31]
	TILES_GO = [0]

	def __init__(self):
		# Check if total amount of tiles is correct
		tilesCount = self.getSize()
		if tilesCount != 41:
			print("Game board consists of %i tiles, instead of 41!" % tilesCount)

		# Setup array to keep track of times a player had landed on a tile
		self.hits = [0] * 41

	def getTileType(self, tile):
		# Return a string of the type of tile corresponding with the index given
		if tile in Board.TILES_REAL_ESTATE:
			return "realestate"
		elif tile in Board.TILES_CHANCE:
			return "chance"
		elif tile in Board.TILES_COMMUNITY:
			return "community"
		elif tile in Board.TILES_UTILITIES:
			return "utitlities"
		elif tile in Board.TILES_TRANSPORT:
			return "transport"
		elif tile in Board.TILES_TAX:
			return "tax"
		elif tile in Board.TILES_JAIL:
			return "jail"
		elif tile in Board.TILES_GO_TO_JAIL:
			return "gotojail"
		elif tile in Board.TILES_GO:
			return "go"
		else:
			return "none"

	def hit(self, tile):
		# Increment tile hit count in array
		print(tile)
		self.hits[tile] += 1

	def getSize(self):
		return (len(Board.TILES_REAL_ESTATE) + len(Board.TILES_CHANCE) +
				len(Board.TILES_COMMUNITY) + len(Board.TILES_UTILITIES) +
				len(Board.TILES_TRANSPORT) + len(Board.TILES_TAX) +
				len(Board.TILES_NONE) + len(Board.TILES_JAIL) +
				len(Board.TILES_GO_TO_JAIL) + len(Board.TILES_GO))
