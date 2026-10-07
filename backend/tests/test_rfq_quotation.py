"""
Comprehensive end-to-end API tests for RFQ, Supplier Invitations, Quotations,
Comparison, Awarding, and Negotiation Notes.

Covers:
- Tenant isolation & organization boundaries
- Supplier invitation enforcement & duplicate prevention
- Competitor quotation isolation
- Immutability of submitted quotations & versioning lineage (V1 SUPERSEDED -> V2)
- State transitions (valid transitions & rejection of invalid ones)
- Deterministic Decimal calculations & landed cost comparison
- Awarding atomicity
- Crucial Security Tests:
  TEST 1: Supplier A cannot retrieve Supplier B quotation.
  TEST 2: Supplier A cannot access buyer quotation comparison.
  TEST 3: Organization A cannot retrieve Organization B RFQ.
  TEST 4: Organization A cannot retrieve Organization B quotations.
  TEST 5: Supplier cannot submit quotation without an invitation.
  TEST 6: Quotation item belonging to RFQ B cannot be inserted into a quotation belonging to RFQ A.
"""
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from tests.conftest import as_user, _make_claims
from app.services.rfq_calculations import calculate_line_total, calculate_quotation_totals


def _create_org(client: TestClient, user_claims: dict, legal_name: str) -> dict:
    with as_user(user_claims):
        res = client.post(
            "/api/v1/organizations/",
            json={"legal_name": legal_name, "country": "US"},
        )
        assert res.status_code == 201
        return res.json()


def _add_member(
    client: TestClient, admin_claims: dict, org_id: str, member_claims: dict, role: str
) -> dict:
    with as_user(member_claims):
        u = client.get("/api/v1/users/me").json()
        user_id = u["id"]
    with as_user(admin_claims):
        res = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"user_id": user_id, "role": role},
        )
        assert res.status_code == 201
        return res.json()


class TestRFQEndpoints:
    def test_create_and_read_rfq(self, client):
        buyer_claims = _make_claims("auth0|buyer-1", "buyer1@example.com", "Buyer 1")
        org = _create_org(client, buyer_claims, "Buyer Corp")
        org_id = org["id"]

        with as_user(buyer_claims):
            # 1. Create RFQ
            payload = {
                "title": "Industrial Stainless Steel Valves",
                "description": "API 6D Ball Valves 2 inch Class 150",
                "destination_country": "DE",
                "destination_port": "Hamburg",
                "preferred_incoterm": "CIF",
                "preferred_payment_terms": "LC at sight",
                "currency": "USD",
                "items": [
                    {
                        "item_index": 1,
                        "product_name_snapshot": "Ball Valve 2in CL150",
                        "quantity": "500.00",
                        "unit": "PCS",
                        "target_unit_price": "120.0000",
                        "specifications": "Stainless Steel 316 Body",
                    }
                ],
            }
            res = client.post(f"/api/v1/organizations/{org_id}/rfqs/", json=payload)
            assert res.status_code == 201
            rfq_data = res.json()
            assert rfq_data["title"] == "Industrial Stainless Steel Valves"
            assert rfq_data["status"] == "DRAFT"
            assert len(rfq_data["items"]) == 1
            assert rfq_data["items"][0]["quantity"] == "500.00"
            rfq_id = rfq_data["id"]

            # 2. Get detail
            get_res = client.get(f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}")
            assert get_res.status_code == 200
            assert get_res.json()["rfq_number"].startswith("RFQ-")

            # 3. List RFQs
            list_res = client.get(f"/api/v1/organizations/{org_id}/rfqs/")
            assert list_res.status_code == 200
            assert len(list_res.json()) >= 1

    def test_rfq_state_machine_valid_and_invalid(self, client):
        buyer_claims = _make_claims("auth0|buyer-state", "b_state@example.com", "Buyer State")
        org = _create_org(client, buyer_claims, "State Machine Org")
        org_id = org["id"]

        with as_user(buyer_claims):
            # Create DRAFT
            rfq_res = client.post(
                f"/api/v1/organizations/{org_id}/rfqs/",
                json={
                    "title": "Test State RFQ",
                    "destination_country": "US",
                    "items": [
                        {
                            "product_name_snapshot": "Test Item",
                            "quantity": "100.00",
                            "unit": "PCS",
                        }
                    ],
                },
            )
            rfq_id = rfq_res.json()["id"]

            # Valid: DRAFT -> OPEN
            open_res = client.post(f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}/open")
            assert open_res.status_code == 200
            assert open_res.json()["status"] == "OPEN"

            # Invalid: cannot open already OPEN RFQ
            invalid_open = client.post(f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}/open")
            assert invalid_open.status_code == 400

            # Valid: OPEN -> CANCELLED
            cancel_res = client.post(f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}/cancel")
            assert cancel_res.status_code == 200
            assert cancel_res.json()["status"] == "CANCELLED"

            # Invalid: cannot cancel terminal CANCELLED RFQ
            invalid_cancel = client.post(f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}/cancel")
            assert invalid_cancel.status_code == 400

    def test_org_isolation_rfq_cannot_be_read_by_other_org(self, client):
        """TEST 3: Organization A cannot retrieve Organization B RFQ."""
        buyer_a_claims = _make_claims("auth0|buyer-a", "ba@example.com", "Buyer A")
        buyer_b_claims = _make_claims("auth0|buyer-b", "bb@example.com", "Buyer B")

        org_a = _create_org(client, buyer_a_claims, "Org A")
        org_b = _create_org(client, buyer_b_claims, "Org B")

        # Org A creates RFQ
        with as_user(buyer_a_claims):
            rfq_res = client.post(
                f"/api/v1/organizations/{org_a['id']}/rfqs/",
                json={
                    "title": "Confidential Org A RFQ",
                    "destination_country": "CA",
                    "items": [{"product_name_snapshot": "Item A", "quantity": "10.00", "unit": "PCS"}],
                },
            )
            rfq_a_id = rfq_res.json()["id"]

        # User B attempts to access Org A's RFQ
        with as_user(buyer_b_claims):
            # Via Org A path
            denied_a_path = client.get(f"/api/v1/organizations/{org_a['id']}/rfqs/{rfq_a_id}")
            assert denied_a_path.status_code == 403

            # Via Org B path
            denied_b_path = client.get(f"/api/v1/organizations/{org_b['id']}/rfqs/{rfq_a_id}")
            assert denied_b_path.status_code == 404


