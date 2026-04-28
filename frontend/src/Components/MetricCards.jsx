export default function MetricCards({ stats }) {
  const cards = [
    { label: "CO₂ saved", value: stats
        ? (stats.total_co2_saved_grams/1000).toFixed(2) + " kg"
        : "—", color: "text-green-600" },
    { label: "Total decisions", value: stats
        ? stats.total_decisions : "—", color: "text-blue-600" },
    { label: "Grid intensity", value: stats
        ? (stats.last_carbon_ci || "—") + " gCO₂/kWh" : "—",
      color: "text-amber-600" },
    { label: "System", value: "Active", color: "text-gray-600" }
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(c => (
        <div key={c.label}
             className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">{c.label}</p>
          <p className={`text-2xl font-medium ${c.color}`}>{c.value}</p>
        </div>
      ))}
    </div>
  )
}