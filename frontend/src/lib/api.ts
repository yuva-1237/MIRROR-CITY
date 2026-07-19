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

let _consecutiveFailures = 0;
let _circuitBreakerOpen = false;
let _lastFailureTime = 0;
const CIRCUIT_BREAKER_LIMIT = 5;
const CIRCUIT_BREAKER_COOLDOWN_MS = 15000;

/**
 * apiFetch — typed, error-aware wrapper around the browser Fetch API.
 * Includes automatic retry on 5xx/network errors and a client-side circuit breaker.
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

  // 1. Check Circuit Breaker
  if (_circuitBreakerOpen) {
    const elapsed = Date.now() - _lastFailureTime;
    if (elapsed < CIRCUIT_BREAKER_COOLDOWN_MS) {
      throw new ApiError(
        'Server connection suspended (Circuit Breaker Tripped).',
        0,
        'CIRCUIT_BREAKER_OPEN',
        `The frontend has temporarily stopped sending requests because the backend server is unreachable. ` +
        `Retrying automatically in ${Math.ceil((CIRCUIT_BREAKER_COOLDOWN_MS - elapsed) / 1000)}s.`
      );
    } else {
      _circuitBreakerOpen = false;
      _consecutiveFailures = 0;
    }
  }

  const url = `${baseUrl}${path}`;
  const authToken = token !== undefined ? token : localStorage.getItem('token');

  // Build headers
  const headers = new Headers(rawHeaders as HeadersInit | undefined);
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`);
  }

  const startMs = Date.now();
  let attempt = 0;
  const maxAttempts = 3;
  let lastError: any = null;

  while (attempt < maxAttempts) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      window.clearTimeout(timeoutId);
      const status = response.status;
      const elapsedMs = Date.now() - startMs;

      // Structured log (non-sensitive)
      console.debug(
        `[API] ${fetchOptions.method ?? 'GET'} ${path} → ${status} (${elapsedMs}ms)`
      );

      // Request succeeded — reset failure counters
      _consecutiveFailures = 0;
      _circuitBreakerOpen = false;

      if (response.ok) {
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

      // Don't retry on 4xx client errors
      if (status < 500) {
        throw apiErr;
      }

      lastError = apiErr;
    } catch (err: unknown) {
      window.clearTimeout(timeoutId);

      if (err instanceof ApiError) {
        if (err.status > 0 && err.status < 500) {
          throw err; // fail fast on client errors
        }
        lastError = err;
      } else if (err instanceof Error && err.name === 'AbortError') {
        lastError = new ApiError(
          `Request timed out after ${timeoutMs / 1000}s.`,
          0,
          'TIMEOUT',
          `The AI Coordinator did not respond within ${timeoutMs / 1000} seconds. ` +
            'Check if the backend is under heavy load.'
        );
      } else if (err instanceof TypeError) {
        lastError = new ApiError(
          'Cannot reach the backend server.',
          0,
          'NETWORK_ERROR',
          `Ensure the FastAPI server is running at ${API_BASE_URL} and there are no firewall or CORS issues.`
        );
      } else {
        lastError = err;
      }
    }

    attempt++;
    if (attempt < maxAttempts) {
      const delay = 500 * Math.pow(2, attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  // All retry attempts failed — increment failures
  _consecutiveFailures++;
  if (_consecutiveFailures >= CIRCUIT_BREAKER_LIMIT) {
    _circuitBreakerOpen = true;
    _lastFailureTime = Date.now();
  }

  throw lastError;
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
