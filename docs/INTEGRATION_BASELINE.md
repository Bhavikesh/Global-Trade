# GlobalTrade.ai — Integration Baseline

> **Critical Notice**: All feature developers must follow this Integration Baseline as the shared integration contract. Feature-specific requirements may extend the contract where necessary, but developers must not independently redefine shared routing, authorization, tenant isolation, response, error, frontend API, or migration conventions. Any conflict must be raised before implementation.

---

## 1. Purpose

GlobalTrade.ai is developed as an industrial, modular monolith by a multi-developer team:
- **Member 1**: Product Management (Catalog, Specifications, Files, Search)
- **Member 2**: Buyer & Supplier Management (CRM Contacts, Verification, Details)
- **Member 3**: RFQ & Quotations (Workflows, Document References)
- **Team Lead / Integration**: Core Identity, Organizations, Cross-Cutting Architecture

The purpose of this Integration Baseline is to eliminate architectural drift and merge friction. All developers share the exact same backend conventions, authentication/authorization helpers, tenant-isolation query rules, API routing patterns, frontend BFF bridge, and database migration coordination.

---

## 2. Authentication

All protected backend endpoints **must** use the canonical authentication dependency:
`backend/app/core/auth/dependencies.py`

### Rules
1. **Always use `get_current_user`**:
   ```python
   from fastapi import Depends
   from app.core.auth.dependencies import get_current_user
   from app.models.user import User

   @router.get("/example")
   def example_endpoint(current_user: User = Depends(get_current_user)):
       ...
   ```
2. **Do NOT manually decode JWTs**: The `get_current_user` dependency automatically calls `verify_jwt` (Auth0 RS256 token verification) and resolves or provisions the local application `User` ORM record.
3. **Do NOT create custom authentication dependencies**: Every feature route must resolve identity through the shared `User` entity.

---

## 3. Authorization & RBAC

All organization membership and role-based access control **must** use:
`backend/app/core/auth/permissions.py`

GlobalTrade.ai uses PostgreSQL `organization_memberships` as the **sole source of truth** for roles and access permissions (DEC-038). Auth0 roles/organizations are not used.

### Canonical Enforcement Helpers

#### READ Operations (Any Active Member)
Use `get_membership_or_403`:
```python
from app.core.auth.permissions import get_membership_or_403

# Signature: get_membership_or_403(organization_id, user, db)
membership = get_membership_or_403(organization_id, current_user, db)
```
- Rejects with `403 Forbidden` (`{"detail": "Access denied: you are not a member of this organization."}`) if the user is not an active member.

#### MUTATION Operations (CREATE, UPDATE, DELETE)
Use `require_organization_membership`:
```python
from app.core.auth.permissions import require_organization_membership

# Signature: require_organization_membership(organization_id, user, db, allowed_roles=None)
membership = require_organization_membership(organization_id, current_user, db)
```
- Rejects with `403 Forbidden` if the user is not an active member or if their role is not included in `allowed_roles`.

#### STRICT ADMIN Operations
Use `require_admin`:
```python
from app.core.auth.permissions import require_admin

# Signature: require_admin(organization_id, user, db)
membership = require_admin(organization_id, current_user, db)
```

### Prohibitions
- Do **NOT** write manual ad-hoc SQL queries to check membership.
- Do **NOT** create feature-specific authorization helpers.

---

## 4. Organization / Tenant Isolation

GlobalTrade.ai is strictly multi-tenant. Every tenant-owned database record belongs to an `Organization`.

### 1. Database Query Scoping
**Every tenant-scoped query must include `organization_id`.** Never query a tenant-owned resource by primary key alone.

- **Single Record Lookup / Mutation**:
  ```python
  resource = (
      db.query(MyModel)
      .filter_by(id=item_id, organization_id=organization_id)
      .first()
  )
  if resource is None:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Resource not found.",
      )
  ```
- **Collection Queries**:
  ```python
  resources = (
      db.query(MyModel)
      .filter_by(organization_id=organization_id)
      .all()
  )
  ```

### 2. Tenant Context Rules
- **Creation**: `organization_id` must come strictly from the authenticated/authorized route path or context. Never accept `organization_id` from client request bodies.
- **Update**: `organization_id` is immutable.
- **Delete**: Deletions must be scoped by `organization_id`.

