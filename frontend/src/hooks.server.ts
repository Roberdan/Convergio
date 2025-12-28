/**
 * 🔐 Convergio Server Hooks
 * Server-side authentication and security handling
 */

import type { Handle } from "@sveltejs/kit";

export const handle: Handle = async ({ event, resolve }) => {
  // Add security headers
  const response = await resolve(event, {
    transformPageChunk: ({ html }) => {
      // Add security meta tags and nonce for CSP
      return html;
    },
  });

  // Set security headers
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=()",
  );

  // CORS is handled by the backend, not the frontend

  return response;
};
