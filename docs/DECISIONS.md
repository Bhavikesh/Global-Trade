```md
# GlobalTrade.ai — Architecture & Product Decisions

## 1. Document Purpose

This document records important product, technical and architectural decisions made for GlobalTrade.ai.

Each decision should explain:

- What was decided
- Why it was decided
- What it affects
- Whether it is currently active

Do not silently change an accepted decision.

---

# 2. Decision Status

Use:

```text
Proposed
Accepted
Superseded
Rejected
```

---

# 3. Decision Log

## DEC-001 — Use GlobalTrade as the Project Directory Name

Status: Accepted

Decision:

The project directory will be:

```text
GlobalTrade/
```

Do not use `.ai` as the project directory or filename convention.

Reason:

The development environment may interpret `.ai` as a single file rather than the intended project directory structure.

---

## DEC-002 — Use a Modular Monolith Initially

Status: Accepted

Decision:

GlobalTrade.ai will initially be implemented as a modular monolith.

Reason:

The current product requires many business modules, but that does not justify distributed microservices during the initial implementation.

Benefits:

- Lower complexity
- Easier development
- Easier debugging
- Easier local setup
- Easier deployment
- Simpler data consistency
- Clear path for future module extraction

---

## DEC-003 — Do Not Start With Microservices

Status: Accepted

Decision:

Microservices will not be used during the initial implementation.

Reason:

The current requirements do not provide sufficient justification for the operational complexity of distributed services.

Microservices may be considered later only when actual requirements justify independent scaling, deployment, ownership or failure isolation.

---

## DEC-004 — Use Next.js for the Frontend

Status: Accepted

Decision:

The frontend will use:

```text
Next.js
React
TypeScript
Tailwind CSS
shadcn/ui
```

Reason:

This provides a modern, maintainable frontend foundation suitable for the application while keeping the UI stack relatively small.

---

## DEC-005 — Use FastAPI for the Backend

Status: Accepted

Decision:

The backend will use:

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
```

Reason:

The platform has substantial AI, document-processing, RAG and data-processing requirements, making Python a natural fit while still supporting structured API development.

---

## DEC-006 — Use PostgreSQL as the Primary Database

Status: Accepted

Decision:

PostgreSQL will be the primary application database.

Reason:

The core business domain is highly relational.

Examples include:

```text
Organization
User
Product
Supplier
Buyer
RFQ
Quotation
Order
Shipment
Document
Compliance
Risk
Payment
```

A relational database provides appropriate support for these relationships, constraints and transactional workflows.

---

## DEC-007 — Use pgvector for Initial Vector Storage

Status: Accepted

Decision:

Use PostgreSQL with pgvector for initial vector storage and semantic retrieval.

Reason:

The initial requirements do not justify operating a separate vector database.

Keeping vectors with PostgreSQL reduces architectural complexity while retaining semantic-search capability.

---

## DEC-008 — Do Not Start With MongoDB

Status: Accepted

Decision:

MongoDB will not be part of the initial architecture.

Reason:

The core domain is predominantly relational and PostgreSQL is sufficient for the initial requirements.

MongoDB may be reconsidered only when a specific requirement demonstrates a clear advantage.

---

## DEC-009 — Do Not Start With Elasticsearch/OpenSearch

Status: Accepted

Decision:

The initial search implementation will use PostgreSQL capabilities and pgvector.

Reason:

A separate search platform is unnecessary until actual search requirements or measured performance demonstrate that PostgreSQL is insufficient.

---

## DEC-010 — Do Not Start With Kafka or RabbitMQ

Status: Accepted

Decision:

Kafka and RabbitMQ will not be introduced during the initial implementation.

Reason:

The initial system does not require a distributed messaging architecture.

Background workers are sufficient for the initial asynchronous workloads.

---

## DEC-011 — Do Not Start With Kubernetes

Status: Accepted

Decision:

Kubernetes will not be used during the initial implementation.

Reason:

Kubernetes adds significant operational complexity and is not required for the initial product architecture.

It may be reconsidered if actual deployment scale or operational requirements justify it.

