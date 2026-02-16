import { useState, useEffect } from 'react'
import { Bell, Search, Menu, Wifi, WifiOff } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'

export function Header() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { connected } = useWebSocket()

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm flex items-center justify-between px-6">
      {/* Mobile menu button */}
      <button
        className="lg:hidden p-2 hover:bg-accent rounded-lg"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Search */}
      <div className="hidden md:flex items-center gap-2 bg-accent rounded-lg px-4 py-2 w-96">
        <Search className="w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search symbols, signals, or analysis..."
          className="bg-transparent border-none outline-none text-sm w-full placeholder:text-muted-foreground"
        />
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Connection status */}
        <div className="flex items-center gap-2 text-sm">
          {connected ? (
            <>
              <Wifi className="w-4 h-4 text-bull" />
              <span className="text-bull hidden sm:inline">Live</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-bear" />
              <span className="text-bear hidden sm:inline">Offline</span>
            </>
          )}
        </div>

        {/* Time */}
        <div className="text-sm text-muted-foreground hidden sm:block">
          {currentTime.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
          })}
        </div>

        {/* Notifications */}
        <button className="relative p-2 hover:bg-accent rounded-lg">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-primary rounded-full" />
        </button>
      </div>
    </header>
  )
}
