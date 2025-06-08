# asset_manager.py
import pygame
import os
import logging

logger = logging.getLogger(__name__)

class AssetManager:
	def __init__(self, project_root):
		assets_dir = 'assets' # Name of your main assets folder
		self.paths = {
			'images': os.path.join(project_root, assets_dir, 'images'),
			'sounds': os.path.join(project_root, assets_dir, 'sounds'),
			'music': os.path.join(project_root, assets_dir, 'music'),
			'fonts': os.path.join(project_root, assets_dir, 'fonts')
		}
		self.loaded_images = {}
		self.loaded_sounds = {}
		self.loaded_fonts = {}

	def get_path(self, asset_type, filename):
		if asset_type not in self.paths:
			logger.error(f"Unknown asset type: {asset_type}")
			return None
		return os.path.join(self.paths[asset_type], filename)

	def load_image(self, filename, use_alpha=False, use_cache=False):
		if use_cache and filename in self.loaded_images:
			logger.debug(f"Returning cached image: {filename}")
			return self.loaded_images[filename]

		image_path = self.get_path('images', filename)
		if not image_path or not os.path.exists(image_path): logger.error(f"Image file not found: {image_path} (filename: {filename})")
		logger.debug(f"Loading image from: {image_path}")
		try:
			image = pygame.image.load(image_path)
			image = image.convert_alpha() if use_alpha else image.convert()
			if use_cache: self.loaded_images[filename] = image
			logger.info(f"Successfully loaded image: {filename}")
			return image
		except pygame.error as e:
			logger.error(f"Pygame error loading image '{filename}': {e}", exc_info=True)
		except Exception as e:
			logger.error(f"Unexpected error loading image '{filename}': {e}", exc_info=True)

	def load_font(self, font_filename_or_name, size, is_system_font=False):
		font_key = (font_filename_or_name, size, is_system_font)
		if font_key in self.loaded_fonts:
			logger.debug(f"Returning cached font: {font_filename_or_name} size {size}")
			return self.loaded_fonts[font_key]
		font_path = None
		if not is_system_font:
			font_path = self.get_path('fonts', font_filename_or_name)
			if not font_path or not os.path.exists(font_path):
				logger.error(f"Font file not found: {font_path} (filename: {font_filename_or_name}). Trying system font.")
				is_system_font = True # Fallback to trying as system font if file not found
		logger.debug(f"Loading font: {'System:' if is_system_font else ''}{font_filename_or_name} size {size}")
		try:
			if is_system_font: font = pygame.font.SysFont(font_filename_or_name, size)
			else: font = pygame.font.Font(font_path, size)
			self.loaded_fonts[font_key] = font
			logger.info(f"Successfully loaded font: {'System:' if is_system_font else ''}{font_filename_or_name} size {size}")
			return font
		except pygame.error as e:
			logger.error(f"Failed to load font '{font_filename_or_name}' size {size}: {e}", exc_info=True)
			try: # Fallback to a default system font
				logger.warning("Attempting to load default system font.")
				return pygame.font.SysFont(None, size) # Pygame's default font
			except Exception as e_fallback:
				logger.error(f"Failed to load default system font: {e_fallback}")
				return None # Absolute fallback
		except Exception as e:
			logger.error(f"Unexpected error loading font '{font_filename_or_name}' size {size}: {e}", exc_info=True)
			return None