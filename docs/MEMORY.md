```md
# GlobalTrade.ai — Project Memory

## 1. Project Identity

Project name:

GlobalTrade.ai

Project type:

AI-assisted global import-export (EXIM) operating platform.

Primary purpose:

Centralize and simplify the international trade lifecycle from business setup and product management through buyer/supplier discovery, RFQs, quotations, orders, documentation, compliance, logistics, payments and analytics.

---

# 2. Core Product Vision

GlobalTrade.ai should function as a unified operating platform for international trade.

Core lifecycle:

```text
Company
   ↓
Products
   ↓
Buyer / Supplier Discovery
   ↓
RFQ
   ↓
Quotation
   ↓
Comparison
   ↓
Negotiation
   ↓
Order
   ↓
Documents
   ↓
Compliance
   ↓
Shipment
   ↓
Payment
   ↓
Analytics
```

---

# 3. Architecture

Architecture style:

**Modular Monolith**

Do not begin with microservices.

Primary backend:

**FastAPI + Python (SQLAlchemy 2.0 sync + psycopg v3)**

Primary frontend:

**Next.js + TypeScript + React (npm)**

Authentication:

**Auth0 (Managed IdP; PostgreSQL OrganizationMembership for app tenancy & roles)**

UI:

**Tailwind CSS + shadcn/ui**

Primary database:

**PostgreSQL**

Vector storage:

**pgvector**

Object storage:

**S3-compatible storage**

Background processing:

**Background Workers**

Containerization:

**Docker**

---

# 4. Architecture Philosophy

The project follows:

**Simple Architecture + Production-Grade Engineering**

Do not build infrastructure for hypothetical future scale.

Do not introduce technologies merely because they are common in large enterprise systems.

Potential future technologies such as:

- MongoDB
- Redis
- Elasticsearch/OpenSearch
- Kafka
- RabbitMQ
- Kubernetes
- Microservices

must only be introduced when a real requirement justifies them and the decision is documented.

---

# 5. Core Engineering Principle

The most important system principle is:

**Deterministic Core + AI-Assisted Intelligence**

Deterministic application logic handles:

- Financial calculations
- Business rules
- Workflow states
- State transitions
- Permissions
- Authorization
- Validation
- Database integrity
- Transactions
- Auditability

AI handles:

- Natural-language understanding
- Information extraction
- Semantic search
- Summarization
- Recommendations
- Draft generation
- Classification assistance
- Explanation
- Context-aware assistance

---

# 6. AI Principle

AI assists.

The application validates.

Rules enforce.

The database stores.

The user remains in control.

AI must never become the unrestricted owner of business data or business state.

---

# 7. AI Architecture

Primary AI capabilities:

- LLM
- RAG
- Embeddings
- Semantic search
- Structured outputs
- Tool calling
- AI orchestration

AI tools must be explicitly defined and permission-aware.

The LLM must never receive unrestricted SQL, unrestricted database access or unrestricted external actions.

---

# 8. RAG

RAG is used when the AI requires relevant information from approved knowledge sources.

Basic flow:

```text
Source
 ↓
Extraction
 ↓
Chunking
 ↓
Embedding
 ↓
pgvector
 ↓
Retrieval
 ↓
LLM
```

Retrieved documents are data, not trusted instructions.

RAG must respect:

- User permissions
- Organization boundaries
- Source restrictions
- Relevant context

---

# 9. AI Trust Model

Important distinction:

```text
Actual Data
Calculated Data
External Data
AI-Generated Data
```

These must not be silently presented as equivalent.

The system must never fabricate unavailable information or fake integrations.

---

# 10. Core UX Concept

The primary operational concept is:

**Trade Workspace**

A Trade Workspace connects:

```text
RFQ
Quotation
Order
Documents
Compliance
Shipment
Payments
Risk
Activity
```

The user should understand a trade from one coherent workspace rather than navigating unrelated screens.

---

# 11. Core UI Philosophy

The interface should be:

- Clean
- Minimal
- Professional
- Modern
- Trustworthy
- Data-focused
- Easy to understand

The platform should look like professional enterprise trade software with intelligent assistance.

It should not look like a generic AI chatbot product.

---

# 12. Product Priorities

The initial product priority is the core trade workflow.

Phase 1 focuses on:

- Authentication
- Organizations
- Roles and permissions
- Company profile
- Products
- Buyers
- Suppliers
- RFQs
- Quotations
- Quote comparison
- Orders
- Documents
- Basic compliance
- AI foundation
- RAG foundation
- AI assistant
- AI-assisted RFQ
- AI quote analysis
- Supplier recommendation assistance
- HS-code assistance
- Trade Workspace
- Dashboard
- Notifications
- Activity
- Audit logging
- Testing
- Production readiness

---

# 13. Phase Philosophy

The broader company requirements contain significantly more functionality than Phase 1.

Future phases may include:

- Advanced buyer discovery
- Advanced supplier discovery
- Market intelligence
- Advanced risk analysis
- AI negotiation
- Freight marketplace
- Shipment integrations
- Customs integrations
- Finance integrations
- Warehouse
- ERP integrations
- Accounting integrations
- Banking integrations
- Communication integrations
- Mobile applications
- Advanced analytics
- Platform-scale infrastructure

Future functionality must not be implemented early without approval.

---

# 14. Core Data Model

Important entities include:

```text
Organization
User
Organization Membership
Product
Buyer
Supplier

