import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: React.ReactNode
  className?: string
}

export function PageHeader({
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn('mb-5', className)}>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-[22px] font-bold tracking-tight'>{title}</h1>
          {description && (
            <p className='text-[13px] text-muted-foreground mt-1'>
              {description}
            </p>
          )}
        </div>
        {actions && <div className='flex items-center gap-2'>{actions}</div>}
      </div>
    </div>
  )
}
