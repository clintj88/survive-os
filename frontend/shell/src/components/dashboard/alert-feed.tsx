import { cn } from '@/lib/utils'

interface AlertItem {
  id: number
  level: 'warning' | 'info' | 'success' | 'error'
  msg: string
  time: string
  module: string
}

interface AlertFeedProps {
  alerts: AlertItem[]
  onAlertClick?: (module: string) => void
}

const levelColors: Record<AlertItem['level'], string> = {
  warning: 'bg-amber-500',
  success: 'bg-green-500',
  info: 'bg-blue-500',
  error: 'bg-red-500',
}

export function AlertFeed({ alerts, onAlertClick }: AlertFeedProps) {
  return (
    <div className='rounded-lg border bg-card overflow-hidden'>
      <div className='flex items-center justify-between px-4 py-3 border-b border-border'>
        <span className='text-xs font-semibold text-muted-foreground uppercase tracking-wider'>
          Recent Alerts
        </span>
        <span className='text-[10px] px-2 py-0.5 rounded-full bg-muted border border-border text-muted-foreground font-medium'>
          Last 24h
        </span>
      </div>
      <div className='px-4 py-2'>
        {alerts.map((alert, i) => (
          <div
            key={alert.id}
            onClick={() => onAlertClick?.(alert.module)}
            className={cn(
              'flex gap-2.5 py-2.5 cursor-pointer',
              i < alerts.length - 1 && 'border-b border-zinc-800/50'
            )}
          >
            <span
              className={cn(
                'mt-1.5 size-[7px] rounded-full shrink-0',
                levelColors[alert.level]
              )}
            />
            <div className='flex-1 min-w-0'>
              <div className='text-[13px] text-zinc-200 leading-snug'>
                {alert.msg}
              </div>
              <div className='text-[11px] text-zinc-600 mt-0.5'>
                {alert.time}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export type { AlertItem, AlertFeedProps }
