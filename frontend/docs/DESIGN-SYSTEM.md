# SURVIVE OS Frontend — Design System

## Color Tokens

Based on shadcn/ui zinc dark theme. ALL colors are CSS variables defined in `globals.css`.

### Base Colors (Zinc Scale)
```css
--background: 240 10% 3.9%;      /* zinc-950: #09090b — page background */
--foreground: 0 0% 98%;           /* zinc-50: #fafafa — primary text */
--card: 240 10% 5.9%;             /* zinc-900 approx: #18181b — card bg */
--card-foreground: 0 0% 98%;
--popover: 240 10% 5.9%;
--popover-foreground: 0 0% 98%;
--muted: 240 3.7% 15.9%;          /* zinc-800: #27272a — muted bg */
--muted-foreground: 240 5% 64.9%; /* zinc-400: #a1a1aa — secondary text */
--border: 240 3.7% 15.9%;         /* zinc-800: #27272a */
--input: 240 3.7% 15.9%;
--ring: 40 96% 53%;               /* amber-500 — focus ring */
```

### Accent Colors
```css
--primary: 40 96% 53%;            /* amber-500: #f59e0b — primary accent */
--primary-foreground: 0 0% 0%;    /* black on amber */
--secondary: 240 3.7% 15.9%;     /* zinc-800 — secondary buttons */
--secondary-foreground: 0 0% 98%;
--accent: 240 3.7% 15.9%;
--accent-foreground: 0 0% 98%;
--destructive: 0 84% 60%;        /* red-500: #ef4444 — danger/critical */
--destructive-foreground: 0 0% 98%;
```

### Semantic Status Colors
```css
--status-online: #22c55e;    /* green-500 */
--status-degraded: #f59e0b;  /* amber-500 */
--status-offline: #ef4444;   /* red-500 */
--status-info: #3b82f6;      /* blue-500 */
```

### Module Group Colors
Used for sidebar group labels and module accent indicators:
```css
--group-comms: #3b82f6;      /* blue-500 */
--group-security: #ef4444;   /* red-500 */
--group-agriculture: #22c55e;/* green-500 */
--group-medical: #ec4899;    /* pink-500 */
--group-resources: #a855f7;  /* purple-500 */
--group-navigation: #06b6d4; /* cyan-500 */
--group-weather: #64748b;    /* slate-500 */
--group-governance: #f97316; /* orange-500 */
--group-education: #14b8a6;  /* teal-500 */
--group-admin: #6b7280;      /* gray-500 */
```

## Typography

### Font Stack
```css
/* Body text — no external fonts for Pi performance */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;

/* Monospace (data, code, timestamps, node names) */
font-family: "JetBrains Mono", "SF Mono", "Fira Code", "Cascadia Code", monospace;
```
Note: JetBrains Mono is pre-installed on the SURVIVE OS image. If unavailable, the fallback chain handles it.

### Scale
| Usage | Size | Weight | Font |
|-------|------|--------|------|
| Page title | 22px | 700 | Sans |
| Page description | 13px | 400 | Sans |
| Card title | 12px uppercase | 600 | Sans |
| Body text | 13-14px | 400 | Sans |
| Table header | 10-11px uppercase | 600 | Sans |
| Table cell | 12px | 400 | Sans / Mono for numbers |
| Badge/label | 10px | 500-600 | Sans |
| Stat value | 28px | 700 | Sans (tabular-nums) |
| Timestamp | 10-11px | 400 | Mono |
| Node name | 11px | 500 | Mono |

### Numeric Display
Always use `font-variant-numeric: tabular-nums` for numbers that change (clocks, counts, stats). This prevents layout shifts when digits update.

## Spacing

Tailwind default 4px base. Key patterns:
| Usage | Value |
|-------|-------|
| Page padding | 20px (`p-5`) |
| Card padding | 16px body, 12px 16px header (`p-4`, `px-4 py-3`) |
| Grid gap | 12px (`gap-3`) |
| Section margin | 16px (`mb-4`) |
| Table row padding | 6-8px vertical (`py-1.5` to `py-2`) |
| Sidebar item padding | 7px 12px |
| Sidebar width | 240px expanded, 52px collapsed |
| Header height | 48px |

