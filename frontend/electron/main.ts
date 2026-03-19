import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'path'
import { spawn, ChildProcess } from 'child_process'
import { fileURLToPath } from 'url'
import { autoUpdater } from 'electron-updater'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Configure autoUpdater
autoUpdater.autoDownload = true
autoUpdater.allowPrerelease = false

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.js
// │
process.env.DIST = path.join(__dirname, '../dist')
process.env.VITE_PUBLIC = app.isPackaged ? process.env.DIST : path.join(process.env.DIST, '../public')

let win: BrowserWindow | null
let backendProcess: ChildProcess | null = null

const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']

function startBackend() {
  const isPackaged = app.isPackaged
  let backendPath: string

  if (isPackaged) {
    // In production, the executable will be in the resources folder
    backendPath = path.join(process.resourcesPath, 'portfolio_api.exe')
  } else {
    // In development, it's in the backend/dist folder
    backendPath = path.join(__dirname, '..', '..', 'backend', 'dist', 'portfolio_api.exe')
  }

  console.log('Starting backend at:', backendPath)

  backendProcess = spawn(backendPath, [], {
    shell: false,
    windowsHide: true
  })

  backendProcess.stdout?.on('data', (data) => {
    console.log(`Backend: ${data}`)
  })

  backendProcess.stderr?.on('data', (data) => {
    console.error(`Backend Error: ${data}`)
  })

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`)
  })
}

function createWindow() {
  win = new BrowserWindow({
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
  })

  // Start the backend
  startBackend()

  // Check for updates on startup
  if (app.isPackaged) {
    autoUpdater.checkForUpdatesAndNotify()
  }

  // Test active push message to Renderer-process.
  win.webContents.on('did-finish-load', () => {
    win?.webContents.send('main-process-message', (new Date).toLocaleString())
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(process.env.DIST, 'index.html'))
  }
}

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill()
  }
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.on('will-quit', () => {
  if (backendProcess) {
    backendProcess.kill()
  }
})

// Update listeners
autoUpdater.on('checking-for-update', () => {
  win?.webContents.send('update-status', 'Checking for update...')
})

autoUpdater.on('update-available', (info) => {
  win?.webContents.send('update-status', `Update available: v${info.version}`)
})

autoUpdater.on('update-not-available', () => {
  win?.webContents.send('update-status', 'You are on the latest version.')
})

autoUpdater.on('error', (err) => {
  win?.webContents.send('update-status', `Error: ${err.message}`)
})

autoUpdater.on('download-progress', (progressObj) => {
  win?.webContents.send('update-status', `Downloading: ${Math.round(progressObj.percent)}%`)
})

autoUpdater.on('update-downloaded', () => {
  win?.webContents.send('update-status', 'Update downloaded; restarting...')
  setTimeout(() => {
    autoUpdater.quitAndInstall()
  }, 2000)
})

ipcMain.on('check-for-updates', () => {
  autoUpdater.checkForUpdates()
})

app.whenReady().then(createWindow)
