```md
# GlobalTrade.ai — Design Specification

## 1. Document Purpose

This document defines the visual and user experience principles for GlobalTrade.ai.

It is the source of truth for:

- Product visual direction
- Information hierarchy
- Navigation
- Layout
- Core UI patterns
- Trade Workspace experience
- Dashboard experience
- AI interaction patterns
- Forms
- Tables
- Status indicators
- Notifications
- Loading states
- Empty states
- Error states
- Responsive behavior
- Accessibility expectations

The interface must follow this document unless an explicit design decision is recorded in `DECISIONS.md`.

---

# 2. Design Philosophy

GlobalTrade.ai is enterprise software for international trade.

The design must communicate:

- Trust
- Clarity
- Professionalism
- Control
- Simplicity
- Operational visibility

The interface should feel modern and premium without becoming visually distracting.

The product must prioritize usability and information clarity over decorative visuals.

---

# 3. Visual Direction

The visual language should be:

- Clean
- Minimal
- Professional
- Modern
- Calm
- Data-focused
- Consistent

Avoid:

- Excessive gradients
- Excessive glassmorphism
- Decorative animations
- Oversized illustrations
- Excessive shadows
- Visually noisy dashboards
- Unnecessary AI-themed visual effects
- UI patterns that make the product look like a generic AI landing page

---

# 4. Design Priority

The visual hierarchy should follow:

```text
User Goal
    ↓
Important Information
    ↓
Required Action
    ↓
Supporting Information
    ↓
Optional Details
```

Users should understand what they are looking at and what they can do next without having to interpret the interface.

---

# 5. Application Layout

The primary application layout should contain:

```text
┌──────────────────────────────────────────────────────┐
│ Top Bar                                              │
├──────────────┬───────────────────────────────────────┤
│              │                                       │
│  Sidebar     │          Main Content                 │
│              │                                       │
│ Navigation   │                                       │
│              │                                       │
└──────────────┴───────────────────────────────────────┘
```

The sidebar should provide access to major product areas.

The main content area should contain the active workflow.

The layout must work well across desktop and smaller screens.

---

# 6. Primary Navigation

Navigation should remain focused on the major business areas.

Recommended structure:

```text
Dashboard

Trade
  RFQs
  Quotations
  Orders
  Shipments

Marketplace
  Buyers
  Suppliers
  Products

Compliance
  Compliance Checks
  HS Codes
  Certificates

Documents

Finance

Risk

Analytics

AI Assistant

Settings
```

Do not expose every internal feature as a top-level navigation item.

Related functionality should be grouped together.

---

# 7. Navigation Principles

The navigation should:

- Clearly indicate the current location
- Use consistent labels
- Avoid unnecessary nesting
- Preserve context when moving between related records
- Make frequently used actions easy to access

The interface should avoid forcing users to navigate through multiple unrelated screens to complete one trade workflow.

---

# 8. Global Search

The application should provide a global search interface.

It should be capable of finding relevant records such as:

- Products
- Buyers
- Suppliers
- RFQs
- Quotations
- Orders
- Shipments
- Documents

The search experience may support natural-language queries where semantic search is available.

The interface should make it clear when search results are:

- Exact matches
- Filtered results
- Semantic matches

---

# 9. Command Search

A command/search interface may be available through:

```text
⌘ K
```

or the platform equivalent.

It should allow users to quickly locate:

- Records
- Pages
- Actions

Examples:

```text
RFQ-1024
Acme Industries
Stainless steel bottle suppliers
Show delayed shipments
```

The command interface must remain simple and focused.

---

# 10. Dashboard

The dashboard should be operational rather than decorative.

It should answer three primary questions:

## What needs attention?

Examples:

- Quotations awaiting review
- Missing documents
- Compliance issues
- Pending supplier verification
- Delayed shipments
- Pending payments

## What is happening?

Examples:

- Active RFQs
- Pending orders
- Shipments in transit
- Open compliance checks
- Pending payments

## What can I do?

Examples:

- Create RFQ
- Add Product
- Find Supplier
- Compare Quotes
- Create Order
- Generate Document
- Check Compliance

---

# 11. Dashboard Layout

A typical dashboard should follow:

```text
Page Header
    ↓
