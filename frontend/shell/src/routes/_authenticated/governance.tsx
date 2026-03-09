import { createFileRoute } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Scale, ThumbsUp, ThumbsDown, Minus } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/governance')({
  component: Governance,
})

const CENSUS = [
  { id: 1, name: 'Johnson, Craig', age: 42, role: 'Community Lead', household: 'Johnson', skills: 'Leadership, Engineering', joined: 'Day 1' },
  { id: 2, name: 'Garcia, Maria', age: 38, role: 'Medical Officer', household: 'Garcia', skills: 'Medicine, Herbalism', joined: 'Day 1' },
  { id: 3, name: 'Thompson, Alex', age: 35, role: 'Agriculture Lead', household: 'Thompson', skills: 'Farming, Irrigation', joined: 'Day 3' },
  { id: 4, name: 'Martinez, Rosa', age: 29, role: 'Security', household: 'Martinez', skills: 'Tactical, Communications', joined: 'Day 1' },
  { id: 5, name: 'Chen, Wei', age: 45, role: 'Engineer', household: 'Chen', skills: 'Solar, Electronics', joined: 'Day 7' },
]

const PROPOSALS = [
  { id: 1, title: 'Expand south field irrigation', description: 'Allocate resources to extend drip irrigation to Field C plots', deadline: 'Mar 15', yes: 89, no: 12, abstain: 8, status: 'active' as const },
  { id: 2, title: 'Establish trade route to Loveland', description: 'Monthly trade caravan with security escort', deadline: 'Mar 20', yes: 67, no: 34, abstain: 15, status: 'active' as const },
]

const ALLOCATIONS = [
  { resource: 'Water', daily: '50 gal', perPerson: '0.34 gal', reserveDays: 28 },
  { resource: 'Food', daily: '32 person-days', perPerson: '1 ration', reserveDays: 28 },
  { resource: 'Fuel', daily: '2 gal', perPerson: 'N/A', reserveDays: 24 },
]

const TREATIES = [
  { partner: 'Berthoud Community', title: 'Mutual Defense Pact', status: 'active', date: 'Jan 2026', summary: 'Joint defense within 10mi radius' },
  { partner: 'Fort Collins Co-op', title: 'Trade Agreement', status: 'active', date: 'Feb 2026', summary: 'Monthly trade with price schedule' },
  { partner: 'Loveland Collective', title: 'Communication Sharing', status: 'draft', date: 'Mar 2026', summary: 'Shared mesh relay network' },
]

const DISPUTES = [
  { case: 'D-001', filedBy: 'Rivera, D.', against: 'Thompson, A.', type: 'Resource', status: 'mediation', filed: 'Mar 3' },
  { case: 'D-002', filedBy: 'Anonymous', against: 'Security Team', type: 'Conduct', status: 'open', filed: 'Mar 7' },
]

