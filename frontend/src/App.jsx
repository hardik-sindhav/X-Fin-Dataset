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
  Newspaper,
  MessageCircle
} from 'lucide-react'
import './App.css'

const API_BASE = '/api'

function App() {
  const [activeTab, setActiveTab] = useState('fiidii') // 'fiidii', 'option-chain', 'banknifty', 'hdfcbank', 'icicibank', 'sbin', 'kotakbank', 'axisbank', 'bankbaroda', 'pnb', 'canbk', 'aubank', 'indusindbk', 'idfcfirstb', 'federalbnk', 'news', or 'twitter'
  
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
  
  // HDFC Bank state
  const [hdfcbankStatus, setHdfcbankStatus] = useState(null)
  const [hdfcbankData, setHdfcbankData] = useState([])
  const [hdfcbankStats, setHdfcbankStats] = useState(null)
  
  // ICICI Bank state
  const [icicibankStatus, setIcicibankStatus] = useState(null)
  const [icicibankData, setIcicibankData] = useState([])
  const [icicibankStats, setIcicibankStats] = useState(null)
  
  // SBIN state
  const [sbinStatus, setSbinStatus] = useState(null)
  const [sbinData, setSbinData] = useState([])
  const [sbinStats, setSbinStats] = useState(null)
  
  // Kotak Bank state
  const [kotakbankStatus, setKotakbankStatus] = useState(null)
  const [kotakbankData, setKotakbankData] = useState([])
  const [kotakbankStats, setKotakbankStats] = useState(null)
  
  // Axis Bank state
  const [axisbankStatus, setAxisbankStatus] = useState(null)
  const [axisbankData, setAxisbankData] = useState([])
  const [axisbankStats, setAxisbankStats] = useState(null)
  
  // Bank of Baroda state
  const [bankbarodaStatus, setBankbarodaStatus] = useState(null)
  const [bankbarodaData, setBankbarodaData] = useState([])
  const [bankbarodaStats, setBankbarodaStats] = useState(null)
  
  // PNB state
  const [pnbStatus, setPnbStatus] = useState(null)
  const [pnbData, setPnbData] = useState([])
  const [pnbStats, setPnbStats] = useState(null)
  
  // CANBK state
  const [canbkStatus, setCanbkStatus] = useState(null)
  const [canbkData, setCanbkData] = useState([])
  const [canbkStats, setCanbkStats] = useState(null)
  
  // AUBANK state
  const [aubankStatus, setAubankStatus] = useState(null)
  const [aubankData, setAubankData] = useState([])
  const [aubankStats, setAubankStats] = useState(null)
  
  // INDUSINDBK state
  const [indusindbkStatus, setIndusindbkStatus] = useState(null)
  const [indusindbkData, setIndusindbkData] = useState([])
  const [indusindbkStats, setIndusindbkStats] = useState(null)
  
  // IDFCFIRSTB state
  const [idfcfirstbStatus, setIdfcfirstbStatus] = useState(null)
  const [idfcfirstbData, setIdfcfirstbData] = useState([])
  const [idfcfirstbStats, setIdfcfirstbStats] = useState(null)
  
  // FEDERALBNK state
  const [federalbnkStatus, setFederalbnkStatus] = useState(null)
  const [federalbnkData, setFederalbnkData] = useState([])
  const [federalbnkStats, setFederalbnkStats] = useState(null)
  
  // News state
  const [newsStatus, setNewsStatus] = useState(null)
  const [newsData, setNewsData] = useState([])
  const [newsStats, setNewsStats] = useState(null)
  
  // Twitter state
  const [twitterStatus, setTwitterStatus] = useState(null)
  const [twitterData, setTwitterData] = useState([])
  const [twitterStats, setTwitterStats] = useState(null)
  
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [optionChainTriggering, setOptionChainTriggering] = useState(false)
  const [bankniftyTriggering, setBankniftyTriggering] = useState(false)
  const [hdfcbankTriggering, setHdfcbankTriggering] = useState(false)
  const [icicibankTriggering, setIcicibankTriggering] = useState(false)
  const [sbinTriggering, setSbinTriggering] = useState(false)
  const [kotakbankTriggering, setKotakbankTriggering] = useState(false)
  const [axisbankTriggering, setAxisbankTriggering] = useState(false)
  const [bankbarodaTriggering, setBankbarodaTriggering] = useState(false)
  const [pnbTriggering, setPnbTriggering] = useState(false)
  const [canbkTriggering, setCanbkTriggering] = useState(false)
  const [aubankTriggering, setAubankTriggering] = useState(false)
  const [indusindbkTriggering, setIndusindbkTriggering] = useState(false)
  const [idfcfirstbTriggering, setIdfcfirstbTriggering] = useState(false)
  const [federalbnkTriggering, setFederalbnkTriggering] = useState(false)
  const [newsTriggering, setNewsTriggering] = useState(false)
  const [twitterTriggering, setTwitterTriggering] = useState(false)

  const fetchData = async () => {
    try {
      const [
        statusRes, dataRes, statsRes, 
        optionChainStatusRes, optionChainDataRes, optionChainStatsRes, 
        bankniftyStatusRes, bankniftyDataRes, bankniftyStatsRes,
        hdfcbankStatusRes, hdfcbankDataRes, hdfcbankStatsRes,
        icicibankStatusRes, icicibankDataRes, icicibankStatsRes,
        sbinStatusRes, sbinDataRes, sbinStatsRes,
        kotakbankStatusRes, kotakbankDataRes, kotakbankStatsRes,
        axisbankStatusRes, axisbankDataRes, axisbankStatsRes,
        bankbarodaStatusRes, bankbarodaDataRes, bankbarodaStatsRes,
        pnbStatusRes, pnbDataRes, pnbStatsRes,
        canbkStatusRes, canbkDataRes, canbkStatsRes,
        aubankStatusRes, aubankDataRes, aubankStatsRes,
        indusindbkStatusRes, indusindbkDataRes, indusindbkStatsRes,
        idfcfirstbStatusRes, idfcfirstbDataRes, idfcfirstbStatsRes,
        federalbnkStatusRes, federalbnkDataRes, federalbnkStatsRes,
        newsStatusRes, newsDataRes, newsStatsRes,
        twitterStatusRes, twitterDataRes, twitterStatsRes
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
        axios.get(`${API_BASE}/hdfcbank/status`),
        axios.get(`${API_BASE}/hdfcbank/data`),
        axios.get(`${API_BASE}/hdfcbank/stats`),
        axios.get(`${API_BASE}/icicibank/status`),
        axios.get(`${API_BASE}/icicibank/data`),
        axios.get(`${API_BASE}/icicibank/stats`),
        axios.get(`${API_BASE}/sbin/status`),
        axios.get(`${API_BASE}/sbin/data`),
        axios.get(`${API_BASE}/sbin/stats`),
        axios.get(`${API_BASE}/kotakbank/status`),
        axios.get(`${API_BASE}/kotakbank/data`),
        axios.get(`${API_BASE}/kotakbank/stats`),
        axios.get(`${API_BASE}/axisbank/status`),
        axios.get(`${API_BASE}/axisbank/data`),
        axios.get(`${API_BASE}/axisbank/stats`),
        axios.get(`${API_BASE}/bankbaroda/status`),
        axios.get(`${API_BASE}/bankbaroda/data`),
        axios.get(`${API_BASE}/bankbaroda/stats`),
        axios.get(`${API_BASE}/pnb/status`),
        axios.get(`${API_BASE}/pnb/data`),
        axios.get(`${API_BASE}/pnb/stats`),
        axios.get(`${API_BASE}/canbk/status`),
        axios.get(`${API_BASE}/canbk/data`),
        axios.get(`${API_BASE}/canbk/stats`),
        axios.get(`${API_BASE}/aubank/status`),
        axios.get(`${API_BASE}/aubank/data`),
        axios.get(`${API_BASE}/aubank/stats`),
        axios.get(`${API_BASE}/indusindbk/status`),
        axios.get(`${API_BASE}/indusindbk/data`),
        axios.get(`${API_BASE}/indusindbk/stats`),
        axios.get(`${API_BASE}/idfcfirstb/status`),
        axios.get(`${API_BASE}/idfcfirstb/data`),
        axios.get(`${API_BASE}/idfcfirstb/stats`),
        axios.get(`${API_BASE}/federalbnk/status`),
        axios.get(`${API_BASE}/federalbnk/data`),
        axios.get(`${API_BASE}/federalbnk/stats`),
        axios.get(`${API_BASE}/news/status`),
        axios.get(`${API_BASE}/news/data`),
        axios.get(`${API_BASE}/news/stats`),
        axios.get(`${API_BASE}/twitter/status`),
        axios.get(`${API_BASE}/twitter/data`),
        axios.get(`${API_BASE}/twitter/stats`)
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
      
      setHdfcbankStatus(hdfcbankStatusRes.data)
      setHdfcbankData(hdfcbankDataRes.data.data || [])
      setHdfcbankStats(hdfcbankStatsRes.data.stats)
      
      setIcicibankStatus(icicibankStatusRes.data)
      setIcicibankData(icicibankDataRes.data.data || [])
      setIcicibankStats(icicibankStatsRes.data.stats)
      
      setSbinStatus(sbinStatusRes.data)
      setSbinData(sbinDataRes.data.data || [])
      setSbinStats(sbinStatsRes.data.stats)
      
      setKotakbankStatus(kotakbankStatusRes.data)
      setKotakbankData(kotakbankDataRes.data.data || [])
      setKotakbankStats(kotakbankStatsRes.data.stats)
      
      setAxisbankStatus(axisbankStatusRes.data)
      setAxisbankData(axisbankDataRes.data.data || [])
      setAxisbankStats(axisbankStatsRes.data.stats)
      
      setBankbarodaStatus(bankbarodaStatusRes.data)
      setBankbarodaData(bankbarodaDataRes.data.data || [])
      setBankbarodaStats(bankbarodaStatsRes.data.stats)
      
      setPnbStatus(pnbStatusRes.data)
      setPnbData(pnbDataRes.data.data || [])
      setPnbStats(pnbStatsRes.data.stats)
      
      setCanbkStatus(canbkStatusRes.data)
      setCanbkData(canbkDataRes.data.data || [])
      setCanbkStats(canbkStatsRes.data.stats)
      
      setAubankStatus(aubankStatusRes.data)
      setAubankData(aubankDataRes.data.data || [])
      setAubankStats(aubankStatsRes.data.stats)
      
      setIndusindbkStatus(indusindbkStatusRes.data)
      setIndusindbkData(indusindbkDataRes.data.data || [])
      setIndusindbkStats(indusindbkStatsRes.data.stats)
      
      setIdfcfirstbStatus(idfcfirstbStatusRes.data)
      setIdfcfirstbData(idfcfirstbDataRes.data.data || [])
      setIdfcfirstbStats(idfcfirstbStatsRes.data.stats)
      
      setFederalbnkStatus(federalbnkStatusRes.data)
      setFederalbnkData(federalbnkDataRes.data.data || [])
      setFederalbnkStats(federalbnkStatsRes.data.stats)
      
      setNewsStatus(newsStatusRes.data)
      setNewsData(newsDataRes.data.data || [])
      setNewsStats(newsStatsRes.data.stats)
      
      setTwitterStatus(twitterStatusRes.data)
      setTwitterData(twitterDataRes.data.data || [])
      setTwitterStats(twitterStatsRes.data.stats)
      
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

  const handleHdfcbankTrigger = async () => {
    setHdfcbankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/hdfcbank/trigger`)
      if (res.data.success) {
        alert('✅ HDFC Bank Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ HDFC Bank Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setHdfcbankTriggering(false)
    }
  }

  const handleIcicibankTrigger = async () => {
    setIcicibankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/icicibank/trigger`)
      if (res.data.success) {
        alert('✅ ICICI Bank Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ ICICI Bank Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setIcicibankTriggering(false)
    }
  }

  const handleSbinTrigger = async () => {
    setSbinTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/sbin/trigger`)
      if (res.data.success) {
        alert('✅ SBIN Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ SBIN Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setSbinTriggering(false)
    }
  }

  const handleKotakbankTrigger = async () => {
    setKotakbankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/kotakbank/trigger`)
      if (res.data.success) {
        alert('✅ Kotak Bank Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ Kotak Bank Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setKotakbankTriggering(false)
    }
  }

  const handleAxisbankTrigger = async () => {
    setAxisbankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/axisbank/trigger`)
      if (res.data.success) {
        alert('✅ Axis Bank Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ Axis Bank Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setAxisbankTriggering(false)
    }
  }

  const handleBankbarodaTrigger = async () => {
    setBankbarodaTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/bankbaroda/trigger`)
      if (res.data.success) {
        alert('✅ Bank of Baroda Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ Bank of Baroda Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setBankbarodaTriggering(false)
    }
  }

  const handlePnbTrigger = async () => {
    setPnbTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/pnb/trigger`)
      if (res.data.success) {
        alert('✅ PNB Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ PNB Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setPnbTriggering(false)
    }
  }

  const handleCanbkTrigger = async () => {
    setCanbkTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/canbk/trigger`)
      if (res.data.success) {
        alert('✅ CANBK Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ CANBK Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setCanbkTriggering(false)
    }
  }

  const handleAubankTrigger = async () => {
    setAubankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/aubank/trigger`)
      if (res.data.success) {
        alert('✅ AUBANK Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ AUBANK Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setAubankTriggering(false)
    }
  }

  const handleIndusindbkTrigger = async () => {
    setIndusindbkTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/indusindbk/trigger`)
      if (res.data.success) {
        alert('✅ INDUSINDBK Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ INDUSINDBK Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setIndusindbkTriggering(false)
    }
  }

  const handleIdfcfirstbTrigger = async () => {
    setIdfcfirstbTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/idfcfirstb/trigger`)
      if (res.data.success) {
        alert('✅ IDFCFIRSTB Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ IDFCFIRSTB Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setIdfcfirstbTriggering(false)
    }
  }

  const handleFederalbnkTrigger = async () => {
    setFederalbnkTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/federalbnk/trigger`)
      if (res.data.success) {
        alert('✅ FEDERALBNK Option Chain Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ FEDERALBNK Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setFederalbnkTriggering(false)
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

  const handleTwitterTrigger = async () => {
    setTwitterTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/twitter/trigger`)
      if (res.data.success) {
        alert('✅ Twitter Data collection completed successfully!')
        setTimeout(fetchData, 2000)
      } else {
        alert('❌ Twitter Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setTwitterTriggering(false)
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
          className={`tab ${activeTab === 'hdfcbank' ? 'active' : ''}`}
          onClick={() => setActiveTab('hdfcbank')}
        >
          <BarChart3 size={18} />
          HDFC Bank Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'icicibank' ? 'active' : ''}`}
          onClick={() => setActiveTab('icicibank')}
        >
          <BarChart3 size={18} />
          ICICI Bank Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'sbin' ? 'active' : ''}`}
          onClick={() => setActiveTab('sbin')}
        >
          <BarChart3 size={18} />
          SBIN Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'kotakbank' ? 'active' : ''}`}
          onClick={() => setActiveTab('kotakbank')}
        >
          <BarChart3 size={18} />
          Kotak Bank Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'axisbank' ? 'active' : ''}`}
          onClick={() => setActiveTab('axisbank')}
        >
          <BarChart3 size={18} />
          Axis Bank Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'bankbaroda' ? 'active' : ''}`}
          onClick={() => setActiveTab('bankbaroda')}
        >
          <BarChart3 size={18} />
          Bank of Baroda Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'pnb' ? 'active' : ''}`}
          onClick={() => setActiveTab('pnb')}
        >
          <BarChart3 size={18} />
          PNB Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'canbk' ? 'active' : ''}`}
          onClick={() => setActiveTab('canbk')}
        >
          <BarChart3 size={18} />
          CANBK Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'aubank' ? 'active' : ''}`}
          onClick={() => setActiveTab('aubank')}
        >
          <BarChart3 size={18} />
          AUBANK Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'indusindbk' ? 'active' : ''}`}
          onClick={() => setActiveTab('indusindbk')}
        >
          <BarChart3 size={18} />
          INDUSINDBK Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'idfcfirstb' ? 'active' : ''}`}
          onClick={() => setActiveTab('idfcfirstb')}
        >
          <BarChart3 size={18} />
          IDFCFIRSTB Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'federalbnk' ? 'active' : ''}`}
          onClick={() => setActiveTab('federalbnk')}
        >
          <BarChart3 size={18} />
          FEDERALBNK Option Chain
        </button>
        <button 
          className={`tab ${activeTab === 'news' ? 'active' : ''}`}
          onClick={() => setActiveTab('news')}
        >
          <Newspaper size={18} />
          News & Sentiment
        </button>
        <button 
          className={`tab ${activeTab === 'twitter' ? 'active' : ''}`}
          onClick={() => setActiveTab('twitter')}
        >
          <MessageCircle size={18} />
          Twitter & Sentiment
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
        ) : activeTab === 'hdfcbank' ? (
          <>
            {/* HDFC Bank Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>HDFC Bank Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={hdfcbankStatus?.running ? 'Running' : 'Stopped'}
                  icon={hdfcbankStatus?.running ? CheckCircle : XCircle}
                  status={hdfcbankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(hdfcbankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(hdfcbankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={hdfcbankStatus?.last_status ? 
                    hdfcbankStatus.last_status.charAt(0).toUpperCase() + hdfcbankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={hdfcbankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={hdfcbankStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleHdfcbankTrigger} 
                  className="btn btn-primary"
                  disabled={hdfcbankTriggering}
                >
                  <Play size={18} />
                  {hdfcbankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* HDFC Bank Option Chain Statistics Card */}
            {hdfcbankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>HDFC Bank Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{hdfcbankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{hdfcbankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(hdfcbankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* HDFC Bank Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>HDFC Bank Option Chain Collected Data</h2>
                <span className="badge">{hdfcbankData.length} records</span>
              </div>

              {hdfcbankData.length === 0 ? (
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
                      {hdfcbankData.map((record) => (
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
        ) : activeTab === 'icicibank' ? (
          <>
            {/* ICICI Bank Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>ICICI Bank Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={icicibankStatus?.running ? 'Running' : 'Stopped'}
                  icon={icicibankStatus?.running ? CheckCircle : XCircle}
                  status={icicibankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(icicibankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(icicibankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={icicibankStatus?.last_status ? 
                    icicibankStatus.last_status.charAt(0).toUpperCase() + icicibankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={icicibankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={icicibankStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleIcicibankTrigger} 
                  className="btn btn-primary"
                  disabled={icicibankTriggering}
                >
                  <Play size={18} />
                  {icicibankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* ICICI Bank Option Chain Statistics Card */}
            {icicibankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>ICICI Bank Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{icicibankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{icicibankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(icicibankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ICICI Bank Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>ICICI Bank Option Chain Collected Data</h2>
                <span className="badge">{icicibankData.length} records</span>
              </div>

              {icicibankData.length === 0 ? (
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
                      {icicibankData.map((record) => (
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
        ) : activeTab === 'sbin' ? (
          <>
            {/* SBIN Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>SBIN Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={sbinStatus?.running ? 'Running' : 'Stopped'}
                  icon={sbinStatus?.running ? CheckCircle : XCircle}
                  status={sbinStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(sbinStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(sbinStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={sbinStatus?.last_status ? 
                    sbinStatus.last_status.charAt(0).toUpperCase() + sbinStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={sbinStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={sbinStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleSbinTrigger} 
                  className="btn btn-primary"
                  disabled={sbinTriggering}
                >
                  <Play size={18} />
                  {sbinTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* SBIN Option Chain Statistics Card */}
            {sbinStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>SBIN Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{sbinStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{sbinStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(sbinStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* SBIN Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>SBIN Option Chain Collected Data</h2>
                <span className="badge">{sbinData.length} records</span>
              </div>

              {sbinData.length === 0 ? (
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
                      {sbinData.map((record) => (
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
        ) : activeTab === 'kotakbank' ? (
          <>
            {/* Kotak Bank Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Kotak Bank Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={kotakbankStatus?.running ? 'Running' : 'Stopped'}
                  icon={kotakbankStatus?.running ? CheckCircle : XCircle}
                  status={kotakbankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(kotakbankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(kotakbankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={kotakbankStatus?.last_status ? 
                    kotakbankStatus.last_status.charAt(0).toUpperCase() + kotakbankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={kotakbankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={kotakbankStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleKotakbankTrigger} 
                  className="btn btn-primary"
                  disabled={kotakbankTriggering}
                >
                  <Play size={18} />
                  {kotakbankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Kotak Bank Option Chain Statistics Card */}
            {kotakbankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Kotak Bank Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{kotakbankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{kotakbankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(kotakbankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Kotak Bank Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Kotak Bank Option Chain Collected Data</h2>
                <span className="badge">{kotakbankData.length} records</span>
              </div>

              {kotakbankData.length === 0 ? (
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
                      {kotakbankData.map((record) => (
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
        ) : activeTab === 'axisbank' ? (
          <>
            {/* Axis Bank Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Axis Bank Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={axisbankStatus?.running ? 'Running' : 'Stopped'}
                  icon={axisbankStatus?.running ? CheckCircle : XCircle}
                  status={axisbankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(axisbankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(axisbankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={axisbankStatus?.last_status ? 
                    axisbankStatus.last_status.charAt(0).toUpperCase() + axisbankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={axisbankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={axisbankStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleAxisbankTrigger} 
                  className="btn btn-primary"
                  disabled={axisbankTriggering}
                >
                  <Play size={18} />
                  {axisbankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Axis Bank Option Chain Statistics Card */}
            {axisbankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Axis Bank Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{axisbankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{axisbankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(axisbankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Axis Bank Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Axis Bank Option Chain Collected Data</h2>
                <span className="badge">{axisbankData.length} records</span>
              </div>

              {axisbankData.length === 0 ? (
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
                      {axisbankData.map((record) => (
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
        ) : activeTab === 'bankbaroda' ? (
          <>
            {/* Bank of Baroda Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Bank of Baroda Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={bankbarodaStatus?.running ? 'Running' : 'Stopped'}
                  icon={bankbarodaStatus?.running ? CheckCircle : XCircle}
                  status={bankbarodaStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(bankbarodaStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(bankbarodaStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={bankbarodaStatus?.last_status ? 
                    bankbarodaStatus.last_status.charAt(0).toUpperCase() + bankbarodaStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={bankbarodaStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={bankbarodaStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleBankbarodaTrigger} 
                  className="btn btn-primary"
                  disabled={bankbarodaTriggering}
                >
                  <Play size={18} />
                  {bankbarodaTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Bank of Baroda Option Chain Statistics Card */}
            {bankbarodaStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Bank of Baroda Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{bankbarodaStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{bankbarodaStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(bankbarodaStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Bank of Baroda Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Bank of Baroda Option Chain Collected Data</h2>
                <span className="badge">{bankbarodaData.length} records</span>
              </div>

              {bankbarodaData.length === 0 ? (
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
                      {bankbarodaData.map((record) => (
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
        ) : activeTab === 'pnb' ? (
          <>
            {/* PNB Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>PNB Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={pnbStatus?.running ? 'Running' : 'Stopped'}
                  icon={pnbStatus?.running ? CheckCircle : XCircle}
                  status={pnbStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(pnbStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(pnbStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={pnbStatus?.last_status ? 
                    pnbStatus.last_status.charAt(0).toUpperCase() + pnbStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={pnbStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={pnbStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handlePnbTrigger} 
                  className="btn btn-primary"
                  disabled={pnbTriggering}
                >
                  <Play size={18} />
                  {pnbTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* PNB Option Chain Statistics Card */}
            {pnbStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>PNB Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{pnbStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{pnbStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(pnbStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* PNB Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>PNB Option Chain Collected Data</h2>
                <span className="badge">{pnbData.length} records</span>
              </div>

              {pnbData.length === 0 ? (
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
                      {pnbData.map((record) => (
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
        ) : activeTab === 'canbk' ? (
          <>
            {/* CANBK Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>CANBK Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={canbkStatus?.running ? 'Running' : 'Stopped'}
                  icon={canbkStatus?.running ? CheckCircle : XCircle}
                  status={canbkStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(canbkStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(canbkStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={canbkStatus?.last_status ? 
                    canbkStatus.last_status.charAt(0).toUpperCase() + canbkStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={canbkStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={canbkStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleCanbkTrigger} 
                  className="btn btn-primary"
                  disabled={canbkTriggering}
                >
                  <Play size={18} />
                  {canbkTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* CANBK Option Chain Statistics Card */}
            {canbkStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>CANBK Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{canbkStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{canbkStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(canbkStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* CANBK Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>CANBK Option Chain Collected Data</h2>
                <span className="badge">{canbkData.length} records</span>
              </div>

              {canbkData.length === 0 ? (
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
                      {canbkData.map((record) => (
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
        ) : activeTab === 'aubank' ? (
          <>
            {/* AUBANK Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>AUBANK Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={aubankStatus?.running ? 'Running' : 'Stopped'}
                  icon={aubankStatus?.running ? CheckCircle : XCircle}
                  status={aubankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(aubankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(aubankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={aubankStatus?.last_status ? 
                    aubankStatus.last_status.charAt(0).toUpperCase() + aubankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={aubankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={aubankStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleAubankTrigger} 
                  className="btn btn-primary"
                  disabled={aubankTriggering}
                >
                  <Play size={18} />
                  {aubankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* AUBANK Option Chain Statistics Card */}
            {aubankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>AUBANK Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{aubankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{aubankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(aubankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* AUBANK Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>AUBANK Option Chain Collected Data</h2>
                <span className="badge">{aubankData.length} records</span>
              </div>

              {aubankData.length === 0 ? (
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
                      {aubankData.map((record) => (
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
        ) : activeTab === 'indusindbk' ? (
          <>
            {/* INDUSINDBK Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>INDUSINDBK Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={indusindbkStatus?.running ? 'Running' : 'Stopped'}
                  icon={indusindbkStatus?.running ? CheckCircle : XCircle}
                  status={indusindbkStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(indusindbkStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(indusindbkStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={indusindbkStatus?.last_status ? 
                    indusindbkStatus.last_status.charAt(0).toUpperCase() + indusindbkStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={indusindbkStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={indusindbkStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleIndusindbkTrigger} 
                  className="btn btn-primary"
                  disabled={indusindbkTriggering}
                >
                  <Play size={18} />
                  {indusindbkTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* INDUSINDBK Option Chain Statistics Card */}
            {indusindbkStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>INDUSINDBK Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{indusindbkStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{indusindbkStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(indusindbkStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* INDUSINDBK Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>INDUSINDBK Option Chain Collected Data</h2>
                <span className="badge">{indusindbkData.length} records</span>
              </div>

              {indusindbkData.length === 0 ? (
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
                      {indusindbkData.map((record) => (
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
        ) : activeTab === 'idfcfirstb' ? (
          <>
            {/* IDFCFIRSTB Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>IDFCFIRSTB Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={idfcfirstbStatus?.running ? 'Running' : 'Stopped'}
                  icon={idfcfirstbStatus?.running ? CheckCircle : XCircle}
                  status={idfcfirstbStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(idfcfirstbStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(idfcfirstbStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={idfcfirstbStatus?.last_status ? 
                    idfcfirstbStatus.last_status.charAt(0).toUpperCase() + idfcfirstbStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={idfcfirstbStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={idfcfirstbStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleIdfcfirstbTrigger} 
                  className="btn btn-primary"
                  disabled={idfcfirstbTriggering}
                >
                  <Play size={18} />
                  {idfcfirstbTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* IDFCFIRSTB Option Chain Statistics Card */}
            {idfcfirstbStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>IDFCFIRSTB Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{idfcfirstbStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{idfcfirstbStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(idfcfirstbStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* IDFCFIRSTB Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>IDFCFIRSTB Option Chain Collected Data</h2>
                <span className="badge">{idfcfirstbData.length} records</span>
              </div>

              {idfcfirstbData.length === 0 ? (
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
                      {idfcfirstbData.map((record) => (
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
        ) : activeTab === 'federalbnk' ? (
          <>
            {/* FEDERALBNK Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>FEDERALBNK Option Chain Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={federalbnkStatus?.running ? 'Running' : 'Stopped'}
                  icon={federalbnkStatus?.running ? CheckCircle : XCircle}
                  status={federalbnkStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(federalbnkStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(federalbnkStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={federalbnkStatus?.last_status ? 
                    federalbnkStatus.last_status.charAt(0).toUpperCase() + federalbnkStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={federalbnkStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={federalbnkStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleFederalbnkTrigger} 
                  className="btn btn-primary"
                  disabled={federalbnkTriggering}
                >
                  <Play size={18} />
                  {federalbnkTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* FEDERALBNK Option Chain Statistics Card */}
            {federalbnkStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>FEDERALBNK Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{federalbnkStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{federalbnkStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(federalbnkStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* FEDERALBNK Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>FEDERALBNK Option Chain Collected Data</h2>
                <span className="badge">{federalbnkData.length} records</span>
              </div>

              {federalbnkData.length === 0 ? (
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
                      {federalbnkData.map((record) => (
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
        ) : (
          <>
            {/* Twitter Collector Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Twitter Collector Cronjob Status</h2>
                <button onClick={fetchData} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={twitterStatus?.running ? 'Running' : 'Stopped'}
                  icon={twitterStatus?.running ? CheckCircle : XCircle}
                  status={twitterStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(twitterStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(twitterStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={twitterStatus?.last_status ? 
                    twitterStatus.last_status.charAt(0).toUpperCase() + twitterStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={twitterStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={twitterStatus?.last_status === 'success' ? 'success' : 'warning'}
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
                  onClick={handleTwitterTrigger} 
                  className="btn btn-primary"
                  disabled={twitterTriggering}
                >
                  <Play size={18} />
                  {twitterTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Twitter Statistics Card */}
            {twitterStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Twitter Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{twitterStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <MessageCircle size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Today's Tweets</div>
                      <div className="stat-value">{twitterStats.today_count || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="stat-label" style={{ color: 'var(--success)' }}>Positive:</div>
                      <div className="stat-value" style={{ fontSize: '1.25rem' }}>{twitterStats.today_positive || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="stat-label" style={{ color: 'var(--danger)' }}>Negative:</div>
                      <div className="stat-value" style={{ fontSize: '1.25rem' }}>{twitterStats.today_negative || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="stat-label">Neutral:</div>
                      <div className="stat-value" style={{ fontSize: '1.25rem' }}>{twitterStats.today_neutral || 0}</div>
                    </div>
                  </div>
                </div>
                {twitterStats.top_users && twitterStats.top_users.length > 0 && (
                  <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                    <div className="stat-label" style={{ marginBottom: '0.5rem' }}>Top Users Today:</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {twitterStats.top_users.map((item, idx) => (
                        <span key={idx} className="badge" style={{ fontSize: '0.75rem' }}>
                          @{item.username} ({item.count} tweets, {item.avg_followers?.toLocaleString()} avg followers)
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Twitter Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Collected Tweets</h2>
                <span className="badge">{twitterData.length} records</span>
              </div>

              {twitterData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No tweet data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Username</th>
                        <th>Content</th>
                        <th>Likes</th>
                        <th>Retweets</th>
                        <th>Followers</th>
                        <th>Sentiment</th>
                        <th>Tweet Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {twitterData.map((record) => (
                        <tr key={record._id}>
                          <td className="date-cell">{record.date || '-'}</td>
                          <td><strong>@{record.username || '-'}</strong></td>
                          <td style={{ maxWidth: '400px', wordWrap: 'break-word' }}>{record.content || '-'}</td>
                          <td>{record.like_count || 0}</td>
                          <td>{record.retweet_count || 0}</td>
                          <td>{record.followers_count?.toLocaleString() || 0}</td>
                          <td className={getSentimentColor(record.sentiment)}>
                            {record.sentiment === 'Positive' && <TrendingUp size={16} />}
                            {record.sentiment === 'Negative' && <TrendingDown size={16} />}
                            {record.sentiment || 'Neutral'}
                          </td>
                          <td className="muted">{formatDateTime(record.tweet_date)}</td>
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
