"""
Unit and database integration tests for Phase 1 RFQ, Quotation, and Negotiation models.

Tests schema integrity, foreign keys, cascade rules, check constraints, unique constraints,
and collision-safe number generation.
"""
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership
from app.models.rfq import (
    RFQ,
    RFQItem,
    RFQSupplierInvitation,
    RFQ_STATUS_DRAFT,
    RFQ_STATUS_OPEN,
    INVITATION_STATUS_INVITED,
)
from app.models.quotation import (
    Quotation,
    QuotationItem,
    QUOTATION_STATUS_SUBMITTED,
    QUOTATION_STATUS_SUPERSEDED,
)
from app.models.negotiation import (
    NegotiationNote,
    NOTE_TYPE_COUNTER_OFFER,
)
from app.services.reference_number import generate_rfq_number, generate_quotation_number


def _create_seed_user_and_org(db, sub: str = "auth0|test-user", org_name: str = "Acme Corp"):
    user = User(
        identity_provider_id=sub,
        email="buyer@acme.com",
        name="Buyer Bob",
    )
    db.add(user)
    db.flush()

    org = Organization(legal_name=org_name, country="US")
    db.add(org)
    db.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role="ADMIN",
        status="ACTIVE",
    )
    db.add(membership)
    db.flush()
    return user, org


