#button_text.py
import pygame

from src.components.button_base import ButtonBase

class ButtonText(ButtonBase):
	"""
	A button with a fixed bounding box. Text is always centered within this box.
	- Up state: Text only, centered in the box.
	- Down state: Text with a background color that fills the box.
	- Can be initialized with or without text.
	"""
	def __init__(self, x, y, width, height, font, text_color=(0, 0, 0),
				 down_bg_color=(255, 255, 224), on_click=None, on_click_args=None):
		super().__init__(x, y, width, height, on_click, on_click_args)
		self.font = font
		self.text_color = text_color
		self.down_bg_color = down_bg_color
		self.text_surfaces = []
		self.text_rects = []

	def set_text(self, new_text):
		self.text_surfaces.clear()
		self.text_rects.clear()
		if not new_text: return
		lines = new_text.split('\n')
		# Calculate the starting Y position to center the whole block of text
		line_height = self.font.get_linesize()
		total_text_height = len(lines) * line_height
		start_y = self.rect.centery - (total_text_height / 2)
		for i, line in enumerate(lines):
			line_surface = self.font.render(line, True, self.text_color) # Render each line individually
			line_rect = line_surface.get_rect( # Position each line. Each line is centered horizontally. The vertical position is calculated from the block's start_y.
				centerx = self.rect.centerx,
				top = start_y + (i * line_height)
			)
			self.text_surfaces.append(line_surface)
			self.text_rects.append(line_rect)
			
	def _render_up_state(self, screen):
		for surface, rect in zip(self.text_surfaces, self.text_rects):
			screen.blit(surface, rect)

	def _render_down_state(self, screen):
		pygame.draw.rect(screen, self.down_bg_color, self.rect) # The background fills the entire fixed self.rect
		for surface, rect in zip(self.text_surfaces, self.text_rects):
			screen.blit(surface, rect)