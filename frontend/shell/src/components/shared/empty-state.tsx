import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 text-center',
        className
      )}
    >
      {Icon && (
        <div className='mb-4 flex size-16 items-center justify-center rounded-xl bg-muted'>
          <Icon className='size-7 text-muted-foreground' />
        </div>
      )}
      <h3 className='text-lg font-semibold'>{title}</h3>
      {description && (
        <p className='mt-1.5 max-w-sm text-[13px] text-muted-foreground'>
          {description}
        </p>
      )}
      {action && <div className='mt-4'>{action}</div>}
    </div>
  )
}

export type { EmptyStateProps }
