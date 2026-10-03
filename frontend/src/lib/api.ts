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

