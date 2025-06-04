# asset_manager.py
import pygame
import os
import logging

logger = logging.getLogger(__name__)

class AssetManager:
	def __init__(self):
		project_root = os.path.dirname(os.path.abspath(__file__))
		assets_dir = 'assets' # Name of your main assets folder
		self.paths = {
			'images': os.path.join(project_root, assets_dir, 'images'),
			'sounds': os.path.join(project_root, assets_dir, 'sounds'),
			'music': os.path.join(project_root, assets_dir, 'music'),
			'fonts': os.path.join(project_root, assets_dir, 'fonts')
		}

	def get_path(self, asset_type, filename):
		if asset_type not in self.paths:
			logger.error(f"Unknown asset type: {asset_type}")
			return None
		return os.path.join(self.paths[asset_type], filename)

	def load_image(self, filename, use_alpha=True):
		image_path = self.get_path('images', filename)
		if not image_path or not os.path.exists(image_path):
			logger.error(f"Image file not found: {image_path} (filename: {filename})")
		logger.debug(f"Loading image from: {image_path}")
		try:
			image = pygame.image.load(image_path)
			image = image.convert_alpha() if use_alpha else image.convert()
			logger.info(f"Successfully loaded image: {filename}")
			return image
		except pygame.error as e:
			logger.error(f"Pygame error loading image '{filename}': {e}", exc_info=True)
		except Exception as e:
			logger.error(f"Unexpected error loading image '{filename}': {e}", exc_info=True)