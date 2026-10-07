"use client";

import React, { useState } from "react";
import { SupplierInvitationInput } from "@/lib/api";
import { Send, UserPlus, X, Trash2, Plus, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface InviteSupplierModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSendInvitations: (invitations: SupplierInvitationInput[]) => Promise<void>;
}

export function InviteSupplierModal({
  isOpen,
  onClose,
  onSendInvitations,
}: InviteSupplierModalProps) {
  const [invites, setInvites] = useState<SupplierInvitationInput[]>([
    { supplier_email: "", supplier_name: "", response_deadline: "" },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  function updateInvite(
    idx: number,
    field: keyof SupplierInvitationInput,
    value: string
  ) {
    setInvites((prev) => {
      const copy = [...prev];
      copy[idx] = { ...copy[idx], [field]: value };
      return copy;
    });
  }

  function addRow() {
    setInvites((prev) => [
      ...prev,
      { supplier_email: "", supplier_name: "", response_deadline: "" },
    ]);
  }

  function removeRow(idx: number) {
    if (invites.length <= 1) return;
    setInvites((prev) => prev.filter((_, i) => i !== idx));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Validation
    const cleaned = invites
      .map((inv) => ({
        supplier_email: inv.supplier_email.trim().toLowerCase(),
        supplier_name: inv.supplier_name.trim(),
        supplier_organization_id: inv.supplier_organization_id?.trim() || null,
        response_deadline: inv.response_deadline?.trim() || null,
      }))
      .filter((inv) => inv.supplier_email && inv.supplier_name);

    if (cleaned.length === 0) {
      setError("Please provide at least one valid supplier email and name.");
      return;
    }

    const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    for (const inv of cleaned) {
      if (!emailRegex.test(inv.supplier_email)) {
        setError(`Invalid email address format: "${inv.supplier_email}"`);
        return;
      }
    }

    setIsSubmitting(true);
    try {
      await onSendInvitations(cleaned);
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
      <div className="bg-card border border-border w-full max-w-2xl rounded-2xl shadow-2xl p-6 overflow-hidden relative">
        <button
          onClick={onClose}
          disabled={isSubmitting}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground p-1 rounded-lg"
          aria-label="Close"
        >
          <X className="size-5" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="size-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
            <UserPlus className="size-5" />
          </div>
          <div>
            <h3 className="font-bold text-lg text-foreground">
              Invite Suppliers to Quote
            </h3>
            <p className="text-xs text-muted-foreground">
              Dispatch formal RFQ invitations to verified platform suppliers or external email partners
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm flex items-start gap-2">
            <AlertCircle className="size-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1">
            {invites.map((inv, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl border border-border bg-muted/20 space-y-3 relative group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">
                    Supplier #{idx + 1}
                  </span>
                  {invites.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRow(idx)}
                      className="text-muted-foreground hover:text-destructive p-1 rounded transition-colors"
                      aria-label="Remove supplier"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Supplier Company / Contact Name *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Apex Textiles Ltd"
                      value={inv.supplier_name}
                      onChange={(e) =>
                        updateInvite(idx, "supplier_name", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Supplier Email Address *
                    </label>
                    <input
                      type="email"
                      required
                      placeholder="e.g. sales@apextextiles.com"
                      value={inv.supplier_email}
                      onChange={(e) =>
                        updateInvite(idx, "supplier_email", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Supplier Org ID (Optional UUID)
                    </label>
                    <input
                      type="text"
                      placeholder="Platform organization UUID (optional)"
                      value={inv.supplier_organization_id || ""}
                      onChange={(e) =>
                        updateInvite(idx, "supplier_organization_id", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20 font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Response Deadline (Optional)
                    </label>
                    <input
                      type="date"
                      value={inv.response_deadline || ""}
                      onChange={(e) =>
                        updateInvite(idx, "response_deadline", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addRow}
            className="w-full border-dashed"
          >
            <Plus className="size-3.5 mr-1" />
            Add Another Supplier
          </Button>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="size-4 animate-spin mr-1.5" />
                  Sending Invitations...
                </>
              ) : (
                <>
                  <Send className="size-4 mr-1.5" />
                  Dispatch Invitations
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
