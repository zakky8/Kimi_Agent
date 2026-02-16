import { useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

// ==================== Settings ====================

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const { data } = await api.get('/config')
      return data
    },
  })
}

export function useSettingsSchema() {
  return useQuery({
    queryKey: ['settings', 'schema'],
    queryFn: async () => {
      const { data } = await api.get('/settings/schema')
      return data
    },
  })
}

export function useCurrentSettings() {
  return useQuery({
    queryKey: ['settings', 'current'],
    queryFn: async () => {
      const { data } = await api.get('/settings/current')
      return data
    },
  })
}

export function useUpdateSettings() {
  return useMutation({
    mutationFn: async ({ section, settings }: { section: string, settings: any }) => {
      const { data } = await api.post('/settings/update', { section, settings })
      return data
    },
  })
}

export function useTestConnection() {
  return useMutation({
    mutationFn: async (provider: string) => {
      const { data } = await api.post(`/settings/test-connection/${provider}`)
      return data
    },
  })
}

// ==================== Chat ====================

export function useChatSessions() {
  return useQuery({
    queryKey: ['chat', 'sessions'],
    queryFn: async () => {
      const { data } = await api.get('/chat/sessions')
      return data
    },
  })
}

export function useChatMessages(sessionId: string) {
  return useQuery({
    queryKey: ['chat', 'messages', sessionId],
    queryFn: async () => {
      const { data } = await api.get(`/chat/session/${sessionId}/messages`)
      return data
    },
    enabled: !!sessionId,
  })
}

export function useCreateChatSession() {
  return useMutation({
    mutationFn: async (title?: string) => {
      const { data } = await api.post('/chat/session/create', null, { params: { title } })
      return data
    },
  })
}

export function useSendMessage() {
  return useMutation({
    mutationFn: async ({ sessionId, content, imageUrl }: { sessionId: string, content: string, imageUrl?: string }) => {
      const { data } = await api.post('/chat/message', { session_id: sessionId, content, image_url: imageUrl })
      return data
    },
  })
}

export function useDeleteChatSession() {
  return useMutation({
    mutationFn: async (sessionId: string) => {
      const { data } = await api.delete(`/chat/session/${sessionId}`)
      return data
    },
  })
}

// ==================== Image Analysis ====================

export function useAnalyzeImage() {
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await api.post('/analysis/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return data
    },
  })
}

export function useChatWithImage() {
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await api.post('/chat/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return data
    },
  })
}

// ==================== Browser Research ====================

export function useStartResearch() {
  return useMutation({
    mutationFn: async ({ query, sources, maxResults }: { query: string, sources?: string[], maxResults?: number }) => {
      const { data } = await api.post('/research', { query, sources, max_results: maxResults })
      return data
    },
  })
}

export function useResearchStatus(taskId: string) {
  return useQuery({
    queryKey: ['research', 'status', taskId],
    queryFn: async () => {
      const { data } = await api.get(`/research/${taskId}/status`)
      return data
    },
    enabled: !!taskId,
    refetchInterval: 5000,
  })
}

export function useResearchSymbol() {
  return useMutation({
    mutationFn: async (symbol: string) => {
      const { data } = await api.post(`/research/symbol/${symbol}`)
      return data
    },
  })
}

// ==================== Market Data ====================

export function usePrice(symbol: string) {
  return useQuery({
    queryKey: ['price', symbol],
    queryFn: async () => {
      const { data } = await api.get(`/market/price/${symbol}`)
      return data
    },
    refetchInterval: 5000,
  })
}

export function useMultiplePrices(symbols: string[]) {
  return useQuery({
    queryKey: ['prices', symbols],
    queryFn: async () => {
      const { data } = await api.get(`/market/prices?symbols=${symbols.join(',')}`)
      return data
    },
    refetchInterval: 5000,
  })
}

