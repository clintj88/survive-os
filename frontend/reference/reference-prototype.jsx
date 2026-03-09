import { useState, useEffect, useCallback, useRef } from "react";
import { Search, ChevronDown, ChevronRight, PanelLeft, Radio, Shield, Sprout, Heart, Package, Map, Cloud, Scale, BookOpen, Settings, Home, MessageSquare, Bell, AlertTriangle, Eye, Navigation, Circle, UserCog, Zap, ArrowLeftRight, Wrench, BarChart3, Send, Wifi, LogOut, ChevronsUpDown, CircleDot, Command, X } from "lucide-react";

// ── Module Registry ──
const NAV_GROUPS = [
  {
    label: "Overview",
    items: [
      { id: "dashboard", label: "Command Center", icon: Home },
    ]
  },
  {
    label: "Communication",
    items: [
      { id: "comms", label: "Radio & Mesh", icon: Radio },
      { id: "bbs", label: "Message Board", icon: MessageSquare },
      { id: "alerts", label: "Emergency Alerts", icon: AlertTriangle, badge: "2", roles: ["security", "admin"] },
    ]
  },
  {
    label: "Security",
    items: [
      { id: "security", label: "Perimeter", icon: Shield, roles: ["security", "admin"] },
      { id: "drones", label: "Drone Ops", icon: Navigation, roles: ["security", "admin"] },
      { id: "patrol", label: "Watch Schedule", icon: Eye, roles: ["security", "admin"] },
    ]
  },
  {
    label: "Agriculture",
    items: [
      { id: "agriculture", label: "Crop Planner", icon: Sprout },
      { id: "seedbank", label: "Seed Bank", icon: Circle },
      { id: "livestock", label: "Livestock", icon: BarChart3 },
    ]
  },
  {
    label: "Medical",
    items: [
      { id: "medical", label: "Patient Records", icon: Heart, roles: ["medical", "admin"] },
      { id: "pharmacy", label: "Pharmacy", icon: CircleDot, roles: ["medical", "admin"] },
    ]
  },
  {
    label: "Resources",
    items: [
      { id: "inventory", label: "Inventory", icon: Package },
      { id: "energy", label: "Energy & Fuel", icon: Zap },
      { id: "trade", label: "Trade Ledger", icon: ArrowLeftRight },
      { id: "tools", label: "Tool Library", icon: Wrench },
    ]
  },
  {
    label: "Intelligence",
    items: [
      { id: "maps", label: "Maps", icon: Map },
      { id: "weather", label: "Weather", icon: Cloud },
    ]
  },
  {
    label: "Governance",
    items: [
      { id: "governance", label: "Council", icon: Scale, roles: ["governance", "admin"] },
      { id: "education", label: "Knowledge Base", icon: BookOpen },
    ]
  },
  {
    label: "System",
    items: [
      { id: "identity", label: "Identity Admin", icon: UserCog, roles: ["admin"] },
      { id: "settings", label: "Settings", icon: Settings, roles: ["admin"] },
    ]
  },
];

const ALL_ITEMS = NAV_GROUPS.flatMap(g => g.items);

// ── Mock Data ──
const ALERTS = [
  { id: 1, level: "warning", msg: "Water filter #3 due for replacement", time: "2 hours ago", module: "inventory" },
  { id: 2, level: "info", msg: "Node RELAY-SOUTH battery 34%", time: "3 hours ago", module: "comms" },
  { id: 3, level: "success", msg: "Patrol Alpha completed perimeter sweep", time: "4 hours ago", module: "security" },
  { id: 4, level: "info", msg: "Tomato seedlings ready for transplant", time: "5 hours ago", module: "agriculture" },
  { id: 5, level: "warning", msg: "Ibuprofen below minimum (23 units)", time: "6 hours ago", module: "pharmacy" },
];

