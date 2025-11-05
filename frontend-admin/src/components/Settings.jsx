import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Settings as SettingsIcon, 
  Save, 
  Calendar, 
  Clock, 
  Plus,
  X,
  AlertCircle,
  CheckCircle
} from 'lucide-react'

const API_BASE = 'https://api.xfinai.cloud/api'

const Settings = ({ authToken }) => {
  const [activeTab, setActiveTab] = useState('banks')
  const [config, setConfig] = useState({
    banks: { interval_minutes: 3, start_time: '09:15', end_time: '15:30', enabled: true },
    indices: { interval_minutes: 3, start_time: '09:15', end_time: '15:30', enabled: true },
    gainers_losers: { interval_minutes: 3, start_time: '09:15', end_time: '15:30', enabled: true },
    news: { interval_minutes: 3, start_time: '09:15', end_time: '15:30', enabled: true },
    fiidii: { interval_minutes: 60, start_time: '17:00', end_time: '17:00', enabled: true }
  })
  const [holidays, setHolidays] = useState([])
  const [newHoliday, setNewHoliday] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [unsavedChanges, setUnsavedChanges] = useState({})

  useEffect(() => {
    loadConfig()
    loadHolidays()
  }, [])

  // Auto-hide message after 5 seconds
  useEffect(() => {
    if (message.text) {
      const timer = setTimeout(() => {
        setMessage({ type: '', text: '' })
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [message.text])

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE}/config`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      if (response.data.success) {
        setConfig(response.data.config)
      }
    } catch (error) {
      console.error('Error loading config:', error)
      setMessage({ type: 'error', text: 'Failed to load configuration' })
    }
  }

  const loadHolidays = async () => {
    try {
      const response = await axios.get(`${API_BASE}/holidays`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      if (response.data.success) {
        setHolidays(response.data.holidays)
      }
    } catch (error) {
      console.error('Error loading holidays:', error)
    }
  }

  const handleConfigChange = (schedulerType, field, value) => {
    const newConfig = { ...config }
    newConfig[schedulerType] = { ...newConfig[schedulerType], [field]: value }
    setConfig(newConfig)
    setUnsavedChanges({ ...unsavedChanges, [schedulerType]: true })
    setMessage({ type: '', text: '' })
  }

  const saveConfig = async (schedulerType) => {
    setLoading(true)
    setMessage({ type: '', text: '' })
    
    try {
      const response = await axios.post(
        `${API_BASE}/config`,
        {
          scheduler_type: schedulerType,
          config: config[schedulerType]
        },
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      )
      
      if (response.data.success) {
        setMessage({ type: 'success', text: `Configuration saved for ${getSchedulerName(schedulerType)}` })
        const newUnsaved = { ...unsavedChanges }
        delete newUnsaved[schedulerType]
        setUnsavedChanges(newUnsaved)
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Failed to save configuration' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to save configuration' })
    } finally {
      setLoading(false)
    }
  }

  const addHoliday = async () => {
    if (!newHoliday) {
      setMessage({ type: 'error', text: 'Please enter a date' })
      return
    }

    // Validate date format (YYYY-MM-DD)
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/
    if (!dateRegex.test(newHoliday)) {
      setMessage({ type: 'error', text: 'Date must be in YYYY-MM-DD format' })
      return
    }

    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const response = await axios.post(
        `${API_BASE}/holidays`,
        { date: newHoliday },
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      )

      if (response.data.success) {
        setHolidays([...holidays, newHoliday].sort())
        setNewHoliday('')
        setMessage({ type: 'success', text: 'Holiday added successfully' })
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Failed to add holiday' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to add holiday' })
    } finally {
      setLoading(false)
    }
  }

  const removeHoliday = async (date) => {
    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const response = await axios.delete(
        `${API_BASE}/holidays`,
        {
          data: { date },
          headers: { Authorization: `Bearer ${authToken}` }
        }
      )

      if (response.data.success) {
        setHolidays(holidays.filter(h => h !== date))
        setMessage({ type: 'success', text: 'Holiday removed successfully' })
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Failed to remove holiday' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to remove holiday' })
    } finally {
      setLoading(false)
    }
  }

  const getSchedulerName = (type) => {
    const names = {
      banks: 'All Banks (12 banks)',
      indices: 'Indices (NIFTY, BankNifty, Finnifty, MidcapNifty)',
      gainers_losers: 'Gainers & Losers',
      news: 'News & LiveMint News',
      fiidii: 'FII/DII'
    }
    return names[type] || type
  }

  const tabs = [
    { id: 'banks', label: 'Banks', icon: '🏦' },
    { id: 'indices', label: 'Indices', icon: '📊' },
    { id: 'gainers_losers', label: 'Gainers/Losers', icon: '📈' },
    { id: 'news', label: 'News', icon: '📰' },
    { id: 'fiidii', label: 'FII/DII', icon: '💰' },
    { id: 'holidays', label: 'Holidays', icon: '📅' }
  ]

  const renderConfigForm = (schedulerType) => {
    const schedulerConfig = config[schedulerType] || {}
    const isFiidii = schedulerType === 'fiidii'

    return (
      <div className="settings-form">
        <div className="form-group">
          <label>
            <Clock size={16} />
            Interval (minutes)
          </label>
          <input
            type="number"
            min="1"
            value={schedulerConfig.interval_minutes || 3}
            onChange={(e) => handleConfigChange(schedulerType, 'interval_minutes', parseInt(e.target.value))}
            disabled={isFiidii}
          />
          {isFiidii && <small>FII/DII runs once per day at the specified time</small>}
        </div>

        <div className="form-group">
          <label>
            <Clock size={16} />
            Start Time
          </label>
          <input
            type="time"
            value={schedulerConfig.start_time || '09:15'}
            onChange={(e) => handleConfigChange(schedulerType, 'start_time', e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>
            <Clock size={16} />
            End Time
          </label>
          <input
            type="time"
            value={schedulerConfig.end_time || '15:30'}
            onChange={(e) => handleConfigChange(schedulerType, 'end_time', e.target.value)}
            disabled={isFiidii}
          />
          {isFiidii && <small>FII/DII runs only at start time</small>}
        </div>

        <div className="form-group save-btn-container">
          <button
            className={`save-btn ${unsavedChanges[schedulerType] ? 'has-changes' : ''}`}
            onClick={() => saveConfig(schedulerType)}
            disabled={loading || !unsavedChanges[schedulerType]}
          >
            <Save size={18} />
            {loading ? 'Saving...' : unsavedChanges[schedulerType] ? 'Save Changes' : 'All Changes Saved'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div className="settings-header-content">
          <div className="settings-title-section">
            <div className="settings-icon-wrapper">
              <SettingsIcon size={28} />
            </div>
            <div>
              <h1>Scheduler Settings</h1>
              <p className="settings-subtitle">Configure intervals, timing, and holidays for all schedulers</p>
            </div>
          </div>
        </div>
      </div>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="settings-layout">
        <div className="settings-tabs-container">
          <div className="settings-tabs-header">
            <h3>Scheduler Groups</h3>
          </div>
          <div className="settings-tabs">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-label">{tab.label}</span>
                {unsavedChanges[tab.id] && <span className="unsaved-indicator" title="Unsaved changes">●</span>}
              </button>
            ))}
          </div>
        </div>

        <div className="settings-content-wrapper">
          {activeTab === 'holidays' ? (
            <div className="holidays-section">
              <div className="holidays-header">
                <div className="holidays-header-content">
                  <div className="holidays-icon-wrapper">
                    <Calendar size={24} />
                  </div>
                  <div>
                    <h2>Market Holidays</h2>
                    <p>All schedulers will skip execution on these dates</p>
                  </div>
                </div>
              </div>

              <div className="holidays-add">
                <input
                  type="date"
                  value={newHoliday}
                  onChange={(e) => setNewHoliday(e.target.value)}
                  placeholder="Select date"
                  className="holiday-input"
                />
                <button 
                  onClick={addHoliday} 
                  disabled={loading || !newHoliday}
                  className="add-holiday-btn"
                >
                  <Plus size={18} />
                  Add Holiday
                </button>
              </div>

              <div className="holidays-list">
                {holidays.length === 0 ? (
                  <div className="no-holidays">
                    <Calendar size={48} className="no-holidays-icon" />
                    <p>No holidays configured</p>
                    <span className="no-holidays-hint">Add holidays to prevent schedulers from running on those dates</span>
                  </div>
                ) : (
                  <div className="holidays-grid">
                    {holidays.map(date => (
                      <div key={date} className="holiday-item">
                        <div className="holiday-item-content">
                          <Calendar size={18} className="holiday-icon" />
                          <div className="holiday-date">
                            <span className="holiday-date-full">{new Date(date).toLocaleDateString('en-US', { 
                              weekday: 'long', 
                              year: 'numeric', 
                              month: 'long', 
                              day: 'numeric' 
                            })}</span>
                            <span className="holiday-date-short">{date}</span>
                          </div>
                        </div>
                        <button
                          className="remove-btn"
                          onClick={() => removeHoliday(date)}
                          disabled={loading}
                          title="Remove holiday"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="settings-card">
              <div className="settings-card-header">
                <h2>{getSchedulerName(activeTab)}</h2>
              </div>
              {renderConfigForm(activeTab)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Settings

