import { useEcoSched } from "./hooks/useEcoSched"
import MetricCards from "./Components/MetricCards"
import EventFeed from "./Components/EventFeed"
import CarbonChart from "./Components/CarbonChart"
import JobSubmitForm from "./Components/JobSubmitForm"

export default function App() {
  const { events, stats, connected } = useEcoSched(
    import.meta.env.VITE_API_URL || "http://localhost:8000"
  )

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <header className="bg-white border-b border-gray-200 px-6 py-4
                         flex items-center justify-between">
        <div>
          <h1 className="text-lg font-medium text-gray-900">EcoSched</h1>
          <p className="text-xs text-gray-500">
            Carbon-aware AI scheduler
          </p>
        </div>
        <span className={`text-xs px-3 py-1 rounded-full border
          ${connected
            ? "bg-green-50 text-green-700 border-green-200"
            : "bg-red-50 text-red-600 border-red-200"}`}>
          {connected ? "Live" : "Disconnected"}
        </span>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        <MetricCards stats={stats} />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <EventFeed events={events} />
          </div>
          <div className="space-y-4">
            <CarbonChart events={events} />
            <JobSubmitForm />
          </div>
        </div>
      </main>
    </div>
  )
}