const NODES = [
  { name: "HUB-MAIN", status: "online", type: "Hub", uptime: "14d 7h" },
  { name: "MED-TERMINAL", status: "online", type: "Terminal", uptime: "14d 7h" },
  { name: "AG-SENSOR-01", status: "online", type: "Edge", uptime: "6d 3h" },
  { name: "GATE-CTRL", status: "online", type: "Access", uptime: "14d 7h" },
  { name: "RELAY-SOUTH", status: "degraded", type: "Mesh", uptime: "29d" },
  { name: "DRONE-GND", status: "offline", type: "Drone", uptime: "—" },
];

const MESH_FEED = [
  { from: "Johnson, C.", ch: "PRIMARY", msg: "Trade team returning from Berthoud, ETA 2hrs", time: "14:45" },
  { from: "WX-STATION-01", ch: "SENSOR", msg: "42°F | 68% RH | NW 8mph | 30.12 inHg rising", time: "14:30" },
  { from: "Martinez, R.", ch: "SECURITY", msg: "Perimeter clear, all sensors nominal", time: "14:15" },
];

const SUPPLY = [
  { name: "Water (gal)", val: 340, max: 500, min: 200 },
  { name: "Food (person-days)", val: 890, max: 1200, min: 600 },
  { name: "Medical supplies", val: 67, max: 150, min: 50 },
  { name: "Fuel (gal)", val: 48, max: 200, min: 100 },
  { name: "Ammunition", val: 1240, max: 2000, min: 500 },
  { name: "Seed varieties", val: 34, max: 50, min: 20 },
];

