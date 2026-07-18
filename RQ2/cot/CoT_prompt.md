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
Request ID: {request_id}
"{request_text}"

Apply the following internal reasoning process:
INTERNAL REASONING STEPS (do not include in final output)
1. Scan the request and identify all elements that are not directly specified in executable form and may require inference, grounding, or interpretation.
2. From these, filter only those elements that affect planning, feasibility, service selection, or coordination.
3. Decompose each selected element into a distinct constraint, ensuring that each constraint represents a single atomic requirement and ensuring that constraints are not merged or overly split.
4. For each constraint:
   - assign the appropriate category (Temporal, Spatial, Logical, Domain-default)
   - determine its resolvability (Implicit, Vague, Borderline)
   - determine its importance (Critical, Useful, Optional)
5. Review the constraints to ensure:
   - no explicitly stated constraints are included
   - no unsupported assumptions are introduced
   - constraint count and density are consistent
6. Perform a final completeness and consistency check to ensure:
   - no relevant implicit constraints were missed
   - constraints are not duplicated or overlapping
   - the set of constraints fully captures the planning requirements of the request


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