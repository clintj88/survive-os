import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

type StatusBadgeVariant =
  | 'online'
  | 'offline'
  | 'degraded'
  | 'warning'
  | 'info'
  | 'critical'

interface StatusBadgeProps {
  status: StatusBadgeVariant
  label?: string
  dot?: boolean
  className?: string
}

const statusConfig: Record<
  StatusBadgeVariant,
  { color: string; bg: string; label: string }
> = {
  online: { color: 'text-green-500', bg: 'bg-green-500/10', label: 'Online' },
  offline: { color: 'text-red-500', bg: 'bg-red-500/10', label: 'Offline' },
  degraded: {
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
    label: 'Degraded',
  },
  warning: {
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
    label: 'Warning',
  },
  info: { color: 'text-blue-500', bg: 'bg-blue-500/10', label: 'Info' },
  critical: { color: 'text-red-500', bg: 'bg-red-500/10', label: 'Critical' },
}

export function StatusBadge({
  status,
  label,
  dot = false,
  className,
}: StatusBadgeProps) {
  const config = statusConfig[status]
  const displayLabel = label ?? config.label

  return (
    <Badge
      variant='outline'
      className={cn(
        'border-transparent font-medium',
        config.bg,
        config.color,
        className
      )}
    >
      {dot && (
        <span
          className={cn('mr-1.5 inline-block size-1.5 rounded-full', {
            'bg-green-500': status === 'online',
            'bg-red-500': status === 'offline' || status === 'critical',
            'bg-amber-500': status === 'degraded' || status === 'warning',
            'bg-blue-500': status === 'info',
          })}
        />
      )}
      {displayLabel}
    </Badge>
  )
}

export type { StatusBadgeVariant, StatusBadgeProps }
