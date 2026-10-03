```md
# GlobalTrade.ai — AI Specification

## 1. Document Purpose

This document defines how Artificial Intelligence is used within GlobalTrade.ai.

It is the source of truth for:

- AI responsibilities
- AI boundaries
- LLM usage
- RAG
- Embeddings
- Semantic search
- Tool calling
- Structured outputs
- AI-assisted workflows
- AI validation
- AI confidence
- Source attribution
- AI security
- AI failure handling
- AI observability

AI implementation must follow this document unless an explicit decision is recorded in `DECISIONS.md`.

---

# 2. AI Architecture Principle

GlobalTrade.ai follows:

**Deterministic Core + AI-Assisted Intelligence**

The system must use AI where language understanding, information extraction, semantic retrieval, reasoning assistance, summarization, drafting or recommendations provide meaningful value.

The system must use deterministic application logic where correctness, consistency, authorization, calculations or state management are required.

---

# 3. What AI Is Responsible For

AI may assist with:

- Natural-language understanding
- Information extraction
- Semantic search
- Summarization
- Recommendation assistance
- Draft generation
- Classification assistance
- Document understanding
- Trade information explanation
- Context-aware assistance
- Conversational interaction

---

# 4. What AI Is Not Responsible For

AI must not be the authoritative source for:

- Authentication
- Authorization
- Organization isolation
- Financial calculations
- Transaction totals
- Database integrity
- Workflow state transitions
- Permission decisions
- Audit records
- Direct unrestricted database access
- Unrestricted external actions

AI must not silently make consequential business decisions on behalf of the user.

---

# 5. AI High-Level Flow

```text
User
  ↓
Application Context
  ↓
AI Orchestrator
  ↓
Task / Intent Understanding
  ↓
Retrieve Data / Call Tools / Use RAG
  ↓
Structured AI Result
  ↓
Validation
  ↓
Business Logic
  ↓
User-Facing Result
```

AI output must pass through the appropriate application validation before being used by the system.

---

# 6. AI Orchestrator

The AI Orchestrator is responsible for coordinating AI operations.

It should:

- Receive the user's request
- Determine the required AI task
- Gather relevant context
- Select approved tools when required
- Retrieve relevant knowledge when required
- Call the configured LLM
- Validate structured outputs
- Return a safe application-level result

The orchestrator must not become a replacement for domain business logic.

---

# 7. Model Strategy

The application must use an OpenAI-compatible or otherwise explicitly supported model interface so that the model provider can be changed without rewriting the application.

The AI layer should isolate:

- Model provider
- Model name
- API configuration
- Prompt construction
- Response parsing
- Usage information

Business modules must not depend directly on a specific model provider.

---

# 8. AI Task Types

AI operations should be represented by explicit task types where practical.

Examples:

```text
TRADE_ASSISTANT
RFQ_GENERATION
QUOTE_ANALYSIS
SUPPLIER_RECOMMENDATION
BUYER_RECOMMENDATION
PRODUCT_DESCRIPTION
DOCUMENT_ASSISTANCE
HS_CODE_ASSISTANCE
COMPLIANCE_EXPLANATION
RISK_EXPLANATION
NEGOTIATION_ASSISTANCE
KNOWLEDGE_QUERY
```

Do not create an independent AI agent for every task.

Use normal deterministic application logic when AI is unnecessary.

---

# 9. Structured Outputs

When AI output will be consumed by application logic, use structured output.

Examples:

- RFQ extraction
- Product information extraction
- Quote extraction
- HS-code candidates
- Risk factors
- Compliance findings
- Document fields
- Supplier attributes

Conceptually:

```text
User Input
   ↓
LLM
   ↓
Structured Output
   ↓
Schema Validation
   ↓
