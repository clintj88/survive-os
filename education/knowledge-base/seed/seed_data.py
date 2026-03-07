#!/usr/bin/env python3
"""Seed the knowledge base with initial survival content."""

import sys
from pathlib import Path

# Allow running as script from the knowledge-base directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import execute, init_db, query, set_db_path
from app.config import load_config

CATEGORIES = [
    ("First Aid", "first-aid", "Emergency medical treatment and basic care"),
    ("Water Purification", "water-purification", "Methods to make water safe for drinking"),
    ("Shelter Building", "shelter-building", "Constructing and maintaining shelters"),
    ("Food Preservation", "food-preservation", "Techniques to store and preserve food safely"),
    ("Navigation", "navigation", "Finding your way without modern technology"),
    ("Radio Communications", "radio-comms", "Setting up and using radio equipment"),
]

ARTICLES = [
    # First Aid
    {
        "title": "Treating Wounds and Stopping Bleeding",
        "slug": "treating-wounds-stopping-bleeding",
        "category": "first-aid",
        "summary": "Essential techniques for wound care and hemorrhage control.",
        "content": """# Treating Wounds and Stopping Bleeding

## Direct Pressure

The most important first step for any bleeding wound is **direct pressure**.

1. Place a clean cloth or bandage directly over the wound
2. Apply firm, steady pressure with your palm
3. Do NOT remove the cloth if it soaks through -- add more layers on top
4. Maintain pressure for at least 15 minutes without checking

## Wound Cleaning

Once bleeding is controlled:

1. Wash your hands thoroughly or use gloves
2. Rinse the wound with clean water (boiled and cooled if possible)
3. Remove any visible debris with clean tweezers
4. Do NOT use alcohol or hydrogen peroxide directly in deep wounds -- they damage tissue
5. Apply a thin layer of antibiotic ointment if available
6. Cover with a sterile bandage

## Tourniquet Use (Life-Threatening Limb Bleeding Only)

Only use a tourniquet when direct pressure fails on a limb wound:

1. Place the tourniquet 2-3 inches above the wound (never on a joint)
2. Tighten until bleeding stops
3. Note the time of application
4. Do NOT loosen once applied
5. Seek advanced medical care immediately

## Signs of Infection

Watch for these signs in the days following injury:

- Increasing redness spreading from the wound
- Swelling or warmth around the wound
- Pus or cloudy drainage
- Fever
- Red streaks leading away from the wound

If infection signs appear, clean the wound again and seek medical help if available.
""",
    },
    {
        "title": "CPR and Basic Life Support",
        "slug": "cpr-basic-life-support",
        "category": "first-aid",
        "summary": "How to perform CPR on adults, children, and infants.",
        "content": """# CPR and Basic Life Support

## When to Perform CPR

Perform CPR when a person is:
- Unresponsive (does not react when you tap their shoulders and shout)
- Not breathing normally (no breath, or only gasping)

## Adult CPR Steps

1. **Call for help** -- send someone to get medical assistance
2. Place the person on their back on a firm surface
3. Place the heel of one hand on the center of the chest (between the nipples)
4. Place your other hand on top, interlace fingers
5. Push hard and fast:
   - Depth: at least 2 inches (5 cm)
   - Rate: 100-120 compressions per minute
   - Allow full chest recoil between compressions
6. After 30 compressions, give 2 rescue breaths:
   - Tilt the head back, lift the chin
   - Pinch the nose, seal your mouth over theirs
   - Blow for about 1 second, watch for chest rise
7. Continue the cycle of 30:2 until help arrives or the person recovers

## Recovery Position

If the person is breathing but unconscious:

1. Kneel beside them
2. Place their far arm across their chest
3. Bend their far knee
4. Roll them toward you onto their side
5. Tilt their head back to keep the airway open
6. Monitor breathing continuously
""",
    },
    {
        "title": "Treating Burns",
        "slug": "treating-burns",
        "category": "first-aid",
        "summary": "First aid treatment for thermal, chemical, and electrical burns.",
        "content": """# Treating Burns

## Burn Classification

- **First-degree**: Red skin, pain, no blisters (like sunburn)
- **Second-degree**: Blisters, severe pain, red/splotchy skin
- **Third-degree**: White or charred skin, may be painless due to nerve damage

## Immediate Treatment

1. **Remove from the source** -- ensure safety first
2. **Cool the burn** with cool (not cold) running water for 10-20 minutes
3. Do NOT use ice, butter, toothpaste, or other home remedies
4. Remove jewelry or tight clothing near the burn before swelling starts
5. Do NOT pop blisters -- they protect against infection

## Covering the Burn

1. Once cooled, cover loosely with a clean, non-stick bandage
2. Use clean plastic wrap as an alternative covering
3. Change dressings daily
4. Watch for signs of infection (increased pain, redness, swelling, fever)

## When Burns Are Serious

Seek advanced care for:
- Burns larger than 3 inches across
- Burns on face, hands, feet, joints, or groin
- Third-degree burns of any size
- Electrical or chemical burns
- Burns in children or elderly
- Burns that wrap around a limb
""",
    },
    # Water Purification
    {
        "title": "Boiling Water for Safe Drinking",
        "slug": "boiling-water-safe-drinking",
        "category": "water-purification",
        "summary": "The most reliable method to purify water using heat.",
        "content": """# Boiling Water for Safe Drinking

## Why Boiling Works

Boiling is the most reliable way to kill bacteria, viruses, and parasites. At a rolling boil (100C / 212F at sea level), all common waterborne pathogens are destroyed.

## Procedure

1. **Collect water** from the cleanest source available
2. **Pre-filter** through a clean cloth or coffee filter to remove sediment
3. Bring water to a **rolling boil** (large, vigorous bubbles)
4. Maintain the boil for **1 minute** (3 minutes above 2000m / 6500ft elevation)
5. Remove from heat and let cool naturally
6. Store in clean, covered containers

## Important Notes

- Boiling does NOT remove chemical contaminants (heavy metals, pesticides)
- Cloudy water should always be pre-filtered
- At higher altitudes, water boils at a lower temperature -- boil longer
- Let water cool before drinking to avoid burns
- Boiled water tastes flat; pour between two clean containers to add air

## Fuel Conservation

- Use a lid on the pot to reach boiling faster
- Only boil what you need for the next 24 hours
- Consider solar pasteurization on sunny days (see Solar Disinfection article)
""",
    },
    {
        "title": "Solar Water Disinfection (SODIS)",
        "slug": "solar-water-disinfection-sodis",
        "category": "water-purification",
        "summary": "Using sunlight and plastic bottles to purify water when fuel is scarce.",
        "content": """# Solar Water Disinfection (SODIS)

## How It Works

UV-A radiation and heat from sunlight destroy pathogens in water. This method is recommended by the WHO for household water treatment.

## Materials Needed

- Clear PET plastic bottles (1-2 liter soda bottles work well)
- Sunlight

## Steps

1. **Select bottles**: Use clear, unscratched PET plastic bottles. Remove labels.
2. **Filter water**: Pre-filter through cloth if cloudy
3. **Check turbidity**: Fill a bottle and hold it over newspaper. If you cannot read the text through the water, it is too cloudy -- filter again or use a different method.
4. **Fill bottles**: Fill 3/4 full, shake for 20 seconds to oxygenate, then fill completely
5. **Place in sun**: Lay bottles horizontally on a dark or reflective surface (corrugated metal roofing works well)
6. **Exposure time**:
   - Sunny or partly cloudy: **6 hours minimum**
   - Overcast: **2 full days**
   - Heavy rain/very overcast: Use a different method
7. **Store** treated water in the bottles until ready to drink

## Limitations

- Does NOT work with glass bottles (glass blocks UV-A)
- Ineffective for chemically contaminated water
- Bottles degrade over time -- replace every 6 months
- Water temperature above 50C (122F) greatly improves effectiveness
""",
    },
    # Shelter Building
    {
        "title": "Emergency Debris Shelter",
        "slug": "emergency-debris-shelter",
        "category": "shelter-building",
        "summary": "Build a quick survival shelter from natural materials.",
        "content": """# Emergency Debris Shelter

## When to Build

Build a debris shelter when you need protection from wind, rain, or cold and have no tent or tarp. This shelter can be built in 1-2 hours with no tools.

## Lean-To Debris Shelter

### Materials Needed
- 1 long ridgepole (2-3 meters, sturdy)
- Support branches (as many as available)
- Leaves, pine needles, grass, or other forest debris

### Construction

1. **Find or create a support**: Prop the ridgepole at roughly 45 degrees against a tree, rock, or forked sticks
2. **Add ribs**: Lean branches along both sides of the ridgepole at 45 degrees, spacing them 15-20cm apart
3. **Add cross-members**: Weave smaller sticks horizontally through the ribs to create a lattice
4. **Pile debris**: Cover the entire structure with at least 60cm (2 feet) of leaves, pine needles, or grass
5. **Create a bed**: Fill the floor with 30cm of dry debris for insulation from ground cold
6. **Block the entrance**: Use a backpack or pile of debris to reduce the opening

### Key Principles

- **Smaller is warmer**: Build just big enough to fit inside
- **Insulation matters more than waterproofing**: Thick debris sheds rain naturally
- **Ground insulation is critical**: You lose more heat to the ground than to the air
- Build with the entrance away from prevailing wind
- Test by crawling inside before nightfall
""",
    },
    {
        "title": "Tarp Shelter Configurations",
        "slug": "tarp-shelter-configurations",
        "category": "shelter-building",
        "summary": "Multiple shelter designs using a basic tarp and cordage.",
        "content": """# Tarp Shelter Configurations

A tarp is one of the most versatile shelter tools. These configurations work with any rectangular tarp (3x3m or larger recommended).

## A-Frame

Best for: Rain protection, general use

1. Tie a ridgeline between two trees at chest height
2. Drape the tarp over the ridgeline evenly
3. Stake out the four corners at 45-degree angles
4. Adjust tension to eliminate sag

## Lean-To

Best for: Wind protection from one direction, heat reflection from a fire

1. Tie the tarp's top edge to a ridgeline at chest height
2. Stake the bottom edge to the ground, angled away from wind
3. Place a fire in front of the open side for warmth (at safe distance)

## Diamond Fly

Best for: Rain in variable wind conditions

1. Tie one corner to a tree at head height
2. Stake the opposite corner to the ground
3. Stake or prop the two side corners out for width

## Ground Rules for All Tarp Shelters

- **Angle matters**: Steeper pitch sheds rain better but reduces living space
- **Tension is everything**: A taut tarp is quiet, sheds water, and resists wind
- Always consider drainage -- never set up in a low spot
- Orient the lowest side toward prevailing wind
- Use truckers hitch or taut-line hitch for adjustable tension
""",
    },
    # Food Preservation
    {
        "title": "Salt Curing and Drying Meat",
        "slug": "salt-curing-drying-meat",
        "category": "food-preservation",
        "summary": "Traditional methods for preserving meat without refrigeration.",
        "content": """# Salt Curing and Drying Meat

## Why Salt Curing Works

Salt draws moisture out of meat through osmosis, creating an environment where bacteria cannot thrive. Properly salt-cured meat can last months without refrigeration.

## Basic Dry Cure

### Materials
- Fresh meat (cut into strips no thicker than 5mm / 1/4 inch)
- Salt (non-iodized preferred, but any salt works in an emergency)

### Process

1. **Prepare the meat**: Remove all fat (fat goes rancid). Cut into thin, uniform strips along the grain.
2. **Apply salt**: Rub generous amounts of salt into every surface. Use roughly 1 part salt to 5 parts meat by weight.
3. **Stack and press**: Layer salted meat in a clean container. Place a weight on top.
4. **Wait**: Refrigerate or keep in the coolest place available for 24-48 hours.
5. **Rinse and dry**: Briefly rinse off excess salt. Pat dry.
6. **Air dry**: Hang strips in a well-ventilated area with good airflow. Protect from flies with cheesecloth or mesh.
7. **Drying time**: 3-7 days depending on humidity and thickness. Meat is done when it cracks but does not break when bent.

## Solar Drying (Jerky)

If salt is scarce:

1. Cut meat into very thin strips (3mm)
2. Place on clean racks in direct sunlight
3. Cover with mesh to keep flies off
4. Bring inside at night to avoid dew moisture
5. Dry for 2-3 sunny days until brittle

## Storage

- Store in airtight containers in a cool, dark place
- Properly dried meat lasts 1-2 months at room temperature
- Salt-cured AND dried meat can last 3-6 months
""",
    },
    {
        "title": "Fermentation and Pickling Basics",
        "slug": "fermentation-pickling-basics",
        "category": "food-preservation",
        "summary": "Preserving vegetables through lacto-fermentation and vinegar pickling.",
        "content": """# Fermentation and Pickling Basics

## Lacto-Fermentation

Lacto-fermentation uses naturally present Lactobacillus bacteria to preserve food. It requires only salt and vegetables.

### Basic Sauerkraut Method

1. **Shred cabbage** finely (or any firm vegetable)
2. **Add salt**: 2% by weight (20g salt per 1kg vegetables)
3. **Massage**: Squeeze and knead for 5-10 minutes until liquid is released
4. **Pack tightly** into a clean jar, pressing down so liquid covers the vegetables
5. **Weight down**: Keep vegetables submerged below the brine (a zip-lock bag filled with brine works well)
6. **Cover**: Use a cloth secured with a rubber band (not an airtight lid -- gas must escape)
7. **Wait**: Ferment at room temperature (18-22C) for 1-4 weeks
8. **Taste test**: Flavor develops over time. Move to cool storage when you like the taste.

### Signs of Healthy Fermentation
- Bubbling during the first few days
- Sour smell (like vinegar, not rotten)
- Cloudy brine is normal

### Signs of Failure (Discard If)
- Fuzzy mold on the surface (white film/kahm yeast is OK -- just remove it)
- Foul or rotten smell
- Slimy texture
- Pink or black discoloration

## Vinegar Pickling

If you have vinegar (at least 5% acidity):

1. Prepare vegetables (slice cucumbers, peppers, onions, etc.)
2. Make brine: equal parts vinegar and water, plus 1 tbsp salt per liter
3. Bring brine to a boil
4. Pack vegetables into clean jars
5. Pour hot brine over vegetables, covering completely
6. Seal tightly while hot
7. Store in cool, dark place -- lasts 6-12 months
""",
    },
    # Navigation
    {
        "title": "Navigation by Sun and Stars",
        "slug": "navigation-sun-and-stars",
        "category": "navigation",
        "summary": "Finding direction without a compass using celestial navigation.",
        "content": """# Navigation by Sun and Stars

## Finding North Using the Sun

### Shadow Stick Method

1. Place a straight stick (1m) vertically in the ground on level terrain
2. Mark the tip of the shadow with a stone
3. Wait 15-30 minutes
4. Mark the new shadow tip position
5. Draw a line between the two marks -- this line runs roughly **east-west**
6. The first mark is west, the second is east (shadows move from west to east)
7. Stand with west on your left, east on your right -- you are facing north

### Watch Method (Northern Hemisphere)

1. Hold an analog watch flat
2. Point the hour hand at the sun
3. The midpoint between the hour hand and 12 o'clock points roughly south
4. The opposite direction is north

## Finding North Using Stars

### Northern Hemisphere -- Polaris (North Star)

1. Find the Big Dipper (Ursa Major)
2. Locate the two "pointer stars" forming the outer edge of the cup
3. Extend an imaginary line through these two stars about 5 times their distance
4. This line points to Polaris, which marks true north
5. Polaris's height above the horizon equals your latitude

### Southern Hemisphere -- Southern Cross

1. Find the Southern Cross (Crux)
2. Extend the long axis of the cross 4.5 times its length downward
3. This imaginary point is roughly the south celestial pole
4. Drop a vertical line from that point to the horizon -- that direction is south

## Estimating Time of Day

- Fist widths between the sun and the horizon estimate time until sunset
- Each fist width at arm's length is approximately 15 minutes (1 hour per 4 fists)
""",
    },
    {
        "title": "Map Reading and Dead Reckoning",
        "slug": "map-reading-dead-reckoning",
        "category": "navigation",
        "summary": "Using paper maps and basic techniques to navigate without GPS.",
        "content": """# Map Reading and Dead Reckoning

## Map Basics

### Orienting a Map

1. Place the map on a flat surface
2. If you have a compass, align the map's north arrow with magnetic north (account for declination)
3. Without a compass, use the sun/shadow method to find north and rotate the map to match

### Reading Contour Lines

- **Close together**: Steep terrain
- **Far apart**: Gentle slopes or flat ground
- **V-shapes pointing uphill**: Valleys and drainages
- **V-shapes pointing downhill**: Ridges and spurs
- **Concentric circles**: Hilltops

### Scale

Common scales and what they mean:
- 1:25,000 -- 1cm on map = 250m on ground (detailed hiking maps)
- 1:50,000 -- 1cm on map = 500m on ground (standard topographic)
- 1:100,000 -- 1cm on map = 1km on ground (regional)

## Dead Reckoning

Navigate without visible landmarks using direction and distance:

1. **Determine your starting point** on the map
2. **Set a bearing** to your destination (use compass or celestial methods)
3. **Estimate distance** as you walk:
   - Average walking pace: count steps for 100m on flat ground to calibrate
   - Typical: 60-70 double-paces per 100m on flat ground
   - Add 10-20% for rough terrain
4. **Track your progress** on the map as you move
5. **Use handrails**: Follow linear features (rivers, ridges, roads) when they align with your route
6. **Use catching features**: Identify large features you cannot miss that tell you you have gone too far

## Common Errors

- Not accounting for magnetic declination
- Underestimating distance in rough terrain
- Forgetting to adjust pace count for uphill/downhill
""",
    },
    # Radio Communications
    {
        "title": "Basic Radio Operation and Protocols",
        "slug": "basic-radio-operation-protocols",
        "category": "radio-comms",
        "summary": "How to use two-way radios effectively for community communication.",
        "content": """# Basic Radio Operation and Protocols

## Radio Types

- **FRS/GMRS (UHF)**: Short range (1-5 km), good for local community use
- **CB Radio (27 MHz)**: Medium range (5-15 km), no license needed
- **Amateur/Ham (HF/VHF/UHF)**: Long range (regional to worldwide), requires knowledge

## Basic Operating Procedures

### Making a Call

1. Listen before transmitting -- make sure the channel is clear
2. Press and hold the PTT (Push-To-Talk) button
3. Wait 1 second before speaking (the radio needs time to activate)
4. Speak clearly and at normal volume
5. Release PTT when done speaking

### Standard Format

> "[Called station] this is [your station], over."

- **"Over"**: I am done speaking, expecting a reply
- **"Out"**: Conversation is finished (never say "over and out")
- **"Roger"**: Message received and understood
- **"Say again"**: Please repeat your last message
- **"Break break"**: Emergency interruption on a busy channel

## Channel Discipline

- Designate a **primary channel** for your community
- Keep a **secondary channel** for overflow
- Reserve one channel for **emergencies only**
- Keep transmissions brief -- others may need the channel
- Identify yourself at the start and end of each session

## Extending Range

- Height is everything: elevate your position or antenna
- External antennas dramatically improve range
- Avoid transmitting near large metal structures
- A repeater on a hilltop can extend UHF range to 50+ km
- Schedule regular check-in times to conserve battery
""",
    },
    {
        "title": "Setting Up a Community Radio Network",
        "slug": "community-radio-network",
        "category": "radio-comms",
        "summary": "Planning and deploying radio communications for a community.",
        "content": """# Setting Up a Community Radio Network

## Planning Your Network

### Assess Needs

1. **Coverage area**: How far apart are community members?
2. **Terrain**: Mountains, forests, and buildings block radio signals
3. **Number of users**: Determines how many channels you need
4. **Use cases**: Daily check-ins, security alerts, supply coordination

### Choose Equipment

For most communities, a tiered approach works best:

- **Tier 1 (Local)**: FRS/PMR446 handheld radios for neighborhood use (1-3 km)
- **Tier 2 (Community)**: GMRS or VHF radios with external antennas (5-15 km)
- **Tier 3 (Regional)**: HF radio for long-distance communication (100+ km)

## Repeater Setup

A repeater receives signals and retransmits them at higher power from an elevated position.

1. **Location**: Highest accessible point (hilltop, tall building, tower)
2. **Power**: Solar panel (50-100W) + deep-cycle battery
3. **Equipment**: Commercial repeater or two radios with a controller
4. **Antenna**: Omnidirectional antenna mounted as high as possible
5. **Maintenance**: Assign someone to check the repeater weekly

## Communication Schedule

Establish regular schedules to conserve power:

- **Morning net** (0800): All stations check in, report status
- **Evening net** (1800): Activity summary, next day planning
- **Emergency channel**: Monitored 24/7, emergencies only
- **Supply net** (weekly): Resource coordination between groups

## Message Handling

For important messages, use a log:

| Field | Example |
|-------|---------|
| Date/Time | 2026-03-07 0815 |
| From | Station Alpha |
| To | Station Bravo |
| Priority | Routine / Urgent / Emergency |
| Message | Supply run to sector 4 complete |
| Acknowledged | Yes, 0817 |
""",
    },
]


def seed() -> None:
    """Run the database seed."""
    config = load_config()
    set_db_path(config["database"]["path"])
    init_db()

    # Check if already seeded
    existing = query("SELECT COUNT(*) as cnt FROM categories")
    if existing and existing[0]["cnt"] > 0:
        print("Database already seeded. Skipping.")
        return

    # Insert categories
    for name, slug, description in CATEGORIES:
        execute(
            "INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)",
            (name, slug, description),
        )

    # Build slug->id map
    cats = query("SELECT id, slug FROM categories")
    cat_map = {c["slug"]: c["id"] for c in cats}

    # Insert articles
    for article in ARTICLES:
        category_id = cat_map[article["category"]]
        execute(
            """INSERT INTO articles (title, slug, category_id, content, summary)
               VALUES (?, ?, ?, ?, ?)""",
            (article["title"], article["slug"], category_id, article["content"], article["summary"]),
        )

    print(f"Seeded {len(CATEGORIES)} categories and {len(ARTICLES)} articles.")


if __name__ == "__main__":
    seed()
