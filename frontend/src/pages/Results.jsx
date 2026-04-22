import { useLocation, useNavigate } from 'react-router-dom'

export default function Results() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const { sessionData } = state || {}

  const topicLabel = sessionData?.topic
    ? sessionData.topic.charAt(0).toUpperCase() + sessionData.topic.slice(1)
    : 'Sessie'

  const levelLabel = sessionData?.level === 'gemiddeld' ? 'Gemiddeld' : 'Basis'

  function startNew() {
    navigate('/')
  }

  function startAgain() {
    navigate('/session', { state: sessionData })
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
      <div className="bg-gray-900 rounded-2xl p-8 max-w-sm w-full text-center space-y-6">
        <div className="text-4xl">✅</div>
        <h1 className="text-white text-2xl font-bold">Sessie klaar!</h1>

        <div className="bg-gray-800 rounded-xl p-4 text-left space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Onderwerp</span>
            <span className="text-white">{topicLabel}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Niveau</span>
            <span className={`font-medium ${sessionData?.level === 'gemiddeld' ? 'text-green-400' : 'text-gray-300'}`}>
              {levelLabel}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Vragen beantwoord</span>
            <span className="text-white">3</span>
          </div>
        </div>

        <p className="text-gray-400 text-sm">
          Je voortgang is opgeslagen. Zwakke onderwerpen komen automatisch terug in volgende sessies.
        </p>

        <div className="space-y-3">
          <button
            onClick={startAgain}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-xl font-medium"
          >
            Nog een ronde
          </button>
          <button
            onClick={startNew}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white p-3 rounded-xl"
          >
            Terug naar dashboard
          </button>
        </div>
      </div>
    </div>
  )
}
