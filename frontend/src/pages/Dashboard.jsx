import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import TopicCard from '../components/TopicCard'

const API = import.meta.env.VITE_API_URL

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    async function load() {
      const { data: { session } } = await supabase.auth.getSession()
      const res = await fetch(`${API}/dashboard/`, {
        headers: { Authorization: `Bearer ${session.access_token}` }
      })
      setData(await res.json())
      setLoading(false)
    }
    load()
  }, [])

  async function startSession(topic) {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
      body: JSON.stringify({ topic })
    })
    const sessionData = await res.json()
    navigate('/session', { state: sessionData })
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-400">Laden...</p>
    </div>
  )

  const weak = data?.weak_subtopics || []

  return (
    <div className="min-h-screen bg-gray-950 p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-white text-2xl font-bold">TRE Coach</h1>
        <button onClick={() => supabase.auth.signOut()} className="text-gray-400 hover:text-white text-sm">Uitloggen</button>
      </div>

      {weak.length > 0 && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 mb-6">
          <p className="text-red-400 font-medium mb-1">Zwakke plekken (&lt;70%)</p>
          <p className="text-gray-300 text-sm">{weak.map(w => w.subtopic.replace(/_/g, ' ')).join(', ')}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 mb-8">
        <button onClick={() => startSession('linux')} className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-xl font-medium">
          Linux oefenen
        </button>
        <button onClick={() => startSession('netwerk')} className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-xl font-medium">
          Netwerk oefenen
        </button>
        <button onClick={() => startSession(null)} className="col-span-2 bg-gray-700 hover:bg-gray-600 text-white p-4 rounded-xl font-medium">
          Laat app kiezen (zwakste plek)
        </button>
      </div>

      <h2 className="text-white font-semibold mb-3">Voortgang per onderwerp</h2>
      <div className="space-y-3">
        {(data?.scores || []).map(s => (
          <TopicCard key={s.subtopic} subtopic={s.subtopic} correct={s.correct_answers} total={s.total_answers} />
        ))}
        {data?.scores?.length === 0 && <p className="text-gray-500 text-sm">Nog geen sessies gedaan.</p>}
      </div>
    </div>
  )
}
