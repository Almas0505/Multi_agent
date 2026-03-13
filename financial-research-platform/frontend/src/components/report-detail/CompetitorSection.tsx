import { Globe, Shield, Users } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { RatingBadge } from '../reports/RatingBadge'
import type { CompetitorData } from '../../types/report'

interface CompetitorSectionProps {
  data: CompetitorData
}

export function CompetitorSection({ data }: CompetitorSectionProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-purple-400" />
              <CardTitle>Competitive Landscape</CardTitle>
            </div>
            <RatingBadge rating={data.rating} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm text-slate-400">Market Position:</span>
            <span className="text-sm font-semibold text-slate-200 capitalize">
              {data.competitive_position}
            </span>
          </div>

          {data.competitors && data.competitors.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-2">Key Competitors</p>
              <div className="flex flex-wrap gap-2">
                {data.competitors.map((ticker) => (
                  <Badge key={ticker} variant="neutral" className="font-mono text-sm px-3 py-1">
                    {ticker}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {data.moat_analysis && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-400" />
              <CardTitle>Economic Moat Analysis</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">{data.moat_analysis}</p>
          </CardContent>
        </Card>
      )}

      {data.analysis_text && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-slate-400" />
              <CardTitle>Competitor Analysis</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">{data.analysis_text}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
