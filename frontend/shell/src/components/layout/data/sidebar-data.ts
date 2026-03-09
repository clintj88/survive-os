import {
  BookOpen,
  Gauge,
  Globe,
  Laptop,
  LayoutDashboard,
  MessageSquare,
  Package,
  Settings,
  Shield,
  Sprout,
  Stethoscope,
  Users,
  Vote,
} from 'lucide-react'
import type { SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'Admin',
    email: 'admin@survive.local',
    avatar: '/avatars/01.png',
  },
  teams: [
    {
      name: 'SURVIVE OS',
      logo: Gauge,
      plan: 'Community Hub',
    },
  ],
  navGroups: [
    {
      title: 'General',
      items: [
        {
          title: 'Dashboard',
          url: '/',
          icon: LayoutDashboard,
        },
        {
          title: 'Tasks',
          url: '/tasks',
          icon: Package,
        },
        {
          title: 'Chats',
          url: '/chats',
          icon: MessageSquare,
        },
        {
          title: 'Apps',
          url: '/apps',
          icon: Laptop,
        },
      ],
    },
    {
      title: 'Modules',
      items: [
        {
          title: 'Governance',
          url: '/governance',
          icon: Vote,
        },
        {
          title: 'Medical',
          url: '/medical',
          icon: Stethoscope,
        },
        {
          title: 'Education',
          url: '/education',
          icon: BookOpen,
        },
        {
          title: 'Identity',
          url: '/identity',
          icon: Users,
        },
        {
          title: 'Security',
          url: '/errors/general',
          icon: Shield,
        },
        {
          title: 'Agriculture',
          url: '/errors/general',
          icon: Sprout,
        },
        {
          title: 'Maps',
          url: '/errors/general',
          icon: Globe,
        },
      ],
    },
    {
      title: 'Other',
      items: [
        {
          title: 'Settings',
          url: '/settings',
          icon: Settings,
        },
        {
          title: 'Help Center',
          url: '/help-center',
          icon: BookOpen,
        },
      ],
    },
  ],
}
