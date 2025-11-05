import React from 'react'

const OptionChainView = ({ records }) => {
  if (!records || !records.data || !Array.isArray(records.data)) {
    return <div>No option chain data available</div>
  }

  const formatNumber = (num) => {
    if (num === null || num === undefined || num === '-') return '-'
    if (typeof num === 'string' && num === '-') return '-'
    const numValue = typeof num === 'string' ? parseFloat(num) : num
    if (isNaN(numValue)) return '-'
    return numValue.toLocaleString('en-IN')
  }

  const formatPrice = (num) => {
    if (num === null || num === undefined || num === '-') return '-'
    if (typeof num === 'string' && num === '-') return '-'
    const numValue = typeof num === 'string' ? parseFloat(num) : num
    if (isNaN(numValue)) return '-'
    return numValue.toFixed(2)
  }

  // Group data by strike price - NSE API typically has CE and PE in same object
  const strikeMap = {}
  records.data.forEach(item => {
    // Get strike price from various possible field names
    const strikePrice = item.strikePrice || item.strike || item.strike_price || 
                       (item.CE && item.CE.strikePrice) || (item.PE && item.PE.strikePrice) ||
                       (item.ce && item.ce.strikePrice) || (item.pe && item.pe.strikePrice)
    
    if (!strikePrice) return

    if (!strikeMap[strikePrice]) {
      strikeMap[strikePrice] = { strike: strikePrice, ce: null, pe: null }
    }

    // Helper function to extract option data
    const extractOptionData = (optionData) => {
      if (!optionData) return null
      return {
        openInterest: optionData.openInterest || optionData.open_interest || optionData.oi || optionData.OpenInterest || '-',
        changeinOpenInterest: optionData.changeinOpenInterest || optionData.changein_open_interest || optionData.change_in_oi || optionData.chngInOI || optionData.changeinOI || '-',
        totalTradedVolume: optionData.totalTradedVolume || optionData.total_traded_volume || optionData.volume || optionData.TotalTradedVolume || '-',
        impliedVolatility: optionData.impliedVolatility || optionData.implied_volatility || optionData.iv || optionData.ImpliedVolatility || '-',
        lastPrice: optionData.lastPrice || optionData.last_price || optionData.ltp || optionData.LastPrice || '-',
        change: optionData.change || optionData.chng || optionData.Change || '-',
        bidPrice: optionData.bidPrice || optionData.bid_price || optionData.bid || optionData.BidPrice || optionData.bidprice || '-',
        askPrice: optionData.askPrice || optionData.ask_price || optionData.ask || optionData.AskPrice || optionData.askprice || '-',
        bidQty: optionData.bidQty || optionData.bid_qty || optionData.BidQty || optionData.bidqty || optionData.bidQty || '-',
        askQty: optionData.askQty || optionData.ask_qty || optionData.AskQty || optionData.askqty || optionData.askQty || '-'
      }
    }

    // CE (Call Option) data
    if (item.CE || item.ce) {
      strikeMap[strikePrice].ce = extractOptionData(item.CE || item.ce)
    }

    // PE (Put Option) data
    if (item.PE || item.pe) {
      strikeMap[strikePrice].pe = extractOptionData(item.PE || item.pe)
    }
  })

  // Convert to array and sort by strike price
  const strikeRows = Object.values(strikeMap).sort((a, b) => {
    const strikeA = parseFloat(a.strike) || 0
    const strikeB = parseFloat(b.strike) || 0
    return strikeA - strikeB
  })

  // Calculate total change in OI
  const totalChangeInOI = strikeRows.reduce((sum, row) => {
    const ceChange = parseFloat(row.ce?.changeinOpenInterest) || 0
    const peChange = parseFloat(row.pe?.changeinOpenInterest) || 0
    return sum + ceChange + peChange
  }, 0)

  return (
    <div style={{ 
      width: '100%', 
      overflowX: 'auto', 
      marginTop: '20px',
      background: '#fff',
      borderRadius: '8px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      {/* Total Change in OI Summary */}
      <div style={{ 
        padding: '8px 12px', 
        background: '#f8f9fa', 
        borderBottom: '1px solid #e0e0e0',
        fontSize: '10px',
        fontWeight: 'bold'
      }}>
        Total Change in OI: {formatNumber(totalChangeInOI)}
      </div>
      
      <table style={{ 
        width: '100%', 
        borderCollapse: 'collapse',
        fontSize: '10px',
        fontFamily: 'Arial, sans-serif'
      }}>
        <thead>
          <tr style={{ background: '#000', color: '#fff' }}>
            {/* CALLS Header */}
            <th colSpan="6" style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 'bold', border: '1px solid #333' }}>
              CALLS
            </th>
            {/* STRIKE Header */}
            <th style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 'bold', border: '1px solid #333', background: '#000' }}>
              STRIKE
            </th>
            {/* PUTS Header */}
            <th colSpan="6" style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 'bold', border: '1px solid #333' }}>
              PUTS
            </th>
          </tr>
          <tr style={{ background: '#333', color: '#fff', fontSize: '9px' }}>
            {/* CALLS Column Headers */}
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>OI</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>CHNG IN OI</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>VOLUME</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>IV</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>LTP</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>CHNG</th>
            {/* STRIKE Column Header */}
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600', background: '#333' }}>STRIKE</th>
            {/* PUTS Column Headers (reversed order) */}
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>CHNG</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>LTP</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>IV</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>VOLUME</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>CHNG IN OI</th>
            <th style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #555', fontWeight: '600' }}>OI</th>
          </tr>
        </thead>
        <tbody>
          {strikeRows.map((row, index) => {
            const ce = row.ce || {}
            const pe = row.pe || {}
            const isEven = index % 2 === 0
            const rowBg = isEven ? '#ffffff' : '#f8f9fa'

            return (
              <tr key={row.strike} style={{ background: rowBg }}>
                {/* CALLS Data */}
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', color: '#000' }}>
                  {formatNumber(ce.openInterest)}
                </td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', color: '#000' }}>{formatNumber(ce.changeinOpenInterest)}</td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', color: '#000' }}>{formatNumber(ce.totalTradedVolume)}</td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', color: '#000' }}>{formatPrice(ce.impliedVolatility)}</td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', textDecoration: 'underline', cursor: 'pointer', color: '#000' }}>
                  {formatPrice(ce.lastPrice)}
                </td>
                <td style={{ 
                  padding: '6px 3px', 
                  textAlign: 'center', 
                  border: '1px solid #e0e0e0',
                  color: '#000'
                }}>
                  {formatPrice(ce.change)}
                </td>
                
                {/* STRIKE Price */}
                <td style={{ 
                  padding: '6px 3px', 
                  textAlign: 'center', 
                  border: '1px solid #e0e0e0',
                  fontWeight: 'bold',
                  background: '#f0f0f0',
                  textDecoration: 'underline',
                  cursor: 'pointer',
                  color: '#000'
                }}>
                  {formatPrice(row.strike)}
                </td>
                
                {/* PUTS Data (reversed order) */}
                <td style={{ 
                  padding: '6px 3px', 
                  textAlign: 'center', 
                  border: '1px solid #e0e0e0',
                  color: '#000'
                }}>
                  {formatPrice(pe.change)}
                </td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', textDecoration: 'underline', cursor: 'pointer', color: '#000' }}>
                  {formatPrice(pe.lastPrice)}
                </td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', color: '#000' }}>{formatPrice(pe.impliedVolatility)}</td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', color: '#000' }}>{formatNumber(pe.totalTradedVolume)}</td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', color: '#000' }}>{formatNumber(pe.changeinOpenInterest)}</td>
                <td style={{ padding: '6px 3px', textAlign: 'center', border: '1px solid #e0e0e0', color: '#000' }}>
                  {formatNumber(pe.openInterest)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default OptionChainView

