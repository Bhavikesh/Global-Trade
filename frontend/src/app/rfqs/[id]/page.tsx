"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useOrganization } from "@/lib/organization-context";
import {
  RFQ,
  Quotation,
  QuoteComparison,
  SupplierInvitationInput,
  fetchWithAuth,
  ApiError,
} from "@/lib/api";
import {
  FileSpreadsheet,
  ArrowLeft,
  Globe2,
  Package,
  UserPlus,
  Award,
  Layers,
  Send,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  DollarSign,
  Share2,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { RFQStatusBadge } from "@/components/rfq/rfq-status-badge";
import { QuotationStatusBadge } from "@/components/rfq/quotation-status-badge";
import { RFQWorkflowPipeline } from "@/components/rfq/rfq-workflow-pipeline";
import { QuoteComparisonView } from "@/components/rfq/quote-comparison";
import { AwardModal } from "@/components/rfq/award-modal";
import { InviteSupplierModal } from "@/components/rfq/invite-supplier-modal";

export default function RFQWorkspacePage() {
  const params = useParams();
  const rfqId = params.id as string;

  const { isLoading: authLoading } = useUser();
  const { activeOrg, isLoading: orgLoading, userRole } = useOrganization();

  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [comparison, setComparison] = useState<QuoteComparison | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPermissionDenied, setIsPermissionDenied] = useState(false);

  // Tabs: 'requirements', 'invitations', 'quotations', 'comparison'
  const [activeTab, setActiveTab] = useState<
    "requirements" | "invitations" | "quotations" | "comparison"
  >("requirements");

  // Modals & Action states
  const [isPublishing, setIsPublishing] = useState(false);
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [awardQuoteTarget, setAwardQuoteTarget] = useState<Quotation | null>(null);

  const canMutate = userRole === "ADMIN" || userRole === "OWNER";

  const loadRFQData = useCallback(async () => {
    if (!activeOrg || !rfqId) return;

    try {
      setError(null);
      setIsPermissionDenied(false);

      // 1. Fetch RFQ Detail
      const rfqData = await fetchWithAuth<RFQ>(
        `/v1/organizations/${activeOrg.id}/rfqs/${rfqId}`
      );
      setRfq(rfqData);

      // 2. Fetch Buyer Quotations (if eligible and authorized)
      try {
        const quotesData = await fetchWithAuth<Quotation[]>(
          `/v1/organizations/${activeOrg.id}/rfqs/${rfqId}/quotations`
        );
        setQuotations(quotesData);
      } catch {
        setQuotations([]);
      }

      // 3. Fetch Comparison Matrix
      try {
        const compData = await fetchWithAuth<QuoteComparison>(
          `/v1/organizations/${activeOrg.id}/rfqs/${rfqId}/comparison`
        );
        setComparison(compData);
      } catch {
        setComparison(null);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 403) {
        setIsPermissionDenied(true);
      } else {
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
      }
    } finally {
      setIsLoading(false);
    }
  }, [activeOrg, rfqId]);

  useEffect(() => {
    let active = true;
    async function fetchInitial() {
      if (!activeOrg || !rfqId) {
        if (active) setIsLoading(false);
        return;
      }
      try {
        const rfqData = await fetchWithAuth<RFQ>(
          `/v1/organizations/${activeOrg.id}/rfqs/${rfqId}`
        );
        if (active) {
          setRfq(rfqData);
        }

        try {
          const quotesData = await fetchWithAuth<Quotation[]>(
            `/v1/organizations/${activeOrg.id}/rfqs/${rfqId}/quotations`
          );
          if (active) setQuotations(quotesData);
        } catch {
          if (active) setQuotations([]);
        }

        try {
          const compData = await fetchWithAuth<QuoteComparison>(
            `/v1/organizations/${activeOrg.id}/rfqs/${rfqId}/comparison`
          );
          if (active) setComparison(compData);
        } catch {
          if (active) setComparison(null);
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
      fetchInitial();
    }
    return () => {
      active = false;
    };
  }, [authLoading, orgLoading, activeOrg, rfqId]);

  // Handle Opening / Publishing RFQ
  async function handleOpenRFQ() {
    if (!activeOrg || !rfq) return;
    setIsPublishing(true);
    try {
      const updated = await fetchWithAuth<RFQ>(
        `/v1/organizations/${activeOrg.id}/rfqs/${rfq.id}/open`,
        { method: "POST" }
      );
      setRfq(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setIsPublishing(false);
    }
  }

  // Handle Sending Supplier Invitations
  async function handleSendInvitations(invites: SupplierInvitationInput[]) {
    if (!activeOrg || !rfq) return;
    await fetchWithAuth(
      `/v1/organizations/${activeOrg.id}/rfqs/${rfq.id}/invitations`,
      {
        method: "POST",
        body: JSON.stringify({ invitations: invites }),
      }
    );
    await loadRFQData();
  }

  // Handle Award Execution
  async function handleAwardQuotation(quoteId: string) {
    if (!activeOrg || !rfq) return;
    const updated = await fetchWithAuth<RFQ>(
      `/v1/organizations/${activeOrg.id}/rfqs/${rfq.id}/award/${quoteId}`,
      { method: "POST" }
    );
    setRfq(updated);
    await loadRFQData();
  }

  if (authLoading || orgLoading || isLoading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <Loader2 className="size-8 text-blue-600 animate-spin mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">Loading RFQ Workspace...</p>
      </div>
    );
  }

  if (isPermissionDenied) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16">
        <div className="max-w-lg mx-auto p-8 rounded-2xl border border-destructive/20 bg-destructive/5 text-destructive text-center">
          <ShieldAlert className="size-10 mx-auto mb-3" />
          <h2 className="text-lg font-bold">Access Denied (403)</h2>
          <p className="text-sm mt-1">
            You do not have active buyer membership in this organization to view this RFQ.
          </p>
          <Link href="/rfqs" className="mt-4 inline-block">
            <Button size="sm" variant="outline">Return to RFQ List</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!rfq || !activeOrg) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <h2 className="text-lg font-bold">
          {!activeOrg ? "No Active Organization" : "RFQ Not Found"}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {!activeOrg
            ? "Please select or join an organization to view RFQ details."
            : error || "The requested procurement inquiry does not exist or has been deleted."}
        </p>
        <Link href="/rfqs" className="mt-4 inline-block">
          <Button size="sm">Back to RFQs</Button>
        </Link>
      </div>
    );
  }

  const isAwardable =
    rfq.status === "UNDER_REVIEW" ||
    rfq.status === "RESPONSES_RECEIVED" ||
    rfq.status === "NEGOTIATION";

  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-8 space-y-6">
      {/* Top back navigation */}
      <div className="flex items-center justify-between">
        <Link
          href="/rfqs"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          Back to RFQs Dashboard
        </Link>

        <span className="text-xs text-muted-foreground font-mono">
          Organization: {activeOrg?.display_name || activeOrg?.legal_name}
        </span>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm flex items-start gap-3">
          <AlertTriangle className="size-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Action Error</p>
            <p className="text-xs mt-0.5 opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* Workspace Header Card */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <span className="font-mono text-sm font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded">
                {rfq.rfq_number}
              </span>
              <RFQStatusBadge status={rfq.status} />
              <span className="text-xs text-muted-foreground font-mono">
                Currency: <strong>{rfq.currency}</strong>
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
              {rfq.title}
            </h1>
            {rfq.description && (
              <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
                {rfq.description}
              </p>
            )}
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2.5">
            {rfq.status === "DRAFT" && canMutate && (
              <Button
                onClick={handleOpenRFQ}
                disabled={isPublishing}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
              >
                {isPublishing ? (
                  <>
                    <Loader2 className="size-4 animate-spin mr-1.5" />
                    Opening RFQ...
                  </>
                ) : (
                  <>
                    <Share2 className="size-4 mr-1.5" />
                    Open RFQ for Sourcing
                  </>
                )}
              </Button>
            )}

            {(rfq.status === "OPEN" ||
              rfq.status === "INVITATIONS_SENT" ||
              rfq.status === "RESPONSES_RECEIVED" ||
              rfq.status === "UNDER_REVIEW") &&
              canMutate && (
                <Button
                  onClick={() => setIsInviteModalOpen(true)}
                  variant="outline"
                  className="font-semibold"
                >
                  <UserPlus className="size-4 mr-1.5 text-blue-500" />
                  Invite Suppliers
                </Button>
              )}

            {quotations.length > 0 && (
              <Button
                variant={activeTab === "comparison" ? "default" : "outline"}
                onClick={() => setActiveTab("comparison")}
                className="font-semibold"
              >
                <Layers className="size-4 mr-1.5 text-purple-500" />
                Side-by-Side Comparison ({quotations.length})
              </Button>
            )}
          </div>
        </div>

        {/* Commercial Metadata Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-border text-xs">
          <div>
            <span className="text-muted-foreground block">Destination</span>
            <span className="font-semibold text-foreground flex items-center gap-1 mt-0.5">
              <Globe2 className="size-3 text-muted-foreground" />
              {rfq.destination_country}
              {rfq.destination_port ? ` (${rfq.destination_port})` : ""}
            </span>
          </div>

          <div>
            <span className="text-muted-foreground block">Preferred Incoterm</span>
            <span className="font-semibold text-foreground font-mono mt-0.5 block">
              {rfq.preferred_incoterm || "Any / Standard"}
            </span>
          </div>

          <div>
            <span className="text-muted-foreground block">Delivery Deadline</span>
            <span className="font-semibold text-foreground mt-0.5 block">
              {rfq.required_delivery_date || "Open / Negotiable"}
            </span>
          </div>

          <div>
            <span className="text-muted-foreground block">Payment Terms</span>
            <span className="font-semibold text-foreground mt-0.5 block">
              {rfq.preferred_payment_terms || "Standard Commercial Terms"}
            </span>
          </div>
        </div>

        {/* State Machine Pipeline */}
        <div className="pt-2 border-t border-border">
          <RFQWorkflowPipeline status={rfq.status} />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-border flex items-center gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("requirements")}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "requirements"
              ? "border-blue-600 text-blue-600 dark:text-blue-400 font-bold"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Package className="size-4" />
          Requirements &amp; Items ({rfq.items.length})
        </button>

        <button
          onClick={() => setActiveTab("invitations")}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "invitations"
              ? "border-blue-600 text-blue-600 dark:text-blue-400 font-bold"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Send className="size-4" />
          Supplier Invitations ({rfq.invitations.length})
        </button>

        <button
          onClick={() => setActiveTab("quotations")}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "quotations"
              ? "border-blue-600 text-blue-600 dark:text-blue-400 font-bold"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <DollarSign className="size-4" />
          Quotations Received ({quotations.length})
        </button>

        <button
          onClick={() => setActiveTab("comparison")}
          className={`pb-3 border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "comparison"
              ? "border-blue-600 text-blue-600 dark:text-blue-400 font-bold"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Layers className="size-4" />
          Comparison Matrix
        </button>
      </div>

      {/* Tab 1: Requirements & Line Items */}
      {activeTab === "requirements" && (
        <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
          <div className="p-4 bg-muted/30 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-foreground text-sm flex items-center gap-2">
              <Package className="size-4 text-blue-500" />
              Procurement Specifications &amp; Line Items
            </h3>
            <span className="text-xs text-muted-foreground font-mono">
              Total {rfq.items.length} items requested
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/20 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  <th className="p-3.5 pl-6">#</th>
                  <th className="p-3.5">Product Name &amp; Description</th>
                  <th className="p-3.5">Quantity &amp; Unit</th>
                  <th className="p-3.5">Target Unit Price</th>
                  <th className="p-3.5">Technical Specifications</th>
                  <th className="p-3.5 pr-6">Packaging Requirements</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rfq.items.map((item, idx) => (
                  <tr key={item.id} className="hover:bg-muted/10">
                    <td className="p-3.5 pl-6 font-mono text-muted-foreground">
                      {item.item_index || idx + 1}
                    </td>
                    <td className="p-3.5">
                      <div className="flex flex-col">
                        <span className="font-semibold text-foreground">
                          {item.product_name_snapshot}
                        </span>
                        {item.description && (
                          <span className="text-xs text-muted-foreground mt-0.5">
                            {item.description}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="p-3.5 font-mono font-medium text-foreground">
                      {Number(item.quantity).toLocaleString()} {item.unit}
                    </td>
                    <td className="p-3.5 font-mono text-foreground">
                      {item.target_unit_price ? (
                        <span>
                          {rfq.currency}{" "}
                          {Number(item.target_unit_price).toFixed(4)}
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-xs italic">
                          Open to bid
                        </span>
                      )}
                    </td>
                    <td className="p-3.5 text-xs text-muted-foreground">
                      {item.specifications || "—"}
                    </td>
                    <td className="p-3.5 pr-6 text-xs text-muted-foreground">
                      {item.packaging_requirements || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Supplier Invitations */}
      {activeTab === "invitations" && (
        <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
          <div className="p-4 bg-muted/30 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-foreground text-sm flex items-center gap-2">
              <Send className="size-4 text-blue-500" />
              Invited Suppliers
            </h3>
            {canMutate && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsInviteModalOpen(true)}
              >
                <UserPlus className="size-3.5 mr-1" />
                Invite Supplier
              </Button>
            )}
          </div>

          {rfq.invitations.length === 0 ? (
            <div className="py-16 text-center">
              <Send className="size-10 text-muted-foreground mx-auto mb-2 opacity-40" />
              <h4 className="font-bold text-foreground text-sm">
                No Suppliers Invited Yet
              </h4>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1 mb-4">
                Send invitations to trade partners to start receiving competitive commercial quotes.
              </p>
              {canMutate && (
                <Button
                  size="sm"
                  onClick={() => setIsInviteModalOpen(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <UserPlus className="size-3.5 mr-1" />
                  Invite Suppliers
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    <th className="p-3.5 pl-6">Supplier Name</th>
                    <th className="p-3.5">Email Address</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Invited At</th>
                    <th className="p-3.5">Response Deadline</th>
                    <th className="p-3.5 pr-6">Responded At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rfq.invitations.map((inv) => (
                    <tr key={inv.id} className="hover:bg-muted/10">
                      <td className="p-3.5 pl-6 font-semibold text-foreground">
                        {inv.supplier_name}
                      </td>
                      <td className="p-3.5 font-mono text-xs text-muted-foreground">
                        {inv.supplier_email}
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                            inv.status === "RESPONDED"
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300"
                              : inv.status === "VIEWED"
                              ? "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/60 dark:text-blue-300"
                              : inv.status === "DECLINED"
                              ? "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/60 dark:text-rose-300"
                              : "bg-neutral-100 text-neutral-700 border-neutral-200 dark:bg-neutral-800 dark:text-neutral-300"
                          }`}
                        >
                          {inv.status}
                        </span>
                      </td>
                      <td className="p-3.5 text-xs text-muted-foreground font-mono">
                        {new Date(inv.invited_at).toLocaleDateString()}
                      </td>
                      <td className="p-3.5 text-xs text-muted-foreground">
                        {inv.response_deadline
                          ? new Date(inv.response_deadline).toLocaleDateString()
                          : "No deadline"}
                      </td>
                      <td className="p-3.5 pr-6 text-xs text-muted-foreground font-mono">
                        {inv.responded_at
                          ? new Date(inv.responded_at).toLocaleString()
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Quotations Received */}
      {activeTab === "quotations" && (
        <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
          <div className="p-4 bg-muted/30 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-foreground text-sm flex items-center gap-2">
              <DollarSign className="size-4 text-emerald-500" />
              Submitted Supplier Quotations
            </h3>
            <span className="text-xs text-muted-foreground font-mono">
              Strictly confidential to buyer organization
            </span>
          </div>

          {quotations.length === 0 ? (
            <div className="py-16 text-center">
              <FileSpreadsheet className="size-10 text-muted-foreground mx-auto mb-2 opacity-40" />
              <h4 className="font-bold text-foreground text-sm">
                No Formal Quotations Submitted Yet
              </h4>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1">
                When invited suppliers submit priced quotes, they will appear here with deterministic landed cost totals.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    <th className="p-3.5 pl-6">Quotation Ref</th>
                    <th className="p-3.5">Supplier Organization</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5 font-mono">Subtotal</th>
                    <th className="p-3.5 font-mono">Total Landed Cost</th>
                    <th className="p-3.5">Incoterm / Terms</th>
                    <th className="p-3.5">Lead Time</th>
                    <th className="p-3.5 pr-6 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {quotations.map((q) => {
                    const isAccepted = q.status === "ACCEPTED";
                    return (
                      <tr
                        key={q.id}
                        className={`hover:bg-muted/10 transition-colors ${
                          isAccepted ? "bg-emerald-500/5" : ""
                        }`}
                      >
                        <td className="p-3.5 pl-6 font-mono font-semibold text-foreground">
                          <div className="flex flex-col">
                            <span>{q.quotation_number}</span>
                            <span className="text-[10px] text-muted-foreground">
                              Version {q.version}
                            </span>
                          </div>
                        </td>

                        <td className="p-3.5 font-medium text-foreground">
                          {q.supplier_organization_name || "Supplier Partner"}
                        </td>

                        <td className="p-3.5">
                          <QuotationStatusBadge
                            status={q.status}
                            version={q.version}
                          />
                        </td>

                        <td className="p-3.5 font-mono text-muted-foreground">
                          {q.currency}{" "}
                          {Number(q.subtotal_amount).toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                          })}
                        </td>

                        <td className="p-3.5 font-mono font-bold text-emerald-600 dark:text-emerald-400">
                          {q.currency}{" "}
                          {Number(q.total_landed_cost).toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                          })}
                        </td>

                        <td className="p-3.5 text-xs text-foreground">
                          {q.incoterm} • {q.payment_terms}
                        </td>

                        <td className="p-3.5 text-xs text-foreground">
                          {q.lead_time_days} days
                        </td>

                        <td className="p-3.5 pr-6 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {isAwardable && canMutate && !isAccepted && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-xs"
                                onClick={() => setAwardQuoteTarget(q)}
                              >
                                <Award className="size-3.5 mr-1" />
                                Award
                              </Button>
                            )}
                            {isAccepted && (
                              <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                                <CheckCircle2 className="size-3.5" />
                                Winning Contract
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Side-by-Side Quote Comparison */}
      {activeTab === "comparison" && (
        <div>
          {comparison ? (
            <QuoteComparisonView
              comparison={comparison}
              onAward={(q) => setAwardQuoteTarget(q)}
              canAward={isAwardable && canMutate}
            />
          ) : (
            <div className="rounded-2xl border border-dashed border-border p-12 text-center bg-card">
              <Layers className="size-10 text-muted-foreground mx-auto mb-3 opacity-50" />
              <h3 className="font-bold text-foreground text-base">
                Comparison Not Available Yet
              </h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto mt-1">
                At least one non-draft quote must be submitted by an invited supplier to generate side-by-side matrices.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Award Modal */}
      <AwardModal
        quotation={awardQuoteTarget}
        isOpen={Boolean(awardQuoteTarget)}
        onClose={() => setAwardQuoteTarget(null)}
        onConfirmAward={handleAwardQuotation}
      />

      {/* Invite Supplier Modal */}
      <InviteSupplierModal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        onSendInvitations={handleSendInvitations}
      />
    </div>
  );
}
