import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Signals from './pages/Signals';
import Analysis from './pages/Analysis';
import Calendar from './pages/Calendar';
import Monitoring from './pages/Monitoring';
import Settings from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 3,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="chat" element={<Chat />} />
            <Route path="signals" element={<Signals />} />
            <Route path="analysis" element={<Analysis />} />
            <Route path="calendar" element={<Calendar />} />
            <Route path="monitoring" element={<Monitoring />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