function Governance() {
  return (
    <>
      <Header />
      <Main>
        <div className='mb-5'>
          <div className='flex items-center justify-between'>
            <div>
              <h1 className='text-[22px] font-bold tracking-tight'>Community Council</h1>
              <p className='text-[13px] text-muted-foreground mt-1'>Census, voting, resource allocation, and governance</p>
            </div>
            <Button size='sm'><Scale className='size-4 mr-1' /> New Proposal</Button>
          </div>
        </div>

        <Tabs defaultValue='census'>
          <TabsList>
            <TabsTrigger value='census'>Census</TabsTrigger>
            <TabsTrigger value='voting'>Voting</TabsTrigger>
            <TabsTrigger value='allocation'>Allocation</TabsTrigger>
            <TabsTrigger value='treaties'>Treaties</TabsTrigger>
            <TabsTrigger value='disputes'>Disputes</TabsTrigger>
          </TabsList>

          <TabsContent value='census' className='mt-4 space-y-4'>
            <div className='grid grid-cols-4 gap-3'>
              {[{ l: 'Total Population', v: '147' }, { l: 'Adults (18+)', v: '112' }, { l: 'Children', v: '35' }, { l: 'New (30d)', v: '2' }].map((s, i) => (
                <Card key={i}><CardContent className='pt-4'><div className='text-xs text-muted-foreground mb-1'>{s.l}</div><div className='text-2xl font-bold tabular-nums'>{s.v}</div></CardContent></Card>
              ))}
            </div>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Age</TableHead><TableHead>Role</TableHead><TableHead>Household</TableHead><TableHead>Skills</TableHead><TableHead>Joined</TableHead></TableRow></TableHeader>
                <TableBody>
                  {CENSUS.map((p) => (<TableRow key={p.id}><TableCell className='font-medium'>{p.name}</TableCell><TableCell>{p.age}</TableCell><TableCell>{p.role}</TableCell><TableCell>{p.household}</TableCell><TableCell className='text-muted-foreground text-xs'>{p.skills}</TableCell><TableCell className='text-muted-foreground'>{p.joined}</TableCell></TableRow>))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value='voting' className='mt-4 space-y-4'>
            {PROPOSALS.map((p) => {
              const total = p.yes + p.no + p.abstain
              return (
                <Card key={p.id}>
                  <CardHeader><CardTitle className='text-sm'>{p.title}</CardTitle></CardHeader>
                  <CardContent className='space-y-3'>
                    <p className='text-xs text-muted-foreground'>{p.description}</p>
                    <div className='flex gap-1 h-3 rounded-full overflow-hidden'>
                      <div className='bg-green-500' style={{ width: `${(p.yes / total) * 100}%` }} />
                      <div className='bg-red-500' style={{ width: `${(p.no / total) * 100}%` }} />
                      <div className='bg-zinc-600' style={{ width: `${(p.abstain / total) * 100}%` }} />
                    </div>
                    <div className='flex gap-4 text-xs'>
                      <span className='text-green-500'><ThumbsUp className='size-3 inline mr-1' />{p.yes} Yes</span>
                      <span className='text-red-500'><ThumbsDown className='size-3 inline mr-1' />{p.no} No</span>
                      <span className='text-zinc-500'><Minus className='size-3 inline mr-1' />{p.abstain} Abstain</span>
                      <span className='ml-auto text-muted-foreground'>Deadline: {p.deadline}</span>
                    </div>
                    <div className='flex gap-2'>
                      <Button size='sm' variant='outline' className='text-green-500'>Vote Yes</Button>
                      <Button size='sm' variant='outline' className='text-red-500'>Vote No</Button>
                      <Button size='sm' variant='outline'>Abstain</Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </TabsContent>

          <TabsContent value='allocation' className='mt-4'>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Resource</TableHead><TableHead>Daily Allocation</TableHead><TableHead>Per Person</TableHead><TableHead>Reserve Days</TableHead></TableRow></TableHeader>
                <TableBody>
                  {ALLOCATIONS.map((a, i) => (<TableRow key={i}><TableCell className='font-medium'>{a.resource}</TableCell><TableCell>{a.daily}</TableCell><TableCell>{a.perPerson}</TableCell><TableCell className='tabular-nums'>{a.reserveDays}</TableCell></TableRow>))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value='treaties' className='mt-4'>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Partner</TableHead><TableHead>Title</TableHead><TableHead>Status</TableHead><TableHead>Date</TableHead><TableHead>Summary</TableHead></TableRow></TableHeader>
                <TableBody>
                  {TREATIES.map((t, i) => (<TableRow key={i}><TableCell className='font-medium'>{t.partner}</TableCell><TableCell>{t.title}</TableCell><TableCell><Badge variant='outline' className={t.status === 'active' ? 'bg-green-500/10 text-green-500 border-transparent' : 'bg-amber-500/10 text-amber-500 border-transparent'}>{t.status}</Badge></TableCell><TableCell className='text-muted-foreground'>{t.date}</TableCell><TableCell className='text-muted-foreground text-xs'>{t.summary}</TableCell></TableRow>))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value='disputes' className='mt-4'>
            <div className='rounded-lg border bg-card overflow-hidden'>
              <Table>
                <TableHeader><TableRow><TableHead>Case #</TableHead><TableHead>Filed By</TableHead><TableHead>Against</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Filed</TableHead></TableRow></TableHeader>
                <TableBody>
                  {DISPUTES.map((d, i) => (<TableRow key={i}><TableCell className='font-mono'>{d.case}</TableCell><TableCell>{d.filedBy}</TableCell><TableCell>{d.against}</TableCell><TableCell>{d.type}</TableCell><TableCell><Badge variant='outline' className={d.status === 'open' ? 'bg-blue-500/10 text-blue-500 border-transparent' : 'bg-amber-500/10 text-amber-500 border-transparent'}>{d.status}</Badge></TableCell><TableCell className='text-muted-foreground'>{d.filed}</TableCell></TableRow>))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}
