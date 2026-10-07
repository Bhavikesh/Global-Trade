/**
 * API client for GlobalTrade.ai backend services
 */

const BACKEND_API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api";

export interface UserProfile {
  id: string;
  identity_provider_id: string;
  email: string | null;
  name: string | null;
  phone: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  legal_name: string;
  display_name: string | null;
  business_type: string | null;
  country: string | null;
  address: string | null;
  tax_identifier: string | null;
  vat_identifier: string | null;
  iec_number: string | null;
  website: string | null;
  contact_information: string | null;
  verification_status: string;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMembership {
  id: string;
  organization_id: string;
  user_id: string;
  role: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface HealthStatus {
  status: string;
  project: string;
  environment: string;
  database: {
    status: string;
    version: string;
    pgvector: string;
  };
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${BACKEND_API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Failed to fetch health status: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Route client requests through the Next.js server-side BFF boundary
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url =
    typeof window !== "undefined"
      ? `/api/backend${cleanEndpoint}`
      : `${BACKEND_API_BASE}${cleanEndpoint}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(
      errorBody.detail || `HTTP error ${response.status}: ${response.statusText}`
    );
  }

  if (response.status === 204) {
    return null as unknown as T;
  }

  return response.json();
}

// ============================================================================
// BUYER / SUPPLIER / CRM CONTACT DOMAIN TYPES & APIS
// ============================================================================

export interface Buyer {
  id: string;
  organization_id: string;
  company_name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  country: string | null;
  address: string | null;
  website: string | null;
  industry: string | null;
  verification_status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BuyerCreateInput {
  company_name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  country?: string | null;
  address?: string | null;
  website?: string | null;
  industry?: string | null;
  verification_status?: string;
  notes?: string | null;
}

export interface BuyerUpdateInput {
  company_name?: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  country?: string | null;
  address?: string | null;
  website?: string | null;
  industry?: string | null;
  verification_status?: string;
  notes?: string | null;
}

export interface BuyerListResponse {
  items: Buyer[];
  total: number;
  limit: number;
  offset: number;
}

export interface Supplier {
  id: string;
  organization_id: string;
  company_name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  country: string | null;
  address: string | null;
  website: string | null;
  supplier_type: string | null;
  verification_status: string;
  certifications: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreateInput {
  company_name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  country?: string | null;
  address?: string | null;
  website?: string | null;
  supplier_type?: string | null;
  verification_status?: string;
  certifications?: string | null;
  notes?: string | null;
}

export interface SupplierUpdateInput {
  company_name?: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  country?: string | null;
  address?: string | null;
  website?: string | null;
  supplier_type?: string | null;
  verification_status?: string;
  certifications?: string | null;
  notes?: string | null;
}

export interface SupplierListResponse {
  items: Supplier[];
  total: number;
  limit: number;
  offset: number;
}

export interface CRMContact {
  id: string;
  organization_id: string;
  buyer_id: string | null;
  supplier_id: string | null;
  name: string;
  email: string | null;
  phone: string | null;
  designation: string | null;
  notes: string | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface CRMContactCreateInput {
  name: string;
  email?: string | null;
  phone?: string | null;
  designation?: string | null;
  notes?: string | null;
  is_primary?: boolean;
}

export interface CRMContactUpdateInput {
  name?: string;
  email?: string | null;
  phone?: string | null;
  designation?: string | null;
  notes?: string | null;
  is_primary?: boolean;
}

// ----------------------------------------------------------------------------
// Buyer API Client Helpers
// ----------------------------------------------------------------------------

export async function fetchBuyers(
  orgId: string,
  params: {
    q?: string;
    country?: string;
    verification_status?: string;
    industry?: string;
    limit?: number;
    offset?: number;
  } = {}
): Promise<BuyerListResponse> {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.country) query.set("country", params.country);
  if (params.verification_status) query.set("verification_status", params.verification_status);
  if (params.industry) query.set("industry", params.industry);
  if (params.limit !== undefined) query.set("limit", params.limit.toString());
  if (params.offset !== undefined) query.set("offset", params.offset.toString());
  const queryString = query.toString() ? `?${query.toString()}` : "";
  return fetchWithAuth<BuyerListResponse>(`/v1/organizations/${orgId}/buyers${queryString}`);
}

export async function fetchBuyer(orgId: string, buyerId: string): Promise<Buyer> {
  return fetchWithAuth<Buyer>(`/v1/organizations/${orgId}/buyers/${buyerId}`);
}

export async function createBuyer(orgId: string, data: BuyerCreateInput): Promise<Buyer> {
  return fetchWithAuth<Buyer>(`/v1/organizations/${orgId}/buyers`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateBuyer(orgId: string, buyerId: string, data: BuyerUpdateInput): Promise<Buyer> {
  return fetchWithAuth<Buyer>(`/v1/organizations/${orgId}/buyers/${buyerId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteBuyer(orgId: string, buyerId: string): Promise<void> {
  return fetchWithAuth<void>(`/v1/organizations/${orgId}/buyers/${buyerId}`, {
    method: "DELETE",
  });
}

// ----------------------------------------------------------------------------
// Supplier API Client Helpers
// ----------------------------------------------------------------------------

export async function fetchSuppliers(
  orgId: string,
  params: {
    q?: string;
    country?: string;
    verification_status?: string;
    supplier_type?: string;
    limit?: number;
    offset?: number;
  } = {}
): Promise<SupplierListResponse> {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.country) query.set("country", params.country);
  if (params.verification_status) query.set("verification_status", params.verification_status);
  if (params.supplier_type) query.set("supplier_type", params.supplier_type);
  if (params.limit !== undefined) query.set("limit", params.limit.toString());
  if (params.offset !== undefined) query.set("offset", params.offset.toString());
  const queryString = query.toString() ? `?${query.toString()}` : "";
  return fetchWithAuth<SupplierListResponse>(`/v1/organizations/${orgId}/suppliers${queryString}`);
}

export async function fetchSupplier(orgId: string, supplierId: string): Promise<Supplier> {
  return fetchWithAuth<Supplier>(`/v1/organizations/${orgId}/suppliers/${supplierId}`);
}

export async function createSupplier(orgId: string, data: SupplierCreateInput): Promise<Supplier> {
  return fetchWithAuth<Supplier>(`/v1/organizations/${orgId}/suppliers`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSupplier(orgId: string, supplierId: string, data: SupplierUpdateInput): Promise<Supplier> {
  return fetchWithAuth<Supplier>(`/v1/organizations/${orgId}/suppliers/${supplierId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteSupplier(orgId: string, supplierId: string): Promise<void> {
  return fetchWithAuth<void>(`/v1/organizations/${orgId}/suppliers/${supplierId}`, {
    method: "DELETE",
  });
}

// ----------------------------------------------------------------------------
// CRM Contacts API Client Helpers
// ----------------------------------------------------------------------------

export async function fetchBuyerContacts(orgId: string, buyerId: string): Promise<CRMContact[]> {
  return fetchWithAuth<CRMContact[]>(`/v1/organizations/${orgId}/buyers/${buyerId}/contacts`);
}

export async function createBuyerContact(orgId: string, buyerId: string, data: CRMContactCreateInput): Promise<CRMContact> {
  return fetchWithAuth<CRMContact>(`/v1/organizations/${orgId}/buyers/${buyerId}/contacts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchSupplierContacts(orgId: string, supplierId: string): Promise<CRMContact[]> {
  return fetchWithAuth<CRMContact[]>(`/v1/organizations/${orgId}/suppliers/${supplierId}/contacts`);
}

export async function createSupplierContact(orgId: string, supplierId: string, data: CRMContactCreateInput): Promise<CRMContact> {
  return fetchWithAuth<CRMContact>(`/v1/organizations/${orgId}/suppliers/${supplierId}/contacts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateContact(orgId: string, contactId: string, data: CRMContactUpdateInput): Promise<CRMContact> {
  return fetchWithAuth<CRMContact>(`/v1/organizations/${orgId}/contacts/${contactId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteContact(orgId: string, contactId: string): Promise<void> {
  return fetchWithAuth<void>(`/v1/organizations/${orgId}/contacts/${contactId}`, {
    method: "DELETE",
  });
}

