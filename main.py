#main.py
import pygame
import json
import logging
import sys
import api.orifice as orifice

from pathlib import Path

from src.components.asset_manager import AssetManager
from src.components.game_data import GameData
from src.components.title_screen import TitleScreen
from src.components.slot_game_screen import SlotGameScreen
from src.components.sperm_bank_screen import SpermBankScreen

PROJECT_ROOT = Path(__file__).parent 
FADE_DURATION = .4

# --- Global Variables ---
screen_surface = None
device = None
asset_manager = AssetManager(PROJECT_ROOT)
game_data = GameData.load_or_create(PROJECT_ROOT)
current_screen = None
show_fps = False

SCREEN_CLASSES = {# Screen class mapping
    "TitleScreen": TitleScreen,
	"SlotGameScreen": SlotGameScreen,
	"SpermBankScreen": SpermBankScreen
    # "GameScreen": GameScreen, # Add other screen classes here
    # "ShopScreen": ShopScreen,
}

def new_screen(next_screen_name):
	global current_screen
	try:
		logger.info(f"Instantiating screen: {next_screen_name}")
		NewScreenClass = SCREEN_CLASSES.get(next_screen_name)
		if NewScreenClass:
			current_screen = NewScreenClass(screen_surface, device, asset_manager, game_data)
			current_screen.on_enter()
			current_screen.fade_from_black(FADE_DURATION, current_screen.on_ready)
		else:
			raise ValueError(f"Unknown screen class key: '{next_screen_name}'.")
	except Exception as e:
		logger.critical(f"Failed to initialize {next_screen_name}: {e}", exc_info=True)
		if device: device.close()
		pygame.quit()
		sys.exit(1)

def end_screen():
	current_screen.on_exit()
	new_screen(current_screen.next_screen_name)

logging.basicConfig( # Initialize logging
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[logging.StreamHandler(stream=sys.stdout)],
	force=True
)
logger = logging.getLogger(__name__)
logger.info("Application starting")

try: # Load game info from JSON
	logger.debug("Loading game info from JSON")
	with open('gameinfo.json', 'r') as f:
		game_info = json.load(f)
	logger.info(f"Loaded game: {game_info['title']} v{game_info['version']}")
except Exception as e:
	logger.error(f"Failed to load game info: {e}")
	game_info = {
		"title": "Depth Explorer",
		"description": "A visualization demo for Orifice hardware.",
		"version": "1.0.0"
	}
	logger.warning("Using default game info")

try: # Initialize Orifice device
	logger.info("Initializing Orifice device")
	device = orifice.Orifice()
except Exception as e:
	logger.critical(f"Failed to initialize device: {e}")
	pygame.quit()
	sys.exit(1)

try: # Initialize Pygame Display
	logger.info("Initializing Pygame")
	SCREEN_WIDTH, SCREEN_HEIGHT = 800, 480
	pygame.init()
	screen_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
	pygame.display.set_caption(game_info["title"])
	logger.debug("Pygame display initialized")
except Exception as e:
	logger.critical(f"Failed to initialize display: {e}")
	device.close()
	sys.exit(1)

try: # Initialize fonts
	small_font = pygame.font.SysFont(None, 24)
	asset_manager.load_font("LibreBaskerville-Bold.ttf", 36)
	asset_manager.load_font("DSEG7Classic-Regular.ttf", 36)
	asset_manager.load_font(None, 32, True)
except Exception as e:
	logger.error(f"Error loading fonts: {e}")

new_screen('TitleScreen')
clock = pygame.time.Clock() # Clock
running = True
fps_update_time = 0
frame_count = 0
fps_display = "FPS: --"

try: # Main Loop
	logger.info("Entering main loop")
	while running:
		time_delta = clock.tick(60) / 1000.0
		for event in pygame.event.get(): # Event handling
			if event.type == pygame.QUIT:
				logger.info("Quit event received")
				running = False
			if current_screen:
				current_screen.handle_event(event)
		if current_screen: # Update and Render
			current_screen.update(time_delta)
			current_screen.render() # Screen draws itself, then BaseScreen draws fade
		else: # This case should ideally not be reached if running is true
			screen_surface.fill((50, 0, 50)) # Dark purple error/fallback if no active screen
		if current_screen and current_screen.end_screen_requested and not current_screen.is_transitioning:
			current_screen.fade_to_black(FADE_DURATION, end_screen)
		if show_fps: # Calculate FPS every second
			frame_count += 1
			current_time = pygame.time.get_ticks()
			if current_time - fps_update_time > 1000:
				fps = frame_count
				fps_display = f"FPS: {fps}"
				logger.debug(f"FPS: {fps}")
				frame_count = 0
				fps_update_time = current_time
			fps_text = small_font.render(fps_display, True, (0, 255, 0))
			screen_surface.blit(fps_text, (10, 10)) # Blit at (10, 10)

		pygame.display.flip()
except Exception as e:
	logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
	
finally: # Clean up
	logger.info("Shutting down application")
	try:
		device.close()
		logger.debug("Device closed")
	except Exception as e:
		logger.error(f"Error closing device: {e}")
	try:
		pygame.quit()
		logger.debug("Pygame resources released")
	except Exception as e:
		logger.error(f"Error quitting pygame: {e}")
		
	logger.info("Application terminated")