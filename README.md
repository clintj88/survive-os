




SURVIVE OS
SYSTEM ARCHITECTURE DOCUMENT
A Debian-Based Operating System for Post-Infrastructure Civilization
Communication. Agriculture. Medicine. Governance. Survival.


Version 1.0 Draft
March 2026
CLASSIFICATION: OPEN SOURCE




Prepared for AI Agent Team Development

TABLE OF CONTENTS



1. Executive Summary
SURVIVE OS is a Debian-based Linux distribution designed to serve as a complete operational platform for communities operating without modern infrastructure. It provides integrated, offline-first tools for communication, agriculture, medicine, governance, security, and education, all running on commodity hardware from Raspberry Pis to salvaged enterprise servers.
The system is architected as a modular, mesh-networked platform where every node is independently useful but becomes exponentially more powerful as additional nodes join the network. Data synchronizes automatically between nodes using conflict-free replicated data types (CRDTs), enabling communities to operate in intermittent-connectivity environments where links between nodes may be unreliable, low-bandwidth, or available only periodically.
A unified identity and access management system based on LDAP directory services provides a single identity for each community member that spans digital access (module permissions), physical access (door controllers and NFC badges via UniFi Access integration), and radio communications (Meshtastic channel provisioning). Role-based access control ensures that medical records, armory doors, and security channels are all governed by the same identity backbone.
The OS integrates three communication tiers: Meshtastic LoRa mesh for low-power local communications and sensor networks, ham radio (HF/VHF/UHF) for regional and global reach, and local network (ethernet/wifi) for high-bandwidth data transfer. Drone surveillance provides aerial reconnaissance, mapping, and agricultural monitoring capabilities.
Design Philosophy
A single Raspberry Pi running SURVIVE OS with a solar panel becomes a useful standalone tool. Connect it to a Meshtastic node and it becomes a communication hub. Add a drone and it gains aerial surveillance. Connect it to other communities and you have distributed epidemic tracking, trade networks, and mutual defense. Every additional node multiplies the capability of the entire system.


1.1 Key Design Principles
Offline-First: Every module functions without internet connectivity. Network connections enhance capability but are never required for core functionality.
Hardware Agnostic: Runs on ARM (Raspberry Pi, Pine64) and x86 (laptops, desktops, servers). Minimum viable hardware: Raspberry Pi 4 with 4GB RAM and 32GB SD card.
Modular Architecture: Each subsystem is an independent module that can be installed, removed, or updated without affecting others. Communities install only what they need.
Mesh-Native: Built from the ground up for multi-node, intermittent-connectivity environments. Data flows between nodes automatically when connections are available.
Militarized Simplicity: Interfaces are designed for stressed, fatigued, minimally-trained operators. High contrast, large targets, clear terminology, minimal steps to accomplish tasks.
Data Sovereignty: Each community owns and controls its data. Sharing between communities is explicit, permissioned, and encrypted.
Extensible: Communities can build custom modules using the provided framework, APIs, and documentation.

2. System Architecture Overview
2.1 Architecture Layers
The system is organized into four distinct layers, each building on the one below it:
Layer
Components
Responsibility
Layer 0: Hardware
Compute, storage, radio, sensors, drones
Physical infrastructure and I/O interfaces
Layer 1: OS Platform
Debian base, drivers, system services
Hardware abstraction, process management, filesystem, security
Layer 2: Core Services
Mesh sync, auth, storage, messaging
Data replication, identity, encryption, inter-module communication
Layer 3: Application Modules
Medical, agriculture, maps, governance, etc.
User-facing functionality, domain-specific logic and interfaces


2.2 Module Map
The complete system comprises 14 major subsystems containing over 65 individual modules. Each subsystem is independently installable and operates standalone, but integrates with other subsystems through the Core Services layer.

Subsystem
Priority
Key Modules
Core Platform
CRITICAL
Mesh networking, module framework, encrypted storage, timekeeping, print system
Identity & Access
CRITICAL
LDAP directory, RBAC, physical access control (UniFi), NFC badges, Meshtastic identity, audit logging
Communication
CRITICAL
Meshtastic gateway, ham radio integration, BBS/messaging, email, emergency alerts
Security & Surveillance
CRITICAL
Drone ops, aerial mapping, perimeter monitoring, watch scheduling, OPSEC
Medical
CRITICAL
Patient records (EHR), medication inventory, epidemic tracker, dental, veterinary
Sanitation & Water
HIGH
Water system monitoring, treatment logs, sanitation management
Agriculture
HIGH
Crop rotation, seed bank, soil log, livestock breeding, drone crop survey
Resource Management
HIGH
Inventory, energy tracking, barter ledger, skills registry, tool library
Navigation & Maps
HIGH
Offline OSM, community annotations, drone aerial maps, route planner
Governance
MEDIUM
Census, voting, resource allocation, treaties, dispute resolution
Weather
MEDIUM
Observation logger, remote stations (Meshtastic), forecasting, storm alerts
Engineering
MEDIUM
Maintenance scheduler, parts database, construction calculators, chemistry DB
Education
MEDIUM
Offline Wikipedia (Kiwix), textbook library, survival KB, apprenticeship tracker
Culture & Records
MEDIUM
Community journal, vital records, calendar, media library, historical archive


2.3 Node Types
Different hardware configurations serve different roles in the network. A community typically operates multiple node types:
Hub Node (Primary Server): Full-spec machine (salvaged desktop/server, or Pi 4/5 with SSD). Runs all modules, stores community master database, acts as mesh sync coordinator. Minimum: 4GB RAM, 128GB storage.
Terminal Node (Workstation): Laptop or desktop running a subset of modules. Used by medical staff, agricultural planners, or administrators. Connected to hub via ethernet or wifi. Minimum: 2GB RAM, 32GB storage.
Edge Node (Sensor/Relay): Raspberry Pi Zero or ESP32 running a single function: Meshtastic relay, weather station, perimeter sensor. Ultra-low power, often solar-powered. Minimum: 512MB RAM, 8GB storage.
Mobile Node (Field Unit): Tablet or laptop carried on patrols, foraging runs, or trade missions. Syncs data when in range of hub. Includes offline maps and knowledge base. Minimum: 2GB RAM, 32GB storage.
Drone Node (Aerial Platform): Companion computer (Pi Zero 2) on drone running ArduPilot interface, image capture, and MAVLink bridge. Minimal storage, focused on real-time data relay to ground station.

