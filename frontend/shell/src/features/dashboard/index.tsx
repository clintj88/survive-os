import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { ThemeSwitch } from '@/components/theme-switch'
import { Search } from '@/components/search'
import {
  StatCard,
  AlertFeed,
  SupplyBars,
  MeshFeed,
  NodeStatus,
  WeatherCard,
} from '@/components/dashboard'
import type { AlertItem } from '@/components/dashboard'
import type { SupplyItem } from '@/components/dashboard'
import type { MeshMessage } from '@/components/dashboard'
import type { NodeInfo } from '@/components/dashboard'
import type { WeatherData } from '@/components/dashboard'

// ── Mock Data ──
const ALERTS: AlertItem[] = [
  { id: 1, level: 'warning', msg: 'Water filter #3 due for replacement', time: '2 hours ago', module: 'inventory' },
  { id: 2, level: 'info', msg: 'Node RELAY-SOUTH battery 34%', time: '3 hours ago', module: 'comms' },
  { id: 3, level: 'success', msg: 'Patrol Alpha completed perimeter sweep', time: '4 hours ago', module: 'security' },
  { id: 4, level: 'info', msg: 'Tomato seedlings ready for transplant', time: '5 hours ago', module: 'agriculture' },
  { id: 5, level: 'warning', msg: 'Ibuprofen below minimum (23 units)', time: '6 hours ago', module: 'pharmacy' },
]

const SUPPLIES: SupplyItem[] = [
  { name: 'Water (gal)', val: 340, max: 500, min: 200 },
  { name: 'Food (person-days)', val: 890, max: 1200, min: 600 },
  { name: 'Medical supplies', val: 67, max: 150, min: 50 },
  { name: 'Fuel (gal)', val: 48, max: 200, min: 100 },
  { name: 'Ammunition', val: 1240, max: 2000, min: 500 },
  { name: 'Seed varieties', val: 34, max: 50, min: 20 },
]

const MESH_MESSAGES: MeshMessage[] = [
  { id: 1, from: 'Johnson, C.', channel: 'PRIMARY', msg: 'Trade team returning from Berthoud, ETA 2hrs', time: '14:45' },
  { id: 2, from: 'WX-STATION-01', channel: 'SENSOR', msg: '42°F | 68% RH | NW 8mph | 30.12 inHg rising', time: '14:30' },
  { id: 3, from: 'Martinez, R.', channel: 'SECURITY', msg: 'Perimeter clear, all sensors nominal', time: '14:15' },
]

const NODES: NodeInfo[] = [
  { name: 'HUB-MAIN', status: 'online', type: 'Hub', uptime: '14d 7h' },
  { name: 'MED-TERMINAL', status: 'online', type: 'Terminal', uptime: '14d 7h' },
  { name: 'AG-SENSOR-01', status: 'online', type: 'Edge', uptime: '6d 3h' },
  { name: 'GATE-CTRL', status: 'online', type: 'Access', uptime: '14d 7h' },
  { name: 'RELAY-SOUTH', status: 'degraded', type: 'Mesh', uptime: '29d' },
  { name: 'DRONE-GND', status: 'offline', type: 'Drone', uptime: '\u2014' },
]

const WEATHER: WeatherData[] = [
  { key: 'Temperature', value: '42\u00b0F' },
  { key: 'Humidity', value: '68%' },
  { key: 'Wind', value: 'NW 8 mph' },
  { key: 'Pressure', value: '30.12 inHg \u2191' },
  { key: 'Clouds', value: 'Cumulus' },
  { key: 'Forecast', value: 'Fair 24h, front 48h' },
]

export function Dashboard() {
  return (
    <>
      <Header>
        <div className='ms-auto flex items-center space-x-4'>
          <Search />
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </Header>

      <Main>
        <div className='max-w-[1200px] mx-auto'>
          {/* Title */}
          <div className='mb-5'>
            <h1 className='text-[22px] font-bold tracking-tight'>
              Command Center
            </h1>
            <p className='text-[13px] text-muted-foreground mt-1'>
              Community operational overview and status
            </p>
          </div>

          {/* Stat Cards */}
          <div className='grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4'>
            <StatCard
              label='Population'
              value='147'
              subtitle='+2 this month'
            />
            <StatCard
              label='Mesh Nodes'
              value='4/6'
              subtitle='1 degraded'
              valueColor='#22c55e'
            />
            <StatCard
              label='Active Alerts'
              value='2'
              subtitle='0 critical'
              valueColor='#f59e0b'
            />
            <StatCard
              label='Days of Water'
              value='28'
              subtitle='340 gallons reserve'
              valueColor='#3b82f6'
            />
          </div>

          {/* Main Grid: Alerts + Supply */}
          <div className='grid grid-cols-1 lg:grid-cols-5 gap-3 mb-4'>
            <div className='lg:col-span-3'>
              <AlertFeed alerts={ALERTS} />
            </div>
            <div className='lg:col-span-2'>
              <SupplyBars supplies={SUPPLIES} />
            </div>
          </div>

          {/* Bottom Grid: Mesh + Nodes + Weather */}
          <div className='grid grid-cols-1 md:grid-cols-3 gap-3'>
            <MeshFeed messages={MESH_MESSAGES} />
            <NodeStatus nodes={NODES} />
            <WeatherCard data={WEATHER} />
          </div>
        </div>
      </Main>
    </>
  )
}
