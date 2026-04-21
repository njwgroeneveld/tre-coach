export default function ChatBubble({ role, text, score }) {
  const isUser = role === 'user'
  const isSystem = role === 'system'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-2xl p-4 ${
        isUser ? 'bg-blue-600 text-white' :
        isSystem ? 'bg-gray-700 text-gray-200' :
        'bg-gray-800 text-gray-100'
      }`}>
        {score !== undefined && (
          <span className={`text-xs font-bold mb-2 block ${score >= 7 ? 'text-green-400' : 'text-red-400'}`}>
            Score: {score}/10
          </span>
        )}
        <p className="text-sm whitespace-pre-wrap">{text}</p>
      </div>
    </div>
  )
}
