# SURVIVE OS Frontend — Agent Team Playbook

## Mission

Build a complete, production-grade frontend shell and module UIs for SURVIVE OS. The frontend is a single web application that serves as the unified interface to all 14 subsystems. It runs on a Raspberry Pi 4 browser, works offline, and is operable by stressed, fatigued, minimally-trained users.

## Reference Implementation

A working prototype exists at `frontend/reference/survive-os-shadcn-frontend.jsx`. This is the **design authority** — all production work must match its visual language, color system, layout patterns, and interaction model. Study it before writing any code.

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | React 19 + Vite 6 | shadcn-admin base, fast HMR, tree-shaking |
| UI Library | shadcn/ui (Tailwind + Radix) | Accessible, composable, dark mode native |
| Routing | TanStack Router | Type-safe, file-based, lazy loading |
| State | Zustand | Lightweight, no boilerplate, works with SSR |
| Data Fetching | TanStack Query | Caching, offline support, retry logic |
| Icons | Lucide React | Tree-shakeable, consistent style |
| Charts | Recharts | Lightweight, composable, React-native |
| Maps | MapLibre GL JS | Offline tiles, open source, GPU-accelerated |
| Forms | React Hook Form + Zod | Validation, performance, type safety |
| Tables | TanStack Table | Headless, sortable, filterable, virtual scroll |
| Language | TypeScript (strict) | Type safety across all modules |
| CSS | Tailwind CSS 4 | Utility-first, design token system |
| Build | Vite 6 | Fast builds, chunked output for Pi |

## Performance Budget (Raspberry Pi 4 Target)

| Metric | Target | Hard Limit |
|--------|--------|------------|
| Initial JS bundle | < 150 KB gzipped | 250 KB |
| First Contentful Paint | < 2s on Pi 4 | 4s |
| Time to Interactive | < 3s on Pi 4 | 5s |
| Per-module chunk | < 50 KB gzipped | 80 KB |
| Memory usage | < 200 MB | 350 MB |
| Idle CPU | < 5% | 15% |

**Rules:**
- Every module is a lazy-loaded route chunk — never bundle everything together
- No heavy animation libraries — CSS transitions only
- Images are lazy loaded and responsive
- Lists virtualize at 50+ items (TanStack Virtual)
- WebSocket connections close when module is not active
- Service worker caches the shell and static assets for instant reload

## File Structure