---

## DEC-012 — Use S3-Compatible Object Storage

Status: Accepted

Decision:

Binary files will be stored in S3-compatible object storage.

PostgreSQL will store file metadata and references rather than large binary file contents.

Reason:

The platform handles documents, certificates, images, videos and other files.

Object storage is better suited to this data than the relational database.

---

## DEC-013 — AI Will Not Control Critical Business Logic

Status: Accepted

Decision:

AI will assist the application but will not become the authoritative source for critical business logic.

Deterministic application logic will control:

- Financial calculations
- Permissions
- Authorization
- Workflow states
- State transitions
- Database integrity
- Transactions
- Auditability
- Critical business rules

Reason:

These areas require predictable, testable and auditable behavior.

---

## DEC-014 — Use Hybrid AI Architecture

Status: Accepted

Decision:

GlobalTrade.ai will use:

```text
LLM
+
RAG
+
Embeddings
+
Tool Calling
+
Structured Outputs
+
Deterministic Business Logic
```

Reason:

Different tasks require different mechanisms.

AI is appropriate for language understanding, extraction, semantic retrieval, summarization and recommendations.

Deterministic application logic is appropriate for calculations, rules and state management.

---

## DEC-015 — AI Must Operate Through Controlled Tools

Status: Accepted

Decision:

AI must interact with application capabilities through explicitly defined tools.

The LLM must not receive unrestricted:

- SQL access
- Database access
- File-system access
- External API access
- Financial transaction capability

Reason:

Controlled tools allow authorization, validation, logging and predictable behavior.

---

## DEC-016 — User Confirmation for Consequential AI-Assisted Actions

Status: Accepted

Decision:

AI may prepare consequential actions, but appropriate user confirmation or authorization is required before execution.

Examples include:

- Sending RFQs
- Sending negotiation messages
- Finalizing important records
- Submitting information to external systems
- Important financial actions

Reason:

The platform must preserve user control over consequential business activity.

---

## DEC-017 — Use RAG for Knowledge-Grounded AI

Status: Accepted

Decision:

Use RAG when AI responses depend on approved knowledge sources.

Potential sources include:

- Trade regulations
- Compliance information
- Internal documents
- Trade documents
- Product information
- Supplier information
- Buyer information
- Approved market information

Reason:

Relevant source information should be retrieved rather than relying only on model memory.

---

## DEC-018 — Retrieved Documents Are Data, Not Instructions

Status: Accepted

Decision:

Retrieved RAG content must be treated as data.

It must not automatically be treated as system instructions or executable commands.

Reason:

This reduces prompt-injection and unauthorized-action risks.

---

## DEC-019 — Deterministic Financial Calculations

Status: Accepted

Decision:

Financial and commercial calculations will be performed by backend application logic.

Examples:

```text
Subtotal
Freight
Insurance
Duty
Tax
Other Charges
Landed Cost
Profit
Margin
Payment Amount
```

Reason:

Financial calculations must be reproducible and testable.

AI may explain calculations but will not be the calculation engine.

---

## DEC-020 — Deterministic Supplier Scoring

Status: Accepted

Decision:

Supplier evaluation will use structured factors and deterministic scoring.

Potential factors:

- Price
- Delivery time
- Certifications
- Reputation
- Country risk
- Trade history
- Financial stability

AI may explain the result.

Reason:

The evaluation should be reproducible and based on identifiable inputs.

---

## DEC-021 — Deterministic Quote Comparison

Status: Accepted

Decision:

Quotation comparison will use structured quotation data and deterministic calculations.

AI may provide explanations and identify notable differences.

Reason:

Commercial comparisons require reliable numerical values and traceable inputs.

---

## DEC-022 — Compliance Uses a Hybrid Approach

Status: Accepted

Decision:

Compliance workflows will combine:

```text
Authoritative Data / Rules
+
Deterministic Evaluation
+
AI Explanation
```

Reason:

AI can assist with interpretation, but critical compliance information should rely on authoritative sources and explicit rules where available.

---

