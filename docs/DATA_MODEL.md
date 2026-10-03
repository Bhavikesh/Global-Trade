```md
# GlobalTrade.ai — Data Model

## 1. Document Purpose

This document defines the canonical business entities and relationships used by GlobalTrade.ai.

It is the source of truth for:

- Core business entities
- Entity relationships
- Organization ownership
- Business lifecycle states
- Required identifiers
- Important data integrity rules
- Audit relationships
- Document relationships

The database implementation must follow this model unless an explicit architectural or product decision changes it.

This document defines the business data model, not every physical database implementation detail.

---

# 2. Data Model Principles

## 2.1 One Canonical Business Concept

A business concept should have one canonical representation.

Do not create multiple independent representations of the same entity without a documented reason.

For example:

- One Product entity
- One Supplier entity
- One RFQ entity
- One Order entity

Related modules should reference these entities rather than duplicate them.

---

## 2.2 Organization Ownership

GlobalTrade.ai is organization-aware.

Business records that belong to a company must be associated with the correct organization.

The application must enforce organization-level data isolation.

A user must never be able to access another organization's business records unless an explicitly supported relationship grants that access.

---

## 2.3 Relationships Over Duplication

Prefer references between entities instead of duplicating full records.

For example:

An RFQ should reference a Product rather than copying the entire Product record into the RFQ.

However, transactional records may preserve historical values where necessary for auditability and historical accuracy.

---

## 2.4 Historical Data Must Remain Meaningful

Business records may need to preserve values that were valid when a transaction occurred.

For example:

- Quoted price
- Payment terms
- Incoterm
- Delivery estimate
- Tax-related values where applicable
- Document version
- Product information relevant to a transaction

Current master data must not accidentally rewrite historical transaction meaning.

---

# 3. Core Entity Map

The initial data model contains the following major entities:

```text
Organization
    |
    +-- User
    +-- Organization Membership
    +-- Product
    +-- Buyer
    +-- Supplier
    +-- RFQ
    +-- Quotation
    +-- Order
    +-- Shipment
    +-- Document
    +-- Compliance Check
    +-- Risk Assessment
    +-- Payment
    +-- CRM Activity
    +-- Notification
    +-- Audit Event
```

Trade relationships:

```text
Buyer
  |
  v
RFQ
  |
  +---- Product
  |
  +---- Supplier
          |
          v
      Quotation
          |
          v
        Order
          |
          v
      Shipment
          |
          v
       Payment
```

Supporting information:

```text
Product
  |
  +-- Documents / Certificates
  +-- Classification information

Order / Shipment
  |
  +-- Documents
  +-- Compliance Checks
  +-- Risk Assessments
  +-- Payments
  +-- Activity
```

---

# 4. Common Entity Fields

Business entities should generally contain:

```text
id
organization_id where applicable
created_at
updated_at
```

Where relevant, records may also contain:

```text
created_by
updated_by
status
```

The exact implementation should use appropriate database types and constraints.

Do not add every possible metadata field to every entity.

---

# 5. Organization

## Purpose

Represents a business or organization using GlobalTrade.ai.

## Core Information

Potential fields:

```text
id
legal_name
display_name
business_type
country
address
tax_identifier
vat_identifier
iec_number
website
contact_information
verification_status
created_at
updated_at
```

The exact regulatory identifiers depend on the organization's country.

## Relationships

```text
Organization
 ├── Users
 ├── Products
 ├── Buyers
 ├── Suppliers
 ├── RFQs
 ├── Quotations
 ├── Orders
 ├── Shipments
 ├── Documents
 ├── Compliance Checks
 ├── Risk Assessments
 ├── Payments
 ├── CRM Activities
 ├── Notifications
 └── Audit Events
