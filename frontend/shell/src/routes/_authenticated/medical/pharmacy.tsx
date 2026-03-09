import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { AlertTriangle, Pill } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/medical/pharmacy')({
  component: Pharmacy,
})

interface Medication {
  id: number; name: string; qty: number; lot: string; expires: string; location: string; status: 'in-stock' | 'low' | 'critical'
}

const MEDICATIONS: Medication[] = [
  { id: 1, name: 'Amoxicillin 500mg', qty: 120, lot: 'AMX-2024-A', expires: 'Mar 25, 2026', location: 'Cabinet A', status: 'in-stock' },
  { id: 2, name: 'Ibuprofen 200mg', qty: 23, lot: 'IBU-2024-C', expires: 'Dec 2026', location: 'Cabinet A', status: 'critical' },
  { id: 3, name: 'Metformin 500mg', qty: 60, lot: 'MET-2024-B', expires: 'Jun 2026', location: 'Cabinet B', status: 'in-stock' },
  { id: 4, name: 'Epinephrine Auto-Injector', qty: 4, lot: 'EPI-2024-A', expires: 'Apr 15, 2026', location: 'Emergency Kit', status: 'low' },
  { id: 5, name: 'Suture Kit (4-0 Silk)', qty: 15, lot: 'SUT-2024-D', expires: 'Jan 2027', location: 'Procedure Room', status: 'in-stock' },
  { id: 6, name: 'Lidocaine 1%', qty: 8, lot: 'LID-2024-B', expires: 'May 2026', location: 'Procedure Room', status: 'low' },
  { id: 7, name: 'Tetanus Toxoid', qty: 3, lot: 'TET-2023-A', expires: 'Mar 15, 2026', location: 'Refrigerator', status: 'critical' },
]

const statusColor: Record<Medication['status'], string> = {
  'in-stock': 'bg-green-500/10 text-green-500',
  low: 'bg-amber-500/10 text-amber-500',
  critical: 'bg-red-500/10 text-red-500',
}

function Pharmacy() {
  const [dispenseOpen, setDispenseOpen] = useState(false)
  const [dispenseMed, setDispenseMed] = useState<Medication | null>(null)

  return (
    <>
      <Header />
      <Main>
        <div className='mb-5'>
          <h1 className='text-[22px] font-bold tracking-tight'>Pharmacy Inventory</h1>
          <p className='text-[13px] text-muted-foreground mt-1'>Medication tracking, dispensing, and expiration alerts</p>
        </div>

        <Alert variant='destructive' className='mb-4'>
          <AlertTriangle className='size-4' />
          <AlertTitle>Expiration Warning</AlertTitle>
          <AlertDescription>Tetanus Toxoid and Amoxicillin 500mg expiring within 30 days</AlertDescription>
        </Alert>

        <div className='rounded-lg border bg-card overflow-hidden'>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Medication</TableHead><TableHead>Qty</TableHead><TableHead>Lot #</TableHead>
                <TableHead>Expiration</TableHead><TableHead>Location</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {MEDICATIONS.map((med) => (
                <TableRow key={med.id}>
                  <TableCell className='font-medium'><div className='flex items-center gap-2'><Pill className='size-4 text-muted-foreground' />{med.name}</div></TableCell>
                  <TableCell className={cn('font-mono tabular-nums', med.status === 'critical' && 'text-red-400 font-semibold')}>{med.qty}</TableCell>
                  <TableCell className='text-muted-foreground font-mono text-xs'>{med.lot}</TableCell>
                  <TableCell className='text-muted-foreground'>{med.expires}</TableCell>
                  <TableCell className='text-muted-foreground'>{med.location}</TableCell>
                  <TableCell><Badge variant='outline' className={cn('border-transparent', statusColor[med.status])}>{med.status}</Badge></TableCell>
                  <TableCell><Button variant='outline' size='sm' onClick={() => { setDispenseMed(med); setDispenseOpen(true) }}>Dispense</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <Dialog open={dispenseOpen} onOpenChange={setDispenseOpen}>
          <DialogContent>
            <DialogHeader><DialogTitle>Dispense: {dispenseMed?.name}</DialogTitle></DialogHeader>
            <div className='space-y-3'>
              <div><Label>Quantity</Label><Input type='number' placeholder='1' min={1} /></div>
              <div><Label>Recipient</Label><Input placeholder='Patient name' /></div>
              <div><Label>Reason</Label><Input placeholder='Reason for dispensing' /></div>
            </div>
            <DialogFooter>
              <Button variant='outline' onClick={() => setDispenseOpen(false)}>Cancel</Button>
              <Button onClick={() => setDispenseOpen(false)}>Dispense</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </Main>
    </>
  )
}
