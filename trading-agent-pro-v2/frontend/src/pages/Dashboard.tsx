import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  BarChart3,
  Globe,
  Zap,
  AlertTriangle,
  CheckCircle,
  Brain,
  RefreshCw
} from 'lucide-react';
import AgentStatusPanel from '../components/AgentStatusPanel';
import PerformancePanel from '../components/PerformancePanel';
import MistakeLog from '../components/MistakeLog';
import EvolutionLog from '../components/EvolutionLog';

const API_URL = '/api/v1';

interface MarketPrice {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  category: string;
  timestamp: string;
}

// TradingView symbol mapping
const TV_SYMBOL_MAP: Record<string, string> = {
  'EURUSD': 'FX:EURUSD',
  'GBPUSD': 'FX:GBPUSD',
  'USDJPY': 'FX:USDJPY',
  'XAUUSD': 'TVC:GOLD',
  'BTCUSD': 'BINANCE:BTCUSDT',
};

const FOREX_PAIRS = [
  { symbol: 'EURUSD', label: 'EUR/USD' },
  { symbol: 'GBPUSD', label: 'GBP/USD' },
  { symbol: 'USDJPY', label: 'USD/JPY' },
  { symbol: 'XAUUSD', label: 'XAU/USD' },
  { symbol: 'BTCUSD', label: 'BTC/USD' },
];

const INTERVALS: Record<string, string> = {
  '1': '1m',
  '5': '5m',
  '15': '15m',
  '60': '1H',
  '240': '4H',
  'D': '1D',
};

// TradingView Chart Component using the Advanced Real-Time Widget
function TradingViewChart({ symbol, interval }: { symbol: string; interval: string }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clean previous widget
    containerRef.current.innerHTML = '';

    const tvSymbol = TV_SYMBOL_MAP[symbol] || `FX:${symbol}`;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (!containerRef.current || !(window as any).TradingView) return;

      new (window as any).TradingView.widget({
        container_id: containerRef.current.id,
        width: '100%',
        height: 450,
        symbol: tvSymbol,
        interval: interval,
        timezone: 'Asia/Kolkata',
        theme: 'dark',
        style: '1', // Candlestick
        locale: 'en',
        toolbar_bg: '#0f172a',
        enable_publishing: false,
        allow_symbol_change: true,
        hide_top_toolbar: false,
        hide_legend: false,
        save_image: false,
        backgroundColor: '#0f172a',
        gridColor: '#1e293b',
        studies: ['MASimple@tv-basicstudies'],
        overrides: {
          'mainSeriesProperties.candleStyle.upColor': '#22c55e',
          'mainSeriesProperties.candleStyle.downColor': '#ef4444',
          'mainSeriesProperties.candleStyle.borderUpColor': '#22c55e',
          'mainSeriesProperties.candleStyle.borderDownColor': '#ef4444',
          'mainSeriesProperties.candleStyle.wickUpColor': '#22c55e',
          'mainSeriesProperties.candleStyle.wickDownColor': '#ef4444',
          'paneProperties.background': '#0f172a',
          'paneProperties.vertGridProperties.color': '#1e293b',
          'paneProperties.horzGridProperties.color': '#1e293b',
        },
      });
    };

    // Check if script already loaded
    if ((window as any).TradingView) {
      script.onload(new Event('load') as any);
    } else {
      document.head.appendChild(script);
    }

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [symbol, interval]);

  return (
    <div
      ref={containerRef}
      id={`tv_chart_${symbol}_${interval}`}
      className="rounded-xl overflow-hidden"
    />
  );
}

