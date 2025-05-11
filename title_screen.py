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

        # --- Wave Effect Parameters ---
        # Amplitude
        self.base_amplitude_x = 1.0  # Max pixels of horizontal shift (at the very bottom of water)
                                     # Reduced this a bit as an example starting point.
        self.amplitude_power_scale = 1.0 # Power for non-linear scaling (e.g., 1.5, 2.0, 2.5).
                                         # > 1.0 makes top much calmer, ramps up fast at bottom.

        # Frequency (how many wave crests)
        self.near_frequency_y = 0.2   # Wave frequency at the closest point (bottom of water region)
        self.far_frequency_y_factor = 1.8 # How much denser (multiplied) the waves are at the horizon (top of water)
                                       # e.g., 1.5 means 50% more waves at the horizon line.

        # Speed
        self.speed_x = 4           # How fast the wave pattern animates horizontally

        # --- Define Water Region (Bottom 20%) ---
        self.water_region_start_y = 412
        self.water_region_height = self.screen_height - self.water_region_start_y
        self.water_region_width = self.screen_width

        self.static_background_part = None
        self.original_water_np = None
        self.rippling_water_surface = None

        # Pre-calculate meshgrid for the water region
        # These will only be fully defined if image loading succeeds
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

            original_water_surface_part = full_background_image.subsurface(
                pygame.Rect(0, self.water_region_start_y, self.water_region_width, self.water_region_height)
            ).copy()
            temp_water_np = pygame.surfarray.array3d(original_water_surface_part)
            self.original_water_np = np.transpose(temp_water_np, (1, 0, 2)) # (height, width, 3)

            if self.water_region_height > 0 and self.water_region_width > 0:
                y_coords_water = np.arange(self.water_region_height)
                x_coords_water = np.arange(self.water_region_width)
                self.xx_water, self.yy_water = np.meshgrid(x_coords_water, y_coords_water)
            else: # Should not happen if water_region_height is > 0
                logger.warning("Water region has zero height or width, cannot create meshgrid.")


            self.rippling_water_surface = pygame.Surface((self.water_region_width, self.water_region_height), pygame.SRCALPHA)

        except Exception as e:
            logger.fatal(f"Could not load/process background. Path tried: {image_path if 'image_path' in locals() else 'N/A'}. Error: {e}", exc_info=True)
            self.static_background_part = pygame.Surface((self.screen_width, self.screen_height))
            self.static_background_part.fill((30, 30, 30)) # Dark gray fallback for the whole screen
            self.original_water_np = None
            self.rippling_water_surface = None
            logger.warning("TitleScreen using fallback background color.")

    def on_enter(self):
        logger.debug("TitleScreen on_enter called.")
        self.is_active = True
        self.time_offset = 0.0

    def on_exit(self):
        logger.debug("TitleScreen on_exit called.")
        self.is_active = False

    def handle_event(self, event):
        """
        Process Pygame events for this screen.
        For this basic version, we won't handle any events.
        """
        if not self.is_active:
            return None
        # No event handling for now, so just pass
        return None # No screen change requested

    def update(self, time_delta):
        if not self.is_active or self.original_water_np is None or self.xx_water is None:
            # Also check if meshgrid (xx_water) was initialized
            return

        self.time_offset += time_delta

        # --- Wave Calculation for the Water Region ---

        # 1. Calculate y_normalized (0 at top of water/horizon, 1 at bottom of water/near)
        if self.water_region_height > 1:
            y_normalized = self.yy_water / (self.water_region_height - 1.0)
        else:
            y_normalized = np.ones_like(self.yy_water) # Avoid division by zero if height is 1

        # 2. Calculate Amplitude Scale Factor with Power Scaling
        # (y_normalized ** power) makes it less pronounced at top, ramps up at bottom
        amplitude_scale_factor = y_normalized ** self.amplitude_power_scale

        # 3. Calculate Current Amplitude for Horizontal Displacement
        current_amplitude_x = self.base_amplitude_x * amplitude_scale_factor

        # 4. Calculate Current Frequency (Modulated by Perspective)
        # We want higher frequency (denser waves) at the horizon (y_normalized = 0)
        # and base frequency (near_frequency_y) near the viewer (y_normalized = 1)
        # So, when y_normalized = 0, freq_multiplier = self.far_frequency_y_factor
        # When y_normalized = 1, freq_multiplier = 1.0
        freq_multiplier = self.far_frequency_y_factor * (1.0 - y_normalized) + 1.0 * y_normalized
        current_frequency_y = self.near_frequency_y * freq_multiplier
        
        # 5. Calculate Horizontal Displacement
        displacement_x = current_amplitude_x * np.sin(current_frequency_y * self.yy_water + self.time_offset * self.speed_x)

        # 6. Calculate Source Coordinates
        source_x = (self.xx_water + displacement_x).astype(int)
        source_y = self.yy_water.astype(int) # No vertical displacement

        # 7. Clamp Coordinates
        source_x = np.clip(source_x, 0, self.water_region_width - 1)
        # source_y is already within bounds as it's not displaced and matches yy_water range.
        # But if you add vertical displacement, you'd clip source_y too:
        # source_y = np.clip(source_y, 0, self.water_region_height - 1)


        # 8. Fetch Pixels from the original_water_np
        rippling_array_data = self.original_water_np[source_y, source_x]

        # 9. Blit the NumPy array data to our dedicated rippling_water_surface
        pygame.surfarray.blit_array(self.rippling_water_surface, np.transpose(rippling_array_data, (1, 0, 2)))

    def render(self):
        if not self.is_active:
            return

        if self.static_background_part:
            self.screen.blit(self.static_background_part, (0, 0))
        else:
            self.screen.fill((30,30,30)) # Full fallback if static part is missing
            return

        if self.rippling_water_surface and self.original_water_np is not None:
            self.screen.blit(self.rippling_water_surface, (0, self.water_region_start_y))
        elif self.static_background_part is None and self.original_water_np is None: # If total fallback
            pass # Already filled screen
        # else:
            # Could draw a static placeholder for water if only water part failed
            # For now, if water part fails, it just won't draw anything extra there.