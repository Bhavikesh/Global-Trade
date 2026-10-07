"""
Phase B3 — Comprehensive security, tenant isolation, and enumeration resistance tests.

Verifies:
  1. Member of Org A cannot GET Org B's buyer (returns 404 via Org A path, 403 via Org B path)
  2. Member of Org A cannot PATCH Org B's buyer (returns 404 via Org A path, 403 via Org B path, Org B record untouched)
  3. Member of Org A cannot DELETE Org B's buyer (returns 404 via Org A path, 403 via Org B path, Org B record untouched)
  4. Member of Org A cannot GET Org B's supplier (returns 404 via Org A path, 403 via Org B path)
  5. Member of Org A cannot PATCH Org B's supplier (returns 404 via Org A path, 403 via Org B path, Org B record untouched)
  6. Member of Org A cannot DELETE Org B's supplier (returns 404 via Org A path, 403 via Org B path, Org B record untouched)
  7. Non-member cannot access any Buyer/Supplier endpoints (POST/GET/PATCH/DELETE return 403)
  8. Unauthenticated requests return 401
  9. Create always uses route organization_id and ignores client-supplied payload IDs
 10. Update cannot mutate organization_id, id, or created_at (only editable fields change)
 11. Enumeration resistance: querying a foreign-org ID produces identical 404 response as a random non-existent UUID
 12. Response isolation: response keys strictly match documented BuyerRead and SupplierRead schemas
"""
import uuid
from typing import Any
import pytest
from fastapi.testclient import TestClient

from tests.conftest import as_user, _make_claims


@pytest.fixture
def user_c_claims() -> dict[str, Any]:
    """User C has no membership in Org A or Org B."""
    return _make_claims(sub="auth0|user-c", email="c@example.com", name="User C")