## Border Radius
| Element | Radius |
|---------|--------|
| Cards | 8px (`rounded-lg`) |
| Buttons | 6px (`rounded-md`) |
| Inputs | 6px (`rounded-md`) |
| Badges | 10px full pill (`rounded-full`) for counts, 3-4px for labels |
| Modals/Dialogs | 12px (`rounded-xl`) |
| Avatar | 50% (`rounded-full`) |
| Sidebar items | 6px (`rounded-md`) |

## Component Patterns

### Stat Card
```
┌─────────────────┐
│ Label (12px, muted)    │
│ 147 (28px, bold, color)│
│ +2 this month (11px)   │
└─────────────────┘
```
Background: `card`. Border: `border`. No shadow.

### Data Card (with header)
```
┌─────────────────────────────┐
│ TITLE (uppercase)    Badge  │ ← header with bottom border
├─────────────────────────────┤
│ Content rows                │ ← body with padding
│ Content rows                │
└─────────────────────────────┘
```

### Data Table Row
```
│ ● NODE-NAME  │ online │ 34%  │ 14d 7h │
```
- Status dot (6px circle) before name
- Monospace for names and values
- Alternating row background optional (`zinc-900/zinc-950`)
- Column headers uppercase, smaller, muted

### Alert Item
```
│ ● Alert message text here        │
│   2 hours ago                     │
```
- Status dot (7px, color-coded by level)
- Clickable — navigates to relevant module
- Time in muted text below message

### Supply Bar
```
│ Water (gal)  ████████░░░░  340 │
```
- Label (fixed width), track (flex), value (fixed width)
- Track: `zinc-800`. Fill: green/amber/red based on threshold
- Height: 6px, rounded

### Mesh Feed Item
```
│ Johnson, C.  PRIMARY  14:45     │
│ Trade team returning from...     │
```
- From (bold), channel badge (colored pill), time (right-aligned, mono)
- Message body in muted text below

### Navigation Item (Sidebar)
```
│ 🏠 Command Center              │  ← active: zinc-800 bg, amber icon
│ 📻 Radio & Mesh                │  ← inactive: transparent bg, muted text
│ 💬 Message Board               │
│ ⚠️ Emergency Alerts        2   │  ← with badge
```

### Command Palette
```
┌─────────────────────────────┐
│ 🔍 Search modules...   ESC │
├─────────────────────────────┤
│ 🏠 Command Center          │
│ 📻 Radio & Mesh            │
│ ...                         │
└─────────────────────────────┘
```
- Fixed width 520px, max-height 420px
- Backdrop blur overlay
- Auto-focus input
- Keyboard navigable (arrow keys + enter)

## Responsive Breakpoints

| Breakpoint | Width | Layout Change |
|------------|-------|---------------|
| Mobile | < 640px | Sidebar hidden, hamburger toggle, single column |
| Tablet | 640-1024px | Sidebar collapsed by default, 2-column grids |
| Desktop | > 1024px | Sidebar expanded, 3-4 column grids |
| Pi Display | 800x480 | Treat as tablet — collapsed sidebar, 2-column |

The Pi target display is typically 800x480 (7" touchscreen) or 1024x600 (10" screen). Optimize for these dimensions. Touch targets minimum 44x44px.

## Accessibility

- All interactive elements keyboard accessible (tab order, enter/space to activate)
- Focus rings visible (`ring-amber-500`)
- ARIA labels on icon-only buttons
- Color is never the ONLY indicator (always pair with icon or text)
- Contrast ratio minimum 4.5:1 for text, 3:1 for large text
- Screen reader support for status changes (aria-live regions for alerts)
- High-contrast theme available (`themes/high-contrast.css`)

## Animation

Minimal. CSS-only. No animation libraries.

```css
/* Fade in for page transitions */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-in { animation: fadeIn 0.2s ease-out; }

/* Sidebar collapse */
transition: width 0.2s ease, min-width 0.2s ease;

/* Hover states */
transition: background 0.1s ease, color 0.1s ease;

/* Progress bars */
transition: width 0.5s ease;
```

No `framer-motion`. No `react-spring`. No GSAP. Every millisecond matters on a Pi.
