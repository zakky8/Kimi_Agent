import { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  DollarSign, 
  BarChart3, 
  Globe,
  Zap,
  Clock,
  AlertTriangle,
  CheckCircle,
  Brain
} from 'lucide-react';

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
}

interface SystemStatus {
  aiAgent: boolean;
  browserAutomation: boolean;
  telegramCollector: boolean;
  forexCalendar: boolean;
  monitoring24_7: boolean;
}

export default function Dashboard() {
  const [marketData, setMarketData] = useState<MarketData[]>([
    { symbol: 'EURUSD', price: 1.0845, change: 0.0023, changePercent: 0.21 },
    { symbol: 'GBPUSD', price: 1.2634, change: -0.0012, changePercent: -0.09 },
    { symbol: 'XAUUSD', price: 2034.56, change: 12.40, changePercent: 0.61 },
    { symbol: 'BTCUSD', price: 52340.00, change: 1240.50, changePercent: 2.43 },
    { symbol: 'ETHUSD', price: 2890.25, change: 45.30, changePercent: 1.59 },
  ]);

  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    aiAgent: true,
    browserAutomation: true,
    telegramCollector: true,
    forexCalendar: true,
    monitoring24_7: true,
  });

  const [recentSignals, setRecentSignals] = useState([
    { id: 1, pair: 'EURUSD', type: 'BUY', confidence: 87, time: '2 min ago', status: 'active' },
    { id: 2, pair: 'XAUUSD', type: 'SELL', confidence: 72, time: '15 min ago', status: 'pending' },
    { id: 3, pair: 'GBPUSD', type: 'BUY', confidence: 91, time: '32 min ago', status: 'completed' },
  ]);

  const stats = [
    { label: 'Active Signals', value: '12', change: '+3', icon: Zap, color: 'blue' },
    { label: 'Win Rate', value: '76.4%', change: '+2.1%', icon: Activity, color: 'green' },
    { label: 'Total P&L', value: '+$2,340', change: '+12.5%', icon: DollarSign, color: 'purple' },
    { label: 'Markets Monitored', value: '24', change: '+5', icon: Globe, color: 'orange' },
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Real-time market overview and system status</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-xl">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-green-400 text-sm font-medium">System Online</span>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <div key={index} className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-slate-400 text-sm">{stat.label}</p>
                <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                <p className={`text-sm mt-1 ${stat.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                  {stat.change} from last week
                </p>
              </div>
              <div className={`p-3 rounded-xl bg-${stat.color}-500/20`}>
                <stat.icon className={`w-6 h-6 text-${stat.color}-400`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Market prices */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              Live Market Prices
            </h2>
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Updated: Just now
            </span>
          </div>
          
          <div className="space-y-3">
            {marketData.map((item) => (
              <div key={item.symbol} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl hover:bg-slate-800 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-slate-700 flex items-center justify-center">
                    <span className="text-sm font-bold text-white">{item.symbol.slice(0, 2)}</span>
                  </div>
                  <div>
                    <p className="font-semibold text-white">{item.symbol}</p>
                    <p className="text-sm text-slate-400">Forex</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-white">{item.price.toFixed(item.symbol === 'XAUUSD' ? 2 : item.symbol.includes('BTC') ? 0 : 4)}</p>
                  <div className={`flex items-center gap-1 ${item.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {item.change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    <span className="text-sm">{item.change >= 0 ? '+' : ''}{item.changePercent}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System status */}
        <div className="space-y-6">
          {/* Status panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-green-400" />
              System Status
            </h2>
            
            <div className="space-y-3">
              {Object.entries(systemStatus).map(([key, status]) => (
                <div key={key} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center gap-3">
                    {status ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                    )}
                    <span className="text-slate-300 capitalize">{key.replace(/_/g, ' ')}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${status ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    {status ? 'Active' : 'Offline'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent signals */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              Recent Signals
            </h2>
            
            <div className="space-y-3">
              {recentSignals.map((signal) => (
                <div key={signal.id} className="p-3 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-white">{signal.pair}</span>
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                      signal.type === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {signal.type}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Confidence: {signal.confidence}%</span>
                    <span className="text-slate-500">{signal.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* AI Agent status */}
      <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-2xl p-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-7 h-7 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white">AI Trading Agent</h3>
            <p className="text-slate-400">Monitoring markets 24/7 • Analyzing price action • Detecting liquidity zones</p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-xl">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-green-400 text-sm font-medium">Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
