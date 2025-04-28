# Bangchain App Store Starter

Welcome to the Bangchain App Store Starter! This is a template project to help you create interactive experiences using the Orifice hardware. Whether you're a seasoned developer or just starting out, this template will help you get up and running quickly.

## 🌟 What's This?

This is a starter template for creating games and interactive experiences that work with the Orifice hardware. It comes with a basic visualization demo that shows how to read depth values from the device.

## 🚀 Quick Start Guide

### For Everyone (Even Non-Programmers!)

1. **Install Python**: 
   - If you don't have Python installed, download it from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Install Required Software**:
   - Open your computer's command prompt or terminal
   - Type this command and press Enter:
     ```
     pip install pygame
     ```

3. **Run the Demo**:
   - Double-click the `main.py` file
   - Or open your command prompt/terminal, navigate to this folder, and type:
     ```
     python main.py
     ```

### For Developers

1. **Setup Virtual Environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```

## 🎮 Sample Vibe Coding Prompt

Here's a technical prompt you can use with code-writing LLMs:

```
Create an endless runner game in Python using Pygame with the following specifications:

Technical Requirements:
- Resolution: 800x480 pixels
- Fullscreen mode
- Target FPS: 60
- Use the Orifice depth sensor (0-1024 range) to control player vertical position

Game Elements:
- Player: 50x50 pixel white cube
- Obstacles: 30x30 pixel red squares
- Background: Black
- Score display: White text in top-right corner

Game Mechanics:
- Player cube moves vertically based on depth sensor input
- Obstacles spawn from right edge and move left at constant speed
- Collision detection between player and obstacles
- Score increases by 1 for each obstacle passed
- Game over on collision

Code Structure:
- Main game loop with depth sensor input handling
- Obstacle class with spawn and movement logic
- Collision detection system
- Score tracking and display
- Clean separation of game logic and rendering

Additional Features:
- Particle effects on collision
- Score persistence between games
- Visual feedback for depth sensor input
```

## 📁 Project Structure

- `main.py` - The main game file
- `gameinfo.json` - Game configuration and metadata
- `api/` - Contains the Orifice hardware interface
- `assets/` - Place your images, sounds, and other resources here
- `config/` - Configuration files
- `src/` - Additional source code files

## 🛠️ Customizing Your Game

1. Edit `gameinfo.json` to update your game's title, description, and other metadata
2. Add your own assets to the `assets` folder
3. Modify `main.py` to create your unique game experience
4. Use the Orifice API to create interactive elements based on depth input
