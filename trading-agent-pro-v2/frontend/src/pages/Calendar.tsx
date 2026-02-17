import { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, Clock, AlertTriangle, TrendingUp, Globe, Filter } from 'lucide-react';

interface EconomicEvent {
  id: string;
  time: string;
  currency: string;
  event: string;
  impact: 'high' | 'medium' | 'low';
  actual?: string;
  forecast?: string;
  previous?: string;
}

export default function Calendar() {
  const [events] = useState<EconomicEvent[]>([
    { id: '1', time: '08:00 AM', currency: 'EUR', event: 'German CPI m/m', impact: 'high', forecast: '0.3%', previous: '0.2%' },
    { id: '2', time: '08:30 AM', currency: 'GBP', event: 'UK GDP m/m', impact: 'high', forecast: '0.1%', previous: '-0.1%' },
    { id: '3', time: '10:00 AM', currency: 'EUR', event: 'EU Economic Forecasts', impact: 'medium', forecast: '-', previous: '-' },
    { id: '4', time: '02:30 PM', currency: 'USD', event: 'CPI m/m', impact: 'high', forecast: '0.3%', previous: '0.4%' },
    { id: '5', time: '02:30 PM', currency: 'USD', event: 'Core CPI m/m', impact: 'high', forecast: '0.3%', previous: '0.3%' },
    { id: '6', time: '04:00 PM', currency: 'USD', event: 'Crude Oil Inventories', impact: 'medium', forecast: '-1.2M', previous: '-2.1M' },
    { id: '7', time: '06:00 PM', currency: 'USD', event: 'FOMC Meeting Minutes', impact: 'high', forecast: '-', previous: '-' },
    { id: '8', time: '08:30 PM', currency: 'USD', event: 'Fed Chair Powell Speaks', impact: 'high', forecast: '-', previous: '-' },
  ]);

  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const filteredEvents = events.filter(e => filter === 'all' || e.impact === filter);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'low': return 'bg-green-500/20 text-green-400 border-green-500/30';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const getCurrencyFlag = (currency: string) => {
    const flags: Record<string, string> = {
      USD: '🇺🇸',
      EUR: '🇪🇺',
      GBP: '🇬🇧',
      JPY: '🇯🇵',
      AUD: '🇦🇺',
      CAD: '🇨🇦',
      CHF: '🇨🇭',
      NZD: '🇳🇿',
    };
    return flags[currency] || '🏳️';
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <CalendarIcon className="w-6 h-6 text-blue-400" />
            Forex Economic Calendar
          </h1>
          <p className="text-slate-400 mt-1">High-impact events from Forex Factory (IST timezone)</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-xl">
          <Clock className="w-4 h-4 text-slate-400" />
          <span className="text-white font-mono">
            {currentTime.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' })}
          </span>
          <span className="text-xs text-slate-500">IST</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'High Impact', value: events.filter(e => e.impact === 'high').length, color: 'red' },
          { label: 'Medium Impact', value: events.filter(e => e.impact === 'medium').length, color: 'yellow' },
          { label: 'Low Impact', value: events.filter(e => e.impact === 'low').length, color: 'green' },
          { label: 'Total Events', value: events.length, color: 'blue' },
        ].map((stat, index) => (
          <div key={index} className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <p className="text-slate-400 text-sm">{stat.label}</p>
            <p className={`text-2xl font-bold text-${stat.color}-400 mt-1`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-2 bg-slate-800 rounded-xl">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-slate-400">Filter:</span>
        </div>
        {(['all', 'high', 'medium', 'low'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${filter === f
                ? 'bg-blue-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
          >
            {f === 'all' ? 'All Events' : `${f.charAt(0).toUpperCase() + f.slice(1)} Impact`}
          </button>
        ))}
      </div>

      {/* Calendar table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-800/50">
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Time (IST)</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Currency</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Event</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Impact</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Actual</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Forecast</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Previous</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredEvents.map((event) => (
                <tr key={event.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-slate-500" />
                      <span className="text-white font-mono">{event.time}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{getCurrencyFlag(event.currency)}</span>
                      <span className="text-white font-semibold">{event.currency}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {event.impact === 'high' && <AlertTriangle className="w-4 h-4 text-red-400" />}
                      <span className="text-white">{event.event}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getImpactColor(event.impact)}`}>
                      {event.impact.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`font-mono ${event.actual ? 'text-white' : 'text-slate-600'}`}>
                      {event.actual || '-'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-slate-400 font-mono">{event.forecast}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-slate-400 font-mono">{event.previous}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-400" />
          Impact Guide
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <span className="font-semibold text-red-400">High Impact</span>
            </div>
            <p className="text-sm text-slate-400">Major market-moving events. Expect high volatility. Consider reducing position sizes.</p>
          </div>
          <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-yellow-400" />
              <span className="font-semibold text-yellow-400">Medium Impact</span>
            </div>
            <p className="text-sm text-slate-400">Moderate volatility expected. Monitor price action closely.</p>
          </div>
          <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              <span className="font-semibold text-green-400">Low Impact</span>
            </div>
            <p className="text-sm text-slate-400">Minimal market impact. Normal trading conditions.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
