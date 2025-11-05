import React from 'react'
import { 
  IndianRupee, 
  CheckCircle, 
  Database, 
  BarChart3, 
  Newspaper, 
  TrendingUp, 
  TrendingDown,
  Zap,
  Shield,
  Clock,
  ArrowRight,
  Code,
  Users,
  Crown,
  Sparkles,
  Brain,
  Target,
  Star,
  Activity,
  BarChart,
  FileText,
  Mail,
  BookOpen,
  Globe,
  FileJson,
  RefreshCw,
  Download,
  Webhook,
  Lock,
  MessageSquare,
  Infinity,
  Headphones
} from 'lucide-react'
import '../App.css'

function Pricing({ onNavigate }) {
  // Function to get appropriate icon for each feature
  const getFeatureIcon = (featureText) => {
    const text = featureText.toLowerCase()
    
    if (text.includes('option chain')) return <BarChart3 size={6} />
    if (text.includes('ohlc')) return <TrendingUp size={6} />
    if (text.includes('news') || text.includes('sentiment')) return <Newspaper size={6} />
    if (text.includes('gainer')) return <TrendingUp size={6} />
    if (text.includes('loser')) return <TrendingDown size={6} />
    if (text.includes('fii') || text.includes('dii')) return <Users size={6} />
    if (text.includes('api call')) return <Zap size={6} />
    if (text.includes('support') || text.includes('manager')) return <Headphones size={6} />
    if (text.includes('documentation') || text.includes('document')) return <BookOpen size={6} />
    if (text.includes('webhook')) return <Webhook size={6} />
    if (text.includes('export') || text.includes('csv') || text.includes('json')) return <Download size={6} />
    if (text.includes('restful') || text.includes('api access')) return <Globe size={6} />
    if (text.includes('json response')) return <FileJson size={6} />
    if (text.includes('real-time') || text.includes('streaming') || text.includes('update')) return <RefreshCw size={6} />
    if (text.includes('rate limit')) return <Activity size={6} />
    if (text.includes('ssl') || text.includes('https') || text.includes('encryption')) return <Lock size={6} />
    if (text.includes('unlimited')) return <Infinity size={6} />
    if (text.includes('custom') || text.includes('integration')) return <Code size={6} />
    if (text.includes('email')) return <Mail size={6} />
    
    // Default icon
    return <CheckCircle size={6} />
  }

  const plans = [
    {
      name: 'Starter',
      price: 2999,
      period: 'month',
      description: 'Perfect for developers getting started with financial data',
      icon: <Code size={24} />,
      color: 'var(--black)',
      popular: false,
      badge: null,
      features: [
        'Option Chain Data (NIFTY, BANKNIFTY)',
        'OHLC Data Access',
        'News with Sentiment Analysis',
        'Top 20 Gainers Data',
        'Top 20 Losers Data',
        'FII/DII Data',
        '10,000 API Calls/month',
        'Email Support',
        'Basic Documentation',
        'RESTful API Access',
        'JSON Response Format'
      ],
      aiModel: null,
      limitations: [
        'Limited to 2 data endpoints',
        'Standard response time',
        'No AI Model Access'
      ]
    },
    {
      name: 'Professional',
      price: 7999,
      period: 'month',
      description: 'Best for serious developers building production applications with AI predictions',
      icon: <Zap size={24} />,
      color: 'var(--green)',
      popular: true,
      badge: 'Most Popular',
      features: [
        'All Option Chain Data (All Indices & Banks)',
        'Complete OHLC Historical Data',
        'News with Sentiment Analysis',
        'Top 20 Gainers & Losers',
        'FII/DII Data',
        'Real-time Data Updates',
        '100,000 API Calls/month',
        'Priority Email Support',
        'Full API Documentation',
        'Webhook Support',
        'Data Export (CSV/JSON)',
        'Rate Limiting: 100 req/min',
        'SSL/HTTPS Encryption'
      ],
      aiModel: {
        name: 'X Fin Model Basic',
        signals: 20,
        accuracy: '60-65%',
        description: 'AI-powered trading signals with basic prediction model'
      },
      limitations: []
    },
    {
      name: 'Enterprise',
      price: 19999,
      period: 'month',
      description: 'For large teams and organizations requiring unlimited access and advanced AI',
      icon: <Crown size={24} />,
      color: 'var(--black)',
      popular: false,
      badge: 'Best Value',
      features: [
        'Unlimited Option Chain Data',
        'Complete OHLC Historical Data',
        'News with Sentiment Analysis',
        'Top 20 Gainers & Losers',
        'FII/DII Data',
        'Real-time Data Streaming',
        'Unlimited API Calls',
        'Dedicated Support Manager',
        'Custom Integration Support',
        'Advanced Webhook Features',
        'Data Export (Multiple Formats)',
        'SLA Guarantee (99.9% Uptime)',
        'Custom Data Requirements',
        'Team Collaboration Tools',
        'Priority Data Refresh',
        'Custom Endpoints Available'
      ],
      aiModel: {
        name: 'X Fin Model Pro',
        signals: 50,
        accuracy: '70-75%',
        description: 'Advanced AI model with higher accuracy predictions'
      },
      limitations: []
    }
  ]

  const dataTypes = [
    {
      icon: <BarChart3 size={20} />,
      name: 'Option Chain Data',
      description: 'Complete option chain data for all indices and stocks'
    },
    {
      icon: <Database size={20} />,
      name: 'OHLC Data',
      description: 'Historical Open, High, Low, Close data'
    },
    {
      icon: <Newspaper size={20} />,
      name: 'News with Sentiment',
      description: 'Market news with AI-powered sentiment analysis'
    },
    {
      icon: <TrendingUp size={20} />,
      name: 'Top Gainers',
      description: 'Top 20 gainers data with real-time updates'
    },
    {
      icon: <TrendingDown size={20} />,
      name: 'Top Losers',
      description: 'Top 20 losers data with real-time updates'
    },
    {
      icon: <Users size={20} />,
      name: 'FII/DII Data',
      description: 'Foreign and Domestic Institutional Investor data'
    }
  ]

  return (
    <div className="pricing-page">
      <div className="pricing-container">
        {/* Header Section */}
        <div className="pricing-header">
          <div className="pricing-badge">
            <Sparkles size={18} />
            <span>API Access Plans</span>
          </div>
          <h1 className="pricing-title">Choose Your Plan</h1>
          <p className="pricing-subtitle">
            Access comprehensive historical financial data through our powerful API. 
            All plans include access to option chain, OHLC data, news with sentiment, 
            top gainers/losers, and FII/DII data.
          </p>
        </div>

        {/* Data Types Section */}
        <div className="pricing-data-types">
          <h2 className="data-types-title">Available Data Types</h2>
          <div className="data-types-grid">
            {dataTypes.map((dataType, index) => (
              <div key={index} className="data-type-card">
                <div className="data-type-icon">
                  {dataType.icon}
                </div>
                <h3 className="data-type-name">{dataType.name}</h3>
                <p className="data-type-desc">{dataType.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Pricing Plans */}
        <div className="pricing-plans-grid">
          {plans.map((plan, index) => (
            <div 
              key={index} 
              className={`pricing-card ${plan.popular ? 'popular' : ''} ${plan.badge === 'Best Value' ? 'enterprise' : ''}`}
            >
              {plan.badge && (
                <div className={`popular-badge ${plan.badge === 'Best Value' ? 'enterprise-badge' : ''}`}>
                  {plan.badge === 'Most Popular' ? <Crown size={16} /> : <Star size={16} />}
                  <span>{plan.badge}</span>
                </div>
              )}
              
              <div className="plan-header">
                <div className="plan-icon-wrapper">
                  <div className="plan-icon" style={{ color: plan.color }}>
                    {plan.icon}
                  </div>
                </div>
                <h3 className="plan-name">{plan.name}</h3>
                <p className="plan-description">{plan.description}</p>
              </div>

              <div className="plan-pricing">
                <div className="price-wrapper">
                  <div className="price-container">
                    <span className="currency"><IndianRupee size={28} /></span>
                    <span className="price">{plan.price.toLocaleString('en-IN')}</span>
                  </div>
                  <span className="price-period">per {plan.period}</span>
                </div>
                {plan.aiModel && (
                  <div className="ai-model-badge">
                    <Brain size={18} />
                    <span>{plan.aiModel.name}</span>
                  </div>
                )}
              </div>

              {plan.aiModel && (
                <div className="ai-model-section">
                  <div className="ai-model-header">
                    <Brain size={20} className="ai-icon" />
                    <h4 className="ai-model-title">AI Prediction Signals</h4>
                  </div>
                  <div className="ai-model-details">
                    <div className="ai-model-stat">
                      <Target size={18} />
                      <div>
                        <span className="ai-stat-label">Signals</span>
                        <span className="ai-stat-value">{plan.aiModel.signals}/month</span>
                      </div>
                    </div>
                    <div className="ai-model-stat">
                      <BarChart size={18} />
                      <div>
                        <span className="ai-stat-label">Accuracy</span>
                        <span className="ai-stat-value">{plan.aiModel.accuracy}</span>
                      </div>
                    </div>
                  </div>
                  <p className="ai-model-desc">{plan.aiModel.description}</p>
                </div>
              )}

              <div className="plan-features">
                <h4 className="features-title">
                  <Database size={14} />
                  Data Features
                </h4>
                <ul className="features-list">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="feature-item">
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                {plan.limitations.length > 0 && (
                  <div className="plan-limitations">
                    <h4 className="limitations-title">Note:</h4>
                    <ul className="limitations-list">
                      {plan.limitations.map((limitation, limitIndex) => (
                        <li key={limitIndex} className="limitation-item">
                          <span>{limitation}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

                  <button
                    className={`plan-cta ${plan.popular ? 'primary' : plan.badge === 'Best Value' ? 'enterprise-cta' : 'secondary'}`}
                    onClick={() => {
                      // Handle plan selection
                      alert(`Selected ${plan.name} plan. Contact us to proceed.`)
                    }}
                  >
                    <span>Choose Plan</span>
                    <ArrowRight size={18} />
                  </button>
            </div>
          ))}
        </div>

        {/* FAQ or Additional Info */}
        <div className="pricing-info">
          <div className="info-card">
            <Shield size={24} />
            <h3>Secure & Reliable</h3>
            <p>All API calls are encrypted and authenticated. 99.9% uptime guarantee.</p>
          </div>
          <div className="info-card">
            <Clock size={24} />
            <h3>Real-Time Updates</h3>
            <p>Get instant updates with our real-time data streaming capabilities.</p>
          </div>
          <div className="info-card">
            <Database size={24} />
            <h3>Historical Data</h3>
            <p>Access comprehensive historical data going back years.</p>
          </div>
        </div>

        {/* Contact Section */}
        <div className="pricing-contact">
          <h2 className="contact-title">Need a Custom Plan?</h2>
          <p className="contact-description">
            We offer custom pricing for large-scale implementations and enterprise solutions.
          </p>
          <button 
            className="contact-btn"
            onClick={() => {
              const element = document.querySelector('.contact-section');
              if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
              }
            }}
          >
            Contact Sales
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default Pricing

