import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Activity, 
  Clock, 
  Database, 
  RefreshCw, 
  Play, 
  TrendingUp, 
  TrendingDown,
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  Newspaper
} from 'lucide-react'
import './App.css'

const API_BASE = '/api'

function App() {
  const [activeTab, setActiveTab] = useState('fiidii') // 'fiidii', 'option-chain', 'banknifty', or 'news'
  
  // FII/DII state
  const [status, setStatus] = useState(null)
  const [data, setData] = useState([])
  const [stats, setStats] = useState(null)
  
  // Option Chain state
  const [optionChainStatus, setOptionChainStatus] = useState(null)
  const [optionChainData, setOptionChainData] = useState([])
  const [optionChainStats, setOptionChainStats] = useState(null)
  
  // BankNifty state
  const [bankniftyStatus, setBankniftyStatus] = useState(null)
  const [bankniftyData, setBankniftyData] = useState([])
  const [bankniftyStats, setBankniftyStats] = useState(null)
  
  // News state
  const [newsStatus, setNewsStatus] = useState(null)
  const [newsData, setNewsData] = useState([])
  const [newsStats, setNewsStats] = useState(null)
  
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [optionChainTriggering, setOptionChainTriggering] = useState(false)
  const [bankniftyTriggering, setBankniftyTriggering] = useState(false)
  const [newsTriggering, setNewsTriggering] = useState(false)

  const fetchData = async () => {
    try {
      const [
        statusRes, dataRes, statsRes, 
        optionChainStatusRes, optionChainDataRes, optionChainStatsRes, 
        bankniftyStatusRes, bankniftyDataRes, bankniftyStatsRes,
        newsStatusRes, newsDataRes, newsStatsRes
      ] = await Promise.all([
        axios.get(`${API_BASE}/status`),
        axios.get(`${API_BASE}/data`),
        axios.get(`${API_BASE}/stats`),
        axios.get(`${API_BASE}/option-chain/status`),
        axios.get(`${API_BASE}/option-chain/data`),
        axios.get(`${API_BASE}/option-chain/stats`),
        axios.get(`${API_BASE}/banknifty/status`),
        axios.get(`${API_BASE}/banknifty/data`),
        axios.get(`${API_BASE}/banknifty/stats`),
        axios.get(`${API_BASE}/news/status`),
        axios.get(`${API_BASE}/news/data`),
        axios.get(`${API_BASE}/news/stats`)
      ])

      setStatus(statusRes.data)
      setData(dataRes.data.data || [])
      setStats(statsRes.data.stats)
      
      setOptionChainStatus(optionChainStatusRes.data)
      setOptionChainData(optionChainDataRes.data.data || [])
      setOptionChainStats(optionChainStatsRes.data.stats)
      
      setBankniftyStatus(bankniftyStatusRes.data)
      setBankniftyData(bankniftyDataRes.data.data || [])
      setBankniftyStats(bankniftyStatsRes.data.stats)
      
      setNewsStatus(newsStatusRes.data)
      setNewsData(newsDataRes.data.data || [])
      setNewsStats(newsStatsRes.data.stats)
      
      setLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const handleTrigger = async () => {
    setTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/trigger`)
      if (res.data.success) {
        alert('✅ FII/DII Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setTriggering(false)
    }
  }

  const handleOptionChainTrigger = async () => {
    setOptionChainTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/option-chain/trigger`)
      if (res.data.success) {
        alert('✅ NIFTY Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ NIFTY Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setOptionChainTriggering(false)
    }
  }

  const handleBankniftyTrigger = async () => {
    setBankniftyTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/banknifty/trigger`)
      if (res.data.success) {
        alert('✅ BankNifty Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ BankNifty Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setBankniftyTriggering(false)
    }
  }

  const handleNewsTrigger = async () => {
    setNewsTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/news/trigger`)
      if (res.data.success) {
        alert('✅ News Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ News Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setNewsTriggering(false)
    }
  }

  const getSentimentColor = (sentiment) => {
    if (sentiment === 'Positive') return 'positive'
    if (sentiment === 'Negative') return 'negative'
    return 'muted'
  }

  const formatDateTime = (isoString) => {
    if (!isoString) return 'Never'
    return new Date(isoString).toLocaleString()
  }

  const formatNumber = (value) => {
    if (!value) return '-'
    const num = parseFloat(value)
    if (isNaN(num)) return value
    return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>
            <Activity className="icon" />
            NSE Data Collector Admin Panel
          </h1>
          <p>Monitor and Manage FII/DII & Option Chain Data Collection</p>
        </div>
      </header>

      {/* Tabs */}
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'fiidii' ? 'active' : ''}`}
          onClick={() => setActiveTab('fiidii')}
        >
          <Activity size={18} />
          FII/DII Data
        </button>
        <button 
          className={`tab ${activeTab === 'option-chain' ? 'active' : ''}`}
          onClick={() => setActiveTab('option-chain')}
        >
          <BarChart3 size={18} />
          NIFTY Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'banknifty' ? 'active' : ''}`}
          onClick={() => setActiveTab('banknifty')}
        >
          <BarChart3 size={18} />
          BankNifty Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'news' ? 'active' : ''}`}
          onClick={() => setActiveTab('news')}
        >
          <Newspaper size={18} />
          News & Sentiment
        </button>
      </div>

      <div className="container">
        {activeTab === 'fiidii' ? (
          <>
            {/* FII/DII Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>FII/DII Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={status?.running ? 'Running' : 'Stopped'}
                  icon={status?.running ? CheckCircle : XCircle}
                  status={status?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(status?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(status?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={status?.last_status ? 
                    status.last_status.charAt(0).toUpperCase() + status.last_status.slice(1) : 
                    'Unknown'}
                  icon={status?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={status?.last_status === 'success' ? 'success' : 'warning'}
                />
              </div>

              <div className="actions">
                <button 
                  onClick={fetchData} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleTrigger} 
                  className="btn btn-primary"
                  disabled={triggering}
                >
                  <Play size={18} />
                  {triggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* FII/DII Statistics Card */}
            {stats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>FII/DII Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{stats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Date</div>
                      <div className="stat-value">{stats.latest_date || '-'}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* FII/DII Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>FII/DII Collected Data</h2>
                <span className="badge">{data.length} records</span>
              </div>

              {data.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>DII Buy</th>
                        <th>DII Sell</th>
                        <th>DII Net</th>
                        <th>FII Buy</th>
                        <th>FII Sell</th>
                        <th>FII Net</th>
                        <th>Updated At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.map((record) => {
                        const dii = record.dii || {}
                        const fii = record.fii || {}
                        const diiNet = parseFloat(dii.netValue) || 0
                        const fiiNet = parseFloat(fii.netValue) || 0

                        return (
                          <tr key={record._id}>
                            <td className="date-cell">{record.date}</td>
                            <td>{formatNumber(dii.buyValue)}</td>
                            <td>{formatNumber(dii.sellValue)}</td>
                            <td className={diiNet >= 0 ? 'positive' : 'negative'}>
                              {diiNet >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                              {formatNumber(dii.netValue)}
                            </td>
                            <td>{formatNumber(fii.buyValue)}</td>
                            <td>{formatNumber(fii.sellValue)}</td>
                            <td className={fiiNet >= 0 ? 'positive' : 'negative'}>
                              {fiiNet >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                              {formatNumber(fii.netValue)}
                            </td>
                            <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        ) : activeTab === 'option-chain' ? (
          <>
            {/* NIFTY Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>NIFTY Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={optionChainStatus?.running ? 'Running' : 'Stopped'}
                  icon={optionChainStatus?.running ? CheckCircle : XCircle}
                  status={optionChainStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(optionChainStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(optionChainStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={optionChainStatus?.last_status ? 
                    optionChainStatus.last_status.charAt(0).toUpperCase() + optionChainStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={optionChainStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={optionChainStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
              </div>

              <div className="actions">
                <button 
                  onClick={fetchData} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleOptionChainTrigger} 
                  className="btn btn-primary"
                  disabled={optionChainTriggering}
                >
                  <Play size={18} />
                  {optionChainTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* NIFTY Option Chain Statistics Card */}
            {optionChainStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>NIFTY Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{optionChainStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{optionChainStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(optionChainStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* NIFTY Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>NIFTY Option Chain Collected Data</h2>
                <span className="badge">{optionChainData.length} records</span>
              </div>

              {optionChainData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {optionChainData.map((record) => (
                        <tr key={record._id}>
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        ) : activeTab === 'banknifty' ? (
          <>
            {/* BankNifty Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>BankNifty Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={bankniftyStatus?.running ? 'Running' : 'Stopped'}
                  icon={bankniftyStatus?.running ? CheckCircle : XCircle}
                  status={bankniftyStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(bankniftyStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(bankniftyStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={bankniftyStatus?.last_status ? 
                    bankniftyStatus.last_status.charAt(0).toUpperCase() + bankniftyStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={bankniftyStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={bankniftyStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
              </div>

              <div className="actions">
                <button 
                  onClick={fetchData} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleBankniftyTrigger} 
                  className="btn btn-primary"
                  disabled={bankniftyTriggering}
                >
                  <Play size={18} />
                  {bankniftyTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* BankNifty Option Chain Statistics Card */}
            {bankniftyStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>BankNifty Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{bankniftyStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{bankniftyStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(bankniftyStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* BankNifty Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>BankNifty Option Chain Collected Data</h2>
                <span className="badge">{bankniftyData.length} records</span>
              </div>

              {bankniftyData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bankniftyData.map((record) => (
                        <tr key={record._id}>
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            {/* News Collector Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>News Collector Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={newsStatus?.running ? 'Running' : 'Stopped'}
                  icon={newsStatus?.running ? CheckCircle : XCircle}
                  status={newsStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(newsStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(newsStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={newsStatus?.last_status ? 
                    newsStatus.last_status.charAt(0).toUpperCase() + newsStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={newsStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={newsStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
              </div>

              <div className="actions">
                <button 
                  onClick={fetchData} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleNewsTrigger} 
                  className="btn btn-primary"
                  disabled={newsTriggering}
                >
                  <Play size={18} />
                  {newsTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* News Statistics Card */}
            {newsStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>News Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{newsStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Newspaper size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Today's News</div>
                      <div className="stat-value">{newsStats.today_count || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="stat-label" style={{ color: 'var(--success)' }}>Positive:</div>
                      <div className="stat-value" style={{ fontSize: '1.25rem' }}>{newsStats.today_positive || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="stat-label" style={{ color: 'var(--danger)' }}>Negative:</div>
                      <div className="stat-value" style={{ fontSize: '1.25rem' }}>{newsStats.today_negative || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="stat-label">Neutral:</div>
                      <div className="stat-value" style={{ fontSize: '1.25rem' }}>{newsStats.today_neutral || 0}</div>
                    </div>
                  </div>
                </div>
                {newsStats.top_keywords && newsStats.top_keywords.length > 0 && (
                  <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                    <div className="stat-label" style={{ marginBottom: '0.5rem' }}>Top Keywords Today:</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {newsStats.top_keywords.map((item, idx) => (
                        <span key={idx} className="badge" style={{ fontSize: '0.75rem' }}>
                          {item.keyword} ({item.count})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* News Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Collected News</h2>
                <span className="badge">{newsData.length} records</span>
              </div>

              {newsData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No news data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Keyword</th>
                        <th>Title</th>
                        <th>Source</th>
                        <th>Sentiment</th>
                        <th>Published</th>
                      </tr>
                    </thead>
                    <tbody>
                      {newsData.map((record) => (
                        <tr key={record._id}>
                          <td className="date-cell">{record.date || '-'}</td>
                          <td><strong>{record.keyword || '-'}</strong></td>
                          <td>
                            <a 
                              href={record.link} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              style={{ color: 'var(--primary)', textDecoration: 'none' }}
                              onMouseOver={(e) => e.target.style.textDecoration = 'underline'}
                              onMouseOut={(e) => e.target.style.textDecoration = 'none'}
                            >
                              {record.title || '-'}
                            </a>
                          </td>
                          <td className="muted">{record.source || '-'}</td>
                          <td className={getSentimentColor(record.sentiment)}>
                            {record.sentiment === 'Positive' && <TrendingUp size={16} />}
                            {record.sentiment === 'Negative' && <TrendingDown size={16} />}
                            {record.sentiment || 'Neutral'}
                          </td>
                          <td className="muted">{formatDateTime(record.pub_date)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function StatusItem({ label, value, icon: Icon, status }) {
  return (
    <div className="status-item">
      <div className="status-item-header">
        <span className="status-label">{label}</span>
        {Icon && <Icon size={20} className={`status-icon ${status || ''}`} />}
      </div>
      <div className="status-value">{value}</div>
    </div>
  )
}

export default App
