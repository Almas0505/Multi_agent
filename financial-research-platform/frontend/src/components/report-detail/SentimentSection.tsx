import { Newspaper, Users, TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { SentimentMeter } from '../charts/SentimentMeter'
import { RatingBadge } from '../reports/RatingBadge'
import { Badge } from '../ui/Badge'
import { formatCurrency } from '../../utils/formatters'
import type { SentimentData } from '../../types/report'

interface SentimentSectionProps {
  data: SentimentData
}

export function SentimentSection({ data }: SentimentSectionProps) {
  const consensus = data.analyst_consensus

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sentiment Score */}
        <Card className="flex flex-col items-center py-8">
          <SentimentMeter score={data.sentiment_score} label={data.sentiment_label} />
          <p className="mt-3 text-sm text-slate-400">
            Based on {data.news_count} news articles
          </p>
          <div className="mt-4">
            <RatingBadge rating={data.rating} />
          </div>
        </Card>

        {/* Analyst Consensus */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-400" />
              <CardTitle>Analyst Consensus</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {consensus ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Consensus</span>
                  <Badge variant={consensus.consensus === 'BUY' ? 'success' : consensus.consensus === 'SELL' ? 'danger' : 'warning'}>
                    {consensus.consensus}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Average Target</span>
                  <span className="text-sm font-semibold text-slate-200">
                    {formatCurrency(consensus.average_target)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Number of Analysts</span>
                  <span className="text-sm font-semibold text-slate-200">
                    {consensus.num_analysts}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No analyst data available</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* News Headlines */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Newspaper className="h-5 w-5 text-slate-400" />
            <CardTitle>Notable Headlines</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.top_positive_headline && (
              <div className="flex items-start gap-3 rounded-lg bg-green-500/10 border border-green-500/20 p-3">
                <TrendingUp className="h-4 w-4 text-green-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs text-green-400 font-medium mb-1">Most Positive</p>
                  <p className="text-sm text-slate-300">{data.top_positive_headline}</p>
                </div>
              </div>
            )}
            {data.top_negative_headline && (
              <div className="flex items-start gap-3 rounded-lg bg-red-500/10 border border-red-500/20 p-3">
                <TrendingDown className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs text-red-400 font-medium mb-1">Most Negative</p>
                  <p className="text-sm text-slate-300">{data.top_negative_headline}</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Insider Activity */}
      {data.insider_activity && (
        <Card>
          <CardHeader>
            <CardTitle>Insider Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-400">Sentiment:</span>
              <span className="text-sm font-semibold text-slate-200 capitalize">
                {data.insider_activity.sentiment.replace(/_/g, ' ')}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {data.analysis_text && (
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">{data.analysis_text}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
