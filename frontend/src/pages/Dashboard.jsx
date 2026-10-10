import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import TopicCard from '../components/TopicCard'

const API = import.meta.env.VITE_API_URL

const TOPICS = [
  { key: 'linux', label: 'Linux', emoji: '🐧', color: 'bg-blue-600 hover:bg-blue-700' },
  { key: 'netwerk', label: 'TCP/IP Network', emoji: '🌐', color: 'bg-purple-600 hover:bg-purple-700' },
  { key: 'kubernetes', label: 'Kubernetes', emoji: '☸️', color: 'bg-green-700 hover:bg-green-800' },
  { key: 'trading', label: 'Trading Context', emoji: '📈', color: 'bg-orange-600 hover:bg-orange-700' },
  { key: 'performance', label: 'Performance', emoji: '⚡', color: 'bg-red-700 hover:bg-red-800' },
]

const INVESTIGATIONS = [
  { env: 'vm', topic: 'performance', label: '🔍 Investigation · VM', color: 'bg-red-800 hover:bg-red-900',
    detail: 'One Linux host: uptime, vmstat, iostat, ss, …' },
  { env: 'k8s', topic: 'kubernetes', label: '☸️ Investigation · Kubernetes', color: 'bg-green-800 hover:bg-green-900',
    detail: 'A cluster: kubectl, then ssh to a node or exec into a pod' },
  { env: 'mixed', topic: 'performance', label: '🎲 Investigation · Mixed', color: 'bg-indigo-800 hover:bg-indigo-900',
    detail: 'VM or Kubernetes, you find out when it starts' },
]

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => { load() }, [])

  async function load() {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/dashboard/`, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })
    setData(await res.json())
    setLoading(false)
  }

  // investigation: 'vm', 'k8s' or 'mixed' starts straight into an investigation; omitted for normal sessions.
  async function startSession(topic, level, investigation) {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
      body: JSON.stringify({ topic: topic || null, level: level || null })
    })
    const sessionData = await res.json()
    navigate('/session', { state: { ...sessionData, investigation } })
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-400">Loading...</p>
    </div>
  )

  const levels = data?.levels || {}
  const weak = data?.weak_subtopics || []

  return (
    <div className="min-h-screen bg-gray-950 p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-white text-2xl font-bold">TRE Coach</h1>
          <p className="text-gray-400 text-sm">Troubleshooting practice for trading systems</p>
        </div>
        <div className="flex gap-4 items-center">
          <button onClick={() => navigate('/learn')} className="text-blue-400 hover:text-blue-300 text-sm">
            📖 Learn
          </button>
          <button onClick={() => navigate('/coach')} className="text-blue-400 hover:text-blue-300 text-sm">
            English Coach
          </button>
          <button onClick={() => supabase.auth.signOut()} className="text-gray-400 hover:text-white text-sm">
            Sign out
          </button>
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl p-4 mb-6">
        <h2 className="text-white font-semibold mb-3">Your level</h2>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-2">
          {TOPICS.map(t => (
            <div key={t.key} className="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2 odd:last:col-span-2 lg:odd:last:col-span-1">
              <span className="text-gray-300 text-sm">{t.emoji} {t.label}</span>
              <span className={`text-xs font-bold px-2 py-1 rounded ${
                levels[t.key] === 'gemiddeld' ? 'bg-green-800 text-green-300' : 'bg-gray-700 text-gray-400'
              }`}>
                {levels[t.key] === 'gemiddeld' ? 'Intermediate' : 'Foundation'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {weak.length > 0 && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 mb-6">
          <p className="text-red-400 font-medium mb-1">Weak areas (&lt;70%)</p>
          <p className="text-gray-300 text-sm">{weak.map(w => w.subtopic.replace(/_/g, ' ')).join(', ')}</p>
        </div>
      )}

      <div className="mb-6">
        <h2 className="text-white font-semibold mb-3">Recommended</h2>
        <button
          onClick={() => startSession(null, null)}
          className="w-full bg-gray-700 hover:bg-gray-600 text-white p-4 rounded-xl font-medium text-left"
        >
          <span className="block text-white">🎯 Start recommended session</span>
          <span className="text-gray-400 text-sm">Weakest topic at your current level</span>
        </button>
      </div>

      <div className="mb-6">
        <h2 className="text-white font-semibold mb-1">Investigation</h2>
        <p className="text-gray-400 text-sm mb-3">A live incident: you only get the symptom, type up to 10 commands and see their output, then give your diagnosis.</p>
        <div className="grid gap-3 md:grid-cols-3">
          {INVESTIGATIONS.map(i => (
            <button
              key={i.env}
              onClick={() => startSession(i.topic, levels[i.topic] || 'basis', i.env)}
              className={`${i.color} text-white p-4 rounded-xl font-medium text-left`}
            >
              <span className="block">{i.label}</span>
              <span className="text-white/70 text-xs">{i.detail}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-white font-semibold mb-3">Choose topic</h2>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          {TOPICS.map(t => (
            <button
              key={t.key}
              onClick={() => startSession(t.key, levels[t.key] || 'basis')}
              className={`${t.color} text-white p-4 rounded-xl font-medium text-left odd:last:col-span-2 lg:odd:last:col-span-1`}
            >
              <span className="block">{t.emoji} {t.label}</span>
              <span className="text-white/70 text-xs">
                {levels[t.key] === 'gemiddeld' ? 'Intermediate' : 'Foundation'}
              </span>
            </button>
          ))}
        </div>
      </div>

      <h2 className="text-white font-semibold mb-3">Progress per topic</h2>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {(data?.scores || []).map(s => (
          <TopicCard key={s.subtopic} subtopic={s.subtopic} correct={s.correct_answers} total={s.total_answers} />
        ))}
        {(!data?.scores || data.scores.length === 0) && (
          <p className="text-gray-500 text-sm col-span-full">No sessions yet. Start your first session above!</p>
        )}
      </div>
    </div>
  )
}
