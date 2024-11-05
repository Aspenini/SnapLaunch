const { app, BrowserWindow, ipcMain } = require('electron');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    }
  });

  win.loadFile('index.html');

  // Ensure artwork directory exists
  const artworkDir = path.join(__dirname, 'artwork');
  if (!fs.existsSync(artworkDir)) {
    fs.mkdirSync(artworkDir);
  }
}

app.whenReady().then(createWindow);

ipcMain.on('launch-app', (event, appPath) => {
  exec(`"${appPath}"`, (error) => {
    if (error) {
      console.error(`Error launching app: ${error.message}`);
    } else {
      app.quit();
    }
  });
});
