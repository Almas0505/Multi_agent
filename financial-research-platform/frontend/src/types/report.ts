export type ReportStatus = 'pending' | 'running' | 'completed' | 'failed' | 'error'
export type Rating = 'BUY' | 'SELL' | 'HOLD' | 'STRONG_BUY' | 'STRONG_SELL'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type TrendLabel = 'BULLISH' | 'BEARISH' | 'NEUTRAL'
export type SentimentLabel = 'BULLISH' | 'BEARISH' | 'NEUTRAL'

export interface FundamentalsData {
  pe_ratio: number
  pb_ratio: number
  ev_ebitda: number
  revenue_growth: number
  net_margin: number
  free_cash_flow: number
  debt_equity: number
  roe: number
  dcf_fair_value: number
  analysis_text: string
  rating: Rating
  sec_summary: string
}

export interface InsiderActivity {
  sentiment: string
}

export interface AnalystConsensus {
  consensus: string
  average_target: number
  num_analysts: number
}

export interface SentimentData {
  sentiment_score: number
  sentiment_label: SentimentLabel
  news_count: number
  top_positive_headline: string
  top_negative_headline: string
  insider_activity: InsiderActivity
  analyst_consensus: AnalystConsensus
  analysis_text: string
  rating: Rating
}

export interface TechnicalData {
  trend: TrendLabel
  rsi: number
  macd: number
  signal_line: number
  bb_upper: number
  bb_lower: number
  bb_middle: number
  sma20: number
  sma50: number
  support: number
  resistance: number
  analysis_text: string
  rating: Rating
}

export interface CompetitorData {
  competitors: string[]
  competitive_position: string
  moat_analysis: string
  analysis_text: string
  rating: Rating
}

export interface RiskData {
  risk_score: number
  risk_level: RiskLevel
  beta: number
  var_95: number
  max_drawdown: number
  volatility: number
  sharpe_ratio: number
  key_risks: string[]
  analysis_text: string
  rating: Rating
}

export interface FinalAnalysis {
  final_rating: Rating
  composite_score: number
  confidence_score: number
  executive_summary: string
  target_price: number
  key_catalysts: string[]
  key_risks: string[]
}

export interface ReportData {
  fundamentals?: FundamentalsData
  sentiment?: SentimentData
  technical?: TechnicalData
  competitor?: CompetitorData
  risk?: RiskData
  final_analysis?: FinalAnalysis
}

export interface ReportResponse {
  id: string
  ticker: string
  status: ReportStatus
  created_at: string
  pdf_url: string
  errors: string[]
  data: ReportData
}
