import tkinter as tk
from tkinter import filedialog, Menu, messagebox
from PIL import Image, ImageTk
import json
import os
import shutil
import subprocess
import platform

# Ensure the "artwork" and "artwork_archive" folders exist
if not os.path.exists("artwork"):
    os.makedirs("artwork")
if not os.path.exists("artwork_archive"):
    os.makedirs("artwork_archive")

# Create the main window
root = tk.Tk()
root.title("Game Launcher")
root.geometry("600x400")

# Main frame that will change content based on selection
content_frame = tk.Frame(root)
content_frame.pack(fill="both", expand=True)

# Utility function to format the artwork filename based on game name
def format_artwork_filename(game_name, extension):
    return game_name.replace(" ", "_").lower() + extension

# Move unused artwork to the artwork_archive folder
def archive_unused_artwork(games):
    # Get the list of artwork files currently referenced in games.json
    used_artwork = {game["artwork"] for game in games if game.get("artwork")}
    # Move unreferenced artwork to artwork_archive
    for filename in os.listdir("artwork"):
        artwork_path = os.path.join("artwork", filename)
        if artwork_path not in used_artwork:
            archive_path = os.path.join("artwork_archive", filename)
            shutil.move(artwork_path, archive_path)
            print(f"Moved unused artwork '{filename}' to artwork_archive")

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

    # Archive any unused artwork
    archive_unused_artwork(games)

    # Display games in a grid layout with multiple squares per row
    columns = 3  # Number of tiles per row (can adjust based on window width)
    row, col = 0, 0  # Initialize row and column variables in case of an empty games list
    for index, game in enumerate(games):
        artwork_path = game.get("artwork")
        
        # Display the game button with artwork if available
        if artwork_path and os.path.exists(artwork_path):
            img = Image.open(artwork_path)
            img.thumbnail((100, 100))
            img = ImageTk.PhotoImage(img)
            game_button = tk.Label(content_frame, image=img, borderwidth=2, relief="groove", width=100, height=100)
            game_button.image = img  # Keep a reference to prevent garbage collection
        else:
            game_button = tk.Label(content_frame, text=game["name"], borderwidth=2, relief="groove", width=12, height=6)

        # Position the game button in a grid layout
        row = index // columns
        col = index % columns
        game_button.grid(row=row, column=col, padx=5, pady=5)

        # Bind left-click to launch game only when clicking inside the square
        game_button.bind("<Button-1>", lambda event, path=game["path"]: launch_game(path))

        # Bind right-click to show options
        game_button.bind("<Button-3>", lambda event, g=game: show_options_menu(event, g))

    # Add the "Add Game" button at the bottom of the window
    add_game_button = tk.Button(content_frame, text="Add Game", command=add_game)
    add_game_button.grid(row=row + 1, column=0, columnspan=columns, pady=20)

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

# Function to add artwork to a game with 1x1 aspect ratio check
def add_artwork(game):
    artwork_path = filedialog.askopenfilename(
        title="Select Artwork", 
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All files", "*.*")]
    )
    
    if artwork_path:
        try:
            img = Image.open(artwork_path)
            width, height = img.size
            if width != height:
                messagebox.showerror("Invalid Image", "Please select a square image with a 1x1 aspect ratio.")
                return

            # Save the artwork if it's square
            extension = os.path.splitext(artwork_path)[1]
            new_artwork_name = format_artwork_filename(game["name"], extension)
            new_artwork_path = os.path.join("artwork", new_artwork_name)
            img.save(new_artwork_path)  # Save as a square image
            game["artwork"] = new_artwork_path

            # Update the JSON file with the new artwork path
            if os.path.exists("games.json"):
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
        # Load the JSON to check for duplicate names
        if os.path.exists("games.json"):
            with open("games.json", "r") as file:
                data = json.load(file)
        else:
            data = {"games": []}

        new_game_name = os.path.basename(game_path)
        
        # Check for duplicate name
        for game in data["games"]:
            if game["name"].lower() == new_game_name.lower():
                messagebox.showerror("Duplicate Game", f"A game with the name '{new_game_name}' already exists.")
                return
        
        # Add new game if no duplicate found
        new_game = {
            "name": new_game_name,
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

# Function to show game details and allow editing
def show_game_details(game):
    # Clear the frame and display game details
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Back button to return to the main launcher
    back_button = tk.Button(content_frame, text="Back", command=load_games)
    back_button.grid(row=0, column=1, sticky="ne", padx=10, pady=10)

    # Game name as the title
    tk.Label(content_frame, text=game["name"], font=("Arial", 16)).grid(row=0, column=0, sticky="w", padx=10, pady=10)

    # Display release date and description
    tk.Label(content_frame, text="Release Date:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
    release_date_label = tk.Label(content_frame, text=game["metadata"].get("release_date", "N/A"))
    release_date_label.grid(row=2, column=0, padx=10, sticky="w", pady=(0, 10))

    tk.Label(content_frame, text="Description:", font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=10, pady=(0, 5))
    description_label = tk.Label(content_frame, text=game["metadata"].get("description", "N/A"), wraplength=250, justify="left")
    description_label.grid(row=4, column=0, padx=10, sticky="w", pady=(0, 10))

    # Display artwork on the right
    if game["artwork"] and os.path.exists(game["artwork"]):
        img = Image.open(game["artwork"])
        img.thumbnail((150, 150))
        artwork = ImageTk.PhotoImage(img)
        artwork_label = tk.Label(content_frame, image=artwork)
        artwork_label.image = artwork  # Keep reference to prevent garbage collection
        artwork_label.grid(row=1, column=1, rowspan=4, padx=10, pady=10, sticky="e")

    # Button to edit details
    edit_button = tk.Button(content_frame, text="Edit Details", command=lambda: edit_game_details(game))
    edit_button.grid(row=5, column=0, pady=10, padx=10)

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

# Function to save edited game details with duplicate name check
def save_game_details(game, new_name, new_release_date, new_description):
    # Check for duplicate name only if the name has been changed
    if new_name != game["name"]:
        if os.path.exists("games.json"):
            with open("games.json", "r") as file:
                data = json.load(file)
            for g in data["games"]:
                if g["name"].lower() == new_name.lower() and g["path"] != game["path"]:
                    messagebox.showerror("Duplicate Name", f"A game with the name '{new_name}' already exists.")
                    return

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

# Initial load of games on startup
load_games()

# Run the main loop
root.mainloop()