Key Metrics
    ↓
Attention / Action Items
    ↓
Active Trade Activity
    ↓
Recent Activity
```

Charts should only be displayed when they communicate useful business information.

Do not add charts merely to make the dashboard look more advanced.

---

# 12. Trade Workspace

The Trade Workspace is the central operational experience.

A Trade Workspace represents one trade operation and connects the relevant information.

Example:

```text
Trade #TR-2026-00124

India → Germany

Stainless Steel Bottles
50,000 Units

Status: Quotation Comparison
```

The workspace should provide access to:

```text
Overview
Product
Buyer
Supplier
RFQ
Quotes
Negotiation
Order
Documents
Compliance
Shipment
Payments
Risk
Activity
```

Users should be able to understand the current trade without navigating through unrelated modules.

---

# 13. Trade Workspace Header

The workspace header should clearly show:

- Trade identifier
- Current status
- Main parties
- Product
- Quantity
- Origin
- Destination
- Important dates
- Primary action

The most relevant action should be visually prominent.

---

# 14. Trade Timeline

Important trade activity should be visible as a timeline.

Example:

```text
RFQ Created
     ↓
RFQ Sent
     ↓
Quotation Received
     ↓
Quotation Comparison
     ↓
Negotiation
     ↓
Supplier Selected
     ↓
Order Confirmed
     ↓
Documents
     ↓
Compliance
     ↓
Shipment
     ↓
Delivery
     ↓
Payment
```

Timeline entries must represent real application events.

The timeline should distinguish:

- Completed
- Current
- Upcoming
- Blocked
- Failed

---

# 15. Status Design

Statuses should be immediately understandable.

Use:

- Text
- Consistent status badges
- Icons where helpful
- Appropriate visual distinction

Do not rely on color alone to communicate a status.

Examples:

```text
Draft
Sent
Under Review
Negotiation
Awarded
Confirmed
In Transit
Delivered
Pending
Action Required
Restricted
```

---

# 16. Page Structure

Most application pages should follow a consistent structure:

```text
Page Title
Supporting Description
Primary Action

Search / Filters

Main Content

Secondary Actions
```

The exact structure may change according to the workflow, but consistency should be maintained.

---

# 17. Tables

Tables are important for enterprise workflows.

Use tables for:

- Suppliers
- Buyers
- RFQs
- Quotations
- Orders
- Shipments
- Documents
- Payments

Tables should support where appropriate:

- Sorting
- Filtering
- Pagination
- Search
- Row actions
- Status visibility

Avoid showing too many columns by default.

Important information should be visible first.

Additional information can be accessed through details views or expandable areas.

---

# 18. Quote Comparison UI

Quote comparison should be one of the clearest data-heavy interfaces.

Example:

```text
                  Supplier A    Supplier B    Supplier C

Unit Price          ₹500          ₹480          ₹520
Freight               ₹60           ₹95           ₹50
Insurance             ₹10           ₹12            ₹8
Duty                  ₹45           ₹45           ₹45
Tax                   ₹20           ₹20           ₹20
---------------------------------------------------------
Estimated Landed
Cost                 ₹635          ₹652          ₹643

Delivery              18 days       27 days       15 days
Incoterm              FOB           CIF           FOB
Payment Terms         30% Advance   LC            50% Advance
```

The UI should make important differences obvious.

The interface should distinguish:

- Actual supplied values
- Calculated values
- AI-generated observations

---

# 19. AI Explanation in Quote Comparison

AI insights should appear beside or below the structured comparison.

Example:

```text
AI Insight

Supplier C has the lowest estimated landed cost among
the available quotations and the shortest stated delivery
time.

