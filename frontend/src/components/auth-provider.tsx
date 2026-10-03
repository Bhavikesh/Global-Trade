"use client";

import React, { ReactNode } from "react";
import { Auth0Provider } from "@auth0/nextjs-auth0/client";

export function AuthProvider({ children }: { children: ReactNode }) {
  return <Auth0Provider>{children}</Auth0Provider>;
}
