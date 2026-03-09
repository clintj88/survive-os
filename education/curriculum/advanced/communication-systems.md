# Advanced Band (Grades 9-12, Ages 14-18) — Communication Systems

## Overview
Communication systems engineering prepares students to build and maintain the community's communication infrastructure — radio, mesh networking, computing, and information security. The capstone is designing and deploying a complete multi-tier communication system.

## Grade 9: Electronics and Radio Theory

### Unit 1: Electronics Fundamentals (Weeks 1-18)
**Duration**: 18 weeks
**Materials**: Electronic components, breadboards, multimeter, oscilloscope (if available), soldering equipment
**Survival Relevance**: Electronics is the foundation of all communication technology. Understanding it enables repair, modification, and construction of communication equipment.

#### Learning Objectives
- Analyze AC and DC circuits (impedance, reactance, resonance)
- Design and build functional electronic circuits (amplifiers, filters, oscillators)
- Use test equipment for circuit analysis and troubleshooting
- Understand semiconductor devices (diodes, transistors, integrated circuits)

#### Lessons
**Lesson 1-6: Advanced Circuit Theory**
- Activity: AC circuits: impedance (resistance to AC), capacitive and inductive reactance, resonance (when a circuit naturally oscillates at a specific frequency — this is how radios tune). Power in AC circuits (real, reactive, apparent power).
- Practice: Calculate AC circuit parameters and build resonant circuits

**Lesson 7-12: Semiconductors and Active Circuits**
- Activity: Diodes (rectification — converting AC to DC), transistors (amplification and switching), operational amplifiers (precision amplification, filtering, comparison). Build: power supply, audio amplifier, signal filter.
- Practice: Build and test 5 functional circuits using semiconductors

**Lesson 13-18: Radio Electronics**
- Activity: Radio receiver stages: antenna → tuned circuit → amplifier → demodulator → audio amplifier → speaker. Radio transmitter stages: oscillator → modulator → power amplifier → antenna. Build a simple receiver or transmitter.
- Practice: Build a functional radio stage and demonstrate operation

#### Assessment
- Analyze AC circuits including impedance and resonance
- Build functional electronic circuits
- Explain radio receiver and transmitter operation at the circuit level

---

### Unit 2: Radio Theory and Digital Communications (Weeks 19-34)
**Duration**: 16 weeks
**Materials**: Radio equipment, antenna materials, digital communication devices
**Survival Relevance**: Understanding radio propagation, antenna design, and digital protocols enables reliable long-range communication