3. Core Platform Layer
The Core Platform provides foundational services that all application modules depend on. This is the first layer built and the most critical to get right.
3.1 Base Operating System
Distribution: Debian 12 (Bookworm) Stable, minimal server install
Init System: systemd (service management for all modules)
Package Management: APT with local repository mirror for offline package installation
Filesystem: ext4 with LUKS full-disk encryption (optional, recommended for sensitive nodes)
Display Server: Wayland/Cage for kiosk-mode terminals, or standard desktop for full workstations
UI Framework: Web-based (local HTTP server + browser) for maximum portability. All module UIs are served as local web applications accessible from any device with a browser on the local network.

The web-based UI approach means any device with a browser (phone, tablet, laptop) can access any module on any node. A community member can check crop rotation data from their phone, a medic can access patient records from a tablet, and an administrator can manage resources from a desktop, all connecting to the same hub node.
3.2 Mesh Networking & Data Synchronization
This is the most architecturally complex and important component. It enables the distributed, offline-first nature of the entire system.
3.2.1 Network Discovery
Nodes automatically discover each other through multiple transport layers:
Local Network: mDNS/Avahi for zero-configuration discovery on ethernet and wifi segments.
Meshtastic Bridge: Node announcements over LoRa mesh for low-bandwidth discovery beyond local network range.
Serial/USB: Direct point-to-point connections for air-gapped or minimal-infrastructure scenarios.
Sneakernet: USB drive-based sync for communities that can only exchange data via physical media carried between sites.

3.2.2 Data Synchronization Protocol
All shared data uses Conflict-free Replicated Data Types (CRDTs), which guarantee eventual consistency without requiring a central coordinator or conflict resolution logic. Each node can independently modify data, and when nodes reconnect, changes merge automatically and deterministically.

Sync Engine: Custom implementation built on Automerge or Yjs CRDT libraries.
Transport: Protocol Buffers over TCP/IP (local network), serialized CRDT operations over Meshtastic (LoRa), or file-based export/import (sneakernet).
Conflict Resolution: CRDTs are conflict-free by design. For the rare cases where semantic conflicts exist (e.g., two people edit the same patient record simultaneously), the UI presents both versions for human resolution.
Bandwidth Adaptation: The sync engine automatically adapts to available bandwidth. Over local network, full document sync. Over Meshtastic (limited to ~200 bytes/message), only critical deltas: emergency alerts, position updates, short messages.

3.2.3 Data Scoping
Not all data should sync everywhere. The system defines three data scopes:
Node-Local: Data that stays on one node only. Example: cached map tiles, temporary files.
Community-Wide: Data shared between all nodes in a community. Example: inventory, crop plans, census data. Syncs automatically over local network.
Inter-Community: Data explicitly shared between communities. Example: trade offers, epidemic alerts, treaty documents. Requires explicit authorization and travels over ham radio or sneakernet.
3.3 Identity & Authentication
Identity and access management is a critical subsystem covered in detail in Section 4. The core platform provides the infrastructure (PKI certificate authority, SSSD integration) while Section 4 defines the complete LDAP directory, role-based access control, physical access control (UniFi), Meshtastic identity binding, and audit logging systems.
3.4 Timekeeping
Without internet NTP servers, clock drift becomes a real problem across distributed nodes. Accurate time is critical for data synchronization, crop scheduling, watch rotations, and medical records.
Solar Noon Calibration: Built-in tool that uses GPS coordinates and shadow length to calculate precise solar noon, which calibrates the system clock.
Network Time Sync: Hub node acts as NTP server for the local community. All nodes sync to hub when connected.
Drift Monitoring: System tracks clock drift rates per node and warns when calibration is needed.
Radio Time Signals: If available, WWV/WWVH radio time signals (broadcast continuously on HF frequencies) provide an external time reference.
3.5 Print System
Screens break. Power fails. Paper works. The system includes comprehensive print generation for critical documents:
Medical records, medication schedules, treatment protocols
Maps with custom overlays (patrol routes, resource locations, hazards)
Agricultural calendars, planting guides, crop rotation schedules
Emergency procedure quick-reference cards
Trade agreements, treaties, community rules
Knowledge base entries for field reference

Print output is generated as PDF, compatible with any connected printer. For communities without printers, hand-copying templates are optimized for legibility.

5. Identity, Access & Physical Security
A unified identity system is foundational to every other subsystem. The same directory that authenticates a user at a workstation also controls which Meshtastic channels their radio can access, which doors they can unlock, which modules they can use, and whether they can launch a drone. This section defines the identity backbone, role-based access control model, physical access integration, and Meshtastic radio identity binding.
Single Identity Principle
Every person in the community has ONE identity that spans digital access, physical access, radio communications, and role assignments. This eliminates separate credentials for each system and provides a unified audit trail across all community operations.


15.1 Directory Services
The system implements a lightweight LDAP-compatible directory service as the single source of truth for all identity and access control decisions.