class TestSupplierInvitations:
    def test_invite_supplier_and_duplicate_rejected(self, client):
        buyer_claims = _make_claims("auth0|buyer-inv", "binv@example.com", "Buyer Inv")
        org = _create_org(client, buyer_claims, "Invite Org")
        org_id = org["id"]

        with as_user(buyer_claims):
            # Create & Open RFQ
            rfq_res = client.post(
                f"/api/v1/organizations/{org_id}/rfqs/",
                json={
                    "title": "Solar Inverters",
                    "destination_country": "NL",
                    "items": [{"product_name_snapshot": "Inverter 10kW", "quantity": "20.00", "unit": "PCS"}],
                },
            )
            rfq_id = rfq_res.json()["id"]
            client.post(f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}/open")

            # Invite supplier 1
            inv_payload = {
                "invitations": [
                    {
                        "supplier_email": "supplier1@solar.de",
                        "supplier_name": "SolarTech GmbH",
                    }
                ]
            }
            inv_res = client.post(
                f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}/invitations",
                json=inv_payload,
            )
            assert inv_res.status_code == 201
            assert len(inv_res.json()) == 1
            assert inv_res.json()[0]["supplier_email"] == "supplier1@solar.de"

            # Verify RFQ transitioned to INVITATIONS_SENT
            rfq_check = client.get(f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}").json()
            assert rfq_check["status"] == "INVITIONS_SENT" or rfq_check["status"] == "INVITATIONS_SENT"

            # Duplicate invitation for same supplier_email on same RFQ must be rejected with 409
            dup_res = client.post(
                f"/api/v1/organizations/{org_id}/rfqs/{rfq_id}/invitations",
                json=inv_payload,
            )
            assert dup_res.status_code == 409


