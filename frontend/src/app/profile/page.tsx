"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  User as UserIcon,
  Mail,
  Phone,
  ShieldCheck,
  Save,
  CheckCircle2,
  AlertCircle,
  LogIn,
  Copy,
  ClipboardCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchWithAuth, UserProfile } from "@/lib/api";

export default function ProfilePage() {
  const { user, isLoading: authLoading } = useUser();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [idCopied, setIdCopied] = useState(false);

  const copyId = useCallback(async () => {
    if (!profile?.id) return;
    try {
      await navigator.clipboard.writeText(profile.id);
      setIdCopied(true);
      setTimeout(() => setIdCopied(false), 2000);
    } catch {
      // fallback: select the text element
    }
  }, [profile]);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      if (!user) {
        if (isMounted) setLoadingProfile(false);
        return;
      }
      try {
        const data = await fetchWithAuth<UserProfile>("/v1/users/me");
        if (isMounted) {
          setProfile(data);
          setFullName(data.name || user.name || "");
          setPhoneNumber(data.phone || "");
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : String(err);
          setFullName(user.name || "");
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoadingProfile(false);
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSavedSuccess(false);
    setError(null);

    try {
      const updated = await fetchWithAuth<UserProfile>("/v1/users/me", {
        method: "PATCH",
        body: JSON.stringify({
          name: fullName || null,
          phone: phoneNumber || null,
        }),
      });
      setProfile(updated);
      setSavedSuccess(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to update profile.");
    } finally {
      setIsSaving(false);
    }
  };

  if (authLoading || loadingProfile) {
    return (
      <div className="container mx-auto max-w-4xl py-12 px-4">
        <div className="space-y-4">
          <div className="h-8 w-48 animate-pulse rounded bg-muted" />
          <div className="h-64 w-full animate-pulse rounded-2xl bg-muted/60" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto max-w-2xl py-20 px-4 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-500 border border-blue-500/20">
          <UserIcon className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground mb-3">
          Sign In to Access Your Profile
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-8">
          GlobalTrade.ai uses Auth0 for identity authentication and PostgreSQL
          for enterprise tenant and membership management.
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
    <div className="container mx-auto max-w-4xl py-10 px-4 sm:px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
          User Profile
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage your personal account settings and identity details.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left card: Summary */}
        <div className="md:col-span-1 space-y-6">
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col items-center text-center">
            <div className="h-20 w-20 rounded-full bg-blue-100 dark:bg-blue-950/80 border-2 border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-2xl overflow-hidden mb-4">
              {user.picture ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={user.picture}
                  alt={user.name || "User"}
                  className="h-full w-full object-cover"
                />
              ) : (
                <span>{(user.name || user.email || "U")[0].toUpperCase()}</span>
              )}
            </div>

            <h2 className="font-semibold text-lg text-foreground">
              {profile?.name || user.name || "Trade Operator"}
            </h2>
            <p className="text-xs text-muted-foreground mb-4">{profile?.email || user.email}</p>

            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-semibold border border-emerald-500/20">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Auth0 Verified</span>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4 text-xs">
            <div className="font-semibold text-foreground uppercase tracking-wider text-[11px]">
              Identity Information
            </div>
            <div className="space-y-3 text-muted-foreground">
              <div className="flex justify-between py-1 border-b border-border/40">
                <span>Account Status:</span>
                <span className="font-medium text-emerald-500">{profile?.status || "ACTIVE"}</span>
              </div>

              {/* Database User ID — full UUID with copy button */}
              <div className="py-1 border-b border-border/40 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span>Database User ID</span>
                  {profile?.id && (
                    <button
                      type="button"
                      onClick={copyId}
                      title="Copy User ID"
                      className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium border transition-colors"
                      style={{
                        borderColor: idCopied ? "rgb(16 185 129 / 0.4)" : "rgb(148 163 184 / 0.3)",
                        color: idCopied ? "rgb(16 185 129)" : "inherit",
                        background: idCopied ? "rgb(16 185 129 / 0.08)" : "transparent",
                      }}
                    >
                      {idCopied ? (
                        <><ClipboardCheck className="h-3 w-3" /> Copied!</>
                      ) : (
                        <><Copy className="h-3 w-3" /> Copy</>  
                      )}
                    </button>
                  )}
                </div>
                <p
                  className="font-mono text-[10px] break-all select-all cursor-text text-foreground/80 bg-muted/40 rounded-lg px-2 py-1.5 leading-relaxed"
                  title="Click to select all"
                >
                  {profile?.id || "—"}
                </p>
              </div>

              <div className="flex justify-between py-1 border-b border-border/40">
                <span>Provider ID:</span>
                <span className="font-mono text-[10px] truncate max-w-[120px]" title={user.sub}>
                  {user.sub}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span>Created:</span>
                <span className="font-medium">
                  {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : "Active"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right card: Profile Form */}
        <div className="md:col-span-2">
          <div className="rounded-2xl border border-border bg-card p-8 shadow-sm">
            <h2 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
              <UserIcon className="h-5 w-5 text-blue-500" />
              Edit Personal Details
            </h2>

            {savedSuccess && (
              <div className="mb-6 flex items-center gap-2.5 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm">
                <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
                <span>Profile details updated successfully.</span>
              </div>
            )}

            {error && (
              <div className="mb-6 flex items-center gap-2.5 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-6">
              <div>
                <label
                  htmlFor="fullName"
                  className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2"
                >
                  Full Name
                </label>
                <div className="relative">
                  <UserIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-colors"
                    placeholder="Enter your full legal name"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2"
                >
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    id="email"
                    type="email"
                    value={profile?.email || user.email || ""}
                    disabled
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-input bg-muted/50 text-muted-foreground text-sm cursor-not-allowed"
                  />
                </div>
                <p className="text-[11px] text-muted-foreground mt-1.5">
                  Managed via Auth0 Identity Provider.
                </p>
              </div>

              <div>
                <label
                  htmlFor="phoneNumber"
                  className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2"
                >
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    id="phoneNumber"
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-colors"
                    placeholder="+1 (555) 000-0000"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-border/60 flex items-center justify-end gap-3">
                <Button
                  type="submit"
                  disabled={isSaving}
                  className="gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md shadow-blue-500/20"
                >
                  <Save className="h-4 w-4" />
                  {isSaving ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
