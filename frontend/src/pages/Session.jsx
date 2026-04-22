import { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import ChatBubble from '../components/ChatBubble'

const API = import.meta.env.VITE_API_URL
const QUESTIONS_PER_SESSION = 3

function useVoiceInput(onTranscript) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef(null)

  function startListening() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      alert('Speech recognition is not supported in this browser. Please use Chrome.')
      return
    }
    const recognition = new SR()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (e) => onTranscript(e.results[0][0].transcript)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)
    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }

  function stopListening() {
    recognitionRef.current?.stop()
    setListening(false)
  }

  return { listening, startListening, stopListening }
}

export default function Session() {
  const { state: sessionData } = useLocation()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [questionCount, setQuestionCount] = useState(0)
  const [hintsUsed, setHintsUsed] = useState(0)
  const [showHintBtn, setShowHintBtn] = useState(false)
  const [followUpMode, setFollowUpMode] = useState(false)
  const [followUpHistory, setFollowUpHistory] = useState([])
  const [currentFeedback, setCurrentFeedback] = useState('')
  const [currentAnswer, setCurrentAnswer] = useState('')
  const subtopicsRef = useRef(sessionData?.subtopics || [sessionData?.subtopic])
  const subtopicIndexRef = useRef(0)
  const bottomRef = useRef(null)

  const { listening, startListening, stopListening } = useVoiceInput((transcript) => {
    setInput(prev => prev ? prev + ' ' + transcript : transcript)
  })

  useEffect(() => { fetchQuestion() }, [])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function fetchQuestion() {
    setLoading(true)
    setHintsUsed(0)
    setShowHintBtn(false)
    setFollowUpMode(false)
    setFollowUpHistory([])
    setCurrentFeedback('')
    setCurrentAnswer('')

    const subtopics = subtopicsRef.current
    const subtopic = subtopics[subtopicIndexRef.current % subtopics.length]
    subtopicIndexRef.current += 1

    const res = await fetch(
      `${API}/session/question?session_id=${sessionData.session_id}&subtopic=${subtopic}&level=${sessionData.level}`,
      { method: 'POST' }
    )
    const q = await res.json()
    setCurrentQuestion(q)
    setMessages(prev => [...prev, { role: 'question', text: q.question, subtopic: q.subtopic }])
    setShowHintBtn(true)
    setLoading(false)
  }

  async function handleHint() {
    if (hintsUsed >= 3 || loading) return
    const nextHint = hintsUsed + 1
    setLoading(true)

    const res = await fetch(`${API}/session/hint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: currentQuestion.question,
        subtopic: currentQuestion.subtopic,
        hint_number: nextHint,
        previous_answer: input,
      })
    })
    const data = await res.json()
    setHintsUsed(nextHint)
    setMessages(prev => [...prev, { role: 'hint', text: `💡 Hint ${nextHint}/3: ${data.hint}` }])
    setLoading(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!input.trim() || loading) return

    if (followUpMode) {
      await handleFollowUp()
      return
    }

    const userAnswer = input.trim()
    setInput('')
    setShowHintBtn(false)
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
        level: sessionData.level,
      })
    })
    const result = await res.json()

    setCurrentFeedback(result.feedback)
    setCurrentAnswer(userAnswer)

    setMessages(prev => [...prev,
      { role: 'feedback', text: result.feedback },
      ...(result.grammar_score != null ? [{ role: 'english', text: result }] : []),
      ...(result.interview_answer ? [{ role: 'interview', text: `🎤 Interview: ${result.interview_answer}` }] : []),
      ...(result.pi_commando ? [{ role: 'pi', text: `🍓 Pi simulation:\n${result.pi_commando}` }] : []),
    ])

    setFollowUpMode(true)
    setLoading(false)
  }

  async function handleFollowUp() {
    const question = input.trim()
    if (!question) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: question }])
    setLoading(true)

    const res = await fetch(`${API}/session/followup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: currentQuestion.question,
        subtopic: currentQuestion.subtopic,
        user_answer: currentAnswer,
        feedback: currentFeedback,
        followup_question: question,
        history: followUpHistory,
      })
    })
    const data = await res.json()

    const newHistory = [
      ...followUpHistory,
      { role: 'user', text: question },
      { role: 'coach', text: data.answer },
    ]
    setFollowUpHistory(newHistory)
    setMessages(prev => [...prev, { role: 'followup', text: data.answer }])
    setLoading(false)
  }

  function handleNextQuestion() {
    const newCount = questionCount + 1
    setQuestionCount(newCount)
    if (newCount >= QUESTIONS_PER_SESSION) {
      navigate('/results', { state: { sessionData } })
    } else {
      fetchQuestion()
    }
  }

  const levelLabel = sessionData?.level === 'gemiddeld' ? 'Intermediate' : 'Foundation'

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col max-w-2xl mx-auto">
      <div className="p-4 border-b border-gray-800 flex justify-between items-center">
        <div>
          <h2 className="text-white font-semibold">
            {sessionData?.topic} — {currentQuestion?.subtopic?.replace(/_/g, ' ') || sessionData?.subtopic?.replace(/_/g, ' ')}
          </h2>
          <p className="text-gray-400 text-xs">{levelLabel} · {questionCount}/{QUESTIONS_PER_SESSION} questions</p>
        </div>
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white text-sm">Stop</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => <ChatBubble key={i} role={m.role} text={m.text} subtopic={m.subtopic} />)}
        {loading && <ChatBubble role="system" text="..." />}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-gray-800">
        {followUpMode ? (
          <div className="px-4 pt-3 pb-1 flex items-center justify-between">
            <p className="text-gray-500 text-xs">💬 Ask follow-up questions about this topic</p>
            <button
              onClick={handleNextQuestion}
              disabled={loading}
              className="text-blue-400 hover:text-blue-300 text-sm font-medium disabled:opacity-50"
            >
              Next question →
            </button>
          </div>
        ) : (
          showHintBtn && hintsUsed < 3 && (
            <div className="px-4 pt-3">
              <button
                onClick={handleHint}
                disabled={loading}
                className="text-yellow-400 hover:text-yellow-300 text-sm disabled:opacity-50"
              >
                💡 Hint {hintsUsed + 1}/3 — I need a nudge
              </button>
            </div>
          )
        )}
        <form onSubmit={handleSubmit} className="p-4 flex gap-3">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSubmit(e)}
            placeholder={followUpMode ? 'Ask a follow-up question...' : 'Type your answer... (Shift+Enter for new line)'}
            rows={3}
            disabled={loading}
            className="flex-1 bg-gray-800 text-white p-3 rounded-xl resize-none text-sm disabled:opacity-50"
          />
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={listening ? stopListening : startListening}
              disabled={loading}
              title={listening ? 'Stop recording' : 'Speak your answer'}
              className={`p-3 rounded-xl text-white disabled:opacity-50 ${
                listening ? 'bg-red-600 hover:bg-red-700 animate-pulse' : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              {listening ? '⏹' : '🎤'}
            </button>
            <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-5 rounded-xl disabled:opacity-50 flex-1">
              {followUpMode ? 'Ask' : 'Send'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
