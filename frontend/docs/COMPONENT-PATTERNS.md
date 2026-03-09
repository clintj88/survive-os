# SURVIVE OS Frontend — Component Patterns & API Guide

## shadcn/ui Component Usage

Every SURVIVE OS component is built on shadcn/ui primitives. Never build a custom component when a shadcn/ui component exists. Here are the exact mappings:

### Component Map

| SURVIVE OS Need | shadcn/ui Component | Usage |
|-----------------|---------------------|-------|
| Sidebar | `Sidebar`, `SidebarMenu`, `SidebarGroup` | Main navigation |
| Data tables | `Table` + TanStack Table | All list views |
| Stat displays | `Card` | Dashboard stat cards |
| Module cards | `Card`, `CardHeader`, `CardContent` | Section containers |
| Forms | `Input`, `Select`, `Textarea`, `Checkbox` | All data entry |
| Dialogs | `Dialog`, `DialogContent`, `DialogHeader` | Create/edit modals |
| Slide panels | `Sheet`, `SheetContent` | Detail panels |
| Tabs | `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` | Module sub-views |
| Dropdowns | `DropdownMenu` | Context menus, actions |
| Toasts | `Sonner` (via `toast()`) | Notifications |
| Command palette | `Command`, `CommandInput`, `CommandList` | Global search |
| Alerts | `Alert`, `AlertTitle`, `AlertDescription` | Inline warnings |
| Badges | `Badge` | Status indicators |
| Buttons | `Button` | All actions |
| Tooltips | `Tooltip` | Icon-only button labels |
| Skeleton | `Skeleton` | Loading states |
| Separator | `Separator` | Visual dividers |
| Scroll area | `ScrollArea` | Scrollable panels |
| Calendar | `Calendar` | Date selection |
| Toggle | `Toggle` | Map layer switches |

### Variant Patterns

**Buttons:**
```tsx
<Button>Primary Action</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Destructive</Button>
<Button variant="link">Link</Button>
<Button size="sm">Small</Button>
<Button size="icon"><Plus className="h-4 w-4" /></Button>
```

**Badges (Status):**
```tsx
<Badge variant="default">Online</Badge>        // amber bg
<Badge variant="secondary">Idle</Badge>         // zinc bg
<Badge variant="destructive">Critical</Badge>   // red bg
<Badge variant="outline">Pending</Badge>        // border only

// Custom status badge component:
<StatusBadge status="online" />   // green dot + "Online"
<StatusBadge status="degraded" /> // amber dot + "Degraded"
<StatusBadge status="offline" />  // red dot + "Offline"
```

## Shared Component Specs

### PageHeader
Every module page starts with this:
```tsx
interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;  // Buttons go here
}

// Usage:
<PageHeader
  title="Community Inventory"
  description="Track and manage all community supplies"
  actions={
    <>
      <Button variant="outline" size="sm">Export</Button>
      <Button size="sm"><Plus className="mr-2 h-4 w-4" />Add Item</Button>
    </>
  }
/>
```

Renders as:
```
Community Inventory                    [Export] [+ Add Item]
Track and manage all community supplies
─────────────────────────────────────────────────
```

### DataTable
Wraps TanStack Table with shadcn/ui Table components:
```tsx
interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  searchKey?: string;        // Column to search
  searchPlaceholder?: string;
  filterColumn?: string;     // Column for dropdown filter
  filterOptions?: string[];  // Filter dropdown options
  pageSize?: number;         // Default 20
  onRowClick?: (row: T) => void;
}

// Usage:
<DataTable
  columns={inventoryColumns}
  data={inventoryData}
  searchKey="name"
  searchPlaceholder="Search items..."
  filterColumn="category"
  filterOptions={["Food", "Water", "Medical", "Fuel", "Tools"]}
  onRowClick={(item) => openDetail(item)}
/>
```

Features: search input, column filter dropdown, sortable headers, pagination, row click handler. Renders as standard shadcn `Table` with `TableHeader`, `TableBody`, `TableRow`, `TableCell`.

### StatCard
```tsx
interface StatCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  color?: string;  // Tailwind text color class
}

// Usage:
<StatCard label="Population" value={147} subtitle="+2 this month" trend="up" />
```

### StatusBadge
```tsx
type Status = "online" | "degraded" | "offline" | "good" | "warning" | "critical";

// Renders a colored dot + label
<StatusBadge status="online" />
```

### EmptyState
```tsx
<EmptyState
  icon={<Inbox className="h-12 w-12" />}
  title="No items found"
  description="Add your first inventory item to get started"
  action={<Button>Add Item</Button>}
/>
```

