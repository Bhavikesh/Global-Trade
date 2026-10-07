"""
Unit tests for Buyer, Supplier, and CRM Contact Pydantic schemas and validation.

Verifies:
  1. valid Buyer create data
  2. invalid Buyer verification status
  3. invalid Buyer country
  4. invalid/blank Buyer company name
  5. valid Supplier create data
  6. invalid Supplier verification status
  7. invalid/blank Supplier company name
  8. valid Contact data
  9. invalid/blank Contact name
  10. partial Buyer update
  11. partial Supplier update
"""
import pytest
from pydantic import ValidationError

from app.schemas.buyer import BuyerCreate, BuyerUpdate, BuyerRead
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierRead
from app.schemas.contact import ContactCreate, ContactUpdate, ContactRead


class TestBuyerValidation:
    def test_valid_buyer_create_data(self):
        """1. valid Buyer create data"""
        data = {
            "company_name": "  Apex Trade Corp  ",
            "contact_name": "  John Smith  ",
            "email": "JOHN@ApexTrade.COM",
            "phone": "+1-202-555-0199",
            "country": "us",
            "address": "123 Trade Way, New York, NY",
            "website": "apextrade.com",
            "industry": "Consumer Goods",
            "verification_status": "unverified",
            "notes": "Verified retail importer",
        }
        buyer = BuyerCreate(**data)
        assert buyer.company_name == "Apex Trade Corp"  # trimmed
        assert buyer.contact_name == "John Smith"      # trimmed
        assert buyer.email == "john@apextrade.com"     # normalized lowercase
        assert buyer.country == "US"                   # uppercase ISO code
        assert buyer.website == "https://apextrade.com"  # auto-prepended https://
        assert buyer.verification_status == "UNVERIFIED"

    def test_invalid_buyer_verification_status(self):
        """2. invalid Buyer verification status"""
        with pytest.raises(ValidationError) as exc_info:
            BuyerCreate(
                company_name="Valid Name",
                verification_status="INVALID_STATUS",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("verification_status",) for e in errors)

    def test_invalid_buyer_country(self):
        """3. invalid Buyer country"""
        # Non-alpha country code
        with pytest.raises(ValidationError):
            BuyerCreate(company_name="Valid Name", country="12")

        # 3-letter country code
        with pytest.raises(ValidationError):
            BuyerCreate(company_name="Valid Name", country="USA")

        # Single letter
        with pytest.raises(ValidationError):
            BuyerCreate(company_name="Valid Name", country="U")

    def test_invalid_blank_buyer_company_name(self):
        """4. invalid/blank Buyer company name"""
        # Whitespace only
        with pytest.raises(ValidationError) as exc_info:
            BuyerCreate(company_name="   ")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("company_name",) for e in errors)

        # Empty string
        with pytest.raises(ValidationError):
            BuyerCreate(company_name="")

    def test_partial_buyer_update(self):
        """10. partial Buyer update"""
        # Only updating industry, all other fields None
        update = BuyerUpdate(industry="Electronics")
        data = update.model_dump(exclude_unset=True)
        assert data == {"industry": "Electronics"}
        assert update.company_name is None
        assert update.email is None

        # Partial update with blank name must fail
        with pytest.raises(ValidationError):
            BuyerUpdate(company_name="   ")

        # Partial update with invalid country must fail
        with pytest.raises(ValidationError):
            BuyerUpdate(country="XYZ")

        # Partial update with invalid verification status must fail
        with pytest.raises(ValidationError):
            BuyerUpdate(verification_status="UNKNOWN")


class TestSupplierValidation:
    def test_valid_supplier_create_data(self):
        """5. valid Supplier create data"""
        data = {
            "company_name": "  Shenzhen Electronics Ltd  ",
            "contact_name": "  Li Wei  ",
            "email": "LI.WEI@SHENZHEN.CN",
            "phone": "+86-755-12345678",
            "country": "cn",
            "address": "456 Tech Park, Shenzhen",
            "website": "http://shenzhentrade.cn",
            "supplier_type": "MANUFACTURER",
            "verification_status": "verified",
            "certifications": "ISO9001, CE",
            "notes": "Primary OEM partner",
        }
        supplier = SupplierCreate(**data)
        assert supplier.company_name == "Shenzhen Electronics Ltd"
        assert supplier.contact_name == "Li Wei"
        assert supplier.email == "li.wei@shenzhen.cn"
        assert supplier.country == "CN"
        assert supplier.website == "http://shenzhentrade.cn"
        assert supplier.verification_status == "VERIFIED"
        assert supplier.certifications == "ISO9001, CE"

    def test_invalid_supplier_verification_status(self):
        """6. invalid Supplier verification status"""
        with pytest.raises(ValidationError) as exc_info:
            SupplierCreate(
                company_name="Valid Supplier",
                verification_status="APPROVED",  # Not in {UNVERIFIED, PENDING, VERIFIED, SUSPENDED}
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("verification_status",) for e in errors)

    def test_invalid_blank_supplier_company_name(self):
        """7. invalid/blank Supplier company name"""
        with pytest.raises(ValidationError):
            SupplierCreate(company_name="   ")

        with pytest.raises(ValidationError):
            SupplierCreate(company_name="")

    def test_partial_supplier_update(self):
        """11. partial Supplier update"""
        update = SupplierUpdate(supplier_type="WHOLESALER", notes="Updated terms")
        data = update.model_dump(exclude_unset=True)
        assert data == {"supplier_type": "WHOLESALER", "notes": "Updated terms"}
        assert update.company_name is None

        # Partial update with valid status update
        update_status = SupplierUpdate(verification_status="SUSPENDED")
        assert update_status.verification_status == "SUSPENDED"

        # Partial update with blank name fails
        with pytest.raises(ValidationError):
            SupplierUpdate(company_name="")


class TestContactValidation:
    def test_valid_contact_data(self):
        """8. valid Contact data"""
        data = {
            "name": "  Sarah Connor  ",
            "email": "SARAH@RESISTANCE.ORG",
            "phone": "+1-555-0144",
            "designation": "Head of Sourcing",
            "notes": "Handles Asia-Pacific contracts",
            "is_primary": True,
        }
        contact = ContactCreate(**data)
        assert contact.name == "Sarah Connor"
        assert contact.email == "sarah@resistance.org"
        assert contact.phone == "+1-555-0144"
        assert contact.designation == "Head of Sourcing"
        assert contact.is_primary is True

    def test_invalid_blank_contact_name(self):
        """9. invalid/blank Contact name"""
        with pytest.raises(ValidationError) as exc_info:
            ContactCreate(name="   ")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

        with pytest.raises(ValidationError):
            ContactCreate(name="")

    def test_partial_contact_update(self):
        """Partial Contact update"""
        update = ContactUpdate(is_primary=True, designation="VP of Trade")
        data = update.model_dump(exclude_unset=True)
        assert data == {"is_primary": True, "designation": "VP of Trade"}
        assert update.name is None

        # Blank name fails on update
        with pytest.raises(ValidationError):
            ContactUpdate(name="  ")
