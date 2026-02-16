import { useState, useRef, useEffect } from 'react'
import { 
  Send, 
  Image, 
  Play, 
  Square, 
  Bot, 
  User, 
  Loader2,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Settings,
  Clock
} from 'lucide-react'
import { useMutation, useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  type?: 'command' | 'chat' | 'analysis'
  data?: any
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `👋 Welcome to AI Trading Agent Pro!

I'm your intelligent trading assistant. I can help you with:

📊 **Market Analysis** - Technical & fundamental analysis
🤖 **24/7 Monitoring** - Automated market surveillance  
📈 **Signal Generation** - High-confidence trade signals
📰 **News & Calendar** - Economic events & sentiment
💬 **Chart Analysis** - Upload images for AI analysis

**Quick Commands:**
• "start monitoring" - Begin 24/7 surveillance
• "analyze BTCUSDT" - Analyze specific symbol
• "status" - Check system status
• "stop" - Stop monitoring

How can I assist you today?`,
      timestamp: new Date(),
      type: 'chat'
    }
  ])
  const [input, setInput] = useState('')
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await axios.post(`${API_URL}/chat/message`, {
        message,
        symbol: selectedSymbol
      })
      return response.data
    },
    onSuccess: (data) => {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        type: data.type,
        data: data.data
      }
      setMessages(prev => [...prev, assistantMessage])
    },
    onError: (error: any) => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date(),
        type: 'chat'
      }
      setMessages(prev => [...prev, errorMessage])
    }
  })

  // Start/Stop monitoring mutation
  const toggleMonitoringMutation = useMutation({
    mutationFn: async (action: 'start' | 'stop') => {
      const response = await axios.post(`${API_URL}/agent/${action}`, {
        pairs: [selectedSymbol]
      })
      return response.data
    },
    onSuccess: (data, action) => {
      setIsMonitoring(action === 'start')
      const message: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        type: 'command',
        data: data.data
      }
      setMessages(prev => [...prev, message])
    }
  })

  // Image analysis mutation
  const analyzeImageMutation = useMutation({
    mutationFn: async () => {
      if (!selectedImage) return
      
      const formData = new FormData()
      formData.append('file', selectedImage)
      formData.append('symbol', selectedSymbol)
      formData.append('timeframe', '1h')
      
      const response = await axios.post(`${API_URL}/chat/analyze-image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return response.data
    },
    onSuccess: (data) => {
      const message: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `📊 Chart Analysis for ${selectedSymbol}\n\n${data.analysis}`,
        timestamp: new Date(),
        type: 'analysis',
        data: data
      }
      setMessages(prev => [...prev, message])
      setSelectedImage(null)
    }
  })

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    sendMessageMutation.mutate(input)
    setInput('')
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
    }
  }

  const handleAnalyzeImage = () => {
    if (selectedImage) {
      analyzeImageMutation.mutate()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-card/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
            <Bot className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-semibold">AI Trading Agent</h1>
            <p className="text-xs text-muted-foreground">
              {isMonitoring ? (
                <span className="flex items-center gap-1 text-bull">
                  <span className="w-2 h-2 rounded-full bg-bull animate-pulse" />
                  Monitoring Active
                </span>
              ) : (
                <span className="flex items-center gap-1 text-muted-foreground">
                  <span className="w-2 h-2 rounded-full bg-neutral" />
                  Standby
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Symbol Selector */}
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="px-3 py-2 bg-accent rounded-lg text-sm border border-border"
          >
            {['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'EURUSD', 'GBPUSD', 'XAUUSD'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* Monitoring Toggle */}
          <button
            onClick={() => toggleMonitoringMutation.mutate(isMonitoring ? 'stop' : 'start')}
            disabled={toggleMonitoringMutation.isPending}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              isMonitoring
                ? 'bg-bear/20 text-bear hover:bg-bear/30'
                : 'bg-bull/20 text-bull hover:bg-bull/30'
            }`}
          >
            {toggleMonitoringMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : isMonitoring ? (
              <>
                <Square className="w-4 h-4" />
                Stop
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Start
              </>
            )}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              message.role === 'user' ? 'bg-accent' : 'bg-primary'
            }`}>
              {message.role === 'user' ? (
                <User className="w-4 h-4" />
              ) : (
                <Bot className="w-4 h-4" />
              )}
            </div>
            
            <div className={`max-w-[80%] rounded-lg p-3 ${
              message.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-accent'
            }`}>
              <div className="whitespace-pre-wrap text-sm">{message.content}</div>
              
              {message.data && (
                <div className="mt-2 pt-2 border-t border-border/50">
                  {message.type === 'command' && message.data?.pairs && (
                    <div className="text-xs text-muted-foreground">
                      Monitoring: {message.data.pairs.join(', ')}
                    </div>
                  )}
                </div>
              )}
              
              <div className={`text-xs mt-1 ${
                message.role === 'user' ? 'text-primary-foreground/60' : 'text-muted-foreground'
              }`}>
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {sendMessageMutation.isPending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-accent rounded-lg p-3">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Image Preview */}
      {selectedImage && (
        <div className="px-4 py-2 border-t border-border bg-accent/30">
          <div className="flex items-center gap-3">
            <div className="relative">
              <img
                src={URL.createObjectURL(selectedImage)}
                alt="Selected"
                className="w-16 h-16 object-cover rounded-lg"
              />
              <button
                onClick={() => setSelectedImage(null)}
                className="absolute -top-1 -right-1 w-5 h-5 bg-bear rounded-full flex items-center justify-center text-white text-xs"
              >
                ×
              </button>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">{selectedImage.name}</p>
              <p className="text-xs text-muted-foreground">
                {(selectedImage.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={handleAnalyzeImage}
              disabled={analyzeImageMutation.isPending}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {analyzeImageMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Analyze Chart'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-border bg-card/50">
        <div className="flex gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-3 bg-accent rounded-lg hover:bg-accent/80 transition-colors"
            title="Upload chart image"
          >
            <Image className="w-5 h-5" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
          
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message or command..."
              className="w-full px-4 py-3 bg-accent rounded-lg resize-none border border-transparent focus:border-primary outline-none"
              rows={1}
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>
          
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMessageMutation.isPending}
            className="p-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {sendMessageMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        
        <p className="text-xs text-muted-foreground mt-2">
          Try: "start monitoring", "analyze BTCUSDT", "status", "stop"
        </p>
      </div>
    </div>
  )
}
