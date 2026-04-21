import { useLocation, useNavigate } from 'react-router-dom'

export default function Results() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const { totalScore, maxScore } = state || {}
  const pct = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
      <div className="bg-gray-900 rounded-2xl p-8 max-w-sm w-full text-center space-y-6">
        <h1 className="text-white text-2xl font-bold">Sessie klaar!</h1>
        <div className={`text-6xl font-bold ${pct >= 70 ? 'text-green-400' : 'text-red-400'}`}>
          {pct}%
        </div>
        <p className="text-gray-400">{totalScore}/{maxScore} punten</p>
        <p className="text-gray-300 text-sm">
          {pct >= 70 ? 'Goed gedaan! Blijf zo doorgaan.' : 'Dit onderwerp komt binnenkort terug voor extra oefening.'}
        </p>
        <div className="space-y-3">
          <button onClick={() => navigate('/session', { state: state?.sessionData })} className="w-full bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-xl">
            Nog een ronde
          </button>
          <button onClick={() => navigate('/')} className="w-full bg-gray-700 hover:bg-gray-600 text-white p-3 rounded-xl">
            Terug naar dashboard
          </button>
        </div>
      </div>
    </div>
  )
}