```

---

# 6. User

## Purpose

Represents an authenticated platform user.

## Core Information

```text
id
identity_provider_id
name
email
phone
status
created_at
updated_at
```

Authentication credentials should not be stored in the application database if a managed identity provider is used.

## Relationships

A User may belong to one or more organizations through Organization Membership.

---

# 7. Organization Membership

## Purpose

Connects users to organizations.

## Core Information

```text
id
organization_id
user_id
role
status
created_at
updated_at
```

This entity is responsible for determining which organization(s) a user belongs to.

Permissions are derived from the user's role and applicable permission rules.

---

# 8. Role

Roles define what actions a user can perform.

Potential roles include:

```text
Organization Admin
Exporter
Importer
Buyer
Supplier
Operations Manager
Finance Manager
Compliance Officer
Logistics Manager
```

The actual permission implementation may use predefined roles and permissions rather than creating a complex custom authorization system in the initial version.

---

# 9. Product

## Purpose

Represents a product managed by an organization.

## Core Information

```text
id
organization_id
name
description
category
specifications
moq
packaging
pricing_information
hs_code
keywords
seo_description
international_description
status
created_at
updated_at
```

Product media and files should be represented through related records or file references rather than embedding binary files directly into the Product table.

## Relationships

```text
Product
 ├── Organization
 ├── Media / Files
 ├── Certificates / Documents
 ├── RFQ Items
 └── Order Items
```

---

# 10. Product Media / Files

## Purpose

Represents files associated with a product.

Potential file types include:

- Image
- Video
- 3D model
- Certificate
- Specification document

## Core Information

```text
id
product_id
document_id or file_reference
file_type
created_at
```

Binary file content belongs in object storage.

The database stores metadata and references.

---

# 11. Buyer

## Purpose

Represents a buyer or potential buyer.

## Core Information

```text
id
organization_id where applicable
company_name
contact_name
email
phone
country
address
website
industry
verification_status
notes
created_at
updated_at
```

The system may support buyer records that originate from external discovery sources.

External-source metadata should identify the source where available.

---

# 12. Supplier

## Purpose

Represents a supplier, manufacturer, factory, trading company or other sourcing entity.

## Core Information

```text
id
organization_id where applicable
company_name
contact_name
email
phone
country
address
website
supplier_type
verification_status
certifications
notes
created_at
updated_at
```

Potential supplier evaluation information includes:

- Price
- Reviews
- Certifications
- Delivery time
- Country risk
- Trade history
- Financial stability

These should be stored as structured data where available.

AI should not be treated as the authoritative source for supplier attributes.

---

# 13. RFQ

## Purpose

Represents a Request for Quotation.

## Core Information

```text
id
organization_id
buyer_id where applicable
title
description
destination_country
required_delivery_date
payment_terms
status
created_by
created_at
updated_at
```

Potential lifecycle:

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

The backend must control valid state transitions.

## Relationships

```text
RFQ
 ├── Organization
 ├── Buyer
 ├── RFQ Items
 ├── Invited Suppliers
 ├── Quotations
 ├── Documents where applicable
 ├── Activity
 └── Audit Events
```

---

# 14. RFQ Item

## Purpose

Represents a product requirement within an RFQ.

## Core Information

```text
id
rfq_id
product_id where applicable
product_name_snapshot where required
description
quantity
unit
quality_requirements
specifications
packaging_requirements
created_at
updated_at
```

Historical transaction information may be stored as a snapshot where necessary.

---

# 15. RFQ Supplier Invitation

## Purpose

Represents a supplier being invited to respond to an RFQ.

## Core Information

```text
id
rfq_id
supplier_id
invited_at
response_deadline
status
responded_at
```

Potential states:

```text
INVITED
VIEWED
RESPONDED
DECLINED
EXPIRED
```

---

# 16. Quotation

## Purpose

Represents a supplier response to an RFQ.

## Core Information

```text
id
rfq_id
supplier_id
currency
valid_until
payment_terms
incoterm
delivery_time
shipping_cost
insurance_cost
duty_amount
tax_amount
other_charges
total_amount
status
created_at
updated_at
```

The exact fields may evolve as quotation requirements become more detailed.

## Important Rule

Quotation totals and comparable commercial values must be calculated using deterministic backend logic.

The LLM must not be the calculation authority.

## Relationships

```text
Quotation
 ├── RFQ
 ├── Supplier
 ├── Quotation Items
 ├── Documents
 ├── Negotiation Activities
 └── Audit Events
