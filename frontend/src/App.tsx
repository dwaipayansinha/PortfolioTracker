import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, Line, ComposedChart
} from 'recharts'
import {
  AlertCircle, Briefcase, Activity, ChevronDown, ChevronRight, Download, Trash2, Loader2, CheckCircle, RefreshCw
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'

// --- Error Boundary ---
class ErrorBoundary extends React.Component<any, any> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: any) { return { hasError: true, error }; }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', color: '#f87171', backgroundColor: '#0d0d0d', height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
          <AlertCircle size={64} /><h2 style={{ marginTop: '20px' }}>Dashboard Error</h2>
          <p style={{ color: '#888', maxWidth: '500px' }}>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()} style={{ marginTop: '30px', padding: '12px 24px', backgroundColor: '#2563eb', color: 'white', borderRadius: '8px', border: 'none', cursor: 'pointer' }}>Restart</button>
        </div>
      );
    }
    return this.props.children;
  }
}

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

type Portfolio = { name: string, ticker: string }
type GroupedPortfolios = { [bank: string]: { [name: string]: string } }
type ChartPoint = { time: string, value: number, trend?: number | null }
type Analysis = {
  recommendation: string
  confidence: number
  reasons: string[]
  metrics: { currentPrice: number, forecast30d: number, sma50: number, sharpeRatio: number }
}

const TIMEFRAMES = [
  { label: '1D', value: '1d', days: 1 },
  { label: '5D', value: '5d', days: 7 },
  { label: '1M', value: '1m', days: 31 },
  { label: '6M', value: '6m', days: 183 },
  { label: '1Y', value: '1y', days: 366 },
  { label: '5Y', value: '5y', days: 1826 },
  { label: '10Y', value: '10y', days: 3653 },
  { label: 'Max', value: 'max', days: 99999 },
]

