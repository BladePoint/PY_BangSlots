# title_screen.py
import pygame
import logging
import random
import numpy as np
from enum import Enum, auto
from collections import Counter

from src.components.base_screen import BaseScreen
from src.components.button_image import ButtonImage
from src.components.button_image import ButtonBase

logger = logging.getLogger(__name__)

class MachineState(Enum):
	LOCKED = auto()
	READY = auto()
	WITHDRAW_RESET = auto()
	ALL_SPINNING = auto()
	STOPPING_REEL_0 = auto()
	PAUSE_AFTER_REEL_0 = auto()
	STOPPING_REEL_1 = auto()
	PAUSE_AFTER_REEL_1 = auto()
	STOPPING_REEL_2 = auto()

class ReelState(Enum):
	STOPPED = auto()
	SPINNING_FREELY = auto()
	OVERSHOOTING = auto()
	BOUNCING_BACK = auto()

class SlotGameScreen(BaseScreen):
	# Total Expected Payout Value (for 1 unit bet): 749005.0
	# Total Possible Combinations: 786432
	# Calculated Theoretical RTP: 94.9201%
	RAW_PAYTABLE = '''
		💋💋💋,800,Triple Wild
		💋💋7,320,Triple Seven (2 Wilds x4)
		💋77,160,Triple Seven (1 Wild x2)
		777,80,Triple Seven
		💋💋≡,160,Triple Bar3 (2 Wilds x4)
		💋≡≡,80,Triple Bar3 (1 Wild x2)
		≡≡≡,40,Triple Bar3
		💋💋=,100,Triple Bar2 (2 Wilds x4)
		💋==,50,Triple Bar2 (1 Wild x2)
		===,25,Triple Bar2
		💋💋-,40,Triple Bar1 (2 Wilds x4)
		💋--,20,Triple Bar1 (1 Wild x2)
		---,10,Triple Bar1
		💋💋🍒,40,Triple Cherry (2 Wilds x4)
		💋🍒🍒,20,Triple Cherry (1 Wild x2)
		🍒🍒🍒,10,Triple Cherry
		💋≡=,10,Any Three Bars (1 Wild x2)
		💋≡-,10,Any Three Bars (1 Wild x2)
		💋=-,10,Any Three Bars (1 Wild x2)
		🍒💋7,10,Any Two Cherries (1 Wild x2)
		🍒💋≡,10,Any Two Cherries (1 Wild x2)
		🍒💋=,10,Any Two Cherries (1 Wild x2)
		🍒💋-,10,Any Two Cherries (1 Wild x2)
		🍒💋□,10,Any Two Cherries (1 Wild x2)
		≡≡=,5,Any Three Bars
		≡≡-,5,Any Three Bars
		==≡,5,Any Three Bars
		==-,5,Any Three Bars
		--≡,5,Any Three Bars
		--=,5,Any Three Bars
		-=≡,5,Any Three Bars
		🍒🍒7,5,Any Two Cherries
		🍒🍒≡,5,Any Two Cherries
		🍒🍒=,5,Any Two Cherries
		🍒🍒-,5,Any Two Cherries
		🍒🍒□,5,Any Two Cherries
		💋7≡,4,Any One Cherry (1 Wild x2)
		💋7=,4,Any One Cherry (1 Wild x2)
		💋7-,4,Any One Cherry (1 Wild x2)
		💋7□,4,Any One Cherry (1 Wild x2)
		💋≡□,4,Any One Cherry (1 Wild x2)
		💋=□,4,Any One Cherry (1 Wild x2)
		💋-□,4,Any One Cherry (1 Wild x2)
		💋□□,4,Any One Cherry (1 Wild x2)
		🍒7≡,2,Any One Cherry
		🍒7=,2,Any One Cherry
		🍒7-,2,Any One Cherry
		🍒7□,2,Any One Cherry
		🍒≡=,2,Any One Cherry
		🍒≡-,2,Any One Cherry
		🍒≡□,2,Any One Cherry
		🍒=-,2,Any One Cherry
		🍒=□,2,Any One Cherry
		🍒-□,2,Any One Cherry
		🍒77,2,Any One Cherry
		🍒≡≡,2,Any One Cherry
		🍒==,2,Any One Cherry
		🍒--,2,Any One Cherry
		🍒□□,2,Any One Cherry
	'''
	REEL_COUNT = 3
	MAXIMUM_BET = 3

	def __init__(self, screen_surface, device, asset_manager, game_data):
		super().__init__(screen_surface, device, asset_manager, game_data)
		self._init_static_gfx()
		self._init_lever_shaft()
		self._init_lever_head()
		self._init_reels()
		self._init_attendant()
		self._init_ui()
		self.machine_state = MachineState.LOCKED
		self.reel_states = [ReelState.STOPPED] * SlotGameScreen.REEL_COUNT
		self.wager = None
		# self.calculate_rtp() # Warning, this calculation is long and may lock up your system for a few seconds

	def _init_static_gfx(self):
		self.background = self.asset_manager.load_image('slot_game_bg.webp', False, False)
		self.reel_shading = self.asset_manager.load_image('reel_shading.webp', True, True)
		self.reel_payline = self.asset_manager.load_image('reel_payline.png', True, True)
		self.digital_panel = self.asset_manager.load_image('bet_win.webp', True, True)

	def _init_lever_shaft(self):
		self.lever_shaft_original = self.asset_manager.load_image('lever_shaft.png', False, True)
		self.lever_shaft_rendered = None
		self.shaft_original_width = self.lever_shaft_original.get_width()
		self.shaft_original_height = self.lever_shaft_original.get_height()
		self.lever_shaft_fixed_bottom_y = 381
		self.lever_shaft_current_topleft_pos = [763, 0.0]
		self.lever_progress = 0.0
		self.lever_return_timer = 0.0
		self.lever_withdraw_duration = .2
		self.withdraw_return_initial_progress = 0.0
		self.lever_shadow_original = self.asset_manager.load_image('lever_shadow.png', True, True)
		self.lever_shadow_rendered = None

	def _init_lever_head(self):
		self.lever_head_original = self.asset_manager.load_image('lever_head.webp', True, True)
		self.lever_head_rect = self.lever_head_original.get_rect()
		self.lever_head_rendered = None
		self.lever_head_content_offset_x_in_padded = 2 # X offset of content within padded image
		self.lever_head_content_offset_y_in_padded = 2 # Y offset of content within padded image
		self.lever_head_content_width_original_hires = self.lever_head_rect.width - (2 * self.lever_head_content_offset_x_in_padded)
		self.lever_head_content_height_original_hires = self.lever_head_rect.height - (2 * self.lever_head_content_offset_y_in_padded)
		self.lever_head_content_target_onscreen_width = 42 
		self.lever_head_content_target_onscreen_height = 42
		self.base_downscale_factor_x = self.lever_head_content_target_onscreen_width / self.lever_head_content_width_original_hires
		self.base_downscale_factor_y = self.lever_head_content_target_onscreen_height / self.lever_head_content_height_original_hires
		self.base_downscale_factor = self.base_downscale_factor_y
		self.lever_head_default_topleft_x = 746
		self.lever_head_default_topleft_y = 158
		self.lever_head_content_default_bottom_y = self.lever_head_default_topleft_y + self.lever_head_content_target_onscreen_height
		self.lever_head_max_y_drop_of_bottom = 140
		self.lever_min_scale_animation = 1.0
		self.lever_max_scale_animation = 1.2
		self.lever_scale_animation_range = self.lever_max_scale_animation - self.lever_min_scale_animation
		self.lever_y_easing_func = lambda t: t * t
		self.lever_scale_easing_func = lambda t: t * (2 - t)
		self.lever_head_current_scale_factor = self.lever_min_scale_animation
		self.lever_head_current_topleft_pos = [0.0, 0.0]

	def _init_reels(self):
		self.reel_viewport_width = 89
		self.reel_viewport_height = 163
		self.blank_height = 29
		self.reel_positions = [(394, 172), (503, 172), (612, 172)]
		self.symbol_images = {}
		self.symbol_images['□'] = pygame.Surface((89, self.blank_height))
		self.symbol_images['□'].fill(pygame.Color("#fffcf9"))
		self.symbol_images['🍒'] = self.asset_manager.load_image('symbol_cherry.webp', False, True)
		self.symbol_images['-'] = self.asset_manager.load_image('symbol_bar_1.webp', False, True)
		self.symbol_images['='] = self.asset_manager.load_image('symbol_bar_2.webp', False, True)
		self.symbol_images['≡'] = self.asset_manager.load_image('symbol_bar_3.webp', False, True)
		self.symbol_images['7'] = self.asset_manager.load_image('symbol_seven.webp', False, True)
		self.symbol_images['💋'] = self.asset_manager.load_image('symbol_wild.webp', False, True)
		self.parsed_paytable = self.parse_paytable_data(SlotGameScreen.RAW_PAYTABLE)
		self.visual_strips_data = [
			['-', '□', '≡', '□', '🍒', '□', '=', '□', '-', '□', '7', '□', '≡', '□', '=', '□', '-', '□', '💋', '□', '🍒', '□'],
			['🍒', '□', '-', '□', '=', '□', '🍒', '□', '≡', '□', '=', '□', '7', '□', '-', '□', '🍒', '□', '💋', '□', '-', '□'],
			['=', '□', '-', '□', '🍒', '□', '-', '□', '7', '□', '🍒', '□', '=', '□', '-', '□', '≡', '□', '💋', '□', '🍒', '□']
		]
		self.logical_strips_compositions = [
			{'💋':1, '7':9, '≡':9, '=': 9, '-':26, '🍒': 1, '□':9}, # Reel 1 (e.g., 64 stops total) - More "action"
			{'💋':1, '7':1, '≡':1, '=':6, '-':41, '🍒':1, '□':45}, # Reel 2 (e.g., 96 stops total) - A bit tighter
			{'💋':1, '7':1, '≡':1, '=':3, '-':22, '🍒':10, '□':90} # Reel 3 (e.g., 128 stops total) - Controls top payouts, fewer high symbols
		]
		self.logical_strips_data = []
		for r_idx, composition in enumerate(self.logical_strips_compositions):
			current_strip = []
			for symbol, count in composition.items():
				current_strip.extend([symbol] * count) # Add the symbol to the strip 'count' number of times
			self.logical_strips_data.append(current_strip)
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
		self.reel_result = None
		self.reel_current_ys = [0.0] * SlotGameScreen.REEL_COUNT
		self.reel_target_ys = [0.0] * SlotGameScreen.REEL_COUNT
		# Animation parameters
		self.all_spin_duration = .6  # seconds all reels spin freely
		self.pause_duration_1 = 0.2       # seconds pause after reel 0 stops
		self.pause_duration_2 = 0.2       # seconds pause after reel 1 stops
		self.spin_speed_normal = self.reel_viewport_height * 8 # pixels per second during free spin / approaching target
		self.bounce_back_speed_factor = .1
		self.overshoot_height = self.blank_height / 2.0
		self.stop_timer = 0.0

	def _init_attendant(self):
		self.attendant = self.asset_manager.load_image('att0.webp', True, False)
		self.arousal = 0
		self.undress_1 = 25
		self.undress_2 = 50
		self.undress_3 = 75
		self.undress_4 = 125
		self.undress_5 = 175
		self.undress_xxx = 250

	def _init_ui(self):
		self.libre_baskerville_36 = self.asset_manager.load_font("LibreBaskerville-Bold.ttf", 36)
		self.money_text_surface = None
		self.money_text_rect = None
		self.dseg7_36 = self.asset_manager.load_font("DSEG7Classic-Regular.ttf", 36)
		self.bet_text_surface = None
		self.bet_text_rect = None
		self.win_amount = 0
		self.win_text_surface = None
		self.win_text_rect = None
		self.bet_plus = ButtonImage(self.asset_manager.load_image('bet_plus.webp', True, True), 319, 416, None, None, self._increment_bet)
		self.bet_minus = ButtonImage(self.asset_manager.load_image('bet_minus.webp', True, True), 487, 416, None, None, self._decrement_bet)
		self.bet_max = ButtonImage(self.asset_manager.load_image('bet_max.webp', True, True), 656, 416, None, None, self._maximize_bet)
		self.sperm_bank_sign = ButtonBase(0, 0, 135, 116, self._to_sperm_bank)
	def _increment_bet(self):
		if self.game_data.increment_bet(SlotGameScreen.MAXIMUM_BET): self.test_machine_ready()
	def _decrement_bet(self):
		if self.game_data.decrement_bet(): self.test_machine_ready()
	def _maximize_bet(self):
		if self.game_data.set_bet(SlotGameScreen.MAXIMUM_BET, SlotGameScreen.MAXIMUM_BET): self.test_machine_ready()
	def _to_sperm_bank(self):
		self.set_next_screen('SpermBankScreen')
		self.request_end_screen()

	def parse_paytable_data(self, raw_data):
		parsed_table = []
		lines = raw_data.strip().split('\n')
		for line_number, raw_line_content in enumerate(lines):
			line = raw_line_content.strip()
			if not line: continue # Skip empty lines that might result from stripping
			parts = line.split(',')
			name = parts[2]
			payout = int(parts[1])
			combination_string = parts[0] # '💋💋7'
			combination_tuple = tuple(combination_string) # ('💋', '💋', '7')
			combination_canonical = self._iterable_to_canonical(combination_tuple) # (('7', 1), ('💋', 2))
			parsed_table.append({
				"combination_canonical": combination_canonical,
				"payout": payout,
				"name": name,
				"original_combo_str": combination_string
			})
		return parsed_table
	def _iterable_to_canonical(self, array_or_tuple):
		counter = Counter(array_or_tuple) # {'💋': 2, '7': 1}
		return tuple(sorted(counter.items()))

	def calculate_rtp(self):
		logger.info("Calculating RTP...")
		total_payouts = 0.0
		len_reel0 = len(self.logical_strips_data[0])
		len_reel1 = len(self.logical_strips_data[1])
		len_reel2 = len(self.logical_strips_data[2])
		total_possible_combinations = len_reel0 * len_reel1 * len_reel2
		total_combinations_processed = 0
		for idx0 in range(len_reel0):
			s1 = self.logical_strips_data[0][idx0]
			for idx1 in range(len_reel1):
				s2 = self.logical_strips_data[1][idx1]
				for idx2 in range(len_reel2):
					s3 = self.logical_strips_data[2][idx2]
					tuple = (s1, s2, s3)
					canonical = self._iterable_to_canonical(tuple)
					payout = self._get_payout_from_canonical(canonical)
					total_payouts += payout
					total_combinations_processed += 1
		if total_combinations_processed != total_possible_combinations: logger.warning(f"Mismatch in processed combinations ({total_combinations_processed}) vs. theoretical ({total_possible_combinations})")
		rtp_decimal = total_payouts / total_possible_combinations
		rtp_percentage = rtp_decimal * 100.0
		logger.info(f"Total Expected Payout Value (for 1 unit bet): {total_payouts}")
		logger.info(f"Total Possible Combinations: {total_possible_combinations}")
		logger.info(f"Calculated Theoretical RTP: {rtp_percentage:.4f}%")
		return rtp_percentage

	def test_machine_ready(self):
		if self.game_data.money >= self.game_data.bet:
			self.reset_device_initial()
			self.machine_state = MachineState.READY
		else:
			logger.info(f"Your holdings of ${self.game_data.money} is not enough to cover the bet of ${self.game_data.bet}.")

	def commit_and_roll(self):
		self.wager = self.game_data.place_bet()
		self.game_data.save()
		logical_indices = self.roll_logical_stops()
		self.reel_result = self.logical_to_symbols(logical_indices)
		visual_indices = self.symbols_to_visual(self.reel_result)
		self.determine_target_ys(visual_indices)
		self.spin_all_reels() # changes self.machine_state to MachineState.ALL_SPINNING

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
		logger.debug("Starting all reel spins.")
		self.machine_state = MachineState.ALL_SPINNING
		for i in range(len(self.reel_states)):
			self.reel_states[i] = ReelState.SPINNING_FREELY
		self.stop_timer = 0.0

	def on_enter(self):
		super().on_enter()
		visual_indices = self.symbols_to_visual(['7', '🍒', '💋'])
		self.determine_target_ys(visual_indices)
		self.current_to_target_ys()
		self.calc_lever(0.0)
		self.update_ui()

	def on_ready(self):
		super().on_ready()
		self.test_machine_ready()

	def on_exit(self):
		super().on_exit()

	def handle_event(self, event):
		base_event = super().handle_event(event)
		if base_event:
			self.bet_plus.handle_event(base_event)
			self.bet_minus.handle_event(base_event)
			self.bet_max.handle_event(base_event)
			self.sperm_bank_sign.handle_event(base_event)

	def _update_always(self, time_delta):
		self.update_reel_animations(time_delta)
		self.update_lever_return(time_delta)
		self.calc_lever(self.lever_progress)
		self.update_ui()

	def _update_interactive(self):
		super()._update_interactive()
		self.update_lever_by_device()

	def update_lever_by_device(self):
		if self.machine_state == MachineState.READY:
			self.lever_progress = max(0.0, min(1.0, self.device_delta / self.device_threshold))
			if self.lever_progress == 1:
				self.lever_return_timer = 0.0
				self.commit_and_roll()
			elif self.device.depth == 0 and self.device_delta > 0:
				self.lever_return_timer = 0.0
				self.withdraw_return_initial_progress = self.lever_progress
				self.machine_state = MachineState.WITHDRAW_RESET

	def update_lever_return(self, time_delta):
		if self.machine_state == MachineState.ALL_SPINNING: self._calc_lever_return(time_delta, self.all_spin_duration, 1.0)
		elif self.machine_state == MachineState.WITHDRAW_RESET:
			if self.lever_progress == 0: self.test_machine_ready()
			else: self._calc_lever_return(time_delta, self.lever_withdraw_duration * self.withdraw_return_initial_progress, self.withdraw_return_initial_progress)
	def _calc_lever_return(self, time_delta, duration, start_progress_for_return):
		self.lever_return_timer += time_delta
		return_progress = self.lever_return_timer / duration
		self.lever_progress = (1.0 - return_progress) * start_progress_for_return
		if return_progress >= 1.0: self.lever_progress = 0.0 # Snap to final position

	def calc_lever(self, progress):
		eased_progress_y = self.lever_y_easing_func(progress)
		eased_progress_scale = self.lever_scale_easing_func(progress)
		self.lever_head_current_animation_scale_factor = self.lever_min_scale_animation + (eased_progress_scale * self.lever_scale_animation_range)
		total_current_scale = self.base_downscale_factor * self.lever_head_current_animation_scale_factor
		self.lever_head_rendered = pygame.transform.rotozoom(self.lever_head_original, 0, total_current_scale)
		target_bottom_y_for_onscreen_content = self.lever_head_content_default_bottom_y + (eased_progress_y * self.lever_head_max_y_drop_of_bottom)
		current_head_scaled_content_height = self.lever_head_content_target_onscreen_height * self.lever_head_current_animation_scale_factor
		current_head_scaled_offset_y = self.lever_head_content_offset_y_in_padded * total_current_scale
		new_top_y_for_rendered_surface = target_bottom_y_for_onscreen_content - (current_head_scaled_offset_y + current_head_scaled_content_height)
		content_default_center_x_onscreen = self.lever_head_default_topleft_x + (self.lever_head_content_target_onscreen_width / 2.0)
		current_onscreen_content_width = self.lever_head_content_target_onscreen_width * self.lever_head_current_animation_scale_factor
		current_onscreen_padding_x = self.lever_head_content_offset_x_in_padded * total_current_scale
		new_top_x_for_rendered_surface = content_default_center_x_onscreen - (current_onscreen_padding_x + current_onscreen_content_width / 2.0)
		self.lever_head_current_topleft_pos[0] = round(new_top_x_for_rendered_surface)
		self.lever_head_current_topleft_pos[1] = round(new_top_y_for_rendered_surface)

		head_content_bottom_y = self.lever_head_current_topleft_pos[1] + current_head_scaled_offset_y + current_head_scaled_content_height
		shaft_top_y = round(head_content_bottom_y - 1)
		shaft_height = max(0,self.lever_shaft_fixed_bottom_y - shaft_top_y)
		self.lever_shaft_current_topleft_pos[1] = shaft_top_y
		self.lever_shaft_rendered = pygame.transform.scale(self.lever_shaft_original, (self.shaft_original_width, shaft_height))

		overall_gradient_alpha = int(eased_progress_y * 191)
		overall_gradient_alpha = max(0, min(255, overall_gradient_alpha)) # Clamp
		self.lever_shadow_rendered = pygame.transform.scale(self.lever_shadow_original, (self.shaft_original_width, shaft_height))
		self.lever_shadow_rendered.set_alpha(overall_gradient_alpha)

	def update_reel_animations(self, time_delta):
		if self.machine_state == MachineState.LOCKED or self.machine_state == MachineState.READY: return
		self.stop_timer += time_delta
		if self.machine_state == MachineState.ALL_SPINNING:
			if self.stop_timer >= self.all_spin_duration:
				self.machine_state = MachineState.STOPPING_REEL_0
				self.reel_states[0] = ReelState.OVERSHOOTING
				logger.debug("All spinning phase complete. Reel 0 overshooting target.")
				self.stop_timer = 0.0
		elif self.machine_state == MachineState.STOPPING_REEL_0:
			if self.reel_states[0] == ReelState.STOPPED:
				self.machine_state = MachineState.PAUSE_AFTER_REEL_0
				self.stop_sequence_timer = 0.0
				logger.debug("Reel 0 stopped. Pausing.")
		elif self.machine_state == MachineState.PAUSE_AFTER_REEL_0:
			if self.stop_timer >= self.pause_duration_1:
				self.machine_state = MachineState.STOPPING_REEL_1
				self.reel_states[1] = ReelState.OVERSHOOTING
				logger.debug("Pause after Reel 0 complete. Reel 1 overshooting target.")
				self.stop_timer = 0.0
		elif self.machine_state == MachineState.STOPPING_REEL_1:
			if self.reel_states[1] == ReelState.STOPPED:
				self.machine_state = MachineState.PAUSE_AFTER_REEL_1
				self.stop_timer = 0.0
				logger.debug("Reel 1 stopped. Pausing.")
		elif self.machine_state == MachineState.PAUSE_AFTER_REEL_1:
			if self.stop_timer >= self.pause_duration_2:
				self.machine_state = MachineState.STOPPING_REEL_2
				self.reel_states[2] = ReelState.OVERSHOOTING
				logger.debug("Pause after Reel 1 complete. Reel 2 overshooting target.")
				self.stop_timer = 0.0
		elif self.machine_state == MachineState.STOPPING_REEL_2:
			if self.reel_states[2] == ReelState.STOPPED:
				self.machine_state = MachineState.LOCKED
				self.stop_timer = 0.0
				logger.debug("All reels stopped. Machine locked.")
				self.evaluate_result()

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
						self.reel_states[i] = ReelState.STOPPED
						logger.debug(f"Reel {i}: Bounced to final target {final_y}. STOPPED.")
					else:
						self.reel_current_ys[i] += move_amount
						if self.reel_current_ys[i] >= cycle_height: self.reel_current_ys[i] -= cycle_height

	def evaluate_result(self):
		result_canonical = self._iterable_to_canonical(self.reel_result)
		paytable_entry = self._get_paytable_entry(result_canonical)
		if paytable_entry:
			multiplier = paytable_entry["payout"]
			self.win_amount = self.wager * multiplier
			logger.info(f'{paytable_entry["name"]} pays {multiplier}x.')
			self.game_data.win(self.win_amount)
			self.game_data.save()
			self.update_attendant()
		else:
			self.win_amount = 0
		self.wager = None
		self.test_machine_ready()
	def _get_paytable_entry(self, result_canonical):
		for winning_entry in self.parsed_paytable:
			if winning_entry['combination_canonical'] == result_canonical: return winning_entry
		return None
	def _get_payout_from_canonical(self, canonical):
		entry = self._get_paytable_entry(canonical)
		if entry: return entry['payout']
		else: return 0

	def update_ui(self):
		money_string = f"${self.game_data.money}"
		shadow_offset = 1
		money_text = self.libre_baskerville_36.render(money_string, True, (0, 255, 0))
		money_shadow = self.libre_baskerville_36.render(money_string, True, (0, 0, 0))
		self.money_text_surface = pygame.Surface((money_text.get_width()+shadow_offset, money_text.get_height()+shadow_offset), pygame.SRCALPHA)
		self.money_text_surface.blit(money_shadow, (0, 1))
		self.money_text_surface.blit(money_text, (1, 0))
		self.money_text_rect = self.money_text_surface.get_rect(midtop=(self.screen_surface.get_width() // 2, 0))
		self.bet_text_surface = self.dseg7_36.render(f"{self.game_data.bet}", True, (255, 0, 0))
		self.bet_text_rect = self.bet_text_surface.get_rect(topright=(417, 361))
		self.win_text_surface = self.dseg7_36.render(f"{self.win_amount}", True, (255, 0, 0))
		self.win_text_rect = self.win_text_surface.get_rect(topright=(781, 361))

	def update_attendant(self):
		self.arousal += self.win_amount
		if self.arousal >= self.undress_5: self.attendant = self.asset_manager.load_image('att5.webp', True, False)
		elif self.arousal >= self.undress_4: self.attendant = self.asset_manager.load_image('att4.webp', True, False)
		elif self.arousal >= self.undress_3: self.attendant = self.asset_manager.load_image('att3.webp', True, False)
		elif self.arousal >= self.undress_2: self.attendant = self.asset_manager.load_image('att2.webp', True, False)
		elif self.arousal >= self.undress_1: self.attendant = self.asset_manager.load_image('att1.webp', True, False)

	def _render_content(self):
		self.screen_surface.blit(self.background, (0, 0))
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
		self.screen_surface.blit(self.lever_shaft_rendered, self.lever_shaft_current_topleft_pos)
		self.screen_surface.blit(self.lever_shadow_rendered, self.lever_shaft_current_topleft_pos)
		self.screen_surface.blit(self.lever_head_rendered, self.lever_head_current_topleft_pos)
		self.screen_surface.blit(self.attendant,(-50, -41))
		self.screen_surface.blit(self.money_text_surface, self.money_text_rect)
		self.screen_surface.blit(self.digital_panel, (319, 348))
		self.screen_surface.blit(self.bet_text_surface, self.bet_text_rect)
		self.screen_surface.blit(self.win_text_surface, self.win_text_rect)
		self.bet_plus.render(self.screen_surface)
		self.bet_minus.render(self.screen_surface)
		self.bet_max.render(self.screen_surface)
