# Task Specification: AI-Assisted Box Selection System

## Context & Objectives
In an ecommerce warehouse, order fulfillment requires dispatchers to determine the most suitable shipping box for every outgoing order. 
- Each **product** has physical dimensions (Length, Width, Height) and weight.
- Each **shipping box** has internal dimensions, maximum weight capacity, tare weight, and procurement cost.
- The system must determine and recommend the optimal box that safely contains the items while **minimizing packaging costs**.

---

## Deliverables & Submission Checklist

- [x] **1. Django-Based Core System**:
  - [x] SQLite database models for `Box`, `Product`, `Order`, `OrderItem`, and `BoxRecommendationHistory`.
  - [x] Pure-Python 3D coordinate placement bin-packing algorithm with 6-DOF item rotation.
  - [x] Strict weight capacity ceiling enforcement.
  - [x] Cost-first candidate ranking with volumetric waste tie-breakers.
  - [x] Multi-box fallback partitioning for oversized or overweight orders.
  - [x] Context-aware AI Packaging Assistant providing void fill calculations, fragile warnings, and handling notes.

- [x] **2. User Interface & REST API**:
  - [x] Warehouse Dashboard (`/`) with active box catalog and recent recommendation logs.
  - [x] Interactive Box Recommendation Simulator (`/simulator/`) supporting database orders and ad-hoc custom dimensions.
  - [x] REST API endpoint `POST /api/recommend/` returning structured JSON recommendations with 3D coordinate layouts.
  - [x] Management command (`python manage.py seed_data`) to pre-populate realistic catalog data.

- [x] **3. Mandatory Documentation Files**:
  - [x] `README.md`: Architecture overview, 3D non-overlap math formulation, installation steps, and API schema.
  - [x] `AI_USAGE.md`: Detailed responses to all 6 prompt questions (tools used, prompts, accepted outputs, rejected outputs, AI mistakes caught, verification).
  - [x] `LEARNINGS.md`: Reflection on NP-hard 3D-BPP, logistics trade-offs, and offline AI fallback design.
  - [x] `TEST_OUTPUT.md`: Terminal log of the full automated test suite run.
  - [x] `TASK.md`: Task breakdown and requirement tracking.

- [x] **4. Authentic Chat Transcript**:
  - [x] Exported directly from the execution environment to `transcripts/chat_transcript.jsonl` without AI re-generation.

- [x] **5. Test Suite & CI/CD**:
  - [x] 19 automated unit and integration tests in `box_selection/tests.py` (100% passing).
  - [x] Continuous Integration workflow in `.github/workflows/django_tests.yml` testing Python 3.10, 3.11, and 3.12.

---

## Project Structure & File Map

```
Ai selection/
├── .github/
│   └── workflows/
│       └── django_tests.yml          # GitHub Actions matrix CI
├── box_selection/                     # Core application
│   ├── management/commands/
│   │   └── seed_data.py               # Seed realistic boxes, products & orders
│   ├── migrations/
│   │   └── 0001_initial.py            # Database schema migration
│   ├── services/
│   │   ├── packer.py                  # 3D Bin packing & coordinate placement engine
│   │   ├── recommender.py             # Box ranking & multi-box partitioner
│   │   └── ai_assistant.py            # AI packaging advice & void-fill calculator
│   ├── templates/box_selection/
│   │   ├── base.html                  # Bootstrap 5 layout
│   │   ├── dashboard.html             # Operational metrics dashboard
│   │   ├── simulator.html             # Interactive 3D calculator
│   │   ├── box_list.html              # Shipping box catalog
│   │   ├── product_list.html          # Product catalog
│   │   ├── order_list.html            # Orders queue
│   │   └── order_detail.html          # Printable warehouse packing slip
│   ├── admin.py                       # Django admin configuration
│   ├── models.py                      # Data models
│   ├── serializers.py                 # REST API serializers
│   ├── tests.py                       # 19 automated test cases
│   ├── urls.py                        # App route definitions
│   └── views.py                       # REST API & Web UI controllers
├── box_selection_system/              # Project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── transcripts/
│   └── chat_transcript.jsonl         # Authentic raw conversation transcript
├── AI_USAGE.md                        # AI usage disclosure
├── LEARNINGS.md                       # Key assignment takeaways
├── README.md                          # Full system documentation
├── TASK.md                            # Task specification and checklist
├── TEST_OUTPUT.md                     # Automated test run terminal trace
├── requirements.txt                   # Dependency definitions
└── manage.py                          # Django management CLI
```

---

## Verification Summary

- **Test Suite Command**: `python manage.py test -v 2`
- **Results**: 19 tests executed in 0.200s, 0 failures, 0 errors.
- **Git Repository**: Initialized, tracked, and committed with clean commits ready for GitHub push.
