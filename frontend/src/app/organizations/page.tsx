"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  Building2,
  Plus,
  Users,
  Shield,
  Globe2,
  CheckCircle2,
  AlertCircle,
  LogIn,
  UserPlus,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchWithAuth, Organization, OrganizationMembership } from "@/lib/api";

const BUSINESS_TYPES = [
  { value: "EXPORTER", label: "Exporter" },
  { value: "IMPORTER", label: "Importer" },
  { value: "BOTH", label: "Exporter & Importer" },
  { value: "LOGISTICS_PROVIDER", label: "Logistics Provider" },
  { value: "CUSTOMS_BROKER", label: "Customs Broker" },
  { value: "FREIGHT_FORWARDER", label: "Freight Forwarder" },
  { value: "FINANCIAL_INSTITUTION", label: "Financial Institution" },
  { value: "OTHER", label: "Other" },
];

const ROLES = [
  "ADMIN",
  "EXPORTER",
  "IMPORTER",
  "BUYER",
  "SUPPLIER",
  "OPERATIONS",
  "FINANCE",
  "COMPLIANCE",
  "LOGISTICS",
  "MEMBER",
];

export default function OrganizationsPage() {
  const { user, isLoading: authLoading } = useUser();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [members, setMembers] = useState<OrganizationMembership[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [isLoadingOrgs, setIsLoadingOrgs] = useState(true);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form states
  const [legalName, setLegalName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [businessType, setBusinessType] = useState("EXPORTER");
  const [country, setCountry] = useState("US");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [inviteUserId, setInviteUserId] = useState("");
  const [inviteRole, setInviteRole] = useState("MEMBER");

  const refreshOrganizations = useCallback(async () => {
    if (!user) return;
    try {
      const data = await fetchWithAuth<Organization[]>("/v1/organizations/");
      setOrganizations(data);
      if (data.length > 0) {
        setSelectedOrgId((prev) =>
          prev && data.some((o) => o.id === prev) ? prev : data[0].id
        );
      } else {
        setSelectedOrgId(null);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg);
    }
  }, [user]);

  const refreshMembers = useCallback(async (orgId: string) => {
    try {
      const data = await fetchWithAuth<OrganizationMembership[]>(
        `/v1/organizations/${orgId}/members`
      );
      setMembers(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg);
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function fetchInitialOrgs() {
      if (!user) {
        if (active) setIsLoadingOrgs(false);
        return;
      }
      try {
        const data = await fetchWithAuth<Organization[]>("/v1/organizations/");
        if (active) {
          setOrganizations(data);
          if (data.length > 0) {
            setSelectedOrgId((prev) =>
              prev && data.some((o) => o.id === prev) ? prev : data[0].id
            );
          } else {
            setSelectedOrgId(null);
          }
        }
      } catch (err: unknown) {
        if (active) {
          const msg = err instanceof Error ? err.message : String(err);
          setErrorMessage(msg);
        }
      } finally {
        if (active) {
          setIsLoadingOrgs(false);
        }
      }
    }
    fetchInitialOrgs();
    return () => {
      active = false;
    };
  }, [user]);

  useEffect(() => {
    let active = true;
    async function fetchInitialMembers() {
      if (!selectedOrgId) {
        if (active) setMembers([]);
        return;
      }
      try {
        const data = await fetchWithAuth<OrganizationMembership[]>(
          `/v1/organizations/${selectedOrgId}/members`
        );
        if (active) {
          setMembers(data);
        }
      } catch (err: unknown) {
        if (active) {
          const msg = err instanceof Error ? err.message : String(err);
          setErrorMessage(msg);
        }
      } finally {
        if (active) {
          setIsLoadingMembers(false);
        }
      }
    }
    fetchInitialMembers();
    return () => {
      active = false;
    };
  }, [selectedOrgId]);

  const selectedOrg = organizations.find((o) => o.id === selectedOrgId) || null;

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const newOrg = await fetchWithAuth<Organization>("/v1/organizations/", {
        method: "POST",
        body: JSON.stringify({
          legal_name: legalName,
          display_name: displayName || legalName,
          business_type: businessType,
          country: country.toUpperCase(),
        }),
      });
      setShowCreateModal(false);
      setLegalName("");
      setDisplayName("");
      await refreshOrganizations();
      setSelectedOrgId(newOrg.id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg || "Failed to create organization.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteUserId || !selectedOrgId) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await fetchWithAuth<OrganizationMembership>(
        `/v1/organizations/${selectedOrgId}/members`,
        {
          method: "POST",
          body: JSON.stringify({
            user_id: inviteUserId,
            role: inviteRole,
          }),
        }
      );
      setShowInviteModal(false);
      setInviteUserId("");
      await refreshMembers(selectedOrgId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg || "Failed to add member to organization.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading || isLoadingOrgs) {
    return (
      <div className="container mx-auto max-w-6xl py-12 px-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-96 animate-pulse rounded-2xl bg-muted/60" />
          <div className="md:col-span-2 h-96 animate-pulse rounded-2xl bg-muted/60" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto max-w-2xl py-20 px-4 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-500 border border-blue-500/20">
          <Building2 className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-3">
          Sign In to Manage Organizations
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-8">
          Enterprise organizations are strictly isolated tenants. Sign in with
          Auth0 to access your trade entity workspaces.
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

  return (
    <div className="container mx-auto max-w-7xl py-10 px-4 sm:px-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
            Organization Management
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage multi-tenant trade entities, member roles, and tenant isolation policies.
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md shadow-blue-500/20"
        >
          <Plus className="h-4 w-4" />
          Create Organization
        </Button>
      </div>

      {errorMessage && (
        <div className="mb-6 flex items-center gap-2.5 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Organization List */}
        <div className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">
            Your Organizations ({organizations.length})
          </div>

          <div className="space-y-3">
            {organizations.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border p-8 text-center text-muted-foreground text-xs">
                No organizations found. Create one to get started.
              </div>
            ) : (
              organizations.map((org) => {
                const isSelected = selectedOrgId === org.id;
                return (
                  <div
                    key={org.id}
                    onClick={() => setSelectedOrgId(org.id)}
                    className={`cursor-pointer rounded-2xl border p-5 transition-all duration-200 ${
                      isSelected
                        ? "border-blue-500/60 bg-blue-500/5 shadow-md shadow-blue-500/5 ring-1 ring-blue-500/40"
                        : "border-border bg-card hover:border-border/80 hover:bg-muted/30"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center font-bold text-sm">
                          <Building2 className="h-5 w-5" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground text-sm">
                            {org.display_name || org.legal_name}
                          </h3>
                          <p className="text-xs text-muted-foreground">
                            {org.legal_name}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-border/40 flex items-center justify-between text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Globe2 className="h-3.5 w-3.5" />
                        {org.country || "N/A"}
                      </span>
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-500 font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        {org.verification_status}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Selected Organization Details & Members */}
        <div className="lg:col-span-2 space-y-6">
          {selectedOrg ? (
            <>
              {/* Organization Header Card */}
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border/50">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-2xl font-bold text-foreground">
                        {selectedOrg.display_name || selectedOrg.legal_name}
                      </h2>
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        {selectedOrg.verification_status}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 font-mono">
                      Org ID: {selectedOrg.id}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      href="/company-profile"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-muted text-xs font-medium text-foreground transition-colors"
                    >
                      <FileText className="h-3.5 w-3.5 text-blue-500" />
                      Company Profile
                    </Link>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowInviteModal(true)}
                      className="gap-1.5 text-xs"
                    >
                      <UserPlus className="h-3.5 w-3.5 text-blue-500" />
                      Add Member
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
                  <div className="p-3 rounded-xl bg-muted/40 border border-border/40">
                    <span className="text-[11px] text-muted-foreground uppercase font-medium">
                      Business Type
                    </span>
                    <p className="text-xs font-semibold text-foreground mt-1">
                      {selectedOrg.business_type || "Standard"}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-muted/40 border border-border/40">
                    <span className="text-[11px] text-muted-foreground uppercase font-medium">
                      Country
                    </span>
                    <p className="text-xs font-semibold text-foreground mt-1">
                      {selectedOrg.country || "N/A"}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-muted/40 border border-border/40">
                    <span className="text-[11px] text-muted-foreground uppercase font-medium">
                      Isolation Status
                    </span>
                    <p className="text-xs font-semibold text-emerald-500 mt-1 flex items-center gap-1">
                      <Shield className="h-3 w-3" />
                      Enforced (T1.6)
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-muted/40 border border-border/40">
                    <span className="text-[11px] text-muted-foreground uppercase font-medium">
                      Created
                    </span>
                    <p className="text-xs font-semibold text-foreground mt-1">
                      {new Date(selectedOrg.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Members Table Card */}
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-blue-500" />
                    <h3 className="font-semibold text-base text-foreground">
                      Organization Members ({members.length})
                    </h3>
                  </div>
                </div>

                {isLoadingMembers ? (
                  <div className="h-24 animate-pulse rounded-xl bg-muted" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-border/60 text-muted-foreground">
                          <th className="pb-3 font-medium uppercase tracking-wider">Member User ID</th>
                          <th className="pb-3 font-medium uppercase tracking-wider">Role</th>
                          <th className="pb-3 font-medium uppercase tracking-wider">Status</th>
                          <th className="pb-3 font-medium uppercase tracking-wider">Joined</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/30">
                        {members.map((m) => (
                          <tr key={m.id} className="hover:bg-muted/20 transition-colors">
                            <td className="py-3.5 font-mono text-[11px] text-foreground">
                              {m.user_id}
                            </td>
                            <td className="py-3.5">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                                {m.role}
                              </span>
                            </td>
                            <td className="py-3.5">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                                {m.status}
                              </span>
                            </td>
                            <td className="py-3.5 text-muted-foreground">
                              {new Date(m.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="rounded-2xl border border-dashed border-border p-12 text-center text-muted-foreground">
              <Building2 className="h-8 w-8 mx-auto mb-2 opacity-40" />
              <p className="text-sm">Select an organization to inspect its details and members.</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal: Create Organization */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <h2 className="text-xl font-bold text-foreground mb-1">
              Create New Organization
            </h2>
            <p className="text-xs text-muted-foreground mb-6">
              You will automatically become the ADMIN of this organization.
            </p>

            <form onSubmit={handleCreateOrg} className="space-y-4">
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                  Legal Entity Name *
                </label>
                <input
                  type="text"
                  required
                  value={legalName}
                  onChange={(e) => setLegalName(e.target.value)}
                  placeholder="e.g. Pacific Coast Trading LLC"
                  className="w-full px-3.5 py-2 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                  Display Name
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Pacific Coast Trading"
                  className="w-full px-3.5 py-2 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                    Business Type
                  </label>
                  <select
                    value={businessType}
                    onChange={(e) => setBusinessType(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    {BUSINESS_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                    Country Code (ISO-2)
                  </label>
                  <input
                    type="text"
                    maxLength={2}
                    required
                    value={country}
                    onChange={(e) => setCountry(e.target.value.toUpperCase())}
                    placeholder="US"
                    className="w-full px-3.5 py-2 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-border/60 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={isSubmitting}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isSubmitting ? "Creating..." : "Create Organization"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Invite Member */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <h2 className="text-xl font-bold text-foreground mb-1">
              Add Organization Member
            </h2>
            <p className="text-xs text-muted-foreground mb-6">
              Assign an approved application role to an invited team member UUID.
            </p>

            <form onSubmit={handleInviteMember} className="space-y-4">
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                  User UUID *
                </label>
                <input
                  type="text"
                  required
                  value={inviteUserId}
                  onChange={(e) => setInviteUserId(e.target.value)}
                  placeholder="e.g. 12345678-1234-5678-1234-567812345678"
                  className="w-full px-3.5 py-2 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
                  Role Assignment
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-4 border-t border-border/60 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowInviteModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={isSubmitting}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isSubmitting ? "Adding..." : "Add Member"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