```

---

# 17. Quotation Item

## Purpose

Represents individual product pricing within a quotation.

## Core Information

```text
id
quotation_id
rfq_item_id where applicable
product_id where applicable
description
quantity
unit_price
unit
subtotal
created_at
updated_at
```

Historical prices must remain unchanged when a quotation has been finalized.

---

# 18. Quote Comparison

## Purpose

Quote comparison is a business operation rather than necessarily a permanent standalone business entity.

Comparison may be generated from quotations using structured fields such as:

```text
Unit Price
Freight
Insurance
Duty
Tax
Other Charges
Estimated Landed Cost
Delivery Time
Incoterm
Payment Terms
```

The system may persist comparison results or calculate them dynamically depending on the implementation requirement.

Avoid creating a permanent `QuoteComparison` table unless the product requires historical comparison snapshots.

---

# 19. Order

## Purpose

Represents a confirmed commercial transaction.

## Core Information

```text
id
organization_id
buyer_id where applicable
supplier_id where applicable
rfq_id where applicable
quotation_id where applicable
order_number
currency
total_amount
status
order_date
expected_delivery_date
created_by
created_at
updated_at
```

Potential lifecycle:

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

The backend must enforce valid transitions.

## Relationships

```text
Order
 ├── Organization
 ├── Buyer
 ├── Supplier
 ├── RFQ
 ├── Quotation
 ├── Order Items
 ├── Documents
 ├── Compliance Checks
 ├── Shipment
 ├── Risk Assessments
 ├── Payments
 ├── Activity
 └── Audit Events
```

---

# 20. Order Item

## Purpose

Represents a product within an order.

## Core Information

```text
id
order_id
product_id where applicable
description
quantity
unit
unit_price
subtotal
created_at
updated_at
```

Transaction-specific information should be preserved where required.

---

# 21. Shipment

## Purpose

Represents the logistics movement associated with an order.

## Core Information

```text
id
order_id
shipment_reference
transport_mode
origin
destination
carrier
tracking_reference
estimated_delivery
actual_delivery
status
created_at
updated_at
```

Potential transport modes:

```text
AIR
SEA
RAIL
ROAD
COURIER
```

Potential lifecycle:

```text
BOOKED
PICKED_UP
IN_TRANSIT
CUSTOMS
CLEARED
DELIVERED
```

## Relationships

```text
Shipment
 ├── Order
 ├── Shipment Events
 ├── Documents
 ├── Compliance Checks
 ├── Risk Assessments
 └── Audit Events
