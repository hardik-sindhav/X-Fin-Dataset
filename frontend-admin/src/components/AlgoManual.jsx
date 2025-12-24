import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronLeft, ChevronRight, RefreshCw, TrendingUp, TrendingDown, Save, Trash2 } from 'lucide-react'
import { API_BASE } from '../config'

const AlgoManual = () => {
  // Option chain options: 12 banks + 4 indices
  const optionChains = [
    { value: 'nifty', label: 'NIFTY' },
    { value: 'banknifty', label: 'BankNifty' },
    { value: 'finnifty', label: 'Finnifty' },
    { value: 'midcpnifty', label: 'MidcapNifty' },
    { value: 'hdfcbank', label: 'HDFC Bank' },
    { value: 'icicibank', label: 'ICICI Bank' },
    { value: 'sbin', label: 'SBIN' },
    { value: 'kotakbank', label: 'Kotak Bank' },
    { value: 'axisbank', label: 'Axis Bank' },
    { value: 'bankbaroda', label: 'Bank of Baroda' },
    { value: 'pnb', label: 'PNB' },
    { value: 'canbk', label: 'CANBK' },
    { value: 'aubank', label: 'AUBANK' },
    { value: 'indusindbk', label: 'IndusInd Bank' },
    { value: 'idfcfirstb', label: 'IDFC First Bank' },
    { value: 'federalbnk', label: 'Federal Bank' }
  ]

  // Lot sizes per instrument (shares per lot)
  const lotSizes = {
    banknifty: 35,
    nifty: 75,
    midcpnifty: 140,
    finnifty: 65,
    hdfcbank: 550,
    icicibank: 700,
    default: 300
  }

  const getLotSize = () => lotSizes[selectedChain] || lotSizes.default

  const [selectedChain, setSelectedChain] = useState('nifty')
  const [dateType, setDateType] = useState('today')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [currentRecord, setCurrentRecord] = useState(null)
  const [currentOI, setCurrentOI] = useState({ totalCallOI: 0, totalPutOI: 0 })
  const [optionData, setOptionData] = useState([])

  const [optionType, setOptionType] = useState('CE')
  const [selectedStrike, setSelectedStrike] = useState('')
  const [tpMode, setTpMode] = useState('rupee') // rupee | percent
  const [tpValue, setTpValue] = useState('')
  const [slMode, setSlMode] = useState('rupee') // rupee | percent
  const [slValue, setSlValue] = useState('')
  const [trade, setTrade] = useState(null) // current open/closed trade state
  const [savedTrades, setSavedTrades] = useState([]) // all saved trades

  // Load saved trades from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('algoManualTrades')
      if (saved) {
        setSavedTrades(JSON.parse(saved))
      }
    } catch (error) {
      console.error('Error loading saved trades:', error)
    }
  }, [])

  // Save trades to localStorage whenever savedTrades changes
  useEffect(() => {
    try {
      localStorage.setItem('algoManualTrades', JSON.stringify(savedTrades))
    } catch (error) {
      console.error('Error saving trades:', error)
    }
  }, [savedTrades])

  const getDateForType = () => {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    switch (dateType) {
      case 'today':
        return today.toISOString().split('T')[0]
      case 'yesterday':
        return yesterday.toISOString().split('T')[0]
      case 'range':
        return { startDate, endDate }
      default:
        return today.toISOString().split('T')[0]
    }
  }

  const extractOptionChainData = (record) => {
    let optionData = null

    if (record?.records?.data && Array.isArray(record.records.data)) {
      optionData = record.records.data
    } else if (record?.data && Array.isArray(record.data)) {
      optionData = record.data
    } else if (record?.optionChain && Array.isArray(record.optionChain)) {
      optionData = record.optionChain
    } else if (record?.option_chain && Array.isArray(record.option_chain)) {
      optionData = record.option_chain
    } else if (Array.isArray(record)) {
      optionData = record
    }

    if (!optionData || !Array.isArray(optionData)) {
      return []
    }

    return optionData
      .map((item) => {
        const strike = item.strikePrice || item.strike || item.strike_price
        const ce = item.CE || item.ce || {}
        const pe = item.PE || item.pe || {}

        return {
          strike: parseFloat(strike) || 0,
          ceOI: parseFloat(ce.openInterest || ce.open_interest || ce.oi || ce.OpenInterest || 0) || 0,
          peOI: parseFloat(pe.openInterest || pe.open_interest || pe.oi || pe.OpenInterest || 0) || 0,
          ceLTP: parseFloat(ce.lastPrice || ce.last_price || ce.ltp || ce.LastPrice || 0) || 0,
          peLTP: parseFloat(pe.lastPrice || pe.last_price || pe.ltp || pe.LastPrice || 0) || 0
        }
      })
      .filter((item) => item.strike > 0)
  }

  const computeOI = (optionData, underlyingValue) => {
    if (!optionData || optionData.length === 0) {
      return { totalCallOI: 0, totalPutOI: 0 }
    }

    // Find ATM strike (closest to underlying value)
    let atmStrike = null
    let minDiff = Infinity
    
    optionData.forEach((s) => {
      const diff = Math.abs(s.strike - (underlyingValue || 0))
      if (diff < minDiff) {
        minDiff = diff
        atmStrike = s.strike
      }
    })

    if (!atmStrike) {
      // Fallback: use all strikes if ATM not found
      const totalCallOI = optionData.reduce((sum, s) => sum + (s.ceOI || 0), 0)
      const totalPutOI = optionData.reduce((sum, s) => sum + (s.peOI || 0), 0)
      return { totalCallOI, totalPutOI }
    }

    // Get strikes: ATM, +1 above, +1 below
    const strikes = [atmStrike]
    
    // Find +1 above (next higher strike)
    const sortedStrikes = [...optionData].sort((a, b) => a.strike - b.strike)
    const atmIndex = sortedStrikes.findIndex(s => s.strike === atmStrike)
    
    if (atmIndex < sortedStrikes.length - 1) {
      strikes.push(sortedStrikes[atmIndex + 1].strike) // +1 above
    }
    if (atmIndex > 0) {
      strikes.push(sortedStrikes[atmIndex - 1].strike) // +1 below
    }

    // Calculate OI for selected strikes only
    let totalCallOI = 0
    let totalPutOI = 0

    optionData.forEach((s) => {
      if (strikes.includes(s.strike)) {
        totalCallOI += s.ceOI || 0
        totalPutOI += s.peOI || 0
      }
    })

    return { totalCallOI, totalPutOI }
  }

  const fetchData = async () => {
    setLoading(true)
    setTrade(null)
    try {
      const dateValue = getDateForType()
      let url = `${API_BASE}/${selectedChain}/data`

      if (dateType === 'range') {
        if (!dateValue.startDate || !dateValue.endDate) {
          alert('Please select both start and end dates')
          setLoading(false)
          return
        }
        url += `?start_date=${dateValue.startDate}&end_date=${dateValue.endDate}&limit=1000&full=true`
      } else {
        url += `?start_date=${dateValue}&end_date=${dateValue}&limit=1000&full=true`
      }

      const response = await axios.get(url)
      const fetchedData = response.data.data || response.data || []

      const sortedData = fetchedData.sort((a, b) => {
        const dateA = new Date(a.insertedAt || a.records?.timestamp || a.timestamp || a.date || a.createdAt || 0)
        const dateB = new Date(b.insertedAt || b.records?.timestamp || b.timestamp || b.date || b.createdAt || 0)
        return dateA - dateB
      })

      setData(sortedData)
      if (sortedData.length > 0) {
        setCurrentIndex(0)
        setCurrentRecord(sortedData[0])
        const optData = extractOptionChainData(sortedData[0])
        setOptionData(optData)
        const underlying = sortedData[0]?.records?.underlyingValue || sortedData[0]?.underlyingValue || null
        setCurrentOI(computeOI(optData, underlying))
      } else {
        setCurrentRecord(null)
        setOptionData([])
        setCurrentOI({ totalCallOI: 0, totalPutOI: 0 })
      }
    } catch (error) {
      console.error('Error fetching data:', error)
      alert('Error fetching data: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  const updateTradeMTM = (record, optData, tradeState) => {
    if (!tradeState || tradeState.status === 'closed') return tradeState
    if (!tradeState.entryPrice || tradeState.entryPrice <= 0) {
      // Prevent invalid MTM on zero entry
      return {
        ...tradeState,
        currentPrice: null,
        currentPNL: 0,
        currentPNLPercent: 0
      }
    }
    const strikeData = optData.find((s) => s.strike === tradeState.strike)
    if (!strikeData) return { ...tradeState, currentPrice: null, currentPNL: 0, currentPNLPercent: 0 }

    const price = tradeState.optionType === 'CE' ? strikeData.ceLTP : strikeData.peLTP
    const shares = getLotSize() * tradeState.lotSize
    const pnl = (price - tradeState.entryPrice) * shares
    const pnlPercent = tradeState.entryPrice > 0 ? ((price - tradeState.entryPrice) / tradeState.entryPrice) * 100 : 0

    let status = tradeState.status
    let exitReason = tradeState.exitReason
    let exitPrice = tradeState.exitPrice

    const hitTP =
      tradeState.tpMode === 'rupee'
        ? pnl >= Number(tradeState.tpValue || 0)
        : pnlPercent >= Number(tradeState.tpValue || 0)
    const hitSL =
      tradeState.slMode === 'rupee'
        ? pnl <= -Math.abs(Number(tradeState.slValue || 0))
        : pnlPercent <= -Math.abs(Number(tradeState.slValue || 0))

    if (status === 'open' && hitTP) {
      status = 'closed'
      exitReason = 'TP'
      exitPrice = price
    } else if (status === 'open' && hitSL) {
      status = 'closed'
      exitReason = 'SL'
      exitPrice = price
    }

    return {
      ...tradeState,
      currentPrice: price,
      currentPNL: pnl,
      currentPNLPercent: pnlPercent,
      status,
      exitReason,
      exitPrice
    }
  }

  const handleEnterTrade = () => {
    if (!currentRecord || !optionData.length) {
      alert('Load data first.')
      return
    }
    if (!selectedStrike) {
      alert('Select a strike price.')
      return
    }
    const strikeNum = Number(selectedStrike)
    const strikeData = optionData.find((s) => s.strike === strikeNum)
    if (!strikeData) {
      alert('Strike not found in current record.')
      return
    }

    const entryPrice = optionType === 'CE' ? strikeData.ceLTP : strikeData.peLTP
    if (!entryPrice || entryPrice <= 0) {
      alert('Entry price is 0; cannot take trade on a zero-priced option.')
      return
    }
    const tradeState = {
      id: Date.now().toString(), // Unique ID for the trade
      optionChain: selectedChain,
      optionType,
      strike: strikeNum,
      entryPrice,
      lotSize: 1,
      tpMode,
      tpValue,
      slMode,
      slValue,
      status: 'open',
      entryIndex: currentIndex,
      entryTimestamp: currentRecord?.records?.timestamp || currentRecord?.timestamp || new Date().toISOString(),
      entryUnderlying: currentRecord?.records?.underlyingValue || currentRecord?.underlyingValue || null
    }

    const updated = updateTradeMTM(currentRecord, optionData, tradeState)
    setTrade(updated)
  }

  const handleSaveTrade = () => {
    if (!trade) {
      alert('No trade to save.')
      return
    }
    
    const shares = getLotSize() * trade.lotSize
    const invested = trade.entryPrice * shares
    const finalPNL = trade.status === 'closed' && trade.exitPrice !== undefined && trade.exitPrice !== null
      ? (trade.exitPrice - trade.entryPrice) * shares
      : trade.currentPNL || 0
    const finalPNLPercent = trade.status === 'closed' && trade.exitPrice !== undefined && trade.exitPrice !== null
      ? (trade.entryPrice > 0 ? ((trade.exitPrice - trade.entryPrice) / trade.entryPrice) * 100 : 0)
      : trade.currentPNLPercent || 0

    const tradeToSave = {
      ...trade,
      shares,
      invested,
      finalPNL,
      finalPNLPercent,
      savedAt: new Date().toISOString(),
      currentRecordIndex: currentIndex,
      currentTimestamp: currentRecord?.records?.timestamp || currentRecord?.timestamp || new Date().toISOString(),
      currentUnderlying: currentRecord?.records?.underlyingValue || currentRecord?.underlyingValue || null
    }

    setSavedTrades([...savedTrades, tradeToSave])
    alert('Trade saved successfully!')
  }

  const handleDeleteTrade = (tradeId) => {
    if (window.confirm('Are you sure you want to delete this trade?')) {
      setSavedTrades(savedTrades.filter(t => t.id !== tradeId))
    }
  }

  const handleClearAllTrades = () => {
    if (window.confirm('Are you sure you want to clear all saved trades?')) {
      setSavedTrades([])
      localStorage.removeItem('algoManualTrades')
    }
  }

  // Calculate total PNL from all saved trades
  const calculateTotalPNL = () => {
    return savedTrades.reduce((sum, t) => {
      const pnl = t.finalPNL !== undefined ? t.finalPNL : (t.currentPNL || 0)
      return sum + pnl
    }, 0)
  }

  // Calculate total invested from all saved trades
  const calculateTotalInvested = () => {
    return savedTrades.reduce((sum, t) => {
      const invested = t.invested !== undefined ? t.invested : (t.entryPrice * getLotSize() * (t.lotSize || 1))
      return sum + invested
    }, 0)
  }

  const handleNext = () => {
    if (currentIndex >= data.length - 1) return
    const newIndex = currentIndex + 1
    const record = data[newIndex]
    const optData = extractOptionChainData(record)
    const underlying = record?.records?.underlyingValue || record?.underlyingValue || null
    setCurrentIndex(newIndex)
    setCurrentRecord(record)
    setOptionData(optData)
    setCurrentOI(computeOI(optData, underlying))
    if (trade) {
      setTrade(updateTradeMTM(record, optData, trade))
    }
  }

  const handlePrev = () => {
    if (currentIndex <= 0) return
    const newIndex = currentIndex - 1
    const record = data[newIndex]
    const optData = extractOptionChainData(record)
    const underlying = record?.records?.underlyingValue || record?.underlyingValue || null
    setCurrentIndex(newIndex)
    setCurrentRecord(record)
    setOptionData(optData)
    setCurrentOI(computeOI(optData, underlying))
    if (trade) {
      setTrade(updateTradeMTM(record, optData, trade))
    }
  }

  const formatNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-'
    return num.toLocaleString('en-IN', { maximumFractionDigits: 2 })
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('en-IN')
    } catch {
      return dateStr
    }
  }

  return (
    <div className="algo-manual-container">
      <div className="card">
        <div className="card-header">
          <h2>Algo Manual</h2>
          <button onClick={fetchData} className="btn-icon" disabled={loading}>
            <RefreshCw size={20} className={loading ? 'spinning' : ''} />
          </button>
        </div>

        <div className="algo-manual-controls">
          <div className="control-group">
            <label>Option Chain:</label>
            <select value={selectedChain} onChange={(e) => setSelectedChain(e.target.value)} className="form-select">
              {optionChains.map((chain) => (
                <option key={chain.value} value={chain.value}>
                  {chain.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Date:</label>
            <select value={dateType} onChange={(e) => setDateType(e.target.value)} className="form-select">
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="range">Date Range</option>
            </select>
          </div>

          {dateType === 'range' && (
            <>
              <div className="control-group">
                <label>Start Date:</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="control-group">
                <label>End Date:</label>
                <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="form-input" />
              </div>
            </>
          )}

          <button onClick={fetchData} className="btn btn-primary" disabled={loading}>
            {loading ? 'Loading...' : 'Fetch Data'}
          </button>
        </div>

        {loading && (
          <div className="loading-container">
            <p>Loading data...</p>
          </div>
        )}

        {!loading && currentRecord && (
          <>
            <div className="card" style={{ marginTop: '20px' }}>
              <div className="card-header">
                <div>
                  <h3>
                    Record {currentIndex + 1} of {data.length}
                  </h3>
                  {currentRecord && (
                    <div className="record-timestamp">
                      <strong>Time:</strong> {formatDate(
                        currentRecord?.records?.timestamp ||
                        currentRecord?.timestamp ||
                        currentRecord?.insertedAt ||
                        currentRecord?.date ||
                        currentRecord?.createdAt ||
                        '-'
                      )}
                    </div>
                  )}
                </div>
                <div className="navigation-buttons">
                  <button onClick={handlePrev} className="btn btn-secondary" disabled={currentIndex === 0}>
                    <ChevronLeft size={16} /> Prev
                  </button>
                  <button onClick={handleNext} className="btn btn-secondary" disabled={currentIndex === data.length - 1}>
                    Next <ChevronRight size={16} />
                  </button>
                </div>
              </div>

              <div className="oi-summary">
                <div className="summary-item">
                  <label>Underlying Value:</label>
                  <span className="value">
                    ₹{formatNumber(
                      currentRecord?.records?.underlyingValue ||
                      currentRecord?.underlyingValue ||
                      currentRecord?.underlying_price ||
                      currentRecord?.underlying ||
                      currentRecord?.spot ||
                      0
                    )}
                  </span>
                </div>
                <div className="summary-item">
                  <label>Total Call OI:</label>
                  <span className="value">{formatNumber(currentOI.totalCallOI)}</span>
                  <div className="oi-note">(ATM + 1 Up + 1 Down)</div>
                </div>
                <div className="summary-item">
                  <label>Total Put OI:</label>
                  <span className="value">{formatNumber(currentOI.totalPutOI)}</span>
                  <div className="oi-note">(ATM + 1 Up + 1 Down)</div>
                </div>
                <div className="summary-item">
                  <label>Lot Size:</label>
                  <span className="value">{getLotSize()} shares/lot</span>
                </div>
              </div>

              <div className="trade-panel">
                <h4>Manual Trade</h4>
                <div className="trade-form">
                  <div className="control-group">
                    <label>Option Type</label>
                    <select value={optionType} onChange={(e) => setOptionType(e.target.value)} className="form-select">
                      <option value="CE">Call (CE)</option>
                      <option value="PE">Put (PE)</option>
                    </select>
                  </div>

                  <div className="control-group">
                    <label>Strike</label>
                    <select
                      value={selectedStrike}
                      onChange={(e) => setSelectedStrike(e.target.value)}
                      className="form-select"
                    >
                      <option value="">Select strike</option>
                      {optionData
                        .slice()
                        .sort((a, b) => a.strike - b.strike)
                        .map((s) => {
                          const price = optionType === 'CE' ? s.ceLTP : s.peLTP
                          return (
                            <option key={s.strike} value={s.strike}>
                              {s.strike} - ₹{formatNumber(price)}
                            </option>
                          )
                        })}
                    </select>
                    {selectedStrike && (
                      <div className="strike-price-display">
                        <div>
                          <strong>Current Price:</strong> ₹{(() => {
                            const strikeNum = Number(selectedStrike)
                            const strikeData = optionData.find((s) => s.strike === strikeNum)
                            if (!strikeData) return '0'
                            const price = optionType === 'CE' ? strikeData.ceLTP : strikeData.peLTP
                            return formatNumber(price || 0)
                          })()}
                        </div>
                        <div style={{ marginTop: '5px', fontSize: '11px', color: '#666' }}>
                          <strong>Market (Underlying):</strong> ₹{formatNumber(
                            currentRecord?.records?.underlyingValue ||
                            currentRecord?.underlyingValue ||
                            currentRecord?.underlying_price ||
                            currentRecord?.underlying ||
                            currentRecord?.spot ||
                            0
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="control-group">
                    <label>Take Profit</label>
                    <div className="inline-inputs">
                      <input
                        type="number"
                        value={tpValue}
                        onChange={(e) => setTpValue(e.target.value)}
                        className="form-input"
                        placeholder="Value"
                      />
                      <select value={tpMode} onChange={(e) => setTpMode(e.target.value)} className="form-select">
                        <option value="rupee">₹</option>
                        <option value="percent">%</option>
                      </select>
                    </div>
                  </div>

                  <div className="control-group">
                    <label>Stop Loss</label>
                    <div className="inline-inputs">
                      <input
                        type="number"
                        value={slValue}
                        onChange={(e) => setSlValue(e.target.value)}
                        className="form-input"
                        placeholder="Value"
                      />
                      <select value={slMode} onChange={(e) => setSlMode(e.target.value)} className="form-select">
                        <option value="rupee">₹</option>
                        <option value="percent">%</option>
                      </select>
                    </div>
                  </div>

                  <div className="control-group">
                    <label>&nbsp;</label>
                    <button className="btn btn-primary" onClick={handleEnterTrade} disabled={!optionData.length}>
                      Enter Trade (1 lot)
                    </button>
                  </div>
                </div>

                {trade && (() => {
                  const shares = getLotSize() * trade.lotSize
                  const invested = trade.entryPrice > 0 ? trade.entryPrice * shares : 0
                  const finalPNL = invested > 0
                    ? (trade.status === 'closed' && trade.exitPrice !== undefined && trade.exitPrice !== null
                        ? (trade.exitPrice - trade.entryPrice) * shares
                        : trade.currentPNL || 0)
                    : 0
                  const finalPNLPercent = invested > 0
                    ? (trade.status === 'closed' && trade.exitPrice !== undefined && trade.exitPrice !== null
                        ? ((trade.exitPrice - trade.entryPrice) / trade.entryPrice) * 100
                        : trade.currentPNLPercent || 0)
                    : 0
                  
                  return (
                    <div className="trade-status">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <h5>Trade Status</h5>
                        <button onClick={handleSaveTrade} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', padding: '6px 12px' }}>
                          <Save size={14} />
                          Save Trade
                        </button>
                      </div>
                      <div className="status-grid">
                        <div>
                          <label>Strike / Type</label>
                          <div className="value">
                            {trade.strike} ({trade.optionType})
                          </div>
                        </div>
                        <div>
                          <label>Entry Price</label>
                          <div className="value">₹{formatNumber(trade.entryPrice)}</div>
                        </div>
                        <div>
                          <label>Current Price</label>
                          <div className="value">
                            {trade.currentPrice !== null && trade.currentPrice !== undefined
                              ? `₹${formatNumber(trade.currentPrice)}`
                              : '-'}
                          </div>
                        </div>
                        <div>
                          <label>Shares</label>
                          <div className="value">{formatNumber(shares)}</div>
                        </div>
                        <div>
                          <label>Invested</label>
                          <div className="value">₹{formatNumber(invested)}</div>
                        </div>
                        <div>
                          <label>PNL</label>
                          <div className={finalPNL >= 0 ? 'value profit' : 'value loss'}>
                            ₹{formatNumber(finalPNL)}{' '}
                            {finalPNL >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                          </div>
                        </div>
                        <div>
                          <label>Return %</label>
                          <div className={finalPNLPercent >= 0 ? 'value profit' : 'value loss'}>
                            {formatNumber(finalPNLPercent)}%
                          </div>
                        </div>
                        <div>
                          <label>Status</label>
                          <div className="value">
                            {trade.status === 'open'
                              ? 'OPEN'
                              : trade.exitReason
                              ? `CLOSED (${trade.exitReason})`
                              : 'CLOSED'}
                          </div>
                        </div>
                        {trade.exitPrice !== undefined && trade.exitPrice !== null && trade.status === 'closed' && (
                          <div>
                            <label>Exit Price</label>
                            <div className="value">₹{formatNumber(trade.exitPrice)}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })()}
              </div>
            </div>
          </>
        )}

        {!loading && data.length === 0 && (
          <div className="no-data">
            <p>No data available. Please select an option chain and date, then click "Fetch Data".</p>
          </div>
        )}
      </div>

      {/* Saved Trades Section */}
      {savedTrades.length > 0 && (
        <div className="card" style={{ marginTop: '20px' }}>
          <div className="card-header">
            <h2>Saved Trades ({savedTrades.length})</h2>
            <button onClick={handleClearAllTrades} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Trash2 size={16} />
              Clear All
            </button>
          </div>

          {/* Total PNL Summary */}
          <div className="total-pnl-summary">
            <div className="summary-card">
              <label>Total Invested:</label>
              <span className="value">₹{formatNumber(calculateTotalInvested())}</span>
            </div>
            <div className="summary-card">
              <label>Total PNL:</label>
              <span className={`value ${calculateTotalPNL() >= 0 ? 'profit' : 'loss'}`}>
                ₹{formatNumber(calculateTotalPNL())}
                {calculateTotalPNL() >= 0 ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
              </span>
            </div>
            <div className="summary-card">
              <label>Total Return %:</label>
              <span className={`value ${calculateTotalInvested() > 0 ? (calculateTotalPNL() / calculateTotalInvested() * 100 >= 0 ? 'profit' : 'loss') : ''}`}>
                {calculateTotalInvested() > 0 
                  ? `${formatNumber((calculateTotalPNL() / calculateTotalInvested()) * 100)}%`
                  : '0%'}
              </span>
            </div>
          </div>

          {/* Saved Trades Table */}
          <div className="trades-table-container">
            <table className="trades-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Chain</th>
                  <th>Strike/Type</th>
                  <th>Entry</th>
                  <th>Exit</th>
                  <th>Shares</th>
                  <th>Invested</th>
                  <th>PNL</th>
                  <th>Return %</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {savedTrades.map((savedTrade) => {
                  const shares = savedTrade.shares || (getLotSize() * (savedTrade.lotSize || 1))
                  const invested = savedTrade.invested || (savedTrade.entryPrice * shares)
                  const pnl = savedTrade.finalPNL !== undefined ? savedTrade.finalPNL : (savedTrade.currentPNL || 0)
                  const returnPercent = savedTrade.finalPNLPercent !== undefined 
                    ? savedTrade.finalPNLPercent 
                    : (invested > 0 ? (pnl / invested) * 100 : 0)
                  
                  return (
                    <tr key={savedTrade.id}>
                      <td>{formatDate(savedTrade.entryTimestamp)}</td>
                      <td>{savedTrade.optionChain || selectedChain}</td>
                      <td>
                        {savedTrade.strike} ({savedTrade.optionType})
                      </td>
                      <td>₹{formatNumber(savedTrade.entryPrice)}</td>
                      <td>
                        {savedTrade.exitPrice !== undefined && savedTrade.exitPrice !== null
                          ? `₹${formatNumber(savedTrade.exitPrice)}`
                          : savedTrade.currentPrice !== undefined && savedTrade.currentPrice !== null
                          ? `₹${formatNumber(savedTrade.currentPrice)}`
                          : '-'}
                      </td>
                      <td>{formatNumber(shares)}</td>
                      <td>₹{formatNumber(invested)}</td>
                      <td className={pnl >= 0 ? 'profit' : 'loss'}>
                        ₹{formatNumber(pnl)}
                        {pnl >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                      </td>
                      <td className={returnPercent >= 0 ? 'profit' : 'loss'}>
                        {formatNumber(returnPercent)}%
                      </td>
                      <td>
                        <span className={`status-badge ${savedTrade.status === 'open' ? 'open' : 'closed'}`}>
                          {savedTrade.status === 'open'
                            ? 'OPEN'
                            : savedTrade.exitReason
                            ? `CLOSED (${savedTrade.exitReason})`
                            : 'CLOSED'}
                        </span>
                      </td>
                      <td>
                        <button
                          onClick={() => handleDeleteTrade(savedTrade.id)}
                          className="btn-icon-small"
                          title="Delete trade"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <style>{`
        .algo-manual-container {
          padding: 20px;
        }
        .algo-manual-controls {
          display: flex;
          flex-wrap: wrap;
          gap: 15px;
          align-items: flex-end;
          margin-bottom: 20px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .control-group {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .control-group label {
          font-size: 12px;
          font-weight: 600;
          color: #333;
        }
        .form-select, .form-input {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          min-width: 150px;
        }
        .inline-inputs {
          display: flex;
          gap: 8px;
          align-items: center;
        }
        .navigation-buttons {
          display: flex;
          gap: 10px;
        }
        .oi-summary {
          display: flex;
          gap: 30px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
          margin-bottom: 20px;
        }
        .summary-item {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .summary-item label {
          font-size: 12px;
          color: #666;
          font-weight: 600;
        }
        .summary-item .value {
          font-size: 16px;
          font-weight: bold;
          color: #333;
        }
        .oi-note {
          font-size: 10px;
          color: #666;
          font-weight: normal;
          margin-top: 2px;
        }
        .record-timestamp {
          font-size: 12px;
          color: #666;
          margin-top: 5px;
        }
        .record-timestamp strong {
          color: #333;
          margin-right: 5px;
        }
        .trade-panel {
          margin-top: 20px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .trade-form {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
          align-items: end;
        }
        .trade-status {
          margin-top: 15px;
          padding: 12px;
          background: #fff;
          border: 1px solid #e1e1e1;
          border-radius: 6px;
        }
        .trade-status h5 {
          margin-bottom: 10px;
          font-size: 14px;
          color: #333;
        }
        .status-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 10px;
        }
        .status-grid label {
          font-size: 11px;
          color: #666;
          font-weight: 600;
        }
        .status-grid .value {
          font-size: 14px;
          font-weight: 600;
          color: #333;
        }
        .strike-price-display {
          margin-top: 5px;
          padding: 8px 12px;
          background: #e3f2fd;
          border-radius: 4px;
          font-size: 12px;
          color: #1976d2;
        }
        .strike-price-display strong {
          color: #333;
          margin-right: 5px;
        }
        .profit {
          color: #28a745 !important;
          font-weight: bold;
          display: inline-flex;
          align-items: center;
          gap: 5px;
        }
        .loss {
          color: #dc3545 !important;
          font-weight: bold;
          display: inline-flex;
          align-items: center;
          gap: 5px;
        }
        .no-data, .loading-container {
          padding: 20px;
          text-align: center;
          color: #666;
        }
        .spinning {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .total-pnl-summary {
          display: flex;
          gap: 20px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }
        .summary-card {
          display: flex;
          flex-direction: column;
          gap: 5px;
          flex: 1;
          min-width: 150px;
        }
        .summary-card label {
          font-size: 12px;
          color: #666;
          font-weight: 600;
        }
        .summary-card .value {
          font-size: 20px;
          font-weight: bold;
          color: #333;
          display: flex;
          align-items: center;
          gap: 5px;
        }
        .trades-table-container {
          overflow-x: auto;
          margin-top: 15px;
        }
        .trades-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }
        .trades-table th {
          background: #333;
          color: #fff;
          padding: 10px;
          text-align: left;
          font-weight: 600;
          position: sticky;
          top: 0;
        }
        .trades-table td {
          padding: 8px 10px;
          border: 1px solid #ddd;
        }
        .trades-table tbody tr:nth-child(even) {
          background: #f8f9fa;
        }
        .trades-table tbody tr:hover {
          background: #e9ecef;
        }
        .status-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
        }
        .status-badge.open {
          background: #d4edda;
          color: #155724;
        }
        .status-badge.closed {
          background: #f8d7da;
          color: #721c24;
        }
        .btn-icon-small {
          background: transparent;
          border: none;
          color: #dc3545;
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .btn-icon-small:hover {
          background: #f8d7da;
        }
      `}</style>
    </div>
  )
}

export default AlgoManual