function AppContent() {
  const [groupedPortfolios, setGroupedPortfolios] = useState<GroupedPortfolios>({})
  const [expandedBanks, setExpandedBanks] = useState<Record<string, boolean>>({ "TD (One-Click 2026)": true })
  const [activePortfolio, setActivePortfolio] = useState<Portfolio | null>(null)
  const [timeframe, setTimeframe] = useState<string>('5d')
  const [availableTimeframes, setAvailableTimeframes] = useState<Record<string, boolean>>({})
  const [fullSeries, setFullSeries] = useState<ChartPoint[]>([])
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [updateStatus, setUpdateStatus] = useState<string | null>(null)

  // Load Initial List
  useEffect(() => {
    const handleUpdate = (_event: any, status: string) => {
      setUpdateStatus(status)
      if (status.includes("latest version") || status.includes("Error")) {
        setTimeout(() => setUpdateStatus(null), 5000)
      }
    }
    
    if (window.ipcRenderer) {
      window.ipcRenderer.on('update-status', handleUpdate)
    }

    axios.get(`${API_BASE}/portfolios`)
      .then(res => {
        setGroupedPortfolios(res.data || {})
        const banks = Object.keys(res.data)
        if (banks.length > 0) {
          const firstBank = banks[0]
          const firstName = Object.keys(res.data[firstBank])[0]
          setActivePortfolio({ name: firstName, ticker: res.data[firstBank][firstName] })
        }
      })
      .catch(() => setError(`Backend Connection Failed`))

    return () => {
      if (window.ipcRenderer) {
        window.ipcRenderer.off('update-status', handleUpdate)
      }
    }
  }, [])

  // Load Data
  useEffect(() => {
    if (!activePortfolio) return
    setLoading(true)
    setError(null)
    setAnalysis(null)
    setFullSeries([])
    
    axios.get(`${API_BASE}/data/${activePortfolio.ticker}`)
      .then(res => {
        setFullSeries(res.data.series || [])
        setAvailableTimeframes(res.data.availability || {})
        setAnalysis(res.data.analysis)
        
        if (res.data.availability?.[timeframe] === false) {
          const valid = TIMEFRAMES.filter(t => res.data.availability?.[t.value])
          if (valid.length > 0) setTimeframe(valid[valid.length - 1].value)
        }
      })
      .catch(() => setError("Data fetch failed"))
      .finally(() => setLoading(false))
  }, [activePortfolio])

  const getVisibleData = () => {
    if (!fullSeries || fullSeries.length === 0) return []
    let filtered = [...fullSeries]
    if (timeframe !== 'max') {
        const tf = TIMEFRAMES.find(t => t.value === timeframe)
        const cutoff = new Date(); cutoff.setDate(cutoff.getDate() - (tf?.days || 365))
        filtered = fullSeries.filter(p => new Date(p.time) >= cutoff)
    }
    
    if (filtered.length > 1 && analysis?.metrics?.forecast30d) {
      const forecast = analysis.metrics.forecast30d
      return filtered.map((p, i) => ({
        ...p, 
        trend: (i === 0) ? p.value : (i === filtered.length - 1 ? forecast : null)
      }))
    }
    return filtered
  }

  const formatXAxis = (tick: string) => {
    const d = new Date(tick); return isNaN(d.getTime()) ? tick : d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  const getStatusColor = (rec: string) => {
    if (rec?.includes('Buy')) return '#4ade80'
    if (rec?.includes('Sell')) return '#f87171'
    return '#facc15'
  }

  return (
    <div className="app-container" style={{ display: 'flex', height: '100vh', backgroundColor: '#0d0d0d', color: '#fff', overflow: 'hidden' }}>
      <div className="sidebar" style={{ width: '300px', borderRight: '1px solid #333', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #333' }}>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><Briefcase color="#4ade80" /> Portfolio Tracker</h2>
        </div>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {Object.entries(groupedPortfolios).map(([bank, portfolios]) => (
            <div key={bank}>
              <button onClick={() => setExpandedBanks(p => ({ ...p, [bank]: !p[bank] }))} style={{ width: '100%', padding: '15px', textAlign: 'left', background: '#1a1a1a', border: 'none', color: '#fff', borderBottom: '1px solid #222', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold' }}>{bank}</span>{expandedBanks[bank] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>
              {expandedBanks[bank] && (
                <div style={{ padding: '5px' }}>
                  {Object.entries(portfolios).map(([name, ticker]) => (
                    <button key={`${bank}-${ticker}-${name}`} onClick={() => setActivePortfolio({ name, ticker })} style={{ width: '100%', padding: '10px', textAlign: 'left', background: activePortfolio?.ticker === ticker && activePortfolio?.name === name ? '#2563eb' : 'transparent', border: 'none', color: '#fff', borderRadius: '4px', cursor: 'pointer', marginBottom: '2px', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                      <span style={{ flex: 1 }}>{name}</span>
                      <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', fontWeight: 'normal' }}>{ticker}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        <div style={{ padding: '20px', borderTop: '1px solid #333' }}>
            {updateStatus && (
              <div style={{ fontSize: '0.75rem', color: updateStatus.includes('Error') ? '#f87171' : '#4ade80', marginBottom: '10px', backgroundColor: 'rgba(255,255,255,0.03)', padding: '8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <RefreshCw size={12} style={{ animation: (updateStatus.includes('Checking') || updateStatus.includes('Downloading')) ? 'spin 1s linear infinite' : 'none' }} />
                {updateStatus}
              </div>
            )}
            <button onClick={() => window.ipcRenderer?.checkForUpdates()} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '10px', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.05)', marginBottom: '10px', padding: '10px', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
              <Download size={16} /><span>Check for updates</span>
            </button>
            <button onClick={() => axios.post(`${API_BASE}/clear-cache`).then(() => window.location.reload())} style={{ width: '100%', padding: '10px', background: 'rgba(248,113,113,0.05)', color: '#f87171', border: '1px solid rgba(248,113,113,0.2)', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}><Trash2 size={14} /> Clear Cache</button>
        </div>
      </div>

      <div className="main-content" style={{ flex: 1, padding: '40px', overflowY: 'auto' }}>
        {error && !activePortfolio ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <AlertCircle size={64} color="#f87171" /><h2 style={{ color: '#f87171', marginTop: '20px' }}>Connection Error</h2><p style={{ color: '#888', marginTop: '10px' }}>{error}</p>
            <button onClick={() => window.location.reload()} style={{ backgroundColor: '#2563eb', color: 'white', padding: '12px 32px', borderRadius: '8px', border: 'none', marginTop: '20px', cursor: 'pointer' }}>Reload</button>
          </div>
        ) : activePortfolio && (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
              <div><h1 style={{ fontSize: '1.8rem' }}>{activePortfolio.name}</h1><span style={{ color: '#888' }}>{activePortfolio.ticker}</span></div>
              <div style={{ display: 'flex', gap: '5px', background: '#1a1a1a', padding: '5px', borderRadius: '8px' }}>
                {TIMEFRAMES.map(tf => (
                  <button key={tf.value} disabled={availableTimeframes[tf.value] === false} onClick={() => setTimeframe(tf.value)} style={{ padding: '8px 12px', background: timeframe === tf.value ? '#2563eb' : 'transparent', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', opacity: availableTimeframes[tf.value] === false ? 0.3 : 1 }}>
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ height: '400px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
              {loading ? <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}><Loader2 className="animate-spin" /> Loading historical data...</div> : (
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart key={`${activePortfolio.ticker}-${timeframe}`} data={getVisibleData()}>
                    <defs><linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient></defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="time" tickFormatter={formatXAxis} stroke="#444" fontSize={11} minTickGap={40} />
                    <YAxis domain={['auto', 'auto']} stroke="#444" fontSize={11} tickFormatter={v => `$${v}`} />
                    <Tooltip contentStyle={{ background: '#000', border: '#333', borderRadius: '8px' }} labelFormatter={l => new Date(l).toLocaleDateString()} formatter={(v: any, n: string) => [`$${Number(v).toFixed(2)}`, n === 'value' ? 'Price' : 'AI Trend']} />
                    <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} fill="url(#colorValue)" fillOpacity={1} animationDuration={500} />
                    <Line type="linear" dataKey="trend" stroke={getStatusColor(analysis?.recommendation || '')} strokeWidth={3} strokeDasharray="5 5" dot={false} connectNulls activeDot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              )}
            </div>

            {analysis && !loading && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px', marginTop: '30px' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '30px', borderRadius: '12px', textAlign: 'center', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <h3 style={{ color: '#888', textTransform: 'uppercase', fontSize: '0.8rem', letterSpacing: '1px' }}>AI Rating</h3>
                  <div style={{ fontSize: '2.2rem', fontWeight: '900', margin: '15px 0', color: getStatusColor(analysis.recommendation) }}>{analysis.recommendation}</div>
                  <div style={{ marginTop: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '5px', color: '#666' }}><span>Model Confidence</span><span>{analysis.confidence}%</span></div>
                    <div style={{ height: '6px', background: '#222', borderRadius: '3px', overflow: 'hidden' }}><div style={{ width: `${analysis.confidence}%`, height: '100%', background: '#2563eb' }} /></div>
                  </div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '30px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#888', textTransform: 'uppercase', fontSize: '0.8rem', letterSpacing: '1px' }}><Activity size={16} /> Analysis Breakdown</h3>
                  <ul style={{ marginTop: '20px', listStyle: 'none', padding: 0 }}>
                    {analysis.reasons?.map((r, i) => (
                        <li key={i} style={{ marginBottom: '12px', color: '#ccc', display: 'flex', gap: '10px', fontSize: '0.95rem', alignItems: 'flex-start' }}>
                            <CheckCircle size={16} color="#4ade80" style={{ flexShrink: 0, marginTop: '2px' }} /> <span>{r}</span>
                        </li>
                    ))}
                  </ul>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '20px', marginTop: '30px' }}>
                    <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '8px' }}><div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Current Price</div><div style={{ fontSize: '1.4rem', fontWeight: '700' }}>${analysis.metrics.currentPrice}</div></div>
                    <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '8px' }}><div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>30D AI Target</div><div style={{ fontSize: '1.4rem', fontWeight: '700', color: analysis.metrics.forecast30d > analysis.metrics.currentPrice ? '#4ade80' : '#f87171' }}>${analysis.metrics.forecast30d}</div></div>
                    <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '8px' }}><div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Sharpe Ratio</div><div style={{ fontSize: '1.4rem', fontWeight: '700' }}>{analysis.metrics.sharpeRatio}</div></div>
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

function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  )
}

export default App
