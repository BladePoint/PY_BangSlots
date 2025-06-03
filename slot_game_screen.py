# title_screen.py
import pygame
import os
import logging
import numpy as np

from base_screen import BaseScreen

logger = logging.getLogger(__name__)

class SlotGameScreen(BaseScreen):
	def __init__(self, screen_surface, device, game_data):
		super().__init__(screen_surface, device, game_data)

		try:
			base_dir = os.path.dirname(os.path.abspath(__file__))
			assets_path = os.path.join(base_dir, 'assets', 'images')
			image_path = os.path.join(assets_path, 'slot_game_bg.webp')
			logger.info(f"Attempting to load image from: {image_path}")

			image = pygame.image.load(image_path).convert()
			self.full_background_image = pygame.transform.scale(image, (self.screen_rect.width, self.screen_rect.height))
			logger.info(f"TitleScreen loaded full background image from: {image_path}")

		except Exception as e:
			logger.fatal(f"Could not load/process background. Path tried: {image_path if 'image_path' in locals() else 'N/A'}. Error: {e}", exc_info=True)
			screen_surface.fill((50, 0, 50))

	def on_enter(self):
		super().on_enter()

	def on_ready(self):
		super().on_ready()

	def on_exit(self):
		super().on_exit()

	def handle_event(self, event):
		base_event = super().handle_event(event)
		#if base_event is not None:
		#	if event.type == pygame.KEYDOWN:
		#		self.request_end_screen()
		#	elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
		#		self.request_end_screen()

	def update(self, time_delta):
		super().update(time_delta)

	def render(self):
		self.screen_surface.blit(self.full_background_image, (0, 0))
		super().render()