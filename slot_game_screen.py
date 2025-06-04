# title_screen.py
import pygame
import logging
import numpy as np

from base_screen import BaseScreen

logger = logging.getLogger(__name__)

class SlotGameScreen(BaseScreen):
	def __init__(self, screen_surface, device, asset_manager, game_data):
		super().__init__(screen_surface, device, asset_manager, game_data)
		self.background_image = self.asset_manager.load_image('slot_game_bg.webp', False)
		self.reel_shading = self.asset_manager.load_image('reel_shading.webp', True)
		self.reel_payline = self.asset_manager.load_image('reel_payline.png', True)
		self.symbol_images = {}
		self.symbol_images['□'] = pygame.Surface((89, 29))
		self.symbol_images['□'].fill(pygame.Color("#fffcf9"))
		self.symbol_images['🍒'] = self.asset_manager.load_image('symbol_cherry.webp', False)
		self.symbol_images['-'] = self.asset_manager.load_image('symbol_bar_1.webp', False)
		self.symbol_images['='] = self.asset_manager.load_image('symbol_bar_2.webp', False)
		self.symbol_images['≡'] = self.asset_manager.load_image('symbol_bar_3.webp', False)
		self.symbol_images['7'] = self.asset_manager.load_image('symbol_seven.webp', False)
		self.symbol_images['💋'] = self.asset_manager.load_image('symbol_wild.webp', False)
		self.reel_viewport_width = 89
		self.reel_viewport_height = 163
		self.reel_positions = [
			(394, 172),
			(503, 172),
			(612, 172)
		]
		self.reel_strips_data = [
			['-', '□', '≡', '□', '🍒', '□', '=', '□', '-', '□', '7', '□', '≡', '□', '=', '□', '-', '□', '💋', '□', '🍒', '□'],
			['🍒', '□', '-', '□', '=', '□', '🍒', '□', '≡', '□', '-', '□', '7', '□', '=', '□', '-', '□', '💋', '□', '🍒', '□'],
			['=', '□', '-', '□', '🍒', '□', '-', '□', '7', '□', '🍒', '□', '=', '□', '-', '□', '≡', '□', '💋', '□', '🍒', '□']
		]
		self.reel_viewport_height = 163
		self.reel_surfaces = []
		self.reel_cycle_heights = [] # Height of one full pass of symbols for each reel
		self.reel_symbol_info_strips = [] # List of lists of dicts: [{'key': key, 'y_start': y, 'height': h, 'mid_y': y + h/2}, ...]
		self.reel_cycle_start_ys = [] # Y pos where main cycle starts on each extended reel

		self.reel_current_ys = [0.0] * len(self.reel_strips_data)
		self.reel_current_ys = [20, -25, 20]
		# Example: To start reel 0 with its first symbol (index 0) centered:
		# target_symbol_info = self.reel_symbol_info_strips[0][0]
		# self.reel_current_y_offsets[0] = target_symbol_info['mid_y'] - (self.reel_viewport_height / 2.0)
		# This reel_current_y_offsets[0] is now the value used for spin logic and for calculating the final blit source.

		for strip_data in self.reel_strips_data:
			current_y = 0
			symbol_info_for_this_strip = []
			for symbol_key in strip_data:
				img_height = self.symbol_images[symbol_key].get_height()
				symbol_info_for_this_strip.append({
					'key': symbol_key,
					'y_start': current_y,
					'height': img_height,
					'mid_y': current_y + img_height / 2.0
				})
				current_y += img_height
			self.reel_symbol_info_strips.append(symbol_info_for_this_strip)
			self.reel_cycle_heights.append(current_y)

		for r_idx, strip_data in enumerate(self.reel_strips_data): # Build the actual extended reel surfaces for drawing
			cycle_height = self.reel_cycle_heights[r_idx]
			# --- Determine symbols for top overlap (end of strip) ---
			top_overlap_symbols = []
			temp_h = 0
			for symbol_key in reversed(strip_data): # Iterate backwards
				img_h = self.symbol_images[symbol_key].get_height()
				top_overlap_symbols.insert(0, symbol_key) # Add to front
				temp_h += img_h
				if temp_h >= self.reel_viewport_height:
					break
			top_overlap_actual_height = sum(self.symbol_images[s].get_height() for s in top_overlap_symbols)
			# --- Determine symbols for bottom overlap (start of strip) ---
			bottom_overlap_symbols = []
			temp_h = 0
			for symbol_key in strip_data:
				img_h = self.symbol_images[symbol_key].get_height()
				bottom_overlap_symbols.append(symbol_key)
				temp_h += img_h
				if temp_h >= self.reel_viewport_height:
					break
			bottom_overlap_actual_height = sum(self.symbol_images[s].get_height() for s in bottom_overlap_symbols)
			extended_surface_height = top_overlap_actual_height + cycle_height + bottom_overlap_actual_height
			reel_surf = pygame.Surface((89, extended_surface_height))

			current_y_blit_pos = 0
			# 1. Blit top overlap (end of strip)
			for symbol_key in top_overlap_symbols:
				symbol_image = self.symbol_images[symbol_key]
				reel_surf.blit(symbol_image, (0, current_y_blit_pos))
				current_y_blit_pos += symbol_image.get_height()
			
			# This is where the "main cycle" conceptually starts on this extended surface.
			self.reel_cycle_start_ys.append(top_overlap_actual_height)

			# 2. Blit main cycle
			for symbol_key in strip_data: # The full original strip
				symbol_image = self.symbol_images[symbol_key]
				reel_surf.blit(symbol_image, (0, current_y_blit_pos))
				current_y_blit_pos += symbol_image.get_height()

			# 3. Blit bottom overlap (start of strip)
			for symbol_key in bottom_overlap_symbols:
				symbol_image = self.symbol_images[symbol_key]
				reel_surf.blit(symbol_image, (0, current_y_blit_pos))
				current_y_blit_pos += symbol_image.get_height()
				
			self.reel_surfaces.append(reel_surf)

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

	def _render_content(self):
		self.screen_surface.blit(self.background_image, (0, 0))
		for i in range(len(self.reel_surfaces)):
			reel_to_blit = self.reel_surfaces[i]
			destination_on_screen = self.reel_positions[i]
			source_rect_on_reel = pygame.Rect(
				0,
				self.reel_cycle_start_ys[i] + self.reel_current_ys[i],
				self.reel_viewport_width,
				self.reel_viewport_height
			)
			try:
				self.screen_surface.blit(
					reel_to_blit,
					destination_on_screen,
					area=source_rect_on_reel
				)
			except Exception as e:
				logger.error(f"Error blitting reel {i}: {e}. Source Rect: {source_rect_on_reel}, Reel Surf Size: {reel_to_blit.get_size()}, Current_ys: {self.reel_current_ys[i]}, MainCycleStart: {self.reel_cycle_start_ys[i]}")
			self.screen_surface.blit(self.reel_shading, destination_on_screen)
			self.screen_surface.blit(self.reel_payline, (386, 253))
