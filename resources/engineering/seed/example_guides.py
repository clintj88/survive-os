"""Pre-seed technical guides for the engineering module."""

import json

from app.database import execute


def seed_guides() -> None:
    guides = [
        {
            "title": "Solar Panel Maintenance Guide",
            "category": "solar",
            "content": """# Solar Panel Maintenance

## Monthly Tasks
- Visual inspection for cracks, discoloration, or hot spots
- Check all wiring connections for corrosion or looseness
- Clean panels with soft cloth and water (no abrasives)
- Verify charge controller readings match expected output

## Quarterly Tasks
- Tighten all mounting hardware
- Check battery bank water levels (flooded lead-acid)
- Clean battery terminals and apply anti-corrosion spray
- Test inverter output voltage and waveform
- Inspect ground fault protection

## Annual Tasks
- Full electrical system audit
- Replace any corroded wiring or connectors
- Recalibrate charge controller settings for battery age
- Check panel tilt angle for seasonal optimization

## Troubleshooting
- **Low output**: Check for shading, dirty panels, loose connections
- **No output**: Check fuses, breakers, charge controller display
- **Battery not charging**: Test charge controller, check battery voltage
- **Inverter alarm**: Check for overload, low battery, overheating""",
            "parts_needed": ["multimeter", "wire brush", "anti-corrosion spray", "distilled water", "replacement fuses"],
            "difficulty": "medium",
            "author": "system",
        },
        {
            "title": "Basic Radio Antenna Construction",
            "category": "radio",
            "content": """# Building a Dipole Antenna

## Overview
A half-wave dipole is the simplest effective antenna for HF communications.

## Formula
Total length (feet) = 468 / frequency (MHz)
Each leg = total length / 2

## Materials
- Copper wire (12-14 AWG stranded)
- Center insulator (or PVC T-fitting)
- End insulators (2)
- Coax cable (RG-8 or RG-213) with PL-259 connector
- Rope for support

## Construction
1. Calculate total length for your target frequency
2. Cut two equal lengths of wire
3. Strip and attach both wires to center insulator
4. Solder coax center conductor to one wire, shield to the other
5. Attach end insulators to each wire end
6. Attach support ropes to end insulators
7. Raise antenna as high as possible, ideally horizontal

## Installation Tips
- Height matters more than perfection
- Keep antenna away from metal objects
- Route coax away from antenna at 90 degrees if possible
- Use a 1:1 balun at feedpoint for best performance
- Seal all connections against weather with self-vulcanizing tape""",
            "parts_needed": ["copper wire 12AWG", "coax cable RG-213", "PL-259 connectors", "insulators", "rope"],
            "difficulty": "medium",
            "author": "system",
        },
        {
            "title": "Emergency Plumbing Repairs",
            "category": "plumbing",
            "content": """# Emergency Plumbing Repair Guide

## Stopping a Leak
1. Shut off water supply immediately
2. Open faucets to drain pressure
3. Identify leak location and type

## Pipe Repair Methods

### Hose Clamp Repair (Temporary)
- Wrap rubber (inner tube) around leak
- Secure with hose clamp or wire
- Works for small cracks in metal or plastic pipe

### Compression Coupling (Permanent)
- Cut out damaged section
- Deburr pipe ends
- Slide compression coupling over joint
- Tighten nuts evenly

### Soldering Copper (Permanent)
- Drain and dry pipe completely
- Clean pipe and fitting with emery cloth
- Apply flux to both surfaces
- Heat joint evenly with torch
- Apply solder - it should flow into the joint
- Allow to cool naturally

## Drain Clearing
1. Try plunger first (seal overflow with wet rag)
2. Use drain snake for stubborn clogs
3. Baking soda + vinegar for minor blockages
4. Never use chemical drain cleaners on septic systems

## Winter Pipe Protection
- Insulate exposed pipes with foam or rags
- Keep faucets dripping in freezing weather
- Know where your main shutoff valve is""",
            "parts_needed": ["pipe wrench", "hose clamps", "rubber sheeting", "compression couplings", "emery cloth", "flux", "solder"],
            "difficulty": "medium",
            "author": "system",
        },
        {
            "title": "Drone Pre-Flight Checklist",
            "category": "drone",
            "content": """# Drone Pre-Flight Checklist

## Before Leaving Base
- [ ] Batteries fully charged (drone + controller + phone)
- [ ] SD card installed and formatted
- [ ] Propellers inspected for damage
- [ ] Spare propellers packed
- [ ] Mission plan reviewed

## At Flight Location
- [ ] Check weather: wind < 15mph, no precipitation
- [ ] Survey area for obstacles (trees, wires, buildings)
- [ ] Identify emergency landing spots
- [ ] Check for restricted airspace
- [ ] Notify nearby community members

## Pre-Flight Hardware Check
- [ ] Propellers securely attached (spin test)
- [ ] Camera/gimbal moves freely
- [ ] Landing gear intact
- [ ] Battery seated properly and latched
- [ ] No visible damage or loose parts
- [ ] Antenna positioned correctly

## Power On Sequence
1. Power on controller first
2. Power on drone
3. Wait for GPS lock (minimum 8 satellites)
4. Verify home point set
5. Check compass calibration
6. Verify camera feed on screen
7. Check battery voltage (should be >90%)

## Post-Flight
- [ ] Power off drone first, then controller
- [ ] Inspect propellers for damage
- [ ] Note any issues in flight log
- [ ] Download and backup footage
- [ ] Charge all batteries for next mission""",
            "parts_needed": ["spare propellers", "SD card", "charging cables", "propeller tool"],
            "difficulty": "easy",
            "author": "system",
        },
    ]

    for guide in guides:
        execute(
            """INSERT INTO technical_guides (title, category, content, parts_needed, difficulty, author)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                guide["title"],
                guide["category"],
                guide["content"],
                json.dumps(guide["parts_needed"]),
                guide["difficulty"],
                guide["author"],
            ),
        )