// ── Main App ──
export default function SurviveOS() {
  const [active, setActive] = useState("dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [cmdQuery, setCmdQuery] = useState("");
  const [clock, setClock] = useState("");
  const [collapsedGroups, setCollapsedGroups] = useState({});
  const role = "admin";

  useEffect(() => {
    const t = setInterval(() => {
      setClock(new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    }, 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); setCmdOpen(true); setCmdQuery(""); }
      if (e.key === "Escape") setCmdOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const activeItem = ALL_ITEMS.find(i => i.id === active) || ALL_ITEMS[0];
  const activeGroup = NAV_GROUPS.find(g => g.items.some(i => i.id === active));

  const toggleGroup = (label) => setCollapsedGroups(p => ({ ...p, [label]: !p[label] }));

  const filteredCmd = cmdQuery.trim()
    ? ALL_ITEMS.filter(i => i.label.toLowerCase().includes(cmdQuery.toLowerCase()))
    : ALL_ITEMS;

  const statusColor = (s) => s === "online" ? "#22c55e" : s === "degraded" ? "#f59e0b" : "#ef4444";
  const supplyColor = (item) => item.val < item.min ? "#ef4444" : item.val < item.min * 1.5 ? "#f59e0b" : "#22c55e";
  const levelColor = (l) => l === "warning" ? "#f59e0b" : l === "success" ? "#22c55e" : l === "info" ? "#3b82f6" : "#ef4444";

  return (
    <div style={{ display: "flex", height: "100vh", background: "#09090b", color: "#fafafa", fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif' }}>

      {/* ── Sidebar ── */}
      <aside style={{
        width: collapsed ? 52 : 240, minWidth: collapsed ? 52 : 240,
        background: "#09090b", borderRight: "1px solid #27272a",
        display: "flex", flexDirection: "column", transition: "width 0.2s, min-width 0.2s",
        overflow: "hidden",
      }}>
        {/* Team Switcher */}
        <div style={{
          padding: collapsed ? "12px 8px" : "12px 16px",
          borderBottom: "1px solid #27272a",
          display: "flex", alignItems: "center", gap: 8, cursor: "pointer",
        }}>
          <div style={{
            width: 28, height: 28, borderRadius: 6,
            background: "linear-gradient(135deg, #f59e0b, #d97706)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 800, fontSize: 13, color: "#000", flexShrink: 0,
          }}>S</div>
          {!collapsed && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#fafafa", whiteSpace: "nowrap" }}>SURVIVE OS</div>
              <div style={{ fontSize: 11, color: "#71717a", whiteSpace: "nowrap" }}>Community Hub</div>
            </div>
          )}
          {!collapsed && <ChevronsUpDown size={14} color="#71717a" />}
        </div>

        {/* Search Trigger */}
        {!collapsed && (
          <div style={{ padding: "8px 12px" }}>
            <button
              onClick={() => { setCmdOpen(true); setCmdQuery(""); }}
              style={{
                width: "100%", display: "flex", alignItems: "center", gap: 8,
                padding: "6px 10px", borderRadius: 6,
                background: "#18181b", border: "1px solid #27272a",
                color: "#71717a", fontSize: 12, cursor: "pointer",
                fontFamily: "inherit",
              }}
            >
              <Search size={13} />
              <span style={{ flex: 1, textAlign: "left" }}>Search...</span>
              <kbd style={{
                fontSize: 10, padding: "1px 5px", borderRadius: 3,
                background: "#27272a", border: "1px solid #3f3f46", color: "#a1a1aa",
                fontFamily: "inherit",
              }}>⌘K</kbd>
            </button>
          </div>
        )}

        {/* Nav Groups */}
        <nav style={{ flex: 1, overflowY: "auto", padding: "4px 0" }}>
          {NAV_GROUPS.map(group => {
            const visibleItems = group.items.filter(i => !i.roles || i.roles.includes(role));
            if (visibleItems.length === 0) return null;
            const isGroupCollapsed = collapsedGroups[group.label];

            return (
              <div key={group.label} style={{ marginBottom: 2 }}>
                {!collapsed && (
                  <button
                    onClick={() => toggleGroup(group.label)}
                    style={{
                      display: "flex", alignItems: "center", gap: 4, width: "100%",
                      padding: "6px 16px", background: "none", border: "none",
                      color: "#71717a", fontSize: 11, fontWeight: 500,
                      cursor: "pointer", fontFamily: "inherit",
                      textTransform: "uppercase", letterSpacing: "0.05em",
                    }}
                  >
                    {isGroupCollapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}
                    {group.label}
                  </button>
                )}

                {(!isGroupCollapsed || collapsed) && visibleItems.map(item => {
                  const Icon = item.icon;
                  const isActive = active === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActive(item.id)}
                      title={collapsed ? item.label : undefined}
                      style={{
                        display: "flex", alignItems: "center", gap: 8,
                        width: "calc(100% - 16px)", margin: "1px 8px",
                        padding: collapsed ? "7px 10px" : "7px 12px",
                        borderRadius: 6, border: "none", cursor: "pointer",
                        background: isActive ? "#27272a" : "transparent",
                        color: isActive ? "#fafafa" : "#a1a1aa",
                        fontSize: 13, fontFamily: "inherit", textAlign: "left",
                        transition: "all 0.1s",
                        justifyContent: collapsed ? "center" : "flex-start",
                      }}
                      onMouseEnter={e => { if (!isActive) e.target.style.background = "#18181b"; }}
                      onMouseLeave={e => { if (!isActive) e.target.style.background = "transparent"; }}
                    >
                      <Icon size={16} style={{ flexShrink: 0, color: isActive ? "#f59e0b" : "inherit" }} />
                      {!collapsed && <span style={{ flex: 1 }}>{item.label}</span>}
                      {!collapsed && item.badge && (
                        <span style={{
                          fontSize: 10, fontWeight: 600, padding: "1px 6px",
                          borderRadius: 10, background: "#ef444420", color: "#ef4444",
                        }}>{item.badge}</span>
                      )}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </nav>

        {/* User Footer */}
        <div style={{
          padding: collapsed ? "12px 8px" : "12px 16px",
          borderTop: "1px solid #27272a",
          display: "flex", alignItems: "center", gap: 10,
        }}>
          <div style={{
            width: 28, height: 28, borderRadius: "50%",
            background: "#27272a", display: "flex", alignItems: "center",
            justifyContent: "center", fontSize: 12, fontWeight: 600,
            color: "#fafafa", flexShrink: 0,
          }}>CJ</div>
          {!collapsed && (
            <>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 500, color: "#fafafa", whiteSpace: "nowrap" }}>Johnson, C.</div>
                <div style={{ fontSize: 10, color: "#71717a", textTransform: "uppercase", letterSpacing: "0.05em" }}>Admin</div>
              </div>
              <LogOut size={14} color="#71717a" style={{ cursor: "pointer", flexShrink: 0 }} />
            </>
          )}
        </div>
      </aside>

      {/* ── Main Area ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Header */}
        <header style={{
          height: 48, flexShrink: 0,
          background: "#09090b", borderBottom: "1px solid #27272a",
          display: "flex", alignItems: "center", padding: "0 16px", gap: 12,
        }}>
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{
              background: "none", border: "none", color: "#a1a1aa",
              cursor: "pointer", display: "flex", padding: 4, borderRadius: 4,
            }}
          >
            <PanelLeft size={18} />
          </button>

          <div style={{ width: 1, height: 16, background: "#27272a" }} />

          {/* Breadcrumb */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
            <span style={{ color: "#71717a" }}>{activeGroup?.label || "System"}</span>
            <span style={{ color: "#3f3f46" }}>/</span>
            <span style={{ color: "#fafafa", fontWeight: 500 }}>{activeItem.label}</span>
          </div>

          <div style={{ flex: 1 }} />

          {/* Right side */}
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {NODES.filter(n => n.status === "online").length > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "#71717a" }}>
                <Wifi size={13} color="#22c55e" />
                <span>{NODES.filter(n => n.status === "online").length} nodes</span>
              </div>
            )}
            <div style={{
              fontSize: 12, color: "#a1a1aa", fontFamily: '"JetBrains Mono", "SF Mono", "Fira Code", monospace',
              letterSpacing: "0.05em", fontVariantNumeric: "tabular-nums",
            }}>{clock}</div>
          </div>
        </header>

        {/* Content */}
        <main style={{ flex: 1, overflowY: "auto", padding: 20, background: "#09090b" }}>
          {active === "dashboard" ? (
            <DashboardView setActive={setActive} statusColor={statusColor} supplyColor={supplyColor} levelColor={levelColor} />
          ) : (
            <ModuleView item={activeItem} />
          )}
        </main>
      </div>

      {/* ── Command Palette ── */}
      {cmdOpen && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
          display: "flex", alignItems: "flex-start", justifyContent: "center",
          paddingTop: "20vh", zIndex: 999,
        }} onClick={() => setCmdOpen(false)}>
          <div style={{
            width: 520, maxHeight: 420, background: "#18181b",
            border: "1px solid #27272a", borderRadius: 12,
            display: "flex", flexDirection: "column", overflow: "hidden",
            boxShadow: "0 25px 50px rgba(0,0,0,0.5)",
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "12px 16px", borderBottom: "1px solid #27272a",
            }}>
              <Search size={16} color="#71717a" />
              <input
                autoFocus
                value={cmdQuery}
                onChange={e => setCmdQuery(e.target.value)}
                placeholder="Search modules..."
                style={{
                  flex: 1, background: "none", border: "none", color: "#fafafa",
                  fontSize: 14, outline: "none", fontFamily: "inherit",
                }}
              />
              <button onClick={() => setCmdOpen(false)} style={{
                background: "#27272a", border: "none", borderRadius: 4,
                padding: "2px 6px", fontSize: 10, color: "#a1a1aa", cursor: "pointer",
              }}>ESC</button>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: "8px" }}>
              {filteredCmd.map(item => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => { setActive(item.id); setCmdOpen(false); }}
                    style={{
                      display: "flex", alignItems: "center", gap: 10, width: "100%",
                      padding: "10px 12px", borderRadius: 6, border: "none",
                      background: "transparent", color: "#a1a1aa", fontSize: 13,
                      cursor: "pointer", fontFamily: "inherit", textAlign: "left",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = "#27272a"; e.currentTarget.style.color = "#fafafa"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#a1a1aa"; }}
                  >
                    <Icon size={16} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
              {filteredCmd.length === 0 && (
                <div style={{ padding: 20, textAlign: "center", color: "#71717a", fontSize: 13 }}>No results found</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Dashboard View ──
function DashboardView({ setActive, statusColor, supplyColor, levelColor }) {
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      {/* Title */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0, color: "#fafafa" }}>Command Center</h1>
        <p style={{ fontSize: 13, color: "#71717a", marginTop: 4 }}>Community operational overview and status</p>
      </div>

      {/* Stat Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
        {[
          { label: "Population", value: "147", sub: "+2 this month", color: "#fafafa" },
          { label: "Mesh Nodes", value: `${NODES.filter(n => n.status === "online").length}/${NODES.length}`, sub: "1 degraded", color: "#22c55e" },
          { label: "Active Alerts", value: "2", sub: "0 critical", color: "#f59e0b" },
          { label: "Days of Water", value: "28", sub: "340 gallons reserve", color: "#3b82f6" },
        ].map((s, i) => (
          <div key={i} style={{
            background: "#18181b", border: "1px solid #27272a", borderRadius: 8, padding: 16,
          }}>
            <div style={{ fontSize: 12, color: "#71717a", marginBottom: 8 }}>{s.label}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: s.color, fontVariantNumeric: "tabular-nums" }}>{s.value}</div>
            <div style={{ fontSize: 11, color: "#52525b", marginTop: 4 }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Main Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: 12, marginBottom: 16 }}>
        {/* Alerts */}
        <Card title="Recent Alerts" badge="Last 24h">
          {ALERTS.map(a => (
            <div key={a.id} onClick={() => setActive(a.module)} style={{
              display: "flex", gap: 10, padding: "10px 0",
              borderBottom: "1px solid #1e1e21", cursor: "pointer",
            }}>
              <div style={{ width: 7, height: 7, borderRadius: "50%", background: levelColor(a.level), marginTop: 5, flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: "#e4e4e7", lineHeight: 1.4 }}>{a.msg}</div>
                <div style={{ fontSize: 11, color: "#52525b", marginTop: 2 }}>{a.time}</div>
              </div>
            </div>
          ))}
        </Card>

        {/* Supply Status */}
        <Card title="Supply Status" badge="Real-time">
          {SUPPLY.map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 0" }}>
              <div style={{ width: 110, fontSize: 12, color: "#a1a1aa", flexShrink: 0 }}>{s.name}</div>
              <div style={{ flex: 1, height: 6, background: "#27272a", borderRadius: 3, overflow: "hidden" }}>
                <div style={{
                  height: "100%", borderRadius: 3, transition: "width 0.5s",
                  width: `${Math.min(100, (s.val / s.max) * 100)}%`,
                  background: supplyColor(s),
                }} />
              </div>
              <div style={{
                width: 36, textAlign: "right", fontSize: 12, fontWeight: 600,
                color: supplyColor(s), fontVariantNumeric: "tabular-nums",
              }}>{s.val}</div>
            </div>
          ))}
        </Card>
      </div>

      {/* Bottom Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
        {/* Mesh Feed */}
        <Card title="Mesh Feed" badge="LIVE" badgeColor="#22c55e">
          {MESH_FEED.map((m, i) => (
            <div key={i} style={{ padding: "8px 0", borderBottom: i < MESH_FEED.length - 1 ? "1px solid #1e1e21" : "none" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: "#e4e4e7" }}>{m.from}</span>
                <span style={{
                  fontSize: 9, padding: "1px 5px", borderRadius: 3, fontWeight: 600,
                  letterSpacing: "0.05em", textTransform: "uppercase",
                  background: m.ch === "SENSOR" ? "#052e16" : m.ch === "SECURITY" ? "#450a0a" : "#172554",
                  color: m.ch === "SENSOR" ? "#4ade80" : m.ch === "SECURITY" ? "#f87171" : "#60a5fa",
                }}>{m.ch}</span>
                <span style={{ fontSize: 10, color: "#52525b", marginLeft: "auto", fontVariantNumeric: "tabular-nums" }}>{m.time}</span>
              </div>
              <div style={{ fontSize: 12, color: "#a1a1aa", lineHeight: 1.4 }}>{m.msg}</div>
            </div>
          ))}
        </Card>

        {/* Node Status */}
        <Card title="Network Nodes" badge={`${NODES.filter(n => n.status === "online").length} online`}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 60px 60px", gap: 0, fontSize: 10, color: "#52525b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", padding: "0 0 6px" }}>
            <div>Node</div><div>Type</div><div>Uptime</div>
          </div>
          {NODES.map((n, i) => (
            <div key={i} style={{
              display: "grid", gridTemplateColumns: "1fr 60px 60px",
              padding: "6px 0", borderBottom: i < NODES.length - 1 ? "1px solid #1e1e21" : "none",
              fontSize: 12, alignItems: "center",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#e4e4e7", fontFamily: '"JetBrains Mono", monospace', fontSize: 11 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: statusColor(n.status) }} />
                {n.name}
              </div>
              <div style={{ color: "#71717a" }}>{n.type}</div>
              <div style={{ color: "#71717a", fontVariantNumeric: "tabular-nums" }}>{n.uptime}</div>
            </div>
          ))}
        </Card>

        {/* Weather */}
        <Card title="Weather Station" badge="Local">
          {[
            { k: "Temperature", v: "42°F" },
            { k: "Humidity", v: "68%" },
            { k: "Wind", v: "NW 8 mph" },
            { k: "Pressure", v: "30.12 inHg ↑" },
            { k: "Clouds", v: "Cumulus" },
            { k: "Forecast", v: "Fair 24h, front 48h" },
          ].map((r, i) => (
            <div key={i} style={{
              display: "flex", justifyContent: "space-between", padding: "7px 0",
              borderBottom: i < 5 ? "1px solid #1e1e21" : "none",
            }}>
              <span style={{ fontSize: 12, color: "#71717a" }}>{r.k}</span>
              <span style={{ fontSize: 12, fontWeight: 500, color: "#e4e4e7" }}>{r.v}</span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

// ── Card Component ──
function Card({ title, badge, badgeColor, children }) {
  return (
    <div style={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, overflow: "hidden" }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 16px", borderBottom: "1px solid #27272a",
      }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: "#a1a1aa", textTransform: "uppercase", letterSpacing: "0.05em" }}>{title}</span>
        {badge && (
          <span style={{
            fontSize: 10, padding: "2px 8px", borderRadius: 10, fontWeight: 500,
            background: badgeColor ? badgeColor + "20" : "#27272a",
            color: badgeColor || "#71717a",
            border: `1px solid ${badgeColor ? badgeColor + "40" : "#3f3f46"}`,
          }}>{badge}</span>
        )}
      </div>
      <div style={{ padding: "8px 16px 16px" }}>{children}</div>
    </div>
  );
}

// ── Module Placeholder ──
function ModuleView({ item }) {
  const Icon = item.icon;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
      <div style={{
        width: 64, height: 64, borderRadius: 12,
        background: "#27272a", display: "flex", alignItems: "center", justifyContent: "center",
        marginBottom: 20,
      }}>
        <Icon size={28} color="#f59e0b" />
      </div>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: "#fafafa", margin: "0 0 6px" }}>{item.label}</h2>
      <p style={{ fontSize: 13, color: "#71717a", margin: "0 0 24px" }}>Module connects on designated port</p>
      <div style={{ display: "flex", gap: 8 }}>
        <button style={{
          padding: "8px 20px", borderRadius: 6, border: "none",
          background: "#fafafa", color: "#09090b", fontSize: 13,
          fontWeight: 500, cursor: "pointer", fontFamily: "inherit",
        }}>Launch Module</button>
        <button style={{
          padding: "8px 20px", borderRadius: 6, fontSize: 13,
          background: "transparent", color: "#a1a1aa",
          border: "1px solid #27272a", cursor: "pointer", fontFamily: "inherit",
        }}>Documentation</button>
      </div>
    </div>
  );
}
