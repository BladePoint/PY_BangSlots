# title_screen.py
import pygame
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

class TitleScreen:
    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.is_active = False
        self.time_offset = 0.0

        # --- Wave Effect Parameters (Simplified Linear Scaling) ---
        # Amplitude: Scales linearly from 0 at the top of water to max_amplitude_at_bottom at the bottom.
        self.max_amplitude_at_bottom = 1.0  # Max pixels of horizontal shift at the very bottom.

        # Frequency: Scales linearly from horizon_frequency at top of water to near_frequency at bottom.
        self.horizon_frequency = 0.36  # Wave frequency at the furthest point (top of water region, 0.2 * 1.8 = 0.36)
        self.near_frequency = 0.24    # Wave frequency at the closest point (bottom of water region)
                                      # Higher value means waves are 'denser' or 'smaller' at horizon.
        # Speed
        self.speed_x = 2.0           # How fast the wave pattern animates horizontally

        # --- Define Water Region ---
        self.water_region_start_y = 412
        self.water_region_height = self.screen_height - self.water_region_start_y
        self.water_region_width = self.screen_width

        self.static_background_part = None
        self.original_water_np = None
        self.rippling_water_surface = None
        self.xx_water = None
        self.yy_water = None

        try:
            base_dir_for_title_screen = os.path.dirname(os.path.abspath(__file__))
            assets_path = os.path.join(base_dir_for_title_screen, 'assets', 'images')
            image_path = os.path.join(assets_path, 'title_background.jpg')
            logger.info(f"Attempting to load image from: {image_path}")

            full_background_image = pygame.image.load(image_path).convert()
            full_background_image = pygame.transform.scale(full_background_image, (self.screen_width, self.screen_height))
            logger.info(f"TitleScreen loaded full background image from: {image_path}")

            self.static_background_part = full_background_image.subsurface(
                pygame.Rect(0, 0, self.screen_width, self.water_region_start_y)
            ).copy()

            if self.water_region_height > 0: # Only process water if its region exists
                original_water_surface_part = full_background_image.subsurface(
                    pygame.Rect(0, self.water_region_start_y, self.water_region_width, self.water_region_height)
                ).copy()
                temp_water_np = pygame.surfarray.array3d(original_water_surface_part)
                self.original_water_np = np.transpose(temp_water_np, (1, 0, 2)) # (height, width, 3)

                if self.water_region_width > 0:
                    y_coords_water = np.arange(self.water_region_height)
                    x_coords_water = np.arange(self.water_region_width)
                    self.xx_water, self.yy_water = np.meshgrid(x_coords_water, y_coords_water)
                else:
                    logger.warning("Water region has zero width, cannot create meshgrid.")
                
                self.rippling_water_surface = pygame.Surface((self.water_region_width, self.water_region_height), pygame.SRCALPHA)
            else:
                logger.warning("Water region has zero height. No water effect will be applied.")
                self.original_water_np = None # Ensure it's None if no water region

        except Exception as e:
            logger.fatal(f"Could not load/process background. Path tried: {image_path if 'image_path' in locals() else 'N/A'}. Error: {e}", exc_info=True)
            self.static_background_part = pygame.Surface((self.screen_width, self.screen_height))
            self.static_background_part.fill((30, 30, 30))
            self.original_water_np = None
            self.rippling_water_surface = None
            logger.warning("TitleScreen using fallback background color.")

    def on_enter(self): # Same as before
        logger.debug("TitleScreen on_enter called.")
        self.is_active = True
        self.time_offset = 0.0

    def on_exit(self): # Same as before
        logger.debug("TitleScreen on_exit called.")
        self.is_active = False

    def handle_event(self, event): # Same as before
        if not self.is_active:
            return None
        if event.type == pygame.KEYDOWN: # Example event
            if event.key == pygame.K_SPACE:
                return "START_GAME"
        return None

    def update(self, time_delta):
        if not self.is_active or self.original_water_np is None or self.xx_water is None:
            return

        self.time_offset += time_delta

        # --- Wave Calculation for the Water Region (Linear Scaling) ---

        # 1. Calculate y_normalized (0 at top of water/horizon, 1 at bottom of water/near)
        if self.water_region_height > 1:
            y_normalized = self.yy_water / (self.water_region_height - 1.0)
        else:
            # If water_region_height is 1, y_normalized can be considered 1 (closest point)
            y_normalized = np.ones_like(self.yy_water)

        # 2. Calculate Current Amplitude (Linearly scaled by y_normalized)
        # Amplitude is 0 at horizon (y_normalized=0) and self.max_amplitude_at_bottom at near (y_normalized=1)
        current_amplitude_x = self.max_amplitude_at_bottom * y_normalized

        # 3. Calculate Current Frequency (Linearly interpolated)
        # Frequency is self.horizon_frequency at horizon (y_normalized=0)
        # and self.near_frequency at near (y_normalized=1)
        current_frequency_y = self.horizon_frequency * (1.0 - y_normalized) + self.near_frequency * y_normalized
        
        # 4. Calculate Horizontal Displacement
        displacement_x = current_amplitude_x * np.sin(current_frequency_y * self.yy_water + self.time_offset * self.speed_x)

        # 5. Calculate Source Coordinates
        source_x = (self.xx_water + displacement_x).astype(int)
        source_y = self.yy_water.astype(int)

        # 6. Clamp Coordinates
        source_x = np.clip(source_x, 0, self.water_region_width - 1)
        # source_y is already within bounds

        # 7. Fetch Pixels
        rippling_array_data = self.original_water_np[source_y, source_x]

        # 8. Blit to Surface
        pygame.surfarray.blit_array(self.rippling_water_surface, np.transpose(rippling_array_data, (1, 0, 2)))

    def render(self): # Same as before
        if not self.is_active:
            return

        if self.static_background_part:
            self.screen.blit(self.static_background_part, (0, 0))
        else:
            self.screen.fill((30,30,30))
            return

        if self.rippling_water_surface and self.original_water_np is not None:
            self.screen.blit(self.rippling_water_surface, (0, self.water_region_start_y))