Directory Engine: LLDAP (Light LDAP) as the primary directory. LLDAP is purpose-built for small deployments, runs on a Raspberry Pi with minimal resources (~20MB RAM), and speaks standard LDAP and LDAPS protocols. It provides a web-based admin interface for user management without requiring LDAP expertise.
Client Integration: SSSD (System Security Services Daemon) on every Linux node. SSSD caches credentials and group memberships locally, enabling authentication even when the hub node (LDAP server) is unreachable. Cache lifetime is configurable (default: 7 days).
Protocol: Standard LDAPv3 over TLS. Any LDAP-compatible application can authenticate against the directory without custom integration.
Replication: LLDAP database replicates to designated backup nodes via the CRDT sync layer. If the primary hub fails, a backup node can be promoted to directory primary within minutes.
Schema: Extended LDAP schema with custom attributes for survival-specific fields (blood type, medical conditions, radio callsign, Meshtastic node ID, certifications, skills, duty status).

4.1.1 Directory Information Tree (DIT)
The LDAP directory is organized in a hierarchical structure:

Distinguished Name (DN)
Purpose
dc=survive,dc=local
Root of the directory tree
ou=People
All community members (user accounts)
ou=Groups
Role groups (medical, security, admin, agriculture, engineering, general)
ou=Devices
Registered devices (radios, door controllers, drones, workstations)
ou=Zones
Physical access zones (residential, armory, medical, supply, comms)
ou=ServiceAccounts
Machine-to-machine accounts for inter-module authentication
ou=Visitors
Temporary accounts for traders, visitors, inter-community liaisons


4.1.2 User Profile Schema
Each user record contains standard LDAP attributes plus survival-specific extensions:

Attribute
Required
Description
uid
Yes
Unique username (login identifier)
cn / displayName
Yes
Full name as known in the community
userCertificate
Yes
X.509 certificate for PKI authentication
memberOf
Yes
Group memberships (determines roles and access)
surviveBloodType
No
Blood type (A+, O-, etc.) for medical emergencies
surviveMedicalNotes
No
Critical medical info (allergies, conditions) — encrypted
surviveCallsign
No
Ham radio callsign (if licensed)
surviveMeshtasticID
No
Bound Meshtastic node long_name and ID
surviveSkills
No
Skill tags (medical, welding, farming, radio, etc.)
surviveCertifications
No
Training completions (CPR, radio operator, drone pilot)
surviveNFCBadgeID
No
NFC badge serial number for physical access
surviveDutyStatus
No
Current status: on-duty, on-call, off-duty, deployed
surviveEmergencyContact
No
Name and relationship of emergency contact
survivePhotoHash
No
Content-addressed reference to ID photo


15.2 Role-Based Access Control (RBAC)
Access to every module, physical zone, and communication channel is governed by role membership. Users can hold multiple roles simultaneously. Roles are implemented as LDAP groups.

4.2.1 Role Hierarchy
Role
Module Access
Physical Zone Access
Administrator
All modules, system configuration, user management
All zones including comms room and server room
Medical
EHR, pharmacy, epidemic tracker, dental, vet records
Medical facility, pharmacy storage, quarantine areas
Security
Perimeter monitoring, drone ops, watch scheduling, OPSEC
Armory, security post, perimeter gates, drone hangar
Agriculture
Crop planner, seed bank, livestock, drone crop survey
Agricultural storage, greenhouses, seed vault
Engineering
Maintenance scheduler, parts DB, construction, chemistry
Workshop, tool storage, generator/power room
Communications
Radio operations, Meshtastic management, BBS, alerts
Communications room, antenna installations
Governance
Census, voting, allocation, treaties, dispute records
Council chamber, records archive
General
Knowledge base, maps, weather, personal messaging, inventory (read)
Residential areas, common areas, general storage


4.2.2 Access Control Policies
Least Privilege: Users receive only the access required for their assigned roles. A farmer does not need access to medical records. A medic does not need access to the armory.
Separation of Duties: Critical operations require two authorized users. Examples: opening the armory requires two Security-role holders. Modifying medication inventory requires two Medical-role holders. Changing user roles requires an Administrator plus one other role holder.
Time-Based Access: Zone access can be restricted to specific time windows. Night-shift security gets armory access only during their watch period. Agricultural zones may be open sunrise to sunset only.
Temporary Elevation: When a role holder is unavailable (illness, travel), an Administrator can grant temporary role access to a designated substitute. Temporary grants have mandatory expiration dates and are prominently logged.
Visitor Access: Traders, inter-community liaisons, and visitors receive temporary accounts in ou=Visitors with limited access (common areas, designated trade zone) and automatic expiration (default: 72 hours, renewable).

4.2.3 Emergency Override (Break-Glass)
In life-threatening emergencies, the access control system must never prevent critical action:
Medical Emergency Override: Any user can request emergency access to medical supplies and records. Override is granted immediately but triggers a high-priority alert to all Administrators and Medical-role holders. Full audit trail is recorded.
Security Emergency Override: Armory access can be forced with a physical key kept in a sealed, tamper-evident container at the security post. Breaking the seal triggers an alert.
Full Lockdown Override: Administrators can issue an emergency lockdown command that locks all controlled doors simultaneously. Propagated over local network and Meshtastic. Requires two Administrators to lift.
Dead-Man Failsafe: If the directory server is unreachable for a configurable period (default: 4 hours), all physical access systems fail to a pre-configured safe state (typically: exterior doors locked, interior doors unlocked) to prevent people from being trapped.
15.3 Authentication Methods
The system supports multiple authentication factors, layered based on the sensitivity of the resource being accessed:

Method
Use Case
Implementation
X.509 Certificate
Workstation login, module access, inter-node auth
Certificate stored on USB token or in local keystore. Issued by community CA. Validated against LDAP directory.
NFC Badge
Physical door access, quick workstation unlock
Unique badge ID stored in LDAP surviveNFCBadgeID attribute. Badge readers at doors and workstations. Badges can be revoked instantly via directory.
PIN / Passphrase
Fallback login, secondary factor for sensitive zones
Hashed and stored in LDAP userPassword field. Minimum 6 digits for PIN, 12 characters for passphrase.
Multi-Factor
Armory, pharmacy, server room, admin actions
Badge + PIN required. Both factors must match the same user identity in the directory.
Biometric (optional)
High-security zones if hardware available
Fingerprint reader integration. Template stored locally on reader, linked to LDAP identity. NOT required, NOT relied upon as sole factor.
Radio Identity
Meshtastic channel access, position reporting
Cryptographic key on Meshtastic node bound to user identity. Node long_name set to uid. Channel encryption keys provisioned from directory.


