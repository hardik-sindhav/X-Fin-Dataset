import React from 'react'
import { Activity, Linkedin, Youtube, Instagram, FileText, HelpCircle, Shield, TrendingUp, BarChart3, Database, Zap, IndianRupee, Cookie, AlertTriangle } from 'lucide-react'
import '../App.css'

function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-main">
          <div className="footer-section footer-brand-section">
            <div className="footer-brand">
              <div className="footer-logo">
                <Activity size={28} />
              </div>
              <h3 className="footer-brand-title">X Fin AI</h3>
              <p className="footer-brand-description">
                Advanced Financial Intelligence Platform powered by AI. 
                Real-time market data, sentiment analysis, and intelligent insights 
                for informed trading decisions.
              </p>
            </div>
            <div className="footer-social">
              <h4 className="footer-social-title">Follow Us</h4>
              <div className="footer-social-links">
                <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" className="social-link" title="YouTube" aria-label="YouTube">
                  <Youtube size={20} />
                </a>
                <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" className="social-link" title="Instagram" aria-label="Instagram">
                  <Instagram size={20} />
                </a>
                <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="social-link" title="LinkedIn" aria-label="LinkedIn">
                  <Linkedin size={20} />
                </a>
              </div>
            </div>
          </div>

          <div className="footer-section">
            <h4 className="footer-heading">Platform</h4>
            <ul className="footer-links">
              <li>
                <a href="#home" className="footer-link">
                  <Activity size={16} />
                  Home
                </a>
              </li>
              <li>
                <a href="#dashboard" className="footer-link">
                  <BarChart3 size={16} />
                  Dashboard
                </a>
              </li>
              <li>
                <a href="#features" className="footer-link">
                  <Zap size={16} />
                  Features
                </a>
              </li>
              <li>
                <a href="#data" className="footer-link">
                  <Database size={16} />
                  Market Data
                </a>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h4 className="footer-heading">Resources</h4>
            <ul className="footer-links">
              <li>
                <a href="#documentation" className="footer-link">
                  <FileText size={16} />
                  Documentation
                </a>
              </li>
              <li>
                <a href="#support" className="footer-link">
                  <HelpCircle size={16} />
                  Support Center
                </a>
              </li>
              <li>
                <a href="#api" className="footer-link">
                  <TrendingUp size={16} />
                  API Access
                </a>
              </li>
              <li>
                <a 
                  href="#pricing" 
                  className="footer-link"
                  onClick={(e) => {
                    e.preventDefault()
                    window.location.hash = '#pricing'
                  }}
                >
                  <IndianRupee size={16} />
                  Pricing Plans
                </a>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h4 className="footer-heading">Legal</h4>
            <ul className="footer-links">
              <li>
                <a href="#privacy" className="footer-link">
                  <Shield size={16} />
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#terms" className="footer-link">
                  <FileText size={16} />
                  Terms of Service
                </a>
              </li>
              <li>
                <a href="#cookies" className="footer-link">
                  <Cookie size={16} />
                  Cookie Policy
                </a>
              </li>
              <li>
                <a href="#disclaimer" className="footer-link">
                  <AlertTriangle size={16} />
                  Disclaimer
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="footer-bottom-content">
            <p className="footer-copyright">
              &copy; {currentYear} X Fin AI. All rights reserved.
            </p>
            <p className="footer-note">
              Financial data is for informational purposes only. Not investment advice.
            </p>
          </div>
          <div className="footer-legal">
            <a href="#terms" className="footer-legal-link">Terms</a>
            <span className="footer-separator">·</span>
            <a href="#privacy" className="footer-legal-link">Privacy</a>
            <span className="footer-separator">·</span>
            <a href="#contact" className="footer-legal-link">Contact</a>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer

