```md
# GlobalTrade.ai — Engineering Rules

## 1. Document Purpose

This document defines the rules that must be followed when designing, implementing, modifying, testing and reviewing GlobalTrade.ai.

These rules exist to keep the codebase:

- Simple
- Clean
- Maintainable
- Secure
- Consistent
- Production-oriented
- Easy to understand

These rules apply to human developers and AI coding agents.

---

# 2. Source of Truth

The project documentation is authoritative.

Use:

- `PRD.md` for product requirements
- `ARCHITECTURE.md` for technical architecture
- `DATA_MODEL.md` for business data
- `AI_SPEC.md` for AI behavior and boundaries
- `DESIGN.md` for UI/UX
- `TASKS.md` for implementation scope
- `MEMORY.md` for compact project context
- `DECISIONS.md` for recorded decisions

Code must not silently contradict these documents.

---

# 3. No Unnecessary Code

Do not write code unless it solves a real requirement.

Before adding code, determine:

1. Is the functionality required?
2. Does existing code already solve it?
3. Can the requirement be solved more simply?
4. Is the added abstraction actually necessary?

Prefer the smallest correct implementation.

---

# 4. No Premature Abstraction

Do not create abstractions only because they appear in common enterprise codebases.

Avoid unnecessary:

- Base classes
- Interfaces
- Abstract factories
- Generic service layers
- Wrapper classes
- Utility layers
- Managers
- Providers
- Registries
- Frameworks
- Configuration systems

Create an abstraction only when it provides a clear and current benefit.

---

# 5. No Premature Infrastructure

Do not introduce new infrastructure without a demonstrated requirement.

Do not introduce:

- Microservices
- Kubernetes
- Kafka
- RabbitMQ
- MongoDB
- Elasticsearch/OpenSearch
- Redis
- Additional databases
- Additional message brokers
- Additional orchestration systems

unless the requirement is documented and the architecture is explicitly updated.

---

# 6. Reuse Before Creating

Before creating:

- A component
- A service
- A helper
- A hook
- A schema
- A validation rule
- A utility

inspect the existing codebase and reuse existing functionality when appropriate.

Do not create duplicate implementations of the same concept.

---

# 7. Keep Responsibilities Clear

Each module should have one clear responsibility.

Business logic belongs in the backend domain layer.

UI logic belongs in the frontend.

Persistence belongs in the data-access layer.

AI orchestration belongs in the AI layer.

External provider logic belongs behind integration boundaries.

Do not mix unrelated responsibilities in the same module.

---

# 8. Backend Is Authoritative

Never rely on frontend logic for:

- Authorization
- Organization isolation
- Financial calculations
- State transitions
- Critical validation
- Business rules

Frontend validation improves user experience.

Backend validation is authoritative.

---

# 9. Organization Isolation

Every organization-owned operation must verify organization access.

A request must never be able to access or modify another organization's data through:

- IDs
- Query parameters
- Request bodies
- AI tools
- Search
- File references
- Background jobs

Do not rely on frontend filtering for tenant isolation.

---

# 10. Authorization

Every protected backend operation must verify that the current user is allowed to perform it.

Permission checks must happen before sensitive reads or writes.

Do not assume that hiding a button provides security.

---

# 11. Input Validation

Validate all external input.

This includes:

- API requests
- File uploads
- Query parameters
- Form data
- External provider responses
- AI-generated structured data

Do not assume input is valid because it originated from another application component.

---

# 12. Database Integrity

Use the database to protect data integrity where appropriate.

Prefer:

- Foreign keys
- Unique constraints
- Not-null constraints
- Check constraints
- Transactions
- Appropriate indexes

Do not rely only on application code when PostgreSQL can enforce the rule.

---

# 13. Financial Data

Financial values must be handled deterministically.

Do not use floating-point arithmetic for money where exact monetary calculations are required.

Do not allow an LLM to determine authoritative:

- Totals
- Subtotals
- Taxes
- Freight calculations
- Landed cost
- Profit
- Margin
- Payment amounts

The backend must perform these calculations.

---

# 14. Workflow State

Business state transitions must be explicit and controlled.

Do not allow arbitrary status changes.

For example:

```text
RFQ
DRAFT
  ↓