Supplier B offers LC payment terms but has higher
estimated landed cost and longer stated delivery.
```

AI explanations must not replace the underlying numerical comparison.

The user must always be able to inspect the actual quotation data.

---

# 20. Forms

Forms should be:

- Clear
- Structured
- Consistent
- Easy to scan
- Divided into logical sections

Do not place excessive fields into one large form without grouping them.

Use meaningful sections such as:

```text
Basic Information
Product Details
Commercial Terms
Delivery
Documents
Additional Information
```

---

# 21. Form Validation

Validation should provide immediate and understandable feedback.

The interface should:

- Identify the field with the problem
- Explain what is wrong
- Preserve valid entered information
- Avoid unnecessary repeated errors

Backend validation remains authoritative.

---

# 22. Primary Actions

Every major page should have a clear primary action.

Examples:

```text
Create RFQ
Add Product
Create Order
Compare Quotes
Generate Document
Check Compliance
Create Shipment
```

Do not provide multiple visually dominant primary actions unless the workflow genuinely requires them.

---

# 23. Destructive Actions

Destructive actions should require clear confirmation.

Examples:

- Delete
- Cancel
- Remove
- Revoke
- Reject

The confirmation should explain the consequence where it matters.

Avoid unnecessary confirmation dialogs for reversible or low-risk actions.

---

# 24. AI Interaction Design

AI should appear naturally within workflows.

Do not make the entire application depend on a single large chatbot.

Examples:

```text
RFQ
[ Generate with AI ]

Quotes
[ Analyze Quotes ]

Product
[ Generate Description ]

Compliance
[ Explain Requirement ]

HS Code
[ Find Candidates ]

Documents
[ Assist with Document ]
```

AI actions should clearly communicate what the AI will do.

---

# 25. AI Assistant

The platform should provide a general AI Assistant.

The assistant should understand the current application context when permitted.

Example:

```text
User:
Compare the supplier responses.

Assistant:
I found three responses for RFQ-1024.
```

The interface should clearly indicate when information is:

- Retrieved
- Calculated
- Generated
- Suggested

The assistant should not pretend to know information that is unavailable.

---

# 26. AI Result Presentation

AI-generated results should use appropriate UI structures rather than large blocks of text.

Use:

- Summaries
- Tables
- Lists
- Highlighted findings
- Citations/source information
- Confidence indicators where meaningful
- Action buttons

The UI should make generated information easy to verify.

---

# 27. AI Loading State

AI operations should provide clear feedback.

Examples:

```text
Analyzing quotations...
Finding relevant suppliers...
Checking trade knowledge...
Generating document...
```

Do not use vague loading messages such as:

```text
Thinking...
Magic happening...
```

The loading message should describe the operation.

---

# 28. AI Error State

When an AI operation fails, show a clear message.

Example:

```text
AI analysis is temporarily unavailable.

Your quotations are still available for manual review.

[Retry]
```

The user should be able to continue the underlying workflow where possible.

---

# 29. AI Confirmation State

When AI creates a draft or recommendation that requires user review, the interface should clearly indicate:

```text
AI Generated Draft
Review before using
```

The user should be able to:

```text
Accept
Edit
Regenerate
Cancel
```

where applicable.

---

# 30. Source and Evidence Display

When AI uses retrieved information, show relevant source information where practical.

Example:

```text
Source
EU Trade Regulation
Updated: 01 Sep 2026

Relevant information...
```

Users should not have to assume that generated information is authoritative.

---

# 31. Empty States

Empty states should explain:

1. What is missing.
2. Why it matters.
3. What the user can do next.

Example:

```text
No RFQs yet

Create your first Request for Quotation to start
collecting supplier responses.

[ Create RFQ ]
```

Avoid empty screens containing only:

```text
No data
```

---

# 32. Loading States

Use appropriate loading indicators.

Loading states should preserve layout where practical and avoid unnecessary screen flashing.

For tables, use skeleton rows or appropriate placeholders.

For page transitions, avoid excessive animations.

---

# 33. Error States

Error messages should be:

- Clear
- Specific
- Actionable

Example:

```text
Unable to load supplier information.

