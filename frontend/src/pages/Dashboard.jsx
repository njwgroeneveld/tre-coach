import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import TopicCard from '../components/TopicCard'

const API = import.meta.env.VITE_API_URL

const TOPICS = [
  { key: 'linux', label: 'Linux', emoji: '🐧', color: 'bg-blue-600 hover:bg-blue-700' },
  { key: 'netwerk', label: 'TCP/IP Netwerk', emoji: '🌐', color: 'bg-purple-600 hover:bg-purple-700' },
  { key: 'kubernetes', label: 'Kubernetes', emoji: '☸️', color: 'bg-green-700 hover:bg-green-800' },
  { key: 'trading', label: 'Trading Context', emoji: '📈', color: 'bg-orange-600 hover:bg-orange-700' },
]

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    load()
  }, [])

  async function load() {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/dashboard/`, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })
    setData(await res.json())
    setLoading(false)
  }

  async function startSession(topic, level) {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
      body: JSON.stringify({ topic: topic || null, level: level || null })
    })
    const sessionData = await res.json()
    navigate('/session', { state: sessionData })
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-400">Laden...</p>
    </div>
  )

  const levels = data?.levels || {}
  const weak = data?.weak_subtopics || []

  return (
    <div className="min-h-screen bg-gray-950 p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-white text-2xl font-bold">TRE Coach</h1>
          <p className="text-gray-400 text-sm">IMC Trading voorbereiding</p>
        </div>
        <button onClick={() => supabase.auth.signOut()} className="text-gray-400 hover:text-white text-sm">
          Uitloggen
        </button>
      </div>

      {/* Niveau overzicht */}
      <div className="bg-gray-900 rounded-xl p-4 mb-6">
        <h2 className="text-white font-semibold mb-3">Jouw niveau</h2>
        <div className="grid grid-cols-2 gap-2">
          {TOPICS.map(t => (
            <div key={t.key} className="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2">
              <span className="text-gray-300 text-sm">{t.emoji} {t.label}</span>
              <span className={`text-xs font-bold px-2 py-1 rounded ${
                levels[t.key] === 'gemiddeld' ? 'bg-green-800 text-green-300' : 'bg-gray-700 text-gray-400'
              }`}>
                {levels[t.key] === 'gemiddeld' ? 'Gemiddeld' : 'Basis'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Zwakke plekken */}
      {weak.length > 0 && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 mb-6">
          <p className="text-red-400 font-medium mb-1">Aandachtspunten (&lt;70%)</p>
          <p className="text-gray-300 text-sm">{weak.map(w => w.subtopic.replace(/_/g, ' ')).join(', ')}</p>
        </div>
      )}

      {/* App stelt voor */}
      <div className="mb-6">
        <h2 className="text-white font-semibold mb-3">App stelt voor</h2>
        <button
          onClick={() => startSession(null, null)}
          className="w-full bg-gray-700 hover:bg-gray-600 text-white p-4 rounded-xl font-medium text-left"
        >
          <span className="block text-white">🎯 Start aanbevolen sessie</span>
          <span className="text-gray-400 text-sm">Zwakste onderwerp op jouw huidige niveau</span>
        </button>
      </div>

      {/* Zelf kiezen */}
      <div className="mb-8">
        <h2 className="text-white font-semibold mb-3">Zelf kiezen</h2>
        <div className="grid grid-cols-2 gap-3">
          {TOPICS.map(t => (
            <button
              key={t.key}
              onClick={() => startSession(t.key, levels[t.key] || 'basis')}
              className={`${t.color} text-white p-4 rounded-xl font-medium text-left`}
            >
              <span className="block">{t.emoji} {t.label}</span>
              <span className="text-white/70 text-xs">
                {levels[t.key] === 'gemiddeld' ? 'Gemiddeld' : 'Basis'}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Voortgang */}
      <h2 className="text-white font-semibold mb-3">Voortgang per onderwerp</h2>
      <div className="space-y-3">
        {(data?.scores || []).map(s => (
          <TopicCard key={s.subtopic} subtopic={s.subtopic} correct={s.correct_answers} total={s.total_answers} />
        ))}
        {(!data?.scores || data.scores.length === 0) && (
          <p className="text-gray-500 text-sm">Nog geen sessies gedaan. Start je eerste sessie hierboven!</p>
        )}
      </div>
    </div>
  )
}
