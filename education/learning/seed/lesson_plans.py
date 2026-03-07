"""Pre-seed lesson plans for the learning module."""

import json

from app.database import execute


def seed_lessons() -> None:
    lessons = [
        {
            "title": "Basic Literacy - Learning to Read",
            "subject": "literacy",
            "age_group": "children",
            "duration": "45 minutes",
            "objectives": [
                "Recognize and name all 26 letters of the alphabet",
                "Associate basic letter sounds with letters",
                "Read simple three-letter words (CVC pattern)",
            ],
            "materials_needed": [
                "Letter cards (handwritten or printed)",
                "Simple word cards",
                "Paper and pencils",
                "Small whiteboard (optional)",
            ],
            "procedure": [
                "Review letter cards - hold up each letter and have students say the name and sound (10 min)",
                "Introduce 5 new CVC words (cat, dog, sun, big, red) - sound out each letter then blend (10 min)",
                "Practice reading words as a group - point and read together (10 min)",
                "Individual practice - each student reads word cards to a partner (10 min)",
                "Wrap up - review new words and preview next lesson (5 min)",
            ],
            "assessment": "Students can correctly read at least 3 of the 5 new words independently.",
        },
        {
            "title": "Basic Arithmetic - Addition and Subtraction",
            "subject": "math",
            "age_group": "children",
            "duration": "40 minutes",
            "objectives": [
                "Add single-digit numbers up to 10",
                "Subtract single-digit numbers",
                "Use physical objects to demonstrate addition and subtraction",
            ],
            "materials_needed": [
                "Counting objects (stones, beans, sticks)",
                "Number line drawn on paper or board",
                "Practice worksheets",
            ],
            "procedure": [
                "Warm up - count together from 1 to 20 (5 min)",
                "Demonstrate addition with counting objects - show 3 stones + 2 stones = 5 stones (10 min)",
                "Practice addition problems together using number line (10 min)",
                "Introduce subtraction - taking away objects. Show 5 stones - 2 stones = 3 stones (10 min)",
                "Independent practice with worksheets or partner work (5 min)",
            ],
            "assessment": "Students complete 5 addition and 5 subtraction problems with 80% accuracy.",
        },
        {
            "title": "First Aid Fundamentals",
            "subject": "health",
            "age_group": "adult",
            "duration": "90 minutes",
            "objectives": [
                "Assess a scene for safety before providing aid",
                "Perform basic wound care (cleaning, bandaging)",
                "Recognize signs of shock and provide initial treatment",
                "Know when to seek additional medical help",
            ],
            "materials_needed": [
                "First aid kit",
                "Clean bandages and gauze",
                "Clean water for wound irrigation",
                "Blankets for shock treatment",
            ],
            "procedure": [
                "Scene safety overview - always check for dangers before helping (15 min)",
                "Wound care demonstration - cleaning, applying pressure, bandaging (20 min)",
                "Hands-on practice - students bandage each other's arms (simulated) (20 min)",
                "Shock recognition and treatment - signs, positioning, warmth (15 min)",
                "When to get help - red flags and emergency situations (10 min)",
                "Review and Q&A (10 min)",
            ],
            "assessment": "Students demonstrate proper wound cleaning and bandaging technique on a partner.",
        },
        {
            "title": "Introduction to Gardening",
            "subject": "agriculture",
            "age_group": "teen",
            "duration": "60 minutes",
            "objectives": [
                "Understand basic plant needs (sunlight, water, soil, nutrients)",
                "Identify common garden vegetables and their growing seasons",
                "Prepare a simple garden bed",
                "Plant seeds at proper depth and spacing",
            ],
            "materials_needed": [
                "Garden tools (shovel, rake, trowel)",
                "Seeds (beans, lettuce, radishes - fast growers)",
                "Compost or manure",
                "Watering can",
                "String and stakes for rows",
            ],
            "procedure": [
                "Classroom discussion - what do plants need to grow? (10 min)",
                "Walk to garden area - observe existing plants and soil (10 min)",
                "Demonstrate bed preparation - turning soil, adding compost (15 min)",
                "Students prepare their own small section (10 min)",
                "Demonstrate seed planting - depth, spacing, watering (10 min)",
                "Assign garden care responsibilities and schedule (5 min)",
            ],
            "assessment": "Students successfully prepare and plant a small garden section with correct seed depth and spacing.",
        },
        {
            "title": "Water Safety and Purification",
            "subject": "health",
            "age_group": "adult",
            "duration": "75 minutes",
            "objectives": [
                "Identify safe and unsafe water sources",
                "Perform three methods of water purification (boiling, chemical, solar)",
                "Build a basic water filter from available materials",
                "Understand waterborne disease prevention",
            ],
            "materials_needed": [
                "Water samples from different sources",
                "Pot and heat source for boiling",
                "Bleach (unscented, 6-8.25%)",
                "Clear plastic bottles for solar disinfection",
                "Sand, gravel, charcoal for filter",
            ],
            "procedure": [
                "Discussion - why is water safety critical? Common waterborne diseases (15 min)",
                "Demonstrate boiling method - rolling boil for 1 minute minimum (10 min)",
                "Chemical treatment demo - proper bleach ratios (8 drops per gallon) (10 min)",
                "Solar disinfection (SODIS) explanation and bottle preparation (10 min)",
                "Hands-on - build a gravity water filter together (20 min)",
                "Review all methods and when to use each one (10 min)",
            ],
            "assessment": "Students can correctly describe and perform at least two water purification methods.",
        },
    ]

    for lesson in lessons:
        execute(
            """INSERT INTO lesson_plans (title, subject, age_group, duration, objectives, materials_needed, procedure, assessment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lesson["title"],
                lesson["subject"],
                lesson["age_group"],
                lesson["duration"],
                json.dumps(lesson["objectives"]),
                json.dumps(lesson["materials_needed"]),
                json.dumps(lesson["procedure"]),
                lesson["assessment"],
            ),
        )
