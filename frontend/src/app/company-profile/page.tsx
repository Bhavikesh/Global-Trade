"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  Building2,
  ShieldCheck,
  FileCheck2,
  MapPin,
  AlertCircle,
  CheckCircle2,
  Save,
  RotateCcw,
  LogIn,
  ExternalLink,
  Lock,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchWithAuth, Organization, OrganizationMembership } from "@/lib/api";

const BUSINESS_TYPES = [
  { value: "EXPORTER", label: "Exporter" },
  { value: "IMPORTER", label: "Importer" },
  { value: "BOTH", label: "Exporter & Importer" },
  { value: "LOGISTICS_PROVIDER", label: "Logistics Provider" },
  { value: "CUSTOMS_BROKER", label: "Customs Broker" },
  { value: "FREIGHT_FORWARDER", label: "Freight Forwarder" },
  { value: "FINANCIAL_INSTITUTION", label: "Financial Institution" },
  { value: "OTHER", label: "Other" },
];

const COMMON_COUNTRIES = [
  { code: "US", name: "United States (US)" },
  { code: "IN", name: "India (IN)" },
  { code: "DE", name: "Germany (DE)" },
  { code: "GB", name: "United Kingdom (GB)" },
  { code: "SG", name: "Singapore (SG)" },
  { code: "AE", name: "United Arab Emirates (AE)" },
  { code: "CN", name: "China (CN)" },
  { code: "JP", name: "Japan (JP)" },
  { code: "AU", name: "Australia (AU)" },
  { code: "CA", name: "Canada (CA)" },
  { code: "NL", name: "Netherlands (NL)" },
  { code: "FR", name: "France (FR)" },
  { code: "VN", name: "Vietnam (VN)" },
  { code: "BR", name: "Brazil (BR)" },
];

