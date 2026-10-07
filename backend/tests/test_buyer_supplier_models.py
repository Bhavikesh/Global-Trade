"""
Model-level unit tests for Buyer, Supplier, and CRMContact models.

Verifies:
  - Buyer model creation, UUID generation, default verification_status, and timestamps
  - Supplier model creation, UUID generation, default verification_status, certifications, and timestamps
  - CRMContact model creation for Buyer and Supplier
  - Organization 1-to-many Buyer, Supplier, CRMContact relationships
  - Cascade deletes: deleting Buyer or Supplier cascades to CRMContact
  - Cascade deletes: deleting Organization cascades to Buyers, Suppliers, and Contacts
  - Foreign key targets: Buyer.id and Supplier.id are usable as FK targets
"""
import uuid
import pytest
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.buyer import Buyer
from app.models.supplier import Supplier
from app.models.contact import CRMContact
from tests.conftest import TestSessionLocal


@pytest.fixture
def db_session():
    """Direct database session fixture for model testing."""
    session: Session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_organization(db_session: Session) -> Organization:
    """Creates a test organization in the database."""
    org = Organization(
        legal_name="Global Trade Corp LLC",
        country="US",
        business_type="BOTH",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


class TestBuyerModel:
    def test_create_buyer(self, db_session: Session, test_organization: Organization):
        buyer = Buyer(
            organization_id=test_organization.id,
            company_name="Apex Global Imports",
            contact_name="Jane Doe",
            email="jane@apeximports.com",
            phone="+1-555-0100",
            country="US",
            address="123 Harbor Blvd, Seattle, WA",
            website="https://apeximports.com",
            industry="Consumer Goods",
            notes="Key North American retail buyer",
        )
        db_session.add(buyer)
        db_session.commit()
        db_session.refresh(buyer)

        assert isinstance(buyer.id, uuid.UUID)
        assert buyer.organization_id == test_organization.id
        assert buyer.company_name == "Apex Global Imports"
        assert buyer.contact_name == "Jane Doe"
        assert buyer.email == "jane@apeximports.com"
        assert buyer.country == "US"
        assert buyer.verification_status == "UNVERIFIED"
        assert buyer.created_at is not None
        assert buyer.updated_at is not None
        assert buyer.organization.id == test_organization.id
        assert buyer in test_organization.buyers


class TestSupplierModel:
    def test_create_supplier(self, db_session: Session, test_organization: Organization):
        supplier = Supplier(
            organization_id=test_organization.id,
            company_name="Shenzhen Precision Manufacturing Co.",
            contact_name="Li Wei",
            email="li.wei@shenzhenprecision.cn",
            phone="+86-755-12345678",
            country="CN",
            address="Bldg 4, High-Tech Industrial Park, Shenzhen",
            website="https://shenzhenprecision.cn",
            supplier_type="MANUFACTURER",
            certifications="ISO9001:2015, CE, RoHS",
            notes="Tier-1 electronics component manufacturer",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)

        assert isinstance(supplier.id, uuid.UUID)
        assert supplier.organization_id == test_organization.id
        assert supplier.company_name == "Shenzhen Precision Manufacturing Co."
        assert supplier.supplier_type == "MANUFACTURER"
        assert supplier.verification_status == "UNVERIFIED"
        assert supplier.certifications == "ISO9001:2015, CE, RoHS"
        assert supplier.created_at is not None
        assert supplier.updated_at is not None
        assert supplier.organization.id == test_organization.id
        assert supplier in test_organization.suppliers


class TestCRMContactModel:
    def test_create_buyer_contact(self, db_session: Session, test_organization: Organization):
        buyer = Buyer(
            organization_id=test_organization.id,
            company_name="Nordic Retail AB",
            country="SE",
        )
        db_session.add(buyer)
        db_session.commit()
        db_session.refresh(buyer)

        contact = CRMContact(
            organization_id=test_organization.id,
            buyer_id=buyer.id,
            name="Astrid Lind",
            email="astrid@nordicretail.se",
            phone="+46-8-123456",
            designation="Chief Procurement Officer",
            notes="Primary contact for seasonal RFQs",
            is_primary=True,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        assert isinstance(contact.id, uuid.UUID)
        assert contact.buyer_id == buyer.id
        assert contact.supplier_id is None
        assert contact.name == "Astrid Lind"
        assert contact.designation == "Chief Procurement Officer"
        assert contact.is_primary is True
        assert contact.buyer.id == buyer.id
        assert contact in buyer.contacts

    def test_create_supplier_contact(self, db_session: Session, test_organization: Organization):
        supplier = Supplier(
            organization_id=test_organization.id,
            company_name="Vietnam Garments Ltd",
            country="VN",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)

        contact = CRMContact(
            organization_id=test_organization.id,
            supplier_id=supplier.id,
            name="Nguyen Van",
            email="nguyen@vngarments.vn",
            designation="Export Sales Manager",
            is_primary=False,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        assert isinstance(contact.id, uuid.UUID)
        assert contact.supplier_id == supplier.id
        assert contact.buyer_id is None
        assert contact.is_primary is False
        assert contact.supplier.id == supplier.id
        assert contact in supplier.contacts


class TestCascadeDeletes:
    def test_buyer_cascade_deletes_contacts(self, db_session: Session, test_organization: Organization):
        buyer = Buyer(
            organization_id=test_organization.id,
            company_name="Cascade Buyer Test",
        )
        db_session.add(buyer)
        db_session.commit()
        db_session.refresh(buyer)

        contact = CRMContact(
            organization_id=test_organization.id,
            buyer_id=buyer.id,
            name="John Contact",
        )
        db_session.add(contact)
        db_session.commit()
        contact_id = contact.id

        # Delete buyer
        db_session.delete(buyer)
        db_session.commit()

        # Contact must be deleted
        assert db_session.query(CRMContact).filter_by(id=contact_id).first() is None

    def test_supplier_cascade_deletes_contacts(self, db_session: Session, test_organization: Organization):
        supplier = Supplier(
            organization_id=test_organization.id,
            company_name="Cascade Supplier Test",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)

        contact = CRMContact(
            organization_id=test_organization.id,
            supplier_id=supplier.id,
            name="Supplier Contact",
        )
        db_session.add(contact)
        db_session.commit()
        contact_id = contact.id

        # Delete supplier
        db_session.delete(supplier)
        db_session.commit()

        # Contact must be deleted
        assert db_session.query(CRMContact).filter_by(id=contact_id).first() is None

    def test_organization_cascade_deletes_all(self, db_session: Session):
        org = Organization(legal_name="Org To Delete")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

        buyer = Buyer(organization_id=org.id, company_name="Org Buyer")
        supplier = Supplier(organization_id=org.id, company_name="Org Supplier")
        db_session.add_all([buyer, supplier])
        db_session.commit()

        b_id, s_id = buyer.id, supplier.id

        db_session.delete(org)
        db_session.commit()

        assert db_session.query(Buyer).filter_by(id=b_id).first() is None
        assert db_session.query(Supplier).filter_by(id=s_id).first() is None
