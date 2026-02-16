import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Signal, 
  BarChart3, 
  Settings, 
  Brain,
  Globe,
  TrendingUp,
  Calendar,
  Bot
} from 'lucide-react';

interface SidebarProps {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/chat', icon: MessageSquare, label: 'AI Chat' },
  { path: '/signals', icon: Signal, label: 'Signals' },
  { path: '/analysis', icon: BarChart3, label: 'Analysis' },
  { path: '/calendar', icon: Calendar, label: 'Forex Calendar' },
  { path: '/monitoring', icon: Bot, label: 'Monitoring' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar({ open, setOpen }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {!open && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setOpen(true)}
        />
      )}
      
      <aside 
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-64 bg-slate-900 border-r border-slate-800
          transform transition-transform duration-300 ease-in-out
          ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-20 xl:w-64'}
          flex flex-col
        `}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div className={`${open ? 'block' : 'hidden xl:block'}`}>
              <h1 className="text-lg font-bold text-white">TradeAgent</h1>
              <p className="text-xs text-slate-400">Pro v2.0</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-xl
                transition-all duration-200 group
                ${isActive 
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }
              `}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <span className={`${open ? 'block' : 'hidden xl:block'} font-medium`}>
                {item.label}
              </span>
            </NavLink>
          ))}
        </nav>

        {/* Status */}
        <div className="p-4 border-t border-slate-800">
          <div className={`${open ? 'block' : 'hidden xl:block'} space-y-3`}>
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-slate-400">System Online</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Globe className="w-4 h-4 text-blue-400" />
              <span className="text-slate-400">24/7 Monitoring</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-400" />
              <span className="text-slate-400">AI Active</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
