# SURVIVE OS Education Module — K-12 Curriculum Architecture

## Purpose

This module provides a complete offline K-12 educational curriculum designed for communities operating without modern infrastructure. Every lesson is self-contained, requires no internet, and can be taught by non-specialist community members using printed materials if needed.

## Design Principles

1. **Survival-first priority**: Core skills (reading, math, science, agriculture, first aid) take precedence over abstract academics
2. **Practical application**: Every subject ties back to real-world survival utility wherever possible
3. **Teachable by non-experts**: Lesson plans include full teacher guides so any literate adult can teach
4. **No technology required**: Lessons work on paper with basic supplies. Digital is a bonus, not a requirement
5. **Culturally neutral**: Content avoids assumptions about specific cultural, religious, or political backgrounds
6. **Spiral curriculum**: Core concepts revisit with increasing depth across grade bands
7. **Assessment built-in**: Each unit includes evaluation criteria and mastery checkpoints
8. **Adaptable pacing**: Communities can adjust pace based on their specific needs and student readiness

## Grade Bands

The curriculum is organized into four developmental bands rather than strict grade levels, allowing flexibility for mixed-age teaching (common in small communities):

| Band | Grades | Ages | Focus |
|------|--------|------|-------|
| Foundation | K-2 | 5-8 | Literacy, numeracy, safety, nature awareness, social skills |
| Building | 3-5 | 8-11 | Applied math, reading comprehension, basic science, community roles |
| Intermediate | 6-8 | 11-14 | Pre-algebra through algebra, life science, earth science, trades introduction |
| Advanced | 9-12 | 14-18 | Advanced math, chemistry, physics, specialized trades, leadership, governance |

## Subject Areas

### Core Subjects (All Bands)
- **Language Arts**: Reading, writing, speaking, listening, storytelling
- **Mathematics**: Arithmetic through calculus, practical measurement, statistics
- **Science**: Biology, chemistry, physics, earth science, ecology
- **Health & Medicine**: First aid, hygiene, nutrition, anatomy, mental health

### Applied Subjects (Building Band and Up)
- **Agriculture & Food Science**: Growing, preserving, animal husbandry, soil science
- **Engineering & Trades**: Woodworking, metalworking, construction, electrical, mechanical
- **Navigation & Geography**: Map reading, compass use, astronomy, local geography
- **Communication & Technology**: Radio operation, signal systems, basic electronics

### History (Thematic — All Bands, Age-Appropriate)
History is taught thematically, NOT as national narratives. See `history-framework/HISTORY-PHILOSOPHY.md` for the full unbiased framework. Nine pillars span all bands:
- **Food & Agriculture**: How humans fed themselves and what happens when food systems fail
- **Governance & Power**: How humans organized and what makes systems endure or collapse
- **Trade & Economics**: How humans exchanged value and the role of trade in peace and conflict
- **Communication & Knowledge**: How knowledge was preserved, shared, and lost
- **Disease & Medicine**: How disease shaped civilization and how humans fought back
- **Engineering & Technology**: How humans built and innovated across cultures
- **Conflict & Peacemaking**: Why humans fight and what actually creates peace
- **Collapse & Resilience**: Why civilizations fall and what distinguishes those that endure
- **Meaning & Culture**: How humans create meaning through art, belief, story, and ritual

### Other Social Subjects (All Bands, Age-Appropriate)
- **Community Living**: Conflict resolution, leadership, cooperation, ethics
- **Arts & Culture**: Music, visual arts, storytelling, drama, cultural preservation

### Specialized Tracks (Advanced Band)
- **Medical Apprenticeship**: Anatomy, pharmacology, patient care, emergency medicine
- **Engineering Apprenticeship**: Structural engineering, water systems, power generation
- **Agricultural Leadership**: Crop science, breeding programs, food system design
- **Security & Defense**: Tactical planning, communication systems, leadership under stress
- **Governance & Law**: Legal frameworks, mediation, community organization, diplomacy
- **Teaching**: Pedagogy, curriculum design, child development (to train the next generation of teachers)

