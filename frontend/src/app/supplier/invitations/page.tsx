"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useOrganization } from "@/lib/organization-context";
import {
  RFQSupplierInvitation,
  fetchWithAuth,
  ApiError,
} from "@/lib/api";
import {
  Inbox,
  ArrowRight,
  Building2,
  ShieldAlert,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SupplierInvitationsPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useUser();
  const { activeOrg, isLoading: orgLoading } = useOrganization();

  const [invitations, setInvitations] = useState<RFQSupplierInvitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPermissionDenied, setIsPermissionDenied] = useState(false);

  useEffect(() => {
    let active = true;
    async function fetchInitialInvitations() {
      if (!activeOrg) {
        if (active) {
          setInvitations([]);
          setIsLoading(false);
        }
        return;
      }

      try {
        const data = await fetchWithAuth<RFQSupplierInvitation[]>(
          `/v1/organizations/${activeOrg.id}/supplier/invitations`
        );
        if (active) {
          setInvitations(data);
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
      fetchInitialInvitations();
    }
    return () => {
      active = false;
    };
  }, [authLoading, orgLoading, activeOrg]);

  if (authLoading || orgLoading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <Loader2 className="size-8 text-blue-600 animate-spin mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">Loading supplier invitations...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-16 text-center">
        <div className="max-w-md mx-auto p-8 rounded-2xl border border-border bg-card">
          <Building2 className="size-12 text-muted-foreground mx-auto mb-3 opacity-50" />
          <h2 className="text-xl font-bold">Authentication Required</h2>
          <p className="text-sm text-muted-foreground mt-2 mb-6">
            Sign in to view trade invitations sent to your supplier account.
          </p>
          <a
            href="/auth/login"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-blue-600 text-white font-medium text-sm hover:bg-blue-700 shadow-sm"
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
        <div className="max-w-md mx-auto p-8 rounded-2xl border border-border bg-card">
          <Building2 className="size-12 text-muted-foreground mx-auto mb-3 opacity-50" />
          <h2 className="text-xl font-bold">Supplier Organization Required</h2>
          <p className="text-sm text-muted-foreground mt-2 mb-6">
            Select or register your supplier organization to view trade invitations.
          </p>
          <Link href="/organizations">
            <Button size="sm">Manage Organizations</Button>
          </Link>
        </div>
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
            You are not authorized to view supplier invitations for this organization.
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
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              Supplier Portal
            </span>
            <span className="text-xs text-muted-foreground font-mono">
              {activeOrg.display_name || activeOrg.legal_name}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            RFQ Invitations Received
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Review purchasing briefs sent to your organization and submit competitive formal quotations.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm flex items-start gap-3">
          <AlertCircle className="size-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Unable to load invitations</p>
            <p className="text-xs mt-0.5 opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* Invitations Table / List */}
      <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="py-20 text-center flex flex-col items-center justify-center">
            <Loader2 className="size-8 text-blue-600 animate-spin mb-3" />
            <p className="text-sm text-muted-foreground">Loading invitations...</p>
          </div>
        ) : invitations.length === 0 ? (
          <div className="py-16 text-center px-4">
            <Inbox className="size-12 text-muted-foreground mx-auto mb-3 opacity-40" />
            <h3 className="font-bold text-foreground text-base">
              No RFQ Invitations Found
            </h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto mt-1">
              Your supplier organization does not currently have any active or pending RFQ invitations.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/40 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  <th className="p-4 pl-6">Invitation ID</th>
                  <th className="p-4">Invited Email / Contact</th>
                  <th className="p-4">Invitation Status</th>
                  <th className="p-4">Invited Date</th>
                  <th className="p-4">Deadline</th>
                  <th className="p-4 pr-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {invitations.map((inv) => (
                  <tr
                    key={inv.id}
                    className="hover:bg-muted/30 transition-colors group cursor-pointer"
                    onClick={() => {
                      router.push(`/supplier/rfqs/${inv.rfq_id}`);
                    }}
                  >
                    <td className="p-4 pl-6 font-mono text-xs font-semibold text-foreground">
                      <span className="text-blue-600 dark:text-blue-400 group-hover:underline">
                        {inv.id.slice(0, 8)}...
                      </span>
                    </td>

                    <td className="p-4">
                      <div className="flex flex-col">
                        <span className="font-semibold text-foreground">
                          {inv.supplier_name}
                        </span>
                        <span className="text-xs text-muted-foreground font-mono">
                          {inv.supplier_email}
                        </span>
                      </div>
                    </td>

                    <td className="p-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
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

                    <td className="p-4 text-xs text-muted-foreground font-mono">
                      {new Date(inv.invited_at).toLocaleDateString()}
                    </td>

                    <td className="p-4 text-xs text-muted-foreground">
                      {inv.response_deadline
                        ? new Date(inv.response_deadline).toLocaleDateString()
                        : "No deadline specified"}
                    </td>

                    <td className="p-4 pr-6 text-right" onClick={(e) => e.stopPropagation()}>
                      <Link href={`/supplier/rfqs/${inv.rfq_id}`}>
                        <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white text-xs">
                          Review &amp; Quote
                          <ArrowRight className="size-3.5 ml-1" />
                        </Button>
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
