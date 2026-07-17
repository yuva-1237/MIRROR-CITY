/**
 * lib/api.ts — Mirror City Centralized API Client
 *
 * Single source of truth for:
 *  - Base URL resolution (env var → fallback)
 *  - HTTP fetch wrapper with timeout, auth, and retry
 *  - Status-code → human-readable error mapping
 *  - Automatic 401 handling (token clear + redirect trigger)
 *  - Structured request/response logging
 */

// ── Base URLs ────────────────────────────────────────────────────────────────
export const API_BASE_URL: string =
  (import.meta as any).env?.VITE_API_URL ?? 'http://127.0.0.1:8000';

export const WS_BASE_URL: string =
  (import.meta as any).env?.VITE_WS_URL ?? 'ws://127.0.0.1:8000';

// ── Error Classes ────────────────────────────────────────────────────────────

export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly suggestion: string;

  constructor(message: string, status: number, code: string, suggestion: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.suggestion = suggestion;
  }
}

// ── Error Mapping ────────────────────────────────────────────────────────────

function mapStatusToError(status: number, serverDetail?: string): ApiError {
  switch (status) {
    case 400:
      return new ApiError(
        serverDetail ?? 'Bad request — invalid input data.',
        400,
        'BAD_REQUEST',
        'Check the data you submitted for missing or invalid fields.'
      );
    case 401:
      return new ApiError(
        'Session expired or invalid credentials.',
        401,
        'UNAUTHORIZED',
        'Your session has expired. Please log in again.'
      );
    case 403:
      return new ApiError(
        'Access denied — insufficient permissions.',
        403,
        'FORBIDDEN',
        'Your account role does not have access to this resource. Contact an Administrator.'
      );
    case 404:
      return new ApiError(
        'API endpoint not found.',
        404,
        'NOT_FOUND',
        'The requested resource does not exist. The backend may need to be restarted.'
      );
    case 422:
      return new ApiError(
        serverDetail ?? 'Validation error in request payload.',
        422,
        'VALIDATION_ERROR',
        'Check that all required fields are present and correctly typed.'
      );
    case 500:
      return new ApiError(
        'Internal server error in AI Coordinator.',
        500,
        'SERVER_ERROR',
        'A backend exception occurred. Check the Python server console for a stack trace.'
      );
    case 502:
    case 503:
    case 504:
      return new ApiError(
        'Backend service unavailable.',
        status,
        'SERVICE_UNAVAILABLE',
        'The FastAPI server may be starting up or crashed. Wait 10s and retry.'
      );
    default:
      return new ApiError(
        serverDetail ?? `Unexpected server response (HTTP ${status}).`,
        status,
        'UNKNOWN',
        'Check browser DevTools → Network tab for details.'
      );
  }
}

// ── Token Utilities ──────────────────────────────────────────────────────────

/** Returns true if the JWT stored in localStorage is expired or missing. */
export function isTokenExpired(): boolean {
  const token = localStorage.getItem('token');
  if (!token) return true;
  try {
    // JWT payload is the second base64url segment
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (!payload.exp) return false; // no expiry claim → treat as valid
    return Date.now() / 1000 > payload.exp;
  } catch {
    return true; // malformed token → treat as expired
  }
}

/** Clear all auth state from localStorage. */
export function clearAuthState(): void {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
}

// ── Callback registry for 401 events ────────────────────────────────────────
// Components register a callback so the API client can trigger logout without
// importing React state setters (which would cause circular deps).

let _on401Callback: (() => void) | null = null;

export function registerOn401Handler(cb: () => void): void {
  _on401Callback = cb;
}

// ── Core Fetch Wrapper ───────────────────────────────────────────────────────

export interface ApiFetchOptions extends Omit<RequestInit, 'signal'> {
  /** Override the base URL (default: API_BASE_URL). */
  baseUrl?: string;
  /** Timeout in ms (default: 15000). */
  timeoutMs?: number;
  /** Auth token (default: read from localStorage). */
  token?: string | null;
}

/**
 * apiFetch — typed, error-aware wrapper around the browser Fetch API.
 *
 * @param path   URL path relative to API_BASE_URL (e.g. '/api/simulations/assistant')
 * @param options  Standard RequestInit + Mirror City extensions
 * @returns      Parsed JSON response body (typed as T)
 * @throws ApiError on any non-2xx response or network/timeout failure
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const {
    baseUrl = API_BASE_URL,
    timeoutMs = 15_000,
    token,
    headers: rawHeaders,
    ...fetchOptions
  } = options;

  const url = `${baseUrl}${path}`;
  const authToken = token !== undefined ? token : localStorage.getItem('token');

  // Build headers
  const headers = new Headers(rawHeaders as HeadersInit | undefined);
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`);
  }

  // Timeout controller
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  const startMs = Date.now();
  let status = 0;

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    status = response.status;
    const elapsedMs = Date.now() - startMs;

    // Structured log (non-sensitive)
    console.debug(
      `[API] ${fetchOptions.method ?? 'GET'} ${path} → ${status} (${elapsedMs}ms)`
    );

    if (response.ok) {
      // Parse JSON body; handle empty responses (204 No Content)
      if (response.status === 204) return undefined as unknown as T;
      return (await response.json()) as T;
    }

    // Attempt to read server error detail
    let serverDetail: string | undefined;
    try {
      const errBody = await response.json();
      serverDetail = errBody?.detail ?? errBody?.message;
    } catch {
      /* ignore */
    }

    const apiErr = mapStatusToError(status, serverDetail);

    // Handle 401 globally — clear auth and notify registered handler
    if (status === 401) {
      clearAuthState();
      _on401Callback?.();
    }

    console.error(
      `[API] ${fetchOptions.method ?? 'GET'} ${path} → ${status} "${apiErr.message}"`,
      { code: apiErr.code, suggestion: apiErr.suggestion }
    );

    throw apiErr;
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof ApiError) throw err;

    // AbortError = timeout
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ApiError(
        `Request timed out after ${timeoutMs / 1000}s.`,
        0,
        'TIMEOUT',
        `The AI Coordinator did not respond within ${timeoutMs / 1000} seconds. ` +
          'Check if the backend is under heavy load.'
      );
    }

    // TypeError: Failed to fetch → network unreachable
    if (err instanceof TypeError) {
      throw new ApiError(
        'Cannot reach the backend server.',
        0,
        'NETWORK_ERROR',
        `Ensure the FastAPI server is running at ${API_BASE_URL} and there are no firewall or CORS issues.`
      );
    }

    throw new ApiError(
      'An unexpected client-side error occurred.',
      0,
      'CLIENT_ERROR',
      'Check the browser console for more details.'
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Convenience helpers ──────────────────────────────────────────────────────

export const apiGet = <T>(path: string, opts?: ApiFetchOptions) =>
  apiFetch<T>(path, { method: 'GET', ...opts });

export const apiPost = <T>(path: string, body: unknown, opts?: ApiFetchOptions) =>
  apiFetch<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    ...opts,
  });

export const apiDelete = <T>(path: string, opts?: ApiFetchOptions) =>
  apiFetch<T>(path, { method: 'DELETE', ...opts });
