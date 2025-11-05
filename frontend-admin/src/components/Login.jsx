import React, { useState, useEffect, useRef } from 'react'
import { AlertCircle, Activity } from 'lucide-react'
import '../App.css'

const API_BASE = '/api'

function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [focusedField, setFocusedField] = useState(null)
  const circlesRef = useRef([])
  const containerRef = useRef(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      const data = await response.json()

      if (data.success && data.token) {
        // Store token in localStorage
        localStorage.setItem('authToken', data.token)
        localStorage.setItem('username', data.username)
        
        // Call success callback
        onLoginSuccess(data.token, data.username)
      } else {
        setError(data.error || 'Login failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
      console.error('Login error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!containerRef.current) return

      const containerRect = containerRef.current.getBoundingClientRect()
      const mouseX = e.clientX - containerRect.left
      const mouseY = e.clientY - containerRect.top

      circlesRef.current.forEach((circle, index) => {
        if (!circle) return

        const circleRect = circle.getBoundingClientRect()
        const circleX = circleRect.left - containerRect.left + circleRect.width / 2
        const circleY = circleRect.top - containerRect.top + circleRect.height / 2

        const distance = Math.sqrt(
          Math.pow(mouseX - circleX, 2) + Math.pow(mouseY - circleY, 2)
        )

        const maxDistance = 150
        const influence = Math.max(0, 1 - distance / maxDistance)

        if (influence > 0.1) {
          const moveX = (mouseX - circleX) * influence * 0.3
          const moveY = (mouseY - circleY) * influence * 0.3
          const scale = 1 + influence * 0.5

          circle.style.transform = `translate(${moveX}px, ${moveY}px) scale(${scale})`
          circle.style.opacity = 0.2 + influence * 0.4
        } else {
          circle.style.transform = ''
          circle.style.opacity = ''
        }
      })
    }

    const container = containerRef.current
    if (container) {
      container.addEventListener('mousemove', handleMouseMove)
      return () => {
        container.removeEventListener('mousemove', handleMouseMove)
      }
    }
  }, [])

  return (
    <div className="login-container">
      {/* Left Side - Login Form */}
      <div className="login-card-simple">
        <div className="login-header-simple">
          <div className="login-logo-xfin">
            <Activity size={32} />
          </div>
        </div>

        <div className="login-content">
          <h2 className="login-title-simple">Login with e-mail and password</h2>

          <form onSubmit={handleSubmit} className="login-form-simple">
            {error && (
              <div className="login-error-simple">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <div className="form-group-simple">
              <label htmlFor="username" className="input-label">E-mail</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onFocus={() => setFocusedField('username')}
                onBlur={() => setFocusedField(null)}
                placeholder=""
                required
                autoFocus
                disabled={loading}
                className="input-simple"
              />
            </div>

            <div className="form-group-simple">
              <label htmlFor="password" className="input-label">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={() => setFocusedField('password')}
                onBlur={() => setFocusedField(null)}
                placeholder=""
                required
                disabled={loading}
                className="input-simple"
              />
            </div>

            <button
              type="submit"
              className="login-btn-simple"
              disabled={loading || !username || !password}
            >
              {loading ? (
                <>
                  <div className="btn-spinner-simple"></div>
                  <span>Logging in...</span>
                </>
              ) : (
                'Login'
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Right Side - Decorative Elements */}
      <div className="login-bg-simple" ref={containerRef}>
        <div className="bg-circle-main">
          <div className="logo-xfin-large">
            <Activity size={120} />
          </div>
        </div>
        <div className="bg-circles-group">
          {[...Array(25)].map((_, i) => (
            <div 
              key={i} 
              ref={el => circlesRef.current[i] = el}
              className="bg-small-circle" 
              style={{ '--index': i, '--delay': `${i * 0.15}s` }}
            ></div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Login
