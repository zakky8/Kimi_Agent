import { useState, useRef, useEffect } from 'react'
import { 
  Send, 
  Plus, 
  Trash2, 
  Image as ImageIcon, 
  MoreVertical,
  Bot,
  User,
  Loader2,
  X,
  BarChart3,
  Clock
} from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface ChatMessage {
  message_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: any
}

interface ChatSession {
  session_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export function Chat() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSession, setActiveSession] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [showImageUpload, setShowImageUpload] = useState(false)
  const [uploadedImage, setUploadedImage] = useState<File | null>(null)
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [timeframe, setTimeframe] = useState('1h')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    if (activeSession) {
      loadMessages(activeSession)
    }
  }, [activeSession])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/chat/sessions`)
      setSessions(response.data.sessions || [])
    } catch (error) {
      console.error('Error loading sessions:', error)
    }
  }

  const loadMessages = async (sessionId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/chat/session/${sessionId}/messages`)
      setMessages(response.data.messages || [])
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }

  const createSession = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/chat/session/create`)
      const newSession = response.data
      setSessions([newSession, ...sessions])
      setActiveSession(newSession.session_id)
      setMessages([])
    } catch (error) {
      console.error('Error creating session:', error)
    }
  }

  const deleteSession = async (sessionId: string) => {
    try {
      await axios.delete(`${API_BASE_URL}/chat/session/${sessionId}`)
      setSessions(sessions.filter(s => s.session_id !== sessionId))
      if (activeSession === sessionId) {
        setActiveSession(null)
        setMessages([])
      }
    } catch (error) {
      console.error('Error deleting session:', error)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() && !uploadedImage) return
    if (!activeSession) {
      await createSession()
      return
    }

    setLoading(true)
    try {
      if (uploadedImage) {
        // Send image for analysis
        const formData = new FormData()
        formData.append('session_id', activeSession)
        formData.append('file', uploadedImage)
        formData.append('symbol', symbol)
        formData.append('timeframe', timeframe)
        if (input.trim()) {
          formData.append('question', input)
        }

        const response = await axios.post(`${API_BASE_URL}/chat/image`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        // Add user message
        const userMessage: ChatMessage = {
          message_id: Date.now().toString(),
          role: 'user',
          content: input || `[Chart Analysis: ${symbol} ${timeframe}]`,
          timestamp: new Date().toISOString()
        }

        // Add assistant response
        const assistantMessage: ChatMessage = {
          message_id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.analysis,
          timestamp: new Date().toISOString(),
          metadata: {
            type: 'chart_analysis',
            symbol: response.data.symbol,
            timeframe: response.data.timeframe
          }
        }

        setMessages(prev => [...prev, userMessage, assistantMessage])
        setUploadedImage(null)
        setShowImageUpload(false)
      } else {
        // Send text message
        const response = await axios.post(`${API_BASE_URL}/chat/message`, {
          session_id: activeSession,
          content: input
        })

        // Reload messages
        await loadMessages(activeSession)
      }

      setInput('')
      loadSessions() // Update session list
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedImage(file)
      setShowImageUpload(true)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-4">
      {/* Sidebar - Sessions */}
      <div className="w-64 glass rounded-xl flex flex-col">
        <div className="p-4 border-b border-border">
          <button
            onClick={createSession}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>
        
        <div className="flex-1 overflow-auto p-2 space-y-1">
          {sessions.map(session => (
            <div
              key={session.session_id}
              onClick={() => setActiveSession(session.session_id)}
              className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                activeSession === session.session_id
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-accent'
              }`}
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{session.title}</p>
                <p className={`text-xs ${activeSession === session.session_id ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                  {new Date(session.updated_at).toLocaleDateString()} • {session.message_count} messages
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  deleteSession(session.session_id)
                }}
                className={`opacity-0 group-hover:opacity-100 p-1 rounded transition-opacity ${
                  activeSession === session.session_id ? 'hover:bg-primary-foreground/20' : 'hover:bg-accent'
                }`}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 glass rounded-xl flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot className="w-6 h-6 text-primary" />
            <div>
              <h2 className="font-semibold">AI Trading Assistant</h2>
              <p className="text-xs text-muted-foreground">
                {activeSession ? 'Chat active' : 'Start a new conversation'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowImageUpload(!showImageUpload)}
              className={`p-2 rounded-lg transition-colors ${showImageUpload ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'}`}
            >
              <ImageIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Image Upload Panel */}
        {showImageUpload && (
          <div className="p-4 border-b border-border bg-accent/30">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="block text-sm text-muted-foreground mb-1">Symbol</label>
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="w-full px-3 py-2 bg-background rounded border border-border outline-none focus:border-primary"
                >
                  <option value="BTCUSDT">BTCUSDT</option>
                  <option value="ETHUSDT">ETHUSDT</option>
                  <option value="SOLUSDT">SOLUSDT</option>
                  <option value="EURUSD">EURUSD</option>
                  <option value="GBPUSD">GBPUSD</option>
                  <option value="XAUUSD">XAUUSD</option>
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm text-muted-foreground mb-1">Timeframe</label>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="w-full px-3 py-2 bg-background rounded border border-border outline-none focus:border-primary"
                >
                  <option value="1m">1m</option>
                  <option value="5m">5m</option>
                  <option value="15m">15m</option>
                  <option value="1h">1h</option>
                  <option value="4h">4h</option>
                  <option value="1d">1d</option>
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm text-muted-foreground mb-1">Upload Chart</label>
                <label className="flex items-center justify-center gap-2 px-4 py-2 bg-background border border-dashed border-border rounded-lg cursor-pointer hover:border-primary transition-colors">
                  <ImageIcon className="w-4 h-4" />
                  <span className="text-sm">{uploadedImage ? uploadedImage.name : 'Choose file'}</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                </label>
              </div>
              {uploadedImage && (
                <button
                  onClick={() => setUploadedImage(null)}
                  className="p-2 text-bear hover:bg-bear/10 rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {!activeSession ? (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
              <Bot className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">Start a conversation</p>
              <p className="text-sm">Ask about trading signals, market analysis, or upload a chart</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
              <BarChart3 className="w-12 h-12 mb-4 opacity-50" />
              <p className="text-sm">Send a message to start the conversation</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.message_id}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-primary-foreground" />
                  </div>
                )}
                <div
                  className={`max-w-[70%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-accent'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.metadata?.type === 'chart_analysis' && (
                    <div className="mt-2 text-xs opacity-70 flex items-center gap-1">
                      <BarChart3 className="w-3 h-3" />
                      {message.metadata.symbol} {message.metadata.timeframe}
                    </div>
                  )}
                  <p className={`text-xs mt-1 ${message.role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-border">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={uploadedImage ? "Ask a question about the chart..." : "Ask about trading signals, market analysis..."}
              className="flex-1 px-4 py-3 bg-accent rounded-lg border border-border outline-none focus:border-primary resize-none"
              rows={2}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || (!input.trim() && !uploadedImage)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}
