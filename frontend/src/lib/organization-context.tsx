"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  fetchWithAuth,
  Organization,
  OrganizationMembership,
} from "@/lib/api";

interface OrganizationContextType {
  organizations: Organization[];
  activeOrg: Organization | null;
  setActiveOrgId: (orgId: string) => void;
  userRole: string | null;
  isLoading: boolean;
  error: string | null;
  refreshOrganizations: () => Promise<void>;
}

const OrganizationContext = createContext<OrganizationContextType>({
  organizations: [],
  activeOrg: null,
  setActiveOrgId: () => {},
  userRole: null,
  isLoading: true,
  error: null,
  refreshOrganizations: async () => {},
});

const STORAGE_KEY = "globaltrade_active_org_id";

export function OrganizationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading: authLoading } = useUser();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [activeOrgId, setActiveOrgIdState] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshOrganizations = useCallback(async () => {
    if (!user) {
      setOrganizations([]);
      setActiveOrgIdState(null);
      setUserRole(null);
      setIsLoading(false);
      return;
    }

    try {
      setError(null);
      const orgs = await fetchWithAuth<Organization[]>("/v1/organizations/");
      setOrganizations(orgs);

      if (orgs.length > 0) {
        const savedId =
          typeof window !== "undefined"
            ? localStorage.getItem(STORAGE_KEY)
            : null;
        const matchingOrg = orgs.find((o) => o.id === savedId);
        const resolvedId = matchingOrg ? matchingOrg.id : orgs[0].id;
        setActiveOrgIdState(resolvedId);
        if (typeof window !== "undefined") {
          localStorage.setItem(STORAGE_KEY, resolvedId);
        }
      } else {
        setActiveOrgIdState(null);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  // Fetch initial organizations
  useEffect(() => {
    let active = true;
    async function loadInitialOrgs() {
      if (!user) {
        if (active) {
          setOrganizations([]);
          setActiveOrgIdState(null);
          setUserRole(null);
          setIsLoading(false);
        }
        return;
      }
      try {
        const orgs = await fetchWithAuth<Organization[]>("/v1/organizations/");
        if (active) {
          setOrganizations(orgs);
          if (orgs.length > 0) {
            const savedId =
              typeof window !== "undefined"
                ? localStorage.getItem(STORAGE_KEY)
                : null;
            const matchingOrg = orgs.find((o) => o.id === savedId);
            const resolvedId = matchingOrg ? matchingOrg.id : orgs[0].id;
            setActiveOrgIdState(resolvedId);
            if (typeof window !== "undefined") {
              localStorage.setItem(STORAGE_KEY, resolvedId);
            }
          } else {
            setActiveOrgIdState(null);
          }
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

    if (!authLoading) {
      loadInitialOrgs();
    }
    return () => {
      active = false;
    };
  }, [authLoading, user]);

  // Fetch role whenever activeOrgId changes
  useEffect(() => {
    let active = true;
    async function fetchRole() {
      if (!activeOrgId || !user) {
        setUserRole(null);
        return;
      }
      try {
        const members = await fetchWithAuth<OrganizationMembership[]>(
          `/v1/organizations/${activeOrgId}/members`
        );
        if (active) {
          if (members.length > 0) {
            setUserRole(members[0].role);
          }
        }
      } catch {
        if (active) setUserRole(null);
      }
    }
    fetchRole();
    return () => {
      active = false;
    };
  }, [activeOrgId, user]);

  const setActiveOrgId = useCallback(
    (orgId: string) => {
      setActiveOrgIdState(orgId);
      if (typeof window !== "undefined") {
        localStorage.setItem(STORAGE_KEY, orgId);
      }
    },
    []
  );

  const activeOrg =
    organizations.find((o) => o.id === activeOrgId) || null;

  return (
    <OrganizationContext.Provider
      value={{
        organizations,
        activeOrg,
        setActiveOrgId,
        userRole,
        isLoading: authLoading || isLoading,
        error,
        refreshOrganizations,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  return useContext(OrganizationContext);
}