### LoadingSkeleton
```tsx
// Automatically matches the component it replaces
<LoadingSkeleton type="table" rows={5} columns={4} />
<LoadingSkeleton type="stat-cards" count={4} />
<LoadingSkeleton type="card" />
```

## API Integration Pattern

### TanStack Query Setup

```tsx
// lib/api.ts
const API_BASE = "/api/v1";

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

### Query Hook Pattern
```tsx
// Every module follows this pattern:
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

// Read
export function useInventory() {
  return useQuery({
    queryKey: ["inventory"],
    queryFn: () => apiFetch<InventoryItem[]>("/inventory"),
    staleTime: 5 * 60 * 1000,  // 5 min cache
    retry: 2,
  });
}

// Write
export function useAddInventoryItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (item: NewInventoryItem) =>
      apiFetch("/inventory", { method: "POST", body: JSON.stringify(item) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inventory"] }),
  });
}
```

### Mock Data Strategy

For initial development, create mock data files that TanStack Query falls back to when the API is unavailable:

```tsx
// hooks/use-inventory.ts
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { MOCK_INVENTORY } from "@/data/mock/inventory";

export function useInventory() {
  return useQuery({
    queryKey: ["inventory"],
    queryFn: async () => {
      try {
        return await apiFetch<InventoryItem[]>("/inventory");
      } catch {
        console.warn("API unavailable, using mock data");
        return MOCK_INVENTORY;
      }
    },
    staleTime: 5 * 60 * 1000,
  });
}
```

Mock data files go in `src/data/mock/` and use realistic SURVIVE OS scenarios (not lorem ipsum).

### WebSocket Pattern

```tsx
// hooks/use-websocket.ts
export function useWebSocket(path: string) {
  const [messages, setMessages] = useState<any[]>([]);
  const [status, setStatus] = useState<"connecting" | "open" | "closed">("connecting");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}${path}`);
    wsRef.current = ws;
    ws.onopen = () => setStatus("open");
    ws.onclose = () => setStatus("closed");
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setMessages(prev => [...prev.slice(-99), data]); // Keep last 100
    };
    return () => ws.close();
  }, [path]);

  const send = useCallback((data: any) => {
    wsRef.current?.send(JSON.stringify(data));
  }, []);

  return { messages, status, send };
}

// Usage in Mesh Feed:
const { messages, status } = useWebSocket("/ws/mesh");
```

## Role-Based Access Pattern

```tsx
// hooks/use-role.ts
import { useAuthStore } from "@/stores/auth-store";

export function useRole() {
  const user = useAuthStore((s) => s.user);
  const roles = user?.roles || ["general"];

  return {
    roles,
    hasRole: (role: string) => roles.includes(role) || roles.includes("admin"),
    isAdmin: roles.includes("admin"),
    isMedical: roles.includes("medical") || roles.includes("admin"),
    isSecurity: roles.includes("security") || roles.includes("admin"),
    isGovernance: roles.includes("governance") || roles.includes("admin"),
  };
}

// In route guards:
function MedicalLayout() {
  const { isMedical } = useRole();
  if (!isMedical) return <Navigate to="/" />;
  return <Outlet />;
}
```

## Page Template

Every module page follows this structure:

```tsx
import { PageHeader } from "@/components/shared/page-header";
import { DataTable } from "@/components/shared/data-table";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { useInventory } from "@/hooks/use-inventory";
import { columns } from "./columns"; // Column definitions

export default function InventoryPage() {
  const { data, isLoading, error } = useInventory();

  return (
    <div className="space-y-4">
      <PageHeader
        title="Community Inventory"
        description="Track and manage all community supplies"
        actions={
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add Item
          </Button>
        }
      />

      {isLoading ? (
        <LoadingSkeleton type="table" rows={8} columns={6} />
      ) : error ? (
        <Alert variant="destructive">
          <AlertTitle>Failed to load inventory</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      ) : (
        <DataTable
          columns={columns}
          data={data ?? []}
          searchKey="name"
          searchPlaceholder="Search items..."
          filterColumn="category"
          filterOptions={["Food", "Water", "Medical", "Fuel", "Tools"]}
        />
      )}
    </div>
  );
}
```

## Testing Checklist Per Module

Before marking a module complete:
- [ ] Page loads without errors
- [ ] Loading state shows skeleton
- [ ] Error state shows alert
- [ ] Empty state shows EmptyState component
- [ ] Data table sorts on all columns
- [ ] Search filters correctly
- [ ] Category/status filter works
- [ ] Row click opens detail (if applicable)
- [ ] Create/edit dialog opens and submits
- [ ] Role gate redirects unauthorized users
- [ ] Responsive at 800x480 viewport
- [ ] No TypeScript errors
- [ ] No console warnings
