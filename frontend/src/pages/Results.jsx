import { useLocation, useNavigate } from 'react-router-dom'

export default function Results() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const { sessionData, questionsAnswered } = state || {}

  const topicLabel = sessionData?.topic
    ? sessionData.topic.charAt(0).toUpperCase() + sessionData.topic.slice(1)
    : 'Session'

  const levelLabel = sessionData?.level === 'gemiddeld' ? 'Intermediate' : 'Foundation'

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
      <div className="bg-gray-900 rounded-2xl p-8 max-w-sm w-full text-center space-y-6">
        <div className="text-4xl">✅</div>
        <h1 className="text-white text-2xl font-bold">Session complete!</h1>

        <div className="bg-gray-800 rounded-xl p-4 text-left space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Topic</span>
            <span className="text-white">{topicLabel}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Level</span>
            <span className={`font-medium ${sessionData?.level === 'gemiddeld' ? 'text-green-400' : 'text-gray-300'}`}>
              {levelLabel}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Questions answered</span>
            <span className="text-white">{questionsAnswered ?? '–'}</span>
          </div>
        </div>

        <p className="text-gray-400 text-sm">
          Your progress has been saved. Weak topics will come back automatically in future sessions.
        </p>

        <div className="space-y-3">
          <button
            onClick={() => navigate('/session', { state: sessionData })}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-xl font-medium"
          >
            Another round
          </button>
          <button
            onClick={() => navigate('/')}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white p-3 rounded-xl"
          >
            Back to dashboard
          </button>
        </div>
      </div>
    </div>
  )
}
