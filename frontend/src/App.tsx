import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart
} from 'recharts'
import {
  TrendingUp, AlertCircle, Briefcase, Activity, CheckCircle, XCircle, ChevronDown, ChevronRight, RefreshCw, Download
} from 'lucide-react'

const API_BASE = 'http://127.0.0.1:8000/api'

// Define the window interface for IPC
declare global {
  interface Window {
    ipcRenderer: {
      on: (channel: string, listener: (event: any, ...args: any[]) => void) => void
      off: (channel: string, ...args: any[]) => void
      send: (channel: string, ...args: any[]) => void
      invoke: (channel: string, ...args: any[]) => Promise<any>
      checkForUpdates: () => void
    }
  }
}

type Portfolio = {
  name: string
  ticker: string
}

type GroupedPortfolios = {
  [bank: string]: {
    [name: string]: string
  }
}

type ChartData = {
  time: string
  value: number
}

type Analysis = {
  recommendation: 'Invest' | 'Remove' | 'Diversify'
  confidence: number
  reasons: string[]
  metrics: {
    currentPrice: number
    sma50: number
    sma200: number
    sharpeRatio: number
    forecast30d: number
  }
}

const TIMEFRAMES = [
  { label: '1D', value: '1d' },
  { label: '1W', value: '1w' },
  { label: '1M', value: '1m' },
  { label: '6M', value: '6m' },
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' },
  { label: '10Y', value: '10y' },
  { label: 'Max', value: 'max' },
]

