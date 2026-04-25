/**
 * Vellum API Configuration
 * ========================
 *
 * Defines how the SDK communicates with the backend.
 * Consumers provide their base URL, auth token getter, and optional endpoint overrides.
 *
 * The SDK never assumes a specific backend — it just needs:
 * 1. A base URL
 * 2. A way to get auth tokens
 * 3. Optional endpoint path overrides
 */

export interface VellumApiConfig {
  /** Base URL for API calls (e.g., "http://localhost:5000" or "https://api.example.com") */
  baseUrl: string;

  /** Async function that returns a valid auth token */
  getAccessToken: () => Promise<string>;

  /** Optional endpoint path overrides (defaults provided by each package) */
  endpoints?: Partial<VellumEndpoints>;
}

/**
 * Default endpoint paths. Each package defines its own defaults.
 * Consumers can override any endpoint via VellumApiConfig.endpoints.
 */
export interface VellumEndpoints {
  /** GraphQL query endpoint (default: "/graphql") */
  graphql: string;

  /** Dynamic mutation endpoint (default: "/dynamic") */
  dynamic: string;

  /** Negotiation API base (default: "/api/negotiation") */
  negotiation: string;

  /** Seal API base (default: "/api/seal") */
  seal: string;

  /** Agent API base (default: "/api/agent") */
  agent: string;

  /** Identity API base (default: "/api/identity") */
  identity: string;
}

export const DEFAULT_ENDPOINTS: VellumEndpoints = {
  graphql: '/graphql',
  dynamic: '/dynamic',
  negotiation: '/api/negotiation',
  seal: '/api/seal',
  agent: '/api/agent',
  identity: '/api/identity',
};

/**
 * Authenticated fetch helper used internally by all SDK packages.
 */
export async function vellumFetch(
  config: VellumApiConfig,
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = await config.getAccessToken();
  const url = `${config.baseUrl}${path}`;

  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
}