## DEC-023 — HS-Code AI Is Assistance, Not Absolute Classification

Status: Accepted

Decision:

The system may provide HS-code candidates and supporting evidence, but AI-generated classification must not automatically be treated as unquestionable authoritative classification.

Possible states include:

```text
AI Suggested
User Confirmed
Authoritative External Source
```

Reason:

Classification can have regulatory and commercial consequences.

---

## DEC-024 — Documents Are Generated From Structured Data

Status: Accepted

Decision:

Trade documents should be generated from validated structured application data and approved templates.

AI may assist with:

- Extraction
- Drafting
- Summarization
- Explanation

Reason:

Critical transactional fields must remain controlled and traceable.

---

## DEC-025 — Trade Workspace Is Primarily a UX/Workflow Concept

Status: Accepted

Decision:

Trade Workspace is initially treated as a product and workflow concept rather than automatically becoming a separate database entity.

Reason:

A separate table is unnecessary unless the product later demonstrates a genuine need for persistent workspace-specific data.

---

## DEC-026 — Use Explicit Workflow States

Status: Accepted

Decision:

Important business processes will use explicit states and controlled transitions.

Examples:

```text
RFQ
Order
Shipment
Quotation
Compliance
Payment
```

Reason:

Explicit state transitions prevent inconsistent workflow behavior and reduce scattered conditional logic.

---

## DEC-027 — Preserve Historical Transaction Values

Status: Accepted

Decision:

Important transaction-time values may be stored as historical snapshots where necessary.

Examples:

```text
Quoted Price
Payment Terms
Incoterm
Delivery Commitment
Product Information
Finalized Commercial Terms
```

Reason:

Changes to current master data must not rewrite the historical meaning of completed transactions.

---

## DEC-028 — Organization-Aware Data Isolation

Status: Accepted

Decision:

GlobalTrade.ai will be organization-aware.

Business data must be isolated by organization where applicable.

Backend authorization and data-access logic are responsible for enforcing isolation.

Reason:

Frontend filtering is not a security boundary.

---

## DEC-029 — No Fake Integrations

Status: Accepted

Decision:

Unavailable external integrations must never be presented as live integrations.

Mock data may be used only when clearly identified as mock/demo data.

Reason:

The platform must maintain trust and avoid presenting fabricated operational information as real.

---

## DEC-030 — No Separate Analytics Database Initially

Status: Accepted

Decision:

Initial analytics will be calculated from canonical transactional data in PostgreSQL.

Reason:

A separate analytics infrastructure is unnecessary until real requirements justify it.

---

## DEC-031 — No Global Cache by Default

Status: Accepted

Decision:

A caching layer such as Redis will not be introduced automatically.

Reason:

Database optimization, indexing, pagination and efficient queries should be attempted first.

Caching may be introduced when actual workload demonstrates the need.

---

## DEC-032 — Documentation Is the Project Source of Truth

Status: Accepted

Decision:

The project documentation will be maintained under:

```text
docs/
├── PRD.md
├── ARCHITECTURE.md
├── DESIGN.md
├── RULES.md
├── AI_SPEC.md
├── DATA_MODEL.md
├── TASKS.md
├── MEMORY.md
└── DECISIONS.md
```

The documents have distinct responsibilities and must not silently contradict one another.

Reason:

AI coding agents need persistent project context that does not depend on a single chat session.

---

## DEC-033 — AI Coding Agents Must Read Documentation Before Coding

Status: Accepted

Decision:

AI coding agents must read the relevant project documentation before modifying the codebase.

They must inspect existing code before creating new implementations.

Reason:

This reduces accidental architectural drift, duplicated code and invented requirements.

---

## DEC-034 — Documentation Changes Require Deliberate Updates

Status: Accepted

Decision:

Meaningful changes to requirements, architecture, data model, AI behavior or design must be reflected in the corresponding documentation.

Major decisions must be recorded in this file.

Reason:

The repository must remain synchronized with the actual system.

---

## DEC-035 — Build in Phases

Status: Accepted

Decision:

The complete GlobalTrade.ai vision will be implemented incrementally.

