# base_screen.py
import pygame
import logging

logger = logging.getLogger(__name__)

class BaseScreen:

	def __init__(self, screen_surface, device, asset_manager, game_data):
		self.screen_surface = screen_surface
		self.device = device
		self.asset_manager = asset_manager
		self.game_data = game_data
		self.screen_rect = screen_surface.get_rect()

		self.device_initial = 0.0
		self.device_delta = 0.0
		self.device_threshold = 512.0

		self.next_screen_name = None
		self.end_screen_requested = False

		self.is_transitioning = False
		self.is_blackening = False
		self.fade_alpha = 0
		self.fade_duration = None  # seconds
		self.fade_timer = 0
		self.fade_surface = pygame.Surface(self.screen_rect.size)
		self.fade_surface.fill((0, 0, 0))
		self.on_fade_complete = None

	def set_next_screen(self, screen_name):
		self.next_screen_name = screen_name

	def request_end_screen(self, next_screen_name=None):
		if not self.end_screen_requested and not self.is_transitioning:
			if self.next_screen_name is None:
				logger.warning(f"{self.__class__.__name__} requested end scene, but next_screen_name is not set!")
				return
			self.end_screen_requested = True
			if next_screen_name is not None: self.next_screen_name = next_screen_name
			logger.debug(f"{self.__class__.__name__} requested end. Next: {self.next_screen_name}")

	def fade_from_black(self, duration=0.5, on_complete=None):
		self._fade_transition(False, duration, on_complete)

	def fade_to_black(self, duration=0.5, on_complete=None):
		self._fade_transition(True, duration, on_complete)
		
	def _fade_transition(self, is_blackening, duration=0.5, on_complete=None):
		self.is_blackening = is_blackening
		self.fade_duration = duration
		self.on_fade_complete = on_complete
		self.fade_timer = 0
		if duration <= 0: # Handle instant transition
			self._complete_fade()
		else:
			self.is_transitioning = True
			self.fade_alpha = 0 if self.is_blackening else 255

	def _update_fade(self, time_delta):
		if self.is_transitioning:
			self.fade_timer += time_delta
			progress = min(1.0, self.fade_timer / self.fade_duration if self.fade_duration > 0 else 1.0)
			if self.is_blackening: self.fade_alpha = int(progress * 255)
			else: self.fade_alpha = int((1.0 - progress) * 255)
			self.fade_alpha = max(0, min(255, self.fade_alpha)) # Clamp alpha
			if self.fade_timer >= self.fade_duration: self._complete_fade()

	def _complete_fade(self):
		self.is_transitioning = False
		self.fade_alpha = 255 if self.is_blackening else 0
		if self.on_fade_complete:
			callback = self.on_fade_complete
			self.on_fade_complete = None
			callback()

	def _render_transition_overlay(self):
		if self.fade_alpha > 0: # Only blit if there's some opacity
			self.fade_surface.set_alpha(self.fade_alpha)
			self.screen_surface.blit(self.fade_surface, (0, 0))

	def reset_device_initial(self):
		self.device_initial = self.device.depth

	# --- Methods to be overridden by subclasses ---
	def handle_event(self, event):
		if self.is_transitioning or self.end_screen_requested: return None
		else: return event

	def update(self, time_delta):
		self._update_fade(time_delta)
		self._update_always(time_delta)
		if self.is_transitioning or self.end_screen_requested:
			return
		self._update_interactive(time_delta)

	def _update_always(self, time_delta): pass

	def _update_interactive(self, time_delta):
		self.device_delta = abs(self.device.depth - self.device_initial)

	def _render_content(self): pass

	def render(self):
		self._render_content()
		self._render_transition_overlay()

	def on_enter(self):
		logger.info(f"{self.__class__.__name__} entered.")
		self.next_screen_name = None
		self.end_screen_requested = False
		self.is_transitioning = False
		self.fade_alpha = 0

	def on_ready(self):
		logger.info(f"{self.__class__.__name__} ready.")
		self.reset_device_initial()

	def on_exit(self):
		logger.info(f"{self.__class__.__name__} exited.")
		pass