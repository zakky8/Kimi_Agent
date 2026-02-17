import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
    GitBranch,
    Cpu,
    RefreshCw,
    Settings,
    PauseCircle,
    PlayCircle,
    ArrowUpRight,
    ArrowDownRight,
} from 'lucide-react';

const API_URL = '/api/v1';

interface EvolutionEvent {
    id: number;
    timestamp: string;
    event_type: string;
    model_name: string | null;
    change_summary: string;
    triggered_by: string;
}

const EVENT_ICONS: Record<string, typeof GitBranch> = {
    retrain: RefreshCw,
    config_change: Settings,
    pause: PauseCircle,
    resume: PlayCircle,
};

const EVENT_COLORS: Record<string, string> = {
    retrain: 'blue',
    config_change: 'purple',
    pause: 'red',
    resume: 'green',
};

export default function EvolutionLog() {
    const { data } = useQuery<EvolutionEvent[]>({
        queryKey: ['evolution-log'],
        queryFn: async () => {
            const res = await axios.get(`${API_URL}/evolution/recent`);
            return res.data;
        },
        refetchInterval: 60000,
    });

    const events: EvolutionEvent[] = data || [];

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <GitBranch className="w-5 h-5 text-cyan-400" />
                    Agent Evolution
                </h2>
                <div className="flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="text-xs text-slate-400">Self-improving</span>
                </div>
            </div>

            {events.length === 0 ? (
                <div className="text-center py-8">
                    <div className="w-12 h-12 rounded-full bg-cyan-500/10 flex items-center justify-center mx-auto mb-3">
                        <GitBranch className="w-6 h-6 text-cyan-500" />
                    </div>
                    <p className="text-slate-400 text-sm">No evolution events yet</p>
                    <p className="text-slate-600 text-xs mt-1">AI will self-tune after processing trades</p>
                </div>
            ) : (
                <div className="relative">
                    {/* Timeline line */}
                    <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-800" />

                    <div className="space-y-4">
                        {events.slice(0, 8).map((evt) => {
                            const Icon = EVENT_ICONS[evt.event_type] || GitBranch;
                            const color = EVENT_COLORS[evt.event_type] || 'slate';
                            const timeStr = new Date(evt.timestamp).toLocaleString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                            });

                            return (
                                <div key={evt.id} className="flex gap-3 relative">
                                    {/* Timeline dot */}
                                    <div className={`w-8 h-8 rounded-full bg-${color}-500/20 flex items-center justify-center z-10 ring-4 ring-slate-900 flex-shrink-0`}>
                                        <Icon className={`w-3.5 h-3.5 text-${color}-400`} />
                                    </div>
                                    <div className="flex-1 min-w-0 pb-1">
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm font-medium text-white capitalize">
                                                {evt.event_type.replace(/_/g, ' ')}
                                            </span>
                                            {evt.model_name && (
                                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                                                    {evt.model_name}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-xs text-slate-500 mt-0.5 truncate">{evt.change_summary}</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-[10px] text-slate-600">{timeStr}</span>
                                            <span className="text-[10px] text-slate-700">•</span>
                                            <span className="text-[10px] text-slate-600 capitalize">{evt.triggered_by}</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
