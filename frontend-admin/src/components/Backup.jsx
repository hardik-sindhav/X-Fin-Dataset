import React, { useState } from 'react'
import { Download, Cloud, HardDrive, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import axios from 'axios'
import { API_BASE } from '../config'

function Backup({ authToken }) {
  const [backupLoading, setBackupLoading] = useState(false)
  const [backupProgress, setBackupProgress] = useState(0)
  const [backupStatus, setBackupStatus] = useState('') // 'preparing', 'downloading', 'complete'
  const [lastBackup, setLastBackup] = useState(null)

  const handleDownloadBackup = async () => {
    if (backupLoading) return
    
    if (!window.confirm('This will download a backup of all MongoDB collections. Continue?')) {
      return
    }
    
    setBackupLoading(true)
    setBackupProgress(0)
    setBackupStatus('preparing')
    
    try {
      const response = await axios.get(`${API_BASE}/backup`, {
        headers: { Authorization: `Bearer ${authToken}` },
        responseType: 'blob', // Important for file download
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setBackupProgress(percentCompleted)
            setBackupStatus('downloading')
          } else {
            // If total is not available, show indeterminate progress
            setBackupStatus('downloading')
          }
        }
      })
      
      // Create a blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition']
      let filename = 'nse_data_backup.zip'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      // Update last backup time
      setBackupStatus('complete')
      setBackupProgress(100)
      setLastBackup(new Date().toISOString())
      
      // Show success message after a brief delay
      setTimeout(() => {
        alert('✅ Backup downloaded successfully!')
        setBackupLoading(false)
        setBackupProgress(0)
        setBackupStatus('')
      }, 500)
    } catch (error) {
      console.error('Backup error:', error)
      if (error.response?.data) {
        // Try to parse error message from blob if it's JSON
        try {
          const text = await error.response.data.text()
          const errorData = JSON.parse(text)
          alert('❌ Backup failed: ' + (errorData.error || errorData.message || 'Unknown error'))
        } catch {
          alert('❌ Backup failed: ' + (error.response.statusText || error.message))
        }
      } else {
        alert('❌ Backup failed: ' + error.message)
      }
    } finally {
      // Only reset if there was an error (success case handles it above)
      if (backupStatus !== 'complete') {
        setBackupLoading(false)
        setBackupProgress(0)
        setBackupStatus('')
      }
    }
  }

  const getStatusText = () => {
    switch (backupStatus) {
      case 'preparing':
        return 'Preparing backup...'
      case 'downloading':
        return backupProgress > 0 ? `Downloading... ${backupProgress}%` : 'Downloading...'
      case 'complete':
        return 'Download complete!'
      default:
        return 'Download Backup'
    }
  }

  const formatDateTime = (isoString) => {
    if (!isoString) return 'Never'
    try {
      const date = new Date(isoString)
      if (isNaN(date.getTime())) return isoString
      return date.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      })
    } catch (error) {
      return isoString
    }
  }

  return (
    <div className="backup-page">
      <div className="card">
        <div className="card-header">
          <h2>Backup & Restore</h2>
        </div>
        <div className="card-body">
          <p className="description">
            Create backups of your MongoDB data for safekeeping and disaster recovery.
          </p>

          <div className="backup-options">
            {/* Offline Backup Option */}
            <div className="backup-option-card">
              <div className="backup-option-header">
                <div className="backup-option-icon">
                  <HardDrive size={32} />
                </div>
                <div className="backup-option-title">
                  <h3>Offline Backup</h3>
                  <p>Download a complete backup of all MongoDB collections</p>
                </div>
              </div>
              
              <div className="backup-option-features">
                <div className="feature-item">
                  <CheckCircle size={16} />
                  <span>All collections included</span>
                </div>
                <div className="feature-item">
                  <CheckCircle size={16} />
                  <span>JSON format for easy restoration</span>
                </div>
                <div className="feature-item">
                  <CheckCircle size={16} />
                  <span>Compressed ZIP file</span>
                </div>
                <div className="feature-item">
                  <CheckCircle size={16} />
                  <span>Includes metadata and timestamps</span>
                </div>
              </div>

              {lastBackup && (
                <div className="last-backup-info">
                  <Clock size={14} />
                  <span>Last backup: {formatDateTime(lastBackup)}</span>
                </div>
              )}

              <div className="backup-download-section">
                {backupLoading && (
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${backupProgress || 0}%` }}
                      ></div>
                    </div>
                    <div className="progress-text">
                      {getStatusText()}
                    </div>
                  </div>
                )}
                <button
                  className={`btn btn-primary btn-large ${backupLoading ? 'loading' : ''}`}
                  onClick={handleDownloadBackup}
                  disabled={backupLoading}
                >
                  {backupLoading ? (
                    <>
                      <span className="spinner"></span>
                      {getStatusText()}
                    </>
                  ) : (
                    <>
                      <Download size={20} />
                      Download Backup
                    </>
                  )}
                </button>
              </div>

              <div className="backup-info">
                <AlertCircle size={14} />
                <span>The backup file will be saved to your downloads folder</span>
              </div>
            </div>

            {/* Online Backup Option */}
            <div className="backup-option-card">
              <div className="backup-option-header">
                <div className="backup-option-icon">
                  <Cloud size={32} />
                </div>
                <div className="backup-option-title">
                  <h3>Online Backup</h3>
                  <p>Cloud backup service (Coming Soon)</p>
                </div>
              </div>
              
              <div className="backup-option-features">
                <div className="feature-item disabled">
                  <Clock size={16} />
                  <span>Automatic cloud synchronization</span>
                </div>
                <div className="feature-item disabled">
                  <Clock size={16} />
                  <span>Scheduled backups</span>
                </div>
                <div className="feature-item disabled">
                  <Clock size={16} />
                  <span>Multiple backup versions</span>
                </div>
                <div className="feature-item disabled">
                  <Clock size={16} />
                  <span>One-click restore</span>
                </div>
              </div>

              <button
                className="btn btn-secondary btn-large"
                disabled
                style={{ opacity: 0.6, cursor: 'not-allowed' }}
              >
                <Cloud size={20} />
                Coming Soon
              </button>

              <div className="backup-info">
                <AlertCircle size={14} />
                <span>Online backup feature is under development</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Backup

