const { ipcRenderer } = require('electron');
const path = require('path');
const fs = require('fs');

let exePaths = []; // To store paths to .exe files with optional artwork
const appContainer = document.getElementById('app-container');
const addBtn = document.getElementById('add-btn');
const fileInput = document.getElementById('file-input');
const imageInput = document.getElementById('image-input');

// Function to render tiles
function renderTiles() {
  appContainer.innerHTML = ''; // Clear existing tiles
  exePaths.forEach((app, index) => {
    const tile = document.createElement('div');
    tile.className = 'tile';
    tile.textContent = app.name;
    if (app.artwork) {
      tile.style.backgroundImage = `url('${app.artwork}')`;
      tile.style.backgroundSize = 'cover';
    }

    // Right-click menu for adding artwork
    tile.oncontextmenu = (e) => {
      e.preventDefault();
      imageInput.onchange = () => {
        const file = imageInput.files[0];
        if (file) {
          const destPath = path.join(__dirname, 'artwork', `${app.name}-${index}.jpg`);
          fs.mkdirSync(path.join(__dirname, 'artwork'), { recursive: true });
          fs.copyFile(file.path, destPath, (err) => {
            if (err) console.error('Error saving artwork:', err);
            else {
              app.artwork = destPath;
              renderTiles(); // Re-render with artwork
            }
          });
        }
      };
      imageInput.click(); // Open file selector for artwork
    };

    tile.onclick = () => ipcRenderer.send('launch-app', app.path); // Launch app on click
    appContainer.appendChild(tile);
  });
}

// Add new path to the list
addBtn.onclick = () => fileInput.click();
fileInput.onchange = () => {
  const file = fileInput.files[0];
  if (file) {
    exePaths.push({ name: path.basename(file.path, '.exe'), path: file.path });
    renderTiles();
  }
};

// Initial render with empty state
renderTiles();
