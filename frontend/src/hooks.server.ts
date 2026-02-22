/**
 * 🔐 Convergio Server Hooks
 * Server-side authentication and security handling
 */

import type { Handle, HandleFetch } from "@sveltejs/kit";

const backendBaseUrls = [
  process.env.BACKEND_URL,
  process.env.VITE_API_URL,
  "https://convergio-backend-prod.eastus.azurecontainerapps.io",
  "http://localhost:9000",
]
  .filter((url): url is string => Boolean(url))
  .map((url) => url.replace(/\/$/, ""));

const shouldForwardCookie = (requestUrl: URL): boolean =>
  backendBaseUrls.some((baseUrl) => requestUrl.href.startsWith(baseUrl));

export const handleFetch: HandleFetch = async ({ event, request, fetch }) => {
  const authCookie = event.request.headers.get("cookie");

  if (authCookie && shouldForwardCookie(new URL(request.url))) {
    const headers = new Headers(request.headers);
    headers.set("cookie", authCookie);

    request = new Request(request, { headers });
  }

  return fetch(request);
};

export const handle: Handle = async ({ event, resolve }) => {
  const response = await resolve(event, {
    transformPageChunk: ({ html }) => html,
  });

  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");

  return response;
};
