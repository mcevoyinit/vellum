/**
 * Table utility functions — domain-agnostic helpers
 */

/**
 * Resolve a dot-notation path into a value from a nested object.
 * e.g. getNestedValue({ a: { b: 42 } }, 'a.b') → 42
 */
export function getNestedValue(obj: unknown, path: string): unknown {
  if (!obj || typeof obj !== 'object') return undefined;
  const parts = path.split('.');
  let current: unknown = obj;
  for (const part of parts) {
    if (current === null || current === undefined) return undefined;
    current = (current as Record<string, unknown>)[part];
  }
  return current;
}

/**
 * Relative time formatting (e.g. "5m ago", "2d ago").
 * Returns null if input is falsy or unparseable.
 */
export function timeAgo(date: string | Date | undefined | null): string | null {
  if (!date) return null;
  const then = new Date(String(date)).getTime();
  if (Number.isNaN(then)) return null;
  const seconds = Math.floor((Date.now() - then) / 1000);
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}

/**
 * Format a value for default cell display.
 * Handles strings, numbers, dates, booleans, and null/undefined.
 */
export function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') return value.toLocaleString();
  if (value instanceof Date) return value.toLocaleDateString();
  if (typeof value === 'string') {
    // Try to detect ISO date strings
    if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
      const parsed = new Date(value);
      if (!Number.isNaN(parsed.getTime())) return parsed.toLocaleDateString();
    }
    return value || '—';
  }
  return String(value);
}