SENT
  ↓
RESPONSES_RECEIVED
```

An invalid transition must be rejected by the backend.

Do not duplicate workflow transition rules across multiple parts of the application.

---

# 15. Historical Data

Do not allow changes to master data to unintentionally alter historical transactions.

Preserve relevant transaction-time values when required.

Examples:

- Quoted prices
- Payment terms
- Incoterms
- Delivery commitments
- Product information
- Finalized commercial terms

---

# 16. Deletion

Do not delete important transactional records casually.

Prefer:

- Archive
- Deactivate
- Cancel
- Close

when historical information must remain available.

Audit records must not be casually deleted.

---

# 17. API Rules

Use consistent:

- URL structure
- HTTP methods
- Status codes
- Request schemas
- Response schemas
- Error responses
- Pagination
- Filtering
- Sorting

Do not create multiple ways of performing the same API operation without a clear reason.

---

# 18. API Error Handling

Errors must be:

- Consistent
- Understandable
- Structured

Do not expose:

- Stack traces
- Internal secrets
- Database errors
- Provider credentials
- Sensitive implementation details

to normal users.

Technical details should be available through appropriate server-side logs.

---

# 19. Frontend Rules

The frontend must remain focused on:

- Presentation
- Interaction
- Client-side user experience
- Displaying server state

Do not duplicate backend business logic in frontend components.

Do not create unnecessary global state.

Use local state when local state is sufficient.

---

# 20. UI Consistency

Use the existing design system before creating new UI patterns.

Reuse established:

- Buttons
- Inputs
- Tables
- Dialogs
- Badges
- Forms
- Tabs
- Drawers
- Notifications
- Loading states
- Empty states
- Error states

Do not create a new visual pattern for an interaction that already exists.

---

# 21. Responsive Design

New UI must remain usable across supported screen sizes.

Do not design desktop-only interfaces for core workflows.

Large data tables must have an intentional responsive strategy.

---

# 22. Accessibility

Interactive UI must provide:

- Keyboard accessibility
- Visible focus states
- Semantic elements
- Accessible labels
- Clear validation messages
- Non-color-only status communication

Accessibility must be considered during implementation.

---

# 23. Loading, Empty and Error States

Every data-driven feature must account for:

- Loading
- Empty
- Success
- Error
- Permission denied where applicable

Do not implement only the successful state.

---

# 24. AI Rules

AI must operate within the boundaries defined in `AI_SPEC.md`.

AI must not:

- Bypass authorization
- Access unrestricted data
- Execute arbitrary SQL
- Invent business records
- Invent external information
- Fabricate integrations
- Perform unrestricted external actions
- Silently change consequential business data
- Replace deterministic calculations
- Replace backend workflow rules

---

# 25. AI Write Operations

AI-generated writes must pass through normal application logic.

Use:

```text
AI
 ↓
Structured Result
 ↓
Validation
 ↓
Authorization
 ↓
Business Logic
 ↓
Database
```

Never:

```text
AI
 ↓
