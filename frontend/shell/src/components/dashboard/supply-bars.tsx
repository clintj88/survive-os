import { cn } from '@/lib/utils'

interface SupplyItem {
  name: string
  val: number
  max: number
  min: number
}

interface SupplyBarsProps {
  supplies: SupplyItem[]
}

function getSupplyColor(item: SupplyItem): string {
  if (item.val < item.min) return '#ef4444'
  if (item.val < item.min * 1.5) return '#f59e0b'
  return '#22c55e'
}

export function SupplyBars({ supplies }: SupplyBarsProps) {
  return (
    <div className='rounded-lg border bg-card overflow-hidden'>
      <div className='flex items-center justify-between px-4 py-3 border-b border-border'>
        <span className='text-xs font-semibold text-muted-foreground uppercase tracking-wider'>
          Supply Status
        </span>
        <span className='text-[10px] px-2 py-0.5 rounded-full bg-muted border border-border text-muted-foreground font-medium'>
          Real-time
        </span>
      </div>
      <div className='px-4 py-2'>
        {supplies.map((item, i) => {
          const color = getSupplyColor(item)
          const pct = Math.min(100, (item.val / item.max) * 100)
          return (
            <div
              key={i}
              className='flex items-center gap-2.5 py-[7px]'
            >
              <div className='w-[110px] shrink-0 text-xs text-muted-foreground'>
                {item.name}
              </div>
              <div className='flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden'>
                <div
                  className='h-full rounded-full transition-all duration-500'
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
              <div
                className='w-9 text-right text-xs font-semibold tabular-nums'
                style={{ color }}
              >
                {item.val}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export type { SupplyItem, SupplyBarsProps }
