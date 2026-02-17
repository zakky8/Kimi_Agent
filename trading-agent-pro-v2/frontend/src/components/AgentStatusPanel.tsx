import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
    Brain,
    ShieldCheck,
    TrendingUp,
    BarChart3,
    HeartPulse,
    Gauge,
    CheckCircle,
    XCircle,
    MinusCircle,
    AlertTriangle,
} from 'lucide-react';

const API_URL = '/api/v1';

interface AgentOpinion {
    agent_name: string;
    vote: string;
    confidence: number;
    reasoning: string;
}

interface ConsensusData {
    symbol: string;
    direction: string;
    consensus_score: number;
    agreement_count: number;
    total_agents: number;
    is_actionable: boolean;
    opinions: Record<string, AgentOpinion>;
    reasons: string[];
}

const AGENT_ICONS: Record<string, typeof Brain> = {
    DataAgent: HeartPulse,
    TechnicalAgent: BarChart3,
    SentimentAgent: Gauge,
    MLAgent: Brain,
    RiskAgent: ShieldCheck,
};

const AGENT_COLORS: Record<string, string> = {
    DataAgent: 'cyan',
    TechnicalAgent: 'blue',
    SentimentAgent: 'amber',
    MLAgent: 'purple',
    RiskAgent: 'emerald',
};

function VoteIcon({ vote }: { vote: string }) {
    switch (vote) {
        case 'LONG':
            return <TrendingUp className="w-4 h-4 text-green-400" />;
        case 'SHORT':
            return <TrendingUp className="w-4 h-4 text-red-400 rotate-180" />;
        case 'ABSTAIN':
            return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
        default:
            return <MinusCircle className="w-4 h-4 text-slate-400" />;
    }
}

function VoteBadge({ vote }: { vote: string }) {
    const styles: Record<string, string> = {
        LONG: 'bg-green-500/20 text-green-400 border-green-500/30',
        SHORT: 'bg-red-500/20 text-red-400 border-red-500/30',
        NEUTRAL: 'bg-slate-700/50 text-slate-400 border-slate-600/30',
        ABSTAIN: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    };

    return (
        <span className={`text-xs px-2 py-0.5 rounded-full border ${styles[vote] || styles.NEUTRAL}`}>
            {vote}
        </span>
    );
}

export default function AgentStatusPanel() {
    const { data: consensusData } = useQuery<ConsensusData>({
        queryKey: ['consensus-status'],
        queryFn: async () => {
            const res = await axios.get(`${API_URL}/consensus/latest`);
            return res.data;
        },
        refetchInterval: 10000,
    });

    // Fallback demo data when API is not yet connected
    const consensus: ConsensusData = consensusData || {
        symbol: 'BTC/USDT',
        direction: 'NEUTRAL',
        consensus_score: 0.0,
        agreement_count: 0,
        total_agents: 5,
        is_actionable: false,
        opinions: {
            DataAgent: { agent_name: 'DataAgent', vote: 'NEUTRAL', confidence: 0.9, reasoning: 'Data OK: fresh feeds' },
            TechnicalAgent: { agent_name: 'TechnicalAgent', vote: 'NEUTRAL', confidence: 0.0, reasoning: 'Awaiting data...' },
            SentimentAgent: { agent_name: 'SentimentAgent', vote: 'NEUTRAL', confidence: 0.3, reasoning: 'Neutral sentiment' },
            MLAgent: { agent_name: 'MLAgent', vote: 'NEUTRAL', confidence: 0.0, reasoning: 'Models loading...' },
            RiskAgent: { agent_name: 'RiskAgent', vote: 'NEUTRAL', confidence: 1.0, reasoning: 'Risk OK' },
        },
        reasons: ['System initializing...'],
    };

    const scoreColor = consensus.consensus_score > 0.3
        ? 'text-green-400'
        : consensus.consensus_score < -0.3
            ? 'text-red-400'
            : 'text-slate-400';

    const directionBg = consensus.direction === 'LONG'
        ? 'from-green-600/20 to-emerald-600/20 border-green-500/30'
        : consensus.direction === 'SHORT'
            ? 'from-red-600/20 to-rose-600/20 border-red-500/30'
            : 'from-slate-700/20 to-slate-800/20 border-slate-700/30';

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-400" />
                    Multi-Agent Consensus
                </h2>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border bg-gradient-to-r ${directionBg}`}>
                    <VoteIcon vote={consensus.direction} />
                    <span className="text-sm font-semibold text-white">{consensus.direction}</span>
                </div>
            </div>

            {/* Score bar */}
            <div className="mb-5">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                    <span>Bearish</span>
                    <span className={`font-mono font-bold text-sm ${scoreColor}`}>
                        {consensus.consensus_score > 0 ? '+' : ''}{consensus.consensus_score.toFixed(3)}
                    </span>
                    <span>Bullish</span>
                </div>
                <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden relative">
                    <div
                        className="absolute top-0 h-full rounded-full transition-all duration-700"
                        style={{
                            left: '50%',
                            width: `${Math.abs(consensus.consensus_score) * 50}%`,
                            transform: consensus.consensus_score < 0 ? 'translateX(-100%)' : 'none',
                            background: consensus.consensus_score >= 0
                                ? 'linear-gradient(90deg, #22c55e, #10b981)'
                                : 'linear-gradient(270deg, #ef4444, #f43f5e)',
                        }}
                    />
                    <div className="absolute top-0 left-1/2 w-0.5 h-full bg-slate-600" />
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500 mt-1">
                    <span>{consensus.agreement_count}/{consensus.total_agents} agree</span>
                    <span>{consensus.is_actionable ? '✅ Actionable' : '⏸ Waiting'}</span>
                </div>
            </div>

            {/* Agent cards */}
            <div className="space-y-2.5">
                {Object.values(consensus.opinions).map((op) => {
                    const Icon = AGENT_ICONS[op.agent_name] || Brain;
                    const color = AGENT_COLORS[op.agent_name] || 'slate';

                    return (
                        <div key={op.agent_name} className="flex items-center gap-3 p-3 bg-slate-800/60 rounded-xl hover:bg-slate-800 transition-colors">
                            <div className={`w-9 h-9 rounded-lg bg-${color}-500/20 flex items-center justify-center flex-shrink-0`}>
                                <Icon className={`w-4.5 h-4.5 text-${color}-400`} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-white">{op.agent_name.replace('Agent', '')}</span>
                                    <VoteBadge vote={op.vote} />
                                </div>
                                <p className="text-xs text-slate-500 truncate mt-0.5">{op.reasoning}</p>
                            </div>
                            <div className="text-right flex-shrink-0">
                                <div className="text-xs font-mono text-slate-400">{(op.confidence * 100).toFixed(0)}%</div>
                                <div className="w-12 h-1 bg-slate-700 rounded-full mt-1 overflow-hidden">
                                    <div
                                        className={`h-full rounded-full ${op.confidence > 0.7 ? 'bg-green-500' : op.confidence > 0.4 ? 'bg-amber-500' : 'bg-slate-500'
                                            }`}
                                        style={{ width: `${op.confidence * 100}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
