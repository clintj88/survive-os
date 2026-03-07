"""Common livestock conditions and treatment protocols."""

CONDITIONS = [
    {
        "name": "Bloat",
        "species": ["cattle", "sheep", "goat"],
        "symptoms": ["Distended left flank", "Difficulty breathing", "Restlessness", "Reluctance to move"],
        "severity": "high",
    },
    {
        "name": "Mastitis",
        "species": ["cattle", "goat", "sheep"],
        "symptoms": ["Swollen udder", "Abnormal milk (clots, watery, blood-tinged)", "Fever", "Reduced milk production"],
        "severity": "medium",
    },
    {
        "name": "Foot Rot",
        "species": ["cattle", "sheep", "goat"],
        "symptoms": ["Lameness", "Swelling between toes", "Foul odor from foot", "Reluctance to walk"],
        "severity": "medium",
    },
    {
        "name": "Respiratory Infection",
        "species": ["cattle", "sheep", "goat", "poultry", "swine"],
        "symptoms": ["Coughing", "Nasal discharge", "Fever", "Labored breathing", "Reduced appetite"],
        "severity": "high",
    },
    {
        "name": "Internal Parasites",
        "species": ["cattle", "sheep", "goat", "swine", "poultry"],
        "symptoms": ["Weight loss", "Dull coat", "Diarrhea", "Anemia (pale mucous membranes)", "Bottle jaw"],
        "severity": "medium",
    },
]

TREATMENT_PROTOCOLS = [
    {
        "condition": "Bloat",
        "treatments": [
            "Frothy bloat: administer anti-foaming agent (poloxalene or vegetable oil 500ml orally)",
            "Free gas bloat: pass stomach tube to relieve gas",
            "Emergency trocar insertion in left flank if life-threatening",
            "Walk animal gently to encourage gas release",
            "Prevention: gradual diet changes, avoid lush legume pastures",
        ],
    },
    {
        "condition": "Mastitis",
        "treatments": [
            "Strip affected quarter completely 3-4 times daily",
            "Intramammary antibiotic treatment if available",
            "Hot compresses on affected udder",
            "Systemic antibiotics for severe cases (penicillin or oxytetracycline)",
            "Isolate animal, milk last to prevent spread",
            "Prevention: proper milking hygiene, teat dipping",
        ],
    },
    {
        "condition": "Foot Rot",
        "treatments": [
            "Trim affected hoof to remove necrotic tissue",
            "Clean thoroughly with antiseptic solution",
            "Topical treatment: copper sulfate or zinc sulfate foot bath",
            "Systemic antibiotics for severe cases (oxytetracycline)",
            "Keep animal in clean, dry area during recovery",
            "Prevention: regular hoof trimming, foot baths, dry footing",
        ],
    },
    {
        "condition": "Respiratory Infection",
        "treatments": [
            "Isolate affected animals immediately",
            "Antibiotics: oxytetracycline or tulathromycin if available",
            "Anti-inflammatory: flunixin meglumine for fever/pain",
            "Ensure adequate ventilation in housing",
            "Provide fresh water and palatable feed",
            "Prevention: vaccination, avoid overcrowding, reduce stress",
        ],
    },
    {
        "condition": "Internal Parasites",
        "treatments": [
            "Fecal egg count to confirm and identify parasite type",
            "Anthelmintic treatment: ivermectin, fenbendazole, or albendazole",
            "Rotate dewormers to prevent resistance",
            "Pasture rotation to break parasite lifecycle",
            "Prevention: FAMACHA scoring, strategic deworming, clean water",
        ],
    },
]
