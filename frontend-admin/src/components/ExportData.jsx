import React, { useState } from 'react'
import axios from 'axios'
import { Download, RefreshCw, Calendar, Clock } from 'lucide-react'
import { API_BASE } from '../config'

const ExportData = () => {
  // Symbol mapping from option chain names to Yahoo Finance symbols
  const symbolMapping = {
    'banknifty': '^NSEBANK',
    'nifty': '^NSEI',
    'finnifty': '^NSEI', // Use NIFTY as fallback, or find correct symbol
    'midcpnifty': '^NSEI', // Use NIFTY as fallback, or find correct symbol
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

  const [selectedChain, setSelectedChain] = useState('banknifty')
  const [selectedDate, setSelectedDate] = useState('')
  const [selectedTime, setSelectedTime] = useState('09:45')
  const [loading, setLoading] = useState(false)
  const [exportData, setExportData] = useState(null)
  const [error, setError] = useState(null)

  // Set today's date as default
  React.useEffect(() => {
    const today = new Date().toISOString().split('T')[0]
    setSelectedDate(today)
  }, [])

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
          ceOIChange: parseFloat(ce.changeinOpenInterest || ce.changein_open_interest || ce.change_in_oi || ce.chngInOI || ce.changeinOI || 0) || 0,
          peOIChange: parseFloat(pe.changeinOpenInterest || pe.changein_open_interest || pe.change_in_oi || pe.chngInOI || pe.changeinOI || 0) || 0,
          ceIV: parseFloat(ce.impliedVolatility || ce.implied_volatility || ce.iv || ce.ImpliedVolatility || 0) || 0,
          peIV: parseFloat(pe.impliedVolatility || pe.implied_volatility || pe.iv || pe.ImpliedVolatility || 0) || 0,
          ceLTP: parseFloat(ce.lastPrice || ce.last_price || ce.ltp || ce.LastPrice || 0) || 0,
          peLTP: parseFloat(pe.lastPrice || pe.last_price || pe.ltp || pe.LastPrice || 0) || 0
        }
      })
      .filter((item) => item.strike > 0)
      .sort((a, b) => a.strike - b.strike)
  }

  const calculateATMStrike = (underlyingValue, optionData) => {
    if (!underlyingValue || !optionData || optionData.length === 0) return null

    let atmStrike = null
    let minDiff = Infinity

    optionData.forEach((s) => {
      const diff = Math.abs(s.strike - underlyingValue)
      if (diff < minDiff) {
        minDiff = diff
        atmStrike = s.strike
      }
    })

    return atmStrike
  }

  const getStrikeInterval = () => {
    if (selectedChain === 'banknifty') return 100
    if (selectedChain === 'nifty') return 50
    if (selectedChain === 'finnifty') return 50
    if (selectedChain === 'midcpnifty') return 50
    return 100
  }


  const findRecordByTime = (data, targetTime) => {
    if (!data || data.length === 0) return null

    const [targetHour, targetMinute] = targetTime.split(':').map(Number)
    let closestRecord = null
    let minDiff = Infinity

    data.forEach((record) => {
      const timestamp = record?.records?.timestamp || record?.timestamp || record?.insertedAt
      if (!timestamp) return

      try {
        const recordDate = new Date(timestamp)
        const recordHour = recordDate.getHours()
        const recordMinute = recordDate.getMinutes()
        const recordTimeInMinutes = recordHour * 60 + recordMinute
        const targetTimeInMinutes = targetHour * 60 + targetMinute

        // Find record at or before target time
        if (recordTimeInMinutes <= targetTimeInMinutes) {
          const diff = targetTimeInMinutes - recordTimeInMinutes
          if (diff < minDiff) {
            minDiff = diff
            closestRecord = record
          }
        }
      } catch (e) {
        // Skip invalid timestamps
      }
    })

    return closestRecord
  }

  const getPastRecords = (data, targetRecord, count = 4) => {
    if (!data || !targetRecord) return []

    const targetIndex = data.findIndex(r => r._id === targetRecord._id)
    if (targetIndex === -1) return []

    const startIndex = Math.max(0, targetIndex - count)
    return data.slice(startIndex, targetIndex).reverse() // Reverse to get chronological order
  }

  const getStrikesAroundATM = (atmStrike, optionData, strikesUp = 2, strikesDown = 2) => {
    if (!atmStrike || !optionData || optionData.length === 0) return []

    const interval = getStrikeInterval()
    const strikes = [atmStrike]

    // Get strikes above ATM
    for (let i = 1; i <= strikesUp; i++) {
      const targetStrike = atmStrike + (i * interval)
      const strikeData = optionData.find(s => s.strike === targetStrike)
      if (strikeData) {
        strikes.push(targetStrike)
      }
    }

    // Get strikes below ATM
    for (let i = 1; i <= strikesDown; i++) {
      const targetStrike = atmStrike - (i * interval)
      const strikeData = optionData.find(s => s.strike === targetStrike)
      if (strikeData) {
        strikes.push(targetStrike)
      }
    }

    return strikes.sort((a, b) => a - b)
  }

  const fetchExportData = async () => {
    if (!selectedDate || !selectedTime) {
      setError('Please select both date and time')
      return
    }

    setLoading(true)
    setError(null)
    setExportData(null)

    try {
      // 1. Fetch option chain data for the selected date
      const optionChainUrl = `${API_BASE}/${selectedChain}/data?start_date=${selectedDate}&end_date=${selectedDate}&limit=1000&full=true`
      const optionChainResponse = await axios.get(optionChainUrl)
      const optionChainData = optionChainResponse.data.data || optionChainResponse.data || []

      if (optionChainData.length === 0) {
        setError(`No data found for ${selectedChain} on ${selectedDate}`)
        setLoading(false)
        return
      }

      // Sort by timestamp
      const sortedData = optionChainData.sort((a, b) => {
        const dateA = new Date(a.insertedAt || a.records?.timestamp || a.timestamp || a.date || a.createdAt || 0)
        const dateB = new Date(b.insertedAt || b.records?.timestamp || b.timestamp || b.date || b.createdAt || 0)
        return dateA - dateB
      })

      // 2. Find record at selected time
      const targetRecord = findRecordByTime(sortedData, selectedTime)
      if (!targetRecord) {
        setError(`No data found for ${selectedChain} at ${selectedTime} on ${selectedDate}`)
        setLoading(false)
        return
      }

      // 3. Extract option chain data from target record
      const optData = extractOptionChainData(targetRecord)
      const underlyingValue = targetRecord?.records?.underlyingValue || targetRecord?.underlyingValue || 0
      
      // Try multiple locations for expiry date
      let expiry = null
      if (targetRecord?.records?.expiry) {
        expiry = targetRecord.records.expiry
      } else if (targetRecord?.expiry) {
        expiry = targetRecord.expiry
      } else if (targetRecord?.records?.data && Array.isArray(targetRecord.records.data) && targetRecord.records.data.length > 0) {
        // Try to get expiry from first option chain item
        // Check expiryDates (plural) first, then other variations
        const firstItem = targetRecord.records.data[0]
        expiry = firstItem?.expiryDates || firstItem?.expiryDate || firstItem?.expiry || firstItem?.expiry_date || null
      } else if (optData.length > 0) {
        // Try to get expiry from extracted option data
        const firstOpt = optData[0]
        expiry = firstOpt?.expiryDates || firstOpt?.expiry || firstOpt?.expiryDate || firstOpt?.expiry_date || null
      }
      
      // If still no expiry, try to get from all records (check previous records too)
      if (!expiry && sortedData.length > 0) {
        for (const record of sortedData) {
          const recExpiry = record?.records?.expiry || record?.expiry
          if (recExpiry && recExpiry !== 'N/A' && !recExpiry.includes('_expiry') && !recExpiry.includes('isoformat')) {
            expiry = recExpiry
            break
          }
        }
      }
      
      // If still no expiry, try to fetch from backend API
      if (!expiry || expiry === 'N/A' || expiry.includes('_expiry')) {
        try {
          // Try to get expiry from option chain expiry endpoint (for NIFTY)
          if (selectedChain === 'nifty') {
            const expiryUrl = `${API_BASE}/option-chain/expiry`
            const expiryResponse = await axios.get(expiryUrl)
            if (expiryResponse.data.success && expiryResponse.data.expiry) {
              expiry = expiryResponse.data.expiry
            }
          }
        } catch (e) {
          console.warn('Could not fetch expiry from API:', e)
        }
      }

      if (optData.length === 0 || !underlyingValue) {
        setError('Invalid option chain data in target record')
        setLoading(false)
        return
      }

      // 4. Calculate ATM strike
      const atmStrike = calculateATMStrike(underlyingValue, optData)
      if (!atmStrike) {
        setError('Could not determine ATM strike')
        setLoading(false)
        return
      }

      // 5. Get ATM strike data for latest snapshot
      const atmStrikeData = optData.find(s => s.strike === atmStrike)
      const targetTimestamp = targetRecord?.records?.timestamp || targetRecord?.timestamp || targetRecord?.insertedAt
      const latestTime = targetTimestamp ? new Date(targetTimestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) : selectedTime
      
      const latestSnapshot = {
        time: latestTime,
        ce: {
          oi: atmStrikeData?.ceOI || 0,
          oi_change: atmStrikeData?.ceOIChange || 0,
          price: atmStrikeData?.ceLTP || 0
        },
        pe: {
          oi: atmStrikeData?.peOI || 0,
          oi_change: atmStrikeData?.peOIChange || 0,
          price: atmStrikeData?.peLTP || 0
        }
      }

      // 6. Get previous record for comparison (for derived metrics)
      const pastRecordsForComparison = getPastRecords(sortedData, targetRecord, 1)
      let previousSnapshot = null
      
      if (pastRecordsForComparison.length > 0) {
        const previousRecord = pastRecordsForComparison[0]
        const prevOptData = extractOptionChainData(previousRecord)
        const prevUnderlying = previousRecord?.records?.underlyingValue || previousRecord?.underlyingValue || 0
        const prevATM = calculateATMStrike(prevUnderlying, prevOptData)
        
        if (prevATM) {
          const prevATMStrikeData = prevOptData.find(s => s.strike === prevATM)
          const prevTimestamp = previousRecord?.records?.timestamp || previousRecord?.timestamp || previousRecord?.insertedAt
          const prevTime = prevTimestamp ? new Date(prevTimestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) : null
          
          previousSnapshot = {
            time: prevTime || 'N/A',
            ce: {
              oi: prevATMStrikeData?.ceOI || 0,
              oi_change: prevATMStrikeData?.ceOIChange || 0,
              price: prevATMStrikeData?.ceLTP || 0
            },
            pe: {
              oi: prevATMStrikeData?.peOI || 0,
              oi_change: prevATMStrikeData?.peOIChange || 0,
              price: prevATMStrikeData?.peLTP || 0
            }
          }
        }
      }

      // 7. Get 20 past records with OI data for ATM ± 3 strikes
      const pastRecordsForOI = getPastRecords(sortedData, targetRecord, 20)
      const pastOIData = []
      
      for (const pastRecord of pastRecordsForOI) {
        const pastOptData = extractOptionChainData(pastRecord)
        const pastUnderlying = pastRecord?.records?.underlyingValue || pastRecord?.underlyingValue || 0
        const pastATM = calculateATMStrike(pastUnderlying, pastOptData)
        
        if (pastATM && pastOptData.length > 0) {
          // Get strikes: ATM ± 3
          const strikesToInclude = getStrikesAroundATM(pastATM, pastOptData, 3, 3)
          
          const strikeData = []
          for (const strike of strikesToInclude) {
            const strikeInfo = pastOptData.find(s => s.strike === strike)
            if (strikeInfo) {
              strikeData.push({
                strike: strike,
                ce: {
                  oi: strikeInfo.ceOI || 0,
                  oi_change: strikeInfo.ceOIChange || 0,
                  price: strikeInfo.ceLTP || 0,
                  iv: strikeInfo.ceIV || 0
                },
                pe: {
                  oi: strikeInfo.peOI || 0,
                  oi_change: strikeInfo.peOIChange || 0,
                  price: strikeInfo.peLTP || 0,
                  iv: strikeInfo.peIV || 0
                }
              })
            }
          }
          
          const pastTimestamp = pastRecord?.records?.timestamp || pastRecord?.timestamp || pastRecord?.insertedAt
          const pastTime = pastTimestamp ? new Date(pastTimestamp).toISOString() : null
          
          if (strikeData.length > 0 && pastTime) {
            pastOIData.push({
              time: pastTime,
              spot_price: pastUnderlying,
              atm_strike: pastATM,
              strikes: strikeData
            })
          }
        }
      }

      // 8. Calculate derived metrics
      let derived = {}
      if (previousSnapshot) {
        const latestTime = new Date(targetRecord?.records?.timestamp || targetRecord?.timestamp || targetRecord?.insertedAt)
        const previousTime = new Date(pastRecordsForComparison[0]?.records?.timestamp || pastRecordsForComparison[0]?.timestamp || pastRecordsForComparison[0]?.insertedAt)
        const deltaMinutes = (latestTime - previousTime) / (1000 * 60)
        
        const ceOIDelta = latestSnapshot.ce.oi - previousSnapshot.ce.oi
        const peOIDelta = latestSnapshot.pe.oi - previousSnapshot.pe.oi
        const cePriceDelta = latestSnapshot.ce.price - previousSnapshot.ce.price
        const pePriceDelta = latestSnapshot.pe.price - previousSnapshot.pe.price
        
        // Determine OI signal (CORRECTED LOGIC)
        // CE OI ↑, PE OI ↓ = Put unwinding (bullish)
        // CE OI ↓, PE OI ↑ = Call unwinding (bearish)
        // CE OI ↓, PE OI ↓ = Short covering
        // CE OI ↑, PE OI ↑ = Writing / range
        let oiSignal = 'neutral'
        if (ceOIDelta > 0 && peOIDelta < 0) {
          oiSignal = 'put_unwinding'  // Bullish
        } else if (ceOIDelta < 0 && peOIDelta > 0) {
          oiSignal = 'call_unwinding'  // Bearish
        } else if (ceOIDelta < 0 && peOIDelta < 0) {
          oiSignal = 'short_covering'
        } else if (ceOIDelta > 0 && peOIDelta > 0) {
          oiSignal = 'writing_range'
        }
        
        // OI divergence: when OI changes in opposite directions
        const oiDivergence = (ceOIDelta > 0 && peOIDelta < 0) || (ceOIDelta < 0 && peOIDelta > 0)
        
        // Pressure bias: neutral for short covering (both OI decreasing)
        // Direction should come from price/VWAP, not OI
        let pressureBias = 'neutral'
        if (ceOIDelta < 0 && peOIDelta < 0) {
          // Short covering on both sides - direction comes from price, not OI
          pressureBias = 'neutral'
        } else {
          // For other scenarios, can use OI ratio but prefer neutral
          // Let price action determine direction
          pressureBias = 'neutral'
        }
        
        // Calculate signal_strength
        // signal_strength = normalize(|ce_oi_delta| + |pe_oi_delta|) × normalize(|ce_price_delta| + |pe_price_delta|) × (1 / delta_minutes)
        // Normalization: divide by max possible value (using reasonable max values)
        const maxOIDelta = 100000  // Reasonable max OI delta
        const maxPriceDelta = 1000  // Reasonable max price delta
        
        const absOIDelta = Math.abs(ceOIDelta) + Math.abs(peOIDelta)
        const absPriceDelta = Math.abs(cePriceDelta) + Math.abs(pePriceDelta)
        
        // Use logarithmic normalization to ensure non-zero values
        // This prevents zero values while still scaling properly
        const normalizedOIDelta = Math.max(0.01, Math.min(absOIDelta / maxOIDelta, 1))
        const normalizedPriceDelta = Math.max(0.01, Math.min(absPriceDelta / maxPriceDelta, 1))
        const timeFactor = deltaMinutes > 0 ? Math.max(0.01, 1 / deltaMinutes) : 0.01
        
        // Calculate base strength
        let signalStrength = normalizedOIDelta * normalizedPriceDelta * timeFactor
        
        // Ensure signal_strength is never zero (minimum 0.01)
        signalStrength = Math.max(0.01, signalStrength)
        
        // Round to 2 decimal places
        signalStrength = Math.round(signalStrength * 100) / 100
        
        // Calculate valid_for_scalping
        // Rule: delta_minutes <= 5 AND abs(ce_oi_delta + pe_oi_delta) > threshold
        const oiDeltaThreshold = 1000  // Threshold for significant OI change
        const totalOIDelta = Math.abs(ceOIDelta + peOIDelta)
        const validForScalping = deltaMinutes <= 5 && totalOIDelta > oiDeltaThreshold
        
        derived = {
          delta_minutes: Math.round(deltaMinutes * 10) / 10,
          ce_oi_delta: ceOIDelta,
          pe_oi_delta: peOIDelta,
          ce_price_delta: Math.round(cePriceDelta * 100) / 100,
          pe_price_delta: Math.round(pePriceDelta * 100) / 100,
          oi_signal: oiSignal,
          oi_divergence: oiDivergence,
          pressure_bias: pressureBias,
          signal_strength: signalStrength,
          valid_for_scalping: validForScalping
        }
      }

      // 9. Format timestamp for prediction_time (with timezone offset)
      const predictionTime = targetTimestamp ? new Date(targetTimestamp).toISOString() : new Date().toISOString()

      // 10. Get symbol name (uppercase)
      const symbolName = selectedChain.toUpperCase()

      // 11. Fetch Yahoo Finance OHLC data
      // Past day: 9:15 to 15:30 (full trading day)
      // Current day: 9:15 to selected time
      let ohlcData = null
      const yahooSymbol = symbolMapping[selectedChain]
      if (yahooSymbol) {
        try {
          // Calculate previous day
          const selectedDateObj = new Date(selectedDate)
          const previousDate = new Date(selectedDateObj)
          previousDate.setDate(previousDate.getDate() - 1)
          const previousDateStr = previousDate.toISOString().split('T')[0]
          
          // Fetch past day data (9:15 to 15:30)
          const pastDayUrl = `${API_BASE}/yahoo-finance/ohlc?symbol=${encodeURIComponent(yahooSymbol)}&date=${previousDateStr}&past_day=true`
          const pastDayResponse = await axios.get(pastDayUrl)
          
          // Fetch current day data (9:15 to selected time)
          const currentDayUrl = `${API_BASE}/yahoo-finance/ohlc?symbol=${encodeURIComponent(yahooSymbol)}&date=${selectedDate}&end_time=${selectedTime}`
          const currentDayResponse = await axios.get(currentDayUrl)
          
          if (pastDayResponse.data.success && currentDayResponse.data.success) {
            ohlcData = {
              past_day: {
                date: previousDateStr,
                time_range: "09:15-15:30",
                '5min': pastDayResponse.data.data['5min'] || [],
                '15min': pastDayResponse.data.data['15min'] || []
              },
              current_day: {
                date: selectedDate,
                time_range: `09:15-${selectedTime}`,
                '5min': currentDayResponse.data.data['5min'] || [],
                '15min': currentDayResponse.data.data['15min'] || []
              }
            }
          } else if (currentDayResponse.data.success) {
            // If past day fails, at least include current day
            ohlcData = {
              current_day: {
                date: selectedDate,
                time_range: `09:15-${selectedTime}`,
                '5min': currentDayResponse.data.data['5min'] || [],
                '15min': currentDayResponse.data.data['15min'] || []
              }
            }
          }
        } catch (e) {
          console.warn('Could not fetch Yahoo Finance OHLC data:', e)
          // Continue without OHLC data
        }
      }

      // 12. Build export data structure matching the required format
      const completeData = {
        option_chain_context: {
          symbol: symbolName,
          prediction_time: predictionTime,
          expiry: expiry || 'N/A',
          spot: {
            price: underlyingValue,
            atm_strike: atmStrike
          },
          snapshots: {
            latest: latestSnapshot,
            ...(previousSnapshot ? { previous: previousSnapshot } : {})
          },
          ...(Object.keys(derived).length > 0 ? { derived } : {}),
          ...(ohlcData ? { ohlc: ohlcData } : {}),
          ...(pastOIData.length > 0 ? { past_oi_data: pastOIData } : {})
        }
      }

      setExportData(completeData)
    } catch (error) {
      console.error('Error fetching export data:', error)
      setError('Error fetching data: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  const downloadJSON = () => {
    if (!exportData) return

    const dataStr = JSON.stringify(exportData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `export_${selectedChain}_${selectedDate}_${selectedTime.replace(':', '')}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const formatNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-'
    return num.toLocaleString('en-IN', { maximumFractionDigits: 2 })
  }

  return (
    <div className="export-data-container">
      <div className="card">
        <div className="card-header">
          <h2>Export Data</h2>
        </div>

        <div className="export-controls">
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
              <Clock size={16} style={{ marginRight: '5px' }} />
              Time:
            </label>
            <input
              type="time"
              value={selectedTime}
              onChange={(e) => setSelectedTime(e.target.value)}
              className="form-input"
            />
          </div>

          <button
            onClick={fetchExportData}
            className="btn btn-primary"
            disabled={loading || !selectedDate || !selectedTime}
          >
            {loading ? (
              <>
                <RefreshCw size={16} className="spinning" style={{ marginRight: '5px' }} />
                Loading...
              </>
            ) : (
              <>
                <RefreshCw size={16} style={{ marginRight: '5px' }} />
                Fetch Data
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {exportData && (
          <div className="export-results">
            <div className="results-header">
              <h3>Export Data Preview</h3>
              <button onClick={downloadJSON} className="btn btn-success">
                <Download size={16} style={{ marginRight: '5px' }} />
                Download JSON
              </button>
            </div>

            <div className="data-summary">
              <div className="summary-item">
                <label>Symbol:</label>
                <span>{exportData.option_chain_context.symbol}</span>
              </div>
              <div className="summary-item">
                <label>Date:</label>
                <span>{selectedDate}</span>
              </div>
              <div className="summary-item">
                <label>Time:</label>
                <span>{selectedTime}</span>
              </div>
              <div className="summary-item">
                <label>Expiry:</label>
                <span>{exportData.option_chain_context.expiry}</span>
              </div>
              <div className="summary-item">
                <label>Spot Price:</label>
                <span>₹{formatNumber(exportData.option_chain_context.spot.price)}</span>
              </div>
              <div className="summary-item">
                <label>ATM Strike:</label>
                <span>{formatNumber(exportData.option_chain_context.spot.atm_strike)}</span>
              </div>
              {exportData.option_chain_context.derived && (
                <>
                  <div className="summary-item">
                    <label>OI Signal:</label>
                    <span>{exportData.option_chain_context.derived.oi_signal}</span>
                  </div>
                  <div className="summary-item">
                    <label>Pressure Bias:</label>
                    <span>{exportData.option_chain_context.derived.pressure_bias}</span>
                  </div>
                </>
              )}
            </div>

            {/* Latest Snapshot */}
            <div className="data-section">
              <h4>Latest Snapshot (ATM Strike)</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Type</th>
                      <th>OI</th>
                      <th>OI Change</th>
                      <th>Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td rowSpan="2"><strong>{exportData.option_chain_context.snapshots.latest.time}</strong></td>
                      <td><strong>CE (Call)</strong></td>
                      <td>{formatNumber(exportData.option_chain_context.snapshots.latest.ce.oi)}</td>
                      <td>{formatNumber(exportData.option_chain_context.snapshots.latest.ce.oi_change)}</td>
                      <td>₹{formatNumber(exportData.option_chain_context.snapshots.latest.ce.price)}</td>
                    </tr>
                    <tr>
                      <td><strong>PE (Put)</strong></td>
                      <td>{formatNumber(exportData.option_chain_context.snapshots.latest.pe.oi)}</td>
                      <td>{formatNumber(exportData.option_chain_context.snapshots.latest.pe.oi_change)}</td>
                      <td>₹{formatNumber(exportData.option_chain_context.snapshots.latest.pe.price)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Previous Snapshot */}
            {exportData.option_chain_context.snapshots.previous && (
              <div className="data-section">
                <h4>Previous Snapshot (ATM Strike)</h4>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Type</th>
                        <th>OI</th>
                        <th>OI Change</th>
                        <th>Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td rowSpan="2"><strong>{exportData.option_chain_context.snapshots.previous.time}</strong></td>
                        <td><strong>CE (Call)</strong></td>
                        <td>{formatNumber(exportData.option_chain_context.snapshots.previous.ce.oi)}</td>
                        <td>{formatNumber(exportData.option_chain_context.snapshots.previous.ce.oi_change)}</td>
                        <td>₹{formatNumber(exportData.option_chain_context.snapshots.previous.ce.price)}</td>
                      </tr>
                      <tr>
                        <td><strong>PE (Put)</strong></td>
                        <td>{formatNumber(exportData.option_chain_context.snapshots.previous.pe.oi)}</td>
                        <td>{formatNumber(exportData.option_chain_context.snapshots.previous.pe.oi_change)}</td>
                        <td>₹{formatNumber(exportData.option_chain_context.snapshots.previous.pe.price)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Derived Metrics */}
            {exportData.option_chain_context.derived && (
              <div className="data-section">
                <h4>Derived Metrics</h4>
                <div className="derived-metrics">
                  <div className="metric-item">
                    <label>Delta Minutes:</label>
                    <span>{exportData.option_chain_context.derived.delta_minutes}</span>
                  </div>
                  <div className="metric-item">
                    <label>CE OI Delta:</label>
                    <span>{formatNumber(exportData.option_chain_context.derived.ce_oi_delta)}</span>
                  </div>
                  <div className="metric-item">
                    <label>PE OI Delta:</label>
                    <span>{formatNumber(exportData.option_chain_context.derived.pe_oi_delta)}</span>
                  </div>
                  <div className="metric-item">
                    <label>CE Price Delta:</label>
                    <span>₹{formatNumber(exportData.option_chain_context.derived.ce_price_delta)}</span>
                  </div>
                  <div className="metric-item">
                    <label>PE Price Delta:</label>
                    <span>₹{formatNumber(exportData.option_chain_context.derived.pe_price_delta)}</span>
                  </div>
                  <div className="metric-item">
                    <label>OI Signal:</label>
                    <span className="signal-badge">{exportData.option_chain_context.derived.oi_signal}</span>
                  </div>
                  <div className="metric-item">
                    <label>OI Divergence:</label>
                    <span>{exportData.option_chain_context.derived.oi_divergence ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="metric-item">
                    <label>Pressure Bias:</label>
                    <span className={`bias-badge ${exportData.option_chain_context.derived.pressure_bias}`}>
                      {exportData.option_chain_context.derived.pressure_bias}
                    </span>
                  </div>
                  <div className="metric-item">
                    <label>Signal Strength:</label>
                    <span className="signal-strength">{exportData.option_chain_context.derived.signal_strength}</span>
                  </div>
                  <div className="metric-item">
                    <label>Valid for Scalping:</label>
                    <span className={exportData.option_chain_context.derived.valid_for_scalping ? 'valid-badge' : 'invalid-badge'}>
                      {exportData.option_chain_context.derived.valid_for_scalping ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Past OI Data */}
            {exportData.option_chain_context.past_oi_data && exportData.option_chain_context.past_oi_data.length > 0 && (
              <div className="data-section">
                <h4>Past OI Data ({exportData.option_chain_context.past_oi_data.length} records)</h4>
                <div className="past-oi-summary">
                  <p>Showing OI data for ATM ± 3 strikes for the past {exportData.option_chain_context.past_oi_data.length} records</p>
                </div>
                <div className="table-container" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Spot</th>
                        <th>ATM</th>
                        <th>Strikes</th>
                        <th>CE OI</th>
                        <th>PE OI</th>
                        <th>CE ΔOI</th>
                        <th>PE ΔOI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {exportData.option_chain_context.past_oi_data.map((record, idx) => {
                        const timeStr = new Date(record.time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
                        const totalCEOI = record.strikes.reduce((sum, s) => sum + (s.ce.oi || 0), 0)
                        const totalPEOI = record.strikes.reduce((sum, s) => sum + (s.pe.oi || 0), 0)
                        const totalCEOIChange = record.strikes.reduce((sum, s) => sum + (s.ce.oi_change || 0), 0)
                        const totalPEOIChange = record.strikes.reduce((sum, s) => sum + (s.pe.oi_change || 0), 0)
                        const strikesStr = record.strikes.map(s => s.strike).join(', ')
                        
                        return (
                          <tr key={idx}>
                            <td>{timeStr}</td>
                            <td>{formatNumber(record.spot_price)}</td>
                            <td><strong>{formatNumber(record.atm_strike)}</strong></td>
                            <td style={{ fontSize: '10px' }}>{strikesStr}</td>
                            <td>{formatNumber(totalCEOI)}</td>
                            <td>{formatNumber(totalPEOI)}</td>
                            <td>{formatNumber(totalCEOIChange)}</td>
                            <td>{formatNumber(totalPEOIChange)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* JSON Preview */}
            <div className="data-section">
              <h4>JSON Preview (First 500 chars)</h4>
              <pre className="json-preview">
                {JSON.stringify(exportData, null, 2).substring(0, 500)}...
              </pre>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .export-data-container {
          padding: 20px;
        }
        .export-controls {
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
          background: #f8d7da;
          color: #721c24;
          border-radius: 4px;
          margin-bottom: 20px;
        }
        .export-results {
          margin-top: 20px;
        }
        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .data-summary {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
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
          font-size: 11px;
          color: #666;
          font-weight: 600;
        }
        .summary-item span {
          font-size: 14px;
          font-weight: bold;
          color: #333;
        }
        .sentiment.positive {
          color: #28a745;
        }
        .sentiment.negative {
          color: #dc3545;
        }
        .sentiment.neutral {
          color: #6c757d;
        }
        .data-section {
          margin-bottom: 30px;
        }
        .data-section h4 {
          margin-bottom: 15px;
          color: #333;
        }
        .table-container {
          overflow-x: auto;
        }
        .data-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }
        .data-table th {
          background: #333;
          color: #fff;
          padding: 10px;
          text-align: left;
          font-weight: 600;
        }
        .data-table td {
          padding: 8px 10px;
          border: 1px solid #ddd;
        }
        .data-table tbody tr:nth-child(even) {
          background: #f8f9fa;
        }
        .data-table tbody tr.atm-row {
          background: #fff3cd;
          font-weight: bold;
        }
        .fiidii-data {
          display: flex;
          gap: 30px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .fiidii-item {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .fiidii-item strong {
          font-size: 14px;
          color: #333;
        }
        .fiidii-item div {
          font-size: 12px;
          color: #666;
        }
        .sentiment-breakdown {
          display: flex;
          gap: 20px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .sentiment-item {
          padding: 8px 16px;
          border-radius: 4px;
          font-weight: 600;
        }
        .sentiment-item.positive {
          background: #d4edda;
          color: #155724;
        }
        .sentiment-item.negative {
          background: #f8d7da;
          color: #721c24;
        }
        .sentiment-item.neutral {
          background: #e2e3e5;
          color: #383d41;
        }
        .derived-metrics {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .metric-item {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .metric-item label {
          font-size: 11px;
          color: #666;
          font-weight: 600;
        }
        .metric-item span {
          font-size: 14px;
          font-weight: bold;
          color: #333;
        }
        .signal-badge {
          padding: 4px 8px;
          background: #007bff;
          color: white;
          border-radius: 4px;
          font-size: 12px;
          display: inline-block;
        }
        .bias-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          display: inline-block;
        }
        .bias-badge.bullish {
          background: #28a745;
          color: white;
        }
        .bias-badge.bearish {
          background: #dc3545;
          color: white;
        }
        .signal-strength {
          font-size: 16px;
          font-weight: bold;
          color: #007bff;
        }
        .valid-badge {
          padding: 4px 8px;
          background: #28a745;
          color: white;
          border-radius: 4px;
          font-size: 12px;
          display: inline-block;
        }
        .invalid-badge {
          padding: 4px 8px;
          background: #6c757d;
          color: white;
          border-radius: 4px;
          font-size: 12px;
          display: inline-block;
        }
        .json-preview {
          background: #f8f9fa;
          padding: 15px;
          border-radius: 4px;
          overflow-x: auto;
          font-size: 11px;
          max-height: 200px;
          overflow-y: auto;
        }
        .spinning {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
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
      `}</style>
    </div>
  )
}

export default ExportData




