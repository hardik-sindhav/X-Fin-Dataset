import React, { useState, useMemo } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import '../App.css'

// List of 12 bank stocks for BANKNIFTY filter
const BANK_STOCKS = [
  'HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'BANKBARODA',
  'PNB', 'CANBK', 'AUBANK', 'INDUSINDBK', 'IDFCFIRSTB', 'FEDERALBNK'
]

const HeatmapView = ({ gainersData, losersData, loading }) => {
  const [selectedView, setSelectedView] = useState('all') // 'all', 'nifty', 'banknifty', 'others'

  // Get timestamp from data
  const getTimestamp = () => {
    if (gainersData?.timestamp) return gainersData.timestamp
    if (losersData?.timestamp) return losersData.timestamp
    if (gainersData?.NIFTY?.timestamp) return gainersData.NIFTY.timestamp
    if (gainersData?.BANKNIFTY?.timestamp) return gainersData.BANKNIFTY.timestamp
    if (losersData?.NIFTY?.timestamp) return losersData.NIFTY.timestamp
    if (losersData?.BANKNIFTY?.timestamp) return losersData.BANKNIFTY.timestamp
    return null
  }

  // Combine and process data
  const processedData = useMemo(() => {
    if (!gainersData || !losersData) return []

    const allStocks = []
    const stockMap = new Map() // To avoid duplicates

    // Process gainers
    const processSection = (data, type, sectionName) => {
      if (data?.data && Array.isArray(data.data)) {
        data.data.forEach(stock => {
          const symbol = stock.symbol || stock.symbolName || ''
          if (!symbol) return
          
          // Use symbol as key (not symbol-type) so we can replace with better data
          const key = symbol.toUpperCase()
          
          // Try multiple field names for percentage change (perChange is primary based on sample)
          const change = parseFloat(
            stock.perChange || 
            stock.pChange || 
            stock.change || 
            stock.pctChange || 
            stock.net_price || 
            0
          )
          // Try multiple field names for price (ltp is primary based on sample)
          const price = parseFloat(
            stock.ltp || 
            stock.lastPrice || 
            stock.price || 
            stock.open_price || 
            0
          )
          
          // Only add if we have valid data (price must be > 0, change must be a valid number)
          if (!isNaN(price) && price > 0 && !isNaN(change)) {
            // If stock already exists, keep the one with larger absolute change
            if (stockMap.has(key)) {
              const existing = stockMap.get(key)
              if (Math.abs(change) > Math.abs(existing.change)) {
                stockMap.set(key, {
                  ...stock,
                  symbol: symbol,
                  type: change >= 0 ? 'gainer' : 'loser', // Determine type from change value
                  section: sectionName,
                  change: change,
                  price: price
                })
              }
            } else {
              stockMap.set(key, {
                ...stock,
                symbol: symbol,
                type: change >= 0 ? 'gainer' : 'loser', // Determine type from change value
                section: sectionName,
                change: change,
                price: price
              })
            }
          }
        })
      }
    }

    // Process gainers sections
    if (gainersData.NIFTY) processSection(gainersData.NIFTY, 'gainer', 'NIFTY')
    if (gainersData.BANKNIFTY) processSection(gainersData.BANKNIFTY, 'gainer', 'BANKNIFTY')
    if (gainersData.NIFTYNEXT50) processSection(gainersData.NIFTYNEXT50, 'gainer', 'NIFTYNEXT50')
    if (gainersData.allSec) processSection(gainersData.allSec, 'gainer', 'allSec')
    if (gainersData.FOSec) processSection(gainersData.FOSec, 'gainer', 'FOSec')

    // Process losers sections
    if (losersData.NIFTY) processSection(losersData.NIFTY, 'loser', 'NIFTY')
    if (losersData.BANKNIFTY) processSection(losersData.BANKNIFTY, 'loser', 'BANKNIFTY')
    if (losersData.NIFTYNEXT50) processSection(losersData.NIFTYNEXT50, 'loser', 'NIFTYNEXT50')
    if (losersData.allSec) processSection(losersData.allSec, 'loser', 'allSec')
    if (losersData.FOSec) processSection(losersData.FOSec, 'loser', 'FOSec')

    // Convert map to array
    allStocks.push(...Array.from(stockMap.values()))

    // Sort by absolute change (highest first)
    allStocks.sort((a, b) => Math.abs(b.change) - Math.abs(a.change))

    return allStocks
  }, [gainersData, losersData])

  // Filter data based on selected view
  const filteredData = useMemo(() => {
    let filtered = processedData

    if (selectedView === 'nifty') {
      filtered = processedData.filter(stock => stock.section === 'NIFTY')
    } else if (selectedView === 'banknifty') {
      // For BANKNIFTY, only show the 12 bank stocks
      filtered = processedData.filter(stock => {
        const symbol = (stock.symbol || stock.symbolName || '').toUpperCase()
        return BANK_STOCKS.includes(symbol)
      })
      // Ensure we have all 12 banks, even if some are missing from data
      const bankMap = new Map()
      filtered.forEach(stock => {
        const symbol = (stock.symbol || stock.symbolName || '').toUpperCase()
        bankMap.set(symbol, stock)
      })
      
      // Sort by change (gainers first, then losers), then by absolute change
      filtered.sort((a, b) => {
        // First sort by type (gainers first)
        if (a.type === 'gainer' && b.type === 'loser') return -1
        if (a.type === 'loser' && b.type === 'gainer') return 1
        // Then by absolute change (highest first)
        return Math.abs(b.change) - Math.abs(a.change)
      })
    } else if (selectedView === 'others') {
      filtered = processedData.filter(stock => 
        !['NIFTY', 'BANKNIFTY'].includes(stock.section)
      )
    }

    return filtered
  }, [processedData, selectedView])

  const getStockName = (stock) => {
    return stock.symbol || stock.symbolName || stock.companyName || 'N/A'
  }

  const formatPrice = (price) => {
    if (!price || isNaN(price) || price === 0) return '-'
    // Format with commas for thousands
    return price.toLocaleString('en-IN', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    })
  }

  const formatChange = (change) => {
    if (change === null || change === undefined || isNaN(change)) return '-'
    const sign = change >= 0 ? '+' : ''
    return `${sign}${change.toFixed(2)}%`
  }

  if (loading) {
    return (
      <div className="heatmap-container">
        <div className="heatmap-loading">
          <div className="spinner"></div>
          <p>Loading heatmap data...</p>
        </div>
      </div>
    )
  }

  if (filteredData.length === 0) {
    return (
      <div className="heatmap-container">
        <div className="heatmap-empty">
          <p>No data available for heatmap</p>
        </div>
      </div>
    )
  }

  const timestamp = getTimestamp()
  const formatTimestamp = (ts) => {
    if (!ts) return ''
    try {
      const date = new Date(ts)
      if (isNaN(date.getTime())) return ts
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }) + ' IST'
    } catch {
      return ts
    }
  }

  return (
    <div className="heatmap-container">
      {/* Header with timestamp */}
      {timestamp && (
        <div className="heatmap-header">
          <div className="heatmap-title">Stock Market Heatmap</div>
          <div className="heatmap-timestamp">As on {formatTimestamp(timestamp)}</div>
        </div>
      )}

      {/* View Selector */}
      <div className="heatmap-view-selector">
        <button
          className={`view-btn ${selectedView === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedView('all')}
        >
          All
        </button>
        <button
          className={`view-btn ${selectedView === 'nifty' ? 'active' : ''}`}
          onClick={() => setSelectedView('nifty')}
        >
          NIFTY
        </button>
        <button
          className={`view-btn ${selectedView === 'banknifty' ? 'active' : ''}`}
          onClick={() => setSelectedView('banknifty')}
        >
          BANKNIFTY
        </button>
        <button
          className={`view-btn ${selectedView === 'others' ? 'active' : ''}`}
          onClick={() => setSelectedView('others')}
        >
          Others
        </button>
      </div>

      {/* Heatmap Grid - Uniform Cards */}
      <div className="heatmap-grid-uniform">
        {filteredData.length === 0 ? (
          <div className="heatmap-empty-state">
            <p>No data available</p>
          </div>
        ) : (
          filteredData.map((stock, index) => {
            const isGainer = stock.type === 'gainer' || stock.change >= 0
            const price = formatPrice(stock.price)
            const changeText = formatChange(stock.change)
            const stockName = getStockName(stock)
            
            // Skip if we don't have valid data
            if (price === '-' || changeText === '-') {
              return null
            }
            
            return (
              <div
                key={`${stock.symbol || stockName}-${stock.type}-${index}`}
                className={`heatmap-card ${isGainer ? 'gainer' : 'loser'}`}
              >
                <div className="card-symbol">{stockName}</div>
                <div className="card-price">{price}</div>
                <div className={`card-change ${isGainer ? 'positive' : 'negative'}`}>
                  {changeText}
                </div>
              </div>
            )
          }).filter(Boolean) // Remove null entries
        )}
      </div>

      {/* Simple Legend */}
      {filteredData.length > 0 && (
        <div className="heatmap-legend">
          <div className="legend-item">
            <div className="legend-color gainer"></div>
            <span>Gainers</span>
          </div>
          <div className="legend-item">
            <div className="legend-color loser"></div>
            <span>Losers</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default HeatmapView

