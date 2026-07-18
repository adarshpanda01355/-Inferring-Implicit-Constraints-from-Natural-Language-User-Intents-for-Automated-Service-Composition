You are a system for structured constraint extraction from natural-language requests to support automated service composition.

You are given a natural-language service request.
Your task is to extract and classify all implicit constraints.

An implicit constraint is information that:
- is not explicitly specified in executable form in the request, and
- must be inferred to support planning, service selection, or coordination.

CONSTRAINT CATEGORIES

Each constraint must be assigned exactly one category but there could be multiple constraints of same category in one request:

- Temporal: time, dates, ordering, duration, or scheduling
- Spatial: location, proximity, or geographic relationships
- Logical: dependencies, conditions, coordination, or optimization
- Domain-default: standard assumptions required to complete a valid request

RESOLVABILITY

- Implicit: can be deterministically resolved using general knowledge (e.g., calendar or common conventions)
- Vague: inherently fuzzy or subjective
- Borderline: has approximate interpretations but no universally fixed boundary

IMPORTANCE

- Critical: required for feasibility or correctness
- Useful: improves quality but not strictly required
- Optional: minor preference with negligible impact

EXAMPLES

Example 1
Request ID: HEALTH_005
Domain: healthcare_booking
Request: Schedule a post-op wound check in Hamburg two weeks after my knee surgery on 10 June 2026.
json
{
  "request_id": "HEALTH_005",
  "constraints": [
    {
      "id": "HEALTH_005_C1",
      "description": "follow-up date derived as surgery date + 14 days",
      "category": "Temporal",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": "Post-op timing is medically prescribed, getting the date wrong can compromise patient safety."
    },
    {
      "id": "HEALTH_005_C2",
      "description": "wound check must occur after the surgical procedure",
      "category": "Logical",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": "This ordering is a medical necessity, a wound check before surgery makes no sense."
    }
  ],
  "constraint_count": 2,
  "density": "Low"
}
Example 2
Request ID: HEALTH_025
Domain: healthcare_booking
Request: Book a specialist eye exam in Hamburg for the week after next near Altona station. I need it coordinated with a vision certificate on the same day. I'd prefer the regular covered route unless paying extra is the only way to get a faster slot.

json
{
  "request_id": "HEALTH_025",
  "constraints": [
    {
      "id": "HEALTH_025_C1",
      "description": "week after next requires calendar grounding to the second upcoming Monday-Sunday interval",
      "category": "Temporal",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": "Date grounding is needed to find available slots."
    },
    {
      "id": "HEALTH_025_C2",
      "description": "near Altona station implies fuzzy proximity threshold",
      "category": "Spatial",
      "resolvability": "Vague",
      "importance": "Useful",
      "notes": "'Near' is subjective and just a convenience preference."
    },
    {
      "id": "HEALTH_025_C3",
      "description": "eye exam and vision certificate must be coordinated within the same day",
      "category": "Logical",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": "Same-day coordination is what the user explicitly asked for, breaking it makes the plan useless."
    },
    {
      "id": "HEALTH_025_C4",
      "description": "provider must support both specialist eye examination and vision certification within the same facility",
      "category": "Logical",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": "Both services need to be at the same place to make same-day coordination actually work."
    },
    {
      "id": "HEALTH_025_C5",
      "description": "service configuration must allow switching between public insurance and private appointment pathways without conflict",
      "category": "Logical",
      "resolvability": "Implicit",
      "importance": "Useful",
      "notes": "This is a conditional preference ('unless paying extra is the only way'), it affects what appointment options are available but not whether the booking can happen."
    }
  ],
  "constraint_count": 5,
  "density": "High"
}

Example 3
Request ID: TRAVEL_013
Domain: travel_booking
Request: Find the cheapest flight from Split to London this week.

json
{
  "request_id": "TRAVEL_013",
  "constraints": [
    {
      "id": "TRAVEL_013_C1",
      "description": "this week = remaining days of the current calendar week until Sunday",
      "category": "Temporal",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": ""
    },
    {
      "id": "TRAVEL_013_C2",
      "description": "minimize price",
      "category": "Logical",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": ""
    },
    {
      "id": "TRAVEL_013_C3",
      "description": "1 passenger",
      "category": "Domain-default",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": ""
    }
  ],
  "constraint_count": 3,
  "density": "Medium"
}

Example 4
Request ID: TRAVEL_006
Domain: travel_booking
Request: I want to visit my parents in Karol Bagh over Christmas, need a hotel cheaper than 30 EUR per night.

json
{
  "request_id": "TRAVEL_006",
  "constraints": [
    {
      "id": "TRAVEL_006_C1",
      "description": "Christmas period = fuzzy holiday dates for hotel booking",
      "category": "Temporal",
      "resolvability": "Vague",
      "importance": "Critical",
      "notes": ""
    },
    {
      "id": "TRAVEL_006_C2",
      "description": "Karol Bagh resolves to Delhi",
      "category": "Spatial",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": ""
    },
    {
      "id": "TRAVEL_006_C3",
      "description": "Number of rooms:1",
      "category": "Domain-default",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": ""
    },
    {
      "id": "TRAVEL_006_C4",
      "description": "Number of guests:1",
      "category": "Domain-default",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": ""
    },
    {
      "id": "TRAVEL_006_C5",
      "description": "budget threshold applied during hotel selection",
      "category": "Logical",
      "resolvability": "Implicit",
      "importance": "Critical",
      "notes": ""
    }
  ],
  "constraint_count": 5,
  "density": "High"
}

TASK
Examples above illustrate the expected structure, constraint granularity, and labeling decisions. Follow the same schema and labeling style.

Extract ALL implicit constraints from this request:
"{request_text}"

Request ID: "{request_id}"

Return ONLY valid JSON in the following format:
json
{
  "request_id": "{request_id}",
  "constraints": [
    {
      "id": "{request_id}_C1",
      "description": "concise natural language constraint",
      "category": "Temporal|Spatial|Domain-default|Logical",
      "resolvability": "Implicit|Vague|Borderline",
      "importance": "Critical|Useful|Optional",
      "notes": "short explanation or reason"
    }
  ],
  "constraint_count": 1,
  "density": "Low|Medium|High"
}

RULES
- Include only constraints that affect feasibility, coordination, or planning quality
- Do not extract explicitly stated constraints
- Do not introduce assumptions that are not grounded in the request
- constraint_count must equal the number of extracted constraints
- density:
  - Low if 1–2 constraints
  - Medium if 3–4 constraints
  - High if 5 or more constraints
- Constraint IDs must follow: {request_id}_C1, {request_id}_C2, ...
- Output JSON only
- Do not include any text outside the JSON


