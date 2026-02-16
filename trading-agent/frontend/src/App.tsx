import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Signals } from './pages/Signals'
import { Analysis } from './pages/Analysis'
import { Sentiment } from './pages/Sentiment'
import { Chat } from './pages/Chat'
import { Settings } from './pages/Settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/signals" element={<Signals />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/sentiment" element={<Sentiment />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