Please try again.

[ Retry ]
```

Technical stack traces must not be shown to normal users.

---

# 34. Permission States

When a user cannot perform an action because of permissions, the UI should clearly explain the limitation where appropriate.

Example:

```text
You do not have permission to modify payment information.
```

Frontend permission controls improve UX but do not replace backend authorization.

---

# 35. Notifications

Notifications should be actionable.

Example:

```text
Quotation awaiting review

Supplier ABC submitted a quotation
for RFQ-1024.

[ Review Quote ]
```

Notifications should connect to the affected workflow whenever practical.

---

# 36. Toasts

Use toast notifications for short-lived feedback.

Good examples:

```text
RFQ created successfully.
Document generated successfully.
Changes saved.
```

Do not use toasts for important information that users may need to review later.

---

# 37. Confirmation Dialogs

Use confirmation dialogs for actions that:

- Cannot easily be undone
- Have business consequences
- Require explicit user confirmation

Do not use confirmation dialogs for every ordinary action.

---

# 38. Detail Views

Clicking an important record should open a clear detail view.

For example:

```text
Supplier Detail

Overview
Verification
Products
Quotations
Trade History
Risk
Documents
Activity
```

The structure should prioritize the information most relevant to the current workflow.

---

# 39. Product Detail

Product pages should clearly present:

- Product name
- Description
- Images
- Specifications
- MOQ
- Packaging
- Pricing
- HS code
- Certificates
- Related RFQs
- Related orders

AI-generated content should be identified where applicable.

---

# 40. Supplier Detail

Supplier pages should present:

- Company information
- Location
- Supplier type
- Verification status
- Certifications
- Products
- Trade history where available
- Performance information where available
- Risk information
- Related RFQs
- Related quotations
- Activity

Do not display unsupported supplier information as fact.

---

# 41. Compliance UI

Compliance should prioritize clarity.

A compliance result may be represented as:

```text
Compliance Status

CLEAR
```

or:

```text
ACTION REQUIRED
```

or:

```text
RESTRICTED
```

The user should be able to see:

- What was checked
- What was found
- What action is required
- Relevant source information
- Effective date where available

---

# 42. Document UI

Documents should provide:

- Document type
- Status
- Version
- Date
- Source
- Related trade/order
- Preview/download action
- Generation status where applicable

Generated documents should remain clearly associated with the structured trade data used to create them.

---

# 43. Shipment UI

Shipment details should emphasize:

- Current status
- Origin
- Destination
- Carrier
- Tracking reference
- ETA
- Timeline
- Customs status
- Related documents
- Related order

A shipment timeline should be easy to scan.

---

# 44. Risk UI

Risk information should be understandable without requiring users to interpret complicated graphics.

Example:

```text
Trade Risk

72 / 100

Medium

Main Factors

