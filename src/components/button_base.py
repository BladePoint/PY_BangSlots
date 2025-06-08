#button_base.py
import pygame

class ButtonBase:
	"""
	An abstract base class for a 2-state touch button. It handles all the core logic:
	- Storing position and size in a Rect.
	- Managing the 'up' and 'down' states.
	- Processing touch events to change state and trigger actions.

	It does NOT know how to render itself. Subclasses MUST implement the _render_up_state and _render_down_state methods.
	"""
	UP = "up"
	DOWN = "down"

	def __init__(self, x, y, width, height, on_click=None, on_click_args=None):
		self.rect = pygame.Rect(x, y, width, height)
		self.state = ButtonBase.UP
		self.on_click = on_click
		self.on_click_args = on_click_args if on_click_args is not None else []
		self.enabled = True

	def handle_event(self, event):
		if not self.enable: return
		if event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1 and self.rect.collidepoint(event.pos): self.state = ButtonBase.DOWN # Check if the press is within the button's area
		elif event.type == pygame.MOUSEBUTTONUP:
			if event.button == 1 and self.state == ButtonBase.DOWN: # Check if the button was in a 'down' state
				if self.rect.collidepoint(event.pos): # Check if the release is still within the button's area to trigger the action
					if self.on_click: self.on_click(*self.on_click_args) # Trigger the action
				self.state = ButtonBase.UP # The button always returns to the 'up' state on release, regardless of where the finger was lifted.

	def render(self, screen):
		if self.state == ButtonBase.UP: self._render_up_state(screen)
		else: self._render_down_state(screen)
	
	def _render_up_state(self, screen): pass

	def _render_down_state(self, screen): pass
	
	def enable(self): self.enable = True
	def disable(self): self.enable = False