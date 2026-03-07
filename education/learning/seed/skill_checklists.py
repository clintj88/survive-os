"""Pre-seed skill checklists and children's content for the learning module."""

import json

from app.database import execute


def seed_checklists() -> None:
    trades = {
        "farming": [
            "Soil preparation and testing",
            "Seed selection and storage",
            "Planting techniques",
            "Irrigation systems",
            "Pest and disease management",
            "Harvesting methods",
            "Food preservation basics",
            "Crop rotation planning",
        ],
        "medical": [
            "Patient assessment",
            "Wound care and suturing",
            "Vital signs measurement",
            "CPR and basic life support",
            "Splinting and immobilization",
            "Medication administration",
            "Infection control",
            "Triage procedures",
        ],
        "mechanical": [
            "Hand tool proficiency",
            "Basic welding techniques",
            "Small engine repair",
            "Electrical systems basics",
            "Plumbing repair",
            "Structural repair",
        ],
        "teaching": [
            "Lesson planning",
            "Classroom management",
            "Assessment design",
            "Differentiated instruction",
            "Mentoring and coaching",
        ],
    }

    for trade, skills in trades.items():
        for i, skill in enumerate(skills):
            execute(
                "INSERT INTO skill_checklists (trade, skill_name, sort_order) VALUES (?, ?, ?)",
                (trade, skill, i),
            )

    # Seed reading passages
    passages = [
        {
            "title": "The Garden",
            "difficulty": 1,
            "passage": "Sam has a garden. The garden has tomatoes and beans. Sam waters the garden every day. The plants grow tall in the sun. Sam picks the tomatoes when they are red.",
            "questions": [
                {"question": "What does Sam have?", "options": ["A garden", "A dog", "A car"], "answer": "A garden"},
                {"question": "What color are ripe tomatoes?", "options": ["Green", "Red", "Blue"], "answer": "Red"},
            ],
        },
        {
            "title": "Clean Water",
            "difficulty": 2,
            "passage": "Water is important for life. We need clean water to drink, cook, and wash. Dirty water can make people sick. There are ways to make water clean. You can boil water to kill germs. You can also filter water through sand and charcoal. Clean water keeps our community healthy.",
            "questions": [
                {"question": "Why is clean water important?", "options": ["For swimming", "For drinking, cooking, and washing", "For painting"], "answer": "For drinking, cooking, and washing"},
                {"question": "What can dirty water do?", "options": ["Make people strong", "Make people sick", "Make plants grow"], "answer": "Make people sick"},
                {"question": "Name one way to clean water.", "options": ["Freeze it", "Boil it", "Color it"], "answer": "Boil it"},
            ],
        },
        {
            "title": "The Solar Panel",
            "difficulty": 3,
            "passage": "Solar panels turn sunlight into electricity. They are made of special materials called semiconductors. When sunlight hits a solar panel, it knocks electrons loose from their atoms. This creates a flow of electricity. Solar panels work best when they face the sun directly. They produce less power on cloudy days, but they still work. Many communities use solar panels because they don't need fuel and they don't pollute the air.",
            "questions": [
                {"question": "What do solar panels turn into electricity?", "options": ["Wind", "Sunlight", "Water"], "answer": "Sunlight"},
                {"question": "What are solar panels made of?", "options": ["Wood", "Semiconductors", "Paper"], "answer": "Semiconductors"},
                {"question": "Do solar panels work on cloudy days?", "options": ["No, never", "Yes, but less", "Only at night"], "answer": "Yes, but less"},
            ],
        },
    ]

    for p in passages:
        execute(
            "INSERT INTO reading_passages (title, difficulty, passage, questions) VALUES (?, ?, ?, ?)",
            (p["title"], p["difficulty"], p["passage"], json.dumps(p["questions"])),
        )

    # Seed science activities
    activities = [
        {
            "title": "Growing Beans in a Jar",
            "difficulty": 1,
            "description": "Watch a bean seed sprout and grow by placing it in a jar with wet paper towels.",
            "materials": ["Glass jar", "Paper towels", "Bean seeds", "Water"],
            "steps": [
                "Wet paper towels and line the inside of the jar.",
                "Place 2-3 bean seeds between the towel and the glass.",
                "Add a small amount of water to the bottom of the jar.",
                "Place in a sunny window.",
                "Observe and draw what you see each day for 2 weeks.",
                "Keep the paper towel moist but not soaked.",
            ],
        },
        {
            "title": "Make a Water Filter",
            "difficulty": 2,
            "description": "Build a simple water filter using sand, gravel, and charcoal to learn about water purification.",
            "materials": ["Plastic bottle (cut in half)", "Cotton balls", "Sand", "Gravel", "Charcoal (crushed)", "Dirty water"],
            "steps": [
                "Cut a plastic bottle in half. Use the top half upside down as a funnel.",
                "Place cotton balls at the neck of the bottle.",
                "Add a layer of crushed charcoal (2 inches).",
                "Add a layer of sand (2 inches).",
                "Add a layer of gravel (2 inches).",
                "Pour dirty water through the top and collect filtered water below.",
                "Compare the filtered water to the original dirty water.",
                "Note: This filter does NOT make water safe to drink without further treatment!",
            ],
        },
        {
            "title": "Build a Simple Compass",
            "difficulty": 3,
            "description": "Create a working compass using a needle, magnet, and water to learn about Earth's magnetic field.",
            "materials": ["Sewing needle", "Small magnet", "Cork or foam piece", "Bowl of water"],
            "steps": [
                "Rub the needle with the magnet in ONE direction only, 50 times.",
                "Carefully push the needle through a small piece of cork or foam.",
                "Float the cork in a bowl of still water.",
                "Watch the needle slowly turn to point north-south.",
                "Compare with a real compass if available.",
                "Try moving a magnet near it and observe what happens.",
            ],
        },
    ]

    for a in activities:
        execute(
            "INSERT INTO science_activities (title, difficulty, description, materials, steps) VALUES (?, ?, ?, ?, ?)",
            (a["title"], a["difficulty"], a["description"], json.dumps(a["materials"]), json.dumps(a["steps"])),
        )