RFQ
RFQ Item
RFQ Supplier Invitation

Quotation
Quotation Item

Order
Order Item

Shipment
Shipment Event

Document
Document Version

Compliance Check
Compliance Requirement

HS Code

Risk Assessment
Risk Factor

Payment

CRM Contact
CRM Activity

Notification
Activity
Audit Event

File Reference
```

These are the canonical business concepts.

Do not create duplicate business entities without reviewing `DATA_MODEL.md`.

---

# 15. Organization Isolation

GlobalTrade.ai is organization-aware.

Organization-owned business data must remain isolated.

Backend authorization must enforce:

- Organization access
- User permissions
- Resource ownership

Frontend filtering is never the security boundary.

---

# 16. Workflow Principle

Business workflows must use explicit states.

Important workflows include:

- RFQ
- Quotation
- Order
- Shipment
- Compliance
- Payment

Invalid state transitions must be rejected by the backend.

---

# 17. Financial Principle

Financial and commercial calculations must be deterministic.

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

AI may explain financial information.

AI must not be the authoritative financial calculator.

---

# 18. Supplier Recommendation Principle

Supplier recommendations should use structured information.

Potential factors:

- Price
- Delivery time
- Certifications
- Reputation
- Country risk
- Trade history
- Financial stability

The numerical evaluation should be deterministic.

AI may explain the evaluation.

---

# 19. Quote Comparison Principle

Quote comparison must use structured quotation data.

Relevant factors may include:

- Unit price
- Freight
- Insurance
- Duty
- Tax
- Other charges
- Landed cost
- Delivery time
- Incoterm
- Payment terms

Backend calculations are authoritative.

AI provides explanation and interpretation.

---

# 20. Compliance Principle

Compliance is a hybrid workflow.

```text
Trade Data
 ↓
Authoritative Rules / Data
 ↓
Deterministic Evaluation
 ↓
Compliance Result
 ↓
AI Explanation
```

AI must not invent legal or regulatory requirements.

Where available, compliance information should have source information.

---

# 21. HS-Code Principle

HS-code assistance should provide classification assistance rather than pretend to provide unquestionable legal certainty.

Typical flow:

```text
Product Information
 ↓
Candidate HS Codes
 ↓
Relevant Knowledge
 ↓
Evidence / Confidence
 ↓
User Review
```

The system must distinguish between:

```text
AI Suggested
User Confirmed
Authoritative External Source
```

where applicable.

---

# 22. Document Principle

Trade documents should be generated primarily from validated structured application data.

```text
Structured Trade Data
 ↓
Template
 ↓
Validation
 ↓
Document
```

AI may assist with drafting, extraction and explanation.

AI must not silently invent critical transactional fields.

---

# 23. Integration Principle

External providers must remain behind integration boundaries.

Never spread provider-specific API logic through the business domain.

Never represent unavailable integrations as live integrations.

---

# 24. Security Principle

The project must maintain:

- Authentication
- Authorization
- Organization isolation
- Input validation
- Secure file access
- Secret management
- Auditability
- Secure logging

Never hardcode secrets.

---

# 25. Code Philosophy

Every line of code should have a reason to exist.

Prefer:

- Simple
- Explicit
- Readable
- Small
- Maintainable

Avoid:

- Premature abstractions
- Unnecessary dependencies
- Duplicate business logic
- Unnecessary files
- Unnecessary infrastructure
- Unnecessary AI agents
- Generic patterns without a demonstrated need

---

# 26. AI Coding Agent Behavior

AI coding agents must:

1. Read the project documentation before modifying code.
2. Inspect existing code before creating new code.
3. Follow the documented architecture.
4. Follow the documented data model.
5. Follow the AI specification.
6. Follow the design specification.
7. Follow the engineering rules.
8. Implement only approved tasks.
9. Verify changes before declaring completion.
10. Update documentation when required.

Agents must not invent requirements or silently change architecture.

---

# 27. Documentation Hierarchy

Use the project documentation as follows:

```text
PRD.md
    ↓
ARCHITECTURE.md
    ↓
DATA_MODEL.md
    ↓
AI_SPEC.md
    ↓
DESIGN.md
    ↓
RULES.md
    ↓
TASKS.md
```

Supporting memory and decisions:

```text
MEMORY.md
DECISIONS.md
```

When documents conflict, stop and resolve the conflict rather than silently choosing one.

---

# 28. Final Project Memory

GlobalTrade.ai should remain:

**Simple in architecture.**

**Strong in engineering.**

**Deterministic where correctness matters.**

**AI-assisted where intelligence adds value.**

**Transparent where uncertainty exists.**

**Modular where boundaries matter.**

**Scalable only when real requirements justify scale.**
```