import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'path'
import { spawn, ChildProcess } from 'child_process'
import { fileURLToPath } from 'url'
import { autoUpdater } from 'electron-updater'
import axios from 'axios'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Configure autoUpdater
autoUpdater.autoDownload = true
autoUpdater.allowPrerelease = false

process.env.DIST = path.join(__dirname, '../dist')
process.env.VITE_PUBLIC = app.isPackaged ? process.env.DIST : path.join(process.env.DIST, '../public')

let win: BrowserWindow | null
let backendProcess: ChildProcess | null = null

const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']

function startBackend() {
  const isPackaged = app.isPackaged
  let backendPath: string

  if (isPackaged) {
    // electron-builder puts extraResources in the resources folder
    backendPath = path.join(process.resourcesPath, 'portfolio_api.exe')
  } else {
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
}

async function waitForBackend(url: string, attempts = 30): Promise<boolean> {
  console.log(`Waiting for backend at ${url}...`)
  for (let i = 0; i < attempts; i++) {
    try {
      const response = await axios.get(url, { timeout: 2000 })
      if (response.status === 200) {
        console.log('Backend is ready!')
        return true
      }
    } catch (e: any) {
      console.log(`Backend not ready yet (attempt ${i + 1}/${attempts}): ${e.message}`)
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }
  return false
}

async function createWindow() {
  // 1. START BACKEND FIRST
  startBackend()

  // 2. WAIT FOR BACKEND TO BE READY (max 10 seconds)
  // We check the health of the API before showing the GUI
  if (app.isPackaged) {
     await waitForBackend('http://127.0.0.1:8000/api/portfolios')
  }

  // 3. NOW CREATE THE GUI
  win = new BrowserWindow({
    title: 'Portfolio Tracker',
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    show: false // Don't show until ready-to-show
  })

  win.once('ready-to-show', () => {
    win?.show()
  })

  // Check for updates on startup
  if (app.isPackaged) {
    autoUpdater.checkForUpdatesAndNotify()
  }

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
