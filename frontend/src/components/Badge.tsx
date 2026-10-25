import React from 'react';

interface BadgeProps {
  label: string;
  variant?: 'cyan' | 'emerald' | 'amber' | 'rose' | 'slate' | 'indigo';
}

export const Badge: React.FC<BadgeProps> = ({ label, variant }) => {
  let computedVariant = variant;
  if (!computedVariant) {
    if (label === 'High' || label.startsWith('S1') || label === 'Failed' || label === 'Fail' || label === 'Rejected') {
      computedVariant = 'rose';
    } else if (label === 'Medium' || label.startsWith('S2') || label === 'Marginal' || label === 'Review-Eng' || label === 'Investigating') {
      computedVariant = 'amber';
    } else if (label === 'Low' || label === 'Passed' || label === 'Pass' || label === 'Closed' || label === 'Implemented' || label === 'Confirmed') {
      computedVariant = 'emerald';
    } else if (label === 'In Progress' || label.startsWith('S3') || label === 'Approved') {
      computedVariant = 'cyan';
    } else {
      computedVariant = 'slate';
    }
  }

  const variantStyles: Record<string, React.CSSProperties> = {
    cyan: { background: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee', border: '1px solid rgba(6, 182, 212, 0.3)' },
    emerald: { background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' },
    amber: { background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' },
    rose: { background: 'rgba(244, 63, 94, 0.15)', color: '#fb7185', border: '1px solid rgba(244, 63, 94, 0.3)' },
    indigo: { background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)' },
    slate: { background: 'rgba(148, 163, 184, 0.15)', color: '#cbd5e1', border: '1px solid rgba(148, 163, 184, 0.3)' }
  };

  const currentVariantStyle = variantStyles[computedVariant || 'slate'] || variantStyles.slate;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: 600,
        letterSpacing: '0.025em',
        whiteSpace: 'nowrap',
        ...currentVariantStyle
      }}
    >
      {label}
    </span>
  );
};
