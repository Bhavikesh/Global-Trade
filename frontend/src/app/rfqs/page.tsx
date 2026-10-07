"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useOrganization } from "@/lib/organization-context";
import {
  RFQ,
  fetchWithAuth,
  ApiError,
} from "@/lib/api";
import {
  FileSpreadsheet,
  Plus,
  Search,
  Filter,
  Globe2,
  Calendar,
  Building2,
  ChevronRight,
  ShieldAlert,
  AlertCircle,
  Loader2,
  ArrowUpDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { RFQStatusBadge } from "@/components/rfq/rfq-status-badge";

const STATUS_FILTERS = [
  { value: "ALL", label: "All Statuses" },
  { value: "DRAFT", label: "Draft" },
  { value: "OPEN", label: "Open" },
  { value: "INVITATIONS_SENT", label: "Invitations Sent" },
  { value: "RESPONSES_RECEIVED", label: "Responses Received" },
  { value: "UNDER_REVIEW", label: "Under Review" },
  { value: "NEGOTIATION", label: "Negotiation" },
  { value: "AWARDED", label: "Awarded" },
  { value: "CANCELLED", label: "Cancelled" },
];

export default function RFQDashboardPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useUser();
  const { activeOrg, isLoading: orgLoading } = useOrganization();

  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPermissionDenied, setIsPermissionDenied] = useState(false);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [sortBy] = useState<"created_at" | "rfq_number">("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    let active = true;
    async function fetchInitialRfqs() {
      if (!activeOrg) {
        if (active) {
          setRfqs([]);
          setIsLoading(false);
        }
        return;
      }
      try {
        const data = await fetchWithAuth<RFQ[]>(
          `/v1/organizations/${activeOrg.id}/rfqs/`
        );
        if (active) {
          setRfqs(data);
        }
      } catch (err: unknown) {
        if (active) {
          if (err instanceof ApiError && err.status === 403) {
            setIsPermissionDenied(true);
          } else {
            const msg = err instanceof Error ? err.message : String(err);
            setError(msg);
          }
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    if (!authLoading && !orgLoading) {
      fetchInitialRfqs();
    }
    return () => {
      active = false;
    };
  }, [authLoading, orgLoading, activeOrg]);

  // Filtering & Sorting
  const filteredRfqs = rfqs.filter((rfq) => {
    const matchesStatus =
      statusFilter === "ALL" || rfq.status === statusFilter;
    const matchesSearch =
      searchQuery === "" ||
      rfq.rfq_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rfq.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rfq.destination_country.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (rfq.destination_port &&
        rfq.destination_port.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesStatus && matchesSearch;
  });

  filteredRfqs.sort((a, b) => {
    if (sortBy === "created_at") {
      const timeA = new Date(a.created_at).getTime();
      const timeB = new Date(b.created_at).getTime();
      return sortOrder === "desc" ? timeB - timeA : timeA - timeB;
    } else {
      return sortOrder === "desc"
        ? b.rfq_number.localeCompare(a.rfq_number)
        : a.rfq_number.localeCompare(b.rfq_number);
    }
  });

  if (authLoading || orgLoading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-12 flex flex-col items-center justify-center min-h-[50vh]">
        <Loader2 className="size-8 text-blue-600 animate-spin mb-3" />
        <p className="text-sm text-muted-foreground">
          Loading procurement workspace...
        </p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <div className="max-w-md mx-auto p-8 rounded-2xl border border-border bg-card shadow-sm">
          <Building2 className="size-12 text-muted-foreground mx-auto mb-4 opacity-50" />
          <h2 className="text-xl font-bold text-foreground">Authentication Required</h2>
          <p className="text-sm text-muted-foreground mt-2 mb-6">
            Please sign in to access your organization&apos;s RFQs and trade procurement workflows.
          </p>
          <a
            href="/auth/login"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-blue-600 text-white font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm"
          >
            Sign In with Auth0
          </a>
        </div>
      </div>
    );
  }

  if (!activeOrg) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <div className="max-w-md mx-auto p-8 rounded-2xl border border-border bg-card shadow-sm">
          <Building2 className="size-12 text-muted-foreground mx-auto mb-4 opacity-50" />
          <h2 className="text-xl font-bold text-foreground">No Organization Selected</h2>
          <p className="text-sm text-muted-foreground mt-2 mb-6">
            You must create or join an organization to create and manage RFQs.
          </p>
          <Link
            href="/organizations"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-blue-600 text-white font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm"
          >
            Manage Organizations
          </Link>
        </div>
      </div>
    );
  }

  if (isPermissionDenied) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16">
        <div className="max-w-lg mx-auto p-6 rounded-2xl border border-destructive/20 bg-destructive/5 text-destructive text-center">
          <ShieldAlert className="size-10 mx-auto mb-3" />
          <h2 className="text-lg font-bold">Access Denied (403)</h2>
          <p className="text-sm mt-1 opacity-90">
            Your user account is not authorized as an active member of{" "}
            <strong>{activeOrg.display_name || activeOrg.legal_name}</strong>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">
              Procurement &amp; Sourcing
            </span>
            <span className="text-xs text-muted-foreground font-mono">
              {activeOrg.display_name || activeOrg.legal_name}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            Request For Quotations (RFQs)
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage global trade purchasing inquiries, supplier invitations, and competitive quotes.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/rfqs/new">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm">
              <Plus className="size-4 mr-1.5" />
              Create RFQ
            </Button>
          </Link>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm flex items-start gap-3">
          <AlertCircle className="size-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Unable to load RFQs</p>
            <p className="text-xs mt-0.5 opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* Controls: Search & Status Filter */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <div className="flex-1 relative">
          <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by RFQ number, title, country, or port..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-border bg-card text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
          <div className="flex items-center gap-1.5 border border-border bg-card rounded-xl px-3 py-1.5 text-xs">
            <Filter className="size-3.5 text-muted-foreground" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent border-none text-xs text-foreground cursor-pointer focus:outline-none"
              aria-label="Filter by status"
            >
              {STATUS_FILTERS.map((f) => (
                <option key={f.value} value={f.value} className="bg-popover text-foreground">
                  {f.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() =>
              setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"))
            }
            className="inline-flex items-center gap-1.5 border border-border bg-card rounded-xl px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            title="Toggle sort direction"
          >
            <ArrowUpDown className="size-3.5" />
            <span className="hidden sm:inline">
              {sortOrder === "desc" ? "Newest First" : "Oldest First"}
            </span>
          </button>
        </div>
      </div>

      {/* RFQ Enterprise Table */}
      <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="py-20 text-center flex flex-col items-center justify-center">
            <Loader2 className="size-8 text-blue-600 animate-spin mb-3" />
            <p className="text-sm text-muted-foreground">Loading RFQs...</p>
          </div>
        ) : filteredRfqs.length === 0 ? (
          <div className="py-16 text-center px-4">
            <FileSpreadsheet className="size-12 text-muted-foreground mx-auto mb-3 opacity-40" />
            <h3 className="font-bold text-foreground text-base">
              {rfqs.length === 0
                ? "No RFQs Created Yet"
                : "No matching RFQs found"}
            </h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto mt-1 mb-5">
              {rfqs.length === 0
                ? "Create your first Request For Quotation to invite global suppliers and source products."
                : "Try adjusting your search query or status filter to see other records."}
            </p>
            {rfqs.length === 0 && (
              <Link href="/rfqs/new">
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold">
                  <Plus className="size-4 mr-1" />
                  Create First RFQ
                </Button>
              </Link>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/40 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  <th className="p-4 pl-6">RFQ Reference</th>
                  <th className="p-4">Title &amp; Destination</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-center">Items</th>
                  <th className="p-4 text-center">Invited</th>
                  <th className="p-4">Created Date</th>
                  <th className="p-4 pr-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredRfqs.map((rfq) => (
                  <tr
                    key={rfq.id}
                    className="hover:bg-muted/30 transition-colors group cursor-pointer"
                    onClick={() => {
                      router.push(`/rfqs/${rfq.id}`);
                    }}
                  >
                    <td className="p-4 pl-6 font-mono font-semibold text-foreground">
                      <div className="flex flex-col">
                        <span className="text-blue-600 dark:text-blue-400 group-hover:underline">
                          {rfq.rfq_number}
                        </span>
                        <span className="text-[11px] text-muted-foreground font-sans font-normal">
                          {rfq.currency}
                        </span>
                      </div>
                    </td>

                    <td className="p-4">
                      <div className="flex flex-col">
                        <span className="font-semibold text-foreground line-clamp-1">
                          {rfq.title}
                        </span>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
                          <Globe2 className="size-3 text-muted-foreground" />
                          <span>
                            {rfq.destination_country}
                            {rfq.destination_port ? ` (${rfq.destination_port})` : ""}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="p-4">
                      <RFQStatusBadge status={rfq.status} />
                    </td>

                    <td className="p-4 text-center">
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-muted text-xs font-mono font-medium text-foreground">
                        {rfq.items?.length ?? 0}
                      </span>
                    </td>

                    <td className="p-4 text-center">
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-muted text-xs font-mono font-medium text-foreground">
                        {rfq.invitations?.length ?? 0}
                      </span>
                    </td>

                    <td className="p-4 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5 font-mono">
                        <Calendar className="size-3" />
                        <span>{new Date(rfq.created_at).toLocaleDateString()}</span>
                      </div>
                    </td>

                    <td className="p-4 pr-6 text-right" onClick={(e) => e.stopPropagation()}>
                      <Link
                        href={`/rfqs/${rfq.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        Workspace
                        <ChevronRight className="size-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
