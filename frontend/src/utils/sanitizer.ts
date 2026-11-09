/**
 * Ensures any accidental backend leaks of sensitive data are masked in the UI.
 * This is a defense-in-depth measure. The backend should not emit these.
 */
export function sanitizeText(text: string): string {
    if (!text) return text;
    // Mask 13-19 digit numbers (PANs)
    let sanitized = text.replace(/\b\d{13,19}\b/g, '[REDACTED PAN]');
    // Mask typical CVV patterns
    sanitized = sanitized.replace(/cvv["']?\s*[:=]\s*["']?\d{3,4}["']?/gi, 'cvv: "[REDACTED]"');
    // Mask Bearer tokens
    sanitized = sanitized.replace(/Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*/gi, 'Bearer [REDACTED]');
    return sanitized;
}

export function sanitizeHtmlToText(html: string): string {
    // Treat everything as text. React does this natively when rendering,
    // but if we need to explicitly scrub strings:
    const doc = new DOMParser().parseFromString(html, 'text/html');
    return doc.body.textContent || "";
}
