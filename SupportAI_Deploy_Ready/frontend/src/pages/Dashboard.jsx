import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../utils/api'

// ── Mini Bar Chart ────────────────────────────────────────────────────────────
function BarChart({ data }) {
  const max = Math.max(...data.map(d => d.count), 1)
  return (
    <div className="flex items-end gap-2 h-32 w-full">
      {data.map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1.5">
          <span className="text-mist/40 text-xs font-mono">{d.count}</span>
          <div className="w-full flex items-end" style={{ height: '80px' }}>
            <div
              className="w-full rounded-t-md bg-gradient-to-t from-plasma to-neon/80 transition-all duration-700"
              style={{ height: `${Math.max((d.count / max) * 80, d.count > 0 ? 6 : 2)}px` }}
            />
          </div>
          <span className="text-mist/40 text-xs">{d.day}</span>
        </div>
      ))}
    </div>
  )
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ icon, label, value, sub, accent }) {
  return (
    <div className={`glass-card p-5 flex items-center gap-4 ${accent ? 'border-' + accent + '/30' : ''}`}>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center text-xl shrink-0
        ${accent === 'red' ? 'bg-red-500/15 text-red-400' : 'bg-plasma/15 text-neon'}`}>
        {icon}
      </div>
      <div>
        <p className="text-mist/40 text-xs mb-0.5">{label}</p>
        <p className={`text-2xl font-bold ${accent === 'red' ? 'text-red-400' : 'text-white'}`}>{value}</p>
        {sub && <p className="text-mist/30 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

// ── Admin Answer Modal ─────────────────────────────────────────────────────────
function AnswerModal({ item, onClose, onSubmit, loading }) {
  const [answer, setAnswer] = useState('')
  if (!item) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 glass-card w-full max-w-lg p-6 animate-slide-up">
        <div className="flex items-start justify-between mb-5">
          <div>
            <h3 className="text-white font-bold text-lg">Provide an Answer</h3>
            <p className="text-mist/40 text-sm mt-1">This will be indexed so future customers get this answer automatically</p>
          </div>
          <button onClick={onClose} className="text-mist/40 hover:text-white transition-colors ml-4 shrink-0">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Question preview */}
        <div className="bg-void/60 border border-white/5 rounded-xl p-4 mb-4">
          <p className="text-mist/40 text-xs mb-1 uppercase tracking-wider">Customer Question</p>
          <p className="text-white text-sm font-medium">"{item.question}"</p>
          {item.count > 1 && (
            <p className="text-mist/30 text-xs mt-2">
              Asked {item.count} times in {item.variants?.length} variation{item.variants?.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        {/* Answer input */}
        <div className="mb-5">
          <label className="text-mist/50 text-xs mb-2 block uppercase tracking-wider">Your Answer</label>
          <textarea
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            rows={5}
            placeholder="Type a clear, helpful answer for this question..."
            className="w-full bg-void border border-white/10 rounded-xl px-4 py-3 text-mist text-sm
                       placeholder-mist/30 focus:outline-none focus:border-plasma/60 focus:ring-2
                       focus:ring-plasma/20 transition-all duration-200 resize-none"
          />
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="btn-ghost flex-1">Cancel</button>
          <button
            onClick={() => onSubmit(item.question, answer)}
            disabled={!answer.trim() || loading}
            className="btn-primary flex-1"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Indexing...
              </span>
            ) : '✓ Submit & Index Answer'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const fileRef = useRef()

  const [activeNav, setActiveNav] = useState('home')

  // Existing state
  const [business, setBusiness] = useState(null)
  const [companyName, setCompanyName] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [trainLoading, setTrainLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [trainTab, setTrainTab] = useState('file')
  const [scrapeUrl, setScrapeUrl] = useState('')
  const [crawl, setCrawl] = useState(false)
  const [scrapeLoading, setScrapeLoading] = useState(false)

  // Analytics
  const [analytics, setAnalytics] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)

  // Chat history
  const [chatHistory, setChatHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historySearch, setHistorySearch] = useState('')
  const [expandedChat, setExpandedChat] = useState(null)
  const [historyFilter, setHistoryFilter] = useState('all') // 'all' | 'unanswered' | 'answered'

  // FAQ
  const [faq, setFaq] = useState([])
  const [faqLoading, setFaqLoading] = useState(false)
  const [expandedFaq, setExpandedFaq] = useState(null)

  // Unanswered
  const [unanswered, setUnanswered] = useState([])
  const [unansweredLoading, setUnansweredLoading] = useState(false)
  const [answerModal, setAnswerModal] = useState(null)
  const [answerLoading, setAnswerLoading] = useState(false)
  const [unansweredCount, setUnansweredCount] = useState(0)

  useEffect(() => { fetchBusiness() }, [])

  useEffect(() => {
    if (activeNav === 'analytics') fetchAnalytics()
    if (activeNav === 'history') fetchChatHistory()
    if (activeNav === 'faq') fetchFaq()
    if (activeNav === 'unanswered') fetchUnanswered()
  }, [activeNav])

  const fetchBusiness = async () => {
    try {
      const { data } = await api.get('/business/me')
      if (data) { setBusiness(data); setCompanyName(data.company_name) }
    } catch (e) {}
    // Also fetch unanswered count for sidebar badge
    try {
      const { data } = await api.get('/analytics/analytics')
      setUnansweredCount(data.unanswered_count || 0)
    } catch (e) {}
  }

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true)
    try {
      const { data } = await api.get('/analytics/analytics')
      setAnalytics(data)
      setUnansweredCount(data.unanswered_count || 0)
    } catch (e) {}
    finally { setAnalyticsLoading(false) }
  }

  const fetchChatHistory = async () => {
    setHistoryLoading(true)
    try {
      const { data } = await api.get('/analytics/chat-history')
      setChatHistory(data)
    } catch (e) {}
    finally { setHistoryLoading(false) }
  }

  const fetchFaq = async () => {
    setFaqLoading(true)
    try {
      const { data } = await api.get('/analytics/faq')
      setFaq(data)
    } catch (e) {}
    finally { setFaqLoading(false) }
  }

  const fetchUnanswered = async () => {
    setUnansweredLoading(true)
    try {
      const { data } = await api.get('/analytics/unanswered')
      setUnanswered(data)
      setUnansweredCount(data.length)
    } catch (e) {}
    finally { setUnansweredLoading(false) }
  }

  const handleAdminAnswer = async (question, answer) => {
    setAnswerLoading(true)
    try {
      await api.post('/analytics/admin-answer', { question, answer })
      setAnswerModal(null)
      setMessage('✓ Answer indexed! Future questions will be answered automatically.')
      setTimeout(() => setMessage(null), 4000)
      fetchUnanswered()
      setUnansweredCount(c => Math.max(0, c - 1))
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to submit answer')
      setTimeout(() => setError(null), 4000)
    }
    finally { setAnswerLoading(false) }
  }

  const handleSaveBusiness = async () => {
    if (!companyName.trim()) return
    setLoading(true); setError(null)
    try {
      const { data } = await api.post('/business/create', { company_name: companyName.trim() })
      setBusiness(data)
      setMessage('Business profile saved!')
      setTimeout(() => setMessage(null), 3000)
    } catch (e) { setError(e.response?.data?.detail || 'Failed to save') }
    finally { setLoading(false) }
  }

  const handleTrain = async () => {
    if (!file || !business) return
    setTrainLoading(true); setError(null); setMessage(null)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('business_id', business.business_id)
    try {
      const { data } = await api.post('/business/train', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      setMessage(`✓ ${data.message} (${data.chunks_indexed} chunks indexed)`)
      setFile(null)
      await fetchBusiness()
    } catch (e) { setError(e.response?.data?.detail || 'Training failed') }
    finally { setTrainLoading(false) }
  }

  const handleTrainFromUrl = async () => {
    if (!scrapeUrl.trim() || !business) return
    setScrapeLoading(true); setError(null); setMessage(null)
    try {
      const { data } = await api.post('/business/train-from-url', {
        business_id: business.business_id, url: scrapeUrl.trim(), crawl
      })
      setMessage(`✓ ${data.message} (${data.chunks_indexed} chunks indexed)`)
      setScrapeUrl('')
      await fetchBusiness()
    } catch (e) { setError(e.response?.data?.detail || 'Scraping failed') }
    finally { setScrapeLoading(false) }
  }

  const handleDrop = (e) => {
    e.preventDefault(); setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) setFile(dropped)
  }

  const chatbotUrl = business ? `${window.location.origin}/chatbot/${business.business_id}` : ''

  const filteredHistory = chatHistory.filter(h => {
    const matchSearch =
      h.user_message.toLowerCase().includes(historySearch.toLowerCase()) ||
      h.bot_response.toLowerCase().includes(historySearch.toLowerCase())
    const matchFilter =
      historyFilter === 'all' ||
      (historyFilter === 'unanswered' && h.unanswered) ||
      (historyFilter === 'answered' && !h.unanswered)
    return matchSearch && matchFilter
  })

  const formatDate = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' +
      d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const navItems = [
    {
      id: 'home', label: 'Dashboard',
      icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    },
    {
      id: 'analytics', label: 'Analytics',
      icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    },
    {
      id: 'unanswered', label: 'Unanswered', badge: unansweredCount,
      icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    },
    {
      id: 'history', label: 'Chat History',
      icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    },
    {
      id: 'faq', label: 'Top Questions',
      icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    },
  ]

  return (
    <div className="min-h-screen bg-obsidian flex">
      {/* Answer Modal */}
      <AnswerModal
        item={answerModal}
        onClose={() => setAnswerModal(null)}
        onSubmit={handleAdminAnswer}
        loading={answerLoading}
      />

      {/* Sidebar */}
      <aside className="w-64 bg-void border-r border-white/5 flex flex-col">
        <div className="p-6 border-b border-white/5">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-plasma rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <span className="font-bold text-white">SupportAI</span>
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
                ${activeNav === item.id ? 'bg-plasma/10 text-neon' : 'text-mist/50 hover:text-mist hover:bg-white/5'}`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {item.icon}
              </svg>
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge > 0 && (
                <span className="bg-red-500 text-white text-xs font-bold rounded-full min-w-[20px] h-5 flex items-center justify-center px-1.5">
                  {item.badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        {business?.trained && (
          <div className="px-4 pb-4">
            <div className="bg-green-500/10 border border-green-500/20 rounded-xl px-3 py-2 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-green-400 text-xs font-medium">Bot is Live</span>
            </div>
          </div>
        )}

        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-plasma/20 rounded-full flex items-center justify-center text-neon text-sm font-bold">
              {user?.name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{user?.name}</p>
              <p className="text-mist/40 text-xs truncate">{user?.email}</p>
            </div>
          </div>
          <button onClick={() => { logout(); navigate('/') }}
                  className="w-full text-left text-mist/40 hover:text-red-400 text-xs transition-colors px-2 py-1">
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-plasma/5 rounded-full blur-[100px] pointer-events-none" />

        {/* Global messages */}
        {(message || error) && (
          <div className="fixed top-4 right-4 z-40 animate-fade-in">
            {message && (
              <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-5 py-3 text-green-400 text-sm shadow-xl backdrop-blur-sm">
                {message}
              </div>
            )}
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-5 py-3 text-red-400 text-sm shadow-xl backdrop-blur-sm">
                {error}
              </div>
            )}
          </div>
        )}

        <div className="relative z-10 max-w-3xl mx-auto px-8 py-10">

          {/* ── DASHBOARD ─────────────────────────────────────────────────── */}
          {activeNav === 'home' && (
            <>
              <div className="mb-10">
                <h1 className="text-3xl font-bold text-white">Dashboard</h1>
                <p className="text-mist/50 mt-1">Manage your AI chatbot</p>
              </div>

              {/* Business Profile */}
              <div className="glass-card p-6 mb-6">
                <h2 className="text-lg font-bold text-white mb-1">Business Profile</h2>
                <p className="text-mist/40 text-sm mb-5">Set your company name for the chatbot</p>
                <div className="flex gap-3">
                  <input type="text" className="input-field flex-1" placeholder="Your Company Name"
                         value={companyName} onChange={e => setCompanyName(e.target.value)} />
                  <button onClick={handleSaveBusiness} disabled={loading || !companyName.trim()} className="btn-primary whitespace-nowrap">
                    {loading ? '...' : 'Save'}
                  </button>
                </div>
              </div>

              {/* Train Chatbot */}
              {business && (
                <div className="glass-card p-6 mb-6">
                  <h2 className="text-lg font-bold text-white mb-1">Train Chatbot</h2>
                  <p className="text-mist/40 text-sm mb-5">Upload a file or scrape a website to train your AI</p>

                  <div className="flex gap-2 mb-6 bg-void rounded-xl p-1">
                    {[['file', '📄 Upload File'], ['url', '🌐 Scrape Website']].map(([id, label]) => (
                      <button key={id} onClick={() => setTrainTab(id)}
                              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200
                                ${trainTab === id ? 'bg-plasma text-white shadow' : 'text-mist/50 hover:text-white'}`}>
                        {label}
                      </button>
                    ))}
                  </div>

                  {trainTab === 'file' && (
                    <>
                      <div
                        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200
                          ${dragging ? 'border-plasma bg-plasma/10' : 'border-white/10 hover:border-plasma/40'}`}
                        onClick={() => fileRef.current?.click()}
                        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={handleDrop}
                      >
                        <input ref={fileRef} type="file" accept=".pdf,.txt" className="hidden"
                               onChange={e => setFile(e.target.files[0])} />
                        {file ? (
                          <div className="flex items-center justify-center gap-3">
                            <div className="w-10 h-10 bg-plasma/20 rounded-xl flex items-center justify-center">
                              <svg className="w-5 h-5 text-neon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                            <div className="text-left">
                              <p className="text-white font-medium text-sm">{file.name}</p>
                              <p className="text-mist/40 text-xs">{(file.size / 1024).toFixed(1)} KB</p>
                            </div>
                            <button onClick={(e) => { e.stopPropagation(); setFile(null) }}
                                    className="ml-2 text-mist/40 hover:text-red-400 transition-colors">
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          </div>
                        ) : (
                          <>
                            <svg className="w-10 h-10 text-mist/20 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            <p className="text-mist/50 text-sm">Drag & drop or <span className="text-neon">browse</span></p>
                            <p className="text-mist/30 text-xs mt-1">PDF or TXT files</p>
                          </>
                        )}
                      </div>
                      <button onClick={handleTrain} disabled={!file || trainLoading} className="btn-primary w-full mt-4 text-center">
                        {trainLoading ? (
                          <span className="flex items-center justify-center gap-2">
                            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            Training chatbot... This may take a minute
                          </span>
                        ) : '🧠 Train Chatbot'}
                      </button>
                    </>
                  )}

                  {trainTab === 'url' && (
                    <>
                      <div className="mb-4">
                        <label className="text-mist/50 text-xs mb-2 block">Website URL</label>
                        <input type="url" placeholder="https://yourcompany.com" value={scrapeUrl}
                               onChange={e => setScrapeUrl(e.target.value)} className="input-field w-full" />
                      </div>
                      <div onClick={() => setCrawl(!crawl)}
                           className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all duration-200 mb-5
                             ${crawl ? 'border-plasma/40 bg-plasma/10' : 'border-white/10 hover:border-white/20'}`}>
                        <div className={`w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 transition-all
                          ${crawl ? 'border-plasma bg-plasma' : 'border-white/20'}`}>
                          {crawl && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>}
                        </div>
                        <div>
                          <p className="text-white text-sm font-medium">Crawl entire website</p>
                          <p className="text-mist/40 text-xs mt-0.5">Scrapes multiple pages for better training data</p>
                        </div>
                      </div>
                      <button onClick={handleTrainFromUrl} disabled={!scrapeUrl.trim() || scrapeLoading} className="btn-primary w-full text-center">
                        {scrapeLoading ? (
                          <span className="flex items-center justify-center gap-2">
                            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            Scraping & training...
                          </span>
                        ) : '🌐 Scrape & Train Chatbot'}
                      </button>
                    </>
                  )}
                </div>
              )}

              {/* Chatbot Link */}
              {business?.trained && (
                <div className="glass-card p-6 animate-fade-in">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse-slow" />
                    <h2 className="text-lg font-bold text-white">Your Chatbot is Live</h2>
                  </div>
                  <p className="text-mist/40 text-sm mb-5">Share this link with your customers</p>
                  <div className="flex gap-3">
                    <div className="flex-1 bg-void border border-white/10 rounded-xl px-4 py-3 font-mono text-sm text-neon truncate">
                      {chatbotUrl}
                    </div>
                    <button onClick={() => { navigator.clipboard.writeText(chatbotUrl); setMessage('Link copied!'); setTimeout(() => setMessage(null), 2000) }}
                            className="btn-ghost px-4 py-3">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <Link to={`/chatbot/${business.business_id}`} target="_blank" className="btn-primary px-4 py-3">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </Link>
                  </div>
                </div>
              )}
            </>
          )}

          {/* ── ANALYTICS ─────────────────────────────────────────────────── */}
          {activeNav === 'analytics' && (
            <>
              <div className="mb-10">
                <h1 className="text-3xl font-bold text-white">Analytics</h1>
                <p className="text-mist/50 mt-1">Track your chatbot's performance</p>
              </div>

              {analyticsLoading ? (
                <div className="flex items-center justify-center py-24">
                  <div className="w-8 h-8 border-2 border-plasma border-t-transparent rounded-full animate-spin" />
                </div>
              ) : analytics ? (
                <>
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <StatCard icon="💬" label="Total Chats" value={analytics.total_chats} sub="All time" />
                    <StatCard icon="📅" label="Today" value={analytics.today_chats} sub="Last 24h" />
                    <StatCard
                      icon="⚠️"
                      label="Unanswered"
                      value={analytics.unanswered_count}
                      sub="Needs attention"
                      accent={analytics.unanswered_count > 0 ? 'red' : undefined}
                    />
                  </div>

                  {analytics.unanswered_count > 0 && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-red-400 text-lg">⚠️</span>
                        <div>
                          <p className="text-red-400 text-sm font-medium">
                            {analytics.unanswered_count} unanswered question{analytics.unanswered_count !== 1 ? 's' : ''} need your attention
                          </p>
                          <p className="text-red-400/60 text-xs mt-0.5">Provide answers to improve your chatbot</p>
                        </div>
                      </div>
                      <button onClick={() => setActiveNav('unanswered')} className="text-red-400 text-xs font-medium hover:text-red-300 transition-colors whitespace-nowrap ml-4">
                        Answer now →
                      </button>
                    </div>
                  )}

                  <div className="glass-card p-6">
                    <h2 className="text-lg font-bold text-white mb-1">Weekly Activity</h2>
                    <p className="text-mist/40 text-sm mb-6">Conversations over the last 7 days</p>
                    <BarChart data={analytics.weekly_chats || []} />
                  </div>
                </>
              ) : (
                <div className="glass-card p-8 text-center">
                  <p className="text-mist/50 text-sm">Failed to load analytics</p>
                </div>
              )}
            </>
          )}

          {/* ── UNANSWERED QUESTIONS ──────────────────────────────────────── */}
          {activeNav === 'unanswered' && (
            <>
              <div className="mb-8 flex items-start justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-white">Unanswered Questions</h1>
                  <p className="text-mist/50 mt-1">Provide answers to train your bot automatically</p>
                </div>
                <button onClick={fetchUnanswered} className="btn-ghost text-sm px-4 py-2 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>

              {/* How it works banner */}
              <div className="bg-plasma/10 border border-plasma/20 rounded-xl p-4 mb-6 flex items-start gap-3">
                <span className="text-neon text-lg mt-0.5">💡</span>
                <div>
                  <p className="text-neon text-sm font-medium">How this works</p>
                  <p className="text-mist/50 text-xs mt-1 leading-relaxed">
                    When your chatbot can't answer a question, it's logged here. Click <strong className="text-mist/70">"Answer"</strong> to provide a response — it will be instantly indexed into your chatbot's knowledge base so future customers get the right answer automatically.
                  </p>
                </div>
              </div>

              {unansweredLoading ? (
                <div className="flex items-center justify-center py-24">
                  <div className="w-8 h-8 border-2 border-plasma border-t-transparent rounded-full animate-spin" />
                </div>
              ) : unanswered.length === 0 ? (
                <div className="glass-card p-12 text-center">
                  <div className="text-5xl mb-4">✅</div>
                  <h3 className="text-white font-bold mb-2">All questions answered!</h3>
                  <p className="text-mist/40 text-sm">Your chatbot is handling all customer queries successfully.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-mist/30 text-xs mb-4">{unanswered.length} unique unanswered question{unanswered.length !== 1 ? 's' : ''}</p>
                  {unanswered.map((item, i) => (
                    <div key={i} className="glass-card p-5 border-red-500/10 hover:border-red-500/20 transition-all duration-200">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3 flex-1 min-w-0">
                          <div className="w-8 h-8 bg-red-500/15 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                            <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-white text-sm font-medium">{item.question}</p>
                            {item.count > 1 && (
                              <p className="text-mist/40 text-xs mt-1">
                                Asked {item.count} time{item.count !== 1 ? 's' : ''} in {item.variants?.length} variation{item.variants?.length !== 1 ? 's' : ''}
                              </p>
                            )}
                            {/* Show variants if multiple */}
                            {item.variants?.length > 1 && (
                              <div className="mt-2 flex flex-wrap gap-1.5">
                                {item.variants.slice(0, 4).map((v, vi) => (
                                  <span key={vi} className="bg-void border border-white/5 rounded-lg px-2 py-0.5 text-mist/40 text-xs">
                                    "{v}"
                                  </span>
                                ))}
                                {item.variants.length > 4 && (
                                  <span className="text-mist/30 text-xs self-center">+{item.variants.length - 4} more</span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => setAnswerModal(item)}
                          className="shrink-0 bg-plasma/20 hover:bg-plasma/30 border border-plasma/30 text-neon text-xs
                                     font-semibold px-4 py-2 rounded-lg transition-all duration-200 flex items-center gap-1.5"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                          Answer
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* ── CHAT HISTORY ──────────────────────────────────────────────── */}
          {activeNav === 'history' && (
            <>
              <div className="mb-8 flex items-start justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-white">Chat History</h1>
                  <p className="text-mist/50 mt-1">All conversations with your AI chatbot</p>
                </div>
                <button onClick={fetchChatHistory} className="btn-ghost text-sm px-4 py-2 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>

              {/* Search + Filter */}
              <div className="flex gap-3 mb-6">
                <div className="relative flex-1">
                  <svg className="w-4 h-4 text-mist/30 absolute left-4 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input type="text" placeholder="Search conversations..."
                         value={historySearch} onChange={e => setHistorySearch(e.target.value)}
                         className="input-field pl-10" />
                </div>
                <div className="flex gap-1 bg-void border border-white/5 rounded-xl p-1">
                  {[['all', 'All'], ['answered', 'Answered'], ['unanswered', 'Unanswered']].map(([val, label]) => (
                    <button key={val} onClick={() => setHistoryFilter(val)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                              ${historyFilter === val ? 'bg-plasma text-white' : 'text-mist/50 hover:text-white'}`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {historyLoading ? (
                <div className="flex items-center justify-center py-24">
                  <div className="w-8 h-8 border-2 border-plasma border-t-transparent rounded-full animate-spin" />
                </div>
              ) : filteredHistory.length === 0 ? (
                <div className="glass-card p-12 text-center">
                  <div className="text-5xl mb-4">{historySearch ? '🔍' : '💬'}</div>
                  <h3 className="text-white font-bold mb-2">{historySearch ? 'No results found' : 'No conversations yet'}</h3>
                  <p className="text-mist/40 text-sm">
                    {historySearch ? 'Try a different search term.' : 'Conversations will appear here once customers start chatting.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-mist/30 text-xs mb-4">{filteredHistory.length} conversation{filteredHistory.length !== 1 ? 's' : ''}</p>
                  {filteredHistory.map((chat) => (
                    <div key={chat.id}
                         className={`glass-card overflow-hidden transition-all duration-200 cursor-pointer
                           ${chat.unanswered ? 'border-red-500/10' : ''}
                           ${expandedChat === chat.id ? 'border-plasma/20' : 'hover:border-white/10'}`}
                         onClick={() => setExpandedChat(expandedChat === chat.id ? null : chat.id)}>
                      <div className="p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3 flex-1 min-w-0">
                            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
                              ${chat.unanswered ? 'bg-red-500/20' : 'bg-plasma/20'}`}>
                              <svg className={`w-3.5 h-3.5 ${chat.unanswered ? 'text-red-400' : 'text-neon'}`}
                                   fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-white text-sm font-medium truncate">{chat.user_message}</p>
                                {chat.unanswered && (
                                  <span className="shrink-0 bg-red-500/15 border border-red-500/20 text-red-400 text-xs px-2 py-0.5 rounded-full">
                                    unanswered
                                  </span>
                                )}
                              </div>
                              {expandedChat !== chat.id && (
                                <p className="text-mist/40 text-xs mt-0.5 truncate">{chat.bot_response}</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-mist/30 text-xs">{formatDate(chat.created_at)}</span>
                            <svg className={`w-4 h-4 text-mist/30 transition-transform duration-200 ${expandedChat === chat.id ? 'rotate-180' : ''}`}
                                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                        </div>
                      </div>

                      {expandedChat === chat.id && (
                        <div className="border-t border-white/5 p-4 space-y-3 animate-fade-in">
                          <div className="flex items-start gap-3">
                            <div className="w-7 h-7 bg-plasma/20 rounded-full flex items-center justify-center shrink-0">
                              <svg className="w-3.5 h-3.5 text-neon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                            </div>
                            <div className="bg-void/60 rounded-xl rounded-tl-md px-4 py-2.5 flex-1">
                              <p className="text-mist text-sm">{chat.user_message}</p>
                            </div>
                          </div>
                          <div className="flex items-start gap-3">
                            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0
                              ${chat.unanswered ? 'bg-red-500/20' : 'bg-green-500/20'}`}>
                              <svg className={`w-3.5 h-3.5 ${chat.unanswered ? 'text-red-400' : 'text-green-400'}`}
                                   fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                              </svg>
                            </div>
                            <div className={`rounded-xl rounded-tl-md px-4 py-2.5 flex-1 border
                              ${chat.unanswered
                                ? 'bg-red-500/5 border-red-500/20'
                                : 'bg-plasma/10 border-plasma/20'}`}>
                              <p className="text-mist text-sm">{chat.bot_response}</p>
                            </div>
                          </div>
                          {chat.unanswered && (
                            <div className="flex justify-end">
                              <button
                                onClick={(e) => { e.stopPropagation(); setAnswerModal({ question: chat.user_message, count: 1, variants: [chat.user_message] }) }}
                                className="text-neon text-xs font-medium hover:text-white transition-colors flex items-center gap-1.5"
                              >
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                                Provide an answer
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* ── TOP QUESTIONS (FAQ) ───────────────────────────────────────── */}
          {activeNav === 'faq' && (
            <>
              <div className="mb-10">
                <h1 className="text-3xl font-bold text-white">Top Questions</h1>
                <p className="text-mist/50 mt-1">Most frequently asked by your customers (grouped by meaning)</p>
              </div>

              {faqLoading ? (
                <div className="flex items-center justify-center py-24">
                  <div className="w-8 h-8 border-2 border-plasma border-t-transparent rounded-full animate-spin" />
                </div>
              ) : faq.length === 0 ? (
                <div className="glass-card p-12 text-center">
                  <div className="text-5xl mb-4">❓</div>
                  <h3 className="text-white font-bold mb-2">No questions yet</h3>
                  <p className="text-mist/40 text-sm">As customers chat with your bot, their most common questions will appear here.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-mist/30 text-xs mb-4">Top {faq.length} unique questions (similar phrasings are merged)</p>
                  {faq.map((item, i) => {
                    const maxCount = faq[0]?.count || 1
                    const pct = Math.round((item.count / maxCount) * 100)
                    const isExpanded = expandedFaq === i
                    return (
                      <div key={i}
                           className="glass-card overflow-hidden cursor-pointer hover:border-white/10 transition-all duration-200"
                           onClick={() => setExpandedFaq(isExpanded ? null : i)}>
                        <div className="p-5">
                          <div className="flex items-start justify-between gap-4 mb-3">
                            <div className="flex items-start gap-3">
                              <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0
                                ${i === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                                  i === 1 ? 'bg-slate-400/20 text-slate-300' :
                                  i === 2 ? 'bg-orange-500/20 text-orange-400' :
                                  'bg-void text-mist/40'}`}>
                                {i + 1}
                              </div>
                              <div>
                                <p className="text-white text-sm font-medium leading-relaxed">{item.question}</p>
                                {item.variants?.length > 1 && (
                                  <p className="text-mist/30 text-xs mt-0.5">
                                    {item.variants.length} similar phrasings • click to see
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <div className="flex items-center gap-1.5 bg-plasma/10 border border-plasma/20 rounded-lg px-2.5 py-1">
                                <span className="text-neon text-sm font-bold">{item.count}</span>
                                <span className="text-mist/40 text-xs">ask{item.count !== 1 ? 's' : ''}</span>
                              </div>
                              {item.variants?.length > 1 && (
                                <svg className={`w-4 h-4 text-mist/30 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                                     fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                              )}
                            </div>
                          </div>
                          <div className="w-full bg-white/5 rounded-full h-1.5">
                            <div className="bg-gradient-to-r from-plasma to-neon h-1.5 rounded-full transition-all duration-700"
                                 style={{ width: `${pct}%` }} />
                          </div>
                        </div>

                        {/* Expanded: show all variant phrasings */}
                        {isExpanded && item.variants?.length > 1 && (
                          <div className="border-t border-white/5 px-5 pb-4 animate-fade-in">
                            <p className="text-mist/30 text-xs uppercase tracking-wider mb-2 pt-3">All phrasings</p>
                            <div className="space-y-1.5">
                              {item.variants.map((v, vi) => (
                                <div key={vi} className="flex items-center gap-2">
                                  <span className="w-1 h-1 bg-mist/20 rounded-full shrink-0" />
                                  <p className="text-mist/60 text-xs">"{v}"</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}

        </div>
      </main>
    </div>
  )
}