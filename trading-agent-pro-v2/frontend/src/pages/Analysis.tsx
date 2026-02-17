import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  TrendingUp,
  Activity,
  Layers,
  Target,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Droplets,
  Box,
  Layout as Gap,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';

const API_URL = '/api/v1';

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

interface AnalysisData {
  symbol: string;
  liquidityZones: LiquidityZone[];
  orderBlocks: OrderBlock[];
  fvgs: FVG[];
  patterns: any[];
}

export default function Analysis() {
  const [selectedPair, setSelectedPair] = useState('EURUSD');
  const [activeTab, setActiveTab] = useState<'liquidity' | 'orderblocks' | 'fvg' | 'priceaction'>('liquidity');

  const pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD'];

  const { data, isLoading, error } = useQuery({
    queryKey: ['analysis', selectedPair],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/analysis/${selectedPair}`);
      return res.data;
    },
    refetchInterval: 60000,
  });

  const analysis: AnalysisData = data || {
    symbol: selectedPair,
    liquidityZones: [],
    orderBlocks: [],
    fvgs: [],
    patterns: []
  };

  const liquidityZones = analysis.liquidityZones;
  const orderBlocks = analysis.orderBlocks;
  const fvgs = analysis.fvgs;
  const priceActionPatterns = analysis.patterns;

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

  const totalLiquidityVolume = liquidityZones.reduce((acc, z) => acc + z.volume, 0);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            Technical Analysis
            {isLoading && <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />}
          </h1>
          <p className="text-slate-400 mt-1">Real-time liquidity zones, order blocks, and price action</p>
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
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${activeTab === tab.id
              ? 'bg-blue-500 text-white'
              : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading && !data ? (
        <div className="flex items-center justify-center p-12">
          <RefreshCw className="w-10 h-10 text-blue-500 animate-spin" />
          <span className="ml-3 text-slate-400">Analyzing market structure...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-2xl text-center">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-white">Analysis Failed</h3>
          <p className="text-slate-400">Could not fetch analysis data for {selectedPair}</p>
        </div>
      ) : (
        <>
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
                      <p className="text-2xl font-bold text-white">{liquidityZones.filter(z => z.type === 'buy_side').length} Zones</p>
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
                      <p className="text-2xl font-bold text-white">{liquidityZones.filter(z => z.type === 'sell_side').length} Zones</p>
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
                      <p className="text-2xl font-bold text-white">{totalLiquidityVolume.toLocaleString()}</p>
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
                {liquidityZones.length === 0 ? (
                  <p className="text-slate-500 text-center py-6">No significant liquidity zones detected near current price.</p>
                ) : (
                  <div className="space-y-3">
                    {liquidityZones.map((zone) => (
                      <div key={zone.id} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl">
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${zone.type === 'buy_side' ? 'bg-green-500/20' : 'bg-red-500/20'
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
                          <p className="text-lg font-bold text-white">{zone.price.toFixed(5)}</p>
                          <p className="text-sm text-slate-400">{zone.volume} lots</p>
                        </div>
                        <div className={`px-3 py-1 rounded-full border text-xs font-medium ${getStrengthColor(zone.strength)}`}>
                          {zone.strength.toUpperCase()} STRENGTH
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
              {orderBlocks.length === 0 ? (
                <p className="text-slate-500 text-center py-6">No clear order blocks identified on H1 timeframe.</p>
              ) : (
                <div className="space-y-3">
                  {orderBlocks.map((ob) => (
                    <div key={ob.id} className="p-4 bg-slate-800/50 rounded-xl">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${ob.type === 'bullish' ? 'bg-green-500/20' : 'bg-red-500/20'
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
                          <p className="text-lg font-bold text-white">{ob.top.toFixed(5)}</p>
                        </div>
                        <div className="p-3 bg-slate-700/50 rounded-lg">
                          <p className="text-xs text-slate-400">Bottom</p>
                          <p className="text-lg font-bold text-white">{ob.bottom.toFixed(5)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Fair Value Gaps */}
          {activeTab === 'fvg' && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Gap className="w-5 h-5 text-yellow-400" />
                Fair Value Gaps (Imbalances)
              </h3>
              {fvgs.length === 0 ? (
                <p className="text-slate-500 text-center py-6">No unfilled fair value gaps detected.</p>
              ) : (
                <div className="space-y-3">
                  {fvgs.map((fvg) => (
                    <div key={fvg.id} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${fvg.type === 'bullish' ? 'bg-green-500/20' : 'bg-red-500/20'
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
                          <p className="font-bold text-white">{fvg.bottom.toFixed(5)} - {fvg.top.toFixed(5)}</p>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(fvg.status)}`}>
                          {fvg.status.toUpperCase()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Price Action */}
          {activeTab === 'priceaction' && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-green-400" />
                Price Action Patterns
              </h3>
              {priceActionPatterns.length === 0 ? (
                <p className="text-slate-500 text-center py-6">No classic candlestick patterns detected in recent price action.</p>
              ) : (
                <div className="space-y-3">
                  {priceActionPatterns.map((pattern, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${pattern.direction === 'bullish' ? 'bg-green-500/20' : 'bg-red-500/20'
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
                        <div className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${pattern.direction === 'bullish'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                          }`}>
                          {pattern.direction}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