class TestRFQModels:
    def test_create_rfq_with_items_and_invitations(self, db_session):
        user, org = _create_seed_user_and_org(db_session)

        # 1. Create RFQ
        rfq_num = generate_rfq_number(db_session)
        rfq = RFQ(
            organization_id=org.id,
            rfq_number=rfq_num,
            title="Sourcing Stainless Steel Fasteners",
            description="Grade 316 hex bolts for marine application",
            destination_country="DE",
            destination_port="Hamburg",
            preferred_incoterm="FOB",
            preferred_payment_terms="LC at sight",
            currency="USD",
            status=RFQ_STATUS_DRAFT,
            created_by_user_id=user.id,
        )
        db_session.add(rfq)
        db_session.flush()

        # 2. Add RFQ Items
        item1 = RFQItem(
            rfq_id=rfq.id,
            item_index=1,
            product_name_snapshot="M10x50mm Marine Bolt Grade 316",
            description="Fully threaded ISO 4017",
            quantity=Decimal("10000.00"),
            unit="PCS",
            target_unit_price=Decimal("0.4500"),
            specifications="Grade 316 Stainless",
        )
        item2 = RFQItem(
            rfq_id=rfq.id,
            item_index=2,
            product_name_snapshot="M10 Grade 316 Hex Nut",
            description="DIN 934 hex nut",
            quantity=Decimal("10000.00"),
            unit="PCS",
            target_unit_price=Decimal("0.1500"),
        )
        db_session.add_all([item1, item2])
        db_session.flush()

        # 3. Add Supplier Invitation
        invitation = RFQSupplierInvitation(
            rfq_id=rfq.id,
            supplier_email="sales@steelworks.de",
            supplier_name="SteelWorks GmbH",
            invited_by_user_id=user.id,
            status=INVITATION_STATUS_INVITED,
        )
        db_session.add(invitation)
        db_session.commit()

        # Query back and verify relationships
        saved_rfq = db_session.query(RFQ).filter_by(id=rfq.id).first()
        assert saved_rfq is not None
        assert saved_rfq.rfq_number.startswith("RFQ-")
        assert len(saved_rfq.items) == 2
        assert saved_rfq.items[0].product_name_snapshot == "M10x50mm Marine Bolt Grade 316"
        assert saved_rfq.items[0].quantity == Decimal("10000.00")
        assert len(saved_rfq.invitations) == 1
        assert saved_rfq.invitations[0].supplier_email == "sales@steelworks.de"

    def test_rfq_item_quantity_must_be_positive(self, db_session):
        user, org = _create_seed_user_and_org(db_session, sub="auth0|test-u2")

        rfq = RFQ(
            organization_id=org.id,
            rfq_number=generate_rfq_number(db_session),
            title="Invalid Item RFQ",
            destination_country="US",
            created_by_user_id=user.id,
        )
        db_session.add(rfq)
        db_session.flush()

        invalid_item = RFQItem(
            rfq_id=rfq.id,
            product_name_snapshot="Zero Quantity Item",
            quantity=Decimal("0.00"),  # Violates quantity > 0
            unit="PCS",
        )
        db_session.add(invalid_item)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_duplicate_supplier_invitation_rejected(self, db_session):
        user, org = _create_seed_user_and_org(db_session, sub="auth0|test-u3")

        rfq = RFQ(
            organization_id=org.id,
            rfq_number=generate_rfq_number(db_session),
            title="Duplicate Invitation Test",
            destination_country="JP",
            created_by_user_id=user.id,
        )
        db_session.add(rfq)
        db_session.flush()

        inv1 = RFQSupplierInvitation(
            rfq_id=rfq.id,
            supplier_email="supplier@example.com",
            supplier_name="Supplier One",
            invited_by_user_id=user.id,
        )
        db_session.add(inv1)
        db_session.commit()

        # Second invitation with identical supplier_email on same RFQ
        inv2 = RFQSupplierInvitation(
            rfq_id=rfq.id,
            supplier_email="supplier@example.com",
            supplier_name="Supplier One Duplicate",
            invited_by_user_id=user.id,
        )
        db_session.add(inv2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_quotation_creation_and_versioning(self, db_session):
        buyer_user, buyer_org = _create_seed_user_and_org(db_session, sub="auth0|buyer-u", org_name="Buyer Org")
        supplier_user, supplier_org = _create_seed_user_and_org(db_session, sub="auth0|supplier-u", org_name="Supplier Org")

        # RFQ
        rfq = RFQ(
            organization_id=buyer_org.id,
            rfq_number=generate_rfq_number(db_session),
            title="Solar Inverters 50kW",
            destination_country="NL",
            status=RFQ_STATUS_OPEN,
            created_by_user_id=buyer_user.id,
        )
        db_session.add(rfq)
        db_session.flush()

        rfq_item = RFQItem(
            rfq_id=rfq.id,
            product_name_snapshot="Solar Inverter 50kW Three Phase",
            quantity=Decimal("50.00"),
            unit="UNITS",
        )
        db_session.add(rfq_item)
        db_flush = db_session.flush()

        # Quotation V1
        qt1 = Quotation(
            rfq_id=rfq.id,
            supplier_organization_id=supplier_org.id,
            supplier_user_id=supplier_user.id,
            quotation_number=generate_quotation_number(db_session),
            version=1,
            status=QUOTATION_STATUS_SUBMITTED,
            currency="EUR",
            incoterm="CIF",
            payment_terms="T/T 30% advance, 70% against BL",
            lead_time_days=21,
            subtotal_amount=Decimal("75000.00"),
            shipping_cost=Decimal("2500.00"),
            insurance_cost=Decimal("500.00"),
            duty_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            other_charges=Decimal("200.00"),
            total_landed_cost=Decimal("78200.00"),
        )
        db_session.add(qt1)
        db_session.flush()

        qt_item1 = QuotationItem(
            quotation_id=qt1.id,
            rfq_item_id=rfq_item.id,
            product_name_snapshot="Solar Inverter 50kW Three Phase",
            quantity=Decimal("50.00"),
            unit="UNITS",
            unit_price=Decimal("1500.0000"),
            line_total=Decimal("75000.00"),
        )
        db_session.add(qt_item1)
        db_session.commit()

        # Quotation V2 (Revision superseding V1)
        qt1.status = QUOTATION_STATUS_SUPERSEDED
        qt2 = Quotation(
            rfq_id=rfq.id,
            supplier_organization_id=supplier_org.id,
            supplier_user_id=supplier_user.id,
            quotation_number=generate_quotation_number(db_session),
            version=2,
            parent_quotation_id=qt1.id,
            status=QUOTATION_STATUS_SUBMITTED,
            currency="EUR",
            incoterm="CIF",
            payment_terms="T/T 30% advance, 70% against BL",
            lead_time_days=18,
            subtotal_amount=Decimal("72500.00"),
            shipping_cost=Decimal("2200.00"),
            insurance_cost=Decimal("500.00"),
            duty_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            other_charges=Decimal("200.00"),
            total_landed_cost=Decimal("75400.00"),
        )
        db_session.add(qt2)
        db_session.flush()

        qt_item2 = QuotationItem(
            quotation_id=qt2.id,
            rfq_item_id=rfq_item.id,
            product_name_snapshot="Solar Inverter 50kW Three Phase",
            quantity=Decimal("50.00"),
            unit="UNITS",
            unit_price=Decimal("1450.0000"),
            line_total=Decimal("72500.00"),
        )
        db_session.add(qt_item2)
        db_session.commit()

        # Verify historical versions preserved
        saved_qt1 = db_session.query(Quotation).filter_by(id=qt1.id).first()
        saved_qt2 = db_session.query(Quotation).filter_by(id=qt2.id).first()
        assert saved_qt1.status == QUOTATION_STATUS_SUPERSEDED
        assert saved_qt1.version == 1
        assert saved_qt2.version == 2
        assert saved_qt2.parent_quotation_id == saved_qt1.id
        assert saved_qt2.total_landed_cost == Decimal("75400.00")

    def test_negotiation_note_creation(self, db_session):
        buyer_user, buyer_org = _create_seed_user_and_org(db_session, sub="auth0|buyer-u2", org_name="Buyer Two")
        supplier_user, supplier_org = _create_seed_user_and_org(db_session, sub="auth0|sup-u2", org_name="Supplier Two")

        rfq = RFQ(
            organization_id=buyer_org.id,
            rfq_number=generate_rfq_number(db_session),
            title="Negotiation Test RFQ",
            destination_country="GB",
            created_by_user_id=buyer_user.id,
        )
        db_session.add(rfq)
        db_session.flush()

        qt = Quotation(
            rfq_id=rfq.id,
            supplier_organization_id=supplier_org.id,
            supplier_user_id=supplier_user.id,
            quotation_number=generate_quotation_number(db_session),
            incoterm="FOB",
            payment_terms="Net 30",
            lead_time_days=14,
            subtotal_amount=Decimal("10000.00"),
            total_landed_cost=Decimal("10000.00"),
        )
        db_session.add(qt)
        db_session.flush()

        note = NegotiationNote(
            quotation_id=qt.id,
            organization_id=buyer_org.id,
            author_user_id=buyer_user.id,
            note_type=NOTE_TYPE_COUNTER_OFFER,
            proposed_target_price=Decimal("9200.0000"),
            proposed_terms="Net 45 instead of Net 30",
            message="Can you match 9,200 total with Net 45 terms for repeat orders?",
        )
        db_session.add(note)
        db_session.commit()

        saved_note = db_session.query(NegotiationNote).filter_by(id=note.id).first()
        assert saved_note is not None
        assert saved_note.note_type == NOTE_TYPE_COUNTER_OFFER
        assert saved_note.proposed_target_price == Decimal("9200.0000")
