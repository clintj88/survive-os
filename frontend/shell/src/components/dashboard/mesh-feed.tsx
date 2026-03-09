import { useRef, useState, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface MeshMessage {
  id: number
  from: string
  channel: string
  msg: string
  time: string
}

interface MeshFeedProps {
  messages: MeshMessage[]
}

const channelStyles: Record<string, { bg: string; text: string }> = {
  PRIMARY: { bg: 'bg-blue-950', text: 'text-blue-400' },
  SECURITY: { bg: 'bg-red-950', text: 'text-red-400' },
  SENSOR: { bg: 'bg-green-950', text: 'text-green-400' },
  MEDICAL: { bg: 'bg-pink-950', text: 'text-pink-400' },
  EMERGENCY: { bg: 'bg-amber-950', text: 'text-amber-400' },
}

export function MeshFeed({ messages }: MeshFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [isPaused, setIsPaused] = useState(false)

  useEffect(() => {
    if (!isPaused && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isPaused])

  return (
    <div className='rounded-lg border bg-card overflow-hidden'>
      <div className='flex items-center justify-between px-4 py-3 border-b border-border'>
        <span className='text-xs font-semibold text-muted-foreground uppercase tracking-wider'>
          Mesh Feed
        </span>
        <span className='text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 border border-green-500/30 text-green-500 font-medium'>
          LIVE
        </span>
      </div>
      <div
        ref={scrollRef}
        className='px-4 py-2 max-h-64 overflow-y-auto'
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        {messages.map((m, i) => {
          const style = channelStyles[m.channel] ?? channelStyles.PRIMARY
          return (
            <div
              key={m.id}
              className={cn(
                'py-2',
                i < messages.length - 1 && 'border-b border-zinc-800/50'
              )}
            >
              <div className='flex items-center gap-1.5 mb-1'>
                <span className='text-xs font-semibold text-zinc-200'>
                  {m.from}
                </span>
                <span
                  className={cn(
                    'text-[9px] px-1.5 py-px rounded font-semibold uppercase tracking-wider',
                    style.bg,
                    style.text
                  )}
                >
                  {m.channel}
                </span>
                <span className='text-[10px] text-zinc-600 ml-auto font-mono tabular-nums'>
                  {m.time}
                </span>
              </div>
              <div className='text-xs text-muted-foreground leading-relaxed'>
                {m.msg}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export type { MeshMessage, MeshFeedProps }
