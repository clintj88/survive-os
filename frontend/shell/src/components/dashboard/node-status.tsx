import { cn } from '@/lib/utils'

interface NodeInfo {
  name: string
  status: 'online' | 'degraded' | 'offline'
  type: string
  uptime: string
}

interface NodeStatusProps {
  nodes: NodeInfo[]
}

const statusColors: Record<NodeInfo['status'], string> = {
  online: 'bg-green-500',
  degraded: 'bg-amber-500',
  offline: 'bg-red-500',
}

export function NodeStatus({ nodes }: NodeStatusProps) {
  const onlineCount = nodes.filter((n) => n.status === 'online').length

  return (
    <div className='rounded-lg border bg-card overflow-hidden'>
      <div className='flex items-center justify-between px-4 py-3 border-b border-border'>
        <span className='text-xs font-semibold text-muted-foreground uppercase tracking-wider'>
          Network Nodes
        </span>
        <span className='text-[10px] px-2 py-0.5 rounded-full bg-muted border border-border text-muted-foreground font-medium'>
          {onlineCount} online
        </span>
      </div>
      <div className='px-4 py-2'>
        <div className='grid grid-cols-[1fr_60px_60px] gap-0 text-[10px] text-zinc-600 font-semibold uppercase tracking-wider pb-1.5'>
          <div>Node</div>
          <div>Type</div>
          <div>Uptime</div>
        </div>
        {nodes.map((node, i) => (
          <div
            key={i}
            className={cn(
              'grid grid-cols-[1fr_60px_60px] items-center py-1.5',
              i < nodes.length - 1 && 'border-b border-zinc-800/50'
            )}
          >
            <div className='flex items-center gap-1.5 text-[11px] text-zinc-200 font-mono'>
              <span
                className={cn(
                  'size-1.5 rounded-full shrink-0',
                  statusColors[node.status]
                )}
              />
              {node.name}
            </div>
            <div className='text-xs text-zinc-500'>{node.type}</div>
            <div className='text-xs text-zinc-500 tabular-nums'>
              {node.uptime}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export type { NodeInfo, NodeStatusProps }
