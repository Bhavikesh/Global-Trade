"use client";

import React from "react";
import {
  QuoteComparison,
  Quotation,
} from "@/lib/api";
import {
  CheckCircle2,
  AlertTriangle,
  Award,
  Zap,
  TrendingDown,
  Clock,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { QuotationStatusBadge } from "./quotation-status-badge";

interface QuoteComparisonProps {
  comparison: QuoteComparison;
  onAward?: (quotation: Quotation) => void;
  canAward?: boolean;
}

export function QuoteComparisonView({
  comparison,
  onAward,
  canAward = false,
}: QuoteComparisonProps) {
  const {
    quotations,
    items_comparison,
    currency_consistent,
    lowest_subtotal_quotation_id,
    lowest_landed_cost_quotation_id,
    fastest_delivery_quotation_id,
  } = comparison;

  if (!quotations || quotations.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-12 text-center bg-card">
        <Layers className="size-10 text-muted-foreground mx-auto mb-3 opacity-60" />
        <h3 className="font-semibold text-foreground text-base">
          No Quotations Available for Comparison
        </h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mt-1">
          When invited suppliers submit formal quotes, a deterministic
          side-by-side landed cost matrix will appear here automatically.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Mixed Currencies Warning */}
      {!currency_consistent && (
        <div className="rounded-xl border border-amber-300 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/40 p-4 text-amber-800 dark:text-amber-300 flex items-start gap-3">
          <AlertTriangle className="size-5 shrink-0 text-amber-600 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold">Mixed Currencies Detected</p>
            <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
              Quotations have been submitted in different currencies. Values
              are displayed in their original submitted currency and are NOT
              directly normalized, as GlobalTrade.ai avoids synthetic FX
              approximations.
            </p>
          </div>
        </div>
      )}

      {/* Comparison Highlights Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="rounded-xl border border-emerald-200 dark:border-emerald-800/60 bg-emerald-500/5 p-4 flex items-center gap-3">
          <div className="size-9 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
            <TrendingDown className="size-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
              Lowest Landed Cost
            </span>
            <p className="text-sm font-bold text-foreground">
              {lowest_landed_cost_quotation_id
                ? quotations.find((q) => q.id === lowest_landed_cost_quotation_id)
                    ?.supplier_organization_name || "Best Landed Offer"
                : "N/A"}
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-blue-200 dark:border-blue-800/60 bg-blue-500/5 p-4 flex items-center gap-3">
          <div className="size-9 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
            <Zap className="size-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
              Lowest Subtotal
            </span>
            <p className="text-sm font-bold text-foreground">
              {lowest_subtotal_quotation_id
                ? quotations.find((q) => q.id === lowest_subtotal_quotation_id)
                    ?.supplier_organization_name || "Lowest Subtotal"
                : "N/A"}
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-purple-200 dark:border-purple-800/60 bg-purple-500/5 p-4 flex items-center gap-3">
          <div className="size-9 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
            <Clock className="size-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
              Fastest Lead Time
            </span>
            <p className="text-sm font-bold text-foreground">
              {fastest_delivery_quotation_id
                ? `${quotations.find((q) => q.id === fastest_delivery_quotation_id)?.lead_time_days ?? 0} days`
                : "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison Matrix Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-3.5 font-semibold text-foreground min-w-[220px] sticky left-0 bg-muted/90 backdrop-blur z-20 border-r border-border">
                  Commercial Parameters
                </th>
                {quotations.map((quote) => {
                  const isLowestLanded =
                    quote.id === lowest_landed_cost_quotation_id;
                  return (
                    <th
                      key={quote.id}
                      className={`p-3.5 min-w-[240px] text-left align-top transition-colors ${
                        isLowestLanded
                          ? "bg-emerald-500/10 border-x-2 border-emerald-500/50"
                          : "border-r border-border"
                      }`}
                    >
                      <div className="flex flex-col gap-1.5">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-foreground text-sm truncate">
                            {quote.supplier_organization_name || "Supplier"}
                          </span>
                          <QuotationStatusBadge
                            status={quote.status}
                            version={quote.version}
                          />
                        </div>

                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span className="font-mono">{quote.quotation_number}</span>
                          <span className="font-semibold text-foreground">
                            {quote.currency}
                          </span>
                        </div>

                        {isLowestLanded && (
                          <div className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded w-fit">
                            <CheckCircle2 className="size-3" />
                            Best Landed Value
                          </div>
                        )}

                        {canAward && onAward && quote.status !== "ACCEPTED" && (
                          <div className="mt-2">
                            <Button
                              size="sm"
                              className="w-full text-xs font-semibold"
                              variant={isLowestLanded ? "default" : "outline"}
                              onClick={() => onAward(quote)}
                            >
                              <Award className="size-3.5 mr-1" />
                              Award Quotation
                            </Button>
                          </div>
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>

            <tbody className="divide-y divide-border">
              {/* Section Header: Line Items */}
              <tr className="bg-muted/20 font-semibold text-xs tracking-wider text-muted-foreground uppercase">
                <td
                  colSpan={quotations.length + 1}
                  className="p-2.5 px-3.5 bg-muted/30 sticky left-0"
                >
                  Line Items (Unit Pricing)
                </td>
              </tr>

              {items_comparison.map((itm) => (
                <tr key={itm.rfq_item_id} className="hover:bg-muted/20">
                  <td className="p-3.5 font-medium text-foreground sticky left-0 bg-card border-r border-border z-10">
                    <div className="flex flex-col">
                      <span className="font-semibold">
                        {itm.product_name_snapshot}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Qty: {Number(itm.quantity).toLocaleString()} {itm.unit}
                      </span>
                    </div>
                  </td>

                  {quotations.map((quote) => {
                    const quoteLine = itm.quotes_by_id[quote.id];
                    const isLowestUnit =
                      quote.id === itm.lowest_unit_price_quotation_id;
                    const isLowestLanded =
                      quote.id === lowest_landed_cost_quotation_id;

                    return (
                      <td
                        key={quote.id}
                        className={`p-3.5 ${
                          isLowestLanded
                            ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                            : "border-r border-border"
                        }`}
                      >
                        {quoteLine ? (
                          <div className="flex flex-col">
                            <div className="flex items-center gap-1.5">
                              <span
                                className={`font-mono font-medium ${
                                  isLowestUnit
                                    ? "text-emerald-600 dark:text-emerald-400 font-bold"
                                    : "text-foreground"
                                }`}
                              >
                                {quote.currency}{" "}
                                {Number(quoteLine.unit_price).toFixed(4)}
                              </span>
                              {isLowestUnit && (
                                <span className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.2 rounded font-semibold">
                                  Lowest
                                </span>
                              )}
                            </div>
                            <span className="text-xs text-muted-foreground font-mono">
                              Total: {quote.currency}{" "}
                              {Number(quoteLine.line_total).toLocaleString(
                                undefined,
                                { minimumFractionDigits: 2 }
                              )}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-xs italic">
                            Not quoted
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}

              {/* Section Header: Landed Cost Breakdown */}
              <tr className="bg-muted/20 font-semibold text-xs tracking-wider text-muted-foreground uppercase">
                <td
                  colSpan={quotations.length + 1}
                  className="p-2.5 px-3.5 bg-muted/30 sticky left-0"
                >
                  Commercial Cost Breakdown
                </td>
              </tr>

              {/* Subtotal */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 font-medium text-foreground sticky left-0 bg-card border-r border-border z-10">
                  Subtotal
                </td>
                {quotations.map((q) => {
                  const isLowestSub = q.id === lowest_subtotal_quotation_id;
                  const isLowestLanded = q.id === lowest_landed_cost_quotation_id;
                  return (
                    <td
                      key={q.id}
                      className={`p-3 font-mono ${
                        isLowestLanded
                          ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                          : "border-r border-border"
                      }`}
                    >
                      <span className={isLowestSub ? "font-bold text-blue-600 dark:text-blue-400" : ""}>
                        {q.currency} {Number(q.subtotal_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                  );
                })}
              </tr>

              {/* Shipping */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Shipping Freight
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 font-mono text-muted-foreground ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.shipping_cost
                      ? `${q.currency} ${Number(q.shipping_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                      : "—"}
                  </td>
                ))}
              </tr>

              {/* Insurance */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Cargo Insurance
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 font-mono text-muted-foreground ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.insurance_cost
                      ? `${q.currency} ${Number(q.insurance_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                      : "—"}
                  </td>
                ))}
              </tr>

              {/* Customs Duty */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Estimated Duty
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 font-mono text-muted-foreground ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.duty_amount
                      ? `${q.currency} ${Number(q.duty_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                      : "—"}
                  </td>
                ))}
              </tr>

              {/* Taxes */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Taxes (VAT / GST)
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 font-mono text-muted-foreground ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.tax_amount
                      ? `${q.currency} ${Number(q.tax_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                      : "—"}
                  </td>
                ))}
              </tr>

              {/* Other Charges */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Other Surcharges
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 font-mono text-muted-foreground ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.other_charges
                      ? `${q.currency} ${Number(q.other_charges).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                      : "—"}
                  </td>
                ))}
              </tr>

              {/* TOTAL LANDED COST ROW */}
              <tr className="bg-muted/40 font-bold border-t-2 border-b-2 border-border">
                <td className="p-4 text-foreground sticky left-0 bg-muted/90 backdrop-blur border-r border-border z-10 text-base">
                  Total Landed Cost
                </td>
                {quotations.map((q) => {
                  const isLowestLanded = q.id === lowest_landed_cost_quotation_id;
                  return (
                    <td
                      key={q.id}
                      className={`p-4 font-mono text-base ${
                        isLowestLanded
                          ? "bg-emerald-500/15 border-x-2 border-emerald-500 text-emerald-600 dark:text-emerald-400"
                          : "border-r border-border text-foreground"
                      }`}
                    >
                      <div className="flex flex-col">
                        <span>
                          {q.currency} {Number(q.total_landed_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                        {isLowestLanded && (
                          <span className="text-[11px] font-sans font-semibold text-emerald-600 dark:text-emerald-400">
                            ★ Lowest Landed
                          </span>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>

              {/* Section Header: Operational & Commercial Terms */}
              <tr className="bg-muted/20 font-semibold text-xs tracking-wider text-muted-foreground uppercase">
                <td
                  colSpan={quotations.length + 1}
                  className="p-2.5 px-3.5 bg-muted/30 sticky left-0"
                >
                  Commercial &amp; Operational Terms
                </td>
              </tr>

              {/* Incoterm */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Incoterm
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 font-semibold text-foreground ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.incoterm}
                  </td>
                ))}
              </tr>

              {/* Lead Time */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Lead Time
                </td>
                {quotations.map((q) => {
                  const isFastest = q.id === fastest_delivery_quotation_id;
                  return (
                    <td
                      key={q.id}
                      className={`p-3 ${
                        q.id === lowest_landed_cost_quotation_id
                          ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                          : "border-r border-border"
                      }`}
                    >
                      <div className="flex items-center gap-1.5">
                        <span className={isFastest ? "font-bold text-purple-600 dark:text-purple-400" : "text-foreground"}>
                          {q.lead_time_days} days
                        </span>
                        {isFastest && (
                          <span className="text-[10px] bg-purple-500/10 text-purple-600 dark:text-purple-400 px-1.5 py-0.2 rounded font-semibold">
                            Fastest
                          </span>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>

              {/* Payment Terms */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Payment Terms
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 text-foreground ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.payment_terms}
                  </td>
                ))}
              </tr>

              {/* Validity */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Validity Deadline
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 text-foreground text-xs ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.valid_until || "Not specified"}
                  </td>
                ))}
              </tr>

              {/* Supplier Notes */}
              <tr className="hover:bg-muted/20">
                <td className="p-3 text-muted-foreground sticky left-0 bg-card border-r border-border z-10">
                  Supplier Notes
                </td>
                {quotations.map((q) => (
                  <td
                    key={q.id}
                    className={`p-3 text-muted-foreground text-xs italic ${
                      q.id === lowest_landed_cost_quotation_id
                        ? "bg-emerald-500/5 border-x-2 border-emerald-500/50"
                        : "border-r border-border"
                    }`}
                  >
                    {q.supplier_notes || "—"}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
