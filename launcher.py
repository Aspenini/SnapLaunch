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
root.geometry("400x400")

# Main frame that will change content based on selection
content_frame = tk.Frame(root)
content_frame.pack(fill="both", expand=True)

# Utility function to format the artwork filename based on game name
def format_artwork_filename(game_name, extension):
    return game_name.replace(" ", "_").lower() + extension

# Load games from JSON and display them as buttons with artwork if available
def load_games():
    # Clear existing content
    for widget in content_frame.winfo_children():
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

    # Ensure artwork filenames match game names
    for game in games:
        if "artwork" in game and game["artwork"]:
            correct_name = format_artwork_filename(game["name"], os.path.splitext(game["artwork"])[1])
            correct_path = os.path.join("artwork", correct_name)
            if os.path.basename(game["artwork"]) != correct_name:
                # Rename artwork to match the game name
                os.rename(game["artwork"], correct_path)
                game["artwork"] = correct_path
                with open("games.json", "w") as file:
                    json.dump({"games": games}, file, indent=4)
                print(f"Renamed artwork for '{game['name']}' to match game name.")

    # Create a button for each game with left-click to launch and right-click for options
    for game in games:
        artwork_path = game.get("artwork")
        
        # Display the game button with artwork if available
        if artwork_path and os.path.exists(artwork_path):
            img = Image.open(artwork_path)
            img.thumbnail((100, 100))
            img = ImageTk.PhotoImage(img)
            game_button = tk.Label(content_frame, image=img)
            game_button.image = img  # Keep a reference to prevent garbage collection
        else:
            game_button = tk.Label(content_frame, text=game["name"])

        game_button.pack(pady=5, padx=5, fill="x")

        # Bind left-click to launch game
        game_button.bind("<Button-1>", lambda event, path=game["path"]: launch_game(path))

        # Bind right-click to show options
        game_button.bind("<Button-3>", lambda event, g=game: show_options_menu(event, g))

    # Add the "Add Game" button at the bottom of the window
    add_game_button = tk.Button(content_frame, text="Add Game", command=add_game)
    add_game_button.pack(pady=20)

# Function to launch the game
def launch_game(path):
    try:
        system = platform.system()
        
        if system == "Darwin" and path.endswith(".app"):
            subprocess.Popen(["open", "-a", path])
        else:
            subprocess.Popen(path, shell=True)
        
        root.quit()  # Close the launcher after launching the game
        print(f"Launching game at {path}")
    except Exception as e:
        print(f"Failed to launch game at {path}: {e}")

# Show options menu on right-click
def show_options_menu(event, game):
    # Create a right-click menu with options
    menu = Menu(root, tearoff=0)
    menu.add_command(label="Add Artwork", command=lambda: add_artwork(game))
    menu.add_command(label="View/Edit Details", command=lambda: show_game_details(game))
    menu.tk_popup(event.x_root, event.y_root)

# Show game details with a back button
def show_game_details(game):
    # Clear the frame and display game details
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Back button to return to the main launcher
    back_button = tk.Button(content_frame, text="Back", command=load_games)
    back_button.pack(anchor="ne", padx=10, pady=10)

    tk.Label(content_frame, text=f"Game: {game['name']}", font=("Arial", 14)).pack(pady=10)
    
    # Display release date and description as read-only by default
    tk.Label(content_frame, text="Release Date:").pack(anchor="w", padx=10)
    release_date_label = tk.Label(content_frame, text=game["metadata"].get("release_date", "N/A"))
    release_date_label.pack(anchor="w", padx=10)

    tk.Label(content_frame, text="Description:").pack(anchor="w", padx=10)
    description_label = tk.Label(content_frame, text=game["metadata"].get("description", "N/A"), wraplength=350, justify="left")
    description_label.pack(anchor="w", padx=10, pady=5)

    # Button to edit details
    edit_button = tk.Button(content_frame, text="Edit Details", command=lambda: edit_game_details(game))
    edit_button.pack(pady=10)

