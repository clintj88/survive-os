import { cn } from '@/lib/utils'

interface WeatherData {
  key: string
  value: string
}

interface WeatherCardProps {
  data: WeatherData[]
}

export function WeatherCard({ data }: WeatherCardProps) {
  return (
    <div className='rounded-lg border bg-card overflow-hidden'>
      <div className='flex items-center justify-between px-4 py-3 border-b border-border'>
        <span className='text-xs font-semibold text-muted-foreground uppercase tracking-wider'>
          Weather Station
        </span>
        <span className='text-[10px] px-2 py-0.5 rounded-full bg-muted border border-border text-muted-foreground font-medium'>
          Local
        </span>
      </div>
      <div className='px-4 py-2'>
        {data.map((row, i) => (
          <div
            key={i}
            className={cn(
              'flex justify-between py-[7px]',
              i < data.length - 1 && 'border-b border-zinc-800/50'
            )}
          >
            <span className='text-xs text-zinc-500'>{row.key}</span>
            <span className='text-xs font-medium text-zinc-200'>
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export type { WeatherData, WeatherCardProps }