Application Logic
```

Do not depend on parsing arbitrary natural-language text when structured data is required.

---

# 10. AI Tool Calling

AI may use explicitly defined application tools.

Potential tools include:

```text
search_products
search_suppliers
search_buyers
get_product
get_supplier
get_buyer
get_rfq
get_quotations
compare_quotes
calculate_landed_cost
get_order
get_shipment
check_compliance
search_knowledge
generate_document
```

Tools must have:

- Explicit input schemas
- Explicit output schemas
- Permission checks
- Organization isolation
- Validation
- Controlled side effects

The LLM must never receive unrestricted access to application data or infrastructure.

---

# 11. Read vs Write Tools

AI tools should distinguish between read operations and write operations.

## Read Operations

Examples:

```text
search_suppliers
get_rfq
get_quotes
get_order
get_shipment
search_knowledge
```

These may be used automatically when the user has the required access.

## Write Operations

Examples:

```text
create_rfq
create_order
generate_document
send_rfq
record_payment
```

Write operations must require normal backend authorization and any necessary user confirmation.

AI must not bypass application permissions.

---

# 12. User Confirmation

Actions that create meaningful external or business consequences should require appropriate confirmation.

Examples:

- Sending an RFQ
- Finalizing an order
- Sending a negotiation message
- Submitting information to an external system
- Recording important financial actions

AI may prepare the action.

The application and user remain responsible for executing the consequential action.

---

# 13. RAG Architecture

Retrieval-Augmented Generation is used when AI needs relevant information from approved knowledge sources.

Flow:

```text
Knowledge Source
      ↓
Document Processing
      ↓
Text Extraction
      ↓
Chunking
      ↓
Embedding
      ↓
Vector Storage
      ↓
Semantic Retrieval
      ↓
Relevant Context
      ↓
LLM
      ↓
Answer
```

RAG should be used when the answer depends on information that should come from specific source material.

---

# 14. RAG Knowledge Sources

Potential knowledge sources include:

- Trade regulations
- Compliance information
- Internal company documents
- Product information
- Supplier information
- Buyer information
- Contracts
- Trade documents
- Approved market information
- Other approved trade knowledge

The source and trust level of knowledge should be preserved where practical.

---

# 15. Document Processing Pipeline

Documents used for AI processing should follow:

```text
Upload
  ↓
File Validation
  ↓
Object Storage
  ↓
Text Extraction / OCR when required
  ↓
Cleaning
  ↓
Chunking
  ↓
Metadata Attachment
  ↓
Embedding
  ↓
Vector Storage
```

Processing may run in a background worker for large or time-consuming files.

---

# 16. Chunking Principles

Document chunking should preserve meaningful context.

Chunks should not be unnecessarily small or unnecessarily large.

The implementation should consider:

- Document structure
- Headings
- Paragraph boundaries
- Tables where extractable
- Relevant metadata

Chunking configuration should remain simple and configurable.

---

# 17. Embeddings

Embeddings are derived representations used for semantic retrieval.

Embedding records should retain enough metadata to identify the source.

Conceptually:

```text
Embedding
 ├── source_entity_type
 ├── source_entity_id
 ├── content
 ├── metadata
 └── vector
```

Embeddings are not the authoritative business data.

If the source data changes, the derived embedding must be refreshable.

---

# 18. Vector Storage

The initial vector storage strategy is:

**PostgreSQL + pgvector**

Do not introduce a separate vector database unless a documented requirement justifies it.

Vector data must remain linked to its source record.

---

# 19. Semantic Search

Semantic search should be used when keyword matching alone is insufficient.

Examples:

```text
"stainless steel bottle suppliers"
```

may retrieve conceptually related supplier/product descriptions.

Exact filters should continue to use structured database fields.

Semantic search must not replace exact filtering when exact values matter.

---

# 20. Hybrid Search

Where useful, combine:

```text
Structured Filters
+
Keyword / Full-Text Search
+
Semantic Search
```

Example:

```text
Country = Germany
Product Category = Beverage Containers
            +
