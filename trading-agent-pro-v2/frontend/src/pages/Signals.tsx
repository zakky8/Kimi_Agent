import { useState } from 'react';
import { 
  Signal, 
  TrendingUp, 
  TrendingDown, 
  Filter, 
  Download, 
  Bell,
  Target,
  Shield,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

interface TradingSignal {
  id: string;
  pair: string;
  type: 'BUY' | 'SELL';
  entry: number;
  stopLoss: number;
  takeProfit: number;
  confidence: number;
  timestamp: string;
  status: 'active' | 'pending' | 'completed' | 'cancelled';
  strategy: string;
  timeframe: string;
}

export default function Signals() {
  const [filter, setFilter] = useState<'all' | 'active' | 'pending' | 'completed'>('all');
  const [signals, setSignals] = useState<TradingSignal[]>([
    {
      id: 'SIG-001',
      pair: 'EURUSD',
      type: 'BUY',
      entry: 1.0845,
      stopLoss: 1.0820,
      takeProfit: 1.0890,
      confidence: 87,
      timestamp: '2024-01-15 14:30:00',
      status: 'active',
      strategy: 'Liquidity Sweep + FVG',
      timeframe: 'H1',
    },
    {
      id: 'SIG-002',
      pair: 'XAUUSD',
      type: 'SELL',
      entry: 2035.50,
      stopLoss: 2045.00,
      takeProfit: 2015.00,
      confidence: 72,
      timestamp: '2024-01-15 13:15:00',
      status: 'pending',
      strategy: 'Order Block Rejection',
      timeframe: 'H4',
    },
    {
      id: 'SIG-003',
      pair: 'GBPUSD',
      type: 'BUY',
      entry: 1.2630,
      stopLoss: 1.2600,
      takeProfit: 1.2680,
      confidence: 91,
      timestamp: '2024-01-15 11:45:00',
      status: 'completed',
      strategy: 'Breaker Block + MSS',
      timeframe: 'M15',
    },
    {
      id: 'SIG-004',
      pair: 'BTCUSD',
      type: 'BUY',
      entry: 52100.00,
      stopLoss: 51500.00,
      takeProfit: 53500.00,
      confidence: 78,
      timestamp: '2024-01-15 10:20:00',
      status: 'active',
      strategy: 'Fair Value Gap Fill',
      timeframe: 'H1',
    },
  ]);

  const filteredSignals = signals.filter(s => filter === 'all' || s.status === filter);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />;
      case 'pending': return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-blue-400" />;
      case 'cancelled': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <AlertCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'pending': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'completed': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'cancelled': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Trading Signals</h1>
          <p className="text-slate-400 mt-1">AI-generated signals with technical analysis</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors">
            <Bell className="w-4 h-4" />
            <span className="text-sm">Alerts</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors">
            <Download className="w-4 h-4" />
            <span className="text-sm">Export</span>
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Signals', value: signals.length, color: 'blue' },
          { label: 'Active', value: signals.filter(s => s.status === 'active').length, color: 'green' },
          { label: 'Pending', value: signals.filter(s => s.status === 'pending').length, color: 'yellow' },
          { label: 'Win Rate', value: '76%', color: 'purple' },
        ].map((stat, index) => (
          <div key={index} className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <p className="text-slate-400 text-sm">{stat.label}</p>
            <p className={`text-2xl font-bold text-${stat.color}-400 mt-1`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-2 bg-slate-800 rounded-xl">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-slate-400">Filter:</span>
        </div>
        {(['all', 'active', 'pending', 'completed'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              filter === f 
                ? 'bg-blue-500 text-white' 
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Signals grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredSignals.map((signal) => (
          <div key={signal.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-colors">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  signal.type === 'BUY' ? 'bg-green-500/20' : 'bg-red-500/20'
                }`}>
                  {signal.type === 'BUY' ? (
                    <TrendingUp className="w-6 h-6 text-green-400" />
                  ) : (
                    <TrendingDown className="w-6 h-6 text-red-400" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{signal.pair}</h3>
                  <p className="text-sm text-slate-400">{signal.id}</p>
                </div>
              </div>
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${getStatusColor(signal.status)}`}>
                {getStatusIcon(signal.status)}
                <span className="text-xs font-medium capitalize">{signal.status}</span>
              </div>
            </div>

            {/* Signal details */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="p-3 bg-slate-800/50 rounded-xl">
                <p className="text-xs text-slate-400 mb-1">Entry</p>
                <p className="text-lg font-bold text-white">{signal.entry.toFixed(signal.pair === 'XAUUSD' ? 2 : signal.pair.includes('BTC') ? 0 : 4)}</p>
              </div>
              <div className="p-3 bg-slate-800/50 rounded-xl">
                <p className="text-xs text-slate-400 mb-1">Stop Loss</p>
                <p className="text-lg font-bold text-red-400">{signal.stopLoss.toFixed(signal.pair === 'XAUUSD' ? 2 : signal.pair.includes('BTC') ? 0 : 4)}</p>
              </div>
              <div className="p-3 bg-slate-800/50 rounded-xl">
                <p className="text-xs text-slate-400 mb-1">Take Profit</p>
                <p className="text-lg font-bold text-green-400">{signal.takeProfit.toFixed(signal.pair === 'XAUUSD' ? 2 : signal.pair.includes('BTC') ? 0 : 4)}</p>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-blue-400" />
                  <span className="text-sm text-slate-400">{signal.strategy}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-400">{signal.timeframe}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-purple-400">{signal.confidence}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredSignals.length === 0 && (
        <div className="text-center py-12">
          <Signal className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No signals found for the selected filter</p>
        </div>
      )}
    </div>
  );
}
