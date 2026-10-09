import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'

const API = import.meta.env.VITE_API_URL

const PARTS = [
  { kind: 'purpose', step: 1, label: 'What does it show?' },
  { kind: 'columns', step: 2, label: 'The columns' },
  { kind: 'read', step: 3, label: 'Conclude' },
]

const VERDICT_STYLE = {
  correct: { label: '✅ Correct', box: 'bg-green-900/30 border-green-700', text: 'text-green-300' },
  partial: { label: '🟡 Partly correct', box: 'bg-yellow-900/30 border-yellow-700', text: 'text-yellow-300' },
  wrong: { label: '❌ Not quite', box: 'bg-red-900/30 border-red-700', text: 'text-red-300' },
}

async function api(path, body) {
  const { data: { session } } = await supabase.auth.getSession()
  const res = await fetch(`${API}${path}`, {
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Error ${res.status}`)
  return data
}

function Card({ card }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-4">
      <h2 className="text-white font-semibold">{card.title}</h2>
      <p className="text-gray-300 text-sm">{card.summary}</p>
      <pre className="bg-black text-gray-200 text-xs font-mono rounded-lg p-3 overflow-x-auto">{card.example}</pre>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-400 text-left">
              <th className="pr-3 pb-2 font-medium">Field</th>
              <th className="pr-3 pb-2 font-medium">What it means</th>
              <th className="pr-3 pb-2 font-medium">Normal</th>
              <th className="pb-2 font-medium">Alarming → what it tells you</th>
            </tr>
          </thead>
          <tbody>
            {card.fields.map(f => (
              <tr key={f.name} className="border-t border-gray-800 align-top">
                <td className="pr-3 py-2 font-mono text-green-400 whitespace-nowrap">{f.name}</td>
                <td className="pr-3 py-2 text-gray-200">{f.meaning}</td>
                <td className="pr-3 py-2 text-gray-400">{f.normal}</td>
                <td className="py-2 text-gray-200">{f.alarming}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">Reading it</p>
        <ol className="list-decimal list-inside text-gray-200 text-sm space-y-1">
          {card.steps.map((s, i) => <li key={i}>{s}</li>)}
        </ol>
      </div>
      <p className="text-sm text-gray-200"><span className="text-gray-400">Next: </span>{card.next}</p>
    </div>
  )
}

function PartProgress({ part }) {
  if (!part.unlocked) return <span className="text-gray-600 text-xs">🔒 locked</span>
  if (part.mastered) return <span className="text-green-400 text-xs">✓ mastered</span>
  return <span className="text-gray-400 text-xs">{part.correct}/5 correct · need 4</span>
}

function Lesson({ lesson, onProgress, onBack }) {
  const [card, setCard] = useState(null)
  const [showCard, setShowCard] = useState(true)
  const [kind, setKind] = useState(null)
  const [drill, setDrill] = useState(null)
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api(`/ladder/lessons/${lesson.lesson}`).then(setCard).catch(e => setError(e.message))
  }, [lesson.lesson])

  async function newDrill(k) {
    const previous = k === kind ? drill?.drill_id : null
    setKind(k)
    setDrill(null)
    setResult(null)
    setAnswer('')
    setError('')
    setShowCard(false)
    setLoading(true)
    try {
      setDrill(await api('/ladder/drill', { lesson: lesson.lesson, kind: k, previous_drill_id: previous }))
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }

  async function submit(e) {
    e.preventDefault()
    if (!answer.trim() || loading) return
    setLoading(true)
    setError('')
    try {
      const data = await api('/ladder/answer', { drill_id: drill.drill_id, answer: answer.trim() })
      setResult(data)
      onProgress(data.progress)
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }

  const style = result && VERDICT_STYLE[result.verdict]
  const partNow = kind && lesson[kind]

  return (
    <div className="space-y-4">
      <button onClick={onBack} className="text-gray-400 hover:text-white text-sm">← All lessons</button>

      <div className="grid grid-cols-3 gap-2">
        {PARTS.map(p => {
          const part = lesson[p.kind]
          return (
            <button
              key={p.kind}
              onClick={() => part.unlocked && newDrill(p.kind)}
              disabled={!part.unlocked || loading}
              className={`text-left rounded-xl p-3 border ${
                kind === p.kind ? 'border-blue-500 bg-blue-900/20' : 'border-gray-800 bg-gray-900'
              } ${part.unlocked ? 'hover:border-blue-400' : 'opacity-60 cursor-not-allowed'}`}
            >
              <span className="block text-white text-sm font-medium">{p.step}. {p.label}</span>
              <PartProgress part={part} />
            </button>
          )
        })}
      </div>

      {card && (
        <div>
          <button onClick={() => setShowCard(!showCard)} className="text-blue-400 hover:text-blue-300 text-sm mb-2">
            {showCard ? '▾ Hide the card' : '▸ Show the card'}
          </button>
          {showCard && <Card card={card} />}
        </div>
      )}

      {!kind && <p className="text-gray-400 text-sm">Read the card, then start with step 1.</p>}
      {error && <p className="text-red-400 text-sm">⚠️ {error}</p>}
      {loading && !drill && <p className="text-gray-400 text-sm">Preparing a drill…</p>}

      {drill && (
        <div className="bg-gray-800 rounded-2xl p-4 space-y-3">
          {drill.context && <p className="text-gray-100 text-sm whitespace-pre-wrap">{drill.context}</p>}
          {drill.output && (
            <pre className="bg-black text-gray-200 text-xs font-mono rounded-lg p-3 overflow-x-auto">{drill.output}</pre>
          )}
          <p className="text-white text-sm font-medium">{drill.question}</p>

          {!result ? (
            <form onSubmit={submit} className="space-y-2">
              <textarea
                value={answer}
                onChange={e => setAnswer(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && submit(e)}
                rows={3}
                disabled={loading}
                placeholder="Your answer… (Shift+Enter for a new line)"
                className="w-full bg-gray-900 text-white p-3 rounded-xl resize-none text-sm disabled:opacity-50"
              />
              <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-xl text-sm disabled:opacity-50">
                {loading ? 'Checking…' : 'Check'}
              </button>
            </form>
          ) : (
            <div className="space-y-3">
              <div className={`border rounded-xl p-3 ${style.box}`}>
                <p className={`font-semibold text-sm mb-1 ${style.text}`}>{style.label}</p>
                <p className="text-gray-100 text-sm whitespace-pre-wrap">{result.feedback}</p>
              </div>
              <div className="text-sm">
                <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">A correct answer covers</p>
                <ul className="list-disc list-inside text-gray-200 space-y-1">
                  {result.key_points.map((p, i) => <li key={i}>{p}</li>)}
                </ul>
                {result.bonus_points?.length > 0 && (
                  <>
                    <p className="text-gray-400 text-xs uppercase tracking-wide mt-2 mb-1">Good to also mention</p>
                    <ul className="list-disc list-inside text-gray-400 space-y-1">
                      {result.bonus_points.map((p, i) => <li key={i}>{p}</li>)}
                    </ul>
                  </>
                )}
              </div>
              {partNow?.mastered && (
                <p className="text-green-400 text-sm">🎉 This part is mastered{kind !== 'read' ? ' — the next part is open.' : ' — lesson done!'}</p>
              )}
              <button onClick={() => newDrill(kind)} disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-xl text-sm disabled:opacity-50">
                Next drill →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Learn() {
  const navigate = useNavigate()
  const [lessons, setLessons] = useState(null)
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/ladder/lessons').then(setLessons).catch(e => setError(e.message))
  }, [])

  const current = selected && lessons?.find(l => l.lesson === selected)

  return (
    <div className="min-h-screen bg-gray-950 p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-white text-2xl font-bold">📖 Learn</h1>
          <p className="text-gray-400 text-sm">One command at a time: what it shows, its columns, then conclude</p>
        </div>
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white text-sm">Dashboard</button>
      </div>

      {error && <p className="text-red-400 text-sm">⚠️ {error}</p>}
      {!lessons && !error && <p className="text-gray-400">Loading…</p>}

      {lessons && !current && (
        <div className="space-y-3">
          {lessons.map(l => (
            <button
              key={l.lesson}
              onClick={() => l.unlocked && setSelected(l.lesson)}
              disabled={!l.unlocked}
              className={`w-full text-left rounded-xl p-4 border ${
                l.unlocked ? 'bg-gray-900 border-gray-800 hover:border-blue-400' : 'bg-gray-900/50 border-gray-900 opacity-60'
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="text-white font-medium">{l.number}. <span className="font-mono">{l.lesson}</span></span>
                <span className="text-xs">{l.done ? '✅ done' : l.unlocked ? '' : '🔒'}</span>
              </div>
              <p className="text-gray-400 text-sm mt-1">{l.title}</p>
              <div className="flex gap-4 mt-2">
                {PARTS.map(p => (
                  <span key={p.kind} className="text-xs text-gray-500">
                    {p.step}. <PartProgress part={l[p.kind]} />
                  </span>
                ))}
              </div>
            </button>
          ))}
          <p className="text-gray-600 text-xs">More lessons follow the Netflix 60-second checklist: dmesg, vmstat, mpstat, pidstat, iostat, free, sar and top.</p>
        </div>
      )}

      {current && <Lesson lesson={current} onProgress={setLessons} onBack={() => setSelected(null)} />}
    </div>
  )
}
