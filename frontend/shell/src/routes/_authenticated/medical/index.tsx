import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Heart, Plus, Search, Printer } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export const Route = createFileRoute('/_authenticated/medical/')({
  component: PatientRecords,
})

interface Patient {
  id: number
  name: string
  dob: string
  bloodType: string
  allergies: string
  lastVisit: string
  status: 'active' | 'follow-up' | 'inactive'
}

const PATIENTS: Patient[] = [
  { id: 1, name: 'Adams, Sarah', dob: 'May 14, 1985', bloodType: 'A+', allergies: 'Penicillin', lastVisit: 'Mar 7', status: 'active' },
  { id: 2, name: 'Chen, Michael', dob: 'Nov 3, 1972', bloodType: 'O-', allergies: 'None', lastVisit: 'Mar 5', status: 'active' },
  { id: 3, name: 'Williams, Emma', dob: 'Aug 22, 1990', bloodType: 'B+', allergies: 'Sulfa drugs', lastVisit: 'Feb 28', status: 'active' },
  { id: 4, name: 'Johnson, David', dob: 'Feb 8, 1968', bloodType: 'AB+', allergies: 'Latex', lastVisit: 'Mar 8', status: 'follow-up' },
  { id: 5, name: 'Martinez, Sofia', dob: 'Dec 15, 2019', bloodType: 'O+', allergies: 'None', lastVisit: 'Mar 6', status: 'active' },
]

const VITALS = [
  { date: 'Mar 1', temp: 98.6, pulse: 72, systolic: 120, diastolic: 80 },
  { date: 'Mar 3', temp: 99.1, pulse: 78, systolic: 125, diastolic: 82 },
  { date: 'Mar 5', temp: 98.8, pulse: 74, systolic: 118, diastolic: 78 },
  { date: 'Mar 7', temp: 98.4, pulse: 70, systolic: 122, diastolic: 80 },
  { date: 'Mar 9', temp: 98.6, pulse: 72, systolic: 120, diastolic: 79 },
]

const VISITS = [
  { date: 'Mar 7', provider: 'Dr. Garcia', type: 'Follow-up', subjective: 'Patient reports improved symptoms.', objective: 'Vitals stable.', assessment: 'Recovering well.', plan: 'Continue current medication.' },
  { date: 'Feb 28', provider: 'Dr. Garcia', type: 'Sick visit', subjective: 'Fever and chills x2 days.', objective: 'Temp 101.2, elevated pulse.', assessment: 'Possible URI.', plan: 'Rest, fluids, recheck in 1 week.' },
]

const MEDICATIONS = [
  { name: 'Amoxicillin 500mg', dosage: '500mg', frequency: '3x daily', start: 'Feb 28', end: 'Mar 7', prescriber: 'Dr. Garcia' },
  { name: 'Ibuprofen 200mg', dosage: '400mg', frequency: 'As needed', start: 'Feb 28', end: '\u2014', prescriber: 'Dr. Garcia' },
]

const statusColor: Record<Patient['status'], string> = {
  active: 'bg-green-500/10 text-green-500',
  'follow-up': 'bg-amber-500/10 text-amber-500',
  inactive: 'bg-zinc-500/10 text-zinc-500',
}