function App() {
  const [groupedPortfolios, setGroupedPortfolios] = useState<GroupedPortfolios>({})
  const [expandedBanks, setExpandedBanks] = useState<Record<string, boolean>>({ "TD (One-Click 2026)": true, "CIBC (New 2025/2026)": true })
  const [activePortfolio, setActivePortfolio] = useState<Portfolio | null>(null)
  const [timeframe, setTimeframe] = useState<string>('1w')
  const [chartData, setChartData] = useState<ChartData[]>([])
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryTimer, setRetryTimer] = useState<number>(60)
  const [updateStatus, setUpdateStatus] = useState<string | null>(null)

  useEffect(() => {
    // Listen for update status from main process
    if (window.ipcRenderer) {
      window.ipcRenderer.on('update-status', (_event, status: string) => {
        setUpdateStatus(status)
        // Auto-clear success messages after 5 seconds
        if (status.includes("latest version") || status.includes("Error")) {
          setTimeout(() => setUpdateStatus(null), 5000)
        }
      })
    }
  }, [])

  useEffect(() => {
    let timer: NodeJS.Timeout
    if (error && retryTimer > 0) {
      timer = setInterval(() => {
        setRetryTimer(prev => prev - 1)
      }, 1000)
    } else if (error && retryTimer === 0) {
      handleRetry()
    }
    return () => clearInterval(timer)
  }, [error, retryTimer])

  const fetchData = async () => {
    if (!activePortfolio) return
    
    setLoading(true)
    setError(null)
    setAnalysis(null)
    setChartData([])
    setRetryTimer(60)
    
    try {
      const fetchChart = axios.get(`${API_BASE}/historical/${activePortfolio.ticker}?range=${timeframe}`)
      const fetchAnalysis = axios.get(`${API_BASE}/analysis/${activePortfolio.ticker}`)
      
      const [chartRes, analysisRes] = await Promise.all([fetchChart, fetchAnalysis])
      
      if (chartRes.data.length === 0) throw new Error("No historical data available")
      
      setChartData(chartRes.data)
      setAnalysis(analysisRes.data)
    } catch (err: any) {
      console.error("Failed to load data", err)
      setError(err.response?.data?.detail || err.message || "An unexpected error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    fetchData()
  }

  useEffect(() => {
    axios.get(`${API_BASE}/portfolios`)
      .then(res => {
        setGroupedPortfolios(res.data)
        // Set first portfolio as active by default
        const banks = Object.keys(res.data)
        if (banks.length > 0) {
          const firstBank = banks[0]
          const firstPortfolioName = Object.keys(res.data[firstBank])[0]
          const firstTicker = res.data[firstBank][firstPortfolioName]
          setActivePortfolio({ name: firstPortfolioName, ticker: firstTicker })
        }
      })
      .catch(err => {
        console.error("Failed to load portfolios", err)
        setError("Could not connect to backend server. Please ensure the Python API is running.")
      })
  }, [])

  useEffect(() => {
    fetchData()
  }, [activePortfolio, timeframe])

  const toggleBank = (bank: string) => {
    setExpandedBanks(prev => ({ ...prev, [bank]: !prev[bank] }))
  }

  const renderReasonIcon = (reason: string) => {
    if (reason.includes("Bullish") || reason.includes(">2% growth") || reason.includes("Favorable") || reason.includes("Golden Cross")) {
      return <CheckCircle className="reason-icon positive" size={18} />
    }
    if (reason.includes("Bearish") || reason.includes("drop") || reason.includes("Poor") || reason.includes("Death Cross")) {
      return <XCircle className="reason-icon negative" size={18} />
    }
    return <AlertCircle className="reason-icon neutral" size={18} />
  }

  const formatXAxis = (tickItem: string) => {
    try {
      if (!tickItem) return ""
      if (timeframe === '1d' || timeframe === '1w') {
        const date = new Date(tickItem)
        return isNaN(date.getTime()) ? tickItem : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      return tickItem.split(' ')[0]
    } catch {
      return tickItem || ""
    }
  }

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <Briefcase size={24} />
          <h1>Portfolio Tracker</h1>
        </div>
        <div className="portfolio-list" style={{ padding: '0', flex: 1 }}>
          {Object.entries(groupedPortfolios).map(([bank, portfolios]) => (
            <div key={bank} className="bank-group">
              <button 
                className="bank-header" 
                onClick={() => toggleBank(bank)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '12px 20px',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '0.9rem',
                  backgroundColor: 'rgba(255,255,255,0.03)',
                  borderBottom: '1px solid rgba(255,255,255,0.05)'
                }}
              >
                {expandedBanks[bank] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                {bank} Portfolios
              </button>
              {expandedBanks[bank] && (
                <div className="bank-content" style={{ padding: '5px 10px' }}>
                  {Object.entries(portfolios).map(([name, ticker]) => (
                    <button
                      key={ticker}
                      className={`portfolio-item ${activePortfolio?.ticker === ticker ? 'active' : ''}`}
                      onClick={() => setActivePortfolio({ name, ticker })}
                      style={{ width: '100%', marginBottom: '2px', fontSize: '0.85rem' }}
                    >
                      <span>{name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Update Section */}
        <div className="sidebar-footer" style={{ padding: '20px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          {updateStatus && (
            <div style={{ 
              fontSize: '0.75rem', 
              color: updateStatus.includes('Error') ? '#f87171' : '#4ade80',
              marginBottom: '10px',
              backgroundColor: 'rgba(255,255,255,0.03)',
              padding: '8px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <RefreshCw size={12} style={{ animation: (updateStatus.includes('Checking') || updateStatus.includes('Downloading')) ? 'spin 1s linear infinite' : 'none' }} />
              {updateStatus}
            </div>
          )}
          <button 
            className="portfolio-item" 
            onClick={() => window.ipcRenderer?.checkForUpdates()}
            style={{ 
              width: '100%', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '10px',
              justifyContent: 'center',
              backgroundColor: 'rgba(255,255,255,0.05)'
            }}
          >
            <Download size={16} />
            <span>Check for updates</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {activePortfolio && (
          <>
            <div className="header">
              <div>
                <h2 className="portfolio-title">{activePortfolio.name}</h2>
                <span className="portfolio-ticker">{activePortfolio.ticker}</span>
              </div>
              <div className="timeframe-selector">
                {TIMEFRAMES.map(tf => (
                  <button
                    key={tf.value}
                    className={`timeframe-btn ${timeframe === tf.value ? 'active' : ''}`}
                    onClick={() => setTimeframe(tf.value)}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="chart-container" style={{ position: 'relative' }}>
              {loading ? (
                <div className="loading-overlay">Loading data...</div>
              ) : error ? (
                <div className="loading-overlay" style={{ flexDirection: 'column', gap: '20px', textAlign: 'center', padding: '0 40px' }}>
                  <AlertCircle size={48} color="#f87171" />
                  <div>
                    <h3 style={{ color: '#f87171', marginBottom: '10px' }}>Data Fetching Error</h3>
                    <p style={{ color: '#888', maxWidth: '400px' }}>{error}</p>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                    <button 
                      onClick={handleRetry}
                      style={{ 
                        backgroundColor: '#2563eb', 
                        color: 'white', 
                        padding: '10px 24px', 
                        borderRadius: '6px',
                        fontWeight: '600'
                      }}
                    >
                      Retry Now
                    </button>
                    <span style={{ fontSize: '0.85rem', color: '#666' }}>
                      Auto-retrying in {retryTimer}s...
                    </span>
                  </div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                    <XAxis 
                      dataKey="time" 
                      stroke="#888" 
                      tickFormatter={formatXAxis}
                      minTickGap={30}
                    />
                    <YAxis 
                      domain={['auto', 'auto']} 
                      stroke="#888" 
                      tickFormatter={(val) => `$${Number(val).toFixed(2)}`}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                      labelFormatter={(label) => label ? label.split(' ')[0] : ""}
                      formatter={(value: any) => [`$${Number(value).toFixed(2)}`, 'Price']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorValue)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {analysis && !error && (
              <div className="analysis-container">
                <div className="card">
                  <h3 className="card-title"><Activity size={20} /> Recommendation</h3>
                  <div className="recommendation-box">
                    <div className={`rec-badge rec-${analysis.recommendation}`}>
                      {analysis.recommendation}
                    </div>
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span className="confidence-text">Confidence</span>
                        <span className="confidence-text">{analysis.confidence}%</span>
                      </div>
                      <div className="confidence-bar">
                        <div className="confidence-fill" style={{ width: `${analysis.confidence}%` }}></div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3 className="card-title"><TrendingUp size={20} /> Analysis Model Output</h3>
                  <ul className="reasons-list">
                    {analysis.reasons?.map((reason, idx) => (
                      <li key={idx} className="reason-item">
                        {renderReasonIcon(reason)}
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="metrics-grid">
                    <div className="metric-item">
                      <div className="metric-label">Current Price</div>
                      <div className="metric-value">${analysis.metrics?.currentPrice}</div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-label">Sharpe Ratio</div>
                      <div className="metric-value">{analysis.metrics?.sharpeRatio}</div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-label">30D Forecast</div>
                      <div className="metric-value" style={{ color: (analysis.metrics?.forecast30d || 0) > (analysis.metrics?.currentPrice || 0) ? '#4ade80' : '#f87171' }}>
                        ${analysis.metrics?.forecast30d}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default App