export default function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');
  const [selectedInterval, setSelectedInterval] = useState('60');

  // Fetch live prices from backend
  const { data: priceData, isLoading: pricesLoading, dataUpdatedAt } = useQuery({
    queryKey: ['market-prices'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/market/prices?symbols=EURUSD,GBPUSD,USDJPY,XAUUSD,BTCUSD`);
      return res.data;
    },
    refetchInterval: 15000,
  });

  const marketPrices: MarketPrice[] = priceData?.prices || [];
  const secondsAgo = dataUpdatedAt ? Math.round((Date.now() - dataUpdatedAt) / 1000) : 0;

  // System health
  const { data: healthData } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/health`);
      return res.data;
    },
    refetchInterval: 60000,
  });

  // Swarm stats for dashboard cards
  const { data: swarmData } = useQuery({
    queryKey: ['swarm-stats'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/swarm/stats`);
      return res.data;
    },
    refetchInterval: 30000,
  });

  const systemStatus = {
    aiAgent: healthData?.ai_connected || false,
    mt5Connected: healthData?.mt5_connected || false,
    browserAutomation: true,
    forexCalendar: true,
    monitoring24_7: true,
  };

  const activeAgents = swarmData?.active_agents ?? 0;
  const totalTrades = swarmData?.total_daily_trades ?? 0;
  const totalPnl = swarmData?.total_daily_pnl ?? 0;

  const stats = [
    { label: 'Active Agents', value: String(activeAgents), change: activeAgents > 0 ? 'Running' : 'Standby', icon: Zap, color: 'blue' },
    { label: 'Daily Trades', value: String(totalTrades), change: totalTrades > 0 ? 'Today' : 'No trades yet', icon: Activity, color: 'green' },
    { label: 'Daily P&L', value: totalPnl >= 0 ? `+$${totalPnl.toFixed(2)}` : `-$${Math.abs(totalPnl).toFixed(2)}`, change: totalPnl >= 0 ? 'Profit' : 'Loss', icon: DollarSign, color: totalPnl >= 0 ? 'green' : 'red' },
    { label: 'Markets Live', value: String(marketPrices.length || 0), change: marketPrices.length > 0 ? 'Streaming' : 'Loading...', icon: Globe, color: 'orange' },
  ];

  const selectedPairLabel = FOREX_PAIRS.find(p => p.symbol === selectedSymbol)?.label || selectedSymbol;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Real-time market overview and system status</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg text-xs text-slate-400">
            <RefreshCw className={`w-3 h-3 ${pricesLoading ? 'animate-spin text-blue-400' : ''}`} />
            <span>{pricesLoading ? 'Updating...' : `Updated ${secondsAgo}s ago`}</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-xl">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-green-400 text-sm font-medium">System Online</span>
          </div>
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
                <p className={`text-sm mt-1 ${stat.change === 'Profit' || stat.change === 'Running' || stat.change === 'Streaming' || stat.change === 'Today'
                  ? 'text-green-400'
                  : stat.change === 'Loss' ? 'text-red-400' : 'text-slate-400'
                  }`}>
                  {stat.change}
                </p>
              </div>
              <div className={`p-3 rounded-xl bg-${stat.color}-500/20`}>
                <stat.icon className={`w-6 h-6 text-${stat.color}-400`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Chart + Prices */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* TradingView Chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                {selectedPairLabel}
              </h2>
              {/* Symbol selector */}
              <div className="flex gap-1">
                {FOREX_PAIRS.map((pair) => (
                  <button
                    key={pair.symbol}
                    onClick={() => setSelectedSymbol(pair.symbol)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${selectedSymbol === pair.symbol
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                      }`}
                  >
                    {pair.label}
                  </button>
                ))}
              </div>
            </div>
            {/* Interval selector */}
            <div className="flex gap-1">
              {Object.entries(INTERVALS).map(([value, label]) => (
                <button
                  key={value}
                  onClick={() => setSelectedInterval(value)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${selectedInterval === value
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* TradingView Widget */}
          <TradingViewChart symbol={selectedSymbol} interval={selectedInterval} />
        </div>

        {/* Live Prices panel */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-green-400" />
                Live Prices
              </h2>
              {pricesLoading && <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />}
            </div>

            <div className="space-y-3">
              {pricesLoading && marketPrices.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                  <p>Fetching live prices...</p>
                </div>
              ) : (
                marketPrices.map((item) => (
                  <button
                    key={item.symbol}
                    onClick={() => setSelectedSymbol(item.symbol)}
                    className={`w-full flex items-center justify-between p-3 rounded-xl transition-all ${selectedSymbol === item.symbol
                      ? 'bg-blue-500/10 border border-blue-500/30'
                      : 'bg-slate-800/50 hover:bg-slate-800 border border-transparent'
                      }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold ${item.changePercent >= 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                        {item.symbol.slice(0, 3)}
                      </div>
                      <div className="text-left">
                        <p className="font-semibold text-white text-sm">{item.symbol}</p>
                        <p className="text-xs text-slate-500">{item.category}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-white text-sm">
                        {item.price.toFixed(item.category === 'Forex' ? 5 : 2)}
                      </p>
                      <div className={`flex items-center gap-1 justify-end ${item.changePercent >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                        {item.changePercent >= 0 ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        <span className="text-xs font-medium">
                          {item.changePercent >= 0 ? '+' : ''}{item.changePercent}%
                        </span>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* System status */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              System Status
            </h2>
            <div className="space-y-2">
              {Object.entries(systemStatus).map(([key, status]) => (
                <div key={key} className="flex items-center justify-between p-2.5 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center gap-2">
                    {status ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                    )}
                    <span className="text-slate-300 text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${status ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                    {status ? 'Active' : key === 'aiAgent' ? 'Missing Keys' : 'Offline'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* AI Agent status banner */}
      <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-2xl p-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-7 h-7 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white">Kimi Agent v3.0</h3>
            <p className="text-slate-400">
              5-agent consensus • Self-improving ML • 40+ indicators • Automated risk management
            </p>
          </div>
          <div className={`flex items-center gap-2 px-4 py-2 border rounded-xl ${systemStatus.aiAgent ? 'bg-green-500/20 border-green-500/30' : 'bg-red-500/20 border-red-500/30'}`}>
            <div className={`w-2 h-2 rounded-full animate-pulse ${systemStatus.aiAgent ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className={`text-sm font-medium ${systemStatus.aiAgent ? 'text-green-400' : 'text-red-400'}`}>
              {systemStatus.aiAgent ? 'Active' : 'Offline (Missing Keys)'}
            </span>
          </div>
        </div>
      </div>

      {/* Intelligence Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentStatusPanel />
        <PerformancePanel />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MistakeLog />
        <EvolutionLog />
      </div>
    </div>
  );
}
