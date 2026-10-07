"""
Phase B4 — Comprehensive Buyer & Supplier Search, Filtering, and Pagination Tests.

Covers all required test scenarios:
BUYER:
 1. authorized member can list buyers
 2. non-member cannot list buyers (403)
 3. unauthenticated request is rejected (401)
 4. q searches company_name
 5. q searches contact_name
 6. q searches email
 7. q is case-insensitive
 8. country filter works
 9. verification_status filter works
10. industry filter works
11. multiple filters combine correctly
12. default limit is 20
13. custom limit works
14. offset works
15. limit cannot exceed 100 (422)
16. negative offset is rejected (422)
17. invalid verification_status is rejected (422)
18. organization isolation is preserved
19. total represents total matching records before pagination
20. response contains the required pagination information (items, total, limit, offset)
21. empty result set
22. filters matching no records
23. invalid country code rejected (422)

SUPPLIER:
24. authorized member can list suppliers
25. non-member cannot list suppliers (403)
26. unauthenticated request is rejected (401)
27. q searches company_name
28. q searches contact_name
29. q searches email
30. q is case-insensitive
31. country filter works
32. verification_status filter works
33. supplier_type filter works
34. multiple filters combine correctly
35. default limit is 20
36. custom limit works
37. offset works
38. limit cannot exceed 100 (422)
39. negative offset is rejected (422)
40. invalid verification_status is rejected (422)
41. organization isolation is preserved
42. total represents total matching records before pagination
43. response contains the required pagination information
44. empty result set
45. filters matching no records
46. invalid country code rejected (422)
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
            json={"legal_name": "Search Org A Inc", "country": "US"},
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
            json={"legal_name": "Search Org B Ltd", "country": "GB"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]


@pytest.fixture
def seeded_buyers_org_a(client: TestClient, user_a_claims, org_a):
    """Seeds a diverse set of 5 buyers into Org A."""
    buyers_data = [
        {
            "company_name": "Alpha Logistics",
            "contact_name": "Alice Cooper",
            "email": "alice@alphalogistics.com",
            "country": "US",
            "industry": "Transportation",
            "verification_status": "VERIFIED",
        },
        {
            "company_name": "Beta Trading House",
            "contact_name": "Bob Martin",
            "email": "bob@betatrading.de",
            "country": "DE",
            "industry": "Wholesale",
            "verification_status": "PENDING",
        },
        {
            "company_name": "Gamma Tech Corp",
            "contact_name": "Charlie Chaplin",
            "email": "charlie@gammatech.jp",
            "country": "JP",
            "industry": "Electronics",
            "verification_status": "UNVERIFIED",
        },
        {
            "company_name": "Delta Electronics",
            "contact_name": "Diana Ross",
            "email": "diana@deltaelec.com",
            "country": "US",
            "industry": "Electronics",
            "verification_status": "VERIFIED",
        },
        {
            "company_name": "Epsilon Sourcing",
            "contact_name": "Edward Norton",
            "email": "edward@epsilonsource.us",
            "country": "US",
            "industry": "Retail",
            "verification_status": "SUSPENDED",
        },
    ]
    created = []
    with as_user(user_a_claims):
        for data in buyers_data:
            resp = client.post(
                f"/api/v1/organizations/{org_a}/buyers",
                json=data,
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            created.append(resp.json())
    return created


@pytest.fixture
def seeded_suppliers_org_a(client: TestClient, user_a_claims, org_a):
    """Seeds a diverse set of 5 suppliers into Org A."""
    suppliers_data = [
        {
            "company_name": "Apex Precision Parts",
            "contact_name": "Adam Smith",
            "email": "adam@apexprecision.com",
            "country": "US",
            "supplier_type": "MANUFACTURER",
            "verification_status": "VERIFIED",
        },
        {
            "company_name": "Baltic Timber Exporters",
            "contact_name": "Birgit Voolaid",
            "email": "birgit@baltictimber.ee",
            "country": "EE",
            "supplier_type": "EXPORTER",
            "verification_status": "PENDING",
        },
        {
            "company_name": "Canton Chip Foundry",
            "contact_name": "Chen Wei",
            "email": "chen@cantonchip.cn",
            "country": "CN",
            "supplier_type": "FACTORY",
            "verification_status": "UNVERIFIED",
        },
        {
            "company_name": "Danube Heavy Machinery",
            "contact_name": "Dieter Schmidt",
            "email": "dieter@danubemachinery.de",
            "country": "DE",
            "supplier_type": "MANUFACTURER",
            "verification_status": "VERIFIED",
        },
        {
            "company_name": "Everest Fasteners",
            "contact_name": "Emily Watson",
            "email": "emily@everestfasteners.us",
            "country": "US",
            "supplier_type": "TRADER",
            "verification_status": "SUSPENDED",
        },
    ]
    created = []
    with as_user(user_a_claims):
        for data in suppliers_data:
            resp = client.post(
                f"/api/v1/organizations/{org_a}/suppliers",
                json=data,
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 201
            created.append(resp.json())
    return created


class TestBuyerSearchFilteringPagination:
    def test_01_authorized_member_can_list_buyers(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 5
            assert len(data["items"]) == 5
            assert data["limit"] == 20
            assert data["offset"] == 0

    def test_02_non_member_cannot_list_buyers(self, client: TestClient, user_b_claims, org_a):
        with as_user(user_b_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403
            assert resp.json()["detail"] == "Access denied: you are not a member of this organization."

    def test_03_unauthenticated_request_is_rejected(self, client: TestClient, org_a):
        resp = client.get(f"/api/v1/organizations/{org_a}/buyers")
        assert resp.status_code == 401

    def test_04_q_searches_company_name(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?q=Gamma",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["company_name"] == "Gamma Tech Corp"

    def test_05_q_searches_contact_name(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?q=Chaplin",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["contact_name"] == "Charlie Chaplin"

    def test_06_q_searches_email(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?q=deltaelec.com",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["company_name"] == "Delta Electronics"

    def test_07_q_is_case_insensitive(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?q=alpha",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["company_name"] == "Alpha Logistics"

    def test_08_country_filter_works(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            # Country US has 3 buyers
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?country=US",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 3
            assert all(item["country"] == "US" for item in data["items"])

    def test_09_verification_status_filter_works(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            # VERIFIED has 2 buyers (Alpha Logistics, Delta Electronics)
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?verification_status=VERIFIED",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert all(item["verification_status"] == "VERIFIED" for item in data["items"])

    def test_10_industry_filter_works(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            # Electronics has 2 buyers (Gamma Tech Corp, Delta Electronics)
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?industry=Electronics",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert all(item["industry"] == "Electronics" for item in data["items"])

    def test_11_multiple_filters_combine_correctly(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            # Country US + Industry Electronics + VERIFIED -> Delta Electronics (1 match)
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?country=US&industry=Electronics&verification_status=VERIFIED",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["company_name"] == "Delta Electronics"

    def test_12_default_limit_is_20(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            assert resp.json()["limit"] == 20

    def test_13_custom_limit_works(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?limit=2",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 5
            assert len(data["items"]) == 2
            assert data["limit"] == 2

    def test_14_offset_works(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            # Fetch all 5
            all_resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?limit=5",
                headers={"Authorization": "Bearer fake"},
            )
            all_ids = [item["id"] for item in all_resp.json()["items"]]

            # Fetch with offset 2, limit 2
            page_resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?offset=2&limit=2",
                headers={"Authorization": "Bearer fake"},
            )
            page_data = page_resp.json()
            assert page_data["total"] == 5
            assert len(page_data["items"]) == 2
            page_ids = [item["id"] for item in page_data["items"]]
            assert page_ids == all_ids[2:4]

    def test_15_limit_cannot_exceed_100(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?limit=101",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422

    def test_16_negative_offset_is_rejected(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?offset=-1",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422

    def test_17_invalid_verification_status_is_rejected(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?verification_status=UNKNOWN",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422

    def test_18_organization_isolation_is_preserved(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, seeded_buyers_org_a
    ):
        # Create 2 buyers in Org B
        with as_user(user_b_claims):
            client.post(
                f"/api/v1/organizations/{org_b}/buyers",
                json={"company_name": "Org B Buyer One"},
                headers={"Authorization": "Bearer fake"},
            )
            client.post(
                f"/api/v1/organizations/{org_b}/buyers",
                json={"company_name": "Org B Buyer Two"},
                headers={"Authorization": "Bearer fake"},
            )

        # Org A list must see strictly 5 items, zero from Org B
        with as_user(user_a_claims):
            resp_a = client.get(
                f"/api/v1/organizations/{org_a}/buyers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_a.status_code == 200
            data_a = resp_a.json()
            assert data_a["total"] == 5
            for item in data_a["items"]:
                assert item["organization_id"] == org_a

        # Org B list must see strictly 2 items, zero from Org A
        with as_user(user_b_claims):
            resp_b = client.get(
                f"/api/v1/organizations/{org_b}/buyers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b.status_code == 200
            data_b = resp_b.json()
            assert data_b["total"] == 2
            for item in data_b["items"]:
                assert item["organization_id"] == org_b

    def test_19_total_represents_total_matching_records_before_pagination(
        self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a
    ):
        with as_user(user_a_claims):
            # Filter country=US matches 3 buyers, but requesting limit=1
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?country=US&limit=1",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 3
            assert len(data["items"]) == 1
            assert data["limit"] == 1

    def test_20_response_contains_the_required_pagination_information(
        self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a
    ):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?limit=10&offset=0",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "items" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert isinstance(data["items"], list)
            assert isinstance(data["total"], int)
            assert data["limit"] == 10
            assert data["offset"] == 0

    def test_21_empty_result_set(self, client: TestClient, user_b_claims, org_b):
        """Org B with zero buyers returns clean empty pagination response."""
        with as_user(user_b_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_b}/buyers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0
            assert data["items"] == []

    def test_22_filters_matching_no_records(self, client: TestClient, user_a_claims, org_a, seeded_buyers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?q=NonExistentCompanyXYZ",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0
            assert data["items"] == []

    def test_23_invalid_country_code_rejected(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            # 3-letter country code
            resp = client.get(
                f"/api/v1/organizations/{org_a}/buyers?country=USA",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422

            # Numeric country code
            resp2 = client.get(
                f"/api/v1/organizations/{org_a}/buyers?country=12",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp2.status_code == 422


class TestSupplierSearchFilteringPagination:
    def test_24_authorized_member_can_list_suppliers(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 5
            assert len(data["items"]) == 5
            assert data["limit"] == 20
            assert data["offset"] == 0

    def test_25_non_member_cannot_list_suppliers(self, client: TestClient, user_b_claims, org_a):
        with as_user(user_b_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 403
            assert resp.json()["detail"] == "Access denied: you are not a member of this organization."

    def test_26_unauthenticated_request_is_rejected(self, client: TestClient, org_a):
        resp = client.get(f"/api/v1/organizations/{org_a}/suppliers")
        assert resp.status_code == 401

    def test_27_q_searches_company_name(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?q=Baltic",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["company_name"] == "Baltic Timber Exporters"

    def test_28_q_searches_contact_name(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?q=Dieter",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["contact_name"] == "Dieter Schmidt"

    def test_29_q_searches_email(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?q=cantonchip.cn",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["company_name"] == "Canton Chip Foundry"

    def test_30_q_is_case_insensitive(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?q=apex",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["company_name"] == "Apex Precision Parts"

    def test_31_country_filter_works(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            # Country US has 2 suppliers (Apex Precision Parts, Everest Fasteners)
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?country=US",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert all(item["country"] == "US" for item in data["items"])

    def test_32_verification_status_filter_works(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            # VERIFIED has 2 suppliers (Apex Precision Parts, Danube Heavy Machinery)
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?verification_status=VERIFIED",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert all(item["verification_status"] == "VERIFIED" for item in data["items"])

    def test_33_supplier_type_filter_works(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            # MANUFACTURER has 2 suppliers (Apex Precision Parts, Danube Heavy Machinery)
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?supplier_type=MANUFACTURER",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert all(item["supplier_type"] == "MANUFACTURER" for item in data["items"])

    def test_34_multiple_filters_combine_correctly(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            # Country US + supplier_type MANUFACTURER + verification_status VERIFIED -> Apex Precision Parts
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?country=US&supplier_type=MANUFACTURER&verification_status=VERIFIED",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["company_name"] == "Apex Precision Parts"

    def test_35_default_limit_is_20(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            assert resp.json()["limit"] == 20

    def test_36_custom_limit_works(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?limit=2",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 5
            assert len(data["items"]) == 2
            assert data["limit"] == 2

    def test_37_offset_works(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            all_resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?limit=5",
                headers={"Authorization": "Bearer fake"},
            )
            all_ids = [item["id"] for item in all_resp.json()["items"]]

            page_resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?offset=2&limit=2",
                headers={"Authorization": "Bearer fake"},
            )
            page_data = page_resp.json()
            assert page_data["total"] == 5
            assert len(page_data["items"]) == 2
            page_ids = [item["id"] for item in page_data["items"]]
            assert page_ids == all_ids[2:4]

    def test_38_limit_cannot_exceed_100(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?limit=101",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422

    def test_39_negative_offset_is_rejected(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?offset=-1",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422

    def test_40_invalid_verification_status_is_rejected(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?verification_status=UNKNOWN",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422

    def test_41_organization_isolation_is_preserved(
        self, client: TestClient, user_a_claims, user_b_claims, org_a, org_b, seeded_suppliers_org_a
    ):
        with as_user(user_b_claims):
            client.post(
                f"/api/v1/organizations/{org_b}/suppliers",
                json={"company_name": "Org B Supplier Alpha"},
                headers={"Authorization": "Bearer fake"},
            )

        with as_user(user_a_claims):
            resp_a = client.get(
                f"/api/v1/organizations/{org_a}/suppliers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_a.status_code == 200
            data_a = resp_a.json()
            assert data_a["total"] == 5
            for item in data_a["items"]:
                assert item["organization_id"] == org_a

        with as_user(user_b_claims):
            resp_b = client.get(
                f"/api/v1/organizations/{org_b}/suppliers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp_b.status_code == 200
            data_b = resp_b.json()
            assert data_b["total"] == 1
            assert data_b["items"][0]["organization_id"] == org_b

    def test_42_total_represents_total_matching_records_before_pagination(
        self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a
    ):
        with as_user(user_a_claims):
            # Country US matches 2 suppliers, requesting limit=1
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?country=US&limit=1",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert len(data["items"]) == 1
            assert data["limit"] == 1

    def test_43_response_contains_the_required_pagination_information(
        self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a
    ):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?limit=10&offset=0",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "items" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert isinstance(data["items"], list)
            assert isinstance(data["total"], int)
            assert data["limit"] == 10
            assert data["offset"] == 0

    def test_44_empty_result_set(self, client: TestClient, user_b_claims, org_b):
        with as_user(user_b_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_b}/suppliers",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0
            assert data["items"] == []

    def test_45_filters_matching_no_records(self, client: TestClient, user_a_claims, org_a, seeded_suppliers_org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?q=NonExistentSupplierXYZ",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0
            assert data["items"] == []

    def test_46_invalid_country_code_rejected(self, client: TestClient, user_a_claims, org_a):
        with as_user(user_a_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_a}/suppliers?country=DEU",
                headers={"Authorization": "Bearer fake"},
            )
            assert resp.status_code == 422
