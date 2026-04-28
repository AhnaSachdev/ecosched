import { useState } from "react"
import axios from "axios"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

export default function JobSubmitForm() {
  const [form, setForm] = useState({
    name: "", urgency: 2, deadline_minutes: 60, description: ""
  })
  const [status, setStatus] = useState("")

  async function handleSubmit() {
    if (!form.name) return
    try {
      const r = await axios.post(API + "/api/jobs", {
        job_id: Date.now().toString(),   
        name: form.name,
        urgency: form.urgency,
        deadline_seconds: form.deadline_minutes * 60,  
        pid: null
      })
    } catch {
      setStatus("Error submitting job")
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs font-medium text-gray-600 mb-3">
        Submit batch job
      </p>
      <div className="space-y-2">
        <input
          placeholder="Job name (e.g. nightly-backup)"
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
          className="w-full text-sm border border-gray-200 rounded-lg
                     px-3 py-2 focus:outline-none focus:ring-1
                     focus:ring-blue-400" />
        <div className="flex gap-2">
          <select value={form.urgency}
            onChange={e =>
              setForm({ ...form, urgency: +e.target.value })}
            className="flex-1 text-sm border border-gray-200
                             rounded-lg px-2 py-2">
            <option value={1}>Urgency 1 — batch</option>
            <option value={2}>Urgency 2 — low</option>
            <option value={3}>Urgency 3 — medium</option>
            <option value={4}>Urgency 4 — high</option>
            <option value={5}>Urgency 5 — critical</option>
          </select>
          <input type="number" value={form.deadline_minutes}
            onChange={e =>
              setForm({ ...form, deadline_minutes: +e.target.value })}
            className="w-20 text-sm border border-gray-200
                            rounded-lg px-2 py-2" />
        </div>
        <button onClick={handleSubmit}
          className="w-full text-sm bg-gray-900 text-white
                           rounded-lg py-2 hover:bg-gray-700
                           transition-colors">
          Submit job
        </button>
        {status && (
          <p className="text-xs text-gray-500">{status}</p>
        )}
      </div>
    </div>
  )
}