Phase 1 focuses on the core trade operating workflow and foundational AI capabilities.

Future capabilities must not be implemented early merely because they exist in the broader product vision.

Reason:

The product requirements cover a very large scope and should not become an oversized first implementation.

---

## DEC-036 — Minimal Complexity Is an Explicit Product Engineering Requirement

Status: Accepted

Decision:

Code, infrastructure and architecture must remain as simple as possible without sacrificing correctness, security or production quality.

Reason:

Unnecessary complexity increases:

- Bugs
- Maintenance cost
- Development time
- Operational cost
- Debugging difficulty

Every additional abstraction, dependency, service or infrastructure component must have a real reason to exist.

---

## DEC-037 — Production Quality Does Not Mean Zero Bugs

Status: Accepted

Decision:

The project will target production-grade engineering rather than claim that the system can contain absolutely zero defects.

Production readiness requires appropriate:

- Validation
- Authorization
- Testing
- Error handling
- Logging
- Security
- Data integrity
- Monitoring
- Backup and recovery
- Controlled failure behavior

Reason:

Zero defects cannot be guaranteed, but engineering discipline can significantly reduce failure risk and limit the impact of failures.

---

## DEC-038 — Use Auth0 as Managed Identity Provider

Status: Accepted

Decision:

Use Auth0 as the managed Identity Provider for authentication and user identity.

Do not implement custom password authentication, password hashing, JWT issuance, refresh-token infrastructure, or session storage in the application.

Auth0 handles authentication and identity.

GlobalTrade.ai remains the application-level authority for:
- Organization
- OrganizationMembership
- Application roles
- Application permissions
- Tenant isolation

The FastAPI backend validates the Auth0-issued JWT identity tokens and enforces authorization against our PostgreSQL models.

Do not introduce Auth0 Organizations or RBAC features unless explicitly required; our `OrganizationMembership` model in PostgreSQL remains the authoritative source of truth for tenancy and permissions.

Reason:

Delegating identity to a managed provider reduces security exposure, eliminates credential management complexity, and allows the platform to focus on EXIM domain logic.

---

## DEC-039 — Use psycopg v3 with Synchronous SQLAlchemy 2.0 Sessions

Status: Accepted

Decision:

The backend database access layer will use `psycopg` (v3) with standard synchronous SQLAlchemy 2.0 sessions (`Session`).

Do not use `asyncpg` or build an asynchronous database layer for the initial implementation.

Reason:

Synchronous database sessions keep the data layer simple, predictable, and easier to debug without unnecessary async complexity in the modular monolith.

---

## DEC-040 — Use npm as Frontend Package Manager

Status: Accepted

Decision:

The frontend will use `npm` with `package-lock.json`.

Do not use `pnpm` or `yarn`.

Reason:

Standardizes frontend dependency management on the default Node.js toolchain, ensuring clean, reproducible local setups.

---

## DEC-041 — Object Storage Strategy and Local Adaptation

Status: Accepted

Decision:

Object storage will not be implemented during Phase 0.

When file storage is implemented in later phases:
- Production will use an S3-compatible object storage service.
- Development may use a simple local filesystem adapter conforming to the storage boundary interface.
- Do not add MinIO or local S3 containers unless an explicit requirement later justifies running an S3-compatible service locally.

Reason:

Prevents premature infrastructure overhead during initial development while maintaining a clean boundary for future S3 integration.

---

# 4. Future Decision Rules

Before introducing a major technology or architectural pattern, document:

1. The problem being solved.
2. Why the current architecture is insufficient.
3. Alternatives considered.
4. Operational impact.
5. Maintenance impact.
6. Security impact.
7. Migration impact.
8. Why the change is required now.

No major architectural change should be introduced silently.

---

# 5. Final Decision Principle

GlobalTrade.ai follows:

**Build only what is required.**

**Prefer the simplest correct solution.**

**Use deterministic systems where correctness matters.**

**Use AI where intelligence adds clear value.**

**Preserve user control.**

**Document important decisions.**

**Do not optimize for hypothetical problems.**
```