class TestQuotationLifecycleAndSecurity:
    def _setup_rfq_and_invitations(self, client):
        buyer_claims = _make_claims("auth0|buyer-full", "bfull@example.com", "Buyer Full")
        sup1_claims = _make_claims("auth0|sup-1", "sup1@example.com", "Supplier 1 User")
        sup2_claims = _make_claims("auth0|sup-2", "sup2@example.com", "Supplier 2 User")

        buyer_org = _create_org(client, buyer_claims, "Buyer Corp")
        sup1_org = _create_org(client, sup1_claims, "Supplier 1 Corp")
        sup2_org = _create_org(client, sup2_claims, "Supplier 2 Corp")

        with as_user(buyer_claims):
            rfq_res = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/",
                json={
                    "title": "Industrial Pumps",
                    "destination_country": "US",
                    "items": [
                        {
                            "item_index": 1,
                            "product_name_snapshot": "Centrifugal Pump 5HP",
                            "quantity": "100.00",
                            "unit": "PCS",
                            "target_unit_price": "250.0000",
                        }
                    ],
                },
            )
            rfq_id = rfq_res.json()["id"]
            rfq_item_id = rfq_res.json()["items"][0]["id"]
            client.post(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/open")

            # Invite Supplier 1 (with supplier_organization_id)
            client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/invitations",
                json={
                    "invitations": [
                        {
                            "supplier_email": "sup1@example.com",
                            "supplier_name": "Supplier 1 Corp",
                            "supplier_organization_id": sup1_org["id"],
                        }
                    ]
                },
            )

        return {
            "buyer_claims": buyer_claims,
            "sup1_claims": sup1_claims,
            "sup2_claims": sup2_claims,
            "buyer_org": buyer_org,
            "sup1_org": sup1_org,
            "sup2_org": sup2_org,
            "rfq_id": rfq_id,
            "rfq_item_id": rfq_item_id,
        }

    def test_supplier_cannot_quote_without_invitation(self, client):
        """TEST 5: Supplier cannot submit quotation without an invitation."""
        ctx = self._setup_rfq_and_invitations(client)
        # Supplier 2 was NOT invited to the RFQ
        with as_user(ctx["sup2_claims"]):
            quote_payload = {
                "incoterm": "FOB",
                "payment_terms": "Net 30",
                "lead_time_days": 15,
                "items": [
                    {
                        "rfq_item_id": ctx["rfq_item_id"],
                        "unit_price": "240.0000",
                    }
                ],
            }
            res = client.post(
                f"/api/v1/organizations/{ctx['sup2_org']['id']}/supplier/rfqs/{ctx['rfq_id']}/quotations",
                json=quote_payload,
            )
            assert res.status_code == 403
            assert "not been invited" in res.json()["detail"].lower()

    def test_item_from_another_rfq_rejected(self, client):
        """TEST 6: Quotation item belonging to RFQ B cannot be inserted into quotation for RFQ A."""
        ctx = self._setup_rfq_and_invitations(client)

        # Buyer creates another RFQ B with item B
        with as_user(ctx["buyer_claims"]):
            rfq_b = client.post(
                f"/api/v1/organizations/{ctx['buyer_org']['id']}/rfqs/",
                json={
                    "title": "RFQ B",
                    "destination_country": "US",
                    "items": [{"product_name_snapshot": "Item B", "quantity": "50.00", "unit": "PCS"}],
                },
            ).json()
            rfq_b_item_id = rfq_b["items"][0]["id"]

        # Invited Supplier 1 tries to submit quote for RFQ A using item from RFQ B
        with as_user(ctx["sup1_claims"]):
            malicious_payload = {
                "incoterm": "FOB",
                "payment_terms": "Net 30",
                "lead_time_days": 10,
                "items": [
                    {
                        "rfq_item_id": rfq_b_item_id,  # From RFQ B!
                        "unit_price": "240.0000",
                    }
                ],
            }
            res = client.post(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/rfqs/{ctx['rfq_id']}/quotations",
                json=malicious_payload,
            )
            assert res.status_code == 400
            assert "does not belong to rfq" in res.json()["detail"].lower()

    def test_supplier_draft_edit_and_submission_immutability(self, client):
        """Verify draft can be edited, but once submitted is immutable."""
        ctx = self._setup_rfq_and_invitations(client)

        with as_user(ctx["sup1_claims"]):
            # 1. Create draft quotation
            create_res = client.post(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/rfqs/{ctx['rfq_id']}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "T/T 30/70",
                    "lead_time_days": 20,
                    "shipping_cost": "1000.00",
                    "insurance_cost": "200.00",
                    "items": [
                        {
                            "rfq_item_id": ctx["rfq_item_id"],
                            "unit_price": "220.0000",
                            "quantity": "100.00",
                        }
                    ],
                },
            )
            assert create_res.status_code == 201
            quote = create_res.json()
            quote_id = quote["id"]
            assert quote["status"] == "DRAFT"
            assert Decimal(quote["subtotal_amount"]) == Decimal("22000.00")
            assert Decimal(quote["total_landed_cost"]) == Decimal("23200.00")

            # 2. Patch draft (allowed)
            patch_res = client.patch(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/quotations/{quote_id}",
                json={"lead_time_days": 18, "shipping_cost": "900.00"},
            )
            assert patch_res.status_code == 200
            assert patch_res.json()["lead_time_days"] == 18
            assert Decimal(patch_res.json()["total_landed_cost"]) == Decimal("23100.00")

            # 3. Formally Submit
            submit_res = client.post(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/quotations/{quote_id}/submit"
            )
            assert submit_res.status_code == 200
            assert submit_res.json()["status"] == "SUBMITTED"

            # 4. Attempt PATCH after submission (MUST BE REJECTED)
            failed_patch = client.patch(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/quotations/{quote_id}",
                json={"shipping_cost": "500.00"},
            )
            assert failed_patch.status_code == 400
            assert "immutable" in failed_patch.json()["detail"].lower()

    def test_quotation_revision_creates_new_version(self, client):
        """Verify revision creates V2 with parent pointer and supersedes V1."""
        ctx = self._setup_rfq_and_invitations(client)

        with as_user(ctx["sup1_claims"]):
            # Create & Submit V1
            c_res = client.post(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/rfqs/{ctx['rfq_id']}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "Net 30",
                    "lead_time_days": 25,
                    "items": [{"rfq_item_id": ctx["rfq_item_id"], "unit_price": "230.0000"}],
                },
            )
            q1_id = c_res.json()["id"]
            client.post(f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/quotations/{q1_id}/submit")

            # Revise to create V2
            rev_res = client.post(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/quotations/{q1_id}/revise",
                json={
                    "incoterm": "CIF",
                    "payment_terms": "Net 45",
                    "lead_time_days": 20,
                    "items": [{"rfq_item_id": ctx["rfq_item_id"], "unit_price": "225.0000"}],
                },
            )
            assert rev_res.status_code == 201
            q2 = rev_res.json()
            assert q2["version"] == 2
            assert q2["parent_quotation_id"] == q1_id
            assert q2["status"] == "SUBMITTED"

            # Check V1 is now SUPERSEDED
            v1_check = client.get(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/quotations/{q1_id}"
            ).json()
            assert v1_check["status"] == "SUPERSEDED"

    def test_supplier_a_cannot_access_supplier_b_quotation(self, client):
        """TEST 1: Supplier A cannot retrieve Supplier B quotation."""
        ctx = self._setup_rfq_and_invitations(client)

        # Invite Supplier 2 as well
        with as_user(ctx["buyer_claims"]):
            client.post(
                f"/api/v1/organizations/{ctx['buyer_org']['id']}/rfqs/{ctx['rfq_id']}/invitations",
                json={
                    "invitations": [
                        {
                            "supplier_email": "sup2@example.com",
                            "supplier_name": "Supplier 2 Corp",
                            "supplier_organization_id": ctx["sup2_org"]["id"],
                        }
                    ]
                },
            )

        # Supplier 1 submits Quote 1
        with as_user(ctx["sup1_claims"]):
            q1 = client.post(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/rfqs/{ctx['rfq_id']}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "Net 30",
                    "lead_time_days": 10,
                    "items": [{"rfq_item_id": ctx["rfq_item_id"], "unit_price": "200.0000"}],
                },
            ).json()
            client.post(f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/quotations/{q1['id']}/submit")

        # Supplier 2 attempts to retrieve Supplier 1's quotation
        with as_user(ctx["sup2_claims"]):
            # Via Supplier 2 org path
            res = client.get(
                f"/api/v1/organizations/{ctx['sup2_org']['id']}/supplier/quotations/{q1['id']}"
            )
            assert res.status_code == 403

            # Via Supplier 1 org path
            res_cross = client.get(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/quotations/{q1['id']}"
            )
            assert res_cross.status_code == 403

    def test_supplier_cannot_access_buyer_comparison(self, client):
        """TEST 2: Supplier A cannot access buyer quotation comparison."""
        ctx = self._setup_rfq_and_invitations(client)

        with as_user(ctx["sup1_claims"]):
            # Supplier attempts to access buyer quotation comparison endpoint
            comp_res = client.get(
                f"/api/v1/organizations/{ctx['buyer_org']['id']}/rfqs/{ctx['rfq_id']}/comparison"
            )
            assert comp_res.status_code == 403

            # Supplier attempts to list all quotations for the RFQ
            quotes_res = client.get(
                f"/api/v1/organizations/{ctx['buyer_org']['id']}/rfqs/{ctx['rfq_id']}/quotations"
            )
            assert quotes_res.status_code == 403

    def test_other_org_cannot_access_quotations(self, client):
        """TEST 4: Organization A cannot retrieve Organization B quotations."""
        ctx = self._setup_rfq_and_invitations(client)
        stranger_claims = _make_claims("auth0|stranger", "stranger@example.com", "Stranger")
        stranger_org = _create_org(client, stranger_claims, "Stranger Corp")

        with as_user(ctx["sup1_claims"]):
            q = client.post(
                f"/api/v1/organizations/{ctx['sup1_org']['id']}/supplier/rfqs/{ctx['rfq_id']}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "Net 30",
                    "lead_time_days": 10,
                    "items": [{"rfq_item_id": ctx["rfq_item_id"], "unit_price": "210.0000"}],
                },
            ).json()

        with as_user(stranger_claims):
            # Stranger attempts to view buyer quotations
            b_res = client.get(f"/api/v1/organizations/{ctx['buyer_org']['id']}/rfqs/{ctx['rfq_id']}/quotations")
            assert b_res.status_code == 403

            # Stranger attempts to view supplier quotation
            s_res = client.get(f"/api/v1/organizations/{stranger_org['id']}/supplier/quotations/{q['id']}")
            assert s_res.status_code == 403


