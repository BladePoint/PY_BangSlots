# src/components/game_data.py
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

class GameData:
	SAVE_FILENAME = "gamedata.sav"

	def __init__(self):
		"""Initializes a new GameData object with default values."""
		self._save_path = None # The save_path will be set later by the factory or a save call.
		self.money = 50
		self.bet = 1
		self.advertising_level = 1
		self.advertising_hourly = 1
		self.advertising_cost = 20
		self.tank_level = 1
		self.tank_max = 50
		self.tank_cost = 10
		self.xl_level = 1
		self.xl_earn = 1
		self.xl_base = 25
		self.xl_growth = 2
		self.xl_cost = 25

	def save(self):
		"""Saves the current game data to the file."""
		if self._save_path is None: # In case save() is called on an object that wasn't created through the proper load_or_create method.
			raise ValueError("Save path has not been set. Use GameData.load_or_create().")
		with open(self._save_path, "wb") as f:
			pickle.dump(self, f)
		logger.info(f"Game data saved to {self._save_path}")

	def increment_bet(self, max_bet):
		if self.bet < max_bet:
			self.bet += 1
			return True
		else: return False

	def decrement_bet(self):
		if self.bet > 1:
			self.bet -= 1
			return True
		else: return False

	def set_bet(self, amount, maximum):
		if amount <= maximum and amount > 0 and amount != self.bet:
			self.bet = amount
			return True
		else: return False

	def place_bet(self):
		if self.money >= self.bet:
			self.money -= self.bet
			logger.info(f"Bet ${self.bet}.")
			return self.bet
		else:
			logger.info("Attempted to bet without enough money. Should not get this far!")
			return None

	def win(self, amount):
		self.money += amount
		logger.info(f"Won ${amount}.")

	def manual_earn(self):
		self.money += self.xl_earn

	def purchase(self, price):
		if self.money >= price:
			self.money -= price
			return True
		else: return False

	def upgrade_xl(self):
		if self.purchase(self.xl_cost):
			self.xl_level += 1
			self.xl_earn += 1
			self.xl_cost = int(self.xl_base * (self.xl_growth ** self.xl_level))
			return True
		else: return False

	@classmethod
	def load_or_create(cls, project_root:Path):
		"""
		A factory method to either load GameData from a file or create a new one.
		This is the recommended way to get a GameData instance.
		"""
		save_path = project_root / cls.SAVE_FILENAME

		if save_path.exists():
			logger.info("Save file found. Loading data.")
			with open(save_path, "rb") as f:
				instance = pickle.load(f) # Load the object from the file
				instance._save_path = save_path # Ensure its internal save path is correctly set
				return instance
		else:
			logger.info("No save file found. Creating new game data.")
			instance = cls() # Create a new instance
			instance._save_path = save_path # Set its save path
			instance.save() # Save it immediately
			return instance