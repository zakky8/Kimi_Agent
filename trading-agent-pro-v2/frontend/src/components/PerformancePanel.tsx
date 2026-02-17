import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
} from 'recharts';
import {
    TrendingUp,
    TrendingDown,
    Target,
    BarChart3,
    AlertOctagon,
    PauseCircle,
} from 'lucide-react';

const API_URL = '/api/v1';

interface PerformanceData {
    win_rate: number;
    total_trades: number;
    total_pnl: number;
    max_drawdown_pct: number;
    sharpe_ratio: number;
    avg_rr: number;
    is_paused: boolean;
}

export default function PerformancePanel() {
    const { data } = useQuery<PerformanceData>({
        queryKey: ['performance'],
        queryFn: async () => {
            const res = await axios.get(`${API_URL}/performance`);
            return res.data;
        },
        refetchInterval: 30000,
    });

    const perf: PerformanceData = data || {
        win_rate: 0,
        total_trades: 0,
        total_pnl: 0,
        max_drawdown_pct: 0,
        sharpe_ratio: 0,
        avg_rr: 0,
        is_paused: false,
    };

    // Demo equity curve
    const equityData = Array.from({ length: 30 }, (_, i) => ({
        day: i + 1,
        equity: 10000 + (perf.total_pnl > 0 ? 1 : -1) * Math.random() * 200 * (i + 1) / 30,
    }));

    const metrics = [
        {
            label: 'Win Rate',
            value: `${(perf.win_rate * 100).toFixed(1)}%`,
            icon: Target,
            color: perf.win_rate >= 0.5 ? 'green' : perf.win_rate >= 0.4 ? 'amber' : 'red',
        },
        {
            label: 'Sharpe',
            value: perf.sharpe_ratio.toFixed(2),
            icon: BarChart3,
            color: perf.sharpe_ratio >= 1.0 ? 'green' : perf.sharpe_ratio >= 0.5 ? 'amber' : 'red',
        },
        {
            label: 'Max DD',
            value: `${perf.max_drawdown_pct.toFixed(1)}%`,
            icon: TrendingDown,
            color: perf.max_drawdown_pct <= 5 ? 'green' : perf.max_drawdown_pct <= 10 ? 'amber' : 'red',
        },
        {
            label: 'Avg R:R',
            value: perf.avg_rr.toFixed(1),
            icon: TrendingUp,
            color: perf.avg_rr >= 2 ? 'green' : perf.avg_rr >= 1.5 ? 'amber' : 'red',
        },
    ];

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-400" />
                    Performance
                </h2>
                {perf.is_paused && (
                    <div className="flex items-center gap-1.5 px-3 py-1 bg-red-500/20 border border-red-500/30 rounded-lg">
                        <PauseCircle className="w-4 h-4 text-red-400" />
                        <span className="text-xs font-semibold text-red-400">PAUSED</span>
                    </div>
                )}
            </div>

            {/* Top line: P&L + trades */}
            <div className="flex items-end justify-between mb-4">
                <div>
                    <p className="text-sm text-slate-400">Total P&L</p>
                    <p className={`text-3xl font-bold ${perf.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {perf.total_pnl >= 0 ? '+' : ''}${perf.total_pnl.toFixed(2)}
                    </p>
                </div>
                <div className="text-right">
                    <p className="text-sm text-slate-400">Trades</p>
                    <p className="text-2xl font-bold text-white">{perf.total_trades}</p>
                </div>
            </div>

            {/* Mini equity chart */}
            <div className="h-24 mb-5 -mx-2">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={equityData}>
                        <defs>
                            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor={perf.total_pnl >= 0 ? '#22c55e' : '#ef4444'} stopOpacity={0.3} />
                                <stop offset="100%" stopColor={perf.total_pnl >= 0 ? '#22c55e' : '#ef4444'} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <Area
                            type="monotone"
                            dataKey="equity"
                            stroke={perf.total_pnl >= 0 ? '#22c55e' : '#ef4444'}
                            strokeWidth={2}
                            fill="url(#equityGradient)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Metrics grid */}
            <div className="grid grid-cols-2 gap-3">
                {metrics.map((m) => (
                    <div key={m.label} className="bg-slate-800/60 rounded-xl p-3">
                        <div className="flex items-center gap-2 mb-1">
                            <m.icon className={`w-3.5 h-3.5 text-${m.color}-400`} />
                            <span className="text-xs text-slate-400">{m.label}</span>
                        </div>
                        <p className={`text-lg font-bold text-${m.color}-400`}>{m.value}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
