# Specs Directory — Spec-Driven Development (SDD)

Welcome to the **FPL Dugout Spec Hub**. This directory hosts all feature specifications, architectural plans, and actionable task manifests following the **Spec-Driven Development (SDD)** framework codified in [CONSTITUTION.md](file:///e:/Fantasy-Premier-League/CONSTITUTION.md).

---

## The 3-Artifact Specification Pattern

Every feature under active development lives in its own isolated directory under `specs/<NNN-feature-name>/` and consists of three living documents:

```
specs/
├── README.md               # This guide
├── _template/              # Standard templates for new features
│   ├── spec.md             # The WHAT and WHY (User stories, functional reqs, acceptance criteria)
│   ├── plan.md             # The HOW (Architecture, OKF contracts, component map)
│   └── tasks.md            # The EXECUTION (Sequenced, verifiable task checklist)
└── 001-example-feature/    # Concrete feature enclaves
    ├── spec.md
    ├── plan.md
    └── tasks.md
```

### 1. `spec.md` — The Specification (What & Why)
- **Primary Audience**: Product Owner, FPL Managers, Developers, AI Agents.
- **Focus**: Problem statement, user stories, functional requirements, and measurable acceptance criteria.
- **Rule**: Written *before* writing code or implementation architecture. Never discuss internal class implementation details here.

### 2. `plan.md` — Technical Design (How)
- **Primary Audience**: Engineers, AI Coding Agents.
- **Focus**: Architectural topology, data contracts from [knowledge/datasets/](file:///e:/Fantasy-Premier-League/knowledge/datasets/index.md), mathematical equations from [knowledge/models/](file:///e:/Fantasy-Premier-League/knowledge/models/index.md), file-by-file modification map, and error-handling strategies.
- **Rule**: Must respect the 3-Tier Codebase Boundary ([CONSTITUTION.md](file:///e:/Fantasy-Premier-League/CONSTITUTION.md) Article I).

### 3. `tasks.md` — Action Manifest (Execution)
- **Primary Audience**: AI Coding Agents and Implementing Engineers.
- **Focus**: Atomic, sequentially ordered checklist items with explicit file targets and verification commands.
- **Rule**: Tasks must be marked `[x]` incrementally as tests pass and verification gates succeed.

---

## How to Start a New Feature

1. **Scaffold a Feature Enclave**:
   Copy `specs/_template/` to `specs/<NNN-feature-name>/`:
   ```bash
   cp -r specs/_template specs/001-my-feature-name
   ```
2. **Draft the Specification** (`spec.md`):
   - Fill out user stories, functional requirements, and acceptance criteria.
   - Run the 3-tier vocabulary filter against [docs/voice-and-tone-guide.md](file:///e:/Fantasy-Premier-League/docs/voice-and-tone-guide.md).
3. **Formulate the Plan** (`plan.md`):
   - Map dependencies to [knowledge/](file:///e:/Fantasy-Premier-League/knowledge/) schemas and models.
   - Specify exact files to create or modify.
4. **Break Down Tasks** (`tasks.md`):
   - Create granular, checkable tasks with automated verification steps.
5. **Implement & Pass Gates**:
   - Execute task-by-task.
   - Verify the 4 Constitutional Quality Gates:
     ```bash
     python scripts/validate_okf.py
     npm run check-copy --prefix frontend
     python knowledge/references/attesters/verify_schema.py --season 2026-27 --gw 2
     python knowledge/references/attesters/verify_solver.py --season 2026-27 --gw 2
     pytest
     ```
6. **Log Progress**: Record completion in [JOURNEY.md](file:///e:/Fantasy-Premier-League/JOURNEY.md).

---

## Historical Archive Note
Prior to the adoption of the Spec-Kit standard, design documents were stored as flat files in [`docs/superpowers/specs/`](file:///e:/Fantasy-Premier-League/docs/superpowers/specs/). Those files are preserved as an immutable historical record. All new features must be scaffolded under `specs/`.
