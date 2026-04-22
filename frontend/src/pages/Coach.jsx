import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const API = import.meta.env.VITE_API_URL

const CATEGORY_COLORS = {
  Grammar: '#818cf8',
  Vocabulary: '#34d399',
  Structure: '#fb923c',
  Fluency: '#f472b6',
}

export default function Coach() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => { load() }, [])

  async function load() {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/coach/`, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })
    setData(await res.json())
    setLoading(false)
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-400">Loading...</p>
    </div>
  )

  const trendData = (data?.trends || []).map((t, i) => ({
    session: `S${i + 1}`,
    Grammar: t.grammar_avg,
    Vocabulary: t.vocabulary_avg,
    Structure: t.structure_avg,
    Fluency: t.fluency_avg,
  }))

  const weakest = data?.weakest_category
  const weakestLabel = weakest ? weakest.charAt(0).toUpperCase() + weakest.slice(1) : null

  return (
    <div className="min-h-screen bg-gray-950 p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-white text-2xl font-bold">English Coach</h1>
          <p className="text-gray-400 text-sm">Your language progress over time</p>
        </div>
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white text-sm">
          ← Dashboard
        </button>
      </div>

      {trendData.length < 2 ? (
        <div className="bg-gray-900 rounded-xl p-6 mb-6 text-center">
          <p className="text-gray-400">Complete at least 2 sessions to see your trend lines.</p>
        </div>
      ) : (
        <div className="bg-gray-900 rounded-xl p-4 mb-6">
          <h2 className="text-white font-semibold mb-4">Score trends</h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trendData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <XAxis dataKey="session" stroke="#6b7280" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 10]} stroke="#6b7280" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                labelStyle={{ color: '#d1d5db' }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {Object.entries(CATEGORY_COLORS).map(([key, color]) => (
                <Line key={key} type="monotone" dataKey={key} stroke={color} strokeWidth={2} dot={{ r: 3 }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {weakestLabel && (
        <div className="bg-indigo-900/20 border border-indigo-700/50 rounded-xl p-4 mb-6">
          <p className="text-indigo-300 font-medium mb-1">
            Focus area: <span style={{ color: CATEGORY_COLORS[weakestLabel] }}>{weakestLabel}</span>
          </p>
          <p className="text-gray-300 text-sm">{data.recommendation}</p>
        </div>
      )}

      {(data?.recent_answers || []).length === 0 ? (
        <div className="bg-gray-900 rounded-xl p-6 text-center">
          <p className="text-gray-400">No English answers recorded yet. Complete a session to get started.</p>
        </div>
      ) : (
        <div>
          <h2 className="text-white font-semibold mb-3">Recent answers</h2>
          <div className="space-y-3">
            {(data.recent_answers || []).map((a) => (
              <div key={a.id} className="bg-gray-900 rounded-xl p-4 space-y-2">
                <p className="text-gray-400 text-xs uppercase tracking-wide">
                  {new Date(a.created_at).toLocaleDateString('en-GB')}
                </p>
                <p className="text-gray-300 text-sm font-medium">{a.question}</p>
                <p className="text-gray-500 text-xs italic">"{a.user_answer}"</p>
                <div className="flex gap-3">
                  {[
                    { label: 'Grammar', score: a.grammar_score },
                    { label: 'Vocab', score: a.vocabulary_score },
                    { label: 'Structure', score: a.structure_score },
                    { label: 'Fluency', score: a.fluency_score },
                  ].map(({ label, score }) => (
                    <span key={label} className={`text-xs px-2 py-1 rounded-full ${
                      score >= 7 ? 'bg-green-900/40 text-green-300' :
                      score >= 5 ? 'bg-yellow-900/40 text-yellow-300' :
                      'bg-red-900/40 text-red-300'
                    }`}>
                      {label} {score ?? '–'}
                    </span>
                  ))}
                </div>
                {a.english_tips && (
                  <p className="text-indigo-300 text-xs">💡 {a.english_tips}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
