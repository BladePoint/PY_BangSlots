# sperm_bank_screen.py
import pygame
import logging

from src.components.base_screen import BaseScreen
from src.components.button_image import ButtonBase
from src.components.button_text import ButtonText

logger = logging.getLogger(__name__)

class SpermBankScreen(BaseScreen):
	def __init__(self, screen_surface, device, asset_manager, game_data):
		super().__init__(screen_surface, device, asset_manager, game_data)
		self.bg_image = self.asset_manager.load_image('sperm_bank_bg.webp', False, False)
		self._init_ui()
		self.thrust_apex = 768
		self.thrust_nadir = 256
		self.isWithdrawing = False
	def _init_ui(self):
		self.bang_slots_sign = ButtonBase(627, 0, 173, 116, self._to_bang_slots)
		self.libre_baskerville_36 = self.asset_manager.load_font("LibreBaskerville-Bold.ttf", 36)
		self.money_text_surface = None
		self.money_text_rect = None
		self.system_32 = self.asset_manager.load_font(None, 32, True)
		text_color = (0,0,0)
		bg_color = (255, 255, 224)
		self.advertising = ButtonText(50, 67, 180, 180, self.system_32, text_color, bg_color, self.upgrade_advertising)
		self.tank = ButtonText(50, 285, 180, 180, self.system_32, text_color, bg_color, self.upgrade_tank)
		self.xl = ButtonText(610, 200, 180, 180, self.system_32, text_color, bg_color, self.upgrade_xl)
	def _to_bang_slots(self):
		self.set_next_screen('SlotGameScreen')
		self.request_end_screen()

	def upgrade_advertising(self):
		pass

	def upgrade_tank(self):
		pass

	def upgrade_xl(self):
		if self.game_data.upgrade_xl():
			self.set_xl()
			self.game_data.save()

	def handle_event(self, event):
		base_event = super().handle_event(event)
		if base_event:
			self.bang_slots_sign.handle_event(base_event)
			self.advertising.handle_event(base_event)
			self.tank.handle_event(base_event)
			self.xl.handle_event(base_event)

	def _update_always(self, time_delta):
		self._update_ui()
	def _update_ui(self):
		money_string = f"${self.game_data.money}"
		shadow_offset = 1
		money_text = self.libre_baskerville_36.render(money_string, True, (0, 255, 0))
		money_shadow = self.libre_baskerville_36.render(money_string, True, (0, 0, 0))
		self.money_text_surface = pygame.Surface((money_text.get_width()+shadow_offset, money_text.get_height()+shadow_offset), pygame.SRCALPHA)
		self.money_text_surface.blit(money_shadow, (0, 1))
		self.money_text_surface.blit(money_text, (1, 0))
		self.money_text_rect = self.money_text_surface.get_rect(midtop=(469, 0))

	def set_advertising(self):
		self.advertising.set_text(f"\
Advertising\n\
Level {self.game_data.advertising_level}\n\
${self.game_data.advertising_hourly} / hour\n\
\n\
UPGRADE\n\
for ${self.game_data.advertising_cost}")

	def set_tank(self):
		self.tank.set_text(f"\
Storage Tank\n\
Level {self.game_data.tank_level}\n\
${self.game_data.tank_max} max\n\
\n\
UPGRADE\n\
for ${self.game_data.tank_cost}")

	def set_xl(self):
		self.xl.set_text(f"\
Orifice XL\n\
Level {self.game_data.xl_level}\n\
${self.game_data.xl_earn} / thrust\n\
\n\
UPGRADE\n\
for ${self.game_data.xl_cost}")

	def _update_interactive(self):
		super()._update_interactive()
		self.test_device()

	def test_device(self):
		if self.device.depth > self.thrust_apex and not self.isWithdrawing:
			self.game_data.manual_earn()
			self.isWithdrawing = True
		elif self.device.depth < self.thrust_nadir:
			self.isWithdrawing = False

	def _render_content(self):
		self.screen_surface.blit(self.bg_image, (0, 0))
		self.screen_surface.blit(self.money_text_surface, self.money_text_rect)
		self.advertising.render(self.screen_surface)
		self.tank.render(self.screen_surface)
		self.xl.render(self.screen_surface)

	def on_enter(self):
		super().on_enter()
		self.set_advertising()
		self.set_tank()
		self.set_xl()
		self._update_ui()

	def on_ready(self):
		super().on_ready()
		self.device_initial = 0

	def on_exit(self):
		super().on_exit()
		logger.info(f"{self.__class__.__name__} exited.")
		self.game_data.save()
		