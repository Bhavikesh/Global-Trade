```md
# GlobalTrade.ai — Implementation Tasks

## 1. Document Purpose

This document defines the implementation sequence for GlobalTrade.ai.

It is the source of truth for:

- What is currently being built
- What is not currently being built
- Implementation order
- Task dependencies
- Completion criteria
- Phase boundaries

Only tasks explicitly marked as active should be implemented.

---

# 2. Task Rules

- Implement tasks in dependency order.
- Do not implement future-phase tasks early.
- Do not expand a task beyond its stated scope.
- Complete and verify a task before marking it complete.
- Reuse existing code where appropriate.
- Follow `PRD.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, `AI_SPEC.md`, `DESIGN.md`, and `RULES.md`.
- Update this file when task status changes.
- Any major scope or architecture change must be recorded in `DECISIONS.md`.

---

# 3. Task Status

Use:

```text
[ ] Not Started
[-] In Progress
[x] Completed
[!] Blocked
```

---

# 4. Phase 0 — Project Foundation

## T0.1 Repository Structure

[x] Create the approved project structure.

Expected top-level structure:

```text
GlobalTrade/
├── docs/
├── frontend/
├── backend/
└── README.md
```

Do not create unnecessary directories.

---

## T0.2 Frontend Foundation

[x] Initialize the Next.js + TypeScript frontend.

Required foundation:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

Verify the application starts successfully.

---

## T0.3 Backend Foundation

[x] Initialize the FastAPI backend.

Required foundation:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

Verify the API starts successfully.

---

## T0.4 Database Foundation

[x] Configure PostgreSQL.

[x] Configure database migrations.

[x] Verify database connectivity.

---

## T0.5 Environment Configuration

[x] Create environment-based configuration.

[x] Ensure secrets are not hardcoded.

[x] Add an appropriate environment example file without real secrets.

---

## T0.6 Development Verification

[x] Verify frontend starts.

[x] Verify backend starts.

[x] Verify database connection.

[x] Verify frontend can communicate with backend.

---

# 5. Phase 1 — Identity and Organization

## T1.1 Authentication

[x] Implement secure user authentication using Auth0.

Requirements:

- Client-side Auth0 integration (sign in, sign out)
- Backend JWT token verification
- Authenticated route protection
- User identity extraction (identity_provider_id)

---

## T1.2 User Profile

[x] Implement authenticated user profile.

Support:

- Name
- Email
- Phone where applicable
- Account status

---

## T1.3 Organization Creation

[x] Allow an authenticated user to create an organization.

Support core organization information defined in `DATA_MODEL.md`.

---

## T1.4 Organization Membership

[x] Implement organization membership.

[x] Associate users with organizations.

[x] Prevent unauthorized cross-organization access.

---

## T1.5 Roles and Permissions

[x] Implement the initial role-based permission system.

Support the roles required for Phase 1.

[x] Enforce permissions in the backend.

[x] Reflect permissions in the frontend where useful for UX.

---

## T1.6 Organization Isolation Verification

[x] Verify that users cannot access another organization's protected records.

[x] Add tests for organization isolation.


---

# 6. Phase 1 — Company Profile

## T1.7 Company Profile

[x] Implement company profile management.

Support relevant fields such as:

- Legal name
- Display name
- Business type
- Country
- Address
- Tax information
- VAT information
- IEC information
- Website
- Contact information
- Verification status

---

## T1.8 Business Documents

[ ] Allow the organization to associate relevant certificates and business documents.

[ ] Store file metadata in PostgreSQL.

[ ] Store binary files in object storage.

---

# 7. Phase 1 — Product Management

## T1.9 Product CRUD

[ ] Implement product creation.

[ ] Implement product listing.

[ ] Implement product detail view.

[ ] Implement product editing.

[ ] Implement product archival/deactivation where required.

---

## T1.10 Product Information

Support:

- Name
- Description
- Category
- Specifications
- MOQ
- Packaging
- Pricing information
- HS code
- Keywords
- SEO description
- International description

---

## T1.11 Product Files

[ ] Support product images.

[ ] Support product certificates and specification files.

[ ] Keep file metadata separate from binary storage.

---

## T1.12 Product Search

[ ] Implement initial product search using PostgreSQL capabilities.

