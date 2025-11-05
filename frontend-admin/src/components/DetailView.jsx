import React from 'react'
import { X } from 'lucide-react'

const DetailView = ({ record, onClose, tabName }) => {
  if (!record) return null

  const renderValue = (key, value) => {
    if (value === null || value === undefined) return '-'
    
    if (typeof value === 'object' && !Array.isArray(value)) {
      return (
        <div style={{ marginLeft: '20px' }}>
          {Object.entries(value).map(([k, v]) => (
            <div key={k} style={{ marginBottom: '8px' }}>
              <strong>{k}:</strong> {renderValue(k, v)}
            </div>
          ))}
        </div>
      )
    }
    
    if (Array.isArray(value)) {
      return (
        <div style={{ marginLeft: '20px' }}>
          {value.map((item, idx) => (
            <div key={idx} style={{ marginBottom: '8px', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
              {typeof item === 'object' ? (
                Object.entries(item).map(([k, v]) => (
                  <div key={k} style={{ marginBottom: '4px' }}>
                    <strong>{k}:</strong> {String(v)}
                  </div>
                ))
              ) : (
                String(item)
              )}
            </div>
          ))}
        </div>
      )
    }
    
    return String(value)
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
          {Object.entries(record).map(([key, value]) => (
            <div key={key} className="detail-view-item">
              <div className="detail-view-label">
                <strong>{key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}:</strong>
              </div>
              <div className="detail-view-value">
                {renderValue(key, value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default DetailView