```

---

# 22. Shipment Event

## Purpose

Represents a status or tracking event associated with a shipment.

## Core Information

```text
id
shipment_id
event_type
event_time
location
description
source
created_at
```

Examples:

```text
Picked Up
Departed Port
Arrived Port
Customs Submitted
Customs Cleared
Out for Delivery
Delivered
```

External tracking events must preserve their provider/source where available.

---

# 23. Document

## Purpose

Represents a trade document and its metadata.

Potential document types include:

```text
COMMERCIAL_INVOICE
PACKING_LIST
BILL_OF_LADING
CERTIFICATE_OF_ORIGIN
SHIPPING_BILL
EXPORT_DECLARATION
IMPORT_DECLARATION
INSPECTION_CERTIFICATE
INSURANCE_CERTIFICATE
PROFORMA_INVOICE
PURCHASE_ORDER
SALES_ORDER
EXPORT_LICENSE
IMPORT_LICENSE
CONTRACT
OTHER
```

## Core Information

```text
id
organization_id
document_type
document_number where applicable
title
file_reference
version
status
source_type
created_by
created_at
updated_at
```

Potential source types:

```text
UPLOADED
GENERATED
EXTERNAL
```

Binary file contents belong in object storage.

---

# 24. Document Version

Documents may require version history.

Potential fields:

```text
id
document_id
version_number
file_reference
created_by
created_at
```

Do not overwrite an important finalized document without preserving the required version history.

---

# 25. Compliance Check

## Purpose

Represents a compliance evaluation associated with a product, transaction, order or shipment.

## Core Information

```text
id
organization_id
product_id where applicable
order_id where applicable
shipment_id where applicable
hs_code where applicable
origin_country
destination_country
status
summary
checked_at
created_at
updated_at
```

Potential statuses:

```text
NOT_CHECKED
IN_REVIEW
CLEAR
ACTION_REQUIRED
RESTRICTED
```

Where the system has authoritative source information, the relevant source should be recorded.

---

# 26. Compliance Requirement

A compliance check may identify individual requirements.

Potential information:

```text
id
compliance_check_id
requirement_type
description
status
source_reference
effective_date
```

Examples:

- Import restriction
- Export restriction
- Certificate requirement
- Sanctions-related restriction
- Anti-dumping requirement
- Trade agreement requirement

Compliance logic should remain distinguishable from AI-generated explanations.

---

# 27. HS Code

## Purpose

Represents product classification information.

The system may store:

```text
id
product_id
code
description
country_or_tariff_system
source
confidence
confirmed_by_user
created_at
updated_at
```

AI-generated candidate classifications should not automatically become confirmed classifications.

The system should distinguish:

```text
AI Suggested
User Confirmed
Authoritative External Source
```

where applicable.

---

# 28. Risk Assessment

## Purpose

Represents a risk evaluation for a supplier, country, transaction or shipment.

## Core Information

```text
id
organization_id
supplier_id where applicable
order_id where applicable
shipment_id where applicable
overall_score
risk_level
summary
assessed_at
created_at
updated_at
```

Potential risk levels:

```text
LOW
MEDIUM
HIGH
```

The actual score should come from structured risk factors and deterministic scoring logic where applicable.

---

# 29. Risk Factor

## Purpose

Represents an individual contributor to a risk assessment.

Potential fields:

```text
id
risk_assessment_id
factor_type
score
severity
description
source
created_at
```

Potential factor types include:

```text
SUPPLIER_RISK
COUNTRY_RISK
POLITICAL_RISK
FINANCIAL_RISK
CURRENCY_RISK
SHIPMENT_RISK
```

---

# 30. Payment

## Purpose

Represents a payment obligation or payment event associated with a trade transaction.

## Core Information

```text
id
organization_id
order_id where applicable
amount
currency
payment_type
payment_terms
due_date
paid_at
status
reference
created_at
updated_at
```

Potential statuses:

```text
PENDING
PROCESSING
PAID
FAILED
CANCELLED
```

Actual movement of funds requires an authorized financial/payment integration.

---

# 31. CRM Contact

## Purpose

Represents an individual contact associated with a buyer, supplier or other business relationship.

Potential fields:

```text
id
organization_id
buyer_id where applicable
supplier_id where applicable
name
email
phone
designation
notes
created_at
updated_at
```

---

# 32. CRM Activity

## Purpose

Represents interactions related to buyers, suppliers and business relationships.

Examples:

- Meeting
- Call
- Email
- Follow-up
- Note

Potential fields:

```text
id
organization_id
buyer_id where applicable
supplier_id where applicable
contact_id where applicable
activity_type
subject
description
scheduled_at
completed_at
created_by
created_at
updated_at
```

---

# 33. Notification

## Purpose

Represents an actionable notification for a user.

Potential fields:

```text
id
organization_id
user_id
type
title
message
resource_type
resource_id
read_at
created_at
```

Notifications should reference the related record where practical.

Examples:

```text
Quotation awaiting review
Compliance issue detected
Shipment delayed
Payment pending
Document missing
```

---

# 34. Activity

## Purpose

Represents a user-visible business activity related to a trade workspace.

Examples:

```text
RFQ created
Quotation received
Supplier selected
Order created
Document generated
Compliance checked
Shipment updated
Payment recorded
```

Potential fields:

```text
id
organization_id
actor_user_id
entity_type
entity_id
activity_type
description
created_at
```

The Activity entity is intended for operational timeline/history presentation.

---

# 35. Audit Event

## Purpose

Represents an important auditable system action.

Potential fields:

```text
id
organization_id
actor_user_id
entity_type
entity_id
action
before_data where appropriate
after_data where appropriate
metadata
created_at
```

Audit data must be treated differently from ordinary user-facing activity.

Not every minor UI interaction needs an audit event.

Audit events should focus on meaningful business or security-sensitive changes.

---

# 36. File Reference

## Purpose

Represents metadata for an object stored in S3-compatible object storage.

Potential information:

```text
id
organization_id
storage_key
file_name
content_type
file_size
checksum where applicable
created_by
created_at
```

The database stores metadata.

The actual binary object is stored in object storage.

---

# 37. Trade Workspace

The Trade Workspace is primarily a product/workflow concept rather than necessarily a separate database entity.

A Trade Workspace groups related records such as:

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

If the implementation demonstrates that an explicit persistent Workspace entity is necessary, it may be introduced later.

Do not create a separate Workspace table merely for organizational aesthetics.

---

# 38. Entity Relationship Summary

The principal relationships are:

```text
Organization
    |
    +---- User
    |
    +---- Product
    |
    +---- Buyer
    |
    +---- Supplier
    |
    +---- RFQ
              |
              +---- RFQ Item
              |
              +---- Supplier Invitation
              |
              +---- Quotation
                        |
                        +---- Quotation Item
                        |
                        v
                     Order
                        |
                        +---- Order Item
                        |
                        +---- Shipment
                        |       |
                        |       +---- Shipment Event
                        |
                        +---- Documents
                        |
                        +---- Compliance
                        |
                        +---- Risk
                        |
                        +---- Payments
