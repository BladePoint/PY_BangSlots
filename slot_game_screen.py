# title_screen.py
import pygame
import logging
import random
from enum import Enum, auto

from base_screen import BaseScreen

logger = logging.getLogger(__name__)

class MachineState(Enum):
	ALL_LOCKED = auto()
	ALL_SPINNING = auto()
	STOPPING_REEL_0 = auto()
	PAUSE_AFTER_REEL_0 = auto()
	STOPPING_REEL_1 = auto()
	PAUSE_AFTER_REEL_1 = auto()
	STOPPING_REEL_2 = auto()

class ReelState(Enum):
	LOCKED = auto()
	SPINNING_FREELY = auto()
	OVERSHOOTING = auto()
	BOUNCING_BACK = auto()

class SlotGameScreen(BaseScreen):
	def __init__(self, screen_surface, device, asset_manager, game_data):
		super().__init__(screen_surface, device, asset_manager, game_data)
		self.background_image = self.asset_manager.load_image('slot_game_bg.webp', False)
		self.reel_shading = self.asset_manager.load_image('reel_shading.webp', True)
		self.reel_payline = self.asset_manager.load_image('reel_payline.png', True)

		self.reel_viewport_width = 89
		self.reel_viewport_height = 163
		self.blank_height = 29
		self.reel_positions = [(394, 172), (503, 172), (612, 172)]
		self.symbol_images = {}
		self.symbol_images['□'] = pygame.Surface((89, self.blank_height))
		self.symbol_images['□'].fill(pygame.Color("#fffcf9"))
		self.symbol_images['🍒'] = self.asset_manager.load_image('symbol_cherry.webp', False)
		self.symbol_images['-'] = self.asset_manager.load_image('symbol_bar_1.webp', False)
		self.symbol_images['='] = self.asset_manager.load_image('symbol_bar_2.webp', False)
		self.symbol_images['≡'] = self.asset_manager.load_image('symbol_bar_3.webp', False)
		self.symbol_images['7'] = self.asset_manager.load_image('symbol_seven.webp', False)
		self.symbol_images['💋'] = self.asset_manager.load_image('symbol_wild.webp', False)
		self.visual_strips_data = [
			['-', '□', '≡', '□', '🍒', '□', '=', '□', '-', '□', '7', '□', '≡', '□', '=', '□', '-', '□', '💋', '□', '🍒', '□'],
			['🍒', '□', '-', '□', '=', '□', '🍒', '□', '≡', '□', '=', '□', '7', '□', '-', '□', '🍒', '□', '💋', '□', '-', '□'],
			['=', '□', '-', '□', '🍒', '□', '-', '□', '7', '□', '🍒', '□', '=', '□', '-', '□', '≡', '□', '💋', '□', '🍒', '□']
		]
		self.logical_strips_data = [
			['💋', '7', '≡', '≡', '≡', '=', '=', '=', '=', '-', '-', '-', '-', '-', '🍒', '🍒', '🍒', '🍒', '🍒', '🍒', '🍒', '□', '□', '□', '□', '□', '□', '□', '□', '□', '□', '□'], # 💋:1, 7:1, ≡:3, =:4, -:5, 🍒:7, □:11, total 32 elements
			['💋', '7', '7', '≡', '≡', '≡', '=', '=', '=', '=', '-', '-', '-', '-', '🍒', '🍒', '🍒', '🍒', '🍒', '🍒', '□', '□', '□', '□', '□', '□', '□', '□', '□', '□', '□', '□'], # 💋:1, 7:2, ≡:3, =:4, -:4, 🍒:6, □:12, total 32 elements
			['💋', '7', '7', '7', '≡', '≡', '≡', '=', '=', '=', '=', '-', '-', '-', '-', '🍒', '🍒', '🍒', '🍒', '🍒', '□', '□', '□', '□', '□', '□', '□', '□', '□', '□', '□', '□'] # 💋:1, 7:3, ≡:3, =:4, -:4, 🍒:5, □:12, total 32 elements
		]
		self.reel_count = len(self.visual_strips_data)
		self.visual_symbol_indices_map = [] # List of dicts, one per reel
		for visual_strip in self.visual_strips_data:
			symbol_to_indices = {} # For the current reel
			for index, symbol_key in enumerate(visual_strip):
				if symbol_key not in symbol_to_indices:
					symbol_to_indices[symbol_key] = []
				symbol_to_indices[symbol_key].append(index)
			self.visual_symbol_indices_map.append(symbol_to_indices)

		self.reel_cycle_heights = [] # Height of one full pass of symbols for each reel
		self.reel_symbol_info = [] # List of lists of dicts: [{'key': key, 'y_start': y, 'height': h, 'mid_y': y + h/2}, ...]
		for strip_data in self.visual_strips_data:
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
			self.reel_symbol_info.append(symbol_info_for_this_strip)
			self.reel_cycle_heights.append(current_y)

		self.reel_surfaces = []
		self.reel_cycle_start_ys = [] # Y pos where main cycle starts on each extended reel
		for r_idx, strip_data in enumerate(self.visual_strips_data): # Build the actual extended reel surfaces for drawing
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

		self.reel_current_ys = [0.0] * self.reel_count
		self.reel_target_ys = [0.0] * self.reel_count

		self.machine_state = MachineState.ALL_LOCKED
		self.reel_states = [ReelState.LOCKED] * self.reel_count

		# Animation parameters
		self.all_spin_duration = .8  # seconds all reels spin freely
		self.pause_duration_1 = 0.2       # seconds pause after reel 0 stops
		self.pause_duration_2 = 0.2       # seconds pause after reel 1 stops
		self.spin_speed_normal = self.reel_viewport_height * 8 # pixels per second during free spin / approaching target
		self.bounce_back_speed_factor = .1
		self.overshoot_height = self.blank_height / 2.0

		self.stop_timer = 0.0

	def roll_logical_stops(self):
		logical_indices = []
		for logical_strip in self.logical_strips_data: logical_indices.append(random.randrange(len(logical_strip)))
		logger.info(f"Logical outcomes determined: {logical_indices})")
		return logical_indices

	def logical_to_symbols(self, logical_indices):
		chosen_symbols = []
		for reel_index, stop_index in enumerate(logical_indices): # indices to symbols
			chosen_symbols.append(self.logical_strips_data[reel_index][stop_index])
		logger.info(f"Outcomes as symbols: {chosen_symbols})")
		return chosen_symbols

	def symbols_to_visual(self, chosen_symbols):
		visual_indices = []
		for reel_index, symbol_key in enumerate(chosen_symbols):
			matching_symbol_indices = self.visual_symbol_indices_map[reel_index].get(symbol_key)
			visual_indices.append(random.choice(matching_symbol_indices))
		logger.info(f"Symbols {chosen_symbols}: mapped to visual indices {visual_indices}")
		return visual_indices

	def determine_target_ys(self, visual_indices):
		for reel_index, visual_index in enumerate(visual_indices):
			visual_symbol_info = self.reel_symbol_info[reel_index][visual_index]
			target_y_offset = visual_symbol_info['mid_y'] - (self.reel_viewport_height / 2.0)
			self.reel_target_ys[reel_index] = target_y_offset

	def current_to_target_ys(self):
		for reel_index, target_y in enumerate(self.reel_target_ys):
			self.reel_current_ys[reel_index] = target_y

	def spin_all_reels(self):
		logger.info("Starting all reel spins.")
		self.machine_state = MachineState.ALL_SPINNING
		for i in range(len(self.reel_states)):
			self.reel_states[i] = ReelState.SPINNING_FREELY
		self.stop_timer = 0.0

	def on_enter(self):
		super().on_enter()

	def on_ready(self):
		super().on_ready()
		logical_indices = self.roll_logical_stops()
		chosen_symbols = self.logical_to_symbols(logical_indices)
		visual_indices = self.symbols_to_visual(chosen_symbols)
		self.determine_target_ys(visual_indices)
		self.spin_all_reels()

	def on_exit(self):
		super().on_exit()

	def handle_event(self, event):
		base_event = super().handle_event(event)
		#if base_event is not None:
		#	if event.type == pygame.KEYDOWN:
		#		self.request_end_screen()
		#	elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
		#		self.request_end_screen()

	def _update_always(self, time_delta):
		self.update_reel_animations(time_delta)

	def update_reel_animations(self, time_delta):
		if self.machine_state == MachineState.ALL_LOCKED: return
		self.stop_timer += time_delta
		if self.machine_state == MachineState.ALL_SPINNING:
			if self.stop_timer >= self.all_spin_duration:
				self.machine_state = MachineState.STOPPING_REEL_0
				self.reel_states[0] = ReelState.OVERSHOOTING
				logger.info("All spinning phase complete. Reel 0 overshooting target.")
				self.stop_timer = 0.0
		elif self.machine_state == MachineState.STOPPING_REEL_0:
			if self.reel_states[0] == ReelState.LOCKED:
				self.machine_state = MachineState.PAUSE_AFTER_REEL_0
				self.stop_sequence_timer = 0.0
				logger.debug("Reel 0 locked. Pausing.")
		elif self.machine_state == MachineState.PAUSE_AFTER_REEL_0:
			if self.stop_timer >= self.pause_duration_1:
				self.machine_state = MachineState.STOPPING_REEL_1
				self.reel_states[1] = ReelState.OVERSHOOTING
				logger.debug("Pause after Reel 0 complete. Reel 1 overshooting target.")
				self.stop_timer = 0.0
		elif self.machine_state == MachineState.STOPPING_REEL_1:
			if self.reel_states[1] == ReelState.LOCKED:
				self.machine_state = MachineState.PAUSE_AFTER_REEL_1
				self.stop_timer = 0.0
				logger.debug("Reel 1 locked. Pausing.")
		elif self.machine_state == MachineState.PAUSE_AFTER_REEL_1:
			if self.stop_timer >= self.pause_duration_2:
				self.machine_state = MachineState.STOPPING_REEL_2
				self.reel_states[2] = ReelState.OVERSHOOTING
				logger.debug("Pause after Reel 1 complete. Reel 2 overshooting target.")
				self.stop_timer = 0.0
		elif self.machine_state == MachineState.STOPPING_REEL_2:
			if self.reel_states[2] == ReelState.LOCKED:
				self.machine_state = MachineState.ALL_LOCKED
				self.stop_timer = 0.0
				logger.info("All reels stopped and locked.")
				# Trigger win evaluation etc.
				# self.evaluate_wins()
				# Potentially set machine_state back to READY_TO_SPIN or IDLE after results displayed

		for i in range(len(self.reel_current_ys)):
			cycle_height = self.reel_cycle_heights[i]

			if self.reel_states[i] == ReelState.SPINNING_FREELY:
				self.reel_current_ys[i] -= self.spin_speed_normal * time_delta
				if self.reel_current_ys[i] < 0: self.reel_current_ys[i] += cycle_height # Wrap around
			else:
				final_y = self.reel_target_ys[i]
				current_y = self.reel_current_ys[i]
				if self.reel_states[i] == ReelState.OVERSHOOTING:
					overshoot_y = final_y - self.overshoot_height
					if overshoot_y < 0: overshoot_y += cycle_height # check wrapping
					distance_to_overshoot = current_y - overshoot_y
					if distance_to_overshoot < 0: distance_to_overshoot += cycle_height # already passed target
					move_amount = self.spin_speed_normal * time_delta
					stop_threshold = move_amount * 1.1
					if distance_to_overshoot <= stop_threshold and distance_to_overshoot >= 0:
						self.reel_current_ys[i] = overshoot_y
						self.reel_states[i] = ReelState.BOUNCING_BACK
						logger.debug(f"Reel {i}: Snapped to point {overshoot_y}. Bouncing back to {self.reel_target_ys[i]}.")
					else:
						self.reel_current_ys[i] -= move_amount
						if self.reel_current_ys[i] < 0: self.reel_current_ys[i] += cycle_height
				elif self.reel_states[i] == ReelState.BOUNCING_BACK:
					distance_to_final = final_y - current_y
					if distance_to_final < 0: distance_to_final += cycle_height
					bounce_speed = self.spin_speed_normal * self.bounce_back_speed_factor
					move_amount = bounce_speed * time_delta
					if distance_to_final <= move_amount * 1.1 and distance_to_final >=0:
						self.reel_current_ys[i] = final_y
						self.reel_states[i] = ReelState.LOCKED
						logger.debug(f"Reel {i}: Bounced to final target {final_y}. LOCKED.")
					else:
						self.reel_current_ys[i] += move_amount
						if self.reel_current_ys[i] >= cycle_height: self.reel_current_ys[i] -= cycle_height

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