## File Structure

```
education/curriculum/
├── README.md                    # This file
├── TEACHING-GUIDE.md            # How to use this curriculum
├── AGENT-TEAM-TASKS.md          # Agent team build specifications
├── history-framework/           # Thematic history philosophy & reference
│   ├── HISTORY-PHILOSOPHY.md    # Unbiased history framework & principles
│   ├── foundation-history.md    # K-2 thematic history (completed reference)
│   ├── building-history.md      # 3-5 thematic history (completed reference)
│   ├── intermediate-history.md  # 6-8 thematic history (completed reference)
│   └── advanced-history.md      # 9-12 thematic history (completed reference)
├── foundation/                  # Grades K-2
│   ├── language-arts.md
│   ├── mathematics.md
│   ├── science-nature.md
│   ├── health-safety.md
│   ├── history.md               # Based on history-framework/foundation-history.md
│   ├── social-skills.md
│   └── arts-music.md
├── building/                    # Grades 3-5
│   ├── language-arts.md
│   ├── mathematics.md
│   ├── science.md
│   ├── health.md
│   ├── history.md               # Based on history-framework/building-history.md
│   ├── agriculture-intro.md
│   ├── trades-intro.md
│   ├── geography-navigation.md
│   └── arts-culture.md
├── intermediate/                # Grades 6-8
│   ├── language-arts.md
│   ├── mathematics.md
│   ├── life-science.md
│   ├── earth-science.md
│   ├── health-first-aid.md
│   ├── history.md               # Based on history-framework/intermediate-history.md
│   ├── economics-trade.md
│   ├── agriculture.md
│   ├── engineering-trades.md
│   ├── communication-tech.md
│   └── arts.md
├── advanced/                    # Grades 9-12
│   ├── language-arts.md
│   ├── mathematics.md
│   ├── biology.md
│   ├── chemistry.md
│   ├── physics.md
│   ├── history.md               # Based on history-framework/advanced-history.md
│   ├── advanced-medicine.md
│   ├── agriculture-science.md
│   ├── engineering.md
│   ├── economics.md
│   ├── communication-systems.md
│   ├── leadership.md
│   └── teaching-pedagogy.md
├── apprenticeships/             # Specialized tracks
│   ├── medical.md
│   ├── engineering.md
│   ├── agricultural.md
│   ├── security.md
│   ├── governance.md
│   └── teaching.md
├── assessments/                 # Evaluation frameworks
│   ├── mastery-criteria.md
│   ├── practical-exams.md
│   └── portfolio-guidelines.md
└── resources/
    ├── supply-list.md           # Physical supplies needed
    ├── book-recommendations.md  # Books to salvage/preserve
    └── printable-templates.md   # Worksheets, charts, reference cards
```

## Unit Structure Standard

Every subject file follows this structure for each unit:

```markdown
## Unit [Number]: [Title]

**Duration**: [X weeks]
**Prerequisites**: [Previous units or skills needed]
**Materials**: [Physical supplies required]
**Survival Relevance**: [Why this matters for survival]

### Learning Objectives
- Students will be able to...

### Teacher Notes
[Background knowledge the teacher needs, common misconceptions, tips]

### Lessons
#### Lesson 1: [Title]
- **Activity**: [Description]
- **Key Concepts**: [List]
- **Practice**: [Exercises]

### Assessment
- **Mastery Check**: [How to verify understanding]
- **Practical Application**: [Real-world task to demonstrate skill]
```

## Integration Points

The curriculum integrates with other SURVIVE OS modules:
- **Knowledge Base**: Cross-references survival knowledge entries
- **Agriculture Module**: Real field data used in math and science lessons
- **Weather Module**: Live weather data for earth science lessons
- **Medical Module**: Health curriculum aligned with community medical protocols
- **Maps Module**: Geography lessons use community maps
- **Governance Module**: Civics lessons connect to actual community governance structures
