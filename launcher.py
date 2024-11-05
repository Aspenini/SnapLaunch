import tkinter as tk
from tkinter import filedialog
import json
import os
import subprocess  # New import for launching games

# Create the main window
root = tk.Tk()
root.title("Game Launcher")
root.geometry("300x300")

# Frame to hold game buttons
games_frame = tk.Frame(root)
games_frame.pack(pady=10)

# Load games from JSON and display them as buttons
def load_games():
    # Clear existing buttons
    for widget in games_frame.winfo_children():
        widget.destroy()

    # Load games from JSON
    if os.path.exists("games.json"):
        with open("games.json", "r") as file:
            data = json.load(file)
            games = data.get("games", [])
            
            # Create a button for each game
            for game in games:
                game_button = tk.Button(games_frame, text=game["name"], command=lambda path=game["path"]: launch_game(path))
                game_button.pack(pady=5, fill="x")

# Function to launch the game
def launch_game(path):
    try:
        # Launch the game using subprocess
        subprocess.Popen(path, shell=True)  # `shell=True` might be necessary on Windows for certain paths
        root.quit()  # Close the launcher after launching the game
        print(f"Launching game at {path}")
    except Exception as e:
        print(f"Failed to launch game at {path}: {e}")

# Function to handle game import
def add_game():
    # Open a file dialog to select a game executable
    game_path = filedialog.askopenfilename(
        title="Select Game Executable",
        filetypes=(("Executable files", "*.exe"), ("All files", "*.*"))
    )
    
    # If a file was selected, save the path
    if game_path:
        # Load existing data or create a new dictionary if the file doesn’t exist
        if os.path.exists("games.json"):
            with open("games.json", "r") as file:
                data = json.load(file)
        else:
            data = {"games": []}

        # Add the new game path to the data
        new_game = {
            "name": os.path.basename(game_path),
            "path": game_path,
            "artwork": "",
            "metadata": {}
        }
        data["games"].append(new_game)

        # Save updated data back to the JSON file
        with open("games.json", "w") as file:
            json.dump(data, file, indent=4)

        print(f"Game '{new_game['name']}' added successfully!")

        # Reload games to display the new addition
        load_games()

# Add a button for importing games
import_button = tk.Button(root, text="+", command=add_game)
import_button.pack(pady=10)

# Load games on startup
load_games()

# Run the window
root.mainloop()
