const { app, BrowserWindow, session, ipcMain } = require('electron')
const path = require('path')

// Enable speech recognition
app.commandLine.appendSwitch('enable-speech-dispatcher')
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required')

let win

app.whenReady().then(() => {
  // Grant ALL permissions
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    console.log('[Permission]', permission, '-> granted')
    callback(true)
  })

  session.defaultSession.setPermissionCheckHandler((webContents, permission) => {
    return true
  })

  win = new BrowserWindow({
    width: 1400,
    height: 900,
    frame: false,
    backgroundColor: '#020408',
    show: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      autoplayPolicy: 'no-user-gesture-required',
      webSecurity: false,
      allowRunningInsecureContent: true,
      experimentalFeatures: true
    }
  })

  win.maximize()
  win.loadFile('../ui/src/index.html')
  win.setMenuBarVisibility(false)

  // Show immediately — no clap needed
  win.once('ready-to-show', () => {
    win.show()
    win.maximize()
    win.focus()
})

  ipcMain.on('wake-jarvis', () => {
    win.show()
    win.focus()
    win.maximize()
  })

  ipcMain.on('sleep-jarvis', () => {
    win.hide()
  })
})

app.on('window-all-closed', () => app.quit())