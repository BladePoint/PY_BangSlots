"""
Orifice API - Simulation/Mock Implementation

This is a MOCK implementation of the Orifice API for development and testing purposes.

In a production environment:
- The actual Orifice hardware device would be used instead of the slider simulator
- The device's physical sensor would provide real depth/penetration measurements
- All socket/simulator code would be replaced with calls to the device's native API

This implementation provides:
1. A fallback simulator UI when no joystick is found (for development without hardware)
2. A consistent API interface that works the same in both mock and real environments

Usage:
    device = orifice.Orifice()
    depth = device.depth  # 0-1024 range
    # Remember to call device.close() when done
"""

import pygame
import subprocess
import os
import socket
import threading
import time
import logging

# Configure logging
logger = logging.getLogger('orifice.api')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class Orifice:
    """
    Interface to the Orifice device (mock implementation)
    
    This class provides access to depth/penetration values either from:
    - A connected joystick (simulating a hardware device)
    - The slider simulator (when no joystick is present)
    
    In production deployment, this would connect to the actual Orifice
    hardware and its depth sensor, not a simulator.
    """
    
    def __init__(self, host='127.0.0.1', port=12345):
        """
        Initialize the Orifice interface
        
        Args:
            host (str): Host for simulator socket connection (mock mode only)
            port (int): Port for simulator socket connection (mock mode only)
        """
        logger.info("Initializing Orifice API")
        pygame.init()
        pygame.joystick.init()

        self.joystick_available = False
        self.depth_value = 0
        self.socket_connected = False
        self.running = True
        self._depth_lock = threading.Lock()  # Thread safety

        if pygame.joystick.get_count() > 0:
            # Using joystick as input method (closer to real hardware)
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.joystick_available = True
            logger.info(f"Using joystick: {self.joystick.get_name()}")
        else:
            # No joystick: launch slider simulator
            # NOTE: In production, this would connect to the actual device instead
            logger.info("No joystick found, launching slider simulator")
            try:
                subprocess.Popen(["python3", "api/slider_simulator.py"])
                logger.debug("Slider simulator process started")
            except Exception as e:
                logger.error(f"Failed to start slider simulator: {e}")
                
            # Give the server a moment to start
            time.sleep(0.2)
            
            # Start socket connection in a separate thread
            logger.debug(f"Connecting to simulator on {host}:{port}")
            self.client_thread = threading.Thread(target=self.connect_to_server, args=(host, port))
            self.client_thread.daemon = True
            self.client_thread.start()
            logger.debug("Client connection thread started")

    def connect_to_server(self, host, port):
        """
        Connect to the slider simulator socket server
        
        Note: This method only exists in the mock implementation.
        A real deployment would connect to physical hardware instead.
        
        Args:
            host (str): Host address for simulator
            port (int): Port for simulator
        """
        logger.debug(f"Attempting to connect to simulator at {host}:{port}")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(0.1)  # Short timeout for responsiveness
        
        # Try to connect with retries
        for attempt in range(5):
            try:
                self.client_socket.connect((host, port))
                self.socket_connected = True
                logger.info(f"Connected to simulator on attempt {attempt+1}")
                break
            except socket.error as e:
                logger.warning(f"Connection attempt {attempt+1} failed: {e}")
                time.sleep(0.2)
                
        if self.socket_connected:
            logger.info("Setting socket to non-blocking mode")
            self.client_socket.setblocking(0)  # Non-blocking for better performance
            buffer = ""
            
            while self.running:
                try:
                    data = self.client_socket.recv(1024).decode()
                    if data:
                        buffer += data
                        # Process complete messages
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            try:
                                with self._depth_lock:
                                    new_value = int(line)
                                    logger.debug(f"Received depth value: {new_value}")
                                    self.depth_value = new_value
                            except ValueError:
                                logger.error(f"Received invalid depth value: '{line}'")
                        # If no newline but we have data, process it
                        if buffer:
                            try:
                                with self._depth_lock:
                                    new_value = int(buffer)
                                    logger.debug(f"Received depth value: {new_value}")
                                    self.depth_value = new_value
                                buffer = ""
                            except ValueError:
                                pass  # Incomplete number, wait for more data
                except BlockingIOError:
                    # No data available right now, no problem
                    time.sleep(0.001)
                except Exception as e:
                    # Other errors, including disconnection
                    logger.error(f"Socket error: {e}")
                    time.sleep(0.01)
        else:
            logger.error("Failed to connect to simulator after 5 attempts")

    def get_depth(self):
        """
        Get the current depth/penetration value
        
        In the real implementation, this would read from the physical device.
        
        Returns:
            int: Depth value between 0-1024
        """
        if self.joystick_available:
            pygame.event.pump()
            y_axis = self.joystick.get_axis(1)  # always -1.0 to 1.0
            y_axis = max(-1.0, min(1.0, y_axis))  # Clamp it clean
            penetration = int((y_axis + 1.0) * 512)  # Map to 0–1024
            logger.debug(f"Joystick depth value: {penetration}")
            return penetration
        else:
            with self._depth_lock:
                logger.debug(f"Simulator depth value: {self.depth_value}")
                return self.depth_value

    @property
    def depth(self):
        """
        Current depth/penetration value (0-1024)
        
        Returns:
            int: Depth value between 0-1024, where:
                 0 = fully retracted
                 1024 = fully inserted
        """
        return self.get_depth()

    def close(self):
        """
        Close the connection to the device and clean up resources
        
        This method should always be called when done using the device.
        """
        logger.info("Closing Orifice API connection")
        self.running = False
        if hasattr(self, 'client_socket') and self.socket_connected:
            try:
                self.client_socket.close()
                logger.debug("Socket connection closed")
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        pygame.quit()
        logger.debug("Pygame resources released")
