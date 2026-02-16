import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Signal, 
  BarChart3, 
  MessageSquare, 
  Settings,
  TrendingUp,
  Activity,
  MessageCircle
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/signals', label: 'Signals', icon: Signal },
  { path: '/analysis', label: 'Analysis', icon: BarChart3 },
  { path: '/sentiment', label: 'Sentiment', icon: MessageSquare },
  { path: '/chat', label: 'AI Chat', icon: MessageCircle },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-card border-r border-border z-50 hidden lg:flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight">AI Trading</h1>
            <p className="text-xs text-muted-foreground">Agent Pro v2.0</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Status */}
      <div className="p-4 border-t border-border">
        <div className="glass rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-bull" />
            <span className="text-sm font-medium">System Status</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="w-2 h-2 rounded-full bg-bull animate-pulse" />
            <span>Connected to API</span>
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary/20 text-primary rounded">
              AI Ready
            </span>
          </div>
        </div>
      </div>
    </aside>
  )
}
