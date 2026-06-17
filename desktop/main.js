
const { app, BrowserWindow } = require('electron')
const path = require('path')

let win

app.whenReady().then(() => {
  win = new BrowserWindow({
    width: 1400,
    height: 900,
    frame: false,
    titleBarStyle: 'hidden',
    backgroundColor: '#020408',
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      autoplayPolicy: 'no-user-gesture-required'
    }
  })

  win.maximize()
  win.loadFile('../ui/src/index.html')
  win.setMenuBarVisibility(false)
})

app.on('window-all-closed', () => app.quit())