export function useHistoricalData(symbol: string, timeframe: string = '1h', limit: number = 100) {
  return useQuery({
    queryKey: ['historical', symbol, timeframe, limit],
    queryFn: async () => {
      const { data } = await api.get(`/market/historical/${symbol}?timeframe=${timeframe}&limit=${limit}`)
      return data
    },
  })
}

export function useBinanceTopVolume(limit: number = 20) {
  return useQuery({
    queryKey: ['binance', 'top-volume', limit],
    queryFn: async () => {
      const { data } = await api.get(`/market/binance/top-volume?limit=${limit}`)
      return data
    },
    refetchInterval: 30000,
  })
}

// ==================== MT5 ====================

export function useMT5Status() {
  return useQuery({
    queryKey: ['mt5', 'status'],
    queryFn: async () => {
      const { data } = await api.get('/mt5/status')
      return data
    },
    refetchInterval: 10000,
  })
}

export function useMT5Account() {
  return useQuery({
    queryKey: ['mt5', 'account'],
    queryFn: async () => {
      const { data } = await api.get('/mt5/account')
      return data
    },
  })
}

export function useMT5Positions() {
  return useQuery({
    queryKey: ['mt5', 'positions'],
    queryFn: async () => {
      const { data } = await api.get('/mt5/positions')
      return data
    },
    refetchInterval: 5000,
  })
}

// ==================== Sentiment ====================

export function useSentiment(symbol: string) {
  return useQuery({
    queryKey: ['sentiment', symbol],
    queryFn: async () => {
      const { data } = await api.get(`/sentiment/${symbol}`)
      return data
    },
    refetchInterval: 60000,
  })
}

export function useRedditData(symbol: string) {
  return useQuery({
    queryKey: ['reddit', symbol],
    queryFn: async () => {
      const { data } = await api.get(`/social/reddit/${symbol}`)
      return data
    },
    refetchInterval: 300000,
  })
}

export function useTelegramData(symbol: string) {
  return useQuery({
    queryKey: ['telegram', symbol],
    queryFn: async () => {
      const { data } = await api.get(`/social/telegram/${symbol}`)
      return data
    },
    refetchInterval: 300000,
  })
}

// ==================== News & RSS ====================

export function useMarketNews() {
  return useQuery({
    queryKey: ['news', 'market'],
    queryFn: async () => {
      const { data } = await api.get('/news/market')
      return data
    },
    refetchInterval: 300000,
  })
}

export function useRSSSummary() {
  return useQuery({
    queryKey: ['news', 'rss', 'summary'],
    queryFn: async () => {
      const { data } = await api.get('/news/rss/summary')
      return data
    },
    refetchInterval: 300000,
  })
}

export function useSearchNews(query: string) {
  return useQuery({
    queryKey: ['news', 'search', query],
    queryFn: async () => {
      const { data } = await api.get(`/news/search?query=${query}`)
      return data
    },
    enabled: !!query,
  })
}

// ==================== Analysis ====================

export function useTechnicalAnalysis(symbol: string, timeframe: string = '1h') {
  return useQuery({
    queryKey: ['analysis', symbol, timeframe],
    queryFn: async () => {
      const { data } = await api.get(`/analysis/${symbol}?timeframe=${timeframe}`)
      return data
    },
    refetchInterval: 30000,
  })
}

// ==================== Signals ====================

export function useGenerateSignal(symbol: string, timeframe: string = '1h') {
  return useQuery({
    queryKey: ['signal', symbol, timeframe],
    queryFn: async () => {
      const { data } = await api.get(`/signals/generate/${symbol}?timeframe=${timeframe}`)
      return data
    },
    refetchInterval: 60000,
  })
}

export function useActiveSignals() {
  return useQuery({
    queryKey: ['signals', 'active'],
    queryFn: async () => {
      const { data } = await api.get('/signals/active')
      return data
    },
    refetchInterval: 30000,
  })
}

// ==================== Trading Pairs ====================

export function useTradingPairs() {
  return useQuery({
    queryKey: ['pairs'],
    queryFn: async () => {
      const { data } = await api.get('/pairs')
      return data
    },
  })
}
