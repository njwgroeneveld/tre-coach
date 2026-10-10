import { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import ChatBubble from '../components/ChatBubble'

const API = import.meta.env.VITE_API_URL
// Performance sessions are one question: an investigation alone takes long enough.
const questionsPerSession = (data) => (data?.investigation || data?.topic === 'performance' ? 1 : 3)

function useVoiceInput(onTranscript) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef(null)
  const listeningRef = useRef(false)
  const silenceTimerRef = useRef(null)

  function resetSilenceTimer(SR) {
    clearTimeout(silenceTimerRef.current)
    silenceTimerRef.current = setTimeout(() => {
      listeningRef.current = false
      recognitionRef.current?.stop()
      setListening(false)
    }, 5000)
  }

  function _start(SR) {
    const recognition = new SR()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (e) => {
      onTranscript(e.results[0][0].transcript)
      resetSilenceTimer(SR)
    }
    recognition.onend = () => {
      if (listeningRef.current) {
        setTimeout(() => _start(SR), 100)
      } else {
        clearTimeout(silenceTimerRef.current)
        setListening(false)
      }
    }
    recognition.onerror = (e) => {
      if (listeningRef.current && e.error !== 'aborted') {
        setTimeout(() => _start(SR), 100)
      } else {
        listeningRef.current = false
        clearTimeout(silenceTimerRef.current)
        setListening(false)
      }
    }
    recognitionRef.current = recognition
    recognition.start()
  }

  function startListening() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      alert('Speech recognition is not supported in this browser. Please use Chrome.')
      return
    }
    listeningRef.current = true
    setListening(true)
    _start(SR)
  }

  function stopListening() {
    listeningRef.current = false
    clearTimeout(silenceTimerRef.current)
    recognitionRef.current?.stop()
  }

  return { listening, startListening, stopListening }
}

const MAX_STEPS = 10
const MAX_ATTEMPTS = 2

async function postJSON(path, body) {
  const { data: { session } } = await supabase.auth.getSession()
  return fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
    body: JSON.stringify(body),
  })
}

async function errorText(res) {
  try {
    const data = await res.json()
    return typeof data.detail === 'string' ? data.detail : `Error ${res.status}`
  } catch {
    return `Error ${res.status}`
  }
}

