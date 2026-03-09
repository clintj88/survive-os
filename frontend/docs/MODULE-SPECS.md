# SURVIVE OS Frontend — Module View Specifications

Each module below defines the views, data requirements, key interactions, and API endpoints. Build each as a lazy-loaded route.

---

## 1. Command Center (Dashboard) — `routes/index.tsx`

**Purpose:** Single-glance operational overview. The first thing anyone sees on login.

### Layout
```
[Stat Cards — 4 columns]
[Alert Feed (2/3) | Supply Status (1/3)]
[Mesh Feed (1/3) | Network Nodes (1/3) | Weather (1/3)]
```

### Components
| Component | Data Source | Refresh |
|-----------|------------|---------|
| StatCard x4 (Population, Nodes Online, Active Alerts, Days of Water) | `/api/v1/stats/summary` | 60s poll |
| AlertFeed | `/api/v1/alerts?limit=10&hours=24` | WebSocket push |
| SupplyBars | `/api/v1/inventory/summary` | 5min poll |
| MeshFeed | WebSocket `/ws/mesh` | Real-time stream |
| NodeStatus | `/api/v1/nodes/status` | 30s poll |
| WeatherCard | `/api/v1/weather/current` | 5min poll |

### Interactions
- Click alert → navigate to relevant module
- Click node → open node detail sheet (slide-in panel)
- Mesh feed auto-scrolls, pauses on hover
- Supply bars color-code by threshold (green/amber/red)

---

## 2. Radio & Mesh — `routes/comms/index.tsx`

**Purpose:** Unified communication dashboard for Meshtastic, ham radio, and local messaging.

### Layout
```
[PageHeader: "Communications" + "New Message" button]
[Mesh Feed (2/3) | Channel List + Node Map (1/3)]
[Connected Radios table]
```

### Views
**Mesh Feed Panel:**
- Filterable by channel (PRIMARY, SECURITY, MEDICAL, SENSOR, EMERGENCY)
- Each message shows: sender, channel badge, timestamp, message body
- Compose bar at bottom (select channel, type message, send)

**Channel List:**
- List of active channels with member count and last activity
- Status indicator (active/idle)

**Connected Radios Table:**
- Columns: Node Name, User, Battery, Signal, Last Seen, GPS
- Sortable by any column
- Battery column shows bar + percentage
- Click row → node detail panel

### API Endpoints
- `GET /api/v1/comms/messages?channel=PRIMARY&limit=50`
- `POST /api/v1/comms/messages` — send message
- `GET /api/v1/comms/channels`
- `GET /api/v1/comms/nodes`
- `WebSocket /ws/mesh` — real-time message stream

---

## 3. Message Board (BBS) — `routes/comms/bbs.tsx`

**Purpose:** Asynchronous community bulletin board with topics and threads.

### Layout
```
[PageHeader: "Message Board" + "New Topic" button]
[Topic List (sortable table)]
```

**Topic Detail (click into topic):**
```
[Topic title + metadata]
[Thread of replies, newest at bottom]
[Reply compose box]
```

### Data
- Topics: title, author, date, reply count, last reply date, category (General, Trade, Agriculture, Medical, Governance)
- Replies: author, date, body
- Categories filterable via tabs

### API Endpoints
- `GET /api/v1/bbs/topics?category=General&sort=latest`
- `GET /api/v1/bbs/topics/:id/replies`
- `POST /api/v1/bbs/topics` — new topic
- `POST /api/v1/bbs/topics/:id/replies` — new reply

---

## 4. Emergency Alerts — `routes/comms/alerts.tsx`

**Roles:** security, admin

### Layout
```
[PageHeader: "Emergency Alerts" + "BROADCAST ALERT" destructive button]
[Active Alerts (priority cards)]
[Alert History (table)]
```

**Broadcast Dialog:**
- Level selector: INFO / WARNING / CRITICAL / EMERGENCY
- Message textarea
- Channel selector: LOCAL / MESH / RADIO / ALL
- Confirm with re-type of alert level (prevents accidents)

### API Endpoints
- `GET /api/v1/alerts?status=active`
- `GET /api/v1/alerts?status=resolved&limit=50`
- `POST /api/v1/alerts/broadcast` — send alert

---

## 5. Security Perimeter — `routes/security/index.tsx`

**Roles:** security, admin

### Layout
```
[PageHeader: "Perimeter Status"]
[Map with sensor overlay (2/3) | Sensor Status List (1/3)]
[Recent Events table]
```

