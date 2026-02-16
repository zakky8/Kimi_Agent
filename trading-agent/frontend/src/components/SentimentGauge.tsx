import { useMemo } from 'react'

interface SentimentGaugeProps {
  value: number // -1 to 1
  size?: 'sm' | 'md' | 'lg'
  showLabels?: boolean
}

export function SentimentGauge({ 
  value, 
  size = 'md', 
  showLabels = true 
}: SentimentGaugeProps) {
  const dimensions = {
    sm: { width: 120, height: 60, stroke: 8 },
    md: { width: 200, height: 100, stroke: 12 },
    lg: { width: 300, height: 150, stroke: 16 },
  }

  const { width, height, stroke } = dimensions[size]
  const radius = (width - stroke) / 2
  const centerX = width / 2
  const centerY = height - stroke / 2

  // Calculate needle position
  const normalizedValue = Math.max(-1, Math.min(1, value))
  const angle = (normalizedValue + 1) * 90 // 0 to 180 degrees
  const angleRad = (angle * Math.PI) / 180
  const needleX = centerX + radius * 0.8 * Math.cos(Math.PI - angleRad)
  const needleY = centerY - radius * 0.8 * Math.sin(angleRad)

  // Determine sentiment label
  const sentiment = useMemo(() => {
    if (value > 0.5) return { label: 'Very Bullish', color: '#22c55e' }
    if (value > 0.2) return { label: 'Bullish', color: '#4ade80' }
    if (value < -0.5) return { label: 'Very Bearish', color: '#ef4444' }
    if (value < -0.2) return { label: 'Bearish', color: '#f87171' }
    return { label: 'Neutral', color: '#6b7280' }
  }, [value])

  // Create gradient segments
  const segments = [
    { color: '#ef4444', start: 0, end: 0.2 },    // Very Bearish
    { color: '#f87171', start: 0.2, end: 0.4 },  // Bearish
    { color: '#6b7280', start: 0.4, end: 0.6 },  // Neutral
    { color: '#4ade80', start: 0.6, end: 0.8 },  // Bullish
    { color: '#22c55e', start: 0.8, end: 1 },    // Very Bullish
  ]

  return (
    <div className="flex flex-col items-center">
      <svg width={width} height={height}>
        {/* Background arc */}
        <path
          d={`M ${stroke / 2} ${centerY} A ${radius} ${radius} 0 0 1 ${width - stroke / 2} ${centerY}`}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={stroke}
          strokeLinecap="round"
        />

        {/* Colored segments */}
        {segments.map((seg, idx) => {
          const startAngle = 180 - (seg.start * 180)
          const endAngle = 180 - (seg.end * 180)
          const startRad = (startAngle * Math.PI) / 180
          const endRad = (endAngle * Math.PI) / 180
          
          const x1 = centerX + radius * Math.cos(startRad)
          const y1 = centerY - radius * Math.sin(startRad)
          const x2 = centerX + radius * Math.cos(endRad)
          const y2 = centerY - radius * Math.sin(endRad)
          
          return (
            <path
              key={idx}
              d={`M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2}`}
              fill="none"
              stroke={seg.color}
              strokeWidth={stroke * 0.8}
              strokeLinecap="round"
            />
          )
        })}

        {/* Needle */}
        <line
          x1={centerX}
          y1={centerY}
          x2={needleX}
          y2={needleY}
          stroke="white"
          strokeWidth={stroke / 4}
          strokeLinecap="round"
        />

        {/* Center dot */}
        <circle
          cx={centerX}
          cy={centerY}
          r={stroke / 2}
          fill="white"
        />
      </svg>

      {/* Labels */}
      {showLabels && (
        <div className="mt-2 text-center">
          <p 
            className="text-lg font-bold"
            style={{ color: sentiment.color }}
          >
            {sentiment.label}
          </p>
          <p className="text-sm text-muted-foreground">
            Score: {(value * 100).toFixed(0)}
          </p>
        </div>
      )}

      {/* Scale labels */}
      {showLabels && size !== 'sm' && (
        <div className="flex justify-between w-full mt-2 text-xs text-muted-foreground">
          <span>Bearish</span>
          <span>Neutral</span>
          <span>Bullish</span>
        </div>
      )}
    </div>
  )
}
