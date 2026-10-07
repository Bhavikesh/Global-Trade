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

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// ---------------------------------------------------------------------------
// RFQ & Quotation Types
// ---------------------------------------------------------------------------

export interface RFQItem {
  id: string;
  rfq_id?: string;
  item_index: number;
  product_id?: string | null;
  product_name_snapshot: string;
  description?: string | null;
  quantity: string;
  unit: string;
  target_unit_price?: string | null;
  specifications?: string | null;
  quality_requirements?: string | null;
  packaging_requirements?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface RFQSupplierInvitation {
  id: string;
  rfq_id: string;
  supplier_organization_id?: string | null;
  supplier_id?: string | null;
  supplier_email: string;
  supplier_name: string;
  invited_by_user_id?: string;
  status: "INVITED" | "VIEWED" | "RESPONDED" | "DECLINED" | "EXPIRED";
  response_deadline?: string | null;
  invited_at: string;
  responded_at?: string | null;
}

export interface RFQ {
  id: string;
  organization_id: string;
  rfq_number: string;
  title: string;
  description?: string | null;
  status:
    | "DRAFT"
    | "OPEN"
    | "INVITATIONS_SENT"
    | "RESPONSES_RECEIVED"
    | "UNDER_REVIEW"
    | "NEGOTIATION"
    | "AWARDED"
    | "CANCELLED"
    | "EXPIRED";
  destination_country: string;
  destination_port?: string | null;
  required_delivery_date?: string | null;
  preferred_incoterm?: string | null;
  preferred_payment_terms?: string | null;
  currency: string;
  awarded_quotation_id?: string | null;
  notes?: string | null;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
  items: RFQItem[];
  invitations: RFQSupplierInvitation[];
}

export interface RFQItemCreate {
  item_index?: number;
  product_name_snapshot: string;
  description?: string | null;
  quantity: string;
  unit?: string;
  target_unit_price?: string | null;
  specifications?: string | null;
  quality_requirements?: string | null;
  packaging_requirements?: string | null;
}

export interface RFQCreate {
  title: string;
  description?: string | null;
  destination_country: string;
  destination_port?: string | null;
  required_delivery_date?: string | null;
  preferred_incoterm?: string | null;
  preferred_payment_terms?: string | null;
  currency?: string;
  notes?: string | null;
  items: RFQItemCreate[];
}

export interface SupplierInvitationInput {
  supplier_email: string;
  supplier_name: string;
  supplier_organization_id?: string | null;
  response_deadline?: string | null;
}

export interface QuotationItem {
  id: string;
  quotation_id?: string;
  rfq_item_id: string;
  product_name_snapshot: string;
  quantity: string;
  unit: string;
  unit_price: string;
  line_total: string;
  moq?: string | null;
  lead_time_days?: number | null;
  notes?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Quotation {
  id: string;
  rfq_id: string;
  supplier_organization_id: string;
  supplier_organization_name?: string | null;
  supplier_user_id: string;
  quotation_number: string;
  version: number;
  parent_quotation_id?: string | null;
  status:
    | "DRAFT"
    | "SUBMITTED"
    | "UNDER_REVIEW"
    | "ACCEPTED"
    | "REJECTED"
    | "SUPERSEDED"
    | "EXPIRED";
  currency: string;
  valid_until?: string | null;
  incoterm: string;
  payment_terms: string;
  lead_time_days: number;
  subtotal_amount: string;
  shipping_cost?: string | null;
  insurance_cost?: string | null;
  duty_amount?: string | null;
  tax_amount?: string | null;
  other_charges?: string | null;
  total_landed_cost: string;
  supplier_notes?: string | null;
  submitted_at?: string | null;
  created_at: string;
  updated_at: string;
  items: QuotationItem[];
}

export interface QuotationItemCreate {
  rfq_item_id: string;
  unit_price: string;
  quantity?: string | null;
  moq?: string | null;
  lead_time_days?: number | null;
  notes?: string | null;
}

export interface QuotationCreate {
  currency?: string;
  valid_until?: string | null;
  incoterm: string;
  payment_terms: string;
  lead_time_days?: number;
  shipping_cost?: string | null;
  insurance_cost?: string | null;
  duty_amount?: string | null;
  tax_amount?: string | null;
  other_charges?: string | null;
  supplier_notes?: string | null;
  items: QuotationItemCreate[];
}

export interface QuotationUpdate {
  currency?: string;
  valid_until?: string | null;
  incoterm?: string;
  payment_terms?: string;
  lead_time_days?: number;
  shipping_cost?: string | null;
  insurance_cost?: string | null;
  duty_amount?: string | null;
  tax_amount?: string | null;
  other_charges?: string | null;
  supplier_notes?: string | null;
  items?: QuotationItemCreate[];
}

export interface QuoteComparisonItem {
  rfq_item_id: string;
  product_name_snapshot: string;
  quantity: string;
  unit: string;
  quotes_by_id: Record<
    string,
    {
      unit_price: string;
      line_total: string;
      lead_time_days?: number | null;
      moq?: string | null;
      notes?: string | null;
    }
  >;
  lowest_unit_price_quotation_id?: string | null;
  lowest_unit_price?: string | null;
}

export interface QuoteComparison {
  rfq_id?: string;
  quotation_count: number;
  currency_consistent: boolean;
  currency?: string | null;
  lowest_subtotal_quotation_id?: string | null;
  lowest_subtotal_amount?: string | null;
  lowest_landed_cost_quotation_id?: string | null;
  lowest_total_landed_cost?: string | null;
  fastest_delivery_quotation_id?: string | null;
  fastest_lead_time_days?: number | null;
  quotations: Quotation[];
  items_comparison: QuoteComparisonItem[];
}

export interface NegotiationNote {
  id: string;
  quotation_id: string;
  organization_id: string;
  author_user_id: string;
  note_type: "BUYER_NOTE" | "COUNTER_OFFER" | "SUPPLIER_RESPONSE";
  proposed_target_price?: string | null;
  proposed_terms?: string | null;
  message: string;
  created_at: string;
}

export interface NegotiationNoteCreate {
  note_type: "BUYER_NOTE" | "COUNTER_OFFER" | "SUPPLIER_RESPONSE";
  proposed_target_price?: string | null;
  proposed_terms?: string | null;
  message: string;
}

export interface SupplierSanitizedRFQ {
  id: string;
  rfq_number: string;
  title: string;
  description?: string | null;
  buyer_organization_name?: string | null;
  destination_country: string;
  destination_port?: string | null;
  required_delivery_date?: string | null;
  preferred_incoterm?: string | null;
  preferred_payment_terms?: string | null;
  currency: string;
  status: string;
  created_at: string;
  items: RFQItem[];
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
    const detail =
      errorBody.detail || `HTTP error ${response.status}: ${response.statusText}`;
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return null as unknown as T;
  }

  return response.json();
}