15.4 Physical Access Control
Physical security is integrated into the same identity system as digital access. The OS manages door controllers, badge readers, and access schedules from a central interface.

4.4.1 UniFi Access Integration
Controller: UniFi Access runs as a self-hosted application on the hub node (or dedicated UniFi hardware if available). The SURVIVE OS communicates with it via the UniFi Access API.
Sync: User identities and badge assignments are synchronized from LDAP to the UniFi Access controller automatically. When a badge is assigned in the directory, it becomes active on all configured door readers within seconds.
Zone Mapping: Physical zones defined in ou=Zones in LDAP map to UniFi Access door groups. Role membership determines which zones a badge can open.
Schedule Enforcement: Time-based access schedules are pushed to UniFi Access from the OS. Watch rotation changes in the security module automatically update door access schedules.
Event Ingestion: Door open/close events, access granted/denied events, and tamper alerts flow from UniFi Access back into the OS security module for logging, mapping, and alerting.

4.4.2 Zone Architecture
The community is divided into physical security zones with cascading access requirements:

Zone
Classification
Auth Required
Access Roles
Perimeter Gates
Controlled
Badge
Security, Admin (visitors escorted)
Common Areas
Open
None (inside perimeter)
All members
Residential
Restricted
Badge
All members (own area only)
Medical Facility
Restricted
Badge
Medical, Admin
Pharmacy Storage
High Security
Badge + PIN
Medical (pharmacist designated)
Agricultural Store
Restricted
Badge
Agriculture, Admin
Seed Vault
High Security
Badge + PIN
Agriculture (curator designated)
Armory
Critical
Badge + PIN + 2-person
Security (2 required), Admin
Communications Room
Restricted
Badge
Communications, Security, Admin
Server / Hub Room
Critical
Badge + PIN
Admin, Engineering
Drone Hangar
Restricted
Badge
Security (drone cert.), Admin
Workshop / Forge
Restricted
Badge
Engineering, Admin
Council Chamber
Restricted
Badge
Governance, Admin
Supply Warehouse
Restricted
Badge
Resource mgmt., Admin
Trade Zone
Controlled
Visitor badge
All + authorized visitors


4.4.3 Alternative Door Controllers
While UniFi Access is the primary supported platform, the system is designed to work with other access control hardware:
ESP32 + Relay: Low-cost DIY door controller. ESP32 reads NFC badge via RC522/PN532 module, validates against cached access list from LDAP, triggers door strike relay. Updates access list over wifi or Meshtastic. Cost: ~$15 per door.
Generic Wiegand: Any Wiegand-protocol badge reader can interface with a Raspberry Pi GPIO running a custom controller daemon. Supports existing commercial badge readers.
Mechanical Override: Every electronically controlled door must have a physical key backup. Electronic systems enhance security; they must never be the only way through a door.
15.5 Meshtastic Radio Identity Binding
Each Meshtastic radio node in the community network is cryptographically bound to a user identity in the directory. This provides accountability, role-based channel access, and enables the system to associate position reports with specific individuals.

4.5.1 Provisioning Workflow
Administrator connects new Meshtastic device to hub node via USB or Bluetooth.
OS detects the device and presents a provisioning interface.
Administrator selects the user this radio is assigned to from the LDAP directory.
OS writes configuration to the device: long_name set to username, channel encryption keys based on user roles, GPS reporting interval, and device-specific PSK.
Meshtastic node ID and configuration hash are recorded in the user's LDAP record (surviveMeshtasticID attribute).
Device is activated and begins participating in the mesh with proper identity and channel access.

4.5.2 Channel Access by Role
Meshtastic channels are encrypted with role-specific keys. A radio only receives the keys for channels its assigned user is authorized to access:

Channel
Authorized Roles
Traffic Type
PRIMARY
All members
General community communication, announcements
SECURITY
Security, Admin
Patrol coordination, perimeter alerts, incident reports
MEDICAL
Medical, Security, Admin
Medical emergencies, patient transport, triage coordination
ADMIN
Admin, Governance
Leadership communication, sensitive operational decisions
SENSOR
System (automated)
Sensor data: weather, soil, perimeter motion, water levels
TRADE
All members + visitors
Trade negotiations, market announcements, inter-community commerce
EMERGENCY
All members (receive-only broadcast)
Community-wide emergency alerts, evacuation orders, lockdown commands


4.5.3 Position Tracking & Privacy
GPS-equipped Meshtastic nodes report position data. This is invaluable for security (patrol tracking) and safety (locating lost/injured members) but raises privacy concerns. The system implements a consent-based model:
Mandatory Tracking: Security-role members on active duty share position on the SECURITY channel. This is a condition of the role and enables the watch management system to verify checkpoint compliance.
Opt-In Tracking: All other members can enable position sharing on the PRIMARY channel. Useful for foraging parties, scouting runs, and general safety. Can be toggled per-trip.
Emergency Beacon: Any member can trigger an emergency position broadcast at any time (dedicated button on Meshtastic hardware). This overrides all privacy settings and broadcasts position on all channels.
Position Data Retention: Position history is retained for 30 days for security analysis, then automatically purged. Only aggregated patrol compliance data is kept long-term.
15.6 Audit & Compliance
Every access event across all systems is logged to a tamper-evident audit trail:
Digital Access Log: Module logins, data reads/writes, role changes, configuration changes. Stored in an append-only log with cryptographic chaining (each entry signs the previous, creating a tamper-evident chain).
Physical Access Log: Door events (open, close, granted, denied, forced, tamper) with badge ID, time, and door ID. Ingested from UniFi Access and ESP32 controllers.
Radio Access Log: Channel join/leave, message send (metadata only, not content), position reports. Ingested from Meshtastic gateway daemon.
Admin Action Log: All administrative actions (user creation, role assignment, badge provisioning, emergency override) logged with who, what, when, and why (mandatory justification field for sensitive actions).

