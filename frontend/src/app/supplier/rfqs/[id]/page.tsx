"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useOrganization } from "@/lib/organization-context";
import {
  SupplierSanitizedRFQ,
  Quotation,
  fetchWithAuth,
  ApiError,
} from "@/lib/api";
import {
  ArrowLeft,
  Globe2,
  Package,
  ShieldAlert,
  AlertCircle,
  Loader2,
  DollarSign,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { RFQStatusBadge } from "@/components/rfq/rfq-status-badge";

export default function SupplierRFQDetailPage() {
  const params = useParams();
  const router = useRouter();
  const rfqId = params.id as string;

  const { isLoading: authLoading } = useUser();
  const { activeOrg, isLoading: orgLoading } = useOrganization();

  const [rfq, setRfq] = useState<SupplierSanitizedRFQ | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPermissionDenied, setIsPermissionDenied] = useState(false);
  const [isCreatingDraft, setIsCreatingDraft] = useState(false);

  useEffect(() => {
    let active = true;
    async function fetchInitial() {
      if (!activeOrg || !rfqId) {
        if (active) setIsLoading(false);
        return;
      }

      try {
        const sanitizedRfq = await fetchWithAuth<SupplierSanitizedRFQ>(
          `/v1/organizations/${activeOrg.id}/supplier/rfqs/${rfqId}`
        );
        if (active) {
          setRfq(sanitizedRfq);
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

  // Handle Create Initial Draft Quote
  async function handleCreateQuoteDraft() {
    if (!activeOrg || !rfq) return;
    setIsCreatingDraft(true);
    setError(null);

    try {
      const payload = {
        incoterm: rfq.preferred_incoterm || "FOB",
        payment_terms: rfq.preferred_payment_terms || "Net 30",
        currency: rfq.currency || "USD",
        items: rfq.items.map((itm) => ({
          rfq_item_id: itm.id,
          unit_price: itm.target_unit_price || "10.0000",
          quantity: itm.quantity,
        })),
      };

      const createdQuote = await fetchWithAuth<Quotation>(
        `/v1/organizations/${activeOrg.id}/supplier/rfqs/${rfq.id}/quotations`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );

      router.push(`/supplier/quotations/${createdQuote.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setIsCreatingDraft(false);
    }
  }

  if (authLoading || orgLoading || isLoading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <Loader2 className="size-8 text-blue-600 animate-spin mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">Loading RFQ Specifications...</p>
      </div>
    );
  }

  if (isPermissionDenied) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16">
        <div className="max-w-lg mx-auto p-8 rounded-2xl border border-destructive/20 bg-destructive/5 text-destructive text-center">
          <ShieldAlert className="size-10 mx-auto mb-3" />
          <h2 className="text-lg font-bold">Invitation Required (403)</h2>
          <p className="text-sm mt-1">
            Your supplier organization has not been invited to participate in this RFQ inquiry.
          </p>
          <Link href="/supplier/invitations" className="mt-4 inline-block">
            <Button size="sm" variant="outline">Back to Invitations</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!rfq) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <h2 className="text-lg font-bold">RFQ Not Found</h2>
        <p className="text-sm text-muted-foreground mt-1">
          {error || "The requested procurement inquiry is unavailable."}
        </p>
        <Link href="/supplier/invitations" className="mt-4 inline-block">
          <Button size="sm">Back to Invitations</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-8 space-y-6">
      {/* Top back bar */}
      <div className="flex items-center justify-between">
        <Link
          href="/supplier/invitations"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          Back to Supplier Invitations
        </Link>

        <span className="text-xs text-muted-foreground font-mono">
          Quoting as: {activeOrg?.display_name || activeOrg?.legal_name}
        </span>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm flex items-start gap-3">
          <AlertCircle className="size-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Error</p>
            <p className="text-xs mt-0.5 opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* Header Card */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <span className="font-mono text-sm font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded">
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
            <p className="text-sm text-muted-foreground mt-1">
              Buyer: <strong>{rfq.buyer_organization_name || "Enterprise Buyer"}</strong>
            </p>
          </div>

          <Button
            onClick={handleCreateQuoteDraft}
            disabled={isCreatingDraft}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-sm"
          >
            {isCreatingDraft ? (
              <>
                <Loader2 className="size-4 animate-spin mr-1.5" />
                Preparing Quotation...
              </>
            ) : (
              <>
                <DollarSign className="size-4 mr-1.5" />
                Prepare &amp; Submit Quotation
              </>
            )}
          </Button>
        </div>

        {/* Commercial Parameters */}
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
      </div>

      {/* Line Items Table */}
      <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="p-4 bg-muted/30 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-foreground text-sm flex items-center gap-2">
            <Package className="size-4 text-emerald-500" />
            Requested Line Items ({rfq.items.length})
          </h3>
          <span className="text-xs text-muted-foreground">
            Price all line items accurately in {rfq.currency}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-border bg-muted/20 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <th className="p-3.5 pl-6">#</th>
                <th className="p-3.5">Product Name &amp; Description</th>
                <th className="p-3.5">Requested Quantity</th>
                <th className="p-3.5">Specifications</th>
                <th className="p-3.5">Quality Requirements</th>
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
                  <td className="p-3.5 font-mono font-bold text-foreground">
                    {Number(item.quantity).toLocaleString()} {item.unit}
                  </td>
                  <td className="p-3.5 text-xs text-muted-foreground">
                    {item.specifications || "—"}
                  </td>
                  <td className="p-3.5 text-xs text-muted-foreground">
                    {item.quality_requirements || "—"}
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
    </div>
  );
}
