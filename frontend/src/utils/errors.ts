import axios from 'axios';

/**
 * Normalizes unknown errors into safe, generic user-facing messages.
 * Prevents stack traces, internal URLs, or raw API errors from leaking to the UI.
 */
export function getSafeApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return 'Network Error or Backend Unavailable.';
    const status = error.response.status;
    if (status === 400) return 'Invalid request.';
    if (status === 401) return 'Authentication or authorization failed.';
    if (status === 403) return 'Permission denied.';
    if (status === 404) return 'Resource not found.';
    if (status === 409) return 'Duplicate event detected.';
    if (status === 413) return 'Payload too large.';
    if (status === 422) return 'Request rejected by schema validation.';
    if (status === 429) return 'Rate limit exceeded.';
    if (status >= 500) return 'Service temporarily unavailable.';
    return 'Request failed.';
  }

  if (error instanceof Error) {
    // We do not return error.message directly because it might contain sensitive data from a nested failure
    return 'An unexpected application error occurred.';
  }

  return 'An unknown error occurred.';
}

/** HTTP status of a failed API call, or null for network / non-HTTP failures. */
export function getErrorStatus(error: unknown): number | null {
  if (axios.isAxiosError(error) && error.response) return error.response.status;
  return null;
}

/** True when the failure came from the demo signer being disabled on the backend. */
export function isDemoSignerDisabled(error: unknown): boolean {
  return (
    axios.isAxiosError(error) &&
    error.response?.status === 404 &&
    typeof error.config?.url === 'string' &&
    error.config.url.includes('/webhooks/demo/sign')
  );
}