Audit logs are synced to backup nodes but are immutable. They cannot be edited or deleted by any user, including administrators. Log review is a Governance function and is included in regular community transparency reporting.
15.7 Inter-Community Identity Federation
When communities establish formal relationships (trade agreements, mutual defense treaties), they can federate their identity systems to enable cross-community authentication:
CA Trust Exchange: Communities exchange root CA certificates during in-person first contact. This enables verification of identity certificates issued by the other community.
Liaison Accounts: A federated community can create liaison accounts that are recognized by the partner community's directory. Liaisons receive visitor-level access plus any specifically granted permissions.
Shared Radio Channels: Inter-community Meshtastic channels use shared encryption keys negotiated between community administrators. Only designated liaison-role members receive these keys.
Trade Identity: Traders from a federated community present their certificate (via NFC badge or USB token). The receiving community's system verifies the certificate against the trusted CA and grants trade-zone access automatically.
Revocation: If a community relationship ends or a member is expelled, their CA can issue a Certificate Revocation List (CRL) that is distributed to partner communities. Revoked certificates are immediately denied access.

5. Communication Subsystem
The communication system provides three integrated tiers of connectivity, each serving different range, bandwidth, and power requirements. Messages flow seamlessly between tiers through gateway services.
15.1 Tier 1: Meshtastic LoRa Mesh
Range: 1-15 km per hop (terrain dependent), unlimited with mesh relay
Bandwidth: ~200 bytes per message, ~10 messages per minute
Power: Extremely low. Solar-powered nodes last indefinitely.
Hardware: Heltec V3, TTGO T-Beam, RAK WisBlock (ESP32 + LoRa radio, $20-40 each)

Integration Points
Gateway Daemon: Meshtastic-python running on hub node bridges mesh traffic to the OS network via serial or Bluetooth. Messages from handhelds appear in the BBS and vice versa.
Sensor Network: ESP32 nodes with attached sensors (temperature, humidity, water level, soil moisture, PIR motion) publish readings over Meshtastic. The OS ingests sensor data into the weather, agriculture, and security modules automatically.
Position Tracking: GPS-equipped Meshtastic nodes (T-Beam) carried by patrol members report positions to the community map in near-real-time.
Emergency Alerts: Priority channel for one-touch emergency alerts. Broadcast across entire mesh with location. Triggers alarm on all connected terminals and handhelds.
Channel Architecture: Encrypted channels segregate traffic: PRIMARY (general), SECURITY (patrols/alerts), MEDICAL (emergency medical), ADMIN (leadership), SENSOR (automated readings).
15.2 Tier 2: Ham Radio (HF/VHF/UHF)
Range: VHF/UHF: 10-80 km (with repeaters). HF: Global (skywave propagation).
Bandwidth: Voice, plus digital modes (300-9600 bps depending on mode)
Power: Moderate. 50-100W for HF, 5-50W for VHF/UHF.

Digital Mode Integration
Winlink: Store-and-forward email over radio. Compose messages on the OS, transmit via Winlink over HF/VHF. Messages route through Winlink network or direct P2P.
JS8Call: Keyboard-to-keyboard messaging over HF with store-and-forward capability. Extremely weak-signal performance. Ideal for inter-community text communication.
Packet Radio: AX.25 packet radio for structured data exchange. BBS-to-BBS relay between communities.
VARA/ARDOP: Higher-speed digital modes for file transfer (images, documents, small databases) over radio.
APRS: Automatic Packet Reporting System for position reporting, weather stations, and short messages over VHF.

Frequency Database
The OS maintains a community-editable frequency database: who is on what frequency, what mode, scheduled check-in times, repeater locations, and propagation predictions based on time of day and solar conditions.
15.3 Tier 3: Local Network (Ethernet/WiFi)
Range: Building to campus scale (10m - 1km)
Bandwidth: 100 Mbps - 1 Gbps
Use: Full data sync, web UI access, file sharing, drone video feed

The local network is the high-bandwidth backbone within a community. All nodes connect via ethernet or wifi to the hub. The OS includes a built-in DHCP server, DNS server, and web server so the network is self-contained.
15.4 Message Routing
The OS implements a unified message bus. A user composes a message and the system automatically selects the best delivery route:
Recipient on local network? Deliver directly via TCP.
Recipient on Meshtastic mesh? Route via LoRa gateway.
Recipient in another community? Queue for ham radio transmission at next scheduled contact window.
No connectivity? Store message, deliver when any path becomes available.

The user does not need to know or care about the transport layer. They send a message, the system handles delivery.

6. Security & Surveillance Subsystem
15.1 Drone Operations
Flight Controller: ArduPilot / PX4 open-source autopilot on Pixhawk-compatible hardware
Companion Computer: Raspberry Pi Zero 2 W running MAVLink bridge, image capture, and telemetry relay
Ground Station: QGroundControl or Mission Planner integrated into the OS, communicating via MAVLink protocol
Communication Link: 900 MHz or 2.4 GHz telemetry radio for command/control, 5.8 GHz for video downlink

Capabilities
Patrol Flights: Pre-programmed routes along community perimeter. Automated launch, fly, photograph, return, charge cycle.
Aerial Mapping: Systematic grid photography with overlap for orthomosaic stitching. Produces high-resolution community maps updated monthly.
Crop Survey: NDVI-capable imaging (modified camera with IR filter removed) identifies plant stress patterns invisible from ground level.
Search & Rescue: Automated grid search patterns. Thermal camera integration for detecting people in wilderness.
Incident Response: On-demand launch to investigate perimeter alerts from Meshtastic sensor network.

