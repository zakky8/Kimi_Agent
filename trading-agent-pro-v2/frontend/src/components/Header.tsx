import { Menu, Bell, User, Moon, Sun } from 'lucide-react';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export default function Header({ sidebarOpen, setSidebarOpen }: HeaderProps) {
  const [darkMode, setDarkMode] = useState(true);
  const [notifications] = useState(3);

  // Fetch AI status for top bar
  const { data: healthData } = useQuery({
    queryKey: ['system-health-header'],
    queryFn: async () => {
      const res = await axios.get('/api/v1/health');
      return res.data;
    },
    refetchInterval: 30000,
  });

  const aiActive = healthData?.ai_connected || false;

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-xl border-b border-slate-800 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden md:flex items-center gap-2 text-sm text-slate-400">
          <span className={`w-2 h-2 rounded-full animate-pulse ${aiActive ? 'bg-green-500' : 'bg-red-500'}`} />
          <span>AI Agent {aiActive ? 'Active' : 'Offline'}</span>
          <span className="text-slate-600">|</span>
          <span>Monitoring 24/7</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Dark mode toggle */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors">
          <Bell className="w-5 h-5" />
          {notifications > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center text-white font-bold">
              {notifications}
            </span>
          )}
        </button>

        {/* User menu */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-white">Trader</p>
            <p className="text-xs text-slate-400">Pro Account</p>
          </div>
          <button className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center hover:opacity-90 transition-opacity">
            <User className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </header>
  );
}