Do not introduce a separate search engine.

---

# 8. Phase 1 — Buyer Management

## T1.13 Buyer Records

[ ] Implement buyer creation.

[ ] Implement buyer listing.

[ ] Implement buyer detail view.

[ ] Implement buyer editing.

---

## T1.14 Buyer Search and Filtering

[ ] Support basic buyer search and filters.

---

# 9. Phase 1 — Supplier Management

## T1.15 Supplier Records

[ ] Implement supplier creation.

[ ] Implement supplier listing.

[ ] Implement supplier detail view.

[ ] Implement supplier editing.

---

## T1.16 Supplier Information

Support:

- Company name
- Contact information
- Country
- Address
- Website
- Supplier type
- Verification status
- Certifications
- Notes

---

## T1.17 Supplier Search

[ ] Implement supplier search and filtering.

[ ] Support relevant structured filters.

---

# 10. Phase 1 — RFQ Management

## T1.18 RFQ Creation

[ ] Implement RFQ creation.

Support:

- Title
- Description
- Destination country
- Required delivery date
- Payment terms
- RFQ items

---

## T1.19 RFQ Items

[ ] Implement RFQ item management.

Support:

- Product
- Description
- Quantity
- Unit
- Specifications
- Quality requirements
- Packaging requirements

---

## T1.20 RFQ Supplier Invitations

[ ] Allow users to select suppliers for an RFQ.

[ ] Implement supplier invitation records.

[ ] Implement invitation statuses.

---

## T1.21 RFQ Lifecycle

[ ] Implement RFQ states.

Support the approved state model:

```text
DRAFT
SENT
RESPONSES_RECEIVED
UNDER_REVIEW
NEGOTIATION
AWARDED
CANCELLED
EXPIRED
```

[ ] Enforce valid transitions in the backend.

---

## T1.22 RFQ List and Detail

[ ] Implement searchable RFQ listing.

[ ] Implement RFQ detail view.

[ ] Show RFQ status and related information.

---

# 11. Phase 1 — Quotation Management

## T1.23 Quotation Creation

[ ] Allow suppliers to submit quotations against an RFQ where the current product workflow supports it.

---

## T1.24 Quotation Items

[ ] Implement quotation item management.

Support:

- Quantity
- Unit
- Unit price
- Subtotal
- Product/reference information

---

## T1.25 Commercial Terms

Support:

- Currency
- Valid-until date
- Payment terms
- Incoterm
- Delivery time
- Shipping cost
- Insurance cost
- Duty
- Tax
- Other charges
- Total amount

---

## T1.26 Deterministic Quote Calculations

[ ] Implement backend calculations for:

- Subtotal
- Freight
- Insurance
- Duty
- Tax
- Other charges
- Estimated landed cost
- Total values where applicable

[ ] Add unit tests for financial calculations.

---

## T1.27 Quotation Detail

[ ] Implement quotation detail view.

[ ] Show supplier and commercial terms clearly.

---

# 12. Phase 1 — Quote Comparison

## T1.28 Quote Comparison

[ ] Implement structured comparison of quotations belonging to the same RFQ.

Compare:

- Unit price
- Freight
- Insurance
- Duty
- Tax
- Other charges
- Estimated landed cost
- Delivery time
- Incoterm
- Payment terms

---

## T1.29 Quote Comparison UI

[ ] Implement a clear comparison table.

[ ] Clearly distinguish supplied values from calculated values.

---

## T1.30 Quote Comparison Verification

[ ] Verify comparison calculations using automated tests.

[ ] Verify missing quotation data is handled safely.

---

# 13. Phase 1 — Order Management

## T1.31 Order Creation

[ ] Create an order from an approved quotation where applicable.

[ ] Preserve required finalized transaction values.

---

## T1.32 Order Items

[ ] Implement order items.

[ ] Preserve transaction-specific values where required.

---

## T1.33 Order Lifecycle

[ ] Implement the approved order states:

```text
CONFIRMED
PRODUCTION
INSPECTION
READY_TO_SHIP
SHIPPED
CUSTOMS
DELIVERED
COMPLETED
CANCELLED
```

[ ] Enforce valid state transitions.

---

## T1.34 Order Detail

[ ] Implement order listing.

