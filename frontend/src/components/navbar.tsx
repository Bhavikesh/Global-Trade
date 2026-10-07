"use client";

import React from "react";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  Globe,
  Building2,
  LogIn,
  LogOut,
  Activity,
  FileSpreadsheet,
  Inbox,
} from "lucide-react";
import { useOrganization } from "@/lib/organization-context";

export function Navbar() {
  const { user, isLoading } = useUser();
  const { organizations, activeOrg, setActiveOrgId, userRole } = useOrganization();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <Globe className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-lg leading-tight tracking-tight bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
                GlobalTrade<span className="text-blue-500">.ai</span>
              </span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold">
                Autonomous Trade Intelligence
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-5 text-sm font-medium">
            <Link
              href="/"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              Overview
            </Link>
            <Link
              href="/rfqs"
              className="text-muted-foreground transition-colors hover:text-foreground flex items-center gap-1.5"
            >
              <FileSpreadsheet className="h-4 w-4 text-blue-500" />
              RFQs
            </Link>
            <Link
              href="/supplier/invitations"
              className="text-muted-foreground transition-colors hover:text-foreground flex items-center gap-1.5"
            >
              <Inbox className="h-4 w-4 text-emerald-500" />
              Supplier RFQs
            </Link>
            <Link
              href="/organizations"
              className="text-muted-foreground transition-colors hover:text-foreground flex items-center gap-1.5"
            >
              <Building2 className="h-4 w-4" />
              Organizations
            </Link>
            <Link
              href="/company-profile"
              className="text-muted-foreground transition-colors hover:text-foreground flex items-center gap-1.5"
            >
              <Globe className="h-4 w-4" />
              Profile
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {activeOrg && (
            <div className="hidden lg:flex items-center gap-2 border border-border/80 bg-muted/40 rounded-lg px-2.5 py-1 text-xs">
              <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
              <div className="flex flex-col">
                <span className="font-medium text-foreground max-w-[130px] truncate leading-tight">
                  {activeOrg.display_name || activeOrg.legal_name}
                </span>
                {userRole && (
                  <span className="text-[10px] text-muted-foreground uppercase font-mono">
                    {userRole}
                  </span>
                )}
              </div>
              {organizations.length > 1 && (
                <select
                  value={activeOrg.id}
                  onChange={(e) => setActiveOrgId(e.target.value)}
                  className="bg-transparent border-none text-[11px] text-muted-foreground cursor-pointer focus:outline-none"
                  aria-label="Switch organization"
                >
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id} className="bg-popover text-foreground">
                      {org.display_name || org.legal_name}
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-medium border border-emerald-500/20">
            <Activity className="h-3 w-3 animate-pulse" />
            <span>API Online</span>
          </div>

          {isLoading ? (
            <div className="h-9 w-24 animate-pulse rounded-md bg-muted" />
          ) : user ? (
            <div className="flex items-center gap-3">
              <Link href="/profile" className="flex items-center gap-2.5 group">
                <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-950/80 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-blue-400 font-semibold text-xs overflow-hidden">
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
                <div className="hidden lg:flex flex-col text-left">
                  <span className="text-xs font-semibold text-foreground group-hover:text-blue-500 transition-colors">
                    {user.name || "Authenticated User"}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {user.email}
                  </span>
                </div>
              </Link>
              <a
                href="/auth/logout"
                className="inline-flex items-center justify-center rounded-lg border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground gap-1.5 transition-colors"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign Out
              </a>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <a
                href="/auth/login"
                className="inline-flex items-center justify-center rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 px-3 py-1.5 text-xs font-medium text-white shadow-md shadow-blue-500/20 gap-1.5 transition-all"
              >
                <LogIn className="h-3.5 w-3.5" />
                Sign In
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
