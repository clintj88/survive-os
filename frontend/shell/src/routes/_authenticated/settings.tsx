import { createFileRoute } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Settings as SettingsIcon, Download, HardDrive } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/settings')({
  component: Settings,
})

const MODULES = [
  { name: 'Communications', port: 8010, enabled: true, health: 'healthy' },
  { name: 'Security', port: 8020, enabled: true, health: 'healthy' },
  { name: 'Agriculture', port: 8030, enabled: true, health: 'healthy' },
  { name: 'Medical', port: 8040, enabled: true, health: 'healthy' },
  { name: 'Resources', port: 8050, enabled: true, health: 'healthy' },
  { name: 'Maps', port: 8060, enabled: true, health: 'degraded' },
  { name: 'Governance', port: 8070, enabled: true, health: 'healthy' },
  { name: 'Weather', port: 8080, enabled: true, health: 'healthy' },
  { name: 'Education', port: 8090, enabled: false, health: 'offline' },
]

const BACKUPS = [
  { date: 'Mar 9, 2026 02:00', size: '1.2 GB', type: 'Full', status: 'complete' },
  { date: 'Mar 8, 2026 02:00', size: '245 MB', type: 'Incremental', status: 'complete' },
  { date: 'Mar 7, 2026 02:00', size: '198 MB', type: 'Incremental', status: 'complete' },
  { date: 'Mar 2, 2026 02:00', size: '1.1 GB', type: 'Full', status: 'complete' },
]

function Settings() {
  return (
    <>
      <Header />
      <Main>
        <div className='mb-5'>
          <h1 className='text-[22px] font-bold tracking-tight'>Settings</h1>
          <p className='text-[13px] text-muted-foreground mt-1'>System configuration and administration</p>
        </div>

        <div className='space-y-4 max-w-3xl'>
          {/* System */}
          <Card>
            <CardHeader><CardTitle className='text-sm'>System</CardTitle></CardHeader>
            <CardContent className='space-y-3'>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>Hostname</span><span className='font-mono'>survive-hub-main</span></div>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>Timezone</span><span>America/Denver (MST)</span></div>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>Network</span><span className='text-green-500'>Connected (192.168.1.1)</span></div>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>NTP Status</span><span>GPS-synced, drift &lt;50ms</span></div>
            </CardContent>
          </Card>

          {/* Display */}
          <Card>
            <CardHeader><CardTitle className='text-sm'>Display</CardTitle></CardHeader>
            <CardContent className='space-y-4'>
              <div>
                <Label className='text-xs text-muted-foreground mb-2 block'>Theme</Label>
                <div className='flex gap-2'>
                  <Button variant='default' size='sm'>Dark</Button>
                  <Button variant='outline' size='sm'>Light</Button>
                  <Button variant='outline' size='sm'>System</Button>
                </div>
              </div>
              <div>
                <Label className='text-xs text-muted-foreground mb-2 block'>Font Size</Label>
                <div className='flex gap-2'>
                  <Button variant='outline' size='sm'>Small</Button>
                  <Button variant='default' size='sm'>Normal</Button>
                  <Button variant='outline' size='sm'>Large</Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Modules */}
          <Card>
            <CardHeader><CardTitle className='text-sm'>Modules</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader><TableRow><TableHead>Module</TableHead><TableHead>Port</TableHead><TableHead>Enabled</TableHead><TableHead>Health</TableHead></TableRow></TableHeader>
                <TableBody>
                  {MODULES.map((m) => (
                    <TableRow key={m.name}>
                      <TableCell className='font-medium'>{m.name}</TableCell>
                      <TableCell className='font-mono text-muted-foreground'>{m.port}</TableCell>
                      <TableCell><Switch defaultChecked={m.enabled} /></TableCell>
                      <TableCell><Badge variant='outline' className={m.health === 'healthy' ? 'bg-green-500/10 text-green-500 border-transparent' : m.health === 'degraded' ? 'bg-amber-500/10 text-amber-500 border-transparent' : 'bg-zinc-500/10 text-zinc-500 border-transparent'}>{m.health}</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Backup */}
          <Card>
            <CardHeader className='flex flex-row items-center justify-between'>
              <CardTitle className='text-sm'>Backup</CardTitle>
              <Button size='sm'><Download className='size-4 mr-1' /> Create Backup</Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Size</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                <TableBody>
                  {BACKUPS.map((b, i) => (
                    <TableRow key={i}><TableCell className='text-xs'>{b.date}</TableCell><TableCell className='font-mono'>{b.size}</TableCell><TableCell>{b.type}</TableCell><TableCell><Badge variant='outline' className='bg-green-500/10 text-green-500 border-transparent'>{b.status}</Badge></TableCell></TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* About */}
          <Card>
            <CardHeader><CardTitle className='text-sm'>About</CardTitle></CardHeader>
            <CardContent className='space-y-2'>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>Version</span><span className='font-mono'>1.0.0-alpha</span></div>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>Build</span><span className='font-mono'>2026-03-09</span></div>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>Node ID</span><span className='font-mono'>HUB-MAIN</span></div>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>Hardware</span><span>Raspberry Pi 4 (4GB)</span></div>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>Uptime</span><span className='font-mono tabular-nums'>14d 7h 23m</span></div>
              <div className='flex justify-between text-sm'><span className='text-muted-foreground'>License</span><span>GPL-3.0</span></div>
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
