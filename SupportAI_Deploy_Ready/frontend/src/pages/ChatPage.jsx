import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import api from '../utils/api'

// ─── Typing Indicator ────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          style={{ animationDelay: `${i * 0.18}s` }}
          className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
        />
      ))}
    </div>
  )
}

// ─── Speaker Button ──────────────────────────────────────────────────────────
function SpeakerButton({ id, speakingId, content, onSpeak }) {
  const isPlaying = speakingId === id
  return (
    <button
      onClick={() => onSpeak(id, content)}
      title={isPlaying ? 'Stop' : 'Read aloud'}
      className={`p-1.5 rounded-md transition-all ${
        isPlaying
          ? 'text-white bg-blue-500/20 border border-blue-500/40'
          : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
      }`}
    >
      {isPlaying ? (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
          <rect x="6" y="5" width="4" height="14" rx="1"/>
          <rect x="14" y="5" width="4" height="14" rx="1"/>
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
        </svg>
      )}
    </button>
  )
}

// ─── Copy Button ─────────────────────────────────────────────────────────────
function CopyButton({ content }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={handleCopy}
      title="Copy"
      className="p-1.5 rounded-md text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-all"
    >
      {copied ? (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4 text-green-400">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
        </svg>
      )}
    </button>
  )
}

// ─── Mic Button ──────────────────────────────────────────────────────────────
function MicButton({ isListening, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={isListening ? 'Stop listening' : 'Voice input'}
      className={`p-2 rounded-lg transition-all ${
        isListening
          ? 'text-white bg-red-500 animate-pulse'
          : 'text-gray-400 hover:text-white hover:bg-white/10'
      } disabled:opacity-30 disabled:cursor-not-allowed`}
    >
      {isListening ? (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
          <line x1="1" y1="1" x2="23" y2="23"/>
          <path d="M9 9v3a3 3 0 005.12 2.12M15 9.34V4a3 3 0 00-5.94-.6"/>
          <path d="M17 16.95A7 7 0 015 12v-2m14 0v2a7 7 0 01-.11 1.23"/>
          <line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
        </svg>
      )}
    </button>
  )
}

// ─── Bot Icon ─────────────────────────────────────────────────────────────────
function BotIcon() {
  return (
    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center flex-shrink-0 mt-0.5">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-white">
        <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7H3a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zM7.25 14a.75.75 0 100 1.5.75.75 0 000-1.5zm9.5 0a.75.75 0 100 1.5.75.75 0 000-1.5zM4 19h16v1a1 1 0 01-1 1H5a1 1 0 01-1-1v-1z"/>
      </svg>
    </div>
  )
}

