export function formatNumber(val?: number | null, decimals: number = 2): string {
  if (val === undefined || val === null || isNaN(val)) return '—';
  return Number(val).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  });
}

export function formatDateTime(isoString?: string): string {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
