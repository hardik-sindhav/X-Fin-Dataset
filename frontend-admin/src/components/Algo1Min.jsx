import React, { useState } from 'react'
import axios from 'axios'
import { Calendar, Play, TrendingDown, TrendingUp, RefreshCw, Download } from 'lucide-react'
import { API_BASE } from '../config'

const Algo1Min = () => {
  // Symbol mapping
  const symbolMapping = {
    'banknifty': '^NSEBANK',
    'nifty': '^NSEI',
    'finnifty': '^NSEI',
    'midcpnifty': '^NSEI',
    'hdfcbank': 'HDFCBANK.NS',
    'icicibank': 'ICICIBANK.NS',
    'sbin': 'SBIN.NS',
    'kotakbank': 'KOTAKBANK.NS',
    'axisbank': 'AXISBANK.NS',
    'bankbaroda': 'BANKBARODA.NS',
    'pnb': 'PNB.NS',
    'canbk': 'CANBK.NS',
    'aubank': 'AUBANK.NS',
    'indusindbk': 'INDUSINDBK.NS',
    'idfcfirstb': 'IDFCFIRSTB.NS',
    'federalbnk': 'FEDERALBNK.NS'
  }

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

  const [selectedChain, setSelectedChain] = useState('banknifty')
  const [selectedDate, setSelectedDate] = useState('')
  const [tpPoints, setTpPoints] = useState(10)
  const [slPoints, setSlPoints] = useState(5)
  const [loading, setLoading] = useState(false)
  const [backtestResults, setBacktestResults] = useState(null)
  const [error, setError] = useState(null)

  // Set today's date as default
  React.useEffect(() => {
    const today = new Date().toISOString().split('T')[0]
    setSelectedDate(today)
  }, [])

  // Calculate EMA
  const calculateEMA = (data, period) => {
    if (data.length < period) return null
    
    const multiplier = 2 / (period + 1)
    let ema = data.slice(0, period).reduce((sum, d) => sum + d.close, 0) / period
    
    const emaValues = [ema]
    for (let i = period; i < data.length; i++) {
      ema = (data[i].close - ema) * multiplier + ema
      emaValues.push(ema)
    }
    
    return emaValues
  }

  const runBacktest = async () => {
    if (!selectedDate) {
      setError('Please select a date')
      return
    }

    setLoading(true)
    setError(null)
    setBacktestResults(null)

    try {
      const yahooSymbol = symbolMapping[selectedChain]
      if (!yahooSymbol) {
        setError(`Symbol mapping not found for ${selectedChain}`)
        setLoading(false)
        return
      }

      // Fetch 1-minute OHLC data
      const url = `${API_BASE}/yahoo-finance/ohlc?symbol=${encodeURIComponent(yahooSymbol)}&date=${selectedDate}&interval=1m`
      const response = await axios.get(url)

      if (!response.data.success || !response.data.data['1min'] || response.data.data['1min'].length === 0) {
        setError('No 1-minute data available for the selected date')
        setLoading(false)
        return
      }

      const candles = response.data.data['1min']
        .map(c => ({
          timestamp: new Date(c.timestamp),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
          volume: c.volume
        }))
        .sort((a, b) => a.timestamp - b.timestamp)

      if (candles.length < 15) {
        setError('Not enough data points (need at least 15 candles for 15 EMA)')
        setLoading(false)
        return
      }

      // Calculate 15 EMA
      const ema15 = calculateEMA(candles, 15)
      if (!ema15 || ema15.length === 0) {
        setError('Could not calculate 15 EMA')
        setLoading(false)
        return
      }

      // Backtest logic
      const trades = []
      let inTrade = false
      let currentTrade = null
      const TP_POINTS = parseFloat(tpPoints) || 10
      const SL_POINTS = parseFloat(slPoints) || 5

      // Start from candle 15 (index 14) since we need 15 candles for EMA
      for (let i = 14; i < candles.length; i++) {
        const candle = candles[i]
        const emaValue = ema15[i - 14] // EMA array starts from index 0

        if (!inTrade) {
          // Check entry condition: close below 15 EMA → PUT trade
          if (candle.close < emaValue) {
            // Enter PUT trade
            inTrade = true
            currentTrade = {
              entryTime: candle.timestamp,
              entryPrice: candle.close,
              type: 'PUT',
              emaAtEntry: emaValue,
              status: 'open',
              exitTime: null,
              exitPrice: null,
              pnl: 0,
              exitReason: null
            }
          }
        } else {
          // In trade - check for TP or SL
          // For PUT: TP when price goes down by 10 points (close <= entry - 10), SL when price goes up by 5 points (close >= entry + 5)
          const priceDiff = currentTrade.entryPrice - candle.close // For PUT: positive when price goes down
          
          if (priceDiff >= TP_POINTS) {
            // Take Profit hit (price went down by 10+ points)
            currentTrade.exitTime = candle.timestamp
            currentTrade.exitPrice = candle.close
            currentTrade.pnl = TP_POINTS // Fixed TP: 10 points profit
            currentTrade.exitReason = 'TP'
            currentTrade.status = 'closed'
            trades.push({ ...currentTrade })
            inTrade = false
            currentTrade = null
          } else if (candle.close >= currentTrade.entryPrice + SL_POINTS) {
            // Stop Loss hit (price went up by 5+ points)
            currentTrade.exitTime = candle.timestamp
            currentTrade.exitPrice = candle.close
            currentTrade.pnl = -SL_POINTS // Fixed SL: 5 points loss
            currentTrade.exitReason = 'SL'
            currentTrade.status = 'closed'
            trades.push({ ...currentTrade })
            inTrade = false
            currentTrade = null
          }
        }
      }

      // If trade is still open at end of day, close it at last candle
      if (inTrade && currentTrade) {
        const lastCandle = candles[candles.length - 1]
        const priceDiff = currentTrade.entryPrice - lastCandle.close // For PUT: positive when price goes down
        currentTrade.exitTime = lastCandle.timestamp
        currentTrade.exitPrice = lastCandle.close
        currentTrade.pnl = priceDiff // Actual PNL based on price movement
        currentTrade.exitReason = 'EOD'
        currentTrade.status = 'closed'
        trades.push({ ...currentTrade })
      }

      // Calculate statistics
      const totalTrades = trades.length
      const winningTrades = trades.filter(t => t.pnl > 0).length
      const losingTrades = trades.filter(t => t.pnl < 0).length
      const totalPNL = trades.reduce((sum, t) => sum + t.pnl, 0)
      const avgPNL = totalTrades > 0 ? totalPNL / totalTrades : 0
      const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0
      const tpTrades = trades.filter(t => t.exitReason === 'TP').length
      const slTrades = trades.filter(t => t.exitReason === 'SL').length
      const eodTrades = trades.filter(t => t.exitReason === 'EOD').length

      setBacktestResults({
        symbol: selectedChain.toUpperCase(),
        date: selectedDate,
        tpPoints: TP_POINTS,
        slPoints: SL_POINTS,
        totalCandles: candles.length,
        trades,
        statistics: {
          totalTrades,
          winningTrades,
          losingTrades,
          totalPNL: Math.round(totalPNL * 100) / 100,
          avgPNL: Math.round(avgPNL * 100) / 100,
          winRate: Math.round(winRate * 100) / 100,
          tpTrades,
          slTrades,
          eodTrades
        }
      })
    } catch (error) {
      console.error('Error running backtest:', error)
      setError('Error running backtest: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  const downloadResults = () => {
    if (!backtestResults) return

    const dataStr = JSON.stringify(backtestResults, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `algo1min_${selectedChain}_${selectedDate}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const formatTime = (date) => {
    if (!date) return 'N/A'
    return new Date(date).toLocaleTimeString('en-IN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false 
    })
  }

  const formatNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-'
    return num.toLocaleString('en-IN', { maximumFractionDigits: 2 })
  }

  return (
    <div className="algo1min-container">
      <div className="card">
        <div className="card-header">
          <h2>1 Min Algo - EMA Strategy</h2>
          <p>Strategy: If candle close &lt; 15 EMA → PUT trade (TP and SL configurable)</p>
        </div>

        <div className="algo-controls">
          <div className="control-group">
            <label>
              <Calendar size={16} style={{ marginRight: '5px' }} />
              Option Chain:
            </label>
            <select
              value={selectedChain}
              onChange={(e) => setSelectedChain(e.target.value)}
              className="form-select"
            >
              {optionChains.map((chain) => (
                <option key={chain.value} value={chain.value}>
                  {chain.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>
              <Calendar size={16} style={{ marginRight: '5px' }} />
              Date:
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="form-input"
            />
          </div>

          <div className="control-group">
            <label>
              <TrendingUp size={16} style={{ marginRight: '5px' }} />
              TP (Points):
            </label>
            <input
              type="number"
              value={tpPoints}
              onChange={(e) => setTpPoints(e.target.value)}
              className="form-input"
              min="1"
              step="0.1"
              style={{ minWidth: '100px' }}
            />
          </div>

          <div className="control-group">
            <label>
              <TrendingDown size={16} style={{ marginRight: '5px' }} />
              SL (Points):
            </label>
            <input
              type="number"
              value={slPoints}
              onChange={(e) => setSlPoints(e.target.value)}
              className="form-input"
              min="1"
              step="0.1"
              style={{ minWidth: '100px' }}
            />
          </div>

            <button
            onClick={runBacktest}
            className="btn btn-primary"
            disabled={loading || !selectedDate || !tpPoints || !slPoints || tpPoints <= 0 || slPoints <= 0}
          >
            {loading ? (
              <>
                <RefreshCw size={16} className="spinning" style={{ marginRight: '5px' }} />
                Running Backtest...
              </>
            ) : (
              <>
                <Play size={16} style={{ marginRight: '5px' }} />
                Run Backtest
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {backtestResults && (
          <div className="backtest-results">
            <div className="results-header">
              <h3>Backtest Results</h3>
              <button onClick={downloadResults} className="btn btn-success">
                <Download size={16} style={{ marginRight: '5px' }} />
                Download JSON
              </button>
            </div>

            {/* Strategy Parameters */}
            <div className="strategy-params">
              <div className="param-item">
                <label>TP Points:</label>
                <span className="param-value">{backtestResults.tpPoints}</span>
              </div>
              <div className="param-item">
                <label>SL Points:</label>
                <span className="param-value">{backtestResults.slPoints}</span>
              </div>
              <div className="param-item">
                <label>Total Candles:</label>
                <span className="param-value">{backtestResults.totalCandles}</span>
              </div>
            </div>

            {/* Statistics */}
            <div className="statistics-grid">
              <div className="stat-card">
                <label>Total Trades</label>
                <span className="stat-value">{backtestResults.statistics.totalTrades}</span>
              </div>
              <div className="stat-card">
                <label>Winning Trades</label>
                <span className="stat-value positive">{backtestResults.statistics.winningTrades}</span>
              </div>
              <div className="stat-card">
                <label>Losing Trades</label>
                <span className="stat-value negative">{backtestResults.statistics.losingTrades}</span>
              </div>
              <div className="stat-card">
                <label>Total PNL</label>
                <span className={`stat-value ${backtestResults.statistics.totalPNL >= 0 ? 'positive' : 'negative'}`}>
                  {formatNumber(backtestResults.statistics.totalPNL)} points
                </span>
              </div>
              <div className="stat-card">
                <label>Average PNL</label>
                <span className={`stat-value ${backtestResults.statistics.avgPNL >= 0 ? 'positive' : 'negative'}`}>
                  {formatNumber(backtestResults.statistics.avgPNL)} points
                </span>
              </div>
              <div className="stat-card">
                <label>Win Rate</label>
                <span className="stat-value">{formatNumber(backtestResults.statistics.winRate)}%</span>
              </div>
              <div className="stat-card">
                <label>TP Hits</label>
                <span className="stat-value positive">{backtestResults.statistics.tpTrades}</span>
              </div>
              <div className="stat-card">
                <label>SL Hits</label>
                <span className="stat-value negative">{backtestResults.statistics.slTrades}</span>
              </div>
            </div>

            {/* Trades Table */}
            <div className="trades-section">
              <h4>All Trades ({backtestResults.trades.length})</h4>
              <div className="table-container">
                <table className="trades-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Entry Time</th>
                      <th>Entry Price</th>
                      <th>EMA</th>
                      <th>Exit Time</th>
                      <th>Exit Price</th>
                      <th>Exit Reason</th>
                      <th>PNL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {backtestResults.trades.map((trade, idx) => (
                      <tr key={idx} className={trade.pnl >= 0 ? 'winning-trade' : 'losing-trade'}>
                        <td>{idx + 1}</td>
                        <td>{formatTime(trade.entryTime)}</td>
                        <td>{formatNumber(trade.entryPrice)}</td>
                        <td>{formatNumber(trade.emaAtEntry)}</td>
                        <td>{formatTime(trade.exitTime)}</td>
                        <td>{formatNumber(trade.exitPrice)}</td>
                        <td>
                          <span className={`exit-badge ${trade.exitReason.toLowerCase()}`}>
                            {trade.exitReason}
                          </span>
                        </td>
                        <td className={trade.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                          {formatNumber(trade.pnl)} pts
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .algo1min-container {
          padding: 20px;
        }
        .card {
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          overflow: hidden;
        }
        .card-header {
          padding: 20px;
          background: #333;
          color: white;
        }
        .card-header h2 {
          margin: 0 0 10px 0;
          font-size: 24px;
        }
        .card-header p {
          margin: 0;
          font-size: 14px;
          opacity: 0.9;
        }
        .algo-controls {
          display: flex;
          flex-wrap: wrap;
          gap: 15px;
          align-items: flex-end;
          padding: 20px;
          background: #f8f9fa;
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
          display: flex;
          align-items: center;
        }
        .form-select, .form-input {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          min-width: 150px;
        }
        .error-message {
          padding: 12px;
          margin: 0 20px 20px 20px;
          background: #f8d7da;
          color: #721c24;
          border-radius: 4px;
        }
        .backtest-results {
          padding: 20px;
        }
        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .results-header h3 {
          margin: 0;
        }
        .strategy-params {
          display: flex;
          gap: 20px;
          padding: 15px;
          background: #e7f3ff;
          border-radius: 8px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }
        .param-item {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .param-item label {
          font-size: 14px;
          font-weight: 600;
          color: #333;
        }
        .param-value {
          font-size: 16px;
          font-weight: bold;
          color: #007bff;
        }
        .statistics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
          margin-bottom: 30px;
        }
        .stat-card {
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
          text-align: center;
        }
        .stat-card label {
          display: block;
          font-size: 12px;
          color: #666;
          margin-bottom: 8px;
          font-weight: 600;
        }
        .stat-value {
          display: block;
          font-size: 20px;
          font-weight: bold;
          color: #333;
        }
        .stat-value.positive {
          color: #28a745;
        }
        .stat-value.negative {
          color: #dc3545;
        }
        .trades-section {
          margin-top: 30px;
        }
        .trades-section h4 {
          margin-bottom: 15px;
        }
        .table-container {
          overflow-x: auto;
          max-height: 500px;
          overflow-y: auto;
        }
        .trades-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }
        .trades-table th {
          background: #333;
          color: white;
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
        .trades-table tbody tr.winning-trade {
          background: #d4edda;
        }
        .trades-table tbody tr.losing-trade {
          background: #f8d7da;
        }
        .exit-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          display: inline-block;
        }
        .exit-badge.tp {
          background: #28a745;
          color: white;
        }
        .exit-badge.sl {
          background: #dc3545;
          color: white;
        }
        .exit-badge.eod {
          background: #6c757d;
          color: white;
        }
        .pnl-positive {
          color: #28a745;
          font-weight: bold;
        }
        .pnl-negative {
          color: #dc3545;
          font-weight: bold;
        }
        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 600;
          display: inline-flex;
          align-items: center;
          font-size: 14px;
        }
        .btn-primary {
          background: #007bff;
          color: white;
        }
        .btn-primary:hover:not(:disabled) {
          background: #0056b3;
        }
        .btn-primary:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }
        .btn-success {
          background: #28a745;
          color: white;
        }
        .btn-success:hover {
          background: #218838;
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

export default Algo1Min