// ─── Message renderer with basic markdown ────────────────────────────────────
function MessageContent({ content }) {
  // Process basic markdown: **bold**, `code`, newlines
  const parts = content.split(/(\*\*.*?\*\*|`[^`]+`)/g)
  return (
    <div className="text-sm leading-7 text-gray-100 whitespace-pre-wrap break-words">
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return <code key={i} className="bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono text-blue-300">{part.slice(1, -1)}</code>
        }
        return <span key={i}>{part}</span>
      })}
    </div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────
export default function ChatPage() {
  const { businessId } = useParams()
  const [business, setBusiness] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [initLoading, setInitLoading] = useState(true)
  const [speakingId, setSpeakingId] = useState(null)
  const [isListening, setIsListening] = useState(false)
  const [sttSupported, setSttSupported] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const bottomRef = useRef()
  const inputRef = useRef()
  const recognitionRef = useRef(null)
  const msgCounter = useRef(0)

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    setSttSupported(!!SR)
  }, [])

  useEffect(() => { window.speechSynthesis.getVoices() }, [])

  useEffect(() => {
    const fetchBusiness = async () => {
      try {
        const { data } = await api.get(`/business/public/${businessId}`)
        setBusiness(data)
        setMessages([{
          id: `msg_${++msgCounter.current}`,
          role: 'bot',
          content: `Hello! I'm the AI assistant for **${data.company_name}**. How can I help you today?`,
          time: new Date()
        }])
      } catch (e) {
        setBusiness(null)
      } finally {
        setInitLoading(false)
      }
    }
    fetchBusiness()
  }, [businessId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // ── TTS ───────────────────────────────────────────────────────────────────
  const handleSpeak = (id, content) => {
    if (speakingId === id) {
      window.speechSynthesis.cancel()
      setSpeakingId(null)
      return
    }
    window.speechSynthesis.cancel()
    const plainText = content.replace(/\*\*(.*?)\*\*/g, '$1').replace(/[*_`#]/g, '').trim()
    const utterance = new SpeechSynthesisUtterance(plainText)
    utterance.lang = 'en-IN'
    const voices = window.speechSynthesis.getVoices()
    const voice = voices.find(v => v.lang === 'en-IN') || voices.find(v => v.lang === 'en-US') || voices.find(v => v.lang.startsWith('en')) || null
    if (voice) utterance.voice = voice
    utterance.onstart = () => setSpeakingId(id)
    utterance.onend = () => setSpeakingId(null)
    utterance.onerror = () => setSpeakingId(null)
    window.speechSynthesis.speak(utterance)
  }

  // ── STT ───────────────────────────────────────────────────────────────────
  const startListening = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    window.speechSynthesis.cancel()
    setSpeakingId(null)
    const recognition = new SR()
    recognition.lang = 'en-IN'
    recognition.continuous = false
    recognition.interimResults = true
    recognition.onstart = () => setIsListening(true)
    recognition.onresult = (e) => {
      const transcript = Array.from(e.results).map(r => r[0].transcript).join('')
      setInput(transcript)
    }
    recognition.onend = () => {
      setIsListening(false)
      recognitionRef.current = null
      setTimeout(() => inputRef.current?.focus(), 100)
    }
    recognition.onerror = () => {
      setIsListening(false)
      recognitionRef.current = null
    }
    recognitionRef.current = recognition
    recognition.start()
  }

  const stopListening = () => {
    if (recognitionRef.current) { recognitionRef.current.stop(); recognitionRef.current = null }
    setIsListening(false)
  }

  // ── Send ──────────────────────────────────────────────────────────────────
  const handleSend = async () => {
    if (!input.trim() || loading) return
    stopListening()
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { id: `msg_${++msgCounter.current}`, role: 'user', content: userMsg, time: new Date() }])
    setLoading(true)
    try {
      const { data } = await api.post('/chat/message', { message: userMsg, business_id: businessId })
      setMessages(prev => [...prev, { id: `msg_${++msgCounter.current}`, role: 'bot', content: data.response, time: new Date() }])
    } catch {
      setMessages(prev => [...prev, { id: `msg_${++msgCounter.current}`, role: 'bot', content: 'Sorry, I encountered an error. Please try again.', time: new Date() }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const formatTime = (date) => date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  // ─── Loading ──────────────────────────────────────────────────────────────
  if (initLoading) {
    return (
      <div className="h-screen bg-[#212121] flex items-center justify-center">
        <div className="flex gap-2">
          {[0,1,2].map(i => (
            <div key={i} style={{ animationDelay: `${i*0.15}s` }}
              className="w-2 h-2 rounded-full bg-gray-500 animate-bounce"/>
          ))}
        </div>
      </div>
    )
  }

  if (!business) {
    return (
      <div className="h-screen bg-[#212121] flex flex-col items-center justify-center gap-4 text-gray-400">
        <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center text-3xl">🤖</div>
        <h2 className="text-white text-xl font-semibold">Chatbot Not Found</h2>
        <p className="text-sm">This chatbot link may be invalid or expired.</p>
      </div>
    )
  }

  // ─── UI ───────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen bg-[#212121] text-white font-sans overflow-hidden">

      {/* ── Main ──────────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <header className="h-14 flex items-center px-4 gap-3 border-b border-white/5 flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"/>
            <span className="text-sm font-medium text-gray-200">{business.company_name} AI</span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.length === 1 && (
              <div className="text-center py-8">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center mx-auto mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-white">
                    <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7H3a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2z"/>
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold text-white mb-1">{business.company_name}</h2>
                <p className="text-gray-400 text-sm">AI Support Assistant</p>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 group ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'bot' && <BotIcon />}

                <div className={`flex flex-col gap-1 max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {msg.role === 'user' ? (
                    <div className="bg-[#2f2f2f] rounded-2xl rounded-tr-sm px-4 py-2.5">
                      <p className="text-sm text-gray-100 leading-6 whitespace-pre-wrap break-words">{msg.content}</p>
                    </div>
                  ) : (
                    <div className="py-1">
                      <MessageContent content={msg.content} />
                    </div>
                  )}

                  {/* Action row */}
                  <div className={`flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <span className="text-xs text-gray-600 px-1">{formatTime(msg.time)}</span>
                    {msg.role === 'bot' && (
                      <>
                        <CopyButton content={msg.content} />
                        <SpeakerButton id={msg.id} speakingId={speakingId} content={msg.content} onSpeak={handleSpeak} />
                      </>
                    )}
                  </div>
                </div>

                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-[#3a3a3a] border border-white/10 flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-semibold text-gray-300">U</div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-3">
                <BotIcon />
                <div className="py-1"><TypingDots /></div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input area */}
        <div className="flex-shrink-0 px-4 pb-4 pt-2">
          <div className="max-w-3xl mx-auto">
            {isListening && (
              <div className="flex items-center gap-2 mb-2 px-1 text-xs text-red-400">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"/>
                Listening... speak now
              </div>
            )}

            <div className="relative flex items-end gap-2 bg-[#2f2f2f] border border-white/10 rounded-2xl px-3 py-2 focus-within:border-white/20 transition-colors shadow-lg">
              {sttSupported && (
                <MicButton isListening={isListening} onClick={isListening ? stopListening : startListening} disabled={loading} />
              )}

              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={e => {
                  setInput(e.target.value)
                  // auto resize
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
                }}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder={isListening ? 'Listening...' : 'Message ' + business.company_name + ' AI...'}
                disabled={loading}
                className="flex-1 bg-transparent text-sm text-gray-100 placeholder-gray-500 resize-none outline-none py-1.5 max-h-48 overflow-y-auto"
                style={{ lineHeight: '1.5rem' }}
              />

              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="p-1.5 rounded-lg bg-white text-black hover:bg-gray-200 disabled:opacity-20 disabled:cursor-not-allowed transition-all flex-shrink-0 self-end mb-0.5"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                  <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                </svg>
              </button>
            </div>

            <p className="text-center text-xs text-gray-600 mt-2">
              {business.company_name} AI can make mistakes. Consider checking important information.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}