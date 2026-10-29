# AI Usage Report (AI_USAGE.md)

This document transparently documents the utilization of AI tools during the conception, design, implementation, and verification of the **AI-Assisted Box Selection System**.

---

## 1. Which AI Tool(s) You Used
- **Google Antigravity Agent (Pair Programming Assistant powered by Gemini 3.8 Flash / Thinking Model)**:
  - Used for rapid architectural ideation, boilerplate generation, Django ORM schema scaffolding, and drafting 3D geometric placement algorithms.
- **Python Documentation & Built-in Tooling**:
  - Used for standard library reference (`dataclasses`, `decimal`, `typing`).

---

## 2. The Prompts You Gave

Key prompt categories given during the development lifecycle:

1. **System Design & Requirements Structuring**:
   > *"We operate an ecommerce platform. Design a Django-based system that recommends the most suitable shipping box for customer orders given product dimensions/weights and box internal dimensions/weights/costs. Must enforce 3D geometric fit, weight limits, and minimize costs."*

2. **3D Packing & Coordinate Placement Algorithm**:
   > *"How can we implement a pure-Python, deterministic 3D bin packing algorithm that tests item rotation (6 degrees of freedom) without relying on fragile external C/C++ libraries? We need exact non-overlapping coordinate placement and bounding box collision checks."*

3. **Domain Modeling & REST API**:
   > *"Generate Django models for Box, Product, Order, OrderItem, and BoxRecommendationHistory. Create a Django REST Framework endpoint at `POST /api/recommend/` that accepts either an existing `order_id` or an ad-hoc list of items."*

4. **AI Packaging Guidance & Warehouse Instructions**:
   > *"Design an AI packaging assistant layer that calculates void-fill percentage, identifies fragile items, evaluates weight distribution (placing heavy items on the bottom), and generates actionable packing notes for warehouse dispatchers."*

5. **Edge Case Test Suite Generation**:
   > *"Write a comprehensive Django test suite covering single-item fit, 3D rotation fit, rotation restriction (liquids/upright items), weight limit disqualification, cost minimization, and multi-box fallback."*

---

## 3. What Output You Accepted

The following outputs and recommendations from the AI were accepted:
- **Anchor-Point 3D Placement Heuristic**: The First-Fit Decreasing algorithm with coordinate pivot generation `(x + dx, y, z)`, `(x, y + dy, z)`, `(x, y, z + dz)` and 3D cuboid intersection math.
- **Django Project Layout**: Separation into a clean Django application (`box_selection`) with dedicated service packages (`packer.py`, `recommender.py`, `ai_assistant.py`).
- **Bootstrap 5 Interactive Web Interface**: Dual-mode simulator supporting both database-backed orders and custom dimension/weight ad-hoc testing.
- **Hierarchical Candidate Sorting**: Ranking boxes strictly by cost ascending first, with volume waste as the secondary tie-breaker.

---

## 4. What Output You Rejected or Modified

1. **Rejected Naive Volume-Only Fit Calculation**:
   - *AI Initial Suggestion*: Initially, simpler AI snippets suggested checking if $\sum V_{\text{items}} \le V_{\text{box}}$ and $\text{weight} \le \text{max\_weight}$.
   - *Reason for Rejection*: In physical logistics, volume alone is notoriously insufficient (e.g., an elongated keyboard cannot fit into a cube of equal volume).
   - *Modification*: Replaced with a two-phase check: bounding box feasibility pre-filter + true 3D coordinate placement with non-overlap verification.

2. **Modified Rigid External LLM Calls**:
   - *AI Initial Suggestion*: Making a direct synchronous HTTP call to an external LLM API (such as OpenAI or Gemini) inside the core recommendation loop.
   - *Reason for Rejection*: Relying on an external cloud API makes automated test runs brittle, introduces network latency into warehouse dispatch loops, and causes failures when running offline or without active API keys.
   - *Modification*: Architected `AIPackingAssistant` with a deterministic, rule-based warehouse intelligence engine as the primary core, with optional LLM API enrichment if API credentials are present.

3. **Modified Item Rotation Permission**:
   - *AI Initial Suggestion*: Allowing unrestricted 6-DOF rotation for all items.
   - *Reason for Rejection*: Real-world items like liquid flasks, fragile electronic monitors, or cosmetics cannot be rotated upside down or sideways.
   - *Modification*: Added `allow_rotation: bool` to the `Product` model and packing engine, constraining rotation to yaw-only when disabled.

---

## 5. Any Mistakes the AI Made

1. **Working Directory & Unicode Path Handling on Windows**:
   - The project path on the local filesystem contained non-breaking Unicode spaces (`\xa0\xa0`). The AI initially ran commands without quoting or path-normalizing the directory, which caused Windows PowerShell to default back to the root `C:\` drive.
   - *Resolution*: Identified the path discrepancy using a Python script, normalized directory paths using `glob`, and executed Git and Django commands within the properly resolved path.

2. **Tie-Breaking in Box Sorting**:
   - The AI initially sorted candidate boxes solely by `cost`. When two different box models had the exact same procurement cost (e.g., $2.50), the order was non-deterministic.
   - *Resolution*: Updated the sort key to `(r.box_cost, r.box_volume)`, ensuring that between two equally priced boxes, the system chooses the more compact box to minimize void fill and transit damage.

3. **Multi-Box Partitioning Edge Case**:
   - The initial multi-box partitioner did not handle an oversized single item that exceeded even the largest box in the catalog, potentially creating an infinite loop.
   - *Resolution*: Added an explicit check that identifies unpackable oversized items, pops them out of the remaining queue, and flags them with a `CUSTOM / OVERSIZED CRATE REQUIRED` advisory.

---

## 6. How You Verified the Final Code

1. **Automated Unit & Integration Testing**:
   - Executed `python manage.py test -v 2` across 19 distinct test cases covering geometric rotation, weight limits, spatial collision, cost ranking, API contracts, and web views. All 19 passed with 100% success in 0.20s.
2. **Database Migration & Data Seeding**:
   - Applied full database migrations cleanly on SQLite and ran `python manage.py seed_data` to verify model constraints, foreign keys, and pre-populated catalog records.
3. **API Contract Verification**:
   - Tested `POST /api/recommend/` with valid order IDs, custom multi-item arrays, and invalid payloads to ensure accurate HTTP status codes (200 OK vs 400 Bad Request vs 404 Not Found).
4. **CI/CD Integration**:
   - Configured `.github/workflows/django_tests.yml` to ensure continuous regression testing across Python versions 3.10, 3.11, and 3.12.
