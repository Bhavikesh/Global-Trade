"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  NegotiationNote,
  NegotiationNoteCreate,
  fetchWithAuth,
} from "@/lib/api";
import {
  MessageSquare,
  Send,
  Loader2,
  DollarSign,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface NegotiationTimelineProps {
  organizationId: string;
  quotationId: string;
  isBuyer: boolean;
  currency?: string;
}

export function NegotiationTimeline({
  organizationId,
  quotationId,
  isBuyer,
  currency = "USD",
}: NegotiationTimelineProps) {
  const [notes, setNotes] = useState<NegotiationNote[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [message, setMessage] = useState("");
  const [proposedPrice, setProposedPrice] = useState("");
  const [proposedTerms, setProposedTerms] = useState("");
  const [noteType, setNoteType] = useState<
    "BUYER_NOTE" | "COUNTER_OFFER" | "SUPPLIER_RESPONSE"
  >(isBuyer ? "COUNTER_OFFER" : "SUPPLIER_RESPONSE");

  const loadNotes = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchWithAuth<NegotiationNote[]>(
        `/v1/organizations/${organizationId}/quotations/${quotationId}/negotiation-notes`
      );
      setNotes(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    }
  }, [organizationId, quotationId]);

  useEffect(() => {
    let active = true;
    async function fetchInitialNotes() {
      try {
        const data = await fetchWithAuth<NegotiationNote[]>(
          `/v1/organizations/${organizationId}/quotations/${quotationId}/negotiation-notes`
        );
        if (active) {
          setNotes(data);
        }
      } catch (err: unknown) {
        if (active) {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg);
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }
    fetchInitialNotes();
    return () => {
      active = false;
    };
  }, [organizationId, quotationId]);

  async function handleSendNote(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const payload: NegotiationNoteCreate = {
        note_type: noteType,
        message: message.trim(),
        proposed_target_price: proposedPrice.trim() || null,
        proposed_terms: proposedTerms.trim() || null,
      };

      await fetchWithAuth(
        `/v1/organizations/${organizationId}/quotations/${quotationId}/negotiation-notes`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );

      setMessage("");
      setProposedPrice("");
      setProposedTerms("");
      await loadNotes();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <MessageSquare className="size-4 text-blue-500" />
          <h3 className="font-semibold text-foreground text-sm">
            Commercial Negotiation &amp; Counter-Offers
          </h3>
        </div>
        <span className="text-xs text-muted-foreground font-mono">
          {notes.length} {notes.length === 1 ? "entry" : "entries"}
        </span>
      </div>

      {error && (
        <div className="p-3 rounded-lg border border-destructive/20 bg-destructive/10 text-destructive text-xs">
          {error}
        </div>
      )}

      {/* Timeline List */}
      <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
        {isLoading ? (
          <div className="py-8 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
            <Loader2 className="size-4 animate-spin" />
            Loading timeline...
          </div>
        ) : notes.length === 0 ? (
          <div className="py-8 text-center text-xs text-muted-foreground">
            No negotiation notes or counter-offers recorded yet.
          </div>
        ) : (
          notes.map((n) => {
            const isCounter = n.note_type === "COUNTER_OFFER";
            const isResponse = n.note_type === "SUPPLIER_RESPONSE";

            return (
              <div
                key={n.id}
                className="p-3.5 rounded-xl border border-border bg-muted/20 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide uppercase ${
                        isCounter
                          ? "bg-purple-500/10 text-purple-600 dark:text-purple-400"
                          : isResponse
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                          : "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                      }`}
                    >
                      {n.note_type.replace("_", " ")}
                    </span>
                    <span className="text-muted-foreground font-mono text-[11px]">
                      {new Date(n.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* Proposed target price or terms */}
                {(n.proposed_target_price || n.proposed_terms) && (
                  <div className="flex flex-wrap gap-2 pt-1 pb-1">
                    {n.proposed_target_price && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-background border border-border font-mono text-foreground font-medium">
                        <DollarSign className="size-3 text-emerald-500" />
                        Target: {currency} {Number(n.proposed_target_price).toFixed(4)}
                      </span>
                    )}
                    {n.proposed_terms && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-background border border-border text-foreground font-medium">
                        <FileText className="size-3 text-blue-500" />
                        Terms: {n.proposed_terms}
                      </span>
                    )}
                  </div>
                )}

                <p className="text-foreground leading-relaxed whitespace-pre-wrap">
                  {n.message}
                </p>
              </div>
            );
          })
        )}
      </div>

      {/* Append New Note Form */}
      <form onSubmit={handleSendNote} className="pt-3 border-t border-border space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">
              Note Type
            </label>
            <select
              value={noteType}
              onChange={(e) =>
                setNoteType(
                  e.target.value as "BUYER_NOTE" | "COUNTER_OFFER" | "SUPPLIER_RESPONSE"
                )
              }
              className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              {isBuyer ? (
                <>
                  <option value="COUNTER_OFFER">Counter-Offer</option>
                  <option value="BUYER_NOTE">Buyer Note / Inquiry</option>
                </>
              ) : (
                <>
                  <option value="SUPPLIER_RESPONSE">Supplier Response</option>
                </>
              )}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">
              Proposed Target Price (Optional)
            </label>
            <input
              type="number"
              step="0.0001"
              min="0"
              placeholder="e.g. 95.0000"
              value={proposedPrice}
              onChange={(e) => setProposedPrice(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs text-foreground font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">
              Proposed Terms (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Net 45, CIF Hamburg"
              value={proposedTerms}
              onChange={(e) => setProposedTerms(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground block mb-1">
            Message *
          </label>
          <textarea
            required
            rows={2}
            placeholder={
              isBuyer
                ? "State your counter-offer or terms request clearly..."
                : "Respond to commercial proposal or clarify lead time/MOQ..."
            }
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="w-full rounded-lg border border-border bg-background p-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <div className="flex justify-end">
          <Button
            type="submit"
            size="sm"
            disabled={isSubmitting || !message.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="size-3.5 animate-spin mr-1" />
                Posting...
              </>
            ) : (
              <>
                <Send className="size-3.5 mr-1" />
                Record Note / Counter
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