[ ] Implement order detail view.

[ ] Show linked RFQ and quotation information where applicable.

---

# 14. Phase 1 — Documents

## T1.35 Document Records

[ ] Implement document metadata management.

Support relevant document types from `DATA_MODEL.md`.

---

## T1.36 File Storage

[ ] Implement secure object-storage integration.

[ ] Implement file metadata records.

[ ] Implement controlled file access.

---

## T1.37 Document Upload

[ ] Implement document upload.

[ ] Validate file type and size.

---

## T1.38 Document Versioning

[ ] Implement document version handling where required.

---

## T1.39 Initial Document Generation

[ ] Implement the first required document-generation workflow using structured application data.

Do not implement every document type at once.

---

# 15. Phase 1 — Compliance

## T1.40 Compliance Record

[ ] Implement compliance check records.

---

## T1.41 Compliance Status

[ ] Implement approved compliance states:

```text
NOT_CHECKED
IN_REVIEW
CLEAR
ACTION_REQUIRED
RESTRICTED
```

---

## T1.42 Compliance Requirements

[ ] Implement individual compliance requirements linked to a compliance check.

---

## T1.43 Compliance Source Metadata

[ ] Store relevant source/reference information where available.

---

## T1.44 Basic Compliance Workflow

[ ] Implement the initial compliance workflow using available authoritative data/rules.

[ ] Do not fabricate regulatory information.

---

# 16. Phase 1 — AI Foundation

## T1.45 AI Provider Integration

[ ] Implement a provider-independent AI integration boundary.

[ ] Keep model/provider configuration outside business modules.

---

## T1.46 AI Orchestrator

[ ] Implement the initial AI orchestration layer.

[ ] Support controlled AI tasks.

---

## T1.47 Structured AI Outputs

[ ] Implement schema validation for AI outputs used by application logic.

---

## T1.48 AI Error Handling

[ ] Handle:

- Model failure
- Timeout
- Rate limit
- Invalid output
- Unavailable provider

---

## T1.49 AI Context Control

[ ] Ensure only relevant authorized context is sent to the model.

---

# 17. Phase 1 — RAG Foundation

## T1.50 Knowledge Ingestion

[ ] Implement initial document ingestion for approved knowledge sources.

---

## T1.51 Text Extraction

[ ] Extract text from supported documents.

[ ] Use OCR only where required.

---

## T1.52 Chunking

[ ] Implement meaningful document chunking.

---

## T1.53 Embeddings

[ ] Generate embeddings for approved knowledge content.

---

## T1.54 Vector Storage

[ ] Store embeddings using PostgreSQL + pgvector.

---

## T1.55 Semantic Retrieval

[ ] Implement permission-aware semantic retrieval.

---

## T1.56 Source Attribution

[ ] Preserve source metadata with retrieved knowledge.

---

# 18. Phase 1 — AI Assistant

## T1.57 Context-Aware Assistant

[ ] Implement the initial AI Assistant.

The assistant should understand relevant current application context where authorized.

---

## T1.58 Knowledge Queries

[ ] Allow the assistant to answer approved knowledge-based questions using RAG.

---

## T1.59 Controlled Tools

[ ] Implement initial read-only tools such as:

```text
search_products
search_suppliers
search_buyers
get_rfq
get_quotations
get_order
search_knowledge
```

---

## T1.60 AI Permission Enforcement

[ ] Verify that AI tools obey the current user's permissions and organization boundaries.

---

# 19. Phase 1 — AI-Assisted RFQ

## T1.61 Natural-Language RFQ Draft

[ ] Allow the user to describe an RFQ in natural language.

---

## T1.62 RFQ Extraction

[ ] Extract structured RFQ fields using AI.

---

## T1.63 RFQ Validation

[ ] Validate the extracted RFQ.

---

## T1.64 RFQ Review

[ ] Require user review before the RFQ becomes an operational record.

---

# 20. Phase 1 — AI Quote Analysis

## T1.65 Quote Analysis

[ ] Implement AI-assisted analysis of quotation differences.

---

## T1.66 Quote Explanation

[ ] Provide explanations based only on available quotation data and deterministic calculations.

[ ] Prevent fabricated values.

---

# 21. Phase 1 — Supplier Recommendation