#### Lessons
**Lesson 1-6: Radio Propagation**
- Activity: Ground wave (follows Earth's curvature — lower frequencies), sky wave (bounces off ionosphere — HF frequencies, enables global communication), line of sight (VHF/UHF — limited by terrain). Propagation prediction: when can you reach a given distance on a given frequency?
- Practice: Predict propagation for different frequencies and distances, verify with actual radio contacts

**Lesson 7-12: Advanced Antenna Design**
- Activity: Antenna types: dipole, Yagi, quad, vertical, log-periodic. Antenna parameters: gain, bandwidth, impedance matching, polarization. Design and build antennas for specific applications. Feedline selection and loss calculation.
- Practice: Design, build, and test 3 antenna types with measured performance

**Lesson 13-16: Digital Communications**
- Activity: Digital modulation (how data is encoded on radio waves). Packet radio concepts. Meshtastic protocol details. Error correction. Digital signal processing basics.
- Practice: Configure digital communication modes and analyze protocol performance

#### Assessment
- Predict radio propagation for different scenarios
- Design and build antennas with measured performance
- Configure and analyze digital communication systems

---

## Grade 10: Ham Radio and Network Design

### Unit 3: Ham Radio Licensing and Operation (Weeks 1-18)
**Duration**: 18 weeks
**Materials**: Ham radio transceivers, study materials, antenna systems
**Survival Relevance**: Ham radio operators are the community's long-range communication specialists — connecting to other communities, monitoring for threats, and coordinating regional responses

#### Learning Objectives
- Master all Technician and General-class license material
- Operate HF, VHF, and UHF radio systems proficiently
- Establish and maintain communication schedules with other communities
- Manage emergency communication operations

#### Lessons
**Lesson 1-6: License Material**
- Activity: Study regulations, operating practices, electronics theory, antenna theory, radio wave propagation, safety — covering Technician and General class material.
- Practice: Pass practice examinations at both levels

**Lesson 7-12: Advanced Operations**
- Activity: HF operations (long-range sky wave communication), VHF/UHF repeater operation, digital modes (FT8, JS8Call, Winlink), emergency communication protocols, field day exercises.
- Practice: Make contacts on multiple bands using multiple modes

**Lesson 13-18: Communication Management**
- Activity: Establish regular communication schedules ("skeds") with other communities. Manage a radio watch schedule. Run emergency nets. Coordinate regional communication exercises.
- Practice: Manage community radio operations for a 1-month period

#### Assessment
- Pass General-class license examination
- Operate on multiple bands and modes proficiently
- Manage communication schedules and emergency operations

---

### Unit 4: Meshtastic Network Planning and Deployment (Weeks 19-34)
**Duration**: 16 weeks
**Materials**: Meshtastic devices, solar panels for powering nodes, mounting hardware, mapping tools
**Survival Relevance**: Meshtastic mesh networking provides infrastructure-free text communication across the community and to neighboring communities

#### Lessons
**Lesson 1-6: Network Design**
- Activity: Coverage analysis: terrain mapping, line-of-sight calculations, link budget analysis, node placement optimization. Design a community-wide mesh network with redundancy (multiple paths between any two points).
- Practice: Design a complete mesh network with coverage analysis

**Lesson 7-12: Deployment**
- Activity: Build and deploy relay nodes: weatherproof enclosures, solar power systems, antenna selection and installation, mounting hardware. Commission nodes and verify coverage.
- Practice: Deploy at least 3 relay nodes and verify network performance

**Lesson 13-16: Network Management**
- Activity: Monitoring: node status, battery health, coverage changes. Maintenance: replace batteries, clean solar panels, repair weather damage. Expansion: add nodes to fill coverage gaps. Documentation: network map, node inventory, maintenance schedule.
- Practice: Manage the community mesh network for 1 month

#### Assessment
- Design a mesh network with coverage analysis
- Deploy relay nodes with solar power
- Manage network operations including maintenance

---

## Grade 11: Network Infrastructure and Programming

### Unit 5: Network Infrastructure (Weeks 1-18)
**Duration**: 18 weeks
**Materials**: Computers, networking equipment, cable tools
**Survival Relevance**: The SURVIVE OS platform relies on local networking — maintaining it keeps all community digital services operational

#### Learning Objectives
- Design and build local area networks
- Configure network services (DHCP, DNS, file sharing)
- Implement network security (firewalls, access control, encryption)
- Troubleshoot complex network problems

#### Lessons
**Lesson 1-6: Network Design and Build**
- Activity: LAN design: topology (star, mesh), cable runs, switch placement, wireless access points. Build: terminate cables, configure switches, set up wireless, verify connectivity.
- Practice: Design and build a functional LAN for a community building

**Lesson 7-12: Network Services**
- Activity: DHCP (automatic IP assignment), DNS (name resolution), file sharing (Samba/NFS), web serving (Nginx/Apache), database services (SQLite). Configure services on SURVIVE OS systems.
- Practice: Configure all essential network services on a SURVIVE OS system

**Lesson 13-18: Information Security**
- Activity: Threat analysis (what are we protecting? from whom?). Access control (authentication, authorization). Encryption (data at rest, data in transit). Firewall configuration. Secure communication protocols. Backup and recovery.
- Practice: Implement security measures on community network infrastructure

#### Assessment
- Design and build functional networks
- Configure network services
- Implement security measures with documented threat analysis

---

### Unit 6: Programming and Database Management (Weeks 19-34)
**Duration**: 16 weeks
**Materials**: Computers with Python installed, database tools
**Survival Relevance**: Programming enables customization of SURVIVE OS tools and creation of new community management applications

#### Lessons
**Lesson 1-6: Python Programming**
- Activity: Data types, control flow, functions, file I/O, modules. Object-oriented programming basics. Libraries: data analysis (csv, statistics), web (http.server, requests), database (sqlite3).
- Practice: Write 10 useful programs for community operations

**Lesson 7-12: Database Management**
- Activity: Relational database design (tables, relationships, normalization). SQL (SELECT, INSERT, UPDATE, DELETE, JOIN). Database administration (backup, restore, integrity checking). Design databases for community needs.
- Practice: Design and implement a database application for a community need

**Lesson 13-16: Web Development Basics**
- Activity: HTML/CSS for creating local web interfaces. JavaScript basics for interactivity. Integration with SURVIVE OS platform (understanding the module architecture). Create or modify a SURVIVE OS module interface.
- Practice: Create a functional web interface for a community tool

#### Assessment
- Write Python programs solving real community problems
- Design and implement database applications
- Create web interfaces for community tools

---

## Grade 12: Communication Systems Capstone

### Unit 7: Capstone — Complete Communication System (Full Year)
**Duration**: Full academic year
**Materials**: All available communication equipment and infrastructure
**Survival Relevance**: The capstone produces a complete, documented, maintainable communication system for the community

#### Structure
Design and deploy a multi-tier communication system:

**Tier 1: Local (within community)**
- Meshtastic mesh network for text messaging
- Local network (LAN) for SURVIVE OS platform
- Signal systems (visual/audio for emergencies)

**Tier 2: Regional (neighboring communities)**
- VHF/UHF radio links
- Extended mesh network connections
- Scheduled communication protocols

**Tier 3: Long-Range (distant contacts)**
- HF radio station with antenna array
- Digital modes for reliable data transfer
- Emergency communication capability

#### Requirements
- System design with coverage analysis and link budgets
- Equipment specification and procurement plan
- Installation and commissioning documentation
- Operations manual (daily procedures, emergency procedures, maintenance)
- Training program for community radio operators
- Succession plan (how does the system continue when you graduate?)

#### Teaching Component
- Train 5+ community members as basic radio operators
- Deliver 5 communication technology lessons to younger students
- Create training materials for ongoing operator development

#### Assessment
- Multi-tier communication system operational
- Complete documentation package
- Community operators trained and competent
- System handed over with succession plan
