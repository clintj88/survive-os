# SURVIVE OS Frontend — Agent Team Prompt

## Prerequisites

Before launching this team:
1. Fork or clone `satnaing/shadcn-admin` as the base
2. Copy the reference prototype into `frontend/reference/`
3. Copy the playbook files into `frontend/docs/`
4. Ensure `frontend/shell/` is initialized as a Vite + React + TS project with shadcn/ui installed

## Initialization Commands

```bash
cd survive-os/frontend/shell

# Initialize from shadcn-admin as a base
npx degit satnaing/shadcn-admin . --force

# Install dependencies
pnpm install

# Add additional dependencies
pnpm add zustand @tanstack/react-query @tanstack/react-router
pnpm add maplibre-gl recharts react-hook-form @hookform/resolvers zod
pnpm add -D @tanstack/router-vite-plugin

# Verify it runs
pnpm dev
```

## Launch Prompt

Copy and paste this entire block into Claude Code:

```
Create an agent team to build the SURVIVE OS frontend.

This is a React + shadcn/ui admin dashboard for a survival
operating system. We're building on top of satnaing/shadcn-admin
as the base template.

READ THESE FILES FIRST (in order):
1. frontend/docs/README.md — Master playbook (tech stack, structure, contracts)
2. frontend/docs/DESIGN-SYSTEM.md — Colors, typography, spacing, components
3. frontend/docs/MODULE-SPECS.md — Every module view specification
4. frontend/reference/survive-os-shadcn-frontend.jsx — Visual reference prototype

The reference prototype defines the EXACT visual language. Match it.
Dark zinc theme, amber accents, collapsible sidebar with grouped nav,
command palette (Cmd+K), breadcrumbs, stat cards, data tables.

Spawn 5 teammates:

1. Shell Architect — Owns: routes/__root.tsx, components/layout/,
   hooks/, stores/, lib/, styles/globals.css
   
   Tasks:
   - Restructure shadcn-admin's sidebar to match our module groups
     (see sidebar-data in MODULE-SPECS). Use the same SidebarProvider/
     SidebarMenu/SidebarGroup pattern from shadcn-admin.
   - Update sidebar-data.ts with SURVIVE OS navigation groups and items
   - Implement role-based nav filtering (useRole hook checks LDAP groups)
   - Build the header with PanelLeft toggle, breadcrumb, node count, clock
   - Build the command palette (Cmd+K) searching all modules
   - Create auth store (Zustand) and useAuth hook
   - Create ui-store for sidebar state and theme preference
   - Set up TanStack Router with lazy-loaded routes for every module
   - Configure TanStack Query with offline-first defaults
   - Set up WebSocket connection manager hook
   - Configure globals.css with our design tokens (see DESIGN-SYSTEM.md)
   - The shell must feel IDENTICAL to the reference prototype

   Branch: feature/frontend/shell

2. Dashboard Builder — Owns: routes/index.tsx, components/dashboard/,
   components/shared/
   
   Tasks:
   - Build the Command Center dashboard matching the reference exactly
   - Create reusable components: StatCard, AlertFeed, MeshFeed,
     NodeStatus, SupplyBars, WeatherCard
   - Build shared components: DataTable (TanStack Table wrapper),
     PageHeader, EmptyState, LoadingSkeleton, StatusBadge,
     ConfirmDialog, toast notifications
   - StatCards in 4-column grid with value, label, subtitle
   - AlertFeed with clickable items that navigate to source module
   - MeshFeed with channel badges, auto-scroll, hover pause
   - NodeStatus grid with status dots, monospace names
   - SupplyBars with threshold coloring
   - All dashboard data via TanStack Query with mock data initially
   - Ensure all shared components follow shadcn/ui patterns
     (use cn() utility, forwardRef, proper variant props)

   Branch: feature/frontend/dashboard

3. Communication & Security Views — Owns: routes/comms/*, routes/security/*
   
   Tasks:
   - Build Radio & Mesh view: message feed with channel filter,
     compose bar, connected radios table, node list
   - Build BBS: topic list table, topic detail with thread, reply box
   - Build Emergency Alerts: active alerts, history, broadcast dialog
     with level selector and confirmation
   - Build Perimeter view: MapLibre map with sensor overlay,
     sensor status list, event log table
   - Build Drone Ops: fleet status cards, mission log, mission planner
   - Build Watch Schedule: week calendar view, current team card,
     checkpoint log
   - All views use PageHeader + DataTable + StatusBadge from shared
   - All maps use MapLibre GL JS with placeholder tile source
   - Role-gate security routes (redirect if not security/admin role)

   Branch: feature/frontend/comms-security

4. Resource & Agriculture Views — Owns: routes/agriculture/*,
   routes/resources/*, routes/weather.tsx
   
   Tasks:
   - Build Crop Planner: field map (MapLibre), plot table, season summary
   - Build Seed Bank: data table with viability color coding, alerts
   - Build Livestock: animal registry table, species filter, breeding
     coefficient warning, production tracking
   - Build Inventory: category tabs, full data table with status,
     bulk edit mode, below-minimum highlighting
   - Build Energy: stat cards, solar chart (Recharts area), battery
     chart (line), fuel table
   - Build Trade Ledger: partner balances, trade history table
   - Build Tool Library: check-in/out table, overdue alerts
   - Build Weather: current conditions card, 24h charts (Recharts),
     observation log, forecast notes

   Branch: feature/frontend/resources-agriculture

5. Governance, Medical, Education & Admin Views — Owns:
   routes/medical/*, routes/governance.tsx, routes/education.tsx,
   routes/identity.tsx, routes/settings.tsx
   
   Tasks:
   - Build Patient Records: search, patient table, patient detail
     with tabs (Visits/Medications/Vitals/Documents), SOAP note
     template, vital signs Recharts line chart, print summary button
   - Build Pharmacy: expiration alerts, medication table with
     color-coded expiry, dispense action
   - Build Governance: tabbed view (Census/Voting/Allocation/
     Treaties/Disputes), population table, voting interface
   - Build Knowledge Base: category grid view, search, entry detail
     (port the existing survival app design)
   - Build Identity Admin: tabbed view (Users/Roles/Badges/Zones/
     Audit), user management table, audit log with search and filter
   - Build Settings: system info, theme selector, module toggles,
     backup controls
   - Medical routes role-gated to medical/admin
   - Governance routes role-gated to governance/admin
   - Identity/Settings routes role-gated to admin

   Branch: feature/frontend/governance-medical-admin

RULES FOR ALL TEAMMATES:
- TypeScript strict mode — no `any` types
- Every component uses shadcn/ui primitives (Button, Card, Table,
  Badge, Dialog, Sheet, Tabs, Input, Select, etc.)
- Use the cn() utility for conditional classes
- Use Tailwind only — no inline styles, no CSS modules
- Every page starts with <PageHeader> (title + description + actions)
- Every table uses the shared <DataTable> wrapper
- Every route is lazy-loaded
- Mock data is fine initially — use realistic SURVIVE OS data
  (not lorem ipsum — real community scenarios)
- Match the reference prototype's visual language exactly
- Test at 800x480 viewport (Pi 7" touchscreen)
- Do NOT edit files outside your assigned directories
- Feature branches as specified above
```

