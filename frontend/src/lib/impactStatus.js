// Single source of truth for how DIRECT / POTENTIAL / NO_IMPACT map to color,
// reused by the impact cards and the ripple summary chips so they stay in sync.
export const IMPACT_STATUS = {
  DIRECT: {
    label: 'Direct',
    badge: 'bg-badge-high-bg text-badge-high-text',
    dot: 'bg-badge-high-text',
    border: 'border-badge-high-text',
    tint: 'bg-badge-high-bg/70',
  },
  POTENTIAL: {
    label: 'Potential',
    badge: 'bg-badge-medium-bg text-badge-medium-text',
    dot: 'bg-badge-medium-text',
    border: 'border-badge-medium-text',
    tint: 'bg-badge-medium-bg/70',
  },
  NO_IMPACT: {
    label: 'No impact',
    badge: 'bg-brand-dark/8 text-body',
    dot: 'bg-muted',
    border: 'border-muted',
    tint: 'bg-brand-dark/5',
  },
}

export function impactStatusOf(llmLabel) {
  return IMPACT_STATUS[llmLabel] ? llmLabel : 'NO_IMPACT'
}