### 3. Cross-Tenant Isolation Semantics & Enumeration Resistance
- **Case 1 (Non-member)**: User is not an active member of the route's organization $\rightarrow$ **`403 Forbidden`**.
- **Case 2 (Foreign resource)**: User is an active member of Organization A, but requests a resource ID belonging to Organization B $\rightarrow$ **`404 Not Found`**.
- **Case 3 (Non-existent resource)**: Resource ID does not exist anywhere $\rightarrow$ **`404 Not Found`**.

> **Enumeration Resistance**: Case 2 and Case 3 must return the exact same HTTP 404 response (`{"detail": "<Resource> not found."}`). A caller must never be able to discover whether a resource exists in another organization.

---

## 5. API Routing

### Base Mount Architecture
All API routers are mounted in `backend/app/main.py` under the global API prefix:
```python
app.include_router(feature_router, prefix=f"{settings.API_V1_PREFIX}/v1")
```
Because `settings.API_V1_PREFIX = "/api"`, the public base path for all v1 routes is:
```
/api/v1
```

### Router Prefix Conventions
There are two established patterns in the codebase for scoping by organization:

1. **Path-Scoped Organization Pattern (Existing Buyer/Supplier)**:
   ```python
   router = APIRouter(
       prefix="/organizations/{organization_id}/buyers",
       tags=["Buyers"],
   )
   ```
   - Collection / Create: `POST|GET /api/v1/organizations/{organization_id}/buyers`
   - Detail / Update / Delete: `GET|PATCH|DELETE /api/v1/organizations/{organization_id}/buyers/{buyer_id}`

2. **Query-Scoped Organization Pattern (Baseline Convention for Top-Level Catalogues)**:
   ```python
   router = APIRouter(
       prefix="/products",
       tags=["Products"],
   )
   ```
   - Collection: `GET /api/v1/products?organization_id=<uuid>` (or `org_id=<uuid>`)
   - Detail: `GET|PATCH|DELETE /api/v1/products/{product_id}`

> **Authoritative Route Rule**: Existing implemented Buyer/Supplier routes are already fully implemented and authoritative. They **MUST NOT** be rewritten merely to match a generalized convention. For NEW modules, before introducing a different organization route pattern, compare against `docs/INTEGRATION_BASELINE.md`, `docs/ARCHITECTURE.md`, `docs/RULES.md`, and `docs/TASKS.md`, and coordinate with the team.

---

## 6. HTTP Status Codes

All backend endpoints must adhere to standard REST HTTP status codes:

| Scenario | Status Code | FastAPI Constant |
| :--- | :--- | :--- |
| Successful Read (GET) | `200 OK` | `status.HTTP_200_OK` |
| Successful Update (PATCH) | `200 OK` | `status.HTTP_200_OK` |
| Successful Creation (POST) | `201 Created` | `status.HTTP_201_CREATED` |
| Successful Deletion (DELETE) | `204 No Content` | `status.HTTP_204_NO_CONTENT` |
| Bad Request (Malformed IDs) | `400 Bad Request` | `status.HTTP_400_BAD_REQUEST` |
| Unauthenticated / Missing Token | `401 Unauthorized` | `status.HTTP_401_UNAUTHORIZED` |
| Forbidden / Non-member Access | `403 Forbidden` | `status.HTTP_403_FORBIDDEN` |
| Not Found / Cross-Tenant Lookup | `404 Not Found` | `status.HTTP_404_NOT_FOUND` |
| Pydantic Schema Validation Error | `422 Unprocessable Entity` | Automatic FastAPI validation |

Do not invent custom status codes per feature.

---

## 7. Response Structure

### Direct Model Serialization (No Global Envelopes)
GlobalTrade.ai does **NOT** use a global response wrapper envelope (e.g. `{"data": ...}`, `{"success": true}`).
Endpoints directly return the Pydantic schema or a list of schemas:

- **Single Resource**:
  ```python
  @router.get("/{id}", response_model=ProductRead)
  def get_product(...) -> ProductRead:
      return product
  ```
  *Response*:
  ```json
  {
    "id": "e839e083-d66a-4959-b1be-17ad226756e2",
    "organization_id": "71a9bbf6-b518-472e-848e-6701f2214309",
    "name": "Precision CNC Milling Machine",
    "created_at": "2026-10-07T12:00:00Z",
    "updated_at": "2026-10-07T12:00:00Z"
  }
  ```

- **Collection**:
  ```python
  @router.get("", response_model=list[ProductRead])
  def list_products(...) -> list[ProductRead]:
      return products
  ```
  *Response*:
  ```json
  [
    {
      "id": "e839e083-d66a-4959-b1be-17ad226756e2",
      "name": "Precision CNC Milling Machine"
    }
  ]
  ```

*(Note: Feature-specific contracts, such as the Buyer/Supplier Phase B4 pagination contract, return `{items, total, limit, offset}` to satisfy explicit domain pagination requirements. See Section 20).*

---

## 8. Error Contract

Error responses follow the standard FastAPI error format:
```json
{
  "detail": "Resource not found."
}
```
Validation errors (`422`) follow the standard FastAPI error list:
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```
Do **not** wrap errors in custom envelopes like `{"error": {"code": 404, "message": "..."}}`.

---

## 9. Pydantic Schema Conventions

Use **Pydantic v2**. Follow the established schema structure in `backend/app/schemas/`:

### Standard Naming
- Creation: `<Resource>Create`
- Partial Update: `<Resource>Update`
- Serialization / Read: `<Resource>Read`

### ORM Configuration
Every read schema must enable ORM attribute mode:
```python
class ProductRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

### Field Validation
Use `@field_validator` with `@classmethod` for string trimming, uppercase formatting (e.g. ISO country codes), and normalization:
```python
@field_validator("name")
@classmethod
def validate_name(cls, v: str) -> str:
    trimmed = v.strip()
    if not trimmed:
        raise ValueError("Name cannot be empty.")
    return trimmed
```

### Partial Updates (PATCH)
All fields in `<Resource>Update` must default to `None`. In route handlers, unpack using `exclude_unset=True`:
```python
update_data = body.model_dump(exclude_unset=True)
for field, value in update_data.items():
    setattr(entity, field, value)
```
Never reset omitted fields to `None`.

---

## 10. Server-Controlled Fields

The following fields are strictly **server-controlled** and must **never** be supplied or mutated by clients:
1. `id`: Generated automatically by database default (`uuid.uuid4()`).
2. `organization_id`: Injected strictly from route parameter or authorized context.
3. `created_at`: Generated automatically via `server_default=func.now()`.
4. `updated_at`: Generated automatically via `server_default=func.now()`, `onupdate=func.now()`.

---

## 11. Frontend BFF (Backend-For-Frontend)

The browser **must never call FastAPI directly**.
All frontend requests route through the Next.js server-side BFF proxy:
`frontend/src/app/api/backend/[...path]/route.ts`

### Why the BFF Exists
- Manages secure server-side Auth0 access tokens via `auth0.getAccessToken()`.
- Automatically attaches the `Authorization: Bearer <access_token>` header.
- Keeps client-side code isolated from direct backend API credentials and URLs.

---

## 12. Frontend API Client

All frontend API calls **must** use `fetchWithAuth<T>()` from `frontend/src/lib/api.ts`:

```typescript
import { fetchWithAuth } from "@/lib/api";

// Example: Fetching products for active organization
const products = await fetchWithAuth<Product[]>(
  `/v1/products?organization_id=${orgId}`
);
```

### Prohibitions
- Do **NOT** use raw `fetch()` directly against backend ports (e.g. `http://localhost:8001`).
- Do **NOT** introduce Axios or other third-party HTTP clients.

---

## 13. Frontend Page Lifecycle

Interactive pages must follow this standard pattern:

1. **Directive**: Start with `"use client";`.
2. **Auth Guard**: Use `const { user, isLoading } = useUser();`.
   - Render a loading spinner or skeleton while `isLoading === true`.
   - Render a sign-in prompt if `!user`.