# Edit game details in the same window
def edit_game_details(game):
    for widget in content_frame.winfo_children():
        widget.destroy()

    tk.Label(content_frame, text="Edit Game Details", font=("Arial", 14)).pack(pady=10)

    # Name field
    tk.Label(content_frame, text="Name:").pack(anchor="w", padx=10)
    name_entry = tk.Entry(content_frame, width=30)
    name_entry.insert(0, game["name"])
    name_entry.pack(padx=10, pady=5)

    # Release Date field
    tk.Label(content_frame, text="Release Date:").pack(anchor="w", padx=10)
    release_date_entry = tk.Entry(content_frame, width=30)
    release_date_entry.insert(0, game["metadata"].get("release_date", ""))
    release_date_entry.pack(padx=10, pady=5)

    # Description field
    tk.Label(content_frame, text="Description:").pack(anchor="w", padx=10)
    description_text = tk.Text(content_frame, width=30, height=4)
    description_text.insert("1.0", game["metadata"].get("description", ""))
    description_text.pack(padx=10, pady=5)

    # Save button to save details and go back to the details view
    save_button = tk.Button(content_frame, text="Save", command=lambda: save_game_details(game, name_entry.get(), release_date_entry.get(), description_text.get("1.0", "end-1c")))
    save_button.pack(pady=10)

# Function to save edited game details
def save_game_details(game, new_name, new_release_date, new_description):
    # Update game details
    old_name = game["name"]
    game["name"] = new_name
    game["metadata"]["release_date"] = new_release_date
    game["metadata"]["description"] = new_description

    # Rename artwork if necessary
    if "artwork" in game and game["artwork"]:
        current_artwork_path = game["artwork"]
        extension = os.path.splitext(current_artwork_path)[1]
        new_artwork_name = format_artwork_filename(new_name, extension)
        new_artwork_path = os.path.join("artwork", new_artwork_name)
        
        if os.path.basename(current_artwork_path) != new_artwork_name:
            os.rename(current_artwork_path, new_artwork_path)
            game["artwork"] = new_artwork_path

    # Save the updated details to JSON
    if os.path.exists("games.json"):
        with open("games.json", "r") as file:
            data = json.load(file)
    else:
        data = {"games": []}

    # Update existing game in JSON
    for g in data["games"]:
        if g["path"] == game["path"]:
            g.update(game)
            break

    with open("games.json", "w") as file:
        json.dump(data, file, indent=4)

    print(f"Details updated for game '{game['name']}'")
    show_game_details(game)  # Go back to the details view after saving

# Function to add artwork to a game
def add_artwork(game):
    artwork_path = filedialog.askopenfilename(
        title="Select Artwork", 
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All files", "*.*")]
    )
    
    if artwork_path:
        extension = os.path.splitext(artwork_path)[1]
        new_artwork_name = format_artwork_filename(game["name"], extension)
        new_artwork_path = os.path.join("artwork", new_artwork_name)
        
        try:
            img = Image.open(artwork_path)
            img.verify()
            shutil.copy(artwork_path, new_artwork_path)
            game["artwork"] = new_artwork_path
            
            # Update the JSON file with the new artwork path
            with open("games.json", "r") as file:
                data = json.load(file)
            
            for g in data["games"]:
                if g["path"] == game["path"]:
                    g["artwork"] = new_artwork_path
                    break
            
            with open("games.json", "w") as file:
                json.dump(data, file, indent=4)

            print(f"Artwork added for game '{game['name']}'")
            load_games()  # Refresh to show updated artwork
        except Exception as e:
            print(f"Failed to add artwork: {e}. Ensure the file is a valid image.")

# Function to add a new game
def add_game():
    game_path = filedialog.askopenfilename(title="Select Game Executable", filetypes=[("Executable files", "*.exe;*.app;*.AppImage"), ("All files", "*.*")])
    
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

# Initial load of games on startup
load_games()

# Run the main loop
root.mainloop()
