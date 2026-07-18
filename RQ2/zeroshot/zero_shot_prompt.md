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

TASK
Extract ALL implicit constraints from this request:
Request ID : {request_id}
"{request_text}"

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