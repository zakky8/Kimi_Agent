import { useState, useEffect } from 'react'
import { 
  Settings2, 
  Bell, 
  Shield, 
  Database, 
  Key, 
  Save,
  Check,
  AlertTriangle,
  Brain,
  LineChart,
  MessageSquare,
  Newspaper,
  Monitor,
  RefreshCw,
  ExternalLink,
  Eye,
  EyeOff,
  Plus,
  Trash2
} from 'lucide-react'
import { useConfig } from '../hooks/useApi'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface SettingsSection {
  id: string
  title: string
  icon: React.ElementType
  description: string
}

const sections: SettingsSection[] = [
  { id: 'ai_providers', title: 'AI Providers', icon: Brain, description: 'Configure AI model providers' },
  { id: 'financial_apis', title: 'Financial APIs', icon: LineChart, description: 'Market data providers' },
  { id: 'social_media', title: 'Social Media & Messaging', icon: MessageSquare, description: 'Social data collection' },
  { id: 'news_rss', title: 'News & RSS', icon: Newspaper, description: 'News aggregation' },
  { id: 'mt5', title: 'MetaTrader 5', icon: Monitor, description: 'Desktop integration' },
  { id: 'risk_management', title: 'Risk Management', icon: Shield, description: 'Trading risk parameters' },
  { id: 'signal_settings', title: 'Signal Settings', icon: Settings2, description: 'Signal generation config' },
]