## T1.67 Supplier Feature Preparation

[ ] Prepare structured supplier evaluation features.

Potential factors:

- Price
- Delivery time
- Certifications
- Reputation
- Country risk
- Trade history
- Financial stability

---

## T1.68 Deterministic Supplier Scoring

[ ] Implement a configurable structured scoring mechanism.

[ ] Do not use the LLM as the numerical scoring engine.

---

## T1.69 AI Supplier Explanation

[ ] Allow AI to explain the structured supplier evaluation using available evidence.

---

# 22. Phase 1 — HS-Code Assistance

## T1.70 HS-Code Candidate Assistance

[ ] Implement initial HS-code assistance using product information.

---

## T1.71 HS-Code Evidence

[ ] Provide relevant evidence/source information where available.

---

## T1.72 HS-Code User Confirmation

[ ] Distinguish AI suggestions from confirmed classifications.

---

# 23. Phase 1 — Trade Workspace

## T1.73 Trade Workspace Overview

[ ] Implement the Trade Workspace experience.

Display relevant:

- RFQ
- Supplier
- Buyer
- Product
- Quotations
- Order
- Documents
- Compliance
- Shipment
- Payments
- Risk
- Activity

Only show information relevant to the current trade.

---

## T1.74 Trade Timeline

[ ] Implement timeline presentation for significant business events.

---

# 24. Phase 1 — Dashboard

## T1.75 Dashboard Metrics

[ ] Implement useful operational metrics.

Potential metrics:

- Active RFQs
- Pending quotations
- Active orders
- Shipments in transit
- Pending payments
- Open compliance items

---

## T1.76 Dashboard Actions

[ ] Provide direct actions such as:

- Create RFQ
- Add Product
- Add Supplier
- Compare Quotes
- Create Order
- Generate Document
- Check Compliance

---

## T1.77 Dashboard Attention Area

[ ] Show actionable items requiring user attention.

---

# 25. Phase 1 — Notifications

## T1.78 In-App Notifications

[ ] Implement in-app notifications.

Support relevant events such as:

- Quotation received
- Compliance issue
- Missing document
- Shipment update
- Payment pending

---

## T1.79 Notification Linking

[ ] Link notifications to their related records where possible.

---

# 26. Phase 1 — Activity and Audit

## T1.80 Activity Timeline

[ ] Implement user-visible business activity.

---

## T1.81 Audit Events

[ ] Implement audit events for important business changes.

---

## T1.82 Audit Verification

[ ] Verify that important mutations generate appropriate audit records.

---

# 27. Phase 1 — Testing and Quality

## T1.83 Backend Unit Tests

[ ] Add tests for:

- Calculations
- Validation
- State transitions
- Supplier scoring
- Core business rules

---

## T1.84 API Tests

[ ] Add tests for critical API endpoints.

---

## T1.85 Authorization Tests

[ ] Verify role-based permissions.

[ ] Verify organization isolation.

---

## T1.86 Frontend Verification

[ ] Verify core workflows in the UI.

[ ] Verify loading states.

[ ] Verify empty states.

[ ] Verify error states.

[ ] Verify permission states.

---

## T1.87 AI Evaluation

[ ] Evaluate:

- Structured extraction
- RAG retrieval
- Source grounding
- Quote analysis
- Supplier explanation
- HS-code assistance

---

## T1.88 Security Review

[ ] Verify:

- No hardcoded secrets
- Secure file access
- Authorization enforcement
- Input validation
- Sensitive logging controls

---

# 28. Phase 1 — Production Readiness

## T1.89 Logging

[ ] Implement structured backend logging.

---

## T1.90 Health Checks

[ ] Implement application health checks.

---

## T1.91 Error Monitoring

[ ] Implement production-appropriate error monitoring.

---

## T1.92 Database Backup Strategy

[ ] Configure production database backup strategy.

---

## T1.93 Deployment

[ ] Containerize the application with Docker.

[ ] Prepare development, staging and production configuration.

---

## T1.94 CI/CD

[ ] Configure automated:

- Linting
- Type checking
- Tests
- Build verification

---

# 29. Phase 2 — Intelligence Expansion

Do not implement during Phase 1.

## T2.1 Advanced Buyer Discovery

