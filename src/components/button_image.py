#button_image.py
import pygame

from src.components.button_base import ButtonBase

class ButtonImage(ButtonBase):
	def __init__(self, bg_image, x=0, y=0, width=None, height=None, on_click=None, on_click_args=None):
		self.bg_image = bg_image
		image_width = bg_image.get_width()
		image_height = bg_image.get_height()
		self.width = width or image_width
		self.height = height or image_height
		if self.width != image_width or self.height != image_height: self.bg_image = pygame.transform.scale(bg_image, (self.width, self.height))
		super().__init__(x, y, self.width, self.height, on_click, on_click_args)

	def _render_up_state(self, screen):
		screen.blit(self.bg_image, self.rect)

	def _render_down_state(self, screen):
		screen.blit(self.bg_image, (self.rect.x, self.rect.y+1))