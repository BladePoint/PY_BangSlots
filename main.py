import pygame
import api.orifice as orifice
import json
import textwrap
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(stream=sys.stdout)]
)

# Get application logger
logger = logging.getLogger('orifice.app')
logger.info("Application starting")

# Load game info from JSON
try:
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

# Initialize Orifice device
try:
    logger.info("Initializing Orifice device")
    device = orifice.Orifice()
except Exception as e:
    logger.critical(f"Failed to initialize device: {e}")
    pygame.quit()
    sys.exit(1)

# Initialize Pygame Display
logger.info("Initializing Pygame")
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

# Fonts
try:
    title_font = pygame.font.SysFont(None, 64)
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    logger.debug("Fonts loaded")
except Exception as e:
    logger.error(f"Error loading fonts: {e}")
    title_font = font = small_font = pygame.font.SysFont(None, 24)  # Fallback

# Clock
clock = pygame.time.Clock()

# Pre-render static text
title_text = title_font.render(game_info["title"], True, (0, 0, 0))
version_text = small_font.render(f"Version: {game_info['version']}", True, (100, 100, 100))

# Pre-wrap description lines
description_lines = textwrap.wrap(game_info["description"], width=70)
desc_text_surfaces = [small_font.render(line, True, (80, 80, 80)) for line in description_lines]

# Main Loop
running = True
last_depth = -1  # Force first render
fps_update_time = 0
frame_count = 0
fps_display = "FPS: --"

logger.info("Entering main loop")
try:
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Quit event received")
                running = False

        # Get current depth
        try:
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
        
        # Only redraw the screen if depth changes or if 10 frames have passed
        if current_depth != last_depth or frame_count % 10 == 0:
            # Fill screen with white
            screen.fill((255, 255, 255))

            # Draw title and version (static content)
            screen.blit(title_text, (50, 30))
            screen.blit(version_text, (SCREEN_WIDTH - 150, 30))
            
            # Draw FPS
            fps_text = small_font.render(fps_display, True, (100, 100, 100))
            screen.blit(fps_text, (SCREEN_WIDTH - 150, 60))
            
            # Draw description
            for i, surface in enumerate(desc_text_surfaces):
                screen.blit(surface, (50, 100 + (i * 25)))

            # Draw depth as text
            depth_text = font.render(f"Depth: {current_depth}", True, (0, 0, 0))
            screen.blit(depth_text, (50, 200))

            # Draw depth bar visualization
            bar_height = int((current_depth / 1024) * 200)  # Smaller bar height
            pygame.draw.rect(screen, (0, 0, 255), (SCREEN_WIDTH - 100, SCREEN_HEIGHT - bar_height, 50, bar_height))

            # Update display
            pygame.display.flip()
            
            if current_depth != last_depth:
                logger.debug(f"Depth updated: {current_depth}")
                
            last_depth = current_depth
        
        # Limit frame rate but ensure we process events even if not redrawing
        clock.tick(120)  # Higher frame rate limit for input responsiveness
        
except Exception as e:
    logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
finally:
    # Clean up
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