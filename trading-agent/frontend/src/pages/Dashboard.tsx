import { useState } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Signal,
  Users,
  Newspaper,
  DollarSign,
  BarChart3
} from 'lucide-react'
import { useMultiplePrices, useActiveSignals, useMarketWideSentiment, useMarketNews } from '../hooks/useApi'
import { PriceChart } from '../components/PriceChart'
import { SignalCard } from '../components/SignalCard'
import { SentimentGauge } from '../components/SentimentGauge'

const DEFAULT_PAIRS = ['BTCUSD', 'ETHUSD', 'EURUSD', 'GBPUSD', 'XAUUSD']

export function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSD')
  
  const { data: prices, isLoading: pricesLoading } = useMultiplePrices(DEFAULT_PAIRS)
  const { data: signals, isLoading: signalsLoading } = useActiveSignals()
  const { data: sentiment, isLoading: sentimentLoading } = useMarketWideSentiment()
  const { data: news, isLoading: newsLoading } = useMarketNews()

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Signals"
          value={signals?.total_active || 0}
          icon={Signal}
          trend={signals?.long_signals > signals?.short_signals ? 'up' : 'down'}
          trendValue={`${signals?.long_signals || 0} Long / ${signals?.short_signals || 0} Short`}
        />
        <StatCard
          title="Market Sentiment"
          value={sentimentLoading ? '-' : 'Bullish'}
          icon={Activity}
          trend="up"
          trendValue="Social + News"
        />
        <StatCard
          title="News Updates"
          value={news?.news_count || 0}
          icon={Newspaper}
          trend="neutral"
          trendValue="Last hour"
        />
        <StatCard
          title="Avg Confidence"
          value={`${((signals?.avg_confidence || 0) * 100).toFixed(1)}%`}
          icon={BarChart3}
          trend="up"
          trendValue="Signal quality"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Price Chart */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Price Chart</h2>
              <div className="flex gap-2">
                {DEFAULT_PAIRS.map((pair) => (
                  <button
                    key={pair}
                    onClick={() => setSelectedSymbol(pair)}
                    className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                      selectedSymbol === pair
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-accent hover:bg-accent/80'
                    }`}
                  >
                    {pair}
                  </button>
                ))}
              </div>
            </div>
            <PriceChart symbol={selectedSymbol} height={400} />
          </div>
        </div>

        {/* Side Panel */}
        <div className="space-y-4">
          {/* Price Ticker */}
          <div className="glass rounded-xl p-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Live Prices</h3>
            <div className="space-y-2">
              {pricesLoading ? (
                <div className="animate-pulse space-y-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="h-12 bg-accent rounded-lg" />
                  ))}
                </div>
              ) : (
                Object.entries(prices?.prices || {}).map(([symbol, data]: [string, any]) => (
                  <div
                    key={symbol}
                    className="flex items-center justify-between p-3 bg-accent/50 rounded-lg hover:bg-accent transition-colors cursor-pointer"
                    onClick={() => setSelectedSymbol(symbol)}
                  >
                    <div>
                      <span className="font-medium">{symbol}</span>
                      <span className="text-xs text-muted-foreground block">
                        Vol: {(data.volume_24h / 1e6).toFixed(2)}M
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="font-mono">${data.price?.toLocaleString()}</span>
                      <span
                        className={`text-xs block ${
                          (data.change_percent_24h || 0) >= 0 ? 'text-bull' : 'text-bear'
                        }`}
                      >
                        {(data.change_percent_24h || 0) >= 0 ? '+' : ''}
                        {(data.change_percent_24h || 0).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Sentiment Gauge */}
          <div className="glass rounded-xl p-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Market Sentiment</h3>
            <SentimentGauge 
              value={sentiment?.markets?.crypto?.sentiment_score || 0} 
              size="md"
            />
          </div>
        </div>
      </div>

      {/* Active Signals */}
      <div className="glass rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Active Signals</h2>
          <span className="text-sm text-muted-foreground">
            {signals?.total_active || 0} signals active
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {signalsLoading ? (
            <div className="animate-pulse space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 bg-accent rounded-lg" />
              ))}
            </div>
          ) : (
            signals?.signals?.slice(0, 6).map((signal: any, index: number) => (
              <SignalCard key={index} signal={signal} />
            ))
          )}
        </div>
      </div>

      {/* Latest News */}
      <div className="glass rounded-xl p-4">
        <h2 className="text-lg font-semibold mb-4">Latest News</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {newsLoading ? (
            <div className="animate-pulse space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 bg-accent rounded-lg" />
              ))}
            </div>
          ) : (
            news?.latest_news?.slice(0, 6).map((item: any, index: number) => (
              <a
                key={index}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-4 bg-accent/50 rounded-lg hover:bg-accent transition-colors"
              >
                <h4 className="font-medium line-clamp-2 mb-2">{item.title}</h4>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="capitalize">{item.source}</span>
                  <span>•</span>
                  <span>{new Date(item.published).toLocaleTimeString()}</span>
                </div>
              </a>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// Stat Card Component
interface StatCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  trend: 'up' | 'down' | 'neutral'
  trendValue: string
}

function StatCard({ title, value, icon: Icon, trend, trendValue }: StatCardProps) {
  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <div className="p-2 bg-accent rounded-lg">
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="flex items-center gap-1 mt-3">
        {trend === 'up' && <TrendingUp className="w-4 h-4 text-bull" />}
        {trend === 'down' && <TrendingDown className="w-4 h-4 text-bear" />}
        {trend === 'neutral' && <Activity className="w-4 h-4 text-neutral" />}
        <span className={`text-sm ${
          trend === 'up' ? 'text-bull' : trend === 'down' ? 'text-bear' : 'text-neutral'
        }`}>
          {trendValue}
        </span>
      </div>
    </div>
  )
}
