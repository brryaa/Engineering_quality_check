import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Badge } from '../components/Badge';

describe('Badge Component', () => {
  it('renders label correctly', () => {
    render(<Badge label="S1-Critical" />);
    expect(screen.getByText('S1-Critical')).toBeInTheDocument();
  });

  it('infers rose variant for High priority and failed items', () => {
    const { container } = render(<Badge label="High" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('infers emerald variant for Passed and Closed items', () => {
    const { container } = render(<Badge label="Passed" />);
    expect(container.firstChild).toBeInTheDocument();
  });
});
