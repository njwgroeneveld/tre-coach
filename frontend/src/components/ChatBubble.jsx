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
        <span className="text-xs text-gray-500 uppercase tracking-wide mb-2 block">Feedback</span>
        <p className="text-gray-100 text-sm whitespace-pre-wrap">{text}</p>
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
