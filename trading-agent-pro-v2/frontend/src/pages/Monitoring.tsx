import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  Activity,
  Server,
  Database,
  Globe,
  Cpu,
  Shield,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Terminal,
  Play,
  Pause,
  Square,
  RefreshCw
} from 'lucide-react';

const API_URL = '/api/v1';

interface ServiceStatus {
  name: string;
  status: 'operational' | 'degraded' | 'down';
  uptime: string;
  latency: number;
}

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: string;
  uptime: string;
  services: ServiceStatus[];
}

export default function Monitoring() {
  const [logs, setLogs] = useState<string[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['monitoring', 'status'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/monitoring/status`);
      return res.data as SystemMetrics;
    },
    refetchInterval: 2000,
  });

  // Simulated log streaming
  useEffect(() => {
    const interval = setInterval(() => {
      const actions = [
        'Analyzed EURUSD market structure - Bullish div detected',
        'Updated trailing stop for XAUUSD position #124',
        'Fetching breakdown of news sentiment...',
        'Risk check passed: Exposure < 2%',
        'Heartbeat signal received from risk_engine',
        'Syncing order book data...',
        'Processing new tick data for BTCUSD',
        'Garbage collection run completed'
      ];

      const randomLog = `[${new Date().toLocaleTimeString()}] [INFO] ${actions[Math.floor(Math.random() * actions.length)]}`;

      setLogs(prev => {
        const newLogs = [...prev, randomLog];
        if (newLogs.length > 50) return newLogs.slice(-50);
        return newLogs;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Auto-scroll logs
  useEffect(() => {
    if (autoScroll) {
      const terminal = document.getElementById('terminal-logs');
      if (terminal) terminal.scrollTop = terminal.scrollHeight;
    }
  }, [logs, autoScroll]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'text-green-400';
      case 'degraded': return 'text-yellow-400';
      case 'down': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'degraded': return <AlertCircle className="w-4 h-4 text-yellow-400" />;
      case 'down': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const systemMetrics = metrics || {
    cpu: 0,
    memory: 0,
    disk: 0,
    network: '0 KB/s',
    uptime: '0h 0m',
    services: [
      { name: 'API Gateway', status: 'operational', uptime: '99.9%', latency: 45 },
      { name: 'Risk Engine', status: 'operational', uptime: '99.9%', latency: 12 },
      { name: 'Market Data Feed', status: 'operational', uptime: '99.9%', latency: 85 },
      { name: 'Execution Service', status: 'operational', uptime: '99.9%', latency: 34 },
      { name: 'AI Inference Node', status: 'operational', uptime: '99.9%', latency: 120 },
    ] as ServiceStatus[]
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            System Monitoring
            {isLoading && <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />}
          </h1>
          <p className="text-slate-400 mt-1">Real-time infrastructure health and logs</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 rounded-lg border border-green-500/20">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm font-medium text-green-400">System Healthy</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg">
            <Clock className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-300">Uptime: {systemMetrics.uptime}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Metrics */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Cpu className="w-4 h-4 text-blue-400" />
                </div>
                <span className="text-slate-400 text-sm">CPU Usage</span>
              </div>
              <p className="text-2xl font-bold text-white">{systemMetrics.cpu}%</p>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${systemMetrics.cpu > 80 ? 'bg-red-500' : 'bg-blue-500'}`}
                  style={{ width: `${systemMetrics.cpu}%` }}
                />
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Activity className="w-4 h-4 text-purple-400" />
                </div>
                <span className="text-slate-400 text-sm">Memory</span>
              </div>
              <p className="text-2xl font-bold text-white">{systemMetrics.memory}%</p>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${systemMetrics.memory > 80 ? 'bg-red-500' : 'bg-purple-500'}`}
                  style={{ width: `${systemMetrics.memory}%` }}
                />
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-yellow-500/20 rounded-lg">
                  <Database className="w-4 h-4 text-yellow-400" />
                </div>
                <span className="text-slate-400 text-sm">Disk I/O</span>
              </div>
              <p className="text-2xl font-bold text-white">{systemMetrics.disk}%</p>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
                <div
                  className="h-full rounded-full bg-yellow-500 transition-all duration-500"
                  style={{ width: `${systemMetrics.disk}%` }}
                />
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-green-500/20 rounded-lg">
                  <Globe className="w-4 h-4 text-green-400" />
                </div>
                <span className="text-slate-400 text-sm">Network</span>
              </div>
              <p className="text-lg font-bold text-white truncate">{systemMetrics.network}</p>
              <p className="text-xs text-green-400 mt-1">Stable</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Server className="w-5 h-5 text-indigo-400" />
              Service Status
            </h3>
            <div className="space-y-4">
              {systemMetrics.services.map((service, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-slate-800/30 rounded-xl hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${service.status === 'operational' ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="font-medium text-white">{service.name}</span>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right hidden sm:block">
                      <p className="text-xs text-slate-400">Latency</p>
                      <p className="text-sm font-mono text-white">{service.latency}ms</p>
                    </div>
                    <div className="text-right hidden sm:block">
                      <p className="text-xs text-slate-400">Uptime</p>
                      <p className="text-sm font-mono text-green-400">{service.uptime}</p>
                    </div>
                    <div className={`flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 capitalize text-sm font-medium ${getStatusColor(service.status)}`}>
                      {getStatusIcon(service.status)}
                      {service.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Live Logs */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[600px] lg:h-auto">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="font-bold text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-slate-400" />
              System Logs
            </h3>
            <div className="flex items-center gap-2">
              <div
                onClick={() => setAutoScroll(!autoScroll)}
                className={`w-2 h-2 rounded-full cursor-pointer ${autoScroll ? 'bg-green-500' : 'bg-slate-500'}`}
                title="Auto-scroll"
              />
              <span className="text-xs text-slate-500">Live</span>
            </div>
          </div>

          <div
            id="terminal-logs"
            className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-xs"
          >
            {logs.map((log, i) => (
              <div key={i} className="text-slate-300 break-all hover:bg-slate-800/50 p-1 rounded">
                <span className="text-slate-500">{log.split(']')[0]}]</span>
                <span className={log.includes('ERROR') ? 'text-red-400' : log.includes('WARN') ? 'text-yellow-400' : 'text-blue-400'}>
                  {log.split(']')[1]}]
                </span>
                <span className="text-slate-300">{log.split(']').slice(2).join(']')}</span>
              </div>
            ))}
            {logs.length === 0 && (
              <div className="text-slate-500 text-center mt-10">Waiting for logs...</div>
            )}
          </div>

          <div className="p-3 border-t border-slate-800 bg-slate-900/50 flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <input
              type="text"
              disabled
              placeholder="System log stream active..."
              className="bg-transparent border-none focus:outline-none text-xs text-slate-500 w-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
