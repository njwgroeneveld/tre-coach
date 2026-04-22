import { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import ChatBubble from '../components/ChatBubble'

const API = import.meta.env.VITE_API_URL
const QUESTIONS_PER_SESSION = 3

export default function Session() {
  const { state: sessionData } = useLocation()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [questionCount, setQuestionCount] = useState(0)
  const [totalScore, setTotalScore] = useState(0)
  const subtopicsRef = useRef(sessionData?.subtopics || [sessionData?.subtopic])
  const subtopicIndexRef = useRef(0)
  const bottomRef = useRef(null)

  useEffect(() => {
    fetchQuestion()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function fetchQuestion() {
    setLoading(true)
    const subtopics = subtopicsRef.current
    const subtopic = subtopics[subtopicIndexRef.current % subtopics.length]
    subtopicIndexRef.current += 1

    const res = await fetch(
      `${API}/session/question?session_id=${sessionData.session_id}&subtopic=${subtopic}`,
      { method: 'POST' }
    )
    const q = await res.json()
    setCurrentQuestion(q)
    setMessages(prev => [...prev, { role: 'assistant', text: q.question }])
    setLoading(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userAnswer = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userAnswer }])
    setLoading(true)

    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/session/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
      body: JSON.stringify({
        session_id: sessionData.session_id,
        question: currentQuestion.question,
        question_type: currentQuestion.question_type,
        subtopic: currentQuestion.subtopic,
        user_answer: userAnswer,
      })
    })
    const result = await res.json()
    const newScore = totalScore + result.score
    setTotalScore(newScore)
    setMessages(prev => [...prev, { role: 'assistant', text: result.feedback, score: result.score }])

    const newCount = questionCount + 1
    setQuestionCount(newCount)

    if (newCount >= QUESTIONS_PER_SESSION) {
      setLoading(false)
      navigate('/results', { state: { totalScore: newScore, maxScore: QUESTIONS_PER_SESSION * 10, sessionData } })
    } else {
      setTimeout(fetchQuestion, 1500)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col max-w-2xl mx-auto">
      <div className="p-4 border-b border-gray-800 flex justify-between items-center">
        <div>
          <h2 className="text-white font-semibold">{sessionData?.topic} — {currentQuestion?.subtopic?.replace(/_/g, ' ') || sessionData?.subtopic?.replace(/_/g, ' ')}</h2>
          <p className="text-gray-400 text-xs">{questionCount}/{QUESTIONS_PER_SESSION} vragen</p>
        </div>
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white text-sm">Stop</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => <ChatBubble key={i} role={m.role} text={m.text} score={m.score} />)}
        {loading && <ChatBubble role="system" text="..." />}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-800 flex gap-3">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSubmit(e)}
          placeholder="Typ je antwoord..."
          rows={3}
          disabled={loading}
          className="flex-1 bg-gray-800 text-white p-3 rounded-xl resize-none text-sm disabled:opacity-50"
        />
        <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-5 rounded-xl disabled:opacity-50">
          Stuur
        </button>
      </form>
    </div>
  )
}