Fleet Management
The OS tracks airframes, batteries, flight hours, maintenance schedules, and mission logs. It calculates remaining battery life based on planned route, wind conditions, and payload weight. Parts inventory integration warns when replacement props, motors, or batteries are needed.
15.2 Perimeter Monitoring
A layered sensor network built on Meshtastic-connected ESP32 nodes:
PIR Motion Sensors: Detect human/large-animal movement. Trigger alert with node ID and timestamp to security terminals.
Magnetic Reed Switches: On gates and doors. Report open/closed status.
Trip Wire Sensors: Mechanical trigger sends alert when wire is disturbed.
Camera Traps: ESP32-CAM modules that capture images on motion detection, store locally, and transmit thumbnail over Meshtastic (or full image when wifi is available).

All sensor events are logged, mapped, and time-stamped. The security module displays a real-time perimeter status map showing sensor health, recent alerts, and patrol positions.
15.3 Watch & Patrol Management
Automated watch schedule generation based on available personnel and shift preferences
Patrol route planning with waypoints displayed on offline map
Check-in system via Meshtastic (patrol members press button at waypoints)
Missed check-in alerts escalate automatically
Incident reporting with location, time, description, and response actions
Historical analysis of security events (time patterns, location clusters)

7. Agriculture Subsystem
Agriculture is the foundation of long-term survival. This subsystem manages the full cycle from planning through harvest and preservation, augmented by sensor data and drone imagery.
15.1 Crop Rotation Planner
Visual field map with plot assignments and rotation schedules
Four-year rotation templates (legume-leaf-fruit-root) customizable per climate
Companion planting database (what grows well together, what to separate)
Planting calendar tied to local frost dates and weather observation data
Yield prediction based on historical data from previous seasons
15.2 Seed Bank Management
Inventory of all seed varieties with quantity, source, and date collected
Germination rate tracking (test samples annually, record results)
Viability prediction based on species, storage conditions, and age
Genetic diversity alerts (warns if a crop relies on too few seed sources)
Cross-community seed exchange coordination
15.3 Livestock Management
Individual animal records with breed, birth date, parentage, health history
Breeding planner with inbreeding coefficient calculator (warns when genetic diversity is low)
Feed requirement calculator based on species, age, weight, and production stage
Veterinary treatment log with medication tracking
Production records (milk yield, egg count, weight gain) for performance optimization
15.4 Drone-Augmented Agriculture
Automated crop health surveys using modified camera (NDVI vegetation index)
Irrigation planning from aerial terrain analysis (water flow patterns)
Pest and disease early detection from aerial imagery patterns
Harvest readiness assessment from color and size analysis
Field boundary mapping and area calculation
15.5 Sensor Integration
Meshtastic-connected ESP32 sensor nodes deployed in fields provide:
Soil moisture at multiple depths (capacitive sensors)
Ambient temperature and humidity
Rainfall measurement (tipping bucket gauge)
Frost alerts (temperature threshold triggers)
All data feeds into the weather module and planting advisor

8. Medical Subsystem
Access-controlled (medical role required). All data encrypted at rest. Designed for trained community health workers, not necessarily physicians.
15.1 Electronic Health Record (EHR-Lite)
Patient demographics, allergies, blood type, chronic conditions
Visit notes with structured templates (SOAP format: Subjective, Objective, Assessment, Plan)
Vital signs tracking with trend visualization (temperature, pulse, BP, respiration)
Wound care log with photo documentation (camera integration)
Vaccination records
Printable patient summary for transfer between communities
15.2 Medication Management
Community pharmacy inventory with lot numbers and expiration dates
Automated expiration alerts (30, 60, 90 day warnings)
Prescription tracking (who received what, when, dosage)
Drug interaction checker (offline database)
Natural medicine reference (cross-linked with knowledge base)
Dosage calculator (weight-based pediatric dosing)
15.3 Epidemic Surveillance
This module provides early warning of disease outbreaks across communities:
Syndromic surveillance: tracks symptom clusters (respiratory, GI, fever, rash) across the population
Automated alert when symptom clusters exceed baseline thresholds
Cross-community data sharing (anonymized symptom counts transmitted via ham radio)
Contact tracing tools for identified infectious cases
Quarantine management (isolation tracking, supply coordination)
Historical epidemic timeline for pattern recognition
15.4 Specialty Modules
Childbirth & Prenatal: Prenatal visit schedule, growth tracking, risk factor identification, delivery log, postpartum follow-up.
Dental: Tooth chart, treatment history, emergency protocols, preventive care scheduling.
Mental Health: Voluntary wellness check-in system (privacy-first design, no forced reporting).
Veterinary: Livestock health records (cross-linked with agriculture livestock module).

9. Resource Management Subsystem
15.1 General Inventory
Categorized inventory: food, water, medical, tools, fuel, ammunition, building materials, trade goods
Barcode/QR scanning support (camera-based) for rapid intake and tracking
Consumption rate tracking with days-of-supply projections
Minimum stock level alerts
Location tracking (which storage area, building, or cache holds what)
Audit log (who added/removed what, when)
15.2 Energy & Fuel Tracking
Solar panel output monitoring (if sensors installed)
Battery bank state-of-charge tracking
Fuel reserves (gasoline, diesel, propane, firewood) with consumption rate projections
Generator runtime logging and maintenance scheduling
Power budget calculator (available watts vs. demand)
15.3 Trade & Barter Ledger
Double-entry bookkeeping for inter-personal and inter-community trades
Community-defined exchange rates (labor hours, commodity units)
Trade history and balance tracking between communities
Market day scheduling and inventory publication
Skills registry (who knows what) as tradeable services
15.4 Tool Library
Shared tool inventory with check-in/check-out system
Maintenance schedules per tool (sharpening, oiling, repair)
Usage history for wear prediction
Reservation system for high-demand items