```
frontend/
├── reference/
│   └── survive-os-shadcn-frontend.jsx  # Design reference (prototype)
├── shell/                               # Main application shell
│   ├── src/
│   │   ├── main.tsx                     # Entry point
│   │   ├── app.tsx                      # Root layout with providers
│   │   ├── routes/                      # TanStack Router file-based routes
│   │   │   ├── __root.tsx               # Root layout (sidebar + header + outlet)
│   │   │   ├── index.tsx                # Dashboard / Command Center
│   │   │   ├── comms/
│   │   │   │   ├── index.tsx            # Radio & Mesh overview
│   │   │   │   ├── bbs.tsx              # Message board
│   │   │   │   └── alerts.tsx           # Emergency alerts
│   │   │   ├── security/
│   │   │   │   ├── index.tsx            # Perimeter overview
│   │   │   │   ├── drones.tsx           # Drone operations
│   │   │   │   └── patrol.tsx           # Watch schedule
│   │   │   ├── agriculture/
│   │   │   │   ├── index.tsx            # Crop planner
│   │   │   │   ├── seedbank.tsx         # Seed inventory
│   │   │   │   └── livestock.tsx        # Animal records
│   │   │   ├── medical/
│   │   │   │   ├── index.tsx            # Patient records
│   │   │   │   └── pharmacy.tsx         # Medication inventory
│   │   │   ├── resources/
│   │   │   │   ├── index.tsx            # Inventory overview
│   │   │   │   ├── energy.tsx           # Power & fuel
│   │   │   │   ├── trade.tsx            # Trade ledger
│   │   │   │   └── tools.tsx            # Tool library
│   │   │   ├── maps.tsx                 # Offline maps
│   │   │   ├── weather.tsx              # Weather station
│   │   │   ├── governance.tsx           # Council / census / voting
│   │   │   ├── education.tsx            # Knowledge base
│   │   │   ├── identity.tsx             # User/role admin
│   │   │   └── settings.tsx             # System settings
│   │   ├── components/
│   │   │   ├── ui/                      # shadcn/ui components
│   │   │   ├── layout/
│   │   │   │   ├── app-sidebar.tsx      # Main sidebar
│   │   │   │   ├── sidebar-data.ts      # Nav group definitions
│   │   │   │   ├── header.tsx           # Top bar with breadcrumb
│   │   │   │   ├── command-menu.tsx     # Cmd+K palette
│   │   │   │   └── user-nav.tsx         # User menu in sidebar footer
│   │   │   ├── dashboard/
│   │   │   │   ├── stat-card.tsx        # Metric card
│   │   │   │   ├── alert-feed.tsx       # Recent alerts list
│   │   │   │   ├── mesh-feed.tsx        # Live Meshtastic feed
│   │   │   │   ├── node-status.tsx      # Network nodes table
│   │   │   │   ├── supply-bars.tsx      # Inventory bar chart
│   │   │   │   └── weather-card.tsx     # Weather summary
│   │   │   └── shared/
│   │   │       ├── data-table.tsx       # Generic sortable/filterable table
│   │   │       ├── page-header.tsx      # Title + description + actions
│   │   │       ├── empty-state.tsx      # "No data" placeholder
│   │   │       ├── loading-skeleton.tsx # Skeleton loaders
│   │   │       ├── status-badge.tsx     # Online/offline/warning badges
│   │   │       ├── confirm-dialog.tsx   # Destructive action confirmation
│   │   │       └── toast-provider.tsx   # Notification toasts
│   │   ├── hooks/
│   │   │   ├── use-auth.ts             # LDAP auth context
│   │   │   ├── use-role.ts             # Role-based access checks
│   │   │   ├── use-websocket.ts        # WebSocket connection manager
│   │   │   ├── use-mesh.ts             # Meshtastic feed hook
│   │   │   └── use-offline.ts          # Offline detection
│   │   ├── lib/
│   │   │   ├── api.ts                  # HTTP client (fetch wrapper)
│   │   │   ├── auth.ts                 # LDAP auth functions
│   │   │   ├── ws.ts                   # WebSocket client
│   │   │   └── utils.ts                # Shared utilities
│   │   ├── stores/
│   │   │   ├── auth-store.ts           # User session state
│   │   │   ├── alert-store.ts          # Active alerts
│   │   │   └── ui-store.ts             # Sidebar state, theme
│   │   └── styles/
│   │       └── globals.css             # Tailwind base + custom tokens
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── components.json                  # shadcn/ui config
│   └── package.json
├── components/                          # Shared component library (npm workspace)
│   ├── src/
│   │   ├── index.ts
│   │   └── ...                          # Exported shared components
│   └── package.json
└── themes/
    ├── default-dark.css                 # Default dark theme
    ├── high-contrast.css                # Accessibility theme
    └── day-mode.css                     # Light theme for outdoor use
```

## Design System

See `DESIGN-SYSTEM.md` for the complete token reference. Key points:

- **Color**: Zinc scale (`zinc-950` through `zinc-50`) with `amber-500` primary accent
- **Typography**: System fonts (no external font loading — Pi performance)
- **Spacing**: Tailwind default scale (4px base)
- **Border radius**: 6px cards, 4px inputs, 8px modals
- **Borders**: `zinc-800` (1px)
- **Shadows**: None in dark mode (borders provide structure)

## Module View Specifications

See `MODULE-SPECS.md` for detailed wireframes and data requirements for each module.

## Agent Team Prompt

See `AGENT-TEAM-PROMPT.md` for the ready-to-paste prompt that launches the team.

## Integration Contract

Every module view:
1. Is a lazy-loaded route under `routes/`
2. Fetches data from its backend via TanStack Query (`/api/v1/{module}/...`)
3. Uses the shared `data-table`, `page-header`, `stat-card`, and `status-badge` components
4. Handles loading, error, and empty states consistently
5. Respects role-based access via `use-role` hook (redirect if unauthorized)
6. Works fully offline with cached data (stale-while-revalidate)
7. Follows the page layout: `PageHeader` → content grid → tables/cards
