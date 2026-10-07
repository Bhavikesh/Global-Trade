"""
Comprehensive test suite for Buyer and Supplier CRUD endpoints.

Verifies all 20 required scenarios:
BUYER:
 1. authorized member can create buyer
 2. authorized member can retrieve buyer
 3. authorized member can update buyer
 4. authorized member can delete buyer
 5. unauthorized/non-member cannot create buyer (403)
 6. unauthorized/non-member cannot retrieve buyer (403)
 7. unauthorized/non-member cannot update buyer (403)
 8. unauthorized/non-member cannot delete buyer (403)
 9. buyer from another organization cannot be accessed through the wrong organization_id (404)
 10. buyer organization_id cannot be changed through update

SUPPLIER:
 11. authorized member can create supplier
 12. authorized member can retrieve supplier
 13. authorized member can update supplier
 14. authorized member can delete supplier
 15. unauthorized/non-member cannot create supplier (403)
 16. unauthorized/non-member cannot retrieve supplier (403)
 17. unauthorized/non-member cannot update supplier (403)
 18. unauthorized/non-member cannot delete supplier (403)
 19. supplier from another organization cannot be accessed through the wrong organization_id (404)
 20. supplier organization_id cannot be changed through update

Additional tests:
 - Invalid request bodies return 422
 - Missing resource returns 404
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
            json={"legal_name": "Org A Corporation", "country": "US"},
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
            json={"legal_name": "Org B Corporation", "country": "DE"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]


class TestBuyerCRUD:
    def test_01_authorized_member_can_create_buyer(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            payload = {
                "company_name": "Global Retail Partners",
                "contact_name": "John Doe",
                "email": "john@globalretail.com",
                "phone": "+1-555-0100",
                "country": "US",
                "address": "123 Market St",
                "website": "globalretail.com",
                "industry": "Retail",
                "verification_status": "UNVERIFIED",
                "notes": "Large volume buyer",
            }
            resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json=payload,
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["company_name"] == "Global Retail Partners"
            assert data["organization_id"] == org_a
            assert data["website"] == "https://globalretail.com"
            assert data["created_at"] is not None
            assert data["updated_at"] is not None
            assert "id" in data

    def test_02_authorized_member_can_retrieve_buyer(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            # Create buyer first
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Retrieve Buyer Test", "country": "US"},
                headers={"Authorization": "Bearer fake"},
            )
            buyer_id = create_resp.json()["id"]

            # Retrieve buyer
            get_resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert get_resp.status_code == 200
            data = get_resp.json()
            assert data["id"] == buyer_id
            assert data["company_name"] == "Retrieve Buyer Test"
            assert data["organization_id"] == org_a

    def test_03_authorized_member_can_update_buyer(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Update Buyer Test", "country": "US", "notes": "Initial notes"},
                headers={"Authorization": "Bearer fake"},
            )
            buyer_id = create_resp.json()["id"]

            # Update notes and industry only
            patch_resp = client.patch(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_id}",
                json={"notes": "Updated notes", "industry": "Automotive"},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            updated = patch_resp.json()
            assert updated["notes"] == "Updated notes"
            assert updated["industry"] == "Automotive"
            assert updated["company_name"] == "Update Buyer Test"  # unchanged
            assert updated["country"] == "US"                      # unchanged

    def test_04_authorized_member_can_delete_buyer(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Delete Buyer Test"},
                headers={"Authorization": "Bearer fake"},
            )
            buyer_id = create_resp.json()["id"]

            # Delete
            del_resp = client.delete(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert del_resp.status_code == 204

            # Verify no longer exists (404)
            get_resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert get_resp.status_code == 404

    def test_05_unauthorized_non_member_cannot_create_buyer(self, client: TestClient, user_b_claims, org_a):
        with as_user(user_b_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Non Member Buyer"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403

    def test_06_unauthorized_non_member_cannot_retrieve_buyer(self, client: TestClient, user_a_claims, user_b_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Buyer A"},
                headers={"Authorization": "Bearer fake"},
            )
            buyer_id = create_resp.json()["id"]

        with as_user(user_b_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403

    def test_07_unauthorized_non_member_cannot_update_buyer(self, client: TestClient, user_a_claims, user_b_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Buyer A"},
                headers={"Authorization": "Bearer fake"},
            )
            buyer_id = create_resp.json()["id"]

        with as_user(user_b_claims):
            resp = client.patch(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_id}",
                json={"notes": "Hacked"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403

    def test_08_unauthorized_non_member_cannot_delete_buyer(self, client: TestClient, user_a_claims, user_b_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Buyer A"},
                headers={"Authorization": "Bearer fake"},
            )
            buyer_id = create_resp.json()["id"]

        with as_user(user_b_claims):
            resp = client.delete(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403

    def test_09_buyer_from_another_org_cannot_be_accessed_via_wrong_org_id(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b
    ):
        # User B creates Buyer in Org B
        with as_user(user_b_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_b}/buyers",
                json={"company_name": "Org B Buyer"},
                headers={"Authorization": "Bearer fake"},
            )
            org_b_buyer_id = create_resp.json()["id"]

        # User A tries to access Org B's buyer by using Org A's URL
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{org_b_buyer_id}",
                headers={"Authorization": "Bearer fake"},
            )
            # Returns 404 because query filters by both id and organization_id
            assert resp.status_code == 404

    def test_10_buyer_organization_id_cannot_be_changed_through_update(
        self, client: TestClient, user_a_claims, org_a, org_b
    ):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "Org Id Test Buyer"},
                headers={"Authorization": "Bearer fake"},
            )
            buyer_id = create_resp.json()["id"]

            # Attempt to change organization_id in update body
            patch_resp = client.patch(
                f"/api/v1/organizations/{org_a}/buyers/{buyer_id}",
                json={"organization_id": org_b, "company_name": "Renamed Buyer"},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            assert patch_resp.json()["organization_id"] == org_a  # organization_id is unchanged!


class TestSupplierCRUD:
    def test_11_authorized_member_can_create_supplier(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            payload = {
                "company_name": "Shenzhen Manufacturing Group",
                "contact_name": "Zhang Wei",
                "email": "zhang@szmfg.cn",
                "phone": "+86-755-98765432",
                "country": "CN",
                "address": "Tower 2, High Tech Zone, Shenzhen",
                "website": "szmfg.cn",
                "supplier_type": "MANUFACTURER",
                "verification_status": "VERIFIED",
                "certifications": "ISO9001, CE",
                "notes": "Direct supplier",
            }
            resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json=payload,
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["company_name"] == "Shenzhen Manufacturing Group"
            assert data["organization_id"] == org_a
            assert data["supplier_type"] == "MANUFACTURER"
            assert data["verification_status"] == "VERIFIED"
            assert data["website"] == "https://szmfg.cn"
            assert data["created_at"] is not None
            assert data["updated_at"] is not None
            assert "id" in data

    def test_12_authorized_member_can_retrieve_supplier(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Retrieve Supplier Test", "country": "DE"},
                headers={"Authorization": "Bearer fake"},
            )
            supplier_id = create_resp.json()["id"]

            get_resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert get_resp.status_code == 200
            data = get_resp.json()
            assert data["id"] == supplier_id
            assert data["company_name"] == "Retrieve Supplier Test"
            assert data["country"] == "DE"

    def test_13_authorized_member_can_update_supplier(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Update Supplier Test", "supplier_type": "FACTORY"},
                headers={"Authorization": "Bearer fake"},
            )
            supplier_id = create_resp.json()["id"]

            patch_resp = client.patch(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_id}",
                json={"supplier_type": "OEM", "certifications": "ISO14001"},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            updated = patch_resp.json()
            assert updated["supplier_type"] == "OEM"
            assert updated["certifications"] == "ISO14001"
            assert updated["company_name"] == "Update Supplier Test"  # unchanged

    def test_14_authorized_member_can_delete_supplier(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Delete Supplier Test"},
                headers={"Authorization": "Bearer fake"},
            )
            supplier_id = create_resp.json()["id"]

            del_resp = client.delete(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert del_resp.status_code == 204

            # Verify 404
            get_resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert get_resp.status_code == 404

    def test_15_unauthorized_non_member_cannot_create_supplier(self, client: TestClient, user_b_claims, org_a):
        with as_user(user_b_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Non Member Supplier"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403

    def test_16_unauthorized_non_member_cannot_retrieve_supplier(self, client: TestClient, user_a_claims, user_b_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Supplier A"},
                headers={"Authorization": "Bearer fake"},
            )
            supplier_id = create_resp.json()["id"]

        with as_user(user_b_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403

    def test_17_unauthorized_non_member_cannot_update_supplier(self, client: TestClient, user_a_claims, user_b_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Supplier A"},
                headers={"Authorization": "Bearer fake"},
            )
            supplier_id = create_resp.json()["id"]

        with as_user(user_b_claims):
            resp = client.patch(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_id}",
                json={"notes": "Hacked"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403

    def test_18_unauthorized_non_member_cannot_delete_supplier(self, client: TestClient, user_a_claims, user_b_claims, org_a):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Supplier A"},
                headers={"Authorization": "Bearer fake"},
            )
            supplier_id = create_resp.json()["id"]

        with as_user(user_b_claims):
            resp = client.delete(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403

    def test_19_supplier_from_another_org_cannot_be_accessed_via_wrong_org_id(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b
    ):
        with as_user(user_b_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_b}/suppliers",
                json={"company_name": "Org B Supplier"},
                headers={"Authorization": "Bearer fake"},
            )
            org_b_supplier_id = create_resp.json()["id"]

        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{org_b_supplier_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404

    def test_20_supplier_organization_id_cannot_be_changed_through_update(
        self, client: TestClient, user_a_claims, org_a, org_b
    ):
        with as_user(user_a_claims):
            create_resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Org Id Test Supplier"},
                headers={"Authorization": "Bearer fake"},
            )
            supplier_id = create_resp.json()["id"]

            patch_resp = client.patch(
                f"/api/v1/organizations/{org_a}/suppliers/{supplier_id}",
                json={"organization_id": org_b, "company_name": "Renamed Supplier"},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            assert patch_resp.json()["organization_id"] == org_a

    def test_invalid_request_bodies_return_validation_error(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            # Blank company name
            resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json={"company_name": "   "},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422

            # Invalid status
            resp2 = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json={"company_name": "Valid Name", "verification_status": "UNKNOWN"},
                headers={"Authorization": "Bearer fake"},
            )
            assert resp2.status_code == 422

    def test_missing_resource_returns_404(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            fake_id = uuid.uuid4()
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers/{fake_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Buyer not found."

            resp2 = client.get(
                f"/api/v1/organizations/{org_a}/suppliers/{fake_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp2.status_code == 404
            assert resp2.json()["detail"] == "Supplier not found."
