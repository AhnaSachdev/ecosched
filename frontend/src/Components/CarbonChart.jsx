import { LineChart, Line, XAxis, YAxis,
         Tooltip, ResponsiveContainer, ReferenceLine } from "recharts"
import { useMemo } from "react"

export default function CarbonChart({ events }) {
  const data = useMemo(() =>
    events.slice(0,30).reverse().map((e,i) => ({
      t: i,
      ci: Math.round(e.carbon_ci || 0),
      action: e.action
    })), [events])

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs font-medium text-gray-600 mb-3">
        Grid carbon intensity (gCO₂/kWh)
      </p>
      <ResponsiveContainer width="100%" height={140}>
        <LineChart data={data}>
          <XAxis dataKey="t" hide />
          <YAxis domain={[0, 600]} width={32}
                 tick={{fontSize:10, fill:"#9ca3af"}} />
          <Tooltip
            contentStyle={{fontSize:11, borderRadius:6}}
            formatter={v => [`${v} gCO₂/kWh`, "Intensity"]} />
          <ReferenceLine y={300} stroke="#f59e0b"
                          strokeDasharray="3 3" label={{
                            value:"Defer threshold",
                            fontSize:9,fill:"#d97706"}} />
          <ReferenceLine y={150} stroke="#10b981"
                          strokeDasharray="3 3" />
          <Line type="monotone" dataKey="ci"
                stroke="#3b82f6" strokeWidth={2}
                dot={false} />
        </LineChart>
      </ResponsiveContainer>
      <div className="flex gap-3 mt-2">
        <span className="text-xs text-green-600">
          &lt;150 clean
        </span>
        <span className="text-xs text-amber-600">
          150–300 moderate
        </span>
        <span className="text-xs text-red-500">
          &gt;300 defer
        </span>
      </div>
    </div>
  )
}
