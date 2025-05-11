import pygame
import api.orifice as orifice
import json
import textwrap
import logging
import os
import sys
from datetime import datetime

from title_screen import TitleScreen

logging.basicConfig( # Configure logging
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(stream=sys.stdout)]
)
logger = logging.getLogger('orifice.app') # Get application logger
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

logger.info("Initializing Pygame") # Initialize Pygame Display
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 480
try:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption(game_info["title"])
    logger.debug("Pygame display initialized")
except Exception as e:
    logger.critical(f"Failed to initialize display: {e}")
    device.close()
    sys.exit(1)

try: # Fonts
    title_font = pygame.font.SysFont(None, 64)
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    logger.debug("Fonts loaded")
except Exception as e:
    logger.error(f"Error loading fonts: {e}")
    title_font = font = small_font = pygame.font.SysFont(None, 24)  # Fallback

clock = pygame.time.Clock() # Clock

title_text = title_font.render(game_info["title"], True, (0, 0, 0)) # Pre-render static text
version_text = small_font.render(f"Version: {game_info['version']}", True, (100, 100, 100))

description_lines = textwrap.wrap(game_info["description"], width=70) # Pre-wrap description lines
desc_text_surfaces = [small_font.render(line, True, (80, 80, 80)) for line in description_lines]

logger.info("Creating screen instances...")
title_screen_handler = TitleScreen(screen)
active_screen_handler = title_screen_handler
active_screen_handler.on_enter()

# Main Loop
running = True
last_depth = -1  # Force first render
fps_update_time = 0
frame_count = 0
fps_display = "FPS: --"

logger.info("Entering main loop")
try:
    while running:
        time_delta = clock.tick(120) / 1000.0
        for event in pygame.event.get(): # Event handling
            if event.type == pygame.QUIT:
                logger.info("Quit event received")
                running = False
            if active_screen_handler:
                active_screen_handler.handle_event(event)

        try: # Get current depth
            current_depth = device.depth
        except Exception as e:
            logger.error(f"Error getting depth: {e}")
            current_depth = last_depth if last_depth >= 0 else 0
            
        current_time = pygame.time.get_ticks()
        
        # Calculate FPS every second
        frame_count += 1
        if current_time - fps_update_time > 1000:
            fps = frame_count
            fps_display = f"FPS: {fps}"
            logger.debug(f"FPS: {fps}")
            frame_count = 0
            fps_update_time = current_time

        if active_screen_handler:
            active_screen_handler.update(time_delta)
            active_screen_handler.render()
            next_screen_signal = active_screen_handler.handle_event(event)
            if next_screen_signal == "START_GAME":
                logger.info("Received START_GAME signal from title screen.")
                # Here you would switch:
                # active_screen_handler.on_exit()
                # active_screen_handler = your_next_screen_handler_instance
                # active_screen_handler.on_enter()
                # For now, you could just set running = False to test
                # running = False
        else: # Fallback if no active screen, fill with a color
            screen.fill((50,0,50)) # Dark purple error/fallback
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