3. **Organization Context**: Read active organization context explicitly (e.g. from route parameter or user profile). Do not invent global Redux stores.
4. **Error Handling**: Store errors in component state and display clear inline alerts.
5. **Controlled Forms**: Use controlled inputs, disable submit buttons while mutations are in-flight, and display field-level validation feedback.
6. **UI Components**: Use existing Tailwind styles, Lucide icons, and components from `frontend/src/components/ui/` (e.g. `button.tsx`).

---

## 14. Shared Files

The following files are **shared integration hotspots**. Do not independently refactor or redesign them without team coordination:

- `backend/app/core/auth/jwt.py`
- `backend/app/core/auth/dependencies.py`
- `backend/app/core/auth/permissions.py`
- `backend/app/db/session.py`
- `backend/app/models/user.py`
- `backend/app/models/organization.py`
- `backend/app/models/organization_membership.py`
- `frontend/src/app/api/backend/[...path]/route.ts`
- `frontend/src/lib/auth0.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/components/navbar.tsx`
- `backend/app/main.py`
- `backend/app/models/__init__.py`
- `backend/alembic/versions/`

---

## 15. Database / Model Conventions

All SQLAlchemy models must adhere to:
- Inherit from `Base` (`app.db.session.Base`).
- Explicit `__tablename__` using plural `snake_case` (e.g. `"products"`, `"buyers"`, `"suppliers"`).
- UUID primary keys: `id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`.
- Tenant foreign key: `organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)`.
- Timestamps:
  ```python
  created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
  ```
- Bidirectional relationships using `back_populates` and `cascade="all, delete-orphan"`.
- Every model must be registered in `backend/app/models/__init__.py`.

---

## 16. Alembic Migration Coordination

### Current Authoritative Migration Chain
The actual current Alembic chain in `backend/alembic/versions/` is authoritative:
```
0001_init_vector
       │
0002_phase1_identity
       │
0003_buyer_supplier_contacts (HEAD)
```

