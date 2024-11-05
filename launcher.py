import tkinter as tk
from tkinter import filedialog, Menu
from PIL import Image, ImageTk
import json
import os
import shutil
import subprocess
import platform

# Ensure the "artwork" folder exists
if not os.path.exists("artwork"):
    os.makedirs("artwork")

# Create the main window
root = tk.Tk()
root.title("Game Launcher")
root.geometry("300x300")

# Frame to hold game buttons
games_frame = tk.Frame(root)
games_frame.pack(pady=10)

# Load games from JSON and display them as buttons with artwork if available
def load_games():
    # Clear existing buttons
    for widget in games_frame.winfo_children():
        widget.destroy()

    # Load games from JSON
    if os.path.exists("games.json"):
        try:
            with open("games.json", "r") as file:
                data = json.load(file)
            games = data.get("games", [])
        except json.JSONDecodeError:
            print("Error: games.json is empty or corrupted. Reinitializing the file.")
            data = {"games": []}
            with open("games.json", "w") as file:
                json.dump(data, file, indent=4)
            games = data["games"]
    else:
        # If games.json does not exist, initialize it with empty structure
        data = {"games": []}
        with open("games.json", "w") as file:
            json.dump(data, file, indent=4)
        games = data["games"]

    # Create a button for each game
    for game in games:
        artwork_path = game.get("artwork")
        
        # Display the game button with artwork if available
        if artwork_path and os.path.exists(artwork_path):
            img = Image.open(artwork_path)
            img.thumbnail((100, 100))  # Resize image to fit button
            img = ImageTk.PhotoImage(img)
            game_button = tk.Button(games_frame, image=img, command=lambda path=game["path"]: launch_game(path))
            game_button.image = img  # Keep a reference to prevent garbage collection
        else:
            game_button = tk.Button(games_frame, text=game["name"], command=lambda path=game["path"]: launch_game(path))
        
        game_button.pack(side=tk.LEFT, pady=5, padx=5)
        
        # Add an "Options" button for each game for additional actions
        options_button = tk.Button(games_frame, text="...", command=lambda g=game: show_options_menu(g))
        options_button.pack(side=tk.LEFT, pady=5)

# Function to launch the game
def launch_game(path):
    try:
        # Detect the operating system
        system = platform.system()
        
        if system == "Darwin" and path.endswith(".app"):
            # macOS-specific launch for .app bundles
            subprocess.Popen(["open", "-a", path])
        else:
            # General case for other executables
            subprocess.Popen(path, shell=True)
        
        root.quit()  # Close the launcher
        print(f"Launching game at {path}")
    except Exception as e:
        print(f"Failed to launch game at {path}: {e}")

# Function to handle game import
def add_game():
    system = platform.system()
    if system == "Windows":
        filetypes = [("Executable files", "*.exe"), ("All files", "*.*")]
    elif system == "Darwin":
        filetypes = [("Application files", "*.app"), ("All files", "*.*")]
    elif system == "Linux":
        filetypes = [("Executable files", "*.AppImage"), ("All files", "*.*")]
    else:
        filetypes = [("All files", "*.*")]

    game_path = filedialog.askopenfilename(title="Select Game Executable", filetypes=filetypes)
    
    if game_path:
        if os.path.exists("games.json"):
            with open("games.json", "r") as file:
                data = json.load(file)
        else:
            data = {"games": []}

        new_game = {
            "name": os.path.basename(game_path),
            "path": game_path,
            "artwork": "",
            "metadata": {
                "release_date": "",
                "description": ""
            }
        }
        data["games"].append(new_game)

        with open("games.json", "w") as file:
            json.dump(data, file, indent=4)

        print(f"Game '{new_game['name']}' added successfully!")
        load_games()

# Function to show an options menu for each game
def show_options_menu(game):
    options_window = tk.Toplevel(root)
    options_window.title("Options")
    options_window.geometry("250x200")

    # Add artwork option
    add_artwork_button = tk.Button(options_window, text="Add Artwork", command=lambda: add_artwork(game))
    add_artwork_button.pack(pady=5)

    # Edit Details option
    edit_details_button = tk.Button(options_window, text="Edit Details", command=lambda: edit_game_details(game))
    edit_details_button.pack(pady=5)

# Function to edit game details in a single window
def edit_game_details(game):
    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Game Details")
    edit_window.geometry("300x250")

    # Name field
    tk.Label(edit_window, text="Name:").pack(anchor="w", padx=10)
    name_entry = tk.Entry(edit_window, width=30)
    name_entry.insert(0, game["name"])
    name_entry.pack(padx=10, pady=5)

    # Release Date field
    tk.Label(edit_window, text="Release Date:").pack(anchor="w", padx=10)
    release_date_entry = tk.Entry(edit_window, width=30)
    release_date_entry.insert(0, game["metadata"].get("release_date", ""))
    release_date_entry.pack(padx=10, pady=5)

    # Description field
    tk.Label(edit_window, text="Description:").pack(anchor="w", padx=10)
    description_text = tk.Text(edit_window, width=30, height=4)
    description_text.insert("1.0", game["metadata"].get("description", ""))
    description_text.pack(padx=10, pady=5)

    # Save button
    save_button = tk.Button(edit_window, text="Save", command=lambda: save_game_details(game, name_entry.get(), release_date_entry.get(), description_text.get("1.0", "end-1c"), edit_window))
    save_button.pack(pady=10)

# Function to save edited game details
def save_game_details(game, new_name, new_release_date, new_description, edit_window):
    # Update game details
    game["name"] = new_name
    game["metadata"]["release_date"] = new_release_date
    game["metadata"]["description"] = new_description

    # Save the updated details to JSON
    with open("games.json", "r") as file:
        data = json.load(file)
    
    for g in data["games"]:
        if g["name"] == game["name"]:
            g.update(game)
            break
    
    with open("games.json", "w") as file:
        json.dump(data, file, indent=4)

    print(f"Details updated for game '{game['name']}'")
    edit_window.destroy()  # Close the edit window
    load_games()  # Refresh to display the updated name

# Function to add artwork to a game
def add_artwork(game):
    artwork_path = filedialog.askopenfilename(
        title="Select Artwork", 
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All files", "*.*")]
    )
    
    if artwork_path:
        artwork_filename = os.path.basename(artwork_path)
        new_artwork_path = os.path.join("artwork", artwork_filename)
        
        try:
            img = Image.open(artwork_path)
            img.verify()  # Verify the image is intact
            shutil.copy(artwork_path, new_artwork_path)
            game["artwork"] = new_artwork_path
            
            with open("games.json", "r") as file:
                data = json.load(file)
            
            for g in data["games"]:
                if g["name"] == game["name"]:
                    g["artwork"] = new_artwork_path
                    break
            
            with open("games.json", "w") as file:
                json.dump(data, file, indent=4)

            print(f"Artwork added for game '{game['name']}'")
            load_games()  # Refresh the game buttons
        except Exception as e:
            print(f"Failed to add artwork: {e}. Please ensure the file is a valid image.")

# Add a button for importing games
import_button = tk.Button(root, text="+", command=add_game)
import_button.pack(pady=10)

# Load games on startup
load_games()

# Run the window
root.mainloop()
