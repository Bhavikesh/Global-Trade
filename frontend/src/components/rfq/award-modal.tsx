"use client";

import React, { useState } from "react";
import { Quotation } from "@/lib/api";
import { Award, AlertTriangle, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AwardModalProps {
  quotation: Quotation | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirmAward: (quotationId: string) => Promise<void>;
}

export function AwardModal({
  quotation,
  isOpen,
  onClose,
  onConfirmAward,
}: AwardModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !quotation) return null;

  async function handleAward() {
    if (!quotation) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await onConfirmAward(quotation.id);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-card border border-border w-full max-w-lg rounded-2xl shadow-2xl p-6 overflow-hidden relative">
        <button
          onClick={onClose}
          disabled={isSubmitting}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground p-1 rounded-lg"
          aria-label="Close"
        >
          <X className="size-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="size-10 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
            <Award className="size-6" />
          </div>
          <div>
            <h3 className="font-bold text-lg text-foreground">
              Confirm Quotation Award
            </h3>
            <p className="text-xs text-muted-foreground">
              Formally award this RFQ to the selected supplier offer
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm flex items-start gap-2">
            <AlertTriangle className="size-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="rounded-xl border border-border bg-muted/30 p-4 space-y-3 mb-5">
          <div className="flex justify-between items-center text-sm">
            <span className="text-muted-foreground">Winning Supplier:</span>
            <span className="font-bold text-foreground">
              {quotation.supplier_organization_name || "Supplier"}
            </span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-muted-foreground">Quotation Reference:</span>
            <span className="font-mono text-xs font-semibold text-foreground">
              {quotation.quotation_number} (V{quotation.version})
            </span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-muted-foreground">Incoterm / Terms:</span>
            <span className="font-medium text-foreground">
              {quotation.incoterm} • {quotation.payment_terms}
            </span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-muted-foreground">Lead Time:</span>
            <span className="font-medium text-foreground">
              {quotation.lead_time_days} days
            </span>
          </div>
          <div className="border-t border-border pt-2 flex justify-between items-center text-base font-bold">
            <span className="text-foreground">Total Landed Cost:</span>
            <span className="font-mono text-emerald-600 dark:text-emerald-400">
              {quotation.currency}{" "}
              {Number(quotation.total_landed_cost).toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-amber-300 dark:border-amber-800/60 bg-amber-500/10 p-3.5 mb-5 flex items-start gap-2.5 text-xs text-amber-800 dark:text-amber-300">
          <AlertTriangle className="size-4 shrink-0 mt-0.5 text-amber-600" />
          <div>
            <p className="font-semibold">Irreversible Trade Commitment</p>
            <p className="mt-0.5 opacity-90">
              Upon awarding, this quotation status becomes <strong>ACCEPTED</strong>,
              all competing active quotations will be automatically transitioned
              to <strong>REJECTED</strong>, and the RFQ will enter <strong>AWARDED</strong> state.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            variant="default"
            onClick={handleAward}
            disabled={isSubmitting}
            className="bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="size-4 animate-spin mr-1.5" />
                Processing Award...
              </>
            ) : (
              <>
                <Award className="size-4 mr-1.5" />
                Confirm &amp; Award Contract
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
