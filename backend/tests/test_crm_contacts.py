"""
Phase B5 — Comprehensive CRM Contact API and isolation tests.

Verifies:
  1. Buyer contact creation (POST 201)
  2. Supplier contact creation (POST 201)
  3. Buyer contact listing (GET 200)
  4. Supplier contact listing (GET 200)
  5. Contact PATCH (200)
  6. Contact DELETE (204)
  7. Missing buyer returns 404
  8. Missing supplier returns 404
  9. Cannot create buyer contact using buyer from another organization (404)
 10. Cannot create supplier contact using supplier from another organization (404)
 11. Cannot read contacts belonging to another organization (404 / 403)
 12. Cannot PATCH contact belonging to another organization (404)
 13. Cannot DELETE contact belonging to another organization (404)
 14. Unauthenticated requests rejected (401)
 15. Non-member requests rejected (403)
 16. Immutable fields (id, organization_id, buyer_id, supplier_id, created_at) cannot be changed through PATCH
 17. Contact validation behavior (empty name rejected, email normalized, length limits)
 18. Response serialization conforms to ContactRead schema
 19. Isolation: Buyer contacts not returned in another organization's list
 20. Isolation: Supplier contacts not returned in another organization's list
 21. No orphan contacts: creation strictly requires and sets parent entity
 22. Empty contacts list returns clean []
 23. PATCH non-existent contact returns 404
 24. DELETE non-existent contact returns 404
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from tests.conftest import as_user


@pytest.fixture
def org_a(client: TestClient, user_a_claims):
    """Creates Organization A owned by User A."""
    with as_user(user_a_claims):
        resp = client.post(
            "/api/v1/organizations/",
            json={"legal_name": "Contact Org A Inc", "country": "US"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]


@pytest.fixture
def org_b(client: TestClient, user_b_claims):
    """Creates Organization B owned by User B."""
    with as_user(user_b_claims):
        resp = client.post(
            "/api/v1/organizations/",
            json={"legal_name": "Contact Org B Ltd", "country": "GB"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]


@pytest.fixture
def buyer_in_org_a(client: TestClient, user_a_claims, org_a):
    """Creates a buyer under Org A."""
    with as_user(user_a_claims):
        resp = client.post(
            f"/api/v1/organizations/{org_a}/buyers",
            json={"company_name": "Org A Test Buyer", "country": "US"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()


@pytest.fixture
def supplier_in_org_a(client: TestClient, user_a_claims, org_a):
    """Creates a supplier under Org A."""
    with as_user(user_a_claims):
        resp = client.post(
            f"/api/v1/organizations/{org_a}/suppliers",
            json={"company_name": "Org A Test Supplier", "country": "US"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()


@pytest.fixture
def buyer_in_org_b(client: TestClient, user_b_claims, org_b):
    """Creates a buyer under Org B."""
    with as_user(user_b_claims):
        resp = client.post(
            f"/api/v1/organizations/{org_b}/buyers",
            json={"company_name": "Org B Secret Buyer", "country": "GB"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()


@pytest.fixture
def supplier_in_org_b(client: TestClient, user_b_claims, org_b):
    """Creates a supplier under Org B."""
    with as_user(user_b_claims):
        resp = client.post(
            f"/api/v1/organizations/{org_b}/suppliers",
            json={"company_name": "Org B Secret Supplier", "country": "GB"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()


class TestCRMContactCRUD:
    def test_01_create_buyer_contact(self, client: TestClient, user_a_claims, org_a, buyer_in_org_a):
        with as_user(user_a_claims):
            payload = {
                "name": "Sarah Connor",
                "email": "sarah@resistance.org",
                "phone": "+1-555-0199",
                "designation": "Head of Procurement",
                "notes": "Key decision maker",
                "is_primary": True,
            }
            resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json=payload,
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["name"] == "Sarah Connor"
            assert data["email"] == "sarah@resistance.org"
            assert data["phone"] == "+1-555-0199"
            assert data["designation"] == "Head of Procurement"
            assert data["notes"] == "Key decision maker"
            assert data["is_primary"] is True
            assert data["organization_id"] == org_a
            assert data["buyer_id"] == buyer_in_org_a["id"]
            assert data["supplier_id"] is None
            assert data["created_at"] is not None
            assert data["updated_at"] is not None
            assert "id" in data

    def test_02_create_supplier_contact(self, client: TestClient, user_a_claims, org_a, supplier_in_org_a):
        with as_user(user_a_claims):
            payload = {
                "name": "Klaus Weber",
                "email": "klaus@mfg-parts.de",
                "phone": "+49-30-123456",
                "designation": "Plant Manager",
                "notes": "Handles quality audits",
                "is_primary": False,
            }
            resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_a['id']}/contacts",
                json=payload,
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["name"] == "Klaus Weber"
            assert data["email"] == "klaus@mfg-parts.de"
            assert data["designation"] == "Plant Manager"
            assert data["organization_id"] == org_a
            assert data["supplier_id"] == supplier_in_org_a["id"]
            assert data["buyer_id"] is None
            assert data["is_primary"] is False

    def test_03_list_buyer_contacts(self, client: TestClient, user_a_claims, org_a, buyer_in_org_a):
        with as_user(user_a_claims):
            # Create 2 contacts
            client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "Contact One", "email": "one@test.com"},
                headers={"Authorization": "Bearer fake"},
            )
            client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "Contact Two", "email": "two@test.com"},
                headers={"Authorization": "Bearer fake"},
            )

            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            names = {item["name"] for item in data}
            assert names == {"Contact One", "Contact Two"}

    def test_04_list_supplier_contacts(self, client: TestClient, user_a_claims, org_a, supplier_in_org_a):
        with as_user(user_a_claims):
            client.post(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_a['id']}/contacts",
                json={"name": "Supplier Contact Alpha"},
                headers={"Authorization": "Bearer fake"},
            )
            client.post(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_a['id']}/contacts",
                json={"name": "Supplier Contact Beta"},
                headers={"Authorization": "Bearer fake"},
            )

            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_a['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            names = {item["name"] for item in data}
            assert names == {"Supplier Contact Alpha", "Supplier Contact Beta"}

    def test_05_update_contact_patch(self, client: TestClient, user_a_claims, org_a, buyer_in_org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "Initial Name", "phone": "+1-111-2222", "designation": "Sales"},
                headers={"Authorization": "Bearer fake"},
            )
            contact_id = create_resp.json()["id"]

            # Partial update: change name and is_primary
            patch_resp = client.patch(
                f"/api/v1/organizations/{org_a}/contacts/{contact_id}",
                json={"name": "Updated Name", "is_primary": True},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            updated = patch_resp.json()
            assert updated["name"] == "Updated Name"
            assert updated["is_primary"] is True
            assert updated["phone"] == "+1-111-2222"  # unchanged
            assert updated["designation"] == "Sales"   # unchanged

    def test_06_delete_contact(self, client: TestClient, user_a_claims, org_a, buyer_in_org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "To Be Deleted"},
                headers={"Authorization": "Bearer fake"},
            )
            contact_id = create_resp.json()["id"]

            # Delete
            del_resp = client.delete(
                f"/api/v1/organizations/{org_a}/contacts/{contact_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert del_resp.status_code == 204

            # Verify subsequent DELETE returns 404
            del_again = client.delete(
                f"/api/v1/organizations/{org_a}/contacts/{contact_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert del_again.status_code == 404

            # Verify list no longer includes deleted contact
            list_resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert len(list_resp.json()) == 0

    def test_07_missing_buyer_returns_404(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            fake_id = uuid.uuid4()
            # POST to non-existent buyer
            post_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{fake_id}/contacts",
                json={"name": "Orphan Contact"},
                headers={"Authorization": "Bearer fake"},
            )
            assert post_resp.status_code == 404
            assert post_resp.json()["detail"] == "Buyer not found."

            # GET from non-existent buyer
            get_resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{fake_id}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert get_resp.status_code == 404
            assert get_resp.json()["detail"] == "Buyer not found."

    def test_08_missing_supplier_returns_404(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            fake_id = uuid.uuid4()
            post_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers/{fake_id}/contacts",
                json={"name": "Orphan Supplier Contact"},
                headers={"Authorization": "Bearer fake"},
            )
            assert post_resp.status_code == 404
            assert post_resp.json()["detail"] == "Supplier not found."

            get_resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{fake_id}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert get_resp.status_code == 404
            assert get_resp.json()["detail"] == "Supplier not found."


class TestCRMContactIsolationAndSecurity:
    def test_09_cannot_create_buyer_contact_cross_org(
        self, client: TestClient, user_a_claims, org_a, buyer_in_org_b
    ):
        """User A in Org A cannot create a contact attached to Org B's buyer."""
        with as_user(user_a_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_b['id']}/contacts",
                json={"name": "Illegitimate Contact"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Buyer not found."

    def test_10_cannot_create_supplier_contact_cross_org(
        self, client: TestClient, user_a_claims, org_a, supplier_in_org_b
    ):
        """User A in Org A cannot create a contact attached to Org B's supplier."""
        with as_user(user_a_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_b['id']}/contacts",
                json={"name": "Illegitimate Contact"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Supplier not found."

    def test_11_cannot_read_contacts_belonging_to_another_org(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, buyer_in_org_b
    ):
        """User A in Org A cannot list contacts of Org B's buyer via Org A URL or Org B URL."""
        # Create contact in Org B
        with as_user(user_b_claims):
            client.post(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}/contacts",
                json={"name": "Confidential Contact"},
                headers={"Authorization": "Bearer fake"},
            )

        # User A attempts via Org A route -> 404 Not Found (buyer not in Org A)
        with as_user(user_a_claims):
            resp_via_org_a = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_b['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_via_org_a.status_code == 404

            # User A attempts via Org B route -> 403 Forbidden (not member of Org B)
            resp_via_org_b = client.get(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_via_org_b.status_code == 403

    def test_12_cannot_patch_contact_belonging_to_another_org(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, buyer_in_org_b
    ):
        """User A in Org A cannot patch Org B's contact via Org A or Org B routes."""
        with as_user(user_b_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}/contacts",
                json={"name": "Pristine Contact Name"},
                headers={"Authorization": "Bearer fake"},
            )
            org_b_contact_id = create_resp.json()["id"]

        with as_user(user_a_claims):
            # Via Org A route: 404 Not Found (does not belong to Org A)
            patch_a = client.patch(
                f"/api/v1/organizations/{org_a}/contacts/{org_b_contact_id}",
                json={"name": "Tampered Name"},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_a.status_code == 404
            assert patch_a.json()["detail"] == "Contact not found."

            # Via Org B route: 403 Forbidden (non-member)
            patch_b = client.patch(
                f"/api/v1/organizations/{org_b}/contacts/{org_b_contact_id}",
                json={"name": "Tampered Name"},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_b.status_code == 403

        # Confirm Org B record remained pristine
        with as_user(user_b_claims):
            list_resp = client.get(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert list_resp.json()[0]["name"] == "Pristine Contact Name"

    def test_13_cannot_delete_contact_belonging_to_another_org(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, buyer_in_org_b
    ):
        """User A in Org A cannot delete Org B's contact."""
        with as_user(user_b_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}/contacts",
                json={"name": "Protected Contact"},
                headers={"Authorization": "Bearer fake"},
            )
            org_b_contact_id = create_resp.json()["id"]

        with as_user(user_a_claims):
            del_a = client.delete(
                f"/api/v1/organizations/{org_a}/contacts/{org_b_contact_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert del_a.status_code == 404

            del_b = client.delete(
                f"/api/v1/organizations/{org_b}/contacts/{org_b_contact_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert del_b.status_code == 403

        # Confirm still exists in Org B
        with as_user(user_b_claims):
            list_resp = client.get(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert len(list_resp.json()) == 1

    def test_14_unauthenticated_requests_rejected(self, client: TestClient, org_a, buyer_in_org_a):
        fake_id = uuid.uuid4()
        # POST
        assert client.post(f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts", json={"name": "Test"}).status_code == 401
        # GET
        assert client.get(f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts").status_code == 401
        # PATCH
        assert client.patch(f"/api/v1/organizations/{org_a}/contacts/{fake_id}", json={"name": "Test"}).status_code == 401
        # DELETE
        assert client.delete(f"/api/v1/organizations/{org_a}/contacts/{fake_id}").status_code == 401

    def test_15_non_member_requests_rejected(self, client: TestClient, user_b_claims, org_a, buyer_in_org_a):
        fake_id = uuid.uuid4()
        with as_user(user_b_claims):
            assert client.post(f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts", json={"name": "Test"}, headers={"Authorization": "Bearer fake"}).status_code == 403
            assert client.get(f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts", headers={"Authorization": "Bearer fake"}).status_code == 403
            assert client.patch(f"/api/v1/organizations/{org_a}/contacts/{fake_id}", json={"name": "Test"}, headers={"Authorization": "Bearer fake"}).status_code == 403
            assert client.delete(f"/api/v1/organizations/{org_a}/contacts/{fake_id}", headers={"Authorization": "Bearer fake"}).status_code == 403

    def test_16_immutable_fields_cannot_be_changed_through_patch(
        self, client: TestClient, user_a_claims, org_a, org_b, buyer_in_org_a
    ):
        """PATCH cannot mutate id, organization_id, buyer_id, supplier_id, or created_at."""
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "Original Contact"},
                headers={"Authorization": "Bearer fake"},
            )
            orig = create_resp.json()
            contact_id = orig["id"]
            orig_created_at = orig["created_at"]

            spoofed_id = str(uuid.uuid4())
            spoofed_buyer = str(uuid.uuid4())
            spoofed_supplier = str(uuid.uuid4())

            patch_resp = client.patch(
                f"/api/v1/organizations/{org_a}/contacts/{contact_id}",
                json={
                    "id": spoofed_id,
                    "organization_id": org_b,
                    "buyer_id": spoofed_buyer,
                    "supplier_id": spoofed_supplier,
                    "created_at": "2020-01-01T00:00:00Z",
                    "name": "Updated Contact Name",
                },
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            updated = patch_resp.json()

            # Immutable fields unchanged
            assert updated["id"] == contact_id
            assert updated["organization_id"] == org_a
            assert updated["buyer_id"] == buyer_in_org_a["id"]
            assert updated["supplier_id"] is None
            assert updated["created_at"] == orig_created_at
            # Mutable field changed
            assert updated["name"] == "Updated Contact Name"

    def test_17_contact_validation_rules(self, client: TestClient, user_a_claims, org_a, buyer_in_org_a):
        with as_user(user_a_claims):
            # 1. Blank/whitespace name rejected
            resp_blank = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "   "},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_blank.status_code == 422

            # 2. Invalid email rejected
            resp_bad_email = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "Valid Name", "email": "not-an-email"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_bad_email.status_code == 422

            # 3. Valid email normalized to lowercase and strings trimmed
            resp_clean = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={
                    "name": "  Trimmed Name  ",
                    "email": "  USER@EXAMPLE.COM  ",
                    "phone": "  +1-555-1234  ",
                    "designation": "  Director  ",
                },
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_clean.status_code == 201
            data = resp_clean.json()
            assert data["name"] == "Trimmed Name"
            assert data["email"] == "user@example.com"
            assert data["phone"] == "+1-555-1234"
            assert data["designation"] == "Director"

    def test_18_response_serialization(self, client: TestClient, user_a_claims, org_a, buyer_in_org_a):
        expected_keys = {
            "id",
            "organization_id",
            "buyer_id",
            "supplier_id",
            "name",
            "email",
            "phone",
            "designation",
            "notes",
            "is_primary",
            "created_at",
            "updated_at",
        }
        with as_user(user_a_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "Schema Test Contact"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            assert set(resp.json().keys()) == expected_keys

    def test_19_buyer_contacts_not_returned_in_another_org_list(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, buyer_in_org_a, buyer_in_org_b
    ):
        with as_user(user_a_claims):
            client.post(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                json={"name": "Org A Contact"},
                headers={"Authorization": "Bearer fake"},
            )

        with as_user(user_b_claims):
            resp_b = client.get(
                f"/api/v1/organizations/{org_b}/buyers/{buyer_in_org_b['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b.status_code == 200
            assert len(resp_b.json()) == 0

    def test_20_supplier_contacts_not_returned_in_another_org_list(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, supplier_in_org_a, supplier_in_org_b
    ):
        with as_user(user_a_claims):
            client.post(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_a['id']}/contacts",
                json={"name": "Org A Supplier Contact"},
                headers={"Authorization": "Bearer fake"},
            )

        with as_user(user_b_claims):
            resp_b = client.get(
                f"/api/v1/organizations/{org_b}/suppliers/{supplier_in_org_b['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b.status_code == 200
            assert len(resp_b.json()) == 0

    def test_21_no_orphan_contact_can_be_created(self, client: TestClient, user_a_claims, org_a):
        """Verifies contacts cannot be created without a valid buyer or supplier route."""
        with as_user(user_a_claims):
            # Attempt to hit non-existent top-level contacts POST (orphan creation route doesn't exist)
            resp = client.post(
                f"/api/v1/organizations/{org_a}/contacts",
                json={"name": "Orphan Contact"},
                headers={"Authorization": "Bearer fake"},
            )
            # Route not registered -> 404/405
            assert resp.status_code in (404, 405)

    def test_22_empty_contacts_list(self, client: TestClient, user_a_claims, org_a, buyer_in_org_a, supplier_in_org_a):
        with as_user(user_a_claims):
            resp_b = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_in_org_a['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b.status_code == 200
            assert resp_b.json() == []

            resp_s = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_in_org_a['id']}/contacts",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_s.status_code == 200
            assert resp_s.json() == []

    def test_23_patch_non_existent_contact(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            fake_id = uuid.uuid4()
            resp = client.patch(
                f"/api/v1/organizations/{org_a}/contacts/{fake_id}",
                json={"name": "Updated Name"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Contact not found."

    def test_24_delete_non_existent_contact(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            fake_id = uuid.uuid4()
            resp = client.delete(
                f"/api/v1/organizations/{org_a}/contacts/{fake_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Contact not found."
