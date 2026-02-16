import { useState } from 'react'
import { MessageSquare, Twitter, MessageCircle, TrendingUp, TrendingDown, Users, ThumbsUp } from 'lucide-react'
import { useSentiment, useTwitterData, useRedditData, useMarketNews } from '../hooks/useApi'
import { SentimentGauge } from '../components/SentimentGauge'

const SYMBOLS = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'EURUSD', 'GBPUSD', 'XAUUSD']

export function Sentiment() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSD')
  
  const { data: sentiment, isLoading: sentimentLoading } = useSentiment(selectedSymbol)
  const { data: twitterData, isLoading: twitterLoading } = useTwitterData(selectedSymbol)
  const { data: redditData, isLoading: redditLoading } = useRedditData(selectedSymbol)
  const { data: newsData, isLoading: newsLoading } = useMarketNews()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Sentiment Analysis</h1>
          <p className="text-muted-foreground">Social media and news sentiment tracking</p>
        </div>
        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="px-4 py-2 bg-accent rounded-lg border border-border outline-none focus:border-primary"
        >
          {SYMBOLS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* Overall Sentiment */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass rounded-xl p-6 text-center">
          <h3 className="text-lg font-semibold mb-4">Overall Sentiment</h3>
          <SentimentGauge 
            value={sentiment?.overall_score || 0} 
            size="lg"
          />
          <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
            <div className="p-2 bg-bull/10 rounded">
              <p className="text-bull font-bold">{sentiment?.source_breakdown?.reduce((acc: number, s: any) => acc + (s.bullish_count || 0), 0) || 0}</p>
              <p className="text-muted-foreground text-xs">Bullish</p>
            </div>
            <div className="p-2 bg-neutral/10 rounded">
              <p className="font-bold">{sentiment?.source_breakdown?.reduce((acc: number, s: any) => acc + (s.neutral_count || 0), 0) || 0}</p>
              <p className="text-muted-foreground text-xs">Neutral</p>
            </div>
            <div className="p-2 bg-bear/10 rounded">
              <p className="text-bear font-bold">{sentiment?.source_breakdown?.reduce((acc: number, s: any) => acc + (s.bearish_count || 0), 0) || 0}</p>
              <p className="text-muted-foreground text-xs">Bearish</p>
            </div>
          </div>
        </div>

        {/* Twitter Sentiment */}
        <div className="glass rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Twitter className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold">Twitter/X</h3>
          </div>
          
          {twitterLoading ? (
            <div className="animate-pulse space-y-3">
              <div className="h-8 bg-accent rounded" />
              <div className="h-8 bg-accent rounded" />
            </div>
          ) : twitterData ? (
            <div className="space-y-3">
              <SentimentGauge value={twitterData.sentiment_score || 0} size="sm" showLabels={false} />
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="p-2 bg-accent/50 rounded">
                  <p className="text-muted-foreground text-xs">Tweets</p>
                  <p className="font-bold">{twitterData.total_tweets?.toLocaleString()}</p>
                </div>
                <div className="p-2 bg-accent/50 rounded">
                  <p className="text-muted-foreground text-xs">Engagement</p>
                  <p className="font-bold">{twitterData.engagement?.toLocaleString()}</p>
                </div>
              </div>
              {twitterData.top_hashtags && (
                <div className="flex flex-wrap gap-1">
                  {twitterData.top_hashtags.slice(0, 5).map(([tag, count]: [string, number], idx: number) => (
                    <span key={idx} className="px-2 py-0.5 bg-accent rounded text-xs">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">No Twitter data available</p>
          )}
        </div>

        {/* Reddit Sentiment */}
        <div className="glass rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <MessageCircle className="w-5 h-5 text-orange-500" />
            <h3 className="font-semibold">Reddit</h3>
          </div>
          
          {redditLoading ? (
            <div className="animate-pulse space-y-3">
              <div className="h-8 bg-accent rounded" />
              <div className="h-8 bg-accent rounded" />
            </div>
          ) : redditData ? (
            <div className="space-y-3">
              <SentimentGauge value={redditData.sentiment_score || 0} size="sm" showLabels={false} />
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="p-2 bg-accent/50 rounded">
                  <p className="text-muted-foreground text-xs">Posts</p>
                  <p className="font-bold">{redditData.total_posts?.toLocaleString()}</p>
                </div>
                <div className="p-2 bg-accent/50 rounded">
                  <p className="text-muted-foreground text-xs">Upvotes</p>
                  <p className="font-bold">{redditData.total_upvotes?.toLocaleString()}</p>
                </div>
              </div>
              {redditData.top_discussions && (
                <div className="space-y-1">
                  {redditData.top_discussions.slice(0, 3).map((post: any, idx: number) => (
                    <a 
                      key={idx}
                      href={post.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs text-muted-foreground hover:text-primary truncate"
                    >
                      r/{post.subreddit}: {post.title}
                    </a>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">No Reddit data available</p>
          )}
        </div>
      </div>

      {/* Fear & Greed Index */}
      <div className="glass rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4">Fear & Greed Index</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-accent/50 rounded-lg">
            <p className="text-sm text-muted-foreground mb-2">Crypto Market</p>
            <div className="flex items-center gap-4">
              <div className="w-24 h-24 rounded-full border-4 border-primary flex items-center justify-center">
                <span className="text-2xl font-bold">{newsData?.fear_greed?.crypto?.index || 50}</span>
              </div>
              <div>
                <p className="text-lg font-medium">{newsData?.fear_greed?.crypto?.sentiment || 'Neutral'}</p>
                <p className="text-sm text-muted-foreground">Last updated: {newsData?.fear_greed?.crypto?.timestamp ? new Date(newsData.fear_greed.crypto.timestamp * 1000).toLocaleTimeString() : 'N/A'}</p>
              </div>
            </div>
          </div>
          <div className="p-4 bg-accent/50 rounded-lg">
            <p className="text-sm text-muted-foreground mb-2">Stock Market</p>
            <div className="flex items-center gap-4">
              <div className="w-24 h-24 rounded-full border-4 border-primary flex items-center justify-center">
                <span className="text-2xl font-bold">{newsData?.fear_greed?.stocks?.index || 50}</span>
              </div>
              <div>
                <p className="text-lg font-medium">{newsData?.fear_greed?.stocks?.sentiment || 'Neutral'}</p>
                <p className="text-sm text-muted-foreground">Source: {newsData?.fear_greed?.stocks?.source || 'N/A'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Latest News */}
      <div className="glass rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4">Latest News</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {newsLoading ? (
            [1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-24 bg-accent animate-pulse rounded-lg" />
            ))
          ) : (
            newsData?.latest_news?.slice(0, 9).map((item: any, idx: number) => (
              <a
                key={idx}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-4 bg-accent/50 rounded-lg hover:bg-accent transition-colors"
              >
                <h4 className="font-medium line-clamp-2 mb-2">{item.title}</h4>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="capitalize">{item.source}</span>
                  <span>•</span>
                  <span>{new Date(item.published).toLocaleTimeString()}</span>
                </div>
              </a>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
