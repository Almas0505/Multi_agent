import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './pages/HomePage'
import { AnalysisPage } from './pages/AnalysisPage'
import { ReportsPage } from './pages/ReportsPage'
import { ReportDetailPage } from './pages/ReportDetailPage'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/analysis" element={<AnalysisPage />} />
        <Route path="/analysis/:taskId" element={<AnalysisPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/reports/:reportId" element={<ReportDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}
