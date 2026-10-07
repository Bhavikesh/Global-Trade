"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  Factory,
  ArrowLeft,
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
  Award,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Supplier,
  SupplierUpdateInput,
  Organization,
  fetchWithAuth,
  fetchSupplier,
  updateSupplier,
  deleteSupplier,
} from "@/lib/api";
import {
  COMMON_COUNTRIES,
  SUPPLIER_TYPES,
  VERIFICATION_STATUSES,
} from "@/lib/trade-constants";
import { ContactsSection } from "@/components/contacts/contacts-section";

interface SupplierDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function SupplierDetailPage({ params }: SupplierDetailPageProps) {
  const { id: supplierId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoading: authLoading } = useUser();

  const [orgId, setOrgId] = useState<string | null>(null);
  const [supplier, setSupplier] = useState<Supplier | null>(null);
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
  const [supplierType, setSupplierType] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("UNVERIFIED");
  const [certifications, setCertifications] = useState("");
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

  // Refresh Supplier Details
  const refreshSupplier = useCallback(async () => {
    if (!orgId || !supplierId) return;

    setIsLoading(true);
    setError(null);
    setIsNotFound(false);

    try {
      const data = await fetchSupplier(orgId, supplierId);
      setSupplier(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("404") || msg.toLowerCase().includes("not found")) {
        setIsNotFound(true);
      } else {
        setError(msg || "Failed to load supplier details.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [orgId, supplierId]);

  useEffect(() => {
    let active = true;
    if (!orgId || !supplierId) return;

    async function fetchSupplierData() {
      try {
        const data = await fetchSupplier(orgId!, supplierId);
        if (!active) return;
        setSupplier(data);
        setError(null);
      } catch (err: unknown) {
        if (!active) return;
        const msg = err instanceof Error ? err.message : String(err);
        if (msg.includes("404") || msg.toLowerCase().includes("not found")) {
          setIsNotFound(true);
        } else {
          setError(msg || "Failed to load supplier details.");
        }
      } finally {
        if (active) setIsLoading(false);
      }
    }

    fetchSupplierData();
    return () => {
      active = false;
    };
  }, [orgId, supplierId]);

  // Populate edit modal fields
  const openEditModal = () => {
    if (!supplier) return;
    setCompanyName(supplier.company_name || "");
    setContactName(supplier.contact_name || "");
    setEmail(supplier.email || "");
    setPhone(supplier.phone || "");
    setCountry(supplier.country || "");
    setAddress(supplier.address || "");
    setWebsite(supplier.website || "");
    setSupplierType(supplier.supplier_type || "");
    setVerificationStatus(supplier.verification_status || "UNVERIFIED");
    setCertifications(supplier.certifications || "");
    setNotes(supplier.notes || "");
    setFormError(null);
    setShowEditModal(true);
  };

  // Submit edit
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgId || !supplier) return;

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
      const payload: SupplierUpdateInput = {
        company_name: companyName.trim(),
        contact_name: contactName.trim() || null,
        email: email.trim() || null,
        phone: phone.trim() || null,
        country: country.trim().toUpperCase() || null,
        address: address.trim() || null,
        website: website.trim() || null,
        supplier_type: supplierType.trim() || null,
        verification_status: verificationStatus,
        certifications: certifications.trim() || null,
        notes: notes.trim() || null,
      };

      const updated = await updateSupplier(orgId, supplier.id, payload);
      setSupplier(updated);
      setShowEditModal(false);
      setSuccessToast("Supplier details successfully updated.");
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFormError(msg || "Failed to update supplier.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete supplier
  const handleDeleteSubmit = async () => {
    if (!orgId || !supplier) return;

    setIsDeleting(true);
    try {
      await deleteSupplier(orgId, supplier.id);
      router.push(`/suppliers?org_id=${orgId}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to delete supplier.");
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
          <Factory className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-3">
          Sign In Required
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-8">
          Please sign in to access supplier records.
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
          Supplier Not Found
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
          The requested supplier record does not exist or does not belong to the selected organization.
        </p>
        <Link
          href={`/suppliers${orgId ? `?org_id=${orgId}` : ""}`}
          className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Return to Suppliers Directory
        </Link>
      </div>
    );
  }

  if (!supplier) {
    return (
      <div className="container mx-auto max-w-3xl py-20 px-4 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive border border-destructive/20">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-2">
          Unable to Load Supplier
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
          {error || "An unexpected error occurred."}
        </p>
        <Link
          href={`/suppliers${orgId ? `?org_id=${orgId}` : ""}`}
          className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Return to Suppliers Directory
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-5xl py-10 px-4 sm:px-6 space-y-8">
      {/* Back Link */}
      <div>
        <Link
          href={`/suppliers${orgId ? `?org_id=${orgId}` : ""}`}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors group"
        >
          <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-0.5" />
          Back to Suppliers
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
            onClick={refreshSupplier}
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
                {supplier.company_name}
              </h1>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${
                  supplier.verification_status === "VERIFIED"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                    : supplier.verification_status === "PENDING"
                    ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"
                    : supplier.verification_status === "SUSPENDED"
                    ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
                    : "bg-muted text-muted-foreground border-border/60"
                }`}
              >
                {supplier.verification_status}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-muted-foreground">
              {supplier.supplier_type && (
                <span className="flex items-center gap-1.5 font-medium text-foreground">
                  <Layers className="h-3.5 w-3.5 text-blue-500" />
                  {supplier.supplier_type}
                </span>
              )}
              {supplier.country && (
                <span className="flex items-center gap-1.5 font-mono">
                  <Globe2 className="h-3.5 w-3.5 text-indigo-500" />
                  {supplier.country}
                </span>
              )}
              {supplier.website && (
                <a
                  href={supplier.website.startsWith("http") ? supplier.website : `https://${supplier.website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-blue-500 hover:text-blue-600 transition-colors"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  {supplier.website}
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
              Edit Supplier
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
                  {supplier.contact_name || "—"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/30">
                <span className="text-muted-foreground">Contact Email:</span>
                {supplier.email ? (
                  <a
                    href={`mailto:${supplier.email}`}
                    className="font-medium text-blue-500 hover:underline flex items-center gap-1"
                  >
                    <Mail className="h-3 w-3" />
                    {supplier.email}
                  </a>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Contact Phone:</span>
                {supplier.phone ? (
                  <a
                    href={`tel:${supplier.phone}`}
                    className="font-medium text-blue-500 hover:underline flex items-center gap-1"
                  >
                    <Phone className="h-3 w-3" />
                    {supplier.phone}
                  </a>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </div>
            </div>
          </div>

          {/* Physical Address & Certifications */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Factory Location &amp; Compliance
            </h3>
            <div className="rounded-xl bg-muted/30 border border-border/40 p-4 text-xs space-y-3">
              <div className="flex items-start gap-2 border-b border-border/30 pb-3">
                <MapPin className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                <p className="leading-relaxed text-foreground">
                  {supplier.address || "No physical factory address specified."}
                </p>
              </div>
              <div className="flex items-start gap-2">
                <Award className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium text-foreground">Certifications:</span>
                  <p className="text-muted-foreground mt-0.5">
                    {supplier.certifications || "No regulatory certifications recorded."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Notes */}
        {supplier.notes && (
          <div className="mt-6 pt-6 border-t border-border/40">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              Sourcing Notes &amp; Capabilities
            </h3>
            <p className="text-xs text-foreground/90 whitespace-pre-wrap leading-relaxed rounded-xl bg-muted/20 border border-border/30 p-4">
              {supplier.notes}
            </p>
          </div>
        )}

        {/* Subtle Metadata Footer */}
        <div className="mt-6 pt-4 border-t border-border/30 flex flex-wrap items-center justify-between gap-4 text-[11px] text-muted-foreground">
          <span>
            Created on {new Date(supplier.created_at).toLocaleDateString()}
          </span>
          <span>
            Last modified {new Date(supplier.updated_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* CRM Contacts Section */}
      {orgId && (
        <ContactsSection
          orgId={orgId}
          parentType="supplier"
          parentId={supplier.id}
          canEdit={true}
        />
      )}

      {/* Modal: Edit Supplier */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200 my-8">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-border/50">
              <div className="flex items-center gap-2">
                <Edit2 className="h-5 w-5 text-blue-500" />
                <h3 className="text-base font-bold text-foreground">
                  Edit Supplier Information
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
                    Supplier Type
                  </label>
                  <select
                    value={supplierType}
                    onChange={(e) => setSupplierType(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    <option value="">Select supplier type...</option>
                    {SUPPLIER_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
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
                    Quality &amp; Compliance Certifications
                  </label>
                  <input
                    type="text"
                    value={certifications}
                    onChange={(e) => setCertifications(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
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
                    Sourcing Notes
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

      {/* Modal: Delete Supplier Confirmation */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <h3 className="text-base font-bold text-foreground mb-2">
              Delete Supplier Record
            </h3>
            <p className="text-xs text-muted-foreground mb-5 leading-relaxed">
              Are you sure you want to permanently delete{" "}
              <strong className="text-foreground">{supplier.company_name}</strong>?
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
