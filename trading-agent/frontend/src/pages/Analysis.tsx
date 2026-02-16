import { useState } from 'react'
import { BarChart3, TrendingUp, Activity, Layers } from 'lucide-react'
import { useTechnicalAnalysis } from '../hooks/useApi'
import { PriceChart } from '../components/PriceChart'

const SYMBOLS = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'USOIL']
const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

export function Analysis() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSD')
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h')
  
  const { data: analysis, isLoading } = useTechnicalAnalysis(selectedSymbol, selectedTimeframe)

  const indicators = analysis?.indicators || {}
  const patterns = analysis?.patterns || {}
  const regime = analysis?.regime || {}
  const srLevels = analysis?.support_resistance || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Technical Analysis</h1>
          <p className="text-muted-foreground">Advanced indicators and pattern recognition</p>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="px-4 py-2 bg-accent rounded-lg border border-border outline-none focus:border-primary"
          >
            {SYMBOLS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="px-4 py-2 bg-accent rounded-lg border border-border outline-none focus:border-primary"
          >
            {TIMEFRAMES.map((tf) => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Chart */}
      <div className="glass rounded-xl p-4">
        <PriceChart 
          symbol={selectedSymbol} 
          timeframe={selectedTimeframe}
          height={450}
        />
      </div>

      {/* Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Indicators */}
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Indicators</h3>
          </div>
          
          {isLoading ? (
            <div className="space-y-2 animate-pulse">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-10 bg-accent rounded" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {/* Trend */}
              <div className="p-3 bg-accent/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Trend</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">EMA 9:</span>
                    <span className="ml-2 font-mono">{indicators.trend?.ema_9?.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">EMA 21:</span>
                    <span className="ml-2 font-mono">{indicators.trend?.ema_21?.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">EMA 50:</span>
                    <span className="ml-2 font-mono">{indicators.trend?.ema_50?.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">ADX:</span>
                    <span className={`ml-2 font-mono ${
                      (indicators.trend?.adx || 0) > 25 ? 'text-bull' : ''
                    }`}>
                      {indicators.trend?.adx?.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Momentum */}
              <div className="p-3 bg-accent/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Momentum</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">RSI (14):</span>
                    <span className={`ml-2 font-mono ${
                      (indicators.momentum?.rsi_14 || 50) > 70 ? 'text-bear' :
                      (indicators.momentum?.rsi_14 || 50) < 30 ? 'text-bull' : ''
                    }`}>
                      {indicators.momentum?.rsi_14?.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Stoch K:</span>
                    <span className="ml-2 font-mono">{indicators.momentum?.stoch_k?.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">CCI:</span>
                    <span className="ml-2 font-mono">{indicators.momentum?.cci?.toFixed(1)}</span>
                  </div>
                </div>
              </div>

              {/* Volatility */}
              <div className="p-3 bg-accent/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Volatility</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">ATR (14):</span>
                    <span className="ml-2 font-mono">{indicators.volatility?.atr_14?.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">BB Width:</span>
                    <span className="ml-2 font-mono">{indicators.volatility?.bb_width?.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Patterns */}
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Patterns</h3>
          </div>

          {isLoading ? (
            <div className="space-y-2 animate-pulse">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-accent rounded" />
              ))}
            </div>
          ) : patterns.patterns?.length > 0 ? (
            <div className="space-y-2">
              {patterns.patterns.slice(0, 5).map((pattern: any, idx: number) => (
                <div 
                  key={idx} 
                  className={`p-3 rounded-lg ${
                    pattern.type === 'bullish' ? 'bg-bull/10 border border-bull/30' :
                    pattern.type === 'bearish' ? 'bg-bear/10 border border-bear/30' :
                    'bg-accent/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm">{pattern.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      pattern.type === 'bullish' ? 'bg-bull/20 text-bull' :
                      pattern.type === 'bearish' ? 'bg-bear/20 text-bear' :
                      'bg-neutral/20 text-neutral'
                    }`}>
                      {pattern.type}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-1 text-xs text-muted-foreground">
                    <span>Confidence: {(pattern.confidence * 100).toFixed(0)}%</span>
                    {pattern.price_target && (
                      <span>Target: {pattern.price_target.toFixed(4)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">No patterns detected</p>
          )}

          {/* Pattern Stats */}
          <div className="grid grid-cols-3 gap-2 mt-4">
            <div className="text-center p-2 bg-accent/50 rounded">
              <p className="text-lg font-bold text-bull">{patterns.bullish_count || 0}</p>
              <p className="text-xs text-muted-foreground">Bullish</p>
            </div>
            <div className="text-center p-2 bg-accent/50 rounded">
              <p className="text-lg font-bold text-bear">{patterns.bearish_count || 0}</p>
              <p className="text-xs text-muted-foreground">Bearish</p>
            </div>
            <div className="text-center p-2 bg-accent/50 rounded">
              <p className="text-lg font-bold">{patterns.neutral_count || 0}</p>
              <p className="text-xs text-muted-foreground">Neutral</p>
            </div>
          </div>
        </div>

        {/* Market Regime & S/R */}
        <div className="space-y-4">
          {/* Regime */}
          <div className="glass rounded-xl p-4">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-primary" />
              <h3 className="font-semibold">Market Regime</h3>
            </div>

            {isLoading ? (
              <div className="h-20 bg-accent animate-pulse rounded" />
            ) : (
              <div className="p-4 bg-accent/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Current Regime</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    regime.current?.includes('up') ? 'bg-bull/20 text-bull' :
                    regime.current?.includes('down') ? 'bg-bear/20 text-bear' :
                    'bg-neutral/20 text-neutral'
                  }`}>
                    {regime.current?.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Confidence</span>
                  <span className="font-mono">{(regime.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm text-muted-foreground">Duration</span>
                  <span className="font-mono">{regime.duration} bars</span>
                </div>
              </div>
            )}
          </div>

          {/* Support/Resistance */}
          <div className="glass rounded-xl p-4">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h3 className="font-semibold">Support / Resistance</h3>
            </div>

            {isLoading ? (
              <div className="space-y-2 animate-pulse">
                <div className="h-10 bg-accent rounded" />
                <div className="h-10 bg-accent rounded" />
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Resistance Levels</p>
                  <div className="flex flex-wrap gap-2">
                    {srLevels.resistance?.slice(0, 4).map((level: number, idx: number) => (
                      <span key={idx} className="px-2 py-1 bg-bear/10 text-bear rounded text-sm font-mono">
                        {level.toFixed(4)}
                      </span>
                    )) || <span className="text-sm text-muted-foreground">None detected</span>}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Support Levels</p>
                  <div className="flex flex-wrap gap-2">
                    {srLevels.support?.slice(0, 4).map((level: number, idx: number) => (
                      <span key={idx} className="px-2 py-1 bg-bull/10 text-bull rounded text-sm font-mono">
                        {level.toFixed(4)}
                      </span>
                    )) || <span className="text-sm text-muted-foreground">None detected</span>}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
