import { createFileRoute } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { UserCog, Plus, CreditCard, Search } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/identity')({
  component: IdentityAdmin,
})

const USERS = [
  { id: 1, username: 'cjohnson', name: 'Johnson, Craig', roles: ['admin'], status: 'online' as const, lastLogin: 'Mar 9 14:30' },
  { id: 2, username: 'mgarcia', name: 'Garcia, Maria', roles: ['medical'], status: 'online' as const, lastLogin: 'Mar 9 13:45' },
  { id: 3, username: 'athompson', name: 'Thompson, Alex', roles: ['agriculture'], status: 'offline' as const, lastLogin: 'Mar 8 18:00' },
  { id: 4, username: 'rmartinez', name: 'Martinez, Rosa', roles: ['security'], status: 'online' as const, lastLogin: 'Mar 9 06:00' },
  { id: 5, username: 'wchen', name: 'Chen, Wei', roles: ['operator'], status: 'offline' as const, lastLogin: 'Mar 7 22:15' },
]

const ROLES = [
  { name: 'admin', description: 'Full system access', members: 1, permissions: 'All' },
  { name: 'security', description: 'Security operations', members: 3, permissions: 'Security, Comms, Alerts' },
  { name: 'medical', description: 'Medical records access', members: 2, permissions: 'Medical, Pharmacy' },
  { name: 'governance', description: 'Council operations', members: 4, permissions: 'Governance, Census' },
  { name: 'agriculture', description: 'Agriculture management', members: 5, permissions: 'Crops, Livestock, Seeds' },
  { name: 'operator', description: 'Basic system operator', members: 8, permissions: 'Comms, Inventory, Maps' },
]

const BADGES = [
  { id: 'NFC-001', assignedTo: 'Johnson, Craig', status: 'active' as const, zones: 'All Zones', lastUsed: 'Mar 9 14:30' },
  { id: 'NFC-002', assignedTo: 'Garcia, Maria', status: 'active' as const, zones: 'Medical, Main', lastUsed: 'Mar 9 13:45' },
  { id: 'NFC-003', assignedTo: 'Martinez, Rosa', status: 'active' as const, zones: 'Security, Armory, Main', lastUsed: 'Mar 9 06:00' },
  { id: 'NFC-010', assignedTo: '\u2014', status: 'unassigned' as const, zones: '\u2014', lastUsed: '\u2014' },
  { id: 'NFC-005', assignedTo: 'Former member', status: 'revoked' as const, zones: '\u2014', lastUsed: 'Feb 15' },
]

const ZONES = [
  { name: 'Main Building', type: 'Building', access: 'All roles', badge: true, status: 'active' },
  { name: 'Medical Clinic', type: 'Restricted', access: 'medical, admin', badge: true, status: 'active' },
  { name: 'Armory', type: 'Restricted', access: 'security, admin', badge: true, status: 'active' },
  { name: 'Generator Room', type: 'Infrastructure', access: 'operator, admin', badge: true, status: 'active' },
  { name: 'Water Treatment', type: 'Infrastructure', access: 'operator, admin', badge: true, status: 'active' },
  { name: 'Perimeter Gates', type: 'Access Point', access: 'All roles', badge: false, status: 'active' },
]

const AUDIT = [
  { id: 1, time: 'Mar 9 14:30', user: 'cjohnson', action: 'Login', resource: 'System', result: 'success' as const },
  { id: 2, time: 'Mar 9 14:15', user: 'rmartinez', action: 'Access Zone', resource: 'Armory', result: 'success' as const },
  { id: 3, time: 'Mar 9 13:50', user: 'mgarcia', action: 'View Record', resource: 'Patient: Adams, S.', result: 'success' as const },
  { id: 4, time: 'Mar 9 12:00', user: 'unknown', action: 'Login Attempt', resource: 'System', result: 'denied' as const },
  { id: 5, time: 'Mar 9 11:30', user: 'athompson', action: 'Update', resource: 'Plot: Field A-1', result: 'success' as const },
]

const badgeStatusColor = { active: 'bg-green-500/10 text-green-500', unassigned: 'bg-zinc-500/10 text-zinc-500', revoked: 'bg-red-500/10 text-red-500' }
const resultColor = { success: 'bg-green-500/10 text-green-500', denied: 'bg-red-500/10 text-red-500', error: 'bg-amber-500/10 text-amber-500' }

