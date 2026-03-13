import { useState, type FormEvent } from 'react'
import { Search } from 'lucide-react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { ErrorAlert } from '../ui/ErrorAlert'

interface TickerSearchFormProps {
  onSubmit: (ticker: string) => void
  loading?: boolean
  error?: string | null
}

export function TickerSearchForm({ onSubmit, loading = false, error }: TickerSearchFormProps) {
  const [ticker, setTicker] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const cleaned = ticker.trim().toUpperCase()
    if (!cleaned) return
    onSubmit(cleaned)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex gap-3">
        <div className="flex-1">
          <Input
            placeholder="e.g. AAPL, MSFT, GOOGL"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            disabled={loading}
            maxLength={10}
            autoFocus
            aria-label="Stock ticker symbol"
          />
        </div>
        <Button
          type="submit"
          variant="primary"
          size="md"
          loading={loading}
          disabled={!ticker.trim()}
          className="shrink-0"
        >
          <Search className="h-4 w-4" />
          Analyze
        </Button>
      </div>
      {error && (
        <ErrorAlert message={error} />
      )}
    </form>
  )
}
