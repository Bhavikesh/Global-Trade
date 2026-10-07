"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useOrganization } from "@/lib/organization-context";
import {
  Quotation,
  QuotationUpdate,
  QuotationCreate,
  fetchWithAuth,
  ApiError,
} from "@/lib/api";
import {
  DollarSign,
  ArrowLeft,
  Save,
  Send,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  FileText,
  Lock,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { QuotationStatusBadge } from "@/components/rfq/quotation-status-badge";
import { NegotiationTimeline } from "@/components/rfq/negotiation-timeline";

const INCOTERMS = [
  "FOB",
  "CIF",
  "CFR",
  "EXW",
  "FCA",
  "CPT",
  "CIP",
  "DAP",
  "DPU",
  "DDP",
];

const CURRENCIES = ["USD", "EUR", "GBP", "CNY", "INR", "JPY", "SGD", "AED"];

export default function SupplierQuotationPage() {
  const params = useParams();
  const router = useRouter();
  const quotationId = params.id as string;

  const { isLoading: authLoading } = useUser();
  const { activeOrg, isLoading: orgLoading } = useOrganization();

  const [quote, setQuote] = useState<Quotation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isPermissionDenied, setIsPermissionDenied] = useState(false);

  // Form states for DRAFT editing
  const [incoterm, setIncoterm] = useState("FOB");
  const [paymentTerms, setPaymentTerms] = useState("Net 30");
  const [currency, setCurrency] = useState("USD");
  const [validUntil, setValidUntil] = useState("");
  const [leadTimeDays, setLeadTimeDays] = useState<number>(14);
  const [shippingCost, setShippingCost] = useState("");
  const [insuranceCost, setInsuranceCost] = useState("");
  const [dutyAmount, setDutyAmount] = useState("");
  const [taxAmount, setTaxAmount] = useState("");
  const [otherCharges, setOtherCharges] = useState("");
  const [supplierNotes, setSupplierNotes] = useState("");

  // Items pricing state
  const [itemsPricing, setItemsPricing] = useState<
    Record<
      string,
      {
        unit_price: string;
        moq?: string;
        lead_time_days?: number;
        notes?: string;
      }
    >
  >({});

  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRevising, setIsRevising] = useState(false);

  useEffect(() => {
    let active = true;
    async function fetchInitial() {
      if (!activeOrg || !quotationId) {
        if (active) setIsLoading(false);
        return;
      }

      try {
        const data = await fetchWithAuth<Quotation>(
          `/v1/organizations/${activeOrg.id}/supplier/quotations/${quotationId}`
        );
        if (active) {
          setQuote(data);
          setIncoterm(data.incoterm || "FOB");
          setPaymentTerms(data.payment_terms || "Net 30");
          setCurrency(data.currency || "USD");
          setValidUntil(data.valid_until || "");
          setLeadTimeDays(data.lead_time_days ?? 14);
          setShippingCost(data.shipping_cost || "");
          setInsuranceCost(data.insurance_cost || "");
          setDutyAmount(data.duty_amount || "");
          setTaxAmount(data.tax_amount || "");
          setOtherCharges(data.other_charges || "");
          setSupplierNotes(data.supplier_notes || "");

          const pMap: Record<
            string,
            { unit_price: string; moq?: string; lead_time_days?: number; notes?: string }
          > = {};
          data.items?.forEach((itm) => {
            pMap[itm.rfq_item_id] = {
              unit_price: itm.unit_price || "0.0000",
              moq: itm.moq || "",
              lead_time_days: itm.lead_time_days ?? undefined,
              notes: itm.notes || "",
            };
          });
          setItemsPricing(pMap);
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
  }, [authLoading, orgLoading, activeOrg, quotationId]);

  // Handle Save Draft
  async function handleSaveDraft() {
    if (!activeOrg || !quote || quote.status !== "DRAFT") return;
    setIsSaving(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const payload: QuotationUpdate = {
        currency,
        incoterm,
        payment_terms: paymentTerms,
        lead_time_days: Number(leadTimeDays) || 0,
        valid_until: validUntil || null,
        shipping_cost: shippingCost || null,
        insurance_cost: insuranceCost || null,
        duty_amount: dutyAmount || null,
        tax_amount: taxAmount || null,
        other_charges: otherCharges || null,
        supplier_notes: supplierNotes || null,
        items: quote.items.map((itm) => ({
          rfq_item_id: itm.rfq_item_id,
          unit_price: itemsPricing[itm.rfq_item_id]?.unit_price || itm.unit_price,
          moq: itemsPricing[itm.rfq_item_id]?.moq || null,
          lead_time_days: itemsPricing[itm.rfq_item_id]?.lead_time_days || null,
          notes: itemsPricing[itm.rfq_item_id]?.notes || null,
        })),
      };

      const updated = await fetchWithAuth<Quotation>(
        `/v1/organizations/${activeOrg.id}/supplier/quotations/${quote.id}`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        }
      );
      setQuote(updated);
      setSuccessMsg("Draft updated successfully. Authoritative totals recalculated.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setIsSaving(false);
    }
  }

  // Handle Formal Submission
  async function handleSubmitQuote() {
    if (!activeOrg || !quote || quote.status !== "DRAFT") return;
    setIsSubmitting(true);
    setError(null);
    setSuccessMsg(null);

    try {
      // First save any recent unsaved draft changes
      await handleSaveDraft();

      const submitted = await fetchWithAuth<Quotation>(
        `/v1/organizations/${activeOrg.id}/supplier/quotations/${quote.id}/submit`,
        { method: "POST" }
      );
      setQuote(submitted);
      setSuccessMsg("Quotation successfully submitted to buyer! Commercial values are now frozen.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Handle Revision (V2 from V1)
  async function handleReviseQuote() {
    if (!activeOrg || !quote) return;
    setIsRevising(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const payload: QuotationCreate = {
        currency: quote.currency,
        incoterm: quote.incoterm,
        payment_terms: quote.payment_terms,
        lead_time_days: quote.lead_time_days,
        valid_until: quote.valid_until || null,
        shipping_cost: quote.shipping_cost || null,
        insurance_cost: quote.insurance_cost || null,
        duty_amount: quote.duty_amount || null,
        tax_amount: quote.tax_amount || null,
        other_charges: quote.other_charges || null,
        supplier_notes: `Revision based on ${quote.quotation_number}`,
        items: quote.items.map((itm) => ({
          rfq_item_id: itm.rfq_item_id,
          unit_price: itm.unit_price,
          quantity: itm.quantity,
          moq: itm.moq || null,
          lead_time_days: itm.lead_time_days || null,
          notes: itm.notes || null,
        })),
      };

      const revised = await fetchWithAuth<Quotation>(
        `/v1/organizations/${activeOrg.id}/supplier/quotations/${quote.id}/revise`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );

      // Redirect to the newly created revision
      router.push(`/supplier/quotations/${revised.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setIsRevising(false);
    }
  }

  if (authLoading || orgLoading || isLoading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <Loader2 className="size-8 text-blue-600 animate-spin mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">Loading Quotation...</p>
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
            You are not authorized to view or edit another supplier&apos;s quotation.
          </p>
        </div>
      </div>
    );
  }

  if (!quote || !activeOrg) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <h2 className="text-lg font-bold">
          {!activeOrg ? "No Active Organization" : "Quotation Not Found"}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {!activeOrg
            ? "Please select or join an organization to view quotation details."
            : error || "The requested quotation record does not exist."}
        </p>
      </div>
    );
  }

  const isDraft = quote.status === "DRAFT";
  const isSubmitted =
    quote.status === "SUBMITTED" ||
    quote.status === "UNDER_REVIEW" ||
    quote.status === "ACCEPTED" ||
    quote.status === "REJECTED";
  const isSuperseded = quote.status === "SUPERSEDED";

  return (
    <div className="container mx-auto max-w-5xl px-4 sm:px-8 py-8 space-y-6">
      {/* Top back bar */}
      <div className="flex items-center justify-between">
        <Link
          href={`/supplier/rfqs/${quote.rfq_id}`}
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          Back to RFQ Requirements
        </Link>

        <span className="text-xs text-muted-foreground font-mono">
          Organization: {activeOrg?.display_name || activeOrg?.legal_name}
        </span>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm flex items-start gap-3">
          <AlertTriangle className="size-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Error</p>
            <p className="text-xs mt-0.5 opacity-90">{error}</p>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl border border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 text-sm flex items-start gap-3">
          <CheckCircle2 className="size-5 shrink-0 mt-0.5 text-emerald-600" />
          <div>
            <p className="font-semibold">Success</p>
            <p className="text-xs mt-0.5 opacity-90">{successMsg}</p>
          </div>
        </div>
      )}

      {/* Header Banner */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <span className="font-mono text-sm font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded">
                {quote.quotation_number}
              </span>
              <QuotationStatusBadge
                status={quote.status}
                version={quote.version}
              />
              <span className="text-xs text-muted-foreground font-mono">
                Currency: <strong>{quote.currency}</strong>
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
              Supplier Quotation (Revision V{quote.version})
            </h1>
            <p className="text-xs text-muted-foreground mt-1">
              Quotation ID: <span className="font-mono">{quote.id}</span>
              {quote.parent_quotation_id && (
                <span className="ml-2">
                  • Supersedes parent quote:{" "}
                  <span className="font-mono">{quote.parent_quotation_id}</span>
                </span>
              )}
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2.5">
            {isDraft && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveDraft}
                  disabled={isSaving || isSubmitting}
                >
                  {isSaving ? (
                    <Loader2 className="size-3.5 animate-spin mr-1.5" />
                  ) : (
                    <Save className="size-3.5 mr-1.5" />
                  )}
                  Save Draft
                </Button>

                <Button
                  size="sm"
                  onClick={handleSubmitQuote}
                  disabled={isSaving || isSubmitting}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
                >
                  {isSubmitting ? (
                    <Loader2 className="size-3.5 animate-spin mr-1.5" />
                  ) : (
                    <Send className="size-3.5 mr-1.5" />
                  )}
                  Submit Formal Quote
                </Button>
              </>
            )}

            {(isSubmitted && !isSuperseded) && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleReviseQuote}
                disabled={isRevising}
                className="text-xs font-semibold"
              >
                {isRevising ? (
                  <Loader2 className="size-3.5 animate-spin mr-1.5" />
                ) : (
                  <RotateCcw className="size-3.5 mr-1.5 text-blue-500" />
                )}
                Issue Revision (V{quote.version + 1})
              </Button>
            )}
          </div>
        </div>

        {/* Immutability / Superseded Status Notices */}
        {!isDraft && (
          <div
            className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 ${
              isSuperseded
                ? "border-neutral-300 bg-neutral-100 text-neutral-700 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300"
                : "border-blue-200 bg-blue-50/70 text-blue-800 dark:border-blue-900/60 dark:bg-blue-950/40 dark:text-blue-300"
            }`}
          >
            <Lock className="size-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">
                {isSuperseded
                  ? "Historical Superseded Record"
                  : "Formally Submitted Quotation — Commercial Values Immutable"}
              </p>
              <p className="mt-0.5 opacity-90">
                {isSuperseded
                  ? "This version was superseded by a subsequent revision. Its commercial values are permanently preserved for auditability."
                  : "Submitted commercial parameters and pricing are locked. To propose revised pricing or terms, click 'Issue Revision' to generate Version " +
                    (quote.version + 1) +
                    "."}
              </p>
            </div>
          </div>
        )}

        {/* Authoritative Financial Totals Card */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl border border-border bg-muted/20">
          <div>
            <span className="text-xs text-muted-foreground block">
              Items Subtotal
            </span>
            <span className="text-base font-bold font-mono text-foreground mt-0.5 block">
              {quote.currency}{" "}
              {Number(quote.subtotal_amount).toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>

          <div>
            <span className="text-xs text-muted-foreground block">
              Shipping &amp; Insurance
            </span>
            <span className="text-base font-semibold font-mono text-foreground mt-0.5 block">
              {quote.currency}{" "}
              {(
                Number(quote.shipping_cost || 0) +
                Number(quote.insurance_cost || 0)
              ).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div>
            <span className="text-xs text-muted-foreground block">
              Duty, Tax &amp; Surcharges
            </span>
            <span className="text-base font-semibold font-mono text-foreground mt-0.5 block">
              {quote.currency}{" "}
              {(
                Number(quote.duty_amount || 0) +
                Number(quote.tax_amount || 0) +
                Number(quote.other_charges || 0)
              ).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div className="border-l border-border pl-4">
            <span className="text-xs text-muted-foreground block font-semibold">
              Total Landed Cost
            </span>
            <span className="text-lg font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5 block">
              {quote.currency}{" "}
              {Number(quote.total_landed_cost).toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>
        </div>
      </div>

      {/* Commercial Terms Section */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-foreground border-b border-border pb-3 flex items-center gap-2">
          <FileText className="size-4 text-blue-500" />
          Commercial &amp; Operational Terms
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="font-medium text-foreground block mb-1">
              Incoterm *
            </label>
            <select
              disabled={!isDraft}
              value={incoterm}
              onChange={(e) => setIncoterm(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground disabled:opacity-60 font-semibold"
            >
              {INCOTERMS.map((inc) => (
                <option key={inc} value={inc}>
                  {inc}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="font-medium text-foreground block mb-1">
              Currency *
            </label>
            <select
              disabled={!isDraft}
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground disabled:opacity-60 font-mono font-bold"
            >
              {CURRENCIES.map((cur) => (
                <option key={cur} value={cur}>
                  {cur}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="font-medium text-foreground block mb-1">
              Lead Time (Days) *
            </label>
            <input
              type="number"
              min="0"
              disabled={!isDraft}
              value={leadTimeDays}
              onChange={(e) => setLeadTimeDays(Number(e.target.value))}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground disabled:opacity-60"
            />
          </div>

          <div>
            <label className="font-medium text-foreground block mb-1">
              Payment Terms *
            </label>
            <input
              type="text"
              disabled={!isDraft}
              value={paymentTerms}
              onChange={(e) => setPaymentTerms(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground disabled:opacity-60"
            />
          </div>

          <div>
            <label className="font-medium text-foreground block mb-1">
              Offer Validity Deadline
            </label>
            <input
              type="date"
              disabled={!isDraft}
              value={validUntil}
              onChange={(e) => setValidUntil(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground disabled:opacity-60"
            />
          </div>

          <div>
            <label className="font-medium text-foreground block mb-1">
              Shipping Freight Cost ({currency})
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              disabled={!isDraft}
              value={shippingCost}
              onChange={(e) => setShippingCost(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground font-mono disabled:opacity-60"
            />
          </div>

          <div>
            <label className="font-medium text-foreground block mb-1">
              Insurance Cost ({currency})
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              disabled={!isDraft}
              value={insuranceCost}
              onChange={(e) => setInsuranceCost(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground font-mono disabled:opacity-60"
            />
          </div>

          <div>
            <label className="font-medium text-foreground block mb-1">
              Estimated Customs Duty ({currency})
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              disabled={!isDraft}
              value={dutyAmount}
              onChange={(e) => setDutyAmount(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground font-mono disabled:opacity-60"
            />
          </div>

          <div>
            <label className="font-medium text-foreground block mb-1">
              Taxes / VAT ({currency})
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              disabled={!isDraft}
              value={taxAmount}
              onChange={(e) => setTaxAmount(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-2 text-foreground font-mono disabled:opacity-60"
            />
          </div>

          <div className="sm:col-span-3">
            <label className="font-medium text-foreground block mb-1">
              Supplier Notes &amp; Commercial Conditions
            </label>
            <textarea
              rows={2}
              disabled={!isDraft}
              value={supplierNotes}
              onChange={(e) => setSupplierNotes(e.target.value)}
              placeholder="Warranty terms, port of loading, shipping packaging specifications..."
              className="w-full rounded-lg border border-border bg-background p-2.5 text-foreground disabled:opacity-60"
            />
          </div>
        </div>
      </div>

      {/* Line Items Pricing Table */}
      <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="p-4 bg-muted/30 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-foreground text-sm flex items-center gap-2">
            <DollarSign className="size-4 text-emerald-500" />
            Line Items &amp; Unit Pricing
          </h3>
          <span className="text-xs text-muted-foreground font-mono">
            {quote.items.length} items to price
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-border bg-muted/20 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <th className="p-3.5 pl-6">Product Snapshot</th>
                <th className="p-3.5">Quantity</th>
                <th className="p-3.5">Unit Price ({currency})</th>
                <th className="p-3.5 font-mono">Line Total ({currency})</th>
                <th className="p-3.5">MOQ</th>
                <th className="p-3.5 pr-6">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {quote.items.map((item) => (
                <tr key={item.id} className="hover:bg-muted/10">
                  <td className="p-3.5 pl-6 font-semibold text-foreground">
                    {item.product_name_snapshot}
                  </td>

                  <td className="p-3.5 font-mono text-foreground font-medium">
                    {Number(item.quantity).toLocaleString()} {item.unit}
                  </td>

                  <td className="p-3.5">
                    {isDraft ? (
                      <input
                        type="number"
                        step="0.0001"
                        min="0"
                        required
                        value={itemsPricing[item.rfq_item_id]?.unit_price || ""}
                        onChange={(e) => {
                          const val = e.target.value;
                          setItemsPricing((prev) => ({
                            ...prev,
                            [item.rfq_item_id]: {
                              ...prev[item.rfq_item_id],
                              unit_price: val,
                            },
                          }));
                        }}
                        className="w-32 rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-mono font-bold text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                      />
                    ) : (
                      <span className="font-mono font-bold text-foreground">
                        {Number(item.unit_price).toFixed(4)}
                      </span>
                    )}
                  </td>

                  <td className="p-3.5 font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    {Number(item.line_total).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </td>

                  <td className="p-3.5">
                    {isDraft ? (
                      <input
                        type="number"
                        step="0.01"
                        placeholder="MOQ"
                        value={itemsPricing[item.rfq_item_id]?.moq || ""}
                        onChange={(e) => {
                          const val = e.target.value;
                          setItemsPricing((prev) => ({
                            ...prev,
                            [item.rfq_item_id]: {
                              ...prev[item.rfq_item_id],
                              moq: val,
                            },
                          }));
                        }}
                        className="w-24 rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-mono text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                      />
                    ) : (
                      <span className="text-xs text-muted-foreground">
                        {item.moq ? `${item.moq} ${item.unit}` : "None"}
                      </span>
                    )}
                  </td>

                  <td className="p-3.5 pr-6 text-xs text-muted-foreground">
                    {isDraft ? (
                      <input
                        type="text"
                        placeholder="Optional notes"
                        value={itemsPricing[item.rfq_item_id]?.notes || ""}
                        onChange={(e) => {
                          const val = e.target.value;
                          setItemsPricing((prev) => ({
                            ...prev,
                            [item.rfq_item_id]: {
                              ...prev[item.rfq_item_id],
                              notes: val,
                            },
                          }));
                        }}
                        className="w-40 rounded-lg border border-border bg-background px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                      />
                    ) : (
                      <span>{item.notes || "—"}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Negotiation History & Counter-Offers Thread */}
      <NegotiationTimeline
        organizationId={activeOrg.id}
        quotationId={quote.id}
        isBuyer={false}
        currency={quote.currency}
      />
    </div>
  );
}