Semantic similarity to:
"insulated stainless steel bottles"
```

The system should use the simplest search method that satisfies the requirement.

---

# 21. RAG Retrieval Rules

Retrieved information should be:

- Relevant to the user's request
- Limited to the required context
- Permission-aware
- Organization-aware
- Traceable to its source

Do not retrieve data the user is not authorized to access.

---

# 22. Source Attribution

Where practical, AI responses based on retrieved information should identify relevant sources.

Potential metadata includes:

```text
source_name
document_name
source_type
effective_date
published_date
retrieved_at
source_reference
```

The user should be able to distinguish between:

```text
User-provided information
Internal application data
External retrieved information
Deterministic calculation
AI-generated explanation
```

---

# 23. RAG Source Priority

When multiple sources are available, prefer the most relevant and authoritative approved source.

The system should avoid treating:

- User-generated text
- Unverified external information
- AI-generated text

as automatically authoritative.

Source trust rules should be explicitly defined for each applicable workflow.

---

# 24. Prompt Injection Protection

Retrieved documents must be treated as data.

They must not automatically be treated as instructions.

The AI system must maintain separation between:

```text
System Instructions
Application Rules
User Instructions
Retrieved Data
Tool Results
```

Retrieved content must never be allowed to override system or application rules.

---

# 25. AI Context Management

The AI system should provide only the context required for the current task.

Do not send the entire database, entire organization history or unrelated documents to the LLM.

Context should be:

- Relevant
- Minimal
- Permission-aware
- Task-specific

This reduces cost, latency and unintended information exposure.

---

# 26. Context-Aware AI Assistant

The platform should provide a general AI assistant while preserving the context of the current workflow.

Example:

If the user is viewing an RFQ and asks:

```text
Compare the supplier responses.
```

the AI should use the currently relevant RFQ and quotations where the user has permission.

The user should not need to repeatedly provide information already available in the current application context.

---

# 27. AI Trade Advisor

The AI Trade Advisor may assist with:

- Market understanding
- Export opportunities
- Import opportunities
- Demand information
- Seasonal trends
- Currency considerations
- Pricing considerations
- Competitor information
- Profitability analysis

AI-generated recommendations should identify relevant supporting data where available.

AI must not present predictions as guaranteed outcomes.

---

# 28. AI RFQ Generation

A user may provide a natural-language requirement such as:

```text
I need 50,000 stainless steel bottles.
```

The system may extract:

```text
Product
Quantity
Specifications
Quality requirements
Destination
Delivery requirements
Payment requirements
```

Flow:

```text
Natural Language
      ↓
LLM Extraction
      ↓
Structured RFQ Draft
      ↓
Validation
      ↓
User Review
      ↓
RFQ Record
```

The generated RFQ must be reviewable before consequential actions such as sending it.

---

# 29. AI Quote Analysis

AI may assist with:

- Identifying meaningful differences
- Summarizing supplier terms
- Highlighting unusual conditions
- Explaining commercial trade-offs
- Preparing a comparison summary

The AI must not calculate financial totals itself when deterministic calculation is possible.

Flow:

```text
Quotation Data
      ↓
Backend Normalization
      ↓
Deterministic Calculations
      ↓
AI Analysis
      ↓
Explanation
```

---

# 30. Supplier Recommendation

Supplier recommendation should use structured supplier information.

Potential factors include:

- Price
- Delivery time
- Certifications
- Reputation
- Country risk
- Trade history
- Financial stability

Flow:

```text
Supplier Data
      ↓
Structured Features
      ↓
Deterministic Scoring
      ↓
AI Explanation
```

AI may assist with interpretation and explanation but must not invent supplier attributes.

Missing data must remain distinguishable from good performance.

---

# 31. Buyer Recommendation

Buyer recommendations may use:

- Product relevance
- Market relevance
- Buyer profile
- Country
- Industry
- Historical interactions
- Other approved structured information

The system must distinguish sourced information from AI-generated suggestions.

---

# 32. HS-Code Assistance

HS-code assistance should use:

```text
Product Description
+
Product Attributes
+
Optional Product Image
      ↓
Candidate Generation
      ↓
Relevant Knowledge Retrieval
      ↓
Classification Assistance
      ↓
Evidence / Confidence
      ↓
