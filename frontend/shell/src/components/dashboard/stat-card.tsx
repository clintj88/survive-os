import { cn } from '@/lib/utils'

interface StatCardProps {
  label: string
  value: string
  subtitle?: string
  valueColor?: string
  className?: string
}

export function StatCard({
  label,
  value,
  subtitle,
  valueColor,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-4',
        className
      )}
    >
      <div className='text-xs text-muted-foreground mb-2'>{label}</div>
      <div
        className='text-[28px] font-bold tabular-nums leading-none'
        style={valueColor ? { color: valueColor } : undefined}
      >
        {value}
      </div>
      {subtitle && (
        <div className='text-[11px] text-zinc-600 mt-1'>{subtitle}</div>
      )}
    </div>
  )
}

export type { StatCardProps }
