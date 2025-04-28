import tkinter as tk
import socket
import threading
import time
import logging

# Configure logging
logger = logging.getLogger('orifice.slider')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class SliderServer:
    def __init__(self, host='127.0.0.1', port=12345):
        logger.info(f"Initializing SliderServer on {host}:{port}")
        self.host = host
        self.port = port
        self.depth_value = 0  # Starting at 0 instead of 512
        self.last_sent_value = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            logger.info(f"Socket bound to {host}:{port}")
            self.server_socket.listen(1)
            logger.debug("Socket listening for connections")
        except Exception as e:
            logger.error(f"Failed to bind socket: {e}")
            raise
            
        self.running = True
        self.clients = []
        
    def start(self):
        logger.info("Starting server connection thread")
        self.thread = threading.Thread(target=self.accept_connections)
        self.thread.daemon = True
        self.thread.start()
        
    def accept_connections(self):
        logger.info("Waiting for client connections")
        while self.running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                logger.info(f"Client connected from {client_addr}")
                client_socket.setblocking(0)  # Non-blocking socket
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, client_addr))
                client_handler.daemon = True
                client_handler.start()
                self.clients.append(client_socket)
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"Error accepting connection: {e}")
                time.sleep(0.1)
                
    def handle_client(self, client_socket, client_addr):
        logger.info(f"Handling client from {client_addr}")
        try:
            while self.running:
                # Only send if value has changed or not sent before
                if self.depth_value != self.last_sent_value:
                    try:
                        message = str(self.depth_value).encode()
                        client_socket.sendall(message)
                        logger.debug(f"Sent depth {self.depth_value} to {client_addr}")
                        self.last_sent_value = self.depth_value
                    except BlockingIOError:
                        # Socket would block, just continue
                        pass
                    except Exception as e:
                        logger.error(f"Error sending to client {client_addr}: {e}")
                        break
                time.sleep(0.01)  # Faster update rate (100Hz)
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            logger.info(f"Client {client_addr} disconnected")
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            try:
                client_socket.close()
            except Exception as e:
                logger.error(f"Error closing client socket: {e}")
            
    def update_depth(self, value):
        value = int(value)
        if value != self.depth_value:
            logger.debug(f"Depth value updated to {value}")
            self.depth_value = value
        
    def stop(self):
        logger.info("Stopping server")
        self.running = False
        
        # Close all client connections
        for client in self.clients[:]:
            try:
                client.close()
                logger.debug("Closed client connection")
            except:
                pass
            self.clients.remove(client)
            
        # Close server socket
        try:
            self.server_socket.close()
            logger.debug("Server socket closed")
        except Exception as e:
            logger.error(f"Error closing server socket: {e}")

def main():
    logger.info("Starting Orifice Slider Simulator")
    root = tk.Tk()
    root.title("Orifice Depth Simulator")
    
    # Wider window
    root.geometry("200x420")
    logger.debug("Window configured")
    
    # Configure a custom style for the slider
    root.option_add("*Slider.Width", 40)  # Wider slider
    
    # Create frame for the slider to give it some padding
    slider_frame = tk.Frame(root, padx=20, pady=20)
    slider_frame.pack(fill=tk.BOTH, expand=True)
    
    try:
        server = SliderServer()
        server.start()
        logger.info("Server started successfully")
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        tk.messagebox.showerror("Error", f"Failed to start server: {e}")
        root.destroy()
        return
    
    # Create a wider slider with a custom style
    slider = tk.Scale(
        slider_frame, 
        from_=1024, 
        to=0, 
        orient=tk.VERTICAL, 
        length=380,
        width=40,  # Wider slider
        sliderlength=40,  # Bigger handle
        command=server.update_depth,
        font=("Arial", 12, "bold"),
        troughcolor="#d0d0d0",
        activebackground="#4080ff"
    )
    slider.set(0)  # Start at 0 (fully retracted)
    slider.pack(fill=tk.BOTH, expand=True)
    logger.debug("Slider UI configured")
    
    # Add a label to show the current value
    value_label = tk.Label(
        root, 
        text="Depth: 0", 
        font=("Arial", 14, "bold"),
        pady=10
    )
    value_label.pack()
    
    # Update label when slider changes
    def update_label(value):
        value_label.config(text=f"Depth: {value}")
        server.update_depth(value)
    
    # Connect the update function
    slider.config(command=update_label)
    
    def on_closing():
        logger.info("Application closing")
        server.stop()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    logger.info("Entering main loop")
    root.mainloop()
    logger.info("Application terminated")

if __name__ == "__main__":
    main()