Supplier Risk       Low
Country Risk        Medium
Payment Risk        High
Shipment Risk       Low
```

The UI should show the factors contributing to the assessment.

AI explanations should remain distinguishable from the underlying structured risk data.

---

# 45. Analytics UI

Analytics should focus on actionable business information.

Potential metrics:

```text
Export Revenue
Import Cost
Profit
Pending Orders
Supplier Performance
Country-wise Sales
Shipment Status
```

Charts should be used only when they help users understand trends, comparisons or changes.

---

# 46. Responsive Design

The application must support:

- Desktop
- Laptop
- Tablet
- Mobile-sized screens

The most important workflows must remain usable on smaller screens.

Large data tables may use:

- Horizontal scrolling
- Responsive column prioritization
- Detail drawers
- Mobile-specific presentations

Do not simply shrink desktop interfaces until they become unusable.

---

# 47. Accessibility

The interface should follow accessible design practices.

Requirements include:

- Keyboard navigation
- Visible focus states
- Semantic HTML
- Appropriate labels
- Form accessibility
- Sufficient text readability
- Non-color-only status communication
- Appropriate contrast
- Accessible interactive elements

Accessibility must be considered while components are created rather than added afterward.

---

# 48. Typography

Typography should prioritize readability.

Use a clear type hierarchy for:

```text
Page Titles
Section Titles
Body Text
Labels
Metadata
Status
Tables
AI Insights
```

Avoid excessive font sizes and unnecessary variations.

---

# 49. Spacing

Use a consistent spacing system throughout the product.

Spacing should create clear grouping between:

- Sections
- Cards
- Forms
- Tables
- Actions
- Supporting information

Do not use arbitrary spacing values throughout individual screens.

---

# 50. Cards

Cards should be used when they help group related information.

Good uses:

- KPI summaries
- Supplier summaries
- Risk summaries
- AI insights
- Important status information

Do not wrap every piece of content inside a card.

Tables and plain content areas are often better for dense operational information.

---

# 51. Color Usage

Color should communicate meaning rather than serve as decoration.

Use consistent semantic meanings for states such as:

```text
Success
Warning
Error
Informational
Neutral
```

Do not rely on color alone.

The exact color tokens should be defined in the frontend design system.

---

# 52. Icons

Icons should support understanding.

Use consistent iconography across the application.

Do not use icons merely for visual decoration.

Important actions should include accessible labels.

---

# 53. Motion and Animation

Animations should be subtle and purposeful.

Use motion for:

- State transitions
- Opening/closing panels
- Feedback
- Loading

Do not add continuous or distracting animations.

Core workflows should remain usable without depending on animation.

---

# 54. Design System

Reusable UI components should be created for recurring patterns.

Examples:

```text
Button
Input
Select
Textarea
Dialog
Dropdown
Tabs
Badge
Table
Pagination
Card
Tooltip
Toast
Drawer
Modal
Timeline
Status Indicator
Empty State
Loading State
Error State
```

Components should be reused where the interaction is genuinely shared.

Do not create generic abstractions for one-off UI.

---

# 55. Consistency Rules

The same interaction should look and behave consistently throughout the application.

For example:

- Create actions should use consistent placement.
- Status badges should use the same semantics.
- Tables should use consistent row interactions.
- Forms should use consistent validation behavior.
- AI actions should use consistent visual treatment.
- Errors should use consistent messaging patterns.

---

# 56. Information Density

GlobalTrade.ai handles complex operational data.

The interface should support information density without becoming cluttered.

Use:

- Clear hierarchy
- Compact metadata
- Tabs
- Sections
- Expandable content
- Progressive disclosure

Do not hide important information merely to make the interface look minimal.

---

# 57. Progressive Disclosure

Show the information needed for the current decision first.

Additional information should be accessible without overwhelming the primary workflow.

Example:

```text
Supplier Summary
      ↓
Key commercial information
      ↓
Risk summary
      ↓
Detailed supplier information
```

---

# 58. Design for Decision Making

Important interfaces should help users compare and act.

Examples:

```text
Quote Comparison
Supplier Comparison
Risk Assessment
Compliance Result
Shipment Status
Order Status
```

The UI should surface:

- Important differences
- Current status
- Required action
- Relevant evidence

without making the decision for the user.

---

# 59. Trust and Transparency

Users should be able to distinguish:

```text
Actual Data
Calculated Data
External Data
AI-Generated Data
```

The interface should avoid presenting all information with the same visual authority.

---

# 60. Phase 1 Design Priority

The initial design effort should focus on:

```text
Authentication
Dashboard
Company Profile

Products
Buyers
Suppliers

RFQs
Quotations
Quote Comparison

Orders
Documents
Compliance

AI Assistant
Trade Workspace
Activity / Timeline
Notifications
```

Other future modules should follow the same design system rather than introducing unrelated visual patterns.

---

# 61. Final Design Principle

GlobalTrade.ai should feel like:

**A professional global trade operating platform with intelligent assistance.**

It should not feel like:

**A chatbot wrapped around a collection of database screens.**

The interface should make complex trade operations feel understandable, organized and controlled while preserving access to the detail required by professional users.
```