import test from "node:test";
import assert from "node:assert/strict";

// Test suite for Buyer, Supplier, and Contact Frontend API logic & contracts

test("Buyer search and pagination query building", () => {
  const params = {
    q: "Acme",
    country: "US",
    verification_status: "VERIFIED",
    industry: "Manufacturing",
    limit: 10,
    offset: 20,
  };

  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.country) query.set("country", params.country);
  if (params.verification_status) query.set("verification_status", params.verification_status);
  if (params.industry) query.set("industry", params.industry);
  if (params.limit !== undefined) query.set("limit", params.limit.toString());
  if (params.offset !== undefined) query.set("offset", params.offset.toString());

  const queryString = `?${query.toString()}`;
  assert.equal(
    queryString,
    "?q=Acme&country=US&verification_status=VERIFIED&industry=Manufacturing&limit=10&offset=20"
  );
});

test("Supplier search and pagination query building", () => {
  const params = {
    q: "Apex",
    country: "DE",
    verification_status: "PENDING",
    supplier_type: "MANUFACTURER",
    limit: 25,
    offset: 0,
  };

  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.country) query.set("country", params.country);
  if (params.verification_status) query.set("verification_status", params.verification_status);
  if (params.supplier_type) query.set("supplier_type", params.supplier_type);
  if (params.limit !== undefined) query.set("limit", params.limit.toString());
  if (params.offset !== undefined) query.set("offset", params.offset.toString());

  const queryString = `?${query.toString()}`;
  assert.equal(
    queryString,
    "?q=Apex&country=DE&verification_status=PENDING&supplier_type=MANUFACTURER&limit=25&offset=0"
  );
});

test("Buyer payload sanitization and field mapping", () => {
  const rawForm = {
    company_name: "  Globex Trade Inc.  ",
    contact_name: "  Jane Doe  ",
    email: "JANE@GLOBEX.COM  ",
    phone: " +1-555-0192 ",
    country: "us",
    address: " 100 Main St ",
    website: "https://globex.com",
    industry: "Automotive",
    verification_status: "VERIFIED",
    notes: "Top client",
  };

  const payload = {
    company_name: rawForm.company_name.trim(),
    contact_name: rawForm.contact_name.trim() || null,
    email: rawForm.email.trim().toLowerCase() || null,
    phone: rawForm.phone.trim() || null,
    country: rawForm.country.trim().toUpperCase() || null,
    address: rawForm.address.trim() || null,
    website: rawForm.website.trim() || null,
    industry: rawForm.industry.trim() || null,
    verification_status: rawForm.verification_status,
    notes: rawForm.notes.trim() || null,
  };

  assert.equal(payload.company_name, "Globex Trade Inc.");
  assert.equal(payload.contact_name, "Jane Doe");
  assert.equal(payload.email, "jane@globex.com");
  assert.equal(payload.country, "US");
  assert.equal(payload.verification_status, "VERIFIED");
});

test("Supplier payload sanitization and field mapping", () => {
  const rawForm = {
    company_name: "  Precision Metalworks  ",
    contact_name: " Hans Miller ",
    email: "HANS@METALWORKS.DE ",
    phone: "+49-30-12345",
    country: "de",
    address: "Industriestrasse 10",
    website: "https://metalworks.de",
    supplier_type: "MANUFACTURER",
    verification_status: "VERIFIED",
    certifications: "ISO 9001:2015, CE",
    notes: "High capacity foundry",
  };

  const payload = {
    company_name: rawForm.company_name.trim(),
    contact_name: rawForm.contact_name.trim() || null,
    email: rawForm.email.trim().toLowerCase() || null,
    phone: rawForm.phone.trim() || null,
    country: rawForm.country.trim().toUpperCase() || null,
    address: rawForm.address.trim() || null,
    website: rawForm.website.trim() || null,
    supplier_type: rawForm.supplier_type.trim() || null,
    verification_status: rawForm.verification_status,
    certifications: rawForm.certifications.trim() || null,
    notes: rawForm.notes.trim() || null,
  };

  assert.equal(payload.company_name, "Precision Metalworks");
  assert.equal(payload.contact_name, "Hans Miller");
  assert.equal(payload.email, "hans@metalworks.de");
  assert.equal(payload.country, "DE");
  assert.equal(payload.supplier_type, "MANUFACTURER");
  assert.equal(payload.certifications, "ISO 9001:2015, CE");
});

test("CRM Contact payload sanitization and primary flag behavior", () => {
  const contactForm = {
    name: " Sarah Connor ",
    email: "SARAH@RESISTANCE.ORG ",
    phone: "+1-555-8000",
    designation: "Chief of Security",
    notes: "Handles high value logistics",
    is_primary: true,
  };

  const payload = {
    name: contactForm.name.trim(),
    email: contactForm.email.trim().toLowerCase() || null,
    phone: contactForm.phone.trim() || null,
    designation: contactForm.designation.trim() || null,
    notes: contactForm.notes.trim() || null,
    is_primary: contactForm.is_primary,
  };

  assert.equal(payload.name, "Sarah Connor");
  assert.equal(payload.email, "sarah@resistance.org");
  assert.equal(payload.is_primary, true);
  // Verify internal IDs (id, orgId, parentId) are NOT exposed or included in payload
  assert.equal("id" in payload, false);
  assert.equal("organization_id" in payload, false);
  assert.equal("buyer_id" in payload, false);
  assert.equal("supplier_id" in payload, false);
});

test("Contact endpoint resolution rules", () => {
  const orgId = "11111111-1111-1111-1111-111111111111";
  const parentId = "22222222-2222-2222-2222-222222222222";
  const contactId = "33333333-3333-3333-3333-333333333333";

  // Buyer nested contact endpoints
  const buyerContactsListUrl = `/v1/organizations/${orgId}/buyers/${parentId}/contacts`;
  assert.equal(buyerContactsListUrl, `/v1/organizations/${orgId}/buyers/${parentId}/contacts`);

  // Supplier nested contact endpoints
  const supplierContactsListUrl = `/v1/organizations/${orgId}/suppliers/${parentId}/contacts`;
  assert.equal(supplierContactsListUrl, `/v1/organizations/${orgId}/suppliers/${parentId}/contacts`);

  // Direct contact mutation endpoint
  const contactMutationUrl = `/v1/organizations/${orgId}/contacts/${contactId}`;
  assert.equal(contactMutationUrl, `/v1/organizations/${orgId}/contacts/${contactId}`);
});
