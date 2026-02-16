import { TrendingUp, TrendingDown, Target, Shield, Clock, BarChart3 } from 'lucide-react'

interface Signal {
  symbol: string
  direction: 'long' | 'short' | 'neutral'
  strength: 'strong' | 'moderate' | 'weak'
  confidence: number
  entry_price?: number
  stop_loss?: number
  take_profit?: number
  risk_reward?: number
  strategy: string
  reasons: string[]
}

interface SignalCardProps {
  signal: Signal
}

export function SignalCard({ signal }: SignalCardProps) {
  const isLong = signal.direction === 'long'
  const isStrong = signal.strength === 'strong'
  
  return (
    <div className={`p-4 rounded-lg border ${
      isLong 
        ? 'bg-bull/10 border-bull/30' 
        : 'bg-bear/10 border-bear/30'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isLong ? (
            <TrendingUp className="w-5 h-5 text-bull" />
          ) : (
            <TrendingDown className="w-5 h-5 text-bear" />
          )}
          <span className="font-bold text-lg">{signal.symbol}</span>
        </div>
        <div className={`px-2 py-1 rounded text-xs font-medium ${
          isStrong 
            ? 'bg-primary text-primary-foreground' 
            : 'bg-accent text-muted-foreground'
        }`}>
          {signal.strength.toUpperCase()}
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-muted-foreground mb-1">
          <span>Confidence</span>
          <span>{(signal.confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-accent rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all ${
              isLong ? 'bg-bull' : 'bg-bear'
            }`}
            style={{ width: `${signal.confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Price Levels */}
      <div className="grid grid-cols-3 gap-2 mb-3 text-sm">
        <div className="bg-accent/50 rounded p-2">
          <div className="text-xs text-muted-foreground flex items-center gap-1">
            <Target className="w-3 h-3" /> Entry
          </div>
          <div className="font-mono font-medium">
            {signal.entry_price?.toFixed(4) || '-'}
          </div>
        </div>
        <div className="bg-accent/50 rounded p-2">
          <div className="text-xs text-muted-foreground flex items-center gap-1">
            <Shield className="w-3 h-3" /> Stop
          </div>
          <div className="font-mono font-medium text-bear">
            {signal.stop_loss?.toFixed(4) || '-'}
          </div>
        </div>
        <div className="bg-accent/50 rounded p-2">
          <div className="text-xs text-muted-foreground flex items-center gap-1">
            <Target className="w-3 h-3" /> Target
          </div>
          <div className="font-mono font-medium text-bull">
            {signal.take_profit?.toFixed(4) || '-'}
          </div>
        </div>
      </div>

      {/* R:R Ratio */}
      {signal.risk_reward && (
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-muted-foreground">Risk:Reward</span>
          <span className={`font-bold ${
            (signal.risk_reward >= 2) ? 'text-bull' : 'text-muted-foreground'
          }`}>
            1:{signal.risk_reward.toFixed(1)}
          </span>
        </div>
      )}

      {/* Strategy */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
        <BarChart3 className="w-3 h-3" />
        <span>{signal.strategy}</span>
      </div>

      {/* Reasons */}
      {signal.reasons && signal.reasons.length > 0 && (
        <div className="mt-3 pt-3 border-t border-border/50">
          <p className="text-xs text-muted-foreground mb-1">Key Factors:</p>
          <ul className="text-xs space-y-1">
            {signal.reasons.slice(0, 3).map((reason, idx) => (
              <li key={idx} className="flex items-start gap-1">
                <span className="text-primary">•</span>
                <span className="line-clamp-1">{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
