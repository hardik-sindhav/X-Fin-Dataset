import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronLeft, ChevronRight, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react'
import { API_BASE } from '../config'

const AlgoTest = () => {
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

  const [selectedChain, setSelectedChain] = useState('nifty')
  const [dateType, setDateType] = useState('today') // 'today', 'yesterday', 'range'
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState([])
  const [groupedData, setGroupedData] = useState([])
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0)
  const [currentGroup, setCurrentGroup] = useState(null)
  const [trades, setTrades] = useState([])

  // Get date based on dateType
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

  // Fetch data
  const fetchData = async () => {
    setLoading(true)
    try {
      const dateValue = getDateForType()
      let url = `${API_BASE}/${selectedChain}/data`

      if (dateType === 'range') {
        if (!dateValue.startDate || !dateValue.endDate) {
          alert('Please select both start and end dates')
          setLoading(false)
          return
        }
        url += `?start_date=${dateValue.startDate}&end_date=${dateValue.endDate}&limit=1000`
      } else {
        // For today/yesterday, use the same date as both start and end
        url += `?start_date=${dateValue}&end_date=${dateValue}&limit=1000`
      }

      const response = await axios.get(url)
      const fetchedData = response.data.data || response.data || []

      // Sort by timestamp/date if available
      const sortedData = fetchedData.sort((a, b) => {
        const dateA = new Date(a.timestamp || a.date || a.createdAt || 0)
        const dateB = new Date(b.timestamp || b.date || b.createdAt || 0)
        return dateA - dateB
      })

      setData(sortedData)
      
      // Group by 10 records
      const groups = []
      for (let i = 0; i < sortedData.length; i += 10) {
        groups.push(sortedData.slice(i, i + 10))
      }
      setGroupedData(groups)
      setCurrentGroupIndex(0)
      
      if (groups.length > 0) {
        processGroup(groups[0], 0)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
      alert('Error fetching data: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  // Extract option chain data from record
  const extractOptionChainData = (record) => {
    // Handle different data structures
    const optionData = record.data || record.optionChain || record.option_chain || record
    
    if (!optionData || !Array.isArray(optionData)) {
      return []
    }

    return optionData.map(item => {
      const strike = item.strikePrice || item.strike || item.strike_price
      const ce = item.CE || item.ce || {}
      const pe = item.PE || item.pe || {}
      
      return {
        strike: parseFloat(strike) || 0,
        ceOI: parseFloat(ce.openInterest || ce.open_interest || ce.oi || ce.OpenInterest || 0) || 0,
        peOI: parseFloat(pe.openInterest || pe.open_interest || pe.oi || pe.OpenInterest || 0) || 0,
        ceLTP: parseFloat(ce.lastPrice || ce.last_price || ce.ltp || ce.LastPrice || 0) || 0,
        peLTP: parseFloat(pe.lastPrice || pe.last_price || pe.ltp || pe.LastPrice || 0) || 0,
        ceIV: parseFloat(ce.impliedVolatility || ce.implied_volatility || ce.iv || ce.ImpliedVolatility || 0) || 0,
        peIV: parseFloat(pe.impliedVolatility || pe.implied_volatility || pe.iv || pe.ImpliedVolatility || 0) || 0
      }
    }).filter(item => item.strike > 0)
  }

  // Find current/ATM strike price
  const findATMStrike = (optionData, underlyingPrice) => {
    if (!optionData || optionData.length === 0) return null
    
    // If we have underlying price, find closest strike
    if (underlyingPrice) {
      return optionData.reduce((prev, curr) => {
        return Math.abs(curr.strike - underlyingPrice) < Math.abs(prev.strike - underlyingPrice) ? curr : prev
      })
    }
    
    // Otherwise, find strike with highest OI (usually ATM)
    return optionData.reduce((prev, curr) => {
      const prevTotalOI = prev.ceOI + prev.peOI
      const currTotalOI = curr.ceOI + curr.peOI
      return currTotalOI > prevTotalOI ? curr : prev
    })
  }

  // Process a group of 10 records
  const processGroup = (group, groupIndex) => {
    if (group.length < 4) {
      setCurrentGroup(null)
      setTrades([])
      return
    }

    // First 4 records: Calculate OI for 5 strikes (current + 2 up + 2 down)
    const first4Records = group.slice(0, 4)
    const allStrikes = []
    
    first4Records.forEach(record => {
      const optionData = extractOptionChainData(record)
      if (optionData.length > 0) {
        // Get underlying price if available
        const underlyingPrice = record.underlyingPrice || record.underlying_price || 
                               record.underlying || record.spot || null
        
        // Find ATM strike
        const atmStrike = findATMStrike(optionData, underlyingPrice)
        if (!atmStrike) return

        // Get strikes: 2 down, ATM, 2 up
        const sortedStrikes = [...optionData].sort((a, b) => a.strike - b.strike)
        const atmIndex = sortedStrikes.findIndex(s => s.strike === atmStrike.strike)
        
        if (atmIndex >= 0) {
          const strikes = []
          // 2 down
          if (atmIndex >= 2) strikes.push(sortedStrikes[atmIndex - 2])
          if (atmIndex >= 1) strikes.push(sortedStrikes[atmIndex - 1])
          // ATM
          strikes.push(sortedStrikes[atmIndex])
          // 2 up
          if (atmIndex + 1 < sortedStrikes.length) strikes.push(sortedStrikes[atmIndex + 1])
          if (atmIndex + 2 < sortedStrikes.length) strikes.push(sortedStrikes[atmIndex + 2])

          allStrikes.push(...strikes)
        }
      }
    })

    // Calculate total Call OI and Put OI
    const totalCallOI = allStrikes.reduce((sum, s) => sum + s.ceOI, 0)
    const totalPutOI = allStrikes.reduce((sum, s) => sum + s.peOI, 0)

    setCurrentGroup({
      groupIndex,
      first4Records,
      allStrikes,
      totalCallOI,
      totalPutOI,
      shouldTrade: totalCallOI > totalPutOI
    })

    // If Call OI > Put OI, calculate trades for next 6 records
    if (totalCallOI > totalPutOI && group.length >= 10) {
      const next6Records = group.slice(4, 10)
      calculateTrades(next6Records, first4Records[first4Records.length - 1])
    } else {
      setTrades([])
    }
  }

  // Calculate trades (ATM, OTM, ITM) and PNL
  const calculateTrades = (records, baseRecord) => {
    const baseOptionData = extractOptionChainData(baseRecord)
    if (baseOptionData.length === 0) {
      setTrades([])
      return
    }

    // Get underlying price from base record
    const underlyingPrice = baseRecord.underlyingPrice || baseRecord.underlying_price || 
                           baseRecord.underlying || baseRecord.spot || null

    // Find ATM strike
    const atmStrikeData = findATMStrike(baseOptionData, underlyingPrice)
    if (!atmStrikeData) {
      setTrades([])
      return
    }

    const sortedStrikes = [...baseOptionData].sort((a, b) => a.strike - b.strike)
    const atmIndex = sortedStrikes.findIndex(s => s.strike === atmStrikeData.strike)
    
    // Get ITM (one strike below ATM) and OTM (one strike above ATM)
    const itmStrike = atmIndex > 0 ? sortedStrikes[atmIndex - 1] : null
    const otmStrike = atmIndex < sortedStrikes.length - 1 ? sortedStrikes[atmIndex + 1] : null

    const tradePositions = []
    
    // ATM Call position
    if (atmStrikeData) {
      tradePositions.push({
        type: 'ATM',
        strike: atmStrikeData.strike,
        optionType: 'CE',
        entryPrice: atmStrikeData.ceLTP,
        lotSize: 1
      })
    }

    // ITM Call position
    if (itmStrike) {
      tradePositions.push({
        type: 'ITM',
        strike: itmStrike.strike,
        optionType: 'CE',
        entryPrice: itmStrike.ceLTP,
        lotSize: 1
      })
    }

    // OTM Call position
    if (otmStrike) {
      tradePositions.push({
        type: 'OTM',
        strike: otmStrike.strike,
        optionType: 'CE',
        entryPrice: otmStrike.ceLTP,
        lotSize: 1
      })
    }

    // Calculate PNL for each record in next 6
    const tradesWithPNL = records.map((record, recordIndex) => {
      const recordOptionData = extractOptionChainData(record)
      const recordUnderlyingPrice = record.underlyingPrice || record.underlying_price || 
                                   record.underlying || record.spot || null

      const pnlTrades = tradePositions.map(trade => {
        // Find matching strike in current record
        const currentStrikeData = recordOptionData.find(s => s.strike === trade.strike)
        
        if (!currentStrikeData) {
          return {
            ...trade,
            exitPrice: 0,
            pnl: 0,
            pnlPercent: 0
          }
        }

        const exitPrice = currentStrikeData.ceLTP
        // PNL calculation: (Exit Price - Entry Price) * Lot Size * Multiplier
        // For NIFTY/BankNifty: 1 lot = 50 shares, so multiplier is 50
        const pnl = (exitPrice - trade.entryPrice) * trade.lotSize * 50
        const pnlPercent = trade.entryPrice > 0 ? ((exitPrice - trade.entryPrice) / trade.entryPrice) * 100 : 0

        return {
          ...trade,
          exitPrice,
          pnl,
          pnlPercent,
          timestamp: record.timestamp || record.date || record.createdAt
        }
      })

      return {
        recordIndex: recordIndex + 4, // Offset by 4 (first 4 records)
        timestamp: record.timestamp || record.date || record.createdAt,
        underlyingPrice: recordUnderlyingPrice,
        trades: pnlTrades,
        totalPNL: pnlTrades.reduce((sum, t) => sum + t.pnl, 0)
      }
    })

    setTrades(tradesWithPNL)
  }

  // Handle next group
  const handleNext = () => {
    if (currentGroupIndex < groupedData.length - 1) {
      const newIndex = currentGroupIndex + 1
      setCurrentGroupIndex(newIndex)
      processGroup(groupedData[newIndex], newIndex)
    }
  }

  // Handle previous group
  const handlePrev = () => {
    if (currentGroupIndex > 0) {
      const newIndex = currentGroupIndex - 1
      setCurrentGroupIndex(newIndex)
      processGroup(groupedData[newIndex], newIndex)
    }
  }

  // Format number
  const formatNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-'
    return num.toLocaleString('en-IN', { maximumFractionDigits: 2 })
  }

  // Format date
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
    <div className="algo-test-container">
      <div className="card">
        <div className="card-header">
          <h2>Algo Test</h2>
          <button onClick={fetchData} className="btn-icon" disabled={loading}>
            <RefreshCw size={20} className={loading ? 'spinning' : ''} />
          </button>
        </div>

        <div className="algo-test-controls">
          <div className="control-group">
            <label>Option Chain:</label>
            <select 
              value={selectedChain} 
              onChange={(e) => setSelectedChain(e.target.value)}
              className="form-select"
            >
              {optionChains.map(chain => (
                <option key={chain.value} value={chain.value}>{chain.label}</option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Date:</label>
            <select 
              value={dateType} 
              onChange={(e) => setDateType(e.target.value)}
              className="form-select"
            >
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
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="form-input"
                />
              </div>
            </>
          )}

          <button 
            onClick={fetchData} 
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Fetch Data'}
          </button>
        </div>

        {loading && (
          <div className="loading-container">
            <p>Loading data...</p>
          </div>
        )}

        {!loading && currentGroup && (
          <>
            <div className="card" style={{ marginTop: '20px' }}>
              <div className="card-header">
                <h3>Group {currentGroupIndex + 1} of {groupedData.length}</h3>
                <div className="navigation-buttons">
                  <button 
                    onClick={handlePrev} 
                    className="btn btn-secondary"
                    disabled={currentGroupIndex === 0}
                  >
                    <ChevronLeft size={16} /> Prev
                  </button>
                  <button 
                    onClick={handleNext} 
                    className="btn btn-secondary"
                    disabled={currentGroupIndex === groupedData.length - 1}
                  >
                    Next <ChevronRight size={16} />
                  </button>
                </div>
              </div>

              <div className="oi-summary">
                <div className="summary-item">
                  <label>Total Call OI:</label>
                  <span className="value">{formatNumber(currentGroup.totalCallOI)}</span>
                </div>
                <div className="summary-item">
                  <label>Total Put OI:</label>
                  <span className="value">{formatNumber(currentGroup.totalPutOI)}</span>
                </div>
                <div className="summary-item">
                  <label>Decision:</label>
                  <span className={`value ${currentGroup.shouldTrade ? 'trade-yes' : 'trade-no'}`}>
                    {currentGroup.shouldTrade ? 'TRADE (Call OI > Put OI)' : 'NO TRADE (Call OI ≤ Put OI)'}
                  </span>
                </div>
              </div>

              {currentGroup.shouldTrade && trades.length > 0 && (
                <div className="trades-section">
                  <h4>Trades (1 Lot Each)</h4>
                  <div className="trades-table-container">
                    <table className="trades-table">
                      <thead>
                        <tr>
                          <th>Record</th>
                          <th>Timestamp</th>
                          <th>Type</th>
                          <th>Strike</th>
                          <th>Entry Price</th>
                          <th>Exit Price</th>
                          <th>PNL</th>
                          <th>PNL %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trades.map((tradeGroup, idx) => (
                          <React.Fragment key={idx}>
                            {tradeGroup.trades.map((trade, tradeIdx) => (
                              <tr key={tradeIdx}>
                                {tradeIdx === 0 && (
                                  <td rowSpan={tradeGroup.trades.length} style={{ verticalAlign: 'top' }}>
                                    {tradeGroup.recordIndex + 1}
                                  </td>
                                )}
                                {tradeIdx === 0 && (
                                  <td rowSpan={tradeGroup.trades.length} style={{ verticalAlign: 'top' }}>
                                    {formatDate(tradeGroup.timestamp)}
                                  </td>
                                )}
                                <td>
                                  <span className={`trade-type ${trade.type.toLowerCase()}`}>
                                    {trade.type}
                                  </span>
                                </td>
                                <td>{formatNumber(trade.strike)}</td>
                                <td>{formatNumber(trade.entryPrice)}</td>
                                <td>{formatNumber(trade.exitPrice)}</td>
                                <td className={trade.pnl >= 0 ? 'profit' : 'loss'}>
                                  {formatNumber(trade.pnl)}
                                  {trade.pnl >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                </td>
                                <td className={trade.pnlPercent >= 0 ? 'profit' : 'loss'}>
                                  {formatNumber(trade.pnlPercent)}%
                                </td>
                              </tr>
                            ))}
                            <tr className="total-row">
                              <td colSpan="6" style={{ textAlign: 'right', fontWeight: 'bold' }}>
                                Total PNL:
                              </td>
                              <td className={tradeGroup.totalPNL >= 0 ? 'profit' : 'loss'} colSpan="2">
                                {formatNumber(tradeGroup.totalPNL)}
                              </td>
                            </tr>
                          </React.Fragment>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {currentGroup.shouldTrade && trades.length === 0 && (
                <div className="no-trades">
                  <p>Not enough records to calculate trades. Need at least 10 records in this group.</p>
                </div>
              )}
            </div>
          </>
        )}

        {!loading && groupedData.length === 0 && data.length === 0 && (
          <div className="no-data">
            <p>No data available. Please select an option chain and date, then click "Fetch Data".</p>
          </div>
        )}
      </div>

      <style>{`
        .algo-test-container {
          padding: 20px;
        }

        .algo-test-controls {
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

        .summary-item .value.trade-yes {
          color: #28a745;
        }

        .summary-item .value.trade-no {
          color: #dc3545;
        }

        .trades-section {
          margin-top: 20px;
        }

        .trades-section h4 {
          margin-bottom: 15px;
          color: #333;
        }

        .trades-table-container {
          overflow-x: auto;
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
        }

        .trades-table td {
          padding: 8px 10px;
          border: 1px solid #ddd;
        }

        .trades-table tbody tr:nth-child(even) {
          background: #f8f9fa;
        }

        .trade-type {
          padding: 4px 8px;
          border-radius: 4px;
          font-weight: 600;
          font-size: 11px;
        }

        .trade-type.atm {
          background: #ffc107;
          color: #000;
        }

        .trade-type.itm {
          background: #17a2b8;
          color: #fff;
        }

        .trade-type.otm {
          background: #6c757d;
          color: #fff;
        }

        .profit {
          color: #28a745;
          font-weight: bold;
          display: flex;
          align-items: center;
          gap: 5px;
        }

        .loss {
          color: #dc3545;
          font-weight: bold;
          display: flex;
          align-items: center;
          gap: 5px;
        }

        .total-row {
          background: #e9ecef !important;
          font-weight: bold;
        }

        .no-trades, .no-data {
          padding: 20px;
          text-align: center;
          color: #666;
        }

        .loading-container {
          padding: 40px;
          text-align: center;
        }

        .spinning {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export default AlgoTest