export default function Session() {
  const { state: sessionData } = useLocation()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingText, setLoadingText] = useState('...')
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [questionCount, setQuestionCount] = useState(0)
  const [hintsUsed, setHintsUsed] = useState(0)
  const [showHintBtn, setShowHintBtn] = useState(false)
  const [followUpMode, setFollowUpMode] = useState(false)
  const [followUpHistory, setFollowUpHistory] = useState([])
  const [currentFeedback, setCurrentFeedback] = useState('')
  const [currentAnswer, setCurrentAnswer] = useState('')
  // Investigation mode: { id, stepsLeft, attemptsLeft, closed } while the question is an investigation.
  const [investigation, setInvestigation] = useState(null)
  const [diagnoseMode, setDiagnoseMode] = useState(false)
  const subtopicsRef = useRef(sessionData?.subtopics || [sessionData?.subtopic])
  const subtopicIndexRef = useRef(0)
  const bottomRef = useRef(null)

  const { listening, startListening, stopListening } = useVoiceInput((transcript) => {
    setInput(prev => prev ? prev + ' ' + transcript : transcript)
  })

  useEffect(() => { fetchQuestion() }, [])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const investigating = investigation && !investigation.closed
  const commandMode = investigating && !diagnoseMode

  function addSystem(text) {
    setMessages(prev => [...prev, { role: 'system', text }])
  }

  async function fetchQuestion() {
    setLoading(true)
    setLoadingText('Preparing the next question… an investigation can take about 15 seconds.')
    setHintsUsed(0)
    setShowHintBtn(false)
    setFollowUpMode(false)
    setFollowUpHistory([])
    setCurrentFeedback('')
    setCurrentAnswer('')
    setInvestigation(null)
    setDiagnoseMode(false)

    const subtopics = subtopicsRef.current
    const subtopic = subtopics[subtopicIndexRef.current % subtopics.length]
    subtopicIndexRef.current += 1

    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(
      `${API}/session/question?session_id=${sessionData.session_id}&subtopic=${subtopic}&level=${sessionData.level}` +
        (sessionData.investigation ? `&force=investigation&env=${sessionData.investigation}` : ''),
      { method: 'POST', headers: { Authorization: `Bearer ${session.access_token}` } }
    )
    if (!res.ok) {
      addSystem(`⚠️ ${await errorText(res)}`)
      setFollowUpMode(true)  // offers "Next question" to retry
      setLoading(false)
      return
    }
    const q = await res.json()
    setCurrentQuestion(q)

    if (q.question_type === 'investigation') {
      setInvestigation({ id: q.investigation_id, stepsLeft: MAX_STEPS, attemptsLeft: MAX_ATTEMPTS, closed: false })
      // No subtopic label: it would give the cause away.
      setMessages(prev => [...prev,
        { role: 'question', text: q.question },
        { role: 'system', text: q.env === 'k8s'
          ? `☸️ Kubernetes investigation: you are on a workstation with kubectl access to the cluster (namespace trading). Use kubectl, 'ssh node-N' to log in to a node ('exit' to leave), or 'kubectl exec -it <pod> -n trading -- <command>'. Up to ${MAX_STEPS} commands; press Diagnose when you know the cause.`
          : `🔍 Investigation: type commands as if you are on the host (up to ${MAX_STEPS}). When you know the cause, press Diagnose.` },
      ])
    } else {
      setMessages(prev => [...prev, { role: 'question', text: q.question, subtopic: q.subtopic }])
      setShowHintBtn(true)
    }
    setLoading(false)
  }

  async function handleInvestigationHint() {
    if (hintsUsed >= 3 || loading) return
    setLoading(true)
    setLoadingText('Thinking of a hint…')

    const res = await postJSON('/investigation/hint', { investigation_id: investigation.id })
    if (!res.ok) {
      addSystem(`⚠️ ${await errorText(res)}`)
      setLoading(false)
      return
    }
    const data = await res.json()
    // The server counts hints; follow its number rather than our own.
    setHintsUsed(data.hint_number)
    setMessages(prev => [...prev, { role: 'hint', text: `💡 Hint ${data.hint_number}/3: ${data.hint}` }])
    setLoading(false)
  }

  async function handleHint() {
    if (hintsUsed >= 3 || loading) return
    const nextHint = hintsUsed + 1
    setLoading(true)
    setLoadingText('...')

    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/session/hint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
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
    if (investigating) {
      await (diagnoseMode ? handleDiagnose() : handleCommand())
      return
    }

    const userAnswer = input.trim()
    setInput('')
    setShowHintBtn(false)
    setMessages(prev => [...prev, { role: 'user', text: userAnswer }])
    setLoading(true)
    setLoadingText('...')

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

  async function handleCommand() {
    const command = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'command', text: command }])
    setLoading(true)
    setLoadingText('running…')

    const res = await postJSON('/investigation/step', { investigation_id: investigation.id, input: command })
    if (!res.ok) {
      addSystem(`⚠️ ${await errorText(res)}`)
      if (res.status === 409) setDiagnoseMode(true)
      setLoading(false)
      return
    }
    const data = await res.json()
    setMessages(prev => [...prev, { role: 'terminal', text: data.output }])
    setInvestigation(prev => ({ ...prev, stepsLeft: data.steps_left }))
    if (data.steps_left === 0) {
      addSystem('No commands left — make your diagnosis.')
      setDiagnoseMode(true)
    }
    setLoading(false)
  }

  async function handleDiagnose() {
    const diagnosis = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'diagnosis', text: diagnosis }])
    setLoading(true)
    setLoadingText('Checking your diagnosis…')

    const res = await postJSON('/investigation/diagnose', { investigation_id: investigation.id, diagnosis })
    if (!res.ok) {
      addSystem(`⚠️ ${await errorText(res)}`)
      setLoading(false)
      return
    }
    const data = await res.json()

    if (data.status === 'open') {
      setMessages(prev => [...prev, { role: 'consequence', text: data.consequence }])
      setInvestigation(prev => ({ ...prev, attemptsLeft: data.attempts_left }))
      setDiagnoseMode(investigation.stepsLeft === 0)  // back to commands if any are left
      setLoading(false)
      return
    }

    const result = data.evaluation
    setInvestigation(prev => ({ ...prev, attemptsLeft: data.attempts_left, closed: true }))
    setDiagnoseMode(false)
    setCurrentFeedback(result.feedback)
    setCurrentAnswer(diagnosis)
    setMessages(prev => [...prev,
      ...(data.consequence ? [{ role: 'consequence', text: data.consequence }] : []),
      { role: 'result', text: data.status },
      { role: 'reveal', text: data.reveal },
      { role: 'feedback', text: result.feedback, score: result.score },
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
    setLoadingText('...')

    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/session/followup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
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
    if (newCount >= questionsPerSession(sessionData)) {
      navigate('/results', { state: { sessionData, questionsAnswered: newCount } })
    } else {
      fetchQuestion()
    }
  }

  const levelLabel = sessionData?.level === 'gemiddeld' ? 'Intermediate' : 'Foundation'
  const isK8s = currentQuestion?.env === 'k8s'
  const subtopicLabel = investigating
    ? (isK8s ? 'kubernetes investigation' : 'investigation')
    : currentQuestion?.subtopic?.replace(/_/g, ' ') || sessionData?.subtopic?.replace(/_/g, ' ')

  const placeholder = followUpMode
    ? 'Ask a follow-up question...'
    : commandMode
      ? (isK8s ? 'kubectl get pods -n trading -o wide' : 'uptime')
      : diagnoseMode
        ? 'Name the culprit and how it causes the symptom, then your fix...'
        : 'Type your answer... (Shift+Enter for new line)'
  const submitLabel = followUpMode ? 'Ask' : commandMode ? 'Run' : diagnoseMode ? 'Diagnose' : 'Send'

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col max-w-7xl mx-auto">
      <div className="p-4 border-b border-gray-800 flex justify-between items-center">
        <div>
          <h2 className="text-white font-semibold">
            {sessionData?.topic} — {subtopicLabel}
          </h2>
          <p className="text-gray-400 text-xs">
            {levelLabel} · {questionCount}/{questionsPerSession(sessionData)} questions
            {investigating && (
              <> · step {MAX_STEPS - investigation.stepsLeft}/{MAX_STEPS} · attempt {MAX_ATTEMPTS - investigation.attemptsLeft + 1}/{MAX_ATTEMPTS}</>
            )}
          </p>
        </div>
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white text-sm">Stop</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => <ChatBubble key={i} role={m.role} text={m.text} subtopic={m.subtopic} score={m.score} />)}
        {loading && <ChatBubble role="system" text={loadingText} />}
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
        ) : investigating ? (
          <div className="px-4 pt-3 flex items-center justify-between">
            <p className="text-gray-500 text-xs">
              {diagnoseMode ? '🩺 State the root cause and your fix' : `$ ${investigation.stepsLeft} commands left`}
            </p>
            <div className="flex items-center gap-4">
              {hintsUsed < 3 && (
                <button
                  onClick={handleInvestigationHint}
                  disabled={loading}
                  className="text-yellow-400 hover:text-yellow-300 text-sm disabled:opacity-50"
                >
                  💡 Hint {hintsUsed + 1}/3
                </button>
              )}
              {investigation.stepsLeft > 0 && (
                <button
                  onClick={() => setDiagnoseMode(!diagnoseMode)}
                  disabled={loading}
                  className="text-purple-400 hover:text-purple-300 text-sm font-medium disabled:opacity-50"
                >
                  {diagnoseMode ? '← Back to commands' : '🩺 Diagnose'}
                </button>
              )}
            </div>
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
          <div className="flex-1 flex items-start bg-gray-800 rounded-xl">
            {commandMode && <span className="text-green-400 font-mono text-sm pl-3 pt-3">$</span>}
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSubmit(e)}
              placeholder={placeholder}
              rows={commandMode ? 1 : 3}
              disabled={loading}
              autoCapitalize="off"
              spellCheck={!commandMode}
              className={`flex-1 bg-transparent text-white p-3 resize-none text-sm disabled:opacity-50 outline-none ${commandMode ? 'font-mono' : ''}`}
            />
          </div>
          <div className="flex flex-col gap-2">
            {!commandMode && (
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
            )}
            <button
              type="submit"
              disabled={loading}
              className={`text-white px-5 rounded-xl disabled:opacity-50 flex-1 ${
                diagnoseMode && !followUpMode ? 'bg-purple-600 hover:bg-purple-700' : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