function IdentityAdmin() {
  return (
    <>
      <Header />
      <Main>
        <div className='mb-5'>
          <div className='flex items-center justify-between'>
            <div>
              <h1 className='text-[22px] font-bold tracking-tight'>Identity & Access</h1>
              <p className='text-[13px] text-muted-foreground mt-1'>User management, roles, badges, and access control</p>
            </div>
            <div className='flex items-center gap-2'>
              <Button variant='outline' size='sm'><CreditCard className='size-4 mr-1' /> Add Badge</Button>
              <Button size='sm'><Plus className='size-4 mr-1' /> Add User</Button>
            </div>
          </div>
        </div>

        <Tabs defaultValue='users'>
          <TabsList>
            <TabsTrigger value='users'>Users</TabsTrigger>
            <TabsTrigger value='roles'>Roles</TabsTrigger>
            <TabsTrigger value='badges'>Badges</TabsTrigger>
            <TabsTrigger value='zones'>Zones</TabsTrigger>
            <TabsTrigger value='audit'>Audit Log</TabsTrigger>
          </TabsList>

          <TabsContent value='users' className='mt-4'>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Username</TableHead><TableHead>Display Name</TableHead><TableHead>Roles</TableHead><TableHead>Status</TableHead><TableHead>Last Login</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
                <TableBody>
                  {USERS.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell className='font-mono'>{u.username}</TableCell>
                      <TableCell className='font-medium'>{u.name}</TableCell>
                      <TableCell><div className='flex gap-1'>{u.roles.map((r) => (<Badge key={r} variant='outline' className='text-[10px] border-transparent bg-muted'>{r}</Badge>))}</div></TableCell>
                      <TableCell><span className={cn('inline-flex items-center gap-1.5 text-xs', u.status === 'online' ? 'text-green-500' : 'text-zinc-500')}><span className={cn('size-1.5 rounded-full', u.status === 'online' ? 'bg-green-500' : 'bg-zinc-500')} />{u.status}</span></TableCell>
                      <TableCell className='text-muted-foreground text-xs'>{u.lastLogin}</TableCell>
                      <TableCell><Button variant='ghost' size='sm'>Edit</Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value='roles' className='mt-4'>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Role</TableHead><TableHead>Description</TableHead><TableHead>Members</TableHead><TableHead>Permissions</TableHead></TableRow></TableHeader>
                <TableBody>{ROLES.map((r) => (<TableRow key={r.name}><TableCell className='font-mono font-medium'>{r.name}</TableCell><TableCell>{r.description}</TableCell><TableCell className='tabular-nums'>{r.members}</TableCell><TableCell className='text-muted-foreground text-xs'>{r.permissions}</TableCell></TableRow>))}</TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value='badges' className='mt-4'>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Badge ID</TableHead><TableHead>Assigned To</TableHead><TableHead>Status</TableHead><TableHead>Zone Access</TableHead><TableHead>Last Used</TableHead></TableRow></TableHeader>
                <TableBody>{BADGES.map((b) => (<TableRow key={b.id}><TableCell className='font-mono'>{b.id}</TableCell><TableCell>{b.assignedTo}</TableCell><TableCell><Badge variant='outline' className={cn('border-transparent', badgeStatusColor[b.status])}>{b.status}</Badge></TableCell><TableCell className='text-muted-foreground text-xs'>{b.zones}</TableCell><TableCell className='text-muted-foreground'>{b.lastUsed}</TableCell></TableRow>))}</TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value='zones' className='mt-4'>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Zone</TableHead><TableHead>Type</TableHead><TableHead>Access Level</TableHead><TableHead>Badge Required</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                <TableBody>{ZONES.map((z, i) => (<TableRow key={i}><TableCell className='font-medium'>{z.name}</TableCell><TableCell>{z.type}</TableCell><TableCell className='text-xs text-muted-foreground'>{z.access}</TableCell><TableCell>{z.badge ? 'Yes' : 'No'}</TableCell><TableCell><Badge variant='outline' className='bg-green-500/10 text-green-500 border-transparent'>active</Badge></TableCell></TableRow>))}</TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value='audit' className='mt-4'>
            <div className='relative max-w-sm mb-3'>
              <Search className='absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground' />
              <Input placeholder='Search audit log...' className='pl-9' />
            </div>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Timestamp</TableHead><TableHead>User</TableHead><TableHead>Action</TableHead><TableHead>Resource</TableHead><TableHead>Result</TableHead></TableRow></TableHeader>
                <TableBody>{AUDIT.map((a) => (<TableRow key={a.id}><TableCell className='font-mono text-xs'>{a.time}</TableCell><TableCell className='font-mono'>{a.user}</TableCell><TableCell>{a.action}</TableCell><TableCell className='text-muted-foreground'>{a.resource}</TableCell><TableCell><Badge variant='outline' className={cn('border-transparent', resultColor[a.result])}>{a.result}</Badge></TableCell></TableRow>))}</TableBody>
              </Table>
            </div>
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}
