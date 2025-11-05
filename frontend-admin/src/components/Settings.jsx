import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Settings as SettingsIcon, 
  Save, 
  Calendar, 
  Clock, 
  ToggleLeft, 
  ToggleRight,
  Plus,
  X,
  AlertCircle,
  CheckCircle
} from 'lucide-react'

const API_BASE = '/api'

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
    { id: 'fiidii', label: 'FII/DII', icon: '💰' }
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

        <div className="form-group">
          <label>
            <ToggleRight size={16} />
            Enabled
          </label>
          <div className="toggle-switch">
            <button
              className={`toggle-btn ${schedulerConfig.enabled ? 'active' : ''}`}
              onClick={() => handleConfigChange(schedulerType, 'enabled', !schedulerConfig.enabled)}
            >
              {schedulerConfig.enabled ? <ToggleRight size={20} /> : <ToggleLeft size={20} />}
              <span>{schedulerConfig.enabled ? 'Enabled' : 'Disabled'}</span>
            </button>
          </div>
        </div>

        <button
          className="save-btn"
          onClick={() => saveConfig(schedulerType)}
          disabled={loading || !unsavedChanges[schedulerType]}
        >
          <Save size={16} />
          {unsavedChanges[schedulerType] ? 'Save Changes' : 'Saved'}
        </button>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <SettingsIcon size={24} />
        <h1>Scheduler Settings</h1>
      </div>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="settings-container">
        <div className="settings-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span>{tab.label}</span>
              {unsavedChanges[tab.id] && <span className="unsaved-indicator">•</span>}
            </button>
          ))}
        </div>

        <div className="settings-content">
          <div className="settings-card">
            <h2>{getSchedulerName(activeTab)}</h2>
            {renderConfigForm(activeTab)}
          </div>
        </div>
      </div>

      <div className="holidays-section">
        <div className="holidays-header">
          <Calendar size={20} />
          <h2>Holidays</h2>
          <p>All schedulers will skip execution on holidays</p>
        </div>

        <div className="holidays-add">
          <input
            type="date"
            value={newHoliday}
            onChange={(e) => setNewHoliday(e.target.value)}
            placeholder="YYYY-MM-DD"
          />
          <button onClick={addHoliday} disabled={loading || !newHoliday}>
            <Plus size={16} />
            Add Holiday
          </button>
        </div>

        <div className="holidays-list">
          {holidays.length === 0 ? (
            <p className="no-holidays">No holidays configured</p>
          ) : (
            holidays.map(date => (
              <div key={date} className="holiday-item">
                <Calendar size={16} />
                <span>{new Date(date).toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}</span>
                <button
                  className="remove-btn"
                  onClick={() => removeHoliday(date)}
                  disabled={loading}
                >
                  <X size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default Settings