10. Navigation & Mapping Subsystem
15.1 Offline Map System
Base Maps: Pre-loaded OpenStreetMap tile data for the community region. Stored as MBTiles format. Can be expanded to larger areas with additional storage.
Tile Server: Local tile server (TileServer GL or similar) serves map tiles to all web-based module UIs that need map display.
Rendering: MapLibre GL JS for web-based map display with custom overlays.

15.2 Community Map Annotations
Users add custom layers to the base map:
Resource locations (water sources, fuel caches, supply depots)
Hazard zones (contamination, structural collapse, flooding)
Agricultural plots with crop assignments
Patrol routes and checkpoints
Inter-community trade routes and travel corridors
Meshtastic node locations with coverage estimation
All annotations sync across community nodes via CRDT
15.3 Drone-Updated Aerial Maps
Orthomosaic generation from drone survey photos (OpenDroneMap integration)
Aerial map layers overlaid on base OSM data
Change detection between survey dates (new construction, crop changes, erosion)
3D terrain modeling for drainage and construction planning
15.4 Printable Map Generation
Generate high-quality printable maps at any scale with selected overlays. Critical for patrols, foraging teams, and inter-community travel where electronic devices may not be available.

11. Additional Subsystems
15.1 Governance
Census and population tracking with skills assessment
Community voting system (transparent, auditable, paper-ballot backup)
Resource allocation calculator and rationing management
Treaty and agreement repository with version history
Dispute resolution case tracking
Legal precedent database (builds over time as community law develops)
Watch/work duty scheduling with fairness tracking
Community journal and historical chronicle
Birth, death, and marriage registry
Calendar with community events, memorial days, and seasonal celebrations
Photo and document archive with date and event tagging
15.2 Weather
Manual observation logger (cloud type, wind, pressure feel, temperature)
Remote weather station data ingestion from Meshtastic sensor nodes
Pattern analysis engine that improves forecasting accuracy over time with local data
Planting window advisor correlated with historical weather patterns
Storm alert propagation between communities via radio
Seasonal trend tracking for long-term agricultural planning
15.3 Engineering & Maintenance
Preventive maintenance scheduler for all community infrastructure (water systems, power, buildings, vehicles)
Parts cross-reference database (what fits what, salvage compatibility)
Construction material calculator (lumber, concrete, roofing estimates from dimensions)
Chemistry recipe database (soap, charcoal, biodiesel, preservation, adhesives)
Drone build and repair guides with parts inventory integration
Technical drawing viewer for reference documents
15.4 Education & Knowledge
Offline Wikipedia via Kiwix (full English Wikipedia is ~90GB, or subset versions available)
OpenStax free textbook library (math, science, medicine, engineering)
Survival knowledge base (the app we already built, integrated as a module)
Apprenticeship tracking with skill assessment checklists
Lesson plan templates and curriculum guides
Music, literature, and story archive (Project Gutenberg integration)
Children's educational software (math games, reading exercises)

12. Data Architecture
15.1 Storage Engine
Primary Database: SQLite per module (lightweight, zero-configuration, battle-tested, runs everywhere). Each module maintains its own SQLite database.
CRDT Sync Layer: Automerge documents for all shared/synced data. SQLite serves as local read-optimized cache.
File Storage: Filesystem-based for large objects (images, documents, map tiles). Content-addressed (hash-named) for deduplication across sync.
Encryption: SQLCipher for encrypted databases (medical, security). LUKS for full-disk encryption on sensitive nodes.

15.2 Schema Design Principles
Every record has a globally unique ID (UUID v7 for time-ordered, or UUID v4).
Every record carries a vector clock (node ID + sequence number) for CRDT ordering.
Soft deletes only. Records are marked deleted, never physically removed (preserves sync consistency).
Schema versioning with forward/backward migration support.
All timestamps in UTC. Local time display is a UI concern only.
Binary data (images, files) stored as content-addressed blobs, referenced by hash from structured records.
15.3 Sync Topology
Within a community, the hub node is the sync coordinator. Nodes sync bidirectionally with the hub. Between communities, designated gateway nodes exchange data over ham radio or sneakernet.

Sync operations are idempotent and ordered. If the same data arrives twice (from two different paths), the result is identical to receiving it once. This is critical for unreliable transport layers like radio.
15.4 Backup Strategy
Automated daily backup of all databases to USB-attached storage on hub node
Encrypted backup export for off-site storage (carry to a cache location)
Each terminal node maintains a full or partial replica, providing inherent redundancy
Paper backup for critical data: printed patient records, inventory summaries, seed bank catalogs

13. Hardware Requirements
Node Type
CPU
RAM
Storage
Example Hardware
Hub
4+ cores
4-8 GB
128 GB+
Pi 4/5, salvaged desktop, Intel NUC
Terminal
2+ cores
2-4 GB
32 GB+
Any laptop, desktop, Pi 4
Edge/Sensor
1 core
512 MB
8 GB
Pi Zero, ESP32 (Meshtastic)
Mobile
2+ cores
2 GB+
32 GB+
Laptop, tablet, Pi 4 + battery
Drone
4 cores
1 GB
16 GB
Pi Zero 2 + Pixhawk FC


15.1 Communication Hardware
System
Hardware
Est. Cost
Range
Meshtastic Node
Heltec V3 / T-Beam
$25-40
1-15 km per hop, unlimited mesh
Meshtastic Solar Relay
T-Beam + 6W panel + battery
$60-80
Permanent autonomous relay node
VHF/UHF Radio
Baofeng UV-5R or similar
$25-60
5-30 km (50+ km with repeater)
HF Radio
Xiegu G90 / IC-7300
$400-1200
Worldwide (HF propagation)
TNC / Sound Card
Digirig, SignaLink
$50-120
Digital mode interface to radio


14. Development Roadmap
Development is organized into four phases, each delivering a usable system with increasing capability:

Phase 1: Foundation (Weeks 1-4)
Deliverable: Bootable Debian image with core services, identity system, and knowledge base.
Debian base image build system (ARM + x86)
Module framework (systemd services, local web server, SQLite per module)
LLDAP directory service with SSSD client integration on all nodes
RBAC role definitions, group structure, and module-level access enforcement
NFC badge provisioning pipeline and authentication middleware
Web UI shell (navigation, LDAP authentication, responsive layout)
Survival knowledge base (existing app, integrated as first module)
Offline map viewer with OpenStreetMap tiles
Basic inventory management
Print system (PDF generation)
Phase 2: Communication & Physical Access (Weeks 5-8)
Deliverable: Networked system with multi-tier communication and physical access control.
Meshtastic gateway daemon and configuration UI
Meshtastic radio identity binding and channel provisioning from LDAP
Mesh sync engine (CRDT-based, local network transport)
BBS / community message board
Ham radio integration (Winlink, JS8Call, packet)
Emergency alert system
UniFi Access integration (API sync, door events, zone management)
ESP32 DIY door controller firmware and LDAP access list caching
Physical access audit log ingestion and security module integration
Frequency database and contact scheduler
Meshtastic sensor data ingestion pipeline
Phase 3: Domain Modules (Weeks 9-16)
Deliverable: Full-featured operational platform.
Medical EHR with medication management
Agriculture suite (crop rotation, seed bank, livestock)
Weather observation and forecasting
Governance (census, voting, resource allocation)
Drone integration (ArduPilot/MAVLink ground station)
Aerial mapping pipeline (OpenDroneMap integration)
Perimeter security sensor network
Trade and barter ledger
Education module (Kiwix integration)
Phase 4: Integration & Hardening (Weeks 17-20)
Deliverable: Production-ready release.
Inter-community identity federation (CA trust exchange, liaison accounts, trade badges)
Inter-community sync over ham radio
Sneakernet sync (USB export/import)
Security audit and penetration testing
Performance optimization for Pi 4 minimum spec
Comprehensive testing on all target hardware
Documentation: user guides, admin guides, developer docs
ISO image generation and distribution

15. AI Agent Team Structure
Development will be executed by specialized AI agent teams, each responsible for a subsystem. Teams work in parallel with integration points defined by the Core Services APIs.

Agent Team
Scope
Key Technologies
Platform Team
Debian image, module framework, web server, print system
Debian, systemd, nginx, SQLite, LUKS
Identity Team
LDAP directory, RBAC, physical access, badge provisioning, Meshtastic identity, UniFi integration, audit logging
LLDAP, SSSD, PKI/X.509, UniFi Access API, NFC, ESP32 door controllers
Sync Team
CRDT engine, mesh sync, data replication, conflict resolution
Automerge/Yjs, Protocol Buffers, CRDTs, WebSocket
Comms Team
Meshtastic gateway, ham radio, BBS, email, alerts
Meshtastic-python, Direwolf, Pat (Winlink), JS8Call
Security Team
Drone ops, perimeter sensors, watch management, OPSEC
ArduPilot, MAVLink, QGroundControl, OpenDroneMap, ESP-IDF
Agriculture Team
Crop planning, seed bank, livestock, soil, drone survey
SQLite, MapLibre, sensor integration, NDVI processing
Medical Team
EHR, pharmacy, epidemic tracker, dental, vet
SQLite, SQLCipher, HL7 FHIR (simplified), PDF reports
Resource Team
Inventory, energy, trade ledger, tools, skills registry
SQLite, barcode scanning, charting libraries
Maps Team
Offline OSM, annotations, drone maps, route planning, print
TileServer GL, MapLibre, OpenDroneMap, GDAL
Governance Team
Census, voting, allocation, treaties, dispute records
SQLite, web forms, PDF generation, CRDT voting protocol
Knowledge Team
Wikipedia, textbooks, survival KB, education, culture
Kiwix, Project Gutenberg, existing React app, Markdown
Weather Team
Observation log, sensor data, forecasting, alerts
Meshtastic sensor pipeline, statistical analysis, charting
Frontend Team
Web UI shell, responsive design, component library, UX
HTML/CSS/JS, React or Preact, Leaflet/MapLibre, Chart.js


15.1 Integration Contract
All teams build to a common integration contract:
Every module is a systemd service with a defined lifecycle (start, stop, health check).
Every module serves its UI as a local web application on a designated port.
Every module stores data in its own SQLite database at a standard path.
Shared data is exposed through the CRDT sync layer, not direct database access.
Inter-module communication uses a local message bus (Redis pub/sub or similar lightweight broker).
All configuration is stored in a standard YAML format at /etc/survive/[module].yml.
Every module includes a health check endpoint that the platform monitors.
All modules must function fully offline. Network connectivity enhances but never gates functionality.

16. Conclusion
SURVIVE OS is more than software. It is the digital foundation for rebuilding civilization after infrastructure failure. By combining battle-tested open source components (Debian, SQLite, OpenStreetMap, ArduPilot, Meshtastic, Kiwix) with a purpose-built integration layer, the system provides capabilities that no single tool can deliver: a unified operational platform where communication, agriculture, medicine, security, governance, and education all share data and reinforce each other.

The modular architecture ensures that the system is useful at every scale: a single Raspberry Pi in a farmhouse, a mesh of nodes across a small town, or a network of communities spanning hundreds of kilometers connected by ham radio. Each node added to the network increases the capability of every other node.

The most important design principle is that every module works offline, works on cheap hardware, and works for operators who may be stressed, exhausted, and minimally trained. Complexity is hidden from the user and managed by the system. The human sees a map with their patrol route, not a CRDT synchronization protocol. They see their crop rotation schedule, not a database query. They send a message to another community, not a Winlink session over AX.25.

The Ultimate Survival Tool
Knowledge that is not accessible is knowledge that does not exist. SURVIVE OS ensures that the collective knowledge and operational capability of a community is preserved, shared, and actionable regardless of what happens to the infrastructure we currently take for granted.



END OF DOCUMENT
v1.0 Draft — March 2026
