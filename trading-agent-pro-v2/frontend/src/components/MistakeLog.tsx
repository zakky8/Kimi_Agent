import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
    AlertTriangle,
    TrendingDown,
    Gauge,
    Shield,
    Repeat,
    XCircle,
} from 'lucide-react';

const API_URL = '/api/v1';

interface Mistake {
    type: string;
    count: number;
    last_seen: string;
    severity: number;
}

interface MistakeData {
    total_mistakes: number;
    patterns: Mistake[];
    corrective_actions: string[];
}

const MISTAKE_ICONS: Record<string, typeof AlertTriangle> = {
    counter_trend: TrendingDown,
    low_confidence: Gauge,
    high_volatility: AlertTriangle,
    repeat_loss: Repeat,
    oversize: Shield,
};

const MISTAKE_COLORS: Record<string, string> = {
    counter_trend: 'red',
    low_confidence: 'amber',
    high_volatility: 'orange',
    repeat_loss: 'rose',
    oversize: 'purple',
};

export default function MistakeLog() {
    const { data } = useQuery<MistakeData>({
        queryKey: ['mistakes'],
        queryFn: async () => {
            const res = await axios.get(`${API_URL}/mistakes`);
            return res.data;
        },
        refetchInterval: 60000,
    });

    const mistakes: MistakeData = {
        total_mistakes: data?.total_mistakes || 0,
        patterns: data?.patterns || [],
        corrective_actions: data?.corrective_actions || [],
    };

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    Mistake Tracker
                </h2>
                <span className={`text-xs px-2.5 py-1 rounded-lg font-mono ${mistakes.total_mistakes === 0
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-amber-500/20 text-amber-400'
                    }`}>
                    {mistakes.total_mistakes} total
                </span>
            </div>

            {mistakes.patterns.length === 0 ? (
                <div className="text-center py-8">
                    <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-3">
                        <Shield className="w-6 h-6 text-green-500" />
                    </div>
                    <p className="text-slate-400 text-sm">No mistakes detected yet</p>
                    <p className="text-slate-600 text-xs mt-1">Mistakes will appear here as the agent trades</p>
                </div>
            ) : (
                <div className="space-y-2.5">
                    {mistakes.patterns.map((m, i) => {
                        const Icon = MISTAKE_ICONS[m.type] || XCircle;
                        const color = MISTAKE_COLORS[m.type] || 'slate';
                        const severityWidth = Math.min(m.severity * 100, 100);

                        return (
                            <div key={i} className="bg-slate-800/60 rounded-xl p-3 hover:bg-slate-800/80 transition-colors">
                                <div className="flex items-center gap-3">
                                    <div className={`w-8 h-8 rounded-lg bg-${color}-500/20 flex items-center justify-center flex-shrink-0`}>
                                        <Icon className={`w-4 h-4 text-${color}-400`} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-white capitalize">
                                                {m.type.replace(/_/g, ' ')}
                                            </span>
                                            <span className="text-xs font-mono text-slate-500">×{m.count}</span>
                                        </div>
                                        <div className="flex items-center gap-2 mt-1.5">
                                            <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full bg-${color}-500`}
                                                    style={{ width: `${severityWidth}%` }}
                                                />
                                            </div>
                                            <span className="text-[10px] text-slate-500 font-mono">
                                                {(m.severity * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Corrective actions */}
            {mistakes.corrective_actions.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                    <p className="text-xs text-slate-400 font-semibold mb-2 uppercase tracking-wider">Corrections Applied</p>
                    <div className="space-y-1.5">
                        {mistakes.corrective_actions.slice(0, 3).map((action, i) => (
                            <div key={i} className="flex items-start gap-2">
                                <div className="w-1 h-1 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                                <p className="text-xs text-slate-500">{action}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