### Map View
- MapLibre GL JS with offline tiles
- Sensor locations as colored dots (green=clear, amber=alert, red=triggered, gray=offline)
- Patrol positions (GPS from Meshtastic) as labeled markers
- Click sensor → popup with details and last 24h event history
- Perimeter zone boundaries as polygon overlays

### Sensor Status List
- Each sensor: name, type (PIR/Reed/Camera), status, battery, last event
- Filter by status (all/alert/offline)

### API Endpoints
- `GET /api/v1/security/sensors`
- `GET /api/v1/security/events?hours=24`
- `GET /api/v1/security/patrols/active`
- `WebSocket /ws/security` — real-time sensor events

---

## 6. Drone Operations — `routes/security/drones.tsx`

**Roles:** security, admin

### Layout
```
[PageHeader: "Drone Operations" + "Plan Mission" button]
[Fleet Status cards (horizontal scroll)]
[Mission Log table]
[Active Mission view (when drone is flying)]
```

### Fleet Cards
Each drone: name, status (ready/flying/charging/maintenance), battery, last flight, flight hours total

### Mission Planning Dialog
- Select drone, draw route on map, set altitude, set camera mode
- Estimated flight time and battery usage
- Launch requires confirmation

### API Endpoints
- `GET /api/v1/drones/fleet`
- `GET /api/v1/drones/missions?limit=20`
- `POST /api/v1/drones/missions` — create mission
- `WebSocket /ws/drone/:id` — live telemetry

---

## 7. Watch Schedule — `routes/security/patrol.tsx`

**Roles:** security, admin

### Layout
```
[PageHeader: "Watch Schedule" + "Generate Schedule" button]
[Calendar/timeline view of shifts]
[Current watch team card]
[Checkpoint log table]
```

### Calendar View
- Week view with time blocks per person
- Color-coded by shift type (day/night/standby)
- Drag to adjust (admin only)

### API Endpoints
- `GET /api/v1/patrol/schedule?week=current`
- `GET /api/v1/patrol/checkpoints?date=today`
- `POST /api/v1/patrol/schedule` — generate/update

---

## 8. Crop Planner — `routes/agriculture/index.tsx`

### Layout
```
[PageHeader: "Crop Planner"]
[Field Map with plot overlays (2/3) | Season Summary (1/3)]
[Plot Table: plot name, current crop, planted date, expected harvest, status]
```

### Field Map
- Aerial photo base (from drone) or hand-drawn plot boundaries
- Each plot colored by status (planted/growing/ready to harvest/fallow)
- Click plot → detail panel with history and soil data

### API Endpoints
- `GET /api/v1/agriculture/plots`
- `GET /api/v1/agriculture/plots/:id/history`
- `PUT /api/v1/agriculture/plots/:id` — update plot

---

## 9. Seed Bank — `routes/agriculture/seedbank.tsx`

### Layout
```
[PageHeader: "Seed Bank" + "Add Variety" button]
[Data Table: variety, quantity, source, date collected, germination rate, viability status]
[Viability alerts panel]
```

### Key Features
- Sort by viability (expiring soon → top)
- Color-coded viability: green (>80%), amber (50-80%), red (<50%)
- Germination test log per variety

---

## 10. Livestock — `routes/agriculture/livestock.tsx`

### Layout
```
[PageHeader: "Livestock Records" + "Add Animal" button]
[Summary cards: total by species]
[Data Table: ID/name, species, breed, sex, DOB, parent IDs, status, notes]
```

### Key Features
- Filter by species (chickens, rabbits, goats, pigs)
- Inbreeding coefficient warning on breeding pair selection
- Health log per animal (click row → detail panel)
- Production tracking (eggs/day, milk/day)

---

## 11. Patient Records — `routes/medical/index.tsx`

**Roles:** medical, admin
**Encryption:** All data in transit and at rest via SQLCipher

### Layout
```
[PageHeader: "Patient Records" + "New Patient" / "New Visit" buttons]
[Search bar (search by name)]
[Patient list (data table)]
```

**Patient Detail (click into patient):**
```
[Demographics + allergies + blood type banner]
[Tabs: Visits | Medications | Vitals | Documents]
```

### Key Features
- SOAP note template for visits
- Vital signs chart (temperature, pulse, BP over time — Recharts line chart)
- Medication list with dosage and schedule
- Print patient summary button (generates PDF)
- RBAC enforced — only medical role can view

---

## 12. Pharmacy — `routes/medical/pharmacy.tsx`

**Roles:** medical, admin

### Layout
```
[PageHeader: "Pharmacy Inventory"]
[Expiration Alerts banner (if any within 30 days)]
[Data Table: medication, quantity, lot#, expiration, location, status]
```