export function Settings() {
  const { data: config, isLoading, refetch } = useConfig()
  const [activeSection, setActiveSection] = useState('ai_providers')
  const [settings, setSettings] = useState<Record<string, any>>({})
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testingConnection, setTestingConnection] = useState<string | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<Record<string, any>>({})
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})
  const [newRssFeed, setNewRssFeed] = useState('')

  useEffect(() => {
    if (config) {
      setSettings({
        ai_providers: {
          OPENROUTER_API_KEY: '',
          GEMINI_API_KEY: '',
          GROQ_API_KEY: '',
          BASETEN_API_KEY: '',
          DEFAULT_AI_PROVIDER: 'openrouter',
          DEFAULT_AI_MODEL: 'anthropic/claude-3.5-sonnet',
        },
        financial_apis: {
          BINANCE_API_KEY: '',
          BINANCE_API_SECRET: '',
          BINANCE_TESTNET: true,
          ALPHA_VANTAGE_API_KEY: '',
          CRYPTOCOMPARE_API_KEY: '',
          FINNHUB_API_KEY: '',
        },
        social_media: {
          REDDIT_CLIENT_ID: '',
          REDDIT_CLIENT_SECRET: '',
          TELEGRAM_API_ID: '',
          TELEGRAM_API_HASH: '',
          TELEGRAM_BOT_TOKEN: '',
        },
        news_rss: {
          NEWSAPI_KEY: '',
          GNEWS_API_KEY: '',
          RSS_FEEDS: '',
        },
        mt5: {
          MT5_ENABLED: false,
          MT5_ACCOUNT: '',
          MT5_PASSWORD: '',
          MT5_SERVER: '',
          MT5_PATH: '',
        },
        risk_management: {
          PER_TRADE_RISK_PERCENT: 1,
          MAX_DRAWDOWN_PERCENT: 10,
          DAILY_LOSS_LIMIT_PERCENT: 2,
          DEFAULT_RISK_REWARD: 2,
        },
        signal_settings: {
          MIN_CONFIDENCE_THRESHOLD: 0.75,
          CONFLUENCE_FACTORS_REQUIRED: 3,
          DEFAULT_TIMEFRAME: '1h',
          CHART_UPDATE_INTERVAL: 60,
        },
      })
    }
  }, [config])

  const handleSave = async () => {
    setSaving(true)
    try {
      await axios.post(`${API_BASE_URL}/settings/update`, {
        section: activeSection,
        settings: settings[activeSection]
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
      refetch()
    } catch (error) {
      console.error('Error saving settings:', error)
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async (provider: string) => {
    setTestingConnection(provider)
    try {
      const response = await axios.post(`${API_BASE_URL}/settings/test-connection/${provider}`)
      setConnectionStatus({ ...connectionStatus, [provider]: response.data })
    } catch (error) {
      setConnectionStatus({ 
        ...connectionStatus, 
        [provider]: { status: 'error', message: 'Connection failed' }
      })
    } finally {
      setTestingConnection(null)
    }
  }

  const updateSetting = (section: string, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }))
  }

  const togglePasswordVisibility = (key: string) => {
    setShowPasswords(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const addRssFeed = () => {
    if (newRssFeed) {
      const currentFeeds = settings.news_rss?.RSS_FEEDS || ''
      const updatedFeeds = currentFeeds ? `${currentFeeds}\n${newRssFeed}` : newRssFeed
      updateSetting('news_rss', 'RSS_FEEDS', updatedFeeds)
      setNewRssFeed('')
    }
  }

  const renderField = (section: string, key: string, value: any, type: string = 'text') => {
    const isPassword = type === 'password' || key.includes('SECRET') || key.includes('PASSWORD') || key.includes('KEY') || key.includes('HASH') || key.includes('TOKEN')
    const showPassword = showPasswords[key]

    if (type === 'toggle') {
      return (
        <label className="flex items-center justify-between p-3 bg-accent/50 rounded-lg cursor-pointer">
          <span className="text-sm">{key.replace(/_/g, ' ')}</span>
          <input
            type="checkbox"
            checked={value}
            onChange={(e) => updateSetting(section, key, e.target.checked)}
            className="w-5 h-5 rounded border-border"
          />
        </label>
      )
    }

    if (type === 'slider') {
      return (
        <div className="p-3 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">
            {key.replace(/_/g, ' ')}: {value}
            {key.includes('PERCENT') && '%'}
            {key.includes('INTERVAL') && ' sec'}
          </label>
          <input
            type="range"
            min={0.5}
            max={key.includes('CONFIDENCE') ? 0.95 : key.includes('INTERVAL') ? 300 : 20}
            step={key.includes('CONFIDENCE') ? 0.05 : key.includes('INTERVAL') ? 10 : 0.5}
            value={value}
            onChange={(e) => updateSetting(section, key, parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
      )
    }

    if (type === 'select') {
      const options = key === 'DEFAULT_AI_PROVIDER' 
        ? ['openrouter', 'gemini', 'groq', 'baseten']
        : key === 'DEFAULT_TIMEFRAME'
        ? ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        : []
      
      return (
        <div className="p-3 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">{key.replace(/_/g, ' ')}</label>
          <select
            value={value}
            onChange={(e) => updateSetting(section, key, e.target.value)}
            className="w-full px-3 py-2 bg-background rounded border border-border outline-none focus:border-primary"
          >
            {options.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </div>
      )
    }

    if (type === 'textarea') {
      return (
        <div className="p-3 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">{key.replace(/_/g, ' ')}</label>
          <textarea
            value={value}
            onChange={(e) => updateSetting(section, key, e.target.value)}
            placeholder="One URL per line"
            rows={4}
            className="w-full px-3 py-2 bg-background rounded border border-border outline-none focus:border-primary resize-none"
          />
        </div>
      )
    }

    return (
      <div className="p-3 bg-accent/50 rounded-lg">
        <label className="block text-sm text-muted-foreground mb-2">{key.replace(/_/g, ' ')}</label>
        <div className="relative">
          <input
            type={isPassword && !showPassword ? 'password' : 'text'}
            value={value}
            onChange={(e) => updateSetting(section, key, e.target.value)}
            placeholder={isPassword ? 'Enter API key...' : 'Enter value...'}
            className="w-full px-3 py-2 bg-background rounded border border-border outline-none focus:border-primary pr-10"
          />
          {isPassword && (
            <button
              onClick={() => togglePasswordVisibility(key)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>
    )
  }

  const renderSection = () => {
    const sectionSettings = settings[activeSection] || {}

    return (
      <div className="space-y-4">
        {Object.entries(sectionSettings).map(([key, value]) => (
          <div key={key}>
            {renderField(activeSection, key, value, 
              typeof value === 'boolean' ? 'toggle' :
              typeof value === 'number' ? 'slider' :
              key === 'DEFAULT_AI_PROVIDER' || key === 'DEFAULT_TIMEFRAME' ? 'select' :
              key === 'RSS_FEEDS' ? 'textarea' : 'text'
            )}
            {(key.includes('API_KEY') || key.includes('CLIENT_ID') || key === 'BINANCE_API_KEY' || key === 'TELEGRAM_API_ID') && (
              <div className="mt-2 flex items-center gap-2">
                <button
                  onClick={() => testConnection(
                    key === 'BINANCE_API_KEY' ? 'binance' :
                    key === 'OPENROUTER_API_KEY' ? 'openrouter' :
                    key === 'GEMINI_API_KEY' ? 'gemini' :
                    key === 'GROQ_API_KEY' ? 'groq' :
                    key === 'REDDIT_CLIENT_ID' ? 'reddit' :
                    key === 'TELEGRAM_API_ID' ? 'telegram' :
                    key === 'ALPHA_VANTAGE_API_KEY' ? 'alpha_vantage' :
                    'unknown'
                  )}
                  disabled={testingConnection === key || !value}
                  className="text-xs flex items-center gap-1 px-2 py-1 bg-primary/20 text-primary rounded hover:bg-primary/30 disabled:opacity-50"
                >
                  <RefreshCw className={`w-3 h-3 ${testingConnection === key ? 'animate-spin' : ''}`} />
                  Test Connection
                </button>
                {connectionStatus[key] && (
                  <span className={`text-xs ${connectionStatus[key].status === 'success' ? 'text-bull' : 'text-bear'}`}>
                    {connectionStatus[key].status === 'success' ? '✓ Connected' : `✗ ${connectionStatus[key].message}`}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}

        {activeSection === 'news_rss' && (
          <div className="p-3 bg-accent/50 rounded-lg">
            <label className="block text-sm text-muted-foreground mb-2">Add RSS Feed</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={newRssFeed}
                onChange={(e) => setNewRssFeed(e.target.value)}
                placeholder="https://example.com/feed.xml"
                className="flex-1 px-3 py-2 bg-background rounded border border-border outline-none focus:border-primary"
              />
              <button
                onClick={addRssFeed}
                className="px-3 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {activeSection === 'ai_providers' && (
          <div className="p-4 bg-accent/30 rounded-lg border border-primary/30">
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Brain className="w-4 h-4 text-primary" />
              Supported AI Providers
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span>OpenRouter</span>
                <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1">
                  Get API Key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="flex items-center justify-between">
                <span>Google Gemini</span>
                <a href="https://ai.google.dev/" target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1">
                  Get API Key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="flex items-center justify-between">
                <span>Groq</span>
                <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1">
                  Get API Key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="flex items-center justify-between">
                <span>Baseten</span>
                <a href="https://www.baseten.co/" target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1">
                  Get API Key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'financial_apis' && (
          <div className="p-4 bg-accent/30 rounded-lg border border-primary/30">
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <LineChart className="w-4 h-4 text-primary" />
              Free API Resources
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span>Binance (Free WebSocket + REST)</span>
                <a href="https://www.binance.com/en/support/faq/how-to-create-api-keys-360002502072" target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1">
                  Get API Key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="flex items-center justify-between">
                <span>Alpha Vantage (25 calls/day)</span>
                <a href="https://www.alphavantage.co/support/#api-key" target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1">
                  Get API Key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="flex items-center justify-between">
                <span>CryptoCompare (100k/month)</span>
                <a href="https://www.cryptocompare.com/cryptopian/api-keys" target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1">
                  Get API Key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="flex items-center justify-between">
                <span>Finnhub (60 calls/min)</span>
                <a href="https://finnhub.io/register" target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1">
                  Get API Key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Configure your trading agent and API connections</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-2">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
                activeSection === section.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-accent/50 hover:bg-accent text-foreground'
              }`}
            >
              <section.icon className="w-5 h-5" />
              <div>
                <p className="font-medium">{section.title}</p>
                <p className={`text-xs ${activeSection === section.id ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                  {section.description}
                </p>
              </div>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="glass rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold">
                {sections.find(s => s.id === activeSection)?.title}
              </h2>
              <button
                onClick={handleSave}
                disabled={saving}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  saved
                    ? 'bg-bull text-white'
                    : 'bg-primary text-primary-foreground hover:bg-primary/90'
                }`}
              >
                {saved ? (
                  <>
                    <Check className="w-4 h-4" />
                    Saved
                  </>
                ) : saving ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Changes
                  </>
                )}
              </button>
            </div>

            {renderSection()}
          </div>
        </div>
      </div>
    </div>
  )
}
