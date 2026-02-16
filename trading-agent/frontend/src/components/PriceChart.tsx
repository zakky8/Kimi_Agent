import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts'
import { useHistoricalData } from '../hooks/useApi'

interface PriceChartProps {
  symbol: string
  height?: number
  timeframe?: string
}

export function PriceChart({ symbol, height = 400, timeframe = '1h' }: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const [isDark, setIsDark] = useState(true)
  
  const { data, isLoading } = useHistoricalData(symbol, timeframe, 200)

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
      height,
    })

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [height])

  // Update data when it changes
  useEffect(() => {
    if (candlestickSeriesRef.current && data?.data) {
      const chartData: CandlestickData[] = data.data.map((candle: any) => ({
        time: candle.timestamp / 1000,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      }))

      candlestickSeriesRef.current.setData(chartData)
      chartRef.current?.timeScale().fitContent()
    }
  }, [data])

  if (isLoading) {
    return (
      <div 
        className="flex items-center justify-center bg-accent/30 rounded-lg"
        style={{ height }}
      >
        <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="relative">
      <div ref={chartContainerRef} className="w-full" />
      
      {/* Chart Controls */}
      <div className="absolute top-2 right-2 flex gap-2">
        {['1m', '5m', '15m', '1h', '4h', '1d'].map((tf) => (
          <button
            key={tf}
            className={`px-2 py-1 text-xs rounded ${
              timeframe === tf
                ? 'bg-primary text-primary-foreground'
                : 'bg-accent/80 hover:bg-accent'
            }`}
          >
            {tf}
          </button>
        ))}
      </div>
    </div>
  )
}
