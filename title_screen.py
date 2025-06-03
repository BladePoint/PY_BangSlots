# title_screen.py
import pygame
import os
import logging
import numpy as np

from base_screen import BaseScreen

logger = logging.getLogger(__name__)

class TitleScreen(BaseScreen):
	def __init__(self, screen_surface, device, game_data):
		super().__init__(screen_surface, device, game_data)
		self.time_offset = 0.0
		# --- Wave Effect Parameters ---
		self.max_amplitude_at_bottom = 1.0  # Amplitude: Scales linearly from 0 at the top of water to max_amplitude_at_bottom at the bottom in pixels.
		self.horizon_frequency = 0.36  # Wave frequency at the top of water region. Higher value means waves are 'denser' or 'smaller' at horizon.
		self.near_frequency = 0.24     # Wave frequency at the bottom of water region
		self.speed_x = 3.0
		# --- Define Water Region ---
		self.water_region_start_y = 411
		self.water_region_height = self.screen_rect.height - self.water_region_start_y
		self.water_region_width = self.screen_rect.width
		self.static_background_part = None
		self.original_water_np = None
		self.rippling_water_surface = None
		self.xx_water = None
		self.yy_water = None

		try:
			base_dir_for_title_screen = os.path.dirname(os.path.abspath(__file__))
			assets_path = os.path.join(base_dir_for_title_screen, 'assets', 'images')
			image_path = os.path.join(assets_path, 'title_screen.jpg')
			logger.info(f"Attempting to load image from: {image_path}")

			full_background_image = pygame.image.load(image_path).convert()
			full_background_image = pygame.transform.scale(full_background_image, (self.screen_rect.width, self.screen_rect.height))
			logger.info(f"TitleScreen loaded full background image from: {image_path}")

			self.static_background_part = full_background_image.subsurface(
				pygame.Rect(0, 0, self.screen_rect.width, self.water_region_start_y)
			).copy()

			if self.water_region_height > 0: # Only process water if its region exists
				original_water_surface_part = full_background_image.subsurface(
					pygame.Rect(0, self.water_region_start_y, self.water_region_width, self.water_region_height)
				).copy()
				temp_water_np = pygame.surfarray.array3d(original_water_surface_part)
				self.original_water_np = np.transpose(temp_water_np, (1, 0, 2)) # (height, width, 3)

				if self.water_region_width > 0:
					y_coords_water = np.arange(self.water_region_height)
					x_coords_water = np.arange(self.water_region_width)
					self.xx_water, self.yy_water = np.meshgrid(x_coords_water, y_coords_water)
				else:
					logger.warning("Water region has zero width, cannot create meshgrid.")
				
				self.rippling_water_surface = pygame.Surface((self.water_region_width, self.water_region_height), pygame.SRCALPHA)
			else:
				logger.warning("Water region has zero height. No water effect will be applied.")
				self.original_water_np = None # Ensure it's None if no water region

		except Exception as e:
			logger.fatal(f"Could not load/process background. Path tried: {image_path if 'image_path' in locals() else 'N/A'}. Error: {e}", exc_info=True)
			self.static_background_part = pygame.Surface((self.screen_rect.width, self.screen_rect.height))
			self.static_background_part.fill((30, 30, 30))
			self.original_water_np = None
			self.rippling_water_surface = None
			logger.warning("TitleScreen using fallback background color.")

	def on_enter(self):
		super().on_enter()
		self.time_offset = 0.0

	def on_ready(self):
		super().on_ready()
		self.set_next_screen('SlotGameScreen')

	def on_exit(self):
		super().on_exit()

	def handle_event(self, event):
		base_event = super().handle_event(event)
		if base_event is not None:
			if event.type == pygame.KEYDOWN:
				self.request_end_screen()
			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				self.request_end_screen()

	def _update_always(self, time_delta):
		if self.original_water_np is None or self.xx_water is None or self.yy_water is None:
			return # Skip water effect if not initialized
		self.time_offset += time_delta
		# --- Wave Calculation for the Water Region (Linear Scaling) ---
		if self.water_region_height > 1: # 1. Calculate y_normalized (0 at top of water/horizon, 1 at bottom of water/near)
			y_normalized = self.yy_water / (self.water_region_height - 1.0)
		elif self.water_region_height == 1: # Handle edge case of 1px high water region
			y_normalized = np.ones_like(self.yy_water)
		else: # water_region_height <= 0, though previous checks should catch this
			return
		# 2. Calculate Current Amplitude (Linearly scaled by y_normalized)
		current_amplitude_x = self.max_amplitude_at_bottom * y_normalized # Amplitude is 0 at horizon (y_normalized=0) and self.max_amplitude_at_bottom at near (y_normalized=1)
		# 3. Calculate Current Frequency (Linearly interpolated)
		# Frequency is self.horizon_frequency at horizon (y_normalized=0)
		# and self.near_frequency at near (y_normalized=1)
		current_frequency_y = self.horizon_frequency * (1.0 - y_normalized) + self.near_frequency * y_normalized
		# 4. Calculate Horizontal Displacement
		displacement_x = current_amplitude_x * np.sin(current_frequency_y * self.yy_water + self.time_offset * self.speed_x)
		# 5. Calculate Source Coordinates
		source_x = (self.xx_water + displacement_x).astype(int)
		source_y = self.yy_water.astype(int)
		# 6. Clamp Coordinates
		source_x = np.clip(source_x, 0, self.water_region_width - 1)
		# source_y is already within bounds
		# 7. Fetch Pixels
		rippling_array_data = self.original_water_np[source_y, source_x]
		# 8. Blit to Surface
		if self.rippling_water_surface is not None:
			pygame.surfarray.blit_array(self.rippling_water_surface, np.transpose(rippling_array_data, (1, 0, 2)))

	def _update_interactive(self, time_delta):
		current_depth = self.device.depth
		if abs(current_depth - self.device_initial) >= self.device_input_threshold: self.request_end_screen()

	def render(self): # Same as before
		if self.static_background_part:
			self.screen_surface.blit(self.static_background_part, (0, 0))
		else:
			self.screen_surface.fill((30,30,30))
			return

		if self.rippling_water_surface and self.original_water_np is not None:
			self.screen_surface.blit(self.rippling_water_surface, (0, self.water_region_start_y))

		super().render()