## Post-Team Integration

After all teammates complete their work:

```bash
# Merge in order (shell first, then views)
git checkout develop
git merge feature/frontend/shell
git merge feature/frontend/dashboard
git merge feature/frontend/comms-security
git merge feature/frontend/resources-agriculture
git merge feature/frontend/governance-medical-admin

# Resolve any conflicts (should be minimal with directory ownership)
# Run the dev server and verify
cd frontend/shell
pnpm dev

# Test at Pi viewport
# Open Chrome DevTools → Device toolbar → Custom: 800x480

# Build for production
pnpm build
# Check bundle sizes against budget (README.md performance section)
```

## Verification Checklist

After merge, verify:
- [ ] Shell loads with sidebar, header, command palette
- [ ] Sidebar collapses/expands, groups collapse/expand
- [ ] Cmd+K opens search, finds all modules
- [ ] Dashboard displays all 6 card sections with mock data
- [ ] Every module route loads (navigate through all 22 sidebar items)
- [ ] Role filtering works (switch mock role, see items appear/disappear)
- [ ] Data tables sort and filter correctly
- [ ] Maps render with placeholder tiles
- [ ] Charts render with mock data
- [ ] 800x480 viewport is usable (sidebar collapses, content readable)
- [ ] No TypeScript errors
- [ ] No console errors
- [ ] Production build under 250KB gzipped total
- [ ] Every page has loading skeleton while data fetches