[ ] Implement advanced buyer discovery.

## T2.2 Advanced Supplier Discovery

[ ] Implement external supplier discovery integrations where permitted.

## T2.3 AI Trade Advisor

[ ] Implement broader AI trade advisory workflows.

## T2.4 Advanced Risk Analysis

[ ] Expand structured risk analysis.

## T2.5 AI Negotiation Assistant

[ ] Implement negotiation assistance.

## T2.6 Advanced HS-Code Assistance

[ ] Expand classification capabilities.

## T2.7 Market Intelligence

[ ] Implement approved market intelligence sources.

---

# 30. Phase 3 — Logistics and Finance Expansion

Do not implement during Phase 1.

## T3.1 Freight Marketplace

[ ] Implement freight comparison and provider integrations.

## T3.2 Shipment Tracking Integrations

[ ] Integrate approved shipment providers.

## T3.3 Customs Integrations

[ ] Integrate approved customs systems.

## T3.4 Payment Integrations

[ ] Integrate approved payment providers.

## T3.5 Finance Features

[ ] Expand finance workflows.

## T3.6 Warehouse

[ ] Implement inventory and warehouse capabilities.

---

# 31. Phase 4 — Ecosystem Integrations

Do not implement during Phase 1.

## T4.1 ERP Integrations

[ ] Implement approved ERP integrations.

## T4.2 Accounting Integrations

[ ] Implement approved accounting integrations.

## T4.3 Banking Integrations

[ ] Implement approved banking integrations.

## T4.4 Communication Integrations

[ ] Implement approved:

- Email
- WhatsApp
- SMS

integrations.

## T4.5 Digital Signatures

[ ] Implement approved digital signature integrations.

## T4.6 GPS / Tracking Integrations

[ ] Implement approved tracking integrations.

---

# 32. Phase 5 — Platform Scale

Do not implement unless actual requirements justify it.

## T5.1 Dedicated Search Infrastructure

[ ] Evaluate OpenSearch/Elasticsearch only if PostgreSQL search is demonstrably insufficient.

## T5.2 Dedicated Messaging Infrastructure

[ ] Evaluate Kafka/RabbitMQ only if actual event-processing requirements justify it.

## T5.3 Distributed Services

[ ] Evaluate extracting modules into services only when independent scaling, deployment, ownership or failure isolation requires it.

## T5.4 Kubernetes

[ ] Evaluate Kubernetes only when operational scale justifies its complexity.

## T5.5 Additional Databases

[ ] Introduce additional databases only when a documented requirement cannot reasonably be solved with PostgreSQL.

---

# 33. Explicitly Out of Scope Until Approved

The following must not be implemented merely because they exist in the broader product vision:

- Full mobile application suite
- Autonomous trade execution
- Autonomous financial transactions
- Unrestricted AI agents
- Unverified external data sources
- Fake live integrations
- Kubernetes
- Kafka
- RabbitMQ
- MongoDB
- Elasticsearch/OpenSearch
- Microservices
- Separate analytics database
- Separate vector database

---

# 34. Task Completion Requirements

A task can be marked `[x] Completed` only when:

- The required functionality is implemented.
- The implementation follows project documentation.
- Relevant validation exists.
- Authorization is enforced where required.
- Error states are handled.
- Relevant tests pass.
- The application still starts successfully.
- Existing functionality is not unnecessarily broken.
- No unnecessary dependencies or infrastructure were introduced.
- Documentation is updated when required.

---

# 35. Current Execution Rule

Only Phase 0 and the currently approved Phase 1 task should be implemented.

Do not begin Phase 2, Phase 3, Phase 4 or Phase 5 without explicit approval.

Do not skip foundational dependencies merely to reach visible UI features faster.

---

# 36. Final Task Principle

Implementation must proceed:

```text
Foundation
    ↓
Identity
    ↓
Organization
    ↓
Master Data
    ↓
RFQ
    ↓
Quotations
    ↓
Comparison
    ↓
Orders
    ↓
Documents
    ↓
Compliance
    ↓
AI Foundation
    ↓
AI Workflows
    ↓
Trade Workspace
    ↓
Dashboard
    ↓
Testing
    ↓
Production Readiness
```

Build the smallest complete step before moving to the next one.
```