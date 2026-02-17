import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  Calendar as CalendarIcon,
  Filter,
  Download,
  Bell,
  Clock,
  Globe,
  RefreshCw,
  AlertTriangle,
  TrendingUp
} from 'lucide-react';

const API_URL = '/api/v1';

interface CalendarEvent {
  id: string;
  title: string;
  country: string;
  impact: 'high' | 'medium' | 'low';
  time: string;
  actual?: string;
  forecast?: string;
  previous?: string;
  currency: string;
}

export default function Calendar() {
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const { data: events = [], isLoading } = useQuery({
    queryKey: ['calendar'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/calendar`);
      return res.data;
    },
    refetchInterval: 300000, // 5 minutes
  });

  // Ensure we access the 'events' array from the response object
  const calendarEvents = events.events || [];
  const filteredEvents = calendarEvents.filter((e: CalendarEvent) => filter === 'all' || e.impact === filter);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'low': return 'bg-green-500/20 text-green-400 border-green-500/30';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            Economic Calendar
            {isLoading && <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />}
          </h1>
          <p className="text-slate-400 mt-1">Key economic events and market-moving news</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors">
            <Bell className="w-4 h-4" />
            <span className="text-sm">Alerts</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors">
            <Download className="w-4 h-4" />
            <span className="text-sm">Export</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-2 bg-slate-800 rounded-xl">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-slate-400">Impact:</span>
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
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Events list */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-800/50 text-slate-400 text-sm">
                <th className="p-4 font-medium">Time</th>
                <th className="p-4 font-medium">Currency</th>
                <th className="p-4 font-medium">Event</th>
                <th className="p-4 font-medium">Impact</th>
                <th className="p-4 font-medium text-right">Actual</th>
                <th className="p-4 font-medium text-right">Forecast</th>
                <th className="p-4 font-medium text-right">Previous</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {isLoading && events.length === 0 ? (
                [1, 2, 3, 4, 5].map(i => (
                  <tr key={i} className="animate-pulse">
                    <td className="p-4"><div className="h-4 bg-slate-800 rounded w-16"></div></td>
                    <td className="p-4"><div className="h-4 bg-slate-800 rounded w-12"></div></td>
                    <td className="p-4"><div className="h-4 bg-slate-800 rounded w-48"></div></td>
                    <td className="p-4"><div className="h-4 bg-slate-800 rounded w-16"></div></td>
                    <td className="p-4"></td>
                    <td className="p-4"></td>
                    <td className="p-4"></td>
                  </tr>
                ))
              ) : filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No events found directly matching your filter.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((event: CalendarEvent) => (
                  <tr key={event.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-white">
                        <Clock className="w-4 h-4 text-slate-400" />
                        {event.time}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-white">
                        <Globe className="w-4 h-4 text-slate-400" />
                        {event.currency}
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="text-white font-medium">{event.title}</span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium border ${getImpactColor(event.impact)} capitalize`}>
                        {event.impact}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <span className={`font-mono font-medium ${!event.actual ? 'text-slate-500' :
                        event.actual.includes('%') && parseFloat(event.actual) > parseFloat(event.forecast || '0') ? 'text-green-400' :
                          'text-white'
                        }`}>
                        {event.actual || '-'}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <span className="font-mono text-slate-400">{event.forecast || '-'}</span>
                    </td>
                    <td className="p-4 text-right">
                      <span className="font-mono text-slate-400">{event.previous || '-'}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
