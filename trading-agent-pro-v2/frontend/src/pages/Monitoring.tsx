import { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  Square,
  Activity,
  Globe,
  Bot,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Terminal,
  Cpu,
  Database,
  Wifi
} from 'lucide-react';

interface MonitoringStatus {
  isRunning: boolean;
  startTime: Date | null;
  uptime: string;
  activeTasks: number;
  completedTasks: number;
  errors: number;
}

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  source: string;
}

export default function Monitoring() {
  const [status, setStatus] = useState<MonitoringStatus>({
    isRunning: false,
    startTime: null,
    uptime: '00:00:00',
    activeTasks: 0,
    completedTasks: 0,
    errors: 0,
  });

  const [logs, setLogs] = useState<LogEntry[]>([
    { id: '1', timestamp: '10:00:00', level: 'info', message: 'System initialized', source: 'Main' },
    { id: '2', timestamp: '10:00:01', level: 'success', message: 'Browser automation ready', source: 'Browser' },
    { id: '3', timestamp: '10:00:02', level: 'success', message: 'Telegram collector connected', source: 'Telegram' },
    { id: '4', timestamp: '10:00:03', level: 'info', message: 'AI models loaded', source: 'AI Engine' },
  ]);

  const [uptime, setUptime] = useState('00:00:00');

  useEffect(() => {
    let interval: any;
    if (status.isRunning && status.startTime) {
      interval = setInterval(() => {
        const now = new Date();
        const diff = now.getTime() - status.startTime!.getTime();
        const hours = Math.floor(diff / 3600000).toString().padStart(2, '0');
        const minutes = Math.floor((diff % 3600000) / 60000).toString().padStart(2, '0');
        const seconds = Math.floor((diff % 60000) / 1000).toString().padStart(2, '0');
        setUptime(`${hours}:${minutes}:${seconds}`);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [status.isRunning, status.startTime]);

  const handleStart = () => {
    setStatus(prev => ({
      ...prev,
      isRunning: true,
      startTime: new Date(),
      activeTasks: 5,
    }));
    addLog('success', '24/7 monitoring started', 'System');
  };

  const handlePause = () => {
    setStatus(prev => ({ ...prev, isRunning: false }));
    addLog('warning', 'Monitoring paused', 'System');
  };

  const handleStop = () => {
    setStatus(prev => ({
      ...prev,
      isRunning: false,
      startTime: null,
      activeTasks: 0,
    }));
    setUptime('00:00:00');
    addLog('error', 'Monitoring stopped', 'System');
  };

  const addLog = (level: LogEntry['level'], message: string, source: string) => {
    const newLog: LogEntry = {
      id: Date.now().toString(),
      timestamp: new Date().toLocaleTimeString(),
      level,
      message,
      source,
    };
    setLogs(prev => [newLog, ...prev].slice(0, 100));
  };

  const getLogColor = (level: string) => {
    switch (level) {
      case 'info': return 'text-blue-400';
      case 'success': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  const getLogBg = (level: string) => {
    switch (level) {
      case 'info': return 'bg-blue-500/10';
      case 'success': return 'bg-green-500/10';
      case 'warning': return 'bg-yellow-500/10';
      case 'error': return 'bg-red-500/10';
      default: return 'bg-slate-500/10';
    }
  };

  const services = [
    { name: 'AI Agent', status: 'online', icon: Bot },
    { name: 'Browser Automation', status: 'online', icon: Globe },
    { name: 'Telegram Collector', status: 'online', icon: Wifi },
    { name: 'Forex Calendar', status: 'online', icon: Clock },
    { name: 'Market Data', status: 'online', icon: Database },
    { name: 'Analysis Engine', status: 'online', icon: Cpu },
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-green-400" />
            24/7 Monitoring
          </h1>
          <p className="text-slate-400 mt-1">Control and monitor the AI trading agent</p>
        </div>
        <div className="flex items-center gap-3">
          {!status.isRunning ? (
            <button
              onClick={handleStart}
              className="flex items-center gap-2 px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-xl font-medium transition-colors"
            >
              <Play className="w-5 h-5" />
              Start Monitoring
            </button>
          ) : (
            <>
              <button
                onClick={handlePause}
                className="flex items-center gap-2 px-4 py-3 bg-yellow-500 hover:bg-yellow-600 text-white rounded-xl font-medium transition-colors"
              >
                <Pause className="w-5 h-5" />
                Pause
              </button>
              <button
                onClick={handleStop}
                className="flex items-center gap-2 px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-xl font-medium transition-colors"
              >
                <Square className="w-5 h-5" />
                Stop
              </button>
            </>
          )}
        </div>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="w-5 h-5 text-blue-400" />
            <span className="text-slate-400 text-sm">Uptime</span>
          </div>
          <p className="text-2xl font-bold text-white font-mono">{uptime}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <RefreshCw className="w-5 h-5 text-yellow-400" />
            <span className="text-slate-400 text-sm">Active Tasks</span>
          </div>
          <p className="text-2xl font-bold text-white">{status.activeTasks}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span className="text-slate-400 text-sm">Completed</span>
          </div>
          <p className="text-2xl font-bold text-white">{status.completedTasks}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-slate-400 text-sm">Errors</span>
          </div>
          <p className="text-2xl font-bold text-white">{status.errors}</p>
        </div>
      </div>

      {/* Services status */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Service Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {services.map((service) => (
            <div key={service.name} className="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl">
              <service.icon className="w-5 h-5 text-slate-400" />
              <div className="flex-1">
                <p className="text-sm font-medium text-white">{service.name}</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs text-green-400 capitalize">{service.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Live logs */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Terminal className="w-5 h-5 text-purple-400" />
            Live Logs
          </h3>
          <button
            onClick={() => setLogs([])}
            className="text-sm text-slate-400 hover:text-white transition-colors"
          >
            Clear
          </button>
        </div>
        <div className="bg-slate-950 rounded-xl p-4 h-80 overflow-y-auto font-mono text-sm space-y-2">
          {logs.map((log) => (
            <div key={log.id} className="flex items-start gap-3">
              <span className="text-slate-500">[{log.timestamp}]</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${getLogBg(log.level)} ${getLogColor(log.level)}`}>
                {log.level.toUpperCase()}
              </span>
              <span className="text-slate-500">[{log.source}]</span>
              <span className="text-slate-300">{log.message}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <p className="text-slate-600 text-center py-8">No logs available</p>
          )}
        </div>
      </div>

      {/* Monitoring info */}
      <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">24/7 Automated Monitoring</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              When started, the AI agent continuously monitors markets, analyzes price action,
              detects liquidity zones, and generates trading signals. The system uses your
              configured API keys for real-time data and executes browser automation for
              web-based analysis.
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <span className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-400">Price Action</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-400">Liquidity Zones</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-400">Order Blocks</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-400">FVG Detection</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-400">Sentiment Analysis</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