class TestComparisonAndAwarding:
    def test_quotation_comparison_and_award_lifecycle(self, client):
        buyer_claims = _make_claims("auth0|b-comp", "bcomp@example.com", "Buyer Comp")
        sup1_claims = _make_claims("auth0|s1-comp", "s1comp@example.com", "Supplier 1")
        sup2_claims = _make_claims("auth0|s2-comp", "s2comp@example.com", "Supplier 2")

        buyer_org = _create_org(client, buyer_claims, "Buyer Comp Corp")
        sup1_org = _create_org(client, sup1_claims, "Supplier 1 Comp")
        sup2_org = _create_org(client, sup2_claims, "Supplier 2 Comp")

        with as_user(buyer_claims):
            rfq = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/",
                json={
                    "title": "Industrial Electric Motors",
                    "destination_country": "US",
                    "items": [
                        {
                            "item_index": 1,
                            "product_name_snapshot": "AC Motor 10HP",
                            "quantity": "10.00",
                            "unit": "PCS",
                        }
                    ],
                },
            ).json()
            rfq_id = rfq["id"]
            rfq_item_id = rfq["items"][0]["id"]
            client.post(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/open")

            client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/invitations",
                json={
                    "invitations": [
                        {"supplier_email": "s1comp@example.com", "supplier_name": "S1", "supplier_organization_id": sup1_org["id"]},
                        {"supplier_email": "s2comp@example.com", "supplier_name": "S2", "supplier_organization_id": sup2_org["id"]},
                    ]
                },
            )

        # Supplier 1 submits quote: lower unit price, higher shipping
        # Unit price: 500, Qty: 10 = Subtotal 5000 + Shipping 1000 = Landed 6000. Lead: 20 days.
        with as_user(sup1_claims):
            q1 = client.post(
                f"/api/v1/organizations/{sup1_org['id']}/supplier/rfqs/{rfq_id}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "T/T 30/70",
                    "lead_time_days": 20,
                    "shipping_cost": "1000.00",
                    "items": [{"rfq_item_id": rfq_item_id, "unit_price": "500.0000"}],
                },
            ).json()
            client.post(f"/api/v1/organizations/{sup1_org['id']}/supplier/quotations/{q1['id']}/submit")

        # Supplier 2 submits quote: higher unit price, lower shipping -> LOWER LANDED COST!
        # Unit price: 520, Qty: 10 = Subtotal 5200 + Shipping 200 = Landed 5400. Lead: 10 days (faster).
        with as_user(sup2_claims):
            q2 = client.post(
                f"/api/v1/organizations/{sup2_org['id']}/supplier/rfqs/{rfq_id}/quotations",
                json={
                    "incoterm": "CIF",
                    "payment_terms": "Net 30",
                    "lead_time_days": 10,
                    "shipping_cost": "200.00",
                    "items": [{"rfq_item_id": rfq_item_id, "unit_price": "520.0000"}],
                },
            ).json()

        # Attempt to award Q2 while still in DRAFT status -> MUST FAIL with 400
        with as_user(buyer_claims):
            fail_draft = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/award/{q2['id']}"
            )
            assert fail_draft.status_code == 400
            assert "DRAFT" in fail_draft.json()["detail"]

        with as_user(sup2_claims):
            client.post(f"/api/v1/organizations/{sup2_org['id']}/supplier/quotations/{q2['id']}/submit")

        # Buyer compares quotes side-by-side
        with as_user(buyer_claims):
            comp_res = client.get(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/comparison")
            assert comp_res.status_code == 200
            comp = comp_res.json()
            assert comp["quotation_count"] == 2
            assert comp["currency_consistent"] is True

            # Unit price check: Q1 has lower unit price
            assert comp["items_comparison"][0]["lowest_unit_price_quotation_id"] == q1["id"]
            # Subtotal check: Q1 has lower subtotal (5000 vs 5200)
            assert comp["lowest_subtotal_quotation_id"] == q1["id"]
            # Landed cost check: Q2 has lower landed cost (5400 vs 6000)
            assert comp["lowest_landed_cost_quotation_id"] == q2["id"]
            # Delivery check: Q2 is faster (10 days vs 20 days)
            assert comp["fastest_delivery_quotation_id"] == q2["id"]

            # Award Q2
            award_res = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/award/{q2['id']}"
            )
            assert award_res.status_code == 200
            awarded_rfq = award_res.json()
            assert awarded_rfq["status"] == "AWARDED"
            assert awarded_rfq["awarded_quotation_id"] == q2["id"]

        # Verify Q2 is ACCEPTED and Q1 is REJECTED
        with as_user(sup2_claims):
            q2_check = client.get(
                f"/api/v1/organizations/{sup2_org['id']}/supplier/quotations/{q2['id']}"
            ).json()
            assert q2_check["status"] == "ACCEPTED"

        with as_user(sup1_claims):
            q1_check = client.get(
                f"/api/v1/organizations/{sup1_org['id']}/supplier/quotations/{q1['id']}"
            ).json()
            assert q1_check["status"] == "REJECTED"


