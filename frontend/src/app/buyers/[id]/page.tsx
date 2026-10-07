"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  Users,
  ArrowLeft,
  Building2,
  Globe2,
  Mail,
  Phone,
  MapPin,
  FileText,
  Edit2,
  Trash2,
  AlertCircle,
  ExternalLink,
  X,
  CheckCircle2,
  LogIn,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Buyer,
  BuyerUpdateInput,
  Organization,
  fetchWithAuth,
  fetchBuyer,
  updateBuyer,
  deleteBuyer,
} from "@/lib/api";
import {
  COMMON_COUNTRIES,
  COMMON_INDUSTRIES,
  VERIFICATION_STATUSES,
} from "@/lib/trade-constants";
import { ContactsSection } from "@/components/contacts/contacts-section";

interface BuyerDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function BuyerDetailPage({ params }: BuyerDetailPageProps) {
  const { id: buyerId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoading: authLoading } = useUser();

  const [orgId, setOrgId] = useState<string | null>(null);
  const [buyer, setBuyer] = useState<Buyer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isNotFound, setIsNotFound] = useState(false);

  // Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Edit form fields
  const [companyName, setCompanyName] = useState("");
  const [contactName, setContactName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [country, setCountry] = useState("");
  const [address, setAddress] = useState("");
  const [website, setWebsite] = useState("");
  const [industry, setIndustry] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("UNVERIFIED");
  const [notes, setNotes] = useState("");

  // Delete Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Determine active organization
  useEffect(() => {
    let active = true;
    async function resolveOrg() {
      if (!user) return;
      try {
        const orgFromUrl = searchParams.get("org_id") || searchParams.get("orgId");
        if (orgFromUrl) {
          if (active) setOrgId(orgFromUrl);
          return;
        }

        const storedOrg = localStorage.getItem("globaltrade_active_org_id");
        if (storedOrg) {
          if (active) setOrgId(storedOrg);
          return;
        }

        const orgs = await fetchWithAuth<Organization[]>("/v1/organizations/");
        if (!active) return;
        if (orgs.length > 0) {
          setOrgId(orgs[0].id);
        }
      } catch (err: unknown) {
        if (active) {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg);
        }
      }
    }
    resolveOrg();
    return () => {
      active = false;
    };
  }, [user, searchParams]);

  // Refresh Buyer Details
  const refreshBuyer = useCallback(async () => {
    if (!orgId || !buyerId) return;

    setIsLoading(true);
    setError(null);
    setIsNotFound(false);

    try {
      const data = await fetchBuyer(orgId, buyerId);
      setBuyer(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("404") || msg.toLowerCase().includes("not found")) {
        setIsNotFound(true);
      } else {
        setError(msg || "Failed to load buyer details.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [orgId, buyerId]);

  useEffect(() => {
    let active = true;
    if (!orgId || !buyerId) return;

    async function fetchBuyerData() {
      try {
        const data = await fetchBuyer(orgId!, buyerId);
        if (!active) return;
        setBuyer(data);
        setError(null);
      } catch (err: unknown) {
        if (!active) return;
        const msg = err instanceof Error ? err.message : String(err);
        if (msg.includes("404") || msg.toLowerCase().includes("not found")) {
          setIsNotFound(true);
        } else {
          setError(msg || "Failed to load buyer details.");
        }
      } finally {
        if (active) setIsLoading(false);
      }
    }

    fetchBuyerData();
    return () => {
      active = false;
    };
  }, [orgId, buyerId]);

  // Populate edit modal fields
  const openEditModal = () => {
    if (!buyer) return;
    setCompanyName(buyer.company_name || "");
    setContactName(buyer.contact_name || "");
    setEmail(buyer.email || "");
    setPhone(buyer.phone || "");
    setCountry(buyer.country || "");
    setAddress(buyer.address || "");
    setWebsite(buyer.website || "");
    setIndustry(buyer.industry || "");
    setVerificationStatus(buyer.verification_status || "UNVERIFIED");
    setNotes(buyer.notes || "");
    setFormError(null);
    setShowEditModal(true);
  };

  // Submit edit
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgId || !buyer) return;

    if (!companyName.trim()) {
      setFormError("Company name is required.");
      return;
    }

    if (email.trim()) {
      const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
      if (!emailRegex.test(email.trim())) {
        setFormError("Please enter a valid email address.");
        return;
      }
    }

    if (country.trim() && country.trim().length !== 2) {
      setFormError("Country code must be a 2-letter ISO code.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const payload: BuyerUpdateInput = {
        company_name: companyName.trim(),
        contact_name: contactName.trim() || null,
        email: email.trim() || null,
        phone: phone.trim() || null,
        country: country.trim().toUpperCase() || null,
        address: address.trim() || null,
        website: website.trim() || null,
        industry: industry.trim() || null,
        verification_status: verificationStatus,
        notes: notes.trim() || null,
      };

      const updated = await updateBuyer(orgId, buyer.id, payload);
      setBuyer(updated);
      setShowEditModal(false);
      setSuccessToast("Buyer details successfully updated.");
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFormError(msg || "Failed to update buyer.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete buyer
  const handleDeleteSubmit = async () => {
    if (!orgId || !buyer) return;

    setIsDeleting(true);
    try {
      await deleteBuyer(orgId, buyer.id);
      router.push(`/buyers?org_id=${orgId}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to delete buyer.");
      setShowDeleteModal(false);
    } finally {
      setIsDeleting(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto max-w-5xl py-12 px-4 sm:px-6">
        <div className="h-6 w-32 animate-pulse rounded bg-muted mb-6" />
        <div className="h-48 rounded-2xl bg-muted/40 animate-pulse mb-8 border border-border/40" />
        <div className="h-64 rounded-2xl bg-muted/30 animate-pulse border border-border/40" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto max-w-2xl py-24 px-4 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-500 border border-blue-500/20">
          <Users className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-3">
          Sign In Required
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-8">
          Please sign in to access buyer records.
        </p>
        <a
          href="/auth/login"
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-700 px-5 py-2.5 text-sm font-medium text-white shadow-md shadow-blue-500/20"
        >
          <LogIn className="h-4 w-4" />
          Sign In with Auth0
        </a>
      </div>
    );
  }

  if (isNotFound) {
    return (
      <div className="container mx-auto max-w-3xl py-20 px-4 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive border border-destructive/20">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-2">
          Buyer Not Found
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
          The requested buyer record does not exist or does not belong to the selected organization.
        </p>
        <Link
          href={`/buyers${orgId ? `?org_id=${orgId}` : ""}`}
          className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Return to Buyers Directory
        </Link>
      </div>
    );
  }

  if (!buyer) {
    return (
      <div className="container mx-auto max-w-3xl py-20 px-4 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive border border-destructive/20">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-2">
          Unable to Load Buyer
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
          {error || "An unexpected error occurred."}
        </p>
        <Link
          href={`/buyers${orgId ? `?org_id=${orgId}` : ""}`}
          className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Return to Buyers Directory
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-5xl py-10 px-4 sm:px-6 space-y-8">
      {/* Back Link */}
      <div>
        <Link
          href={`/buyers${orgId ? `?org_id=${orgId}` : ""}`}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors group"
        >
          <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-0.5" />
          Back to Buyers
        </Link>
      </div>

      {/* Success Notification */}
      {successToast && (
        <div className="flex items-center gap-2.5 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm">
          <CheckCircle2 className="h-5 w-5 shrink-0" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Error Notification */}
      {error && (
        <div className="flex items-center justify-between p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshBuyer}
            className="text-destructive hover:bg-destructive/20 text-xs"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Top Profile Card */}
      <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-border/50">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
                {buyer.company_name}
              </h1>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${
                  buyer.verification_status === "VERIFIED"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                    : buyer.verification_status === "PENDING"
                    ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"
                    : buyer.verification_status === "SUSPENDED"
                    ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
                    : "bg-muted text-muted-foreground border-border/60"
                }`}
              >
                {buyer.verification_status}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-muted-foreground">
              {buyer.industry && (
                <span className="flex items-center gap-1.5 font-medium text-foreground">
                  <Building2 className="h-3.5 w-3.5 text-blue-500" />
                  {buyer.industry}
                </span>
              )}
              {buyer.country && (
                <span className="flex items-center gap-1.5 font-mono">
                  <Globe2 className="h-3.5 w-3.5 text-indigo-500" />
                  {buyer.country}
                </span>
              )}
              {buyer.website && (
                <a
                  href={buyer.website.startsWith("http") ? buyer.website : `https://${buyer.website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-blue-500 hover:text-blue-600 transition-colors"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  {buyer.website}
                </a>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={openEditModal}
              className="gap-1.5 text-xs"
            >
              <Edit2 className="h-3.5 w-3.5" />
              Edit Buyer
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowDeleteModal(true)}
              className="gap-1.5 text-xs"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete
            </Button>
          </div>
        </div>

        {/* Company Overview & Contact Info Grids */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-6">
          {/* Primary Contact Details */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Primary Account Information
            </h3>
            <div className="rounded-xl bg-muted/30 border border-border/40 p-4 space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-border/30">
                <span className="text-muted-foreground">Primary Contact:</span>
                <span className="font-semibold text-foreground">
                  {buyer.contact_name || "—"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/30">
                <span className="text-muted-foreground">Contact Email:</span>
                {buyer.email ? (
                  <a
                    href={`mailto:${buyer.email}`}
                    className="font-medium text-blue-500 hover:underline flex items-center gap-1"
                  >
                    <Mail className="h-3 w-3" />
                    {buyer.email}
                  </a>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Contact Phone:</span>
                {buyer.phone ? (
                  <a
                    href={`tel:${buyer.phone}`}
                    className="font-medium text-blue-500 hover:underline flex items-center gap-1"
                  >
                    <Phone className="h-3 w-3" />
                    {buyer.phone}
                  </a>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </div>
            </div>
          </div>

          {/* Physical Address & Jurisdiction */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Registered Address &amp; Location
            </h3>
            <div className="rounded-xl bg-muted/30 border border-border/40 p-4 text-xs space-y-3">
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                <p className="leading-relaxed text-foreground">
                  {buyer.address || "No physical address specified."}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Notes */}
        {buyer.notes && (
          <div className="mt-6 pt-6 border-t border-border/40">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              Trade Notes &amp; Account History
            </h3>
            <p className="text-xs text-foreground/90 whitespace-pre-wrap leading-relaxed rounded-xl bg-muted/20 border border-border/30 p-4">
              {buyer.notes}
            </p>
          </div>
        )}

        {/* Subtle Metadata Footer */}
        <div className="mt-6 pt-4 border-t border-border/30 flex flex-wrap items-center justify-between gap-4 text-[11px] text-muted-foreground">
          <span>
            Created on {new Date(buyer.created_at).toLocaleDateString()}
          </span>
          <span>
            Last modified {new Date(buyer.updated_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* CRM Contacts Section */}
      {orgId && (
        <ContactsSection
          orgId={orgId}
          parentType="buyer"
          parentId={buyer.id}
          canEdit={true}
        />
      )}

      {/* Modal: Edit Buyer */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200 my-8">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-border/50">
              <div className="flex items-center gap-2">
                <Edit2 className="h-5 w-5 text-blue-500" />
                <h3 className="text-base font-bold text-foreground">
                  Edit Buyer Information
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowEditModal(false)}
                className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                aria-label="Close dialog"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {formError && (
              <div className="mb-4 flex items-center gap-2 p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Primary Contact Name
                  </label>
                  <input
                    type="text"
                    value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Contact Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Contact Phone
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Country (ISO-2)
                  </label>
                  <select
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    <option value="">Select country...</option>
                    {COMMON_COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Industry Sector
                  </label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    <option value="">Select industry...</option>
                    {COMMON_INDUSTRIES.map((ind) => (
                      <option key={ind} value={ind}>
                        {ind}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Verification Status
                  </label>
                  <select
                    value={verificationStatus}
                    onChange={(e) => setVerificationStatus(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    {VERIFICATION_STATUSES.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Corporate Website
                  </label>
                  <input
                    type="text"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Business Address
                  </label>
                  <textarea
                    rows={2}
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Trade Notes
                  </label>
                  <textarea
                    rows={2}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-border/50 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowEditModal(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={isSubmitting}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isSubmitting ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Delete Buyer Confirmation */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <h3 className="text-base font-bold text-foreground mb-2">
              Delete Buyer Record
            </h3>
            <p className="text-xs text-muted-foreground mb-5 leading-relaxed">
              Are you sure you want to permanently delete{" "}
              <strong className="text-foreground">{buyer.company_name}</strong>?
              This will also remove all associated CRM contacts. This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowDeleteModal(false)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                variant="destructive"
                onClick={handleDeleteSubmit}
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Confirm Delete"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