User Review
```

The system should support multiple candidates where appropriate.

An AI-generated classification must not automatically become a confirmed classification without the required confirmation.

The system must clearly distinguish:

```text
AI Suggested
User Confirmed
Authoritative External Source
```

where applicable.

---

# 33. Compliance AI

AI may assist with:

- Explaining compliance requirements
- Summarizing regulations
- Extracting requirements from documents
- Explaining why a rule may apply
- Preparing compliance checklists

Compliance decisions should use deterministic rules and authoritative data where available.

AI must not invent legal requirements.

---

# 34. Risk AI

AI may assist with:

- Risk explanation
- Risk summarization
- Identifying relevant evidence
- Explaining risk factors
- Highlighting unusual information

Risk scores should be based on structured factors and deterministic logic where applicable.

AI must not create unsupported risk scores.

---

# 35. AI Negotiation Assistant

The AI Negotiation Assistant may provide:

- Counter-offer drafts
- Discount strategy suggestions
- Email drafts
- Meeting preparation
- Supplier response summaries

Generated negotiation content must be clearly presented as a draft or recommendation.

The application must not automatically send consequential communications without the appropriate user action or authorization.

---

# 36. AI Document Assistance

AI may assist with:

- Extracting document fields
- Summarizing documents
- Drafting text
- Identifying missing information
- Explaining document contents

Final documents must be generated from validated structured data and approved templates where applicable.

AI must not silently invent critical transactional fields.

---

# 37. AI Contract Assistance

AI may assist with:

- Clause extraction
- Clause summarization
- Identifying notable terms
- Highlighting potentially important provisions
- Comparing contract language

Contract analysis should be presented as assistance rather than definitive legal advice.

---

# 38. AI Fraud Assistance

AI may assist in identifying potentially unusual supplier or transaction information.

Potential inputs include:

- Supplier information
- Transaction history
- Documents
- Inconsistencies
- Risk indicators

AI-generated fraud indicators must be treated as signals requiring appropriate review, not as definitive proof of fraud.

---

# 39. AI Market Intelligence

AI may summarize and interpret approved market data.

Potential outputs include:

- Price trends
- Commodity trends
- Currency information
- Shipping information
- Competitor information
- Demand information

The underlying data source and freshness should be identifiable where possible.

AI must not present unsupported forecasts as guaranteed outcomes.

---

# 40. Deterministic Financial Logic

The following must remain deterministic:

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

Conceptually:

```text
Landed Cost =
Product Cost
+ Freight
+ Insurance
+ Duty
+ Taxes
+ Other Applicable Charges
```

The backend calculates these values.

AI may explain the result.

---

# 41. Deterministic Workflow Logic

AI must not decide whether a record can move between business states.

Example:

```text
RFQ
DRAFT
  ↓
SENT
  ↓
RESPONSES_RECEIVED
```

The backend determines whether a transition is valid.

The AI may explain workflow status but does not control workflow state.

---

# 42. AI Permissions

AI operations must execute within the permissions of the current user.

The AI must not gain additional privileges merely because the user asked the assistant to perform an action.

Example:

```text
User lacks permission to view payment data
        ↓
AI must not retrieve payment data
```

---

# 43. Organization Isolation

AI retrieval and tool execution must respect organization boundaries.

The AI must not retrieve information belonging to another organization unless the platform explicitly supports and authorizes that relationship.

---

# 44. AI Data Privacy

Only the minimum necessary information should be sent to external AI providers.

Sensitive information should not be transmitted unnecessarily.

The system should avoid logging:

- Secrets
- Passwords
- Authentication tokens
- Sensitive document contents
- Unnecessary personal information

AI provider data-handling requirements must be considered before production use.

---

# 45. AI Failure Handling

The application must handle:

- Model unavailable
- API timeout
- Rate limit
- Invalid AI output
- Malformed structured output
- Retrieval failure
- Tool failure
- Missing context
- Low-confidence result

Failure must not corrupt business data.

Where possible, the user should receive a clear fallback message.

---

# 46. AI Fallback Behavior

When AI is unavailable:

```text
AI unavailable
      ↓