### Migration Rules
1. **Current Alembic Head is Authoritative**: Do NOT rewrite migration history simply to match older planning documents. The Buyer/Supplier module is already migrated under `0003_buyer_supplier_contacts`.
2. **No Blind Historical Numbers**: Future migrations (e.g. for Product Management or RFQ) **MUST NOT** blindly use historical or planned numbers (such as an older plan's `0003_products`). They **MUST** inspect the actual Alembic head at the time of branching and coordinate `down_revision` across branches.
3. **Next Migration**: Any new migration branched from the current state (e.g. `0004_products`) must declare:
   ```python
   down_revision = "0003_buyer_supplier_contacts"
   ```
4. **Never Create Multiple Heads**: Always run `alembic heads` before committing a migration to guarantee a strictly linear sequence.

---

## 17. Product Management Ownership (Member 1)

Member 1 owns the Product Management module (T1.9–T1.12):

### Backend Responsibilities
- Model: `backend/app/models/product.py` (`Product`, `ProductFile`)
- Schemas: `backend/app/schemas/product.py` (`ProductCreate`, `ProductUpdate`, `ProductRead`)
- Router: `backend/app/api/v1/products.py`
- Tests: `backend/tests/test_products.py`

### Frontend Responsibilities
- Pages: `frontend/src/app/products/page.tsx`, `frontend/src/app/products/[id]/page.tsx`
- Components: `frontend/src/components/products/`

Member 1 must follow this baseline and must **not** invent competing auth dependencies, response envelopes, or pagination schemas.

---

## 18. Buyer/Supplier Ownership (Member 2)

Member 2 owns Buyer & Supplier Management (T1.13–T1.17):

### Implemented Files
- Models: `backend/app/models/buyer.py`, `backend/app/models/supplier.py`, `backend/app/models/contact.py`
- Schemas: `backend/app/schemas/buyer.py`, `backend/app/schemas/supplier.py`, `backend/app/schemas/contact.py`
- Routes: `backend/app/api/v1/buyers.py`, `backend/app/api/v1/suppliers.py`
- Tests:
  - `backend/tests/test_buyer_supplier_models.py`
  - `backend/tests/test_buyer_supplier_schemas.py`
  - `backend/tests/test_buyer_supplier_crud.py`
  - `backend/tests/test_buyer_supplier_isolation.py`
  - `backend/tests/test_buyer_supplier_search.py`

---

## 19. RFQ / Quotation Ownership (Member 3)

Member 3 owns RFQ & Quotation workflows (Phase 2):

### Expected Ownership
- Models: `backend/app/models/rfq.py`, `backend/app/models/quotation.py`
- Schemas: `backend/app/schemas/rfq.py`, `backend/app/schemas/quotation.py`
- Routes: `backend/app/api/v1/rfqs.py`, `backend/app/api/v1/quotations.py`
- Frontend: `frontend/src/app/rfqs/`

### Integration Requirement
RFQs and Quotations must reference canonical `Buyer`, `Supplier`, and `Product` models by foreign key UUIDs. Do **not** duplicate buyer or supplier tables.

---

## 20. Search / Filtering / Pagination

### Pagination Contract
1. **No Universal Envelope**: GlobalTrade.ai does **NOT** have a universal global response wrapper envelope (e.g. `{"data": ...}`, `{"items": ..., "meta": ...}`).
2. **Buyer/Supplier B4 Pagination**: For Phase B4, Buyer and Supplier list endpoints return:
   ```json
   {
     "items": [...],
     "total": 12,
     "limit": 20,
     "offset": 0
   }
   ```
   This `{items, total, limit, offset}` shape is a **feature-specific contract** created to satisfy the explicit Buyer/Supplier requirements (T1.14 / T1.17). It must **NOT** be treated as a universally mandated global envelope for all other modules unless explicitly standardized by the team later.
3. **Other Modules**: When implementing collections for other modules, return raw `list[<Resource>Read]` or follow their specific documented task requirements without inventing uncoordinated wrapper envelopes.

### Search Contract
- All search operations **must** use PostgreSQL capabilities (e.g. `ILIKE` or full-text search).
- External search engines (Elasticsearch, OpenSearch, Meilisearch) are **prohibited**.
- Query parameters must use standard names: `q: Optional[str] = Query(None)`.

---

## 21. Merge Conflict Hotspots

To prevent Git merge conflicts in shared files:

1. **`backend/app/main.py`**:
   Add new routers cleanly in the designated router section:
   ```python
   app.include_router(products_router, prefix=f"{settings.API_V1_PREFIX}/v1")
   ```
2. **`backend/app/models/__init__.py`**:
   Import new models with one line per model and preserve alphabetical ordering:
   ```python
   from app.models.product import Product  # noqa: F401
   ```
3. **`frontend/src/lib/api.ts`**:
   Add new TypeScript interfaces in a dedicated section; do not touch existing fetch helpers.
4. **`frontend/src/components/navbar.tsx`**:
   Make minimal, targeted additions for navigation links.

---

## 22. Conflict Resolution Rule

If a developer discovers that requirements, existing code, or this baseline appear to conflict, **STOP** before changing shared architecture.

Post a report to the team using this format:
```text
CONFLICT:
<Brief description of conflict>

CURRENT IMPLEMENTATION:
<File and line references in codebase>

BASELINE RULE:
<Section of docs/INTEGRATION_BASELINE.md>

FEATURE REQUIREMENT:
<Requirement from docs/PRD.md or docs/TASKS.md>

PROPOSED RESOLUTION:
<Minimal, non-breaking architectural proposal>
```

---

## 23. Developer Pre-Flight Checklist

Before implementing any feature, every developer **MUST**:

1. Read `docs/INTEGRATION_BASELINE.md`.
2. Read the relevant `docs/PRD.md` requirements.
3. Read `docs/ARCHITECTURE.md`.
4. Read `docs/RULES.md`.
5. Read `docs/DATA_MODEL.md` for the affected domain.
6. Inspect existing authentication and authorization patterns.
7. Inspect existing route conventions.
8. Inspect existing schema conventions.
9. Inspect current Alembic head before creating migrations.
10. Check shared-file conflict hotspots.
11. Stay within assigned ownership boundaries.
12. Avoid modifying shared infrastructure unnecessarily.
13. Run backend tests.
14. Run frontend lint/build when frontend changes are made.
15. Report any convention conflict before implementation.
