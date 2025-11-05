import React from 'react'
import { X } from 'lucide-react'
import OptionChainView from './OptionChainView'

const DetailView = ({ record, onClose, tabName }) => {
  if (!record) return null

  // Check if this is option chain data that should be displayed in table format
  const isOptionChainData = record.records && record.records.data && Array.isArray(record.records.data)

  const renderValue = (key, value, depth = 0) => {
    if (value === null || value === undefined) return '-'
    
    if (typeof value === 'object' && !Array.isArray(value)) {
      return (
        <div style={{ marginLeft: depth > 0 ? '20px' : '0px', marginTop: '8px' }}>
          {Object.entries(value).map(([k, v]) => (
            <div key={k} style={{ marginBottom: '8px', padding: '8px', background: depth === 0 ? '#f9f9f9' : '#f5f5f5', borderRadius: '4px', border: '1px solid #e0e0e0' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '4px', color: '#333' }}>
                {k.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}:
              </div>
              <div style={{ marginLeft: '10px' }}>
                {renderValue(k, v, depth + 1)}
              </div>
            </div>
          ))}
        </div>
      )
    }
    
    if (Array.isArray(value)) {
      if (value.length === 0) return <span style={{ color: '#999' }}>Empty array</span>
      return (
        <div style={{ marginLeft: depth > 0 ? '20px' : '0px', marginTop: '8px' }}>
          <div style={{ marginBottom: '8px', fontWeight: 'bold', color: '#666' }}>
            Array ({value.length} items)
          </div>
          {value.slice(0, 100).map((item, idx) => (
            <div key={idx} style={{ marginBottom: '8px', padding: '10px', background: '#f5f5f5', borderRadius: '4px', border: '1px solid #e0e0e0' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '4px', color: '#666', fontSize: '0.9em' }}>
                Item {idx + 1}:
              </div>
              <div style={{ marginLeft: '10px' }}>
                {typeof item === 'object' ? (
                  renderValue(`${key}[${idx}]`, item, depth + 1)
                ) : (
                  <span>{String(item)}</span>
                )}
              </div>
            </div>
          ))}
          {value.length > 100 && (
            <div style={{ padding: '8px', background: '#fff3cd', borderRadius: '4px', marginTop: '8px' }}>
              ... and {value.length - 100} more items (showing first 100)
            </div>
          )}
        </div>
      )
    }
    
    return <span>{String(value)}</span>
  }

  return (
    <div className="detail-view-overlay" onClick={onClose}>
      <div className="detail-view-modal" onClick={(e) => e.stopPropagation()}>
        <div className="detail-view-header">
          <h2>Record Details</h2>
          <button className="detail-view-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        <div className="detail-view-content">
          {isOptionChainData ? (
            <div>
              {/* Show option chain table */}
              <div style={{ marginBottom: '20px', padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
                <h3 style={{ margin: '0 0 12px 0', color: '#1e3a8a' }}>Option Chain Data</h3>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Timestamp:</strong> {record.records?.timestamp || '-'}
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Underlying Value:</strong> {record.records?.underlyingValue || record.records?.underlying_value || '-'}
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Total Options:</strong> {record.records?.data?.length || 0}
                </div>
              </div>
              <OptionChainView records={record.records} />
              
              {/* Show other metadata */}
              {(record.insertedAt || record.updatedAt) && (
                <div style={{ marginTop: '20px', padding: '16px', background: '#f8fafc', borderRadius: '8px', fontSize: '14px' }}>
                  {record.insertedAt && (
                    <div style={{ marginBottom: '8px' }}>
                      <strong>Inserted At:</strong> {new Date(record.insertedAt).toLocaleString()}
                    </div>
                  )}
                  {record.updatedAt && (
                    <div>
                      <strong>Updated At:</strong> {new Date(record.updatedAt).toLocaleString()}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            Object.entries(record).map(([key, value]) => (
              <div key={key} className="detail-view-item">
                <div className="detail-view-label">
                  <strong>{key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}:</strong>
                </div>
                <div className="detail-view-value">
                  {renderValue(key, value)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default DetailView