Continue normal deterministic workflow where possible
```

Examples:

- A user should still be able to create an RFQ manually.
- A user should still be able to compare quotes using deterministic calculations.
- A user should still be able to view orders.
- A user should still be able to access stored documents.

AI should enhance the platform, not make core functionality unusable.

---

# 47. AI Confidence

Confidence indicators may be used where meaningful.

Examples:

- HS-code assistance
- Entity extraction
- Classification
- Recommendation assistance

Confidence must not be treated as mathematical certainty.

A high confidence value does not replace appropriate validation or user confirmation.

---

# 48. AI Provenance

Where an AI result depends materially on external or internal information, the system should preserve or expose the relevant provenance.

Possible provenance:

```text
Source Document
Source Record
External Provider
Calculation
Retrieved Knowledge
AI Generation
```

The user should not be forced to treat generated text as authoritative when the underlying source is available.

---

# 49. AI Result Storage

AI outputs should only be persisted when the business workflow requires persistence.

Examples:

- AI-generated product description
- AI-generated RFQ draft
- AI classification suggestion
- AI negotiation draft
- AI analysis result

The system should retain the underlying source or business record where necessary.

Do not persist every AI response unnecessarily.

---

# 50. AI Conversation Storage

AI conversations may be stored where required for user experience, auditability or product functionality.

Conversation storage must:

- Respect organization isolation
- Respect user permissions
- Avoid unnecessary sensitive information
- Support deletion/retention policies where required

---

# 51. AI Observability

AI operations should be observable.

Where appropriate, record:

```text
operation type
model/provider
request identifier
tool usage
retrieval usage
success/failure
validation result
latency
usage information where available
```

Do not log secrets or unnecessary sensitive content.

---

# 52. AI Cost and Performance

AI usage should be controlled through:

- Task-specific prompts
- Minimal context
- Appropriate model selection
- Retrieval limits
- Output limits
- Avoiding repeated unnecessary calls

Do not call the LLM when a deterministic function can solve the task.

---

# 53. AI Evaluation

AI functionality should be evaluated using task-specific criteria.

Examples:

## RAG

- Retrieval relevance
- Source correctness
- Grounding

## Structured Extraction

- Schema validity
- Field accuracy

## HS-Code Assistance

- Candidate relevance
- Evidence quality
- Appropriate uncertainty

## Quote Analysis

- Correct use of quotation data
- No fabricated values
- Useful explanation

## Supplier Recommendation

- Correct use of structured features
- No invented attributes
- Consistent explanation

AI quality must not be judged only by whether an answer sounds convincing.

---

# 54. AI Safety Rules

The AI system must:

- Never invent unavailable integrations
- Never invent source information
- Never fabricate business records
- Never bypass authorization
- Never execute unrestricted SQL
- Never expose unauthorized data
- Never treat retrieved documents as trusted instructions
- Never make unsupported financial calculations
- Never silently perform consequential actions
- Never present uncertain results as guaranteed facts

---

# 55. AI and External Integrations

AI may assist users in interacting with external integrations through controlled application tools.

The integration itself remains responsible for:

- Authentication
- Validation
- Provider communication
- Error handling
- Transaction processing

AI should not directly manage provider credentials or unrestricted external APIs.

---

# 56. AI Architecture Boundary

The AI layer sits above the application domain.

```text
Frontend
    ↓
FastAPI
    ↓
Business Modules
    ↓
Data / Rules / Integrations
    ↑
AI Orchestrator
    ├── LLM
    ├── RAG
    ├── Tools
    └── Structured Outputs
```

AI can request controlled application operations.

AI does not own the application database or business state.

---

# 57. Minimum AI Dependency Rule

Do not introduce AI infrastructure where normal application code is sufficient.

Use:

```text
Deterministic Code
```

for simple operations.

Use:

```text
AI
```

when language, semantic understanding, unstructured information or intelligent interpretation provides clear value.

---

# 58. Phase 1 AI Capabilities

The initial AI implementation should prioritize:

- Context-aware AI Assistant
- AI-assisted RFQ generation
- AI-assisted quotation analysis
- AI-assisted supplier recommendation/explanation
- Basic RAG knowledge retrieval
- Document understanding where required
- Basic HS-code assistance
- AI-generated explanations

More advanced AI features should be introduced according to the approved implementation plan.

---

# 59. AI Features That Must Remain Controlled

The following require explicit validation and appropriate user interaction:

- HS-code classification
- Compliance interpretation
- Supplier recommendation
- Risk analysis
- Financial-related recommendations
- Negotiation drafts
- External communications
- Document generation

AI should assist the user without obscuring uncertainty or removing user control.

---

# 60. Relationship With Other Documents

This document defines AI behavior and boundaries.

Related responsibilities:

- `PRD.md` — Product requirements
- `ARCHITECTURE.md` — Technical architecture
- `DATA_MODEL.md` — Canonical business data
- `DESIGN.md` — User experience
- `RULES.md` — Coding and implementation rules
- `TASKS.md` — Implementation sequence
- `MEMORY.md` — Compact project context
- `DECISIONS.md` — Important decisions

The implementation must not introduce unrestricted AI behavior that conflicts with this document.

---

# 61. Final AI Principle

GlobalTrade.ai must follow:

**AI assists.**

**The application validates.**

**Rules enforce.**

**The database stores.**

**The user remains in control.**

The objective is to use AI where it meaningfully reduces complexity for the user without making the system itself unpredictable, unauditable or dependent on unsupported model behavior.
```