import { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Activity, 
  Layers,
  Target,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Droplets,
  Box,
  Gap
} from 'lucide-react';

interface LiquidityZone {
  id: string;
  pair: string;
  type: 'buy_side' | 'sell_side';
  price: number;
  strength: 'high' | 'medium' | 'low';
  volume: number;
}

interface OrderBlock {
  id: string;
  pair: string;
  type: 'bullish' | 'bearish';
  top: number;
  bottom: number;
  timestamp: string;
}

interface FVG {
  id: string;
  pair: string;
  type: 'bullish' | 'bearish';
  top: number;
  bottom: number;
  status: 'unfilled' | 'filled' | 'partial';
}

export default function Analysis() {
  const [selectedPair, setSelectedPair] = useState('EURUSD');
  const [activeTab, setActiveTab] = useState<'liquidity' | 'orderblocks' | 'fvg' | 'priceaction'>('liquidity');

  const pairs = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD', 'ETHUSD'];

  const liquidityZones: LiquidityZone[] = [
    { id: 'LQ-001', pair: 'EURUSD', type: 'buy_side', price: 1.0820, strength: 'high', volume: 1250 },
    { id: 'LQ-002', pair: 'EURUSD', type: 'sell_side', price: 1.0860, strength: 'high', volume: 980 },
    { id: 'LQ-003', pair: 'EURUSD', type: 'buy_side', price: 1.0800, strength: 'medium', volume: 650 },
  ];

  const orderBlocks: OrderBlock[] = [
    { id: 'OB-001', pair: 'EURUSD', type: 'bullish', top: 1.0835, bottom: 1.0825, timestamp: '2024-01-15 14:00' },
    { id: 'OB-002', pair: 'EURUSD', type: 'bearish', top: 1.0855, bottom: 1.0845, timestamp: '2024-01-15 12:30' },
  ];

  const fvgs: FVG[] = [
    { id: 'FVG-001', pair: 'EURUSD', type: 'bullish', top: 1.0842, bottom: 1.0838, status: 'unfilled' },
    { id: 'FVG-002', pair: 'EURUSD', type: 'bearish', top: 1.0852, bottom: 1.0848, status: 'partial' },
  ];

  const priceActionPatterns = [
    { name: 'Bullish Engulfing', pair: 'EURUSD', timeframe: 'H1', confidence: 85, direction: 'bullish' },
    { name: 'Bearish Pin Bar', pair: 'EURUSD', timeframe: 'M15', confidence: 72, direction: 'bearish' },
    { name: 'Morning Star', pair: 'EURUSD', timeframe: 'H4', confidence: 91, direction: 'bullish' },
  ];

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'high': return 'text-red-400 bg-red-500/20 border-red-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      case 'low': return 'text-green-400 bg-green-500/20 border-green-500/30';
      default: return 'text-slate-400 bg-slate-500/20 border-slate-500/30';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'unfilled': return 'text-green-400 bg-green-500/20';
      case 'filled': return 'text-red-400 bg-red-500/20';
      case 'partial': return 'text-yellow-400 bg-yellow-500/20';
      default: return 'text-slate-400 bg-slate-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Technical Analysis</h1>
          <p className="text-slate-400 mt-1">Liquidity zones, order blocks, and price action</p>
        </div>
        <select
          value={selectedPair}
          onChange={(e) => setSelectedPair(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-blue-500"
        >
          {pairs.map(pair => (
            <option key={pair} value={pair}>{pair}</option>
          ))}
        </select>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        {[
          { id: 'liquidity', label: 'Liquidity Zones', icon: Droplets },
          { id: 'orderblocks', label: 'Order Blocks', icon: Box },
          { id: 'fvg', label: 'Fair Value Gaps', icon: Gap },
          { id: 'priceaction', label: 'Price Action', icon: Activity },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              activeTab === tab.id 
                ? 'bg-blue-500 text-white' 
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Liquidity Zones */}
      {activeTab === 'liquidity' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-green-500/20 rounded-xl">
                  <ArrowUpRight className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Buy-Side Liquidity</p>
                  <p className="text-2xl font-bold text-white">3 Zones</p>
                </div>
              </div>
              <p className="text-sm text-slate-500">Above current price - targets for longs</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-red-500/20 rounded-xl">
                  <ArrowDownRight className="w-6 h-6 text-red-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Sell-Side Liquidity</p>
                  <p className="text-2xl font-bold text-white">2 Zones</p>
                </div>
              </div>
              <p className="text-sm text-slate-500">Below current price - targets for shorts</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-blue-500/20 rounded-xl">
                  <Layers className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Total Volume</p>
                  <p className="text-2xl font-bold text-white">2,880 lots</p>
                </div>
              </div>
              <p className="text-sm text-slate-500">Combined liquidity pool size</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Droplets className="w-5 h-5 text-blue-400" />
              Detected Liquidity Zones
            </h3>
            <div className="space-y-3">
              {liquidityZones.map((zone) => (
                <div key={zone.id} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      zone.type === 'buy_side' ? 'bg-green-500/20' : 'bg-red-500/20'
                    }`}>
                      {zone.type === 'buy_side' ? (
                        <ArrowUpRight className="w-5 h-5 text-green-400" />
                      ) : (
                        <ArrowDownRight className="w-5 h-5 text-red-400" />
                      )}
                    </div>
                    <div>
                      <p className="font-semibold text-white">{zone.id}</p>
                      <p className="text-sm text-slate-400 capitalize">{zone.type.replace('_', ' ')}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-white">{zone.price.toFixed(4)}</p>
                    <p className="text-sm text-slate-400">{zone.volume} lots</p>
                  </div>
                  <div className={`px-3 py-1 rounded-full border text-xs font-medium ${getStrengthColor(zone.strength)}`}>
                    {zone.strength.toUpperCase()} STRENGTH
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Order Blocks */}
      {activeTab === 'orderblocks' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Box className="w-5 h-5 text-purple-400" />
            Order Blocks (Smart Money Concepts)
          </h3>
          <div className="space-y-3">
            {orderBlocks.map((ob) => (
              <div key={ob.id} className="p-4 bg-slate-800/50 rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      ob.type === 'bullish' ? 'bg-green-500/20' : 'bg-red-500/20'
                    }`}>
                      {ob.type === 'bullish' ? (
                        <TrendingUp className="w-5 h-5 text-green-400" />
                      ) : (
                        <TrendingUp className="w-5 h-5 text-red-400 rotate-180" />
                      )}
                    </div>
                    <div>
                      <p className="font-semibold text-white">{ob.id}</p>
                      <p className="text-sm text-slate-400 capitalize">{ob.type} Order Block</p>
                    </div>
                  </div>
                  <span className="text-xs text-slate-500">{ob.timestamp}</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-700/50 rounded-lg">
                    <p className="text-xs text-slate-400">Top</p>
                    <p className="text-lg font-bold text-white">{ob.top.toFixed(4)}</p>
                  </div>
                  <div className="p-3 bg-slate-700/50 rounded-lg">
                    <p className="text-xs text-slate-400">Bottom</p>
                    <p className="text-lg font-bold text-white">{ob.bottom.toFixed(4)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fair Value Gaps */}
      {activeTab === 'fvg' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Gap className="w-5 h-5 text-yellow-400" />
            Fair Value Gaps (Imbalances)
          </h3>
          <div className="space-y-3">
            {fvgs.map((fvg) => (
              <div key={fvg.id} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    fvg.type === 'bullish' ? 'bg-green-500/20' : 'bg-red-500/20'
                  }`}>
                    <Zap className={`w-5 h-5 ${fvg.type === 'bullish' ? 'text-green-400' : 'text-red-400'}`} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">{fvg.id}</p>
                    <p className="text-sm text-slate-400 capitalize">{fvg.type} FVG</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm text-slate-400">Range</p>
                    <p className="font-bold text-white">{fvg.bottom.toFixed(4)} - {fvg.top.toFixed(4)}</p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(fvg.status)}`}>
                    {fvg.status.toUpperCase()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Price Action */}
      {activeTab === 'priceaction' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-400" />
            Price Action Patterns
          </h3>
          <div className="space-y-3">
            {priceActionPatterns.map((pattern, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    pattern.direction === 'bullish' ? 'bg-green-500/20' : 'bg-red-500/20'
                  }`}>
                    <Target className={`w-5 h-5 ${pattern.direction === 'bullish' ? 'text-green-400' : 'text-red-400'}`} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">{pattern.name}</p>
                    <p className="text-sm text-slate-400">{pattern.pair} • {pattern.timeframe}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm text-slate-400">Confidence</p>
                    <p className="font-bold text-purple-400">{pattern.confidence}%</p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${
                    pattern.direction === 'bullish' 
                      ? 'bg-green-500/20 text-green-400' 
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {pattern.direction}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
