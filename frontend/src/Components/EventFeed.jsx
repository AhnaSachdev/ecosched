const ACTION_STYLES = {
  run:      "bg-green-50 text-green-700 border-green-200",
  throttle: "bg-amber-50 text-amber-700 border-amber-200",
  defer:    "bg-red-50 text-red-600 border-red-200"
}

export default function EventFeed({ events }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h2 className="text-sm font-medium text-gray-700">
          Live decisions
        </h2>
      </div>
      <div className="divide-y divide-gray-50 max-h-96 overflow-y-auto">
        {events.length === 0 && (
          <p className="text-sm text-gray-400 px-4 py-8 text-center">
            Waiting for first decision...
          </p>
        )}
        {events.map((e, i) => (
          <div key={i} className="px-4 py-3 flex items-start gap-3
                                   hover:bg-gray-50 transition-colors">
            <span className={`mt-0.5 text-xs px-2 py-0.5 rounded-full
                              border shrink-0
                              ${ACTION_STYLES[e.action] || ""}`}>
              {e.action}
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">
                {e.job_name}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {e.reasoning}
              </p>
              <p className="text-xs text-green-600 mt-0.5">
                +{(e.co2_saved || 0).toFixed(1)}g CO₂ saved
              </p>
            </div>
            <span className="text-xs text-gray-400 shrink-0 ml-auto">
              {e.carbon_ci} gCO₂/kWh
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}