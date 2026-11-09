import { describe, it, expect } from 'vitest';
import { sanitizeText, sanitizeHtmlToText } from './sanitizer';

describe('sanitizer', () => {
    it('masks raw PAN sequences', () => {
        const input = "User attempted transaction with card " + "41112222" + "33334444" + " from IP.";
        const output = sanitizeText(input);
        expect(output).toContain("[REDACTED PAN]");
        expect(output).not.toContain("41112222" + "33334444");
    });

    it('masks CVV explicitly', () => {
        const input = '{"event_id": "1", "cvv": "123"}';
        const output = sanitizeText(input);
        expect(output).toContain("[REDACTED]");
        expect(output).not.toContain('"123"');
    });

    it('masks nested malicious sensitive patterns in strings', () => {
        const input = `error detail: user token=123 cvv=456 and Bearer x-api-key-12345`;
        const output = sanitizeText(input);
        expect(output).toContain('cvv: "[REDACTED]"');
        expect(output).toContain('Bearer [REDACTED]');
    });

    it('treats untrusted HTML as text (XSS defense)', () => {
        const maliciousHtml = '<script>alert("x")</script><img src="x" onerror="alert(\'x\')" /><p>Safe string</p>';
        const textOnly = sanitizeHtmlToText(maliciousHtml);
        expect(textOnly).toContain('Safe string');
        expect(textOnly).not.toContain('<script>');
        expect(textOnly).not.toContain('onerror=');
    });
});
