import { useState } from 'react'
import { RefreshCw, Filter, Download, Bell } from 'lucide-react'
import { useActiveSignals, useGenerateSignal } from '../hooks/useApi'
import { SignalCard } from '../components/SignalCard'

const SYMBOLS = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'USOIL']
const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

export function Signals() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSD')
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h')
  const [filter, setFilter] = useState<'all' | 'long' | 'short'>('all')
  
  const { data: activeSignals, isLoading: activeLoading, refetch: refetchActive } = useActiveSignals()
  const { data: newSignal, isLoading: signalLoading, refetch: generateSignal } = useGenerateSignal(selectedSymbol, selectedTimeframe)

  const filteredSignals = activeSignals?.signals?.filter((s: any) => {
    if (filter === 'all') return true
    return s.direction === filter
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Trading Signals</h1>
          <p className="text-muted-foreground">AI-generated signals with confluence analysis</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => refetchActive()}
            className="flex items-center gap-2 px-4 py-2 bg-accent rounded-lg hover:bg-accent/80 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-accent rounded-lg hover:bg-accent/80 transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
            <Bell className="w-4 h-4" />
            Alerts
          </button>
        </div>
      </div>

      {/* Signal Generator */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Generate New Signal</h2>
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="block text-sm text-muted-foreground mb-2">Symbol</label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="px-4 py-2 bg-accent rounded-lg border border-border outline-none focus:border-primary"
            >
              {SYMBOLS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-2">Timeframe</label>
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
          <div className="flex items-end">
            <button
              onClick={() => generateSignal()}
              disabled={signalLoading}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {signalLoading ? 'Generating...' : 'Generate Signal'}
            </button>
          </div>
        </div>

        {/* New Signal Result */}
        {newSignal && newSignal.symbol && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Generated Signal</h3>
            <SignalCard signal={newSignal} />
          </div>
        )}
      </div>

      {/* Active Signals */}
      <div className="glass rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-lg font-semibold">Active Signals</h2>
            <p className="text-sm text-muted-foreground">
              {activeSignals?.total_active || 0} signals currently active
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <div className="flex bg-accent rounded-lg p-1">
              {(['all', 'long', 'short'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1 rounded text-sm capitalize transition-colors ${
                    filter === f
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-accent/80'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Signals Grid */}
        {activeLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-48 bg-accent/50 animate-pulse rounded-lg" />
            ))}
          </div>
        ) : filteredSignals?.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSignals.map((signal: any, index: number) => (
              <SignalCard key={index} signal={signal} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            <p>No active signals match your filter criteria</p>
          </div>
        )}
      </div>

      {/* Signal Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-muted-foreground">Total Signals</p>
          <p className="text-2xl font-bold">{activeSignals?.total_active || 0}</p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-muted-foreground">Long Signals</p>
          <p className="text-2xl font-bold text-bull">{activeSignals?.long_signals || 0}</p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-muted-foreground">Short Signals</p>
          <p className="text-2xl font-bold text-bear">{activeSignals?.short_signals || 0}</p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-muted-foreground">Strong Signals</p>
          <p className="text-2xl font-bold text-primary">{activeSignals?.strong_signals || 0}</p>
        </div>
      </div>
    </div>
  )
}