export default function CompanyProfilePage() {
  const { user, isLoading: authLoading } = useUser();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form Fields
  const [legalName, setLegalName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [businessType, setBusinessType] = useState("EXPORTER");
  const [country, setCountry] = useState("US");
  const [website, setWebsite] = useState("");
  const [address, setAddress] = useState("");
  const [contactInformation, setContactInformation] = useState("");
  const [taxIdentifier, setTaxIdentifier] = useState("");
  const [vatIdentifier, setVatIdentifier] = useState("");
  const [iecNumber, setIecNumber] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("UNVERIFIED");
  const [hasChanges, setHasChanges] = useState(false);

  // Fetch initial organizations list
  useEffect(() => {
    let active = true;
    async function fetchInitialOrgs() {
      if (!user) {
        if (active) setIsLoading(false);
        return;
      }
      try {
        const data = await fetchWithAuth<Organization[]>("/v1/organizations/");
        if (active) {
          setOrganizations(data);
          if (data.length > 0) {
            setSelectedOrgId((prev) =>
              prev && data.some((o) => o.id === prev) ? prev : data[0].id
            );
          } else {
            setSelectedOrgId(null);
          }
        }
      } catch (err: unknown) {
        if (active) {
          const msg = err instanceof Error ? err.message : String(err);
          setErrorMessage(msg);
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }
    fetchInitialOrgs();
    return () => {
      active = false;
    };
  }, [user]);

  // Load selected organization details & user's role
  const loadOrgDetails = useCallback(async (orgId: string) => {
    try {
      const [orgData, membersData] = await Promise.all([
        fetchWithAuth<Organization>(`/v1/organizations/${orgId}`),
        fetchWithAuth<OrganizationMembership[]>(`/v1/organizations/${orgId}/members`),
      ]);

      setLegalName(orgData.legal_name || "");
      setDisplayName(orgData.display_name || "");
      setBusinessType(orgData.business_type || "EXPORTER");
      setCountry(orgData.country || "US");
      setWebsite(orgData.website || "");
      setAddress(orgData.address || "");
      setContactInformation(orgData.contact_information || "");
      setTaxIdentifier(orgData.tax_identifier || "");
      setVatIdentifier(orgData.vat_identifier || "");
      setIecNumber(orgData.iec_number || "");
      setVerificationStatus(orgData.verification_status || "UNVERIFIED");
      setHasChanges(false);

      if (user && membersData) {
        try {
          const myProfile = await fetchWithAuth<{ id: string }>("/v1/users/me");
          const myMembership = membersData.find((m) => m.user_id === myProfile.id);
          setUserRole(myMembership ? myMembership.role : "MEMBER");
        } catch {
          setUserRole("MEMBER");
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg || "Failed to load organization details.");
    }
  }, [user]);

  useEffect(() => {
    let active = true;
    if (!selectedOrgId) return;

    async function fetchDetails() {
      try {
        const [orgData, membersData] = await Promise.all([
          fetchWithAuth<Organization>(`/v1/organizations/${selectedOrgId}`),
          fetchWithAuth<OrganizationMembership[]>(`/v1/organizations/${selectedOrgId}/members`),
        ]);

        if (!active) return;

        setLegalName(orgData.legal_name || "");
        setDisplayName(orgData.display_name || "");
        setBusinessType(orgData.business_type || "EXPORTER");
        setCountry(orgData.country || "US");
        setWebsite(orgData.website || "");
        setAddress(orgData.address || "");
        setContactInformation(orgData.contact_information || "");
        setTaxIdentifier(orgData.tax_identifier || "");
        setVatIdentifier(orgData.vat_identifier || "");
        setIecNumber(orgData.iec_number || "");
        setVerificationStatus(orgData.verification_status || "UNVERIFIED");
        setHasChanges(false);

        if (user && membersData) {
          try {
            const myProfile = await fetchWithAuth<{ id: string }>("/v1/users/me");
            const myMembership = membersData.find((m) => m.user_id === myProfile.id);
            if (active) setUserRole(myMembership ? myMembership.role : "MEMBER");
          } catch {
            if (active) setUserRole("MEMBER");
          }
        }
      } catch (err: unknown) {
        if (active) {
          const msg = err instanceof Error ? err.message : String(err);
          setErrorMessage(msg || "Failed to load organization details.");
        }
      }
    }

    fetchDetails();
    return () => {
      active = false;
    };
  }, [selectedOrgId, user]);

  const isAdmin = userRole === "ADMIN";

  const handleFieldChange = (setter: React.Dispatch<React.SetStateAction<string>>, val: string) => {
    setter(val);
    setHasChanges(true);
    setSuccessMessage(null);
  };

  const handleReset = () => {
    if (selectedOrgId) {
      loadOrgDetails(selectedOrgId);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId || !isAdmin) return;

    if (!legalName.trim()) {
      setErrorMessage("Legal entity name is required.");
      return;
    }

    if (country.trim().length !== 2) {
      setErrorMessage("Country code must be a 2-letter ISO code.");
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const updated = await fetchWithAuth<Organization>(
        `/v1/organizations/${selectedOrgId}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            legal_name: legalName.trim(),
            display_name: displayName.trim() || null,
            business_type: businessType || null,
            country: country.trim().toUpperCase(),
            website: website.trim() || null,
            address: address.trim() || null,
            contact_information: contactInformation.trim() || null,
            tax_identifier: taxIdentifier.trim() || null,
            vat_identifier: vatIdentifier.trim() || null,
            iec_number: iecNumber.trim() || null,
          }),
        }
      );

      // Refresh list to keep names updated
      setOrganizations((prev) =>
        prev.map((o) => (o.id === updated.id ? updated : o))
      );
      setLegalName(updated.legal_name || "");
      setDisplayName(updated.display_name || "");
      setWebsite(updated.website || "");
      setHasChanges(false);
      setSuccessMessage("Company Profile successfully updated and synchronized.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg || "Failed to update company profile.");
    } finally {
      setIsSaving(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto max-w-5xl py-12 px-4 sm:px-6">
        <div className="h-8 w-64 animate-pulse rounded-lg bg-muted mb-3" />
        <div className="h-4 w-96 animate-pulse rounded bg-muted/60 mb-8" />
        <div className="space-y-6">
          <div className="h-48 animate-pulse rounded-2xl bg-muted/40" />
          <div className="h-64 animate-pulse rounded-2xl bg-muted/40" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto max-w-2xl py-24 px-4 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-500 border border-blue-500/20">
          <Building2 className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-3">
          Sign In to Access Company Profile
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-8">
          Company profiles are tenant-isolated. Sign in with your verified
          account to manage legal trade records and regulatory compliance IDs.
        </p>
        <a
          href="/auth/login"
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 px-5 py-2.5 text-sm font-medium text-white shadow-md shadow-blue-500/20 transition-all"
        >
          <LogIn className="h-4 w-4" />
          Sign In with Auth0
        </a>
      </div>
    );
  }

  if (organizations.length === 0) {
    return (
      <div className="container mx-auto max-w-3xl py-20 px-4 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-muted text-muted-foreground border border-border">
          <Building2 className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-2">
          No Organization Found
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
          To maintain a Company Profile, you must first create or join an organization workspace.
        </p>
        <Link
          href="/organizations"
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 text-sm font-medium transition-all shadow-md shadow-blue-500/20"
        >
          Go to Organizations
        </Link>
      </div>
    );
  }

  const selectedOrg = organizations.find((o) => o.id === selectedOrgId);

  return (
    <div className="container mx-auto max-w-5xl py-10 px-4 sm:px-6">
      {/* Header & Org Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
              Company Profile
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              T1.7 Scope
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Official trade identity, regulatory registrations, and operational jurisdiction.
          </p>
        </div>

        {/* Organization Switcher */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <label className="block text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
              Active Organization
            </label>
            <div className="relative">
              <select
                value={selectedOrgId || ""}
                onChange={(e) => setSelectedOrgId(e.target.value)}
                className="appearance-none pr-9 pl-3.5 py-2 rounded-xl border border-input bg-background text-xs font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 cursor-pointer shadow-sm"
              >
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.display_name || org.legal_name}
                  </option>
                ))}
              </select>
              <ChevronDown className="h-4 w-4 text-muted-foreground absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          <div className="pt-4">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border ${
                isAdmin
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                  : "bg-muted text-muted-foreground border-border"
              }`}
            >
              {isAdmin ? (
                <ShieldCheck className="h-3.5 w-3.5" />
              ) : (
                <Lock className="h-3.5 w-3.5" />
              )}
              Role: {userRole || "MEMBER"}
            </span>
          </div>
        </div>
      </div>

      {/* Role permission notification for non-admins */}
      {!isAdmin && (
        <div className="mt-6 flex items-center gap-2.5 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 text-xs">
          <Lock className="h-4 w-4 flex-shrink-0" />
          <span>
            <strong>Read-only View:</strong> You have <code>{userRole}</code> privileges.
            Only organization Administrators (ADMIN) can update company profile details.
          </span>
        </div>
      )}

      {/* Error & Success Feedback Banners */}
      {errorMessage && (
        <div className="mt-6 flex items-center gap-2.5 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="mt-6 flex items-center gap-2.5 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm">
          <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Main Profile Form */}
      <form onSubmit={handleSave} className="mt-8 space-y-8">
        {/* Section 1: Legal Entity Overview */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 mb-6 border-b border-border/50">
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-500" />
              <h2 className="text-base font-semibold text-foreground">
                Legal Entity Overview
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Verification:</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                {verificationStatus}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Official Registered Legal Name *
              </label>
              <input
                type="text"
                required
                disabled={!isAdmin || isSaving}
                value={legalName}
                onChange={(e) => handleFieldChange(setLegalName, e.target.value)}
                placeholder="e.g. Apex Global Logistics Private Limited"
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                Must match your certificate of incorporation / registration.
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Public Display / Trade Name
              </label>
              <input
                type="text"
                disabled={!isAdmin || isSaving}
                value={displayName}
                onChange={(e) => handleFieldChange(setDisplayName, e.target.value)}
                placeholder="e.g. Apex Global"
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                Name shown to buyers, suppliers, and external partners.
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Business Classification / Type
              </label>
              <select
                disabled={!isAdmin || isSaving}
                value={businessType}
                onChange={(e) => handleFieldChange(setBusinessType, e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              >
                {BUSINESS_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Corporate Website
              </label>
              <div className="relative">
                <input
                  type="text"
                  disabled={!isAdmin || isSaving}
                  value={website}
                  onChange={(e) => handleFieldChange(setWebsite, e.target.value)}
                  placeholder="https://example.com"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
                />
                {website && (
                  <a
                    href={website.startsWith("http") ? website : `https://${website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute right-3 top-3 text-muted-foreground hover:text-blue-500"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Location & Registered Address */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2 pb-4 mb-6 border-b border-border/50">
            <MapPin className="h-5 w-5 text-indigo-500" />
            <h2 className="text-base font-semibold text-foreground">
              Jurisdiction &amp; Physical Address
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Operating Country (ISO-2) *
              </label>
              <select
                disabled={!isAdmin || isSaving}
                value={country}
                onChange={(e) => handleFieldChange(setCountry, e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              >
                {COMMON_COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-muted-foreground mt-1">
                ISO 3166-1 alpha-2 standard country code.
              </p>
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Registered Physical Address
              </label>
              <textarea
                rows={3}
                disabled={!isAdmin || isSaving}
                value={address}
                onChange={(e) => handleFieldChange(setAddress, e.target.value)}
                placeholder="Suite / Unit, Street Address, City, State/Province, Postal Code"
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              />
            </div>

            <div className="md:col-span-3">
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Operational Contact Details &amp; Directory Notes
              </label>
              <textarea
                rows={2}
                disabled={!isAdmin || isSaving}
                value={contactInformation}
                onChange={(e) =>
                  handleFieldChange(setContactInformation, e.target.value)
                }
                placeholder="Key trade representatives, phone numbers, trade desk email, operational hours"
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Regulatory & Trade Identifiers */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2 pb-4 mb-6 border-b border-border/50">
            <FileCheck2 className="h-5 w-5 text-emerald-500" />
            <h2 className="text-base font-semibold text-foreground">
              Trade Compliance &amp; Regulatory Identifiers
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Tax Identifier (EIN / GSTIN / Tax ID)
              </label>
              <input
                type="text"
                disabled={!isAdmin || isSaving}
                value={taxIdentifier}
                onChange={(e) =>
                  handleFieldChange(setTaxIdentifier, e.target.value)
                }
                placeholder="e.g. 12-3456789 or 27AAAAA0000A1Z5"
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm font-mono text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                National tax registration number.
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                VAT Registration Number
              </label>
              <input
                type="text"
                disabled={!isAdmin || isSaving}
                value={vatIdentifier}
                onChange={(e) =>
                  handleFieldChange(setVatIdentifier, e.target.value)
                }
                placeholder="e.g. GB999 9999 73 or DE123456789"
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm font-mono text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                Value Added Tax identification number.
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                Import Export Code (IEC)
              </label>
              <input
                type="text"
                disabled={!isAdmin || isSaving}
                value={iecNumber}
                onChange={(e) => handleFieldChange(setIecNumber, e.target.value)}
                placeholder="e.g. 0102030405"
                className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm font-mono text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                DGFT IEC or customs foreign trade license.
              </p>
            </div>
          </div>
        </div>

        {/* Section 4: Metadata Footer */}
        {selectedOrg && (
          <div className="rounded-xl bg-muted/30 border border-border/40 p-4 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-muted-foreground gap-2">
            <div className="flex items-center gap-1 font-mono">
              <span>Organization UUID:</span>
              <span className="text-foreground">{selectedOrg.id}</span>
            </div>
            <div className="flex items-center gap-4">
              <span>
                Created: {new Date(selectedOrg.created_at).toLocaleDateString()}
              </span>
              <span>
                Updated: {new Date(selectedOrg.updated_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        )}

        {/* Action Controls for Admin */}
        {isAdmin && (
          <div className="pt-4 flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              size="default"
              onClick={handleReset}
              disabled={!hasChanges || isSaving}
              className="gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </Button>
            <Button
              type="submit"
              size="default"
              disabled={!hasChanges || isSaving}
              className="gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md shadow-blue-500/20"
            >
              <Save className="h-4 w-4" />
              {isSaving ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        )}
      </form>
    </div>
  );
}
