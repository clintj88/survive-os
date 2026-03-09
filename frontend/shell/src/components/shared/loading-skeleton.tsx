import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

type SkeletonVariant = 'card' | 'table' | 'stat-cards' | 'page'

interface LoadingSkeletonProps {
  variant?: SkeletonVariant
  className?: string
}

function StatCardsSkeleton() {
  return (
    <div className='grid grid-cols-4 gap-3'>
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className='rounded-lg border bg-card p-4'
        >
          <Skeleton className='mb-2 h-3 w-16' />
          <Skeleton className='mb-1 h-8 w-20' />
          <Skeleton className='h-3 w-24' />
        </div>
      ))}
    </div>
  )
}

function CardSkeleton() {
  return (
    <div className='rounded-lg border bg-card overflow-hidden'>
      <div className='flex items-center justify-between px-4 py-3 border-b border-border'>
        <Skeleton className='h-3 w-24' />
        <Skeleton className='h-5 w-16 rounded-full' />
      </div>
      <div className='p-4 space-y-3'>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className='h-4 w-full' />
        ))}
      </div>
    </div>
  )
}

function TableSkeleton() {
  return (
    <div className='rounded-lg border bg-card overflow-hidden'>
      <div className='border-b border-border p-3'>
        <Skeleton className='h-8 w-64' />
      </div>
      <div className='divide-y divide-border'>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className='flex items-center gap-4 p-3'>
            <Skeleton className='h-4 w-32' />
            <Skeleton className='h-4 w-24' />
            <Skeleton className='h-4 w-16' />
            <Skeleton className='h-4 flex-1' />
          </div>
        ))}
      </div>
    </div>
  )
}

function PageSkeleton() {
  return (
    <div className='space-y-4'>
      <div>
        <Skeleton className='h-7 w-48 mb-2' />
        <Skeleton className='h-4 w-72' />
      </div>
      <StatCardsSkeleton />
      <div className='grid grid-cols-2 gap-3'>
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  )
}

export function LoadingSkeleton({
  variant = 'page',
  className,
}: LoadingSkeletonProps) {
  return (
    <div className={cn('animate-in fade-in-50 duration-300', className)}>
      {variant === 'stat-cards' && <StatCardsSkeleton />}
      {variant === 'card' && <CardSkeleton />}
      {variant === 'table' && <TableSkeleton />}
      {variant === 'page' && <PageSkeleton />}
    </div>
  )
}

export type { LoadingSkeletonProps, SkeletonVariant }
