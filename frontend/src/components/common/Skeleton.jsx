export function Skeleton({ width = '100%', height = 16, className = '' }) {
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      style={{ width, height }}
    />
  )
}

export function IndexCardSkeleton() {
  return (
    <div className="border border-border rounded-lg p-4 space-y-2">
      <Skeleton height={14} width="60%" />
      <Skeleton height={22} width="80%" />
      <Skeleton height={12} width="50%" />
      <Skeleton height={40} />
    </div>
  )
}

export function NewsCardSkeleton() {
  return (
    <div className="py-4 border-b border-border space-y-2">
      <Skeleton height={16} width="90%" />
      <Skeleton height={16} width="70%" />
      <Skeleton height={12} width="40%" />
    </div>
  )
}

export function SectorRowSkeleton() {
  return (
    <div className="flex items-center px-4 py-2 gap-3">
      <div className="flex-1 space-y-1">
        <Skeleton height={13} width="70%" />
        <Skeleton height={11} width="40%" />
      </div>
      <Skeleton width={80} height={24} />
      <div className="text-right space-y-1">
        <Skeleton height={13} width={60} />
        <Skeleton height={11} width={50} />
      </div>
    </div>
  )
}

export function ChatMessageSkeleton() {
  return (
    <div className="flex gap-2 px-4 py-3">
      <Skeleton width={28} height={28} className="rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton height={14} width="90%" />
        <Skeleton height={14} width="70%" />
        <Skeleton height={14} width="50%" />
      </div>
    </div>
  )
}
