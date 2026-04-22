export default function ChatBubble({ role, text, subtopic }) {
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
        <span className="text-xs text-gray-500 uppercase tracking-wide mb-2 block">Technical Feedback</span>
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