```

Supporting relationships:

```text
Product
  └── Product Files / Certificates

Buyer
  └── CRM Contacts / Activities

Supplier
  └── CRM Contacts / Activities

Documents
  └── Document Versions

Compliance
  └── Compliance Requirements

Risk Assessment
  └── Risk Factors

Organization
  └── Notifications

Important business records
  └── Audit Events
```

---

# 39. Data Ownership Rules

The following ownership principles apply.

## Organization-owned records

Examples:

- Products
- RFQs
- Orders
- Documents
- Payments
- Compliance checks
- Risk assessments
- CRM activities

These must be associated with an organization.

## External or shared records

Some buyer and supplier records may represent external businesses.

The implementation must clearly distinguish:

- An organization's own user/business identity
- An external buyer/supplier record
- A platform participant that has its own organization account

Do not assume that every Supplier or Buyer is the same thing as a User.

A company can exist as a Supplier without having a registered GlobalTrade.ai user account.

---

# 40. Historical Snapshot Rules

Transactional records may require snapshots of important master-data values.

Examples:

An RFQ may preserve:

```text
Product name at RFQ time
Product description at RFQ time
Required specifications at RFQ time
```

A quotation may preserve:

```text
Quoted price
Currency
Payment terms
Incoterm
Delivery commitment
```

An order may preserve the finalized commercial terms from the selected quotation.

This prevents later master-data edits from changing the historical meaning of completed transactions.

---

# 41. Status Rules

Statuses must be explicit and controlled.

The database should not accept arbitrary status strings when the allowed state is known.

Use application validation and database constraints where appropriate.

Invalid transitions must be rejected by backend logic.

---

# 42. Soft Delete Rules

Do not automatically use soft deletion on every entity.

Use soft deletion only where business requirements require historical retention or recovery.

Transactional records such as:

- Orders
- Payments
- Compliance records
- Audit records

must not be casually deleted.

Master records such as Products may support archival instead of deletion when appropriate.

---

# 43. Deletion and Referential Integrity

Before deleting a record, determine whether related historical records depend on it.

Prefer:

- Archiving
- Deactivation
- Status changes

over destructive deletion where historical business meaning would be lost.

Database foreign keys must protect important relationships.

---

# 44. Auditability Requirements

Important changes to the following should be auditable:

- RFQs
- Quotations
- Orders
- Payments
- Compliance records
- User permissions
- Important documents
- Other critical trade records

The audit record should identify:

```text
Who
What
When
Entity
Change
```

Where necessary, previous and new values should be preserved.

---

# 45. Data Source and Provenance

The system should distinguish data origin where it materially affects trust.

Potential source types:

```text
USER_PROVIDED
INTERNAL_DATABASE
EXTERNAL_PROVIDER
IMPORTED_FILE
AI_GENERATED
AI_DERIVED
```

Generated or AI-derived information should not automatically be treated as authoritative business data.

Where important, source metadata should be retained.

---

# 46. AI Data Storage

AI conversations, retrieval results and AI operations should not be mixed directly into core business entities.

AI-specific persistence should be defined in `AI_SPEC.md`.

Core business entities may store references to relevant AI-generated outputs only when the business workflow requires it.

Examples:

```text
AI-generated product description
AI-assisted classification suggestion
AI-generated RFQ draft
AI-generated negotiation draft
```

The original source data must remain identifiable where necessary.

---

# 47. Analytics Data

Initial analytics should be calculated from the canonical transactional data.

Do not create a separate analytics database during Phase 1 without a demonstrated requirement.

Examples:

```text
Export revenue
Import cost
Profit
Pending orders
Shipment status
Supplier performance
Country-wise sales
```

Analytics should use consistent definitions derived from the canonical data model.

---

# 48. Search Data

Search indexes and vectors are derived representations, not authoritative business records.

The authoritative record remains PostgreSQL.

If indexed/search data becomes stale, it must be possible to regenerate it from canonical records.

---

# 49. IDs and Identifiers

Every persisted entity should have a stable primary identifier.

Human-readable identifiers should be created separately where required.

Examples:

```text
Organization ID
RFQ Number
Order Number
Shipment Reference
Document Number
Payment Reference
```

Internal IDs and human-readable business identifiers should not be treated as the same concept.

---

# 50. Timestamps

Business records should maintain appropriate creation and update timestamps.

Where business events require explicit timing, store event timestamps separately.

Examples:

```text
created_at
updated_at
sent_at
responded_at
order_date
expected_delivery_date
actual_delivery_date
paid_at
```

Do not use `created_at` as a substitute for a meaningful business event time.

---

# 51. Database Integrity Principles

Use PostgreSQL features to protect the model.

Where appropriate:

- Foreign keys
- Unique constraints
- Check constraints
- Not-null constraints
- Indexes
- Transactions

Business-critical calculations should use appropriate numeric database types.

Money must not be represented using floating-point database fields when exact monetary arithmetic is required.

---

# 52. Indexing Principles

Indexes should be created based on actual query patterns.

Likely indexed fields include:

```text
organization_id
status
created_at
updated_at
foreign keys
business identifiers
frequently searched exact fields
```

Do not create indexes for every column.

Indexing should be justified by query behavior.

---

# 53. Vector Data Principles

Vector embeddings are derived data.

They should contain enough metadata to identify their source record.

Conceptually:

```text
Embedding
 ├── source_entity_type
 ├── source_entity_id
 ├── content
 ├── embedding
 └── metadata
