import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  Globe,
  HardDrive,
  Monitor,
  Palette,
  Server,
  Settings2,
  Type,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { ThemeSwitch } from '@/components/theme-switch'
import { cn } from '@/lib/utils'

export const Route = createFileRoute('/_authenticated/system-settings')({
  component: SettingsView,
})

/* ---------- inline helpers ---------- */

function PageHeader({
  title,
  description,
  actions,
}: {
  title: string
  description?: string
  actions?: React.ReactNode
}) {
  return (
    <div className='mb-5'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-[22px] font-bold tracking-tight'>{title}</h1>
          {description && (
            <p className='mt-1 text-[13px] text-muted-foreground'>
              {description}
            </p>
          )}
        </div>
        {actions && <div className='flex items-center gap-2'>{actions}</div>}
      </div>
    </div>
  )
}

/* ---------- role check ---------- */

function useHasRole(_roles: string[]): boolean {
  return true
}

/* ---------- types ---------- */

interface Module {
  name: string
  port: number
  description: string
  enabled: boolean
  status: 'running' | 'stopped' | 'error'
}

interface BackupEntry {
  id: string
  timestamp: string
  size: string
  modules: number
  status: 'completed' | 'failed' | 'in-progress'
}

/* ---------- mock data ---------- */

const modules: Module[] = [
  { name: 'Communication', port: 8010, description: 'BBS, Ham Radio, Meshtastic', enabled: true, status: 'running' },
  { name: 'Security', port: 8020, description: 'Perimeter monitoring, drone ops', enabled: true, status: 'running' },
  { name: 'Agriculture', port: 8030, description: 'Crop management, irrigation', enabled: true, status: 'running' },
  { name: 'Medical', port: 8040, description: 'Patient records, pharmacy', enabled: true, status: 'running' },
  { name: 'Resources', port: 8050, description: 'Inventory management', enabled: true, status: 'running' },
  { name: 'Maps', port: 8060, description: 'Offline mapping, TileServer GL', enabled: true, status: 'running' },
  { name: 'Governance', port: 8070, description: 'Census, voting, disputes', enabled: true, status: 'running' },
  { name: 'Weather', port: 8080, description: 'Local weather monitoring', enabled: false, status: 'stopped' },
  { name: 'Education', port: 8090, description: 'Knowledge base, curriculum', enabled: true, status: 'running' },
]

const backups: BackupEntry[] = [
  { id: 'BKP-001', timestamp: '2026-03-09 06:00:00', size: '2.4 GB', modules: 9, status: 'completed' },
  { id: 'BKP-002', timestamp: '2026-03-08 06:00:00', size: '2.3 GB', modules: 9, status: 'completed' },
  { id: 'BKP-003', timestamp: '2026-03-07 06:00:00', size: '2.3 GB', modules: 9, status: 'completed' },
  { id: 'BKP-004', timestamp: '2026-03-06 06:00:00', size: '2.2 GB', modules: 8, status: 'failed' },
  { id: 'BKP-005', timestamp: '2026-03-05 06:00:00', size: '2.2 GB', modules: 9, status: 'completed' },
]

