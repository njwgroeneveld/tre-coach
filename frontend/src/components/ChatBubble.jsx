export default function ChatBubble({ role, text, subtopic, score }) {
  if (role === 'command') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[90%] bg-gray-900 border border-gray-700 rounded-xl px-3 py-2">
          <p className="text-green-400 text-sm font-mono whitespace-pre-wrap break-all">$ {text}</p>
        </div>
      </div>
    )
  }

  if (role === 'terminal') {
    return (
      <div className="bg-black border border-gray-800 rounded-xl p-3 overflow-x-auto">
        <pre className="text-gray-200 text-xs font-mono leading-relaxed">{text}</pre>
      </div>
    )
  }

  if (role === 'diagnosis') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-purple-700 rounded-2xl p-4">
          <span className="text-xs text-purple-200 uppercase tracking-wide mb-1 block">Diagnosis</span>
          <p className="text-white text-sm whitespace-pre-wrap">{text}</p>
        </div>
      </div>
    )
  }

  if (role === 'consequence') {
    return (
      <div className="bg-red-900/30 border border-red-800/60 rounded-2xl p-4">
        <span className="text-xs text-red-400 uppercase tracking-wide mb-2 block">Not the root cause</span>
        <p className="text-red-200 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'result') {
    const solved = text === 'solved'
    return (
      <div className={`rounded-2xl p-4 text-center font-semibold ${solved ? 'bg-green-800/50 text-green-200' : 'bg-red-800/50 text-red-200'}`}>
        {solved ? '✅ Root cause found' : '❌ Not solved — here is what was going on'}
      </div>
    )
  }

  if (role === 'reveal') {
    const { cause, fix, fastest_path } = text
    return (
      <div className="bg-gray-800 border border-gray-600 rounded-2xl p-4 space-y-3">
        <div>
          <span className="text-xs text-gray-400 uppercase tracking-wide block mb-1">Root cause</span>
          <p className="text-gray-100 text-sm">{cause}</p>
        </div>
        <div>
          <span className="text-xs text-gray-400 uppercase tracking-wide block mb-1">Fix</span>
          <p className="text-gray-100 text-sm">{fix}</p>
        </div>
        <div>
          <span className="text-xs text-gray-400 uppercase tracking-wide block mb-1">Fastest path</span>
          <ol className="list-decimal list-inside space-y-1">
            {fastest_path.map((step, i) => (
              <li key={i} className="text-gray-200 text-xs font-mono">{step}</li>
            ))}
          </ol>
        </div>
      </div>
    )
  }

  if (role === 'question') {
    return (
      <div className="bg-gray-800 rounded-2xl p-4">
        {subtopic && (
          <span className="text-xs text-gray-500 uppercase tracking-wide mb-2 block">
            {subtopic.replace(/_/g, ' ')}
          </span>
        )}
        <p className="text-gray-100 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-600 rounded-2xl p-4">
          <p className="text-white text-sm whitespace-pre-wrap">{text}</p>
        </div>
      </div>
    )
  }

  if (role === 'hint') {
    return (
      <div className="bg-yellow-900/30 border border-yellow-800/50 rounded-2xl p-4">
        <p className="text-yellow-300 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'feedback') {
    return (
      <div className="bg-gray-800 rounded-2xl p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs text-gray-500 uppercase tracking-wide">Technical Feedback</span>
          {score != null && (
            <span className={`text-sm font-bold ${score >= 7 ? 'text-green-400' : score >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
              {score}/10
            </span>
          )}
        </div>
        <p className="text-gray-100 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'english') {
    const { grammar_score, vocabulary_score, structure_score, fluency_score, english_tips } = text
    return (
      <div className="bg-indigo-900/30 border border-indigo-700/50 rounded-2xl p-4 space-y-3">
        <span className="text-xs text-indigo-400 uppercase tracking-wide block">English Feedback</span>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Grammar', score: grammar_score },
            { label: 'Vocabulary', score: vocabulary_score },
            { label: 'Structure', score: structure_score },
            { label: 'Fluency', score: fluency_score },
          ].map(({ label, score }) => (
            <div key={label} className="flex items-center justify-between bg-indigo-900/30 rounded-lg px-3 py-2">
              <span className="text-indigo-300 text-xs">{label}</span>
              <span className={`text-xs font-bold ${score >= 7 ? 'text-green-400' : score >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
                {score ?? '–'}/10
              </span>
            </div>
          ))}
        </div>
        {english_tips && (
          <p className="text-indigo-200 text-sm">💡 {english_tips}</p>
        )}
      </div>
    )
  }

  if (role === 'interview') {
    return (
      <div className="bg-green-900/30 border border-green-800/50 rounded-2xl p-4">
        <p className="text-green-300 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'followup') {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-2xl p-4">
        <span className="text-xs text-blue-400 uppercase tracking-wide mb-2 block">Coach</span>
        <p className="text-gray-100 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'pi') {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-4">
        <p className="text-pink-300 text-sm whitespace-pre-wrap font-mono">{text}</p>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="bg-gray-700 rounded-2xl p-4">
        <p className="text-gray-300 text-sm">{text}</p>
      </div>
    </div>
  )
}