function PatientRecords() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)
  const filtered = PATIENTS.filter((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase()))

  return (
    <>
      <Header />
      <Main>
        <div className='mb-5'>
          <div className='flex items-center justify-between'>
            <div>
              <h1 className='text-[22px] font-bold tracking-tight'>Patient Records</h1>
              <p className='text-[13px] text-muted-foreground mt-1'>Manage patient health records and visits</p>
            </div>
            <div className='flex items-center gap-2'>
              <Button variant='outline' size='sm'><Plus className='size-4 mr-1' /> New Patient</Button>
              <Button size='sm'><Heart className='size-4 mr-1' /> New Visit</Button>
            </div>
          </div>
        </div>

        <div className='relative max-w-sm mb-4'>
          <Search className='absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground' />
          <Input placeholder='Search patients...' value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className='pl-9' />
        </div>

        <div className='rounded-lg border bg-card overflow-hidden'>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>DOB</TableHead>
                <TableHead>Blood Type</TableHead>
                <TableHead>Allergies</TableHead>
                <TableHead>Last Visit</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((patient) => (
                <TableRow key={patient.id} className='cursor-pointer' onClick={() => setSelectedPatient(patient)}>
                  <TableCell className='font-medium'>{patient.name}</TableCell>
                  <TableCell className='text-muted-foreground'>{patient.dob}</TableCell>
                  <TableCell className='font-mono'>{patient.bloodType}</TableCell>
                  <TableCell className='text-muted-foreground'>{patient.allergies}</TableCell>
                  <TableCell className='text-muted-foreground'>{patient.lastVisit}</TableCell>
                  <TableCell><Badge variant='outline' className={cn('border-transparent', statusColor[patient.status])}>{patient.status}</Badge></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <Sheet open={!!selectedPatient} onOpenChange={() => setSelectedPatient(null)}>
          <SheetContent className='sm:max-w-xl overflow-y-auto'>
            {selectedPatient && (
              <>
                <SheetHeader><SheetTitle>{selectedPatient.name}</SheetTitle></SheetHeader>
                <div className='mt-4 p-3 rounded-lg bg-muted/50 grid grid-cols-2 gap-2 text-sm'>
                  <div><span className='text-muted-foreground'>DOB:</span> {selectedPatient.dob}</div>
                  <div><span className='text-muted-foreground'>Blood:</span> <span className='font-mono font-semibold'>{selectedPatient.bloodType}</span></div>
                  <div className='col-span-2'><span className='text-muted-foreground'>Allergies:</span> <span className='text-red-400 font-medium'>{selectedPatient.allergies}</span></div>
                </div>
                <Tabs defaultValue='visits' className='mt-4'>
                  <TabsList className='w-full'>
                    <TabsTrigger value='visits' className='flex-1'>Visits</TabsTrigger>
                    <TabsTrigger value='medications' className='flex-1'>Medications</TabsTrigger>
                    <TabsTrigger value='vitals' className='flex-1'>Vitals</TabsTrigger>
                    <TabsTrigger value='documents' className='flex-1'>Documents</TabsTrigger>
                  </TabsList>
                  <TabsContent value='visits' className='space-y-3 mt-3'>
                    {VISITS.map((v, i) => (
                      <Card key={i}>
                        <CardHeader className='pb-2'>
                          <div className='flex justify-between items-center'>
                            <CardTitle className='text-sm'>{v.type}</CardTitle>
                            <span className='text-xs text-muted-foreground'>{v.date} — {v.provider}</span>
                          </div>
                        </CardHeader>
                        <CardContent className='text-xs space-y-1.5'>
                          <div><strong className='text-muted-foreground'>S:</strong> {v.subjective}</div>
                          <div><strong className='text-muted-foreground'>O:</strong> {v.objective}</div>
                          <div><strong className='text-muted-foreground'>A:</strong> {v.assessment}</div>
                          <div><strong className='text-muted-foreground'>P:</strong> {v.plan}</div>
                        </CardContent>
                      </Card>
                    ))}
                  </TabsContent>
                  <TabsContent value='medications' className='mt-3'>
                    <Table>
                      <TableHeader><TableRow><TableHead>Medication</TableHead><TableHead>Dosage</TableHead><TableHead>Frequency</TableHead><TableHead>Dates</TableHead></TableRow></TableHeader>
                      <TableBody>
                        {MEDICATIONS.map((m, i) => (
                          <TableRow key={i}><TableCell className='font-medium'>{m.name}</TableCell><TableCell>{m.dosage}</TableCell><TableCell>{m.frequency}</TableCell><TableCell className='text-muted-foreground'>{m.start} — {m.end}</TableCell></TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TabsContent>
                  <TabsContent value='vitals' className='mt-3'>
                    <div className='h-64'>
                      <ResponsiveContainer width='100%' height='100%'>
                        <LineChart data={VITALS}>
                          <CartesianGrid strokeDasharray='3 3' stroke='#27272a' />
                          <XAxis dataKey='date' tick={{ fill: '#71717a', fontSize: 11 }} />
                          <YAxis tick={{ fill: '#71717a', fontSize: 11 }} />
                          <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }} />
                          <Line type='monotone' dataKey='pulse' stroke='#ef4444' strokeWidth={2} dot={false} />
                          <Line type='monotone' dataKey='systolic' stroke='#3b82f6' strokeWidth={2} dot={false} />
                          <Line type='monotone' dataKey='diastolic' stroke='#60a5fa' strokeWidth={2} dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </TabsContent>
                  <TabsContent value='documents' className='mt-3'>
                    <div className='text-center py-8 text-muted-foreground text-sm'>No documents attached.</div>
                    <div className='flex justify-center'><Button variant='outline' size='sm'><Printer className='size-4 mr-1' /> Print Summary</Button></div>
                  </TabsContent>
                </Tabs>
              </>
            )}
          </SheetContent>
        </Sheet>
      </Main>
    </>
  )
}