```

The exact embedding implementation belongs to `AI_SPEC.md`.

If source content changes, its derived embedding must be refreshable.

---

# 54. Data Integrity Rules for AI

AI-generated information must not bypass normal database validation.

For example:

```text
AI-generated RFQ
      ↓
Structured Output
      ↓
Validation
      ↓
User / Workflow Confirmation
      ↓
Database
```

Not:

```text
LLM
 ↓
Direct Database Write
```

AI tools must operate through controlled application logic.

---

# 55. Phase 1 Canonical Entities

The initial implementation should prioritize these entities:

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

Not every optional field listed above must be implemented immediately.

Only fields required by the approved Phase 1 workflows should be added.

---

# 56. Entities That Should Not Be Prematurely Added

Do not create separate entities merely because they are mentioned as future possibilities.

Examples:

- Freight Marketplace Provider
- Customs Agency
- Bank
- Insurance Company
- Warehouse
- Driver
- Inspector
- Market Intelligence Dataset
- Trade Fair
- Government Portal
- ERP Connector
- Shipping Line

These may require dedicated models later when actual product functionality is implemented.

---

# 57. Data Model Evolution

The data model will evolve as product requirements become more concrete.

When a new entity is proposed:

1. Identify the business requirement.
2. Determine whether an existing entity already represents the concept.
3. Determine whether the new entity is actually persistent.
4. Identify its ownership.
5. Identify its relationships.
6. Determine lifecycle/state requirements.
7. Determine historical/audit requirements.
8. Add the entity only when justified.

Do not add tables simply to anticipate hypothetical future requirements.

---

# 58. Source Basis

The product requirements identify the need for entities and workflows around:

- Products
- Buyers
- Suppliers
- RFQs
- Quotations
- Orders
- Documents
- Compliance
- Shipments
- Payments
- Risk
- CRM
- Analytics

The end-to-end workflow connects these areas from company registration through analytics.

The exact relational data model in this document is the project's engineering interpretation of those requirements.

---

# 59. Relationship With Other Documents

This document defines the canonical business data model.

Related responsibilities:

- `PRD.md` — Product requirements
- `ARCHITECTURE.md` — Technical architecture
- `AI_SPEC.md` — AI-specific persistence and processing
- `DESIGN.md` — User-facing representation
- `RULES.md` — Implementation rules
- `TASKS.md` — Implementation sequence
- `MEMORY.md` — Compact project context
- `DECISIONS.md` — Significant model/architecture decisions

Implementation must not introduce duplicate business entities without reviewing this document.

---

# 60. Final Data Model Principle

The data model must remain:

**Relational where relationships matter.**

**Explicit where business state matters.**

**Historical where transaction accuracy matters.**

**Auditable where accountability matters.**

**Minimal where a separate entity provides no real value.**

The goal is a clean canonical model that supports the complete trade lifecycle without prematurely modeling every future capability.
```