class TestNegotiationNotes:
    def test_counter_offer_and_timeline(self, client):
        buyer_claims = _make_claims("auth0|b-neg", "bneg@example.com", "Buyer Neg")
        sup_claims = _make_claims("auth0|s-neg", "sneg@example.com", "Supplier Neg")

        buyer_org = _create_org(client, buyer_claims, "Buyer Neg Corp")
        sup_org = _create_org(client, sup_claims, "Supplier Neg Corp")

        with as_user(buyer_claims):
            rfq = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/",
                json={
                    "title": "Raw Cotton Bales",
                    "destination_country": "VN",
                    "items": [{"product_name_snapshot": "Cotton Grade A", "quantity": "1000.00", "unit": "KG"}],
                },
            ).json()
            rfq_id = rfq["id"]
            rfq_item_id = rfq["items"][0]["id"]
            client.post(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/open")
            client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/invitations",
                json={
                    "invitations": [
                        {"supplier_email": "sneg@example.com", "supplier_name": "Sup", "supplier_organization_id": sup_org["id"]}
                    ]
                },
            )

        with as_user(sup_claims):
            q = client.post(
                f"/api/v1/organizations/{sup_org['id']}/supplier/rfqs/{rfq_id}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "Net 30",
                    "lead_time_days": 14,
                    "items": [{"rfq_item_id": rfq_item_id, "unit_price": "2.5000"}],
                },
            ).json()
            client.post(f"/api/v1/organizations/{sup_org['id']}/supplier/quotations/{q['id']}/submit")

        # Buyer posts counter-offer
        with as_user(buyer_claims):
            note_res = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/quotations/{q['id']}/negotiation-notes",
                json={
                    "note_type": "COUNTER_OFFER",
                    "proposed_target_price": "2.3000",
                    "proposed_terms": "Net 45",
                    "message": "Can you offer 2.30 USD/kg for 1,000kg with Net 45 payment terms?",
                },
            )
            assert note_res.status_code == 201
            assert note_res.json()["note_type"] == "COUNTER_OFFER"
            assert Decimal(note_res.json()["proposed_target_price"]) == Decimal("2.3000")

            # Check timeline
            timeline = client.get(
                f"/api/v1/organizations/{buyer_org['id']}/quotations/{q['id']}/negotiation-notes"
            ).json()
            assert len(timeline) == 1

        # Supplier views timeline and posts response
        with as_user(sup_claims):
            s_timeline = client.get(
                f"/api/v1/organizations/{sup_org['id']}/quotations/{q['id']}/negotiation-notes"
            ).json()
            assert len(s_timeline) == 1
            assert s_timeline[0]["message"].startswith("Can you offer 2.30")

            reply = client.post(
                f"/api/v1/organizations/{sup_org['id']}/quotations/{q['id']}/negotiation-notes",
                json={
                    "note_type": "SUPPLIER_RESPONSE",
                    "proposed_target_price": "2.3500",
                    "proposed_terms": "Net 30",
                    "message": "We can meet at 2.35 USD/kg with Net 30.",
                },
            )
            assert reply.status_code == 201
            assert reply.json()["note_type"] == "SUPPLIER_RESPONSE"

    def test_buyer_member_role_can_read_quotes_but_cannot_award(self, client):
        """
        Verify:
        - Active MEMBER of RFQ-owning buyer org has read-only access to quotes & comparison.
        - Active MEMBER cannot execute award mutation (receives 403 Forbidden).
        """
        admin_claims = _make_claims("auth0|b-admin-rbac", "badmin@example.com", "Admin Bob")
        member_claims = _make_claims("auth0|b-member-rbac", "bmember@example.com", "Member Mary")
        sup_claims = _make_claims("auth0|s-rbac", "srbac@example.com", "Supplier Sam")

        buyer_org = _create_org(client, admin_claims, "Buyer RBAC Org")
        sup_org = _create_org(client, sup_claims, "Supplier RBAC Org")

        # Add Mary as MEMBER in buyer org
        _add_member(client, admin_claims, buyer_org["id"], member_claims, role="MEMBER")

        # Admin creates RFQ, invites supplier
        with as_user(admin_claims):
            rfq = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/",
                json={
                    "title": "RBAC Test RFQ",
                    "destination_country": "DE",
                    "items": [{"product_name_snapshot": "RBAC Item", "quantity": "10.00", "unit": "PCS"}],
                },
            ).json()
            rfq_id = rfq["id"]
            rfq_item_id = rfq["items"][0]["id"]
            client.post(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/open")
            client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/invitations",
                json={
                    "invitations": [
                        {"supplier_email": "srbac@example.com", "supplier_name": "Sup", "supplier_organization_id": sup_org["id"]}
                    ]
                },
            )

        # Supplier submits quote
        with as_user(sup_claims):
            q = client.post(
                f"/api/v1/organizations/{sup_org['id']}/supplier/rfqs/{rfq_id}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "Net 30",
                    "lead_time_days": 10,
                    "items": [{"rfq_item_id": rfq_item_id, "unit_price": "100.0000"}],
                },
            ).json()
            client.post(f"/api/v1/organizations/{sup_org['id']}/supplier/quotations/{q['id']}/submit")

        # Mary (MEMBER) CAN read quotations and comparison
        with as_user(member_claims):
            q_list = client.get(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/quotations")
            assert q_list.status_code == 200
            assert len(q_list.json()) == 1

            comp_res = client.get(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/comparison")
            assert comp_res.status_code == 200

            # But Mary (MEMBER) CANNOT award quotation (requires ADMIN or BUYER)
            award_res = client.post(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/award/{q['id']}")
            assert award_res.status_code == 403
            assert "not permitted to perform this action" in award_res.json()["detail"].lower()

    def test_supplier_cannot_claim_invitation_with_mismatched_email(self, client):
        """
        Verify:
        - When an invitation is sent to an external email, a user with an uninvited email
          cannot submit a quotation for that RFQ.
        """
        buyer_claims = _make_claims("auth0|b-email-test", "bemail@example.com", "Buyer Email")
        buyer_org = _create_org(client, buyer_claims, "Buyer Email Org")

        with as_user(buyer_claims):
            rfq = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/",
                json={
                    "title": "Email Specific RFQ",
                    "destination_country": "US",
                    "items": [{"product_name_snapshot": "Spec Item", "quantity": "5.00", "unit": "PCS"}],
                },
            ).json()
            rfq_id = rfq["id"]
            rfq_item_id = rfq["items"][0]["id"]
            client.post(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/open")
            # Sent specifically to authorized_vendor@example.com
            client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/invitations",
                json={
                    "invitations": [
                        {"supplier_email": "authorized_vendor@example.com", "supplier_name": "Vendor Corp"}
                    ]
                },
            )

        # Attacker user logs in with imposter@example.com under Attacker Org
        attacker_claims = _make_claims("auth0|attacker", "imposter@example.com", "Attacker")
        attacker_org = _create_org(client, attacker_claims, "Attacker Org")

        with as_user(attacker_claims):
            # Attempt to submit quote
            res = client.post(
                f"/api/v1/organizations/{attacker_org['id']}/supplier/rfqs/{rfq_id}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "Net 30",
                    "lead_time_days": 10,
                    "items": [{"rfq_item_id": rfq_item_id, "unit_price": "50.0000"}],
                },
            )
            assert res.status_code == 403
            assert "not been invited" in res.json()["detail"].lower()

    def test_superseded_quotation_remains_superseded_when_another_is_awarded(self, client):
        """
        Verify that awarding a winning quotation does NOT mutate SUPERSEDED historical quotes to REJECTED.
        Historical quotation versions must remain SUPERSEDED.
        """
        buyer_claims = _make_claims("auth0|b-super-test", "bsuper@example.com", "Buyer Super")
        sup1_claims = _make_claims("auth0|s1-super", "s1super@example.com", "Supplier 1")
        sup2_claims = _make_claims("auth0|s2-super", "s2super@example.com", "Supplier 2")

        buyer_org = _create_org(client, buyer_claims, "Buyer Super Org")
        sup1_org = _create_org(client, sup1_claims, "Supplier 1 Super Org")
        sup2_org = _create_org(client, sup2_claims, "Supplier 2 Super Org")

        with as_user(buyer_claims):
            rfq = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/",
                json={
                    "title": "Super Test RFQ",
                    "destination_country": "US",
                    "items": [{"product_name_snapshot": "Test Item", "quantity": "10.00", "unit": "PCS"}],
                },
            ).json()
            rfq_id = rfq["id"]
            rfq_item_id = rfq["items"][0]["id"]
            client.post(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/open")
            client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/invitations",
                json={
                    "invitations": [
                        {"supplier_email": "s1super@example.com", "supplier_name": "S1", "supplier_organization_id": sup1_org["id"]},
                        {"supplier_email": "s2super@example.com", "supplier_name": "S2", "supplier_organization_id": sup2_org["id"]},
                    ]
                },
            )

        # Supplier 1 submits V1, then revises to V2
        with as_user(sup1_claims):
            q1_v1 = client.post(
                f"/api/v1/organizations/{sup1_org['id']}/supplier/rfqs/{rfq_id}/quotations",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "Net 30",
                    "lead_time_days": 15,
                    "items": [{"rfq_item_id": rfq_item_id, "unit_price": "100.0000"}],
                },
            ).json()
            client.post(f"/api/v1/organizations/{sup1_org['id']}/supplier/quotations/{q1_v1['id']}/submit")

            # Revise V1 -> V2
            q1_v2 = client.post(
                f"/api/v1/organizations/{sup1_org['id']}/supplier/quotations/{q1_v1['id']}/revise",
                json={
                    "incoterm": "FOB",
                    "payment_terms": "Net 30",
                    "lead_time_days": 12,
                    "items": [{"rfq_item_id": rfq_item_id, "unit_price": "95.0000"}],
                },
            ).json()

        # Supplier 2 submits Quote 2
        with as_user(sup2_claims):
            q2 = client.post(
                f"/api/v1/organizations/{sup2_org['id']}/supplier/rfqs/{rfq_id}/quotations",
                json={
                    "incoterm": "CIF",
                    "payment_terms": "Net 30",
                    "lead_time_days": 10,
                    "items": [{"rfq_item_id": rfq_item_id, "unit_price": "90.0000"}],
                },
            ).json()
            client.post(f"/api/v1/organizations/{sup2_org['id']}/supplier/quotations/{q2['id']}/submit")

        # Buyer attempts to award superseded V1 -> MUST FAIL with 400
        with as_user(buyer_claims):
            fail_super = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/award/{q1_v1['id']}"
            )
            assert fail_super.status_code == 400
            assert "SUPERSEDED" in fail_super.json()["detail"]

            # Buyer attempts to award non-existent or foreign quotation -> MUST FAIL with 404
            fail_foreign = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/award/{uuid.uuid4()}"
            )
            assert fail_foreign.status_code == 404

        # Buyer awards Q2
        with as_user(buyer_claims):
            award_res = client.post(f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/award/{q2['id']}")
            assert award_res.status_code == 200

            # Buyer attempts to award again (RFQ already AWARDED) -> MUST FAIL with 400
            fail_again = client.post(
                f"/api/v1/organizations/{buyer_org['id']}/rfqs/{rfq_id}/award/{q2['id']}"
            )
            assert fail_again.status_code == 400
            assert "terminal status" in fail_again.json()["detail"]

        # Verify statuses:
        # Q2 -> ACCEPTED
        with as_user(sup2_claims):
            q2_check = client.get(f"/api/v1/organizations/{sup2_org['id']}/supplier/quotations/{q2['id']}").json()
            assert q2_check["status"] == "ACCEPTED"

        # Supplier 1 V2 (competing active quote) -> REJECTED
        # Supplier 1 V1 (historical superseded quote) -> MUST STILL BE SUPERSEDED!
        with as_user(sup1_claims):
            v2_check = client.get(f"/api/v1/organizations/{sup1_org['id']}/supplier/quotations/{q1_v2['id']}").json()
            assert v2_check["status"] == "REJECTED"

            v1_check = client.get(f"/api/v1/organizations/{sup1_org['id']}/supplier/quotations/{q1_v1['id']}").json()
            assert v1_check["status"] == "SUPERSEDED"
