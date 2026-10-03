"""
Phase 1 — T1.7 Company Profile tests.

Covers:
  - Reading organization company profile as active member
  - Updating all company profile fields as ADMIN (legal_name, display_name, business_type, country, address, tax_identifier, vat_identifier, iec_number, website, contact_information)
  - Preventing non-admin member from updating company profile (403)
  - Preventing non-member from reading company profile (403)
  - Preventing non-member from updating company profile (403)
  - Server-side validation of country ISO code, legal_name, website
"""
import pytest
from fastapi.testclient import TestClient

from tests.conftest import as_user


class TestCompanyProfile:
    """Test suite for T1.7 Company Profile management."""

    def test_get_company_profile_as_member(
        self, client: TestClient, user_a_claims
    ):
        """Active members can read their organization's full company profile."""
        with as_user(user_a_claims):
            create_resp = client.post(
                "/api/v1/organizations/",
                json={
                    "legal_name": "Pacific Coast Importers LLC",
                    "display_name": "Pacific Coast",
                    "business_type": "IMPORTER",
                    "country": "US",
                    "address": "100 Ocean Blvd, Suite 400, Long Beach, CA 90802",
                    "tax_identifier": "EIN-12-3456789",
                    "vat_identifier": "US-VAT-9999",
                    "iec_number": "IEC-0102030405",
                    "website": "https://pacificcoasttrade.com",
                    "contact_information": "Phone: +1-555-0199, ops@pacificcoasttrade.com",
                },
                headers={"Authorization": "Bearer fake"},
            )
            assert create_resp.status_code == 201
            org_id = create_resp.json()["id"]

            # Read full profile
            read_resp = client.get(
                f"/api/v1/organizations/{org_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert read_resp.status_code == 200
            data = read_resp.json()
            assert data["id"] == org_id
            assert data["legal_name"] == "Pacific Coast Importers LLC"
            assert data["display_name"] == "Pacific Coast"
            assert data["business_type"] == "IMPORTER"
            assert data["country"] == "US"
            assert data["address"] == "100 Ocean Blvd, Suite 400, Long Beach, CA 90802"
            assert data["tax_identifier"] == "EIN-12-3456789"
            assert data["vat_identifier"] == "US-VAT-9999"
            assert data["iec_number"] == "IEC-0102030405"
            assert data["website"] == "https://pacificcoasttrade.com"
            assert data["contact_information"] == "Phone: +1-555-0199, ops@pacificcoasttrade.com"
            assert data["verification_status"] == "UNVERIFIED"

    def test_update_company_profile_as_admin(
        self, client: TestClient, user_a_claims
    ):
        """ADMIN can update all mutable company profile fields."""
        with as_user(user_a_claims):
            create_resp = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Initial Name LLC", "country": "DE"},
                headers={"Authorization": "Bearer fake"},
            )
            org_id = create_resp.json()["id"]

            update_payload = {
                "legal_name": "Global Trade Solutions GmbH",
                "display_name": "GTS Global",
                "business_type": "BOTH",
                "country": "DE",
                "address": "Friedrichstraße 42, 10117 Berlin, Germany",
                "tax_identifier": "DE123456789",
                "vat_identifier": "DE987654321",
                "iec_number": "IEC-DE-9900",
                "website": "gts-global.de",  # will be normalized to https://gts-global.de
                "contact_information": "contact@gts-global.de | +49 30 123456",
            }

            patch_resp = client.patch(
                f"/api/v1/organizations/{org_id}",
                json=update_payload,
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 200
            data = patch_resp.json()
            assert data["legal_name"] == "Global Trade Solutions GmbH"
            assert data["display_name"] == "GTS Global"
            assert data["business_type"] == "BOTH"
            assert data["country"] == "DE"
            assert data["address"] == "Friedrichstraße 42, 10117 Berlin, Germany"
            assert data["tax_identifier"] == "DE123456789"
            assert data["vat_identifier"] == "DE987654321"
            assert data["iec_number"] == "IEC-DE-9900"
            assert data["website"] == "https://gts-global.de"
            assert data["contact_information"] == "contact@gts-global.de | +49 30 123456"

    def test_non_admin_cannot_update_company_profile(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """Non-admin members cannot update company profile (403)."""
        # First provision User B
        with as_user(user_b_claims):
            user_b_id = client.get(
                "/api/v1/users/me",
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

        # User A creates Org and invites User B as MEMBER
        with as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Admin Only LLC"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

            invite_resp = client.post(
                f"/api/v1/organizations/{org_id}/members",
                json={"user_id": user_b_id, "role": "MEMBER"},
                headers={"Authorization": "Bearer fake"},
            )
            assert invite_resp.status_code == 201

        # User B attempts to patch organization profile
        with as_user(user_b_claims):
            patch_resp = client.patch(
                f"/api/v1/organizations/{org_id}",
                json={"legal_name": "Tampered Name"},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 403
            assert "not permitted" in patch_resp.json()["detail"]

    def test_non_member_cannot_read_or_update_company_profile(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """Non-members cannot read or update organization company profile (403)."""
        # User A creates Org
        with as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Org Alpha"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

        # User B (non-member) attempts to read Org Alpha
        with as_user(user_b_claims):
            read_resp = client.get(
                f"/api/v1/organizations/{org_id}",
                headers={"Authorization": "Bearer fake"},
            )
            assert read_resp.status_code == 403

            patch_resp = client.patch(
                f"/api/v1/organizations/{org_id}",
                json={"legal_name": "Hacked Alpha"},
                headers={"Authorization": "Bearer fake"},
            )
            assert patch_resp.status_code == 403

    def test_company_profile_validation_rules(
        self, client: TestClient, user_a_claims
    ):
        """Server-side validation rejects invalid ISO country code, empty legal name, or malformed website."""
        with as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Validation Test LLC"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

            # Invalid country code (3 letters)
            res1 = client.patch(
                f"/api/v1/organizations/{org_id}",
                json={"country": "USA"},
                headers={"Authorization": "Bearer fake"},
            )
            assert res1.status_code == 422

            # Invalid country code (digits)
            res2 = client.patch(
                f"/api/v1/organizations/{org_id}",
                json={"country": "12"},
                headers={"Authorization": "Bearer fake"},
            )
            assert res2.status_code == 422

            # Empty legal name
            res3 = client.patch(
                f"/api/v1/organizations/{org_id}",
                json={"legal_name": "   "},
                headers={"Authorization": "Bearer fake"},
            )
            assert res3.status_code == 422

            # Invalid website (no dot)
            res4 = client.patch(
                f"/api/v1/organizations/{org_id}",
                json={"website": "nodotdomain"},
                headers={"Authorization": "Bearer fake"},
            )
            assert res4.status_code == 422
