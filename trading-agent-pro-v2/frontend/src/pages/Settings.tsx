import { useState, useEffect } from 'react'
import { 
  Key, 
  Save, 
  Check, 
  AlertCircle, 
  ExternalLink,
  Bot,
  TrendingUp,
  MessageSquare,
  Settings2,
  Shield,
  Globe,
  Loader2
} from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface SettingsSection {
  id: string
  name: string
  icon: React.ElementType
  description: string
}

const sections: SettingsSection[] = [
  { id: 'ai', name: 'AI Providers', icon: Bot, description: 'Configure AI model APIs' },
  { id: 'trading', name: 'Trading APIs', icon: TrendingUp, description: 'Binance, Alpha Vantage, etc.' },
  { id: 'social', name: 'Social Media', icon: MessageSquare, description: 'Telegram, Reddit APIs' },
  { id: 'risk', name: 'Risk Management', icon: Shield, description: 'Trading limits and alerts' },
  { id: 'general', name: 'General', icon: Settings2, description: 'Timezone and preferences' },
]

export function Settings() {
  const [activeSection, setActiveSection] = useState('ai')
  const [saved, setSaved] = useState(false)
  
  // Settings state
  const [settings, setSettings] = useState({
    // AI Providers
    openrouter_api_key: '',
    gemini_api_key: '',
    groq_api_key: '',
    anthropic_api_key: '',
    default_ai_model: 'openrouter/anthropic/claude-3-opus',
    
    // Trading APIs
    binance_api_key: '',
    binance_api_secret: '',
    binance_testnet: true,
    alpha_vantage_api_key: '',
    
    // Social Media
    telegram_api_id: '',
    telegram_api_hash: '',
    telegram_phone: '',
    reddit_client_id: '',
    reddit_client_secret: '',
    telegram_channels: '',
    
    // Risk Management
    max_drawdown: 10,
    daily_loss_limit: 2,
    per_trade_risk: 1,
    max_positions: 5,
    
    // General
    default_timezone: 'Asia/Kolkata',
    default_timeframe: '1h',
    monitor_interval: 60,
    alert_enabled: true,
  })

  // Fetch current settings
  const { data: currentSettings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/settings/current`)
      return response.data
    }
  })

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: async (section: string, data: any) => {
      const response = await axios.post(`${API_URL}/settings/update`, {
        section,
        settings: data
      })
      return response.data
    },
    onSuccess: () => {
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    }
  })

  const handleSave = () => {
    updateSettingsMutation.mutate(activeSection, settings)
  }

  const renderSection = () => {
    switch (activeSection) {
      case 'ai':
        return <AIProvidersSettings settings={settings} setSettings={setSettings} />
      case 'trading':
        return <TradingAPISettings settings={settings} setSettings={setSettings} />
      case 'social':
        return <SocialMediaSettings settings={settings} setSettings={setSettings} />
      case 'risk':
        return <RiskSettings settings={settings} setSettings={setSettings} />
      case 'general':
        return <GeneralSettings settings={settings} setSettings={setSettings} />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Configure your AI Trading Agent</p>
        </div>
        <button
          onClick={handleSave}
          disabled={updateSettingsMutation.isPending}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
            saved
              ? 'bg-bull text-white'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }`}
        >
          {updateSettingsMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : saved ? (
            <>
              <Check className="w-5 h-5" />
              Saved
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Save Changes
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-2">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full flex items-center gap-3 p-4 rounded-lg text-left transition-colors ${
                activeSection === section.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-accent hover:bg-accent/80'
              }`}
            >
              <section.icon className="w-5 h-5" />
              <div>
                <p className="font-medium">{section.name}</p>
                <p className={`text-xs ${
                  activeSection === section.id ? 'text-primary-foreground/70' : 'text-muted-foreground'
                }`}>
                  {section.description}
                </p>
              </div>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="glass rounded-xl p-6">
            {renderSection()}
          </div>
        </div>
      </div>
    </div>
  )
}

// AI Providers Settings
function AIProvidersSettings({ settings, setSettings }: any) {
  const providers = [
    {
      name: 'OpenRouter',
      key: 'openrouter_api_key',
      url: 'https://openrouter.ai/keys',
      description: 'Access Claude, GPT-4, Gemini, Llama (Recommended)',
      models: ['anthropic/claude-3-opus', 'openai/gpt-4-turbo', 'google/gemini-pro']
    },
    {
      name: 'Google Gemini',
      key: 'gemini_api_key',
      url: 'https://aistudio.google.com/app/apikey',
      description: 'Free tier with vision support',
      models: ['gemini-pro', 'gemini-pro-vision']
    },
    {
      name: 'Groq',
      key: 'groq_api_key',
      url: 'https://console.groq.com/keys',
      description: 'Fast inference with Llama and Mixtral',
      models: ['llama2-70b-4096', 'mixtral-8x7b-32768']
    },
    {
      name: 'Anthropic',
      key: 'anthropic_api_key',
      url: 'https://console.anthropic.com/',
      description: 'Claude 3 Opus/Sonnet (Paid)',
      models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229']
    }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">AI Providers</h2>
        <p className="text-muted-foreground">
          Configure AI model APIs for analysis and chat. At least one provider is required.
        </p>
      </div>

      <div className="space-y-4">
        {providers.map((provider) => (
          <div key={provider.key} className="p-4 bg-accent/50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-medium">{provider.name}</h3>
                <p className="text-sm text-muted-foreground">{provider.description}</p>
              </div>
              <a
                href={provider.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-primary hover:underline"
              >
                Get API Key <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            
            <div className="relative">
              <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="password"
                value={settings[provider.key]}
                onChange={(e) => setSettings({ ...settings, [provider.key]: e.target.value })}
                placeholder={`Enter ${provider.name} API Key`}
                className="w-full pl-10 pr-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
              />
            </div>
            
            <div className="mt-2 flex flex-wrap gap-1">
              {provider.models.map((model) => (
                <span key={model} className="px-2 py-0.5 bg-accent rounded text-xs text-muted-foreground">
                  {model.split('/').pop()}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 bg-bull/10 border border-bull/30 rounded-lg">
        <div className="flex items-start gap-3">
          <Check className="w-5 h-5 text-bull flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-bull">Recommendation</p>
            <p className="text-sm text-bull/80">
              Start with <strong>OpenRouter</strong> for access to multiple models, 
              or <strong>Gemini</strong> for free tier with vision support.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Trading API Settings
function TradingAPISettings({ settings, setSettings }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Trading APIs</h2>
        <p className="text-muted-foreground">
          Configure financial data APIs for market data and trading.
        </p>
      </div>

      {/* Binance */}
      <div className="p-4 bg-accent/50 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-medium">Binance</h3>
            <p className="text-sm text-muted-foreground">Real-time crypto data (Free: 1200 req/min)</p>
          </div>
          <a
            href="https://www.binance.com/en/support/faq/how-to-create-api-keys-360002502072"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-primary hover:underline"
          >
            Get API Key <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        
        <div className="space-y-3">
          <div className="relative">
            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="password"
              value={settings.binance_api_key}
              onChange={(e) => setSettings({ ...settings, binance_api_key: e.target.value })}
              placeholder="API Key"
              className="w-full pl-10 pr-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
            />
          </div>
          <div className="relative">
            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="password"
              value={settings.binance_api_secret}
              onChange={(e) => setSettings({ ...settings, binance_api_secret: e.target.value })}
              placeholder="API Secret"
              className="w-full pl-10 pr-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
            />
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.binance_testnet}
              onChange={(e) => setSettings({ ...settings, binance_testnet: e.target.checked })}
              className="rounded border-border"
            />
            <span className="text-sm">Use Testnet (recommended for testing)</span>
          </label>
        </div>
      </div>

      {/* Alpha Vantage */}
      <div className="p-4 bg-accent/50 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-medium">Alpha Vantage</h3>
            <p className="text-sm text-muted-foreground">Forex & stock data (Free: 25 calls/day)</p>
          </div>
          <a
            href="https://www.alphavantage.co/support/#api-key"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-primary hover:underline"
          >
            Get API Key <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        
        <div className="relative">
          <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="password"
            value={settings.alpha_vantage_api_key}
            onChange={(e) => setSettings({ ...settings, alpha_vantage_api_key: e.target.value })}
            placeholder="Alpha Vantage API Key"
            className="w-full pl-10 pr-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          />
        </div>
      </div>
    </div>
  )
}

// Social Media Settings
function SocialMediaSettings({ settings, setSettings }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Social Media</h2>
        <p className="text-muted-foreground">
          Configure social media APIs for sentiment analysis.
        </p>
      </div>

      {/* Telegram */}
      <div className="p-4 bg-accent/50 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-medium">Telegram</h3>
            <p className="text-sm text-muted-foreground">Collect data from channels (Free)</p>
          </div>
          <a
            href="https://my.telegram.org/apps"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-primary hover:underline"
          >
            Create App <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        
        <div className="space-y-3">
          <input
            type="text"
            value={settings.telegram_api_id}
            onChange={(e) => setSettings({ ...settings, telegram_api_id: e.target.value })}
            placeholder="API ID"
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          />
          <input
            type="password"
            value={settings.telegram_api_hash}
            onChange={(e) => setSettings({ ...settings, telegram_api_hash: e.target.value })}
            placeholder="API Hash"
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          />
          <input
            type="tel"
            value={settings.telegram_phone}
            onChange={(e) => setSettings({ ...settings, telegram_phone: e.target.value })}
            placeholder="Phone Number (with country code)"
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          />
          <textarea
            value={settings.telegram_channels}
            onChange={(e) => setSettings({ ...settings, telegram_channels: e.target.value })}
            placeholder="Channel usernames (one per line):&#10;@forexsignals&#10;@cryptosignals"
            rows={4}
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary resize-none"
          />
        </div>
      </div>

      {/* Reddit */}
      <div className="p-4 bg-accent/50 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-medium">Reddit</h3>
            <p className="text-sm text-muted-foreground">Community sentiment (Free: 60 req/min)</p>
          </div>
          <a
            href="https://www.reddit.com/prefs/apps"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-primary hover:underline"
          >
            Create App <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        
        <div className="space-y-3">
          <input
            type="text"
            value={settings.reddit_client_id}
            onChange={(e) => setSettings({ ...settings, reddit_client_id: e.target.value })}
            placeholder="Client ID"
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          />
          <input
            type="password"
            value={settings.reddit_client_secret}
            onChange={(e) => setSettings({ ...settings, reddit_client_secret: e.target.value })}
            placeholder="Client Secret"
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          />
        </div>
      </div>
    </div>
  )
}

// Risk Management Settings
function RiskSettings({ settings, setSettings }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Risk Management</h2>
        <p className="text-muted-foreground">
          Configure trading limits and risk parameters.
        </p>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">
            Max Drawdown: {settings.max_drawdown}%
          </label>
          <input
            type="range"
            min="5"
            max="30"
            value={settings.max_drawdown}
            onChange={(e) => setSettings({ ...settings, max_drawdown: parseInt(e.target.value) })}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Maximum portfolio loss before stopping
          </p>
        </div>

        <div className="p-4 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">
            Daily Loss Limit: {settings.daily_loss_limit}%
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={settings.daily_loss_limit}
            onChange={(e) => setSettings({ ...settings, daily_loss_limit: parseInt(e.target.value) })}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Maximum daily loss limit
          </p>
        </div>

        <div className="p-4 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">
            Risk Per Trade: {settings.per_trade_risk}%
          </label>
          <input
            type="range"
            min="0.5"
            max="5"
            step="0.5"
            value={settings.per_trade_risk}
            onChange={(e) => setSettings({ ...settings, per_trade_risk: parseFloat(e.target.value) })}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Percentage of account risked per trade
          </p>
        </div>

        <div className="p-4 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">
            Max Concurrent Positions: {settings.max_positions}
          </label>
          <input
            type="number"
            min="1"
            max="20"
            value={settings.max_positions}
            onChange={(e) => setSettings({ ...settings, max_positions: parseInt(e.target.value) })}
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          />
        </div>
      </div>
    </div>
  )
}

// General Settings
function GeneralSettings({ settings, setSettings }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">General Settings</h2>
        <p className="text-muted-foreground">
          Configure general preferences and system settings.
        </p>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">Default Timezone</label>
          <select
            value={settings.default_timezone}
            onChange={(e) => setSettings({ ...settings, default_timezone: e.target.value })}
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          >
            <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
            <option value="America/New_York">America/New_York (EST)</option>
            <option value="Europe/London">Europe/London (GMT)</option>
            <option value="UTC">UTC</option>
          </select>
        </div>

        <div className="p-4 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">Default Timeframe</label>
          <select
            value={settings.default_timeframe}
            onChange={(e) => setSettings({ ...settings, default_timeframe: e.target.value })}
            className="w-full px-4 py-2 bg-background rounded-lg border border-border outline-none focus:border-primary"
          >
            <option value="1m">1 Minute</option>
            <option value="5m">5 Minutes</option>
            <option value="15m">15 Minutes</option>
            <option value="1h">1 Hour</option>
            <option value="4h">4 Hours</option>
            <option value="1d">1 Day</option>
          </select>
        </div>

        <div className="p-4 bg-accent/50 rounded-lg">
          <label className="block text-sm text-muted-foreground mb-2">
            Monitor Interval: {settings.monitor_interval} seconds
          </label>
          <input
            type="range"
            min="30"
            max="300"
            step="30"
            value={settings.monitor_interval}
            onChange={(e) => setSettings({ ...settings, monitor_interval: parseInt(e.target.value) })}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground mt-1">
            How often to check market conditions
          </p>
        </div>

        <label className="flex items-center gap-3 p-4 bg-accent/50 rounded-lg cursor-pointer">
          <input
            type="checkbox"
            checked={settings.alert_enabled}
            onChange={(e) => setSettings({ ...settings, alert_enabled: e.target.checked })}
            className="w-5 h-5 rounded border-border"
          />
          <div>
            <p className="font-medium">Enable Alerts</p>
            <p className="text-sm text-muted-foreground">Receive notifications for important events</p>
          </div>
        </label>
      </div>
    </div>
  )
}