const moduleStatusConfig: Record<Module['status'], { label: string; className: string }> = {
  running: { label: 'Running', className: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
  stopped: { label: 'Stopped', className: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20' },
  error: { label: 'Error', className: 'bg-red-500/10 text-red-500 border-red-500/20' },
}

const backupStatusConfig: Record<BackupEntry['status'], { label: string; className: string }> = {
  completed: { label: 'Completed', className: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
  failed: { label: 'Failed', className: 'bg-red-500/10 text-red-500 border-red-500/20' },
  'in-progress': { label: 'In Progress', className: 'bg-blue-500/10 text-blue-500 border-blue-500/20' },
}

/* ---------- main component ---------- */

function SettingsView() {
  const hasRole = useHasRole(['admin'])
  const [hostname, setHostname] = useState('survive-base-01')
  const [timezone, setTimezone] = useState('America/Chicago')
  const [theme, setTheme] = useState('dark')
  const [fontSize, setFontSize] = useState('14')
  const [moduleStates, setModuleStates] = useState<Record<string, boolean>>(
    Object.fromEntries(modules.map((m) => [m.name, m.enabled]))
  )

  if (!hasRole) {
    return (
      <>
        <Header>
          <div className='ms-auto flex items-center space-x-4'>
            <ThemeSwitch />
            <ProfileDropdown />
          </div>
        </Header>
        <Main>
          <Card className='mx-auto mt-20 max-w-md border-zinc-800 bg-zinc-900'>
            <CardContent className='pt-6 text-center'>
              <AlertTriangle className='mx-auto mb-3 size-10 text-amber-500' />
              <h2 className='text-lg font-semibold'>Access Denied</h2>
              <p className='mt-1 text-sm text-zinc-400'>
                You do not have the required admin role to access system settings.
              </p>
            </CardContent>
          </Card>
        </Main>
      </>
    )
  }

  const handleModuleToggle = (name: string) => {
    setModuleStates((prev) => ({ ...prev, [name]: !prev[name] }))
  }

  return (
    <>
      <Header>
        <div className='ms-auto flex items-center space-x-4'>
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </Header>

      <Main>
        <PageHeader
          title='System Settings'
          description='Configure system parameters, display preferences, and manage modules.'
          actions={
            <Button size='sm' variant='outline'>
              <Settings2 className='mr-1 size-4' />
              Export Config
            </Button>
          }
        />

        <div className='space-y-6'>
          {/* System Configuration */}
          <Card className='border-zinc-800 bg-zinc-900'>
            <CardHeader className='border-b border-zinc-800'>
              <CardTitle className='flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400'>
                <Server className='size-4' />
                System Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className='pt-6'>
              <div className='grid gap-6 sm:grid-cols-2'>
                <div className='space-y-2'>
                  <Label htmlFor='hostname'>Hostname</Label>
                  <Input
                    id='hostname'
                    value={hostname}
                    onChange={(e) => setHostname(e.target.value)}
                  />
                </div>
                <div className='space-y-2'>
                  <Label htmlFor='timezone'>Timezone</Label>
                  <Select value={timezone} onValueChange={setTimezone}>
                    <SelectTrigger className='w-full'>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value='America/New_York'>
                        America/New_York (EST)
                      </SelectItem>
                      <SelectItem value='America/Chicago'>
                        America/Chicago (CST)
                      </SelectItem>
                      <SelectItem value='America/Denver'>
                        America/Denver (MST)
                      </SelectItem>
                      <SelectItem value='America/Los_Angeles'>
                        America/Los_Angeles (PST)
                      </SelectItem>
                      <SelectItem value='UTC'>UTC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className='mt-4 flex justify-end'>
                <Button size='sm'>Save System Config</Button>
              </div>
            </CardContent>
          </Card>

          {/* Display Settings */}
          <Card className='border-zinc-800 bg-zinc-900'>
            <CardHeader className='border-b border-zinc-800'>
              <CardTitle className='flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400'>
                <Palette className='size-4' />
                Display Settings
              </CardTitle>
            </CardHeader>
            <CardContent className='pt-6'>
              <div className='space-y-6'>
                <div className='space-y-3'>
                  <Label>Theme</Label>
                  <RadioGroup
                    value={theme}
                    onValueChange={setTheme}
                    className='flex gap-4'
                  >
                    <div className='flex items-center gap-2'>
                      <RadioGroupItem value='dark' id='theme-dark' />
                      <Label htmlFor='theme-dark' className='font-normal'>
                        <Monitor className='mr-1 inline size-4' />
                        Dark
                      </Label>
                    </div>
                    <div className='flex items-center gap-2'>
                      <RadioGroupItem value='light' id='theme-light' />
                      <Label htmlFor='theme-light' className='font-normal'>
                        Light
                      </Label>
                    </div>
                    <div className='flex items-center gap-2'>
                      <RadioGroupItem value='system' id='theme-system' />
                      <Label htmlFor='theme-system' className='font-normal'>
                        System
                      </Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className='space-y-2'>
                  <Label>
                    <Type className='mr-1 inline size-4' />
                    Font Size
                  </Label>
                  <Select value={fontSize} onValueChange={setFontSize}>
                    <SelectTrigger className='w-32'>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value='12'>12px</SelectItem>
                      <SelectItem value='13'>13px</SelectItem>
                      <SelectItem value='14'>14px (default)</SelectItem>
                      <SelectItem value='16'>16px</SelectItem>
                      <SelectItem value='18'>18px</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Modules */}
          <Card className='border-zinc-800 bg-zinc-900'>
            <CardHeader className='border-b border-zinc-800'>
              <CardTitle className='flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400'>
                <Cpu className='size-4' />
                Modules
              </CardTitle>
            </CardHeader>
            <CardContent className='p-0'>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Module</TableHead>
                    <TableHead>Port</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className='text-right'>Enabled</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {modules.map((mod) => {
                    const isEnabled = moduleStates[mod.name] ?? mod.enabled
                    const status = isEnabled
                      ? moduleStatusConfig[mod.status]
                      : moduleStatusConfig.stopped
                    return (
                      <TableRow key={mod.name}>
                        <TableCell className='font-medium'>
                          {mod.name}
                        </TableCell>
                        <TableCell className='font-mono text-xs text-zinc-400'>
                          :{mod.port}
                        </TableCell>
                        <TableCell className='text-zinc-400'>
                          {mod.description}
                        </TableCell>
                        <TableCell>
                          <Badge className={status.className}>
                            {isEnabled ? status.label : 'Stopped'}
                          </Badge>
                        </TableCell>
                        <TableCell className='text-right'>
                          <Switch
                            checked={isEnabled}
                            onCheckedChange={() =>
                              handleModuleToggle(mod.name)
                            }
                          />
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Backup History */}
          <Card className='border-zinc-800 bg-zinc-900'>
            <CardHeader className='border-b border-zinc-800'>
              <div className='flex items-center justify-between'>
                <CardTitle className='flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400'>
                  <Database className='size-4' />
                  Backup History
                </CardTitle>
                <Button size='sm' variant='outline'>
                  <HardDrive className='mr-1 size-4' />
                  Backup Now
                </Button>
              </div>
            </CardHeader>
            <CardContent className='p-0'>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead className='text-right'>Modules</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backups.map((backup) => {
                    const status = backupStatusConfig[backup.status]
                    return (
                      <TableRow key={backup.id}>
                        <TableCell className='font-mono text-xs'>
                          {backup.timestamp}
                        </TableCell>
                        <TableCell>{backup.size}</TableCell>
                        <TableCell className='text-right'>
                          {backup.modules}
                        </TableCell>
                        <TableCell>
                          <Badge className={status.className}>
                            {status.label}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* About */}
          <Card className='border-zinc-800 bg-zinc-900'>
            <CardHeader className='border-b border-zinc-800'>
              <CardTitle className='flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400'>
                <Globe className='size-4' />
                About
              </CardTitle>
            </CardHeader>
            <CardContent className='pt-6'>
              <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
                <div>
                  <p className='text-xs text-zinc-400'>Version</p>
                  <p className='font-mono text-sm font-medium text-zinc-100'>
                    v1.0.0-alpha
                  </p>
                </div>
                <div>
                  <p className='text-xs text-zinc-400'>Hardware</p>
                  <p className='text-sm font-medium text-zinc-100'>
                    Raspberry Pi 4 (4GB)
                  </p>
                </div>
                <div>
                  <p className='text-xs text-zinc-400'>Uptime</p>
                  <p className='flex items-center gap-1 text-sm font-medium text-zinc-100'>
                    <Clock className='size-3 text-emerald-500' />
                    14d 6h 32m
                  </p>
                </div>
                <div>
                  <p className='text-xs text-zinc-400'>System Status</p>
                  <p className='flex items-center gap-1 text-sm font-medium text-emerald-400'>
                    <CheckCircle className='size-3' />
                    All systems operational
                  </p>
                </div>
              </div>
              <div className='mt-4 rounded-lg border border-zinc-800 bg-zinc-950 p-3'>
                <p className='font-mono text-xs text-zinc-500'>
                  SURVIVE OS -- Offline-first platform for post-infrastructure communities
                  <br />
                  Built with Debian 12, Python 3.11+, Preact, SQLite, Automerge CRDTs
                  <br />
                  Licensed under AGPLv3
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
