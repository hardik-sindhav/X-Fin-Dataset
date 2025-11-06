import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Activity, 
  TrendingUp,
  TrendingDown,
  BarChart3,
  Database,
  Newspaper,
  Zap,
  Shield,
  Clock,
  ArrowRight,
  CheckCircle,
  LineChart,
  Mail,
  Phone,
  MapPin,
  Send,
  Rocket,
  Sparkles,
  Brain,
  Target,
  Users,
  Award,
  Crown,
  IndianRupee,
  MessageCircle,
  Star,
  Lock
} from 'lucide-react'
import '../App.css'

import { API_BASE } from '../config'

function HomePage({ onNavigate }) {
  const [overviewStats, setOverviewStats] = useState({
    totalRecords: 0,
    activeCollectors: 0,
    lastUpdate: null
  })
  const [loading, setLoading] = useState(true)
  
  // Launch countdown - 1 year from today
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0
  })

  useEffect(() => {
    // Calculate launch date (1 year from today)
    const launchDate = new Date()
    launchDate.setFullYear(launchDate.getFullYear() + 1)
    
    const updateCountdown = () => {
      const now = new Date().getTime()
      const distance = launchDate.getTime() - now
      
      if (distance > 0) {
        setTimeLeft({
          days: Math.floor(distance / (1000 * 60 * 60 * 24)),
          hours: Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)),
          seconds: Math.floor((distance % (1000 * 60)) / 1000)
        })
      } else {
        setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 })
      }
    }
    
    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Don't fetch detailed stats on home page
    setOverviewStats({
      totalRecords: 0,
      activeCollectors: 0,
      lastUpdate: new Date().toLocaleTimeString()
    })
    setLoading(false)
  }, [])

  const features = [
    {
      icon: <BarChart3 size={32} />,
      title: 'Real-Time Analytics',
      description: 'Advanced analytics and insights for informed decision making',
      color: 'var(--green)'
    },
    {
      icon: <TrendingUp size={32} />,
      title: 'Market Trends',
      description: 'Track market movements and identify opportunities',
      color: 'var(--green)'
    },
    {
      icon: <Database size={32} />,
      title: 'Data Insights',
      description: 'Comprehensive data visualization and reporting',
      color: 'var(--black)'
    },
    {
      icon: <Newspaper size={32} />,
      title: 'Market News',
      description: 'Stay updated with latest market news and analysis',
      color: 'var(--red)'
    },
    {
      icon: <Zap size={32} />,
      title: 'Fast Updates',
      description: 'Get instant updates and real-time data synchronization',
      color: 'var(--green)'
    },
    {
      icon: <Shield size={32} />,
      title: 'Secure Platform',
      description: 'Enterprise-grade security and data protection',
      color: 'var(--black)'
    }
  ]

  const quickLinks = [
    { name: 'FII/DII Data', tab: 'fiidii', icon: <Database size={20} /> },
    { name: 'NIFTY Options', tab: 'option-chain', icon: <BarChart3 size={20} /> },
    { name: 'BANKNIFTY', tab: 'banknifty', icon: <BarChart3 size={20} /> },
    { name: 'Top Gainers', tab: 'gainers', icon: <TrendingUp size={20} /> },
    { name: 'Top Losers', tab: 'losers', icon: <TrendingDown size={20} /> },
    { name: 'News Analysis', tab: 'news', icon: <Newspaper size={20} /> }
  ]

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background"></div>
        <div className="hero-container">
          <div className="hero-content">
            <div className="hero-badge">
              <Activity size={18} />
              <span>Live Data Dashboard</span>
              <div className="badge-pulse"></div>
            </div>
            <h1 className="hero-title">
              Welcome to <span className="gradient-text">X Fin AI</span>
            </h1>
            <p className="hero-description">
              Comprehensive financial data analytics platform for NSE market data collection,
              analysis, and insights. Real-time monitoring of option chains, institutional flows,
              and market sentiment.
            </p>
            <div className="hero-stats">
              <div className="hero-stat-card">
                <div className="stat-icon-wrapper">
                  <Clock size={28} />
                </div>
                <div className="stat-content">
                  <div className="hero-stat-value">24/7</div>
                  <div className="hero-stat-label">System Availability</div>
                </div>
              </div>
              <div className="hero-stat-card">
                <div className="stat-icon-wrapper">
                  <Zap size={28} />
                </div>
                <div className="stat-content">
                  <div className="hero-stat-value">Real-Time</div>
                  <div className="hero-stat-label">Data Updates</div>
                </div>
              </div>
              <div className="hero-stat-card">
                <div className="stat-icon-wrapper success">
                  <CheckCircle size={28} />
                </div>
                <div className="stat-content">
                  <div className="hero-stat-value">Active</div>
                  <div className="hero-stat-label">Platform Status</div>
                </div>
              </div>
            </div>
            <div className="hero-actions">
              <button 
                className="hero-cta-btn primary"
                onClick={() => onNavigate('fiidii')}
              >
                Explore Dashboard
                <ArrowRight size={20} />
              </button>
              <button 
                className="hero-cta-btn secondary"
                onClick={() => {
                  const element = document.querySelector('.features-section');
                  element?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Learn More
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="hero-visual-background">
              <div className="visual-glow"></div>
            </div>
            <div className="hero-card-grid">
              <div className="hero-card mini-card-1">
                <div className="card-icon-wrapper">
                  <TrendingUp size={28} />
                </div>
                <span>Live Data</span>
                <div className="card-badge">Real-time</div>
              </div>
              <div className="hero-card mini-card-2">
                <div className="card-icon-wrapper">
                  <BarChart3 size={28} />
                </div>
                <span>Analytics</span>
                <div className="card-badge">Advanced</div>
              </div>
              <div className="hero-card mini-card-3">
                <div className="card-icon-wrapper">
                  <Database size={28} />
                </div>
                <span>Storage</span>
                <div className="card-badge">Secure</div>
              </div>
              <div className="hero-card mini-card-4">
                <div className="card-icon-wrapper">
                  <Zap size={28} />
                </div>
                <span>Auto Sync</span>
                <div className="card-badge">Instant</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* AI Model Launch Announcement */}
      <section className="launch-section">
        <div className="launch-background">
          <div className="launch-glow-1"></div>
          <div className="launch-glow-2"></div>
        </div>
        <div className="launch-container">
          <div className="launch-header">
            <div className="launch-badge-modern">
              <div className="badge-icon-wrapper">
                <Rocket size={18} />
              </div>
              <span className="badge-text">Launching Soon</span>
              <div className="badge-pulse"></div>
            </div>
            <h2 className="launch-title-modern">
              <span className="title-word">We're Launching</span>
              <span className="launch-highlight-modern">
                <span className="highlight-text">X Fin AI Model</span>
                <span className="highlight-glow"></span>
                <span className="highlight-sparkle"></span>
              </span>
            </h2>
            <p className="launch-subtitle-modern">
              Revolutionary AI-powered trading model that predicts market movements with unprecedented accuracy. 
              Join the countdown and be among the first to experience next-generation financial intelligence.
            </p>
            <div className="launch-timer-label">
              <Clock size={18} />
              <span>Official Launch Countdown</span>
            </div>
          </div>

          <div className="launch-content-grid">
            {/* Left Side - Signals */}
            <div className="launch-left">
              <div className="ai-signals-demo">
                <h3 className="signals-title">AI Signals</h3>
                <div className="signals-container">
                  <div className="signal-item buy-signal">
                    <TrendingUp size={18} className="signal-icon-inline" />
                    <div className="signal-content">
                      <div className="signal-stock">NIFTY 50</div>
                      <div className="signal-meta">
                        <span className="signal-type">BUY</span>
                        <span className="signal-confidence">94.5%</span>
                      </div>
                    </div>
                    <div className="signal-price">₹22,450</div>
                  </div>
                  <div className="signal-item sell-signal">
                    <TrendingDown size={18} className="signal-icon-inline" />
                    <div className="signal-content">
                      <div className="signal-stock">BANKNIFTY</div>
                      <div className="signal-meta">
                        <span className="signal-type">SELL</span>
                        <span className="signal-confidence">87.2%</span>
                      </div>
                    </div>
                    <div className="signal-price">₹48,320</div>
                  </div>
                  <div className="signal-item buy-signal">
                    <TrendingUp size={18} className="signal-icon-inline" />
                    <div className="signal-content">
                      <div className="signal-stock">FINNIFTY</div>
                      <div className="signal-meta">
                        <span className="signal-type">BUY</span>
                        <span className="signal-confidence">91.8%</span>
                      </div>
                    </div>
                    <div className="signal-price">₹19,780</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Side - Chart & Countdown */}
            <div className="launch-right">
              <div className="chart-container-compact">
                <div className="chart-header-compact">
                  <span className="chart-symbol">NIFTY 50</span>
                  <span className="chart-price positive">₹22,450.75 <TrendingUp size={14} /></span>
                </div>
                <div className="chart-area-compact">
                  <svg className="chart-svg-compact" viewBox="0 0 300 120">
                    <line x1="0" y1="30" x2="300" y2="30" stroke="#e5e7eb" strokeWidth="1" strokeDasharray="3"/>
                    <line x1="0" y1="60" x2="300" y2="60" stroke="#e5e7eb" strokeWidth="1" strokeDasharray="3"/>
                    <line x1="0" y1="90" x2="300" y2="90" stroke="#e5e7eb" strokeWidth="1" strokeDasharray="3"/>
                    
                    <rect x="15" y="80" width="8" height="25" fill="#10b981" className="candle"/>
                    <line x1="19" y1="70" x2="19" y2="80" stroke="#10b981" strokeWidth="1.5"/>
                    <rect x="35" y="65" width="8" height="20" fill="#10b981" className="candle"/>
                    <line x1="39" y1="55" x2="39" y2="65" stroke="#10b981" strokeWidth="1.5"/>
                    <rect x="55" y="50" width="8" height="35" fill="#10b981" className="candle"/>
                    <line x1="59" y1="40" x2="59" y2="50" stroke="#10b981" strokeWidth="1.5"/>
                    <rect x="75" y="70" width="8" height="20" fill="#ef4444" className="candle"/>
                    <line x1="79" y1="60" x2="79" y2="70" stroke="#ef4444" strokeWidth="1.5"/>
                    <rect x="95" y="55" width="8" height="40" fill="#10b981" className="candle"/>
                    <line x1="99" y1="45" x2="99" y2="55" stroke="#10b981" strokeWidth="1.5"/>
                    <rect x="115" y="70" width="8" height="20" fill="#ef4444" className="candle"/>
                    <line x1="119" y1="60" x2="119" y2="70" stroke="#ef4444" strokeWidth="1.5"/>
                    <rect x="135" y="35" width="8" height="50" fill="#10b981" className="candle"/>
                    <line x1="139" y1="25" x2="139" y2="35" stroke="#10b981" strokeWidth="1.5"/>
                    <rect x="155" y="45" width="8" height="35" fill="#10b981" className="candle"/>
                    <line x1="159" y1="35" x2="159" y2="45" stroke="#10b981" strokeWidth="1.5"/>
                    <rect x="175" y="30" width="8" height="55" fill="#10b981" className="candle"/>
                    <line x1="179" y1="20" x2="179" y2="30" stroke="#10b981" strokeWidth="1.5"/>
                    <rect x="195" y="40" width="8" height="50" fill="#10b981" className="candle"/>
                    <line x1="199" y1="30" x2="199" y2="40" stroke="#10b981" strokeWidth="1.5"/>
                    <rect x="215" y="25" width="8" height="60" fill="#10b981" className="candle"/>
                    <line x1="219" y1="15" x2="219" y2="25" stroke="#10b981" strokeWidth="1.5"/>
                    
                    <polyline points="19,95 39,80 59,67 79,80 99,75 119,80 139,60 159,62 179,57 199,65 219,57" 
                      fill="none" stroke="#10b981" strokeWidth="2" opacity="0.5" className="trend-line"/>
                    
                    <circle cx="219" cy="57" r="4" fill="#10b981" className="prediction-marker">
                      <animate attributeName="r" values="4;6;4" dur="2s" repeatCount="indefinite"/>
                      <animate attributeName="opacity" values="1;0.7;1" dur="2s" repeatCount="indefinite"/>
                    </circle>
                  </svg>
                </div>
              </div>

              <div className="countdown-container-compact">
                <div className="countdown-title-compact">
                  <Rocket size={16} />
                  <span>Until X Fin AI Goes Live</span>
                </div>
                <div className="countdown-grid-compact">
                  <div className="countdown-item-compact">
                    <div className="countdown-value-compact">{String(timeLeft.days).padStart(2, '0')}</div>
                    <div className="countdown-label-compact">Days</div>
                  </div>
                  <div className="countdown-separator-compact">:</div>
                  <div className="countdown-item-compact">
                    <div className="countdown-value-compact">{String(timeLeft.hours).padStart(2, '0')}</div>
                    <div className="countdown-label-compact">Hours</div>
                  </div>
                  <div className="countdown-separator-compact">:</div>
                  <div className="countdown-item-compact">
                    <div className="countdown-value-compact">{String(timeLeft.minutes).padStart(2, '0')}</div>
                    <div className="countdown-label-compact">Min</div>
                  </div>
                  <div className="countdown-separator-compact">:</div>
                  <div className="countdown-item-compact">
                    <div className="countdown-value-compact">{String(timeLeft.seconds).padStart(2, '0')}</div>
                    <div className="countdown-label-compact">Sec</div>
                  </div>
                </div>
                <div className="countdown-note">
                  Get ready for the most advanced AI trading model launch
                </div>
              </div>
            </div>
          </div>

          <div className="launch-cta-compact">
            <button className="notify-btn-compact primary">
              <Mail size={16} />
              Notify Me
            </button>
            <button className="notify-btn-compact" onClick={() => onNavigate('fiidii')}>
              <Activity size={16} />
              Explore Dashboard
            </button>
          </div>
        </div>
      </section>

      {/* Exclusive Access Section */}
      <section className="access-section">
        <div className="access-container-modern">
          <div className="access-header-modern">
            <div className="access-badge-modern">
              <Crown size={20} />
              <span>Limited Access</span>
            </div>
            <h2 className="access-title-modern">
              Join the <span className="access-gold">Top 10</span> Elite Users
            </h2>
            <p className="access-desc-modern">
              Exclusive monthly access to X Fin AI. New bidding opens at the start of each month. Bid to secure your spot among the elite 10 users.
            </p>
          </div>

          <div className="access-main-grid">
            {/* Process Steps */}
            <div className="process-card">
              <h3 className="card-title-modern">
                <Target size={22} />
                How It Works
              </h3>
              <div className="steps-modern">
                <div className="step-modern">
                  <div className="step-badge">1</div>
                  <div className="step-text">
                    <h4>Place Your Bid</h4>
                    <p>When bidding opens, submit your bid for monthly access</p>
                  </div>
                </div>
                <div className="step-modern">
                  <div className="step-badge">2</div>
                  <div className="step-text">
                    <h4>Top 10 Win</h4>
                    <p>Highest 10 bidders get monthly access. Others get instant refund</p>
                  </div>
                </div>
                <div className="step-modern">
                  <div className="step-badge">3</div>
                  <div className="step-text">
                    <h4>Monthly Renewal</h4>
                    <p>At month end, new bidding starts. Top 10 bidders get access for next month</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Benefits */}
            <div className="benefits-card-modern">
              <h3 className="card-title-modern">
                <Award size={22} />
                Elite Benefits
              </h3>
              <div className="benefits-modern">
                <div className="benefit-modern">
                  <IndianRupee size={20} />
                  <div>
                    <strong>Massive Daily Profits</strong>
                    <span>Premium AI predictions for maximum returns</span>
                  </div>
                </div>
                <div className="benefit-modern">
                  <Clock size={20} />
                  <div>
                    <strong>Monthly Access</strong>
                    <span>New bidding cycle every month. Top 10 renew their access</span>
                  </div>
                </div>
                <div className="benefit-modern">
                  <MessageCircle size={20} />
                  <div>
                    <strong>Live Support</strong>
                    <span>9:00 AM - 6:30 PM IST dedicated help</span>
                  </div>
                </div>
                <div className="benefit-modern">
                  <Users size={20} />
                  <div>
                    <strong>Exclusive Community</strong>
                    <span>Only 10 elite users - quality over quantity</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bid Timer Section */}
          <div className="bid-section-modern">
            <div className="bid-card-premium">
              <div className="bid-header-premium">
                <div className="bid-icon-premium">
                  <Lock size={28} />
                  <div className="icon-glow"></div>
                </div>
                <div className="bid-title-group">
                  <h3 className="bid-title-premium">Bidding Opens In</h3>
                  <p className="bid-subtitle-premium">Secure your spot among the top 10</p>
                </div>
              </div>
              
              <div className="bid-timer-premium">
                <div className="timer-unit-premium">
                  <div className="timer-value-premium">
                    <span className="timer-number">{String(timeLeft.days).padStart(2, '0')}</span>
                  </div>
                  <div className="timer-label-premium">Days</div>
                </div>
                <div className="timer-separator-premium">:</div>
                <div className="timer-unit-premium">
                  <div className="timer-value-premium">
                    <span className="timer-number">{String(timeLeft.hours).padStart(2, '0')}</span>
                  </div>
                  <div className="timer-label-premium">Hours</div>
                </div>
                <div className="timer-separator-premium">:</div>
                <div className="timer-unit-premium">
                  <div className="timer-value-premium">
                    <span className="timer-number">{String(timeLeft.minutes).padStart(2, '0')}</span>
                  </div>
                  <div className="timer-label-premium">Minutes</div>
                </div>
                <div className="timer-separator-premium">:</div>
                <div className="timer-unit-premium">
                  <div className="timer-value-premium">
                    <span className="timer-number">{String(timeLeft.seconds).padStart(2, '0')}</span>
                  </div>
                  <div className="timer-label-premium">Seconds</div>
                </div>
              </div>

              <button className="bid-btn-premium" disabled>
                <div className="btn-icon-premium">
                  <IndianRupee size={20} />
                </div>
                <div className="btn-content-premium">
                  <span className="btn-text-premium">Join Bidding Queue</span>
                  <span className="btn-status-premium">Opens at Launch</span>
                </div>
                <div className="btn-shine"></div>
              </button>

              <div className="bid-footer-premium">
                <CheckCircle size={18} />
                <span>Top 10 bidders win monthly access. New bidding starts each month.</span>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="stats-modern">
            <div className="stat-box">
              <Crown size={28} />
              <div>
                <div className="stat-value-modern">10</div>
                <div className="stat-label-modern">Elite Users</div>
              </div>
            </div>
            <div className="stat-box">
              <TrendingUp size={28} />
              <div>
                <div className="stat-value-modern">Daily</div>
                <div className="stat-label-modern">Massive Profits</div>
              </div>
            </div>
            <div className="stat-box">
              <Shield size={28} />
              <div>
                <div className="stat-value-modern">100%</div>
                <div className="stat-label-modern">Refund Guarantee</div>
              </div>
            </div>
            <div className="stat-box">
              <Clock size={28} />
              <div>
                <div className="stat-value-modern">9:00-6:30</div>
                <div className="stat-label-modern">Live Support</div>
              </div>
            </div>
          </div>

          {/* Final CTA */}
          <div className="final-cta-modern">
            <h3>Ready to Become Elite?</h3>
            <p>Join the bidding when it opens each month. Top 10 bidders secure their access for the month</p>
            <button className="cta-btn-modern">
              <Mail size={18} />
              Notify Me When Bidding Opens
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-header">
          <h2 className="section-title">Platform Features</h2>
          <p className="section-subtitle">Powerful tools for financial data analysis</p>
        </div>
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon" style={{ color: feature.color }}>
                {feature.icon}
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Links Section */}
      <section className="quick-links-section">
        <div className="section-header">
          <h2 className="section-title">Quick Access</h2>
          <p className="section-subtitle">Jump to your favorite data views</p>
        </div>
        <div className="quick-links-grid">
          {quickLinks.map((link, index) => (
            <button
              key={index}
              className="quick-link-card"
              onClick={() => onNavigate(link.tab)}
            >
              <div className="quick-link-icon">
                {link.icon}
              </div>
              <span className="quick-link-name">{link.name}</span>
              <ArrowRight size={16} className="quick-link-arrow" />
            </button>
          ))}
        </div>
      </section>

      {/* Benefits Section */}
      <section className="benefits-section">
        <div className="section-header">
          <h2 className="section-title">Why Choose Our Platform</h2>
          <p className="section-subtitle">Experience the power of advanced financial analytics</p>
        </div>
        <div className="benefits-grid">
          <div className="benefit-card">
            <div className="benefit-icon">
              <Zap size={32} />
            </div>
            <h3 className="benefit-title">Lightning Fast</h3>
            <p className="benefit-description">Ultra-fast data processing and real-time updates for instant insights</p>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">
              <Shield size={32} />
            </div>
            <h3 className="benefit-title">Bank-Level Security</h3>
            <p className="benefit-description">Your data is protected with enterprise-grade security measures</p>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">
              <LineChart size={32} />
            </div>
            <h3 className="benefit-title">Advanced Analytics</h3>
            <p className="benefit-description">Powerful analytical tools to help you make informed decisions</p>
          </div>
        </div>
      </section>

      {/* Platform Highlights */}
      <section className="highlights-section">
        <div className="section-header">
          <h2 className="section-title">Platform Highlights</h2>
          <p className="section-subtitle">Everything you need in one powerful platform</p>
        </div>
        <div className="highlights-container">
          <div className="highlight-item">
            <div className="highlight-number">01</div>
            <div className="highlight-content">
              <h3>Comprehensive Dashboard</h3>
              <p>Access all your data and insights from a unified, intuitive dashboard</p>
            </div>
          </div>
          <div className="highlight-item">
            <div className="highlight-number">02</div>
            <div className="highlight-content">
              <h3>Customizable Views</h3>
              <p>Organize and view data exactly how you need it for your workflow</p>
            </div>
          </div>
          <div className="highlight-item">
            <div className="highlight-number">03</div>
            <div className="highlight-content">
              <h3>Export & Share</h3>
              <p>Easily export data and share insights with your team or clients</p>
            </div>
          </div>
          <div className="highlight-item">
            <div className="highlight-number">04</div>
            <div className="highlight-content">
              <h3>Mobile Responsive</h3>
              <p>Access your dashboard from any device, anywhere, anytime</p>
            </div>
          </div>
        </div>
      </section>

      {/* About Us Section */}
      <section className="about-section">
        <div className="about-background-decoration"></div>
        <div className="about-container">
          <div className="section-header">
            <h2 className="section-title">About Us</h2>
            <p className="section-subtitle">Empowering financial decisions through advanced analytics</p>
          </div>
          
          <div className="about-main-content">
            <div className="about-intro">
              <div className="about-intro-card">
                <div className="intro-icon">
                  <Activity size={32} />
                </div>
                <h3 className="intro-title">Who We Are</h3>
                <p className="intro-description">
                  X Fin AI is a cutting-edge financial analytics platform designed to provide comprehensive
                  market insights and data analysis tools. We combine advanced technology with deep financial
                  expertise to deliver actionable intelligence that helps professionals make informed decisions.
                </p>
              </div>
              <div className="about-intro-card">
                <div className="intro-icon">
                  <LineChart size={32} />
                </div>
                <h3 className="intro-title">What We Do</h3>
                <p className="intro-description">
                  Our platform leverages real-time data processing, sophisticated analytics engines, and intuitive
                  visualization tools to transform complex financial data into clear, actionable insights. Whether
                  you're tracking market trends, analyzing institutional flows, or monitoring market sentiment,
                  X Fin AI provides the tools you need to stay ahead.
                </p>
              </div>
            </div>

            <div className="about-values-section">
              <h3 className="values-title">Our Core Values</h3>
              <div className="values-grid">
                <div className="value-card">
                  <div className="value-card-header">
                    <CheckCircle size={28} className="value-icon" />
                    <h4>Mission</h4>
                  </div>
                  <p>Democratize access to professional-grade financial analytics for everyone, making advanced market insights accessible to all.</p>
                </div>
                <div className="value-card">
                  <div className="value-card-header">
                    <TrendingUp size={28} className="value-icon" />
                    <h4>Vision</h4>
                  </div>
                  <p>Become the leading platform for financial data intelligence, setting new standards in market analytics and insights.</p>
                </div>
                <div className="value-card">
                  <div className="value-card-header">
                    <Shield size={28} className="value-icon" />
                    <h4>Values</h4>
                  </div>
                  <p>Innovation, Reliability, Security, and User-Centric Design - these principles guide everything we build.</p>
                </div>
              </div>
            </div>

            <div className="about-stats-section">
              <div className="about-stat-card">
                <div className="about-stat-icon">
                  <CheckCircle size={32} />
                </div>
                <div className="about-stat-content">
                  <div className="about-stat-number">100%</div>
                  <div className="about-stat-label">Uptime Guarantee</div>
                  <div className="about-stat-description">Reliable infrastructure</div>
                </div>
              </div>
              <div className="about-stat-card">
                <div className="about-stat-icon">
                  <Clock size={32} />
                </div>
                <div className="about-stat-content">
                  <div className="about-stat-number">24/7</div>
                  <div className="about-stat-label">Support Available</div>
                  <div className="about-stat-description">Always here to help</div>
                </div>
              </div>
              <div className="about-stat-card">
                <div className="about-stat-icon">
                  <BarChart3 size={32} />
                </div>
                <div className="about-stat-content">
                  <div className="about-stat-number">99.9%</div>
                  <div className="about-stat-label">Data Accuracy</div>
                  <div className="about-stat-description">Precision guaranteed</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Us Section */}
      <section className="contact-section">
        <div className="contact-container">
          <div className="section-header">
            <h2 className="section-title">Get In Touch</h2>
            <p className="section-subtitle">Have questions? We'd love to hear from you</p>
          </div>
          <div className="contact-grid">
            <div className="contact-info">
              <h3 className="contact-info-title">Contact Information</h3>
              <p className="contact-info-description">
                Reach out to us through any of these channels. Our team is ready to assist you.
              </p>
              <div className="contact-details">
                <div className="contact-detail-item">
                  <div className="contact-icon-wrapper">
                    <Mail size={24} />
                  </div>
                  <div className="contact-detail-content">
                    <h4>Email</h4>
                    <p>support@xfinai.com</p>
                    <p>info@xfinai.com</p>
                  </div>
                </div>
                <div className="contact-detail-item">
                  <div className="contact-icon-wrapper">
                    <Phone size={24} />
                  </div>
                  <div className="contact-detail-content">
                    <h4>Phone</h4>
                    <p>+91 XXX XXX XXXX</p>
                    <p>Mon - Fri, 9:00 AM - 6:00 PM IST</p>
                  </div>
                </div>
                <div className="contact-detail-item">
                  <div className="contact-icon-wrapper">
                    <MapPin size={24} />
                  </div>
                  <div className="contact-detail-content">
                    <h4>Address</h4>
                    <p>Mumbai, Maharashtra</p>
                    <p>India</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="contact-form-wrapper">
              <form className="contact-form" onSubmit={(e) => e.preventDefault()}>
                <div className="form-group">
                  <label htmlFor="name">Full Name</label>
                  <input 
                    type="text" 
                    id="name" 
                    name="name" 
                    placeholder="John Doe"
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="email">Email Address</label>
                  <input 
                    type="email" 
                    id="email" 
                    name="email" 
                    placeholder="john@example.com"
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="subject">Subject</label>
                  <input 
                    type="text" 
                    id="subject" 
                    name="subject" 
                    placeholder="How can we help?"
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="message">Message</label>
                  <textarea 
                    id="message" 
                    name="message" 
                    rows="5"
                    placeholder="Tell us about your inquiry..."
                    className="form-textarea"
                  ></textarea>
                </div>
                <button type="submit" className="form-submit-btn">
                  Send Message
                  <Send size={18} />
                </button>
              </form>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default HomePage

