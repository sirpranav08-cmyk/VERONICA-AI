const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('ipcRenderer', {
  send: (channel, data) => {
    const allowed = ['wake-jarvis', 'sleep-jarvis']
    if (allowed.includes(channel)) ipcRenderer.send(channel, data)
  },
  on: (channel, func) => {
    ipcRenderer.on(channel, (event, ...args) => func(...args))
  }
})
