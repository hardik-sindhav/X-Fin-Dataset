import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Activity, 
  Clock, 
  Database, 
  RefreshCw, 
  Play, 
  TrendingUp, 
  TrendingDown,
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  Newspaper,
  MessageCircle,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Settings as SettingsIcon,
  Trash2,
  Filter,
  Calendar
} from 'lucide-react'
import Login from './components/Login'
import Settings from './components/Settings'
import DetailView from './components/DetailView'
import HeatmapView from './components/HeatmapView'
import './App.css'

import { API_BASE } from './config'

function App() {
  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authToken, setAuthToken] = useState(null)
  const [username, setUsername] = useState('')
  const [showLogoutDialog, setShowLogoutDialog] = useState(false)
  const [activeTab, setActiveTab] = useState('fiidii') // 'fiidii', 'option-chain', 'banknifty', 'finnifty', 'midcpnifty', 'hdfcbank', 'icicibank', 'sbin', 'kotakbank', 'axisbank', 'bankbaroda', 'pnb', 'canbk', 'aubank', 'indusindbk', 'idfcfirstb', 'federalbnk', 'gainers', 'losers', 'news', or 'livemint-news'
  
  // FII/DII state
  const [status, setStatus] = useState(null)
  const [data, setData] = useState([])
  const [stats, setStats] = useState(null)
  
  // Option Chain state
  const [optionChainStatus, setOptionChainStatus] = useState(null)
  const [optionChainData, setOptionChainData] = useState([])
  const [optionChainStats, setOptionChainStats] = useState(null)
  const [optionChainExpiry, setOptionChainExpiry] = useState(null)
  
  // BankNifty state
  const [bankniftyStatus, setBankniftyStatus] = useState(null)
  const [bankniftyData, setBankniftyData] = useState([])
  const [bankniftyStats, setBankniftyStats] = useState(null)
  const [bankniftyExpiry, setBankniftyExpiry] = useState(null)
  
  // Finnifty state
  const [finniftyStatus, setFinniftyStatus] = useState(null)
  const [finniftyData, setFinniftyData] = useState([])
  const [finniftyStats, setFinniftyStats] = useState(null)
  const [finniftyExpiry, setFinniftyExpiry] = useState(null)
  
  // MidcapNifty state
  const [midcpniftyStatus, setMidcpniftyStatus] = useState(null)
  const [midcpniftyData, setMidcpniftyData] = useState([])
  const [midcpniftyStats, setMidcpniftyStats] = useState(null)
  const [midcpniftyExpiry, setMidcpniftyExpiry] = useState(null)
  
  // HDFC Bank state
  const [hdfcbankStatus, setHdfcbankStatus] = useState(null)
  const [hdfcbankData, setHdfcbankData] = useState([])
  const [hdfcbankStats, setHdfcbankStats] = useState(null)
  const [hdfcbankExpiry, setHdfcbankExpiry] = useState(null)
  
  // ICICI Bank state
  const [icicibankStatus, setIcicibankStatus] = useState(null)
  const [icicibankData, setIcicibankData] = useState([])
  const [icicibankStats, setIcicibankStats] = useState(null)
  const [icicibankExpiry, setIcicibankExpiry] = useState(null)
  
  // SBIN state
  const [sbinStatus, setSbinStatus] = useState(null)
  const [sbinData, setSbinData] = useState([])
  const [sbinStats, setSbinStats] = useState(null)
  const [sbinExpiry, setSbinExpiry] = useState(null)
  
  // Kotak Bank state
  const [kotakbankStatus, setKotakbankStatus] = useState(null)
  const [kotakbankData, setKotakbankData] = useState([])
  const [kotakbankStats, setKotakbankStats] = useState(null)
  const [kotakbankExpiry, setKotakbankExpiry] = useState(null)
  
  // Axis Bank state
  const [axisbankStatus, setAxisbankStatus] = useState(null)
  const [axisbankData, setAxisbankData] = useState([])
  const [axisbankStats, setAxisbankStats] = useState(null)
  const [axisbankExpiry, setAxisbankExpiry] = useState(null)
  
  // Bank of Baroda state
  const [bankbarodaStatus, setBankbarodaStatus] = useState(null)
  const [bankbarodaData, setBankbarodaData] = useState([])
  const [bankbarodaStats, setBankbarodaStats] = useState(null)
  const [bankbarodaExpiry, setBankbarodaExpiry] = useState(null)
  
  // PNB state
  const [pnbStatus, setPnbStatus] = useState(null)
  const [pnbData, setPnbData] = useState([])
  const [pnbStats, setPnbStats] = useState(null)
  const [pnbExpiry, setPnbExpiry] = useState(null)
  
  // CANBK state
  const [canbkStatus, setCanbkStatus] = useState(null)
  const [canbkData, setCanbkData] = useState([])
  const [canbkStats, setCanbkStats] = useState(null)
  const [canbkExpiry, setCanbkExpiry] = useState(null)
  
  // AUBANK state
  const [aubankStatus, setAubankStatus] = useState(null)
  const [aubankData, setAubankData] = useState([])
  const [aubankStats, setAubankStats] = useState(null)
  const [aubankExpiry, setAubankExpiry] = useState(null)
  
  // INDUSINDBK state
  const [indusindbkStatus, setIndusindbkStatus] = useState(null)
  const [indusindbkData, setIndusindbkData] = useState([])
  const [indusindbkStats, setIndusindbkStats] = useState(null)
  const [indusindbkExpiry, setIndusindbkExpiry] = useState(null)
  
  // IDFCFIRSTB state
  const [idfcfirstbStatus, setIdfcfirstbStatus] = useState(null)
  const [idfcfirstbData, setIdfcfirstbData] = useState([])
  const [idfcfirstbStats, setIdfcfirstbStats] = useState(null)
  const [idfcfirstbExpiry, setIdfcfirstbExpiry] = useState(null)
  
  // FEDERALBNK state
  const [federalbnkStatus, setFederalbnkStatus] = useState(null)
  const [federalbnkData, setFederalbnkData] = useState([])
  const [federalbnkStats, setFederalbnkStats] = useState(null)
  const [federalbnkExpiry, setFederalbnkExpiry] = useState(null)
  
  // News state
  const [newsStatus, setNewsStatus] = useState(null)
  const [newsData, setNewsData] = useState([])
  const [newsStats, setNewsStats] = useState(null)
  
  // LiveMint News state
  const [livemintNewsStatus, setLivemintNewsStatus] = useState(null)
  const [livemintNewsData, setLivemintNewsData] = useState([])
  const [livemintNewsStats, setLivemintNewsStats] = useState(null)
  
  // Gainers state
  const [gainersStatus, setGainersStatus] = useState(null)
  const [gainersData, setGainersData] = useState([])
  const [gainersStats, setGainersStats] = useState(null)
  
  // Losers state
  const [losersStatus, setLosersStatus] = useState(null)
  const [losersData, setLosersData] = useState([])
  const [losersStats, setLosersStats] = useState(null)
  
  // Heatmap state
  const [heatmapGainersData, setHeatmapGainersData] = useState(null)
  const [heatmapLosersData, setHeatmapLosersData] = useState(null)
  const [heatmapLoading, setHeatmapLoading] = useState(false)
  
  const [loading, setLoading] = useState(false)
  const [loadingTab, setLoadingTab] = useState(null)
  const [loadedTabs, setLoadedTabs] = useState(new Set())
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  // Pagination state for each tab
  const [pagination, setPagination] = useState({})
  const RECORDS_PER_PAGE = 15
  const [triggering, setTriggering] = useState(false)
  const [optionChainTriggering, setOptionChainTriggering] = useState(false)
  const [bankniftyTriggering, setBankniftyTriggering] = useState(false)
  const [finniftyTriggering, setFinniftyTriggering] = useState(false)
  const [midcpniftyTriggering, setMidcpniftyTriggering] = useState(false)
  const [hdfcbankTriggering, setHdfcbankTriggering] = useState(false)
  const [icicibankTriggering, setIcicibankTriggering] = useState(false)
  const [sbinTriggering, setSbinTriggering] = useState(false)
  const [kotakbankTriggering, setKotakbankTriggering] = useState(false)
  const [axisbankTriggering, setAxisbankTriggering] = useState(false)
  const [bankbarodaTriggering, setBankbarodaTriggering] = useState(false)
  const [pnbTriggering, setPnbTriggering] = useState(false)
  const [canbkTriggering, setCanbkTriggering] = useState(false)
  const [aubankTriggering, setAubankTriggering] = useState(false)
  const [indusindbkTriggering, setIndusindbkTriggering] = useState(false)
  const [idfcfirstbTriggering, setIdfcfirstbTriggering] = useState(false)
  const [federalbnkTriggering, setFederalbnkTriggering] = useState(false)
  const [gainersTriggering, setGainersTriggering] = useState(false)
  const [losersTriggering, setLosersTriggering] = useState(false)
  const [newsTriggering, setNewsTriggering] = useState(false)
  const [livemintNewsTriggering, setLivemintNewsTriggering] = useState(false)
  
  // Date filters for each tab
  const [dateFilters, setDateFilters] = useState({})
  
  // Selected record for detail view
  const [selectedRecord, setSelectedRecord] = useState(null)
  const [selectedTabName, setSelectedTabName] = useState(null)
  
  // Config state
  const [config, setConfig] = useState(null)
  
  // Helper function to get scheduler type for a tab
  const getSchedulerTypeForTab = (tabName) => {
    const tabToSchedulerMap = {
      'fiidii': 'fiidii',
      'option-chain': 'indices',
      'banknifty': 'indices',
      'finnifty': 'indices',
      'midcpnifty': 'indices',
      'hdfcbank': 'banks',
      'icicibank': 'banks',
      'sbin': 'banks',
      'kotakbank': 'banks',
      'axisbank': 'banks',
      'bankbaroda': 'banks',
      'pnb': 'banks',
      'canbk': 'banks',
      'aubank': 'banks',
      'indusindbk': 'banks',
      'idfcfirstb': 'banks',
      'federalbnk': 'banks',
      'gainers': 'gainers_losers',
      'losers': 'gainers_losers',
      'news': 'news',
      'livemint-news': 'news'
    }
    return tabToSchedulerMap[tabName] || null
  }
  
  // Helper function to render config status items
  const renderConfigStatusItems = (tabName) => {
    const schedulerType = getSchedulerTypeForTab(tabName)
    if (!config || !schedulerType || !config[schedulerType]) {
      return null
    }
    const schedulerConfig = config[schedulerType]
    return (
      <>
        <StatusItem
          label="Start Time"
          value={schedulerConfig.start_time || 'N/A'}
          icon={Clock}
        />
        <StatusItem
          label="End Time"
          value={schedulerConfig.end_time || 'N/A'}
          icon={Clock}
        />
        <StatusItem
          label="Interval"
          value={schedulerConfig.interval_minutes ? `${schedulerConfig.interval_minutes} min` : 'N/A'}
          icon={Clock}
        />
      </>
    )
  }
  
  // Load config on mount
  useEffect(() => {
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
      }
    }
    if (isAuthenticated && authToken) {
      loadConfig()
    }
  }, [isAuthenticated, authToken])

  // Fetch data for a specific tab only if not already loaded
  const fetchTabData = async (tabName, forceRefresh = false, page = 1, startDate = null, endDate = null) => {
    setLoadingTab(tabName)

    try {
      const limit = RECORDS_PER_PAGE
      
      switch (tabName) {
        case 'fiidii':
          let dataUrl = `${API_BASE}/data?page=${page}&limit=${limit}`
          if (startDate) dataUrl += `&start_date=${startDate}`
          if (endDate) dataUrl += `&end_date=${endDate}`
          const [statusRes, dataRes, statsRes] = await Promise.all([
            axios.get(`${API_BASE}/status`),
            axios.get(dataUrl),
            axios.get(`${API_BASE}/stats`)
          ])
          setStatus(statusRes.data)
          setData(dataRes.data.data || [])
          setStats(statsRes.data.stats)
          // Update pagination state
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: dataRes.data.page || page,
              total: dataRes.data.total || 0,
              total_pages: dataRes.data.total_pages || 1,
              has_next: dataRes.data.has_next || false,
              has_prev: dataRes.data.has_prev || false
            }
          }))
          break

        case 'option-chain':
          let optDataUrl = `${API_BASE}/option-chain/data?page=${page}&limit=${limit}`
          if (startDate) optDataUrl += `&start_date=${startDate}`
          if (endDate) optDataUrl += `&end_date=${endDate}`
          const [optStatusRes, optDataRes, optStatsRes, optExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/option-chain/status`),
            axios.get(optDataUrl),
            axios.get(`${API_BASE}/option-chain/stats`),
            axios.get(`${API_BASE}/option-chain/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setOptionChainStatus(optStatusRes.data)
          setOptionChainData(optDataRes.data.data || [])
          setOptionChainStats(optStatsRes.data.stats)
          setOptionChainExpiry(optExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: optDataRes.data.page || page,
              total: optDataRes.data.total || 0,
              total_pages: optDataRes.data.total_pages || 1,
              has_next: optDataRes.data.has_next || false,
              has_prev: optDataRes.data.has_prev || false
            }
          }))
          break

        case 'banknifty':
          let bnDataUrl = `${API_BASE}/banknifty/data?page=${page}&limit=${limit}`
          if (startDate) bnDataUrl += `&start_date=${startDate}`
          if (endDate) bnDataUrl += `&end_date=${endDate}`
          const [bnStatusRes, bnDataRes, bnStatsRes, bnExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/banknifty/status`),
            axios.get(bnDataUrl),
            axios.get(`${API_BASE}/banknifty/stats`),
            axios.get(`${API_BASE}/banknifty/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setBankniftyStatus(bnStatusRes.data)
          setBankniftyData(bnDataRes.data.data || [])
          setBankniftyStats(bnStatsRes.data.stats)
          setBankniftyExpiry(bnExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: bnDataRes.data.page || page,
              total: bnDataRes.data.total || 0,
              total_pages: bnDataRes.data.total_pages || 1,
              has_next: bnDataRes.data.has_next || false,
              has_prev: bnDataRes.data.has_prev || false
            }
          }))
          break

        case 'finnifty':
          let fnDataUrl = `${API_BASE}/finnifty/data?page=${page}&limit=${limit}`
          if (startDate) fnDataUrl += `&start_date=${startDate}`
          if (endDate) fnDataUrl += `&end_date=${endDate}`
          const [fnStatusRes, fnDataRes, fnStatsRes, fnExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/finnifty/status`),
            axios.get(fnDataUrl),
            axios.get(`${API_BASE}/finnifty/stats`),
            axios.get(`${API_BASE}/finnifty/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setFinniftyStatus(fnStatusRes.data)
          setFinniftyData(fnDataRes.data.data || [])
          setFinniftyStats(fnStatsRes.data.stats)
          setFinniftyExpiry(fnExpiryRes.data.expiry || null)
          // Update pagination state
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: fnDataRes.data.page || page,
              total: fnDataRes.data.total || 0,
              total_pages: fnDataRes.data.total_pages || 1,
              has_next: fnDataRes.data.has_next || false,
              has_prev: fnDataRes.data.has_prev || false
            }
          }))
          break

        case 'midcpnifty':
          let midcpDataUrl = `${API_BASE}/midcpnifty/data?page=${page}&limit=${limit}`
          if (startDate) midcpDataUrl += `&start_date=${startDate}`
          if (endDate) midcpDataUrl += `&end_date=${endDate}`
          const [midcpStatusRes, midcpDataRes, midcpStatsRes, midcpExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/midcpnifty/status`),
            axios.get(midcpDataUrl),
            axios.get(`${API_BASE}/midcpnifty/stats`),
            axios.get(`${API_BASE}/midcpnifty/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setMidcpniftyStatus(midcpStatusRes.data)
          setMidcpniftyData(midcpDataRes.data.data || [])
          setMidcpniftyStats(midcpStatsRes.data.stats)
          setMidcpniftyExpiry(midcpExpiryRes.data.expiry || null)
          // Update pagination state
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: midcpDataRes.data.page || page,
              total: midcpDataRes.data.total || 0,
              total_pages: midcpDataRes.data.total_pages || 1,
              has_next: midcpDataRes.data.has_next || false,
              has_prev: midcpDataRes.data.has_prev || false
            }
          }))
          break

        case 'hdfcbank':
          let hdfcDataUrl = `${API_BASE}/hdfcbank/data?page=${page}&limit=${limit}`
          if (startDate) hdfcDataUrl += `&start_date=${startDate}`
          if (endDate) hdfcDataUrl += `&end_date=${endDate}`
          const [hdfcStatusRes, hdfcDataRes, hdfcStatsRes, hdfcExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/hdfcbank/status`),
            axios.get(hdfcDataUrl),
            axios.get(`${API_BASE}/hdfcbank/stats`),
            axios.get(`${API_BASE}/hdfcbank/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setHdfcbankStatus(hdfcStatusRes.data)
          setHdfcbankData(hdfcDataRes.data.data || [])
          setHdfcbankStats(hdfcStatsRes.data.stats)
          setHdfcbankExpiry(hdfcExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: hdfcDataRes.data.page || page,
              total: hdfcDataRes.data.total || 0,
              total_pages: hdfcDataRes.data.total_pages || 1,
              has_next: hdfcDataRes.data.has_next || false,
              has_prev: hdfcDataRes.data.has_prev || false
            }
          }))
          break

        case 'icicibank':
          let iciciDataUrl = `${API_BASE}/icicibank/data?page=${page}&limit=${limit}`
          if (startDate) iciciDataUrl += `&start_date=${startDate}`
          if (endDate) iciciDataUrl += `&end_date=${endDate}`
          const [iciciStatusRes, iciciDataRes, iciciStatsRes, iciciExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/icicibank/status`),
            axios.get(iciciDataUrl),
            axios.get(`${API_BASE}/icicibank/stats`),
            axios.get(`${API_BASE}/icicibank/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setIcicibankStatus(iciciStatusRes.data)
          setIcicibankData(iciciDataRes.data.data || [])
          setIcicibankStats(iciciStatsRes.data.stats)
          setIcicibankExpiry(iciciExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: iciciDataRes.data.page || page,
              total: iciciDataRes.data.total || 0,
              total_pages: iciciDataRes.data.total_pages || 1,
              has_next: iciciDataRes.data.has_next || false,
              has_prev: iciciDataRes.data.has_prev || false
            }
          }))
          break

        case 'sbin':
          let sbinDataUrl = `${API_BASE}/sbin/data?page=${page}&limit=${limit}`
          if (startDate) sbinDataUrl += `&start_date=${startDate}`
          if (endDate) sbinDataUrl += `&end_date=${endDate}`
          const [sbinStatusRes, sbinDataRes, sbinStatsRes, sbinExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/sbin/status`),
            axios.get(sbinDataUrl),
            axios.get(`${API_BASE}/sbin/stats`),
            axios.get(`${API_BASE}/sbin/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setSbinStatus(sbinStatusRes.data)
          setSbinData(sbinDataRes.data.data || [])
          setSbinStats(sbinStatsRes.data.stats)
          setSbinExpiry(sbinExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: sbinDataRes.data.page || page,
              total: sbinDataRes.data.total || 0,
              total_pages: sbinDataRes.data.total_pages || 1,
              has_next: sbinDataRes.data.has_next || false,
              has_prev: sbinDataRes.data.has_prev || false
            }
          }))
          break

        case 'kotakbank':
          let kotakDataUrl = `${API_BASE}/kotakbank/data?page=${page}&limit=${limit}`
          if (startDate) kotakDataUrl += `&start_date=${startDate}`
          if (endDate) kotakDataUrl += `&end_date=${endDate}`
          const [kotakStatusRes, kotakDataRes, kotakStatsRes, kotakExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/kotakbank/status`),
            axios.get(kotakDataUrl),
            axios.get(`${API_BASE}/kotakbank/stats`),
            axios.get(`${API_BASE}/kotakbank/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setKotakbankStatus(kotakStatusRes.data)
          setKotakbankData(kotakDataRes.data.data || [])
          setKotakbankStats(kotakStatsRes.data.stats)
          setKotakbankExpiry(kotakExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: kotakDataRes.data.page || page,
              total: kotakDataRes.data.total || 0,
              total_pages: kotakDataRes.data.total_pages || 1,
              has_next: kotakDataRes.data.has_next || false,
              has_prev: kotakDataRes.data.has_prev || false
            }
          }))
          break

        case 'axisbank':
          let axisDataUrl = `${API_BASE}/axisbank/data?page=${page}&limit=${limit}`
          if (startDate) axisDataUrl += `&start_date=${startDate}`
          if (endDate) axisDataUrl += `&end_date=${endDate}`
          const [axisStatusRes, axisDataRes, axisStatsRes, axisExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/axisbank/status`),
            axios.get(axisDataUrl),
            axios.get(`${API_BASE}/axisbank/stats`),
            axios.get(`${API_BASE}/axisbank/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setAxisbankStatus(axisStatusRes.data)
          setAxisbankData(axisDataRes.data.data || [])
          setAxisbankStats(axisStatsRes.data.stats)
          setAxisbankExpiry(axisExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: axisDataRes.data.page || page,
              total: axisDataRes.data.total || 0,
              total_pages: axisDataRes.data.total_pages || 1,
              has_next: axisDataRes.data.has_next || false,
              has_prev: axisDataRes.data.has_prev || false
            }
          }))
          break

        case 'bankbaroda':
          let bbDataUrl = `${API_BASE}/bankbaroda/data?page=${page}&limit=${limit}`
          if (startDate) bbDataUrl += `&start_date=${startDate}`
          if (endDate) bbDataUrl += `&end_date=${endDate}`
          const [bbStatusRes, bbDataRes, bbStatsRes, bbExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/bankbaroda/status`),
            axios.get(bbDataUrl),
            axios.get(`${API_BASE}/bankbaroda/stats`),
            axios.get(`${API_BASE}/bankbaroda/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setBankbarodaStatus(bbStatusRes.data)
          setBankbarodaData(bbDataRes.data.data || [])
          setBankbarodaStats(bbStatsRes.data.stats)
          setBankbarodaExpiry(bbExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: bbDataRes.data.page || page,
              total: bbDataRes.data.total || 0,
              total_pages: bbDataRes.data.total_pages || 1,
              has_next: bbDataRes.data.has_next || false,
              has_prev: bbDataRes.data.has_prev || false
            }
          }))
          break

        case 'pnb':
          let pnbDataUrl = `${API_BASE}/pnb/data?page=${page}&limit=${limit}`
          if (startDate) pnbDataUrl += `&start_date=${startDate}`
          if (endDate) pnbDataUrl += `&end_date=${endDate}`
          const [pnbStatusRes, pnbDataRes, pnbStatsRes, pnbExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/pnb/status`),
            axios.get(pnbDataUrl),
            axios.get(`${API_BASE}/pnb/stats`),
            axios.get(`${API_BASE}/pnb/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setPnbStatus(pnbStatusRes.data)
          setPnbData(pnbDataRes.data.data || [])
          setPnbStats(pnbStatsRes.data.stats)
          setPnbExpiry(pnbExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: pnbDataRes.data.page || page,
              total: pnbDataRes.data.total || 0,
              total_pages: pnbDataRes.data.total_pages || 1,
              has_next: pnbDataRes.data.has_next || false,
              has_prev: pnbDataRes.data.has_prev || false
            }
          }))
          break

        case 'canbk':
          let canbkDataUrl = `${API_BASE}/canbk/data?page=${page}&limit=${limit}`
          if (startDate) canbkDataUrl += `&start_date=${startDate}`
          if (endDate) canbkDataUrl += `&end_date=${endDate}`
          const [canbkStatusRes, canbkDataRes, canbkStatsRes, canbkExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/canbk/status`),
            axios.get(canbkDataUrl),
            axios.get(`${API_BASE}/canbk/stats`),
            axios.get(`${API_BASE}/canbk/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setCanbkStatus(canbkStatusRes.data)
          setCanbkData(canbkDataRes.data.data || [])
          setCanbkStats(canbkStatsRes.data.stats)
          setCanbkExpiry(canbkExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: canbkDataRes.data.page || page,
              total: canbkDataRes.data.total || 0,
              total_pages: canbkDataRes.data.total_pages || 1,
              has_next: canbkDataRes.data.has_next || false,
              has_prev: canbkDataRes.data.has_prev || false
            }
          }))
          break

        case 'aubank':
          let aubankDataUrl = `${API_BASE}/aubank/data?page=${page}&limit=${limit}`
          if (startDate) aubankDataUrl += `&start_date=${startDate}`
          if (endDate) aubankDataUrl += `&end_date=${endDate}`
          const [aubankStatusRes, aubankDataRes, aubankStatsRes, aubankExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/aubank/status`),
            axios.get(aubankDataUrl),
            axios.get(`${API_BASE}/aubank/stats`),
            axios.get(`${API_BASE}/aubank/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setAubankStatus(aubankStatusRes.data)
          setAubankData(aubankDataRes.data.data || [])
          setAubankStats(aubankStatsRes.data.stats)
          setAubankExpiry(aubankExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: aubankDataRes.data.page || page,
              total: aubankDataRes.data.total || 0,
              total_pages: aubankDataRes.data.total_pages || 1,
              has_next: aubankDataRes.data.has_next || false,
              has_prev: aubankDataRes.data.has_prev || false
            }
          }))
          break

        case 'indusindbk':
          let indusindDataUrl = `${API_BASE}/indusindbk/data?page=${page}&limit=${limit}`
          if (startDate) indusindDataUrl += `&start_date=${startDate}`
          if (endDate) indusindDataUrl += `&end_date=${endDate}`
          const [indusindStatusRes, indusindDataRes, indusindStatsRes, indusindExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/indusindbk/status`),
            axios.get(indusindDataUrl),
            axios.get(`${API_BASE}/indusindbk/stats`),
            axios.get(`${API_BASE}/indusindbk/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setIndusindbkStatus(indusindStatusRes.data)
          setIndusindbkData(indusindDataRes.data.data || [])
          setIndusindbkStats(indusindStatsRes.data.stats)
          setIndusindbkExpiry(indusindExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: indusindDataRes.data.page || page,
              total: indusindDataRes.data.total || 0,
              total_pages: indusindDataRes.data.total_pages || 1,
              has_next: indusindDataRes.data.has_next || false,
              has_prev: indusindDataRes.data.has_prev || false
            }
          }))
          break

        case 'idfcfirstb':
          let idfcDataUrl = `${API_BASE}/idfcfirstb/data?page=${page}&limit=${limit}`
          if (startDate) idfcDataUrl += `&start_date=${startDate}`
          if (endDate) idfcDataUrl += `&end_date=${endDate}`
          const [idfcStatusRes, idfcDataRes, idfcStatsRes, idfcExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/idfcfirstb/status`),
            axios.get(idfcDataUrl),
            axios.get(`${API_BASE}/idfcfirstb/stats`),
            axios.get(`${API_BASE}/idfcfirstb/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setIdfcfirstbStatus(idfcStatusRes.data)
          setIdfcfirstbData(idfcDataRes.data.data || [])
          setIdfcfirstbStats(idfcStatsRes.data.stats)
          setIdfcfirstbExpiry(idfcExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: idfcDataRes.data.page || page,
              total: idfcDataRes.data.total || 0,
              total_pages: idfcDataRes.data.total_pages || 1,
              has_next: idfcDataRes.data.has_next || false,
              has_prev: idfcDataRes.data.has_prev || false
            }
          }))
          break

        case 'federalbnk':
          let federalDataUrl = `${API_BASE}/federalbnk/data?page=${page}&limit=${limit}`
          if (startDate) federalDataUrl += `&start_date=${startDate}`
          if (endDate) federalDataUrl += `&end_date=${endDate}`
          const [federalStatusRes, federalDataRes, federalStatsRes, federalExpiryRes] = await Promise.all([
            axios.get(`${API_BASE}/federalbnk/status`),
            axios.get(federalDataUrl),
            axios.get(`${API_BASE}/federalbnk/stats`),
            axios.get(`${API_BASE}/federalbnk/expiry`).catch(() => ({ data: { success: false, expiry: null } }))
          ])
          setFederalbnkStatus(federalStatusRes.data)
          setFederalbnkData(federalDataRes.data.data || [])
          setFederalbnkStats(federalStatsRes.data.stats)
          setFederalbnkExpiry(federalExpiryRes.data.expiry || null)
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: federalDataRes.data.page || page,
              total: federalDataRes.data.total || 0,
              total_pages: federalDataRes.data.total_pages || 1,
              has_next: federalDataRes.data.has_next || false,
              has_prev: federalDataRes.data.has_prev || false
            }
          }))
          break

        case 'gainers':
          const [gainersStatusRes, gainersDataRes, gainersStatsRes] = await Promise.all([
            axios.get(`${API_BASE}/gainers/status`),
            axios.get(`${API_BASE}/gainers/data?page=${page}&limit=${limit}`, {
              headers: { 'Authorization': `Bearer ${authToken}` }
            }),
            axios.get(`${API_BASE}/gainers/stats`)
          ])
          setGainersStatus(gainersStatusRes.data)
          setGainersData(gainersDataRes.data?.data || [])
          setGainersStats(gainersStatsRes.data?.stats || null)
          // Update pagination state
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: gainersDataRes.data.page || page,
              total: gainersDataRes.data.total || 0,
              total_pages: gainersDataRes.data.total_pages || 1,
              has_next: gainersDataRes.data.has_next || false,
              has_prev: gainersDataRes.data.has_prev || false
            }
          }))
          break

        case 'losers':
          const [losersStatusRes, losersDataRes, losersStatsRes] = await Promise.all([
            axios.get(`${API_BASE}/losers/status`),
            axios.get(`${API_BASE}/losers/data?page=${page}&limit=${limit}`, {
              headers: { 'Authorization': `Bearer ${authToken}` }
            }),
            axios.get(`${API_BASE}/losers/stats`)
          ])
          setLosersStatus(losersStatusRes.data)
          setLosersData(losersDataRes.data?.data || [])
          setLosersStats(losersStatsRes.data?.stats || null)
          // Update pagination state
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: losersDataRes.data.page || page,
              total: losersDataRes.data.total || 0,
              total_pages: losersDataRes.data.total_pages || 1,
              has_next: losersDataRes.data.has_next || false,
              has_prev: losersDataRes.data.has_prev || false
            }
          }))
          break

        case 'news':
          const [newsStatusRes, newsDataRes, newsStatsRes] = await Promise.all([
            axios.get(`${API_BASE}/news/status`),
            axios.get(`${API_BASE}/news/data?page=${page}&limit=${limit}`),
            axios.get(`${API_BASE}/news/stats`)
          ])
          setNewsStatus(newsStatusRes.data)
          setNewsData(newsDataRes.data.data || [])
          setNewsStats(newsStatsRes.data.stats)
          // Update pagination state
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: newsDataRes.data.page || page,
              total: newsDataRes.data.total || 0,
              total_pages: newsDataRes.data.total_pages || 1,
              has_next: newsDataRes.data.has_next || false,
              has_prev: newsDataRes.data.has_prev || false
            }
          }))
          break

        case 'livemint-news':
          const [livemintStatusRes, livemintDataRes, livemintStatsRes] = await Promise.all([
            axios.get(`${API_BASE}/livemint-news/status`),
            axios.get(`${API_BASE}/livemint-news/data?page=${page}&limit=${limit}`),
            axios.get(`${API_BASE}/livemint-news/stats`)
          ])
          setLivemintNewsStatus(livemintStatusRes.data)
          setLivemintNewsData(livemintDataRes.data.data || [])
          setLivemintNewsStats(livemintStatsRes.data.stats)
          // Update pagination state
          setPagination(prev => ({
            ...prev,
            [tabName]: {
              page: livemintDataRes.data.page || page,
              total: livemintDataRes.data.total || 0,
              total_pages: livemintDataRes.data.total_pages || 1,
              has_next: livemintDataRes.data.has_next || false,
              has_prev: livemintDataRes.data.has_prev || false
            }
          }))
          break

        case 'heatmap':
          setHeatmapLoading(true)
          try {
            // Get latest records from gainers and losers (first page = latest)
            const [gainersListRes, losersListRes] = await Promise.all([
              axios.get(`${API_BASE}/gainers/data?page=1&limit=1`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
              }),
              axios.get(`${API_BASE}/losers/data?page=1&limit=1`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
              })
            ])

            const latestGainersRecord = gainersListRes.data.data?.[0]
            const latestLosersRecord = losersListRes.data.data?.[0]

            // Fetch full record data if we have IDs
            if (latestGainersRecord?._id && latestLosersRecord?._id) {
              const [gainersFullRes, losersFullRes] = await Promise.all([
                axios.get(`${API_BASE}/gainers/data/${latestGainersRecord._id}`, {
                  headers: { 'Authorization': `Bearer ${authToken}` }
                }),
                axios.get(`${API_BASE}/losers/data/${latestLosersRecord._id}`, {
                  headers: { 'Authorization': `Bearer ${authToken}` }
                })
              ])

              if (gainersFullRes.data.success && gainersFullRes.data.data) {
                // Extract the actual data - could be in data.data or directly in data
                const gainersRecord = gainersFullRes.data.data.data || gainersFullRes.data.data
                setHeatmapGainersData(gainersRecord)
              }
              if (losersFullRes.data.success && losersFullRes.data.data) {
                // Extract the actual data - could be in data.data or directly in data
                const losersRecord = losersFullRes.data.data.data || losersFullRes.data.data
                setHeatmapLosersData(losersRecord)
              }
            } else {
              // No records found
              setHeatmapGainersData(null)
              setHeatmapLosersData(null)
            }
          } catch (error) {
            console.error('Error fetching heatmap data:', error)
            setHeatmapGainersData(null)
            setHeatmapLosersData(null)
          } finally {
            setHeatmapLoading(false)
          }
          break

        default:
          break
      }

      // Mark tab as loaded
      setLoadedTabs(prev => new Set([...prev, tabName]))
    } catch (error) {
      console.error(`Error fetching data for ${tabName}:`, error)
      
      // If unauthorized (401), redirect to login
      if (error.response && error.response.status === 401) {
        localStorage.removeItem('authToken')
        localStorage.removeItem('username')
        setIsAuthenticated(false)
        setAuthToken(null)
        setShowHome(true)
        delete axios.defaults.headers.common['Authorization']
      }
    } finally {
      setLoadingTab(null)
    }
  }

  // Pagination component
  const Pagination = ({ tabName }) => {
    const paginationData = pagination[tabName]
    if (!paginationData || paginationData.total_pages <= 1) return null

    const handlePageChange = (newPage) => {
      if (newPage >= 1 && newPage <= paginationData.total_pages) {
        const filter = dateFilters[tabName] || {}
        fetchTabData(tabName, true, newPage, filter.startDate || null, filter.endDate || null)
      }
    }

    return (
      <div className="pagination">
        <button
          className="pagination-btn"
          onClick={() => handlePageChange(paginationData.page - 1)}
          disabled={!paginationData.has_prev}
        >
          <ChevronLeft size={18} />
          Previous
        </button>
        <div className="pagination-info">
          Page {paginationData.page} of {paginationData.total_pages}
          <span className="pagination-total">({paginationData.total} total records)</span>
        </div>
        <button
          className="pagination-btn"
          onClick={() => handlePageChange(paginationData.page + 1)}
          disabled={!paginationData.has_next}
        >
          Next
          <ChevronRight size={18} />
        </button>
      </div>
    )
  }

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem('authToken')
    const storedUsername = localStorage.getItem('username')
    
    if (token) {
      // Verify token is still valid
      verifyToken(token, storedUsername)
    }
  }, [])

  // Configure axios to include token in all requests
  useEffect(() => {
    if (authToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }, [authToken])


  // Verify token validity
  const verifyToken = async (token, storedUsername) => {
    try {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      const response = await axios.get(`${API_BASE}/verify-token`)
      
      if (response.data.success) {
        setIsAuthenticated(true)
        setAuthToken(token)
        setUsername(storedUsername || 'Admin')
      } else {
        // Token invalid, clear storage
        localStorage.removeItem('authToken')
        localStorage.removeItem('username')
        setIsAuthenticated(false)
        setAuthToken(null)
      }
    } catch (error) {
      // Token invalid or expired
      localStorage.removeItem('authToken')
      localStorage.removeItem('username')
      setIsAuthenticated(false)
      setAuthToken(null)
      delete axios.defaults.headers.common['Authorization']
    }
  }

  // Handle successful login
  const handleLoginSuccess = (token, user) => {
    setAuthToken(token)
    setUsername(user)
    setIsAuthenticated(true)
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    // After login, go directly to dashboard
    if (activeTab) {
      fetchTabData(activeTab)
    } else {
      // Default to FII/DII tab
      setActiveTab('fiidii')
      fetchTabData('fiidii')
    }
  }

  // Handle logout click - show confirmation dialog
  const handleLogoutClick = () => {
    setShowLogoutDialog(true)
  }

  // Handle logout confirmation
  const handleLogout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('username')
    setIsAuthenticated(false)
    setAuthToken(null)
    setShowLogoutDialog(false)
    delete axios.defaults.headers.common['Authorization']
  }

  // Cancel logout
  const handleCancelLogout = () => {
    setShowLogoutDialog(false)
  }

  // Handle tab change - fetch data if not loaded
  const handleTabChange = (tabName) => {
    setActiveTab(tabName)
    // Don't fetch data for settings tab
    if (tabName !== 'settings') {
      fetchTabData(tabName)
    }
    // Close sidebar on mobile after selecting a tab
    if (window.innerWidth <= 768) {
      setSidebarOpen(false)
    }
  }

  // Toggle sidebar on mobile
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  // Refresh function - force reload current tab
  const refreshCurrentTab = () => {
    if (activeTab) {
      fetchTabData(activeTab, true)
    }
  }

  const handleTrigger = async () => {
    setTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/trigger`)
      if (res.data.success) {
        alert('✅ FII/DII Data collection completed successfully!')
        setTimeout(() => fetchTabData('fiidii', true), 2000)
      } else {
        alert('❌ Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setTriggering(false)
    }
  }

  const handleOptionChainTrigger = async () => {
    setOptionChainTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/option-chain/trigger`)
      if (res.data.success) {
        alert('✅ NIFTY Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('option-chain', true), 2000)
      } else {
        alert('❌ NIFTY Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setOptionChainTriggering(false)
    }
  }

  const handleBankniftyTrigger = async () => {
    setBankniftyTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/banknifty/trigger`)
      if (res.data.success) {
        alert('✅ BankNifty Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('banknifty', true), 2000)
      } else {
        alert('❌ BankNifty Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setBankniftyTriggering(false)
    }
  }

  const handleFinniftyTrigger = async () => {
    setFinniftyTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/finnifty/trigger`)
      if (res.data.success) {
        alert('✅ Finnifty Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('finnifty', true), 2000)
      } else {
        alert('❌ Finnifty Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setFinniftyTriggering(false)
    }
  }

  const handleMidcpniftyTrigger = async () => {
    setMidcpniftyTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/midcpnifty/trigger`)
      if (res.data.success) {
        alert('✅ MidcapNifty Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('midcpnifty', true), 2000)
      } else {
        alert('❌ MidcapNifty Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setMidcpniftyTriggering(false)
    }
  }

  const handleHdfcbankTrigger = async () => {
    setHdfcbankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/hdfcbank/trigger`)
      if (res.data.success) {
        alert('✅ HDFC Bank Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('hdfcbank', true), 2000)
      } else {
        alert('❌ HDFC Bank Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setHdfcbankTriggering(false)
    }
  }

  const handleIcicibankTrigger = async () => {
    setIcicibankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/icicibank/trigger`)
      if (res.data.success) {
        alert('✅ ICICI Bank Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('icicibank', true), 2000)
      } else {
        alert('❌ ICICI Bank Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setIcicibankTriggering(false)
    }
  }

  const handleSbinTrigger = async () => {
    setSbinTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/sbin/trigger`)
      if (res.data.success) {
        alert('✅ SBIN Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('sbin', true), 2000)
      } else {
        alert('❌ SBIN Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setSbinTriggering(false)
    }
  }

  const handleKotakbankTrigger = async () => {
    setKotakbankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/kotakbank/trigger`)
      if (res.data.success) {
        alert('✅ Kotak Bank Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('kotakbank', true), 2000)
      } else {
        alert('❌ Kotak Bank Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setKotakbankTriggering(false)
    }
  }

  const handleAxisbankTrigger = async () => {
    setAxisbankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/axisbank/trigger`)
      if (res.data.success) {
        alert('✅ Axis Bank Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('axisbank', true), 2000)
      } else {
        alert('❌ Axis Bank Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setAxisbankTriggering(false)
    }
  }

  const handleBankbarodaTrigger = async () => {
    setBankbarodaTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/bankbaroda/trigger`)
      if (res.data.success) {
        alert('✅ Bank of Baroda Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('bankbaroda', true), 2000)
      } else {
        alert('❌ Bank of Baroda Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setBankbarodaTriggering(false)
    }
  }

  const handlePnbTrigger = async () => {
    setPnbTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/pnb/trigger`)
      if (res.data.success) {
        alert('✅ PNB Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('pnb', true), 2000)
      } else {
        alert('❌ PNB Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setPnbTriggering(false)
    }
  }

  const handleCanbkTrigger = async () => {
    setCanbkTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/canbk/trigger`)
      if (res.data.success) {
        alert('✅ CANBK Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('canbk', true), 2000)
      } else {
        alert('❌ CANBK Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setCanbkTriggering(false)
    }
  }

  const handleAubankTrigger = async () => {
    setAubankTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/aubank/trigger`)
      if (res.data.success) {
        alert('✅ AUBANK Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('aubank', true), 2000)
      } else {
        alert('❌ AUBANK Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setAubankTriggering(false)
    }
  }

  const handleIndusindbkTrigger = async () => {
    setIndusindbkTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/indusindbk/trigger`)
      if (res.data.success) {
        alert('✅ INDUSINDBK Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('indusindbk', true), 2000)
      } else {
        alert('❌ INDUSINDBK Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setIndusindbkTriggering(false)
    }
  }

  const handleIdfcfirstbTrigger = async () => {
    setIdfcfirstbTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/idfcfirstb/trigger`)
      if (res.data.success) {
        alert('✅ IDFCFIRSTB Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('idfcfirstb', true), 2000)
      } else {
        alert('❌ IDFCFIRSTB Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setIdfcfirstbTriggering(false)
    }
  }

  const handleFederalbnkTrigger = async () => {
    setFederalbnkTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/federalbnk/trigger`)
      if (res.data.success) {
        alert('✅ FEDERALBNK Option Chain Data collection completed successfully!')
        setTimeout(() => fetchTabData('federalbnk', true), 2000)
      } else {
        alert('❌ FEDERALBNK Option Chain Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setFederalbnkTriggering(false)
    }
  }

  const handleGainersTrigger = async () => {
    setGainersTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/gainers/trigger`, {}, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      })
      if (res.data.success) {
        alert('✅ Top 20 Gainers Data collection completed successfully!')
        setTimeout(() => fetchTabData('gainers', true), 2000)
      } else {
        alert('❌ Top 20 Gainers Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.message || 'Unknown error'
      alert('❌ Error: ' + errorMsg)
      console.error('Gainers trigger error:', error)
    } finally {
      setGainersTriggering(false)
    }
  }

  const handleLosersTrigger = async () => {
    setLosersTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/losers/trigger`, {}, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      })
      if (res.data.success) {
        alert('✅ Top 20 Losers Data collection completed successfully!')
        setTimeout(() => fetchTabData('losers', true), 2000)
      } else {
        alert('❌ Top 20 Losers Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.message || 'Unknown error'
      alert('❌ Error: ' + errorMsg)
      console.error('Losers trigger error:', error)
    } finally {
      setLosersTriggering(false)
    }
  }

  const handleNewsTrigger = async () => {
    setNewsTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/news/trigger`)
      if (res.data.success) {
        alert('✅ News Data collection completed successfully!')
        setTimeout(() => fetchTabData('news', true), 2000)
      } else {
        alert('❌ News Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setNewsTriggering(false)
    }
  }

  const handleLivemintNewsTrigger = async () => {
    setLivemintNewsTriggering(true)
    try {
      const res = await axios.post(`${API_BASE}/livemint-news/trigger`)
      if (res.data.success) {
        alert('✅ LiveMint News Data collection completed successfully!')
        setTimeout(() => fetchTabData('livemint-news', true), 2000)
      } else {
        alert('❌ LiveMint News Data collection failed: ' + (res.data.error || res.data.message))
      }
    } catch (error) {
      alert('❌ Error: ' + error.message)
    } finally {
      setLivemintNewsTriggering(false)
    }
  }


  const getSentimentColor = (sentiment) => {
    if (sentiment === 'Positive') return 'positive'
    if (sentiment === 'Negative') return 'negative'
    return 'muted'
  }

  const formatDateTime = (isoString) => {
    if (!isoString) return 'Never'
    try {
      const date = new Date(isoString)
      if (isNaN(date.getTime())) return isoString
      // Convert to IST (UTC+5:30)
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

  const formatNumber = (value) => {
    if (!value) return '-'
    const num = parseFloat(value)
    if (isNaN(num)) return value
    return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  // Handle delete record
  const handleDeleteRecord = async (recordId, tabName) => {
    if (!window.confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
      return
    }

    try {
      let endpoint = ''
      switch(tabName) {
        case 'fiidii':
          endpoint = `${API_BASE}/data/${recordId}`
          break
        case 'option-chain':
          endpoint = `${API_BASE}/option-chain/data/${recordId}`
          break
        default:
          endpoint = `${API_BASE}/${tabName}/data/${recordId}`
      }
      
      const res = await axios.delete(endpoint)
      if (res.data.success) {
        alert('✅ Record deleted successfully')
        fetchTabData(tabName, true, 1, dateFilters[tabName]?.startDate || null, dateFilters[tabName]?.endDate || null)
      } else {
        alert('❌ Failed to delete record: ' + (res.data.error || 'Unknown error'))
      }
    } catch (error) {
      alert('❌ Error deleting record: ' + error.message)
    }
  }

  // Handle apply date filter
  const handleApplyDateFilter = (tabName) => {
    const filter = dateFilters[tabName] || {}
    fetchTabData(tabName, true, 1, filter.startDate || null, filter.endDate || null)
  }

  // Handle clear date filter
  const handleClearDateFilter = (tabName) => {
    setDateFilters(prev => ({
      ...prev,
      [tabName]: { startDate: '', endDate: '' }
    }))
    fetchTabData(tabName, true, 1, null, null)
  }

  // Handle row click to show detail
  const handleRowClick = async (record, tabName) => {
    try {
      // For option chain and bank tabs, fetch full record data
      const optionChainTabs = ['option-chain', 'banknifty', 'finnifty', 'midcpnifty', 'hdfcbank', 'icicibank', 'sbin', 'kotakbank', 'axisbank', 'bankbaroda', 'pnb', 'canbk', 'aubank', 'indusindbk', 'idfcfirstb', 'federalbnk']
      
      if (optionChainTabs.includes(tabName)) {
        // Fetch full record with all data
        let endpoint = ''
        if (tabName === 'option-chain') {
          endpoint = `${API_BASE}/option-chain/data/${record._id}`
        } else {
          endpoint = `${API_BASE}/${tabName}/data/${record._id}`
        }
        
        const response = await axios.get(endpoint, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        })
        
        if (response.data.success) {
          setSelectedRecord(response.data.data)
          setSelectedTabName(tabName)
        } else {
          alert('Failed to load record details: ' + (response.data.error || 'Unknown error'))
        }
      } else {
        // For other tabs, use the record as is
        setSelectedRecord(record)
        setSelectedTabName(tabName)
      }
    } catch (error) {
      console.error('Error fetching record details:', error)
      alert('Error loading record details: ' + (error.response?.data?.error || error.message))
    }
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  if (loadingTab) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p className="loading-text">Loading {loadingTab} data...</p>
      </div>
    )
  }

  return (
    <>
      {/* Logout Confirmation Dialog */}
      {showLogoutDialog && (
        <div className="logout-dialog-overlay" onClick={handleCancelLogout}>
          <div className="logout-dialog" onClick={(e) => e.stopPropagation()}>
            <button className="dialog-close-btn" onClick={handleCancelLogout}>
              <X size={20} />
            </button>
            <div className="dialog-icon-wrapper">
              <AlertCircle size={48} className="dialog-icon" />
            </div>
            <h2 className="dialog-title">Confirm Logout</h2>
            <p className="dialog-message">
              Are you sure you want to logout? You will need to login again to access the dashboard.
            </p>
            <div className="dialog-actions">
              <button 
                className="dialog-btn dialog-btn-cancel" 
                onClick={handleCancelLogout}
              >
                <X size={18} />
                Cancel
              </button>
              <button 
                className="dialog-btn dialog-btn-confirm" 
                onClick={handleLogout}
              >
                <LogOut size={18} />
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="app">
        <header className="header">
          <div className="header-content">
            <div className="header-brand">
              <button className="menu-toggle" onClick={toggleSidebar}>
                <Menu size={24} />
              </button>
              <div className="brand-logo">
                <Activity size={24} />
              </div>
              <h1>X Fin Ai - Admin Panel</h1>
            </div>
            <div className="header-actions">
              <span className="user-name">{username}</span>
              <button 
                className="logout-btn"
                onClick={handleLogoutClick}
                title="Logout"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </header>

      {/* Sidebar Overlay for mobile */}
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)}></div>}

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>Navigation</h2>
          <button className="sidebar-close" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>
        <div className="sidebar-section">
          <div className="sidebar-section-title">Main Menu</div>
          <ul className="sidebar-menu">
            <li 
              className={`sidebar-item ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => {
                handleTabChange('settings')
                setSidebarOpen(false)
              }}
            >
              <SettingsIcon size={20} />
              Settings
            </li>
          </ul>
        </div>
        <div className="sidebar-section">
          <div className="sidebar-section-title">Market Data</div>
          <ul className="sidebar-menu">
            <li 
              className={`sidebar-item ${activeTab === 'fiidii' ? 'active' : ''}`}
              onClick={() => handleTabChange('fiidii')}
            >
              <Activity size={20} />
              FII/DII Data
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'gainers' ? 'active' : ''}`}
              onClick={() => handleTabChange('gainers')}
            >
              <TrendingUp size={20} />
              Top 20 Gainers
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'losers' ? 'active' : ''}`}
              onClick={() => handleTabChange('losers')}
            >
              <TrendingDown size={20} />
              Top 20 Losers
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'heatmap' ? 'active' : ''}`}
              onClick={() => handleTabChange('heatmap')}
            >
              <BarChart3 size={20} />
              Heatmap
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'news' ? 'active' : ''}`}
              onClick={() => handleTabChange('news')}
            >
              <Newspaper size={20} />
              News & Sentiment
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'livemint-news' ? 'active' : ''}`}
              onClick={() => handleTabChange('livemint-news')}
            >
              <Newspaper size={20} />
              LiveMint News
            </li>
          </ul>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-title">Index Options</div>
          <ul className="sidebar-menu">
            <li 
              className={`sidebar-item ${activeTab === 'option-chain' ? 'active' : ''}`}
              onClick={() => handleTabChange('option-chain')}
            >
              <BarChart3 size={20} />
              NIFTY
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'banknifty' ? 'active' : ''}`}
              onClick={() => handleTabChange('banknifty')}
            >
              <BarChart3 size={20} />
              BankNifty
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'finnifty' ? 'active' : ''}`}
              onClick={() => handleTabChange('finnifty')}
            >
              <BarChart3 size={20} />
              Finnifty
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'midcpnifty' ? 'active' : ''}`}
              onClick={() => handleTabChange('midcpnifty')}
            >
              <BarChart3 size={20} />
              MidcapNifty
            </li>
          </ul>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-title">Bank Options</div>
          <ul className="sidebar-menu">
            <li 
              className={`sidebar-item ${activeTab === 'hdfcbank' ? 'active' : ''}`}
              onClick={() => handleTabChange('hdfcbank')}
            >
              <BarChart3 size={20} />
              HDFC Bank
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'icicibank' ? 'active' : ''}`}
              onClick={() => handleTabChange('icicibank')}
            >
              <BarChart3 size={20} />
              ICICI Bank
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'sbin' ? 'active' : ''}`}
              onClick={() => handleTabChange('sbin')}
            >
              <BarChart3 size={20} />
              SBIN
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'kotakbank' ? 'active' : ''}`}
              onClick={() => handleTabChange('kotakbank')}
            >
              <BarChart3 size={20} />
              Kotak Bank
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'axisbank' ? 'active' : ''}`}
              onClick={() => handleTabChange('axisbank')}
            >
              <BarChart3 size={20} />
              Axis Bank
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'bankbaroda' ? 'active' : ''}`}
              onClick={() => handleTabChange('bankbaroda')}
            >
              <BarChart3 size={20} />
              Bank of Baroda
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'pnb' ? 'active' : ''}`}
              onClick={() => handleTabChange('pnb')}
            >
              <BarChart3 size={20} />
              PNB
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'canbk' ? 'active' : ''}`}
              onClick={() => handleTabChange('canbk')}
            >
              <BarChart3 size={20} />
              CANBK
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'aubank' ? 'active' : ''}`}
              onClick={() => handleTabChange('aubank')}
            >
              <BarChart3 size={20} />
              AUBANK
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'indusindbk' ? 'active' : ''}`}
              onClick={() => handleTabChange('indusindbk')}
            >
              <BarChart3 size={20} />
              IndusInd Bank
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'idfcfirstb' ? 'active' : ''}`}
              onClick={() => handleTabChange('idfcfirstb')}
            >
              <BarChart3 size={20} />
              IDFC First Bank
            </li>
            <li 
              className={`sidebar-item ${activeTab === 'federalbnk' ? 'active' : ''}`}
              onClick={() => handleTabChange('federalbnk')}
            >
              <BarChart3 size={20} />
              Federal Bank
            </li>
          </ul>
        </div>
      </aside>

      <main className="main-content">
        <div className="container">
        {activeTab === 'fiidii' ? (
          <>
            {/* FII/DII Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>FII/DII Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={status?.running ? 'Running' : 'Stopped'}
                  icon={status?.running ? CheckCircle : XCircle}
                  status={status?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(status?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(status?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={status?.last_status ? 
                    status.last_status.charAt(0).toUpperCase() + status.last_status.slice(1) : 
                    'Unknown'}
                  icon={status?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={status?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('fiidii')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleTrigger} 
                  className="btn btn-primary"
                  disabled={triggering}
                >
                  <Play size={18} />
                  {triggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* FII/DII Statistics Card */}
            {stats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>FII/DII Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{stats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Date</div>
                      <div className="stat-value">{stats.latest_date || '-'}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* FII/DII Data Table Card */}
            <div className="card data-card">
                <div className="card-header">
                <h2>FII/DII Collected Data</h2>
                <span className="badge">{pagination['fiidii']?.total || data.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['fiidii']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      fiidii: { ...prev.fiidii, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['fiidii']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      fiidii: { ...prev.fiidii, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('fiidii')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['fiidii']?.startDate || dateFilters['fiidii']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('fiidii')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {data.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>DII Buy</th>
                        <th>DII Sell</th>
                        <th>DII Net</th>
                        <th>FII Buy</th>
                        <th>FII Sell</th>
                        <th>FII Net</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.map((record) => {
                        const dii = record.dii || {}
                        const fii = record.fii || {}
                        const diiNet = parseFloat(dii.netValue) || 0
                        const fiiNet = parseFloat(fii.netValue) || 0

                        return (
                          <tr 
                            key={record._id}
                            onClick={() => handleRowClick(record, 'fiidii')}
                            style={{ cursor: 'pointer' }}
                          >
                            <td className="date-cell">{record.date}</td>
                            <td>{formatNumber(dii.buyValue)}</td>
                            <td>{formatNumber(dii.sellValue)}</td>
                            <td className={diiNet >= 0 ? 'positive' : 'negative'}>
                              {diiNet >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                              {formatNumber(dii.netValue)}
                            </td>
                            <td>{formatNumber(fii.buyValue)}</td>
                            <td>{formatNumber(fii.sellValue)}</td>
                            <td className={fiiNet >= 0 ? 'positive' : 'negative'}>
                              {fiiNet >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                              {formatNumber(fii.netValue)}
                            </td>
                            <td className="muted">{formatDateTime(record.updatedAt)}</td>
                            <td onClick={(e) => e.stopPropagation()}>
                              <button
                                className="btn-icon btn-danger"
                                onClick={() => handleDeleteRecord(record._id, 'fiidii')}
                                title="Delete record"
                              >
                                <Trash2 size={16} />
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
                <Pagination tabName="fiidii" />
                </>
              )}
            </div>
          </>
        ) : activeTab === 'option-chain' ? (
          <>
            {/* NIFTY Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>NIFTY Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={optionChainStatus?.running ? 'Running' : 'Stopped'}
                  icon={optionChainStatus?.running ? CheckCircle : XCircle}
                  status={optionChainStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(optionChainStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(optionChainStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={optionChainStatus?.last_status ? 
                    optionChainStatus.last_status.charAt(0).toUpperCase() + optionChainStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={optionChainStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={optionChainStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('option-chain')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleOptionChainTrigger} 
                  className="btn btn-primary"
                  disabled={optionChainTriggering}
                >
                  <Play size={18} />
                  {optionChainTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* NIFTY Option Chain Statistics Card */}
            {optionChainStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>NIFTY Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{optionChainStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{optionChainStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(optionChainStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {optionChainExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{optionChainExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* NIFTY Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>NIFTY Option Chain Collected Data</h2>
                <span className="badge">{optionChainData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['option-chain']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      'option-chain': { ...prev['option-chain'], startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['option-chain']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      'option-chain': { ...prev['option-chain'], endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('option-chain')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['option-chain']?.startDate || dateFilters['option-chain']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('option-chain')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {optionChainData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {optionChainData.map((record) => (
                        <tr 
                          key={record._id}
                          onClick={() => handleRowClick(record, 'option-chain')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'option-chain')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="option-chain" />
            </div>
          </>
        ) : activeTab === 'banknifty' ? (
          <>
            {/* BankNifty Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>BankNifty Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={bankniftyStatus?.running ? 'Running' : 'Stopped'}
                  icon={bankniftyStatus?.running ? CheckCircle : XCircle}
                  status={bankniftyStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(bankniftyStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(bankniftyStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={bankniftyStatus?.last_status ? 
                    bankniftyStatus.last_status.charAt(0).toUpperCase() + bankniftyStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={bankniftyStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={bankniftyStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('banknifty')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleBankniftyTrigger} 
                  className="btn btn-primary"
                  disabled={bankniftyTriggering}
                >
                  <Play size={18} />
                  {bankniftyTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* BankNifty Option Chain Statistics Card */}
            {bankniftyStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>BankNifty Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{bankniftyStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{bankniftyStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(bankniftyStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {bankniftyExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{bankniftyExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* BankNifty Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>BankNifty Option Chain Collected Data</h2>
                <span className="badge">{bankniftyData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['banknifty']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      banknifty: { ...prev.banknifty, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['banknifty']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      banknifty: { ...prev.banknifty, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('banknifty')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['banknifty']?.startDate || dateFilters['banknifty']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('banknifty')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {bankniftyData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bankniftyData.map((record) => (
                        <tr 
                          key={record._id}
                          onClick={() => handleRowClick(record, 'banknifty')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'banknifty')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="banknifty" />
            </div>
          </>
        ) : activeTab === 'finnifty' ? (
          <>
            {/* Finnifty Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Finnifty Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={finniftyStatus?.running ? 'Running' : 'Stopped'}
                  icon={finniftyStatus?.running ? CheckCircle : XCircle}
                  status={finniftyStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(finniftyStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(finniftyStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={finniftyStatus?.last_status ? 
                    finniftyStatus.last_status.charAt(0).toUpperCase() + finniftyStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={finniftyStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={finniftyStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('finnifty')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleFinniftyTrigger} 
                  className="btn btn-primary"
                  disabled={finniftyTriggering}
                >
                  <Play size={18} />
                  {finniftyTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Finnifty Option Chain Statistics Card */}
            {finniftyStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Finnifty Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{finniftyStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{finniftyStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(finniftyStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {finniftyExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{finniftyExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Finnifty Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Finnifty Option Chain Collected Data</h2>
                <span className="badge">{finniftyData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['finnifty']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      finnifty: { ...prev.finnifty, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['finnifty']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      finnifty: { ...prev.finnifty, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('finnifty')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['finnifty']?.startDate || dateFilters['finnifty']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('finnifty')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {finniftyData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {finniftyData.map((record) => (
                        <tr 
                          key={record._id}
                          onClick={() => handleRowClick(record, 'finnifty')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'finnifty')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="finnifty" />
            </div>
          </>
        ) : activeTab === 'midcpnifty' ? (
          <>
            {/* MidcapNifty Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>MidcapNifty Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={midcpniftyStatus?.running ? 'Running' : 'Stopped'}
                  icon={midcpniftyStatus?.running ? CheckCircle : XCircle}
                  status={midcpniftyStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(midcpniftyStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(midcpniftyStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={midcpniftyStatus?.last_status ? 
                    midcpniftyStatus.last_status.charAt(0).toUpperCase() + midcpniftyStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={midcpniftyStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={midcpniftyStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('midcpnifty')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleMidcpniftyTrigger} 
                  className="btn btn-primary"
                  disabled={midcpniftyTriggering}
                >
                  <Play size={18} />
                  {midcpniftyTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* MidcapNifty Option Chain Statistics Card */}
            {midcpniftyStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>MidcapNifty Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{midcpniftyStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{midcpniftyStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(midcpniftyStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {midcpniftyExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{midcpniftyExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* MidcapNifty Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>MidcapNifty Option Chain Collected Data</h2>
                <span className="badge">{midcpniftyData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['midcpnifty']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      midcpnifty: { ...prev.midcpnifty, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['midcpnifty']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      midcpnifty: { ...prev.midcpnifty, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('midcpnifty')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['midcpnifty']?.startDate || dateFilters['midcpnifty']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('midcpnifty')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {midcpniftyData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {midcpniftyData.map((record) => (
                        <tr 
                          key={record._id}
                          onClick={() => handleRowClick(record, 'midcpnifty')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'midcpnifty')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="midcpnifty" />
            </div>
          </>
        ) : activeTab === 'hdfcbank' ? (
          <>
            {/* HDFC Bank Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>HDFC Bank Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={hdfcbankStatus?.running ? 'Running' : 'Stopped'}
                  icon={hdfcbankStatus?.running ? CheckCircle : XCircle}
                  status={hdfcbankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(hdfcbankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(hdfcbankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={hdfcbankStatus?.last_status ? 
                    hdfcbankStatus.last_status.charAt(0).toUpperCase() + hdfcbankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={hdfcbankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={hdfcbankStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('hdfcbank')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleHdfcbankTrigger} 
                  className="btn btn-primary"
                  disabled={hdfcbankTriggering}
                >
                  <Play size={18} />
                  {hdfcbankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* HDFC Bank Option Chain Statistics Card */}
            {hdfcbankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>HDFC Bank Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{hdfcbankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{hdfcbankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(hdfcbankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {hdfcbankExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{hdfcbankExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* HDFC Bank Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>HDFC Bank Option Chain Collected Data</h2>
                <span className="badge">{hdfcbankData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['hdfcbank']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      hdfcbank: { ...prev.hdfcbank, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['hdfcbank']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      hdfcbank: { ...prev.hdfcbank, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('hdfcbank')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['hdfcbank']?.startDate || dateFilters['hdfcbank']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('hdfcbank')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {hdfcbankData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {hdfcbankData.map((record) => (
                        <tr 
                          key={record._id}
                          onClick={() => handleRowClick(record, 'hdfcbank')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'hdfcbank')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="hdfcbank" />
            </div>
          </>
        ) : activeTab === 'icicibank' ? (
          <>
            {/* ICICI Bank Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>ICICI Bank Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={icicibankStatus?.running ? 'Running' : 'Stopped'}
                  icon={icicibankStatus?.running ? CheckCircle : XCircle}
                  status={icicibankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(icicibankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(icicibankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={icicibankStatus?.last_status ? 
                    icicibankStatus.last_status.charAt(0).toUpperCase() + icicibankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={icicibankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={icicibankStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('icicibank')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleIcicibankTrigger} 
                  className="btn btn-primary"
                  disabled={icicibankTriggering}
                >
                  <Play size={18} />
                  {icicibankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* ICICI Bank Option Chain Statistics Card */}
            {icicibankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>ICICI Bank Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{icicibankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{icicibankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(icicibankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {icicibankExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{icicibankExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ICICI Bank Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>ICICI Bank Option Chain Collected Data</h2>
                <span className="badge">{icicibankData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['icicibank']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      icicibank: { ...prev.icicibank, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['icicibank']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      icicibank: { ...prev.icicibank, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('icicibank')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['icicibank']?.startDate || dateFilters['icicibank']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('icicibank')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {icicibankData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {icicibankData.map((record) => (
                        <tr 
                          key={record._id}
                          onClick={() => handleRowClick(record, 'icicibank')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'icicibank')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="icicibank" />
            </div>
          </>
        ) : activeTab === 'sbin' ? (
          <>
            {/* SBIN Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>SBIN Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={sbinStatus?.running ? 'Running' : 'Stopped'}
                  icon={sbinStatus?.running ? CheckCircle : XCircle}
                  status={sbinStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(sbinStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(sbinStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={sbinStatus?.last_status ? 
                    sbinStatus.last_status.charAt(0).toUpperCase() + sbinStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={sbinStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={sbinStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('sbin')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleSbinTrigger} 
                  className="btn btn-primary"
                  disabled={sbinTriggering}
                >
                  <Play size={18} />
                  {sbinTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* SBIN Option Chain Statistics Card */}
            {sbinStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>SBIN Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{sbinStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{sbinStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(sbinStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {sbinExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{sbinExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* SBIN Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>SBIN Option Chain Collected Data</h2>
                <span className="badge">{sbinData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['sbin']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      sbin: { ...prev.sbin, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['sbin']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      sbin: { ...prev.sbin, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('sbin')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['sbin']?.startDate || dateFilters['sbin']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('sbin')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {sbinData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sbinData.map((record) => (
                        <tr 
                          key={record._id}
                          onClick={() => handleRowClick(record, 'sbin')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'sbin')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="sbin" />
            </div>
          </>
        ) : activeTab === 'kotakbank' ? (
          <>
            {/* Kotak Bank Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Kotak Bank Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={kotakbankStatus?.running ? 'Running' : 'Stopped'}
                  icon={kotakbankStatus?.running ? CheckCircle : XCircle}
                  status={kotakbankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(kotakbankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(kotakbankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={kotakbankStatus?.last_status ? 
                    kotakbankStatus.last_status.charAt(0).toUpperCase() + kotakbankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={kotakbankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={kotakbankStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('kotakbank')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleKotakbankTrigger} 
                  className="btn btn-primary"
                  disabled={kotakbankTriggering}
                >
                  <Play size={18} />
                  {kotakbankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Kotak Bank Option Chain Statistics Card */}
            {kotakbankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Kotak Bank Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{kotakbankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{kotakbankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(kotakbankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {kotakbankExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{kotakbankExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Kotak Bank Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Kotak Bank Option Chain Collected Data</h2>
                <span className="badge">{kotakbankData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['kotakbank']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      kotakbank: { ...prev.kotakbank, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['kotakbank']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      kotakbank: { ...prev.kotakbank, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('kotakbank')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['kotakbank']?.startDate || dateFilters['kotakbank']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('kotakbank')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {kotakbankData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {kotakbankData.map((record) => (
                        <tr 
                          key={record._id}
                          onClick={() => handleRowClick(record, 'kotakbank')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'kotakbank')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="kotakbank" />
            </div>
          </>
        ) : activeTab === 'axisbank' ? (
          <>
            {/* Axis Bank Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Axis Bank Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={axisbankStatus?.running ? 'Running' : 'Stopped'}
                  icon={axisbankStatus?.running ? CheckCircle : XCircle}
                  status={axisbankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(axisbankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(axisbankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={axisbankStatus?.last_status ? 
                    axisbankStatus.last_status.charAt(0).toUpperCase() + axisbankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={axisbankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={axisbankStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('axisbank')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleAxisbankTrigger} 
                  className="btn btn-primary"
                  disabled={axisbankTriggering}
                >
                  <Play size={18} />
                  {axisbankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Axis Bank Option Chain Statistics Card */}
            {axisbankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Axis Bank Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{axisbankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{axisbankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(axisbankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {axisbankExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{axisbankExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Axis Bank Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Axis Bank Option Chain Collected Data</h2>
                <span className="badge">{axisbankData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['axisbank']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      axisbank: { ...prev.axisbank, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['axisbank']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      axisbank: { ...prev.axisbank, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('axisbank')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['axisbank']?.startDate || dateFilters['axisbank']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('axisbank')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {axisbankData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {axisbankData.map((record) => (
                        <tr
                          key={record._id}
                          onClick={() => handleRowClick(record, 'axisbank')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'axisbank')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="axisbank" />
            </div>
          </>
        ) : activeTab === 'bankbaroda' ? (
          <>
            {/* Bank of Baroda Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Bank of Baroda Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={bankbarodaStatus?.running ? 'Running' : 'Stopped'}
                  icon={bankbarodaStatus?.running ? CheckCircle : XCircle}
                  status={bankbarodaStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(bankbarodaStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(bankbarodaStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={bankbarodaStatus?.last_status ? 
                    bankbarodaStatus.last_status.charAt(0).toUpperCase() + bankbarodaStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={bankbarodaStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={bankbarodaStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('bankbaroda')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleBankbarodaTrigger} 
                  className="btn btn-primary"
                  disabled={bankbarodaTriggering}
                >
                  <Play size={18} />
                  {bankbarodaTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Bank of Baroda Option Chain Statistics Card */}
            {bankbarodaStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Bank of Baroda Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{bankbarodaStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{bankbarodaStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(bankbarodaStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {bankbarodaExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{bankbarodaExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Bank of Baroda Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Bank of Baroda Option Chain Collected Data</h2>
                <span className="badge">{bankbarodaData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['bankbaroda']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      bankbaroda: { ...prev.bankbaroda, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['bankbaroda']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      bankbaroda: { ...prev.bankbaroda, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('bankbaroda')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['bankbaroda']?.startDate || dateFilters['bankbaroda']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('bankbaroda')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {bankbarodaData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bankbarodaData.map((record) => (
                        <tr
                          key={record._id}
                          onClick={() => handleRowClick(record, 'bankbaroda')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'bankbaroda')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="bankbaroda" />
            </div>
          </>
        ) : activeTab === 'pnb' ? (
          <>
            {/* PNB Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>PNB Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={pnbStatus?.running ? 'Running' : 'Stopped'}
                  icon={pnbStatus?.running ? CheckCircle : XCircle}
                  status={pnbStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(pnbStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(pnbStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={pnbStatus?.last_status ? 
                    pnbStatus.last_status.charAt(0).toUpperCase() + pnbStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={pnbStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={pnbStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('pnb')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handlePnbTrigger} 
                  className="btn btn-primary"
                  disabled={pnbTriggering}
                >
                  <Play size={18} />
                  {pnbTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* PNB Option Chain Statistics Card */}
            {pnbStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>PNB Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{pnbStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{pnbStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(pnbStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {pnbExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{pnbExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* PNB Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>PNB Option Chain Collected Data</h2>
                <span className="badge">{pnbData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['pnb']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      pnb: { ...prev.pnb, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['pnb']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      pnb: { ...prev.pnb, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('pnb')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['pnb']?.startDate || dateFilters['pnb']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('pnb')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {pnbData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pnbData.map((record) => (
                        <tr
                          key={record._id}
                          onClick={() => handleRowClick(record, 'pnb')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'pnb')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="pnb" />
            </div>
          </>
        ) : activeTab === 'canbk' ? (
          <>
            {/* CANBK Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>CANBK Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={canbkStatus?.running ? 'Running' : 'Stopped'}
                  icon={canbkStatus?.running ? CheckCircle : XCircle}
                  status={canbkStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(canbkStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(canbkStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={canbkStatus?.last_status ? 
                    canbkStatus.last_status.charAt(0).toUpperCase() + canbkStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={canbkStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={canbkStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('canbk')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleCanbkTrigger} 
                  className="btn btn-primary"
                  disabled={canbkTriggering}
                >
                  <Play size={18} />
                  {canbkTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* CANBK Option Chain Statistics Card */}
            {canbkStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>CANBK Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{canbkStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{canbkStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(canbkStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {canbkExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{canbkExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* CANBK Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>CANBK Option Chain Collected Data</h2>
                <span className="badge">{canbkData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['canbk']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      canbk: { ...prev.canbk, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['canbk']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      canbk: { ...prev.canbk, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('canbk')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['canbk']?.startDate || dateFilters['canbk']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('canbk')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {canbkData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {canbkData.map((record) => (
                        <tr
                          key={record._id}
                          onClick={() => handleRowClick(record, 'canbk')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'canbk')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="canbk" />
            </div>
          </>
        ) : activeTab === 'aubank' ? (
          <>
            {/* AUBANK Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>AUBANK Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={aubankStatus?.running ? 'Running' : 'Stopped'}
                  icon={aubankStatus?.running ? CheckCircle : XCircle}
                  status={aubankStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(aubankStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(aubankStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={aubankStatus?.last_status ? 
                    aubankStatus.last_status.charAt(0).toUpperCase() + aubankStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={aubankStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={aubankStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('aubank')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleAubankTrigger} 
                  className="btn btn-primary"
                  disabled={aubankTriggering}
                >
                  <Play size={18} />
                  {aubankTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* AUBANK Option Chain Statistics Card */}
            {aubankStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>AUBANK Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{aubankStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{aubankStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(aubankStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {aubankExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{aubankExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* AUBANK Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>AUBANK Option Chain Collected Data</h2>
                <span className="badge">{aubankData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['aubank']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      aubank: { ...prev.aubank, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['aubank']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      aubank: { ...prev.aubank, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('aubank')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['aubank']?.startDate || dateFilters['aubank']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('aubank')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {aubankData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aubankData.map((record) => (
                        <tr
                          key={record._id}
                          onClick={() => handleRowClick(record, 'aubank')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'aubank')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="aubank" />
            </div>
          </>
        ) : activeTab === 'indusindbk' ? (
          <>
            {/* INDUSINDBK Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>INDUSINDBK Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={indusindbkStatus?.running ? 'Running' : 'Stopped'}
                  icon={indusindbkStatus?.running ? CheckCircle : XCircle}
                  status={indusindbkStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(indusindbkStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(indusindbkStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={indusindbkStatus?.last_status ? 
                    indusindbkStatus.last_status.charAt(0).toUpperCase() + indusindbkStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={indusindbkStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={indusindbkStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('indusindbk')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleIndusindbkTrigger} 
                  className="btn btn-primary"
                  disabled={indusindbkTriggering}
                >
                  <Play size={18} />
                  {indusindbkTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* INDUSINDBK Option Chain Statistics Card */}
            {indusindbkStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>INDUSINDBK Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{indusindbkStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{indusindbkStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(indusindbkStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {indusindbkExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{indusindbkExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* INDUSINDBK Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>INDUSINDBK Option Chain Collected Data</h2>
                <span className="badge">{indusindbkData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['indusindbk']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      indusindbk: { ...prev.indusindbk, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['indusindbk']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      indusindbk: { ...prev.indusindbk, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('indusindbk')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['indusindbk']?.startDate || dateFilters['indusindbk']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('indusindbk')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {indusindbkData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {indusindbkData.map((record) => (
                        <tr
                          key={record._id}
                          onClick={() => handleRowClick(record, 'indusindbk')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'indusindbk')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="indusindbk" />
            </div>
          </>
        ) : activeTab === 'idfcfirstb' ? (
          <>
            {/* IDFCFIRSTB Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>IDFCFIRSTB Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={idfcfirstbStatus?.running ? 'Running' : 'Stopped'}
                  icon={idfcfirstbStatus?.running ? CheckCircle : XCircle}
                  status={idfcfirstbStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(idfcfirstbStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(idfcfirstbStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={idfcfirstbStatus?.last_status ? 
                    idfcfirstbStatus.last_status.charAt(0).toUpperCase() + idfcfirstbStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={idfcfirstbStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={idfcfirstbStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('idfcfirstb')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleIdfcfirstbTrigger} 
                  className="btn btn-primary"
                  disabled={idfcfirstbTriggering}
                >
                  <Play size={18} />
                  {idfcfirstbTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* IDFCFIRSTB Option Chain Statistics Card */}
            {idfcfirstbStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>IDFCFIRSTB Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{idfcfirstbStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{idfcfirstbStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(idfcfirstbStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {idfcfirstbExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{idfcfirstbExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* IDFCFIRSTB Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>IDFCFIRSTB Option Chain Collected Data</h2>
                <span className="badge">{idfcfirstbData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['idfcfirstb']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      idfcfirstb: { ...prev.idfcfirstb, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['idfcfirstb']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      idfcfirstb: { ...prev.idfcfirstb, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('idfcfirstb')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['idfcfirstb']?.startDate || dateFilters['idfcfirstb']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('idfcfirstb')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {idfcfirstbData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {idfcfirstbData.map((record) => (
                        <tr
                          key={record._id}
                          onClick={() => handleRowClick(record, 'idfcfirstb')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'idfcfirstb')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="idfcfirstb" />
            </div>
          </>
        ) : activeTab === 'federalbnk' ? (
          <>
            {/* FEDERALBNK Option Chain Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>FEDERALBNK Option Chain Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={federalbnkStatus?.running ? 'Running' : 'Stopped'}
                  icon={federalbnkStatus?.running ? CheckCircle : XCircle}
                  status={federalbnkStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(federalbnkStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(federalbnkStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={federalbnkStatus?.last_status ? 
                    federalbnkStatus.last_status.charAt(0).toUpperCase() + federalbnkStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={federalbnkStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={federalbnkStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('federalbnk')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleFederalbnkTrigger} 
                  className="btn btn-primary"
                  disabled={federalbnkTriggering}
                >
                  <Play size={18} />
                  {federalbnkTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* FEDERALBNK Option Chain Statistics Card */}
            {federalbnkStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>FEDERALBNK Option Chain Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{federalbnkStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{federalbnkStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <BarChart3 size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Underlying Value</div>
                      <div className="stat-value">{formatNumber(federalbnkStats.latest_underlying_value)}</div>
                    </div>
                  </div>
                  {federalbnkExpiry && (
                    <div className="stat-item">
                      <Calendar size={24} className="stat-icon" />
                      <div>
                        <div className="stat-label">Current Expiry Date</div>
                        <div className="stat-value" style={{ color: 'var(--green)', fontWeight: 'bold' }}>{federalbnkExpiry}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* FEDERALBNK Option Chain Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>FEDERALBNK Option Chain Collected Data</h2>
                <span className="badge">{federalbnkData.length} records</span>
              </div>

              {/* Date Filter */}
              <div className="date-filter-container">
                <div className="date-filter-group">
                  <Filter size={18} />
                  <label>Start Date:</label>
                  <input
                    type="date"
                    value={dateFilters['federalbnk']?.startDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      federalbnk: { ...prev.federalbnk, startDate: e.target.value }
                    }))}
                  />
                  <label>End Date:</label>
                  <input
                    type="date"
                    value={dateFilters['federalbnk']?.endDate || ''}
                    onChange={(e) => setDateFilters(prev => ({
                      ...prev,
                      federalbnk: { ...prev.federalbnk, endDate: e.target.value }
                    }))}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyDateFilter('federalbnk')}
                  >
                    Apply Filter
                  </button>
                  {(dateFilters['federalbnk']?.startDate || dateFilters['federalbnk']?.endDate) && (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleClearDateFilter('federalbnk')}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {federalbnkData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Underlying Value</th>
                        <th>Data Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {federalbnkData.map((record) => (
                        <tr
                          key={record._id}
                          onClick={() => handleRowClick(record, 'federalbnk')}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="date-cell">{record.timestamp || '-'}</td>
                          <td>{formatNumber(record.underlyingValue)}</td>
                          <td>{record.dataCount || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                          <td onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn-icon btn-danger"
                              onClick={() => handleDeleteRecord(record._id, 'federalbnk')}
                              title="Delete record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="federalbnk" />
            </div>
          </>
        ) : activeTab === 'gainers' ? (
          <>
            {/* Top 20 Gainers Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Top 20 Gainers Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={gainersStatus?.running ? 'Running' : 'Stopped'}
                  icon={gainersStatus?.running ? CheckCircle : XCircle}
                  status={gainersStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(gainersStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(gainersStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={gainersStatus?.last_status ? 
                    gainersStatus.last_status.charAt(0).toUpperCase() + gainersStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={gainersStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={gainersStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('gainers')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleGainersTrigger} 
                  className="btn btn-primary"
                  disabled={gainersTriggering}
                >
                  <Play size={18} />
                  {gainersTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Top 20 Gainers Statistics Card */}
            {gainersStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Top 20 Gainers Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{gainersStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{gainersStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <TrendingUp size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest NIFTY Count</div>
                      <div className="stat-value">{gainersStats.latest_nifty_count || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <TrendingUp size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest BANKNIFTY Count</div>
                      <div className="stat-value">{gainersStats.latest_banknifty_count || 0}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Top 20 Gainers Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Top 20 Gainers Collected Data</h2>
                <span className="badge">{gainersData.length} records</span>
              </div>

              {gainersData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                  <p style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
                    Click "Trigger Collection Now" to collect data
                  </p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>NIFTY Count</th>
                        <th>BANKNIFTY Count</th>
                        <th>Legends Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {gainersData.map((record) => (
                        <tr key={record._id}>
                          <td>{record.timestamp || '-'}</td>
                          <td>{record.nifty_count || 0}</td>
                          <td>{record.banknifty_count || 0}</td>
                          <td>{record.legends?.length || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="gainers" />
            </div>
          </>
        ) : activeTab === 'losers' ? (
          <>
            {/* Top 20 Losers Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>Top 20 Losers Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={losersStatus?.running ? 'Running' : 'Stopped'}
                  icon={losersStatus?.running ? CheckCircle : XCircle}
                  status={losersStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(losersStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(losersStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={losersStatus?.last_status ? 
                    losersStatus.last_status.charAt(0).toUpperCase() + losersStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={losersStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={losersStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('losers')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleLosersTrigger} 
                  className="btn btn-primary"
                  disabled={losersTriggering}
                >
                  <Play size={18} />
                  {losersTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* Top 20 Losers Statistics Card */}
            {losersStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>Top 20 Losers Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{losersStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Clock size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest Timestamp</div>
                      <div className="stat-value">{losersStats.latest_timestamp || '-'}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <TrendingDown size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest NIFTY Count</div>
                      <div className="stat-value">{losersStats.latest_nifty_count || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <TrendingDown size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Latest BANKNIFTY Count</div>
                      <div className="stat-value">{losersStats.latest_banknifty_count || 0}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Top 20 Losers Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Top 20 Losers Collected Data</h2>
                <span className="badge">{losersData.length} records</span>
              </div>

              {losersData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No data available</p>
                  <p style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
                    Click "Trigger Collection Now" to collect data
                  </p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>NIFTY Count</th>
                        <th>BANKNIFTY Count</th>
                        <th>Legends Count</th>
                        <th>Inserted At</th>
                        <th>Updated At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {losersData.map((record) => (
                        <tr key={record._id}>
                          <td>{record.timestamp || '-'}</td>
                          <td>{record.nifty_count || 0}</td>
                          <td>{record.banknifty_count || 0}</td>
                          <td>{record.legends?.length || 0}</td>
                          <td className="muted">{formatDateTime(record.insertedAt)}</td>
                          <td className="muted">{formatDateTime(record.updatedAt)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="losers" />
            </div>
          </>
        ) : activeTab === 'news' ? (
          <>
            {/* News Collector Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>News Collector Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={newsStatus?.running ? 'Running' : 'Stopped'}
                  icon={newsStatus?.running ? CheckCircle : XCircle}
                  status={newsStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(newsStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(newsStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={newsStatus?.last_status ? 
                    newsStatus.last_status.charAt(0).toUpperCase() + newsStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={newsStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={newsStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('news')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleNewsTrigger} 
                  className="btn btn-primary"
                  disabled={newsTriggering}
                >
                  <Play size={18} />
                  {newsTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* News Statistics Card */}
            {newsStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>News Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{newsStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Newspaper size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Today's News</div>
                      <div className="stat-value">{newsStats.today_count || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <TrendingUp size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label" style={{ color: 'var(--green)' }}>Positive</div>
                      <div className="stat-value">{newsStats.today_positive || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <TrendingDown size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label" style={{ color: 'var(--red)' }}>Negative</div>
                      <div className="stat-value">{newsStats.today_negative || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Activity size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Neutral</div>
                      <div className="stat-value">{newsStats.today_neutral || 0}</div>
                    </div>
                  </div>
                </div>
                {newsStats.top_keywords && newsStats.top_keywords.length > 0 && (
                  <div className="stats-keywords-section">
                    <div className="stat-label" style={{ marginBottom: '0.75rem', fontSize: '0.8rem' }}>Top Keywords Today</div>
                    <div className="keywords-list">
                      {newsStats.top_keywords.map((item, idx) => (
                        <span key={idx} className="badge badge-keyword">
                          {item.keyword} ({item.count})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* News Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Collected News</h2>
                <span className="badge">{newsData.length} records</span>
              </div>

              {newsData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No news data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Keyword</th>
                        <th>Title</th>
                        <th>Source</th>
                        <th>Sentiment</th>
                        <th>Published</th>
                      </tr>
                    </thead>
                    <tbody>
                      {newsData.map((record) => (
                        <tr key={record._id}>
                          <td className="date-cell">{record.date || '-'}</td>
                          <td><strong>{record.keyword || '-'}</strong></td>
                          <td>
                            <a 
                              href={record.link} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              style={{ color: 'var(--primary)', textDecoration: 'none' }}
                              onMouseOver={(e) => e.target.style.textDecoration = 'underline'}
                              onMouseOut={(e) => e.target.style.textDecoration = 'none'}
                            >
                              {record.title || '-'}
                            </a>
                          </td>
                          <td className="muted">{record.source || '-'}</td>
                          <td className={getSentimentColor(record.sentiment)}>
                            {record.sentiment === 'Positive' && <TrendingUp size={16} />}
                            {record.sentiment === 'Negative' && <TrendingDown size={16} />}
                            {record.sentiment || 'Neutral'}
                          </td>
                          <td className="muted">{formatDateTime(record.pub_date)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="news" />
            </div>
          </>
        ) : activeTab === 'settings' ? (
          <Settings authToken={authToken} />
        ) : activeTab === 'livemint-news' ? (
          <>
            {/* LiveMint News Collector Status Card */}
            <div className="card status-card">
              <div className="card-header">
                <h2>LiveMint News Collector Cronjob Status</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>

              <div className="status-grid">
                <StatusItem
                  label="Status"
                  value={livemintNewsStatus?.running ? 'Running' : 'Stopped'}
                  icon={livemintNewsStatus?.running ? CheckCircle : XCircle}
                  status={livemintNewsStatus?.running ? 'success' : 'danger'}
                />
                <StatusItem
                  label="Next Run"
                  value={formatDateTime(livemintNewsStatus?.next_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Run"
                  value={formatDateTime(livemintNewsStatus?.last_run)}
                  icon={Clock}
                />
                <StatusItem
                  label="Last Status"
                  value={livemintNewsStatus?.last_status ? 
                    livemintNewsStatus.last_status.charAt(0).toUpperCase() + livemintNewsStatus.last_status.slice(1) : 
                    'Unknown'}
                  icon={livemintNewsStatus?.last_status === 'success' ? CheckCircle : AlertCircle}
                  status={livemintNewsStatus?.last_status === 'success' ? 'success' : 'warning'}
                />
                {renderConfigStatusItems('livemint-news')}
              </div>

              <div className="actions">
                <button 
                  onClick={refreshCurrentTab} 
                  className="btn btn-secondary"
                >
                  <RefreshCw size={18} />
                  Refresh Status
                </button>
                <button 
                  onClick={handleLivemintNewsTrigger} 
                  className="btn btn-primary"
                  disabled={livemintNewsTriggering}
                >
                  <Play size={18} />
                  {livemintNewsTriggering ? 'Processing...' : 'Trigger Collection Now'}
                </button>
              </div>
            </div>

            {/* LiveMint News Statistics Card */}
            {livemintNewsStats && (
              <div className="card stats-card">
                <div className="card-header">
                  <h2>LiveMint News Statistics</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <Database size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Total Records</div>
                      <div className="stat-value">{livemintNewsStats.total_records || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Newspaper size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Today's News</div>
                      <div className="stat-value">{livemintNewsStats.today_count || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <TrendingUp size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label" style={{ color: 'var(--green)' }}>Positive</div>
                      <div className="stat-value">{livemintNewsStats.today_positive || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <TrendingDown size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label" style={{ color: 'var(--red)' }}>Negative</div>
                      <div className="stat-value">{livemintNewsStats.today_negative || 0}</div>
                    </div>
                  </div>
                  <div className="stat-item">
                    <Activity size={24} className="stat-icon" />
                    <div>
                      <div className="stat-label">Neutral</div>
                      <div className="stat-value">{livemintNewsStats.today_neutral || 0}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* LiveMint News Data Table Card */}
            <div className="card data-card">
              <div className="card-header">
                <h2>Collected LiveMint News</h2>
                <span className="badge">{livemintNewsData.length} records</span>
              </div>

              {livemintNewsData.length === 0 ? (
                <div className="empty-state">
                  <Database size={48} />
                  <p>No news data available</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Title</th>
                        <th>Source</th>
                        <th>Sentiment</th>
                        <th>Published</th>
                      </tr>
                    </thead>
                    <tbody>
                      {livemintNewsData.map((record) => (
                        <tr key={record._id}>
                          <td className="date-cell">{record.date || '-'}</td>
                          <td>
                            <a 
                              href={record.link} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              style={{ color: 'var(--primary)', textDecoration: 'none' }}
                              onMouseOver={(e) => e.target.style.textDecoration = 'underline'}
                              onMouseOut={(e) => e.target.style.textDecoration = 'none'}
                            >
                              {record.title || '-'}
                            </a>
                          </td>
                          <td className="muted">{record.source || '-'}</td>
                          <td className={getSentimentColor(record.sentiment)}>
                            {record.sentiment === 'Positive' && <TrendingUp size={16} />}
                            {record.sentiment === 'Negative' && <TrendingDown size={16} />}
                            {record.sentiment || 'Neutral'}
                          </td>
                          <td className="muted">{formatDateTime(record.pub_date)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pagination tabName="livemint-news" />
            </div>
          </>
        ) : activeTab === 'heatmap' ? (
          <>
            <div className="card data-card">
              <div className="card-header">
                <h2>Stock Market Heatmap</h2>
                <button onClick={refreshCurrentTab} className="btn-icon">
                  <RefreshCw size={20} />
                </button>
              </div>
              <HeatmapView 
                gainersData={heatmapGainersData}
                losersData={heatmapLosersData}
                loading={heatmapLoading}
              />
            </div>
          </>
        ) : null}
        </div>
      </main>
    </div>
    
    {/* Detail View Modal */}
    {selectedRecord && (
      <DetailView
        record={selectedRecord}
        tabName={selectedTabName}
        onClose={() => {
          setSelectedRecord(null)
          setSelectedTabName(null)
        }}
      />
    )}
    </>
  )
}

function StatusItem({ label, value, icon: Icon, status }) {
  return (
    <div className="status-item">
      <div className="status-item-header">
        <span className="status-label">{label}</span>
        {Icon && <Icon size={20} className={`status-icon ${status || ''}`} />}
      </div>
      <div className="status-value">{value}</div>
    </div>
  )
}

export default App

