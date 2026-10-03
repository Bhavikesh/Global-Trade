import { Auth0Client } from "@auth0/nextjs-auth0/server";

export const auth0 = new Auth0Client({
  domain: process.env.AUTH0_DOMAIN || "placeholder.auth0.com",
  clientId: process.env.AUTH0_CLIENT_ID || "placeholder_client_id",
  clientSecret: process.env.AUTH0_CLIENT_SECRET || "placeholder_client_secret_minimum_32_chars_12345",
  secret: process.env.AUTH0_SECRET || "placeholder_secret_must_be_at_least_32_chars_long_123456",
  appBaseUrl: process.env.APP_BASE_URL || "http://localhost:3000",
  authorizationParameters: {
    audience: process.env.AUTH0_AUDIENCE || undefined,
    scope: "openid profile email",
  },
});