### Key Features
- Sort by expiration (soonest first)
- Expiration color coding (red <30d, amber <90d, green >90d)
- Dispense action (reduce quantity, log who received it)
- Low stock alerts (below configured minimum)

---

## 13. Inventory — `routes/resources/index.tsx`

### Layout
```
[PageHeader: "Community Inventory" + "Add Item" / "Audit" buttons]
[Category tabs: All, Food, Water, Medical, Tools, Fuel, Ammo, Seeds, Other]
[Data Table: item, category, quantity, unit, location, minimum, status, last updated]
```

### Key Features
- Bulk edit mode for inventory audits
- Barcode/QR scan button (opens camera for Pi touchscreen)
- Export to CSV/PDF
- Consumption rate trend per item (sparkline in table)
- Below-minimum items highlighted

---

## 14. Energy & Fuel — `routes/resources/energy.tsx`

### Layout
```
[PageHeader: "Energy & Fuel"]
[Stat Cards: Solar output today, Battery SOC, Fuel reserves, Generator hours]
[Solar production chart (24h line chart)]
[Fuel inventory table]
```

### Charts
- 24-hour solar production (Recharts area chart, amber fill)
- Battery state-of-charge over 7 days (line chart)
- Generator run hours this month (bar chart)

---

## 15. Trade Ledger — `routes/resources/trade.tsx`

### Layout
```
[PageHeader: "Trade Ledger" + "Record Trade" button]
[Balance summary with partner communities]
[Trade History table: date, partner, gave, received, fair value, notes]
```

---

## 16. Tool Library — `routes/resources/tools.tsx`

### Layout
```
[PageHeader: "Tool Library" + "Add Tool" button]
[Data Table: tool, category, status (available/checked out), borrower, due date, condition]
[Overdue items alert banner]
```

### Key Features
- Check-out / check-in actions
- Maintenance schedule per tool
- History log per tool

---

## 17. Maps — `routes/maps.tsx`

### Layout
```
[Full-screen MapLibre GL map with overlay controls]
[Floating layer panel (top-right): toggle layers on/off]
[Floating tool panel (top-left): measure, draw, print]
```

### Map Layers (toggleable)
- Base: Offline OpenStreetMap tiles
- Aerial: Drone orthomosaic (if available)
- Community annotations (resources, hazards, routes)
- Sensor positions (Meshtastic nodes)
- Agricultural plots
- Security perimeter and sensors
- Patrol positions (live GPS)
- Weather station locations

### Key Features
- Measure distance and area tools
- Add annotation (point, line, polygon with label and category)
- Print current view to PDF at selected scale
- Zoom to community bounds

---

## 18. Weather — `routes/weather.tsx`

### Layout
```
[PageHeader: "Weather Station"]
[Current Conditions card (large)]
[24-hour history charts (temp, humidity, pressure, wind — Recharts)]
[7-day observation log table]
[Forecast notes (manual entry from pattern analysis)]
```

---

## 19. Governance — `routes/governance.tsx`

**Roles:** governance, admin

### Layout
```
[PageHeader: "Community Council"]
[Tabs: Census | Voting | Allocation | Treaties | Disputes]
```

Each tab is its own sub-view. Census is a population table with demographics. Voting shows active proposals with yes/no/abstain. Allocation shows resource rationing calculations. Treaties is a document list. Disputes is a case tracker.

---

## 20. Knowledge Base — `routes/education.tsx`

### Layout
```
[PageHeader: "Knowledge Base" + search bar]
[Category grid (same as the survival app we built)]
[Entry detail view on click]
```

This embeds the existing survival knowledge app as a module. Can be rendered directly or via iframe to the education service on port 8090.

---

## 21. Identity Admin — `routes/identity.tsx`

**Roles:** admin only

### Layout
```
[PageHeader: "Identity & Access" + "Add User" / "Add Badge" buttons]
[Tabs: Users | Roles | Badges | Zones | Audit Log]
```

**Users tab:** Data table of all community members with role, status, last login
**Roles tab:** Role definitions and member counts
**Badges tab:** NFC badge registry with assignment status
**Zones tab:** Physical access zones and their configurations
**Audit tab:** Searchable, filterable audit log (date, user, action, resource, result)

---

## 22. Settings — `routes/settings.tsx`

**Roles:** admin

### Sections
- System: Hostname, timezone, network config, NTP calibration
- Display: Theme selection, language, font size
- Modules: Enable/disable modules, port assignments
- Backup: Trigger backup, view backup history, restore
- About: Version, build date, node ID, license