@pytest.fixture
def org_a(client: TestClient, user_a_claims):
    with as_user(user_a_claims):
        resp = client.post(
            "/api/v1/organizations/",
            json={"legal_name": "Tenancy Org A Inc", "country": "US"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]


@pytest.fixture
def org_b(client: TestClient, user_b_claims):
    with as_user(user_b_claims):
        resp = client.post(
            "/api/v1/organizations/",
            json={"legal_name": "Tenancy Org B Inc", "country": "GB"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]


@pytest.fixture
def buyer_in_org_b(client: TestClient, user_b_claims, org_b):
    with as_user(user_b_claims):
        resp = client.post(
            f"/api/v1/organizations/{org_b}/buyers",
            json={"company_name": "Confidential Org B Buyer", "notes": "Secret notes"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()


@pytest.fixture
def supplier_in_org_b(client: TestClient, user_b_claims, org_b):
    with as_user(user_b_claims):
        resp = client.post(
            f"/api/v1/organizations/{org_b}/suppliers",
            json={"company_name": "Confidential Org B Supplier", "notes": "Secret supplier notes"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()


class TestCrossOrgBuyerIsolation:
    def test_member_a_cannot_get_org_b_buyer_via_org_a_route(
        self, client: TestClient, user_a_claims, org_a, buyer_in_org_b
    ):
        """Cross-tenant lookup via Org A's URL must return 404 without data leak."""
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Buyer not found."

    def test_member_a_cannot_patch_org_b_buyer_via_org_a_route(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, buyer_in_org_b
    ):
        """Cross-tenant PATCH via Org A's URL must return 404 and leave Org B record unchanged."""
        with as_user(user_a_claims):
            resp = client.patch(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_b['id']}",
                json={"company_name": "Tampered Name"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404

        # Verify Org B's record remains pristine
        with as_user(user_b_claims):
            check_resp = client.get(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert check_resp.status_code == 200
            assert check_resp.json()["company_name"] == "Confidential Org B Buyer"

    def test_member_a_cannot_delete_org_b_buyer_via_org_a_route(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, buyer_in_org_b
    ):
        """Cross-tenant DELETE via Org A's URL must return 404 and not delete Org B record."""
        with as_user(user_a_claims):
            resp = client.delete(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404

        # Verify Org B's record still exists
        with as_user(user_b_claims):
            check_resp = client.get(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert check_resp.status_code == 200

    def test_member_a_cannot_access_org_b_buyer_via_org_b_route(
        self, client: TestClient, user_a_claims, org_b, buyer_in_org_b
    ):
        """Direct access to Org B route by non-member must return 403 on all operations."""
        with as_user(user_a_claims):
            # POST
            resp_post = client.post(
                f"/api/v1/organizations/{org_b}/buyers",
                json={"company_name": "Unauthorized Buyer"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_post.status_code == 403

            # GET
            resp_get = client.get(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_get.status_code == 403

            # PATCH
            resp_patch = client.patch(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}",
                json={"notes": "Hacked"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_patch.status_code == 403

            # DELETE
            resp_del = client.delete(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_del.status_code == 403


class TestCrossOrgSupplierIsolation:
    def test_member_a_cannot_get_org_b_supplier_via_org_a_route(
        self, client: TestClient, user_a_claims, org_a, supplier_in_org_b
    ):
        """Cross-tenant lookup via Org A's URL must return 404."""
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Supplier not found."

    def test_member_a_cannot_patch_org_b_supplier_via_org_a_route(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, supplier_in_org_b
    ):
        """Cross-tenant PATCH via Org A's URL must return 404 and leave Org B record unchanged."""
        with as_user(user_a_claims):
            resp = client.patch(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_b['id']}",
                json={"company_name": "Tampered Supplier"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404

        with as_user(user_b_claims):
            check_resp = client.get(
                f"/api/v1/organizations/{org_b}/suppliers/{supplier_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert check_resp.status_code == 200
            assert check_resp.json()["company_name"] == "Confidential Org B Supplier"

    def test_member_a_cannot_delete_org_b_supplier_via_org_a_route(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, supplier_in_org_b
    ):
        """Cross-tenant DELETE via Org A's URL must return 404 and leave Org B record untouched."""
        with as_user(user_a_claims):
            resp = client.delete(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404

        with as_user(user_b_claims):
            check_resp = client.get(
                f"/api/v1/organizations/{org_b}/suppliers/{supplier_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert check_resp.status_code == 200

    def test_member_a_cannot_access_org_b_supplier_via_org_b_route(
        self, client: TestClient, user_a_claims, org_b, supplier_in_org_b
    ):
        """Direct access to Org B route by non-member must return 403 on all operations."""
        with as_user(user_a_claims):
            # POST
            resp_post = client.post(
                f"/api/v1/organizations/{org_b}/suppliers",
                json={"company_name": "Unauthorized Supplier"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_post.status_code == 403

            # GET
            resp_get = client.get(
                f"/api/v1/organizations/{org_b}/suppliers/{supplier_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_get.status_code == 403

            # PATCH
            resp_patch = client.patch(
                f"/api/v1/organizations/{org_b}/suppliers/{supplier_in_org_b['id']}",
                json={"notes": "Hacked"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_patch.status_code == 403

            # DELETE
            resp_del = client.delete(
                f"/api/v1/organizations/{org_b}/suppliers/{supplier_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_del.status_code == 403


class TestNonMemberAccess:
    def test_user_without_memberships_cannot_access_org_endpoints(
        self, client: TestClient, user_c_claims, org_a, buyer_in_org_b, supplier_in_org_b
    ):
        """A user with no organization memberships is rejected with 403 for all endpoints."""
        with as_user(user_c_claims):
            # Buyer operations on org_a
            resp_b_post = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Denied Buyer"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b_post.status_code == 403

            fake_id = uuid.uuid4()
            resp_b_get = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{fake_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b_get.status_code == 403

            resp_b_patch = client.patch(
                f"/api/v1/organizations/{org_a}/buyers/{fake_id}",
                json={"company_name": "Denied"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b_patch.status_code == 403

            resp_b_del = client.delete(
                f"/api/v1/organizations/{org_a}/buyers/{fake_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b_del.status_code == 403

            # Supplier operations on org_a
            resp_s_post = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Denied Supplier"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_s_post.status_code == 403

            resp_s_get = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{fake_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_s_get.status_code == 403

            resp_s_patch = client.patch(
                f"/api/v1/organizations/{org_a}/suppliers/{fake_id}",
                json={"company_name": "Denied"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_s_patch.status_code == 403

            resp_s_del = client.delete(
                f"/api/v1/organizations/{org_a}/suppliers/{fake_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_s_del.status_code == 403

    def test_unauthenticated_request_returns_401(self, client: TestClient, org_a):
        """Requests with missing or invalid token are rejected with 401."""
        fake_id = uuid.uuid4()
        # No Authorization header
        resp_get = client.get(f"/api/v1/organizations/{org_a}/buyers/{fake_id}")
        assert resp_get.status_code == 401

        resp_sup = client.get(f"/api/v1/organizations/{org_a}/suppliers/{fake_id}")
        assert resp_sup.status_code == 401


class TestCreateAndEnumerationHardening:
    def test_create_always_uses_route_org_id_and_ignores_payload(
        self, client: TestClient, user_a_claims, org_a, org_b
    ):
        """Attempting to inject foreign organization_id in request body is ignored."""
        with as_user(user_a_claims):
            # Buyer create with spoofed organization_id in body
            resp_buyer = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={
                    "company_name": "Injected Org Buyer",
                    "organization_id": org_b,
                },
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_buyer.status_code == 201
            # Must strictly belong to org_a
            assert resp_buyer.json()["organization_id"] == org_a

            # Supplier create with spoofed organization_id in body
            resp_sup = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={
                    "company_name": "Injected Org Supplier",
                    "organization_id": org_b,
                },
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_sup.status_code == 201
            assert resp_sup.json()["organization_id"] == org_a

    def test_enumeration_resistance_foreign_vs_nonexistent_buyer(
        self, client: TestClient, user_a_claims, org_a, buyer_in_org_b
    ):
        """Cross-org foreign resource query must return exact same 404 response as non-existent UUID."""
        with as_user(user_a_claims):
            # Querying foreign org's buyer ID
            foreign_resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )

            # Querying completely non-existent UUID
            fake_uuid = uuid.uuid4()
            fake_resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{fake_uuid}",
                headers={"Authorization": "Bearer fake"},
            )

            assert foreign_resp.status_code == 404
            assert fake_resp.status_code == 404
            assert foreign_resp.json() == fake_resp.json()
            assert foreign_resp.json() == {"detail": "Buyer not found."}

    def test_enumeration_resistance_foreign_vs_nonexistent_supplier(
        self, client: TestClient, user_a_claims, org_a, supplier_in_org_b
    ):
        """Cross-org foreign supplier query must return exact same 404 response as non-existent UUID."""
        with as_user(user_a_claims):
            foreign_resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_b['id']}",
                headers={"Authorization": "Bearer fake"},
            )

            fake_uuid = uuid.uuid4()
            fake_resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{fake_uuid}",
                headers={"Authorization": "Bearer fake"},
            )

            assert foreign_resp.status_code == 404
            assert fake_resp.status_code == 404
            assert foreign_resp.json() == fake_resp.json()
            assert foreign_resp.json() == {"detail": "Supplier not found."}


class TestUpdateAndResponseIsolation:
    def test_buyer_patch_cannot_change_id_organization_id_or_created_at(
        self, client: TestClient, user_a_claims, org_a, org_b
    ):
        """PATCH cannot mutate id, organization_id, or created_at; only editable fields change."""
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Original Buyer Name"},
                headers={"Authorization": "Bearer fake"},
            )
            assert create_resp.status_code == 201
            original_data = create_resp.json()
            original_id = original_data["id"]
            original_created_at = original_data["created_at"]

            # Attempt to modify id, organization_id, and created_at via PATCH
            spoofed_id = str(uuid.uuid4())
            patch_resp = client.patch(
                f"/api/v1/organizations/{org_a}/buyers/{original_id}",
                json={
                    "id": spoofed_id,
                    "organization_id": org_b,
                    "created_at": "2020-01-01T00:00:00Z",
                    "company_name": "Updated Buyer Name",
                },
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            updated_data = patch_resp.json()

            # Immutable fields must remain unchanged
            assert updated_data["id"] == original_id
            assert updated_data["organization_id"] == org_a
            assert updated_data["created_at"] == original_created_at
            # Editable field changed
            assert updated_data["company_name"] == "Updated Buyer Name"

    def test_supplier_patch_cannot_change_id_organization_id_or_created_at(
        self, client: TestClient, user_a_claims, org_a, org_b
    ):
        """PATCH cannot mutate id, organization_id, or created_at on supplier."""
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Original Supplier Name"},
                headers={"Authorization": "Bearer fake"},
            )
            assert create_resp.status_code == 201
            original_data = create_resp.json()
            original_id = original_data["id"]
            original_created_at = original_data["created_at"]

            spoofed_id = str(uuid.uuid4())
            patch_resp = client.patch(
                f"/api/v1/organizations/{org_a}/suppliers/{original_id}",
                json={
                    "id": spoofed_id,
                    "organization_id": org_b,
                    "created_at": "2020-01-01T00:00:00Z",
                    "company_name": "Updated Supplier Name",
                },
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            updated_data = patch_resp.json()

            assert updated_data["id"] == original_id
            assert updated_data["organization_id"] == org_a
            assert updated_data["created_at"] == original_created_at
            assert updated_data["company_name"] == "Updated Supplier Name"

    def test_buyer_response_isolation_no_internal_leakage(
        self, client: TestClient, user_a_claims, org_a
    ):
        """BuyerRead response contains strictly the documented schema fields and no internal leaks."""
        expected_fields = {
            "id",
            "organization_id",
            "company_name",
            "contact_name",
            "email",
            "phone",
            "country",
            "address",
            "website",
            "industry",
            "verification_status",
            "notes",
            "created_at",
            "updated_at",
        }
        with as_user(user_a_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Schema Check Buyer"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            assert set(resp.json().keys()) == expected_fields

    def test_supplier_response_isolation_no_internal_leakage(
        self, client: TestClient, user_a_claims, org_a
    ):
        """SupplierRead response contains strictly the documented schema fields and no internal leaks."""
        expected_fields = {
            "id",
            "organization_id",
            "company_name",
            "contact_name",
            "email",
            "phone",
            "country",
            "address",
            "website",
            "supplier_type",
            "verification_status",
            "certifications",
            "notes",
            "created_at",
            "updated_at",
        }
        with as_user(user_a_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Schema Check Supplier"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            assert set(resp.json().keys()) == expected_fields
