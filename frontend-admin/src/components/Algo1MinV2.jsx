import React, { useState, useEffect, useRef } from 'react'
import { Play, TrendingDown, TrendingUp, RefreshCw, FileText, DollarSign, ChevronRight, ChevronLeft, ZoomIn, ZoomOut, Plus, Eye, Pause, SkipForward } from 'lucide-react'

const Algo1MinV2 = () => {
  const [jsonData, setJsonData] = useState('')
  const [tpPercent, setTpPercent] = useState(2) // Percentage
  const [slPercent, setSlPercent] = useState(1) // Percentage
  const [lotSize, setLotSize] = useState(1)
  const [loading, setLoading] = useState(false)
  const [backtestResults, setBacktestResults] = useState(null)
  const [error, setError] = useState(null)
  
  // Chart view mode state
  const [viewMode, setViewMode] = useState('chart')
  const [currentCandleIndex, setCurrentCandleIndex] = useState(15)
  const [manualTrades, setManualTrades] = useState([])
  const [chartZoom, setChartZoom] = useState(1)
  const [chartPan, setChartPan] = useState(0)
  const [candlesData, setCandlesData] = useState(null)
  const [ema15Values, setEma15Values] = useState(null)
  const [ema50Values, setEma50Values] = useState(null)
  const [vwapValues, setVwapValues] = useState(null)
  const [visibleCandles, setVisibleCandles] = useState(50) // Show 50 candles at a time
  const [replayMode, setReplayMode] = useState(true) // Replay mode: only show candles up to current
  const [isPlaying, setIsPlaying] = useState(false) // Auto-play mode
  const [autoTrades, setAutoTrades] = useState([]) // Auto-generated trades
  const [algoStatus, setAlgoStatus] = useState(null) // Current algo status
  const playIntervalRef = useRef(null)
  
  // Algo parameters
  const [pullbackBuffer, setPullbackBuffer] = useState(0.05) // X points buffer for pullback
  const [emaDiffThreshold, setEmaDiffThreshold] = useState(0.1) // Minimum EMA15-EMA50 difference
  const [maxTradesPerDay, setMaxTradesPerDay] = useState(5)
  const [maxConsecutiveLosses, setMaxConsecutiveLosses] = useState(2)
  const [dailyMaxLossPercent, setDailyMaxLossPercent] = useState(2) // 2% daily max loss
  const [enableAutoTrade, setEnableAutoTrade] = useState(false) // Enable/disable auto trading

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

  // Calculate VWAP (Volume Weighted Average Price)
  const calculateVWAP = (data) => {
    if (data.length === 0) return null
    
    const vwapValues = []
    let cumulativeTPV = 0 // Typical Price * Volume
    let cumulativeVolume = 0
    
    for (let i = 0; i < data.length; i++) {
      const typicalPrice = (data[i].high + data[i].low + data[i].close) / 3
      const volume = data[i].volume || 0
      
      cumulativeTPV += typicalPrice * volume
      cumulativeVolume += volume
      
      const vwap = cumulativeVolume > 0 ? cumulativeTPV / cumulativeVolume : typicalPrice
      vwapValues.push(vwap)
    }
    
    return vwapValues
  }

  // Calculate EMA slope (rate of change)
  const calculateEMASlope = (emaValues, index) => {
    if (!emaValues || index < 1 || index >= emaValues.length) return 0
    return emaValues[index] - emaValues[index - 1]
  }

  // Check if time is within trading hours
  const isWithinTradingHours = (timestamp) => {
    const date = new Date(timestamp)
    const hours = date.getHours()
    const minutes = date.getMinutes()
    const timeInMinutes = hours * 60 + minutes
    
    // 09:20 - 10:30 (560 - 630 minutes)
    // 13:45 - 14:45 (825 - 885 minutes)
    return (timeInMinutes >= 560 && timeInMinutes <= 630) || 
           (timeInMinutes >= 825 && timeInMinutes <= 885)
  }

  // Check no-trade zone conditions
  const isNoTradeZone = (candles, index, ema15Values, avgVolume) => {
    if (index < 5 || index >= candles.length) return true
    
    const candle = candles[index]
    const prevCandles = candles.slice(Math.max(0, index - 20), index)
    
    // Check 1: Candle range < average range
    const avgRange = prevCandles.reduce((sum, c) => sum + (c.high - c.low), 0) / prevCandles.length
    if (candle.high - candle.low < avgRange * 0.5) return true
    
    // Check 2: Both wicks large (doji-like)
    const bodySize = Math.abs(candle.close - candle.open)
    const upperWick = candle.high - Math.max(candle.open, candle.close)
    const lowerWick = Math.min(candle.open, candle.close) - candle.low
    const totalRange = candle.high - candle.low
    if (totalRange > 0 && (upperWick / totalRange > 0.4 && lowerWick / totalRange > 0.4)) return true
    
    // Check 3: EMA15 crossed multiple times in last 5 candles
    if (index >= 20) {
      let crosses = 0
      for (let i = index - 4; i <= index; i++) {
        if (i > 0 && ema15Values && ema15Values[i - 15] && ema15Values[i - 1 - 15]) {
          const prevPrice = candles[i - 1].close
          const currPrice = candles[i].close
          const prevEMA = ema15Values[i - 1 - 15]
          const currEMA = ema15Values[i - 15]
          if ((prevPrice < prevEMA && currPrice > currEMA) || (prevPrice > prevEMA && currPrice < currEMA)) {
            crosses++
          }
        }
      }
      if (crosses >= 3) return true
    }
    
    // Check 4: Volume < 20-period avg volume
    if (candle.volume < avgVolume * 0.8) return true
    
    return false
  }

  const loadData = () => {
    if (!jsonData.trim()) {
      setError('Please paste JSON data')
      return
    }

    setLoading(true)
    setError(null)
    setBacktestResults(null)

    try {
      // Parse JSON
      const parsed = JSON.parse(jsonData)
      
      // Support both old format: { "data": { "candles": [...] } }
      // and new format: { "candles": [...] }
      let candlesArray = null
      if (parsed.data && parsed.data.candles && Array.isArray(parsed.data.candles)) {
        candlesArray = parsed.data.candles
      } else if (parsed.candles && Array.isArray(parsed.candles)) {
        candlesArray = parsed.candles
      } else {
        setError('Invalid JSON structure. Expected: { "candles": [...] } or { "data": { "candles": [...] } }')
        setLoading(false)
        return
      }

      // Convert candles to structured format
      // Format: [timestamp, open, high, low, close, volume]
      const candles = candlesArray.map((candle, index) => {
        if (!Array.isArray(candle) || candle.length < 5) {
          throw new Error(`Invalid candle format at index ${index}`)
        }
        
        // Handle timestamp - could be Unix timestamp (seconds) or ISO string
        let timestamp = candle[0]
        if (typeof timestamp === 'number') {
          // If timestamp is a number, check if it's seconds or milliseconds
          // Timestamps around 1764560940 are likely seconds (Unix timestamp)
          // Timestamps around 1764560940000 are milliseconds
          if (timestamp < 10000000000) {
            // Likely seconds, convert to milliseconds
            timestamp = new Date(timestamp * 1000).toISOString()
          } else {
            // Likely milliseconds
            timestamp = new Date(timestamp).toISOString()
          }
        } else if (typeof timestamp === 'string') {
          // Already a string, use as is
          timestamp = timestamp
        } else {
          throw new Error(`Invalid timestamp format at index ${index}`)
        }
        
        return {
          timestamp: timestamp,
          open: parseFloat(candle[1]),
          high: parseFloat(candle[2]),
          low: parseFloat(candle[3]),
          close: parseFloat(candle[4]),
          volume: candle[5] || 0
        }
      })

      if (candles.length < 50) {
        setError('Need at least 50 candles to calculate EMA 50')
        setLoading(false)
        return
      }

      // Calculate indicators
      const ema15Values = calculateEMA(candles, 15)
      const ema50Values = calculateEMA(candles, 50)
      const vwapValues = calculateVWAP(candles)
      
      if (!ema15Values || !ema50Values || !vwapValues) {
        setError('Failed to calculate indicators')
        setLoading(false)
        return
      }

      // Calculate average volume for no-trade zone filter
      const avgVolume = candles.slice(0, 20).reduce((sum, c) => sum + (c.volume || 0), 0) / 20

      // Prepare chart data (include all candles, indicators only available from their respective periods)
      const chartData = []
      for (let i = 0; i < candles.length; i++) {
        const candle = candles[i]
        // EMA15 available from index 15, EMA50 from index 50, VWAP from start
        const ema15 = i >= 15 ? ema15Values[i - 15] : null
        const ema50 = i >= 50 ? ema50Values[i - 50] : null
        const vwap = vwapValues[i]
        
        chartData.push({
          ...candle,
          ema15,
          ema50,
          vwap
        })
      }

      // Store candles and indicators for chart view
      setCandlesData(candles)
      setEma15Values(ema15Values)
      setEma50Values(ema50Values)
      setVwapValues(vwapValues)
      setCurrentCandleIndex(50) // Start from index 50 (when all indicators available)
      setManualTrades([])
      setAutoTrades([])
      setViewMode('chart')
      
      setBacktestResults({
        totalCandles: candles.length,
        trades: [],
        chartData,
        statistics: {
          totalTrades: 0,
          winningTrades: 0,
          losingTrades: 0,
          totalPNL: 0,
          avgPNL: 0,
          winRate: 0,
          tpTrades: 0,
          slTrades: 0,
          eodTrades: 0,
          callTrades: 0,
          putTrades: 0,
          callPNL: 0,
          putPNL: 0
        },
        parameters: {
          tpPercent: parseFloat(tpPercent) || 2,
          slPercent: parseFloat(slPercent) || 1,
          lotSize: parseFloat(lotSize) || 1,
          sharesPerLot: 75,
          totalShares: (parseFloat(lotSize) || 1) * 75
        }
      })

    } catch (err) {
      setError(`Error parsing JSON: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const clearData = () => {
    setJsonData('')
    setBacktestResults(null)
    setError(null)
    setViewMode('chart')
    setCurrentCandleIndex(0)
      setManualTrades([])
      setAutoTrades([])
      setCandlesData(null)
      setEma15Values(null)
      setEma50Values(null)
      setVwapValues(null)
      setAlgoStatus(null)
      setVisibleCandles(50)
  }

  // Add manual trade
  const addManualTrade = (type) => {
    if (!candlesData || currentCandleIndex < 0 || currentCandleIndex >= candlesData.length) return
    
    const candle = candlesData[currentCandleIndex]
    // EMA might not be available for first 15 candles
    const ema15 = currentCandleIndex >= 15 ? ema15Values[currentCandleIndex - 15] : null
    const SHARES_PER_LOT = 75
    const TOTAL_SHARES = parseFloat(lotSize) * SHARES_PER_LOT
    const TP_PERCENT = parseFloat(tpPercent) || 2
    const SL_PERCENT = parseFloat(slPercent) || 1
    
    // Entry price is current candle's close price
    const entryPrice = candle.close
    
    // Calculate TP and SL prices based on percentage
    let tpPrice, slPrice
    if (type === 'PUT') {
      // PUT: Profit when price goes DOWN, Loss when price goes UP
      // TP: Price goes down by TP%
      tpPrice = entryPrice * (1 - TP_PERCENT / 100)
      // SL: Price goes up by SL%
      slPrice = entryPrice * (1 + SL_PERCENT / 100)
    } else {
      // CALL: Profit when price goes UP, Loss when price goes DOWN
      // TP: Price goes up by TP%
      tpPrice = entryPrice * (1 + TP_PERCENT / 100)
      // SL: Price goes down by SL%
      slPrice = entryPrice * (1 - SL_PERCENT / 100)
    }
    
    const newTrade = {
      id: Date.now(),
      type: type,
      entryTime: candle.timestamp,
      entryPrice: entryPrice,
      ema15: ema15 ? Math.round(ema15 * 100) / 100 : null,
      ema50: currentCandleIndex >= 50 ? (ema50Values[currentCandleIndex - 50] ? Math.round(ema50Values[currentCandleIndex - 50] * 100) / 100 : null) : null,
      vwap: vwapValues ? (vwapValues[currentCandleIndex] ? Math.round(vwapValues[currentCandleIndex] * 100) / 100 : null) : null,
      tpPercent: TP_PERCENT,
      slPercent: SL_PERCENT,
      tpPrice: Math.round(tpPrice * 100) / 100,
      slPrice: Math.round(slPrice * 100) / 100,
      lotSize: parseFloat(lotSize),
      totalShares: TOTAL_SHARES,
      exitTime: null,
      exitPrice: null,
      exitReason: null,
      pnl: null,
      points: null,
      isManual: true
    }
    
    setManualTrades([...manualTrades, newTrade])
  }

  // Process manual trades (check TP/SL)
  const processManualTrades = () => {
    if (!candlesData || manualTrades.length === 0) return
    
    const updatedTrades = manualTrades.map(trade => {
      if (trade.exitTime) return trade // Already closed
      
      // Find entry candle index
      const entryIndex = candlesData.findIndex(c => {
        const cTime = new Date(c.timestamp).getTime()
        const tTime = new Date(trade.entryTime).getTime()
        return Math.abs(cTime - tTime) < 1000 // Within 1 second
      })
      
      if (entryIndex === -1 || currentCandleIndex <= entryIndex) return trade
      
      // Check all candles from entry to current
      for (let i = entryIndex + 1; i <= currentCandleIndex; i++) {
        const candle = candlesData[i]
        let exitPrice = null
        let exitReason = null
        
        if (trade.type === 'PUT') {
          if (candle.low <= trade.tpPrice) {
            exitPrice = trade.tpPrice
            exitReason = 'TP'
          } else if (candle.high >= trade.slPrice) {
            exitPrice = trade.slPrice
            exitReason = 'SL'
          }
        } else if (trade.type === 'CALL') {
          if (candle.high >= trade.tpPrice) {
            exitPrice = trade.tpPrice
            exitReason = 'TP'
          } else if (candle.low <= trade.slPrice) {
            exitPrice = trade.slPrice
            exitReason = 'SL'
          }
        }
        
        if (exitPrice !== null) {
          // Calculate PNL correctly
          let pnl, points
          if (trade.type === 'PUT') {
            // PUT: Profit when exit price < entry price (price went down)
            // PNL = (Entry Price - Exit Price) * Shares
            points = trade.entryPrice - exitPrice
            pnl = points * trade.totalShares
          } else {
            // CALL: Profit when exit price > entry price (price went up)
            // PNL = (Exit Price - Entry Price) * Shares
            points = exitPrice - trade.entryPrice
            pnl = points * trade.totalShares
          }
          
          return {
            ...trade,
            exitTime: candle.timestamp,
            exitPrice,
            exitReason,
            pnl: Math.round(pnl * 100) / 100,
            points: Math.round(points * 100) / 100
          }
        }
      }
      
      return trade
    })
    
    setManualTrades(updatedTrades)
  }

  // Algo Engine - Process candle and generate trades
  const processAlgoCandle = (index) => {
    if (!candlesData || !ema15Values || !ema50Values || !vwapValues || index < 50) return null
    
    const candle = candlesData[index]
    const prevCandle = index > 0 ? candlesData[index - 1] : null
    
    // Check time filter
    if (!isWithinTradingHours(candle.timestamp)) {
      setAlgoStatus({ mode: 'NO_TRADE', reason: 'Outside trading hours', index })
      return null
    }
    
    // Get indicators
    const ema15 = ema15Values[index - 15]
    const ema50 = ema50Values[index - 50]
    const vwap = vwapValues[index]
    const ema15Slope = calculateEMASlope(ema15Values, index - 15)
    const price = candle.close
    
    // Calculate average volume
    const avgVolume = candlesData.slice(Math.max(0, index - 20), index).reduce((sum, c) => sum + (c.volume || 0), 0) / Math.min(20, index)
    
    // Check no-trade zone
    if (isNoTradeZone(candlesData, index, ema15Values, avgVolume)) {
      setAlgoStatus({ mode: 'NO_TRADE', reason: 'No-trade zone conditions', index })
      return null
    }
    
    // Market Trend Filter
    const emaDiff = Math.abs(ema15 - ema50)
    if (emaDiff < emaDiffThreshold) {
      setAlgoStatus({ mode: 'NO_TRADE', reason: 'EMA15-EMA50 difference too small', index })
      return null
    }
    
    if (Math.abs(ema15Slope) < 0.01) {
      setAlgoStatus({ mode: 'NO_TRADE', reason: 'EMA15 slope too flat', index })
      return null
    }
    
    // Check CALL mode enable
    const callModeEnabled = ema15 > ema50 && ema15Slope > 0 && price > vwap
    // Check PUT mode enable
    const putModeEnabled = ema15 < ema50 && ema15Slope < 0 && price < vwap
    
    if (!callModeEnabled && !putModeEnabled) {
      setAlgoStatus({ mode: 'NO_TRADE', reason: 'Trend filter not met', index })
      return null
    }
    
    // Check for pullback setup (current candle)
    const pullbackBufferPoints = price * (pullbackBuffer / 100)
    
    let setupType = null
    let rejectionCandle = null
    
    // CALL SETUP: Candle touches/comes within X points of EMA15, closes ABOVE EMA15, low < EMA15
    if (callModeEnabled) {
      const touchesEMA = candle.low <= ema15 + pullbackBufferPoints && candle.low >= ema15 - pullbackBufferPoints
      const closesAbove = candle.close > ema15
      const hasRejectionWick = candle.low < ema15
      
      if (touchesEMA && closesAbove && hasRejectionWick) {
        setupType = 'CALL_SETUP'
        rejectionCandle = candle
      }
    }
    
    // PUT SETUP: Candle touches/comes within X points of EMA15, closes BELOW EMA15, high > EMA15
    if (putModeEnabled) {
      const touchesEMA = candle.high >= ema15 - pullbackBufferPoints && candle.high <= ema15 + pullbackBufferPoints
      const closesBelow = candle.close < ema15
      const hasRejectionWick = candle.high > ema15
      
      if (touchesEMA && closesBelow && hasRejectionWick) {
        setupType = 'PUT_SETUP'
        rejectionCandle = candle
      }
    }
    
    if (!setupType || !rejectionCandle) {
      setAlgoStatus({ mode: 'WAITING', reason: 'Looking for pullback setup', index })
      return null
    }
    
    // Setup found, wait for confirmation on next candle
    const setupInfo = { 
      setupType, 
      rejectionCandle,
      rejectionCandleIndex: index,
      ema15: ema15,
      ema50: ema50,
      vwap: vwap
    }
    setAlgoStatus({ 
      mode: 'SETUP_FOUND', 
      setupInfo: setupInfo,
      index 
    })
    
    return setupInfo
  }

  // Check confirmation on next candle after setup
  const checkConfirmation = (setupInfo, confirmationCandleIndex) => {
    if (!setupInfo || !candlesData || !ema15Values || !ema50Values || !vwapValues || confirmationCandleIndex >= candlesData.length) return null
    
    const confirmationCandle = candlesData[confirmationCandleIndex]
    const prevCandle = confirmationCandleIndex > 0 ? candlesData[confirmationCandleIndex - 1] : null
    const rejectionCandle = setupInfo.rejectionCandle
    
    if (!prevCandle || !rejectionCandle) return null
    
    // Get rejection candle from data to ensure we have the right one
    const actualRejectionCandle = candlesData[setupInfo.rejectionCandleIndex]
    if (!actualRejectionCandle) return null
    
    // Check daily risk limits
    const pnlData = getAllTradesPNL()
    if (pnlData.todayTrades >= maxTradesPerDay) {
      setAlgoStatus({ mode: 'NO_TRADE', reason: 'Max trades per day reached', index: confirmationCandleIndex })
      return null
    }
    if (pnlData.consecutiveLosses >= maxConsecutiveLosses) {
      setAlgoStatus({ mode: 'NO_TRADE', reason: 'Max consecutive losses reached', index: confirmationCandleIndex })
      return null
    }
    
    let confirmed = false
    let tradeType = null
    
    if (setupInfo.setupType === 'CALL_SETUP') {
      // CALL: Next candle HIGH > Rejection HIGH, CLOSE > Rejection HIGH, Volume > Previous
      confirmed = confirmationCandle.high > actualRejectionCandle.high && 
                  confirmationCandle.close > actualRejectionCandle.high &&
                  confirmationCandle.volume > prevCandle.volume
      tradeType = 'CALL'
    } else if (setupInfo.setupType === 'PUT_SETUP') {
      // PUT: Next candle LOW < Rejection LOW, CLOSE < Rejection LOW, Volume > Previous
      confirmed = confirmationCandle.low < actualRejectionCandle.low && 
                  confirmationCandle.close < actualRejectionCandle.low &&
                  confirmationCandle.volume > prevCandle.volume
      tradeType = 'PUT'
    }
    
    if (confirmed) {
      // Entry trigger - create trade
      const entryPrice = confirmationCandle.close
      const SHARES_PER_LOT = 75
      const TOTAL_SHARES = parseFloat(lotSize) * SHARES_PER_LOT
      
      // Calculate SL and Target
      let slPrice, tpPrice
      if (tradeType === 'CALL') {
        slPrice = actualRejectionCandle.low // Rejection candle LOW
        const slPoints = entryPrice - slPrice
        tpPrice = entryPrice + slPoints // 1:1 RR
      } else {
        slPrice = actualRejectionCandle.high // Rejection candle HIGH
        const slPoints = slPrice - entryPrice
        tpPrice = entryPrice - slPoints // 1:1 RR
      }
      
      const newTrade = {
        id: Date.now() + Math.random(),
        type: tradeType,
        entryTime: confirmationCandle.timestamp,
        entryPrice: entryPrice,
        ema15: ema15Values[confirmationCandleIndex - 15],
        ema50: ema50Values[confirmationCandleIndex - 50],
        vwap: vwapValues[confirmationCandleIndex],
        slPrice: Math.round(slPrice * 100) / 100,
        tpPrice: Math.round(tpPrice * 100) / 100,
        rejectionCandleIndex: setupInfo.rejectionCandleIndex,
        lotSize: parseFloat(lotSize),
        totalShares: TOTAL_SHARES,
        exitTime: null,
        exitPrice: null,
        exitReason: null,
        pnl: null,
        points: null,
        candlesSinceEntry: 0,
        isManual: false
      }
      
      setAlgoStatus({ mode: 'TRADE_ENTERED', trade: newTrade, index: confirmationCandleIndex })
      return newTrade
    }
    
    return null
  }

  // Process auto trades (check TP/SL and exit conditions)
  const processAutoTrades = (currentIndex) => {
    if (!candlesData || autoTrades.length === 0) return
    
    const updatedTrades = autoTrades.map(trade => {
      if (trade.exitTime) return trade // Already closed
      
      // Find entry candle index
      const entryIndex = candlesData.findIndex(c => {
        const cTime = new Date(c.timestamp).getTime()
        const tTime = new Date(trade.entryTime).getTime()
        return Math.abs(cTime - tTime) < 1000
      })
      
      if (entryIndex === -1 || currentIndex <= entryIndex) return trade
      
      // Update candles since entry
      trade.candlesSinceEntry = currentIndex - entryIndex
      
      // Check all candles from entry to current
      for (let i = entryIndex + 1; i <= currentIndex; i++) {
        const candle = candlesData[i]
        let exitPrice = null
        let exitReason = null
        
        // Check TP/SL
        if (trade.type === 'PUT') {
          if (candle.low <= trade.tpPrice) {
            exitPrice = trade.tpPrice
            exitReason = 'TP'
          } else if (candle.high >= trade.slPrice) {
            exitPrice = trade.slPrice
            exitReason = 'SL'
          }
        } else if (trade.type === 'CALL') {
          if (candle.high >= trade.tpPrice) {
            exitPrice = trade.tpPrice
            exitReason = 'TP'
          } else if (candle.low <= trade.slPrice) {
            exitPrice = trade.slPrice
            exitReason = 'SL'
          }
        }
        
        // Check exit on opposite side of EMA15
        if (!exitPrice && i >= 15) {
          const ema15 = ema15Values[i - 15]
          if (trade.type === 'CALL' && candle.close < ema15) {
            exitPrice = candle.close
            exitReason = 'EMA_EXIT'
          } else if (trade.type === 'PUT' && candle.close > ema15) {
            exitPrice = candle.close
            exitReason = 'EMA_EXIT'
          }
        }
        
        // Check time exit (max 3 candles)
        if (!exitPrice && trade.candlesSinceEntry >= 3) {
          exitPrice = candle.close
          exitReason = 'TIME_EXIT'
        }
        
        if (exitPrice !== null) {
          // Calculate PNL
          let pnl, points
          if (trade.type === 'PUT') {
            points = trade.entryPrice - exitPrice
            pnl = points * trade.totalShares
          } else {
            points = exitPrice - trade.entryPrice
            pnl = points * trade.totalShares
          }
          
          return {
            ...trade,
            exitTime: candle.timestamp,
            exitPrice,
            exitReason,
            pnl: Math.round(pnl * 100) / 100,
            points: Math.round(points * 100) / 100
          }
        }
      }
      
      return trade
    })
    
    setAutoTrades(updatedTrades)
  }

  // Navigate to next candle
  const nextCandle = () => {
    if (!candlesData || currentCandleIndex >= candlesData.length - 1) {
      setIsPlaying(false)
      return
    }
    const nextIndex = currentCandleIndex + 1
    setCurrentCandleIndex(nextIndex)
    
    // Process manual trades
    processManualTrades()
    
    // Process auto trades
    processAutoTrades(nextIndex)
    
    // Run algo if auto-trade enabled
    if (enableAutoTrade && nextIndex >= 50) {
      // Check if we have a pending setup from previous candle
      const prevSetup = algoStatus?.mode === 'SETUP_FOUND' ? algoStatus.setupInfo : null
      
      if (prevSetup && algoStatus.index === currentCandleIndex) {
        // Check confirmation on next candle
        const confirmedTrade = checkConfirmation(prevSetup, nextIndex)
        if (confirmedTrade) {
          setAutoTrades(prev => [...prev, confirmedTrade])
          setAlgoStatus({ mode: 'TRADE_ENTERED', trade: confirmedTrade, index: nextIndex })
        } else {
          // Setup not confirmed, reset and process new candle
          processAlgoCandle(nextIndex)
        }
      } else {
        // Process new candle for setup
        processAlgoCandle(nextIndex)
      }
    }
  }

  // Navigate to previous candle
  const prevCandle = () => {
    if (currentCandleIndex <= 0) return
    setCurrentCandleIndex(currentCandleIndex - 1)
  }

  // Toggle play/pause
  const togglePlay = () => {
    if (isPlaying) {
      setIsPlaying(false)
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current)
        playIntervalRef.current = null
      }
    } else {
      setIsPlaying(true)
      playIntervalRef.current = setInterval(() => {
        nextCandle()
      }, 500) // Move to next candle every 500ms
    }
  }

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current)
      }
    }
  }, [])

  // Stop playing when reaching the end
  useEffect(() => {
    if (candlesData && currentCandleIndex >= candlesData.length - 1) {
      setIsPlaying(false)
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current)
        playIntervalRef.current = null
      }
    }
  }, [currentCandleIndex, candlesData])

  // Calculate all trades PNL (manual + auto)
  const getAllTradesPNL = () => {
    const allTrades = [...manualTrades, ...autoTrades]
    
    const totalPNL = allTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
    const closedTrades = allTrades.filter(t => t.exitTime !== null)
    const openTrades = allTrades.filter(t => t.exitTime === null)
    
    // Daily risk management checks
    const todayTrades = allTrades.filter(t => {
      const tradeDate = new Date(t.entryTime).toDateString()
      const today = new Date().toDateString()
      return tradeDate === today
    })
    
    const todayPNL = todayTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
    const consecutiveLosses = (() => {
      let count = 0
      for (let i = allTrades.length - 1; i >= 0; i--) {
        if (allTrades[i].pnl === null) break
        if (allTrades[i].pnl < 0) count++
        else break
      }
      return count
    })()
    
    return {
      allTrades,
      totalPNL: Math.round(totalPNL * 100) / 100,
      closedTrades: closedTrades.length,
      openTrades: openTrades.length,
      totalTrades: allTrades.length,
      todayTrades: todayTrades.length,
      todayPNL: Math.round(todayPNL * 100) / 100,
      consecutiveLosses
    }
  }

  // Chart Component - Show only visible candles around current
  const ChartComponent = ({ chartData, trades, viewMode, currentIndex, manualTrades, autoTrades, visibleCandlesCount, replayMode }) => {
    const canvasRef = useRef(null)
    const containerRef = useRef(null)
    const [hoveredIndex, setHoveredIndex] = useState(null)

    useEffect(() => {
      if (!canvasRef.current || !chartData || chartData.length === 0) return

      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      
      // Set canvas size based on container
      const container = containerRef.current
      if (container) {
        canvas.width = container.clientWidth
        canvas.height = 600
      }
      
      const width = canvas.width
      const height = canvas.height
      const padding = { top: 50, right: 80, bottom: 70, left: 90 }

      // Clear canvas with white background
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, width, height)

      // In replay mode, only show candles up to current index
      // Otherwise, show candles around current index
      let startIndex, endIndex, visibleData
      
      if (replayMode) {
        // Replay mode: show from start to current (or last visibleCandlesCount candles if current is far)
        const maxVisible = Math.min(visibleCandlesCount, currentIndex + 1)
        startIndex = Math.max(0, currentIndex + 1 - maxVisible)
        endIndex = currentIndex + 1 // Only up to current candle
        visibleData = chartData.slice(startIndex, endIndex)
      } else {
        // Normal mode: show candles around current index
        const halfVisible = Math.floor(visibleCandlesCount / 2)
        startIndex = Math.max(0, currentIndex - halfVisible)
        endIndex = Math.min(chartData.length, startIndex + visibleCandlesCount)
        
        // If we're near the start, show from beginning
        if (currentIndex < halfVisible) {
          startIndex = 0
          endIndex = Math.min(chartData.length, visibleCandlesCount)
        }
        
        visibleData = chartData.slice(startIndex, endIndex)
      }

      if (visibleData.length === 0) return

      // Calculate price range for visible data (filter out null indicator values)
      const allPrices = visibleData.flatMap(d => {
        const prices = [d.high, d.low, d.open, d.close]
        if (d.ema15 !== null && d.ema15 !== undefined) prices.push(d.ema15)
        if (d.ema50 !== null && d.ema50 !== undefined) prices.push(d.ema50)
        if (d.vwap !== null && d.vwap !== undefined) prices.push(d.vwap)
        return prices
      })
      const minPrice = Math.min(...allPrices)
      const maxPrice = Math.max(...allPrices)
      const priceRange = maxPrice - minPrice
      const pricePadding = priceRange * 0.15

      const chartWidth = width - padding.left - padding.right
      const chartHeight = height - padding.top - padding.bottom
      const candleWidth = Math.max(1, (chartWidth / visibleData.length) * 0.7)
      const candleSpacing = chartWidth / visibleData.length

      // Price to Y coordinate
      const priceToY = (price) => {
        return padding.top + chartHeight - ((price - minPrice + pricePadding) / (priceRange + pricePadding * 2)) * chartHeight
      }

      // Draw clean grid lines
      ctx.strokeStyle = '#f0f0f0'
      ctx.lineWidth = 1
      for (let i = 0; i <= 5; i++) {
        const price = minPrice - pricePadding + (priceRange + pricePadding * 2) * (i / 5)
        const y = priceToY(price)
        ctx.beginPath()
        ctx.moveTo(padding.left, y)
        ctx.lineTo(width - padding.right, y)
        ctx.stroke()
        
        // Price labels with better formatting
        ctx.fillStyle = '#666'
        ctx.font = '12px Arial'
        ctx.textAlign = 'right'
        ctx.fillText(price.toFixed(2), padding.left - 15, y + 4)
      }
      
      // Vertical grid lines
      ctx.strokeStyle = '#f5f5f5'
      ctx.lineWidth = 1
      for (let i = 0; i < visibleData.length; i += Math.max(1, Math.floor(visibleData.length / 10))) {
        const x = padding.left + i * candleSpacing + candleSpacing / 2
        ctx.beginPath()
        ctx.moveTo(x, padding.top)
        ctx.lineTo(x, height - padding.bottom)
        ctx.stroke()
      }

      // Draw EMA15 line
      ctx.strokeStyle = '#e63946'
      ctx.lineWidth = 2.5
      ctx.lineJoin = 'round'
      ctx.beginPath()
      let ema15Started = false
      for (let i = 0; i < visibleData.length; i++) {
        if (visibleData[i].ema15 !== null && visibleData[i].ema15 !== undefined) {
          const x = padding.left + i * candleSpacing + candleSpacing / 2
          const y = priceToY(visibleData[i].ema15)
          if (!ema15Started) {
            ctx.moveTo(x, y)
            ema15Started = true
          } else {
            ctx.lineTo(x, y)
          }
        }
      }
      if (ema15Started) {
        ctx.stroke()
      }

      // Draw EMA50 line
      ctx.strokeStyle = '#3b82f6'
      ctx.lineWidth = 2
      ctx.lineJoin = 'round'
      ctx.beginPath()
      let ema50Started = false
      for (let i = 0; i < visibleData.length; i++) {
        if (visibleData[i].ema50 !== null && visibleData[i].ema50 !== undefined) {
          const x = padding.left + i * candleSpacing + candleSpacing / 2
          const y = priceToY(visibleData[i].ema50)
          if (!ema50Started) {
            ctx.moveTo(x, y)
            ema50Started = true
          } else {
            ctx.lineTo(x, y)
          }
        }
      }
      if (ema50Started) {
        ctx.stroke()
      }

      // Draw VWAP line
      ctx.strokeStyle = '#8b5cf6'
      ctx.lineWidth = 2
      ctx.lineJoin = 'round'
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      let vwapStarted = false
      for (let i = 0; i < visibleData.length; i++) {
        if (visibleData[i].vwap !== null && visibleData[i].vwap !== undefined) {
          const x = padding.left + i * candleSpacing + candleSpacing / 2
          const y = priceToY(visibleData[i].vwap)
          if (!vwapStarted) {
            ctx.moveTo(x, y)
            vwapStarted = true
          } else {
            ctx.lineTo(x, y)
          }
        }
      }
      if (vwapStarted) {
        ctx.stroke()
      }
      ctx.setLineDash([])

      // Draw indicator labels
      let labelY = padding.top + 5
      if (ema15Started) {
        ctx.fillStyle = 'rgba(230, 57, 70, 0.1)'
        ctx.fillRect(width - padding.right - 80, labelY, 75, 20)
        ctx.fillStyle = '#e63946'
        ctx.font = 'bold 12px Arial'
        ctx.textAlign = 'left'
        ctx.fillText('EMA15', width - padding.right - 75, labelY + 15)
        labelY += 25
      }
      if (ema50Started) {
        ctx.fillStyle = 'rgba(59, 130, 246, 0.1)'
        ctx.fillRect(width - padding.right - 80, labelY, 75, 20)
        ctx.fillStyle = '#3b82f6'
        ctx.font = 'bold 12px Arial'
        ctx.textAlign = 'left'
        ctx.fillText('EMA50', width - padding.right - 75, labelY + 15)
        labelY += 25
      }
      if (vwapStarted) {
        ctx.fillStyle = 'rgba(139, 92, 246, 0.1)'
        ctx.fillRect(width - padding.right - 80, labelY, 75, 20)
        ctx.fillStyle = '#8b5cf6'
        ctx.font = 'bold 12px Arial'
        ctx.textAlign = 'left'
        ctx.fillText('VWAP', width - padding.right - 75, labelY + 15)
      }

      // Draw candles (clean style)
      for (let i = 0; i < visibleData.length; i++) {
        const candle = visibleData[i]
        const globalIndex = startIndex + i
        const x = padding.left + i * candleSpacing + candleSpacing / 2 - candleWidth / 2
        const centerX = padding.left + i * candleSpacing + candleSpacing / 2

        const openY = priceToY(candle.open)
        const closeY = priceToY(candle.close)
        const highY = priceToY(candle.high)
        const lowY = priceToY(candle.low)

        const isBullish = candle.close >= candle.open
        const color = isBullish ? '#10b981' : '#ef4444'
        const borderColor = isBullish ? '#059669' : '#dc2626'

        // Draw wick (thinner)
        ctx.strokeStyle = color
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.moveTo(centerX, highY)
        ctx.lineTo(centerX, lowY)
        ctx.stroke()

        // Draw body with border
        const bodyTop = Math.min(openY, closeY)
        const bodyHeight = Math.max(1, Math.abs(closeY - openY))
        ctx.fillStyle = color
        ctx.fillRect(x, bodyTop, candleWidth, bodyHeight)
        ctx.strokeStyle = borderColor
        ctx.lineWidth = 1
        ctx.strokeRect(x, bodyTop, candleWidth, bodyHeight)

        // Highlight current candle
        if (globalIndex === currentIndex) {
          ctx.strokeStyle = '#3b82f6'
          ctx.lineWidth = 3
          ctx.strokeRect(x - 2, padding.top, candleWidth + 4, chartHeight)
          
          // Draw current price line
          ctx.strokeStyle = '#3b82f6'
          ctx.lineWidth = 2
          ctx.setLineDash([5, 5])
          ctx.beginPath()
          ctx.moveTo(padding.left, closeY)
          ctx.lineTo(width - padding.right, closeY)
          ctx.stroke()
          ctx.setLineDash([])
        }

        // Draw trade markers (manual + auto)
        const allTradesToShow = [...manualTrades, ...autoTrades]
        allTradesToShow.forEach(trade => {
          const tradeEntryTime = new Date(trade.entryTime).getTime()
          const candleTime = new Date(candle.timestamp).getTime()
          
          // Check if entry matches this candle (within 1 second)
          if (Math.abs(tradeEntryTime - candleTime) < 1000) {
            const markerY = priceToY(trade.entryPrice)
            ctx.fillStyle = trade.type === 'CALL' ? '#6366f1' : '#f97316'
            ctx.beginPath()
            ctx.arc(centerX, markerY, 10, 0, Math.PI * 2)
            ctx.fill()
            ctx.strokeStyle = '#fff'
            ctx.lineWidth = 3
            ctx.stroke()
            // Draw label for trade type
            ctx.fillStyle = '#fff'
            ctx.font = 'bold 10px Arial'
            ctx.textAlign = 'center'
            ctx.fillText(trade.isManual ? 'M' : 'A', centerX, markerY + 3)
          }
          
          // Check if exit matches this candle (within 1 second)
          if (trade.exitTime) {
            const tradeExitTime = new Date(trade.exitTime).getTime()
            if (Math.abs(tradeExitTime - candleTime) < 1000) {
              const markerY = priceToY(trade.exitPrice)
              ctx.fillStyle = trade.exitReason === 'TP' ? '#10b981' : '#ef4444'
              ctx.beginPath()
              ctx.arc(centerX, markerY, 10, 0, Math.PI * 2)
              ctx.fill()
              ctx.strokeStyle = '#fff'
              ctx.lineWidth = 3
              ctx.stroke()
            }
          }
        })
      }

      // Draw time labels (cleaner)
      ctx.fillStyle = '#666'
      ctx.font = '11px Arial'
      ctx.textAlign = 'center'
      const labelInterval = Math.max(1, Math.floor(visibleData.length / 8))
      for (let i = 0; i < visibleData.length; i += labelInterval) {
        const x = padding.left + i * candleSpacing + candleSpacing / 2
        const time = new Date(visibleData[i].timestamp).toLocaleTimeString('en-IN', { 
          hour: '2-digit', 
          minute: '2-digit',
          second: '2-digit'
        })
        ctx.fillText(time, x, height - padding.bottom + 25)
      }

      // Draw clean legend
      const legendY = height - padding.bottom + 15
      ctx.fillStyle = '#333'
      ctx.font = '11px Arial'
      ctx.textAlign = 'left'
      ctx.fillText('Legend:', padding.left, legendY)
      
      const legendItems = [
        { color: '#6366f1', text: 'CALL Entry' },
        { color: '#f97316', text: 'PUT Entry' },
        { color: '#10b981', text: 'TP Exit' },
        { color: '#ef4444', text: 'SL Exit' }
      ]
      
      let legendX = padding.left + 60
      legendItems.forEach((item, idx) => {
        ctx.fillStyle = item.color
        ctx.fillRect(legendX, legendY - 8, 12, 12)
        ctx.fillStyle = '#333'
        ctx.fillText(item.text, legendX + 16, legendY)
        legendX += item.text.length * 7 + 30
      })

    }, [chartData, trades, viewMode, currentIndex, manualTrades, autoTrades, visibleCandlesCount, replayMode])

    return (
      <div className="chart-container" ref={containerRef}>
        <div className="chart-controls">
          <div className="visible-candles-control">
            <label>Visible Candles:</label>
            <input
              type="number"
              value={visibleCandlesCount}
              onChange={(e) => setVisibleCandles(Math.max(10, Math.min(200, parseInt(e.target.value) || 50)))}
              className="form-input"
              min="10"
              max="200"
              style={{ width: '80px', marginLeft: '10px' }}
            />
          </div>
        </div>
        <div className="chart-wrapper">
          <canvas
            ref={canvasRef}
            style={{ 
              maxWidth: '100%', 
              height: 'auto', 
              border: '1px solid #e5e7eb', 
              borderRadius: '8px',
              display: 'block'
            }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="algo-container">
      <div className="card">
        <div className="card-header">
          <h2>EMA 15 Scalping Algo - Final Version</h2>
          <p>Strategy: Pullback to EMA15 with EMA15/EMA50 trend filter, VWAP confirmation, 1:1 RR</p>
        </div>

        <div className="card-body">
          {/* Controls */}
          <div className="controls-section">
            <div className="control-group">
              <label>
                <FileText size={16} style={{ marginRight: '5px' }} />
                JSON Data:
              </label>
              <textarea
                value={jsonData}
                onChange={(e) => setJsonData(e.target.value)}
                className="form-textarea"
                placeholder='Paste JSON data here...\n\nExample:\n{\n  "status": "success",\n  "data": {\n    "candles": [\n      ["2025-12-19T09:15:00", 55.0, 64.45, 51.35, 61.3, 6093225],\n      ...\n    ]\n  }\n}'
                rows={8}
                style={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
            </div>

            <div className="controls-row">
              <div className="control-group">
                <label>
                  <TrendingUp size={16} style={{ marginRight: '5px' }} />
                  TP (%):
                </label>
                <input
                  type="number"
                  value={tpPercent}
                  onChange={(e) => setTpPercent(e.target.value)}
                  className="form-input"
                  min="0.1"
                  step="0.1"
                  style={{ minWidth: '100px' }}
                />
              </div>

              <div className="control-group">
                <label>
                  <TrendingDown size={16} style={{ marginRight: '5px' }} />
                  SL (%):
                </label>
                <input
                  type="number"
                  value={slPercent}
                  onChange={(e) => setSlPercent(e.target.value)}
                  className="form-input"
                  min="0.1"
                  step="0.1"
                  style={{ minWidth: '100px' }}
                />
              </div>

              <div className="control-group">
                <label>
                  <DollarSign size={16} style={{ marginRight: '5px' }} />
                  Lot Size:
                </label>
                <input
                  type="number"
                  value={lotSize}
                  onChange={(e) => setLotSize(e.target.value)}
                  className="form-input"
                  min="1"
                  step="1"
                  style={{ minWidth: '100px' }}
                />
                <span style={{ marginLeft: '5px', fontSize: '12px', color: '#666' }}>
                  (1 lot = 75 shares)
                </span>
              </div>
            </div>

            <div className="controls-row">
              <div className="control-group">
                <label>
                  Pullback Buffer (%):
                </label>
                <input
                  type="number"
                  value={pullbackBuffer}
                  onChange={(e) => setPullbackBuffer(e.target.value)}
                  className="form-input"
                  min="0.01"
                  step="0.01"
                  style={{ minWidth: '100px' }}
                />
              </div>

              <div className="control-group">
                <label>
                  EMA Diff Threshold:
                </label>
                <input
                  type="number"
                  value={emaDiffThreshold}
                  onChange={(e) => setEmaDiffThreshold(e.target.value)}
                  className="form-input"
                  min="0.01"
                  step="0.01"
                  style={{ minWidth: '100px' }}
                />
              </div>

              <div className="control-group">
                <label>
                  <input
                    type="checkbox"
                    checked={enableAutoTrade}
                    onChange={(e) => setEnableAutoTrade(e.target.checked)}
                    style={{ marginRight: '5px' }}
                  />
                  Enable Auto Trade
                </label>
              </div>
            </div>

            <div className="button-group">
              <button
                onClick={loadData}
                className="btn btn-primary"
                disabled={loading || !jsonData.trim()}
              >
                {loading ? (
                  <>
                    <RefreshCw size={16} className="spinning" style={{ marginRight: '5px' }} />
                    Loading...
                  </>
                ) : (
                  <>
                    <Play size={16} style={{ marginRight: '5px' }} />
                    Load Chart
                  </>
                )}
              </button>
              <button
                onClick={clearData}
                className="btn btn-secondary"
                disabled={loading}
              >
                <RefreshCw size={16} style={{ marginRight: '5px' }} />
                Clear
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* Chart View Mode */}
          {backtestResults && candlesData && (
            <div className="chart-view-section">
              {/* Navigation Controls */}
              <div className="chart-nav-controls">
                <div className="nav-left">
                  <button
                    onClick={prevCandle}
                    className="btn-nav"
                    disabled={currentCandleIndex <= 0 || isPlaying}
                  >
                    <ChevronLeft size={20} />
                    Previous
                  </button>
                  
                  <button
                    onClick={togglePlay}
                    className={`btn-play ${isPlaying ? 'playing' : ''}`}
                    disabled={currentCandleIndex >= candlesData.length - 1}
                  >
                    {isPlaying ? (
                      <>
                        <Pause size={18} style={{ marginRight: '5px' }} />
                        Pause
                      </>
                    ) : (
                      <>
                        <Play size={18} style={{ marginRight: '5px' }} />
                        Play
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={nextCandle}
                    className="btn-nav"
                    disabled={currentCandleIndex >= candlesData.length - 1 || isPlaying}
                  >
                    Next
                    <ChevronRight size={20} />
                  </button>
                </div>
                
                <div className="candle-info">
                  <div className="info-item">
                    <label>Candle:</label>
                    <span>{currentCandleIndex + 1} / {candlesData.length}</span>
                  </div>
                  <div className="info-item">
                    <label>Time:</label>
                    <span>{new Date(candlesData[currentCandleIndex]?.timestamp).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="info-item">
                    <label>Price:</label>
                    <span>O: {candlesData[currentCandleIndex]?.open.toFixed(2)} | H: {candlesData[currentCandleIndex]?.high.toFixed(2)} | L: {candlesData[currentCandleIndex]?.low.toFixed(2)} | C: {candlesData[currentCandleIndex]?.close.toFixed(2)}</span>
                  </div>
                  <div className="info-item">
                    <label>EMA15:</label>
                    <span>{currentCandleIndex >= 15 ? (ema15Values[currentCandleIndex - 15]?.toFixed(2) || 'N/A') : 'N/A'}</span>
                  </div>
                  <div className="info-item">
                    <label>EMA50:</label>
                    <span>{currentCandleIndex >= 50 ? (ema50Values[currentCandleIndex - 50]?.toFixed(2) || 'N/A') : 'N/A'}</span>
                  </div>
                  <div className="info-item">
                    <label>VWAP:</label>
                    <span>{vwapValues ? (vwapValues[currentCandleIndex]?.toFixed(2) || 'N/A') : 'N/A'}</span>
                  </div>
                </div>
                
                <div className="nav-right">
                  <div className="replay-mode-toggle">
                    <label>
                      <input
                        type="checkbox"
                        checked={replayMode}
                        onChange={(e) => setReplayMode(e.target.checked)}
                        style={{ marginRight: '5px' }}
                      />
                      Replay Mode
                    </label>
                  </div>
                </div>
              </div>

              {/* Manual Trade Buttons */}
              <div className="manual-trade-controls">
                <button
                  onClick={() => addManualTrade('CALL')}
                  className="btn-manual-call"
                  disabled={currentCandleIndex < 0 || currentCandleIndex >= candlesData.length}
                >
                  <Plus size={16} style={{ marginRight: '5px' }} />
                  Add CALL Trade
                </button>
                <button
                  onClick={() => addManualTrade('PUT')}
                  className="btn-manual-put"
                  disabled={currentCandleIndex < 0 || currentCandleIndex >= candlesData.length}
                >
                  <Plus size={16} style={{ marginRight: '5px' }} />
                  Add PUT Trade
                </button>
              </div>

              {/* Algo Status Display */}
              {algoStatus && (
                <div className="algo-status-display">
                  <h4>Algo Status</h4>
                  <div className="status-info">
                    <span className="status-mode">{algoStatus.mode}</span>
                    {algoStatus.reason && <span className="status-reason">{algoStatus.reason}</span>}
                  </div>
                </div>
              )}

              {/* Chart */}
              {backtestResults.chartData && backtestResults.chartData.length > 0 && (
                <ChartComponent 
                  chartData={backtestResults.chartData}
                  trades={backtestResults.trades}
                  viewMode={viewMode}
                  currentIndex={currentCandleIndex}
                  manualTrades={manualTrades}
                  autoTrades={autoTrades}
                  visibleCandlesCount={visibleCandles}
                  replayMode={replayMode}
                />
              )}

              {/* All Trades PNL Summary */}
              {(() => {
                const pnlData = getAllTradesPNL()
                return (
                  <div className="all-trades-pnl">
                    <h3>All Trades PNL Summary</h3>
                    <div className="pnl-grid">
                      <div className="pnl-card">
                        <label>Total Trades</label>
                        <span className="pnl-value">{pnlData.totalTrades}</span>
                      </div>
                      <div className="pnl-card">
                        <label>Closed Trades</label>
                        <span className="pnl-value">{pnlData.closedTrades}</span>
                      </div>
                      <div className="pnl-card">
                        <label>Open Trades</label>
                        <span className="pnl-value">{pnlData.openTrades}</span>
                      </div>
                      <div className="pnl-card highlight">
                        <label>Total PNL</label>
                        <span className={`pnl-value ${pnlData.totalPNL >= 0 ? 'positive' : 'negative'}`}>
                          ₹{pnlData.totalPNL.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="pnl-card">
                        <label>Today Trades</label>
                        <span className="pnl-value">{pnlData.todayTrades} / {maxTradesPerDay}</span>
                      </div>
                      <div className="pnl-card">
                        <label>Today PNL</label>
                        <span className={`pnl-value ${pnlData.todayPNL >= 0 ? 'positive' : 'negative'}`}>
                          ₹{pnlData.todayPNL.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="pnl-card">
                        <label>Consecutive Losses</label>
                        <span className={`pnl-value ${pnlData.consecutiveLosses >= maxConsecutiveLosses ? 'negative' : ''}`}>
                          {pnlData.consecutiveLosses} / {maxConsecutiveLosses}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })()}

              {/* All Trades Table */}
              {(() => {
                const pnlData = getAllTradesPNL()
                return (
                  <div className="all-trades-table">
                    <h3>All Trades ({pnlData.allTrades.length})</h3>
                    <div className="table-container">
                      <table className="trades-table">
                        <thead>
                          <tr>
                            <th>#</th>
                            <th>Type</th>
                            <th>Entry Time</th>
                            <th>Entry Price</th>
                            <th>EMA15</th>
                            <th>EMA50</th>
                            <th>VWAP</th>
                            <th>Exit Time</th>
                            <th>Exit Price</th>
                            <th>Points</th>
                            <th>Exit Reason</th>
                            <th>PNL (₹)</th>
                            <th>Source</th>
                          </tr>
                        </thead>
                        <tbody>
                          {pnlData.allTrades.map((trade, index) => (
                            <tr key={trade.id || index} className={trade.pnl >= 0 ? 'trade-profit' : trade.pnl < 0 ? 'trade-loss' : ''}>
                              <td>{index + 1}</td>
                              <td>
                                <span className={`trade-type ${trade.type.toLowerCase()}`}>
                                  {trade.type}
                                </span>
                              </td>
                              <td>{new Date(trade.entryTime).toLocaleTimeString('en-IN')}</td>
                              <td>{trade.entryPrice.toFixed(2)}</td>
                              <td>{trade.ema15 ? trade.ema15.toFixed(2) : '-'}</td>
                              <td>{trade.ema50 ? trade.ema50.toFixed(2) : '-'}</td>
                              <td>{trade.vwap ? trade.vwap.toFixed(2) : '-'}</td>
                              <td>{trade.exitTime ? new Date(trade.exitTime).toLocaleTimeString('en-IN') : '-'}</td>
                              <td>{trade.exitPrice ? trade.exitPrice.toFixed(2) : '-'}</td>
                              <td>{trade.points ? trade.points.toFixed(2) : '-'}</td>
                              <td>
                                {trade.exitReason ? (
                                  <span className={`exit-reason ${trade.exitReason.toLowerCase()}`}>
                                    {trade.exitReason}
                                  </span>
                                ) : (
                                  <span className="exit-reason open">OPEN</span>
                                )}
                              </td>
                              <td className={trade.pnl !== null ? (trade.pnl >= 0 ? 'positive' : 'negative') : ''}>
                                {trade.pnl !== null ? `₹${trade.pnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}
                              </td>
                              <td>
                                <span className={`trade-source ${trade.isManual ? 'manual' : 'auto'}`}>
                                  {trade.isManual ? 'Manual' : 'Auto'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )
              })()}
            </div>
          )}
        </div>
      </div>

      <style>{`
        .algo-container {
          padding: 20px;
        }
        .card {
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          overflow: hidden;
        }
        .card-header {
          padding: 20px;
          background: #333;
          color: white;
        }
        .card-header h2 {
          margin: 0 0 5px 0;
          font-size: 24px;
        }
        .card-header p {
          margin: 0;
          opacity: 0.9;
          font-size: 14px;
        }
        .visible-candles-control {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .visible-candles-control label {
          font-weight: 600;
          color: #333;
          font-size: 13px;
        }
        .card-body {
          padding: 20px;
        }
        .controls-section {
          padding: 20px;
          background: #f8f9fa;
        }
        .control-group {
          display: flex;
          flex-direction: column;
          gap: 5px;
          margin-bottom: 15px;
        }
        .control-group label {
          font-size: 12px;
          font-weight: 600;
          color: #333;
          display: flex;
          align-items: center;
        }
        .form-textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          resize: vertical;
          font-family: 'Courier New', monospace;
        }
        .form-textarea:focus {
          outline: none;
          border-color: #007bff;
        }
        .controls-row {
          display: flex;
          flex-wrap: wrap;
          gap: 15px;
          align-items: flex-end;
        }
        .form-input {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          min-width: 150px;
        }
        .form-input:focus {
          outline: none;
          border-color: #007bff;
        }
        .button-group {
          display: flex;
          gap: 10px;
          margin-top: 20px;
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
          background: #ccc;
          cursor: not-allowed;
        }
        .btn-secondary {
          background: #6c757d;
          color: white;
        }
        .btn-secondary:hover:not(:disabled) {
          background: #5a6268;
        }
        .error-message {
          padding: 12px;
          margin: 0 20px 20px 20px;
          background: #f8d7da;
          color: #721c24;
          border-radius: 4px;
        }
        .results-section {
          padding: 20px;
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
        .chart-container {
          margin-bottom: 30px;
          padding: 20px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .chart-container h3 {
          margin: 0 0 15px 0;
          color: #333;
        }
        .trades-section {
          margin-top: 30px;
        }
        .trades-section h3 {
          margin-bottom: 15px;
          color: #333;
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
        .trades-table thead {
          background: #333;
          color: white;
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
        .trades-table tbody tr.trade-profit {
          background: #d4edda;
        }
        .trades-table tbody tr.trade-loss {
          background: #f8d7da;
        }
        .trade-type {
          padding: 4px 8px;
          border-radius: 4px;
          font-weight: 600;
          font-size: 11px;
        }
        .trade-type.call {
          background: #28a745;
          color: white;
        }
        .trade-type.put {
          background: #dc3545;
          color: white;
        }
        .exit-reason {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          display: inline-block;
        }
        .exit-reason.tp {
          background: #28a745;
          color: white;
        }
        .exit-reason.sl {
          background: #dc3545;
          color: white;
        }
        .exit-reason.eod {
          background: #6c757d;
          color: white;
        }
        .exit-reason.ema_exit {
          background: #f59e0b;
          color: white;
        }
        .exit-reason.time_exit {
          background: #6366f1;
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
        .spinning {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .mode-toggle {
          display: flex;
          gap: 10px;
          margin: 20px;
          padding: 10px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .mode-btn {
          flex: 1;
          padding: 12px 20px;
          border: 2px solid #ddd;
          border-radius: 6px;
          background: white;
          cursor: pointer;
          font-weight: 600;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s;
        }
        .mode-btn:hover {
          border-color: #007bff;
          background: #f0f7ff;
        }
        .mode-btn.active {
          background: #007bff;
          color: white;
          border-color: #007bff;
        }
        .chart-view-section {
          padding: 20px;
        }
        .chart-nav-controls {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }
        .nav-left {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .nav-right {
          display: flex;
          align-items: center;
        }
        .btn-play {
          padding: 10px 20px;
          border: 2px solid #10b981;
          border-radius: 6px;
          background: #10b981;
          color: white;
          cursor: pointer;
          font-weight: 600;
          display: flex;
          align-items: center;
          transition: all 0.3s;
        }
        .btn-play:hover:not(:disabled) {
          background: #059669;
          border-color: #059669;
        }
        .btn-play.playing {
          background: #ef4444;
          border-color: #ef4444;
        }
        .btn-play.playing:hover:not(:disabled) {
          background: #dc2626;
          border-color: #dc2626;
        }
        .btn-play:disabled {
          background: #ccc;
          border-color: #ccc;
          cursor: not-allowed;
        }
        .replay-mode-toggle {
          display: flex;
          align-items: center;
          padding: 8px 12px;
          background: white;
          border-radius: 6px;
          border: 1px solid #ddd;
        }
        .replay-mode-toggle label {
          display: flex;
          align-items: center;
          cursor: pointer;
          font-weight: 600;
          font-size: 13px;
          color: #333;
          margin: 0;
        }
        .replay-mode-toggle input[type="checkbox"] {
          cursor: pointer;
        }
        .btn-nav {
          padding: 10px 20px;
          border: 2px solid #007bff;
          border-radius: 6px;
          background: #007bff;
          color: white;
          cursor: pointer;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: all 0.3s;
        }
        .btn-nav:hover:not(:disabled) {
          background: #0056b3;
          border-color: #0056b3;
        }
        .btn-nav:disabled {
          background: #ccc;
          border-color: #ccc;
          cursor: not-allowed;
        }
        .candle-info {
          display: flex;
          gap: 30px;
          flex-wrap: wrap;
          flex: 1;
          justify-content: center;
        }
        .info-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .info-item label {
          font-weight: 600;
          color: #666;
          font-size: 13px;
        }
        .info-item span {
          font-weight: bold;
          color: #333;
          font-size: 14px;
        }
        .manual-trade-controls {
          display: flex;
          gap: 15px;
          margin-bottom: 20px;
          justify-content: center;
        }
        .btn-manual-call {
          padding: 12px 24px;
          border: 2px solid #10b981;
          border-radius: 6px;
          background: #10b981;
          color: white;
          cursor: pointer;
          font-weight: 600;
          display: flex;
          align-items: center;
          transition: all 0.3s;
        }
        .btn-manual-call:hover:not(:disabled) {
          background: #059669;
          border-color: #059669;
        }
        .btn-manual-put {
          padding: 12px 24px;
          border: 2px solid #ef4444;
          border-radius: 6px;
          background: #ef4444;
          color: white;
          cursor: pointer;
          font-weight: 600;
          display: flex;
          align-items: center;
          transition: all 0.3s;
        }
        .btn-manual-put:hover:not(:disabled) {
          background: #dc2626;
          border-color: #dc2626;
        }
        .btn-manual-call:disabled,
        .btn-manual-put:disabled {
          background: #ccc;
          border-color: #ccc;
          cursor: not-allowed;
        }
        .chart-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
          padding: 10px;
          background: #f8f9fa;
          border-radius: 6px;
        }
        .zoom-controls {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .btn-icon {
          padding: 6px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          transition: all 0.2s;
        }
        .btn-icon:hover {
          background: #f0f0f0;
          border-color: #007bff;
        }
        .zoom-value {
          font-weight: 600;
          color: #333;
          min-width: 50px;
          text-align: center;
        }
        .btn-reset {
          padding: 6px 12px;
          border: 1px solid #6c757d;
          border-radius: 4px;
          background: #6c757d;
          color: white;
          cursor: pointer;
          font-size: 12px;
          font-weight: 600;
        }
        .btn-reset:hover {
          background: #5a6268;
        }
        .chart-wrapper {
          position: relative;
          overflow: hidden;
          border-radius: 8px;
        }
        .all-trades-pnl {
          margin-top: 30px;
          padding: 20px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .all-trades-pnl h3 {
          margin: 0 0 15px 0;
          color: #333;
        }
        .pnl-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }
        .pnl-card {
          padding: 20px;
          background: white;
          border-radius: 8px;
          text-align: center;
          border: 2px solid #e5e7eb;
        }
        .pnl-card.highlight {
          border-color: #007bff;
          background: #f0f7ff;
        }
        .pnl-card label {
          display: block;
          font-size: 13px;
          color: #666;
          margin-bottom: 10px;
          font-weight: 600;
        }
        .pnl-value {
          display: block;
          font-size: 24px;
          font-weight: bold;
          color: #333;
        }
        .pnl-value.positive {
          color: #10b981;
        }
        .pnl-value.negative {
          color: #ef4444;
        }
        .all-trades-table {
          margin-top: 30px;
        }
        .all-trades-table h3 {
          margin-bottom: 15px;
          color: #333;
        }
        .trade-source {
          padding: 4px 8px;
          border-radius: 4px;
          font-weight: 600;
          font-size: 11px;
        }
        .trade-source.manual {
          background: #fef3c7;
          color: #92400e;
        }
        .trade-source.auto {
          background: #dbeafe;
          color: #1e40af;
        }
        .exit-reason.open {
          background: #f3f4f6;
          color: #374151;
        }
        .algo-status-display {
          padding: 15px;
          margin-bottom: 20px;
          background: #f0f7ff;
          border-radius: 8px;
          border-left: 4px solid #007bff;
        }
        .algo-status-display h4 {
          margin: 0 0 10px 0;
          color: #333;
          font-size: 16px;
        }
        .status-info {
          display: flex;
          gap: 15px;
          align-items: center;
        }
        .status-mode {
          padding: 6px 12px;
          background: #007bff;
          color: white;
          border-radius: 4px;
          font-weight: 600;
          font-size: 13px;
        }
        .status-reason {
          color: #666;
          font-size: 13px;
        }
      `}</style>
    </div>
  )
}

export default Algo1MinV2