Direct Database Write
```

Consequential actions must require the appropriate user confirmation or authorization.

---

# 26. RAG Rules

Retrieved content must be treated as data.

Do not treat retrieved documents as trusted instructions.

RAG retrieval must respect:

- Organization boundaries
- User permissions
- Source restrictions
- Relevant context

Do not send unnecessary data to the model.

---

# 27. AI Output Validation

Whenever AI output is consumed by application logic:

1. Use a defined schema.
2. Validate the output.
3. Reject invalid results.
4. Never assume the model is correct.

Natural-language output must not be used as a substitute for structured validation.

---

# 28. AI Uncertainty

Do not hide uncertainty.

When an AI result is uncertain or incomplete, the UI and workflow should communicate that appropriately.

Do not convert uncertain AI output into authoritative business data without the required validation or confirmation.

---

# 29. No Fake Data

Never present fake data as real production data.

If mock data is required:

- Label it clearly.
- Keep it isolated.
- Do not mix it silently with production data.

If an external integration is unavailable, show that the integration is unavailable.

---

# 30. No Fake Integrations

Do not create an interface that claims:

- Live shipment tracking
- Live customs status
- Live bank status
- Live freight rates
- Live market data

unless the corresponding real provider is connected and verified.

Mock providers may be used for development and testing when clearly identified.

---

# 31. Secrets

Never commit or hardcode:

- API keys
- Passwords
- Tokens
- Private keys
- Database credentials
- AI provider credentials
- Encryption secrets

Use environment configuration locally and appropriate secret management in production.

---

# 32. File Uploads

Uploaded files must be validated.

Consider:

- File type
- File size
- Access permissions
- Storage path
- Processing state

Binary files belong in object storage.

Database records should store metadata and references.

---

# 33. External Integrations

External provider-specific code must remain isolated.

Do not spread provider-specific API calls throughout the business domain.

Use a clear integration boundary.

External failures must not corrupt internal business transactions.

---

# 34. Background Jobs

Use background processing only when the operation is actually long-running or asynchronous.

Examples:

- OCR
- Document processing
- Embedding generation
- Large imports
- AI document analysis
- External synchronization

Do not move simple operations into background jobs without a reason.

Background jobs should be:

- Retryable where appropriate
- Observable
- Safe against unintended duplication
- Explicit about failure

---

# 35. Idempotency

Operations that may be retried must not create unintended duplicates.

Consider idempotency for:

- External submissions
- Payment operations
- Notifications
- Document generation
- Background jobs

Use an explicit strategy only where the operation requires it.

---

# 36. Logging

Use structured logs for meaningful server-side events.

Logs should help answer:

- What happened?
- Where did it happen?
- Which request caused it?
- Which operation failed?
- Is it retryable?

Do not log:

- Passwords
- Secrets
- Tokens
- Unnecessary sensitive information

---

# 37. Audit Logging

Important business changes must be auditable.

Examples:

- RFQ changes
- Quote changes
- Order changes
- Payment changes
- Compliance changes
- Permission changes
- Important document changes

Do not create audit records for every minor UI interaction.

---

# 38. Testing

New functionality must include appropriate tests.

At minimum, test important:

- Business rules
- Calculations
- State transitions
- Validation
- Authorization
- Critical API behavior

Do not add tests that simply duplicate implementation details without protecting useful behavior.

---

# 39. AI Testing

AI features should be tested according to their purpose.

Examples:

### Structured extraction

Verify:

- Valid schema
- Correct field extraction
- Invalid output handling

### RAG

Verify:

- Relevant retrieval
- Source grounding
- Permission boundaries

### Recommendations

Verify:

- Correct use of structured data
- No fabricated attributes
- Consistent explanations

### Quote analysis

Verify:

- Actual quotation data is used
- No fabricated values
- Deterministic calculations remain correct

---

# 40. Dependency Rules

Before adding a dependency:

1. Check whether the requirement can be solved with existing dependencies.
2. Check whether the standard library or existing framework is sufficient.
3. Consider maintenance and security implications.
4. Add the dependency only when it provides meaningful value.

Do not add libraries for trivial functionality.

---

# 41. File and Folder Rules

Do not create files merely to satisfy a pattern.

A module does not need every possible file type.

For example, do not automatically create:

```text
service.py
repository.py
manager.py
factory.py
interface.py
adapter.py
utils.py
```

for every feature.

Create only the files that improve the actual implementation.

---

# 42. Naming

Use clear, descriptive names.

Avoid:

- Single-letter business variable names
- Ambiguous names
- Generic names such as `data`, `thing`, `manager`, `helper` when a precise name exists

Names should communicate intent.

---

# 43. Comments

Write comments only when they explain:

- Why something is done
- A non-obvious constraint
- A business rule
- A security consideration
- A non-obvious technical decision

Do not comment obvious code.

Do not write comments simply to increase apparent documentation.

---

# 44. Code Duplication

Do not copy business logic between modules.

If the same real business rule is needed in multiple places, identify the correct shared location.

Do not immediately create a generic abstraction.

First understand the actual shared responsibility.

---

# 45. Configuration

Configuration should be centralized and explicit.

Do not scatter configuration values throughout the codebase.

Environment-specific values must not require source-code modification.

---

# 46. Database Queries

Write queries for actual use cases.

Avoid:

- Loading unnecessary columns
- Loading large datasets without pagination
- N+1 query patterns
- Repeated identical queries when avoidable

Do not optimize prematurely without evidence.

---

# 47. Pagination

Use pagination for potentially large collections.

Do not load unbounded lists into memory.

The API and UI should use consistent pagination behavior.

---

# 48. Transaction Boundaries

Use database transactions when multiple related changes must succeed or fail together.

Do not create partial business state.

Example:

```text
Create Order
+
Create Order Items
+
Update Related State
+
Create Audit Event
```

should be handled transactionally where required.

---

# 49. Documentation Synchronization

When a meaningful implementation change affects:

- Requirements
- Architecture
- Data model
- AI behavior
- Design
- Project decisions

update the appropriate documentation.

Do not allow implementation and documentation to permanently diverge.

---

# 50. Decision Control

If implementation reveals that an existing architectural decision is insufficient:

1. Identify the problem.
2. Propose the smallest viable change.
3. Update the affected documentation.
4. Record the decision in `DECISIONS.md`.
5. Implement the approved change.

Do not silently change architecture.

---

# 51. Scope Control

Do not implement future features simply because they are mentioned in the broader product vision.

Implement only the current approved tasks in `TASKS.md`.

Do not expand a task unnecessarily.

---

# 52. Refactoring Rules

Refactor when it improves:

- Correctness
- Readability
- Maintainability
- Reusability with proven need
- Performance with evidence
- Security

Do not refactor working code merely to introduce a preferred pattern.

Avoid large unrelated refactors while implementing a focused feature.

---

# 53. Error Prevention

Before declaring a task complete, verify:

- The application starts
- The feature works
- Relevant tests pass
- Validation works
- Error cases are handled
- Authorization works
- Existing functionality still works
- No unnecessary dependencies were added
- Documentation is updated where required

---

# 54. AI Coding Agent Rules

AI coding agents must:

1. Read the relevant project documentation before modifying code.
2. Inspect existing code before creating new code.
3. Reuse existing functionality when appropriate.
4. Follow `ARCHITECTURE.md`.
5. Follow `DATA_MODEL.md`.
6. Follow `AI_SPEC.md`.
7. Follow `DESIGN.md`.
8. Follow these rules.
9. Implement only the approved task scope.
10. Verify changes before declaring completion.

AI coding agents must not:

- Invent requirements
- Invent architecture
- Rewrite unrelated code
- Add unnecessary dependencies
- Introduce premature infrastructure
- Create fake integrations
- Mark unverified work as complete

---

# 55. Change Discipline

Make focused changes.

When implementing a task:

- Modify only the necessary files.
- Avoid unrelated formatting changes.
- Avoid unrelated refactoring.
- Preserve existing working behavior.
- Keep the change easy to review.

---

# 56. Simplicity Test

Before finalizing an implementation, ask:

```text
Can this be simpler?
Can an existing component solve this?
Can an existing module handle this?
Can fewer files solve this?
Can fewer dependencies solve this?
Can deterministic code solve this instead of AI?
Can the same result be achieved with less complexity?
```

If the answer is yes, prefer the simpler solution.

---

# 57. Production Quality Rule

Minimal code does not mean incomplete engineering.

The project must still provide appropriate:

- Security
- Validation
- Authorization
- Error handling
- Testing
- Logging
- Data integrity
- Auditability
- Maintainability

Remove unnecessary complexity, not necessary engineering.

---

# 58. Final Engineering Principle

GlobalTrade.ai must be built according to this rule:

**Do the simplest thing that correctly solves the requirement.**

**Do not build for hypothetical problems.**

**Do not add technology because it looks impressive.**

**Do not use AI where normal code is better.**

**Do not sacrifice correctness for minimal code.**

**Do not sacrifice simplicity for imagined scale.**

**Every line of code should have a reason to exist.**
```