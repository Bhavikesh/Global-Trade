"use client";

import React, { useState, useEffect, useCallback, useTransition } from "react";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  Factory,
  Plus,
  Search,
  Building2,
  AlertCircle,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  LogIn,
  RotateCcw,
  Globe2,
  X,
  CheckCircle2,
  Award,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Supplier,
  SupplierCreateInput,
  Organization,
  fetchWithAuth,
  fetchSuppliers,
  createSupplier,
} from "@/lib/api";
import {
  COMMON_COUNTRIES,
  SUPPLIER_TYPES,
  VERIFICATION_STATUSES,
} from "@/lib/trade-constants";

export default function SuppliersPage() {
  const { user, isLoading: authLoading } = useUser();
  const [, startTransition] = useTransition();

  // Organization context
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [isLoadingOrgs, setIsLoadingOrgs] = useState(true);

  // Supplier list state
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);
  const [isLoadingSuppliers, setIsLoadingSuppliers] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  // Search & Filters state
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [selectedSupplierType, setSelectedSupplierType] = useState("");

  // Create Supplier Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Form fields for creation
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

  // Debounce search query input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch initial organizations
  useEffect(() => {
    let active = true;
    async function loadOrgs() {
      if (!user) {
        if (active) setIsLoadingOrgs(false);
        return;
      }
      try {
        const orgs = await fetchWithAuth<Organization[]>("/v1/organizations/");
        if (!active) return;
        setOrganizations(orgs);

        if (orgs.length > 0) {
          const urlParams = new URLSearchParams(window.location.search);
          const orgFromUrl = urlParams.get("org_id") || urlParams.get("orgId");
          const storedOrg = localStorage.getItem("globaltrade_active_org_id");

          const validOrg =
            (orgFromUrl && orgs.find((o) => o.id === orgFromUrl)?.id) ||
            (storedOrg && orgs.find((o) => o.id === storedOrg)?.id) ||
            orgs[0].id;

          setSelectedOrgId(validOrg);
        } else {
          setSelectedOrgId(null);
        }
      } catch (err: unknown) {
        if (active) {
          const msg = err instanceof Error ? err.message : String(err);
          setListError(msg || "Failed to load organizations.");
        }
      } finally {
        if (active) setIsLoadingOrgs(false);
      }
    }
    loadOrgs();
    return () => {
      active = false;
    };
  }, [user]);

  // Handle org change
  const handleOrgChange = (orgId: string) => {
    setSelectedOrgId(orgId);
    localStorage.setItem("globaltrade_active_org_id", orgId);
    setOffset(0);
  };

  // Refresh Suppliers list
  const refreshSuppliers = useCallback(async () => {
    if (!selectedOrgId) {
      setSuppliers([]);
      setTotal(0);
      setIsLoadingSuppliers(false);
      return;
    }

    setIsLoadingSuppliers(true);
    setListError(null);

    try {
      const data = await fetchSuppliers(selectedOrgId, {
        q: debouncedSearch.trim() || undefined,
        country: selectedCountry || undefined,
        verification_status: selectedStatus || undefined,
        supplier_type: selectedSupplierType || undefined,
        limit,
        offset,
      });

      startTransition(() => {
        setSuppliers(data.items);
        setTotal(data.total);
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setListError(msg || "Failed to load suppliers list.");
    } finally {
      setIsLoadingSuppliers(false);
    }
  }, [
    selectedOrgId,
    debouncedSearch,
    selectedCountry,
    selectedStatus,
    selectedSupplierType,
    limit,
    offset,
  ]);

  useEffect(() => {
    let active = true;
    if (!selectedOrgId) return;

    async function fetchSuppliersData() {
      try {
        const data = await fetchSuppliers(selectedOrgId!, {
          q: debouncedSearch.trim() || undefined,
          country: selectedCountry || undefined,
          verification_status: selectedStatus || undefined,
          supplier_type: selectedSupplierType || undefined,
          limit,
          offset,
        });

        if (!active) return;
        startTransition(() => {
          setSuppliers(data.items);
          setTotal(data.total);
        });
      } catch (err: unknown) {
        if (!active) return;
        const msg = err instanceof Error ? err.message : String(err);
        setListError(msg || "Failed to load suppliers list.");
      } finally {
        if (active) setIsLoadingSuppliers(false);
      }
    }

    fetchSuppliersData();
    return () => {
      active = false;
    };
  }, [
    selectedOrgId,
    debouncedSearch,
    selectedCountry,
    selectedStatus,
    selectedSupplierType,
    limit,
    offset,
  ]);

  // Reset pagination offset whenever search or filter criteria change
  const handleSearchChange = (val: string) => {
    setSearchQuery(val);
    setOffset(0);
  };

  const handleCountryFilterChange = (val: string) => {
    setSelectedCountry(val);
    setOffset(0);
  };

  const handleStatusFilterChange = (val: string) => {
    setSelectedStatus(val);
    setOffset(0);
  };

  const handleSupplierTypeFilterChange = (val: string) => {
    setSelectedSupplierType(val);
    setOffset(0);
  };

  const resetFilters = () => {
    setSearchQuery("");
    setDebouncedSearch("");
    setSelectedCountry("");
    setSelectedStatus("");
    setSelectedSupplierType("");
    setOffset(0);
  };

  // Open Create Modal
  const openCreateModal = () => {
    setCompanyName("");
    setContactName("");
    setEmail("");
    setPhone("");
    setCountry("");
    setAddress("");
    setWebsite("");
    setSupplierType("");
    setVerificationStatus("UNVERIFIED");
    setCertifications("");
    setNotes("");
    setFormError(null);
    setShowCreateModal(true);
  };

  // Handle Create Submit
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId) return;

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
      const payload: SupplierCreateInput = {
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

      const newSupplier = await createSupplier(selectedOrgId, payload);
      setShowCreateModal(false);
      setSuccessToast(`Supplier "${newSupplier.company_name}" successfully registered.`);
      setTimeout(() => setSuccessToast(null), 4000);

      // Refresh list
      await refreshSuppliers();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFormError(msg || "Failed to create supplier.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Auth & loading guard
  if (authLoading || isLoadingOrgs) {
    return (
      <div className="container mx-auto max-w-7xl py-12 px-4 sm:px-6">
        <div className="h-8 w-48 animate-pulse rounded-lg bg-muted mb-4" />
        <div className="h-4 w-96 animate-pulse rounded bg-muted/60 mb-8" />
        <div className="h-96 rounded-2xl bg-muted/30 animate-pulse border border-border/40" />
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
          Sign In to Access Suppliers
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-8">
          Supplier directories are strictly tenant-isolated. Sign in to view and manage suppliers and vendors for your active organization.
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
          To manage suppliers, you must belong to an organization workspace.
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

  const hasActiveFilters =
    Boolean(debouncedSearch) ||
    Boolean(selectedCountry) ||
    Boolean(selectedStatus) ||
    Boolean(selectedSupplierType);

  return (
    <div className="container mx-auto max-w-7xl py-10 px-4 sm:px-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
              Suppliers Directory
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
              Vendor Sourcing
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Maintain international suppliers, manufacturers, compliance credentials, and sourcing partners.
          </p>
        </div>

        {/* Right side: Org switcher & Add Supplier button */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <label className="block text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
              Active Organization
            </label>
            <div className="relative">
              <select
                value={selectedOrgId || ""}
                onChange={(e) => handleOrgChange(e.target.value)}
                className="appearance-none pr-9 pl-3.5 py-2 rounded-xl border border-input bg-background text-xs font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 cursor-pointer shadow-xs"
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
            <Button
              onClick={openCreateModal}
              className="gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md shadow-blue-500/20"
            >
              <Plus className="h-4 w-4" />
              Add Supplier
            </Button>
          </div>
        </div>
      </div>

      {/* Success Notification */}
      {successToast && (
        <div className="mt-6 flex items-center gap-2.5 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm">
          <CheckCircle2 className="h-5 w-5 shrink-0" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Error Notification */}
      {listError && (
        <div className="mt-6 flex items-center justify-between p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>{listError}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshSuppliers}
            className="text-destructive hover:bg-destructive/20"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Search & Filter Toolbar */}
      <div className="mt-8 rounded-2xl border border-border bg-card p-5 shadow-xs">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Free text search */}
          <div className="lg:col-span-2 relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Search vendor, contact, certifications..."
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            />
          </div>

          {/* Country filter */}
          <div>
            <select
              value={selectedCountry}
              onChange={(e) => handleCountryFilterChange(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            >
              <option value="">All Countries</option>
              {COMMON_COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Verification Status filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => handleStatusFilterChange(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            >
              <option value="">All Statuses</option>
              {VERIFICATION_STATUSES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Supplier Type filter */}
          <div>
            <select
              value={selectedSupplierType}
              onChange={(e) => handleSupplierTypeFilterChange(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            >
              <option value="">All Supplier Types</option>
              {SUPPLIER_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Filter Summary & Reset */}
        {hasActiveFilters && (
          <div className="mt-3 pt-3 border-t border-border/50 flex items-center justify-between text-xs text-muted-foreground">
            <span>Filters applied</span>
            <button
              type="button"
              onClick={resetFilters}
              className="inline-flex items-center gap-1 text-blue-500 hover:text-blue-600 font-medium"
            >
              <RotateCcw className="h-3 w-3" />
              Reset filters
            </button>
          </div>
        )}
      </div>

      {/* Results Count & Data Table */}
      <div className="mt-6 rounded-2xl border border-border bg-card shadow-xs overflow-hidden">
        {/* Table Top Status Bar */}
        <div className="px-6 py-4 border-b border-border/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-muted-foreground">
          <div className="font-medium text-foreground">
            {isLoadingSuppliers ? (
              <span>Loading suppliers...</span>
            ) : total === 0 ? (
              <span>0 suppliers found</span>
            ) : (
              <span>
                Showing <strong>{offset + 1}</strong> to{" "}
                <strong>{Math.min(offset + limit, total)}</strong> of{" "}
                <strong>{total}</strong> suppliers
              </span>
            )}
          </div>
        </div>

        {/* Table / Responsive List */}
        {isLoadingSuppliers ? (
          <div className="p-6 space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="h-12 w-full animate-pulse rounded-xl bg-muted/40"
              />
            ))}
          </div>
        ) : suppliers.length === 0 ? (
          /* Empty State */
          <div className="p-12 text-center">
            <Factory className="h-10 w-10 mx-auto mb-3 text-muted-foreground/40" />
            <h3 className="text-base font-semibold text-foreground mb-1">
              {hasActiveFilters ? "No matching suppliers found" : "No suppliers yet"}
            </h3>
            <p className="text-xs text-muted-foreground max-w-sm mx-auto mb-6">
              {hasActiveFilters
                ? "Try adjusting your search query or removing filter criteria to find suppliers."
                : "Register your first supplier or manufacturing partner to manage procurement relationships and quotations."}
            </p>
            {hasActiveFilters ? (
              <Button
                variant="outline"
                size="sm"
                onClick={resetFilters}
                className="gap-1.5 text-xs"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Clear Filters
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={openCreateModal}
                className="gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs"
              >
                <Plus className="h-3.5 w-3.5" />
                Add Supplier
              </Button>
            )}
          </div>
        ) : (
          /* Data Table */
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border/60 bg-muted/30 text-muted-foreground font-medium uppercase tracking-wider">
                  <th className="py-3.5 px-6">Company Name</th>
                  <th className="py-3.5 px-6">Primary Contact</th>
                  <th className="py-3.5 px-6">Country</th>
                  <th className="py-3.5 px-6">Supplier Type</th>
                  <th className="py-3.5 px-6">Certifications</th>
                  <th className="py-3.5 px-6">Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {suppliers.map((supplier) => (
                  <tr
                    key={supplier.id}
                    className="hover:bg-muted/20 transition-colors group"
                  >
                    <td className="py-4 px-6 font-semibold text-foreground">
                      <Link
                        href={`/suppliers/${supplier.id}?org_id=${selectedOrgId}`}
                        className="text-foreground hover:text-blue-600 transition-colors inline-flex items-center gap-1.5"
                      >
                        {supplier.company_name}
                      </Link>
                      {supplier.website && (
                        <p className="text-[11px] text-muted-foreground font-normal truncate max-w-xs">
                          {supplier.website}
                        </p>
                      )}
                    </td>

                    <td className="py-4 px-6 text-muted-foreground">
                      <div className="font-medium text-foreground">
                        {supplier.contact_name || "—"}
                      </div>
                      <div className="text-[11px] text-muted-foreground">
                        {supplier.email || supplier.phone || "—"}
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      {supplier.country ? (
                        <span className="inline-flex items-center gap-1 font-mono text-xs px-2 py-0.5 rounded-md bg-muted border border-border/50 text-foreground">
                          <Globe2 className="h-3 w-3 text-muted-foreground" />
                          {supplier.country}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>

                    <td className="py-4 px-6 text-muted-foreground">
                      {supplier.supplier_type ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[11px] font-medium border border-blue-500/20">
                          {supplier.supplier_type}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>

                    <td className="py-4 px-6 text-muted-foreground">
                      {supplier.certifications ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-foreground truncate max-w-xs">
                          <Award className="h-3 w-3 text-amber-500 shrink-0" />
                          {supplier.certifications}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>

                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
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
                    </td>

                    <td className="py-4 px-6 text-right">
                      <Link
                        href={`/suppliers/${supplier.id}?org_id=${selectedOrgId}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-border/80 bg-background hover:bg-muted text-xs font-medium text-foreground transition-colors"
                      >
                        <span>Details</span>
                        <ExternalLink className="h-3 w-3 text-muted-foreground" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {total > limit && (
          <div className="px-6 py-4 border-t border-border/50 flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              Page {Math.floor(offset / limit) + 1} of{" "}
              {Math.ceil(total / limit)}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={offset === 0 || isLoadingSuppliers}
                onClick={() => setOffset((prev) => Math.max(0, prev - limit))}
                className="gap-1 text-xs"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + limit >= total || isLoadingSuppliers}
                onClick={() => setOffset((prev) => prev + limit)}
                className="gap-1 text-xs"
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Modal: Create Supplier */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200 my-8">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-border/50">
              <div className="flex items-center gap-2">
                <Factory className="h-5 w-5 text-blue-500" />
                <h3 className="text-base font-bold text-foreground">
                  Register New Supplier
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
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

            <form onSubmit={handleCreateSubmit} className="space-y-4">
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
                    placeholder="e.g. Apex Industrial Sourcing Ltd."
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
                    placeholder="e.g. Marcus Vance"
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
                    placeholder="marcus@apexindustrial.com"
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
                    placeholder="+1 (555) 098-7654"
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
                    placeholder="e.g. ISO 9001:2015, CE Certified, GMP, RoHS"
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
                    placeholder="https://apexindustrial.com"
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
                    placeholder="Factory Complex 4, Industrial Zone B"
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
                    placeholder="Production capacity, lead times, export credentials, factory audit notes"
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-border/50 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCreateModal(false)}
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
                  {isSubmitting ? "Registering..." : "Create Supplier"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
