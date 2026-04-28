import { useState, useEffect, useRef } from "react"

export function useEcoSched(apiBase = "http://localhost:8000") {
  const [events, setEvents]     = useState([])
  const [stats, setStats]       = useState(null)
  const [connected, setConnected] = useState(false)
  const ws = useRef(null)

  useEffect(() => {
    const wsUrl = apiBase.replace("http","ws") + "/ws"
    ws.current = new WebSocket(wsUrl)

    ws.current.onopen  = () => setConnected(true)
    ws.current.onclose = () => setConnected(false)
    ws.current.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === "decision") {
        setEvents(prev => [data, ...prev].slice(0, 50))
        setStats(s => ({
          ...s,
          total_co2_saved_grams: data.total_co2_saved,
          last_carbon_ci: data.carbon_ci
        }))
      }
    }
    fetch(apiBase + "/api/stats")
      .then(r => r.json()).then(setStats)

    return () => ws.current?.close()
  }, [apiBase])

  return { events, stats, connected }
}