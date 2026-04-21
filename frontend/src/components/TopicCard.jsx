export default function TopicCard({ subtopic, correct, total }) {
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0
  const isWeak = pct < 70 && total > 0
  return (
    <div className={`p-4 rounded-lg ${isWeak ? 'bg-red-900/30 border border-red-700' : 'bg-gray-800'}`}>
      <div className="flex justify-between items-center">
        <span className="text-white font-medium">{subtopic.replace(/_/g, ' ')}</span>
        <span className={`font-bold ${isWeak ? 'text-red-400' : 'text-green-400'}`}>{pct}%</span>
      </div>
      <div className="mt-2 bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${isWeak ? 'bg-red-500' : 'bg-green-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-gray-400 text-xs mt-1">{correct}/{total} goed</p>
    </div>
  )
}
